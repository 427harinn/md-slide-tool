# TASKS

## M1: QMD -> PPTX -> Microsoft PowerPoint

Codex は上から順番に実行する。

### T-101: 現在のbuild出力規則を確認する

- `slidegen render` の成功/失敗判定を確認
- input QMD から最終 PPTX path をどう決定しているか確認
- template / postprocess 後の最終ファイルを特定
- Windows bind mount と `/work` の対応を確認

**状態:** 完了。既存CLIがQMDと同じstemのPPTXを出力することを確認。

### T-102: Host Bridge feasibility PoC

VS Code公式のRemote Development方針を優先する。

確認すること:

- UI/local extension host
- `vscode.env.openExternal`
- host-side PPTX file URI
- `${localWorkspaceFolder}` または同等のhost path mapping
- workspace/container側からhost/UI側へopen requestを渡す方法

PoCは最小コードで行い、成功条件をテストまたは実機確認可能な形にする。

成立しない場合は代替案を勝手に大規模実装せず、原因と候補をPR/タスクへ記録する。

**状態:** workspace-only PoCはWindows実機でFAIL（remote hostから開いた`file:` URIが`vscode-remote` link扱い）。UI extension + workspace extensionの二層構成で、手動diagnostic install時の実機command routing / PowerPoint openはPASS（ユーザー確認）。二層bridgeのPoCは完了。通常Reopen flowでの自動配布は正式リリース前のRelease / Distribution gateへ移管し、M1完了条件から除外。

### T-103: Host Bridgeを最小実装する

PoCで成立した方式のみ実装する。

Host側の責務:

- 対象PPTX pathを受け取る
- .pptx validation
- host OSでopenする
- error reporting

禁止:

- QMD parsing
- Quarto実行
- Python実行
- PPTX変換
- file watch
- PowerPoint edit/save logic

**状態:** workspace extensionで既存renderとhost path mapping、local UI extensionでlocal file URI生成とopenを実装。各extensionを正しいhostへ手動installした実機cross-host command routingとPowerPoint openはPASS（ユーザー確認）。自動配布のMarketplace準備は正式リリース前のRelease / Distribution課題。

### T-104: build成功後のopen flowを接続する

- 既存 `slidegen render` の互換性を維持
- build failure時はopenしない
- final PPTXのみを開く
- host bridge unavailableでもrender結果を失わない
- 二重openを避ける

自動QMD save watcherは追加しない。

**状態:** 実装済み。build failure/missing output時はopenせず、bridge failureはbuild成功を維持。

### T-105: path / platform handling

最低限確認:

- Windows host path
- spaces
- 日本語 path
- nested project path
- Windows path separator
- PowerPoint already running

macOSは実装が自然に対応できる場合は対応する。実機未確認なら未確認と明記する。

**状態:** unit testsでWindows/POSIX mapping、日本語/空白pathを確認。Windows実機のhost mapping/openはユーザー確認によりPASS。PowerPoint起動済みの追加確認等は正式リリース前の自動配布E2Eで扱い、M1の必須Gateにはしない。

### T-106: tests

追加/更新:

- output PPTX resolution
- bridge request/path mapping
- build failure -> no open
- bridge unavailable -> render success preserved
- invalid/non-PPTX rejection
- current PPTX image-placement tests
- smoke test
- docx regression

**状態:** Dockerでextension tests 18件、両VSIX生成/成果物確認、root tests 10件、CLI smoke、代表5-slide PPTX render、docx generation/ZIP検査を再実行しPASS。`git diff --check`もPASS。PR CI実行結果はpush後に確認する。

### T-107: documentation

更新:

- README
- PROJECT_CONTEXT
- MILESTONE
- TASKS
- DEBUG_SCENARIOS if needed

標準利用手順を以下に統一する。

```text
Docker Desktop
-> VS Code
-> Reopen in Container
-> build
-> Microsoft PowerPoint
```

**状態:** README / PROJECT_CONTEXT / MILESTONE / TASKS / M1 docを、ユーザー確認済みのM1完了条件と正式リリース前のRelease / Distribution課題に合わせて更新。

### T-108: final self-review and PR

- 全テスト
- REVIEW_CHECKLIST
- M1以外を先回りしていないか
- docx regression
- Windows実機で必要な手動確認項目をPR本文へ記載
- PowerPoint起動方法/host bridge責務を説明
- 未確認事項を明記

**状態:** PR #14の最終セルフレビュー、独立Review/Architecture、Docker自動テスト/回帰、latest PR head CIを確認する。Marketplace公開判断と通常Reopen flowの自動配布E2Eは正式リリース前のRelease / Distribution gateであり、M1完了やPR #14のDraft解除を妨げない。SHAやCI run番号は固定せず最新headの状態を確認する。

## 横断課題: Release / Distribution (正式リリース前; M1完了条件外)

- Marketplace publisherの確定と公開承認
- UI extension / Workspace extensionのMarketplace公開とversioning
- `customizations.vscode.extensions` とdependencyによるLocal / Remote自動配置
- 手動VSIX installやExtension Development Host起動を伴わない通常Reopen in Container E2E
- 公開後のupdate / compatibility確認

これらの外部公開・配布作業は別途正式リリース前に実施し、今回実行しない。
