# MILESTONE

## マイルストーン名

M4: Docker Sync Engine

## 背景

M0 Repository Cleanup、M1 QMD -> PPTX -> Microsoft PowerPoint、M2 Stable IDs and Element Layout、M3 PPTX -> QMD Import は完了した。

M3により、managed PPTXをPowerPointで編集・保存し、`slidegen import` でQMD/assetsへ安全に戻せるようになった。M4ではこの手動往復を保存ベースの自動同期へ進める。

詳細仕様は `docs/M4_SYNC_ENGINE.md`。

## 目的

通常操作ではユーザーがBuild/importコマンドを意識せず、保存を同期トリガーにする。

```text
QMD save  -> automatic render -> PPTX
PPTX save -> automatic import -> QMD/assets
```

通常時は自動同期し、未保存/独立変更が両側に存在して上書き危険がある場合だけ自動処理を止める。

```text
possible conflict
  -> stop
  -> [Cancel] [Compare]
```

## 設計原則

- Docker / Dev Containerをwatch・debounce・state machine・render/import orchestrationの中心にする。
- QMD/PPTX保存を主triggerにする。assets/imageのmd-slide-tool自身による書き込みを独立user triggerにしない。
- file eventの回数ではなく、hash/fingerprintとmanaged metadataで実変更を判定する。
- self-generated write suppressionを時間だけのignore windowに依存させない。
- active operation中の追加saveはcoalesced pendingとして1件にまとめ、現在処理を途中cancelしない。
- QMDとPPTXの両側に未保存/独立変更がある場合は自動で勝者を選ばずCONFLICTへ遷移する。
- conflict promptは原則 `Cancel / Compare`。曖昧なContinueで片側を上書きしない。
- PowerPoint未保存状態の比較では本体を強制保存せず、SaveCopyAs相当のnon-destructive snapshotを作る。
- QMD未保存状態の比較ではVS Code editorのin-memory textをsnapshotとして使う。
- internal stable IDs / hashes / generation tokensは通常ユーザーへ見せない。
- M4は競合検出・snapshot・比較entrypointまで。Semantic Diffと採用側決定はM5。
- incremental/selective buildはM4初期実装の必須要件にしない。


- destructive syncはadmission時とcommit直前の二段階でdirty/fingerprintを再検証し、途中編集を上書きしない。
- QMD/PPTX eventが同じdebounce windowに来た場合はarrival orderで方向を決めずpair全体を再評価する。
- M4 sync checkpointはfront matter込みQMD hashを持ち、canonical outputsと同じrecoverable transaction境界でcommit/recoverする。
- Workspace/Core -> Windows Local UIのdirty-state / snapshot request-responseはT-401でtimeout/disconnectを含めてfeasibility確認する。
- manual render/importとのDOCUMENT_BUSYはspin retryせずpending re-evaluationへ戻す。

- final validation後からcanonical publication完了まではcommit barrier / conditional publicationで保護し、check-then-write raceを許可しない。
- PowerPointがopenのまま自動publishする場合はvalidated tokenに結びついたexclusive presentation publish leaseを必須とし、成立しなければその経路をre-scopeする。
- PPTX -> QMDはVS Code TextDocument versionに結びついたeditor publish leaseまたはversion-conditional publicationを必須とする。
- COMMITTING中のsave/change eventはPENDINGとして保持し、barrier release後にpair全体を再評価する。
- DOCUMENT_BUSY後はfile eventがなくてもbounded timer/backoffでlock releaseを再確認する。

- Core -> Workspace extensionにQMD lease RPC（acquire/renew/release）を持たせ、transaction全体でleaseを保持する。
- canonical file publicationは全replace/delete targetのexclusive filesystem leaseとexpected-old-hash/expected-absence確認を必須とする。
- FileTransaction.commitはunconditional replaceを行わず、lease下のCAS preconditionを満たした場合のみpublishする。
- Windows host-visible file leaseが実証できないtargetはautomatic destructive publication対象外にre-scopeする。

## 対象外

- keystroke-level live sync
- automatic field-level merge
- final Semantic Diff/resolution UI
- per-change merge
- arbitrary PowerPoint shapes beyond M3
- PowerPoint Add-in（feasibilityで必要性が判明した場合は設計変更を先に行う）
- incremental render optimization
- Marketplace publication
- PPTX -> Word

## 完了条件

- managed QMD/PPTX pairのsaveを自動監視できる。
- QMD saveでautomatic render、PPTX saveでautomatic importが動く。
- duplicate filesystem eventsをdebounce/coalesceできる。
- running中の追加saveをpendingとして安全に再評価できる。
- render/import自身の書き込みで逆方向処理が無限連鎖しない。
- last synchronized fingerprintからsaved-side changesを判定できる。
- VS Code QMD dirty stateとPowerPoint dirty stateを安全に確認できる。
- conflict時は自動上書きを止め、Cancel/Compareを提示できる。
- unsaved PowerPoint/QMDのlatest-state snapshotを元ファイルを破壊せず作れる。
- status barでSynced/Building/Importing/Pending/Conflict/Error/Paused等の状態を確認できる。
- syncはworkspace起動時に自動開始し、pause/resumeできる。
- error時に無限retryせず、安全に再試行できる。
- remote disconnect/build failure/PowerPoint host failureを区別して診断できる。
- M1/M2/M3/docx regressionを壊さない。

## 状態

設計中。M4 design PRで Review / Architecture gateを通過後にproduction implementationへ進む。
PowerPoint dirty-state / SaveCopyAs host bridge feasibilityは実装前必須gate。
