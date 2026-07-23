export class PreviewError extends Error {
  constructor(code, userMessage, detail, cause) { super(userMessage); this.name = 'PreviewError'; this.code = code; this.userMessage = userMessage; this.detail = detail ?? userMessage; this.cause = cause; }
}
export const messages = {
  notFound: 'The selected PPTX file does not exist.',
  notPptx: 'Please select a .pptx file.',
  libreOfficeMissing: 'LibreOffice was not found in the Dev Container PATH. Rebuild the Dev Container image, then run Refresh again.',
  libreOfficeLaunchFailed: 'LibreOffice could not be started.',
  conversionFailed: 'LibreOffice could not convert the PPTX to PDF.',
  pdfMissing: 'LibreOffice finished, but no PDF was generated.',
  renderFailed: 'The PDF could not be loaded or rendered.',
  deletedDuringRefresh: 'The PPTX file was deleted during refresh.',
  cancelled: 'The preview operation was cancelled.'
};
