# TEST_PLAN

## Purpose

This plan covers the remaining M1 task: automatically distributing the Local UI and Remote Workspace extensions during the standard VS Code **Reopen in Container** workflow. The Windows two-extension build/open path has already been confirmed by the user and is not a requested rerun target unless an implementation changes that path.

## Verification layers

### 1. Deterministic automated checks

Use reproducible tests for extension manifests, packaging, Dev Container settings, failure handling, repository scope, and existing build regressions. Prefer tests that inspect both extension packages and the actual generated VSIX contents. Run the checks from the repository's documented container environment when Docker is available.

### 2. Independent agent review

The Test Agent verifies every AC ID maps to a named check or HUMAN_REQUIRED step. The Review Agent independently inspects the implementation for supported VS Code/Dev Containers behavior, correct extension-host placement, fallback behavior, regressions, and scope. The Architecture Agent checks the M1 responsibility split and confirms no future milestone has been pulled in. These reviews do not replace deterministic checks.

### 3. HUMAN_REQUIRED environment checks

Only VS Code's Windows + Dev Containers GUI install/activation behavior, which cannot be reliably reproduced in the current agent environment, remains a human gate. The already-confirmed manual-VSIX two-host build/open flow is recorded as evidence and should not be requested again.

## Planned automated checks

1. **Extension manifest/package test** (`vscode-extension/test/*.test.js`): assert the UI and Workspace packages have distinct IDs, expected `extensionKind`, expected command ownership, valid entrypoints, and no preview/webview/PDF.js responsibilities. The test invokes the real packaging script after seeding a stale `dist` marker, then asserts stale output is cleared and both VSIX artifacts exist. The vsce file-list check ensures each package candidate contains only its intended manifest and runtime source.
2. **Dev Container distribution/config test** (extend extension manifest tests or add a focused test): parse `.devcontainer/devcontainer.json`; assert the selected supported distribution mechanism targets the local UI host and remote workspace host in the intended way, has no dependency on `postStartCommand`/`postAttachCommand` invoking `code`, and does not list local VSIX paths under `customizations.vscode.extensions`. Assert only explicitly intended extension IDs are configured.
3. **Installation/distribution integration check**: `scripts/smoke-test.sh` runs `npm ci --prefix vscode-extension` from the checked-in lockfile, invokes `npm --prefix vscode-extension run package`, and checks that both named VSIX artifacts exist before running extension tests. This is the same smoke script called by PR CI after root `npm ci`. If the selected supported mechanism inherently requires Marketplace publication, do not fake success or publish: mark the publication decision HUMAN_REQUIRED and retain Draft status.
4. **Extension behavior tests**: `npm test --prefix vscode-extension` (or equivalent documented command); retain tests for render failure => no open, host bridge unavailable => build remains successful, expected PPTX resolution, and path mapping for Windows, nested, spaced, and Japanese paths.
5. **Existing repository regression**: `npm test`; `bash scripts/smoke-test.sh`; `python3 -m unittest tests/test_postprocess_place.py`; representative `slidegen render` to PPTX; docx generation/regression from its existing template. Run the relevant commands in the Dev Container. State any unavailable environment explicitly.
6. **Forbidden-scope scan**: automated repository/dependency checks for `pdfjs-dist`, PDF.js/Webview preview code, preview-only scripts, or Preview-only LibreOffice. Also inspect the diff for QMD/PPTX watchers, PPTX -> QMD, `assets.json`, stable IDs, conflict handling, PowerPoint Add-in, and PPTX -> Word.
7. **CI and hygiene**: PR CI runs `bash scripts/smoke-test.sh`; that script verifies the generated Workspace and UI VSIX files, then runs extension tests. The packaging behavior test seeds a stale `dist` file and verifies a clean rebuild removes it and produces both artifacts. Run `git diff --check`. Confirm no package publish command/workflow was run or added.

## AC-to-check mapping

| Acceptance criterion | Verification | Planned check / evidence | Current state |
| --- | --- | --- | --- |
| AC-M1-01 — Manually installed two-host path works | HUMAN_REQUIRED evidence already supplied by user | User-confirmed: install UI VSIX locally + Workspace VSIX remotely; command visible, container QMD build succeeds, correct PPTX opens in Windows PowerPoint. Do not request this again. | PASS |
| AC-M1-02 — Reopen in Container automatically makes both extensions available in correct hosts without VSIX/Extension Development Host user steps | AUTOMATED + HUMAN_REQUIRED | Automated: manifest/config/package tests (checks 1-3). Human: H-02 in `.ai/HUMAN_GATES.md`, clean Windows Reopen in Container flow after an approved Marketplace release. | HUMAN_REQUIRED |
| AC-M1-03 — Distribution mechanism is supported and avoids known failed/unsupported mechanisms | AUTOMATED + independent review | Check 2; official VS Code/Dev Containers specification references and limitations recorded in design docs; independent Review + Architecture Agents. | PASS for supported metadata design; actual package auto-install remains AC-M1-02 HUMAN_REQUIRED |
| AC-M1-04 — Successful command builds via existing `slidegen render` and selects the expected PPTX for local open | AUTOMATED; prior GUI behavior already confirmed | Extension behavior tests (check 4), container smoke/render (check 5); user-confirmed GUI result in AC-M1-01. Rerun GUI only if implementation changes execution or routing. | PASS for manually installed two-host route and automated regression |
| AC-M1-05 — Render failure or absent PPTX does not open PowerPoint | AUTOMATED | Explicit rejection/no-op assertions in extension behavior unit tests (check 4). | PASS |
| AC-M1-06 — Bridge failure does not invalidate successful PPTX build | AUTOMATED | Simulate mapping/open failure and assert build success/result is retained (check 4). | PASS |
| AC-M1-07 — Host path mapping handles nested, spaced, Japanese paths | AUTOMATED; tested Windows route is existing evidence | Path fixtures in extension unit tests (check 4); do not repeat real Windows mapping test unless mapping code changes. | PASS for automated fixtures; no bridge GUI rerun |
| AC-M1-08 — Existing `slidegen render`, PPTX output, and docx remain functional | AUTOMATED | `npm test`; `bash scripts/smoke-test.sh`; `python3 -m unittest tests/test_postprocess_place.py`; representative PPTX render and docx regression (check 5). | PASS |
| AC-M1-09 — No M0 preview stack or out-of-scope future feature returns | AUTOMATED + independent review | Forbidden-scope scan (check 6), diff review, Architecture Agent review. | PASS |
| AC-M1-10 — Relevant CI and all automated checks pass | AUTOMATED | CI on PR branch, local check results, `git diff --check` (check 7). | UNVERIFIED until current PR CI completes; all local Docker gates PASS |
| AC-M1-11 — No Marketplace publication without authorization; publication decision handled by human if required | AUTOMATED + HUMAN_REQUIRED if publication is necessary | Inspect commands/workflows and PR activity to confirm nothing was published; if official distribution requires listing/publication, report exact required decision as H-01 and stop short of publication. | HUMAN_REQUIRED |

## Human gate boundary

When all agent-executable checks and independent reviews pass, report only the remaining human checks together. For this task, the expected human gate is a clean Windows Dev Containers install/activation check with no manual VSIX installation. The established two-extension build/open behavior is already confirmed and should not be repeated. If Marketplace publication is the only viable standard distribution method, obtain a human decision before any publication; until then keep PR #14 Draft.

## Regression baseline policy

Run the relevant baseline for any code/config change: `npm test`, smoke test, Python postprocess unit tests, representative PPTX render, docx regression, and `git diff --check`. If Docker/Quarto or another environment dependency is unavailable, report that gate as `UNVERIFIED` or `HUMAN_REQUIRED` according to `.ai/AGENT_WORKFLOW.md`; never report it as PASS.
