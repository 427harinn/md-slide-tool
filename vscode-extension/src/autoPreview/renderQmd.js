import path from 'node:path';
import { runProcess } from '../preview/processRunner.js';

export async function renderQmdToPptx({ qmdPath, workspaceRoot, runner = runProcess, signal }) {
  if (!workspaceRoot) {
    throw new Error('No VS Code workspace folder is available for slidegen render.');
  }

  const slidegenPath = path.join(workspaceRoot, 'cli', 'slidegen.js');
  const result = await runner(process.execPath, [slidegenPath, 'render', qmdPath], {
    cwd: workspaceRoot,
    signal
  });

  if (result.code !== 0) {
    const detail = result.stderr || result.stdout || `slidegen render exited with code ${result.code}`;
    const error = new Error('slidegen render failed.');
    error.detail = detail;
    error.result = result;
    throw error;
  }

  return result;
}
