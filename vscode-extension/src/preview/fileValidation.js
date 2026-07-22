import fs from 'node:fs/promises';
import path from 'node:path';
import { PreviewError, messages } from './errors.js';
export function isPptxPath(filePath) { return typeof filePath === 'string' && path.extname(filePath).toLowerCase() === '.pptx'; }
export async function validatePptxPath(filePath) {
  if (!isPptxPath(filePath)) throw new PreviewError('notPptx', messages.notPptx, `Invalid extension: ${filePath}`);
  try { const stat = await fs.stat(filePath); if (!stat.isFile()) throw new Error('not a file'); }
  catch (error) { throw new PreviewError('notFound', messages.notFound, `PPTX not found: ${filePath}`, error); }
  return filePath;
}
