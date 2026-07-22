# DEBUG_SCENARIOS

## CLI が起動しない

確認候補:

```bash
node --version
npm --version
npm install
npm run start -- --help
node cli/slidegen.js --help
```

見る場所:

- `package.json`
- `cli/slidegen.js`
- `package-lock.json`

## テンプレート一覧や生成が失敗する

確認候補:

```bash
npm run start -- list-templates
npm run start -- new sample --type pptx
```

見る場所:

- `cli/slidegen.js`
- `templates/`
- `projects/`

注意:

- 既存プロジェクト名を使うと、既存 QMD 保護により失敗する場合がある。
- `code` コマンドがない環境では、VS Code の自動オープンだけ失敗する可能性がある。

## PPTX レンダリングが失敗する

確認候補:

```bash
npm run start -- render projects/selfintroduction/selfintroduction_pptx.qmd
bash scripts/render-current.sh projects/selfintroduction/selfintroduction_pptx.qmd
quarto --version
python3 --version
```

見る場所:

- `scripts/render-current.sh`
- `scripts/prepare-qmd-for-pptx.py`
- `scripts/postprocess-pptx.py`
- `scripts/normalize-pptx-template.js`
- 対象 `.qmd`
- 対象 `template.pptx`

注意:

- Quarto、Bash、Python 3、`python-pptx`、Pillow が必要。
- Windows では Git Bash または Dev Container / Docker 環境が推奨されている。

## Docker / Dev Container で失敗する

確認候補:

```bash
docker build -t md-slide-tool .
docker run --rm -v "$(pwd):/work" -w /work md-slide-tool npm run start -- --help
```

見る場所:

- `Dockerfile`
- `compose.yml`
- `.devcontainer/devcontainer.json`

注意:

- `compose.yml` は現時点で空。
- Dockerfile は Quarto 1.9.36 をインストールする。

## CI の smoke test が失敗する

確認候補:

```bash
bash scripts/smoke-test.sh
npm pack --dry-run
```

見る場所:

- `.github/workflows/ci.yml`
- `scripts/smoke-test.sh`
- `package.json`

## GUI/E2E の確認

現状:

- GUI プロジェクト向け E2E 環境は未確認または未整備。
- Playwright、Cypress 等の設定は確認できない。

注意:

- E2E ツールを勝手に導入しない。
- 導入前に対象画面、検証観点、CI 実行方針を決める。
