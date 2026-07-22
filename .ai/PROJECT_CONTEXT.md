# PROJECT_CONTEXT

このファイルには、このリポジトリで実際に確認できた事実を記録します。

## プロジェクトの目的

- QuartoベースのMarkdown、スライド、ドキュメントプロジェクトをテンプレートから生成するツール。
- 主な入口は`slidegen` CLI。
- テンプレートから`projects/`配下へQuartoプロジェクトを作成する。
- PPTX向けQMDのレンダリングと画像配置の後処理を提供している。

## 現在の動作形態

- 現在はVS Code拡張ではなく、主にCLIとして動作している。
- `.vscode/tasks.json`によるVS Codeタスク連携がある。
- VS Code Webviewや専用プレビュー機能は未実装。
- GUI向けE2E環境は未整備。

## 主な使用技術

- Node.js ES Modules
- npm
- Commander
- adm-zip
- Bash
- Python 3
- python-pptx
- Pillow
- Quarto / Pandoc
- Docker / Dev Container

## 推奨実行環境

- READMEではNode.js 20系が推奨されている。
- GitHub ActionsではNode.js 20を使用している。
- Dockerfileは`node:20-bullseye`を使用している。
- npmの具体的な推奨バージョンは未確認。

## 主なコマンド

### セットアップとCLI

```bash
npm install
npm run start -- --help
npm run start -- <command>
node cli/slidegen.js list-templates
npm link
slidegen list-templates
```

### プロジェクト作成

```bash
npm run start -- new <project-name> --type <type>
```

### PPTXレンダリング

```bash
npm run start -- render <pptx-qmd-path>
bash scripts/render-current.sh <pptx-qmd-path>
```

### 既存テスト

```bash
python3 -m unittest tests/test_postprocess_place.py
bash scripts/smoke-test.sh
```

### Docker

```bash
docker build -t md-slide-tool .
docker run --rm -v "$(pwd):/work" -w /work md-slide-tool npm run start -- --help
```

## テストと静的検査

* ビルド用npm script: 未整備。
* 型チェック用npm script: 未整備。
* Lint用npm script: 未整備。
* JavaScript単体テスト用npm script: 未整備。
* Python unittestとして`tests/test_postprocess_place.py`が存在する。
* `scripts/smoke-test.sh`がCLI help、テンプレート一覧、npm package内容を確認する。
* CIでは`npm ci`後に`scripts/smoke-test.sh`を実行する。
* Playwright、Cypress等のGUI E2E設定は存在しない。

## 外部実行環境

* QuartoはQMDからPPTXを生成する。
* Bashはレンダリングスクリプトとsmoke testで使用される。
* Python 3はQMD前処理とPPTX後処理で使用される。
* PPTX後処理は`python-pptx`とPillowを使用する。
* DockerfileにはQuarto、Pandoc、Chrome Headless Shell、OpenJDK、Python関連パッケージ、フォントが含まれる。
* `compose.yml`は現時点で実質未設定。

## OS別の既知事項

* WindowsではGit Bash、Dev Container、またはDocker環境の利用がREADMEで推奨されている。
* macOS固有の検証済み手順は未確認。

## 主なディレクトリ

* `cli/`: `slidegen` CLI
* `scripts/`: レンダリング、前処理、後処理
* `templates/`: docx、html、pptx用テンプレート
* `projects/`: 生成済みまたはサンプルプロジェクト
* `tests/`: Python unittestとfixture
* `.github/workflows/`: CI
* `.vscode/`: VS Codeタスク
* `.devcontainer/`: Dev Container設定
* `.ai/`: AI駆動開発用のルール、仕様、タスク、レビュー資料

## 既存の設計上の慣例

* `slidegen new`は`templates/<type>/<template>/`から`projects/<project-name>/`を作成する。
* テンプレートディレクトリ内のQMDは1ファイルを前提とする。
* 生成QMD名は`<project-name>_<type>.qmd`。
* QMD内の`{{TITLE}}`をプロジェクト名へ置換する。
* QMD以外のテンプレート補助ファイルも生成先へコピーする。
* `slidegen render`の正式対象は現時点でPPTX向けQMD。
* PPTXレンダリングでは、一時QMDと画像配置用JSONを生成する。
* Quartoレンダリング後にPPTX画像後処理を行う。
* 一時ファイルは処理終了後に削除する。

## GitHub Actions

* `.github/workflows/ci.yml`が存在する。
* Pull Requestと`main`へのpushで実行される。
* Ubuntu環境とNode.js 20を使用する。
* `npm ci`後に`bash scripts/smoke-test.sh`を実行する。

## VS Code関連

* `.vscode/tasks.json`が存在する。
* `Slidegen New`タスクが`slidegen new`を実行する。
* `Quarto Build`タスクが現在のファイルをレンダリングする。
* Dev Container起動時に`npm install`と`npm link`を行う。
* 現時点ではVS Code拡張用のエントリーポイントやWebview実装は存在しない。

## 現時点で不明な点

* macOSでのローカル実行手順の検証状況。
* npmの推奨マイナーバージョン。
* QuartoとPython依存をローカルへ直接導入する標準手順。
* docx、html、pdfレンダリングの今後の方針。
* GUI E2E環境を導入する場合のツールと実行方法。

## VS Code PPTX Preview MVP実装後の確認事項

* `vscode-extension/`に独立したVS Code拡張MVPを追加した。
* 拡張の入口は`vscode-extension/src/extension.js`で、`mdSlideTool.openPptxPreview` / `Open PPTX Preview`を登録する。
* PPTX選択・検証、LibreOffice検出、PPTX to PDF変換、一時ディレクトリ管理、Webview管理、Webview描画を分離した。
* LibreOffice検出はPATH、Windows標準候補、macOS標準候補を確認する。
* PDF描画UIは`vscode-extension/webview/`配下のローカルリソースだけを参照し、外部CDNを使用しない。
* `pdfjs-dist`を拡張の正式依存関係として宣言し、`npm run build`で実ファイルを`webview/`へコピーする。仮PDF.jsファイルが残っている場合は検証スクリプトが失敗する。`package:check`も`npm run build`を先に実行する。
* 一時PDFは`context.globalStorageUri/pptx-preview`配下へ生成し、その固定ディレクトリをWebviewの`localResourceRoots`へ含める。
* WebviewはPDF描画後に`renderComplete`または`renderFailed`を拡張へ返し、拡張側は描画完了まで更新をアイドル状態へ戻さない。
* この環境ではnpm registryへのアクセスが403となったため、`pdfjs-dist`取得、実PDF.jsコピー、Windows/macOS実機GUI検証は未実施。静的検証とモックテストで代替した。
* 確認済みコマンド: `npm test`、`cd vscode-extension && npm test`、`python3 -m unittest tests/test_postprocess_place.py`、`bash scripts/smoke-test.sh`、`npm run start -- --help`、`npm run start -- list-templates`。

## Dev Container前提への修正事項

* PR #10レビューを受け、PPTXプレビューMVPの正式実行経路をWindows/macOSホスト上のVS Code Dev Containerに変更した。
* ホスト側Node.js、LibreOffice、pdfjs-dist、npm installは要求しない。
* DockerfileへDebian公式パッケージのLibreOffice Impressを追加し、コンテナ内PATHの`libreoffice`または`soffice`でPPTX→PDF変換を行う方針にした。
* `.devcontainer/devcontainer.json`の`postCreateCommand`は`/work/scripts/devcontainer-setup.sh`へ分離し、ルート依存、`slidegen`リンク、拡張依存、拡張ビルド、既存補完設定を再実行可能にした。
* VS Code拡張のLibreOffice検出はWindows/macOS固有パスを探索せず、コンテナ内PATHの`libreoffice`、`soffice`に限定した。
* 実GUI確認はこのLinuxコンテナからは未実施。変換処理は共通コンテナ内で行われるが、Windows/macOSホストでのDev Container GUI結果は未確認として扱う。

## 今回の環境制約付き検証結果

* この実行環境では`docker`コマンドが存在しないため、Dev Container rebuild、Dockerfile内LibreOfficeバージョン確認、コンテナ内PPTX→PDF実変換は未実施。
* この実行環境では`quarto`、`libreoffice`、`soffice`がPATHになく、`slidegen render`と実LibreOffice変換は未完了。
* この実行環境ではnpm registryが`pdfjs-dist`取得に403を返すため、拡張の`npm run build`と`npm run package:check`は実PDF.js不足ガードで失敗する。
* 成功確認済み: `npm test`、`cd vscode-extension && npm test`、`python3 -m unittest tests/test_postprocess_place.py`、`bash scripts/smoke-test.sh`、`npm run start -- --help`、`npm run start -- list-templates`、`npm run start -- new pr10-smoke --type pptx`（`code`コマンドなし警告あり、生成物は削除）。
* 未完了確認: `quarto --version`、`libreoffice --version || soffice --version`、Dev Container GUI確認、実PPTX→PDF変換、スクリーンショット保存。

## VS Code拡張起動設定の修正

* `vscode-extension/.vscode/launch.json`は、`vscode-extension`フォルダをワークスペースとして開く前提で`--extensionDevelopmentPath=${workspaceFolder}`を使う。
* Extension Development Hostで開く対象として`/work`をargsへ追加した。
* `vscode-extension/package.json`に`extensionKind: ["workspace"]`を追加し、Dev Containerのワークスペース側で拡張が動作することを明示した。

## Webview CSPとPDF.js source map対応

* 実機確認でPDF fetchとPDF.js workerがCSPに拒否されたため、Webview CSPへ`connect-src ${webview.cspSource}`を追加した。
* `default-src 'none'`、nonce付きscript、`${webview.cspSource}`によるローカルリソース制限、`worker-src ${webview.cspSource} blob:`、外部CDN不使用は維持した。
* `pdf.mjs.map`などsource mapの取得失敗がプレビュー本体へ波及しないよう、ビルド時コピーで`sourceMappingURL`コメントを除去する。
