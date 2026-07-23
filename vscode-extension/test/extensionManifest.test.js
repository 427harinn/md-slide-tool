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

test('extension manifest contributes manual and auto preview commands', async () => {
  const manifest = JSON.parse(await fs.readFile(new URL('../package.json', import.meta.url), 'utf8'));
  const commands = manifest.contributes.commands.map((entry) => entry.command);
  assert.ok(commands.includes('mdSlideTool.openPptxPreview'));
  assert.ok(commands.includes('mdSlideTool.startAutoPreview'));
  assert.ok(commands.includes('mdSlideTool.stopAutoPreview'));
  assert.equal(manifest.contributes.configuration.properties['mdSlideTool.autoPreview.enabled'].default, true);
  assert.ok(manifest.activationEvents.includes('onCommand:mdSlideTool.startAutoPreview'));
});

test('extension manifest can package a VSIX for Dev Container installation', async () => {
  const manifest = JSON.parse(await fs.readFile(new URL('../package.json', import.meta.url), 'utf8'));
  assert.match(manifest.scripts['package:vsix'], /vsce package/);
});
