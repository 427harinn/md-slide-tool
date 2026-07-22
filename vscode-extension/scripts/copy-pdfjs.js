import fs from 'node:fs/promises';
import path from 'node:path';

const root = new URL('..', import.meta.url);
const sources = [
  ['node_modules/pdfjs-dist/build/pdf.mjs', 'webview/pdf.mjs'],
  ['node_modules/pdfjs-dist/build/pdf.worker.mjs', 'webview/pdf.worker.mjs']
];

async function copyPdfJs() {
  for (const [from, to] of sources) {
    const src = path.join(root.pathname, from);
    const dest = path.join(root.pathname, to);
    let contents;
    try {
      contents = await fs.readFile(src, 'utf8');
    } catch (error) {
      throw new Error(`Missing ${from}. Run npm install in vscode-extension before building.`);
    }
    if (/placeholder|offline static validation|Bundled PDF\.js is unavailable/i.test(contents)) {
      throw new Error(`${from} appears to be a placeholder, not the real pdfjs-dist file.`);
    }
    await fs.mkdir(path.dirname(dest), { recursive: true });
    await fs.writeFile(dest, contents);
  }
}

await copyPdfJs();
console.log('Copied pdfjs-dist Webview assets.');
