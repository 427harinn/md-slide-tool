# TASKS

## M1: QMD -> PPTX -> Microsoft PowerPoint

### T-101: 実行経路と前提の確認

- 既存 render 経路と VS Code extension を確認する。
- host bridge PoC は `vscode.env.openExternal` を使う。
- 完了条件: build が Dev Container 内に閉じることを確認する。

**状態:** 完了（build 経路を確認。VS Code GUI からの host への配送は実機確認待ち）

### T-102: Host Bridge 用 path mapping

- `${localWorkspaceFolder}` を container environment へ渡す。
- `/work` の相対パスをホストパスへ変換し、空白・日本語を含む URI を扱う。
- 完了条件: Windows / POSIX path の unit tests と workspace 外拒否を確認する。

**状態:** 完了

### T-103: VS Code UI から build を起動

- QMD の context menu / command palette から既存 render script を呼ぶ。
- build logic は Dev Container 内に維持する。
- 完了条件: 既存 `slidegen render` の経路を再利用する。

**状態:** 完了

### T-104: build 成功後の PowerPoint 起動

- build が成功した後に限り `vscode.env.openExternal` で PPTX を開く。
- 起動済み PowerPoint の再利用は OS file association に委ねる。
- 完了条件: build failure では open しない。

**状態:** 実装済み（Windows GUI 実機確認待ち）

### T-105: Host Bridge unavailable 時の動作

- bridge が利用不能でも build は成功として扱い、PPTX の場所を通知する。
- 完了条件: bridge unavailable のテストで build result を維持する。

**状態:** 完了

### T-106: unit tests と既存回帰確認

- path mapping / build failure / bridge unavailable を unit tests で確認する。
- extension tests、既存 smoke、PPTX render、docx regression を実行する。

**状態:** 完了

### T-107: README / project docs の更新

- 利用手順、Host Bridge 方式、未確認の Windows 実機項目を記載する。
- PROJECT_CONTEXT / MILESTONE / TASKS を実装に合わせる。

**状態:** 完了

### T-108: 最終セルフレビューと Pull Request

- `.ai/REVIEW_CHECKLIST.md` に沿って差分を確認する。
- テスト結果、Host Bridge、path 変換、未確認項目、M2 以降の対象外を PR に記載する。

**状態:** 未着手
