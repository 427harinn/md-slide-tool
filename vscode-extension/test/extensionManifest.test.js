import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const root = new URL('../', import.meta.url);
async function manifest(kind) {
  return JSON.parse(await fs.readFile(new URL(`extensions/${kind}/package.json`, root), 'utf8'));
}

test('workspace package owns only remote build/path mapping', async () => {
  const pkg = await manifest('workspace');
  assert.deepEqual(pkg.extensionKind, ['workspace']);
  assert.deepEqual(pkg.contributes ?? {}, {});
  assert.deepEqual(pkg.activationEvents, ['onCommand:mdSlideTool.buildRemotePptx']);
});

test('UI package owns the single user-facing command and local host opener', async () => {
  const pkg = await manifest('ui');
  assert.deepEqual(pkg.extensionKind, ['ui']);
  assert.deepEqual(pkg.contributes.commands.map(({ command }) => command), ['mdSlideTool.buildAndOpenPowerPoint']);
});

test('Dev Container does not call an unavailable lifecycle VSIX installer or list unpublished packages', async () => {
  const devcontainer = JSON.parse(await fs.readFile(new URL('../../.devcontainer/devcontainer.json', import.meta.url), 'utf8'));
  assert.equal(devcontainer.postStartCommand, undefined);
  assert.equal(devcontainer.postAttachCommand, undefined);
  assert.equal(devcontainer.customizations.vscode.extensions.some((id) => id.startsWith('md-slide-tool.')), false);
});

test('extension packages do not include the removed Preview/PDF.js/LibreOffice stack', async () => {
  for (const kind of ['workspace', 'ui']) {
    const pkg = await manifest(kind);
    const source = await fs.readFile(new URL(`../extensions/${kind}/src/extension.js`, import.meta.url), 'utf8');
    assert.doesNotMatch(JSON.stringify(pkg), /openPptxPreview|pdfjs-dist|LibreOffice/i);
    assert.doesNotMatch(source, /PreviewPanel|pdfjs|LibreOffice/i);
  }
});
