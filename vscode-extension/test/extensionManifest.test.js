import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { listFiles, PackageManager } from '@vscode/vsce';

const root = new URL('../', import.meta.url);
async function manifest(kind) {
  return JSON.parse(await fs.readFile(new URL(`extensions/${kind}/package.json`, root), 'utf8'));
}

test('workspace package owns only remote build/path mapping', async () => {
  const pkg = await manifest('workspace');
  assert.deepEqual(pkg.extensionKind, ['workspace']);
  assert.deepEqual(pkg.extensionDependencies, ['md-slide-tool.md-slide-tool-powerpoint-ui']);
  assert.deepEqual(pkg.contributes ?? {}, {});
  assert.deepEqual(pkg.activationEvents, [
    'onCommand:mdSlideTool.buildRemotePptx',
    'onCommand:mdSlideTool.t401.stageHostPptx',
    'onCommand:mdSlideTool.t401.cleanupHostPptx',
  ]);
});

test('UI package owns the single user-facing command and local host opener', async () => {
  const pkg = await manifest('ui');
  assert.deepEqual(pkg.extensionKind, ['ui']);
  assert.equal(pkg.api, 'none');
  assert.deepEqual(pkg.contributes.commands.map(({ command }) => command), [
    'mdSlideTool.buildAndOpenPowerPoint',
    'mdSlideTool.t401.verifyHostPptxAccess',
  ]);
});

test('Dev Container avoids unavailable lifecycle installs, local VSIX paths, and unpublished extension IDs', async () => {
  const devcontainer = JSON.parse(await fs.readFile(new URL('../../.devcontainer/devcontainer.json', import.meta.url), 'utf8'));
  assert.equal(devcontainer.postStartCommand, undefined);
  assert.equal(devcontainer.postAttachCommand, undefined);
  const serialized = JSON.stringify(devcontainer);
  assert.doesNotMatch(serialized, /code\s+--install-extension/i);
  assert.doesNotMatch(serialized, /\.vsix|file:/i);
  assert.equal(devcontainer.customizations.vscode.extensions.some((id) => id.startsWith('md-slide-tool.')), false);
});

test('smoke test clean-installs tooling, packages both VSIXs, and checks generated artifacts', async () => {
  const smokeScript = await fs.readFile(new URL('../../scripts/smoke-test.sh', import.meta.url), 'utf8');
  const installIndex = smokeScript.indexOf('npm ci --prefix vscode-extension');
  const packageIndex = smokeScript.indexOf('npm --prefix vscode-extension run package');
  const workspaceArtifactCheckIndex = smokeScript.indexOf('test -f vscode-extension/dist/md-slide-tool-powerpoint-workspace.vsix');
  const uiArtifactCheckIndex = smokeScript.indexOf('test -f vscode-extension/dist/md-slide-tool-powerpoint-ui.vsix');
  const testIndex = smokeScript.indexOf('npm --prefix vscode-extension test');
  await fs.access(new URL('../package-lock.json', import.meta.url));
  assert.notEqual(installIndex, -1);
  assert.ok(packageIndex > installIndex, 'extension dependencies must be installed before packaging');
  assert.ok(workspaceArtifactCheckIndex > packageIndex, 'smoke test must verify the Workspace VSIX was generated');
  assert.ok(uiArtifactCheckIndex > packageIndex, 'smoke test must verify the UI VSIX was generated');
  assert.ok(testIndex > uiArtifactCheckIndex, 'extension tests run after clean install and packaging');
});

test('extension packages do not include the removed Preview/PDF.js/LibreOffice stack', async () => {
  for (const kind of ['workspace', 'ui']) {
    const pkg = await manifest(kind);
    const source = await fs.readFile(new URL(`../extensions/${kind}/src/extension.js`, import.meta.url), 'utf8');
    assert.doesNotMatch(JSON.stringify(pkg), /openPptxPreview|pdfjs-dist|LibreOffice/i);
    assert.doesNotMatch(source, /PreviewPanel|pdfjs|LibreOffice/i);
  }
});

test('VSIX packaging contents stay limited to each extension manifest and runtime source', async () => {
  for (const kind of ['workspace', 'ui']) {
    const files = await listFiles({
      cwd: fileURLToPath(new URL(`../extensions/${kind}/`, import.meta.url)),
      packageManager: PackageManager.None,
    });
    const paths = files.sort();
    assert.deepEqual(paths, ['package.json', 'src/extension.js', 'src/hostBridge.js', 'src/t401Probe.js']);
  }
});

test('package command clears stale dist output and generates both VSIX artifacts', async () => {
  const extensionRoot = new URL('../', import.meta.url);
  const stalePath = new URL('dist/stale-marker.tmp', extensionRoot);
  await fs.mkdir(new URL('dist/', extensionRoot), { recursive: true });
  await fs.writeFile(stalePath, 'stale');

  const result = spawnSync(process.execPath, [
    fileURLToPath(new URL('../scripts/package-extensions.js', import.meta.url)),
  ], { cwd: fileURLToPath(extensionRoot), encoding: 'utf8' });
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);

  await assert.rejects(fs.access(stalePath));
  await fs.access(new URL('dist/md-slide-tool-powerpoint-workspace.vsix', extensionRoot));
  await fs.access(new URL('dist/md-slide-tool-powerpoint-ui.vsix', extensionRoot));
});
