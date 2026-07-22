import fs from 'node:fs/promises';
import path from 'node:path';
import * as vscode from 'vscode';
import { findLibreOffice } from './libreOfficeLocator.js';
import { convertPptxToPdf } from './pptxToPdf.js';
import { PreviewError, messages } from './errors.js';

function esc(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  })[char]);
}

export class PreviewPanel {
  static panels = new Map();

  static async open(context, pptxPath, output) {
    const key = path.resolve(pptxPath);
    const existing = this.panels.get(key);
    if (existing) {
      existing.panel.reveal();
      existing.refresh();
      return existing;
    }

    const storageRoot = vscode.Uri.joinPath(context.globalStorageUri, 'pptx-preview');
    await vscode.workspace.fs.createDirectory(storageRoot);

    const panel = vscode.window.createWebviewPanel(
      'pptxPreview',
      `PPTX: ${path.basename(pptxPath)}`,
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        localResourceRoots: [
          vscode.Uri.file(path.join(context.extensionPath, 'webview')),
          storageRoot
        ]
      }
    );
    const preview = new PreviewPanel(context, panel, pptxPath, output, storageRoot.fsPath);
    this.panels.set(key, preview);
    preview.refresh();
    return preview;
  }

  constructor(context, panel, pptxPath, output, storageRoot) {
    this.context = context;
    this.panel = panel;
    this.pptxPath = pptxPath;
    this.output = output;
    this.storageRoot = storageRoot;
    this.phase = 'idle';
    this.currentWorkspace = null;
    this.pendingWorkspace = null;
    this.abort = null;
    panel.onDidDispose(() => this.dispose());
    panel.webview.onDidReceiveMessage((message) => this.handleMessage(message));
    this.renderShell();
  }

  handleMessage(message) {
    if (message?.type === 'refresh') this.refresh();
    if (message?.type === 'renderComplete') this.finishRender(true, message);
    if (message?.type === 'renderFailed') this.finishRender(false, message);
  }

  async finishRender(success, message) {
    if (success) {
      await this.currentWorkspace?.dispose(this.output);
      this.currentWorkspace = this.pendingWorkspace;
    } else {
      await this.pendingWorkspace?.dispose(this.output);
      this.output.appendLine(`[renderFailed] ${message?.message ?? 'PDF render failed'}`);
    }
    this.pendingWorkspace = null;
    this.phase = 'idle';
    this.post({ type: 'idle' });
  }

  async dispose() {
    PreviewPanel.panels.delete(path.resolve(this.pptxPath));
    this.abort?.abort();
    await this.pendingWorkspace?.dispose(this.output);
    await this.currentWorkspace?.dispose(this.output);
  }

  post(message) {
    try {
      this.panel.webview.postMessage(message);
    } catch {
      // Webview was disposed while an async operation was finishing.
    }
  }

  renderShell() {
    const webview = this.panel.webview;
    const nonce = String(Date.now());
    const script = webview.asWebviewUri(vscode.Uri.file(path.join(this.context.extensionPath, 'webview', 'viewer.js')));
    const css = webview.asWebviewUri(vscode.Uri.file(path.join(this.context.extensionPath, 'webview', 'viewer.css')));
    const pdfjs = webview.asWebviewUri(vscode.Uri.file(path.join(this.context.extensionPath, 'webview', 'pdf.mjs')));
    const worker = webview.asWebviewUri(vscode.Uri.file(path.join(this.context.extensionPath, 'webview', 'pdf.worker.mjs')));
    this.panel.webview.html = `<!doctype html><html><head><meta charset="UTF-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${webview.cspSource} data:; style-src ${webview.cspSource}; script-src 'nonce-${nonce}' ${webview.cspSource}; worker-src ${webview.cspSource} blob:;"><link rel="stylesheet" href="${css}"><title>${esc(path.basename(this.pptxPath))}</title></head><body><header><div><h1>${esc(path.basename(this.pptxPath))}</h1><p id="status">Ready</p></div><button id="refresh">Refresh</button></header><main><div id="error" hidden></div><div id="slides"></div></main><script nonce="${nonce}">window.__PDFJS_URL__=${JSON.stringify(String(pdfjs))};window.__PDFJS_WORKER_URL__=${JSON.stringify(String(worker))};</script><script nonce="${nonce}" type="module" src="${script}"></script></body></html>`;
  }

  async refresh() {
    if (this.phase !== 'idle') return;
    this.phase = 'converting';
    this.abort = new AbortController();
    this.post({ type: 'loading', message: 'Converting PPTX…' });
    try {
      await fs.mkdir(this.storageRoot, { recursive: true });
      const libreOffice = await findLibreOffice();
      if (!libreOffice.found) {
        throw new PreviewError('libreOfficeMissing', messages.libreOfficeMissing, `Checked: ${libreOffice.candidates.join(', ')}`);
      }
      const result = await convertPptxToPdf({
        pptxPath: this.pptxPath,
        libreOfficePath: libreOffice.path,
        outputRoot: this.storageRoot,
        signal: this.abort.signal,
        logger: this.output
      });
      this.pendingWorkspace = result.workspace;
      this.phase = 'rendering';
      const pdfUri = this.panel.webview.asWebviewUri(vscode.Uri.file(result.pdfPath));
      this.post({ type: 'pdf', uri: String(pdfUri) });
    } catch (error) {
      const previewError = error instanceof PreviewError
        ? error
        : new PreviewError('unknown', 'PPTX preview failed.', error?.message ?? String(error), error);
      this.output.appendLine(`[${previewError.code}] ${previewError.detail}`);
      this.phase = 'idle';
      this.post({ type: 'error', code: previewError.code, message: previewError.userMessage });
      this.post({ type: 'idle' });
    } finally {
      this.abort = null;
    }
  }
}

export { esc as escapeHtml };
