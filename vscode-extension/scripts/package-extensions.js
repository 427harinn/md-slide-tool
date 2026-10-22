import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'dist');
fs.mkdirSync(output, { recursive: true });

for (const name of ['workspace', 'ui']) {
  const extensionRoot = path.join(root, 'extensions', name);
  const extensionName = JSON.parse(fs.readFileSync(path.join(extensionRoot, 'package.json'), 'utf8')).name;
  const vsce = path.join(root, 'node_modules', '@vscode', 'vsce', 'vsce');
  const result = spawnSync(process.execPath, [vsce, 'package', '--no-dependencies', '--out', path.join(output, `${extensionName}.vsix`)], {
    cwd: extensionRoot,
    stdio: 'inherit',
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
