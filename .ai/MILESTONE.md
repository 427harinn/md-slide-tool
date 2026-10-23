# MILESTONE

## マイルストーン名

M4: Docker Sync Engine

## 背景

M0〜M3で、QMD -> PPTX、stable ID、assets、managed PPTX -> QMD import、recoverable transactionまで完了した。

M4では、この手動往復を保存ベースの自動同期へ進める。

詳細仕様は `docs/M4_SYNC_ENGINE.md`。

## 目的

```text
QMD save  -> automatic render -> PPTX
PPTX save -> automatic import -> QMD/assets
```

通常は自動同期し、相手側に未保存/独立変更がある場合だけ自動処理を止める。

```text
possible conflict
  -> [Cancel] [Compare]
```

## M4の簡略化方針

M4は、PowerPoint/VS Codeを編集可能なまま複数leaseで同時保護する方式を採用しない。

正式サポートする編集経路は:

```text
QMD  -> VS Code
PPTX -> Microsoft PowerPoint desktop
```

同期中は書き込み先を短時間だけfreezeする。

- QMD -> PPTX: PowerPointがopen-dirtyならCONFLICT。open-cleanなら対象presentationを一時closeしてからpublishし、完了後reopen。
- PPTX -> QMD: QMDがdirtyならCONFLICT。open-cleanならVS Code側でeditorを一時close/hideしてからpublishし、完了後restore。
- Coreは document lock -> destination freeze -> final hash check -> M3 transaction + sync checkpoint -> restore -> unlock の順で処理する。
- arbitrary external processとの同時書き込みをM4の保証範囲にしない。
- ただしcommit直前のexpected hash確認とM3 recoverable transactionは維持する。

## 設計原則

- watcher/debounce/state machineはDocker / Dev Container側。
- VS Codeはdirty-state、QMD freeze、status、Conflict/Compare UI。
- Windows Local UIはPowerPoint state、close/reopen、SaveCopyAs。
- running中の複数saveは1件のPENDINGにcoalesce。
- self-generated writesはhash/fingerprintで抑制。
- sync checkpointはfront matter込みQMD hashとPPTX fingerprintを持つが、本文を複製しない。
- checkpointは同期outputsと同じrecoverable transactionでcommit。
- M4はConflict検出/Compare snapshotまで。Semantic Diffとwinner selectionはM5。
- incremental buildはM4初期要件にしない。

## 対象外

- keystroke-level live sync
- automatic semantic merge
- final M5 diff/resolution UI
- arbitrary external editors/processesとの完全な同時書き込み保証
- Windows-wide filesystem lease
- long-lived QMD/PowerPoint publish lease
- incremental render optimization
- arbitrary PowerPoint shapes beyond M3
- Marketplace publication
- PPTX -> Word

## 完了条件

- QMD saveでautomatic render。
- PPTX saveでautomatic import。
- duplicate event debounce / pending coalescing。
- self-write loop防止。
- PowerPoint dirty/clean/closed判定。
- QMD dirty/clean判定。
- QMD -> PPTX時にclean presentationを安全にclose/reopen。
- PPTX -> QMD時にclean QMD editorを安全にfreeze/restore。
- dirty destinationは自動で閉じずCONFLICT。
- conflictはCancel / Compare。
- Compareはunsaved PowerPoint/QMDの最新状態を壊さずsnapshot化。
- checkpoint / crash recoveryがM3 transactionと整合。
- DOCUMENT_BUSYはbounded pending re-evaluation。
- status bar / pause-resume。
- M1/M2/M3/docx regressionを維持。

## 状態

設計中。destination freeze方式へ再整理済み。
T-401でPowerPoint close/reopen、QMD editor freeze/restore、cross-host controlを実機検証してからproduction implementationへ進む。
