# MILESTONE

## M1: QMD -> PPTX -> Microsoft PowerPoint

### 目的

QMD の build は Docker / Dev Container 内で実行し、生成した PPTX を Windows ホスト側の Microsoft PowerPoint で開く。VS Code extension は build の起動とホストへの最小通知だけを担う。

### 確定方針

- 既存の `slidegen render` を build の正規経路として維持する。
- VS Code の `vscode.env.openExternal` でホスト側の `file:` URI を開く feasibility PoC を行う。
- Dev Container の `${localWorkspaceFolder}` を `MD_SLIDE_TOOL_HOST_WORKSPACE` として container extension へ渡し、`/work` からの相対位置でホストパスを作る。
- build が失敗した場合は PowerPoint を開かない。
- host bridge が使えない場合は build 成功を維持し、警告を表示する。
- パスに空白・日本語が含まれる場合と PowerPoint が起動済みの場合を考慮する。
- VS Code 内 PPTX Preview、QMD 保存時 build、PPTX 保存監視は導入しない。
- docx の正式機能は維持する。

### 対象外

PPTX->QMD、`assets.json`、stable ID、Sync Engine、競合処理、PowerPoint Add-in、build watcher、自動保存、差分同期。

### 完了条件

- VS Code UI から Dev Container 内で既存 PPTX build を起動できる。
- 成功後だけ `vscode.env.openExternal` によってホスト側 PowerPoint を開く。
- `/work` -> Windows host workspace の path mapping を検証する。
- mapping / build failure / bridge unavailable の unit tests がある。
- 既存 smoke、PPTX render、docx regression を確認する。
- README と開発ドキュメントに利用方法・実機確認項目を記載する。

### 状態

実装済み。Windows 上の VS Code Remote/Dev Containers 経由で `openExternal` が PowerPoint を起動するかは実機検証待ち。
