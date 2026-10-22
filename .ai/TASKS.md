# TASKS

## M3: PPTX -> QMD Import

Codexは `.ai/AGENT_WORKFLOW.md` に従い、実装前に `docs/M3_PPTX_IMPORT.md`、Acceptance Criteria、Test Planを確認する。

### T-301: Import feasibility / structural fixtures

実装開始前の必須gate。

- M2 stable slide/element metadataを読む方法を確認
- supported templateで生成したPPTXのslide/master/layout/placeholder/shape構造をfixture化
- title/body/list placeholder構造をfixture化
- picture bytes / format / crop raw OOXML値をfixture化
- inherited master/layout decorationとslide-local objectの差を確認
- current supported templateが未知のslide-local decorative shapeを生成する場合は、位置heuristicではなくdeterministic marker/structural ruleを設計してから先へ進む
- presentation custom propertiesとreserved title-slide markerがPowerPoint-compatible save/reopenで保持できる方式を検証

**状態:** 未着手

### T-302: Managed presentation metadata / QMD baseline guard

- M3-capable renderでmanaged marker / format version / document-idをPPTXへ保存
- assets schema v2のtop-level documentIdへ同じdocument-idを保存
- stable ID normalization後のcanonical QMD normal-slide body SHA-256を保存
- BOM / front matter境界 / LF-CRLF-CR正規化ルールを共通helperとして固定
- same-stem QMD必須
- unmarked legacy/arbitrary PPTXをrejectし、re-renderを案内
- current QMD body hash mismatchは `QMD_CHANGED_SINCE_RENDER` としてpre-commit FAIL
- force import/mergeは追加しない

**状態:** 未着手

### T-303: Title-slide role / normal slide IDs

- front-matter title slideへreserved internal role markerを付与
- markerはpositionに依存しない
- moved/deleted title slideを安全に扱う
- duplicate title markerをFAIL
- ID-less title-layout slideがambiguousならFAIL
- existing normal `slide-id` を読む
- new supported normal slideへUUID stable IDを発行しQMD/PPTXへ反映
- malformed/duplicate slide-idをFAIL
- slide order/deleteをPPTX順で反映

**状態:** 未着手

### T-304: Text reconstruction / caption companion

- md-slide-tool生成caption textboxへ `mdst-caption-<element-uuid>` markerを付与
- caption markerはassociated picture `element-id` と1:1で対応
- caption textをMarkdown image alt/captionへ復元
- orphan/duplicate caption markerをFAIL
- arbitrary unmarked textboxはunsupportedのまま

### T-304b: Text reconstruction

- title
- ordinary paragraph
- bullet list
- numbered list
をnormalized Markdownへ変換する。

- front matter byte-preserve
- front-matter title slideはreverse import対象外
- unsupported text structuresは明示的にFAIL

**状態:** 未着手

### T-305: Existing/new/replaced image handling

- existing `element-id` を保持
- malformed/duplicate element-idをFAIL
- same identified picture shapeのreplacementをsame elementとして扱う
- new pictureへ `element-id` を発行しPPTXへ書き戻す
- changed/new imageを `img/imported/<element-id>.<ext>` に抽出
- shared original sourceを破壊的に上書きしない
- deleted imageをQMD/assetsから除外

**状態:** 未着手

### T-306: Assets schema v2 / geometry / crop

- schema v1をno-cropとして読み込む
- M3 writeでschema v2へmigration
- x/y/width/heightをEMU整数で保存
- cropはraw OOXML percentage整数で保存（100000 = 100%）
- negative PowerPoint-valid cropを保持
- effective source rectがnon-positive、非integer、grossly invalidな値はFAIL
- next renderでv1/v2両方を読み、v2 cropを再適用
- source image自体はcrop目的で加工しない
- rotation / z-orderはunsupported

**状態:** 未着手

### T-307: Unsupported content guard / template classification

- inherited master/layout objectはuser contentにしない
- supported title/body/content placeholderとpictureのみ明示対応
- slide-local autoshape / arbitrary textbox / group / table / chart / SmartArt / OLE/media / unknownはpre-commit FAIL
- unknown contentをdecorativeと推測しない
- T-301 fixturesでclassification ruleを固定してから実装

**状態:** 未着手

### T-308: Recoverable transaction / crash recovery

- documentId未生成のschema v1ではcanonical same-stem QMD path由来のbootstrap lockを先に取得
- bootstrap lock保持中にassets/PPTX metadataを再読込し、既にmigration済みなら既存documentIdを再利用
- unmigratedならbootstrap lock下でdocumentIdを1つだけ生成しschema v2/PPTX metadata migrationを完了
- migrationを実行したprocess自身もbootstrap lockを保持したまま新document lockを取得し、その取得後にのみbootstrapを解放
- re-readでmigration済みを発見したprocessもbootstrap保持中にexisting document lockを取得してからbootstrapを解放
- bootstrap -> document lockのhandoffにunlock gapを作らず、逆順取得は禁止
- 通常はper-document lockをatomicに取得し、concurrent render/importは `DOCUMENT_BUSY`
- `.md-slide-tool/transactions/<document-id>/<txid>/` にmanifest/old/newをstage
- create / replace / delete operationとold/new SHA-256をmanifestへ記録
- state machine: prepared -> committing -> committed -> cleanup / rolling_back -> rolled_back -> cleanup
- per-file atomic replaceを使用
- handled commit failureではcreate/replace/deleteをrollbackしてからFAIL
- abrupt termination時はphase別にrecovery
- committedならrollbackせずnew state検証後cleanup
- current hashがold/newどちらでもない場合は自動上書きせずmanual-recovery error
- failure injectionとsimulated abrupt terminationをテスト

**状態:** 未着手

### T-309: Tests / regression

最低限:

- managed marker valid/missing/invalid
- concurrent first M3 render from schema v1 produces exactly one documentId
- bootstrap re-read/reuse and bootstrap->document lock handoff
- document-id / format version validation
- QMD body hash match/mismatch
- title marker move/delete/duplicate/loss ambiguity
- new slide before/after title slide
- all previously managed normal slides deleted but presentation marker remains
- front matter byte preservation
- title/paragraph/bullet/numbered list import
- slide reorder/delete/new ID writeback
- image move/resize
- crop schema v1 compatibility + v2 migration + valid/negative/invalid crop + re-render roundtrip
- same-shape image replacement identity
- new image extraction/ID/writeback
- image deletion
- shared-source replacement safety
- template/master/layout fixtures
- unsupported slide-local content FAIL
- handled commit failure rollback after each step
- simulated crash + next-command recovery
- recovery unknown-hash safety stop
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
