# M4: Docker Sync Engine

## 1. Goal

M4 makes the normal QMD <-> PowerPoint workflow save-driven and automatic.

```text
QMD save
  -> debounce
  -> render
  -> managed PPTX update

PowerPoint save
  -> debounce
  -> import
  -> QMD/assets update
```

The common path should require no manual Build or `slidegen import` command.

M4 does not attempt continuous keystroke-level live synchronization. A successful save is the synchronization trigger.

## 2. Product principle

Normal operation is automatic. Human intervention is required only when synchronization could overwrite unsaved or independently changed work.

The sync engine must prefer stopping over guessing.

```text
normal save
  -> automatic sync

possible conflict
  -> stop
  -> [Cancel] [Compare]
```

The labels shown to users should be ordinary product language. Internal stable IDs, hashes, generation tokens, transaction IDs and watcher details are not user-facing concepts.

## 3. Runtime responsibility split

### Docker / Dev Container

Owns:
- QMD/PPTX file watch
- debounce
- state machine
- render/import orchestration
- self-generated write suppression
- last-synchronized fingerprints
- conflict detection from saved filesystem state
- M3 lock/transaction integration

### VS Code Workspace extension

Owns:
- starting/stopping the sync service for the workspace
- receiving sync state/events from the Core
- detecting VS Code editor dirty state for the paired QMD
- supplying unsaved QMD text as a comparison snapshot when required
- status UI and conflict prompt routing

### Windows Local UI extension

Owns only host-specific PowerPoint integration:
- determine whether the paired presentation is currently open in desktop PowerPoint
- determine whether that open presentation has unsaved changes
- create a non-destructive comparison copy of the current PowerPoint state when requested
- never contain render/import/merge logic

The preferred Windows implementation may use the PowerPoint COM object model or an equivalent host adapter. Keep the host API behind an interface so a future platform-specific implementation can differ.

## 4. Watched inputs

Primary synchronization triggers:
- managed `*.qmd`
- its paired managed `*.pptx`

Do not use `assets.json` or imported image writes as independent user synchronization triggers in M4. They are outputs/inputs of the managed render/import transaction and are covered by self-generated write suppression.

A future milestone may watch explicit source image edits if needed.

## 5. State machine

Per managed document:

```text
IDLE
  -> DEBOUNCING
  -> REVALIDATING
  -> RENDERING or IMPORTING
  -> PRECOMMIT_REVALIDATING
  -> ACQUIRING_COMMIT_BARRIER
  -> COMMITTING
  -> IDLE

RENDERING / IMPORTING / REVALIDATING / PRECOMMIT_REVALIDATING
  + new relevant save
  -> PENDING

ACQUIRING_COMMIT_BARRIER / COMMITTING
  + new relevant save or editor/host change signal
  -> record PENDING
  -> do not start another operation
  -> after barrier release, re-evaluate both sides

current operation completes
  + PENDING
  -> re-evaluate both sides once
  -> next operation or CONFLICT

possible destructive overlap
  -> CONFLICT

operation failure
  -> ERROR

CONFLICT / ERROR
  -> explicit user action or later valid retry
```

Queue policy:
- at most one coalesced pending intent per managed document;
- pending records that "something changed", not a fixed winner/direction;
- after the active operation finishes, inspect both newest QMD and PPTX states and decide what is actually needed;
- do not cancel an already-running render/import merely because a newer save arrives;
- if QMD and PPTX events both arrive during the same debounce window, do not choose the first event. Enter one combined re-evaluation of both sides and either select the only independently changed side or enter CONFLICT.

### Two-phase safety check

Dirty-state/fingerprint checks are not one-time admission checks.

Every destructive sync operation has two validation points:

1. **admission validation** before render/import starts;
2. **pre-commit validation** immediately before publishing canonical QMD/PPTX/assets.

The pre-commit validation must prove that the side which would be overwritten has not changed since the admission snapshot.

Use version/fingerprint tokens captured at admission:
- VS Code document version + current in-memory text fingerprint for QMD;
- PowerPoint host snapshot token sufficient to detect a new edit/save after the dirty-state query;
- saved-file hashes/fingerprints for both sides.

If any protected token changed while render/import was running:
- do not publish over that newer work;
- discard the candidate output;
- transition to PENDING or CONFLICT after re-evaluating both latest sides.

M3 document locks protect md-slide-tool processes only and are not treated as locks on PowerPoint or VS Code user editing.

### Commit barrier / conditional publication

Pre-commit revalidation alone is not sufficient. After the final token check succeeds, M4 must acquire a **commit barrier** before the first canonical file is replaced, and keep that barrier until all canonical files plus the sync checkpoint have reached a committed/recoverable state.

The barrier must close the time-of-check/time-of-use window. A design that performs:

```text
check clean
-> return from check
-> ordinary multi-file replacement
```

is forbidden.

The barrier contract is:

1. revalidate the protected side;
2. acquire a short-lived publish lease or equivalent conditional-publication guard tied to the exact validated version/token;
3. if the lease cannot be acquired because the user edited/saved/reopened the protected side, publish nothing and re-evaluate;
4. while the barrier is held, a user edit/save must either be prevented/serialized or cause the conditional publication to fail before overwriting that edit;
5. commit all staged canonical files and the durable sync checkpoint;
6. release the barrier;
7. if any save/change event occurred during COMMITTING, keep one PENDING intent and immediately re-evaluate after release.

The exact platform mechanisms are mandatory feasibility gates, not implementation guesses.

#### PowerPoint-protected publication

For QMD -> PPTX, when the paired presentation is open, the Windows host adapter must provide an **exclusive presentation publish lease** or equivalent atomic host-side publication primitive.

Required guarantee:
- the lease is granted only for the exact open presentation and exact validated state token;
- from lease acquisition until PPTX publication is complete, PowerPoint cannot accept an unobserved edit/save that would be overwritten by the publication;
- if the presentation state changes before lease acquisition completes, lease acquisition fails;
- the lease is always released on success, failure, timeout, disconnect, or host crash recovery.

Candidate mechanisms may include a host-side critical section that safely closes/replaces/reopens an open-saved presentation, or another mechanism that demonstrably serializes PowerPoint edits across publication. The design does **not** assume that `Presentation.Saved` polling by itself is a lease.

If no supported/reliable PowerPoint barrier can be demonstrated, QMD -> PPTX automatic publication while PowerPoint is open must be disabled/re-scoped rather than accepting a race.

#### QMD-protected publication

For PPTX -> QMD, the VS Code Workspace extension must provide an **editor publish lease** or version-conditional publication primitive for the paired QMD.

Required guarantee:
- the guard is tied to the exact TextDocument version/in-memory fingerprint validated before commit;
- if the document changes after validation, canonical QMD publication fails before overwriting that edit;
- if the editor is already dirty, the guard is not granted;
- the guard covers the actual QMD replacement interval, not only the initial query;
- failure releases the guard and transitions to re-evaluation/CONFLICT.

A simple `document.version` read followed later by an unconditional filesystem replace is forbidden.

If VS Code's supported APIs cannot provide either a short read-only/write lease or version-conditional publication with this guarantee, stop and revise the M4 publication path before implementation.

## 6. Debounce

File systems and Office applications may emit multiple events for one logical save.

Requirements:
- coalesce rapid events for the same managed pair;
- debounce is time-based only for event aggregation, never for correctness;
- correctness comes from hashes/generation fingerprints and M3 managed metadata;
- initial implementation should use a conservative configurable value in roughly the 500-1000 ms range and validate it with Windows/PowerPoint fixtures;
- atomic rename/temp-file save patterns must not be interpreted as multiple logical user edits;
- QMD and PPTX events arriving in one debounce window are merged into one pair-level re-evaluation, never resolved by event arrival order.

## 7. Self-generated write suppression

M4 must not implement "ignore the next event for N seconds" as its correctness mechanism.

Render and import write QMD/PPTX/assets themselves, so watcher loops must be suppressed deterministically.

Use content/fingerprint information such as:
- expected file hash after the operation;
- managed documentId;
- operation/generation token kept in sync-engine runtime state;
- M3 baseline metadata where applicable.

When a watched event matches the exact output committed by the active md-slide-tool operation, classify it as self-generated and do not trigger the opposite operation.

If the resulting file does not match the expected generated state, treat it as a real external/new change and re-evaluate instead of silently suppressing it.

## 8. Last synchronized state

M4 keeps a minimal per-document sync checkpoint, for example under:

```text
.md-slide-tool/sync/<document-id>.json
```

The checkpoint is synchronization metadata, not a second canonical content store.

Required fingerprints:
- full QMD file SHA-256 including BOM/front matter/body bytes;
- canonical QMD body SHA-256 where useful for M3 compatibility;
- managed PPTX package fingerprint or a reviewed deterministic semantic/package fingerprint;
- documentId;
- generation/checkpoint version.

Do not rely on the M3 QMD-body hash alone because it intentionally excludes front matter. A front-matter-only edit must still be visible to M4 conflict detection after restart.

Do not persist duplicated title/body text merely for M4 conflict detection.

### Checkpoint commit / crash rule

Advancing the sync checkpoint must be part of the same recoverable commit boundary as the render/import outputs whose synchronized state it describes.

Preferred implementation:
- extend the existing M3 recoverable transaction to stage the M4 checkpoint alongside QMD/PPTX/assets writes;
- mark the synchronization successful only after that transaction reaches committed state.

There must not be a normal window where canonical output commit succeeds and the process later writes the new checkpoint as an unrelated best-effort file.

Recovery rules:
- if a transaction is recovered to its old state, the old checkpoint remains authoritative;
- if a committed transaction is recovered/completed, its new checkpoint is completed with the same committed state;
- unknown/corrupt checkpoint or a checkpoint whose recorded fingerprints match neither safely reconstructible state causes re-evaluation/CONFLICT or manual recovery, never silent overwrite;
- on workspace/process restart, always hash the current full QMD and paired PPTX and compare them to the durable checkpoint before automatic sync.

## 9. QMD save -> PowerPoint flow

On QMD save:

1. debounce and combine any QMD/PPTX events for the managed pair;
2. read the durable sync checkpoint and current saved fingerprints of both sides;
3. obtain the VS Code QMD document version/dirty state and capture an admission QMD token;
4. through the host bridge, query the paired PowerPoint presentation state and capture an admission PowerPoint token;
5. if PowerPoint is open-dirty, or both saved sides independently changed since the checkpoint, enter CONFLICT;
6. otherwise render to candidate outputs without publishing over the live PPTX yet;
7. immediately before publication, re-query/revalidate the protected QMD/PowerPoint tokens and saved fingerprints;
8. if PowerPoint or protected state changed after admission, discard candidate publication and re-evaluate -> PENDING/CONFLICT;
9. if still safe, acquire the PowerPoint commit barrier / exclusive presentation publish lease for the exact validated token;
10. only while that barrier is held, commit candidate PPTX/assets plus the new sync checkpoint in one recoverable transaction;
11. release the barrier in a finally-style path;
12. if any event/change was observed during COMMITTING, keep PENDING and re-evaluate immediately; otherwise return to IDLE.

A dirty-state query followed by a later unconditional overwrite is forbidden.

## 10. PowerPoint save -> QMD flow

On PPTX save:

1. debounce until the saved package is stable/readable and combine any QMD/PPTX events for the pair;
2. read the durable sync checkpoint and current saved fingerprints of both sides;
3. obtain the VS Code QMD document version/dirty state and capture an admission QMD token;
4. capture the current PowerPoint/file state token through the host bridge;
5. if QMD is dirty, or both saved sides independently changed since the checkpoint, enter CONFLICT;
6. otherwise reconstruct/import to candidate outputs without publishing over the live QMD yet;
7. immediately before publication, re-check the VS Code document version/dirty state and relevant PowerPoint/file token;
8. if QMD or protected state changed after admission, do not publish; re-evaluate -> PENDING/CONFLICT;
9. if still safe, acquire the VS Code QMD editor publish lease / version-conditional publication guard for the exact validated document version;
10. only while that guard is held, commit QMD/assets/PPTX metadata writeback plus the new sync checkpoint in one recoverable transaction;
11. release the guard in a finally-style path;
12. if any event/change was observed during COMMITTING, keep PENDING and re-evaluate immediately; otherwise return to IDLE.

### Manual command interaction / DOCUMENT_BUSY

Manual `slidegen render` / `slidegen import` and automatic sync share the existing M3 document lock.

If the automatic engine receives `DOCUMENT_BUSY`:
- do not treat it as a destructive failure and do not spin-retry;
- record one pending re-evaluation;
- schedule a bounded lock re-check even if no watched file changes: first retry after about 250 ms, then bounded backoff up to about 2 s, with a total wait budget around 10 s;
- any relevant filesystem event may trigger an earlier re-evaluation, but an event is not required;
- once the lock is observed free, immediately recompute both sides from the durable checkpoint;
- if the total wait budget expires, remain PENDING/attention-required rather than spin forever;
- then choose normal sync, CONFLICT, or IDLE from the latest state.

If a manual command encounters the automatic engine holding the lock, existing explicit `DOCUMENT_BUSY` behavior may remain; M4 must not bypass the lock.

## 11. Conflict UX contract

M4 detects and safely enters conflict state. M5 owns the full resolution UI.

When a conflict is detected, show a VS Code prompt using ordinary language. Preferred interaction:

```text
Changes exist in both QMD and PowerPoint.
Compare them before continuing?

[Cancel] [Compare]
```

Context-specific wording may say "PowerPoint has unsaved changes" or "QMD has unsaved changes", but button semantics remain:
- **Cancel**: perform no destructive synchronization; keep both current states untouched.
- **Compare**: create non-destructive snapshots of both latest states and open/hand off to the comparison flow.

Do not show a generic **Continue** button that silently chooses one side.

## 12. Comparison snapshots

Comparison must use the latest user-visible state, including unsaved edits.

### Unsaved PowerPoint

Do not force-save the user's presentation merely to compare.

Use a host-side non-destructive copy operation (for Windows PowerPoint, `Presentation.SaveCopyAs` or equivalent) to create a temporary PPTX snapshot representing the current in-memory presentation while leaving the original presentation's saved/dirty state unchanged.

Feed the temporary PPTX through a non-committing M3 reconstruction path to produce a comparison QMD/semantic representation. It must not overwrite the real QMD/assets/PPTX.

### Unsaved QMD

Use the VS Code TextDocument's current in-memory text as a temporary QMD snapshot. Do not force-save the editor merely to compare.

### Snapshot lifetime

- snapshots are temporary;
- do not become canonical project files;
- clean them after comparison/decision when safe;
- crash leftovers must be identifiable and cleanable without touching user files.

## 13. Diff boundary between M4 and M5

M4 must provide enough normalized data/snapshots for comparison and invoke the comparison entrypoint.

M5 defines the final Semantic Diff and resolution experience.

Target M5 presentation:
- show the entire document's changes;
- group changes by slide for readability;
- within each slide, identify title/body/list/caption/image-layout/crop changes;
- hide internal `slide-id` / `element-id` / metadata noise from normal users;
- initial resolution may choose QMD side or PowerPoint side for the conflict;
- finer per-change resolution can be added only after the basic flow is reliable.

M4 must not implement an automatic field-level merge.

## 14. VS Code status UI

Expose current state in the Status Bar, for example:
- `md-slide-tool: Synced`
- `md-slide-tool: Building...`
- `md-slide-tool: Importing...`
- `md-slide-tool: Pending changes`
- `md-slide-tool: Conflict`
- `md-slide-tool: Error`
- `md-slide-tool: Paused`

The exact wording may be refined during implementation, but the user must be able to tell when work is running and when attention is required.

## 15. Start / pause behavior

Default:
- sync starts automatically when the Dev Container workspace extension activates and discovers eligible managed QMD/PPTX pairs;
- provide an explicit pause/resume command from VS Code;
- pausing prevents automatic render/import but does not alter files;
- resuming re-evaluates current fingerprints before deciding whether to sync or enter conflict.

Do not require the user to manually start a watcher for normal use.

## 16. Failure behavior

On render/import failure:
- stop the current operation;
- preserve M3 transaction/recovery guarantees;
- enter ERROR;
- do not retry forever;
- show a concise VS Code error and make logs available;
- a later explicit save/retry may re-evaluate and run again.

A remote/Dev Container disconnect must not be misreported as a PowerPoint open failure. Diagnostics should distinguish:
- build/import process failure;
- host bridge failure;
- remote connection loss;
- PowerPoint launch/status failure.

## 17. PowerPoint dirty-state and cross-host feasibility gate

Before production implementation proceeds, verify the real Windows + PowerPoint host behavior **and** the complete Local UI <-> Workspace/Core request/response path.

PowerPoint host adapter must safely:
- identify the target open presentation by canonical paired path/identity;
- read whether it has unsaved changes;
- distinguish closed/open-saved/open-dirty;
- produce a state/version token that changes when an edit/save relevant to overwrite safety occurs, or provide an equivalent revalidation mechanism;
- acquire and release an exclusive presentation publish lease (or equivalent atomic host-side publication primitive) tied to that exact validated token;
- prove that edits/saves cannot slip between final validation and PPTX publication while the lease is held;
- create a comparison copy without changing the original presentation's dirty/saved state;
- handle multiple PowerPoint presentations without selecting the wrong document;
- fail safely if COM/PowerPoint is unavailable.

Cross-host bridge must prove:
- Workspace/Core can request PowerPoint state from the Windows Local UI and receive a typed response;
- Workspace/Core can request a comparison snapshot and receive its result/path safely;
- request IDs correlate responses so concurrent documents cannot cross wires;
- timeout, Remote Extension Host disconnect, Local UI restart, PowerPoint exit during request, and malformed/stale responses all fail closed;
- cancellation/disconnect never gets converted into "safe/clean" state;
- pre-commit revalidation can issue a second host request and detect a changed token;
- commit-barrier acquire/release requests are correlated, timeout-safe, and fail closed;
- host disconnect during a held barrier cannot be treated as a successful publication;
- no implementation depends solely on file locks/timestamps.

The VS Code side must separately prove that the paired QMD can be protected by a supported short-lived editor publish lease or version-conditional publication primitive from final validation through replacement. A plain version check followed by unconditional file replacement does not pass this gate.

If either the reverse bridge, the PowerPoint publish lease, or the QMD editor publish guard cannot be made reliable with the existing topology, stop and revise the design before implementation. Do not silently substitute heuristics or add a PowerPoint Add-in without explicit design review.

## 18. Incremental build

Incremental/selective rendering is not required for initial M4.

First make save-driven sync safe and deterministic.

Track optimization separately after M4 stability, for example:
- text change -> full Quarto render;
- geometry/crop-only update -> possible python-pptx fast path;
- avoid unnecessary full rebuilds.

Do not mix an unproven incremental compiler into the first sync-engine implementation.

## 19. Out of scope

M4 does not include:
- keystroke-level live synchronization;
- automatic semantic merge;
- choosing a winner without user input during conflict;
- final M5 Semantic Diff/resolution implementation;
- arbitrary PowerPoint shape support beyond M3;
- PowerPoint Add-in unless the feasibility gate proves the host adapter approach insufficient and design is explicitly revised;
- incremental render optimization;
- Marketplace publication;
- PPTX -> Word.

## 20. Intended M4 completion flow

Normal path:

```text
edit QMD -> Save -> automatic render -> Synced
edit PowerPoint -> Save -> automatic import -> Synced
```

Conflict path:

```text
one side is saved while the other side contains unsaved/independent work
  -> automatic sync stops
  -> Conflict
  -> [Cancel] [Compare]
  -> non-destructive latest-state snapshots
  -> M5 comparison/resolution flow
```
