import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { renderQmdToPptx } from '../src/autoPreview/renderQmd.js';

test('renderQmdToPptx delegates to slidegen render with argument array', async () => {
  const workspaceRoot = path.join('workspace root');
  const qmdPath = path.join(workspaceRoot, 'projects', 'demo', 'demo_pptx.qmd');
  let seen;
  const result = await renderQmdToPptx({
    qmdPath,
    workspaceRoot,
    runner: async (command, args, options) => {
      seen = { command, args, options };
      return { code: 0, stdout: 'ok', stderr: '' };
    }
  });

  assert.equal(seen.command, process.execPath);
  assert.deepEqual(seen.args, [path.join(workspaceRoot, 'cli', 'slidegen.js'), 'render', qmdPath]);
  assert.equal(seen.options.cwd, workspaceRoot);
  assert.equal(result.stdout, 'ok');
});

test('renderQmdToPptx exposes render failure details', async () => {
  await assert.rejects(
    () => renderQmdToPptx({
      qmdPath: '/work/projects/demo/demo_pptx.qmd',
      workspaceRoot: '/work',
      runner: async () => ({ code: 1, stdout: '', stderr: 'quarto failed' })
    }),
    (error) => {
      assert.equal(error.message, 'slidegen render failed.');
      assert.equal(error.detail, 'quarto failed');
      return true;
    }
  );
});
