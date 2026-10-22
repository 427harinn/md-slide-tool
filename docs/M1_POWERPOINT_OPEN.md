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

**現状:** 二層extensionのbuild/open、cross-host command routing、host path mapping、Windows PowerPoint openは実機確認済み。機能実装は完了扱い。通常のReopen in Containerからの自動配布とMarketplace公開は正式リリース前のRelease / Distribution課題であり、M1 Gateではない。

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

M1 is complete when the following are satisfied:

1. QMD builds to PPTX through the existing `slidegen render` path in the Dev Container.
2. The Workspace extension builds in the Dev Container and the Local UI extension opens the output on the host.
3. Windows E2E confirms the two-layer extension setup, command routing, host path mapping, and correct PowerPoint open. The confirmed diagnostic setup used manual VSIX installation.
4. Build failure does not open PowerPoint.
5. Host bridge failure preserves a successful PPTX build.
6. PPTX / docx regressions pass.
7. No removed Preview / PDF.js / Webview / Preview-only build / LibreOffice code is restored.
8. Tests, smoke test, representative PPTX render, docx regression, and latest PR head CI pass.

Marketplace publication, publisher configuration, automatic installation in a plain Reopen in Container flow, and post-publication E2E are not M1 completion criteria. They remain a cross-cutting Release / Distribution gate before formal public release; see `docs/ROADMAP.md` and `.ai/HUMAN_GATES.md`.

## Manual validation

The two-layer Windows build/open behavior is already user-confirmed. Do not repeat it for documentation-only changes.

## Automated checks and Windows evidence

自動テストで確認する項目:

- remote build failure時にopen可能な結果を返さない
- missing output時にopen可能な結果を返さない
- `/work` からWindows/POSIX host pathへのmapping
- 日本語、空白、nested path
- workspace外pathの拒否
- UI extensionが `vscode.Uri.file(hostPath)` 相当のlocal `file:` URIを作る
- `openExternal` / mapping failureでもbuild成功結果を保持
- smoke test、PPTX render、docx regression

Windows実機で確認済み:

- Local UI packageとRemote Workspace packageを各hostへ配置
- command表示、cross-host VS Code command routing
- Dev Container内の実QMD build
- host path mappingと正しいPPTXのWindows PowerPoint open

自動配布後の通常Reopen E2E、既起動PowerPoint、日本語/空白を含む実workspace path、編集/保存の追加確認は正式リリース前のRelease / Distribution gateに含め、M1完了を止めない。

## PR #14 implementation status

### Architecture decision (Windows E2E follow-up)

The workspace-only Host Bridge failed on Windows: calling `vscode.env.openExternal` with a `file://C:/...` URI from the remote extension host was surfaced as a `vscode-remote` link. Publishing that design would not fix the URI ownership problem.

Use two small extension packages with explicit responsibilities:

- Workspace extension: run `slidegen render`, verify the final same-stem PPTX, map its `/work`-relative path with `MD_SLIDE_TOOL_HOST_WORKSPACE`, and return the resulting Windows host path through a registered VS Code command. It never opens a URI.
- UI extension: expose **Build and Open in Microsoft PowerPoint**, invoke the workspace command, construct a local `vscode.Uri.file(hostPath)`, and call `vscode.env.openExternal` from the local extension host.
- Communication: the UI command invokes the workspace extension's internal command through `vscode.commands.executeCommand`; the workspace command returns a small result object with build status and host path/error.

The single UI extension + Tasks API alternative was considered. VS Code can execute process tasks in remote contexts, but the task API exposes task completion/exit status rather than a structured return value containing the remote process's resolved host path. Returning that result through task output or a temporary file would add a second result channel. The two-extension command result keeps the remote path mapping beside `remoteEnv` and gives the local opener a plain host path.

### Verification split

Automated tests cover remote build failure/output validation, host path mapping, command result handling, and that the UI side creates a local `file:` URI before `openExternal`. The user has confirmed extension-host placement and cross-host dispatch for the manual diagnostic install, as well as Windows PowerPoint opening. Additional normal-flow distribution checks belong to the pre-release gate.

The M1 build/open code is implemented as separate workspace and UI extension packages, and both VSIX packages build locally. Windows has confirmed the two packages run in the intended extension hosts, the command routes across hosts, and a successful build opens the correct PPTX in PowerPoint. These bridge checks are PASS and will not be repeated as part of distribution work.

Automatic distribution through the regular **Reopen in Container** flow remains intentionally deferred. Windows validation showed that the remote `code` CLI is not on `PATH` in lifecycle hooks, so lifecycle-hook VSIX installation was removed. The Dev Container extension list accepts Marketplace extension IDs, not local VSIX paths. Neither package is published; manual VSIX installation was used to verify the M1 feature. Marketplace publication and normal-flow automatic placement are pre-release Release / Distribution tasks, not M1 blockers.

### Extension distribution options and decision

| Option | Fit for the standard flow | Decision / limitation |
| --- | --- | --- |
| `customizations.vscode.extensions` with a Marketplace ID | Dev Containers can provision listed extensions during container setup/reopen. | Standard distribution entry point, but a package must be published first. Never point it at a local VSIX or add unpublished IDs. |
| Workspace extension `extensionDependencies` on the UI extension | VS Code remote-extension guidance recommends this dependency for a remote extension that needs a local extension; the provider must declare `"api": "none"` so it exports no activation API across extension hosts. The extensions can still communicate through VS Code commands. | Add the dependency metadata now. It expresses the two-package install relationship but does not remove the Marketplace publication requirement. Automatic placement into Local UI and Remote Workspace hosts still requires the final Reopen E2E gate. |
| `postStartCommand` / `postAttachCommand` calling remote `code --install-extension` | Would require the remote CLI in lifecycle-hook PATH. | Rejected: both hooks were tried on the target setup and the remote `code` CLI was unavailable. |
| Local VSIX path in `customizations.vscode.extensions` | Would avoid Marketplace publication. | Rejected: Dev Container extension IDs do not accept local VSIX paths. |
| Tasks API launched from one UI extension | Can execute remote tasks but does not itself provision the missing extension package into the proper host. | Does not solve the distribution problem; task output/result channels would also be needed for the host path. |

Current metadata: the Remote Workspace package declares an `extensionDependencies` entry for the exact Local UI package ID, and the Local UI package declares `"api": "none"`. The Dev Container config remains free of unpublished IDs and local VSIX paths. Before formal public release, decide whether to publish, then list the published Remote Workspace extension ID in `customizations.vscode.extensions` and verify dependency installation/host placement through the normal Reopen flow. No publication is performed by M1.

Official references: [Extension Manifest](https://code.visualstudio.com/api/references/extension-manifest), [Remote Development: extension placement, cross-host dependencies and command routing](https://code.visualstudio.com/api/advanced-topics/remote-extensions), and [Dev Container metadata reference](https://containers.dev/implementors/json_reference/). VS Code documents that extension kind determines the correct installation location, Marketplace builds are used for automatic remote installation, and a remote extension may depend on a local provider with `"api": "none"` while still communicating through commands. The docs do not establish that this unpublished package pair is installed correctly through our exact Dev Container setup; this remains a HUMAN_REQUIRED Release / Distribution check before formal public release, not an M1 gate.

The remote command runs the existing `slidegen render` CLI in the container. It checks for the final same-stem `.pptx` output and maps its path relative to `/work` onto `MD_SLIDE_TOOL_HOST_WORKSPACE`. The local command invokes the remote command through `vscode.commands.executeCommand`, then creates `vscode.Uri.file(hostPath)` and calls `vscode.env.openExternal`. A build error or missing output prevents opening. Host mapping or `openExternal` failure leaves the generated PPTX build intact and reports a warning.

The extension packages contain only the M1 build/open responsibilities and path mapping. They do not contain Preview/Webview/PDF.js code or `pdfjs-dist` dependencies. The M1 bridge E2E is confirmed. No HUMAN_REQUIRED gate remains for M1. Marketplace publisher/publication, automatic host placement, and post-publication compatibility are retained as HUMAN_REQUIRED Release / Distribution gates before formal release; they do not determine M1 completion or PR #14 Draft status.
