import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { exactQmdState, applyCandidateThroughWorkspaceApi, contentHash, pendingFallbackDecision } from '../extensions/workspace/src/m4EditorProbe.js';

function doc(filePath, text, { dirty = false, version = 3 } = {}) {
  return { uri: { scheme: 'file', fsPath: filePath }, isDirty: dirty, version, text,
    getText() { return this.text; }, positionAt: (offset) => offset,
    save: async function () { this.isDirty = false; return true; } };
}

function editorFor(document, beforeCallback = () => {}) {
  return { document, edit: async (callback) => {
    beforeCallback(document);
    let pending;
    callback({ replace(_range, value) { pending = value; } });
    if (pending === undefined) return false;
    document.text = pending;
    document.version++;
    document.isDirty = true;
    return true;
  } };
}

function apiFor(diskRead) {
  return { Range: class { constructor() {} }, workspace: { fs: { readFile: diskRead } } };
}

test('exact QMD state ignores similarly named documents and detects dirty duplicate tabs', () => {
  const qmdPath = path.resolve('/workspace/deck.qmd');
  const vscode = { workspace: { textDocuments: [
    doc(path.resolve('/workspace/deck-copy.qmd'), 'other'),
    doc(qmdPath, 'one'), doc(qmdPath, 'two', { dirty: true }),
  ] } };
  assert.equal(exactQmdState(vscode, qmdPath).state, 'open-dirty');
  assert.equal(exactQmdState({ workspace: { textDocuments: [] } }, qmdPath).state, 'closed');
});

test('exact QMD state matches VS Code remote URI scheme and authority', () => {
  const uri = { scheme: 'vscode-remote', authority: 'dev-container+mdst', path: '/work/deck.qmd' };
  const vscode = { workspace: { textDocuments: [
    { uri: { ...uri, authority: 'ssh-remote+other' }, isDirty: false },
    { uri, isDirty: false },
  ] } };
  assert.equal(exactQmdState(vscode, uri).state, 'open-clean');
});

test('closed QMD imports through M3, open-clean stays Pending, and dirty becomes Conflict', () => {
  assert.equal(pendingFallbackDecision('closed'), 'M3_IMPORT');
  assert.equal(pendingFallbackDecision('open-clean'), 'PENDING');
  assert.equal(pendingFallbackDecision('open-dirty'), 'CONFLICT');
});

test('candidate apply refuses dirty, wrong-target, and stale version before edit', async () => {
  const filePath = path.resolve('/workspace/deck.qmd');
  const expected = { qmdPath: filePath, version: 3, savedHash: contentHash('saved') };
  const api = apiFor(async () => Buffer.from('saved'));
  assert.equal((await applyCandidateThroughWorkspaceApi(api, editorFor(doc(path.resolve('/workspace/other.qmd'), 'saved')), 'candidate', expected)).status, 'wrong-document');
  assert.equal((await applyCandidateThroughWorkspaceApi(api, editorFor(doc(filePath, 'saved', { dirty: true })), 'candidate', expected)).status, 'conflict-dirty');
  assert.equal((await applyCandidateThroughWorkspaceApi(api, editorFor(doc(filePath, 'user edit', { version: 4 })), 'candidate', expected)).status, 'stale-candidate');
});

test('candidate apply compares remote URI scheme and authority, not only fsPath', async () => {
  const expectedUri = { scheme: 'vscode-remote', authority: 'dev-container+deck', path: '/work/deck.qmd' };
  const document = {
    uri: { ...expectedUri, authority: 'ssh-remote+other' }, isDirty: false, version: 3,
    getText() { return 'saved'; }, positionAt: (offset) => offset,
  };
  const result = await applyCandidateThroughWorkspaceApi(apiFor(async () => Buffer.from('saved')),
    editorFor(document), 'candidate', {
      qmdUri: expectedUri, version: 3, savedHash: contentHash('saved'),
    });
  assert.equal(result.status, 'wrong-document');
});

test('candidate helper applies and saves through TextEditor API for matching clean version', async () => {
  const filePath = path.resolve('/workspace/deck.qmd');
  const document = doc(filePath, 'saved', { version: 3 });
  const api = apiFor(async () => Buffer.from(document.getText(), 'utf8'));
  const result = await applyCandidateThroughWorkspaceApi(api, editorFor(document), 'candidate', {
    qmdPath: filePath, version: 3, savedHash: contentHash('saved'),
  });
  assert.equal(result.status, 'saved');
  assert.equal(result.savedHash, contentHash('candidate'));
  assert.equal(result.diskHash, contentHash('candidate'));
  assert.equal(document.getText(), 'candidate');
});

test('candidate save is rejected when on-disk bytes differ from UTF-8 candidate', async () => {
  const filePath = path.resolve('/workspace/deck.qmd');
  const document = doc(filePath, 'saved', { version: 3 });
  const api = apiFor(async () => Buffer.from('candidate\r\n', 'utf8'));
  const result = await applyCandidateThroughWorkspaceApi(api, editorFor(document), 'candidate', {
    qmdPath: filePath, version: 3, savedHash: contentHash('saved'),
  });
  assert.equal(result.status, 'save-mismatch');
});

test('user edit injected immediately before TextEditor edit callback refuses stale candidate', async () => {
  const filePath = path.resolve('/workspace/deck.qmd');
  const document = doc(filePath, 'saved', { version: 3 });
  const editor = editorFor(document, (current) => {
    current.text = 'user edit';
    current.version++;
    current.isDirty = true;
  });
  const result = await applyCandidateThroughWorkspaceApi(apiFor(async () => Buffer.from('user edit')), editor, 'candidate', {
    qmdPath: filePath, version: 3, savedHash: contentHash('saved'),
  });
  assert.equal(result.status, 'conflict-dirty');
  assert.equal(document.getText(), 'user edit');
});
