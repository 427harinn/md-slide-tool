import fs from 'node:fs/promises';
import path from 'node:path';
import * as vscode from 'vscode';

export function isQmdPath(filePath) {
  return typeof filePath === 'string' && path.extname(filePath).toLowerCase() === '.qmd';
}

export function getPptxPathForQmd(qmdPath) {
  return path.join(path.dirname(qmdPath), `${path.basename(qmdPath, path.extname(qmdPath))}.pptx`);
}

export async function validateQmdPath(filePath) {
  if (!isQmdPath(filePath)) {
    throw new Error('Please open or select a .qmd file before starting auto preview.');
  }

  const stat = await fs.stat(filePath);
  if (!stat.isFile()) {
    throw new Error('The selected QMD path is not a file.');
  }

  return path.resolve(filePath);
}

export function getWorkspaceRootForPath(filePath) {
  const uri = vscode.Uri.file(filePath);
  const folder = vscode.workspace.getWorkspaceFolder(uri);
  return folder?.uri.fsPath ?? vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

function uriPath(uri) {
  return uri?.fsPath;
}

export async function resolveQmdTarget(arg) {
  const candidates = [
    uriPath(arg),
    uriPath(vscode.window.activeTextEditor?.document?.uri)
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (isQmdPath(candidate)) {
      const qmdPath = await validateQmdPath(candidate);
      return {
        qmdPath,
        pptxPath: getPptxPathForQmd(qmdPath),
        workspaceRoot: getWorkspaceRootForPath(qmdPath)
      };
    }
  }

  throw new Error('Please open a .qmd file before starting auto preview.');
}
