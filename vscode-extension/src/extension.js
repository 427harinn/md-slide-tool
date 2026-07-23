import * as vscode from 'vscode';
import { resolvePptxTarget } from './fileSelection.js';
import { PreviewPanel } from './preview/previewPanel.js';
import { PreviewError } from './preview/errors.js';

export function activate(context) {
  const output = vscode.window.createOutputChannel('md-slide-tool PPTX Preview');
  context.subscriptions.push(output);
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
