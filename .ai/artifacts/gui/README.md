# GUI確認資料

この実行環境にはDocker CLI、VS Code GUI、LibreOffice、Quartoがなく、Windows/macOSホスト上のDev Container Extension Development Hostを起動できませんでした。そのためGUIスクリーンショットは保存していません。

代替確認:

- `vscode-extension/package.json`のコマンドパレット登録とExplorer `.pptx`コンテキストメニュー登録を静的確認。
- Webview HTML/JS/CSSのCSP、外部CDN不使用、更新メッセージ処理、`renderComplete`/`renderFailed`通知を単体テストで確認。
- LibreOffice検出、変換失敗、PDF未生成などはモックテストで確認。
- Dev Container前提では変換処理が共通コンテナ内で動作する設計に修正済み。

未検証:

- Windowsホスト上のDev Container Extension Development Host操作。
- macOSホスト上のDev Container Extension Development Host操作。
- 実LibreOfficeと実`pdfjs-dist`を使用したPPTX表示スクリーンショット。
- コマンドパレット、PPTX右クリック、複数スライド成功表示、処理中表示、エラー表示のスクリーンショット。
- `docker build` / Dev Container rebuild（この環境では`docker`コマンドなし）。
