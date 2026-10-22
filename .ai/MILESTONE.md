# MILESTONE

## マイルストーン名

M3: PPTX -> QMD Import

## 背景

M0 Repository Cleanup、M1 QMD -> PPTX -> Microsoft PowerPoint、M2 Stable IDs and Element Layout は完了した。

M2でQMD/PPTX/assetsの間に `slide-id` / `element-id` を導入し、画像のx/y/width/heightを永続化できるようになった。PowerPoint desktop保存後もstable IDが保持されることを実機確認済み。

M3では、このidentityを利用して、md-slide-toolが生成したPPTXをPowerPointで編集した結果を既存QMD/assetsへ安全に戻す。

詳細仕様は `docs/M3_PPTX_IMPORT.md`。

## 目的

```text
QMD + assets
  -> slidegen render
  -> managed PPTX
  -> PowerPoint edit/save
  -> slidegen import
  -> rebuilt QMD + updated assets
```

## 設計原則

- arbitrary PPTXを推測変換せず、presentation-level managed markerを持つM3-managed PPTXだけをimportする。
- M3-capable renderはmanaged marker / format-version / document-id / QMD body SHA-256 baselineをPPTXへ埋め込む。
- QMD normal-slide bodyがrender後に変更されていたらimportをpre-commit FAILし、意図しない上書きを防ぐ。
- front matterは既存QMDからbyte-preserveする。
- front-matter title slideはreserved internal role markerで位置と独立に識別する。
- normal slideはstable `slide-id`、visual elementは `element-id` で識別する。
- 新規supported slide/imageにはIDを発行しPPTXにも書き戻す。
- title/bodyはnormalized QMDへ書き戻し、persistent intermediate text JSONは作らない。
- image geometryとcropはassetsへ保存する。
- crop導入でassets schema v2へmigrationし、v1はno-cropとして後方互換で読む。
- unsupported slide-local user contentを黙って捨てない。
- importはtransaction journal + backup + recoveryによりrecoverable consistencyを保証する。
- M4 watcher/sync、M5 full conflict handlingを先取りしない。

## 対象外

- arbitrary external PPTX conversion
- heuristic legacy M2 import（M3-capable renderを一度実行する）
- automatic file watch / sync
- full dirty-state conflict merge
- force import over changed QMD
- arbitrary shapes / SmartArt / charts / free-position text boxes
- rotation / z-order
- title slide/front matter reverse import
- PowerPoint Add-in
- Marketplace publication
- PPTX -> Word

## 完了条件

- managed marker/version/document-idによってmanaged PPTXを明確に判定できる。
- current QMD bodyがrender baselineと違う場合にimportを止められる。
- title slideをpositionではなくreserved role markerで識別できる。
- title marker移動/削除/duplicate/ambiguous lossを安全に扱える。
- `slidegen import <pptx>` がsame-stem QMDを対象に動作する。
- QMD front matterを維持する。
- title / paragraph / bullet / numbered listをnormalized QMDへ復元できる。
- slide reorder/delete/new slideをstable IDで反映できる。
- existing imageのmove/resizeをassetsへ反映できる。
- assets v1を読み、v2へ安全にmigrationできる。
- image cropをv2 assetsへ保存し、次renderで見た目を再現できる。
- same identified shapeの画像差し替えでelement-idを維持できる。
- 新規imageへelement-idを発行し、画像を安全に抽出してQMD/PPTX/assetsへ反映できる。
- image削除をQMD/assetsへ反映できる。
- template/master/layoutとuser contentをexplicit structural ruleで分類できる。
- unsupported destructive contentを検出した場合はcommit前にFAILする。
- handled commit failureはrollbackし、simulated crashは次回commandでrecoverできる。
- unknown post-crash editsをrecoveryが勝手に上書きしない。
- existing render / M1 open / M2 assets / docx regressionを壊さない。

## 状態

設計レビュー指摘を反映済み。再Review / Architecture待ち。未実装。
