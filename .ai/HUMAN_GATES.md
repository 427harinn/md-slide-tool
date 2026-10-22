# HUMAN_GATES

## Purpose

This file defines how Codex reports verification that genuinely requires the user's environment.

The goal is to minimize user intervention.

## Rules

- Do not ask the user to perform manual checks until all currently possible automated checks and independent agent reviews have finished.
- Group manual checks into one handoff whenever possible.
- Give exact steps, expected results, and what evidence to return.
- If a human check fails, diagnose that failure before asking for unrelated checks.
- A HUMAN_REQUIRED result is not a failure by itself; it means the final gate is still open.
- A failed manual test is a FAIL and must be fed back into the correction loop.

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

## M1 automatic extension distribution (PR #14)

The two-layer bridge E2E is already confirmed on Windows: Local UI and Remote Workspace packages were manually installed once for diagnosis, the command routed across hosts, and the correct PPTX opened in PowerPoint. Do not request those same checks again. The remaining gates concern only a normal Reopen in Container install without manual VSIX installation or Extension Development Host.

```text
HUMAN_REQUIRED

H-01: Approve or decline public Marketplace publication
Steps:
1. Decide whether md-slide-tool may publicly publish the Remote Workspace and Local UI VS Code extension packages to the Visual Studio Marketplace.
2. If approved, provide/authorize the publisher account and public listing metadata needed for publication. No publication occurs before this decision.
Expected:
- An explicit decision is recorded. Approval permits the separately prepared publication work; decline leaves standard automatic distribution blocked and M1 incomplete.

Result: WAITING

H-02: Verify automatic package delivery through normal Reopen in Container
Steps:
1. After an approved Marketplace release and configuration update, start Docker Desktop and open the repository in VS Code.
2. Run Dev Containers: Reopen in Container, without manually installing VSIX packages and without starting Extension Development Host.
3. Confirm the Build and Open in Microsoft PowerPoint command is available and run it on a QMD.
Expected:
- Remote Workspace extension is installed in the Dev Container host and Local UI extension is installed in the Windows UI host through the declared dependency.
- Build succeeds and the generated PPTX opens in Windows PowerPoint.
- No lifecycle hook invokes `code --install-extension` and no manual VSIX install is needed.

Result: WAITING
```

After the user replies, update each result to PASS or FAIL.

## Typical md-slide-tool checks

Depending on the milestone:

- Windows + Docker Desktop + VS Code Dev Container startup;
- command availability in normal VS Code use;
- Microsoft PowerPoint opens the correct PPTX;
- already-running PowerPoint behavior;
- Japanese/space-containing real paths;
- PowerPoint editing and save behavior.

These are examples, not automatic requirements for every task.
