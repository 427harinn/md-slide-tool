import path from 'node:path';
import * as vscode from 'vscode';
import { PreviewPanel } from '../preview/previewPanel.js';
import { renderQmdToPptx } from './renderQmd.js';
import { getPptxPathForQmd, resolveQmdTarget } from './qmdTarget.js';

const debounceMs = 500;

function samePath(a, b) {
  return path.resolve(a) === path.resolve(b);
}

export class AutoPreviewController {
  constructor(context, output, options = {}) {
    this.context = context;
    this.output = output;
    this.renderer = options.renderer ?? renderQmdToPptx;
    this.previewPanel = options.previewPanel ?? PreviewPanel;
    this.target = null;
    this.timer = null;
    this.running = false;
    this.pending = false;
    this.abort = null;
    this.lastErrorNotification = null;
    this.statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    this.statusBar.command = 'mdSlideTool.startAutoPreview';
    this.setState('notStarted');

    context.subscriptions.push(
      this.statusBar,
      vscode.workspace.onDidSaveTextDocument((document) => this.handleSave(document)),
      { dispose: () => this.dispose() }
    );
  }

  isEnabled() {
    return vscode.workspace.getConfiguration('mdSlideTool.autoPreview').get('enabled', true);
  }

  async start(arg) {
    if (!this.isEnabled()) {
      vscode.window.showInformationMessage('Auto Preview is disabled. Enable mdSlideTool.autoPreview.enabled in VS Code settings to use it.');
      this.setState('disabled');
      return;
    }

    const target = await resolveQmdTarget(arg);
    if (!target.workspaceRoot) {
      throw new Error('No workspace folder is available for the selected QMD file.');
    }

    const alreadyWatching = this.target && samePath(this.target.qmdPath, target.qmdPath);
    if (!alreadyWatching && this.target) {
      this.output.appendLine(`[auto-preview] Switching target from ${this.target.qmdPath} to ${target.qmdPath}`);
      this.cancelScheduled();
      this.pending = false;
    }

    this.target = target;
    this.lastErrorNotification = null;
    this.setState('idle', target);

    vscode.window.showInformationMessage(
      alreadyWatching
        ? `Auto Preview is already watching ${path.basename(target.qmdPath)}.`
        : `Auto Preview started for ${path.basename(target.qmdPath)}.`
    );

    this.enqueueRender();
  }

  stop({ notify = true } = {}) {
    this.cancelScheduled();
    this.pending = false;
    this.target = null;
    this.abort?.abort();
    this.abort = null;
    this.setState('stopped');
    if (notify) vscode.window.showInformationMessage('Auto Preview stopped.');
  }

  handleSave(document) {
    if (!this.target) return;
    if (document.uri.scheme !== 'file') return;
    if (!samePath(document.uri.fsPath, this.target.qmdPath)) return;
    this.scheduleRender();
  }

  scheduleRender() {
    this.cancelScheduled();
    this.timer = setTimeout(() => {
      this.timer = null;
      this.enqueueRender();
    }, debounceMs);
  }

  enqueueRender() {
    if (!this.target) return;
    if (this.running) {
      this.pending = true;
      this.setState('pending', this.target);
      return;
    }
    void this.runRenderLoop();
  }

  async runRenderLoop() {
    let finalState = 'idle';
    while (this.target) {
      const target = this.target;
      this.running = true;
      this.pending = false;
      this.abort = new AbortController();
      this.setState('rendering', target);
      this.output.appendLine(`[auto-preview] Rendering ${target.qmdPath}`);

      try {
        await this.renderer({
          qmdPath: target.qmdPath,
          pptxPath: target.pptxPath,
          workspaceRoot: target.workspaceRoot,
          signal: this.abort.signal
        });
        this.output.appendLine(`[auto-preview] Rendered ${target.pptxPath}`);
        if (!this.target || !samePath(this.target.qmdPath, target.qmdPath)) break;
        this.setState('converting', target);
        await this.previewPanel.open(this.context, target.pptxPath, this.output, { preserveFocus: true });
        this.setState('success', target);
        finalState = 'success';
        this.lastErrorNotification = null;
      } catch (error) {
        if (!this.target || !samePath(this.target.qmdPath, target.qmdPath)) break;
        this.logError(error, target);
        this.setState('failed', target);
        finalState = 'failed';
        this.showDedupedError(error);
      } finally {
        this.abort = null;
        this.running = false;
      }

      if (!this.pending || !this.target || !samePath(this.target.qmdPath, target.qmdPath)) break;
    }

    if (this.target && !this.running) {
      this.setState(this.pending ? 'pending' : finalState, this.target);
    }
  }

  logError(error, target) {
    this.output.appendLine(`[auto-preview] Failed: ${target.qmdPath}`);
    this.output.appendLine(error?.detail ?? error?.stack ?? error?.message ?? String(error));
  }

  showDedupedError(error) {
    const message = error?.message ?? String(error);
    if (message === this.lastErrorNotification) return;
    this.lastErrorNotification = message;
    vscode.window.showErrorMessage(`Auto Preview failed. See "md-slide-tool PPTX Preview" output for details.`);
  }

  setState(state, target = this.target) {
    const label = target ? path.basename(target.qmdPath) : '';
    const states = {
      notStarted: '$(eye-closed) Auto Preview',
      disabled: '$(circle-slash) Auto Preview disabled',
      idle: `$(eye) Auto Preview: ${label}`,
      pending: `$(sync~spin) Auto Preview queued: ${label}`,
      rendering: `$(sync~spin) Rendering: ${label}`,
      converting: `$(sync~spin) Updating preview: ${label}`,
      success: `$(check) Auto Preview: ${label}`,
      failed: `$(error) Auto Preview failed: ${label}`,
      stopped: '$(debug-stop) Auto Preview stopped'
    };
    this.statusBar.text = states[state] ?? states.notStarted;
    this.statusBar.tooltip = target
      ? `QMD: ${target.qmdPath}\nPPTX: ${target.pptxPath ?? getPptxPathForQmd(target.qmdPath)}`
      : 'Start Auto Preview from a PPTX QMD file.';
    this.statusBar.show();
  }

  cancelScheduled() {
    if (!this.timer) return;
    clearTimeout(this.timer);
    this.timer = null;
  }

  dispose() {
    this.cancelScheduled();
    this.abort?.abort();
  }
}
