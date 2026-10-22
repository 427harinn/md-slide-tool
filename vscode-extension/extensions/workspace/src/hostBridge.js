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
