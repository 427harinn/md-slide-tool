# MILESTONE

## マイルストーン名

VS Code PPTXプレビューMVP

## 背景

md-slide-toolはQuartoベースのQMDからPPTXを生成できるが、VS Code拡張、Webview、PPTXプレビュー機能は未実装。外部アプリを開かずVS Code内で完成済みPPTXを確認する機能を追加する。

## 目的

完成済みの`.pptx`をVS Code内の別タブでスライド順にプレビューできるようにする。既存CLIとPPTX生成処理を維持し、変換処理とVS Code固有UIを分離する。

## 確定仕様

- 対象環境はWindows/macOSのVS Codeローカル環境。LibreOfficeが必要。Linuxは正式対象外。
- 完成済み`.pptx`を対象とし、QMD自動レンダリングや`slidegen render`連携は行わない。
- `Open PPTX Preview`をコマンドパレットと`.pptx`コンテキストメニューから実行する。
- 対象決定順はURI引数、現在選択中`.pptx`、ファイル選択ダイアログ。
- PPTX検証、LibreOffice検出、一時ディレクトリ作成、headless PDF変換、Webview安全読み込み、PDF.js Canvas描画、全スライド縦一覧表示を行う。
- PDF.jsはローカルにバンドルし、外部CDNは使わない。
- Webviewにはファイル名、スライド番号、全スライド縦一覧、更新ボタン、処理中表示、エラー表示を表示する。
- 更新ボタンは同じPPTXを再変換し、処理中は重複実行を防ぐ。
- LibreOffice検出はWindows/macOS代表パスとPATHを確認し、未検出時はインストールとVS Code再起動/再実行を案内する。自動インストールはしない。
- ファイル不存在、非PPTX、LibreOffice未検出/起動失敗、変換失敗、PDF未生成、PDF読み込み/描画失敗、更新中削除、破棄/キャンセルを区別する。
- 一時ファイルは処理単位でOS一時ディレクトリ配下へ作り、更新完了後またはWebview破棄時に削除する。元PPTXは変更しない。
- CSP、HTMLエスケープ、localResourceRoots制限、引数配列実行、`shell: true`非依存、外部送信なしを守る。
- VS Code拡張は原則`vscode-extension/`に独立追加し、LibreOffice検出、変換、一時管理、Webview管理、UI、PDF描画を分離する。
- 依存関係は最小限にし、UIフレームワークは導入しない。

## 完了条件

Windows/macOS向けLibreOffice検出、コマンドパレット/右クリック起動、LibreOffice PDF変換、全スライド順序表示、スライド番号、更新、重複防止、未導入案内、変換失敗表示、一時ファイル削除、元PPTX非変更、既存`slidegen new`/`render`/画像配置回帰なし、自動テスト、既存テストとsmoke成功、GUI主要状態の確認資料、README更新が完了している。

## 対象外

QMD保存時自動レンダリング、`slidegen render`自動連携、リアルタイムプレビュー、ファイル監視、編集、画像配置変更、サムネイルグリッド、拡大モーダル、ズーム、PDF/PNGエクスポート、複数比較、Linux正式対応、LibreOffice自動インストール、外部ブラウザ版、クラウド保存、GitHubリポジトリ作成、認証/共同編集、Marketplace公開。

## 影響範囲

新規VS Code拡張ディレクトリ、拡張package設定、LibreOffice検出・実行、PDF.js Webview、一時ファイル管理、拡張テスト、README、`.ai/PROJECT_CONTEXT.md`、必要最小限のルート開発設定。既存CLI、既存レンダリング、テンプレート、生成済みプロジェクトは原則変更しない。

## 今回固有の注意事項

完成済みPPTX表示に集中し、QMDレンダリング統合は追加しない。Windows/macOS検出を分離してテストする。未実機検証OSは成功報告せず、モックテスト結果と未検証事項をPRへ明記する。PDF.js workerをパッケージ対象に含め、PPTX/PDF等の生成物を不要にGitへ追加しない。

## 今回固有の停止条件

有料ソフト/APIが必要、LibreOfficeでは目的を満たせず別Office製品が必須、PPTX/PDF内容を外部送信する必要、既存CLI公開IF破壊が必要、拡張独立構成にできず既存npm配布を大幅変更する必要、PDF.jsでは要件を満たせず新ネイティブ依存が必須の場合は停止する。

## 状態

完了（実機GUI検証は環境制約により未実施）
