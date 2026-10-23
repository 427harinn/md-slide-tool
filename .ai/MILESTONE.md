# MILESTONE

## マイルストーン名

M4: Save-driven Sync Engine v2

## 背景

M0〜M3で、QMD -> PPTX、stable ID、assets、managed PPTX -> QMD import、recoverable transactionまで完了した。

PR #20ではdestination-freeze / mutation-broker方式を設計したが、T-401 feasibilityで以下が成立しないことが分かった。

- VS Code側のatomic QMD freeze/replace primitive
- timeout後に遅延broker writeが発生しない保証
- commit/rollback/recoveryすべてを安全にcross-host broker化する前提

そのためM4はv2へ方向転換する。

詳細: `docs/M4_SYNC_ENGINE.md`

## 目的

```text
QMD save
  -> versioned preview PPTX
  -> PowerPointで最新preview表示

canonical PPTX save
  -> import candidate
  -> QMDへ安全に反映
```

## v2 原則

**supported editorが所有しているcanonical fileを別processからreplaceしない。**

- QMD編集時はcanonical PPTXを直接更新せず、versioned preview PPTXを生成する。
- PowerPoint編集時はcanonical managed PPTXを保存し、QMD側へ取り込む。
- preview PPTXは非canonical・disposable・import対象外。
- open-clean QMDへの反映はVS Code API経由をprobeする。
- これが安全に成立しなければ、QMDが閉じるまでPendingにする。

## 完了条件

- QMD save -> versioned preview PPTX生成。
- 最新previewをPowerPointで表示。
- 前previewがopen-cleanなら安全にclose可能。
- dirty previewは自動closeしない。
- previewはcanonical import triggerにならない。
- canonical PPTX save -> import candidate生成。
- QMD closedなら既存M3 transaction経由で反映。
- QMD open-cleanはeditor-mediated applyがfeasibility PASSの場合のみ自動反映。
- QMD open-dirtyはCONFLICT。
- canonical checkpointはpreview renderでは進めない。
- watcher/debounce/pending/self-write suppression。
- Cancel / Compare。
- M1/M2/M3/docx regression維持。

## 実装前gate

T-402A:
- versioned preview生成
- exact preview open
- prior clean preview close
- dirty preview保護
- multiple presentation targeting
- Japanese/space paths
- preview cleanup
- previewがcanonical import triggerにならない

T-402B:
- QMD open-clean/open-dirty判定
- candidate textをVS Code APIでexact editorへapply
- save through VS Code
- editor version race
- dirty buffer保護
- remaining M3 outputsとの整合

T-402B FAILの場合はclosed-QMD Pending fallbackを採用する。

## 状態

設計v2。production implementation前にT-402A/T-402B feasibilityを実施する。
