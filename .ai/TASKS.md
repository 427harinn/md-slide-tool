# TASKS

## M3: PPTX -> QMD Import

Codexは `.ai/AGENT_WORKFLOW.md` に従い、実装前に `docs/M3_PPTX_IMPORT.md`、Acceptance Criteria、Test Planを確認する。

### T-301: Import feasibility / PPTX structure inspection

- M2 stable metadataを読む方法を確認
- title/body/list placeholderのPowerPoint構造をfixture化
- picture image bytes / format / crop値の取得方法を検証
- template/master/layout由来shapeとuser contentの分類方法を整理
- unsupported content classificationを実装前に決定

**状態:** 未着手

### T-302: CLI and managed-presentation validation

- `slidegen import <pptx>` を追加
- same-stem QMDを必須にする
- arbitrary unmanaged PPTXを拒否
- assets path / project pathsを安全に解決
- watcher/sync optionは追加しない

**状態:** 未着手

### T-303: PPTX slide model and stable IDs

- existing `slide-id` を読む
- new supported slideへUUID stable IDを発行
- new IDをrebuilt QMDとPPTXへ書き戻す
- slide orderをPPTX順で保持
- deleted managed slideをrebuilt QMDから除外

**状態:** 未着手

### T-304: Text reconstruction

- title
- ordinary paragraph
- bullet list
- numbered list
をnormalized Markdownへ変換する。

- front matter維持
- front-matter title slideはimport対象外
- unsupported text structuresは明示的に検出

**状態:** 未着手

### T-305: Existing/new/replaced image handling

- existing `element-id` を保持
- same identified picture shapeのreplacementをsame elementとして扱う
- new pictureへ `element-id` を発行しPPTXへ書き戻す
- changed/new imageを `img/imported/<element-id>.<ext>` に抽出
- shared original sourceを破壊的に上書きしない
- deleted imageをQMD/assetsから除外

**状態:** 未着手

### T-306: Image layout and crop import

- x/y/width/heightをEMUでassetsへ保存
- PowerPoint cropをper-element assets metadataへ保存
- cropなしschema v1 assetsとの後方互換を維持
- imported cropを次renderでPowerPointへ再適用
- rotation / z-orderはunsupported

**状態:** 未着手

### T-307: Unsupported content guard

- shapes / SmartArt / charts / arbitrary text boxes / unsupported structuresを分類
- data-loss riskがあるunsupported contentはcommit前FAIL
- known harmless template-only contentだけ明示ルールで除外
- unknown contentを推測で無視しない

**状態:** 未着手

### T-308: Atomic import transaction

- parse/validateを先に完了
- QMD/assets/images/PPTX metadata updateをstage
- 全て成功後にcommit
- failure時にoriginal filesを変更しない
- temporary artifactsをcleanup

**状態:** 未着手

### T-309: Tests / regression

最低限:

- managed/unmanaged validation
- front matter preservation
- title/paragraph/bullet/numbered list import
- slide reorder/delete
- new slide ID generation/writeback
- image move/resize
- crop import + re-render visual/metadata roundtrip
- same-shape image replacement identity
- new image extraction/ID/writeback
- image deletion
- shared-source replacement safety
- unsupported-content FAIL
- atomic rollback
- M1/M2/render/docx regression
- smoke / CI / diff-check

**状態:** 未着手

### T-310: Final documentation / independent review

- README / PROJECT_CONTEXT / ROADMAP更新
- Test Agent
- Review Agent
- Architecture Agent
- M4/M5を先取りしていないことを確認
- FAILがあれば最小修正して再検証

**状態:** 未着手
