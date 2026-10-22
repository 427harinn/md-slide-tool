# md-slide-tool Roadmap

## 目的

md-slide-tool は、Quarto を使って QMD から PowerPoint / Word などの成果物を生成するツールとして発展させる。

今後の PowerPoint 系の中心思想は、独自スライドエディタを作ることではなく、Microsoft PowerPoint を実編集環境として利用し、QMD と PPTX を往復できるようにすること。

## 長期設計原則

### 1. Docker / Dev Container をロジックの中心にする

変換、監視、同期、競合判定などの主要ロジックは Docker / Dev Container 側に置く。

VS Code と PowerPoint 側には、できるだけ変換ロジックを置かない。

将来的な役割:

- Docker / Core: build, import, watch, sync, conflict handling
- VS Code: editor UI, dirty state notification, diff display
- PowerPoint: actual slide editing, save, later dirty-state notification

### 2. QMD と PPTX は差分同期しない

QMD と PPTX の内容をフィールド単位で双方向マージしない。

保存された側を入力として、もう一方を原則毎回再生成する。

- QMD save -> QMD -> PPTX rebuild
- PPTX save -> PPTX -> QMD rebuild

文字情報は中間 JSON に複製しない。

### 3. Visual elementのレイアウトだけを永続化する

QMD では保持しにくいvisual elementのレイアウト情報だけを専用ファイルに保存する。M2では画像のみを実装対象にする。

想定:

```text
presentation.qmd
presentation.pptx
presentation.assets.json
img/
```

`assets.json` の初期責務:

- slide id
- element id
- element type
- source path（imageの場合）
- x / y
- width / height

必要になった段階で crop / rotation / z-order などを追加する。

タイトルや本文などの文字情報は保存しない。

### 4. 永続 ID を導入する

将来的に QMD と PPTX を往復するため、タイトル文字列やファイル名だけで要素を識別しない。

導入候補:

- slide id
- element id

QMD、PPTX shape、assets.json の間で同じ ID を利用する。M2では `element-id` を画像に適用し、将来のshape等でも同じidentity modelを使えるようにする。

### 5. Word 対応は正式機能として維持する

docx は現在利用中の正式機能なので削除対象にしない。

PowerPoint 系の再設計完了後には、完成したプレゼンテーション内容から Word 文書を生成する機能も検討する。

html は現状の利用状況・実装品質を確認してから継続可否を判断する。

---

# 実装ロードマップ

## M0: Repository Cleanup ✅

状態: 完了

目的:
今後の開発の土台を作る。

実施候補:

- 現在利用している機能と実験コードの棚卸し
- 不採用となった VS Code 内 PPTX->PDF preview 実験の削除
- PDF.js 関連依存・Webview 実装の削除
- Preview 専用でしか使っていない LibreOffice 依存の削除可否確認
- `triggerTaskOnSave` など複数存在する自動 build 経路の整理
- 空の `compose.yml`、コミット済み `.DS_Store` 等の整理
- CLI / render / template / tests の責務整理
- README / .ai ドキュメントを現在の実装と一致させる
- docx 機能を維持
- 既存の QMD -> PPTX 出力結果を壊さない

この段階では PPTX->QMD、assets.json、競合処理は実装しない。

## M1: QMD -> PPTX -> PowerPoint

状態: 実装完了。Windows実機で二層extension、cross-host command routing、Dev Container build、host path mapping、正しいPowerPoint openを確認済み。自動テストとCIもPASSを完了条件とする。

詳細: `docs/M1_POWERPOINT_OPEN.md`

目的:
現在の片方向ワークフローを完成させる。

完成フロー:

```text
QMD save/build
  -> Docker / Dev Container で PPTX build
  -> host bridge
  -> Microsoft PowerPoint で生成 PPTX を開く
```

方針:

- build ロジックは Docker 側
- host 側には「指定された PPTX を PowerPoint で開く」最小責務のみ
- Windows / macOS の差異は host adapter に閉じ込める
- VS Code 内 PDF preview は前提にしない

Marketplace公開、publisher設定、通常のReopen in Containerでの自動extension配置、公開後E2EはM1 completion gateに含めず、正式リリース前の横断Release / Distribution gateで扱う。

## M2: Stable IDs and Element Layout

状態: 完了。stable ID、image assets layout、PowerPoint desktop保存後のmetadata保持まで確認済み。

目的:
将来の往復変換に必要なstable identityとvisual element layout保存を導入する。

詳細: `docs/M2_STABLE_IDS_ASSETS.md`

内容:

- `slide-id`
- `element-id`
- M2 element typeはimageのみ
- `assets.json` schema v1
- EMU座標の x / y / width / height
- 既存layoutがあればstable IDで再適用
- layoutがなければ現在の画像自動配置を利用して保存
- title/path変更でもIDが同じならidentity/layoutを維持
- generated PPTXへ同じstable IDを埋め込み、M3のimportに備える
- 将来のshape等へ拡張できるが、shape persistence自体はM2で実装しない

## M3: PPTX -> QMD Import

状態: 設計レビュー指摘を反映済み・未実装。

詳細: `docs/M3_PPTX_IMPORT.md`

目的:
md-slide-toolで生成したmanaged PPTXをPowerPointで編集・保存した結果を、stable IDとpresentation-level metadataを使って既存QMD/assetsへ安全に戻せるようにする。

初期CLI:

```bash
slidegen import presentation.pptx
```

主要方針:

- arbitrary PPTXはimportせず、managed marker / format version / document-idを持つPPTXだけを対象
- same-stem QMD必須
- render時にQMD normal-body SHA-256をPPTXへ保存し、未render QMD編集があればimportを止める
- front matterを維持
- front-matter title slideはreserved internal role markerでpositionと独立に識別
- title / paragraph / bullet / numbered listをnormalized Markdownへ再構築
- slide reorder / delete / new slideをstable IDで反映
- image add / delete / replacementを `element-id` で追跡
- changed/new imageは `img/imported/<element-id>.<ext>` へ安全に抽出
- image x/y/width/heightをassetsへ保存
- assets schema v2でPowerPoint image cropをraw OOXML percentage整数として保存し、次renderで再適用
- schema v1はno-cropとして後方互換で読む
- template/master/layoutとuser contentはexplicit structural ruleで分類し、unknown slide-local contentはFAIL
- QMD/assets/images/PPTX ID writebackはjournal + backup + hash recoveryを使うrecoverable transaction
- watch/syncはM4、full dirty conflict handlingはM5

## M4: Docker Sync Engine

目的:
QMD と PPTX の保存を自動監視して build/import を呼び分ける。

想定:

```text
QMD save  -> render
PPTX save -> import
```

責務:

- file watch
- debounce
- running / pending
- self-generated write suppression
- error handling

過去の Auto Preview 実験にある debounce / running / pending の考え方は参考にできるが、ブランチをそのまま統合することは前提にしない。

## M5: Conflict Handling

目的:
両側で編集された場合にもデータを失わない。

想定:

```text
presentation.qmd
presentation.conflict-pptx.qmd
presentation.assets.json
presentation.conflict-pptx.assets.json
```

QMD が dirty の状態で PPTX 保存が発生した場合:

- 本体 QMD は上書きしない
- PPTX から conflict QMD を生成
- VS Code で diff を表示
- 人間が採用 / 手動マージする

自動テキストマージは初期仕様にしない。

## M6: PPTX -> Word

PowerPoint / QMD 往復が安定した後に検討する。

候補:

- PPTX の完成内容を QMD に取り込む
- QMD を中間表現として既存 docx 出力へ接続
- プレゼン資料を報告書・配布資料へ変換する

## Cross-cutting: Release / Distribution (before formal release)

This release gate is separate from M0–M6 milestone completion. Complete it before the first formal public release, after the product structure is sufficiently stable. Marketplace publication is not part of M1 and is not authorized by this roadmap entry.

- Decide and configure the Marketplace publisher.
- Publish the Local UI and Remote Workspace extension packages.
- Establish extension versioning and compatibility policy.
- Add the published extension ID(s) to `customizations.vscode.extensions` and use extension dependencies for Local / Remote placement.
- Verify the standard **Reopen in Container** flow without manual VSIX installation or Extension Development Host.
- Verify post-publication updates and compatibility.

Publication and publisher ownership require an explicit human release decision. Track the detailed human gates in `.ai/HUMAN_GATES.md`.

---

# 削除判断の原則

過去の実験コードは「作ったから残す」のではなく、現在のプロダクト方向に必要かで判断する。

削除しても Git 履歴から復元できるため、以下を優先する。

- 現在の正式経路が一つである
- 同じ責務を複数方式で実装しない
- 今後使う予定のない依存を保持しない
- 実験実装を production path に混ぜない

ただし docx のように現在利用している正式機能は、PPTX 再設計と無関係に削除しない。
