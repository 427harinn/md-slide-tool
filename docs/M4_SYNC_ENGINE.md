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

### Docker / Dev Container Core

Owns:
- managed QMD/PPTX watch;
- debounce;
- per-document state machine;
- render/import orchestration;
- pending/coalescing;
- self-generated-write suppression;
- durable sync checkpoint;
- M3 document lock and recoverable transaction integration.

### VS Code Workspace extension

Owns:
- QMD editor dirty-state query;
- QMD destination freeze/unfreeze;
- QMD latest in-memory snapshot for Compare;
- status bar;
- pause/resume;
- conflict prompt;
- sync-state UI.

### Windows Local UI / PowerPoint host adapter

Owns:
- locate the exact paired presentation;
- report closed / open-saved / open-dirty;
- temporarily close a clean target presentation before QMD -> PPTX publication;
- reopen the same presentation after publication;
- create a non-destructive comparison copy from an unsaved presentation using SaveCopyAs or equivalent;
- report host/PowerPoint failures separately from render failures.

PowerPoint/VS Code do not contain render/import/merge logic.

## 5. State machine

Per managed document:

```text
IDLE
  -> DEBOUNCING
  -> CHECKING
  -> PREPARING
  -> FREEZING_DESTINATION
  -> COMMITTING
  -> RESTORING_DESTINATION
  -> IDLE

CHECKING / PREPARING / FREEZING_DESTINATION / COMMITTING / RESTORING_DESTINATION
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

The key simplification in M4 is that synchronization does not write into a destination that is actively being edited in the supported application.

### QMD save -> PPTX

Before publishing a new PPTX:

1. inspect the paired PowerPoint presentation;
2. if open-dirty -> CONFLICT;
3. if open-saved -> close that presentation without saving;
4. if already closed -> continue;
5. verify the on-disk PPTX still matches the state/hash used to start the operation;
6. commit candidate PPTX/assets/checkpoint with the M3 recoverable transaction;
7. if M4 closed the presentation, reopen the updated PPTX;
8. re-evaluate any PENDING event.

PowerPoint application itself does not need to exit.

M4 must never automatically close an open-dirty presentation.

### PPTX save -> QMD

Before publishing imported QMD:

1. inspect the paired VS Code QMD editor;
2. if dirty -> CONFLICT;
3. if open-clean -> enter QMD freeze;
4. freeze means the Workspace extension closes/hides the clean managed QMD editor for the short publication window and marks the document as Syncing;
5. verify the on-disk QMD still matches the state/hash used to start the operation;
6. commit QMD/assets/PPTX metadata/checkpoint with the M3 recoverable transaction;
7. restore/reopen the QMD editor if it had been open;
8. re-evaluate any PENDING event.

T-401 must verify the exact VS Code freeze behavior. If VS Code cannot reliably close/restore a clean text editor without data loss, implementation stops and the design is revised.

M4 does not require a long-lived editor lease/RPC after the destination is frozen.

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
- restart -> hash both sides against the durable checkpoint before automatic sync.

## 9. QMD save -> PPTX flow

```text
QMD save
  -> debounce
  -> pair-level evaluation
  -> PowerPoint state check
      dirty -> CONFLICT
      clean/closed -> continue
  -> render candidate
  -> close clean target presentation if currently open
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
  -> VS Code QMD dirty check
      dirty -> CONFLICT
      clean -> continue
  -> reconstruct import candidate
  -> freeze/close clean QMD editor
  -> final saved-file hash validation
  -> M3 transaction:
       QMD
       assets/imported images as needed
       PPTX metadata writeback if M3 still requires it
       sync checkpoint
  -> restore/reopen QMD editor
  -> re-evaluate pending
```

Because M3 import may write PPTX metadata, T-401 must specifically verify PowerPoint behavior for this flow:
- if the presentation remains open after a user save, either close the clean presentation before the transaction and reopen it afterwards, or remove the M3 PPTX writeback only if separate tests prove that doing so preserves stable IDs/managed metadata correctly;
- do not leave an open presentation writing the same PPTX during import commit.

The implementation must choose one of those two explicit paths before production work proceeds.

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
- restore/reopen destination UI in finally-style cleanup where possible;
- M3 transaction/recovery remains authoritative for file consistency;
- host bridge failure, PowerPoint close/reopen failure, render/import failure and Remote disconnect are distinct diagnostics;
- next save or explicit Retry can re-evaluate after transient failure.

## 17. T-401 feasibility gate

Before production implementation, verify the simplified freeze model on real Windows + Docker Desktop + VS Code Dev Container + PowerPoint.

Required PowerPoint checks:
- exact target identification with multiple presentations open;
- closed / open-saved / open-dirty detection;
- close an open-saved presentation without save prompt/data loss;
- never close an open-dirty presentation automatically;
- reopen the exact updated presentation after commit;
- SaveCopyAs preserves unsaved edits and original dirty state for Compare;
- PPTX -> QMD import path safely handles M3 PPTX metadata writeback by either close/reopen or a separately proven no-writeback design;
- PowerPoint exit/close/reopen failure is reported safely.

Required VS Code checks:
- exact paired QMD dirty-state detection;
- close/hide a clean managed QMD for the short import publication window;
- restore/reopen it after commit;
- dirty QMD is never automatically closed;
- closing/restoring a clean editor does not lose cursor-independent file content or create false dirty state;
- if the user reopens/changes the destination during Syncing, the operation detects the changed saved/dirty state before commit when feasible and otherwise preserves that user buffer for subsequent conflict handling.

Required cross-host checks:
- Workspace -> Local UI state/close/reopen/SaveCopyAs requests return correlated typed results;
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
