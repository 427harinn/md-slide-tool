# ACCEPTANCE_CRITERIA

## Purpose and format

Acceptance criteria define observable requirements before implementation. Keep IDs stable across follow-up revisions; add a new ID rather than reusing an old one.

```text
AC-M1-01: <observable requirement>
Verification: AUTOMATED | HUMAN_REQUIRED
Status: PASS | FAIL | UNVERIFIED | HUMAN_REQUIRED
Evidence: <test, log, or human confirmation>
```

`HUMAN_REQUIRED` is a verification method and also the status while a human gate is pending. A criterion is not complete while any criterion required for the current milestone is `FAIL`, `UNVERIFIED`, or `HUMAN_REQUIRED`. Criteria explicitly marked DEFERRED are not required for the current milestone; their gate becomes active when the stated future phase begins.

## M1: QMD -> PPTX -> Microsoft PowerPoint

M1 is the build-and-open capability. Marketplace publication and automatic extension delivery are cross-cutting release/distribution work and are not M1 exit criteria. Do not repeat the already confirmed Windows host bridge checks unless a future implementation changes that path.

### Existing Windows confirmations

- **AC-M1-01 — PASS (user-confirmed):** With the Local UI extension installed on Windows and the Workspace extension installed in the Dev Container, the normal command is visible, the container builds the selected QMD, and Windows Microsoft PowerPoint opens the correct generated PPTX. This confirms the two-host command route, host path mapping, and local `openExternal` for that tested setup.
### Required outcomes for this change

- **AC-M1-02 — DEFERRED (Release / Distribution):** Starting with the documented Windows + Docker Desktop + VS Code workflow and choosing **Reopen in Container** makes the public build-and-open command available without the user installing either VSIX or opening Extension Development Host. Both packages must land in their intended hosts: UI package on Windows Local, build package in the Dev Container Workspace host.
  - Verification: AUTOMATED configuration/package checks plus HUMAN_REQUIRED Windows Dev Containers GUI check before formal release.
  - Status: HUMAN_REQUIRED (DEFERRED until formal release; not an M1 completion criterion).
  - Evidence: Manual VSIX installation has been confirmed for M1 functionality. Automatic installation is a future release/distribution task; existing lifecycle `code --install-extension` attempts failed because `code` was absent, and `customizations.vscode.extensions` cannot point at a local VSIX.
- **AC-M1-03:** Extension host metadata follows current VS Code Remote Extensions guidance and the implementation does not depend on unavailable lifecycle-hook `code` commands or unsupported local-VSIX entries in `customizations.vscode.extensions`.
  - Verification: AUTOMATED source/config tests and official-specification review.
  - Status: PASS for the documented candidate mechanism.
  - Evidence: Workspace `extensionDependencies` + UI provider `api: "none"` matches official Remote Extensions guidance. This metadata does not claim automatic delivery is implemented or verified.
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
- **AC-M1-10:** Latest PR head CI runs the automated extension package/configuration checks and existing relevant repository regression checks; all pass.
  - Verification: AUTOMATED.
  - Status: PASS
  - Evidence: Latest PR head CI is the required evidence; local Docker smoke and regression gates also pass. Do not pin a historical SHA or workflow run number here.
- **AC-M1-11 — DEFERRED (Release / Distribution):** No extension is published to the Visual Studio Marketplace, and no public release/ownership decision is made without explicit human authorization.
  - Verification: HUMAN_REQUIRED at formal release time; automated review can confirm no publish command/workflow was run or added.
  - Status: HUMAN_REQUIRED (DEFERRED until formal release; not an M1 completion criterion).
  - Evidence: No publication action/workflow is part of M1. See the cross-cutting Release / Distribution gate in `docs/ROADMAP.md` and `.ai/HUMAN_GATES.md`.

## Release / Distribution (before formal public release; not an M1 gate)

Retain AC-M1-02 and AC-M1-11 as future release criteria. Marketplace publisher decisions, package publication, automatic extension placement, and post-publication Reopen E2E are not required to complete M1.

## Scope constraints

Do not implement QMD save watcher, PPTX save watcher, PPTX -> QMD, `assets.json`, stable IDs, conflict handling, PowerPoint Add-in, or PPTX -> Word. Preserve docx and existing `slidegen render`. Do not restore Preview/PDF.js/LibreOffice preview code.
