import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

test('extension exposes only the M1 build-and-open command', async () => {
  const manifest = JSON.parse(await fs.readFile(new URL('../package.json', import.meta.url), 'utf8'));
  assert.deepEqual(manifest.extensionKind, ['workspace']);
  assert.deepEqual(manifest.contributes.commands.map(({ command }) => command), ['mdSlideTool.buildAndOpenPowerPoint']);
  assert.deepEqual(manifest.dependencies ?? {}, {});
  assert.equal(manifest.devDependencies['@vscode/vsce'], '3.3.2');
});

test('Dev Container setup packages and installs the extension automatically', async () => {
  const devcontainer = JSON.parse(await fs.readFile(new URL('../../.devcontainer/devcontainer.json', import.meta.url), 'utf8'));
  const installer = await fs.readFile(new URL('../../scripts/install-vscode-extension.sh', import.meta.url), 'utf8');
  assert.equal(devcontainer.postStartCommand, 'bash /work/scripts/install-vscode-extension.sh');
  assert.match(installer, /npm --prefix "\$EXTENSION_DIR" ci/);
  assert.match(installer, /npm --prefix "\$EXTENSION_DIR" run package/);
  assert.match(installer, /code --install-extension "\$VSIX_PATH" --force/);
});

test('extension source does not include the removed Preview or PDF.js stack', async () => {
  const manifest = JSON.parse(await fs.readFile(new URL('../package.json', import.meta.url), 'utf8'));
  const source = await fs.readFile(new URL('../src/extension.js', import.meta.url), 'utf8');
  assert.doesNotMatch(JSON.stringify(manifest), /openPptxPreview|pdfjs-dist|LibreOffice/i);
  assert.doesNotMatch(source, /PreviewPanel|pdfjs|LibreOffice/i);
});
