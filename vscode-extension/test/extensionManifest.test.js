import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

test('launch configuration uses current extension folder and opens /work', async () => {
  const launch = JSON.parse(await fs.readFile(new URL('../.vscode/launch.json', import.meta.url), 'utf8'));
  const args = launch.configurations[0].args;
  assert.ok(args.includes('--extensionDevelopmentPath=${workspaceFolder}'));
  assert.ok(args.includes('/work'));
  assert.ok(!args.some((arg) => arg.includes('${workspaceFolder}/vscode-extension')));
});

test('extension manifest runs as workspace extension in Dev Container', async () => {
  const manifest = JSON.parse(await fs.readFile(new URL('../package.json', import.meta.url), 'utf8'));
  assert.deepEqual(manifest.extensionKind, ['workspace']);
});
