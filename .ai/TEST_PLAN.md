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

## M3 required checks

1. M3-managed marker/version/document-id accepted.
2. Unmarked legacy/arbitrary PPTX rejected with re-render guidance.
3. Presentation remains managed if all old normal slide IDs are deleted.
4. QMD body baseline hash match accepted.
5. QMD body changed since render rejected before staging.
6. Front matter byte-preserved.
7. Title-slide role marker survives move.
8. Title slide deletion leaves front matter untouched.
9. Duplicate title marker fails.
10. Missing/ambiguous title marker with ID-less title-layout slide fails.
11. New supported normal slide before/after title slide gets new ID.
12. Malformed/duplicate slide IDs fail.
13. Title/paragraph/bullet/numbered list normalized.
14. Slide reorder reflected.
15. Slide deletion reflected.
16. Existing image move/resize updates exact EMU geometry.
17. Malformed/duplicate element IDs fail.
18. Crop schema v1 read compatibility.
19. v1 -> v2 migration.
20. Zero/positive/PowerPoint-valid negative crop preserved.
21. Invalid crop rejected.
22. PPTX -> assets v2 -> PPTX crop roundtrip.
23. Same identified picture replacement keeps element ID.
24. Newly inserted picture gets new element ID.
25. New/changed image extraction under `img/imported/`.
26. Shared source image is not destructively overwritten.
27. Image deletion reflected only after full validation.
28. Master/layout inherited content is not imported.
29. Supported placeholders are imported structurally.
30. Unknown slide-local shape/text/chart/SmartArt/etc. causes pre-commit FAIL.
31. Handled failure after every file replacement rolls back.
32. Simulated abrupt termination leaves recoverable transaction journal.
33. Next render/import auto-recovers old/new-known states.
34. Recovery stops rather than overwrites if a target hash matches neither old nor new.
35. Existing M1/M2/render/docx regressions pass.
36. Scope scan confirms no watcher/sync/full conflict merge or unrelated feature implementation.

## AC-to-check mapping

| AC | Planned evidence |
| --- | --- |
| AC-M3-01 | managed marker/version/document-id + unmarked rejection fixtures |
| AC-M3-02 | front matter byte-preservation fixture |
| AC-M3-03 | stable slide ID title/reorder/delete + malformed/duplicate fixtures |
| AC-M3-04 | new slide ID + title-layout ambiguity fixtures |
| AC-M3-05 | paragraph/bullet/numbered-list normalization fixtures |
| AC-M3-06 | image geometry + element-ID validation fixtures |
| AC-M3-07 | schema v1/v2 crop migration + crop roundtrip |
| AC-M3-08 | replacement-vs-new-picture identity fixtures |
| AC-M3-09 | imported image extraction + shared-source safety |
| AC-M3-10 | image deletion after complete validation |
| AC-M3-11 | template structural fixtures + unsupported slide-local FAIL |
| AC-M3-12 | commit failure injection + crash journal recovery |
| AC-M3-13 | source scan + Architecture Agent |
| AC-M3-14 | existing regression suite + representative render/docx |
| AC-M3-15 | repository scope scan + Review/Architecture |
| AC-M3-16 | managed custom properties/title metadata save-reopen evidence |
| AC-M3-17 | QMD changed-since-render hash mismatch fixture |
| AC-M3-18 | title-role move/delete/duplicate/ambiguity fixtures |

## Regression baseline

For implementation PRs run relevant:

- `npm test`
- `bash scripts/smoke-test.sh`
- M2 Python tests
- new M3 unit/integration tests
- representative QMD -> PPTX render
- representative PPTX -> QMD -> PPTX roundtrip
- docx regression
- `git diff --check`
- latest PR head CI

Any unavailable verification must be reported as UNVERIFIED or HUMAN_REQUIRED, never PASS.
