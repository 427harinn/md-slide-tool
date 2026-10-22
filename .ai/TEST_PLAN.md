# TEST_PLAN

## Purpose

Current milestone: M3 PPTX -> QMD Import.

Verify safe manual import from an md-slide-tool-managed PPTX into its paired QMD/assets while preserving M1/M2 behavior.

## Verification layers

### 1. Deterministic automated checks

Use constructed PPTX/QMD/assets fixtures for content import, stable IDs, images, crop, unsupported-content guards, and atomic rollback.

### 2. Independent agent review

- Test Agent maps every AC-M3 criterion to concrete evidence.
- Review Agent checks destructive failure modes, classification mistakes, partial writes, and regressions.
- Architecture Agent checks managed-PPTX scope, source-of-truth boundaries, assets responsibilities, and that M4/M5 are not pulled forward.

### 3. HUMAN_REQUIRED

Prefer fully automated package/Open XML/python-pptx fixtures. Use desktop PowerPoint only for behavior that cannot be reliably reproduced otherwise, especially crop or picture-replacement semantics if needed.

Do not request human checks until all agent-executable gates pass.

## M3 required checks

1. managed PPTX accepted; unrelated PPTX rejected.
2. front matter unchanged.
3. title edit imported.
4. paragraph imported.
5. bullet/numbered list normalized.
6. slide reorder reflected.
7. slide deletion reflected.
8. new slide gets stable ID in QMD and PPTX.
9. existing image move/resize updates exact EMU geometry.
10. crop import and next-render crop reapplication.
11. same identified picture replacement keeps element ID.
12. newly inserted picture gets new element ID.
13. new/changed image extraction under `img/imported/`.
14. shared source image is not destructively overwritten.
15. image deletion reflected after successful validation.
16. unsupported user content causes pre-commit FAIL.
17. injected failures prove atomic rollback for QMD/assets/images/PPTX.
18. title slide/front matter limitation is preserved.
19. existing M1/M2/render/docx regressions pass.
20. scope scan confirms no M4/M5 or unrelated feature implementation.

## AC-to-check mapping

| AC | Planned evidence |
| --- | --- |
| AC-M3-01 | managed/unmanaged CLI fixtures |
| AC-M3-02 | front matter byte-preservation fixture |
| AC-M3-03 | title/reorder/delete stable-ID fixtures |
| AC-M3-04 | new slide ID generation + PPTX writeback |
| AC-M3-05 | paragraph/bullet/numbered-list normalization fixtures |
| AC-M3-06 | image geometry assets assertions |
| AC-M3-07 | crop extraction + render roundtrip |
| AC-M3-08 | replacement-vs-new-picture identity fixtures |
| AC-M3-09 | imported image extraction + shared-source safety |
| AC-M3-10 | image deletion after complete validation |
| AC-M3-11 | unsupported shape/SmartArt/chart/text fixtures + Review |
| AC-M3-12 | staged transaction failure injection / rollback tests |
| AC-M3-13 | source scan + Architecture Agent |
| AC-M3-14 | existing regression suite + representative render/docx |
| AC-M3-15 | repository scope scan + Review/Architecture |

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
