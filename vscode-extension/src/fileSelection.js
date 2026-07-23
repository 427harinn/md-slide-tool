import * as vscode from 'vscode'; import { validatePptxPath, isPptxPath } from './preview/fileValidation.js';
function uriPath(uri) { return uri?.fsPath; }
export async function resolvePptxTarget(arg) {
  const candidates = [uriPath(arg), uriPath(vscode.window.activeTextEditor?.document?.uri)].filter(Boolean);
  for (const c of candidates) { if (isPptxPath(c)) return validatePptxPath(c); }
  const picked = await vscode.window.showOpenDialog({ canSelectMany:false, filters:{ 'PowerPoint files':['pptx'] }, title:'Select a PPTX file to preview' });
  if (!picked?.[0]) return null; return validatePptxPath(picked[0].fsPath);
}
