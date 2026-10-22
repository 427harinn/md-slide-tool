# MILESTONE

## マイルストーン名

Repository Cleanup for PowerPoint Workflow

## 背景

このリポジトリには、CLI ベースの正式機能に加え、VS Code 内 PPTX Preview、LibreOffice/PDF.js、保存時 Task 実行、Auto Preview 実験など、異なる時期に試した実装が混在している。

今後は Microsoft PowerPoint を実編集環境として利用し、Docker / Dev Container 側を QMD/PPTX 変換・監視・同期の中心にする。

双方向同期を実装する前に、不要な実験経路と重複責務を整理し、QMD -> PPTX の既存機能と docx の正式機能を保ったまま次の開発に進める状態にする。

## 目的

- 現在の正式機能と実験コードを区別する
- 不採用となった実験経路を削除する
- build の入口を整理する
- CLI / core / UI の責務境界を明確にする
- ドキュメントと実装の状態を一致させる
- 次マイルストーン「QMD -> PPTX -> Microsoft PowerPoint」を実装しやすい状態にする

## 維持する正式機能

- `slidegen new`
- PPTX 向け `slidegen render`
- Quarto / Pandoc ベースの PPTX build
- `prepare-qmd-for-pptx.py`
- `postprocess-pptx.py`
- PPTX 画像自動配置
- PPTX template
- docx project/template 機能
- Dev Container
- 現在利用中の project データ
- 既存テストの有効な部分

## 削除・整理候補

実装前に参照関係を確認し、利用経路がないことを確認してから削除する。

- VS Code 内 PPTX -> PDF preview
- PDF.js Webview
- preview 専用 VS Code Extension コード
- preview 専用 LibreOffice 依存
- 重複した save-trigger build 経路
- 空の `compose.yml`
- tracked `.DS_Store`
- stale / contradictory documentation
- main に採用しない Auto Preview 実験に由来する設計記述

## 対象外

このマイルストーンでは実装しない。

- Microsoft PowerPoint 自動起動
- PPTX -> QMD
- assets.json
- slide id / image id
- file watcher based sync engine
- dirty state handling
- conflict QMD
- automatic diff
- PPTX -> Word

これらは `docs/ROADMAP.md` の後続マイルストーンで扱う。

## リファクタリング方針

- cleanup と新機能追加を混ぜない
- 既存の公開 CLI を不用意に変更しない
- docx を削除・縮小しない
- 先に不要コードを削除し、その後必要最小限の内部整理を行う
- `slidegen render` が将来 Sync Engine から再利用できる構造を目指すが、今回過剰な抽象化はしない
- Git 履歴から復元できる実験コードを「念のため」で残さない

## 完了条件

- 正式機能 / 実験機能の棚卸しが記録されている
- 削除対象の依存関係とコードが除去されている
- build 経路が重複していない
- `slidegen new` / `slidegen render` が動作する
- PPTX画像後処理の既存テストが通る
- docx project/template が残っている
- README / PROJECT_CONTEXT が実装と一致している
- CI が cleanup 後の正式機能を確認できる
- PR に削除内容、残した内容、検証結果、未検証事項が記載されている

## 次のマイルストーン

QMD -> PPTX -> Microsoft PowerPoint

詳細は `docs/ROADMAP.md` を参照する。

## 状態

計画済み・未着手
