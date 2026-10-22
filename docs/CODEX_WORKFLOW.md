# Codex Development Workflow

## 基本運用

このリポジトリの実装は原則 Codex に任せる。

人間の役割は主に以下。

1. 目的とマイルストーンを決める
2. Codex が作成した PR をレビューする
3. GUI / PowerPoint など実環境が必要な項目を確認する
4. 仕様判断が必要な場合だけ判断する
5. 問題なければ merge する

Codex は `AGENTS.md` から参照される `.ai/` 文書を実装の基準にする。

## 開発フロー

```text
Human
  -> MILESTONE / TASKS を確定

Codex
  -> branch
  -> implementation
  -> tests
  -> self review
  -> PR

Automated review
  -> Codex Code Review / CI

Human + ChatGPT
  -> PR review
  -> 必要なら修正依頼

Codex
  -> same PR に修正

Human
  -> merge
```

## Codex が実装開始前に読むもの

必須:

- `AGENTS.md`
- `.ai/PROJECT_RULES.md`
- `.ai/PROJECT_CONTEXT.md`
- `.ai/MILESTONE.md`
- `.ai/TASKS.md`
- `.ai/REVIEW_CHECKLIST.md`

長期方針が必要な場合:

- `docs/ROADMAP.md`

## PR の単位

1 PR = 1つのレビュー可能な機能または整理作業。

避ける:

- cleanup と大型新機能を同じ PR に入れる
- 無関係なリファクタ
- 将来使うかもしれないという理由だけで大規模な基盤を先に作る

推奨:

- M0 repository cleanup
- M1 PowerPoint open
- M2 IDs/assets
- M3 import

のようにマイルストーン単位またはその中の独立した機能単位で PR を作る。

## PR の必須情報

Codex は PR 本文に以下を記載する。

- 目的
- 対応した TASK
- 変更した主要ファイル
- 削除した実験コードと削除理由
- 動作確認
- 実行したテスト
- GUI / PowerPoint 実機確認の有無
- 未確認事項
- 既知の制限
- 次のマイルストーンへ残した事項

## 自動レビュー

### Codex Code Review

Codex Code Review が利用可能な環境では、PR に対する追加レビュアーとして利用する。

リポジトリ固有のレビュー判断は `AGENTS.md` に簡潔に記載する。

重要:

- Codex Code Review は CI や人間レビューの代替にしない
- 機械的に確認できるものは tests / CI に置く
- `AGENTS.md` には破壊的変更、責務境界、互換性など人間が毎回確認する事項を書く
- review noise が増えるルールは削除または scope を狭める

手動レビュー要求が必要な環境では `@codex review` を利用できる。

### GitHub Copilot Code Review

利用可能な契約・設定がある場合は補助レビュアーとして併用可能。

GitHub 側では pull request の自動レビューや new push 後の再レビューを設定できる。

ただし、このリポジトリの標準を Codex とするため、Copilot 固有設定を必須依存にはしない。

## CI の役割

AI reviewer に任せず CI で判定するもの:

- unit tests
- smoke tests
- CLI help / command availability
- deterministic file-format validation
- lint / format（導入した場合）
- fixture based conversion tests

AI reviewer に確認させるもの:

- 責務分離が崩れていないか
- Docker/Core に置くべきロジックが UI 側へ漏れていないか
- 既存の正式機能を不要に削除していないか
- temporary experiment が production path に戻っていないか
- マイルストーン外の先回り実装をしていないか

## Codex に対するレビュー指針

PR review 時は特に以下を確認する。

1. `slidegen render` の既存出力を壊していないか
2. docx の正式機能を壊していないか
3. Docker / Dev Container 中心という責務境界を守っているか
4. VS Code / PowerPoint 側に変換ロジックを増やしていないか
5. 文字情報を不要な永続 JSON に複製していないか
6. 将来機能を現在のマイルストーンへ過剰実装していないか
7. 削除したコードに現在利用中の経路が含まれていないか
