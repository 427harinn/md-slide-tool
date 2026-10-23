import * as vscode from 'vscode';
import path from 'node:path';
import { spawn } from 'node:child_process';
import fs from 'node:fs/promises';
import { buildPptxForHost } from './hostBridge.js';
import { cleanupT401HostPptxProbe, stageT401HostPptxProbe } from './t401Probe.js';

const BUILD_COMMAND = 'mdSlideTool.buildRemotePptx';
const T401_STAGE_COMMAND = 'mdSlideTool.t401.stageHostPptx';
const T401_CLEANUP_COMMAND = 'mdSlideTool.t401.cleanupHostPptx';

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
  const output = vscode.window.createOutputChannel('md-slide-tool PowerPoint Build');
  context.subscriptions.push(output);
  context.subscriptions.push(vscode.commands.registerCommand(BUILD_COMMAND, async (qmdUriString) => {
    if (typeof qmdUriString !== 'string') throw new Error('The UI extension did not provide a QMD URI.');
    const qmdUri = vscode.Uri.parse(qmdUriString);
    const qmdPath = path.posix.resolve(qmdUri.path);
    const workspace = vscode.workspace.workspaceFolders?.find((folder) => {
      const folderPath = path.posix.resolve(folder.uri.fsPath);
      const relative = path.posix.relative(folderPath, qmdPath);
      return relative !== '..' && !relative.startsWith('../') && !path.posix.isAbsolute(relative);
    });
    if (!qmdPath.toLowerCase().endsWith('.qmd') || !workspace) {
      throw new Error('Select a QMD file inside the Dev Container workspace.');
    }

    try {
      const result = await buildPptxForHost({
        qmdPath,
        workspacePath: workspace.uri.fsPath,
        hostWorkspace: process.env.MD_SLIDE_TOOL_HOST_WORKSPACE,
        runBuild: (qmdPath) => runRender(qmdPath, workspace.uri.fsPath),
        outputExists: async (filePath) => fs.stat(filePath).then((stat) => stat.isFile(), () => false),
      });
      if (result.status === 'built-host-bridge-unavailable') {
        output.appendLine(`PPTX build succeeded: ${result.pptxPath}`);
        output.appendLine(`Host path mapping failed: ${result.error}`);
      }
      return result;
    } catch (error) {
      output.appendLine(error?.stack ?? String(error));
      throw error;
    }
  }));
  context.subscriptions.push(vscode.commands.registerCommand(T401_STAGE_COMMAND, async (probeId) => {
    const workspace = vscode.workspace.workspaceFolders?.[0];
    if (!workspace) throw new Error('Open the repository in the Dev Container before running T-401.');
    return stageT401HostPptxProbe({
      workspacePath: workspace.uri.fsPath,
      hostWorkspace: process.env.MD_SLIDE_TOOL_HOST_WORKSPACE,
      probeId,
    });
  }));
  context.subscriptions.push(vscode.commands.registerCommand(T401_CLEANUP_COMMAND, async (probeId) => {
    const workspace = vscode.workspace.workspaceFolders?.[0];
    if (!workspace) throw new Error('Open the repository in the Dev Container before running T-401.');
    return cleanupT401HostPptxProbe({ workspacePath: workspace.uri.fsPath, probeId });
  }));
}

export function deactivate() {}
