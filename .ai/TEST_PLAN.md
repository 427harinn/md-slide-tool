# TEST_PLAN

## Purpose

The test plan maps every acceptance criterion to a concrete verification method before implementation begins.

## Verification layers

### 1. Deterministic automated checks

Use tests or commands for behavior that can be reproduced in the agent environment.

Examples:

- unit tests;
- integration tests;
- smoke tests;
- CLI exit codes;
- deterministic file validation;
- PPTX/DOCX archive validation;
- path mapping;
- fixture-based rendering.

### 2. Independent agent review

Use subagents for non-deterministic repository-level checks.

Examples:

- responsibility boundaries;
- stale experiment reintroduction;
- scope creep;
- architecture consistency;
- missing regression coverage.

Agent review does not replace deterministic tests.

### 3. HUMAN_REQUIRED environment checks

Use only when the actual environment cannot be reproduced reliably by the agent.

Examples:

- Windows host application integration;
- VS Code Dev Container GUI lifecycle;
- Microsoft PowerPoint behavior;
- visual or physical-device validation.

## Required mapping

Before implementation, create a mapping like:

| Acceptance criterion | Verification | Planned check | State |
| --- | --- | --- | --- |
| AC-01 | AUTOMATED | `npm test` / named test | UNVERIFIED |
| AC-02 | AUTOMATED | smoke test | UNVERIFIED |
| AC-03 | HUMAN_REQUIRED | Windows E2E steps | HUMAN_REQUIRED |

No required AC may be left without a planned verification.

## Environment limitation rule

If the current Codex environment cannot reproduce a required path:

- mark the gate HUMAN_REQUIRED;
- finish all other automated work first;
- provide the exact user steps and expected result in one batch;
- do not claim milestone completion until the user reports the result.

## Regression baseline for md-slide-tool

When relevant to the change, include:

- `npm test`;
- `bash scripts/smoke-test.sh`;
- `python3 -m unittest tests/test_postprocess_place.py`;
- representative PPTX render;
- docx regression;
- `git diff --check`.

Only run checks relevant to the change, but explain any baseline check intentionally omitted.
