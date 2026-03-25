# md-slide-tool

Quarto ベースの Markdown / スライド / ドキュメント生成を補助するツールです。

主役は `slidegen` という CLI で、テンプレートから Quarto プロジェクトを生成するために使います。

このリポジトリには次の 2 つが含まれています。

- `slidegen` CLI: テンプレートから新しいプロジェクトを作成する
- レンダリング補助スクリプト: Quarto を使って `pptx` / `docx` / `html` / `pdf` を出力する

## 特徴

- 出力形式ごとのテンプレートからプロジェクトをすばやく作成
- `{{TITLE}}` をプロジェクト名で置き換えて `.qmd` を生成
- `pptx` は PowerPoint テンプレートファイルも一緒にコピー
- `docx` は Word テンプレートファイルも一緒にコピー
- Docker ベースで Quarto / Pandoc / TinyTeX をまとめて実行可能

## ディレクトリ構成

```text
.
├── cli/                  # slidegen CLI
├── scripts/              # レンダリング・補助スクリプト
├── templates/            # 出力形式ごとのテンプレート
│   ├── docx/
│   ├── html/
│   ├── pdf/
│   └── pptx/
└── projects/             # 生成されたプロジェクト
```

## 動作環境

### CLI を使う場合

- Node.js 20 系推奨
- npm

### レンダリングする場合

ローカルに Quarto と Pandoc を入れてもよいですが、このリポジトリには Dockerfile が含まれているため、基本的には Docker 利用が前提です。

Docker イメージには次が含まれます。

- Quarto CLI
- Pandoc
- TinyTeX
- OpenJDK 17
- 日本語フォント `Noto Sans CJK JP`

## セットアップ

```bash
npm install
```

CLI ヘルプ:

```bash
npm run start -- --help
```

## slidegen の概要

`slidegen` は、`templates/` 配下にあるテンプレートを使って `projects/` 配下へ新しいプロジェクトを作る CLI です。

やっていることはシンプルです。

1. 出力形式とテンプレートを選ぶ
2. `projects/<name>/` を作る
3. テンプレート内の `.qmd` を `projects/<name>/<name>_<type>.qmd` として生成する
4. `{{TITLE}}` をプロジェクト名に置き換える
5. `.qmd` 以外のテンプレートファイルをそのままコピーする
6. 最後に VS Code で生成した `.qmd` を開こうとする

つまり、`slidegen` は「Quarto のひな形を作るところまで」を担当し、実際の出力は Quarto でレンダリングします。

## slidegen の使い方

### 実行方法

このリポジトリでは主に次の形で使います。

```bash
npm run start -- <command>
```

例:

```bash
npm run start -- list-templates
npm run start -- new demo --type pptx
```

直接実行することもできます。

```bash
node cli/slidegen.js list-templates
node cli/slidegen.js new demo --type docx
```

グローバルまたはローカルリンクして `slidegen` コマンドとして使うこともできます。

```bash
npm link
slidegen list-templates
slidegen new demo --type pdf
```

### コマンド一覧

```bash
slidegen --help
slidegen new --help
```

### テンプレート一覧を表示

```bash
slidegen list-templates
```

現状のテンプレート:

- `docx/template`
- `html/template`
- `pdf/template`
- `pptx/template`
- `pptx/self_introduction`

このコマンドは `templates/` 配下を走査して、利用可能な出力形式とテンプレート名を表示します。

### 新しいプロジェクトを作成

```bash
slidegen new <project-name> --type <type> [--template <template>]
```

例:

```bash
slidegen new samplepptx --type pptx
slidegen new selfintroduction --type pptx --template self_introduction
slidegen new report --type docx
```

`--type` は必須です。現状使える値は次の 4 つです。

- `pptx`
- `docx`
- `html`
- `pdf`

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

生成されるもの:

- `projects/<project-name>/README.md`
- `projects/<project-name>/img/`
- `projects/<project-name>/<project-name>_<type>.qmd`
- テンプレートに含まれる補助ファイル
  - 例: `template.pptx`, `template.docx`

補足:

- `.qmd` のタイトルはテンプレート中の `{{TITLE}}` をプロジェクト名に置換して作成されます
- 生成後、CLI は `code <qmd-file>` を実行して VS Code で対象ファイルを開こうとします
- `code` コマンドが使えない環境では、ファイル作成自体は完了しても自動オープンは失敗する可能性があります
- 同名の `.qmd` がすでに存在する場合は上書きせず終了します
- `projects/<project-name>/` 自体が存在していても、対象 `.qmd` がなければそのまま利用されます

### よくある作業フロー

最短の流れは次のとおりです。

1. 使えるテンプレートを確認する

```bash
slidegen list-templates
```

2. プロジェクトを作る

```bash
slidegen new monthly-report --type docx
```

3. 生成された `.qmd` を編集する

```text
projects/monthly-report/monthly-report_docx.qmd
```

4. Quarto でレンダリングする

```bash
bash scripts/render-current.sh projects/monthly-report/monthly-report_docx.qmd
```

### エラーになる条件

`slidegen new` は次のような場合に失敗します。

- `templates/` ディレクトリが存在しない
- `--type` で指定した形式が存在しない
- `--template` で指定したテンプレートが存在しない
- テンプレートディレクトリ内に `.qmd` が 0 個
- テンプレートディレクトリ内に `.qmd` が 2 個以上
- 生成先の `.qmd` がすでに存在する

テンプレートの作り方に制約があるので、自作テンプレートを追加する場合は後述の「テンプレート追加方法」を見るのが安全です。

## レンダリング

`scripts/render-current.sh` は指定した `.qmd` を Quarto でレンダリングします。

```bash
bash scripts/render-current.sh projects/samplepptx/samplepptx_pptx.qmd
```

内部で行っていること:

1. 対象 `.qmd` の絶対パスを取得
2. `pptx` を含むファイルの場合は `reference-doc:` を確認
3. テンプレート `.pptx` があれば `scripts/normalize-pptx-template.js` を実行
4. `quarto render <file>` を実行

### PPTX テンプレート正規化について

PowerPoint テンプレートのスライドレイアウト名が日本語だと、Quarto / Pandoc 側で期待する英語名と一致せず崩れることがあります。

`scripts/normalize-pptx-template.js` は `.pptx` を zip として開き、代表的なレイアウト名を次のように英語へ置換します。

- `タイトル スライド` -> `Title Slide`
- `タイトルとコンテンツ` -> `Title and Content`
- `セクション見出し` -> `Section Header`
- `空白` -> `Blank`

PowerPoint テンプレート単体を正規化したい場合:

```bash
node scripts/normalize-pptx-template.js projects/samplepptx/template.pptx
```

## Docker で使う

まずイメージをビルドします。

```bash
docker build -t md-slide-tool .
```

その後、リポジトリを `/work` にマウントしてレンダリングします。

```bash
docker run --rm \
  -v "$(pwd):/work" \
  -w /work \
  md-slide-tool \
  bash scripts/render-current.sh projects/samplepptx/samplepptx_pptx.qmd
```

`render-current.sh` は `/work/scripts/normalize-pptx-template.js` を参照するため、Docker ではこのマウント前提で使うのが安全です。

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

## サンプル

既存のサンプルプロジェクト:

- `projects/samplepptx`
- `projects/selfintroduction`

それぞれ `.qmd` と出力済みファイルの例が含まれています。

## 注意点

- `html/template/template.qmd` は `style.css` を参照していますが、現時点でテンプレート内に CSS は含まれていません
- `compose.yml` は現時点では未設定です
- Dockerfile 内の Quarto インストールは特定バージョン固定です

## ライセンス

必要に応じて追記してください。
