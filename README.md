# md-slide-tool

Quarto ベースの Markdown / スライド / ドキュメントプロジェクトを、テンプレートから生成するためのツールです。

主な入口は `slidegen` CLI です。現在の実装では、テンプレートから `projects/` 配下に Quarto プロジェクトを作成し、PPTX 向け QMD をレンダリングするための補助コマンドを提供しています。

## できること / できないこと

現在できること:

- `templates/` 配下のテンプレートからプロジェクトを作成する
- `pptx` / `docx` / `html` テンプレートを使って `.qmd` を生成する
- テンプレート内の `{{TITLE}}` をプロジェクト名で置き換える
- `.qmd` 以外のテンプレート補助ファイルを生成先へコピーする
- PPTX 向け QMD を `slidegen render` でレンダリングする
- Docker 環境で Quarto、Pandoc、Chrome Headless Shell、Python ベースの PPTX 後処理を使う

現在できないこと:

- `pdf` テンプレートからのプロジェクト生成
- `docx` / `html` / `pdf` の `slidegen render` による CLI レンダリング
- `slidegen preview`

## ディレクトリ構成

```text
.
├── cli/                  # slidegen CLI
├── completions/          # shell completion
├── scripts/              # レンダリング・補助スクリプト
├── templates/            # 出力形式ごとのテンプレート
│   ├── docx/
│   ├── html/
│   └── pptx/
└── projects/             # 生成済みまたはサンプルプロジェクト
```

## セットアップ

CLI の利用には Node.js 20 系と npm を推奨します。

```bash
npm install
```

ヘルプを確認します。

```bash
npm run start -- --help
```

## クイックスタート

このリポジトリ内では、主に次の形で `slidegen` を実行します。

```bash
npm run start -- <command>
```

例:

```bash
npm run start -- list-templates
npm run start -- new monthly-report --type pptx
npm run start -- render projects/monthly-report/monthly-report_pptx.qmd
```

直接実行することもできます。

```bash
node cli/slidegen.js list-templates
node cli/slidegen.js new report --type docx
```

`npm link` した場合は、`slidegen` コマンドとして実行できます。

```bash
npm link
slidegen list-templates
slidegen new demo --type pptx
```

## コマンド一覧

現在の CLI コマンドは次の 3 つです。

- `slidegen list-templates`
- `slidegen new`
- `slidegen render`

```bash
slidegen --help
slidegen new --help
slidegen render --help
```

### slidegen list-templates

利用可能なテンプレートを `templates/` 配下から走査して表示します。

```bash
slidegen list-templates
```

現在のテンプレート:

- `docx/template`
- `html/template`
- `pptx/template`
- `pptx/self_introduction`

### slidegen new

テンプレートから新しいプロジェクトを `projects/<project-name>/` 配下に作成します。

```bash
slidegen new <project-name> --type <type> [--template <template>]
```

例:

```bash
slidegen new sample --type pptx
slidegen new selfintroduction --type pptx --template self_introduction
slidegen new report --type docx
slidegen new webdoc --type html
```

`--type` は必須です。現在使える値は、実体として `templates/` に存在する次の 3 つです。

- `pptx`
- `docx`
- `html`

`--template` は省略可能で、未指定時は `template` が使われます。

たとえば次のコマンド:

```bash
slidegen new meeting --type pptx
```

は `templates/pptx/template/` を元に、次のような構成を作ります。

```text
projects/meeting/
├── README.md
├── img/
├── meeting_pptx.qmd
└── template.pptx
```

`slidegen new` が行うこと:

1. `templates/<type>/<template>/` を探す
2. 生成先として `projects/<project-name>/` と `img/` を作る
3. テンプレート内の唯一の `.qmd` を `<project-name>_<type>.qmd` として生成する
4. `.qmd` 内の `{{TITLE}}` をプロジェクト名に置き換える
5. `.qmd` 以外のテンプレートファイルをそのままコピーする
6. 最後に `code <qmd-file>` で VS Code を開こうとする

補足:

- `code` コマンドが使えない環境では、自動オープンだけ失敗する可能性があります。
- 生成先の `.qmd` がすでに存在する場合は、上書きせず終了します。
- テンプレートディレクトリ内の `.qmd` は 1 ファイルだけである必要があります。

### slidegen render

PPTX 向け QMD をレンダリングするための正式な CLI 入口です。

```bash
slidegen render <file.qmd>
slidegen render projects/selfintroduction/selfintroduction_pptx.qmd
```

現時点で `slidegen render` の正式対象は PPTX 向け QMD です。`docx` / `html` / `pdf` の CLI レンダリングは未対応です。

通常は低レベルスクリプトを直接実行せず、`slidegen render` を使用してください。内部では `scripts/render-current.sh` を呼び出します。

Advanced:

```bash
bash scripts/render-current.sh projects/selfintroduction/selfintroduction_pptx.qmd
```

内部では主に次の処理を行います。

1. 入力 `.qmd` をレンダリング用の一時 `.render.qmd` に変換する
2. 単独行の Markdown 画像を抽出し、後処理用の `.images.json` を作る
3. PPTX テンプレートがあれば `scripts/normalize-pptx-template.js` でレイアウト名を正規化する
4. `quarto render` を実行する
5. 生成された PPTX に抽出済み画像を後処理で追加する
6. 一時ファイルを削除する

実行には Bash、Quarto、Node.js、Python 3、`python-pptx`、Pillow などが必要です。Windows では Git Bash または Dev Container / Docker 環境での利用を推奨します。

## 対応状況

| 項目 | 現在の対応 |
| --- | --- |
| Project generation | `pptx` / `docx` / `html` |
| CLI render | PPTX 向け QMD のみ |
| `pdf` | テンプレート未同梱、現時点では未対応 |
| `slidegen preview` | 未実装 |

## PPTX テンプレート正規化

PowerPoint テンプレートのスライドレイアウト名が日本語だと、Quarto / Pandoc 側で期待する英語名と一致せず、出力が崩れることがあります。

`scripts/normalize-pptx-template.js` は `.pptx` を zip として開き、代表的なレイアウト名を英語へ置換します。

例:

- `タイトル スライド` -> `Title Slide`
- `タイトルとコンテンツ` -> `Title and Content`
- `セクション見出し` -> `Section Header`
- `空白` -> `Blank`

PowerPoint テンプレート単体を正規化したい場合:

```bash
node scripts/normalize-pptx-template.js projects/selfintroduction/template.pptx
```

## Docker での利用

まずイメージをビルドします。

```bash
docker build -t md-slide-tool .
```

Docker image には主に次が含まれます。

- Quarto 1.9.36
- Chrome Headless Shell
- Pandoc
- OpenJDK 17
- Noto CJK fonts
- Python 3
- `python-pptx`
- Pillow

リポジトリを `/work` にマウントしてレンダリングします。

```bash
docker run --rm \
  -v "$(pwd):/work" \
  -w /work \
  md-slide-tool \
  slidegen render projects/selfintroduction/selfintroduction_pptx.qmd
```

`slidegen render` はインストール先の `scripts/render-current.sh` を解決して呼び出します。対象 QMD と関連ファイルをコンテナから参照できるようにマウントしてください。

## Mermaid / Chrome Headless Shell

Docker 環境では Chrome Headless Shell が入っているため、Mermaid 入り QMD の PPTX レンダリングを扱えます。

確認用 fixture を使う場合:

```bash
docker run --rm \
  -v "$(pwd):/work" \
  -w /work \
  md-slide-tool \
  quarto render tests/fixtures/mermaid-pptx.qmd
```

ローカルで同等のレンダリングを行う場合は、Quarto や Chrome Headless Shell などを別途用意する必要があります。

## テンプレート追加方法

新しいテンプレートは `templates/<type>/<template-name>/` に配置します。

ルール:

- テンプレートディレクトリ内の `.qmd` は 1 ファイルだけ
- `.qmd` 以外のファイルはそのまま生成先プロジェクトへコピー
- デフォルトテンプレート名は `template`

例:

```text
templates/pptx/my_template/
├── my_template.qmd
└── template.pptx
```

## npm package に含まれるもの

`package.json` の `files` 設定により、npm package には主に次が含まれます。

- CLI
- templates
- scripts
- completions
- README.md
- package.json

`projects/` や生成済みの `pptx` / `docx` / `html` / `pdf` などの成果物は、配布対象ではありません。

## サンプル

既存のサンプルプロジェクト:

- `projects/sample`
- `projects/selfintroduction`

それぞれ `.qmd` と出力済みファイルの例が含まれています。

## 既知の注意点

- `html/template/template.qmd` は `style.css` を参照していますが、現時点でテンプレート内に `style.css` は含まれていません。
- `compose.yml` は現時点では未設定です。
- Dockerfile 内の Quarto インストールは 1.9.36 に固定されています。
- PPTX 画像処理では `place` 属性が抽出されますが、配置制御としてはまだ限定的です。

## ライセンス

必要に応じて追記してください。
