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
