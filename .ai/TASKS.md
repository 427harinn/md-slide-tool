# TASKS

## M2: Stable IDs and Element Layout

Codexは `.ai/AGENT_WORKFLOW.md` に従い、実装前にAcceptance CriteriaとTest Planを確認し、上から順に進める。

### T-201: M2 data model / existing pipeline inspection

- 現在のQMD parsingと一時images JSONを確認
- title-based slide matching箇所を特定
- PPTX slide/shapeへstable metadataを保存する最小方式を検証
- PowerPointで通常saveした後も選択したmetadataが残ることを検証可能にする
- `assets.json` schema v1を実装前にfixture化する

**状態:** 完了。既存パイプライン、assets schema v1、`Slide.name` / picture `Shape.name` のsave/reopen可否を確認。

### T-202: Stable ID parser / validation

- QMDの `slide-id` / `element-id` をparse
- UUID-based opaque IDを不足分だけ生成
- 既存IDを保持
- duplicate slide-id / element-idをFAIL
- source QMDへの書き戻しはatomic
- ID追加以外のQMD本文を変更しない

**状態:** 完了。UUID形式、duplicate検出、atomic QMD更新を実装・テスト。

### T-203: General element model, image implementation

- internal modelを `elementId` / `type` ベースにする
- M2では `type=image` のみ実装
- `image-id` という別identity体系を作らない
- current image path / caption / place parsingを維持

**状態:** 完了。共通identityを `element-id` とし、M2ではimageのみ実装。

### T-204: assets.json schema v1

- `<qmd stem>.assets.json`
- `schemaVersion: 1`
- actual PPTX slide sizeをEMUで記録
- `elements[]` に slideId / elementId / type=image / path / x / y / width / height
- title/body等の文字情報を保存しない
- schema validation / invalid layout handlingを追加

**状態:** 完了。schema v1、EMU座標、atomic write、invalid layout validationを実装・テスト。

### T-205: Stable ID embedding into PPTX

- slideへ `slide-id` を埋め込む
- picture shapeへ `element-id` を埋め込む
- PowerPoint内部numeric slide IDをmd-slide-tool stable IDとして流用しない
- save/reopenでmetadataが維持される方式を選ぶ

**状態:** 完了。slide / picture名へstable IDを設定し、python-pptx save/reopenをテスト。

### T-206: Layout restore and fallback

優先順位:

1. slide-id + element-idのsaved layout
2. existing `place=` preference
3. current automatic placement engine

- valid assets layoutをそのまま適用
- missing layoutはcurrent auto layout
- resulting rectangleをassetsへ保存
- invalid single-element layoutはWARN + auto fallback

**状態:** 完了。saved -> `place=` -> autoの優先順、auto/off-slide layout保存と復元を実装・テスト。

### T-207: Stale assets cleanup

- QMDに存在しないslideId/elementId entryを成功render時に削除
- failed renderでは正常な既存assetsを不用意に破壊しない
- path変更のみではsame elementIdのlayoutを保持

**状態:** 完了。successful postprocess後にatomic更新し、stale entryを整理。

### T-208: Tests / regression

最低限:

- missing ID generation
- existing ID stability
- duplicate ID failure
- source QMD preservation
- assets schema / EMU integer validation
- first render auto layout persistence
- second render saved layout restore
- title rename with same slide-id
- image path change with same element-id
- stale asset cleanup
- invalid layout fallback
- PPTX embedded ID roundtrip
- current placement tests
- representative PPTX render
- docx regression
- smoke / CI

**状態:** 完了。Python 18件、代表Quarto/PPTX render、DOCX回帰、smoke、PR #17 CI run #60がPASS。

### T-209: Documentation / final independent review

- README / PROJECT_CONTEXT / ROADMAPを実装結果に合わせる
- Review Agent
- Architecture Agent
- Test Agent
- M3機能を先取りしていないことを確認
- FAILがあればImplementationへ差し戻して再レビュー

**状態:** 完了。Review/Architecture、PR #17 CI run #60がPASS。PowerPoint desktop保存保持はHUMAN_REQUIRED。
