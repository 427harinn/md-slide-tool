# REVIEW_CHECKLIST

## 共通レビュー

- 依頼範囲外の機能実装、リファクタリング、依存追加、設定変更がないか。
- README、CLI、scripts、tests、CI、Dev Container、VS Code 設定の整合性を壊していないか。
- 確認済み事実と未確認事項を区別しているか。
- 生成物やバイナリを意図せず変更していないか。

## CLI 変更時

- `slidegen --help` の表示と README の説明が矛盾していないか。
- `slidegen new` のテンプレート探索、QMD 生成、`{{TITLE}}` 置換、既存ファイル保護を壊していないか。
- `slidegen render` の対象が PPTX 向け QMD である現状と矛盾していないか。

## レンダリング処理変更時

- 一時 `.render.qmd`、`.images.json`、中間 PPTX の扱いを確認したか。
- Quarto、Bash、Python、Node.js の外部依存を明記したか。
- PPTX テンプレート正規化と画像後処理の順序を壊していないか。

## テスト・CI

- 既存の `scripts/smoke-test.sh` と Python unittest の関係を確認したか。
- 新しいテスト環境を勝手に導入していないか。
- GUI/E2E が未整備の場合、未整備として報告しているか。

## GUI / VS Code 関連

- 現状が VS Code 拡張ではなく CLI 中心であることを前提にしているか。
- Webview、プレビュー、変換処理、LibreOffice 連携を未確定仕様として扱っているか。
- GUI 表示を変更した場合、可能な範囲でスクリーンショット確認を行ったか。
