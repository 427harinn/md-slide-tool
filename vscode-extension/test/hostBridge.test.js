import test from 'node:test';
import assert from 'node:assert/strict';
import { buildPptxForHost, mapContainerPathToHostPath, resolveCanonicalPptxForHost, generateVersionedPreviewForHost } from '../extensions/workspace/src/hostBridge.js';
import { buildAndOpenLocally, openExactPptxLocally, openEditablePowerPoint, openVersionedPreview } from '../extensions/ui/src/hostBridge.js';

test('maps container paths to Windows host paths with Japanese and spaces', () => {
  assert.equal(mapContainerPathToHostPath(
    '/work/projects/資料 folder/発表.pptx',
    '/work',
    'C:\\Users\\rinnr\\Documents\\GitHub\\md-slide-tool',
  ), 'C:\\Users\\rinnr\\Documents\\GitHub\\md-slide-tool\\projects\\資料 folder\\発表.pptx');
});

test('open exact PPTX path passes the selected preview URI unchanged', async () => {
  const selected = 'C:\\Users\\rinnr\\資料 Folder\\preview-000007.pptx';
  let opened;
  const result = await openExactPptxLocally(selected, {
    fileUri: (path) => ({ scheme: 'file', fsPath: path }),
    openExternal: async (uri) => { opened = uri; return true; },
  });
  assert.equal(result.status, 'opened-exact-path');
  assert.equal(opened.fsPath, selected);
});

test('editable PowerPoint resolves and opens the exact canonical path, never a preview', async () => {
  const qmd = '/work/projects/資料 folder/deck.qmd';
  const canonical = '/work/projects/資料 folder/deck.pptx';
  const result = await resolveCanonicalPptxForHost({
    qmdPath: qmd,
    workspacePath: '/work',
    hostWorkspace: 'C:\\Users\\rinnr\\Documents\\Project With Spaces',
    inspectCanonical: async () => canonical,
    outputExists: async (candidate) => candidate === canonical,
  });
  assert.equal(result.pptxPath, canonical);
  assert.equal(result.hostPath, 'C:\\Users\\rinnr\\Documents\\Project With Spaces\\projects\\資料 folder\\deck.pptx');
  assert.equal(result.hostPath.includes('previews'), false);
  let command;
  let opened;
  const openedResult = await openEditablePowerPoint({
    qmdUri: 'file:///work/projects/%E8%B3%87%E6%96%99%20folder/deck.qmd',
    executeCommand: async (name) => { command = name; return { status: 'canonical-ready', hostPath: result.hostPath }; },
    fileUri: (fsPath) => ({ scheme: 'file', fsPath }),
    openExternal: async (uri) => { opened = uri; return true; },
  });
  assert.equal(command, 'mdSlideTool.resolveEditablePptx');
  assert.equal(openedResult.status, 'opened-exact-path');
  assert.equal(opened.fsPath, result.hostPath);
  await assert.rejects(resolveCanonicalPptxForHost({
    qmdPath: qmd, workspacePath: '/work', hostWorkspace: 'C:\\Project',
    inspectCanonical: async () => '/work/.md-slide-tool/previews/document-x/preview-000001.pptx',
    outputExists: async () => true,
  }), /non-canonical/);
});

test('versioned preview command returns and opens exact generated Japanese/space path without closing prior previews', async () => {
  const qmd = '/work/projects/資料 folder/deck.qmd';
  const preview = '/work/projects/資料 folder/.md-slide-tool/previews/document-123e4567-e89b-42d3-a456-426614174000/preview-000042.pptx';
  let runInput;
  const result = await generateVersionedPreviewForHost({
    qmdPath: qmd,
    workspacePath: '/work',
    hostWorkspace: 'C:\\Users\\rinnr\\Documents\\Project With Spaces',
    runPreview: async (exactQmd) => {
      runInput = exactQmd;
      return `Rendering...\nPREVIEW_PATH=${preview}\nPREVIEW_DOCUMENT_ID=document-123e4567-e89b-42d3-a456-426614174000\nPREVIEW_SOURCE_QMD=${qmd}\n`;
    },
    outputExists: async (path) => path === preview,
  });
  assert.equal(runInput, qmd);
  assert.equal(result.previewPath, preview);
  assert.equal(result.generation, 42);
  assert.equal(result.documentId, 'document-123e4567-e89b-42d3-a456-426614174000');
  assert.equal(result.sourceQmd, qmd);
  assert.equal(result.hostPath, 'C:\\Users\\rinnr\\Documents\\Project With Spaces\\projects\\資料 folder\\.md-slide-tool\\previews\\document-123e4567-e89b-42d3-a456-426614174000\\preview-000042.pptx');
  assert.equal(result.previousPreviewsClosed, false);
  assert.match(result.note, /open\/dirty state was not inspected/);

  let command;
  let opened;
  const openedResult = await openVersionedPreview({
    qmdUri: 'file:///work/projects/%E8%B3%87%E6%96%99%20folder/deck.qmd',
    executeCommand: async (name) => {
      command = name;
      return { status: result.status, hostPath: result.hostPath, previewPath: result.previewPath, generation: result.generation };
    },
    fileUri: (fsPath) => ({ scheme: 'file', fsPath }),
    openExternal: async (uri) => { opened = uri; return true; },
  });
  assert.equal(command, 'mdSlideTool.generateVersionedPreview');
  assert.equal(openedResult.status, 'preview-opened');
  assert.equal(opened.fsPath, result.hostPath);
  assert.equal(openedResult.previousPreviewsClosed, false);
  assert.match(openedResult.note, /all prior previews remain open/);
});

test('preview path resolver rejects outside-workspace inputs, canonical files, malformed paths, and missing output', async () => {
  let calls = 0;
  const common = {
    workspacePath: '/work', hostWorkspace: 'C:\\Project',
    runPreview: async () => {
      calls++;
      return 'PREVIEW_PATH=/work/deck.pptx\nPREVIEW_DOCUMENT_ID=document-123e4567-e89b-42d3-a456-426614174000\nPREVIEW_SOURCE_QMD=/work/deck.qmd';
    },
    outputExists: async () => true,
  };
  await assert.rejects(generateVersionedPreviewForHost({ ...common, qmdPath: '/elsewhere/deck.qmd' }), /inside the workspace/);
  await assert.rejects(generateVersionedPreviewForHost({ ...common, qmdPath: '/work/deck.qmd' }), /selected QMD project directory/);
  assert.equal(calls, 1);
  const preview = '/work/.md-slide-tool/previews/document-123e4567-e89b-42d3-a456-426614174000/preview-000001.pptx';
  const metadata = `PREVIEW_PATH=${preview}\nPREVIEW_DOCUMENT_ID=document-123e4567-e89b-42d3-a456-426614174000\nPREVIEW_SOURCE_QMD=/work/deck.qmd`;
  await assert.rejects(generateVersionedPreviewForHost({ ...common, qmdPath: '/work/deck.qmd', runPreview: async () => metadata, outputExists: async () => false }), /does not exist/);
  const otherProject = '/work/projects/other/.md-slide-tool/previews/document-123e4567-e89b-42d3-a456-426614174000/preview-000001.pptx';
  await assert.rejects(generateVersionedPreviewForHost({
    ...common,
    qmdPath: '/work/projects/資料 folder/deck.qmd',
    runPreview: async () => `PREVIEW_PATH=${otherProject}\nPREVIEW_DOCUMENT_ID=document-123e4567-e89b-42d3-a456-426614174000\nPREVIEW_SOURCE_QMD=/work/projects/資料 folder/deck.qmd`,
  }), /selected QMD project directory/);
  await assert.rejects(generateVersionedPreviewForHost({
    ...common,
    qmdPath: '/work/projects/資料 folder/deck.qmd',
    runPreview: async () => `PREVIEW_PATH=/work/projects/資料 folder/.md-slide-tool/previews/document-123e4567-e89b-42d3-a456-426614174000/preview-000001.pptx\nPREVIEW_DOCUMENT_ID=document-123e4567-e89b-42d3-a456-426614174000\nPREVIEW_SOURCE_QMD=/work/projects/other/deck.qmd`,
  }), /source QMD does not match/);
});

test('preview opener does not open when generation fails or returns an invalid result', async () => {
  let opened = false;
  const local = {
    qmdUri: 'file:///work/deck.qmd',
    executeCommand: async () => { throw new Error('preview failed'); },
    fileUri: (fsPath) => ({ scheme: 'file', fsPath }),
    openExternal: async () => { opened = true; return true; },
  };
  await assert.rejects(openVersionedPreview(local), /preview failed/);
  await assert.rejects(openVersionedPreview({ ...local, executeCommand: async () => ({ status: 'built', hostPath: 'C:\\deck.pptx' }) }), /exact versioned preview/);
  assert.equal(opened, false);
});

test('maps a POSIX host workspace', () => {
  assert.equal(mapContainerPathToHostPath('/work/subdir/slides.pptx', '/work', '/Users/example/Project'), '/Users/example/Project/subdir/slides.pptx');
});

test('rejects paths outside the mapped workspace', () => {
  assert.throws(() => mapContainerPathToHostPath('/outside/slides.pptx', '/work', 'C:\\Project'), /outside the mapped workspace/);
});

test('build failure never returns an openable result', async () => {
  await assert.rejects(buildPptxForHost({
    qmdPath: '/work/slides.qmd', workspacePath: '/work', hostWorkspace: 'C:\\Project',
    runBuild: async () => { throw new Error('Quarto failed'); }, outputExists: async () => true,
  }), /Quarto failed/);
});

test('rejects outside-workspace and non-QMD inputs before build', async () => {
  let buildCalls = 0;
  const options = { workspacePath: '/work', hostWorkspace: 'C:\\Project', runBuild: async () => { buildCalls += 1; }, outputExists: async () => true };
  await assert.rejects(buildPptxForHost({ ...options, qmdPath: '/elsewhere/slides.qmd' }), /inside the workspace/);
  await assert.rejects(buildPptxForHost({ ...options, qmdPath: '/work/slides.pptx' }), /\.qmd file/);
  assert.equal(buildCalls, 0);
});

test('missing build output rejects before the local opener can be invoked', async () => {
  await assert.rejects(buildPptxForHost({
    qmdPath: '/work/slides.qmd', workspacePath: '/work', hostWorkspace: 'C:\\Project',
    runBuild: async () => {}, outputExists: async () => false,
  }), /without creating the expected output/);
});

test('unavailable mapping preserves successful build result', async () => {
  const result = await buildPptxForHost({
    qmdPath: '/work/slides.qmd', workspacePath: '/work', hostWorkspace: undefined,
    runBuild: async () => {}, outputExists: async () => true,
  });
  assert.equal(result.status, 'built-host-bridge-unavailable');
  assert.equal(result.pptxPath, '/work/slides.pptx');
});

test('local opener uses a file URI created from the mapped host path', async () => {
  const calls = [];
  const result = await buildAndOpenLocally({
    qmdUri: 'vscode-remote://dev-container/work/slides.qmd',
    executeCommand: async (command, uri) => { calls.push(['command', command, uri]); return { status: 'built', pptxPath: '/work/slides.pptx', hostPath: 'C:\\Project\\slides.pptx' }; },
    fileUri: (hostPath) => { calls.push(['fileUri', hostPath]); return { scheme: 'file', fsPath: hostPath }; },
    openExternal: async (uri) => { calls.push(['open', uri]); return true; },
  });
  assert.equal(result.status, 'built-and-opened');
  assert.deepEqual(calls[0], ['command', 'mdSlideTool.buildRemotePptx', 'vscode-remote://dev-container/work/slides.qmd']);
  assert.deepEqual(calls[1], ['fileUri', 'C:\\Project\\slides.pptx']);
  assert.equal(calls[2][1].scheme, 'file');
});

test('remote build command failure prevents local open', async () => {
  let openCalls = 0;
  await assert.rejects(buildAndOpenLocally({
    qmdUri: 'vscode-remote://dev-container/work/slides.qmd',
    executeCommand: async () => { throw new Error('Quarto failed'); },
    fileUri: (hostPath) => ({ scheme: 'file', fsPath: hostPath }),
    openExternal: async () => { openCalls += 1; return true; },
  }), /PowerPoint was not opened.*Quarto failed/);
  assert.equal(openCalls, 0);
});

test('local open failure preserves successful remote build result', async () => {
  const result = await buildAndOpenLocally({
    qmdUri: 'vscode-remote://dev-container/work/slides.qmd',
    executeCommand: async () => ({ status: 'built', pptxPath: '/work/slides.qmd', hostPath: 'C:\\Project\\slides.pptx' }),
    fileUri: (hostPath) => ({ scheme: 'file', fsPath: hostPath }),
    openExternal: async () => false,
  });
  assert.equal(result.status, 'built-host-bridge-unavailable');
  assert.equal(result.hostPath, 'C:\\Project\\slides.pptx');
});

test('UI rejects non-local URIs from its opener abstraction', async () => {
  const result = await buildAndOpenLocally({
    qmdUri: 'vscode-remote://dev-container/work/slides.qmd',
    executeCommand: async () => ({ status: 'built', pptxPath: '/work/slides.pptx', hostPath: '/host/slides.pptx' }),
    fileUri: () => ({ scheme: 'vscode-remote' }), openExternal: async () => true,
  });
  assert.equal(result.status, 'built-host-bridge-unavailable');
  assert.match(result.error, /local file URI/);
});
