# MILESTONE

## マイルストーン名

M1: QMD -> PPTX -> Microsoft PowerPoint

## 背景

M0 Repository Cleanup が完了し、不採用だった VS Code 内 PPTX Preview、PDF.js、Preview 専用 LibreOffice、重複した保存時 build 経路を削除した。

現在の正式 PPTX build は以下。

```text
slidegen render
  -> scripts/render-current.sh
  -> prepare-qmd-for-pptx.py
  -> Quarto / Pandoc
  -> postprocess-pptx.py
  -> final PPTX
```

標準利用環境は、Windows で Docker Desktop を起動し、VS Code から Reopen in Container して Dev Container 内で作業する。

次は、生成した PPTX を VS Code 内で preview するのではなく、ホスト Windows 側の Microsoft PowerPoint で直接開くところまでを正式ワークフローにする。

## 目的

```text
QMD build
  -> Dev Container で PPTX生成
  -> host bridge
  -> Microsoft PowerPointで生成PPTXを開く
```

## 設計原則

- build / render logic は Dev Container 側に置く
- host 側は PPTX を開く最小責務だけ持つ
- PowerPoint を直接 container から spawn しない
- Remote/Dev Container対応のため VS Code UI/local side を bridge 候補とする
- 既存 `slidegen render` を壊さない
- docx を壊さない
- VS Code内Previewを復活させない
- M4より前に自動save watcherを実装しない

## 最初に行うPoC

- UI Extension / `vscode.env.openExternal` で host-side PPTX を開けるか
- container path `/work/...` と host workspace path のmapping
- `${localWorkspaceFolder}` の bridge利用
- Windows path / spaces / 日本語 path
- bridge unavailable 時の挙動

PoCが成立しない場合は、代替案を調査結果とともに止めて報告し、無理に別方式を実装しない。

## 対象外

- PPTX -> QMD
- assets.json
- stable IDs
- PPTX save watch
- QMD save watch
- dirty state
- conflict handling
- PowerPoint Add-in
- PPTX -> Word

## 完了条件

- Windows標準環境でReopen in Container後に利用可能
- QMD build成功後に正しいPPTXがPowerPointで開く
- build failure時は開かない
- bridge failureでrender自体を失敗扱いにしない
- PPTX/docx回帰テストが通る
- README / PROJECT_CONTEXTを更新
- 実機未確認項目をPR本文に明記

詳細は `docs/M1_POWERPOINT_OPEN.md`。

## 状態

未完了。remote workspace buildとlocal UI openを2つの小さなVS Code extension packageに分割した。workspace-only構成ではWindows実機でremote `openExternal(file://C:/...)` が `vscode-remote` linkとして扱われることを確認したため、local UI extensionが `vscode.Uri.file` と `vscode.env.openExternal` を担う。2 package間の実機command routingおよびWindows PowerPoint E2Eは未確認。

自動配布も未解決。lifecycle hookからの `code --install-extension` はWindows実機でCLI不在により失敗し撤回済み。Dev Container設定へローカルVSIX pathを指定できず、extensionも未公開のため通常のReopen in Containerだけではcommandが使えない。PR #14はDraftを維持し、M1 GateはFAIL。
