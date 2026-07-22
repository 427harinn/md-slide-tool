# TASKS

## タスク一覧

### T-001: 既存構成の限定調査と拡張設計

**目的**
既存CLIへ不要な影響を与えず、VS Code拡張を追加できる構成を確定する。

**実装内容**
AGENTS.mdと.ai配下、ルートpackage.json、.gitignore、.vscode、CI、READMEを必要最小限確認し、vscode-extension/独立構成、PDF.js worker配置、LibreOffice検出候補、実装予定ファイル、テスト方針を確定する。

**変更対象候補**
.ai/PROJECT_CONTEXT.md、.ai/MILESTONE.md、.ai/TASKS.md

**完了条件**
拡張構成、ビルド方法、PDF.js worker配布方法、Windows/macOS LibreOffice検出方法が決定し、停止条件に該当しない。

**実行するテスト**
なし。調査結果と既存構成の整合性をセルフレビューする。

**GUI確認**
なし

**状態**
完了

---

### T-002: VS Code拡張の最小基盤を追加

**目的**
PPTXプレビュー機能を実装できる最小限のVS Code拡張基盤を作る。

**実装内容**
vscode-extension/、package.json、Open PPTX Previewコマンド、.pptxコンテキストメニュー、activation、開発ビルド/ウォッチ、Extension Development Host起動構成を追加する。UIフレームワークは導入しない。

**変更対象候補**
vscode-extension/package.json、src、.vscode、.gitignore、README

**完了条件**
拡張がビルドでき、コマンド/右クリック登録があり、仮または実Webview/通知を表示でき、既存CLIを壊さない。

**実行するテスト**
拡張ビルド、manifest検証、bash scripts/smoke-test.sh

**GUI確認**
コマンドパレット表示、PPTXコンテキストメニュー表示、コマンド実行、スクリーンショット保存

**状態**
完了

---

### T-003: PPTX対象選択と入力検証を実装

**目的**
プレビュー対象PPTXを安全かつ一貫して決定する。

**実装内容**
URI、現在選択中ファイル、ファイル選択ダイアログ順の選択、非PPTX/不存在拒否、空白・日本語パス、キャンセル、利用者向けエラー、VS Code API依存と検証分離を実装する。

**状態**
完了

---

### T-004: LibreOffice検出処理を実装

**目的**
Windows/macOSでLibreOfficeを検出し未導入案内を表示できるようにする。

**実装内容**
PATH、Windows標準候補、macOS標準候補、OS判定、存在/実行可能性確認、検出結果再利用、未検出案内を実装し、自動インストールは行わない。

**状態**
完了

---

### T-005: PPTXからPDFへの変換サービスを実装

**目的**
完成済みPPTXをLibreOfficeでPDFへ安全に変換する。

**実装内容**
VS Code非依存の変換、一時ディレクトリ、headless実行、shell非依存、stdout/stderr/終了コード、PDF存在確認、キャンセル、後始末、利用者向けエラーとログ詳細分離を実装する。

**状態**
完了

---

### T-006: WebviewプレビューUIとPDF描画を実装

**目的**
変換済みPDFをVS Code Webviewでスライド順に表示する。

**実装内容**
Webview管理、CSP、ローカルPDF.js、worker読込、PDFページ順Canvas描画、ファイル名/番号/更新ボタン、レスポンシブ縮小、HTMLエスケープ、localResourceRoots制限、破棄時解放を実装する。

**状態**
完了

---

### T-007: 更新・処理中・エラー状態を実装

**目的**
同じPPTXを安全に再変換し、状態と失敗理由を確認できるようにする。

**実装内容**
更新要求、再変換、処理中表示、更新ボタン無効化、重複防止、ページ置換、主要エラー区別、Output Channelログ、破棄時キャンセルを実装する。

**状態**
完了

---

### T-008: 拡張テスト・回帰テスト・文書を整備

**目的**
プレビュー機能と既存CLI品質を確認し利用方法を文書化する。

**実装内容**
単体テスト、Extension Host smoke testまたは代替記録、ビルド/テストコマンド、README、PROJECT_CONTEXT更新、不要生成物確認を行う。

**状態**
完了

---

### T-009: 最終セルフレビューとPR作成

**目的**
完了条件を確認しPRを作成する。

**実装内容**
MILESTONE完了条件、REVIEW_CHECKLIST、変更範囲、依存/ライセンス、外部通信なし、生成物/秘密情報なし、全テスト、GUI資料、PR、完了レポートを行う。

**状態**
完了
