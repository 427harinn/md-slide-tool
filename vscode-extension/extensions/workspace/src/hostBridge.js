import path from 'node:path';

function isWindowsPath(value) {
  return /^[A-Za-z]:[\\/]/.test(value) || /^\\\\/.test(value);
}

export function mapContainerPathToHostPath(containerPath, containerWorkspace, hostWorkspace) {
  if (!containerPath || !containerWorkspace || !hostWorkspace) {
    throw new Error('Host workspace path mapping is not configured. Reopen this project in the Dev Container.');
  }

  const absoluteContainerPath = path.posix.resolve(containerPath);
  const absoluteWorkspacePath = path.posix.resolve(containerWorkspace);
  const relativePath = path.posix.relative(absoluteWorkspacePath, absoluteContainerPath);
  if (relativePath === '..' || relativePath.startsWith('../') || path.posix.isAbsolute(relativePath)) {
    throw new Error('The PPTX output is outside the mapped workspace.');
  }

  const segments = relativePath ? relativePath.split('/') : [];
  return isWindowsPath(hostWorkspace)
    ? path.win32.resolve(hostWorkspace, ...segments)
    : path.posix.resolve(hostWorkspace, ...segments);
}

export async function buildPptxForHost({ qmdPath, workspacePath, hostWorkspace, runBuild, outputExists }) {
  const inputPath = path.posix.resolve(qmdPath);
  const rootPath = path.posix.resolve(workspacePath);
  const relativeInput = path.posix.relative(rootPath, inputPath);
  if (relativeInput === '..' || relativeInput.startsWith('../') || path.posix.isAbsolute(relativeInput)) {
    throw new Error('Select a QMD file inside the workspace.');
  }
  if (path.posix.extname(inputPath).toLowerCase() !== '.qmd') {
    throw new Error('Select a .qmd file to build.');
  }

  await runBuild(inputPath);
  const parsedInput = path.posix.parse(inputPath);
  const pptxPath = path.posix.join(parsedInput.dir, `${parsedInput.name}.pptx`);
  if (!await outputExists(pptxPath)) {
    throw new Error(`PPTX build completed without creating the expected output: ${pptxPath}`);
  }

  try {
    return {
      status: 'built',
      pptxPath,
      hostPath: mapContainerPathToHostPath(pptxPath, workspacePath, hostWorkspace),
    };
  } catch (error) {
    return { status: 'built-host-bridge-unavailable', pptxPath, error: error.message };
  }
}

export async function resolveCanonicalPptxForHost({ qmdPath, workspacePath, hostWorkspace, inspectCanonical, outputExists }) {
  const inputPath = path.posix.resolve(qmdPath);
  const rootPath = path.posix.resolve(workspacePath);
  const relativeInput = path.posix.relative(rootPath, inputPath);
  if (relativeInput === '..' || relativeInput.startsWith('../') || path.posix.isAbsolute(relativeInput)) {
    throw new Error('Select a QMD file inside the workspace.');
  }
  if (path.posix.extname(inputPath).toLowerCase() !== '.qmd') throw new Error('Select a .qmd file.');

  const expectedPath = `${inputPath.slice(0, -path.posix.extname(inputPath).length)}.pptx`;
  const canonicalPath = path.posix.resolve(await inspectCanonical(inputPath));
  if (canonicalPath !== expectedPath) throw new Error('Workspace returned a non-canonical PowerPoint path.');
  if (!await outputExists(canonicalPath)) throw new Error(`Canonical managed PPTX does not exist: ${canonicalPath}`);
  return {
    status: 'canonical-ready',
    pptxPath: canonicalPath,
    hostPath: mapContainerPathToHostPath(canonicalPath, rootPath, hostWorkspace),
  };
}

export async function generateVersionedPreviewForHost({ qmdPath, workspacePath, hostWorkspace, runPreview, outputExists }) {
  const inputPath = path.posix.resolve(qmdPath);
  const rootPath = path.posix.resolve(workspacePath);
  const relativeInput = path.posix.relative(rootPath, inputPath);
  if (relativeInput === '..' || relativeInput.startsWith('../') || path.posix.isAbsolute(relativeInput)) {
    throw new Error('Select a QMD file inside the workspace.');
  }
  if (path.posix.extname(inputPath).toLowerCase() !== '.qmd') throw new Error('Select a .qmd file.');

  const output = await runPreview(inputPath);
  const lines = String(output).split(/\r?\n/);
  const readOne = (key) => {
    const matches = lines.filter((line) => line.startsWith(`${key}=`));
    if (matches.length !== 1 || !matches[0].slice(key.length + 1)) {
      throw new Error(`Preview generation did not return exactly one ${key} value.`);
    }
    return matches[0].slice(key.length + 1);
  };
  const reportedPath = readOne('PREVIEW_PATH');
  const documentId = readOne('PREVIEW_DOCUMENT_ID');
  const sourceQmd = path.posix.resolve(readOne('PREVIEW_SOURCE_QMD'));
  if (sourceQmd !== inputPath) throw new Error('Preview source QMD does not match the selected document.');
  const previewPath = path.posix.resolve(reportedPath);
  const previewRoot = path.posix.resolve(path.posix.dirname(inputPath), '.md-slide-tool', 'previews');
  const relativePreview = path.posix.relative(previewRoot, previewPath);
  const parts = relativePreview.split('/');
  const previewName = parts.at(-1) ?? '';
  if (relativePreview === '..' || relativePreview.startsWith('../') || path.posix.isAbsolute(relativePreview) ||
      parts.length !== 2 || parts.at(-2) !== documentId ||
      !/^document-[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(documentId) ||
      !/^preview-\d{6,}\.pptx$/.test(previewName)) {
    throw new Error('Workspace returned a preview outside the selected QMD project directory.');
  }
  if (!await outputExists(previewPath)) throw new Error(`Generated preview does not exist: ${previewPath}`);
  const generation = Number(previewName.slice('preview-'.length, -'.pptx'.length));
  return {
    status: 'preview-ready', previewPath, generation, documentId, sourceQmd,
    hostPath: mapContainerPathToHostPath(previewPath, rootPath, hostWorkspace),
    previousPreviewsClosed: false,
    note: 'PowerPoint open/dirty state was not inspected; all prior previews remain open.',
  };
}
