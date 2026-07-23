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

## QMD保存時自動PPTXプレビュー調査

* 既存VS Code拡張の入口は`vscode-extension/src/extension.js`で、手動コマンドは`mdSlideTool.openPptxPreview` / `Open PPTX Preview`。
* 既存`PreviewPanel`はPPTX絶対パスをキーに`panels` Mapで同じWebviewを再利用する。既存パネルがある場合は`refresh()`で同じタブを更新する。
* 既存`PreviewPanel`はPPTX→PDF変換、PDF.js Webview描画、一時作業領域、Webview CSP、描画失敗時の古い成功表示維持に使える。
* 現状の`PreviewPanel.open()`は既存パネル表示時に`reveal()`し、新規作成時も右側に作成するため、自動プレビューではフォーカスを戻す制御が必要。
* `slidegen render <file.qmd>`は入力存在、ファイル種別、`.qmd`拡張子を検証し、`bash scripts/render-current.sh <absolute-qmd-path>`を`shell: false`で呼び出す。
* `scripts/render-current.sh`は入力QMDと同じディレクトリへ一時`.${stem}.render.qmd`、`.${stem}.images.json`、`.${stem}.render.pptx`を生成し、最終PPTXを`<stem>.pptx`へコピーする。
* QMDから対応PPTXを決定する既存規則は、QMDの拡張子を`.pptx`へ置き換えた同一ディレクトリのパス。
* Dev Containerセットアップは`scripts/devcontainer-setup.sh`で`npm install`、`npm link`、`vscode-extension`依存導入、拡張ビルドを実行する。現状では通常ワークスペースへの拡張インストールまでは行っていない。
* 自動プレビューの最小設計は、拡張側に1ファイルだけの監視状態を持ち、保存イベントを500msデバウンスし、`slidegen render`を直列実行してから既存`PreviewPanel`を更新する形が既存境界に合う。

## QMD保存時自動PPTXプレビュー実装後の確認事項

* `vscode-extension`に`mdSlideTool.startAutoPreview` / `Start Auto Preview`と`mdSlideTool.stopAutoPreview` / `Stop Auto Preview`を追加した。
* VS Code設定`mdSlideTool.autoPreview.enabled`を追加し、初期値は`true`。無効時は開始せず案内を表示する。
* 自動プレビューは同時に1つのQMDだけを対象にする。同じQMDで再開始しても重複登録せず、別QMDで開始すると対象を切り替える。
* QMD保存イベントは対象ファイルだけを処理し、500msデバウンスする。停止時と破棄時にタイマーを破棄する。
* レンダリングは`node <workspace>/cli/slidegen.js render <qmd>`を`shell: false`の子プロセスで呼び出し、既存の`slidegen render`経路を再利用する。
* レンダリング中の再保存は`pending`フラグで最後の1回だけ保持する。現在の処理完了後、対象が変わっていない場合だけ再実行する。
* `PreviewPanel.open()`に`preserveFocus`オプションを追加し、自動更新時は可能な範囲でQMDエディターのフォーカスを維持する。
* 既存`PreviewPanel`はPPTX絶対パス単位で再利用されるため、同じPPTXの保存更新でタブを増やさない。
* Webview側のPDF描画は、全ページ描画が成功してから既存スライドを差し替えるように変更し、PDF描画失敗時も前回成功表示を維持する。
* Dev Containerセットアップは`npm --prefix /work/vscode-extension run package:vsix`でVSIXを作成し、`code --install-extension /work/vscode-extension/dist/md-slide-tool-pptx-preview.vsix --force`で通常ワークスペースへ導入する。
* `vscode-extension/dist/`と`*.vsix`は生成物としてGit管理対象外にした。

## 今回の環境制約付き検証結果（自動プレビュー）

* 成功確認済み: `cd vscode-extension && npm test`、`cd vscode-extension && npm run build`、`cd vscode-extension && npm run package:vsix`。
* 成功確認済み: `cd vscode-extension && npm run package:check`（Windowsのユーザーnpm cache権限問題を避けるため、`npm_config_cache`をワークスペース内一時ディレクトリへ向けて実行）。
* 成功確認済み: `python -m unittest tests/test_postprocess_place.py`、`npm run start -- --help`、`npm run start -- list-templates`、`npm run start -- new codex-auto-smoke --type pptx`（生成物は削除）。
* 成功確認済み: `npm pack --dry-run`（Windowsのユーザーnpm cache権限問題を避けるため、`npm_config_cache`をワークスペース内一時ディレクトリへ向けて実行）。この確認で`__pycache__`が配布対象へ混入しないよう`package.json`の`files`へ除外指定を追加した。
* 成功確認済み: `C:\Program Files\Git\bin\bash.exe -n scripts/devcontainer-setup.sh`。
* `npm test`（root）は`scripts`上の`python3`がこのWindows環境で起動できず失敗したため、`python -m unittest tests/test_postprocess_place.py`で代替確認した。
* `scripts/smoke-test.sh`はWindowsの`bash`解決がWSLへ流れ、WSLディストリビューション未導入のため失敗した。スクリプト内の`--help`、`list-templates`、`npm pack --dry-run`は個別に成功確認した。
* `slidegen render`は内部で`bash scripts/render-current.sh`を起動するため、このWindows環境ではWSL未導入により失敗した。QuartoもホストPATHになく、実レンダリングは未確認。
* Docker Desktop起動後、承認付き`docker info --format '{{.ServerVersion}}'`でDocker daemon 28.5.1へ接続できた。
* 成功確認済み: `docker build -t md-slide-tool .`。Dockerfile内の`libreoffice --version || soffice --version`は`LibreOffice 7.0.4.2`を返した。
* 成功確認済み: Dockerコンテナ内の`node --version`は`v20.20.2`、`quarto --version`は`1.9.36`、`libreoffice --version`は`LibreOffice 7.0.4.2`。
* 成功確認済み: Dockerコンテナ内で`npm test`、`bash scripts/smoke-test.sh`、`npm run start -- render projects/selfintroduction/selfintroduction_pptx.qmd`。
* 成功確認済み: Dockerコンテナ内で`bash scripts/devcontainer-setup.sh`。ルート依存、`npm link`、拡張依存、拡張ビルド、VSIX作成まで成功した。plain DockerコンテナにはVS Code CLI `code`がないため、`code --install-extension`だけは想定どおりskipされた。
* `@vscode/vsce`は`3.2.2`に固定した。Dev ContainerのNode.js 20でVSIX作成は成功するが、一部の推移依存がNode 22要求の`EBADENGINE`警告を出す。`@vscode/vsce` 2.xでは警告の代わりにaudit脆弱性が増えたため、脆弱性0件の3.2.2固定を採用した。
* この実行環境ではVS Code `code` CLIがPATHになく、通常のWindows/macOS VS Code Dev Container GUIを操作できないため、`/work`ウィンドウでのコマンド表示、手動PPTXプレビュー、QMD保存からの自動更新、スクリーンショット保存は未確認。
