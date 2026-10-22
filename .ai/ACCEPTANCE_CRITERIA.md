# ACCEPTANCE_CRITERIA

## Purpose and format

Acceptance criteria define observable requirements before implementation. Keep IDs stable across follow-up revisions; add a new ID rather than reusing an old one.

```text
AC-M1-01: <observable requirement>
Verification: AUTOMATED | HUMAN_REQUIRED
Status: PASS | FAIL | UNVERIFIED | HUMAN_REQUIRED
Evidence: <test, log, or human confirmation>
```

`HUMAN_REQUIRED` is a verification method and also the status while the user-side gate is pending. A criterion is not complete while any required criterion is `FAIL`, `UNVERIFIED`, or `HUMAN_REQUIRED`.

## M1: Dev Container extension distribution and build/open

The remaining M1 issue is standard-flow extension distribution. Do not repeat the already confirmed Windows host bridge checks unless a future implementation changes that path.

### Existing Windows confirmations

- **AC-M1-01 — PASS (user-confirmed):** With the Local UI extension installed on Windows and the Workspace extension installed in the Dev Container, the normal command is visible, the container builds the selected QMD, and Windows Microsoft PowerPoint opens the correct generated PPTX. This confirms the two-host command route, host path mapping, and local `openExternal` for that tested setup.
### Required outcomes for this change

- **AC-M1-02:** Starting with the documented Windows + Docker Desktop + VS Code workflow and choosing **Reopen in Container** makes the public build-and-open command available without the user installing either VSIX or opening Extension Development Host. Both packages must land in their intended hosts: UI package on Windows Local, build package in the Dev Container Workspace host.
  - Verification: AUTOMATED configuration/package checks plus HUMAN_REQUIRED Windows Dev Containers GUI check.
  - Status: HUMAN_REQUIRED
  - Evidence: Manual VSIX installation has been confirmed, but automatic installation has not. Existing lifecycle `code --install-extension` attempts failed because `code` was absent; `customizations.vscode.extensions` cannot point at a local VSIX.
- **AC-M1-03:** The extension distribution mechanism is supported by the current VS Code / Dev Containers extension installation model and does not depend on unavailable lifecycle-hook `code` commands or unsupported local-VSIX entries in `customizations.vscode.extensions`.
  - Verification: AUTOMATED source/config tests and official-specification review.
  - Status: PASS for the documented candidate mechanism.
  - Evidence: Workspace `extensionDependencies` + UI provider `api: "none"` matches official Remote Extensions guidance, confirmed independently by Review and Architecture Agents. Marketplace publication and exact Windows automatic-install behavior remain separate HUMAN_REQUIRED gates under AC-M1-02/11.
- **AC-M1-04:** A successful command invokes the existing `slidegen render` in the Dev Container and opens the expected same-stem final PPTX through the Windows-local UI extension.
  - Verification: AUTOMATED unit/integration checks; Windows E2E already PASS for the manually installed two-package setup and must only be repeated if the distribution change alters execution/routing.
  - Status: PASS for the manually installed two-host route.
  - Evidence: User-confirmed Windows build/open; 18 extension tests, Docker smoke, and representative five-slide `slidegen render` passed.
- **AC-M1-05:** A failed render or missing final PPTX does not request or open a file in PowerPoint.
  - Verification: AUTOMATED.
  - Status: PASS
  - Evidence: Extension failure/missing-output tests passed; the command returns no openable result.
- **AC-M1-06:** Failure to map the container result to a host path or failure to invoke the host opener does not turn a successful PPTX build into a failed render result.
  - Verification: AUTOMATED.
  - Status: PASS
  - Evidence: Extension bridge failure-path tests passed.
- **AC-M1-07:** `/work` to Windows host mapping continues to handle nested paths, spaces, and Japanese characters without corrupting the generated PPTX path.
  - Verification: AUTOMATED path tests; Windows path behavior from the existing successful real run is already user-confirmed for its tested path.
  - Status: PASS for automated mapping fixtures.
  - Evidence: Extension tests passed for Windows paths with Japanese/space characters, nested POSIX paths, and workspace-outside rejection. Previously confirmed Windows bridge was not rerun.
- **AC-M1-08:** Existing `slidegen render`, representative PPTX rendering, and docx generation remain functional.
  - Verification: AUTOMATED regression checks.
  - Status: PASS
  - Evidence: Docker root tests, smoke, isolated five-slide PPTX render/ZIP check, and DOCX template project generation/ZIP check passed.
- **AC-M1-09:** M0-rejected PPTX Preview, PDF.js, Webview preview, preview-only build scripts, and Preview-only LibreOffice are not reintroduced; QMD/PPTX watchers, PPTX-to-QMD, `assets.json`, stable IDs, conflict handling, PowerPoint Add-in, and PPTX-to-Word remain out of scope.
  - Verification: AUTOMATED repository/dependency/config scan plus independent review.
  - Status: PASS
  - Evidence: Automated package/scope scans and independent Review/Architecture reviews found no production reintroduction or M2+ implementation.
- **AC-M1-10:** CI runs the automated extension package/configuration checks and existing relevant repository regression checks; all pass on the PR branch.
  - Verification: AUTOMATED.
  - Status: PASS
  - Evidence: PR #14 head `7152053` GitHub Actions CI run #50 succeeded; local Docker smoke and regression gates also pass.
- **AC-M1-11:** No extension is published to the Visual Studio Marketplace, and no public release/ownership decision is made without explicit human authorization. If Marketplace publication is the only supported standard distribution path, report that prerequisite as a HUMAN_REQUIRED decision and keep the PR Draft.
  - Verification: HUMAN_REQUIRED for any publication decision; automated review can confirm no publish command/workflow was run or added.
  - Status: HUMAN_REQUIRED for the public publication decision.
  - Evidence: Automatic distribution needs a Marketplace listing; no publish action/workflow was run or added. See H-01.

## Scope constraints

Do not implement QMD save watcher, PPTX save watcher, PPTX -> QMD, `assets.json`, stable IDs, conflict handling, PowerPoint Add-in, or PPTX -> Word. Preserve docx and existing `slidegen render`. Do not restore Preview/PDF.js/LibreOffice preview code.
