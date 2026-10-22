import * as vscode from 'vscode';
import { resolvePptxTarget } from './fileSelection.js';
import { PreviewPanel } from './preview/previewPanel.js';
import { PreviewError } from './preview/errors.js';
import { buildAndOpenPowerPoint } from './hostBridge.js';
import path from 'node:path';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';

function runRender(qmdPath, workspaceRoot) {
  return new Promise((resolve, reject) => {
    const slidegenCli = path.posix.join(workspaceRoot, 'cli', 'slidegen.js');
    const child = spawn('node', [slidegenCli, 'render', qmdPath], { cwd: workspaceRoot, stdio: 'inherit' });
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
  context.subscriptions.push(vscode.commands.registerCommand('mdSlideTool.buildAndOpenPowerPoint', async (uri) => {
    const workspace = vscode.workspace.workspaceFolders?.[0];
    const qmdUri = uri instanceof vscode.Uri ? uri : vscode.window.activeTextEditor?.document.uri;
    if (!workspace || !qmdUri || qmdUri.scheme !== 'file' || qmdUri.fsPath.toLowerCase().endsWith('.qmd') === false) {
      vscode.window.showErrorMessage('Open or select a QMD file inside the Dev Container workspace.');
      return;
    }

    try {
      const result = await buildAndOpenPowerPoint({
        qmdPath: qmdUri.fsPath,
        workspaceRoot: workspace.uri.fsPath,
        hostWorkspace: process.env.MD_SLIDE_TOOL_HOST_WORKSPACE,
        runBuild: (qmdPath) => runRender(qmdPath, workspace.uri.fsPath),
        outputExists: async (pptxPath) => fs.stat(pptxPath).then((stat) => stat.isFile(), () => false),
        openExternal: (fileUri) => vscode.env.openExternal(vscode.Uri.parse(fileUri)),
      });
      if (result.status === 'built-host-bridge-unavailable') {
        output.appendLine(`Build succeeded: ${result.pptxPath}`);
        output.appendLine(`Host bridge unavailable: ${result.error?.stack ?? 'openExternal returned false'}`);
        vscode.window.showWarningMessage(`PPTX build succeeded, but PowerPoint could not be opened. Output: ${result.pptxPath}`);
      } else {
        vscode.window.showInformationMessage(`PPTX built and opened in PowerPoint: ${result.pptxPath}`);
      }
    } catch (error) {
      output.appendLine(error?.stack ?? String(error));
      vscode.window.showErrorMessage(`PPTX build failed. PowerPoint was not opened. ${error.message}`);
    }
  }));
  context.subscriptions.push(vscode.commands.registerCommand('mdSlideTool.openPptxPreview', async (uri) => {
    try {
      const target = await resolvePptxTarget(uri);
      if (!target) return;
      await PreviewPanel.open(context, target, output);
    } catch (error) {
      const message = error instanceof PreviewError ? error.userMessage : 'Could not open PPTX preview.';
      output.appendLine(error?.detail ?? error?.stack ?? String(error));
      vscode.window.showErrorMessage(message);
    }
  }));
}

export function deactivate() {}
