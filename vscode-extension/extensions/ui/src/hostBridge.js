const BUILD_COMMAND = 'mdSlideTool.buildRemotePptx';

export async function buildAndOpenLocally({ qmdUri, executeCommand, fileUri, openExternal }) {
  let result;
  try {
    result = await executeCommand(BUILD_COMMAND, qmdUri);
  } catch (error) {
    throw new Error(`PPTX build failed. PowerPoint was not opened. ${error?.message ?? error}`);
  }

  if (!result || result.status !== 'built') {
    return {
      status: 'built-host-bridge-unavailable',
      pptxPath: result?.pptxPath,
      error: result?.error ?? 'The workspace extension could not map the PPTX to a host path.',
    };
  }

  try {
    if (typeof result.hostPath !== 'string' || !result.hostPath) {
      throw new Error('The workspace extension returned no host path.');
    }
    const uri = fileUri(result.hostPath);
    if (uri.scheme !== 'file') throw new Error('The host extension did not create a local file URI.');
    const opened = await openExternal(uri);
    if (!opened) throw new Error('VS Code could not open the host file with its default application.');
    return { status: 'built-and-opened', pptxPath: result.pptxPath, hostPath: result.hostPath };
  } catch (error) {
    return {
      status: 'built-host-bridge-unavailable',
      pptxPath: result.pptxPath,
      hostPath: result.hostPath,
      error: error.message,
    };
  }
}
