import path from 'node:path';

function isWindowsPath(value) {
  return /^[A-Za-z]:[\\/]/.test(value) || /^\\\\/.test(value);
}

function toFileUri(hostPath) {
  if (isWindowsPath(hostPath)) {
    const normalized = hostPath.replaceAll('\\', '/');
    if (normalized.startsWith('//')) {
      const [authority, ...segments] = normalized.slice(2).split('/');
      return `file://${authority}/${segments.map(encodeURIComponent).join('/')}`;
    }
    const [drive, ...segments] = normalized.split('/');
    return `file:///${drive}/${segments.map(encodeURIComponent).join('/')}`;
  }
  const encodedPath = hostPath.split('/').map(encodeURIComponent).join('/');
  return `file://${encodedPath.startsWith('/') ? '' : '/'}${encodedPath}`;
}

export function mapContainerPathToHostUri(containerPath, containerWorkspace, hostWorkspace) {
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
  const hostPath = isWindowsPath(hostWorkspace)
    ? path.win32.resolve(hostWorkspace, ...segments)
    : path.posix.resolve(hostWorkspace, ...segments);
  return { hostPath, uri: toFileUri(hostPath) };
}

export async function buildAndOpenPowerPoint({
  qmdPath,
  workspacePath,
  hostWorkspace,
  runBuild,
  outputExists,
  openExternal,
}) {
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
    const mapped = mapContainerPathToHostUri(pptxPath, workspacePath, hostWorkspace);
    const opened = await openExternal(mapped.uri);
    if (!opened) return { status: 'built-host-bridge-unavailable', pptxPath, hostPath: mapped.hostPath };
    return { status: 'built-and-opened', pptxPath, hostPath: mapped.hostPath };
  } catch (error) {
    return { status: 'built-host-bridge-unavailable', pptxPath, error };
  }
}
