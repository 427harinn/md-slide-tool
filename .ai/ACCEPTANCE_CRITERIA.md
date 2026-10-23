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


## M2: Stable IDs and Element Layout

All AC-M2 gates have passed. AC-M2-04 includes the completed PowerPoint desktop save check recorded below.

- **AC-M2-01:** Missing stable IDs are generated only where needed, written back safely to QMD, and existing valid IDs remain unchanged.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m2_stable_ids_assets.py` verifies only missing IDs are added, existing IDs remain stable, and non-ID QMD content is preserved; atomic write helper is used.
- **AC-M2-02:** Duplicate `slide-id` or `element-id` causes a deterministic failure and is not silently repaired.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: Duplicate slide/element fixtures fail before source write and leave QMD unchanged.
- **AC-M2-03:** The element identity model is `element-id`; M2 implements image elements without creating a separate incompatible image-only identity system.
  - Verification: AUTOMATED + Architecture review
  - Status: PASS
  - Evidence: `elementId` / `type=image` model, source scan, and independent Architecture review.
- **AC-M2-04:** Generated PPTX carries the same slide/element stable IDs in metadata that survives the supported save/reopen path.
  - Verification: AUTOMATED where possible; HUMAN_REQUIRED only if actual PowerPoint save behavior cannot be reproduced reliably by the agent environment.
  - Status: PASS
  - Evidence: python-pptx 0.6.23 save/reopen tests pass. User confirmed Microsoft PowerPoint desktop overwrite-save, close, and reopen retained `slide.name` and picture `shape.name` IDs on the identified image slides; see H-M2-01 in `.ai/HUMAN_GATES.md`.
- **AC-M2-05:** First render with no saved layout uses the current placement engine and persists the resulting image rectangle to `<stem>.assets.json`.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: First postprocess creates schema v1 assets with integer auto-placement rectangle; CI integration fixture also exercises first render.
- **AC-M2-06:** Later render with valid saved layout applies the stored EMU rectangle before considering automatic placement.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: Second-run unit fixture verifies exact rectangle restoration, including engine-generated off-slide placement; CI integration asserts unchanged EMU rectangle.
- **AC-M2-07:** Changing the slide title while retaining `slide-id` does not break image association/layout.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: Stable slide ID matches the slide after title rename; covered by unit and CI integration fixtures.
- **AC-M2-08:** Changing the image source path while retaining `element-id` preserves the element's saved layout.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: Same element ID with changed source path restores the previous rectangle; covered by unit and CI integration fixtures.
- **AC-M2-09:** Invalid layout falls back for that element with a warning; stale entries are removed only after a successful render.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: Invalid values warn and fall back per element; sibling layouts remain intact; stale entries are pruned after successful postprocess only.
- **AC-M2-10:** `assets.json` stores schema/version, slide size and image-element layout only; title/body text is not duplicated as canonical persistent state.
  - Verification: AUTOMATED + Architecture review
  - Status: PASS
  - Evidence: Assets assertions check schema v1, slide size, integer geometry, and absence of title/caption; independent Architecture review passed.
- **AC-M2-11:** Existing image placement behavior, representative PPTX render, and docx generation remain functional.
  - Verification: AUTOMATED regression
  - Status: PASS
  - Evidence: PR #17 head CI run #62 passed root tests, existing smoke, Docker image build, representative two-pass Quarto/PPTX render with title/path/layout preservation, and DOCX render.
- **AC-M2-12:** M2 does not implement PPTX -> QMD import, watchers, sync, conflict handling, shape persistence, crop/rotation/z-order, Marketplace publication, or PPTX -> Word.
  - Verification: scope scan + independent Review/Architecture
  - Status: PASS
  - Evidence: Scope scan and independent Review/Architecture confirmed no M3+ production implementation.


## M3: PPTX -> QMD Import

M3 acceptance criteria are verified against the retained implementation and regression evidence below.

- **AC-M3-01:** `slidegen import <pptx>` accepts only an M3-managed presentation with valid managed marker/version/document-id, an existing same-stem QMD, and assets schema v2 carrying the same `documentId`; body hash alone is never sufficient to pair files. Unmarked legacy/arbitrary PPTX or document-id mismatch is rejected and must be re-rendered/repaired first.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` covers pairing, unmarked input and document mismatch rejection.
- **AC-M3-02:** Existing QMD YAML front matter remains byte-preserved while normal-slide content is rebuilt from the PPTX.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` front-matter byte-preservation fixture.
- **AC-M3-03:** Existing valid `slide-id` values identify managed normal slides; title edits, reorder, and deletion are reflected without changing surviving IDs. Malformed or duplicate IDs cause FAIL.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` stable ID, title edit, reorder/delete, malformed and duplicate ID fixtures.
- **AC-M3-04:** A newly added supported normal PowerPoint slide receives a new `slide-id` written to both rebuilt QMD and staged PPTX, while ambiguous ID-less title-layout slides cause FAIL instead of heuristic classification.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` new slide ID writeback and ambiguous title-layout fixtures.
- **AC-M3-05:** Supported text content (title, ordinary paragraphs, bullets, numbered lists) is reconstructed as normalized Markdown without claiming byte-for-byte source recovery.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` title, paragraph, bullet and numbered-list reconstruction fixtures.
- **AC-M3-06:** Existing image elements preserve `element-id`; move/resize changes update exact EMU geometry in assets; malformed or duplicate element IDs cause FAIL.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` geometry and element-ID validation fixtures. H-M3-01 additionally confirmed PowerPoint desktop move/resize changes import into QMD/assets and survive re-render.
- **AC-M3-07:** Assets schema v2 represents image crop with integer OOXML percentage values, reads schema v1 as no-crop, migrates safely to v2, rejects invalid crop, and re-applies crop on the next render without destructively modifying source images.
  - Verification: AUTOMATED + representative PowerPoint-compatible roundtrip + HUMAN_REQUIRED desktop PowerPoint save/reopen roundtrip (completed by H-M3-01).
  - Status: PASS
  - Evidence: `tests/test_m3_core.py`, `tests/test_m3_import.py`, and `tests/m3-pptx-qmd-roundtrip.sh` cover v1/v2, crop validation and reapplication. H-M3-01 confirms desktop crop import and visual preservation after re-render.
- **AC-M3-08:** Replacing image contents while preserving the identified picture shape keeps the same `element-id`; a newly inserted picture shape receives a new ID rather than being guessed as a replacement.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` verifies identified-picture replacement preserves identity and new shapes receive new IDs.
- **AC-M3-09:** New/changed picture bytes are extracted safely under `img/imported/<element-id>.<ext>` when required without overwriting a shared source image used by another element.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` verifies safe extraction and shared-source protection.
- **AC-M3-10:** Deleting a supported image removes its QMD/assets representation only after full import validation succeeds.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` deletion fixtures validate before staging changes.
- **AC-M3-11:** Template/user content classification is structural and fixture-backed: inherited master/layout content is ignored, supported placeholders/pictures and md-slide-tool caption companion textboxes are recognized deterministically, caption text roundtrips to the image caption, and unknown slide-local content that could be lost causes pre-commit FAIL.
  - Verification: AUTOMATED + Review/Architecture
  - Status: PASS
  - Evidence: `tests/test_m3_feasibility_fixture.py`, `tests/test_m3_import.py`, and independent Review/Architecture gates. H-M3-01 confirms a desktop-edited caption imports into QMD/assets and survives re-render.
- **AC-M3-12:** Import provides recoverable multi-file transactional consistency across QMD, assets, extracted images, and PPTX metadata writeback. Before a document-id exists, concurrent first M3 renders/imports serialize on a deterministic bootstrap lock derived from the canonical paired-QMD path. The process that performs or observes migration must acquire the corresponding document-id lock while still holding bootstrap, then release bootstrap; no unlocked handoff gap is permitted. Transaction state distinguishes prepared/committing/committed/rolling_back/rolled_back; create/replace/delete rollback is defined; handled commit failures roll back; simulated abrupt termination is recovered phase-specifically on the next render/import via journal and hash-checked backups.
  - Verification: AUTOMATED failure injection + crash-recovery simulation
  - Status: PASS
  - Evidence: `tests/test_m3_transaction.py` covers locking, concurrency, rollback, crash recovery and unknown-hash stop behavior.
- **AC-M3-13:** No persistent intermediate JSON becomes a second canonical store for title/body text; transaction metadata contains only recovery/identity/state information.
  - Verification: Architecture review + source scan
  - Status: PASS
  - Evidence: Architecture review and source/scope scan confirm QMD remains canonical for text; persistent assets contain layout state only.
- **AC-M3-14:** Existing QMD -> PPTX render, M2 stable assets behavior, M1 open workflow, and docx generation remain functional.
  - Verification: AUTOMATED regression
  - Status: PASS
  - Evidence: `tests/m2-render-regression.sh`, `tests/m3-pptx-qmd-roundtrip.sh`, DOCX render, and earlier successful smoke test.
- **AC-M3-15:** M3 does not implement watchers, automatic sync, full dirty-state conflict merge, arbitrary shape support, rotation/z-order, Marketplace publication, or PPTX -> Word.
  - Verification: scope scan + independent Review/Architecture
  - Status: PASS
  - Evidence: independent Review and Architecture scope checks found no watcher, sync, conflict-merge, arbitrary-shape, publication or Word-import work.
- **AC-M3-16:** M3-capable render writes a valid presentation-level managed marker, format version, document-id, reserved title role/caption companion metadata, and QMD normal-body SHA-256 baseline that survive the supported PPTX save/reopen path; the same document-id is persisted in assets schema v2. The first schema-v1 -> v2 migration generates exactly one document-id even under concurrent render attempts.
  - Verification: AUTOMATED + HUMAN_REQUIRED desktop PowerPoint save/close/reopen/import roundtrip (completed by H-M3-01).
  - Status: PASS
  - Evidence: `tests/test_m3_feasibility_fixture.py`, M3 import/transaction tests and real CLI roundtrip cover properties, IDs, title/caption markers and baseline. H-M3-01 confirms the desktop-edited presentation remains importable after save/close and that its caption/crop metadata is applied on re-render.
- **AC-M3-17:** The QMD normal-body hash uses the documented canonical-byte algorithm (UTF-8 BOM handling, front-matter delimiter boundary, CRLF/CR -> LF only, no Unicode/whitespace normalization). If the current canonical body differs from the hash embedded at render time, import fails before staging/commit with an explicit changed-since-render error; M3 provides no force-merge override.
  - Verification: AUTOMATED
  - Status: PASS
  - Evidence: `tests/test_m3_core.py` canonical-byte fixtures and `tests/test_m3_import.py` changed-since-render pre-stage rejection.
- **AC-M3-18:** The front-matter-generated title slide carries a reserved internal title-role marker independent of slide position. Moving/deleting it remains safe; duplicate marker or ambiguous marker loss causes FAIL. Fixtures cover new slides before/after the title slide.
  - Verification: AUTOMATED + Architecture review
  - Status: PASS
  - Evidence: `tests/test_m3_import.py` covers moved/deleted/duplicate/lost title markers and ambiguous classification; Architecture review passed.

- **AC-M3-19:** Before production M3 implementation, the current repository PPTX template/render output has a retained structural fixture proving explicit classification of supported placeholders, pictures and marked captions; unknown slide-local shapes remain rejectable without position/color/appearance heuristics. Fixture probes cover title/body/list XML, image bytes/format, raw crop reapplication, master/layout inheritance, custom properties, title/caption marker and stable-ID coexistence through python-pptx/Open XML save/reopen.
  - Verification: AUTOMATED + Test/Architecture review
  - Status: PASS
  - Evidence: `tests/fixtures/m3/structure.pptx`, `tests/fixtures/m3/selfintroduction/structure.pptx`, `tests/fixtures/m3/structure-report.json`, and `python tests/test_m3_feasibility_fixture.py`; real Dev Container renders completed from both repository template sources. This verifies package-level save/reopen, not a new Microsoft PowerPoint desktop save cycle.

## M4: Docker Sync Engine

M4 turns the M3 manual roundtrip into safe save-driven synchronization. AC IDs already introduced during design review remain stable; superseded lease-model criteria are retained as DEFERRED history rather than reused.

- **AC-M4-01:** A save of an eligible managed QMD triggers exactly one effective M3-capable render after debounce, without requiring the manual Build command.
  - Verification: AUTOMATED + HUMAN_REQUIRED Windows E2E
  - Status: UNVERIFIED
- **AC-M4-02:** A save of the paired managed PPTX triggers exactly one effective M3 import after debounce, without requiring manual `slidegen import`.
  - Verification: AUTOMATED + HUMAN_REQUIRED Windows E2E
  - Status: UNVERIFIED
- **AC-M4-03:** Rapid duplicate filesystem events for one logical save are coalesced; correctness does not depend on a magic delay alone.
  - Verification: AUTOMATED
  - Status: UNVERIFIED
- **AC-M4-04:** At most one render/import runs per managed document. Saves arriving while an operation is active become one coalesced pending intent and the newest state is re-evaluated after completion.
  - Verification: AUTOMATED concurrency tests
  - Status: UNVERIFIED
- **AC-M4-05:** Writes committed by md-slide-tool render/import are deterministically recognized by expected hashes/fingerprints and do not trigger an opposite-direction loop. A mismatching write is not silently suppressed.
  - Verification: AUTOMATED
  - Status: UNVERIFIED
- **AC-M4-06:** Sync state persists/retains only minimal fingerprints/identity needed for synchronization and does not create a second canonical title/body text store.
  - Verification: Architecture review + source scan
  - Status: UNVERIFIED
- **AC-M4-07:** Before QMD -> PPTX auto-render, the system can determine whether the paired presentation is closed, open-saved, or open-dirty in desktop PowerPoint. Open-dirty causes conflict instead of automatic overwrite.
  - Verification: T-401 feasibility + HUMAN_REQUIRED Windows E2E
  - Status: UNVERIFIED
- **AC-M4-08:** Before PPTX -> QMD auto-import, VS Code's actual paired QMD editor dirty state is checked. Unsaved editor text causes conflict instead of automatic overwrite.
  - Verification: AUTOMATED extension tests + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-09:** Saved independent changes on both sides since the last successful synchronization are detected as conflict; M4 never silently selects QMD or PowerPoint as winner.
  - Verification: AUTOMATED
  - Status: UNVERIFIED
- **AC-M4-10:** Conflict notification uses non-destructive actions equivalent to **Cancel** and **Compare**. Cancel leaves both current states untouched.
  - Verification: AUTOMATED UI/state tests + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-11:** Compare can snapshot the latest unsaved PowerPoint state without force-saving the original presentation, using SaveCopyAs or equivalent, and the original dirty/saved state remains unchanged.
  - Verification: T-401 + HUMAN_REQUIRED Windows PowerPoint
  - Status: UNVERIFIED
- **AC-M4-12:** Compare can snapshot the latest unsaved QMD editor text without forcing a save to the real QMD file.
  - Verification: AUTOMATED extension tests
  - Status: UNVERIFIED
- **AC-M4-13:** Comparison snapshot/reconstruction is non-committing and cannot overwrite canonical QMD/PPTX/assets. Temporary artifacts are identifiable and safely cleanable.
  - Verification: AUTOMATED failure/recovery tests + Architecture review
  - Status: UNVERIFIED
- **AC-M4-14:** VS Code exposes useful per-document state (Synced/Building/Importing/Pending/Conflict/Error/Paused or equivalent), auto-starts synchronization for eligible pairs, and provides pause/resume.
  - Verification: AUTOMATED extension tests + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-15:** Operation failures do not enter infinite retry loops. A later save/retry can re-evaluate safely, while M3 transaction/recovery guarantees remain intact.
  - Verification: AUTOMATED failure injection
  - Status: UNVERIFIED
- **AC-M4-16:** Diagnostics distinguish render/import failure, remote/Dev Container disconnect, host bridge failure, and PowerPoint status/launch failure instead of reporting all as "build failed".
  - Verification: AUTOMATED + targeted E2E
  - Status: UNVERIFIED
- **AC-M4-17:** PowerPoint targeting remains correct with multiple presentations open; a similarly named or unrelated presentation is never used as the dirty-state/snapshot source.
  - Verification: T-401 + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-18:** M4 does not implement automatic semantic merge, final M5 winner-selection UI, keystroke-level live sync, incremental rendering, arbitrary-shape expansion, Marketplace publication, or PPTX -> Word.
  - Verification: scope scan + Review/Architecture
  - Status: UNVERIFIED
- **AC-M4-19:** Existing M1 build/open, M2 stable layout, M3 manual render/import and transaction recovery, and docx generation continue to pass regression tests.
  - Verification: AUTOMATED regression + CI
  - Status: UNVERIFIED
- **AC-M4-20:** Dirty-state/fingerprint validation is performed both before candidate work and immediately before canonical commit. If QMD or PowerPoint changes between those checks, the candidate is not published and the document is re-evaluated into PENDING/CONFLICT.
  - Verification: AUTOMATED race injection + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-21:** QMD and PPTX events arriving in the same debounce window are resolved by one pair-level state evaluation, never by event arrival order.
  - Verification: AUTOMATED
  - Status: UNVERIFIED
- **AC-M4-22:** The durable sync checkpoint includes a full-QMD fingerprint that detects front-matter-only edits and is committed/recovered in the same recoverable transaction boundary as the synchronized render/import outputs.
  - Verification: AUTOMATED crash recovery + Architecture review
  - Status: UNVERIFIED
- **AC-M4-23:** A crash cannot leave canonical outputs committed with a silently stale last-synchronized checkpoint that later authorizes overwrite. Restart/recovery either completes the matching checkpoint or stops for safe re-evaluation/manual recovery.
  - Verification: AUTOMATED crash injection
  - Status: UNVERIFIED
- **AC-M4-24:** The Workspace/Core -> Windows Local UI request/response path for PowerPoint state and comparison snapshot is explicitly correlated and fails closed on timeout, disconnect, restart, PowerPoint exit, malformed response, or stale response.
  - Verification: T-401 cross-host feasibility + AUTOMATED bridge tests + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-25:** Manual render/import and automatic sync never bypass the M3 document lock. Automatic DOCUMENT_BUSY becomes a bounded pending re-evaluation rather than spin retry or destructive failure.
  - Verification: AUTOMATED concurrency tests
  - Status: UNVERIFIED

### Superseded publication-lease criteria

AC-M4-26 through AC-M4-34 were introduced while exploring a layered publication-lease/filesystem-lease model. That model was intentionally replaced by the simpler destination-freeze design. These IDs are retained only as design history and are not M4 completion gates.

- **AC-M4-26 — DEFERRED (superseded):** commit-barrier publication lease.
- **AC-M4-27 — DEFERRED (superseded):** QMD version-bound publication lease.
- **AC-M4-28 — DEFERRED (superseded):** PowerPoint exclusive publish lease.
- **AC-M4-29 — DEFERRED (superseded):** COMMITTING event handling under publication barrier.
- **AC-M4-30 — DEFERRED (superseded):** prior publication-barrier variant of DOCUMENT_BUSY handling.
- **AC-M4-31 — DEFERRED (superseded):** Core/Workspace QMD lease RPC.
- **AC-M4-32 — DEFERRED (superseded):** Windows-visible filesystem lease for every target.
- **AC-M4-33 — DEFERRED (superseded):** filesystem-lease expected-absence/CAS requirement.
- **AC-M4-34 — DEFERRED (superseded):** Windows-wide writer exclusion requirement.

### Destination-freeze criteria

- **AC-M4-35:** An open-saved paired PowerPoint presentation is temporarily closed without saving before QMD -> PPTX publication and the exact updated presentation is reopened after commit; an open-dirty presentation is never automatically closed.
  - Verification: T-401 + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-36:** A clean paired QMD editor can be temporarily frozen/closed for PPTX -> QMD publication and restored/reopened afterward without content loss or false dirty state; a dirty QMD is never automatically closed.
  - Verification: T-401 + AUTOMATED extension tests + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-37:** If M3 import still writes PPTX metadata, PPTX -> QMD synchronization does not keep the same PPTX actively editable in PowerPoint during that writeback. It either closes/reopens the clean presentation or uses a separately verified no-writeback design.
  - Verification: T-401 + AUTOMATED regression + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-38:** M4's formal concurrency guarantee covers VS Code for QMD and Microsoft PowerPoint desktop for PPTX. Arbitrary external writers during the short destination-freeze/commit interval are explicitly outside the M4 guarantee; M4 still performs final saved-state validation and M3 recoverable transaction handling.
  - Verification: Architecture review + documentation scan
  - Status: UNVERIFIED
- **AC-M4-39:** If destination close/freeze succeeds but publication or restore/reopen later fails, canonical file consistency follows M3 transaction/recovery and the UI/host failure is reported separately without pretending the opposite side is synchronized.
  - Verification: AUTOMATED failure injection + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-40:** T-401 proves the simplified destination-freeze operations and cross-host close/reopen/state requests using supported APIs before production implementation begins.
  - Verification: T-401 feasibility
  - Status: UNVERIFIED

- **AC-M4-41:** The VS Code Workspace extension is the automatic M4 orchestrator. It establishes a correlated pair freeze before starting any Core command that may run M3 recovery or publish files.
  - Verification: AUTOMATED extension/integration tests + Architecture review
  - Status: UNVERIFIED
- **AC-M4-42:** Reopening/editing before Core owns `committing` invalidates the freeze and yields zero destructive writes. After commit ownership, reopen is handled by the owning per-target mutation broker; it does not reuse the pre-ownership invalidation rule, and user work is preserved for post-transaction re-evaluation.
  - Verification: T-401 + AUTOMATED freeze-invalidation/broker tests + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-43:** Automatic M3 transaction recovery runs only after the paired VS Code/PowerPoint views are frozen. Before recovery commit ownership, invalidation yields zero destructive writes; after ownership, QMD/PPTX recovery mutations use the same broker/suspend rules as normal commit operations.
  - Verification: AUTOMATED crash/recovery integration + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-44:** Workspace -> Local UI freeze/restore/state requests and Local UI -> Workspace reopen-invalidation events are correlated by freezeSessionId; timeout/disconnect/restart cannot be interpreted as a valid freeze.
  - Verification: T-401 + AUTOMATED cross-host tests
  - Status: UNVERIFIED

- **AC-M4-45:** Workspace and Core coordinate freeze validity through one atomic shared guard keyed by documentId/freezeSessionId. Core must atomically claim `frozen -> committing` immediately before the first destructive transaction/recovery mutation.
  - Verification: AUTOMATED guard/race tests + Architecture review
  - Status: UNVERIFIED
- **AC-M4-46:** Reopen/edit before Core claims `committing` invalidates the guard and results in zero destructive writes. Reopen/edit after `committing` does not trigger ad-hoc rollback; supported-app reopen is rejected/re-closed, `pendingReopen` is recorded, and the transaction reaches a stable committed/rolled-back/manual-recovery state before re-evaluation.
  - Verification: T-401 + AUTOMATED first-write race tests + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-47:** A crash during `committing` leaves the M3 journal authoritative. A stale guard never authorizes recovery; a brand-new pair freeze/session is required before recovery can perform destructive writes.
  - Verification: AUTOMATED crash/recovery tests + Architecture review
  - Status: UNVERIFIED
- **AC-M4-48:** Checkpoint state after partial commit plus reopen/invalidation follows the M3 transaction outcome: committed output has the new checkpoint, rolled-back output has the old checkpoint, and ManualRecoveryRequired never fabricates a synchronized checkpoint.
  - Verification: AUTOMATED failure injection
  - Status: UNVERIFIED

- **AC-M4-49:** The `frozen -> invalidated` and `frozen -> committing` race is serialized by competing atomic rename of the same runtime state token. There is no stale read followed by unconditional state overwrite; exactly one transition wins.
  - Verification: AUTOMATED high-iteration race test + Architecture review
  - Status: UNVERIFIED
- **AC-M4-50:** Post-ownership reopen notification uses an append-only/create-if-absent `pending-reopen` marker and cannot overwrite the primary committing state.
  - Verification: AUTOMATED concurrency tests
  - Status: UNVERIFIED
- **AC-M4-51:** Every automatic Core process has a freezeSessionId-bound Workspace control channel. Core checks it before each destructive transaction/recovery mutation. Workspace/Local UI loss after commit ownership prevents the next mutation.
  - Verification: AUTOMATED IPC/failure-injection + T-401
  - Status: UNVERIFIED
- **AC-M4-52:** Control loss after one or more transaction operations causes a typed TransactionSuspended path that leaves the journal in `committing` and does not run the normal immediate rollback path. A new pair freeze/session is required before recovery resumes.
  - Verification: AUTOMATED partial-commit/crash tests + Architecture review
  - Status: UNVERIFIED
- **AC-M4-53:** A suspended transaction does not advance the durable sync checkpoint unless the transaction had already reached `committed`; recovery under a later valid freeze determines the final checkpoint/file state.
  - Verification: AUTOMATED checkpoint/recovery tests
  - Status: UNVERIFIED

- **AC-M4-54:** After commit ownership, a supported-app reopen is handled by the owning per-target mutation broker. For QMD/PPTX, freeze validation/re-establishment and the actual file mutation occur in one broker critical section; timeout/failure/unknown outcome causes TransactionSuspended instead of a later Core replace.
  - Verification: AUTOMATED IPC/broker race tests + T-401 + HUMAN_REQUIRED
  - Status: UNVERIFIED
- **AC-M4-55:** TransactionSuspended bypasses FileTransaction.commit()'s generic immediate-rollback path. Suspension during commit preserves a `committing` journal; suspension during rollback recovery may preserve `rolling_back`; both require later recovery under a new valid pair freeze.
  - Verification: AUTOMATED transaction failure injection + Architecture/Review
  - Status: UNVERIFIED
- **AC-M4-56:** A suspension after the final target replacement but before the journal is durably marked `committed` remains an incomplete transaction and is resolved by journal recovery, not inferred as successful from target hashes alone.
  - Verification: AUTOMATED crash/suspend fixture
  - Status: UNVERIFIED
- **AC-M4-57:** On startup, pending transaction journal detection/recovery precedes any use of the sync checkpoint to decide render/import/conflict. After recovery stabilizes, checkpoint and current fingerprints are re-read before pair evaluation.
  - Verification: AUTOMATED restart/recovery tests
  - Status: UNVERIFIED

- **AC-M4-58:** Automatic M4 does not use a pre-mutation re-freeze ACK followed by a later Core QMD/PPTX replace. The component that owns the supported-app freeze performs the actual QMD/PPTX create/replace/delete in the same broker critical section and returns only a post-mutation result.
  - Verification: T-401 + AUTOMATED broker/race tests + Architecture/Review
  - Status: UNVERIFIED
- **AC-M4-59:** A reopen injected after broker freeze validation but before the actual QMD/PPTX file operation cannot be silently overwritten: the broker must keep/re-establish the supported-app freeze through mutation or return NOT_MUTATED/UNKNOWN so Core suspends and recovery resolves the journal.
  - Verification: T-401 race probe + AUTOMATED broker failure injection
  - Status: UNVERIFIED
- **AC-M4-60:** QMD mutation is brokered by Workspace, PPTX mutation by Windows Local UI, while Core remains journal/transaction authority. Broker requests are correlated by documentId/freezeSessionId/transaction/op index and verify expected old hash/absence and final outcome.
  - Verification: AUTOMATED integration + T-401
  - Status: UNVERIFIED

