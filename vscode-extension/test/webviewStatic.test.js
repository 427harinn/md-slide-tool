import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

function escapeHtml(s) {
  return String(s).replace(/[&<>'"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[c]);
}

test('escapeHtml escapes unsafe characters', () => {
  assert.equal(escapeHtml('<x>&"\''), '&lt;x&gt;&amp;&quot;&#39;');
});

test('webview viewer reports render completion and has no external CDN', async () => {
  const js = await fs.readFile(new URL('../webview/viewer.js', import.meta.url), 'utf8');
  const css = await fs.readFile(new URL('../webview/viewer.css', import.meta.url), 'utf8');
  assert.match(js, /postMessage\(\{ type: 'refresh'/);
  assert.match(js, /type: 'renderComplete'/);
  assert.match(js, /type: 'renderFailed'/);
  assert.doesNotMatch(js + css, /https?:\/\//);
});

test('build scripts require real pdfjs-dist assets and reject placeholders', async () => {
  const copyScript = await fs.readFile(new URL('../scripts/copy-pdfjs.js', import.meta.url), 'utf8');
  const verifyScript = await fs.readFile(new URL('../scripts/verify-package.js', import.meta.url), 'utf8');
  assert.match(copyScript, /fileURLToPath/);
  assert.match(copyScript, /path\.join\(root, from\)/);
  assert.match(copyScript, /node_modules\/pdfjs-dist\/build\/pdf\.mjs/);
  assert.match(copyScript, /node_modules\/pdfjs-dist\/build\/pdf\.worker\.mjs/);
  assert.match(copyScript + verifyScript, /placeholder\|offline static validation\|Bundled PDF\\\.js is unavailable/);
});

test('package check runs build before npm pack', async () => {
  const packageJson = JSON.parse(await fs.readFile(new URL('../package.json', import.meta.url), 'utf8'));
  assert.equal(packageJson.scripts['package:check'], 'npm run build && npm pack --dry-run');
});

test('preview panel CSP allows nonce scripts and Webview local script modules', async () => {
  const panel = await fs.readFile(new URL('../src/preview/previewPanel.js', import.meta.url), 'utf8');
  assert.match(panel, /script-src 'nonce-\$\{nonce\}' \$\{webview\.cspSource\}/);
});

test('extension awaits async PreviewPanel.open', async () => {
  const extension = await fs.readFile(new URL('../src/extension.js', import.meta.url), 'utf8');
  assert.match(extension, /await PreviewPanel\.open\(context, target, output\)/);
});
