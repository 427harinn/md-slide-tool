import * as vscode from 'vscode';
import { resolvePptxTarget } from './fileSelection.js';
import { PreviewPanel } from './preview/previewPanel.js';
import { PreviewError } from './preview/errors.js';
import { AutoPreviewController } from './autoPreview/autoPreviewController.js';

export function activate(context) {
  const output = vscode.window.createOutputChannel('md-slide-tool PPTX Preview');
  context.subscriptions.push(output);
  const autoPreview = new AutoPreviewController(context, output);
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
  context.subscriptions.push(vscode.commands.registerCommand('mdSlideTool.startAutoPreview', async (uri) => {
    try {
      await autoPreview.start(uri);
    } catch (error) {
      output.appendLine(error?.detail ?? error?.stack ?? String(error));
      vscode.window.showErrorMessage(error?.message ?? 'Could not start Auto Preview.');
    }
  }));
  context.subscriptions.push(vscode.commands.registerCommand('mdSlideTool.stopAutoPreview', () => {
    autoPreview.stop();
  }));
}

export function deactivate() {}
