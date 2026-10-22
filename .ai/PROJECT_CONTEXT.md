# PROJECT_CONTEXT

このファイルには、現在のリポジトリで確認できる事実と、今後の開発で前提にする設計判断を記録する。

## プロジェクトの目的

md-slide-tool は、Quarto ベースの QMD から PowerPoint / Word などの成果物を生成するためのツール。

現在の中心機能:

- template から project を作成
- PPTX 向け QMD を `slidegen render` で build
- PPTX に画像を後処理で配置
- docx project/template を利用
- Docker / Dev Container で実行環境を揃える
- M1: VS Code commandから `slidegen render` を呼び、成功後にhost-side `file:` URIを開く

## 現在の正式機能

### CLI

- `slidegen new`
- `slidegen list-templates`
- `slidegen render`

### PPTX

```text
slidegen render
  -> scripts/render-current.sh
  -> prepare-qmd-for-pptx.py
  -> Quarto / Pandoc
  -> postprocess-pptx.py
  -> final PPTX
```

`postprocess-pptx.py` は python-pptx / Pillow を使い、QMD から抽出した画像を生成済み PPTX に追加する。

現在の画像紐付けは主に slide title を使っている。

### DOCX

docx は現在も利用している正式機能。削除・縮小しない。

PowerPoint 系が安定した後、完成した PPTX/QMD の内容から Word 文書を生成する機能も将来候補とする。

## 削除した実験経路

- VS Code 内 PPTX -> PDF preview と PDF.js Webview は不採用。関連拡張コードと `pdfjs-dist` 依存を削除した。
- Preview 専用だった LibreOffice は Dockerfile から削除した。PPTX build に必要な Quarto / Pandoc / Python / python-pptx / Pillow は維持する。
- `triggerTaskOnSave` による保存時 build は削除した。`.vscode/tasks.json` の `Quarto Build` は手動 task として残す。
- `pptx_autostartup` 等の Auto Preview 実験は main に取り込んでいない。

## 主な技術

- Node.js 20
- Commander / adm-zip
- Bash
- Python 3 / python-pptx / Pillow
- Quarto / Pandoc
- Docker / Dev Container
- VS Code task integration (manual tasks only)

## 今後の設計原則

詳細は `docs/ROADMAP.md` を参照する。

1. Docker / Dev Container を変換・監視・同期ロジックの中心にする
2. VS Code / PowerPoint 側には変換ロジックを持たせない
3. QMD と PPTX は差分同期せず、保存された側からもう一方を再生成する
4. 文字情報を中間 JSON に永続化しない
5. 永続 JSON は主にvisual elementのlayout情報を持ち、文字情報の正本にはしない
6. slide / element に stable id を導入する。M2ではelement type=imageのみ実装する
7. 競合時は自動マージせず conflict QMD を生成して diff を表示する

## 今後のマイルストーン

- M0: Repository Cleanup
- M1: QMD -> PPTX -> Microsoft PowerPoint
- M2: Stable IDs and Image Layout
- M3: PPTX -> QMD Import
- M4: Docker Sync Engine
- M5: Conflict Handling
- M6: PPTX -> Word

## 開発運用

実装は原則 Codex に任せる。

```text
Human -> milestone/tasks
Codex -> implementation/tests/self review/PR
AI review + CI + Human review
Codex -> fixes
Human -> merge
```

詳細は `docs/CODEX_WORKFLOW.md`。

## 現在のテスト / CI

- `python3 -m unittest tests/test_postprocess_place.py`
- `bash scripts/smoke-test.sh`
- GitHub Actions: npm ci -> smoke test

CI smoke test は CLI help、template listing、npm package contents を確認する。Python unittest は PPTX image placement 後処理を確認する。Preview 専用テストは削除した。

## Cleanup 時の注意

- docx を削除しない
- project データを不用意に削除しない
- PPTX image placement の現在動作を壊さない
- 実験コードを削除する前に正式経路から参照されていないことを確認する
- cleanup と次マイルストーンの新機能を同一 PR に混ぜない
- `projects/` 配下の既存データは、個別に対象指定されない限り削除しない

## Cleanup後の確認済み状態

- 正式 build 経路は `slidegen render` -> `scripts/render-current.sh` -> QMD前処理 -> Quarto -> PPTX画像後処理。
- `slidegen new` は `pptx` / `docx` / `html` の各 template を生成する。docx は正式機能として維持する。
- VS Code に残る build task は手動実行。保存時自動実行の拡張・設定はない。
- `compose.yml` と追跡済み `.DS_Store` を削除し、`.DS_Store` は Git ignore に追加済み。既存 project コンテンツは変更しない。
- HTML template は残した。現行 template QMD は `style.css` を参照するが、同梱されていない。既存 HTML project の利用状況・修正方針は未確認のため、今回その template は変更していない。
- M1のPowerPoint openは実装済み。M2 stable ID / image assets layoutは本ブランチで実装し、Draft PR検証中。

## M1実装状況

- M0で削除した Preview / PDF.js / Preview専用LibreOffice は復活させない。
- M1 extension はworkspace build packageとlocal UI packageの2つ。build packageはDev Container内で既存 `slidegen render` を実行し、UI packageだけがhost上で `vscode.Uri.file` / `vscode.env.openExternal` を呼ぶ。
- UI と workspace package は `vscode.commands.executeCommand` でQMD URI文字列と小さなJSON結果をやり取りする。Tasks API案は検討したが、remote buildの結果pathを返す追加channelが必要になるため採用しなかった。
- `.devcontainer/devcontainer.json` の `remoteEnv.MD_SLIDE_TOOL_HOST_WORKSPACE` が `${localWorkspaceFolder}` を渡す。
- Dev Container lifecycle hookから `code --install-extension` を呼ぶ方式はWindows実機でCLIがPATHに存在せず失敗したため撤回した。
- Windows実機ではLocal UI packageとRemote Workspace packageを各hostへ手動installし、command表示、cross-host command routing、container build、host path mapping、PowerPoint openを確認済み。手動配置は機能成立の診断用で、M1の完了を妨げない。
- Workspace packageはUI packageを `extensionDependencies` に指定し、UI packageは `api: "none"` を宣言する。Dev Containerのextension ID listはMarketplace形式で、ローカルVSIX pathを指定できない。
- lifecycle hookの `code --install-extension` はWindows実機でCLI不在により失敗し、撤回済み。未公開packageの通常自動配布は未実装。Marketplace公開・publisher設定・自動配置は正式リリース前のRelease / Distribution課題であり、M1完了条件ではない。
- M1 build/openとHost Bridgeは手動diagnostic installでWindows実機PASS。M1の完了条件は既存 `slidegen render` によるDev Container build、Local UI host open、失敗時の正しい挙動、PPTX/docx regression、禁止されたPreview stackを戻さないこと、およびCI PASS。Release / Distributionの将来gateは `docs/ROADMAP.md` と `.ai/HUMAN_GATES.md` を参照。

## Repository Cleanup 検証記録 (2026-10-22)

- `npm test` は 10 件成功。CLI help / template listing、docx template からの一時 project 生成、`npm pack --dry-run` も確認した。
- `scripts/smoke-test.sh` はこの Windows 実行環境から直接起動できなかったため、構成コマンドを個別に確認した。Git Bash と `python3` の WindowsApps shim が実行権限エラーとなる。
- PPTX render 実行は Python 起動時に権限エラーで停止した。Quarto は PATH 上になく、Docker daemon もアクセス拒否のため、実コンテナ / 実PPTX生成は未確認。
- VS Code GUI、Dev Container GUI、PowerPoint 実機は未確認。


## M1開始時点の標準実行環境

ユーザーの標準操作は以下。

```text
Windows
  -> Docker Desktop起動
  -> VS Codeでrepositoryを開く
  -> Dev Containers: Reopen in Container
  -> Dev Container内でslidegen / Quarto / Pythonを実行
  -> PowerPointのみWindows host側で利用
```

M1ではこの経路を第一検証対象にする。

Remote/Dev Containerで外部アプリを開く場合、Workspace Extensionからhostアプリを直接spawnする設計を避ける。VS Code公式ドキュメントでは、ローカルアプリを開く用途に `vscode.env.openExternal` を推奨し、local resourceが必要な処理にはUI extensionを使える。

Dev Containersでは `${localWorkspaceFolder}` を `remoteEnv` 等でcontainerへ渡せるため、`/work` 配下の相対pathとhost workspace pathを組み合わせる方式をPoC候補とする。

詳細は `docs/M1_POWERPOINT_OPEN.md`。


## M2確定設計

詳細は `docs/M2_STABLE_IDS_ASSETS.md`。

- slide identityはQMDの `slide-id`。
- visual element identityはQMDの `element-id`。画像専用の `image-id` は採用しない。
- M2で実装するelement typeは `image` のみ。将来shape等へ拡張できるidentity modelにする。
- IDのない既存QMDには不足IDだけをUUIDベースで自動付与し、既存IDは変更しない。
- duplicate IDは自動修正せずFAIL。
- `<stem>.assets.json` schema v1はslide sizeとimage elementの x/y/width/height をEMU整数で保持する。
- title/body等の文字情報はassetsへ永続化しない。
- render時は saved layout -> existing `place=` preference -> current auto layout の順で配置する。
- auto layout結果もassetsへ保存し、次回renderでは同じlayoutを復元する。
- slide title変更やimage path変更はstable IDが同じならidentity/layoutを維持する。
- generated PPTXにも同じslide/element IDを埋め込み、M3のimportで利用できるようにする。
- PowerPointで同一identified picture shapeの画像内容だけ差し替えた場合は同じelementとして扱える設計にする。削除後に新規挿入されたIDなしshapeは将来M3で新規elementとして扱い、置換だったと推測しない。
- crop / rotation / z-order / shape persistence / PPTX -> QMD importはM2対象外。

## M2実装状況

- Python testsは18件PASS。PPTX metadataのpython-pptx save/reopen、ID/重複検証、assets layout restore/fallback/stale cleanupを含む。
- GitHub Actionsはroot tests、既存smoke、Docker内の2回render/title+path変更/layout維持とdocx render回帰を実行する。
- Windows実行環境ではQuarto / Docker / Bashが使えなかったため、PR #17 head CI run #60で代表render・docx回帰・smokeを実行しPASS。
- PowerPoint desktopで編集・保存後のmetadata保持のみHUMAN_REQUIRED。
