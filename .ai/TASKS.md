# TASKS

## M4: Docker Sync Engine

Codexは `.ai/AGENT_WORKFLOW.md` に従い、実装前に `docs/M4_SYNC_ENGINE.md`、Acceptance Criteria、Test Planを確認する。

### T-401: Pair-freeze feasibility and orchestration

production implementation前の必須gate。

#### PowerPoint
- freezeSessionIdを受け取り、paired presentationのfreeze/restoreを実行
- freeze中のPresentationOpen/reopenを検出してsession invalidationを返す
- reopen後にdirty化したpresentationを保存せず保護し、CONFLICTへ再評価

- exact paired presentationを特定
- closed / open-saved / open-dirtyを区別
- open-saved presentationをsaveせず安全にclose
- open-dirty presentationは自動closeしない
- commit後にexact same pathをreopen
- multiple presentations open時にwrong targetを触らない
- SaveCopyAsでunsaved comparison snapshotを作りoriginal dirty stateを保持
- PowerPoint exit / close / reopen failureがsafe FAIL
- PPTX -> QMD importでM3 metadata writebackが必要な場合、clean presentationをclose/reopenする経路を検証
- またはPPTX writeback削除案を別fixtureで安全性確認してから採用

#### VS Code QMD
- Workspace extensionをM4のsync orchestratorとする
- Core automatic command起動前にpaired QMD/PPTX両方のfreezeを完了する
- paired QMDのreopen/editをfreeze中に検出してsession invalidation
- reopen後dirty bufferを失わずCONFLICTへ再評価

- paired QMD dirty/clean判定
- open-clean QMD editorを短時間close/hide
- commit後にrestore/reopen
- dirty QMDは自動closeしない
- close/restoreでcontent lossやfalse dirtyを起こさない
- userがSyncing中に再open/editした場合の検出/後続CONFLICT挙動を確認

#### Recovery / ordering
- pending M3 transactionがある状態でも、Core起動前にpair freezeを完了
- recover_transactions()はfreeze成立後にのみautomatic M4 pathから呼ばれる
- recoveryの最初のdestructive mutation直前にexact guardを frozen -> committing へatomic transition
- frozen token rename競合でinvalidationとcommit claimを直列化
- claim前のreopen -> invalidated、destructive write 0件
- claim後のreopen + control healthy -> pending-reopen marker
- Coreは次のdestructive mutation前にsame freezeSessionId/reopen generationのre-freeze ACKを必須確認
- ACK timeout/failure/stale -> TransactionSuspended before next mutation
- claim後にWorkspace/Local UI control loss -> 次mutation前にTransactionSuspended、journal保持、no immediate rollback
- crash/suspend後は新しいpair freeze/session後にrecovery

#### Cross-host
- Workspace -> Local UI freeze/restore requestにfreezeSessionIdを付与
- Local UI -> WorkspaceのPowerPoint reopen invalidation eventを同じsessionにcorrelate

- Workspace -> Local UI state / close / reopen / SaveCopyAs request
- typed correlated response
- timeout / Remote disconnect / Local UI restart / PowerPoint exitがsafe FAIL
- Windows-wide filesystem leaseを前提にしない

成立しない場合はproduction実装を止め、設計を再検討する。

### T-402: Sync state / checkpoint
- ephemeral runtime session dir: /tmp/md-slide-tool/freeze/<workspace-key>/<document-id>/<freezeSessionId>/
- primary state token is one filename: frozen / invalidated / committing / restoring
- frozen -> invalidated and frozen -> committing are competing same-directory atomic rename operations; exactly one can succeed
- pending reopen is separate append-only/create-if-absent marker, never a competing JSON update
- automatic Core receives a dedicated Workspace control pipe tied to freezeSessionId
- Core checks control health before every destructive mutation
- control loss after committing raises TransactionSuspended and leaves journal in committing; do not run immediate rollback for this condition
- stale runtime state after crash never authorizes recovery; new pair freeze/session required
- FREEZING_PAIR / RECOVERING_IF_NEEDED / RESTORING_PAIR stateを含む
- freezeSessionId validityをper-document stateに持つ

- IDLE / DEBOUNCING / CHECKING / PREPARING / FREEZING_DESTINATION / COMMITTING / RESTORING_DESTINATION / PENDING / CONFLICT / ERROR / PAUSED
- per-document state
- full QMD file hash（front matter込み）
- PPTX fingerprint
- documentId pairing
- no second canonical text store
- checkpointをM3 transactionと同じcommit/recovery boundaryに含める
- restart/resume時に両側再評価

### T-403: Watcher / debounce

- QMD/PPTX pairをprimary trigger
- rapid duplicate event coalescing
- same debounce windowのQMD/PPTX eventはpair-level re-evaluation
- assets/self-generated image writesを独立triggerにしない
- package stable/readable待ち

### T-404: Running / pending / document lock

- one active operation per document
- running中のsaveは1件PENDING
- eventごとのFIFO queueを作らない
- operation後にlatest pair再評価
- manual render/importとM3 document lock共有
- DOCUMENT_BUSYはbounded backoffで再評価
- file eventがなくてもlock releaseを確認
- no spin retry

### T-405: Self-generated write suppression

- expected committed fingerprintでself-write判定
- time-only ignore禁止
- mismatching eventはreal changeとして再評価
- no render/import loop

### T-406: QMD -> PPTX automatic sync
- Workspace orchestratorがCore起動前にpaired QMD + PowerPointをfreeze
- freeze中reopen/edit -> FREEZE_INVALIDATED、commit中止/再評価
- pending recoveryもfreeze後に実行

- QMD save
- pair-level evaluation
- PowerPoint dirty check
- dirty -> CONFLICT
- clean open -> close target presentation
- closed ->そのまま
- candidate render
- final on-disk hash validation
- M3 transactionでPPTX/assets/checkpoint commit
- M4が閉じたpresentationのみreopen
- pending再評価

### T-407: PPTX -> QMD automatic sync
- Workspace orchestratorがCore起動前にpaired QMD + PowerPointをfreeze
- M3 PPTX metadata writebackも同一pair freeze内で実行
- freeze中reopen/edit -> FREEZE_INVALIDATED、commit中止/再評価
- pending recoveryもfreeze後に実行

- PPTX save/package stable
- pair-level evaluation
- QMD dirty check
- dirty -> CONFLICT
- clean open -> QMD freeze
- candidate import
- final on-disk hash validation
- M3 transactionでQMD/assets/images/PPTX metadata/checkpoint commit
- QMD restore/reopen
- M3 PPTX writebackがある場合はclean PowerPoint close/reopenを含める
- pending再評価

### T-408: Conflict / Compare

- opposite side unsaved/independent changes -> CONFLICT
- automatic overwrite停止
- Cancel / Compare
- unsaved PowerPoint -> SaveCopyAs temporary snapshot
- unsaved QMD -> VS Code in-memory snapshot
- comparison reconstructionはnon-committing
- M5へsnapshot/normalized dataを渡す
- M4でwinner selectionしない

### T-409: Status / controls / diagnostics

- Synced / Building / Importing / Syncing / Pending / Conflict / Error / Paused
- auto start
- pause/resume
- destination freeze中の状態を明示
- render/import failure、host bridge failure、PowerPoint close/reopen failure、remote disconnectを区別

### T-410: Tests / regression

最低限:
- QMD save -> one effective render
- PPTX save -> one effective import
- duplicate debounce
- same-window pair re-evaluation
- running repeated save -> one pending
- self-write suppression
- PowerPoint open-dirty -> no auto close/render publish
- PowerPoint open-clean -> close, publish, reopen
- QMD dirty -> no auto freeze/import publish
- QMD open-clean -> freeze, publish, restore
- compare snapshots latest in-memory state
- checkpoint crash recovery
- front-matter-only change detection
- DOCUMENT_BUSY bounded re-evaluation without watched event
- PowerPoint close/reopen failure
- QMD restore failure
- M3 PPTX metadata writeback path while PowerPoint was open
- QMD/PPTX reopen before claim -> invalidated rename wins or Core committing rename wins; both never win
- claim/invalidation race repeated stress test
- reopen after claim with healthy control -> pending-reopen + immediate re-close
- Workspace/Local UI disconnect after claim -> TransactionSuspended before next file mutation, journal remains committing
- TransactionSuspendedはFileTransaction.commit()のgeneric BaseException -> immediate rollback経路を明示的に迂回
- rollback recovery中のsuspendはjournal phase=rolling_backを保持
- first replace後にcontrol loss -> no immediate rollback, new freeze/session before recovery
- checkpoint remains old unless transaction had already reached committed
- final replace後/committed marker前のsuspendもjournal未完了としてrecovery
- startupはjournal有無をcheckpointより先に確認し、pending journalがあればfreeze+recovery完了後にcheckpointを再読込してsync direction決定
- pending M3 recovery starts only after pair freeze
- reopen/invalidate during recovery -> safe stop/re-evaluation
- pause/resume
- M1/M2/M3/docx regression
- Windows real E2E after agent gates

### T-411: Final documentation / independent review

- PROJECT_CONTEXT / ROADMAP更新
- Test Agent
- Review Agent
- Architecture Agent
- old multi-lease/filesystem-lease designが残っていないこと
- M5を先取りしていないこと
- FAILなら最小修正して再レビュー
