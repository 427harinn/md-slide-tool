# AGENT_WORKFLOW

## Purpose

This repository uses a lead-agent workflow so that the user gives one instruction to the root Codex, and Codex autonomously delegates implementation, testing, and review to independent subagents.

The user should not be required to create or coordinate additional chats.

## Root / Lead Agent

The Codex conversation that receives the user's task is the Root / Lead Agent.

The Root Agent must:

1. read `AGENTS.md`, `.ai/PROJECT_RULES.md`, `.ai/PROJECT_CONTEXT.md`, `.ai/MILESTONE.md`, `.ai/TASKS.md`, and the files in this workflow;
2. derive or update acceptance criteria before implementation;
3. derive or update the test plan before implementation;
4. delegate implementation and independent verification to actual subagents when subagent capability is available;
5. collect the results;
6. send failed findings back for correction;
7. repeat the required gates after fixes;
8. create or update a PR only after all AI-executable gates pass;
9. report remaining HUMAN_REQUIRED gates together, instead of asking the user to perform small checks throughout the implementation.

Do not simulate subagents by writing multiple role sections in one response. If actual subagent capability is unavailable, state that explicitly and fall back to the existing single-agent workflow.

## Required roles

For changes larger than a trivial documentation-only edit, use these independent roles.

### Planning Agent

Responsibilities:

- check milestone scope and repository constraints;
- identify acceptance criteria;
- identify automated and human-required verification;
- flag architecture decisions that need to be resolved before coding.

The Planning Agent does not implement the feature.

### Implementation Agent

Responsibilities:

- implement the approved task;
- add or update deterministic tests;
- keep changes within current milestone scope;
- report files changed and tests run.

The Implementation Agent must not be the final reviewer of its own work.

### Test Agent

Responsibilities:

- verify every acceptance criterion has a corresponding test or HUMAN_REQUIRED gate;
- run all available automated checks;
- inspect failure-path coverage and regressions;
- report PASS / FAIL / UNVERIFIED / HUMAN_REQUIRED for each gate.

### Review Agent

Responsibilities:

- independently review the diff;
- look for regressions, stale experiments, incorrect assumptions, missing error paths, unnecessary dependencies, and scope creep;
- verify that deleted or rejected approaches were not accidentally reintroduced.

### Architecture Agent

Responsibilities:

- compare the implementation with `PROJECT_RULES.md`, `PROJECT_CONTEXT.md`, `MILESTONE.md`, `ROADMAP.md`, and `REVIEW_CHECKLIST.md`;
- verify responsibility boundaries;
- verify the implementation does not pull future-milestone work forward.

For small tasks the Root Agent may combine Test Agent and Review Agent, but implementation and final independent review must remain separate.

## Gate states

Every required gate must use one of these states:

- **PASS**: verified successfully.
- **FAIL**: verified and incorrect.
- **UNVERIFIED**: verification has not been performed.
- **HUMAN_REQUIRED**: verification cannot be performed reliably in the current agent environment and must be checked by the user.

Rules:

- Never report UNVERIFIED as PASS.
- Never report HUMAN_REQUIRED as PASS before the user confirms it.
- A PR may remain Draft while HUMAN_REQUIRED gates remain.
- A task must not be described as complete while required FAIL or UNVERIFIED gates remain.
- If a HUMAN_REQUIRED gate is essential to milestone completion, explicitly state that the milestone gate is still open.

## Correction loop

If Test, Review, or Architecture Agent reports FAIL:

1. Root Agent summarizes the failure without hiding details.
2. Root Agent sends the concrete finding back to the Implementation Agent.
3. Implementation Agent makes the smallest correction.
4. Relevant automated gates run again.
5. Independent review runs again.

Do not loop indefinitely. Follow the retry/stop rules in `PROJECT_RULES.md`.

## PR rule

Before opening or updating a PR, the Root Agent must provide an internal gate summary:

- acceptance criteria coverage;
- automated tests;
- independent code review;
- architecture review;
- regression tests;
- HUMAN_REQUIRED items.

PRs should be Draft when required HUMAN_REQUIRED gates or known unresolved distribution/environment gates remain.

## Human handoff

When agent-executable work is finished, report the user's required checks in one compact section:

```text
HUMAN_REQUIRED

H-01: <what to do>
Expected: <what success looks like>

H-02: ...
```

Do not make the user discover manual checks one by one unless a failed human check creates a new diagnostic branch.
