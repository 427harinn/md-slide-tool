# M1: QMD から PowerPoint を開く

## 実行方式

VS Code extension の `Build and Open in Microsoft PowerPoint` command が、workspace extension host (Dev Container) 内で既存の `scripts/render-current.sh` を実行します。build 成功後だけ `vscode.env.openExternal` に `file:` URI を渡します。VS Code / OS の file association が `.pptx` を既に起動している PowerPoint に渡します。

変換処理や PPTX の編集・監視は extension に実装していません。既存の `slidegen render` と同じ render script を使います。

## Path mapping

`.devcontainer/devcontainer.json` は `${localWorkspaceFolder}` を `MD_SLIDE_TOOL_HOST_WORKSPACE` として container extension host に渡します。container workspace は `/work` です。extension は生成 PPTX の `/work` からの相対 path を求め、Windows の場合はそれを host workspace path に `path.win32.resolve` で結合し、Windows `file:///C:/...` URI として符号化します。POSIX host の場合は `path.resolve` と `pathToFileURL` を使います。workspace 外の path は拒否します。

例:

```text
/work/projects/資料 folder/発表.pptx
  -> C:\Users\name\Documents\GitHub\md-slide-tool\projects\資料 folder\発表.pptx
  -> file:///C:/Users/name/Documents/GitHub/md-slide-tool/projects/%E8%B3%87%E6%96%99%20folder/%E7%99%BA%E8%A1%A8.pptx
```

## 利用方法

この checkout の extension を使う場合は VS Code で `vscode-extension/.vscode/launch.json` の **Run Extension** を起動し、Extension Development Host で Dev Container workspace を開きます。QMD を Explorer で右クリックして **Build and Open in Microsoft PowerPoint** を選択します。active QMD を開いている場合は Command Palette からも実行できます。

M1 は QMD 保存時自動 build や PPTX 保存監視を追加しません。

## 検証

自動テストは `vscode-extension/test/hostBridge.test.js` で Windows/POSIX path mapping、空白と日本語、workspace 外拒否、build failure、bridge unavailable を確認します。

### Windows 実機で必要な確認

- Docker Desktop を起動し、Dev Containers: Reopen in Container を実行する。
- Extension Development Host 上で `MD_SLIDE_TOOL_HOST_WORKSPACE` が Windows workspace path に展開されていることを確認する。
- 空白と日本語を含む Windows workspace path 上の QMD を build する。
- build 成功後に PowerPoint が開くこと、PowerPoint 起動済みでも既存 instance が対象 PPTX を開くことを確認する。
- Quarto failure 時に PowerPoint が開かないことを確認する。
- host bridge が利用できない場合も PPTX が生成済みで command が build success と警告を報告することを確認する。

これらの GUI / Windows 実機確認は今回の container 実行環境では未確認です。自動テストは `vscode.env.openExternal` の VS Code Remote から Windows file association への実機配送までは証明しません。
