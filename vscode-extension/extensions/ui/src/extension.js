import * as vscode from 'vscode';
import { randomUUID } from 'node:crypto';
import { buildAndOpenLocally } from './hostBridge.js';
import { inspectT401StagedFile } from './t401Probe.js';

const T401_PROBE_ID = 'mdSlideTool.t401.verifyHostPptxAccess';
const T401_STAGE_COMMAND = 'mdSlideTool.t401.stageHostPptx';
const T401_CLEANUP_COMMAND = 'mdSlideTool.t401.cleanupHostPptx';

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
  context.subscriptions.push(vscode.commands.registerCommand(T401_PROBE_ID, async () => {
    const probeId = randomUUID();
    let staged;
    try {
      staged = await vscode.commands.executeCommand(T401_STAGE_COMMAND, probeId);
      if (!staged?.hostPath || !staged?.sha256) throw new Error('Workspace probe did not return a mapped staged file.');
      const result = await inspectT401StagedFile({ hostPath: staged.hostPath, expectedHash: staged.sha256 });
      if (result.status !== 'READ_OK') throw new Error(`Local UI could not verify staged PPTX: ${result.reason ?? result.status}`);
      vscode.window.showInformationMessage(`T-401 staged PPTX is readable from Windows Local UI (${result.bytesRead} bytes, SHA-256 verified).`);
      return { ...result, containerPath: staged.containerPath, probeId };
    } catch (error) {
      vscode.window.showErrorMessage(`T-401 staged PPTX access failed: ${error.message}`);
      return { status: 'UNAVAILABLE', probeId, error: error.message };
    } finally {
      if (staged?.probeId) {
        await vscode.commands.executeCommand(T401_CLEANUP_COMMAND, staged.probeId).catch(() => {});
      }
    }
  }));
}

export function deactivate() {}
