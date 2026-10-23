import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

export async function inspectT401StagedFile({ hostPath, expectedHash }) {
  try {
    const bytes = await readFile(hostPath);
    const actualHash = createHash('sha256').update(bytes).digest('hex');
    return {
      status: actualHash === expectedHash ? 'READ_OK' : 'HASH_MISMATCH',
      actualHash,
      bytesRead: bytes.length,
      hostPath,
    };
  } catch (error) {
    return { status: 'UNAVAILABLE', hostPath, reason: error?.code ?? String(error) };
  }
}
