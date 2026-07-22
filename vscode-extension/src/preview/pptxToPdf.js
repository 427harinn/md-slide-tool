import fs from 'node:fs/promises'; import path from 'node:path';
import { PreviewError, messages } from './errors.js'; import { validatePptxPath } from './fileValidation.js'; import { createTempWorkspace } from './tempWorkspace.js'; import { runProcess } from './processRunner.js';
export async function convertPptxToPdf({ pptxPath, libreOfficePath, runner = runProcess, signal, logger = console }) {
  await validatePptxPath(pptxPath); const workspace = await createTempWorkspace();
  try { const args = ['--headless','--convert-to','pdf','--outdir',workspace.dir,pptxPath]; let result;
    try { result = await runner(libreOfficePath, args, { signal }); } catch (e) { if (e.code === 'cancelled') throw new PreviewError('cancelled', messages.cancelled, 'Conversion cancelled', e); throw new PreviewError('libreOfficeLaunchFailed', messages.libreOfficeLaunchFailed, e.message, e); }
    if (result.code !== 0) throw new PreviewError('conversionFailed', messages.conversionFailed, `exit=${result.code}\n${result.stderr || result.stdout}`);
    const pdfPath = path.join(workspace.dir, `${path.basename(pptxPath, path.extname(pptxPath))}.pdf`);
    try { const stat = await fs.stat(pdfPath); if (!stat.isFile()) throw new Error('not a file'); } catch (e) { throw new PreviewError('pdfMissing', messages.pdfMissing, `Expected PDF missing: ${pdfPath}`, e); }
    return { pdfPath, workspace };
  } catch (e) { await workspace.dispose(logger); throw e; }
}
