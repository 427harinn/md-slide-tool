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
  -> DEBOUNCING_QMD
  -> RENDERING
  -> IDLE

IDLE
  -> DEBOUNCING_PPTX
  -> IMPORTING
  -> IDLE

RENDERING / IMPORTING
  + new relevant save
  -> PENDING

current operation completes
  + PENDING
  -> re-evaluate latest state once
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
- do not enqueue every filesystem event;
- after the active operation finishes, inspect the newest hashes/state and decide what is actually needed;
- do not cancel an already-running render/import merely because a newer save arrives.

## 6. Debounce

File systems and Office applications may emit multiple events for one logical save.

Requirements:
- coalesce rapid events for the same managed pair;
- debounce is time-based only for event aggregation, never for correctness;
- correctness comes from hashes/generation fingerprints and M3 managed metadata;
- initial implementation should use a conservative configurable value in roughly the 500-1000 ms range and validate it with Windows/PowerPoint fixtures;
- atomic rename/temp-file save patterns must not be interpreted as multiple logical user edits.

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

Maintain only the minimal persistent/runtime information needed to determine whether each side changed since the last successful synchronization.

Do not introduce a second canonical text store.

Permitted examples:
- QMD canonical-body SHA-256;
- managed PPTX package/semantic fingerprint;
- documentId;
- last successful direction/generation metadata.

Do not persist a duplicate title/body JSON representation merely for M4 conflict detection.

The exact persisted representation must be reviewed before implementation. Prefer reconstructible fingerprints over snapshots.

## 9. QMD save -> PowerPoint flow

On QMD save:

1. debounce;
2. obtain the paired managed document state;
3. ask the VS Code side whether the paired QMD editor has additional unsaved changes beyond the save event;
4. ask the host adapter whether the paired presentation is open in PowerPoint and, if open, whether PowerPoint currently has unsaved edits;
5. if PowerPoint has no unsaved edits and there is no independent PPTX-side saved change, run normal M3-capable render;
6. classify resulting PPTX/assets writes as self-generated;
7. update the synchronized fingerprint;
8. return to IDLE.

If PowerPoint has unsaved edits or an independent PPTX change makes overwrite unsafe, enter CONFLICT and do not render over it automatically.

## 10. PowerPoint save -> QMD flow

On PPTX save:

1. debounce until the saved package is stable/readable;
2. inspect VS Code's paired QMD document dirty state;
3. compare saved-state fingerprints against the last synchronized state;
4. if QMD has no unsaved/independent changes, run normal M3 import;
5. classify QMD/assets/PPTX metadata writeback as self-generated;
6. update synchronized fingerprint;
7. return to IDLE.

If QMD contains unsaved editor changes or an independent saved QMD change makes import unsafe, enter CONFLICT and do not overwrite QMD automatically.

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

## 17. PowerPoint dirty-state feasibility gate

Before production implementation proceeds, verify on the real Windows + PowerPoint environment that the host adapter can safely:
- identify the target open presentation;
- read whether it has unsaved changes;
- distinguish closed/open-saved/open-dirty;
- create a comparison copy without changing the original presentation's dirty/saved state;
- handle multiple PowerPoint presentations without selecting the wrong document;
- fail safely if COM/PowerPoint is unavailable.

If these cannot be made reliable without a PowerPoint Add-in, stop and revise the M4 scope instead of guessing based on file locks/timestamps.

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
