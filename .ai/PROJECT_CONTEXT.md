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
- VS Code extension の `Build and Open in Microsoft PowerPoint` command から既存 render script を実行し、成功後に host bridge で PPTX を開く（M1）

M1 の unit tests と Dev Container build regression は通過。Windows VS Code Remote から `vscode.env.openExternal` が実際の PowerPoint へ配送されるかは Windows GUI 実機で要確認。

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

## 現在存在する実験実装

### VS Code PPTX Preview (legacy)

既存 Preview MVP のコードは repository に残存しているが、M1 workflow では利用しない。

```text
PPTX -> LibreOffice -> PDF -> PDF.js -> VS Code Webview
```

Microsoft PowerPoint 自体を実編集環境として利用する。Preview UI は M1 で使わず、cleanup の別タスクとして扱う。

### Auto Preview

`pptx_autostartup` branch には QMD save -> render -> preview refresh の実験がある。

main へそのまま merge する予定はない。debounce / running / pending / error handling の考え方は将来の Sync Engine の参考にできる。

## 現在の自動 build 経路

Dev Container settings には `triggerTaskOnSave` を利用した QMD save -> `Quarto Build` task の設定がある。

M1 では QMD save の自動 build は有効化しない。`Build and Open in Microsoft PowerPoint` はユーザーが明示的に起動する command。

将来 Docker Sync Engine を導入すると経路が重複するため、Repository Cleanup で整理対象とする。

## 主な技術

- Node.js 20
- Commander / adm-zip
- Bash
- Python 3 / python-pptx / Pillow
- Quarto / Pandoc
- Docker / Dev Container
- VS Code Extension

## 今後の設計原則

詳細は `docs/ROADMAP.md` を参照する。

1. Docker / Dev Container を変換・監視・同期ロジックの中心にする
2. VS Code / PowerPoint 側には変換ロジックを持たせない
3. QMD と PPTX は差分同期せず、保存された側からもう一方を再生成する
4. 文字情報を中間 JSON に永続化しない
5. 将来の永続 JSON は主に画像レイアウト情報を持つ
6. slide / image に stable id を導入する
7. 競合時は自動マージせず conflict QMD を生成して diff を表示する

## 今後のマイルストーン

- M1: QMD -> PPTX -> Microsoft PowerPoint (実装済み、Windows GUI 実機確認待ち)
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
- VS Code extension: `npm --prefix vscode-extension test`

M1 は Docker image 内で smoke、PPTX render、docx regression を確認する。

## Cleanup 時の注意

- docx を削除しない
- project データを不用意に削除しない
- PPTX image placement の現在動作を壊さない
- 実験コードを削除する前に正式経路から参照されていないことを確認する
- cleanup と次マイルストーンの新機能を同一 PR に混ぜない
