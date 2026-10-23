# M4: Docker Sync Engine

## 1. Goal

M4 turns the M3 manual roundtrip into save-driven synchronization.

```text
QMD save
  -> automatic render
  -> PPTX update

PowerPoint save
  -> automatic import
  -> QMD/assets update
```

This is save-level near-real-time synchronization. It is not keystroke-level live synchronization.

Normal use should not require a manual Build or `slidegen import` command.

## 2. Product rule

Normal saves synchronize automatically.

If the opposite side contains unsaved or independently changed work, automatic synchronization stops.

```text
possible conflict
  -> [Cancel] [Compare]
```

M4 never silently chooses QMD or PowerPoint as the winner.

M5 owns the final Semantic Diff and winner-selection flow.

## 3. Supported editing model

M4 formally supports this editing model:

```text
QMD  -> VS Code
PPTX -> Microsoft PowerPoint desktop
```

During the few seconds in which M4 updates the opposite side, that destination is temporarily **frozen**.

M4 does not attempt to guarantee concurrent edits from arbitrary external programs during that freeze window. Examples outside the M4 guarantee:

- another text editor writing the managed QMD;
- a script replacing the managed PPTX;
- another process directly modifying managed assets while synchronization is committing.

Before commit, M4 still validates the destination's expected hash/state and uses the existing M3 recoverable transaction. Unexpected state causes the operation to stop rather than intentionally overwrite it.

This scoped editing model replaces the previous design that attempted to coordinate PowerPoint leases, QMD leases and Windows-wide filesystem leases simultaneously.

## 4. Responsibility split

### VS Code Workspace extension (Dev Container host)

The Workspace extension is the M4 synchronization **orchestrator**. It runs in the Dev Container extension host, so orchestration remains on the Docker/Dev Container side while having direct access to VS Code editor state.

Owns:
- managed QMD/PPTX watch;
- debounce and per-document state machine;
- pending/coalescing;
- QMD dirty-state query and QMD freeze/restore;
- requesting PowerPoint state/freeze/restore from the Windows Local UI;
- starting Core recovery/render/import only after the freeze session is established;
- observing freeze invalidation/reopen events;
- self-generated-write suppression metadata;
- status bar, pause/resume and conflict prompt;
- QMD latest in-memory snapshot for Compare.

### Docker / Core scripts

Own:
- M3 document lock;
- transaction recovery;
- render/import candidate creation;
- recoverable transaction commit/rollback;
- durable sync checkpoint commit;
- deterministic file/fingerprint operations.

Core never initiates a VS Code freeze. Automatic M4 Core commands are invoked only by the Workspace orchestrator after a valid freeze session exists.

### Windows Local UI / PowerPoint host adapter

Owns:
- locate the exact paired presentation;
- report closed / open-saved / open-dirty;
- temporarily close a clean target presentation before QMD -> PPTX publication;
- reopen the same presentation after publication;
- create a non-destructive comparison copy from an unsaved presentation using SaveCopyAs or equivalent;
- report host/PowerPoint failures separately from render failures.

PowerPoint/VS Code do not contain render/import/merge logic.

### Freeze session contract

Every automatic M4 operation has one cooperative guard file owned jointly by the Workspace orchestrator and Core:

```text
.md-slide-tool/freeze/<document-id>.json
```

Example logical fields:

```json
{
  "documentId": "document-...",
  "freezeSessionId": "freeze-...",
  "state": "frozen",
  "pendingReopen": false
}
```

Allowed states:
- `frozen`: both supported views are closed/frozen and Core has not begun destructive mutation;
- `invalidated`: reopen/edit happened before the first destructive write; Core must not start commit/recovery mutation;
- `committing`: Core has atomically claimed the destructive transaction window;
- `restoring`: transaction reached a stable committed/rolled-back/recovery state and Workspace is restoring UI.

The Workspace extension creates the guard only after both supported views are successfully frozen. Automatic Core entrypoints receive the `freezeSessionId` and refuse recovery/render/import mutation if the guard is missing, mismatched, or invalidated.

### Commit boundary rule

The freeze invalidation policy changes at one explicit boundary: **the first destructive file mutation**.

Before that boundary:
- QMD/PPTX reopen or edit invalidates the session;
- Core writes no canonical file;
- the operation aborts/re-evaluates.

Immediately before the first destructive mutation:
1. Core re-reads the guard;
2. requires exact documentId/freezeSessionId and state=`frozen`;
3. atomically changes the guard to state=`committing`;
4. only then may `FileTransaction.commit()`, rollback, or transaction recovery mutate canonical files.

After state=`committing`:
- reopen requests no longer cause mid-transaction abort/rollback;
- Workspace/Local UI must reject or immediately re-close supported-app reopen attempts while preserving any unsaved buffer/presentation if one was created;
- such attempts set `pendingReopen=true`;
- the transaction is allowed to reach one stable state: committed, rolled back, or ManualRecoveryRequired;
- after that, Workspace restores/re-evaluates and surfaces CONFLICT if user work exists.

This removes the contradiction between "stop after invalidation" and M3 rollback. Once the transaction owns the commit window, transaction integrity takes priority until a stable state is reached.

### Crash / recovery rule

If Core crashes while the guard says `committing`:
- the guard is stale and does not authorize recovery by itself;
- the transaction journal remains authoritative;
- next automatic invocation must establish a **new pair freeze with a new freezeSessionId first**;
- only under that new frozen session may Core run `recover_transactions()`;
- Core transitions the new guard to `committing` before recovery performs its first destructive mutation;
- unknown hashes still stop with ManualRecoveryRequired.

### Guard transport

The guard file is the single Core-visible coordination mechanism for M4 freeze validity.

Workspace writes/updates it atomically. Core does not need a reverse RPC to ask whether the session is valid.

PowerPoint reopen events and QMD reopen/edit events are handled by Workspace/Local UI and reflected into the guard:
- before commit ownership -> `state=invalidated`;
- after commit ownership -> keep `state=committing`, set `pendingReopen=true`.

This is cooperative coordination for VS Code and PowerPoint only, not an OS-wide file lock.

## 5. State machine

Per managed document:

```text
IDLE
  -> DEBOUNCING
  -> CHECKING
  -> FREEZING_PAIR
  -> RECOVERING_IF_NEEDED
  -> PREPARING
  -> COMMITTING
  -> RESTORING_PAIR
  -> IDLE

CHECKING / FREEZING_PAIR / RECOVERING_IF_NEEDED / PREPARING / COMMITTING / RESTORING_PAIR
  + new relevant save
  -> remember one PENDING intent

after current operation
  + PENDING
  -> re-evaluate both sides once
  -> IDLE / next sync / CONFLICT

unsafe overlap
  -> CONFLICT

operation failure
  -> ERROR

paused by user
  -> PAUSED
```

Rules:
- only one active sync per managed document;
- repeated events coalesce into one PENDING intent;
- pending means "re-check both sides", not "run this direction";
- QMD and PPTX events inside the same debounce window are evaluated together;
- event arrival order never decides the winner.

## 6. Destination freeze

The key simplification in M4 is that automatic synchronization freezes the **paired interactive views before any Core command that may write**, including M3 recovery.

For safety, M4 freezes both supported interactive views for the managed pair when either side may be mutated by recovery/render/import:
- the paired QMD editor if open-clean;
- the paired PowerPoint presentation if open-clean.

A dirty view causes CONFLICT and Core is not started.

The Workspace orchestrator remembers which views were open and restores only those views after Core finishes.

### QMD save -> PPTX

Before starting Core:

1. inspect the paired QMD editor and PowerPoint presentation;
2. if either supported view contains unsaved work that could be affected -> CONFLICT;
3. close/hide the clean QMD editor if open and close the clean paired PowerPoint presentation if open;
4. start a `freezeSessionId` and confirm both sides are frozen;
5. only then invoke the automatic Core entrypoint;
6. Core performs pending M3 recovery first, then render/import preparation as required;
7. Core validates the freeze session and expected saved fingerprints before each destructive recovery/commit phase;
8. commit candidate outputs/checkpoint with the M3 recoverable transaction;
9. Workspace restores/reopens the views that were open before freeze;
10. re-evaluate any PENDING event.

PowerPoint application itself does not need to exit.

M4 must never automatically close a dirty QMD editor or open-dirty PowerPoint presentation.

### PPTX save -> QMD

The same pair-freeze sequence is used before starting Core:

1. inspect both supported views;
2. dirty QMD or dirty paired PowerPoint -> CONFLICT;
3. close/hide clean QMD and close clean paired PowerPoint if currently open;
4. establish `freezeSessionId`;
5. invoke Core only after freeze succeeds;
6. Core performs any pending M3 recovery before import, now while both supported views are frozen;
7. import/transaction may update QMD/assets/images and PPTX metadata without a supported editor holding those files open;
8. restore/reopen views after completion;
9. re-evaluate PENDING.

This also resolves the M3 PPTX metadata-writeback case without a separate PowerPoint publication lease.

T-401 must verify the exact VS Code and PowerPoint freeze/restore behavior. If either cannot be made reliable without data loss, implementation stops and the design is revised.

M4 does not require a long-lived publication lease after the pair is frozen.

### Reopen/edit during Syncing

The response depends on the guard state.

#### Before Core owns the destructive window (`state=frozen`)

If the paired QMD is reopened/edited or the paired PPTX is reopened:
- Workspace/Local UI atomically changes the guard to `invalidated`;
- Core must observe this before changing the guard to `committing`;
- Core performs no destructive transaction mutation;
- user state is preserved;
- Workspace re-evaluates both sides and enters CONFLICT when appropriate.

#### After Core owns the destructive window (`state=committing`)

A mid-transaction invalidation is not allowed to force ad-hoc rollback.

Instead:
- Workspace immediately closes/hides a reopened clean QMD editor and records `pendingReopen=true`;
- Local UI immediately closes a reopened clean PowerPoint presentation and records `pendingReopen=true`;
- if the user manages to create unsaved work before the close completes, that buffer/presentation must not be force-saved or discarded; it is preserved for post-transaction conflict handling;
- Core continues the existing transaction to a stable committed/rolled-back/manual-recovery state;
- after the stable state, Workspace re-evaluates the preserved user work against the resulting files.

T-401 must prove that supported-app reopen can be blocked/re-closed reliably once `state=committing`. If this cannot be made safe enough, the destination-freeze design fails feasibility.

## 7. Pre-commit validation

Destination freeze is the main protection for supported interactive editors.

Immediately before commit, Core also verifies:
- expected QMD full-file hash;
- expected PPTX package hash/fingerprint;
- documentId pairing;
- expected file presence.

If a destination changed unexpectedly after preparation:
- do not publish the candidate;
- restore the destination UI;
- re-evaluate both sides;
- enter CONFLICT if both sides now differ.

This check is a safety stop, not a promise to serialize arbitrary external programs.

## 8. Durable sync checkpoint

M4 keeps minimal synchronization metadata, for example:

```text
.md-slide-tool/sync/<document-id>.json
```

It may include:
- documentId;
- full QMD SHA-256 including front matter;
- M3 canonical body SHA-256 where useful;
- managed PPTX fingerprint;
- generation/checkpoint version.

It must not duplicate canonical title/body content.

The sync checkpoint is staged and committed in the same recoverable transaction as the synchronized outputs.

Crash behavior:
- rolled-back transaction -> old checkpoint remains;
- committed transaction -> new checkpoint is completed/recovered with the committed outputs;
- unknown hashes -> stop for safe recovery; never guess which side won;
- a stale freeze guard never authorizes recovery;
- restart -> establish a new pair freeze first, then run M3 recovery under the new freezeSessionId, then hash both sides against the durable checkpoint.

## 9. QMD save -> PPTX flow

```text
QMD save
  -> debounce
  -> pair-level evaluation
  -> freeze clean paired QMD + PowerPoint views
      dirty -> CONFLICT
  -> Core starts
  -> M3 transaction recovery if needed
  -> render candidate
  -> verify freezeSessionId still valid
  -> final saved-file hash validation
  -> M3 transaction:
       PPTX
       assets
       sync checkpoint
  -> reopen presentation if M4 closed it
  -> re-evaluate pending
```

If closing or reopening PowerPoint fails:
- canonical transaction result remains authoritative;
- report a host/UI error separately;
- do not misreport a successful render as a render failure.

## 10. PPTX save -> QMD flow

```text
PPTX save
  -> debounce / wait until package is stable
  -> pair-level evaluation
  -> freeze clean paired QMD + PowerPoint views
      either dirty -> CONFLICT
  -> Core starts
  -> M3 transaction recovery if needed
  -> reconstruct import candidate
  -> verify freezeSessionId still valid
  -> final saved-file hash validation
  -> M3 transaction:
       QMD
       assets/imported images as needed
       PPTX metadata writeback if M3 still requires it
       sync checkpoint
  -> restore/reopen QMD editor
  -> re-evaluate pending
```

## 11. Manual command interaction / DOCUMENT_BUSY

Manual `slidegen render` / `slidegen import` and M4 automatic sync share the existing M3 document lock.

If automatic sync sees `DOCUMENT_BUSY`:
- keep one PENDING re-evaluation;
- do not spin;
- re-check lock availability with bounded backoff even if no watched file changes;
- when the lock becomes free, recompute both QMD and PPTX from the durable checkpoint;
- choose IDLE / sync / CONFLICT from current state.

M4 never bypasses the M3 document lock.

## 12. Self-generated write suppression

Render/import writes may themselves trigger filesystem events.

M4 suppresses loops using expected committed fingerprints/document identity, not only a fixed time window.

Generated events matching the just-committed state are ignored.

A mismatching event is treated as a real new change and causes pair-level re-evaluation.

## 13. Conflict and Compare

Conflict prompt:

```text
Changes exist in both QMD and PowerPoint.
Compare them before continuing?

[Cancel] [Compare]
```

### Cancel

- no destructive sync;
- current QMD and PowerPoint work remain untouched.

### Compare

Use the latest user-visible states.

Unsaved PowerPoint:
- SaveCopyAs/equivalent temporary PPTX snapshot;
- original remains dirty and is not force-saved.

Unsaved QMD:
- current VS Code in-memory text;
- real QMD is not force-saved.

Comparison reconstruction is non-committing.

M4 prepares the snapshots/normalized data. M5 owns:
- document-wide Semantic Diff;
- slide-grouped presentation;
- hidden internal IDs;
- QMD vs PowerPoint winner selection;
- later finer-grained resolution if needed.

## 14. Status UI

Status bar should expose states equivalent to:
- Synced
- Building...
- Importing...
- Syncing...
- Pending changes
- Conflict
- Error
- Paused

While a destination is frozen/closed by M4, the status must clearly say synchronization is in progress.

## 15. Start / pause

Default:
- sync starts automatically for eligible managed pairs when the Dev Container workspace activates;
- user can Pause / Resume;
- Resume re-evaluates current files against the checkpoint before taking action.

## 16. Error behavior

- no infinite retry;
- FREEZE_INVALIDATED is a normal safe-abort/re-evaluation condition, not a generic render failure;
- restore/reopen destination UI in finally-style cleanup where possible;
- M3 transaction/recovery remains authoritative for file consistency;
- host bridge failure, PowerPoint close/reopen failure, render/import failure and Remote disconnect are distinct diagnostics;
- next save or explicit Retry can re-evaluate after transient failure.

## 17. T-401 feasibility gate

Before production implementation, verify the simplified freeze model on real Windows + Docker Desktop + VS Code Dev Container + PowerPoint.

Required PowerPoint checks:
- exact target identification with multiple presentations open;
- start/end a freezeSessionId for the paired presentation;
- detect PresentationOpen/reopen of the paired PPTX while frozen and invalidate the session before further destructive Core writes;
- reopened dirty presentation is preserved and leads to re-evaluation/CONFLICT;
- closed / open-saved / open-dirty detection;
- close an open-saved presentation without save prompt/data loss;
- never close an open-dirty presentation automatically;
- reopen the exact updated presentation after commit;
- SaveCopyAs preserves unsaved edits and original dirty state for Compare;
- PPTX -> QMD import path safely handles M3 PPTX metadata writeback by either close/reopen or a separately proven no-writeback design;
- PowerPoint exit/close/reopen failure is reported safely.

Required VS Code checks:
- Workspace extension is the M4 orchestrator and freezes the pair before spawning any automatic Core command;
- exact paired QMD dirty-state detection;
- detect reopening/editing of the paired QMD while frozen and invalidate the session before further destructive Core writes;
- reopened dirty QMD buffer is preserved and leads to re-evaluation/CONFLICT;
- close/hide a clean managed QMD for the short import publication window;
- restore/reopen it after commit;
- dirty QMD is never automatically closed;
- closing/restoring a clean editor does not lose cursor-independent file content or create false dirty state;
- if the user reopens/changes the destination during Syncing, the operation detects the changed saved/dirty state before commit when feasible and otherwise preserves that user buffer for subsequent conflict handling.

Required recovery/order checks:
- create a pending M3 transaction, then start automatic M4 sync;
- Workspace freezes both supported views before Core is invoked;
- Core recovery runs only after freeze establishment;
- before the first recovery mutation, Core atomically changes the exact guard from frozen -> committing;
- reopen before that transition invalidates and recovery performs no destructive mutation;
- reopen after that transition is blocked/re-closed, sets pendingReopen, and recovery is allowed to reach a stable state;
- crash while committing leaves the journal; next recovery requires a brand-new pair freeze/session first;
- checkpoint state after partial commit/rollback matches the M3 journal outcome.

Required cross-host checks:
- Workspace -> Local UI state/freeze/restore/SaveCopyAs requests return correlated typed results;
- PowerPoint reopen invalidation event is correlated to the correct freezeSessionId;
- timeout, disconnect, Local UI restart and PowerPoint exit fail safely;
- no arbitrary Windows-wide filesystem lease is required for M4 completion.

If the freeze operations cannot be implemented reliably with supported APIs, stop implementation and revise the design.

## 18. Explicit non-goals / unsupported concurrency

M4 does not guarantee concurrent modification of managed files by arbitrary external programs during the short destination-freeze/commit interval.

This is deliberate scope reduction.

M4 still:
- validates expected hashes immediately before transaction commit;
- uses M3 transaction journal/rollback/recovery;
- stops on unexpected state rather than intentionally overwriting it.

Future hardening may add OS-level exclusive file coordination if real user workflows require it.

Also out of scope:
- keystroke-level live sync;
- automatic field-level merge;
- final M5 Semantic Diff UI;
- incremental/selective render optimization;
- arbitrary PowerPoint shapes beyond M3;
- PowerPoint Add-in unless later required by a redesigned scope;
- Marketplace publication;
- PPTX -> Word.

## 19. Intended user experience

Normal:

```text
edit QMD -> Save
  -> PowerPoint briefly closes/reopens if needed
  -> updated PPTX

edit PowerPoint -> Save
  -> QMD briefly freezes/reloads
  -> updated QMD
```

Conflict:

```text
other side has unsaved/independent work
  -> automatic sync stops
  -> [Cancel] [Compare]
```

The temporary destination freeze is an implementation safety mechanism; the user-facing model remains "save and the other side updates automatically".
