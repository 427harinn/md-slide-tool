# DEBUG_SCENARIOS

問題が発生した場合は、最初にエラーメッセージ、実行コマンド、対象ファイル、OS、利用バージョンを記録してください。

同じ調査を繰り返さず、原因候補を切り分けてください。

## CLIが起動しない

確認:

```bash
node --version
npm --version
npm install
npm run start -- --help
node cli/slidegen.js --help
```

見る場所:

* `package.json`
* `package-lock.json`
* `cli/slidegen.js`

確認事項:

* Node.js 20系か。
* `node_modules`が作成されているか。
* ES Modulesとして読み込まれているか。
* 実行中の作業ディレクトリがリポジトリ直下か。

## テンプレート一覧・プロジェクト生成が失敗する

確認:

```bash
npm run start -- list-templates
npm run start -- new debug-sample --type pptx
```

見る場所:

* `cli/slidegen.js`
* `templates/`
* `projects/`

確認事項:

* 指定した種類とテンプレートが存在するか。
* テンプレート内のQMDが1ファイルか。
* 同名プロジェクトや既存QMDが存在しないか。
* `code`コマンドの失敗とプロジェクト生成自体の失敗を区別する。

## PPTXレンダリングが失敗する

確認:

```bash
npm run start -- render projects/selfintroduction/selfintroduction_pptx.qmd
bash scripts/render-current.sh projects/selfintroduction/selfintroduction_pptx.qmd
quarto --version
python3 --version
```

見る場所:

* `scripts/render-current.sh`
* `scripts/prepare-qmd-for-pptx.py`
* `scripts/postprocess-pptx.py`
* `scripts/normalize-pptx-template.js`
* 対象QMD
* 対象テンプレートPPTX
* 一時QMD
* 画像配置JSON

確認事項:

* Quarto、Python 3、python-pptx、Pillowが利用可能か。
* QMDのfront matterが正しいか。
* テンプレートPPTXが存在するか。
* 一時ファイルが途中状態で残っていないか。
* Quarto生成前の問題か、PPTX後処理の問題かを分ける。

## Docker・Dev Containerで失敗する

確認:

```bash
docker build -t md-slide-tool .
docker run --rm -v "$(pwd):/work" -w /work md-slide-tool npm run start -- --help
```

見る場所:

* `Dockerfile`
* `compose.yml`
* `.devcontainer/devcontainer.json`

確認事項:

* Dockerイメージが正常にビルドされるか。
* ワークスペースが`/work`へマウントされているか。
* コンテナ内でNode.js、Quarto、Pythonが利用可能か。
* ホストとコンテナのパス差異がないか。

## CIのsmoke testが失敗する

確認:

```bash
bash scripts/smoke-test.sh
npm pack --dry-run
```

見る場所:

* `.github/workflows/ci.yml`
* `scripts/smoke-test.sh`
* `package.json`

確認事項:

* ローカルとCIのNode.jsバージョン差異。
* npm packageへ必要ファイルが含まれているか。
* OS依存コマンドをCIで実行していないか。

## VS Code拡張・Webviewが起動しない

確認候補:

* Extension Hostのログ
* VS CodeのDeveloper Toolsコンソール
* コマンド登録
* 拡張機能のactivation条件
* 対象ワークスペースと対象ファイル
* Webview HTML生成処理

保存する情報:

* VS Codeのバージョン
* OS
* 実行したコマンド
* Extension Hostのエラー
* Webviewコンソールエラー
* 失敗時スクリーンショット

## 外部プロセスが失敗する

確認事項:

* 実行ファイルをPATHから検出できるか。
* WindowsとmacOSで実行ファイル名や標準パスが異ならないか。
* `shell: true`へ不要に依存していないか。
* 引数を文字列連結せず、安全に配列で渡しているか。
* パスに空白や日本語が含まれていないか。
* 終了コード、標準出力、標準エラーを取得しているか。
* タイムアウトやキャンセル時に子プロセスが残らないか。

## GUI・E2E確認が失敗する

保存する情報:

* 失敗時スクリーンショット
* Trace
* Extension Hostログ
* Webviewコンソールログ
* 外部プロセスの標準エラー
* テスト結果

注意:

* 読み込みや画面更新が完了してからスクリーンショットを撮る。
* パスワード、トークン、個人情報を画像やログへ残さない。
* E2E環境が未導入の場合は勝手に追加せず、現在のタスクで導入が許可されているか確認する。
