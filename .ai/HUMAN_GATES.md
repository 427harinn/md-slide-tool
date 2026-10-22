# HUMAN_GATES

## Purpose

This file defines verification that genuinely requires the user's environment or an explicit release decision.

## Rules

- Do not ask the user for manual checks until all currently possible automated checks and independent agent reviews have finished.
- Group manual checks into one handoff whenever possible.
- Give exact steps, expected results, and what evidence to return.
- If a human check fails, diagnose that failure before asking for unrelated checks.
- A HUMAN_REQUIRED result is not a failure by itself; it means that gate is still open.

## Required report format

```text
HUMAN_REQUIRED

H-01: <short name>
Steps:
1. ...
2. ...
Expected:
- ...

Result: WAITING
```

## M1 status

No HUMAN_REQUIRED gate remains for M1. The user has already confirmed the Windows two-layer extension setup, command availability, cross-host routing, Dev Container QMD build, host path mapping, and correct PowerPoint open. These checks used manual VSIX placement for diagnosis, which does not prevent M1 completion.

## Release / Distribution (before formal public release; not an M1 gate)

The following gates remain for a future formal public release. They are not active blockers for M1 or PR #14.

```text
HUMAN_REQUIRED

H-01: Authorize Marketplace publisher and public extension listings
Steps:
1. Before formal public release, decide whether the UI and Workspace extensions may be published to the Visual Studio Marketplace.
2. If approved, provide/authorize publisher ownership and listing metadata for a separately planned release task.
Expected:
- An explicit release decision is recorded. No publication occurs as part of M1 or PR #14.

Result: HUMAN_REQUIRED (deferred until formal release)

H-02: Verify standard automatic extension distribution before formal release
Steps:
1. After publication and the corresponding Dev Container configuration is prepared, start Docker Desktop and open the repository in VS Code.
2. Run Dev Containers: Reopen in Container without manually installing VSIX packages or starting Extension Development Host.
3. Confirm the command is available, build a QMD, and open the generated PPTX in Windows PowerPoint.
4. Check Japanese/space paths, an already-running PowerPoint instance, build failure behavior, and editing/saving the output.
Expected:
- The Local UI and Remote Workspace extensions are placed in their intended hosts by the declared distribution mechanism.
- Build/open, path handling, failure behavior, and PowerPoint editing work as expected.

Result: HUMAN_REQUIRED (deferred until formal release)
```

## Typical md-slide-tool checks

Depending on the milestone and release gate:

- Windows + Docker Desktop + VS Code Dev Container startup;
- command availability in normal VS Code use;
- Microsoft PowerPoint opens the correct PPTX;
- already-running PowerPoint behavior;
- Japanese/space-containing real paths;
- PowerPoint editing and save behavior.

These are examples, not automatic requirements for every task.
