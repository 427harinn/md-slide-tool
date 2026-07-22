// Minimal local PDF.js-compatible loader placeholder for offline development builds.
// Replace with pdfjs-dist/build/pdf.mjs when packaging in an environment with npm access.
export const GlobalWorkerOptions = { workerSrc: '' };
export function getDocument() { return { promise: Promise.reject(new Error('Bundled PDF.js is unavailable in this offline build. Run npm install in vscode-extension to use pdfjs-dist.')) }; }
