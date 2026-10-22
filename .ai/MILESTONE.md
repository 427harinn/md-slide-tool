# MILESTONE

## マイルストーン名

M3: PPTX -> QMD Import

## 背景

M0 Repository Cleanup、M1 QMD -> PPTX -> Microsoft PowerPoint、M2 Stable IDs and Element Layout は完了した。

M2でQMD/PPTX/assetsの間に `slide-id` / `element-id` を導入し、画像のx/y/width/heightを永続化できるようになった。PowerPoint desktop保存後もstable IDが保持されることを実機確認済み。

M3では、このidentityを利用して、md-slide-toolが生成したPPTXをPowerPointで編集した結果を既存QMD/assetsへ戻せるようにする。

詳細仕様は `docs/M3_PPTX_IMPORT.md`。

## 目的

```text
QMD + assets
  -> slidegen render
  -> PPTX
  -> PowerPoint edit/save
  -> slidegen import
  -> rebuilt QMD + updated assets
```

## 設計原則

- 任意PPTX変換ではなく、md-slide-tool管理PPTXのimportを対象にする。
- import時は保存済みPPTXをsupported contentのsource of truthとする。
- front matterは既存QMDから維持する。
- normal slideはstable `slide-id` で識別する。
- visual elementは `element-id` で識別する。
- 新規PowerPoint slide/imageにはIDを発行しPPTXにも書き戻す。
- title/bodyはQMDへ正規化して書き戻し、persistent intermediate text JSONは作らない。
- image geometryとcropはassetsへ保存する。
- PowerPoint画像cropはM3正式対応。
- unsupported contentを黙って捨てない。
- import全体はatomicに行う。
- M4 watcher/sync、M5 conflict handlingを先取りしない。

## 対象外

- arbitrary external PPTX conversion
- automatic file watch / sync
- dirty-state conflict handling
- automatic text merge
- arbitrary shapes / SmartArt / charts / free-position text boxes
- rotation / z-order
- title slide/front matter reverse import
- PowerPoint Add-in
- Marketplace publication
- PPTX -> Word

## 完了条件

- `slidegen import <pptx>` がmanaged PPTXとsame-stem QMDを対象に動作する。
- QMD front matterを維持する。
- title / paragraph / bullet / numbered listをnormalized QMDへ復元できる。
- slide reorder/deleteをQMDへ反映できる。
- PowerPoint新規supported slideへslide-idを発行してQMD/PPTXへ反映できる。
- existing imageのmove/resizeをassetsへ反映できる。
- image cropをassetsへ保存し、次renderで見た目を再現できる。
- same identified shapeの画像差し替えでelement-idを維持できる。
- 新規imageへelement-idを発行し、画像を安全に抽出してQMD/PPTX/assetsへ反映できる。
- image削除をQMD/assetsへ反映できる。
- unsupported destructive contentを検出した場合はcommit前にFAILする。
- import失敗時にQMD/assets/PPTX/managed imagesを部分更新しない。
- existing render / M1 open / M2 assets / docx regressionを壊さない。

## 状態

設計確定・未実装。
