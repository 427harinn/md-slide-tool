import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { mapContainerPathToHostPath } from './hostBridge.js';

export const T401_MUTATION_RESULTS = Object.freeze({
  MUTATED: 'MUTATED',
  NOT_MUTATED: 'NOT_MUTATED',
  UNKNOWN: 'UNKNOWN',
});

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function assertInside(root, candidate, label) {
  const resolvedRoot = path.posix.resolve(root);
  const resolvedCandidate = path.posix.resolve(candidate);
  const relative = path.posix.relative(resolvedRoot, resolvedCandidate);
  if (relative === '..' || relative.startsWith('../') || path.posix.isAbsolute(relative)) {
    throw new Error(`${label} escapes the workspace.`);
  }
  return resolvedCandidate;
}

export function createT401MutationRequest({
  documentId, freezeSessionId, transactionId, operationIndex,
  targetPath, stagedSource, expectedOldHash, expectedAbsence = false,
  newHash, workspacePath, hostWorkspace,
}) {
  if (!documentId || !freezeSessionId || !transactionId || !Number.isInteger(operationIndex) || operationIndex < 0) {
    throw new Error('T-401 mutation request is missing correlation identifiers.');
  }
  if ((expectedAbsence && expectedOldHash != null) || (!expectedAbsence && !expectedOldHash)) {
    throw new Error('T-401 request must specify expected old hash or expected absence.');
  }
  const target = assertInside(workspacePath, targetPath, 'Target');
  const stage = assertInside(workspacePath, stagedSource, 'Staged source');
  return {
    documentId,
    freezeSessionId,
    transactionId,
    operationIndex,
    targetPath: target,
    stagedSource: stage,
    hostTargetPath: mapContainerPathToHostPath(target, workspacePath, hostWorkspace),
    hostStagedSource: mapContainerPathToHostPath(stage, workspacePath, hostWorkspace),
    expectedOldHash: expectedOldHash ?? null,
    expectedAbsence,
    newHash,
  };
}

async function fileHash(filePath) {
  try {
    return sha256(await fs.readFile(filePath));
  } catch (error) {
    if (error?.code === 'ENOENT') return null;
    throw error;
  }
}

function correlatedResult(request, status, extra = {}) {
  return {
    status,
    documentId: request.documentId,
    freezeSessionId: request.freezeSessionId,
    transactionId: request.transactionId,
    operationIndex: request.operationIndex,
    ...extra,
  };
}

// Probe-only broker: its critical section owns the final replace and verifies
// the postcondition before it reports MUTATED. Hooks allow deterministic race
// injection; this is not wired to a production sync command.
export async function runT401MutationProbe({
  request,
  getFreezeState,
  beforeMutation = async () => {},
  replace = async (source, target) => fs.rename(source, target),
  timeoutMs = 5000,
}) {
  const work = (async () => {
    const initialFreeze = await getFreezeState(request.freezeSessionId);
    if (initialFreeze?.freezeSessionId !== request.freezeSessionId || initialFreeze?.state !== 'committing') {
      return correlatedResult(request, T401_MUTATION_RESULTS.NOT_MUTATED, { reason: 'freeze-mismatch' });
    }
    const existingHash = await fileHash(request.targetPath);
    if ((request.expectedAbsence && existingHash !== null) ||
        (!request.expectedAbsence && existingHash !== request.expectedOldHash)) {
      return correlatedResult(request, T401_MUTATION_RESULTS.NOT_MUTATED, { reason: 'expected-old-mismatch' });
    }
    const stageHash = await fileHash(request.stagedSource);
    if (!request.newHash || stageHash !== request.newHash) {
      return correlatedResult(request, T401_MUTATION_RESULTS.NOT_MUTATED, { reason: 'staged-hash-mismatch' });
    }
    await beforeMutation(request);
    const currentFreeze = await getFreezeState(request.freezeSessionId);
    if (currentFreeze?.freezeSessionId !== request.freezeSessionId || currentFreeze?.state !== 'committing') {
      return correlatedResult(request, T401_MUTATION_RESULTS.NOT_MUTATED, { reason: 'freeze-invalidated' });
    }
    try {
      await replace(request.stagedSource, request.targetPath);
    } catch (error) {
      const observedHash = await fileHash(request.targetPath).catch(() => undefined);
      if (observedHash === request.newHash) {
        return correlatedResult(request, T401_MUTATION_RESULTS.MUTATED, { resultingHash: observedHash });
      }
      if (observedHash === existingHash) {
        return correlatedResult(request, T401_MUTATION_RESULTS.NOT_MUTATED, { reason: error.message });
      }
      return correlatedResult(request, T401_MUTATION_RESULTS.UNKNOWN, { reason: error.message });
    }
    const resultingHash = await fileHash(request.targetPath).catch(() => undefined);
    if (resultingHash === request.newHash) {
      return correlatedResult(request, T401_MUTATION_RESULTS.MUTATED, { resultingHash });
    }
    return correlatedResult(request, T401_MUTATION_RESULTS.UNKNOWN, { resultingHash: resultingHash ?? null });
  })();

  let timer;
  const timeout = new Promise((resolve) => {
    timer = setTimeout(() => resolve(correlatedResult(
      request, T401_MUTATION_RESULTS.UNKNOWN, { reason: 'timeout', lateCompletionPossible: true },
    )), timeoutMs);
  });
  const result = await Promise.race([work, timeout]).finally(() => clearTimeout(timer));
  return result;
}

export async function verifyT401HostStagedFile({ hostPath, expectedHash }) {
  try {
    const bytes = await fs.readFile(hostPath);
    const actualHash = sha256(bytes);
    return actualHash === expectedHash
      ? { status: 'READ_OK', hostPath, actualHash, bytesRead: bytes.length }
      : { status: 'HASH_MISMATCH', hostPath, actualHash, reason: 'hash-mismatch' };
  } catch (error) {
    return { status: 'UNAVAILABLE', hostPath, reason: error?.code ?? String(error) };
  }
}

export async function stageT401HostPptxProbe({ workspacePath, hostWorkspace, probeId }) {
  if (!/^[a-f0-9-]{36}$/i.test(probeId ?? '')) throw new Error('Invalid T-401 probe id.');
  if (!hostWorkspace) throw new Error('MD_SLIDE_TOOL_HOST_WORKSPACE is not configured.');
  const source = path.posix.join(workspacePath, 'templates', 'pptx', 'template', 'template.pptx');
  const staged = path.posix.join(workspacePath, '.md-slide-tool', 't401-probe', `${probeId}.pptx`);
  const hostPath = mapContainerPathToHostPath(staged, workspacePath, hostWorkspace);
  await fs.mkdir(path.posix.dirname(staged), { recursive: true });
  await fs.copyFile(source, staged);
  const bytes = await fs.readFile(staged);
  return {
    probeId,
    containerPath: staged,
    hostPath,
    sha256: sha256(bytes),
    bytes: bytes.length,
  };
}

export async function cleanupT401HostPptxProbe({ workspacePath, probeId }) {
  if (!/^[a-f0-9-]{36}$/i.test(probeId ?? '')) throw new Error('Invalid T-401 probe id.');
  const staged = path.posix.join(workspacePath, '.md-slide-tool', 't401-probe', `${probeId}.pptx`);
  await fs.rm(staged, { force: true });
  return { removed: true, probeId };
}
