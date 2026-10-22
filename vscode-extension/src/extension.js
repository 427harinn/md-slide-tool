import * as vscode from 'vscode';
import path from 'node:path';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import { buildAndOpenPowerPoint } from './hostBridge.js';

function runRender(qmdPath, workspacePath) {
  return new Promise((resolve, reject) => {
    const cliPath = path.posix.join(workspacePath, 'cli', 'slidegen.js');
    const child = spawn('node', [cliPath, 'render', qmdPath], { cwd: workspacePath, stdio: 'inherit' });
    child.once('error', reject);
    child.once('close', (code, signal) => {
      if (signal) reject(new Error(`PPTX build stopped by signal: ${signal}`));
      else if (code !== 0) reject(new Error(`PPTX build failed with exit code ${code ?? 1}.`));
      else resolve();
    });
  });
}

export function activate(context) {
  const output = vscode.window.createOutputChannel('md-slide-tool PowerPoint');
  context.subscriptions.push(output);
  context.subscriptions.push(vscode.commands.registerCommand('mdSlideTool.buildAndOpenPowerPoint', async (resource) => {
    const selectedUri = resource instanceof vscode.Uri ? resource : vscode.window.activeTextEditor?.document.uri;
    const workspace = selectedUri && vscode.workspace.getWorkspaceFolder(selectedUri);
    if (!selectedUri || selectedUri.scheme !== 'file' || !selectedUri.path.toLowerCase().endsWith('.qmd') || !workspace) {
      vscode.window.showErrorMessage('Open or select a QMD file in the Dev Container workspace.');
      return;
    }

    try {
      const result = await buildAndOpenPowerPoint({
        qmdPath: selectedUri.fsPath,
        workspacePath: workspace.uri.fsPath,
        hostWorkspace: process.env.MD_SLIDE_TOOL_HOST_WORKSPACE,
        runBuild: (qmdPath) => runRender(qmdPath, workspace.uri.fsPath),
        outputExists: async (filePath) => fs.stat(filePath).then((stat) => stat.isFile(), () => false),
        openExternal: (fileUri) => vscode.env.openExternal(vscode.Uri.parse(fileUri)),
      });

      if (result.status === 'built-host-bridge-unavailable') {
        output.appendLine(`PPTX build succeeded: ${result.pptxPath}`);
        output.appendLine(`Host bridge failed: ${result.error?.stack ?? 'openExternal returned false'}`);
        vscode.window.showWarningMessage(`PPTX build succeeded, but PowerPoint could not be opened. Output: ${result.hostPath ?? result.pptxPath}`);
      } else {
        vscode.window.showInformationMessage(`PPTX built and opened in PowerPoint: ${result.hostPath}`);
      }
    } catch (error) {
      output.appendLine(error?.stack ?? String(error));
      vscode.window.showErrorMessage(`PPTX build failed. PowerPoint was not opened. ${error.message}`);
    }
  }));
}
