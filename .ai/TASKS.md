# TASKS

## M1: QMD -> PPTX -> Microsoft PowerPoint

Codex は上から順番に実行する。

### T-101: 現在のbuild出力規則を確認する

- `slidegen render` の成功/失敗判定を確認
- input QMD から最終 PPTX path をどう決定しているか確認
- template / postprocess 後の最終ファイルを特定
- Windows bind mount と `/work` の対応を確認

**状態:** 未着手

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

**状態:** 未着手

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

**状態:** 未着手

### T-104: build成功後のopen flowを接続する

- 既存 `slidegen render` の互換性を維持
- build failure時はopenしない
- final PPTXのみを開く
- host bridge unavailableでもrender結果を失わない
- 二重openを避ける

自動QMD save watcherは追加しない。

**状態:** 未着手

### T-105: path / platform handling

最低限確認:

- Windows host path
- spaces
- 日本語 path
- nested project path
- Windows path separator
- PowerPoint already running

macOSは実装が自然に対応できる場合は対応する。実機未確認なら未確認と明記する。

**状態:** 未着手

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

**状態:** 未着手

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

**状態:** 未着手

### T-108: final self-review and PR

- 全テスト
- REVIEW_CHECKLIST
- M1以外を先回りしていないか
- docx regression
- Windows実機で必要な手動確認項目をPR本文へ記載
- PowerPoint起動方法/host bridge責務を説明
- 未確認事項を明記

**状態:** 未着手
