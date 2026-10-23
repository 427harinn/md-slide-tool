import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {
  createT401MutationRequest,
  runT401MutationProbe,
  verifyT401HostStagedFile,
} from '../extensions/workspace/src/t401Probe.js';
import { inspectT401StagedFile } from '../extensions/ui/src/t401Probe.js';

const hash = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

test('T-401 request maps staged files under /work including Japanese and spaces', () => {
  const request = createT401MutationRequest({
    documentId: 'doc-1', freezeSessionId: 'freeze-1', transactionId: 'tx-1', operationIndex: 0,
    targetPath: '/work/projects/資料 folder/slides.pptx',
    stagedSource: '/work/.md-slide-tool/stage/tx-1/新しい slide.pptx',
    expectedOldHash: 'a'.repeat(64), newHash: 'b'.repeat(64),
    workspacePath: '/work', hostWorkspace: 'C:\\Users\\test\\資料 folder',
  });
  assert.equal(request.hostTargetPath, 'C:\\Users\\test\\資料 folder\\projects\\資料 folder\\slides.pptx');
  assert.equal(request.hostStagedSource, 'C:\\Users\\test\\資料 folder\\.md-slide-tool\\stage\\tx-1\\新しい slide.pptx');
  assert.equal(request.operationIndex, 0);
  assert.throws(() => createT401MutationRequest({
    documentId: 'd', freezeSessionId: 'f', transactionId: 't', operationIndex: 0,
    targetPath: '/outside/file.pptx', stagedSource: '/work/new.pptx',
    expectedAbsence: true, newHash: 'b'.repeat(64), workspacePath: '/work', hostWorkspace: 'C:\\work',
  }), /escapes the workspace/);
});

test('T-401 broker mutates only after freeze and expected-hash checks, then verifies the result', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 't401-broker-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const targetPath = path.join(root, 'target.pptx');
  const stagedSource = path.join(root, 'stage.pptx');
  await fs.writeFile(targetPath, 'old');
  await fs.writeFile(stagedSource, 'new');
  const request = {
    documentId: 'doc-1', freezeSessionId: 'freeze-1', transactionId: 'tx-1', operationIndex: 2,
    targetPath, stagedSource, expectedOldHash: hash('old'), expectedAbsence: false, newHash: hash('new'),
  };
  const result = await runT401MutationProbe({
    request, getFreezeState: async (id) => ({ freezeSessionId: id, state: 'committing' }),
  });
  assert.equal(result.status, 'MUTATED');
  assert.equal(result.resultingHash, hash('new'));
  assert.equal(await fs.readFile(targetPath, 'utf8'), 'new');
  assert.equal(result.operationIndex, 2);
});

test('T-401 broker returns NOT_MUTATED for a stale target hash', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 't401-race-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const targetPath = path.join(root, 'target.qmd');
  const stagedSource = path.join(root, 'stage.qmd');
  await fs.writeFile(targetPath, 'user edit');
  await fs.writeFile(stagedSource, 'generated');
  const request = {
    documentId: 'doc-1', freezeSessionId: 'freeze-2', transactionId: 'tx-2', operationIndex: 0,
    targetPath, stagedSource, expectedOldHash: hash('old'), expectedAbsence: false, newHash: hash('generated'),
  };
  const result = await runT401MutationProbe({
    request, getFreezeState: async (id) => ({ freezeSessionId: id, state: 'committing' }),
  });
  assert.equal(result.status, 'NOT_MUTATED');
  assert.equal(result.reason, 'expected-old-mismatch');
  assert.equal(await fs.readFile(targetPath, 'utf8'), 'user edit');
});

test('T-401 post-check detects a synchronous reopen race before actual replace', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 't401-reopen-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const targetPath = path.join(root, 'target.qmd');
  const stagedSource = path.join(root, 'stage.qmd');
  await fs.writeFile(targetPath, 'old');
  await fs.writeFile(stagedSource, 'new');
  const request = {
    documentId: 'doc-1', freezeSessionId: 'freeze-3', transactionId: 'tx-3', operationIndex: 0,
    targetPath, stagedSource, expectedOldHash: hash('old'), expectedAbsence: false, newHash: hash('new'),
  };
  let calls = 0;
  const result = await runT401MutationProbe({
    request,
    getFreezeState: async () => ({ freezeSessionId: 'freeze-3', state: calls++ === 0 ? 'committing' : 'invalidated' }),
  });
  assert.equal(result.status, 'NOT_MUTATED');
  assert.equal(result.reason, 'freeze-invalidated');
  assert.equal(await fs.readFile(targetPath, 'utf8'), 'old');
});

test('T-401 timeout is UNKNOWN and old broker work may complete late', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 't401-late-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const targetPath = path.join(root, 'target.pptx');
  const stagedSource = path.join(root, 'stage.pptx');
  await fs.writeFile(targetPath, 'old');
  await fs.writeFile(stagedSource, 'late new');
  const request = {
    documentId: 'doc-1', freezeSessionId: 'freeze-old', transactionId: 'tx-old', operationIndex: 0,
    targetPath, stagedSource, expectedOldHash: hash('old'), expectedAbsence: false, newHash: hash('late new'),
  };
  let release;
  const delayedReplace = new Promise((resolve) => { release = resolve; });
  const result = await runT401MutationProbe({
    request,
    getFreezeState: async () => ({ freezeSessionId: 'freeze-old', state: 'committing' }),
    timeoutMs: 10,
    replace: async (source, target) => {
      await delayedReplace;
      await fs.rename(source, target);
    },
  });
  assert.equal(result.status, 'UNKNOWN');
  assert.equal(result.lateCompletionPossible, true);
  release();
  await new Promise((resolve) => setTimeout(resolve, 30));
  assert.equal(await fs.readFile(targetPath, 'utf8'), 'late new');
});

test('T-401 Local UI staged-file probe reads and hashes a staged file with JP/space path', async (t) => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 't401-host-資料 space-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const stagedPath = path.join(root, 'staged presentation.pptx');
  await fs.writeFile(stagedPath, 'pptx probe bytes');
  const expectedHash = hash('pptx probe bytes');
  const workspaceResult = await verifyT401HostStagedFile({ hostPath: stagedPath, expectedHash });
  const uiResult = await inspectT401StagedFile({ hostPath: stagedPath, expectedHash });
  assert.equal(workspaceResult.status, 'READ_OK');
  assert.equal(uiResult.status, 'READ_OK');
  assert.equal(uiResult.actualHash, expectedHash);
});

test('T-401 Local UI staged-file probe reports inaccessible files', async () => {
  const missing = await inspectT401StagedFile({ hostPath: path.join(os.tmpdir(), 'missing-t401-stage.pptx'), expectedHash: 'a'.repeat(64) });
  assert.equal(missing.status, 'UNAVAILABLE');
});
