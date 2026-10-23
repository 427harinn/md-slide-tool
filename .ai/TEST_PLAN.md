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

### T-401 feasibility tests

Run before production sync-engine implementation:

1. PowerPoint closed -> host adapter reports closed.
2. Target presentation open and saved -> open-saved.
3. Modify target without save -> open-dirty.
4. Querying dirty state must not modify presentation or clear dirty state.
5. SaveCopyAs/equivalent creates a readable copy containing current unsaved edits.
6. Original remains dirty after comparison copy.
7. Original saved path/content is unchanged by comparison copy.
8. Two or more presentations open -> target resolved by canonical paired path/identity, not title alone.
9. Target closed between query and snapshot -> safe failure/re-evaluation.
10. PowerPoint/COM unavailable -> explicit safe error.
11. No timestamp/file-lock heuristic is accepted as the sole dirty-state source.

### Watch/debounce

- one QMD logical save producing multiple change events -> one render;
- one PowerPoint logical save/atomic rename sequence -> one import;
- unrelated files do not trigger;
- assets/imported-image writes from managed operations do not independently trigger;
- deletion/recreation/transient unreadable package is debounced/retried only within bounded handling.

### State machine / pending

- IDLE -> QMD debounce -> RENDERING -> IDLE;
- IDLE -> PPTX debounce -> IMPORTING -> IDLE;
- repeated QMD saves during render -> one pending re-evaluation;
- PPTX save during render -> latest state re-evaluated, not blindly queued;
- repeated events do not grow an unbounded queue;
- per-document serialization and M3 document lock agree.

### Self-write suppression

- render's PPTX write is ignored as self-generated by exact expected result;
- import's QMD/PPTX metadata writeback is ignored as self-generated;
- an external edit immediately after generated write is not swallowed;
- restart with stale in-memory generation token still re-evaluates hashes safely;
- no render -> import -> render loop.

### Conflict detection

- QMD saved while PowerPoint open-dirty -> CONFLICT, no render;
- PPTX saved while VS Code QMD dirty -> CONFLICT, no import;
- saved independent changes on both sides -> CONFLICT;
- only one side changed -> normal automatic sync;
- Cancel changes no canonical file;
- conflict remains visible/understandable after Cancel until state changes or user acts.

### Compare snapshots

- unsaved QMD snapshot contains current editor buffer, not disk text;
- unsaved PowerPoint comparison copy contains current in-memory edits;
- comparison copy leaves original dirty state unchanged;
- non-committing M3 reconstruction never stages/commits canonical files;
- temp cleanup after success;
- crash/failure leaves only identifiable safe temp state;
- internal IDs/hashes are not required in normal comparison UI data.

### Status / controls

- auto-start on eligible workspace activation;
- pause prevents automatic operations;
- resume re-evaluates rather than blindly replaying old events;
- status transitions reflect running/pending/conflict/error;
- per-document state does not leak between two managed presentations.

### Error / diagnostics

- render fail -> ERROR, no infinite retry;
- import fail -> ERROR, no infinite retry;
- Remote Extension Host disconnect classified separately;
- host bridge failure classified separately;
- PowerPoint unavailable/dirty-state query failure classified separately;
- next explicit save/retry can recover after transient failure.

### Regression

- root Python/npm tests;
- M2 render regression;
- M3 PPTX -> QMD -> PPTX roundtrip;
- M3 crash recovery tests;
- VS Code extension host bridge tests;
- smoke test;
- DOCX regression;
- latest PR head CI.

### HUMAN_REQUIRED

Run only after all feasible automated/Test/Review/Architecture gates pass:

- real Windows + Docker Desktop + VS Code Dev Container;
- PowerPoint closed: QMD save auto-renders;
- PowerPoint open-saved: QMD save auto-renders safely;
- PowerPoint open-dirty: QMD save shows Cancel/Compare and does not overwrite;
- QMD dirty: PowerPoint save shows Cancel/Compare and does not overwrite;
- Compare from unsaved PowerPoint uses latest edits while original stays dirty;
- Compare from unsaved QMD uses editor buffer;
- repeated saves/builds do not disconnect/OOM;
- pause/resume;
- normal PowerPoint save -> automatic QMD update.
