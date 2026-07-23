# MILESTONE

## マイルストーン名

Dev Container版 VS Code PPTXプレビューMVP

## 背景

md-slide-toolはDocker / Dev ContainerでQuarto、Pandoc、Python、フォントを揃えて利用する構成を持つ。PPTXプレビューもホストOSへNode.js、LibreOffice、pdfjs-distを直接導入するのではなく、WindowsまたはmacOS上のVS CodeからDev Container内で実行する前提へ修正する。

## 目的

完成済み`.pptx`を、Dev Containerで動作するVS Code拡張からLibreOffice headless変換し、VS Code Webviewでスライド順にプレビューできるようにする。既存CLIとレンダリング処理を壊さず、Webview、PDF.js描画、更新処理、変換サービス、一時ファイル管理、入力検証の既存実装はDev Container前提で利用できる範囲を残す。

## 確定仕様

- ホストOSはWindowsまたはmacOS。
- 実際の実行環境はVS Code Dev Container。
- VS Code拡張はDev Containerのワークスペース側で利用する。
- ホスト側へのNode.js、LibreOffice、pdfjs-dist、npm installは要求しない。
- LibreOfficeはコンテナ内へインストールする。
- PPTXからPDFへの変換はコンテナ内で行う。
- Windows/macOS固有のLibreOfficeパス探索は今回の対象外。
- LibreOffice検出はコンテナ内PATH上の`libreoffice`、次に`soffice`を使用する。
- コンテナ内でLibreOfficeが見つからない場合は、Dev Containerイメージが正しくビルドされていないことを示す。
- ホストOS差異はDocker / Dev Containerの起動とファイルマウントに限定する。
- 完成済み`.pptx`を対象とし、QMD自動レンダリングや`slidegen render`自動連携は行わない。
- PDF.jsはDev Container内の`vscode-extension/node_modules`へインストールし、ビルド時に実ファイルをWebview用ディレクトリへコピーする。
- placeholder PDF.jsファイルを正式実装として使用しない。
- Webviewは外部CDNを使わず、CSPと`localResourceRoots`を設定する。
- 変換済みPDFはWebviewから許可されたコンテナ内ディレクトリに生成する。
- 更新処理、処理中表示、重複防止、エラー表示、一時ファイル削除を維持する。

## 完了条件

DockerfileにLibreOfficeが追加され、Dev Container作成後にルート依存、`slidegen`リンク、拡張依存、拡張ビルドが利用できる。拡張はコンテナ内PATHの`libreoffice`または`soffice`を検出し、コンテナ内でPPTXをPDFへ変換できる。WebviewでPDF.jsによる全スライド表示、更新、エラー表示が動作する。既存CLI、既存smoke、画像配置後処理が壊れていない。Dev Container内テスト、実PPTX→PDF変換、可能なGUI確認、README/PROJECT_CONTEXT更新、PR報告が完了している。

## 対象外

Windows/macOSネイティブ実行、ホストOSへのLibreOffice導入、ホストOSへのNode.js/npm依存導入、Windows/macOS固有LibreOfficeパス探索、QMD保存時自動レンダリング、`slidegen render`自動連携、リアルタイムプレビュー、ファイル監視、編集、画像配置変更、サムネイルグリッド、拡大モーダル、ズーム、PDF/PNGエクスポート、複数比較、LibreOffice自動ダウンロード、外部変換API、VS Code Marketplace公開。

## 影響範囲

Dockerfile、`.devcontainer/devcontainer.json`、Dev Containerセットアップスクリプト、`vscode-extension/`、LibreOffice検出処理、README、`.ai/PROJECT_CONTEXT.md`、`.ai/MILESTONE.md`、`.ai/TASKS.md`。既存CLI、テンプレート、レンダリングスクリプトは原則変更しない。

## 今回固有の注意事項

Dev Container前提へ修正し、既存実装のうち利用可能なWebview、PDF.js描画、更新処理、変換サービス、一時ファイル管理、入力検証は残す。全面的な作り直しや無関係なリファクタリングは行わない。テスト用PPTX/PDFやスクリーンショットなどの生成物は不要にGitへ追加しない。WindowsまたはmacOSの一方だけでGUI確認できた場合、未確認側を成功済みと報告しない。

## 今回固有の停止条件

有料ソフト/APIが必要、PPTX/PDF内容を外部サービスへ送信する必要、Dev Container前提で既存CLI公開IFを破壊しなければ実装できない、新しいネイティブ依存が必須、既存Docker/Dev Container構成を大幅に壊す必要がある場合は停止する。

## 状態

実装中
