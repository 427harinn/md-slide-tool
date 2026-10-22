import * as vscode from 'vscode';
import { buildAndOpenLocally } from './hostBridge.js';

export function activate(context) {
  const output = vscode.window.createOutputChannel('md-slide-tool PowerPoint');
  context.subscriptions.push(output);
  context.subscriptions.push(vscode.commands.registerCommand('mdSlideTool.buildAndOpenPowerPoint', async (resource) => {
    const selectedUri = resource instanceof vscode.Uri ? resource : vscode.window.activeTextEditor?.document.uri;
    const workspace = selectedUri && vscode.workspace.getWorkspaceFolder(selectedUri);
    if (!selectedUri || !selectedUri.path.toLowerCase().endsWith('.qmd') || !workspace) {
      vscode.window.showErrorMessage('Open or select a QMD file in the Dev Container workspace.');
      return;
    }

    try {
      const result = await buildAndOpenLocally({
        qmdUri: selectedUri.toString(),
        executeCommand: (command, ...args) => vscode.commands.executeCommand(command, ...args),
        fileUri: (hostPath) => vscode.Uri.file(hostPath),
        openExternal: (uri) => vscode.env.openExternal(uri),
      });
      if (result.status === 'built-host-bridge-unavailable') {
        output.appendLine(`PPTX build succeeded: ${result.pptxPath ?? '(path unavailable)'}`);
        output.appendLine(`Host bridge failed: ${result.error}`);
        vscode.window.showWarningMessage(`PPTX build succeeded, but PowerPoint could not be opened. Output: ${result.hostPath ?? result.pptxPath ?? 'see the remote build output'}`);
      } else {
        vscode.window.showInformationMessage(`PPTX built and opened in PowerPoint: ${result.hostPath}`);
      }
    } catch (error) {
      output.appendLine(error?.stack ?? String(error));
      vscode.window.showErrorMessage(error.message);
    }
  }));
}

export function deactivate() {}
