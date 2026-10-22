import path from 'node:path';

function isWindowsPath(value) {
  return /^[A-Za-z]:[\\/]/.test(value) || /^\\\\/.test(value);
}

function toHostFileUri(hostPath) {
  if (!isWindowsPath(hostPath)) {
    const encodedPath = hostPath.split('/').map(encodeURIComponent).join('/');
    return `file://${encodedPath.startsWith('/') ? '' : '/'}${encodedPath}`;
  }

  const normalized = hostPath.replaceAll('\\', '/');
  if (normalized.startsWith('//')) {
    const [authority, ...segments] = normalized.slice(2).split('/');
    return `file://${authority}/${segments.map(encodeURIComponent).join('/')}`;
  }

  const [drive, ...segments] = normalized.split('/');
  return `file:///${drive}/${segments.map(encodeURIComponent).join('/')}`;
}

export function mapContainerPathToHostUri(containerPath, containerWorkspace, hostWorkspace) {
  if (!containerPath || !containerWorkspace || !hostWorkspace) {
    throw new Error('Container path mapping is not configured.');
  }

  const absoluteContainerPath = path.posix.resolve(containerPath);
  const absoluteContainerWorkspace = path.posix.resolve(containerWorkspace);
  const relativePath = path.posix.relative(absoluteContainerWorkspace, absoluteContainerPath);
  if (relativePath === '..' || relativePath.startsWith(`..${path.posix.sep}`) || path.posix.isAbsolute(relativePath)) {
    throw new Error('The PPTX is outside the mapped workspace.');
  }

  const parts = relativePath ? relativePath.split(path.posix.sep) : [];
  const hostPath = isWindowsPath(hostWorkspace)
    ? path.win32.resolve(hostWorkspace, ...parts)
    : path.posix.resolve(hostWorkspace, ...parts);
  return { hostPath, uri: toHostFileUri(hostPath) };
}

export async function buildAndOpenPowerPoint({
  qmdPath,
  workspaceRoot,
  hostWorkspace,
  runBuild,
  outputExists,
  openExternal,
}) {
  const absoluteQmdPath = path.posix.resolve(qmdPath);
  const relativeQmdPath = path.posix.relative(path.posix.resolve(workspaceRoot), absoluteQmdPath);
  if (relativeQmdPath === '..' || relativeQmdPath.startsWith('../') || path.posix.isAbsolute(relativeQmdPath)) {
    throw new Error('Select a QMD file inside the workspace.');
  }
  if (path.posix.extname(absoluteQmdPath).toLowerCase() !== '.qmd') {
    throw new Error('Select a .qmd file to build.');
  }

  await runBuild(absoluteQmdPath);
  const parsedQmd = path.posix.parse(absoluteQmdPath);
  const pptxPath = path.posix.join(parsedQmd.dir, `${parsedQmd.name}.pptx`);
  if (!await outputExists(pptxPath)) throw new Error(`PPTX build completed without creating the expected output: ${pptxPath}`);

  let mapped;
  try {
    mapped = mapContainerPathToHostUri(pptxPath, workspaceRoot, hostWorkspace);
    const opened = await openExternal(mapped.uri);
    if (!opened) return { status: 'built-host-bridge-unavailable', pptxPath, hostPath: mapped.hostPath };
    return { status: 'built-and-opened', pptxPath, hostPath: mapped.hostPath };
  } catch (error) {
    return { status: 'built-host-bridge-unavailable', pptxPath, error };
  }
}
