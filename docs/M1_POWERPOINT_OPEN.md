# M1: QMD -> PPTX -> Microsoft PowerPoint

## Goal

Dev Container 内で QMD を PPTX に build し、build 成功後に Windows/macOS ホスト側の Microsoft PowerPoint で生成 PPTX を開けるようにする。

このマイルストーンでは、PowerPoint を「実編集環境」として使う最初の一歩だけを実装する。

## Standard user flow

標準利用環境:

1. Docker Desktop を起動
2. VS Code で md-slide-tool を開く
3. Dev Containers: Reopen in Container
4. Dev Container 内で QMD を build
5. build 成功後、ホスト OS の Microsoft PowerPoint で生成 PPTX を開く

PowerPoint 以外の build / conversion logic は Dev Container 側に置く。

## Scope

M1 で実装するもの:

- QMD -> PPTX build の既存経路を維持
- build 成功後に生成 PPTX を特定
- Dev Container からホスト側へ「この PPTX を開く」要求を渡す
- ホスト側で既定アプリ、原則 Microsoft PowerPoint を起動
- Windows を主検証対象とする
- macOS は設計上対応可能な形にし、未検証なら明記する
- PowerPoint がインストールされていない場合の明確なエラー表示
- build failure 時は PowerPoint を開かない

## Out of scope

M1 では実装しない:

- QMD 保存時の自動 build
- PPTX 保存監視
- PPTX -> QMD
- assets.json
- stable slide/image IDs
- dirty state
- conflict handling
- PowerPoint Add-in
- PowerPoint を閉じる制御
- VS Code 内 PPTX preview

自動保存監視は M4 Sync Engine で扱う。

## Architecture principle

```text
Dev Container / Core
  - slidegen render
  - output PPTX resolution
  - build result
        |
        | open request only
        v
Host Bridge
  - no build logic
  - no QMD parsing
  - open the requested host-side PPTX
        |
        v
Microsoft PowerPoint
```

Host Bridge は「PPTXを開く」以外の責務を持たない。

## Feasibility spike first

Remote / Dev Container 環境では Workspace Extension は container 側で動くため、ホスト OS の PowerPoint を直接 spawn しない。

VS Code の公式方針に沿い、最初に以下を検証する。

1. UI Extension をホスト側で動かす
2. `vscode.env.openExternal` で host-side PPTX を既定アプリで開く
3. Dev Container の `${localWorkspaceFolder}` を host path として bridge に渡せることを確認する
4. `/work/.../file.pptx` と host workspace path + relative path の対応を確認する
5. Windows の path separator / spaces / non-ASCII filenames を確認する

参考:
- VS Code Remote extensions: UI extensions run locally; workspace extensions run remotely.
- VS Code recommends `vscode.env.openExternal` for opening a local browser/application from remote development.
- Dev Containers supports passing `${localWorkspaceFolder}` into the container via `remoteEnv`.

## Preferred implementation direction

PoC で成立する場合は、以下の責務分離を優先する。

### Container/Core side

- build
- output path determination
- relative path generation
- open request generation

### Host/UI side

- receive host path or workspace-relative PPTX path
- validate .pptx
- call `vscode.env.openExternal`
- show host-open errors

Host/UI sideに Quarto、Python、QMD parsing、render logic を置かない。

## CLI behavior

既存の `slidegen render <qmd>` は壊さない。

M1 では以下のどちらかを PoC 結果に応じて選ぶ。

- A: `slidegen render` 成功後に host bridge が利用可能なら自動 open
- B: `Build and Open PowerPoint` という VS Code command/task を追加し、その中で既存 render を呼ぶ

将来 M4 で QMD save -> render -> open に接続しやすい方式を選ぶ。

CLI単体利用時にホスト bridge が存在しない場合でも、render 自体は成功できることを優先する。

## Error behavior

- build failure -> openしない
- PPTX output missing -> openしない + error
- host bridge unavailable -> build successは維持し、open failureを明示
- PowerPoint/default app unavailable -> open failureを明示
- host path mapping failure -> openしない + actionable error

## Completion criteria

Windows + Docker Desktop + VS Code + Reopen in Container の標準環境で:

1. Dev Container build succeeds
2. `slidegen render` の既存 render が成功する
3. build 後に対象 PPTX が Windows 側で開く
4. PowerPoint で正しいファイルが開かれる
5. 日本語/空白を含む path でも動く
6. build failure 時に開かない
7. host bridge failure でも PPTX build 自体は壊れない
8. docx の正式機能を壊さない
9. tests / smoke tests が通る

## Manual validation

人間が実機で確認する項目:

- Docker Desktop起動
- Reopen in Container
- 既知の QMD を build
- 正しい PPTX が PowerPoint で自動的に開く
- PowerPoint で編集可能
- 同名の別 PPTX が誤って開かれない
- 日本語ファイル名/パス
- PowerPointが既に起動中の場合

## PR #14 implementation status

The M1 extension is a workspace extension installed in the Dev Container. `.devcontainer/devcontainer.json` passes `${localWorkspaceFolder}` as `remoteEnv.MD_SLIDE_TOOL_HOST_WORKSPACE`. The `postAttachCommand` runs `scripts/install-vscode-extension.sh` after VS Code attaches; the script checks that the remote `code` CLI is available, then hashes the extension sources and packages/installs a VSIX only when the source changed or the extension is missing. This makes the command available after the regular **Reopen in Container** flow without starting an Extension Development Host.

The command runs the existing `slidegen render` CLI in the container. It checks for the final same-stem `.pptx` output, maps its path relative to `/work` onto the host workspace, and calls `vscode.env.openExternal`. A build error or missing output prevents opening. Host mapping or `openExternal` failure leaves the generated PPTX build intact and reports a warning.

The extension package contains only the M1 command, its host path mapping, and tests. It does not contain Preview/Webview/PDF.js code or `pdfjs-dist` dependencies. The Windows VS Code Remote -> host PowerPoint GUI path and automatic extension installation in a live Dev Container still require manual verification.
