# TASKS

## M4: Save-driven Sync Engine v2

Codexは実装前に `docs/M4_SYNC_ENGINE.md`、Acceptance Criteria、Test Plan、T-401結果を確認する。

### T-402A: Versioned PowerPoint preview feasibility

production implementation前の必須gate。

- QMDからcanonical PPTXとは別pathへpreview PPTX生成
- previewにdocumentId / generation / preview marker
- Local UIがexact previewをPowerPointでopen
- previous md-slide-tool previewがopen-cleanならclose
- dirty previewはcloseしない
- unrelated presentationは触らない
- canonical PPTXがopen/dirtyでもpreview生成を許可
- Japanese/space path
- bounded cleanup
- preview save/editがcanonical import triggerにならない

FAILならproduction実装を止めて再設計。

### T-402B: VS Code editor-mediated QMD apply feasibility

- exact paired QMD open/closed/clean/dirty判定
- import candidateをcanonical QMDへ先に書かず生成
- open-clean QMDへVS Code APIでcandidate text適用
- VS Code経由でsave
- candidate作成後のdocument version change検出
- dirty bufferは上書きしない
- assets/images/PPTX metadata/checkpointとのtransaction整合を検証
- coherent transactionが成立しない場合はFAIL

FAIL時fallback:
- QMD open中はPending
- QMD closed後に既存M3 transactionでimport

### T-403: Watch / debounce / preview generation

- canonical QMD saveをtrigger
- rapid duplicate event coalescing
- versioned preview path generation
- preview eventsをcanonical triggerとして無視
- one active preview render + one pending
- cleanup best-effort

### T-404: Canonical PPTX import

- exact canonical managed PPTXだけをtrigger
- preview PPTXは除外
- package stable/readable待ち
- QMD closed -> M3 import transaction
- QMD open-clean -> T-402B PASS時のみeditor-mediated apply
- QMD open-dirty -> CONFLICT
- T-402B FAILならopen QMDはPending fallback

### T-405: Checkpoint / self-write suppression

- canonical QMD hash + canonical PPTX fingerprintのみsync checkpoint
- preview renderでcanonical checkpointを進めない
- preview fingerprintはdiagnostic only
- generated assets/images/preview eventsをloop triggerにしない
- journal recoveryをcheckpoint interpretationより先に行う

### T-406: PowerPoint UX

- latest preview表示
- prior clean preview close
- dirty preview untouched
- Open Editable PowerPoint commandでcanonical PPTXをopen
- previewとcanonicalを明確に識別
- wrong targetを触らない

### T-407: Conflict / Compare

- canonical PPTX save + dirty QMD -> CONFLICT
- canonical QMD/PPTX independent changes -> CONFLICT
- Cancel / Compare
- previewはcanonical conflict判定に含めない
- M5を先取りしない

### T-408: Status / controls

- Synced / Rendering Preview / Preview Ready / Importing / Applying QMD / Pending / Conflict / Error / Paused
- auto-start
- pause/resume

### T-409: Regression

- M1/M2/M3/docx
- root npm/python/smoke
- preview path cleanup
- no canonical PPTX overwrite while previewing
- no preview import
- no production use of v1 freeze/broker mechanisms

### T-410: Final review

- independent Test / Review / Architecture
- T-402A/B evidence
- v1 destination-freeze/mutation-broker requirements no longer active
- production implementation only after required feasibility PASS/fallback decision
