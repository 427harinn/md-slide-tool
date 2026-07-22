import fs from 'node:fs';
const required = ['src/extension.js', 'webview/viewer.js', 'webview/viewer.css', 'webview/pdf.mjs', 'webview/pdf.worker.mjs'];
const missing = required.filter((p) => !fs.existsSync(new URL(`../${p}`, import.meta.url)));
if (missing.length) { console.error(`Missing extension files: ${missing.join(', ')}`); process.exit(1); }
console.log('Extension package verification passed.');
