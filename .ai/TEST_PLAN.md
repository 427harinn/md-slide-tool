# TEST_PLAN

## Purpose

Current milestone: M2 Stable IDs and Element Layout.

Verify stable identity and persistent image layout while preserving existing M1 build/open behavior and docx functionality.

## Verification layers

### 1. Deterministic automated checks

Use unit/integration/fixture tests for ID parsing/generation, duplicate detection, QMD preservation, assets schema, PPTX metadata, layout restore/fallback, cleanup, and regressions.

### 2. Independent agent review

- Test Agent maps every AC-M2 ID to evidence.
- Review Agent checks failure paths, stale-title matching, accidental data loss, and regression risk.
- Architecture Agent checks that `element-id` remains general while M2 implements images only, and that M3+ features are not pulled forward.

### 3. HUMAN_REQUIRED

Prefer automated PPTX package/save-reopen validation. If the selected PPTX metadata cannot be proven to survive an actual Microsoft PowerPoint save without a Windows GUI test, report only that specific preservation check as HUMAN_REQUIRED after all agent-executable gates pass.

## M2 required checks

1. ID-free QMD -> add only missing slide/element IDs.
2. Re-render -> IDs byte-for-byte stable.
3. Duplicate IDs -> FAIL without auto-repair.
4. ID augmentation preserves all non-ID QMD content.
5. assets schema v1 validates integer EMU coordinates and supported `type=image`.
6. First render -> existing auto layout -> assets persistence.
7. Second render -> assets layout restored exactly.
8. Title rename with same slide-id -> association preserved.
9. Image path change with same element-id -> layout preserved.
10. Invalid layout -> warning + per-element fallback.
11. Stale entries -> cleaned only after successful render.
12. PPTX metadata contains stable slide/element IDs and survives supported roundtrip.
13. Existing placement tests, root tests, smoke, representative PPTX render, docx regression.
14. Scope scan confirms no M3+ implementation.

## AC-to-check mapping

| AC | Planned evidence |
| --- | --- |
| AC-M2-01 | ID generation/stability/QMD preservation tests |
| AC-M2-02 | duplicate-ID failure tests |
| AC-M2-03 | model/manifest/source review + Architecture Agent |
| AC-M2-04 | PPTX metadata roundtrip test; HUMAN_REQUIRED only if actual PowerPoint preservation remains unverified |
| AC-M2-05 | first-render layout persistence fixture |
| AC-M2-06 | second-render exact layout restore fixture |
| AC-M2-07 | title rename fixture |
| AC-M2-08 | path replacement fixture with same element-id |
| AC-M2-09 | invalid-layout + stale-cleanup tests |
| AC-M2-10 | assets schema/content assertions + Architecture Agent |
| AC-M2-11 | existing regression suite, representative render, docx regression |
| AC-M2-12 | repository scope scan + Review/Architecture |

## Regression baseline

For M2 implementation PRs run relevant:

- `npm test`
- `bash scripts/smoke-test.sh`
- `python3 -m unittest tests/test_postprocess_place.py`
- new M2 unit/integration tests
- representative PPTX render
- docx regression
- `git diff --check`
- latest PR head CI
