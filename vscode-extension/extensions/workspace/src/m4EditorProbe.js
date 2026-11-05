import path from 'node:path';
import { createHash } from 'node:crypto';
import { Buffer } from 'node:buffer';

export function contentHash(text) {
  return createHash('sha256').update(text, 'utf8').digest('hex');
}

function canonical(filePath) {
  return process.platform === 'win32'
    ? path.resolve(filePath).toLocaleLowerCase('en-US')
    : path.resolve(filePath);
}

export function exactQmdState(vscode, qmdPath) {
  const target = typeof qmdPath === 'string' ? null : {
    scheme: qmdPath.scheme,
    authority: qmdPath.authority ?? '',
    path: qmdPath.scheme === 'file' ? canonical(qmdPath.fsPath) : path.posix.resolve(qmdPath.path),
  };
  const targetPath = target ? null : canonical(qmdPath);
  const matches = vscode.workspace.textDocuments.filter((doc) =>
    target
      ? doc.uri.scheme === target.scheme && (doc.uri.authority ?? '') === target.authority &&
        (doc.uri.scheme === 'file' ? canonical(doc.uri.fsPath) : path.posix.resolve(doc.uri.path)) === target.path
      : (doc.uri.scheme === 'file' ? canonical(doc.uri.fsPath) : path.posix.resolve(doc.uri.path)) === targetPath);
  if (!matches.length) return { state: 'closed', documents: [] };
  return {
    state: matches.some((doc) => doc.isDirty) ? 'open-dirty' : 'open-clean',
    documents: matches,
  };
}

export function pendingFallbackDecision(state) {
  if (state === 'closed') return 'M3_IMPORT';
  if (state === 'open-dirty') return 'CONFLICT';
  return 'PENDING';
}

function sameDocumentUri(actual, expected) {
  if (!actual || !expected || actual.scheme !== expected.scheme ||
      (actual.authority ?? '') !== (expected.authority ?? '')) return false;
  const actualPath = actual.scheme === 'file' ? canonical(actual.fsPath) : path.posix.resolve(actual.path);
  const expectedPath = expected.scheme === 'file' ? canonical(expected.fsPath) : path.posix.resolve(expected.path);
  return actualPath === expectedPath;
}

export async function applyCandidateThroughWorkspaceApi(vscode, editor, candidate, expected) {
  const document = editor.document;
  const expectedUri = expected.qmdUri ?? { scheme: 'file', fsPath: expected.qmdPath };
  if (!sameDocumentUri(document.uri, expectedUri)) return { status: 'wrong-document' };
  let refusal;
  const applied = await editor.edit((builder) => {
    // TextEditor.edit creates the edit from the currently active document version.
    // Recheck inside its synchronous callback so the candidate cannot use an
    // earlier version/hash observed before the editor schedules this edit.
    if (document.isDirty) { refusal = 'conflict-dirty'; return; }
    if (document.version !== expected.version || contentHash(document.getText()) !== expected.savedHash) {
      refusal = 'stale-candidate';
      return;
    }
    builder.replace(new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length)), candidate);
  });
  if (refusal) return { status: refusal };
  if (!applied) return { status: 'apply-failed' };
  if (document.getText() !== candidate) return { status: 'apply-mismatch' };
  if (!(await document.save())) return { status: 'save-failed' };
  if (document.isDirty || document.getText() !== candidate) return { status: 'save-mismatch' };
  const diskBytes = Buffer.from(await vscode.workspace.fs.readFile(document.uri));
  const candidateBytes = Buffer.from(candidate, 'utf8');
  if (!diskBytes.equals(candidateBytes)) return { status: 'save-mismatch' };
  return {
    status: 'saved', version: document.version, savedHash: contentHash(document.getText()),
    diskHash: createHash('sha256').update(diskBytes).digest('hex'),
  };
}
