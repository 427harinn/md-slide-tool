import test from 'node:test';
import assert from 'node:assert/strict';
import { buildAndOpenPowerPoint, mapContainerPathToHostUri } from '../src/hostBridge.js';

test('maps a container output to a Windows host path with Japanese and spaces', () => {
  const mapped = mapContainerPathToHostUri(
    '/work/資料 folder/発表.pptx',
    '/work',
    'C:\\Users\\rinnr\\Documents\\GitHub\\md-slide-tool',
  );
  assert.equal(mapped.hostPath, 'C:\\Users\\rinnr\\Documents\\GitHub\\md-slide-tool\\資料 folder\\発表.pptx');
  assert.equal(mapped.uri, 'file:///C:/Users/rinnr/Documents/GitHub/md-slide-tool/%E8%B3%87%E6%96%99%20folder/%E7%99%BA%E8%A1%A8.pptx');
});

test('maps POSIX host workspace paths', () => {
  const mapped = mapContainerPathToHostUri('/work/subdir/slides.pptx', '/work', '/Users/example/Project');
  assert.equal(mapped.hostPath, '/Users/example/Project/subdir/slides.pptx');
  assert.equal(mapped.uri, 'file:///Users/example/Project/subdir/slides.pptx');
});

test('rejects container paths outside the mapped workspace', () => {
  assert.throws(() => mapContainerPathToHostUri('/outside/slides.pptx', '/work', 'C:\\Project'), /outside the mapped workspace/);
});

test('does not open PowerPoint after a failed build', async () => {
  let openCalls = 0;
  await assert.rejects(buildAndOpenPowerPoint({
    qmdPath: '/work/slides.qmd',
    workspaceRoot: '/work',
    hostWorkspace: 'C:\\Project',
    runBuild: async () => { throw new Error('build failed'); },
    outputExists: async () => true,
    openExternal: async () => { openCalls += 1; return true; },
  }), /build failed/);
  assert.equal(openCalls, 0);
});

test('keeps a successful build successful when the host bridge is unavailable', async () => {
  const result = await buildAndOpenPowerPoint({
    qmdPath: '/work/slides.qmd',
    workspaceRoot: '/work',
    hostWorkspace: undefined,
    runBuild: async () => {},
    outputExists: async () => true,
    openExternal: async () => true,
  });
  assert.equal(result.status, 'built-host-bridge-unavailable');
  assert.equal(result.pptxPath, '/work/slides.pptx');
});

test('does not open a missing output even if the build process exits successfully', async () => {
  let openCalls = 0;
  await assert.rejects(buildAndOpenPowerPoint({
    qmdPath: '/work/slides.qmd',
    workspaceRoot: '/work',
    hostWorkspace: 'C:\\Project',
    runBuild: async () => {},
    outputExists: async () => false,
    openExternal: async () => { openCalls += 1; return true; },
  }), /without creating the expected output/);
  assert.equal(openCalls, 0);
});
