# AGENTS.md

このリポジトリで作業する Codex は、作業開始前に以下を確認してください。

1. `.ai/PROJECT_RULES.md`
2. `.ai/PROJECT_CONTEXT.md`
3. `.ai/MILESTONE.md`
4. `.ai/TASKS.md`
5. `docs/ROADMAP.md`
6. `.ai/REVIEW_CHECKLIST.md`
7. `.ai/AGENT_WORKFLOW.md`
8. `.ai/ACCEPTANCE_CRITERIA.md`
9. `.ai/TEST_PLAN.md`
10. `.ai/HUMAN_GATES.md`

問題発生時は `.ai/DEBUG_SCENARIOS.md` を確認してください。

## Subagent / Gate 運用

- 実際のsubagent機能が利用できる場合、Root / Lead Codex は `.ai/AGENT_WORKFLOW.md` に従って実装・テスト・レビューを独立したAgentへ委譲する。
- ユーザーに複数チャットや複数Agentを手動で作らせない。
- 実装前にAcceptance CriteriaとTest Planを確認する。
- Gateは `PASS / FAIL / UNVERIFIED / HUMAN_REQUIRED` を明確に区別する。
- HUMAN_REQUIRED項目は、AI側で可能な確認を終えた後にまとめてユーザーへ報告する。
- FAILまたはUNVERIFIEDの必須Gateが残る状態で「完了」と報告しない。

## 基本ルール

- `.ai/TASKS.md` を上から順番に実行する。
- 変更は現在のマイルストーンに必要な範囲へ限定する。
- 停止条件に該当しない限り、小タスクごとの承認を求めず進める。
- 各タスク後に関連テストと簡易セルフレビューを行う。
- 不明点や未確認事項を推測で仕様として確定しない。
- 既存の正式機能を「整理のため」という理由だけで削除しない。
- 過去の実験コードは現在の方針に不要なら Git 履歴へ任せ、production tree に残さない。

## 現在の重要な設計判断

- Docker / Dev Container を変換・同期ロジックの中心にする。
- VS Code / PowerPoint は UI と最小限の状態通知に留める。
- QMD と PPTX は差分同期せず、保存された側からもう一方を再生成する方針。
- 文字情報を中間 JSON に永続化しない。
- 将来永続化する JSON は主に画像レイアウト情報を対象とする。
- docx は現在利用中の正式機能であり、削除・縮小しない。
- PowerPoint 系が安定した後、PPTX/QMD を利用した Word 変換機能も検討する。

## レビュー時に特に確認すること

- `slidegen render` の既存動作を壊していないか。
- docx の正式機能を壊していないか。
- Docker/Core にあるべきロジックが VS Code / PowerPoint 側へ漏れていないか。
- マイルストーン外の将来機能を先回り実装していないか。
- 削除したコードに現在利用中の経路が含まれていないか。
- tests / CI で機械的に確認できる事項を AI review だけに任せていないか。

Codex Code Review を使う場合、このセクションを repository-specific review rules として利用してください。

指示が矛盾する場合は、より新しく、現在のマイルストーンに具体的な指示を優先してください。
