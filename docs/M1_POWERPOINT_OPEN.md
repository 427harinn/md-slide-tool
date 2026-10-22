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

**現状:** 二層extensionのbuild/open、cross-host command routing、host path mapping、Windows PowerPoint openは実機確認済み。未解決なのは未公開extension packageの自動配布だけである。Marketplace公開を伴う通常利用フローは判断待ちで、M1 GateはHUMAN_REQUIRED。

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
Dev Container / Workspace extension
  - slidegen render
  - output PPTX resolution
  - build result
        |
        | open request only
        v
VS Code command bridge
  - workspace command returns a small JSON result
  - no build logic on UI side
        |
        v
Local UI extension
  - create a local `file:` URI from the Windows host path
  - call `vscode.env.openExternal`
        |
        v
Microsoft PowerPoint
```

Local UI extension は「受け取ったhost pathのPPTXを開く」以外の責務を持たない。Workspace extensionはbuildとcontainer-to-host path mappingを担当し、PowerPointをspawnしない。

## Feasibility spike result and architecture decision

Remote / Dev Container 環境では Workspace Extension は container 側で動くため、ホスト OS の PowerPoint を直接 spawn しない。

最初に試したworkspace-only PoCはWindows実機で失敗した。remote extension hostから `vscode.env.openExternal(file://C:/...)` を呼ぶと、Windowsで `vscode-remote` linkとして処理されることを確認した。Marketplaceへ公開してもこのURI所有元の問題は解決しない。

二層構成を選択した。Workspace extensionが既存buildを実行し、`/work/...` の出力pathを `${localWorkspaceFolder}` から渡されたhost workspace pathへ変換する。登録commandの戻り値でhost pathをlocal UI extensionへ返す。UI extensionは `vscode.Uri.file(hostPath)` でローカルURIを作り、local extension host上から `vscode.env.openExternal` を呼ぶ。

UI extension単体 + VS Code Tasks API案も検討した。Task APIはremote側のprocess task実行と終了/exit status通知には使えるが、workspace extension側で確定したhost pathをUI extensionへ構造化結果として返すにはtask output等の別channelが必要となる。VS Code command間の小さなJSON結果を使う二層案の方がpath mapping責務をworkspace側に保てるため採用した。

VS Code Remote Extensions guidanceではUI extensionがlocal、workspace extensionがremoteで実行され、extension間commandは場所に応じてrouteされる。Dev Containerの `remoteEnv` には `${localWorkspaceFolder}` を設定し `/work` とWindows host workspaceの対応を渡す。

## Preferred implementation direction

PoC で成立する場合は、以下の責務分離を優先する。

### Container/Core side

- build
- output path determination
- relative path generation
- host path mapping
- registered command result generation

### Host/UI side

- receive the workspace command result
- create a local file URI from the host path
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

## Automated checks and Windows HUMAN_REQUIRED gate

自動テストで確認する項目:

- remote build failure時にopen可能な結果を返さない
- missing output時にopen可能な結果を返さない
- `/work` からWindows/POSIX host pathへのmapping
- 日本語、空白、nested path
- workspace外pathの拒否
- UI extensionが `vscode.Uri.file(hostPath)` 相当のlocal `file:` URIを作る
- `openExternal` / mapping failureでもbuild成功結果を保持
- smoke test、PPTX render、docx regression

Windows実機で人間が確認する項目（M1 GateをPASSにする前に必要）:

- Dev Containerへ接続したwindowにlocal UI packageとremote workspace packageが配置される
- Extension Development Hostや最終利用者の手動操作なしでcommandが表示される
- cross-host VS Code command routingが成功する
- 実QMDから正しいPPTXがWindows側PowerPointで開く
- PowerPoint起動済み、日本語/空白を含む実workspace path
- 意図的build failureではPowerPointが起動しない
- PowerPointで生成ファイルを通常編集・保存できる

## PR #14 implementation status

### Architecture decision (Windows E2E follow-up)

The workspace-only Host Bridge failed on Windows: calling `vscode.env.openExternal` with a `file://C:/...` URI from the remote extension host was surfaced as a `vscode-remote` link. Publishing that design would not fix the URI ownership problem.

Use two small extension packages with explicit responsibilities:

- Workspace extension: run `slidegen render`, verify the final same-stem PPTX, map its `/work`-relative path with `MD_SLIDE_TOOL_HOST_WORKSPACE`, and return the resulting Windows host path through a registered VS Code command. It never opens a URI.
- UI extension: expose **Build and Open in Microsoft PowerPoint**, invoke the workspace command, construct a local `vscode.Uri.file(hostPath)`, and call `vscode.env.openExternal` from the local extension host.
- Communication: the UI command invokes the workspace extension's internal command through `vscode.commands.executeCommand`; the workspace command returns a small result object with build status and host path/error.

The single UI extension + Tasks API alternative was considered. VS Code can execute process tasks in remote contexts, but the task API exposes task completion/exit status rather than a structured return value containing the remote process's resolved host path. Returning that result through task output or a temporary file would add a second result channel. The two-extension command result keeps the remote path mapping beside `remoteEnv` and gives the local opener a plain host path.

### Verification split

Automated tests cover remote build failure/output validation, host path mapping, command result handling, and that the UI side creates a local `file:` URI before `openExternal`. Windows HUMAN_REQUIRED covers actual extension-host placement and cross-host command dispatch, Windows file association/PowerPoint opening, an already-running PowerPoint, Japanese/space paths, and editable output.

The M1 build/open code is implemented as separate workspace and UI extension packages, and both VSIX packages build locally. Windows has confirmed the two packages run in the intended extension hosts, the command routes across hosts, and a successful build opens the correct PPTX in PowerPoint. These bridge checks are PASS and will not be repeated as part of distribution work.

Automatic distribution through the regular **Reopen in Container** flow remains unresolved. Windows validation showed that the remote `code` CLI is not on `PATH` in lifecycle hooks, so lifecycle-hook VSIX installation was removed. The Dev Container extension list accepts Marketplace extension IDs, not local VSIX paths. Neither package is published, so the current standard flow does not install them. Manual VSIX installation is diagnostic-only and is not the final workflow.

### Extension distribution options and decision

| Option | Fit for the standard flow | Decision / limitation |
| --- | --- | --- |
| `customizations.vscode.extensions` with a Marketplace ID | Dev Containers can provision listed extensions during container setup/reopen. | Standard distribution entry point, but a package must be published first. Never point it at a local VSIX or add unpublished IDs. |
| Workspace extension `extensionDependencies` on the UI extension | VS Code remote-extension guidance recommends this dependency for a remote extension that needs a local extension; the provider must declare `"api": "none"` so it exports no activation API across extension hosts. The extensions can still communicate through VS Code commands. | Add the dependency metadata now. It expresses the two-package install relationship but does not remove the Marketplace publication requirement. Automatic placement into Local UI and Remote Workspace hosts still requires the final Reopen E2E gate. |
| `postStartCommand` / `postAttachCommand` calling remote `code --install-extension` | Would require the remote CLI in lifecycle-hook PATH. | Rejected: both hooks were tried on the target setup and the remote `code` CLI was unavailable. |
| Local VSIX path in `customizations.vscode.extensions` | Would avoid Marketplace publication. | Rejected: Dev Container extension IDs do not accept local VSIX paths. |
| Tasks API launched from one UI extension | Can execute remote tasks but does not itself provision the missing extension package into the proper host. | Does not solve the distribution problem; task output/result channels would also be needed for the host path. |

Selected preparation: the Remote Workspace package declares an `extensionDependencies` entry for the exact Local UI package ID, and the Local UI package declares `"api": "none"`. The Dev Container config remains free of both unpublished IDs and local VSIX paths. If standard automatic distribution requires Marketplace publication, publishing is an external HUMAN_REQUIRED decision and will not be performed without authorization. Once approved, list the Remote Workspace Marketplace ID in `customizations.vscode.extensions`, then verify dependency installation/host placement through the normal Reopen flow.

Official references: [Extension Manifest](https://code.visualstudio.com/api/references/extension-manifest), [Remote Development: extension placement, cross-host dependencies and command routing](https://code.visualstudio.com/api/advanced-topics/remote-extensions), and [Dev Container metadata reference](https://containers.dev/implementors/json_reference/). VS Code documents that extension kind determines the correct installation location, Marketplace builds are used for automatic remote installation, and a remote extension may depend on a local provider with `"api": "none"` while still communicating through commands. The docs do not establish that this unpublished package pair is installed correctly through our exact Dev Container setup; that is reserved for the final Windows HUMAN_REQUIRED Reopen gate.

The remote command runs the existing `slidegen render` CLI in the container. It checks for the final same-stem `.pptx` output and maps its path relative to `/work` onto `MD_SLIDE_TOOL_HOST_WORKSPACE`. The local command invokes the remote command through `vscode.commands.executeCommand`, then creates `vscode.Uri.file(hostPath)` and calls `vscode.env.openExternal`. A build error or missing output prevents opening. Host mapping or `openExternal` failure leaves the generated PPTX build intact and reports a warning.

The extension packages contain only the M1 build/open responsibilities and path mapping. They do not contain Preview/Webview/PDF.js code or `pdfjs-dist` dependencies. Automated checks are separate from the Windows HUMAN_REQUIRED distribution gate. Bridge E2E is already confirmed. The only remaining human gates are the external decision to publish the extension package(s), then final normal-flow Reopen verification without manual VSIX installation or Extension Development Host. Until those gates pass, M1 remains HUMAN_REQUIRED and PR #14 stays Draft.
