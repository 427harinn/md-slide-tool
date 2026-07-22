# PROJECT_CONTEXT

この内容は、現時点で実際に確認できた範囲だけを記載する。

## プロジェクトの目的

- Quarto ベースの Markdown / スライド / ドキュメントプロジェクトをテンプレートから生成するツール。
- 主な入口は `slidegen` CLI。
- テンプレートから `projects/` 配下に Quarto プロジェクトを作成し、PPTX 向け QMD をレンダリングする補助コマンドを提供している。

## 現在の動作形態

- 現在は VS Code 拡張ではなく、主に `slidegen` CLI として動作している。
- `slidegen preview` は README 上で未実装と記載されている。

## 主な使用技術

- Node.js ES Modules。
- npm。
- Commander による CLI。
- adm-zip による PPTX テンプレート zip/XML 処理。
- Bash によるレンダリング orchestration。
- Python 3 による QMD 前処理と PPTX 後処理。
- Quarto / Pandoc。
- Docker / Dev Container。

## Node.js と npm の推奨バージョン

- README では Node.js 20 系と npm が推奨されている。
- GitHub Actions では Node.js 20 を使用している。
- Dockerfile のベースイメージは `node:20-bullseye`。
- npm の具体的な推奨バージョンは未確認。

## 起動コマンド

```bash
npm install
npm run start -- --help
npm run start -- <command>
node cli/slidegen.js list-templates
node cli/slidegen.js new report --type docx
npm link
slidegen list-templates
```

## レンダリングコマンド

```bash
npm run start -- render projects/selfintroduction/selfintroduction_pptx.qmd
bash scripts/render-current.sh projects/selfintroduction/selfintroduction_pptx.qmd
node scripts/normalize-pptx-template.js projects/selfintroduction/template.pptx
```

Docker での例:

```bash
docker build -t md-slide-tool .
docker run --rm -v "$(pwd):/work" -w /work md-slide-tool npm run start -- render projects/selfintroduction/selfintroduction_pptx.qmd
```

Mermaid fixture の Docker 確認例:

```bash
docker run --rm -v "$(pwd):/work" -w /work md-slide-tool quarto render tests/fixtures/mermaid-pptx.qmd
```

## ビルド、型チェック、Lint、単体テスト、統合テストのコマンド

- ビルド: 未整備。`package.json` に build script はない。
- 型チェック: 未整備。`package.json` に typecheck script はない。
- Lint: 未整備。`package.json` に lint script はない。
- 単体テスト: npm script は未整備。`tests/test_postprocess_place.py` に Python `unittest` ベースのテストがある。
- 統合テスト: 明示的な npm script は未整備。`scripts/smoke-test.sh` は `npm run start -- --help`、`npm run start -- list-templates`、`npm pack --dry-run` を実行する。

確認できた実行候補:

```bash
python3 -m unittest tests/test_postprocess_place.py
bash scripts/smoke-test.sh
```

## 外部実行環境との関係

- Quarto は PPTX 向け QMD のレンダリングに使われる。
- Bash は `scripts/render-current.sh` と `scripts/smoke-test.sh` で使われる。
- Python 3 は `scripts/prepare-qmd-for-pptx.py` と `scripts/postprocess-pptx.py` で使われる。
- `scripts/postprocess-pptx.py` は `python-pptx` と Pillow を使う。
- Dockerfile は Quarto 1.9.36、Chrome Headless Shell、Pandoc、OpenJDK 17、Noto CJK fonts、Python 3、`python-pptx`、Pillow を含める。
- `compose.yml` は空で、README でも未設定と記載されている。

## Windows と macOS における既知の実行条件

- Windows では Git Bash または Dev Container / Docker 環境での利用が README で推奨されている。
- macOS 固有の実行条件は未確認。

## 主なディレクトリ

- `cli/`: `slidegen` CLI。
- `scripts/`: レンダリング・補助スクリプト。
- `templates/`: `docx`、`html`、`pptx` テンプレート。
- `projects/`: 生成済みまたはサンプルプロジェクト。
- `tests/`: Python unittest と fixture。
- `.github/workflows/`: CI workflow。
- `.vscode/`: VS Code tasks。
- `.devcontainer/`: Dev Container 設定。

## 既存の設計上の慣例

- `slidegen new` は `templates/<type>/<template>/` から `projects/<project-name>/` を作成する。
- テンプレートディレクトリ内の `.qmd` は 1 ファイルだけである必要がある。
- 生成 QMD 名は `<project-name>_<type>.qmd`。
- `.qmd` 内の `{{TITLE}}` はプロジェクト名に置換される。
- `.qmd` 以外のテンプレート補助ファイルは生成先へコピーされる。
- `slidegen render` の正式対象は現時点で PPTX 向け QMD。
- PPTX レンダリングは一時 `.render.qmd` と `.images.json` を作成し、Quarto render 後に PPTX 画像後処理を行い、一時ファイルを削除する。

## GitHub Actions の内容

- `.github/workflows/ci.yml` が存在する。
- `pull_request` と `main` ブランチへの `push` で実行される。
- Ubuntu latest、Node.js 20、npm cache を使用する。
- `npm ci` 後に `bash scripts/smoke-test.sh` を実行する。

## VS Code 関連設定の現状

- `.vscode/tasks.json` が存在する。
- `Slidegen New` タスクは `slidegen new` を実行する。
- `Quarto Build` タスクは `bash scripts/render-current.sh "${file}"` を実行する。
- `.devcontainer/devcontainer.json` は Dockerfile を使って `/work` を workspace にし、`npm install`、`npm link`、completion 読み込みを行う。
- Dev Container 推奨拡張は Quarto、Markdown All in One、Trigger Task on Save、tasks-shell-input。

## E2E 環境の有無

- GUI プロジェクト向けの E2E 環境は確認できない。
- Playwright、Cypress 等の E2E テスト設定は確認できない。
- 現状は主に CLI であり、今回は E2E 環境を新規導入していない。

## 現時点で不明な点

- macOS 固有の検証済み手順。
- npm の具体的な推奨バージョン。
- Quarto や Python 依存をローカルに直接インストールする場合の標準手順。
- docx/html/pdf レンダリングの今後の方針。
- VS Code 拡張、Webview、PPTX プレビュー等の将来仕様。
- GUI/E2E テストを導入する場合の対象範囲と採用ツール。
