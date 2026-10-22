# ACCEPTANCE_CRITERIA

## Purpose

Acceptance criteria define what must be true before a task or milestone can be considered complete.

They must be written or confirmed before implementation begins.

## Format

Use stable IDs.

```text
AC-01: <observable requirement>
Verification: AUTOMATED | HUMAN_REQUIRED
Status: PASS | FAIL | UNVERIFIED | HUMAN_REQUIRED
Evidence: <test command, test file, log, or manual confirmation>
```

## Rules

- Criteria must describe observable behavior, not implementation preference.
- Every required behavior must have at least one acceptance criterion.
- Existing formal features such as `slidegen render` and docx must receive regression criteria when touched.
- Environment-specific behavior must explicitly state the required environment.
- If a criterion cannot be verified by Codex, mark it HUMAN_REQUIRED before implementation instead of discovering that at the end.
- Do not silently downgrade a required criterion because the current agent environment cannot execute it.
- When requirements change during implementation, update the criteria before changing code.

## Example

```text
AC-01: A successful QMD build produces the expected final PPTX.
Verification: AUTOMATED

AC-02: A build failure must not open PowerPoint.
Verification: AUTOMATED

AC-03: In Windows + Docker Desktop + VS Code Dev Containers, the generated PPTX opens in Microsoft PowerPoint.
Verification: HUMAN_REQUIRED

AC-04: Existing docx rendering continues to succeed.
Verification: AUTOMATED
```

The current milestone may add task-specific criteria below or in its dedicated design document.
