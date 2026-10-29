// Native Chromium layout/screenshot commands, called only inside the isolated runner.
const fs = require('node:fs');
const path = require('node:path');
const views = [
  {name: 'desktop', width: 1280, height: 1000, right: false},
  {name: 'narrow-left', width: 390, height: 844, right: false},
  {name: 'narrow-right', width: 390, height: 844, right: true},
];
function validateLayout(layout, view) {
  if (!layout || !layout.open || layout.rows !== 4 || layout.columns !== 5 || layout.modelUnknowns !== 4)
    throw Error('Comparison content missing');
  for (const field of ['panelLeft', 'panelRight', 'tableTop', 'tableBottom', 'regionLeft', 'regionRight', 'clientWidth', 'scrollWidth', 'scrollLeft']) {
    if (!Number.isFinite(layout[field])) throw Error('Invalid layout measurement');
  }
  if (layout.panelLeft < -1 || layout.panelRight > view.width + 1 || layout.regionLeft < -1
      || layout.regionRight > view.width + 1 || layout.clientWidth <= 0 || layout.scrollWidth < layout.clientWidth
      || layout.tableTop < -1 || layout.tableBottom > view.height + 1 || layout.tableBottom <= layout.tableTop)
    throw Error('Comparison escapes viewport');
  if (view.right && layout.scrollLeft < layout.scrollWidth - layout.clientWidth - 1)
    throw Error('Rightmost evidence columns cannot be reached');
}
async function captureComparisons(command, directory) {
  const captures = [];
  for (const view of views) {
    await command('Emulation.setDeviceMetricsOverride', {width: view.width, height: view.height, deviceScaleFactor: 1, mobile: false});
    const response = await command('Runtime.evaluate', {awaitPromise: true, returnByValue: true,
      expression: `(async () => {
        const panel = document.getElementById('party-review-examples'); panel.open = true;
        panel.scrollIntoView({block: 'start'});
        const region = panel.querySelector('[role="region"]');
        region.scrollLeft = ${view.right ? 'region.scrollWidth' : '0'};
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        const p = panel.getBoundingClientRect(), r = region.getBoundingClientRect(), t = panel.querySelector('table').getBoundingClientRect();
        return {open: panel.open, rows: panel.querySelectorAll('tbody tr').length,
          columns: panel.querySelectorAll('thead th').length,
          modelUnknowns: [...panel.querySelectorAll('tbody tr')].filter(row => row.lastElementChild.textContent === 'Unknown').length,
          panelLeft: p.left, panelRight: p.right, tableTop: t.top, tableBottom: t.bottom, regionLeft: r.left, regionRight: r.right,
          clientWidth: region.clientWidth, scrollWidth: region.scrollWidth, scrollLeft: region.scrollLeft};
      })()`});
    if (response.exceptionDetails) throw Error('Comparison render failed');
    validateLayout(response.result.value, view);
    const screenshot = await command('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false, fromSurface: true});
    const bytes = Buffer.from(screenshot.data || '', 'base64');
    if (bytes.length < 24 || bytes.length > 16 * 1024 * 1024 || !bytes.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex'))
        || bytes.readUInt32BE(16) !== view.width || bytes.readUInt32BE(20) !== view.height)
      throw Error('Screenshot is missing or has unexpected dimensions');
    const filename = view.name + '.png';
    fs.writeFileSync(path.join(directory, filename), bytes, {flag: 'wx', mode: 0o600});
    captures.push({file: filename, width: view.width, height: view.height, layout: response.result.value});
  }
  return {status: 'captured', captures, limitations: 'Synthetic comparison panel only; geometry is checked, human visual review is separate'};
}
module.exports = {views, validateLayout, captureComparisons};
