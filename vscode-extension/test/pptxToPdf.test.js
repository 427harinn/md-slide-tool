import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { convertPptxToPdf } from '../src/preview/pptxToPdf.js';

test('convertPptxToPdf uses argument array, configured output root, and finds generated pdf', async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'pptx-src '));
  const outputRoot = path.join(dir, 'allowed-preview-root');
  const pptx = path.join(dir, '資料 sample.pptx');
  await fs.writeFile(pptx, 'x');
  let seen;
  const result = await convertPptxToPdf({
    pptxPath: pptx,
    libreOfficePath: '/lo',
    outputRoot,
    runner: async (cmd, args) => {
      seen = { cmd, args };
      await fs.writeFile(path.join(args[args.indexOf('--outdir') + 1], '資料 sample.pdf'), 'pdf');
      return { code: 0, stdout: '', stderr: '' };
    }
  });
  assert.equal(seen.cmd, '/lo');
  assert.deepEqual(seen.args.slice(0, 4), ['--headless', '--convert-to', 'pdf', '--outdir']);
  assert.ok(result.pdfPath.startsWith(outputRoot));
  await fs.stat(result.pdfPath);
  await result.workspace.dispose();
  await fs.rm(dir, { recursive: true, force: true });
});

test('convertPptxToPdf handles failures', async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'pptx-src '));
  const pptx = path.join(dir, 'x.pptx');
  await fs.writeFile(pptx, 'x');
  await assert.rejects(
    () => convertPptxToPdf({ pptxPath: pptx, libreOfficePath: '/lo', runner: async () => ({ code: 1, stdout: '', stderr: 'bad' }) }),
    /could not convert/
  );
  await assert.rejects(
    () => convertPptxToPdf({ pptxPath: pptx, libreOfficePath: '/lo', runner: async () => ({ code: 0, stdout: '', stderr: '' }) }),
    /no PDF/
  );
  await fs.rm(dir, { recursive: true, force: true });
});
