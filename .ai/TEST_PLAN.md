# TEST_PLAN

## Purpose

Current milestone: M3 PPTX -> QMD Import.

Verify safe manual import from an M3-managed PPTX into its paired QMD/assets while preserving M1/M2 behavior and preventing accidental overwrite/data loss.

## Verification layers

### 1. Deterministic automated checks

Use constructed PPTX/QMD/assets fixtures for managed metadata, title-slide role, QMD baseline hashes, content import, crop, unsupported-content guards, and transaction recovery.

### 2. Independent agent review

- Test Agent maps every AC-M3 criterion to concrete evidence.
- Review Agent checks destructive failure modes, ambiguous classification, stale-QMD overwrite risk, transaction recovery, and regressions.
- Architecture Agent checks source-of-truth boundaries, package-level managed metadata, title-slide role, assets v2 responsibilities, and that M4/M5 are not pulled forward.

### 3. HUMAN_REQUIRED

Prefer fully automated Open XML/python-pptx/package fixtures.

Use desktop PowerPoint only for a preservation behavior that cannot be proved otherwise, such as custom document properties, title-role marker, or crop/replacement semantics after real PowerPoint save.

Do not request human checks until all agent-executable gates pass.

## Pre-implementation feasibility gates

Before production implementation proceeds beyond T-301:

1. Generate representative PPTX files with every currently supported repository PPTX template.
2. Enumerate slide-local shapes, placeholders, master/layout inheritance, and placeholder types.
3. Confirm explicit structural classification rules cover current templates without position/name/color guessing.
4. Confirm package-level managed custom properties and reserved title-role marker survive the selected save/reopen path.
5. Confirm raw crop representation can be extracted and re-applied without visible drift.
6. If any of these cannot be resolved deterministically, stop implementation and report UNVERIFIED rather than inventing heuristics.

## T-301 fixture evidence (2026-10-22)

**Gate: PASS** for all current repository PPTX template sources and python-pptx/Open XML save/reopen scope. The retained fixtures include real Dev Container `slidegen render` outputs for `templates/pptx/template/template.pptx` and `projects/selfintroduction/template.pptx`, with immutable source copies and render provenance under `tests/fixtures/m3/`. Run `python tests/test_m3_feasibility_fixture.py` to verify both outputs and regenerate `tests/fixtures/m3/structure-report.json`.

| Required probe | Result / evidence |
| --- | --- |
| Template slide/master/layout/placeholder/shape inventory | PASS — report enumerates both source templates, their masters/layouts/placeholders/shapes, source hashes, and both rendered decks' slide-local shapes/XML. |
| Title, paragraph, bullet, numbered-list OOXML | PASS — title type 3; normal title type 1; body type 7; ordinary paragraph has `a:buNone`; bullets inherit the body placeholder style; numbered items have `a:buAutoNum`. |
| Renderer image-caption textbox | PASS — slide-local `p:sp` text box, not a placeholder; current M2 name is generic, and the verifier stamps/roundtrips the reserved caption name in a probe copy. |
| Picture bytes and format | PASS — fixture records PNG content type, extension, length and SHA-256, and verifies bytes survive save/reopen. |
| Raw crop read/reapply | PASS — verifier sets and reads OOXML integer `a:srcRect` values including a valid negative value across two save/reopen cycles. |
| Inherited vs slide-local content | PASS — both templates' master/layout prototypes are enumerated separately from `slide.shapes`; observed inherited decorations are not slide-local import candidates. |
| Presentation custom properties | PASS — standard `docProps/custom.xml` managed property survives python-pptx open/save/reopen/save. |
| Reserved title-slide marker | PASS — `slide.name` role marker survives save/reopen alongside normal stable slide IDs. |
| Stable slide/element metadata coexistence | PASS — slide IDs, picture element ID, caption marker, title role, custom property, and crop coexist in one reopened package. |
| Save/reopen supported scope | PASS — custom property, title/caption markers, stable IDs, picture bytes/format and crop verified with python-pptx 0.6.23 on the host and 1.0.2 in the Dev Container; the retained report was generated with 1.0.2. This does not claim a new desktop PowerPoint roundtrip. |

The current caption remains unnamed in production M2 output. M3 rendering must add its reserved marker before import is implemented. Classification rule for T-307: recognize supported placeholder roles structurally, picture shapes by shape type, and only caption text boxes with the reserved marker; reject every other slide-local shape. Do not use position, color, or appearance to classify content.

## M3 required checks

1. M3-managed marker/version/document-id accepted only when assets schema v2 carries the same documentId.
2. Same-body but different-documentId PPTX/QMD pair rejected.
3. Unmarked legacy/arbitrary PPTX rejected with re-render guidance.
4. Presentation remains managed if all old normal slide IDs are deleted.
5. QMD body baseline hash match accepted.
6. QMD body changed since render rejected before staging.
7. Canonical body hash fixtures cover BOM, LF/CRLF/CR, front matter/no front matter, trailing newline and whitespace-only changes.
8. Front matter byte-preserved.
9. Title-slide role marker survives move.
10. Title slide deletion leaves front matter untouched.
11. Duplicate title marker fails.
12. Missing/ambiguous title marker with ID-less title-layout slide fails.
13. New supported normal slide before/after title slide gets new ID.
14. Malformed/duplicate slide IDs fail.
15. Title/paragraph/bullet/numbered list normalized.
16. Slide reorder reflected.
17. Slide deletion reflected.
18. Existing image move/resize updates exact EMU geometry.
19. Malformed/duplicate element IDs fail.
20. Existing generated caption textbox is recognized by reserved marker and roundtrips to image caption.
21. Orphan/duplicate caption marker fails; arbitrary textbox still fails.
22. Crop schema v1 read compatibility.
23. v1 -> v2 migration.
24. Zero/positive/PowerPoint-valid negative crop preserved.
25. Invalid crop rejected.
26. PPTX -> assets v2 -> PPTX crop roundtrip.
27. Same identified picture replacement keeps element ID.
28. Newly inserted picture gets new element ID.
29. New/changed image extraction under `img/imported/`.
30. Shared source image is not destructively overwritten.
31. Image deletion reflected only after full validation.
32. Master/layout inherited content is not imported.
33. Supported placeholders are imported structurally.
34. Unknown slide-local shape/text/chart/SmartArt/etc. causes pre-commit FAIL.
35. Two concurrent first M3 renders from schema v1 serialize on the same bootstrap lock and produce exactly one shared documentId.
36. Bootstrap re-read detects migration completed by another process and reuses the existing documentId.
37. Migrating process keeps bootstrap lock held until it acquires the newly created document lock; a second process attempting entry during this exact handoff cannot enter.
38. Process that discovers an already-completed migration while holding bootstrap acquires the existing document lock before releasing bootstrap.
39. Bootstrap -> document lock handoff follows the documented ordering without deadlock.
40. Per-document concurrent second render/import fails with DOCUMENT_BUSY.
41. Create/replace/delete handled failure after every file operation rolls back.
42. Simulated abrupt termination leaves recoverable transaction journal.
43. Recovery in prepared/committing/rolling_back/committed/rolled_back phases follows documented policy, including committed-cleanup completion without rollback.
44. Recovery stops rather than overwrites if a target hash matches neither old nor new.
45. Existing M1/M2/render/docx regressions pass.
46. Scope scan confirms no watcher/sync/full conflict merge or unrelated feature implementation.

## AC-to-check mapping

| AC | Planned evidence |
| --- | --- |
| AC-M3-01 | managed marker/version/document-id + assets documentId pairing + same-body wrong-pair + unmarked rejection fixtures |
| AC-M3-02 | front matter byte-preservation fixture |
| AC-M3-03 | stable slide ID title/reorder/delete + malformed/duplicate fixtures |
| AC-M3-04 | new slide ID + title-layout ambiguity fixtures |
| AC-M3-05 | paragraph/bullet/numbered-list normalization fixtures |
| AC-M3-06 | image geometry + element-ID validation fixtures |
| AC-M3-07 | schema v1/v2 crop migration + crop roundtrip |
| AC-M3-08 | replacement-vs-new-picture identity fixtures |
| AC-M3-09 | imported image extraction + shared-source safety |
| AC-M3-10 | image deletion after complete validation |
| AC-M3-11 | template structural fixtures + caption companion fixtures + unsupported slide-local FAIL |
| AC-M3-12 | bootstrap-lock first-migration concurrency + gapless migrating/discovered-state lock handoff + document exclusion + create/replace/delete failure injection + phase-specific crash recovery |
| AC-M3-13 | source scan + Architecture Agent |
| AC-M3-14 | existing regression suite + representative render/docx |
| AC-M3-15 | repository scope scan + Review/Architecture |
| AC-M3-16 | managed custom properties/title/caption metadata save-reopen + assets documentId + concurrent first-migration single-ID evidence |
| AC-M3-17 | canonical hash byte fixtures + QMD changed-since-render mismatch fixture |
| AC-M3-18 | title-role move/delete/duplicate/ambiguity fixtures |

## Regression baseline

For implementation PRs run relevant:

- `npm test`
- `bash scripts/smoke-test.sh`
- M2 Python tests
- new M3 unit/integration tests
- representative QMD -> PPTX render
- `bash tests/m3-pptx-qmd-roundtrip.sh` for a real repository-template render, PowerPoint text/caption edit, CLI import, and re-render; asserts punctuation escapes, stable slide identity, and caption-marker retention
- docx regression
- `git diff --check`
- latest PR head CI

Any unavailable verification must be reported as UNVERIFIED or HUMAN_REQUIRED, never PASS.

## M3 execution record (2026-10-23)

- Test Gate: PASS. Dev Container `python3 -m unittest discover -s tests`: 60/60; `npm test`: 60/60.
- Representative roundtrip: PASS. `bash tests/m3-pptx-qmd-roundtrip.sh` rendered from the repository template, edited PPTX title/body/caption text, imported through `slidegen import`, and re-rendered; escaped punctuation, stable slide ID, and caption marker/text were preserved.
- Existing regression: PASS. `bash tests/m2-render-regression.sh` confirmed M2 image layout/stable metadata and DOCX rendering.
- T-301: PASS. `tests/test_m3_feasibility_fixture.py` verifies both retained repository-template render fixtures and package-level Open XML/python-pptx save/reopen probes. No new Microsoft PowerPoint desktop save cycle is claimed.
- Review Gate: PASS. Architecture Gate: PASS. Independent agents inspected the final change set; the Architecture review records a non-blocking visual risk that a caption regenerated below an image moved to the slide edge may clip or overlap nearby content.
- `git diff --check`: PASS. An earlier smoke-test run passed; a later repeat was interrupted during extension `npm ci` and is not counted as a final rerun.

## M4 Test Plan

### T-401 pair-freeze feasibility

Run before production sync-engine implementation.

#### PowerPoint
- freezeSessionId開始後、paired PPTXをPowerPointで再open -> session invalidated;
- freeze中reopen後に編集 -> user presentation preserved, no further destructive automatic write;

1. Closed target -> report closed.
2. Exact paired target open and saved -> report open-saved.
3. Modify without save -> report open-dirty.
4. Open-saved target can be closed without save prompt or data loss.
5. Open-dirty target is never automatically closed.
6. After canonical PPTX update, reopen the exact same path and show the updated presentation.
7. Multiple presentations open -> only the paired target is closed/reopened.
8. SaveCopyAs/equivalent contains current unsaved edits while original stays dirty.
9. PowerPoint close/reopen/exit failure returns a typed failure and does not become "safe".
10. For PPTX -> QMD, verify the M3 PPTX metadata writeback path: either close/reopen the clean presentation around commit, or prove a separately reviewed no-writeback implementation.

#### VS Code QMD
- Workspace extension owns automatic sync orchestration;
- paired QMD/PPTX freeze completes before Core process starts;
- freeze中QMD reopen/edit -> session invalidated;
- dirty reopened buffer preserved for later conflict handling;

11. Exact paired QMD dirty/clean state is reported.
12. Dirty QMD is never automatically closed.
13. Open-clean QMD can be closed/hidden for the publication window.
14. After commit, QMD can be restored/reopened without content loss or false dirty state.
15. If the user reopens/edits during Syncing, current buffer is preserved and later pair-level evaluation can surface conflict rather than silently discard it.

#### Shared freeze guard / transaction boundary
- runtime session is ephemeral: `/tmp/md-slide-tool/freeze/<workspace-key>/<document-id>/<freezeSessionId>/`;
- one primary state token exists: frozen / invalidated / committing / restoring;
- Workspace invalidation uses atomic same-directory rename `frozen -> invalidated`;
- Core ownership claim uses atomic same-directory rename `frozen -> committing`;
- race them repeatedly; exactly one rename succeeds and the loser observes missing source;
- no JSON read-modify-write is used for the frozen/invalidated/committing decision;
- post-ownership reopen uses create-if-absent `pending-reopen`, which cannot replace the primary state token;
- Workspace creates `.md-slide-tool/freeze/<document-id>.json` atomically with exact freezeSessionId;
- Core receives expected session ID and rejects missing/mismatched/invalidated guard;
- reopen immediately before frozen -> committing CAS -> invalidated, zero destructive writes;
- Core atomically changes frozen -> committing before first FileTransaction/recovery mutation;
- reopen immediately after committing transition but before first replace -> pendingReopen, supported view re-closed, transaction continues to stable state;
- reopen immediately after first replace -> no ad-hoc rollback caused by freeze invalidation; existing transaction semantics finish commit/rollback;
- token rename race is injected repeatedly to prove invalidated and committing can never both win;
- stale runtime session after process death cannot be reused.

#### Control-loss / suspend
- Workspace spawns Core with a dedicated control pipe/channel bound to freezeSessionId;
- Core checks control health immediately before every destructive file mutation;
- Workspace shutdown/restart -> pipe EOF;
- Local UI disconnect/restart while committing -> Workspace signals suspend/closes control channel;
- inject control loss before first mutation -> zero destructive writes;
- inject control loss after operation 1 of N -> Core raises TransactionSuspended before operation 2;
- TransactionSuspended leaves journal phase=committing and does not enter normal immediate rollback;
- checkpoint remains old unless phase already reached committed;
- next automatic attempt creates a new freeze session before recovery.

#### Recovery / ordering
- pending M3 transaction fixture + automatic sync -> pair freeze happens before recover_transactions();
- recovery destructive step checks valid freezeSessionId;
- QMD reopen during recovery -> invalidate, stop later destructive writes, safe re-evaluate;
- PowerPoint reopen during recovery -> invalidate, stop later destructive writes, safe re-evaluate;

#### Cross-host
- freeze/restore request and reopen invalidation event share freezeSessionId;

16. Workspace -> Local UI state request works with typed correlated response.
17. Workspace -> Local UI close/reopen request targets the exact presentation.
18. SaveCopyAs request returns the correct temporary result.
19. Timeout, Remote disconnect, Local UI restart, PowerPoint exit, malformed response and stale response fail safely.
19a. If disconnect occurs before commit ownership, the session invalidates and Core performs zero destructive writes.
19b. If disconnect occurs after commit ownership, Core suspends before the next mutation and leaves the transaction journal for recovery under a new freeze session.
20. No Windows-wide filesystem lease is required for M4 completion.

If the destination-freeze operations cannot be made reliable with supported APIs, feasibility FAILS and production implementation stops.

### Watch / debounce / pending

- one QMD logical save -> one effective render;
- one PPTX logical save -> one effective import;
- duplicate events coalesce;
- same-window QMD + PPTX events -> one pair-level evaluation;
- repeated events during active sync -> one PENDING intent;
- no unbounded FIFO queue;
- assets/imported-image generated events do not become independent user triggers.

### QMD -> PPTX

- PowerPoint closed -> render/commit succeeds;
- PowerPoint open-saved -> close, render/commit, reopen;
- PowerPoint open-dirty -> CONFLICT, no automatic close;
- final saved PPTX hash differs from expected before commit -> abort/re-evaluate;
- close failure -> no unsafe publication;
- commit succeeds but reopen fails -> file result remains authoritative and host/UI error is reported;
- M4-generated PPTX event does not trigger import loop.

### PPTX -> QMD

- QMD closed -> import/commit succeeds;
- QMD open-clean -> freeze, import/commit, restore;
- QMD dirty -> CONFLICT, no automatic close;
- final saved QMD hash differs from expected before commit -> abort/re-evaluate;
- restore failure -> committed file remains authoritative and UI error is reported;
- M3 PPTX metadata writeback path is safe when PowerPoint was open;
- M4-generated QMD/PPTX metadata events do not trigger render/import loop.

### Checkpoint / recovery

- full-QMD hash detects front-matter-only changes;
- checkpoint commits in the same transaction as synchronized outputs;
- crash after partial commit follows M3 recovery;
- automatic recovery is entered only after pair freeze is established;
- invalidation rename wins before recovery claim -> recovery performs zero destructive writes;
- Core committing rename wins -> recovery owns transaction window while control remains healthy;
- control loss during recovery after one mutation -> TransactionSuspended, no immediate rollback, journal retained;
- crash after first recovery replace -> journal retained; new pair freeze/session required before next recovery;
- checkpoint verified for committed, rolled-back, and ManualRecoveryRequired outcomes;
- committed transaction recovery completes matching checkpoint;
- rolled-back transaction retains old checkpoint;
- unknown hash state stops instead of guessing;
- restart re-evaluates both sides against durable checkpoint.

### DOCUMENT_BUSY

- manual render/import holds document lock -> automatic sync records PENDING;
- bounded timer/backoff detects lock release even if no watched file changed;
- no spin retry;
- after release, both sides are re-evaluated from checkpoint.

### Conflict / Compare

- saved independent changes on both sides -> CONFLICT;
- Cancel is non-destructive;
- unsaved PowerPoint Compare uses latest SaveCopyAs snapshot;
- unsaved QMD Compare uses current editor buffer;
- comparison reconstruction never commits canonical files;
- internal IDs/hashes are not required in normal comparison presentation.

### Status / controls / diagnostics

- auto-start;
- pause/resume;
- Syncing state visible while destination is frozen;
- Building/Importing/Pending/Conflict/Error transitions;
- render/import failure distinct from Remote/host/PowerPoint close-reopen failure;
- no infinite retry.

### Unsupported external-writer scope

- documentation states arbitrary external concurrent writers during freeze/commit are outside M4 guarantee;
- unexpected saved-file hash detected before commit causes safe stop;
- tests do not claim Windows-wide writer exclusion.

### Regression

- root Python/npm tests;
- M2 render regression;
- M3 PPTX -> QMD -> PPTX roundtrip;
- M3 transaction/crash recovery;
- VS Code extension bridge tests;
- smoke;
- DOCX regression;
- latest PR head CI.

### HUMAN_REQUIRED

After all agent-executable gates pass:
- Windows + Docker Desktop + VS Code Dev Container;
- PowerPoint closed QMD save auto-render;
- PowerPoint open-clean QMD save -> brief close/reopen with updated content;
- PowerPoint open-dirty QMD save -> Cancel/Compare, no close;
- QMD open-clean PowerPoint save -> brief freeze/reload with imported content;
- QMD dirty PowerPoint save -> Cancel/Compare, no close;
- Compare both unsaved sides correctly;
- repeated saves/pending;
- pause/resume;
- no reconnect/OOM regression.
