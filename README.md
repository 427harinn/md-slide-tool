# md-slide-tool

Quarto ベースの Markdown / スライド / ドキュメント生成を補助するツールです。

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

## CLI の使い方

### テンプレート一覧を表示

```bash
npm run start -- list-templates
```

現状のテンプレート:

- `docx/template`
- `html/template`
- `pdf/template`
- `pptx/template`
- `pptx/self_introduction`

### 新しいプロジェクトを作成

```bash
npm run start -- new <project-name> --type <type> [--template <template>]
```

例:

```bash
npm run start -- new samplepptx --type pptx
npm run start -- new selfintroduction --type pptx --template self_introduction
npm run start -- new report --type docx
```

生成される内容:

- `projects/<project-name>/README.md`
- `projects/<project-name>/img/`
- `projects/<project-name>/<project-name>_<type>.qmd`
- テンプレートに含まれる補助ファイル
  - 例: `template.pptx`, `template.docx`

補足:

- `.qmd` のタイトルはテンプレート中の `{{TITLE}}` をプロジェクト名に置換して作成されます
- 生成後、CLI は `code <qmd-file>` を実行して VS Code で対象ファイルを開こうとします
- `code` コマンドが使えない環境では、ファイル作成自体は完了しても自動オープンは失敗する可能性があります

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
