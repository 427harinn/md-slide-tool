import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

export async function createTempWorkspace(options = {}) {
  const root = options.root ?? os.tmpdir();
  const prefix = options.prefix ?? 'md-slide-pptx-';
  await fs.mkdir(root, { recursive: true });
  const dir = await fs.mkdtemp(path.join(root, prefix));
  return {
    dir,
    dispose: async (logger = console) => {
      try {
        await fs.rm(dir, { recursive: true, force: true });
      } catch (error) {
        logger.warn?.(`Failed to remove temp workspace ${dir}: ${error.message}`);
      }
    }
  };
}
