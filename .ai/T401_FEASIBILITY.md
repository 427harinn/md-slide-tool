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

## Feasibility result

## Source and scope

The initial local checkout was the PR #20 design branch, which did not yet contain `.ai/T401_FEASIBILITY.md`. After fetching PR #21's head branch, I read its probe matrix and used it with the request and `docs/M4_SYNC_ENGINE.md`. This PR adds probe-only helpers, a manual PowerPoint host script, and deterministic fixtures. It does not add an automatic watcher, production synchronization state machine, or production M4 mutation path.

The available host did not have a running PowerPoint or VS Code process, `MD_SLIDE_TOOL_HOST_WORKSPACE` was unset, and Docker's active Dev Container workspace could not be reached from the running extension hosts. Consequently desktop-only evidence is HUMAN_REQUIRED, not PASS.

## T-401 Feasibility Result

| Probe | Result | Evidence / limitation |
| --- | --- | --- |
| PowerPoint state detection | HUMAN_REQUIRED | `scripts/t401-powerpoint-probe.ps1` matches presentations by canonical full path and reads `Presentation.Saved`; no desktop PowerPoint was available to execute it. COM enumeration/FullName errors currently collapse to no match, so the probe must distinguish inspection failure from positively observed `closed` during desktop validation. |
| PowerPoint close/reopen | HUMAN_REQUIRED | Probe closes only a clean exact-path presentation and reopens the same path; multiple presentations, save prompts, data retention and app survival require desktop verification. |
| PowerPoint reopen detection | HUMAN_REQUIRED | `WatchReopen` correlates the observation with `freezeSessionId`, but polling is not event delivery and has not run against desktop PowerPoint. |
| Local UI staged-file access | UNVERIFIED | Added a Local UI command that asks Workspace to stage an actual repository PPTX under the `/work` bind mount and read/hash it via the mapped Windows path. Unit tests prove file hash logic only; command was not run in VS Code + Dev Container. |
| PPTX mutation broker | FAIL | The PowerShell probe checks exact target state, expected hash/absence, staged hash and resulting hash and performs the replace itself. It does not validate a live freeze token/control channel or execute as a correlated Workspace-to-Local-UI request; no broker critical section is established. |
| Windows atomic replace | CONDITIONAL | The probe uses `File.Replace` for replace and `File.Move` for create and refuses an open PowerPoint target. Its same-drive-root comparison is only a heuristic, not proof of same volume (for example, mounted volumes/reparse points); no actual Windows replace was run. Cross-volume behavior and `File.Replace` semantics remain unverified. |
| VS Code QMD freeze/restore | FAIL | Workspace extension has no public document freeze/close lock. No reliable close/reopen proof exists; an active-editor command can race focus and dirty buffers. |
| Workspace QMD mutation broker | FAIL | Probe helper tests pre/post hashes and a reopen-state race hook, but is not connected to a live editor freeze/restore critical section. Dirty-buffer preservation, false-dirty behavior and exact reopen remain unproven. |
| Commit through broker | FAIL | M3 `commit()` still calls filesystem replace/unlink directly. Tests monkeypatch those call sites to show they are observable; they do not exercise a broker that validates freeze ownership and expected hashes or returns correlated results. |
| Rollback through broker | FAIL | A test hook observes rollback replacements, but no shared mutation abstraction or broker ownership check exists. `TransactionSuspended` currently triggers immediate generic rollback. |
| Recovery through broker | FAIL | Fixtures exercise `committing` and `rolling_back` recovery for create/replace/delete through patched filesystem calls; this is not a broker. Recovery's production path still directly replaces/unlinks. |
| UNKNOWN late-operation fencing | FAIL | Delayed broker fixture returns `UNKNOWN`, then demonstrates the old operation can still replace the target after timeout. Cancellation, settlement or fencing is required before recovery can start. |
| TransactionSuspended | FAIL | Fixtures suspend before operation 2 and during rollback. Current `FileTransaction.commit()` catches `BaseException`: pre-operation suspension immediately rolls back and removes the journal; suspension inside rollback leaves `rolling_back` only because it interrupts the handler, and a later recovery can continue. There is no deliberate suspension contract/exemption. |
| Journal-first startup | UNVERIFIED | A contract fixture asserts journal-check → pair-freeze → recovery → checkpoint/fingerprint reread → pair evaluation. It hardcodes the order and does not exercise a runtime startup coordinator; current M3 has no sync checkpoint/direction selection. |
| Regression | PASS | Root `npm test` (60 tests), `python3 -m unittest discover -s tests` via the bundled Python runtime (70 tests), extension `npm test` (25 tests), and `bash scripts/smoke-test.sh` passed. Windows/Dev Container render remains HUMAN_REQUIRED. |

**Production M4 implementation may begin: NO.**

**PR #20 design remains viable: NO, not as currently specified.** UNKNOWN late completion can still write after timeout, and Workspace has no demonstrated atomic QMD freeze/restore primitive. Revise these contracts before production M4.

## Automated evidence

- `vscode-extension/test/t401Probe.test.js`: path mapping (including Japanese and spaces), traversal rejection, mutation outcomes, hash guards, synchronous reopen race, timeout and late completion, and local staged-file hash probe.
- `tests/test_t401_transaction_broker.py`: monkeypatched M3 filesystem call sites for commit/rollback/recovery; create/replace/delete fixtures, suspension before operation 2 and during rollback, plus final replacement before committed marker. These fixtures do not establish a broker abstraction.
- `tests/test_t401_journal_first.py`: self-contained journal-first order contract with a new-checkpoint fixture; not runtime coordinator evidence.
- The Local UI and Workspace helpers remain probe-only and do not start a watcher or automatic sync.

## Required design changes before production M4

1. Establish and validate an ownership/fencing or settlement protocol that guarantees an UNKNOWN broker operation cannot write after a new recovery session begins. The current delayed-operation probe fails this property.
2. Make `TransactionSuspended` preserve the current journal phase and bypass immediate generic rollback. Recovery must check control before each brokered mutation, including rollback.
3. Introduce one injectable mutation abstraction that covers M3 commit, rollback and recovery without letting Core replace QMD/PPTX after a pre-write acknowledgement.
4. Revisit the QMD freeze design: VS Code exposes dirty state but no atomic editor-freeze primitive. Define a supported, testable restore/reopen contract that preserves an open dirty buffer.
5. Complete actual Dev Container-to-Windows staged PPTX access. Keep the staging file under the `/work` bind mount (or add a verified host-visible staging root); `/tmp/md-slide-tool/freeze` is not mapped by the current host-path helper.
6. Keep Windows replacement staging and target on the same volume, verified by volume identity rather than drive-root string. A different volume cannot use an atomic rename/replace path and must return NOT_MUTATED before replacement.

## HUMAN_REQUIRED desktop run

Run in Windows PowerShell 5.1 with Microsoft PowerPoint installed, and in the active VS Code Dev Container:

1. Run **T-401 Probe: Verify Windows Access to Staged PPTX** from the Command Palette. Expect a byte count and SHA-256 verified result; the temporary staged copy is removed.
2. With one and then multiple presentations open, invoke `State` for the exact canonical target. Verify `closed`, `open-saved`, and `open-dirty` never select a same-name presentation at another path.
3. Run `CloseClean` only for an open-saved fixture and confirm there is no save prompt, no unsaved-data loss, only the target closes, and PowerPoint remains open. Confirm open-dirty returns `NOT_MUTATED`.
4. Mutate the fixture while closed and run `Reopen`; verify the exact path and updated bytes. Run `WatchReopen` with a known freezeSessionId and reopen that exact target before timeout.
5. With PowerPoint closed and target/staged file on the same volume, run the exploratory `Replace` mode only with a disposable fixture and its required document/session/transaction/operation identifiers, freeze-token file, and expected old/new SHA-256 values. It is a standalone direct-write probe, not a broker or race-safe command. Verify target hash equals resulting hash. Repeat across volumes and confirm safe refusal; do not treat drive-root comparison as volume proof.
6. In VS Code, open the paired QMD clean and dirty in turn. Verify exact dirty-state detection, close/hide/restore behavior, no content loss/false dirty state, and a reopen/edit injected immediately before broker mutation. Return NOT_MUTATED or UNKNOWN if an atomic safe result cannot be proven.

Do not report these gates PASS until the actual host results and test evidence are recorded here.
