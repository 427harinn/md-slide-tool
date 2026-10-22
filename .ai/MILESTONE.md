# MILESTONE

## マイルストーン名

M2: Stable IDs and Element Layout

## 背景

M0 Repository Cleanup と M1 QMD -> PPTX -> Microsoft PowerPoint は完了した。

現在のPPTX後処理は主に slide title でQMD側のスライド情報と生成済みPPTXを対応付けている。この方式ではタイトル変更、同名タイトル、将来のPPTX -> QMD往復に弱い。

M2では、QMD / PPTX / persistent layout の間で同じstable IDを使い、画像の配置を再render後も保持できる土台を作る。

詳細仕様は `docs/M2_STABLE_IDS_ASSETS.md`。

## 目的

```text
QMD
  slide-id
  element-id
     |
     v
QMD -> PPTX render
     |
     +-> PPTXへstable IDを埋め込む
     |
     +-> assets.jsonにlayoutあり -> 再適用
     |
     +-> layoutなし -> 現在のauto layout -> assets.jsonへ保存
```

## 設計原則

- slide title、slide order、image pathをstable identityとして使わない。
- slideは `slide-id`、要素は `element-id` で識別する。
- `element-id` は将来のshape等にも使える一般IDとする。
- M2実装対象のelement typeはimageのみ。
- QMDがstable IDの正本。
- IDがない既存QMDには不足分だけ自動発行する。
- 既存IDはrender時に変更しない。
- duplicate IDは自動修正せずFAIL。
- persistent JSONは文字情報の正本にしない。
- image layoutはEMU整数で保存する。
- assets layoutがあれば優先し、なければ既存auto layoutを使う。
- 既存 `place=` は初回/fallback preferenceとして維持する。
- docxを壊さない。
- M3のPPTX -> QMD importを先取り実装しない。

## 対象外

- PPTX -> QMD import
- QMD/PPTX file watcher
- automatic sync
- conflict handling
- PowerPoint Add-in
- shape layout persistence
- crop / rotation / z-order
- text-box layout persistence
- Marketplace publication
- PPTX -> Word

## 完了条件

- IDなしQMDへ不足している `slide-id` / `element-id` を安全に付与できる。
- 既存IDは繰り返しrenderしても変わらない。
- duplicate slide/element IDを検出してFAILできる。
- generated PPTXへslide/element stable IDを埋め込める。
- 初回画像は現在のauto layoutを使用できる。
- 初回/fallback layoutを `<stem>.assets.json` に保存できる。
- 次回renderではsaved layoutを優先して同じ画像矩形を復元できる。
- slide title変更後もstable IDで正しいslideへ画像を配置できる。
- image path変更後も同じ `element-id` ならlayoutを維持できる。
- stale assetsを成功render時に整理できる。
- invalid layoutは対象要素だけWARN + auto layoutへfallbackできる。
- PPTX / docx回帰テストがPASSする。
- M3以降の機能を先取りしていない。

## 状態

実装・自動テスト・独立Test/Review/Architecture・PR #17 head CI run #62はPASS。H-M2-01のPowerPoint desktop保存後metadata保持もPASSし、必須ACはすべて完了。PR #17はDraft解除可能（mergeは別判断）。
