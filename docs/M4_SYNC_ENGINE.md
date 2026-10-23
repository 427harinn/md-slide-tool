# M4: Save-driven Sync Engine v2

## 1. Goal

M4 keeps the normal workflow save-driven without replacing files that are actively owned by VS Code or PowerPoint from another process.

Primary UX:

```text
QMD editing
  -> save QMD
  -> generate a versioned preview PPTX
  -> show the latest preview in PowerPoint

PowerPoint editing
  -> save canonical managed PPTX
  -> import to a QMD candidate
  -> apply to QMD safely
```

M4 is save-level synchronization, not keystroke-level live sync.

## 2. Design rule

**Do not externally replace a canonical file while its supported editor owns it.**

Supported editors:

```text
QMD  -> VS Code
PPTX -> Microsoft PowerPoint desktop
```

This rule replaces the M4 v1 destination-freeze / mutation-broker design.

T-401 showed that:
- VS Code has no demonstrated atomic editor-freeze primitive suitable for external QMD replacement;
- a timed-out cross-host broker operation may complete later;
- safe fencing/settlement across Workspace/Core/Local UI would make M4 substantially more complex than the product requires.

Therefore M4 v2 avoids that class of race instead of building a distributed file-mutation protocol.

## 3. Two working modes

### QMD editing mode

QMD is the active editable source.

Saving QMD generates a **versioned preview PPTX**, not an in-place replacement of the currently open canonical PPTX.

Example:

```text
presentation.qmd
presentation.pptx                 # canonical editable PPTX

.md-slide-tool/previews/<document-id>/
  preview-000001.pptx
  preview-000002.pptx
  preview-000003.pptx
```

The newest preview is opened in PowerPoint for visual confirmation.

A preview PPTX is disposable:
- it is not the canonical editable PPTX;
- it is never imported back into QMD;
- failure to delete an old preview is cleanup debt, not document corruption;
- generated preview IDs/metadata may be retained for diagnostics but do not become synchronization authority.

### PowerPoint editing mode

The canonical managed `presentation.pptx` is the editable PowerPoint document.

Saving the canonical PPTX triggers import candidate creation.

For QMD publication:
- QMD closed -> Core may update the canonical QMD through the existing M3 transaction path;
- QMD open-clean -> Workspace applies the imported QMD text through VS Code APIs and saves it through VS Code;
- QMD open-dirty -> CONFLICT; never overwrite the editor buffer.

M4 v2 does not externally replace an open QMD file.

## 4. Canonical vs preview PPTX

There is exactly one canonical managed PPTX:

```text
presentation.pptx
```

Versioned previews are separate files.

Rules:
- canonical PPTX remains the PowerPoint -> QMD import source;
- preview PPTX is QMD -> visual-preview output only;
- preview saves/edits are never automatically imported;
- preview files carry an explicit preview marker so watcher logic can ignore them as canonical input;
- opening a preview must never cause a canonical PPTX save/import event.

## 5. QMD save -> PowerPoint preview flow

```text
QMD save
  -> debounce
  -> render from current saved QMD
  -> write new versioned preview PPTX
  -> ask Local UI to show that exact preview
  -> if prior md-slide-tool preview is open-clean:
       close prior preview
     else:
       leave it alone
  -> open newest preview
  -> cleanup old closed previews later
```

Important properties:
- never replace an already-open preview file;
- never replace the canonical PPTX merely to refresh visual preview;
- PowerPoint application itself stays open;
- if an older preview has user edits/dirty state, do not close or overwrite it;
- user edits made to preview files are treated as non-canonical and must be surfaced as such.

Initial retention policy:
- keep the newest small bounded set of closed preview files;
- cleanup is best-effort;
- never delete an open/unknown preview.

## 6. Editable PowerPoint command

M4 exposes a command equivalent to:

```text
Open Editable PowerPoint
```

This opens the canonical managed PPTX, not a preview.

If the user wants to switch from QMD visual checking to PowerPoint editing:
1. save QMD;
2. explicitly open the canonical PPTX;
3. edit/save in PowerPoint;
4. M4 imports from the canonical PPTX.

The first M4 v2 implementation does not silently promote a preview to canonical.

A future explicit "Promote preview to editable PPTX" command may be considered only after safety and UX are proven.

## 7. PowerPoint save -> QMD flow

Only the canonical managed PPTX is an automatic import trigger.

```text
canonical PPTX save
  -> debounce / wait until package is stable
  -> create import candidate using M3 import logic
  -> inspect paired QMD editor state

QMD closed
  -> commit QMD/assets/images/PPTX metadata using M3 transaction

QMD open-clean
  -> do not externally replace QMD
  -> Workspace applies candidate QMD text through VS Code API
  -> Workspace saves the document
  -> commit remaining non-QMD transaction outputs coherently

QMD open-dirty
  -> CONFLICT
  -> [Cancel] [Compare]
```

The exact transaction boundary for "open-clean QMD via VS Code API + remaining M3 outputs" must be proven by a focused feasibility probe before production implementation.

If that cannot be made safely recoverable, v2 falls back to:

```text
QMD open-clean
  -> Pending import
  -> apply automatically once QMD is closed
```

This fallback is acceptable for M4.

## 8. Preview while canonical PowerPoint is open

A common desired workflow is:

```text
edit QMD in VS Code
while looking at PowerPoint
```

M4 v2 supports this through preview files.

If canonical `presentation.pptx` is open:
- QMD save still creates a new preview PPTX;
- Local UI may open/show the preview separately;
- canonical PPTX is not replaced;
- no conflict exists merely because canonical PowerPoint is open.

If the canonical PPTX contains unsaved edits:
- those edits remain untouched;
- preview generation is still allowed because it writes a different file;
- switching back to canonical PowerPoint editing may later produce a normal saved-state conflict if both canonical QMD and canonical PPTX changed independently.

## 9. Preview identification and PowerPoint UX

Local UI must distinguish:
- canonical managed PPTX;
- md-slide-tool preview PPTX;
- unrelated presentations.

Preview files must contain enough identity to map them to:
- documentId;
- source QMD;
- preview generation number.

Suggested display behavior:
- keep one latest clean preview visible when practical;
- close the previous md-slide-tool preview only if it is open-clean and exact identity matches;
- never close unrelated presentations;
- never close a dirty preview automatically.

T-402 feasibility must prove the exact PowerPoint behavior before production implementation.

## 10. Conflict rules

M4 v2 still never performs automatic semantic merge.

Conflict exists when canonical states diverge in a way that cannot be safely applied.

Examples:
- canonical PPTX saved while paired QMD editor is dirty;
- canonical QMD and canonical PPTX both changed independently since last successful canonical synchronization;
- applying an imported QMD candidate through VS Code detects unexpected editor/version change.

Conflict UX remains:

```text
[Cancel] [Compare]
```

M4 prepares latest-state snapshots.
M5 owns Semantic Diff and winner-selection/resolution.

Preview files do not participate in canonical conflict detection.

## 11. Checkpoint model

The durable sync checkpoint tracks only canonical states:
- documentId;
- full saved QMD hash including front matter;
- canonical managed PPTX fingerprint;
- generation/version metadata.

Preview fingerprints are optional diagnostics only and never determine canonical sync direction.

A preview render must not advance the canonical PPTX checkpoint.

Canonical checkpoint advances only after a successful canonical QMD <-> canonical PPTX synchronization.

## 12. Watchers

Primary automatic triggers:
- saved canonical QMD;
- saved canonical managed PPTX.

Ignored as canonical triggers:
- preview PPTX files;
- assets generated by the current operation;
- imported images generated by the current operation;
- temporary candidate/staging files.

QMD save may always produce a visual preview even when canonical PPTX is open.

Canonical PPTX save may produce QMD import only for the exact managed canonical path/documentId.

## 13. Responsibility split

### Workspace extension

Owns:
- watch/debounce/pending state;
- QMD dirty/clean state;
- applying imported QMD candidate through VS Code APIs when safe;
- saving the QMD through VS Code when using the open-clean path;
- status UI / pause / conflict prompt;
- requesting Local UI preview/canonical PowerPoint actions.

### Docker/Core

Owns:
- QMD -> preview render;
- canonical PPTX -> import candidate creation;
- stable IDs/assets semantics;
- M3 transaction/recovery for files Core safely owns;
- canonical checkpoint computation;
- deterministic candidate/fingerprint generation.

### Windows Local UI

Owns:
- open exact preview PPTX;
- identify exact preview/canonical presentation by full path/identity;
- close prior clean md-slide-tool preview when requested;
- open canonical editable PPTX on explicit command;
- report PowerPoint state needed for UX/diagnostics.

Local UI no longer owns a cross-host canonical PPTX mutation broker.

## 14. State model

Initial v2 state can remain small:

```text
IDLE
RENDERING_PREVIEW
SHOWING_PREVIEW
IMPORTING
APPLYING_QMD
PENDING
CONFLICT
ERROR
PAUSED
```

No freezeSessionId / committing token / mutation-broker state machine is required for v2 preview generation.

## 15. Recovery

M3 recovery remains authoritative for canonical Core-owned transaction output.

Preview generation:
- is disposable;
- does not require M3 multi-file rollback;
- incomplete preview files are ignored/cleaned.

Canonical PowerPoint -> QMD import:
- must not use an incomplete transaction/checkpoint to choose sync direction;
- existing journal recovery runs before canonical checkpoint interpretation;
- the special open-clean QMD-via-VS-Code path must be separately proven before it is admitted to production.

If that path fails feasibility, use the closed-QMD Pending fallback.

## 16. Feasibility gates before production implementation

### T-402A: Versioned PowerPoint preview

Prove on Windows + Docker Desktop + VS Code Dev Container + desktop PowerPoint:

1. QMD save/render can generate a new preview path without touching canonical PPTX.
2. Local UI can open the exact preview.
3. A previous clean preview can be closed while PowerPoint stays open.
4. A dirty preview is left untouched.
5. Multiple presentations do not cause wrong-target close/open.
6. Japanese/space paths work.
7. Repeated preview generation does not accumulate unbounded files.
8. Preview save/edit never triggers canonical import.

### T-402B: Open-clean QMD apply

Probe VS Code APIs:

1. detect exact paired QMD open-clean/open-dirty;
2. generate candidate text without mutating canonical QMD first;
3. apply candidate to the exact open-clean editor through VS Code APIs;
4. save through VS Code;
5. detect editor/version changes between candidate creation and apply;
6. preserve dirty buffers;
7. determine whether remaining assets/images/PPTX metadata/checkpoint can be committed coherently with this editor-mediated QMD save.

Result:
- PASS -> use editor-mediated apply;
- FAIL -> M4 v2 uses Pending until QMD is closed.

Production implementation must not start until these two probes are evaluated.

## 17. Explicitly superseded M4 v1 design

The following M4 v1 mechanisms are not production requirements after T-401:
- pair-wide destination freeze;
- freezeSessionId state tokens;
- Core/Workspace control pipe for mutation authority;
- QMD mutation broker;
- PPTX mutation broker;
- UNKNOWN broker fencing/settlement protocol;
- transaction-wide cross-host mutation coordination;
- forced close/reopen of canonical PowerPoint merely to refresh QMD preview.

The T-401 evidence remains useful as the reason these mechanisms were rejected.

## 18. Non-goals

M4 v2 does not include:
- keystroke-level live sync;
- automatic semantic merge;
- final M5 diff/resolution UI;
- arbitrary external-editor synchronization;
- PowerPoint Add-in;
- preview-to-canonical promotion;
- incremental rendering optimization;
- PPTX -> Word.
