import fs from 'node:fs/promises';

const required = [
  'src/extension.js',
  'webview/viewer.js',
  'webview/viewer.css',
  'webview/pdf.mjs',
  'webview/pdf.worker.mjs'
];

for (const file of required) {
  const url = new URL(`../${file}`, import.meta.url);
  let contents;
  try {
    contents = await fs.readFile(url, 'utf8');
  } catch {
    console.error(`Missing extension file: ${file}`);
    process.exit(1);
  }
  if (file.startsWith('webview/pdf') && /placeholder|offline static validation|Bundled PDF\.js is unavailable/i.test(contents)) {
    console.error(`Invalid placeholder PDF.js asset: ${file}`);
    process.exit(1);
  }
}
console.log('Extension package verification passed.');
