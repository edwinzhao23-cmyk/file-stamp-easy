import './style.css';
import * as pdfjsLib from 'pdfjs-dist';
import workerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url';
import { PDFDocument } from 'pdf-lib';

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;

const STORAGE_KEY = 'file-stamp-easy-web-state-v2';
const MM_TO_PT = 72 / 25.4;

const state = {
  pdfBytes: null,
  pdfDoc: null,
  pdfName: '',
  outputName: '文件盖章易_已盖章.pdf',
  pageIndex: 0,
  pageCount: 0,
  zoom: 1.25,
  mode: 'view',
  selectedMarkId: '',
  marks: [],
  stamps: {
    normal: defaultStamp('normal', 40, 40),
    signature: defaultStamp('signature', 35, 15),
    seam: defaultStamp('seam', 120, 40),
  },
};

function defaultStamp(type, widthMm, heightMm) {
  return {
    type,
    sourceDataUrl: '',
    processedDataUrl: '',
    widthMm,
    heightMm,
    removeWhite: true,
    whiteThreshold: 245,
    opacity: 0.92,
    mottled: 0.03,
    soften: 0.12,
  };
}

document.querySelector('#app').innerHTML = `
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">${icon('stamp')}</div>
      <div>
        <strong>文件盖章易 Web</strong>
        <span>本地浏览器处理，不上传文件</span>
      </div>
    </div>
    <label class="file-button">${icon('file')}<input id="pdfFile" type="file" accept="application/pdf" />选择 PDF</label>
    <label class="output-field">
      <span>输出文件名</span>
      <input id="outputName" value="${state.outputName}" />
    </label>
    <button id="exportBtn" class="primary">${icon('download')}导出已盖章 PDF</button>
  </header>

  <main class="workspace">
    <aside class="sidebar">
      <section class="card drop-card" data-stamp-target="normal">
        <h2>普通公章</h2>
        <label class="file-button full">${icon('image')}<input id="normalFile" type="file" accept="image/*" />选择图片 / 拖入图片</label>
        <div class="grid2">
          <label>宽度 mm<input id="normalW" type="number" value="40" min="1" /></label>
          <label>高度 mm<input id="normalH" type="number" value="40" min="1" /></label>
        </div>
        <div class="card-actions">
          <button data-copy-current="normal">当前页应用到全部页</button>
        </div>
      </section>

      <section class="card drop-card" data-stamp-target="signature">
        <h2>法人签字章</h2>
        <label class="file-button full">${icon('image')}<input id="signatureFile" type="file" accept="image/*" />选择图片 / 拖入图片</label>
        <div class="grid2">
          <label>宽度 mm<input id="signatureW" type="number" value="35" min="1" /></label>
          <label>高度 mm<input id="signatureH" type="number" value="15" min="1" /></label>
        </div>
        <div class="card-actions">
          <button data-copy-current="signature">当前页应用到全部页</button>
        </div>
      </section>

      <section class="card drop-card" data-stamp-target="seam">
        <h2>骑缝章</h2>
        <label class="switch"><input id="seamEnabled" type="checkbox" />启用骑缝章</label>
        <label class="file-button full">${icon('image')}<input id="seamFile" type="file" accept="image/*" />选择骑缝章图片</label>
        <label>页码范围<input id="seamPages" value="全部" /></label>
        <div class="grid2">
          <label>总宽 mm<input id="seamW" type="number" value="120" min="1" /></label>
          <label>总高 mm<input id="seamH" type="number" value="40" min="1" /></label>
          <label>离边 mm<input id="seamEdge" type="number" value="0" min="0" /></label>
          <label>沿边 mm<input id="seamOffset" type="number" value="80" min="0" /></label>
        </div>
        <select id="seamSide"><option value="right">右侧</option><option value="left">左侧</option></select>
      </section>

      <section class="card">
        <h2>印章处理</h2>
        <select id="processTarget">
          <option value="normal">普通公章</option>
          <option value="signature">法人签字章</option>
          <option value="seam">骑缝章</option>
        </select>
        <label class="switch"><input id="removeWhite" type="checkbox" checked />去白底</label>
        <label>白底阈值<input id="whiteThreshold" type="range" min="220" max="255" value="245" /></label>
        <label>印泥透明度<input id="opacity" type="range" min="0.3" max="1" step="0.01" value="0.92" /></label>
        <label>斑驳强度<input id="mottled" type="range" min="0" max="0.12" step="0.005" value="0.03" /></label>
        <label>边缘柔化<input id="soften" type="range" min="0" max="0.5" step="0.01" value="0.12" /></label>
        <div id="stampPreview" class="stamp-preview">印章预览</div>
      </section>

      <section class="card">
        <h2>页面标记</h2>
        <div class="mark-summary" id="markSummary">暂无 PDF</div>
        <ul id="markList" class="mark-list"></ul>
        <div class="card-actions wrap">
          <button id="selectCurrent">选中当前项</button>
          <button id="deleteMark" class="danger">${icon('trash')}删除选中</button>
          <button id="clearPage">清空当前页</button>
          <button id="clearAll" class="danger-light">清空全部</button>
          <button id="copyPage">当前页复制到全部</button>
        </div>
      </section>
    </aside>

    <section class="preview-pane">
      <div class="preview-toolbar">
        <button id="prevPage">上一页</button>
        <input id="pageInput" value="1" />
        <span id="pageTotal">/ -</span>
        <button id="nextPage">下一页</button>
        <button id="zoomOut">缩小</button>
        <span id="zoomText">125%</span>
        <button id="zoomIn">放大</button>
        <button id="fitWidth">适合宽度</button>
        <div class="segmented">
          <button data-mode="view" class="active">${icon('cursor')}查看</button>
          <button data-mode="normal">${icon('stamp')}放公章</button>
          <button data-mode="signature">${icon('pen')}放签字</button>
        </div>
        <button id="resetBtn">${icon('reset')}清空当前页</button>
      </div>
      <div id="pageStage" class="page-stage">
        <div class="empty">选择 PDF 后在这里预览和放置印章</div>
      </div>
      <div id="status" class="status">就绪</div>
    </section>
  </main>

  <footer id="log" class="log">就绪：请选择 PDF 和印章图片。</footer>
`;

const $ = (id) => document.getElementById(id);

bind();
restoreState();
refreshAll();

function bind() {
  $('pdfFile').addEventListener('change', (event) => {
    const file = event.target.files?.[0];
    if (file) loadPdf(file);
  });

  ['normal', 'signature', 'seam'].forEach((type) => {
    $(`${type}File`).addEventListener('change', (event) => {
      const file = event.target.files?.[0];
      if (file) loadStamp(type, file);
    });
  });

  ['normalW', 'normalH', 'signatureW', 'signatureH', 'seamW', 'seamH', 'seamPages', 'seamEdge', 'seamOffset', 'seamSide', 'seamEnabled'].forEach((id) => {
    $(id).addEventListener('input', syncSettings);
    $(id).addEventListener('change', syncSettings);
  });

  ['processTarget', 'removeWhite', 'whiteThreshold', 'opacity', 'mottled', 'soften'].forEach((id) => {
    $(id).addEventListener('input', syncProcessControls);
    $(id).addEventListener('change', syncProcessControls);
  });

  $('outputName').addEventListener('input', () => {
    state.outputName = $('outputName').value.trim() || '文件盖章易_已盖章.pdf';
    saveState();
  });

  document.querySelectorAll('[data-mode]').forEach((button) => {
    button.addEventListener('click', () => setMode(button.dataset.mode));
  });

  $('prevPage').addEventListener('click', () => goPage(state.pageIndex - 1));
  $('nextPage').addEventListener('click', () => goPage(state.pageIndex + 1));
  $('pageInput').addEventListener('change', () => goPage(Number($('pageInput').value) - 1));
  $('zoomIn').addEventListener('click', () => setZoom(state.zoom + 0.15));
  $('zoomOut').addEventListener('click', () => setZoom(state.zoom - 0.15));
  $('fitWidth').addEventListener('click', fitWidth);
  $('deleteMark').addEventListener('click', deleteSelected);
  $('resetBtn').addEventListener('click', clearCurrentPageMarks);
  $('clearPage').addEventListener('click', clearCurrentPageMarks);
  $('clearAll').addEventListener('click', clearAllMarks);
  $('copyPage').addEventListener('click', copyCurrentPageToAll);
  $('selectCurrent').addEventListener('click', selectCurrentMark);
  $('exportBtn').addEventListener('click', exportPdf);
  $('pageStage').addEventListener('click', placeMark);
  $('markList').addEventListener('click', handleMarkListClick);

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Delete') deleteSelected();
  });

  setupDropHandling();
  window.addEventListener('beforeunload', saveState);
}

function setupDropHandling() {
  document.addEventListener('dragover', (event) => {
    event.preventDefault();
  });

  document.addEventListener('drop', async (event) => {
    event.preventDefault();
    const file = event.dataTransfer?.files?.[0];
    if (!file) return;
    if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
      await loadPdf(file);
      return;
    }
    if (file.type.startsWith('image/')) {
      const target = event.target.closest?.('[data-stamp-target]')?.dataset.stampTarget || $('processTarget').value;
      await loadStamp(target, file);
    }
  });
}

async function loadPdf(file) {
  state.pdfBytes = await file.arrayBuffer();
  state.pdfDoc = await pdfjsLib.getDocument({ data: state.pdfBytes.slice(0) }).promise;
  state.pageCount = state.pdfDoc.numPages;
  state.pageIndex = 0;
  state.marks = [];
  state.pdfName = file.name;
  state.outputName = `${file.name.replace(/\.[^.]+$/, '')}_已盖章.pdf`;
  $('outputName').value = state.outputName;
  log(`已载入 PDF：${file.name}，共 ${state.pageCount} 页。`);
  saveState();
  await renderPage();
}

async function loadStamp(type, file) {
  const stamp = state.stamps[type];
  stamp.sourceDataUrl = await readAsDataUrl(file);
  stamp.processedDataUrl = '';
  $('processTarget').value = type;
  await processStamp(type);
  log(`已载入${labelOf(type)}图片：${file.name}`);
  saveState();
  refreshAll();
}

function syncSettings() {
  state.stamps.normal.widthMm = Number($('normalW').value || 40);
  state.stamps.normal.heightMm = Number($('normalH').value || 40);
  state.stamps.signature.widthMm = Number($('signatureW').value || 35);
  state.stamps.signature.heightMm = Number($('signatureH').value || 15);
  state.stamps.seam.widthMm = Number($('seamW').value || 120);
  state.stamps.seam.heightMm = Number($('seamH').value || 40);
  state.stamps.seam.removeWhite = $('removeWhite').checked;
  state.stamps.seam.whiteThreshold = Number($('whiteThreshold').value);
  state.stamps.seam.opacity = Number($('opacity').value);
  state.stamps.seam.mottled = Number($('mottled').value);
  state.stamps.seam.soften = Number($('soften').value);
  saveState();
  refreshAll();
}

async function syncProcessControls() {
  const type = $('processTarget').value;
  const stamp = state.stamps[type];
  stamp.removeWhite = $('removeWhite').checked;
  stamp.whiteThreshold = Number($('whiteThreshold').value);
  stamp.opacity = Number($('opacity').value);
  stamp.mottled = Number($('mottled').value);
  stamp.soften = Number($('soften').value);
  if (stamp.sourceDataUrl) {
    await processStamp(type);
    saveState();
    refreshAll();
  }
}

async function processStamp(type) {
  const stamp = state.stamps[type];
  if (!stamp.sourceDataUrl) return;
  const img = await readImage(stamp.sourceDataUrl);
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0);
  const image = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = image.data;
  let minX = canvas.width;
  let minY = canvas.height;
  let maxX = 0;
  let maxY = 0;
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    let alpha = data[i + 3];
    if (stamp.removeWhite && r >= stamp.whiteThreshold && g >= stamp.whiteThreshold && b >= stamp.whiteThreshold) {
      alpha = 0;
    }
    const darkness = Math.max(0, 255 - (r * 0.3 + g * 0.59 + b * 0.11));
    const noise = 1 - seededNoise(i) * stamp.mottled;
    data[i] = 215;
    data[i + 1] = 25;
    data[i + 2] = 32;
    data[i + 3] = Math.min(255, Math.round(Math.max(alpha, darkness) * stamp.opacity * noise));
    if (data[i + 3] > 8) {
      const px = (i / 4) % canvas.width;
      const py = Math.floor((i / 4) / canvas.width);
      minX = Math.min(minX, px);
      minY = Math.min(minY, py);
      maxX = Math.max(maxX, px);
      maxY = Math.max(maxY, py);
    }
  }
  ctx.putImageData(image, 0, 0);
  const trimmed = cropCanvas(canvas, minX, minY, maxX, maxY);
  stamp.processedDataUrl = trimmed.toDataURL('image/png');
  if ($('processTarget').value === type) {
    $('stampPreview').innerHTML = `<img src="${stamp.processedDataUrl}" alt="${labelOf(type)}预览" />`;
  }
}

async function renderPage() {
  if (!state.pdfDoc) {
    $('pageStage').innerHTML = '<div class="empty">选择 PDF 后在这里预览和放置印章</div>';
    refreshMarkPanel();
    return;
  }
  const page = await state.pdfDoc.getPage(state.pageIndex + 1);
  const viewport = page.getViewport({ scale: state.zoom });
  $('pageStage').innerHTML = `
    <div id="pageWrap" class="page-wrap" style="width:${viewport.width}px;height:${viewport.height}px">
      <canvas id="pdfCanvas" width="${viewport.width}" height="${viewport.height}"></canvas>
      <div id="markLayer" class="mark-layer"></div>
    </div>
  `;
  await page.render({ canvasContext: $('pdfCanvas').getContext('2d'), viewport }).promise;
  $('pageInput').value = state.pageIndex + 1;
  $('pageTotal').textContent = `/ ${state.pageCount}`;
  $('zoomText').textContent = `${Math.round(state.zoom * 100)}%`;
  refreshMarkPanel();
  drawMarks();
}

function drawMarks() {
  const layer = $('markLayer');
  if (!layer) return;
  layer.innerHTML = '';
  const pageMarks = state.marks.filter((mark) => mark.pageIndex === state.pageIndex);
  for (const mark of pageMarks) {
    const stamp = state.stamps[mark.type];
    const el = document.createElement('div');
    el.className = `mark ${mark.type} ${state.selectedMarkId === mark.id ? 'selected' : ''}`;
    el.style.left = `${mark.xPt * state.zoom}px`;
    el.style.top = `${mark.yPt * state.zoom}px`;
    el.style.width = `${mark.widthPt * state.zoom}px`;
    el.style.height = `${mark.heightPt * state.zoom}px`;
    if (stamp.processedDataUrl) {
      el.innerHTML = `<img src="${stamp.processedDataUrl}" alt="${labelOf(mark.type)}" />`;
    } else {
      el.textContent = labelOf(mark.type);
    }
    el.addEventListener('click', (event) => {
      event.stopPropagation();
      selectMark(mark.id);
    });
    enableDrag(el, mark);
    layer.appendChild(el);
  }
  const current = pageMarks.filter((m) => m.type === 'normal').length;
  const signature = pageMarks.filter((m) => m.type === 'signature').length;
  $('status').textContent = `第 ${state.pageIndex + 1} / ${state.pageCount || '-'} 页，普通章 ${current} 个，签字章 ${signature} 个，缩放 ${Math.round(state.zoom * 100)}%`;
}

function refreshAll() {
  updatePreview();
  refreshMarkPanel();
  drawMarks();
}

function updatePreview() {
  const stamp = state.stamps[$('processTarget').value];
  if (stamp.processedDataUrl) {
    $('stampPreview').innerHTML = `<img src="${stamp.processedDataUrl}" alt="印章预览" />`;
  } else {
    $('stampPreview').textContent = '印章预览';
  }
}

function refreshMarkPanel() {
  const summary = $('markSummary');
  const list = $('markList');
  if (!state.pdfDoc) {
    summary.textContent = '暂无 PDF';
    list.innerHTML = '';
    return;
  }
  const pageMarks = state.marks.filter((mark) => mark.pageIndex === state.pageIndex);
  const totalNormal = pageMarks.filter((m) => m.type === 'normal').length;
  const totalSignature = pageMarks.filter((m) => m.type === 'signature').length;
  summary.textContent = `当前页 ${state.pageIndex + 1}/${state.pageCount}，普通章 ${totalNormal} 个，签字章 ${totalSignature} 个，标记总数 ${pageMarks.length}`;
  list.innerHTML = pageMarks.length
    ? pageMarks.map((mark, index) => `
        <li class="${mark.id === state.selectedMarkId ? 'selected' : ''}" data-mark-id="${mark.id}">
          <span>${index + 1}. ${labelOf(mark.type)}</span>
          <small>x=${mark.xPt.toFixed(1)}pt, y=${mark.yPt.toFixed(1)}pt</small>
        </li>
      `).join('')
    : '<li class="empty-item">当前页暂无标记</li>';
}

function handleMarkListClick(event) {
  const item = event.target.closest('[data-mark-id]');
  if (!item) return;
  selectMark(item.dataset.markId);
}

function selectMark(markId) {
  state.selectedMarkId = markId;
  drawMarks();
  refreshMarkPanel();
}

function selectCurrentMark() {
  const current = state.marks.filter((mark) => mark.pageIndex === state.pageIndex);
  if (!current.length) return log('当前页没有可选中的标记。', 'warning');
  selectMark(current[current.length - 1].id);
}

function enableDrag(el, mark) {
  el.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    event.stopPropagation();
    el.setPointerCapture(event.pointerId);
    selectMark(mark.id);
    const startX = event.clientX;
    const startY = event.clientY;
    const originalX = mark.xPt;
    const originalY = mark.yPt;
    const move = (moveEvent) => {
      mark.xPt = Math.max(0, originalX + (moveEvent.clientX - startX) / state.zoom);
      mark.yPt = Math.max(0, originalY + (moveEvent.clientY - startY) / state.zoom);
      refreshMarkPanel();
      drawMarks();
    };
    const up = () => {
      el.removeEventListener('pointermove', move);
      el.removeEventListener('pointerup', up);
      saveState();
    };
    el.addEventListener('pointermove', move);
    el.addEventListener('pointerup', up);
  });
}

function placeMark(event) {
  if (!state.pdfDoc || state.mode === 'view') return;
  const wrap = $('pageWrap');
  if (!wrap || !wrap.contains(event.target)) return;
  const rect = wrap.getBoundingClientRect();
  const stamp = state.stamps[state.mode];
  const widthPt = stamp.widthMm * MM_TO_PT;
  const heightPt = stamp.heightMm * MM_TO_PT;
  const xPt = (event.clientX - rect.left) / state.zoom - widthPt / 2;
  const yPt = (event.clientY - rect.top) / state.zoom - heightPt / 2;
  const mark = {
    id: crypto.randomUUID(),
    type: state.mode,
    pageIndex: state.pageIndex,
    xPt: Math.max(0, xPt),
    yPt: Math.max(0, yPt),
    widthPt,
    heightPt,
  };
  state.marks.push(mark);
  selectMark(mark.id);
  saveState();
}

function deleteSelected() {
  if (!state.selectedMarkId) return;
  const before = state.marks.length;
  state.marks = state.marks.filter((mark) => mark.id !== state.selectedMarkId);
  state.selectedMarkId = '';
  if (state.marks.length !== before) log('已删除选中的标记。');
  saveState();
  refreshMarkPanel();
  drawMarks();
}

function clearCurrentPageMarks() {
  const before = state.marks.length;
  state.marks = state.marks.filter((mark) => mark.pageIndex !== state.pageIndex);
  state.selectedMarkId = '';
  if (state.marks.length !== before) log('已清空当前页标记。');
  saveState();
  refreshMarkPanel();
  drawMarks();
}

function clearAllMarks() {
  state.marks = [];
  state.selectedMarkId = '';
  log('已清空全部标记。');
  saveState();
  refreshMarkPanel();
  drawMarks();
}

function copyCurrentPageToAll() {
  if (!state.pdfDoc) return;
  const currentMarks = state.marks.filter((mark) => mark.pageIndex === state.pageIndex);
  if (!currentMarks.length) return log('当前页没有可复制的标记。', 'warning');
  const copies = [];
  for (let pageIndex = 0; pageIndex < state.pageCount; pageIndex += 1) {
    if (pageIndex === state.pageIndex) continue;
    for (const mark of currentMarks) {
      copies.push({
        ...structuredClone(mark),
        id: crypto.randomUUID(),
        pageIndex,
      });
    }
  }
  state.marks.push(...copies);
  log(`已将当前页标记复制到其余 ${state.pageCount - 1} 页。`);
  saveState();
  refreshMarkPanel();
  drawMarks();
}

async function exportPdf() {
  if (!state.pdfBytes) return log('请先选择 PDF。', 'error');
  const doc = await PDFDocument.load(state.pdfBytes.slice(0));
  const stampErrors = [];
  for (const mark of state.marks) {
    const stamp = state.stamps[mark.type];
    if (!stamp.processedDataUrl) continue;
    await drawStampOnPdf(doc, mark, stamp);
  }
  if ($('seamEnabled').checked) {
    try {
      await exportSeam(doc);
    } catch (error) {
      stampErrors.push(error.message);
    }
  }
  if (stampErrors.length) {
    log(stampErrors[0], 'error');
    return;
  }
  const bytes = await doc.save();
  const filename = $('outputName').value.trim() || state.outputName || '文件盖章易_已盖章.pdf';
  downloadBytes(bytes, filename.endsWith('.pdf') ? filename : `${filename}.pdf`);
  log('导出完成。');
}

async function drawStampOnPdf(doc, mark, stamp) {
  const page = doc.getPage(mark.pageIndex);
  const image = await doc.embedPng(stamp.processedDataUrl);
  page.drawImage(image, {
    x: mark.xPt,
    y: page.getHeight() - mark.yPt - mark.heightPt,
    width: mark.widthPt,
    height: mark.heightPt,
    opacity: stamp.opacity,
  });
}

async function exportSeam(doc) {
  const stamp = state.stamps.seam;
  if (!stamp.processedDataUrl) throw new Error('请先选择骑缝章图片。');
  const pagesResult = parsePages($('seamPages').value, doc.getPageCount());
  if (!pagesResult.ok) throw new Error(pagesResult.error);
  const pages = pagesResult.pages;
  if (pages.length < 2) throw new Error('骑缝章至少需要 2 页。');
  const slices = await splitImage(stamp.processedDataUrl, pages.length);
  const totalW = Number($('seamW').value || 120) * MM_TO_PT;
  const totalH = Number($('seamH').value || 40) * MM_TO_PT;
  const sliceW = totalW / pages.length;
  const edge = Number($('seamEdge').value || 0) * MM_TO_PT;
  const offset = Number($('seamOffset').value || 0) * MM_TO_PT;
  for (let i = 0; i < pages.length; i += 1) {
    const page = doc.getPage(pages[i]);
    const image = await doc.embedPng(slices[i]);
    const x = $('seamSide').value === 'left' ? edge : page.getWidth() - edge - sliceW;
    const yFromTop = Math.min(offset, Math.max(0, page.getHeight() - totalH));
    page.drawImage(image, {
      x,
      y: page.getHeight() - yFromTop - totalH,
      width: sliceW,
      height: totalH,
      opacity: stamp.opacity,
    });
  }
}

function parsePages(text, count) {
  const value = text.trim();
  if (!value || value === '全部') {
    return { ok: true, pages: Array.from({ length: count }, (_, i) => i) };
  }
  const pages = new Set();
  for (const part of value.split(',').map((x) => x.trim()).filter(Boolean)) {
    if (part.includes('-')) {
      const [startText, endText] = part.split('-').map((x) => x.trim());
      const start = Number(startText);
      const end = Number(endText);
      if (!Number.isInteger(start) || !Number.isInteger(end) || start <= 0 || end <= 0 || start > end) {
        return { ok: false, error: '页码范围格式不正确，请输入类似：全部、1,3,5 或 2-6。' };
      }
      for (let page = start; page <= end; page += 1) pages.add(page - 1);
    } else {
      const page = Number(part);
      if (!Number.isInteger(page) || page <= 0) {
        return { ok: false, error: '页码范围格式不正确，请输入类似：全部、1,3,5 或 2-6。' };
      }
      pages.add(page - 1);
    }
  }
  const filtered = [...pages].filter((page) => page >= 0 && page < count).sort((a, b) => a - b);
  if (!filtered.length) {
    return { ok: false, error: '页码范围没有可用页面。' };
  }
  return { ok: true, pages: filtered };
}

function splitImage(dataUrl, count) {
  return readImage(dataUrl).then((img) => {
    const out = [];
    for (let i = 0; i < count; i += 1) {
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(img.naturalWidth / count));
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, -i * canvas.width, 0);
      out.push(canvas.toDataURL('image/png'));
    }
    return out;
  });
}

function fitWidth() {
  if (!state.pdfDoc) return;
  const stage = $('pageStage');
  const available = Math.max(420, stage.clientWidth - 72);
  state.zoom = Math.min(3, Math.max(0.45, available / 595));
  renderPage();
  saveState();
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll('[data-mode]').forEach((button) => {
    button.classList.toggle('active', button.dataset.mode === mode);
  });
  saveState();
}

function goPage(index) {
  if (!state.pdfDoc || index < 0 || index >= state.pageCount) return;
  state.pageIndex = index;
  state.selectedMarkId = '';
  saveState();
  renderPage();
}

function setZoom(value) {
  state.zoom = Math.min(3, Math.max(0.45, value));
  saveState();
  renderPage();
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      outputName: $('outputName')?.value || state.outputName,
      zoom: state.zoom,
      mode: state.mode,
      stamps: {
        normal: state.stamps.normal,
        signature: state.stamps.signature,
        seam: state.stamps.seam,
      },
      controls: {
        normalW: $('normalW')?.value,
        normalH: $('normalH')?.value,
        signatureW: $('signatureW')?.value,
        signatureH: $('signatureH')?.value,
        seamW: $('seamW')?.value,
        seamH: $('seamH')?.value,
        seamEdge: $('seamEdge')?.value,
        seamOffset: $('seamOffset')?.value,
        seamSide: $('seamSide')?.value,
        seamPages: $('seamPages')?.value,
        seamEnabled: $('seamEnabled')?.checked,
        processTarget: $('processTarget')?.value,
        removeWhite: $('removeWhite')?.checked,
        whiteThreshold: $('whiteThreshold')?.value,
        opacity: $('opacity')?.value,
        mottled: $('mottled')?.value,
        soften: $('soften')?.value,
      },
    }));
  } catch {
    // localStorage may be full; ignore.
  }
}

function restoreState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    state.zoom = saved.zoom || state.zoom;
    state.mode = saved.mode || state.mode;
    state.outputName = saved.outputName || state.outputName;
    $('outputName').value = state.outputName;
    if (saved.controls) {
      Object.entries(saved.controls).forEach(([key, value]) => {
        const el = $(key);
        if (!el) return;
        if (el.type === 'checkbox') el.checked = Boolean(value);
        else if (value !== undefined) el.value = value;
      });
    }
    if (saved.stamps) {
      ['normal', 'signature', 'seam'].forEach((type) => {
        if (saved.stamps[type]) {
          Object.assign(state.stamps[type], saved.stamps[type]);
        }
      });
    }
    $('pageInput').value = 1;
    setMode(state.mode);
  } catch {
    // ignore malformed persisted state
  }
}

function downloadBytes(bytes, filename) {
  const blob = new Blob([bytes], { type: 'application/pdf' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function labelOf(type) {
  return { normal: '普通公章', signature: '法人签字章', seam: '骑缝章' }[type];
}

function log(message, level = 'info') {
  $('log').textContent = message;
  $('log').dataset.level = level;
}

function readAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function readImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

function cropCanvas(source, minX, minY, maxX, maxY) {
  if (maxX <= minX || maxY <= minY) return source;
  const canvas = document.createElement('canvas');
  canvas.width = maxX - minX + 1;
  canvas.height = maxY - minY + 1;
  canvas.getContext('2d').drawImage(source, minX, minY, canvas.width, canvas.height, 0, 0, canvas.width, canvas.height);
  return canvas;
}

function seededNoise(seed) {
  const x = Math.sin(seed * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

function icon(name) {
  const paths = {
    stamp: '<circle cx="12" cy="8" r="3"/><path d="M8 13h8l2 6H6l2-6Z"/><path d="M5 21h14"/>',
    file: '<path d="M14 2H6a2 2 0 0 0-2 2v16h16V8Z"/><path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="m9 15 3-3 3 3"/>',
    download: '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
    image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8" cy="9" r="2"/><path d="m21 15-5-5L5 20"/>',
    cursor: '<path d="M4 3 19 14l-7 1-3 6Z"/>',
    pen: '<path d="m16 3 5 5L8 21H3v-5Z"/><path d="m14 5 5 5"/>',
    trash: '<path d="M4 7h16"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M6 7l1 14h10l1-14"/><path d="M9 7V4h6v3"/>',
    reset: '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v6h6"/>',
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]}</svg>`;
}
