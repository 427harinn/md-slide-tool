# T-401 Feasibility

## Purpose

Verify the risky platform assumptions behind M4 before any production sync implementation.

This branch/PR is a feasibility probe only. It may add isolated test helpers, probe commands, fixtures and temporary instrumentation, but must not implement the production M4 sync engine.

## Questions to answer

### PowerPoint / Windows Local UI

- Can the exact paired presentation be classified as closed / open-saved / open-dirty?
- Can an open-saved presentation be closed without saving and reopened reliably?
- Can reopen of the paired PPTX be detected and correlated to the correct freeze session?
- Can Local UI access the staged source needed for a PPTX mutation from the Dev Container workflow?
- Can Local UI perform the final PPTX create/replace/delete on the Windows host with the required atomicity/replace semantics?
- If the broker times out or disconnects, can the operation be proven finished, not-started, or fenced before a later recovery session begins?

### VS Code / Workspace

- Can a clean managed QMD editor be closed/hidden and restored without data loss or false dirty state?
- Can reopen/edit during freeze be detected?
- Can Workspace perform the actual managed-QMD create/replace/delete inside the same critical section that owns the editor freeze?
- Can dirty user buffers be preserved when a broker operation cannot proceed?

### Transaction integration

- Can Core remain the single M3 journal/transaction authority while QMD/PPTX mutations are delegated to brokers?
- Can normal commit, immediate rollback, and recovery all route QMD/PPTX mutations through the same brokers?
- Can broker outcomes be represented as MUTATED / NOT_MUTATED / UNKNOWN and safely resolved with existing old/new hash recovery?
- If a broker returns UNKNOWN, can later recovery be prevented until that old broker operation is confirmed finished or fenced?
- Can TransactionSuspended bypass the current generic BaseException -> immediate rollback path without weakening M3 recovery?
- Can suspension while rolling_back be resumed safely under a later valid pair freeze?
- Can a final replacement followed by suspension before phase=committed be recovered correctly?

### Startup ordering

Verify:

```text
journal check
-> pair freeze if recovery is needed
-> recovery to stable state
-> checkpoint/fingerprint re-read
-> pair evaluation
-> choose render/import/conflict
```

Checkpoint state from an incomplete transaction must never choose sync direction before journal recovery.

## Required evidence

- automated probe tests where possible;
- Windows + Docker Desktop + VS Code Dev Container evidence for cross-host behavior;
- PowerPoint desktop evidence where COM/application behavior matters;
- explicit PASS / FAIL / UNVERIFIED for each question;
- no claim of production readiness from a partial probe.

## Stop conditions

Stop and revise M4 design if any of these cannot be demonstrated safely:

- clean PowerPoint close/reopen and exact targeting;
- clean QMD freeze/restore;
- Workspace QMD mutation broker;
- Windows Local UI PPTX mutation broker;
- rollback/recovery using those same brokers;
- fencing/settling an UNKNOWN broker operation before a new recovery session;
- journal-first startup ordering.

## Output

At the end of T-401, produce:

- feasibility result per item;
- evidence/tests;
- design changes required;
- whether PR #20's design remains viable;
- whether production M4 implementation may begin.
