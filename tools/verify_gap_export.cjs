// Only invoked in the runner's disposable, network-isolated Chromium session.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const MAX_REPORT_BYTES = 256 * 1024;
function readSavedReport(filename) {
  // Check the opened object, not an earlier pathname stat. Nonblocking open
  // refuses special files without waiting for a writer; never follow a leaf link.
  const fd = fs.openSync(filename, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
  try {
    const info = fs.fstatSync(fd);
    assert.ok(info.isFile() && info.size > 0 && info.size <= MAX_REPORT_BYTES, 'Invalid saved report');
    const buffer = Buffer.alloc(MAX_REPORT_BYTES + 1);
    let size = 0, read;
    while (size < buffer.length && (read = fs.readSync(fd, buffer, size, buffer.length - size, null))) size += read;
    assert.ok(size > 0 && size <= MAX_REPORT_BYTES, 'Saved report exceeds byte limit');
    return buffer.subarray(0, size);
  } finally { fs.closeSync(fd); }
}
function verifySavedReport(directory, expected) {
  const name = 'roster-gap-row-2.json';
  assert.deepEqual(fs.readdirSync(directory), [name]);
  assert.equal(typeof expected, 'string');
  assert.ok(Buffer.byteLength(expected, 'utf8') <= MAX_REPORT_BYTES, 'Copy field exceeds byte limit');
  const bytes = readSavedReport(path.join(directory, name));
  assert.ok(bytes.equals(Buffer.from(expected, 'utf8')), 'Saved report differs from copy-field bytes');
  const report = JSON.parse(bytes.toString('utf8'));
  assert.equal(report.schema, 'dit-admin-roster-gap-report-v1');
  assert.equal(report.selectedSnapshotRow, 2);
  assert.equal(report.reason, 'repeated_loaded_id');
  assert.deepEqual(report.candidates.map(row => row.snapshotRow), [2, 3]);
  assert.deepEqual(report.differingFields, ['name', 'game']);
  assert.deepEqual(report, JSON.parse(expected));
  return {status: 'passed', savedBytes: bytes.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
    candidates: 2, selectedSnapshotRow: 2,
    limitations: 'Synthetic local report only; saved in a disposable directory, not authenticated provenance'};
}
async function waitForSavedReport(directory, expected, timeoutMs = 3000) {
  assert.ok(Number.isFinite(timeoutMs) && timeoutMs > 0 && timeoutMs <= 3000);
  const deadline = performance.now() + timeoutMs;
  do {
    try { return verifySavedReport(directory, expected); }
    catch { /* A file appearing does not establish completed, matching bytes. */ }
    const remaining = deadline - performance.now();
    if (remaining <= 0) break;
    await new Promise(resolve => setTimeout(resolve, Math.min(20, remaining)));
  } while (performance.now() < deadline);
  throw Error('Native gap download did not produce a complete matching report within the deadline');
}
async function verifyGapExport({send, evaluate, waitFor, press}, directory) {
  await send('Browser.setDownloadBehavior', {behavior: 'allow', downloadPath: directory});
  await evaluate(`(() => {
    const gaps = document.getElementById('roster-gaps'); gaps.closest('details').open = true;
    gaps.querySelector('button').focus(); return true;
  })()`);
  await press('Enter');
  await waitFor("!!document.querySelector('#roster-gap-detail textarea')");
  const layout = await evaluate(`(() => {
    const region = document.querySelector('#roster-gap-detail [role="region"]');
    const table = region.querySelector('table');
    return {rows: table.querySelectorAll('tbody tr').length, columns: table.querySelectorAll('thead th').length,
      width: region.clientWidth, scrollWidth: region.scrollWidth,
      differences: [...table.querySelectorAll('tbody th')].filter(n => n.textContent.includes('(differs)')).map(n => n.textContent),
      copy: document.querySelector('#roster-gap-detail textarea').value,
      href: document.querySelector('#roster-gap-detail a[download]').getAttribute('href')};
  })()`);
  assert.equal(layout.rows, 9); assert.equal(layout.columns, 3);
  assert.match(layout.href, /^blob:/, 'Native download must exercise the Blob URL');
  assert.ok(Number.isFinite(layout.width) && layout.width > 0 && layout.scrollWidth >= layout.width);
  assert.deepEqual(layout.differences, ['name (differs)', 'game (differs)']);
  await evaluate("document.querySelector('#roster-gap-detail a[download]').focus(); true");
  await press('Enter');
  return {...await waitForSavedReport(directory, layout.copy), nativeActivation: 'Enter', table: {rows: layout.rows, columns: layout.columns, width: layout.width}};
}
module.exports = {verifySavedReport, waitForSavedReport, verifyGapExport};
