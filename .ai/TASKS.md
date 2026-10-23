# TASKS

## M4: Docker Sync Engine

Codexは `.ai/AGENT_WORKFLOW.md` に従い、実装前に `docs/M4_SYNC_ENGINE.md`、Acceptance Criteria、Test Planを確認する。

### T-401: Windows PowerPoint dirty-state / snapshot feasibility

production implementation前の必須gate。

- paired presentationをPowerPointで正しく特定できること
- closed / open-saved / open-dirtyを区別できること
- unsaved stateを読むこと自体がpresentation stateを変えないこと
- SaveCopyAs相当でcurrent in-memory stateの一時copyを作れること
- comparison copy作成後もoriginalのdirty/saved stateが変わらないこと
- multiple presentations open時にwrong documentを選ばないこと
- PowerPoint/COM unavailable時にsafe FAILすること
- Workspace/Core -> Windows Local UI のdirty-state request/responseが成立すること
- comparison snapshot request/responseがrequest IDで正しくcorrelateされること
- timeout / Remote切断 / Local UI再起動 / PowerPoint終了中のrequestがfail closedすること
- admission時とpre-commit時の2回問い合わせで変更token差分を検出できること
- pre-commit後〜publication完了までを守るexclusive presentation publish lease / commit barrierを取得・解放できること
- barrier中のedit/saveが未観測のままoverwriteされないこと
- barrier acquire/releaseのtimeout / disconnect / host crashがfail closedすること
- file lock/timestamp heuristicだけでdirty判定しないこと

成立しない場合はPowerPoint Add-in等を勝手に実装せず、設計をReviewへ戻す。

### T-402: Sync state model / fingerprints

- per-document IDLE/DEBOUNCING/RENDERING/IMPORTING/PENDING/CONFLICT/ERROR/PAUSED state
- minimal last-synchronized fingerprints
- no second canonical title/body JSON
- managed documentIdとのpairing
- restart/resume時のre-evaluation
- full QMD file hash（front matter込み）を持ち、M3 body hashだけに依存しない
- sync checkpointをrender/import outputsと同じrecoverable transaction commit境界に含める
- transaction commit後/checkpoint更新前というcrash gapを作らない
- corrupt/stale checkpointはsilent overwriteせずre-evaluate/conflict/manual recovery

### T-403: Watcher / debounce

- managed QMD/PPTX pairのみprimary trigger
- rapid duplicate event coalescing
- atomic rename/temp-save patterns
- 同一debounce windowにQMD/PPTX両eventが来たらpair全体を1回再評価し、arrival orderで方向を決めない
- configurable initial debounce around 500-1000ms
- assets/self-generated image writesをuser trigger化しない

### T-404: Running / pending serialization

- one active operation per managed document
- active operation中のsaveはcoalesced pending
- queueをevent数だけ積まない
- operation完了後にlatest stateを再評価
- admission validationとpre-commit validationの二段階確認
- pre-commit成功後にCOMMIT_BARRIERを取得し、canonical publication完了まで保持
- COMMITTING中のsave/change eventは1件PENDINGとして記録し、barrier release後に必ず再評価
- protected sideのdocument version / dirty token / saved fingerprintが途中で変わったらpublishしない
- M3 document lock/transactionとの整合
- QMD側はTextDocument versionに結びついたeditor publish leaseまたはversion-conditional publicationを必須とし、単純なversion check + unconditional replaceは禁止
- PowerPoint側はvalidated tokenに結びついたexclusive presentation publish leaseまたは同等のatomic host publicationを必須
- manual render/importと競合してDOCUMENT_BUSYなら1件pendingとしてbounded re-evaluationし、spin retryしない
- DOCUMENT_BUSY後に監視対象fileが変わらなくても、約250msから最大約2sのbounded backoff（総待機約10s）でlock解放を再確認

### T-405: Self-generated write suppression

- render/import expected output hash/fingerprintでself-write判定
- fixed time ignore onlyを禁止
- generated outputと一致しないeventはexternal changeとして再評価
- infinite render/import loop防止fixture

### T-406: Automatic QMD -> PPTX sync

- QMD save検知
- QMD editor dirty-state確認
- host PowerPoint dirty-state確認
- safeならM3-capable render
- self writes抑制
- synchronized fingerprint更新
- candidate生成後、commit直前にPowerPoint/QMD stateを再検証し、途中編集ならpublishせずCONFLICT/PENDING

### T-407: Automatic PPTX -> QMD sync

- PPTX save検知
- package stable/readable待ち
- VS Code QMD dirty-state確認
- safeならM3 import
- self writes抑制
- synchronized fingerprint更新
- candidate生成後、commit直前にPowerPoint/QMD stateを再検証し、途中編集ならpublishせずCONFLICT/PENDING

### T-408: Conflict detection / snapshots

- opposite side unsaved or independently changedならCONFLICT
- destructive automatic syncを停止
- VS Code promptはCancel / Compare
- unsaved PowerPointはSaveCopyAs相当でtemporary PPTX snapshot
- unsaved QMDはeditor in-memory textからtemporary QMD snapshot
- comparison reconstructionはnon-committing
- snapshot cleanup/recovery
- M5へcomparison entrypoint/dataを渡す
- M4ではwinner selection/mergeを実装しない

### T-409: VS Code status / controls / diagnostics

- status bar: Synced / Building / Importing / Pending / Conflict / Error / Paused
- workspace activate時にauto start
- pause/resume
- concise error + logs
- build/import failure、remote disconnect、host bridge failure、PowerPoint failureを区別

### T-410: Tests / regression

最低限:
- QMD save -> exactly one render
- PPTX save -> exactly one import
- duplicate events debounce
- render self-write does not trigger import
- import self-write does not trigger render
- running + repeated saves -> one pending re-evaluation
- simultaneous/independent change -> CONFLICT
- QMD/PPTX eventsが同じdebounce windowに到着 -> pair-level re-evaluation
- dirty-state admission後〜commit直前にQMD編集 -> no publish + CONFLICT/PENDING
- dirty-state admission後〜commit直前にPowerPoint編集 -> no publish + CONFLICT/PENDING
- final token check後〜first canonical replace前にQMD編集を注入 -> barrier/conditional publishが失敗しuser change保持
- final token check後〜first canonical replace前にPowerPoint編集を注入 -> barrier acquire/validation失敗しuser change保持
- multi-file COMMITTING途中にchange/save event注入 -> current commitはbarrier contractどおり完了/abortし、eventをPENDINGとしてrelease後re-evaluate
- barrier acquire/release timeout/disconnect -> fail closed
- M3 transaction commitとsync checkpointのcrash recovery
- front-matter-only changeをrestart後も検出
- manual operationによるDOCUMENT_BUSY -> bounded pending/re-evaluation
- QMD dirty / PowerPoint dirty paths
- Cancel is non-destructive
- Compare snapshots latest in-memory state
- PowerPoint SaveCopyAs original dirty state unchanged
- multi-presentation targeting
- pause/resume
- error no infinite retry
- remote disconnect diagnostic
- M1/M2/M3/docx regression
- Windows real E2E human gate after automated gates

### T-411: Final documentation / independent review

- PROJECT_CONTEXT / ROADMAP更新
- Test Agent
- Review Agent
- Architecture Agent
- M5 Semantic Diff/resolutionを先取りしていないこと
- FAILなら最小修正して再検証
