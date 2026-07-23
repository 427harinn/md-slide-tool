const vscode = acquireVsCodeApi();
const refresh = document.getElementById('refresh');
const statusEl = document.getElementById('status');
const errorEl = document.getElementById('error');
const slidesEl = document.getElementById('slides');
let busy = false;

refresh.addEventListener('click', () => {
  if (!busy) vscode.postMessage({ type: 'refresh' });
});

function setBusy(nextBusy, message) {
  busy = nextBusy;
  refresh.disabled = nextBusy;
  if (message) statusEl.textContent = message;
}

async function renderPdf(uri) {
  try {
    setBusy(true, 'Rendering PDF…');
    errorEl.hidden = true;
    const pdfjs = await import(window.__PDFJS_URL__);
    pdfjs.GlobalWorkerOptions.workerSrc = window.__PDFJS_WORKER_URL__;
    const pdf = await pdfjs.getDocument(uri).promise;
    const nextSlides = document.createDocumentFragment();
    for (let pageNo = 1; pageNo <= pdf.numPages; pageNo += 1) {
      const page = await pdf.getPage(pageNo);
      const viewport = page.getViewport({ scale: 1.4 });
      const section = document.createElement('section');
      section.className = 'slide';
      const title = document.createElement('div');
      title.className = 'slide-title';
      title.textContent = `Slide ${pageNo} / ${pdf.numPages}`;
      const canvas = document.createElement('canvas');
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      section.append(title, canvas);
      nextSlides.append(section);
      await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
    }
    slidesEl.replaceChildren(nextSlides);
    setBusy(false, `Rendered ${pdf.numPages} slide${pdf.numPages === 1 ? '' : 's'}.`);
    vscode.postMessage({ type: 'renderComplete', pageCount: pdf.numPages });
  } catch (error) {
    errorEl.textContent = 'The PDF could not be loaded or rendered.';
    errorEl.hidden = false;
    setBusy(false, 'Render failed');
    vscode.postMessage({ type: 'renderFailed', message: error?.message ?? String(error) });
  }
}

window.addEventListener('message', (event) => {
  const message = event.data;
  if (message.type === 'loading') setBusy(true, message.message ?? 'Loading…');
  if (message.type === 'idle') setBusy(false);
  if (message.type === 'error') {
    errorEl.textContent = message.message;
    errorEl.hidden = false;
    setBusy(false, 'Error');
  }
  if (message.type === 'pdf') renderPdf(message.uri);
});
