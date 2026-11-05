# T-402 Feasibility Record (M4 v2 probe)

Date: 2026-10-23
Scope: feasibility probe only. No production watcher, sync state machine, status UI, or PowerPoint window controller was added.

Prerequisites: `.ai/T401_FEASIBILITY.md` was read on the PR #21 source checkout before switching to `codex/m4-design-v2`; that file is not present on this target branch.

## Result

T-402A has deterministic code-level evidence for a unique preview path, marker, source identity, and import-source filtering. Preview is permitted only for an existing schema-v2 managed pair and refuses a pending M3 journal without running recovery. Actual QMD rendering requires the repository's Docker/Quarto environment, and desktop PowerPoint behavior is not available in this environment. Therefore T-402A is **UNVERIFIED overall**, not PASS.

T-402B is **FAIL** for editor-mediated publication. M3 import candidate bytes can be reconstructed without changing canonical files, and a probe helper demonstrates exact-target/version/dirty checks and a Workspace API apply/save sequence. However, VS Code save is outside M3 `FileTransaction`; the remaining assets, imported images, PPTX metadata, and checkpoint cannot be atomically committed with that save or rolled back as one recovery unit. The split-failure fixtures prove observable partial states. Selected path: **PENDING_UNTIL_QMD_CLOSED**; when QMD is closed, use existing M3 transaction import.

Regression: **UNVERIFIED overall**. Root npm, Python, and extension suites pass; the required Bash smoke script could not start in this sandbox.

## T-402A Versioned Preview

| Gate | Result | Evidence / limitation |
| --- | --- | --- |
| Preview generation | UNVERIFIED | `m3_entry.py preview` requires schema-v2 assets and an existing same-document managed canonical PPTX, refuses a pending transaction without recovery, reserves a fresh path, and calls the existing QMD render/postprocess pipeline in preview mode. Actual Quarto/Docker render not run here. |
| Canonical PPTX untouched | PASS (helper fixture only) | Marker is written to a copied candidate and canonical bytes are fingerprinted unchanged in `test_preview_paths_identity_and_canonical_untouched`. This does not invoke `m3_entry preview` or the render pipeline; end-to-end untouched status remains UNVERIFIED with preview generation. |
| Preview identity | PASS (fixture) | Custom properties identify preview marker, documentId, generation, and resolved source QMD path. |
| Preview ignored as import source | PASS (policy fixture) | `is_preview()` distinguishes the marker; import trigger selection must reject marked preview files. Production watcher is out of scope and does not exist. |
| Exact preview path handoff | PASS (mock) | Isolated Local UI helper forwards the exact supplied file URI, including Japanese/space paths. It is not yet wired to the command, and PowerPoint selection/focus remains HUMAN_REQUIRED. |
| Previous clean preview close | HUMAN_REQUIRED | No PowerPoint state controller exists. Cleanup eligibility policy is tested, but actual close behavior is not. |
| Dirty preview preservation | HUMAN_REQUIRED | Policy keeps dirty/unknown/open previews; actual desktop dirty state reporting remains unverified. |
| Canonical PPTX open while previewing | HUMAN_REQUIRED | Distinct output path means there is no file replacement by design; real PowerPoint open-clean/open-dirty coexistence requires Windows check. |
| Preview cleanup | UNVERIFIED | Eligibility policy keeps the exact canonical path, open, dirty, and unknown previews. No real PowerPoint open/dirty inventory or cleanup controller exists, so actual cleanup safety is not proven. |
| Canonical checkpoint unchanged | UNVERIFIED | No canonical checkpoint writer/state exists on this branch, so the preview fixture cannot observe a checkpoint value. Preview skips M3 render commit and rejects a pending journal, but checkpoint non-mutation needs re-evaluation when that state exists. |
| Open Editable PowerPoint exact canonical path | HUMAN_REQUIRED | Probe command validates same-stem QMD/assets/PPTX document identity, resolves under the M3 document lock, refuses a pending transaction without recovery, maps the canonical path to the host, and passes it unchanged to `openExternal`. Unit fixtures distinguish canonical PPTX from preview paths; desktop PowerPoint target behavior remains unverified. |
| Required internal status labels representable | PASS (unit probe) | Probe enum contains Rendering Preview, Preview Ready, Importing, Applying QMD, Pending, Conflict, and Error. |

## T-402B Editor-mediated QMD Apply

| Gate | Result | Evidence / limitation |
| --- | --- | --- |
| Exact QMD state detection | PASS (helper-level probe) | `exactQmdState()` compares URI scheme, authority, and exact path when passed a VS Code URI; fixtures detect closed/open-clean/open-dirty, including dirty duplicate tabs. It is not wired into an extension command or watcher, so operational extension detection and real VS Code tab/split behavior are HUMAN_REQUIRED. String-path input is limited to local filesystem path matching. |
| Candidate generation without canonical mutation | PASS (fixture) | `create_import_candidate()` captures all `reconstruct()` staged writes in memory; QMD, assets, and PPTX fixture bytes remain unchanged. |
| Open-clean editor apply helper | PASS (mock only) | Probe helper compares URI scheme, authority, and exact path; it uses `TextEditor.edit` with a clean buffer, document version, and saved-content hash checks inside its synchronous edit callback. Real Extension Host behavior is UNVERIFIED, and the helper is not wired into an import command. |
| VS Code API save | PASS (mock only) | Helper calls `TextDocument.save()`, then reads `workspace.fs.readFile()` and compares exact disk bytes to UTF-8 candidate bytes. Tests cover equality and a newline-byte mismatch. Actual undo/redo, encoding, cursor, and false-dirty behavior are HUMAN_REQUIRED. |
| Document-version race protection | PASS (API fixture only) | A user edit is injected immediately before the `TextEditor.edit` callback; the callback detects changed dirty/version/hash state and refuses the candidate. Real Extension Host scheduling semantics remain UNVERIFIED. |
| Dirty QMD preservation | PASS (unit probe) | Dirty buffer returns `conflict-dirty`; no apply/save is attempted. |
| Front matter byte preservation | PASS (M3 reuse) | Candidate generation reuses M3 `split_front_matter` reconstruction, which retains front matter bytes. Workspace encoding/EOL roundtrip remains HUMAN_REQUIRED. |
| M3 multi-file transaction coherence | FAIL | Real M3 `FileTransaction` fixtures stage candidate assets, PPTX metadata, and imported image bytes. Injected commit failure after editor QMD save rolls Core outputs back but leaves QMD changed; a successful Core transaction followed by rejected editor apply leaves QMD old and sidecars new; metadata-operation failure rolls back Core outputs but not the editor save. A checkpoint sentinel remains old in a separate split-state fixture; this is not an injected checkpoint update failure because no checkpoint writer exists on this branch. Assertions compare actual canonical file bytes. |
| Pending fallback decision | PASS (unit policy probe) | Closed QMD -> M3 import; open-clean -> PENDING; open-dirty -> CONFLICT. |
| Selected production path | **PENDING_UNTIL_QMD_CLOSED** | QMD open (clean or dirty) stays pending/conflict-managed until closed; then import through existing M3 transaction. No cross-host transaction or v1 broker is introduced. |

## Regression and remaining gates

Automated commands to run after probe implementation:

```text
npm test
python3 -m unittest discover -s tests
npm test --prefix vscode-extension
bash scripts/smoke-test.sh
```

Automated results in this execution environment:

- `python -m unittest discover -s tests` — PASS, 70 tests (using a workspace-local TEMP/TMP directory because the Windows sandbox redirects AppData temp operations and denies atomic replacement there).
- `python -m unittest discover -s tests -p test_m4_probe.py` — PASS, 10 T-402 probe tests.
- `npm test --prefix vscode-extension` — PASS, 28 tests.
- `npm test` — PASS, 70 tests. A temporary workspace-local `python3` shim routed the script to the installed Python runtime.
- `bash scripts/smoke-test.sh` — UNVERIFIED; both Windows Bash and Git Bash could not start because the sandbox denied creation of an MSYS named object (`E_ACCESSDENIED` / `0xC0000022`).
- Dev Container preview render and actual desktop PowerPoint / VS Code Extension Host checks — HUMAN_REQUIRED.

The fixture tests do not substitute for a Dev Container render. Actual PowerPoint open/close/dirty behavior, Japanese and space-containing host paths, canonical PPTX open-dirty preservation, and real VS Code undo/EOL/encoding behavior remain **HUMAN_REQUIRED**.

**Production M4 v2 implementation may begin: NO.** T-402A remains UNVERIFIED until actual Windows + Dev Container + PowerPoint checks pass. T-402B's production path is the tested/designated Pending-until-QMD-closed fallback.

## Rejected v1 mechanisms

This probe does not introduce pair-wide destination freeze, mutation brokers, `freezeSessionId`, UNKNOWN late-operation fencing, or `TransactionSuspended` cross-host coordination.
