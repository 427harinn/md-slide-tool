# TASKS

## タスク一覧

### T-001: Dev Container前提への仕様更新

**目的**
Windows/macOSネイティブ実行前提をDev Container実行前提へ修正する。

**実装内容**
`.ai/MILESTONE.md`と`.ai/TASKS.md`からネイティブLibreOffice探索前提を削除し、ホストOSはWindows/macOS、実行環境はDev Container、LibreOffice/PDF.js/Node.jsはコンテナ内で利用する方針へ更新する。

**状態**
完了

---

### T-002: DockerfileへLibreOfficeを追加

**目的**
既存のNode.js、Quarto、Pandoc、Python、フォントを維持しつつ、コンテナ内PPTX→PDF変換に必要なLibreOfficeを追加する。

**実装内容**
Debian公式パッケージを優先してLibreOfficeを最小限追加し、aptキャッシュを残さず、日本語フォントとheadless利用を維持する。

**状態**
完了

---

### T-003: Dev Containerセットアップを更新

**目的**
コンテナ作成後にルート依存、`slidegen`リンク、拡張依存、拡張ビルドを利用可能にする。

**実装内容**
長い`postCreateCommand`を再実行可能なセットアップスクリプトへ分離し、既存シェル補完設定を維持する。

**状態**
完了

---

### T-004: LibreOffice検出をコンテナPATH前提へ簡略化

**目的**
Windows/macOS固有パス探索を今回の実行経路から削除し、コンテナ内PATHの`libreoffice`または`soffice`を使う。

**実装内容**
検出順を`libreoffice`、`soffice`に限定し、未検出時はDev Containerイメージ不備として案内する。テストも更新する。

**状態**
完了

---

### T-005: Dev Container前提の拡張・PDF.js・Webviewを確認

**目的**
既存Webview、PDF.js描画、更新処理、変換サービス、一時ファイル管理、入力検証をDev Container前提で維持する。

**実装内容**
`pdfjs-dist`をコンテナ内でインストールし、ビルド時コピーとpackage checkを維持する。Webviewからコンテナ内生成PDFを安全に読める構成を維持する。

**状態**
完了

---

### T-006: READMEとPROJECT_CONTEXT更新

**目的**
Docker / Dev Containerが正式な実行前提であることを文書化する。

**実装内容**
ホスト側Node.js/LibreOffice/npm install不要、必要なホストツール、Dev Container再ビルド、拡張起動、LibreOffice/PDF.jsのコンテナ内導入、ネイティブ実行対象外、既知の制限、実機確認状況を記載する。

**状態**
完了

---

### T-007: Dev Container検証・実変換・GUI確認・PR更新

**目的**
回帰確認、実PPTX→PDF変換、可能なGUI確認、PR報告を行う。

**実装内容**
指定コマンド、既存CLI回帰、Docker/Dev Container確認、実PPTX→PDF変換、GUI主要状態確認、スクリーンショット保存、未確認事項記録、PR更新を行う。

**状態**
完了
