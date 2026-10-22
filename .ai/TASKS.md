# TASKS

## M0: Repository Cleanup

Codex は上から順番に実行する。

### T-001: 現在の正式経路を確定する

- CLI commands の確認
- QMD -> PPTX render path の確認
- docx template/project path の確認
- VS Code task / extension / Dev Container setup の参照関係確認
- preview / auto-preview 実験が正式経路から呼ばれているか確認
- 調査結果を `.ai/PROJECT_CONTEXT.md` へ反映

**状態:** 完了

### T-002: 不採用 Preview 実験を削除する

正式経路から未使用であることを確認してから、PDF.js / Webview / PPTX->PDF Preview / Preview専用extension code・tests・build scripts・依存を整理する。

docx、PPTX render、template 処理は削除しない。

**状態:** 完了

### T-003: Dev Container / 自動 build 経路を整理する

- `triggerTaskOnSave` の利用状況確認
- `.vscode/tasks.json` の役割確認
- `scripts/devcontainer-setup.sh` の不要処理削除
- Preview 専用 LibreOffice が不要になった場合のみ Dockerfile から削除
- 次マイルストーンで Sync Engine を追加しやすい状態へ整理

**状態:** 完了

### T-004: 不要ファイル・古い設定を整理する

- tracked `.DS_Store` 削除と ignore 確認
- 空の `compose.yml` 削除
- 壊れた / 未完成 template 資産があれば利用状況を確認して扱いを決定
- 生成物や fixture を誤って削除しない

**状態:** 完了

### T-005: CLI / render の責務を最小限整理する

- `cli/slidegen.js` の責務確認
- CLI parsing と処理本体が過度に密結合している箇所のみ分離
- `slidegen render` の公開挙動は維持
- Bash/Python/Quarto の全面書き換えはしない
- 将来のためだけの過剰抽象化をしない

**状態:** 完了

### T-006: テストとCIを cleanup 後の正式機能へ合わせる

- PPTX画像後処理テスト
- CLI smoke
- template listing
- docx template が残っていること
- 削除した preview 用 test の整理
- 必要最小限の regression test 追加

**状態:** 完了

### T-007: ドキュメントを現在状態へ更新する

README / PROJECT_CONTEXT / 必要なDEBUG_SCENARIOS を更新し、過去マイルストーンの結果を現在仕様のように残さない。

**状態:** 完了

### T-008: 最終セルフレビューとPR作成

- 全テスト実行
- `.ai/REVIEW_CHECKLIST.md` に沿ってレビュー
- docx が維持されていることを確認
- PPTX render の回帰確認
- 削除内容と理由を PR に記載
- PowerPoint 自動起動を先回り実装していないことを確認

**状態:** 完了（実コンテナ・GUI検証は環境制約により未確認）
