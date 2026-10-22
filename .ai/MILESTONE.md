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

- QMDを既存 `slidegen render` 経路でPPTXへbuildできる
- Workspace extensionがDev Container側でbuildし、Local UI extensionがhost側でPPTXを開く
- QMD build成功後に正しいPPTXがPowerPointで開く
- build failure時は開かない
- bridge failureでrender自体を失敗扱いにしない
- Windows実機で二層extension構成とPowerPoint openが確認済み
- PPTX/docx回帰テストが通る
- Preview / PDF.js / Webview / LibreOfficeを復活させない
- tests / smoke test / render / docx regression / latest PR head CI がPASS
- README / PROJECT_CONTEXTを更新

Marketplace公開、publisher設定、`customizations.vscode.extensions`による自動配布、通常のReopen in Containerからの手動installなしの導入、および公開後E2EはM1完了条件に含めない。これらは正式リリース前の横断的なRelease / Distribution gateとして保持する。

詳細は `docs/M1_POWERPOINT_OPEN.md`。

## 状態

実装完了。Windows実機でLocal UI extensionとDev Container Workspace extensionを各hostへ配置し、command表示、cross-host command routing、container build、host path mapping、正しいPPTXのPowerPoint openを確認済み。build failure時にopenしないこと、bridge failureでもbuild成功結果を維持すること、PPTX/docx回帰、禁止scopeに戻っていないこと、CI PASSを完了条件とする。

Marketplace公開と通常のReopen in Containerからの自動配布は正式リリース前のRelease / Distribution gateであり、M1の未完了理由ではない。PR #14をDraft解除可能とするための判断にMarketplace公開は不要。詳細は `docs/ROADMAP.md` と `.ai/HUMAN_GATES.md`。
