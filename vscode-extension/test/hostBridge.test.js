import test from 'node:test';
import assert from 'node:assert/strict';
import { buildAndOpenPowerPoint, mapContainerPathToHostUri } from '../src/hostBridge.js';

test('maps nested container paths to Windows host paths and encodes Japanese and spaces', () => {
  const mapped = mapContainerPathToHostUri(
    '/work/projects/資料 folder/発表.pptx',
    '/work',
    'C:\\Users\\rinnr\\Documents\\GitHub\\md-slide-tool',
  );
  assert.equal(mapped.hostPath, 'C:\\Users\\rinnr\\Documents\\GitHub\\md-slide-tool\\projects\\資料 folder\\発表.pptx');
  assert.equal(mapped.uri, 'file:///C:/Users/rinnr/Documents/GitHub/md-slide-tool/projects/%E8%B3%87%E6%96%99%20folder/%E7%99%BA%E8%A1%A8.pptx');
});

test('maps a POSIX host workspace', () => {
  const mapped = mapContainerPathToHostUri('/work/subdir/slides.pptx', '/work', '/Users/example/Project');
  assert.equal(mapped.hostPath, '/Users/example/Project/subdir/slides.pptx');
  assert.equal(mapped.uri, 'file:///Users/example/Project/subdir/slides.pptx');
});

test('rejects paths outside the mapped workspace', () => {
  assert.throws(() => mapContainerPathToHostUri('/outside/slides.pptx', '/work', 'C:\\Project'), /outside the mapped workspace/);
});

test('build failure never requests PowerPoint open', async () => {
  let openCalls = 0;
  await assert.rejects(buildAndOpenPowerPoint({
    qmdPath: '/work/slides.qmd',
    workspacePath: '/work',
    hostWorkspace: 'C:\\Project',
    runBuild: async () => { throw new Error('Quarto failed'); },
    outputExists: async () => true,
    openExternal: async () => { openCalls += 1; return true; },
  }), /Quarto failed/);
  assert.equal(openCalls, 0);
});

test('rejects inputs outside the workspace and non-QMD files before build', async () => {
  let buildCalls = 0;
  const options = {
    workspacePath: '/work',
    hostWorkspace: 'C:\\Project',
    runBuild: async () => { buildCalls += 1; },
    outputExists: async () => true,
    openExternal: async () => true,
  };
  await assert.rejects(buildAndOpenPowerPoint({ ...options, qmdPath: '/elsewhere/slides.qmd' }), /inside the workspace/);
  await assert.rejects(buildAndOpenPowerPoint({ ...options, qmdPath: '/work/slides.pptx' }), /\.qmd file/);
  assert.equal(buildCalls, 0);
});

test('missing output never requests PowerPoint open', async () => {
  let openCalls = 0;
  await assert.rejects(buildAndOpenPowerPoint({
    qmdPath: '/work/slides.qmd',
    workspacePath: '/work',
    hostWorkspace: 'C:\\Project',
    runBuild: async () => {},
    outputExists: async () => false,
    openExternal: async () => { openCalls += 1; return true; },
  }), /without creating the expected output/);
  assert.equal(openCalls, 0);
});

test('bridge rejection preserves the completed build result', async () => {
  const result = await buildAndOpenPowerPoint({
    qmdPath: '/work/slides.qmd',
    workspacePath: '/work',
    hostWorkspace: undefined,
    runBuild: async () => {},
    outputExists: async () => true,
    openExternal: async () => true,
  });
  assert.equal(result.status, 'built-host-bridge-unavailable');
  assert.equal(result.pptxPath, '/work/slides.pptx');
});

test('an unavailable default application does not change build success', async () => {
  const result = await buildAndOpenPowerPoint({
    qmdPath: '/work/slides.qmd',
    workspacePath: '/work',
    hostWorkspace: 'C:\\Project',
    runBuild: async () => {},
    outputExists: async () => true,
    openExternal: async () => false,
  });
  assert.equal(result.status, 'built-host-bridge-unavailable');
  assert.equal(result.hostPath, 'C:\\Project\\slides.pptx');
});
