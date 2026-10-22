# TEST_PLAN

## Purpose

This plan verifies the M1 build-and-open capability: the Dev Container builds a QMD through the existing `slidegen render` path and the Local UI extension opens the resulting PPTX through the host bridge. Marketplace publication and automatic extension delivery are future Release / Distribution work, not M1 completion gates.

## Verification layers

### 1. Deterministic automated checks

Use reproducible tests for extension manifests, packaging, failure handling, path mapping, repository scope, and existing build regressions. Run the checks from the documented container environment when Docker is available.

### 2. Independent agent review

The Review Agent checks implementation correctness, fallback behavior, and scope. The Architecture Agent checks the M1 responsibility split and confirms no future milestone has been pulled in. These reviews do not replace deterministic checks.

### 3. Confirmed Windows environment behavior

The user has confirmed the two-layer extension setup on Windows: Local UI package and Dev Container Workspace package were installed manually for diagnosis; the command appeared, cross-host routing succeeded, QMD built in the container, path mapping succeeded, and the correct PPTX opened in Windows PowerPoint. Do not repeat these checks for documentation-only changes.

## M1 required checks

1. **Extension behavior tests** (`npm test --prefix vscode-extension`): output PPTX resolution; build failure or missing output prevents opening; bridge/mapping failure preserves build success; reject invalid/non-PPTX paths; handle Windows, nested, spaced, and Japanese paths.
2. **Packaging and smoke test**: `npm ci --prefix vscode-extension`, package both extensions, verify expected VSIX artifacts and package contents, then run `bash scripts/smoke-test.sh`.
3. **Repository regression**: `npm test`; `python3 -m unittest tests/test_postprocess_place.py`; representative `slidegen render` to PPTX; docx generation/regression using the existing template.
4. **Forbidden-scope scan**: verify no M0-rejected Preview/PDF.js/Webview/Preview-only build script/Preview-only LibreOffice has returned. Check that QMD/PPTX watchers, PPTX -> QMD, `assets.json`, stable IDs, conflict handling, PowerPoint Add-in, and PPTX -> Word remain out of scope.
5. **CI and hygiene**: latest PR head CI passes all relevant checks; run `git diff --check`; verify code changes stay within M1.
6. **Independent reviews**: Review Agent PASS and Architecture Agent PASS.

## AC-to-check mapping

| Acceptance criterion | Verification / check | Current state |
| --- | --- | --- |
| AC-M1-01 — Two-host build/open works | User-confirmed Windows E2E; no rerun required for docs-only changes | PASS |
| AC-M1-02 — Automatic distribution on Reopen in Container | Deferred Release / Distribution; manual VSIX installation was used for the confirmed M1 E2E | DEFERRED; not an M1 gate |
| AC-M1-03 — Supported extension metadata | Manifest inspection and official-specification review | PASS |
| AC-M1-04 — Build through `slidegen render` and resolve expected PPTX | Extension behavior tests, smoke/render; Windows behavior user-confirmed | PASS |
| AC-M1-05 — Build failure or missing PPTX does not open PowerPoint | Explicit failure/no-open tests | PASS |
| AC-M1-06 — Bridge failure preserves successful build | Simulated mapping/open failure tests | PASS |
| AC-M1-07 — Host mapping handles nested, spaced, Japanese paths | Automated path fixtures; existing Windows path behavior user-confirmed | PASS |
| AC-M1-08 — PPTX and docx regressions | Smoke, representative render, docx template generation/ZIP verification | PASS |
| AC-M1-09 — No preview stack or future-scope implementation returns | Forbidden-scope scan and independent reviews | PASS |
| AC-M1-10 — CI and automated checks pass | Latest PR head CI, local checks, `git diff --check` | PASS when latest PR head CI is green |
| AC-M1-11 — Marketplace publication requires release decision | Deferred Release / Distribution; no publication in M1 | DEFERRED; not an M1 gate |

## Release / Distribution checks (before formal public release; not M1 gates)

Retain these checks for the release milestone that authorizes Marketplace distribution:

- Confirm a Marketplace publisher and authorize the public listing.
- Publish the UI and Workspace extension packages and establish versioning.
- Add the published Workspace extension ID to `customizations.vscode.extensions`; verify dependency-based Local UI and Remote Workspace placement.
- Verify the ordinary **Reopen in Container** flow without manual VSIX installation or Extension Development Host.
- Verify post-publication updates and compatibility.

These checks must not block M1 completion or determine PR #14 Draft status. External publication remains HUMAN_REQUIRED at the formal release decision.

## Regression baseline policy

For code/configuration changes, run the relevant baseline: `npm test`, `bash scripts/smoke-test.sh`, Python postprocess unit tests, representative PPTX render, docx regression, and `git diff --check`. If Docker/Quarto or another environment dependency is unavailable, report that gate as `UNVERIFIED` or `HUMAN_REQUIRED` according to `.ai/AGENT_WORKFLOW.md`; never report it as PASS. Documentation-only changes still require doc consistency review, latest PR head CI status, and independent Review and Architecture checks as specified for the task.
