import test from 'node:test'; import assert from 'node:assert/strict'; import fs from 'node:fs/promises';
function escapeHtml(s) { return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
test('escapeHtml escapes unsafe characters', () => { assert.equal(escapeHtml('<x>&"\''), '&lt;x&gt;&amp;&quot;&#39;'); });
test('webview viewer has refresh handling and no external CDN', async () => { const js = await fs.readFile(new URL('../webview/viewer.js', import.meta.url),'utf8'); const css = await fs.readFile(new URL('../webview/viewer.css', import.meta.url),'utf8'); assert.match(js, /postMessage\(\{ type:'refresh'/); assert.doesNotMatch(js + css, /https?:\/\//); });
