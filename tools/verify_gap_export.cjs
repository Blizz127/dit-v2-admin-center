// Only invoked in the runner's disposable, network-isolated Chromium session.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
function verifySavedReport(directory, expected) {
  const name = 'roster-gap-row-2.json';
  assert.deepEqual(fs.readdirSync(directory), [name]);
  const filename = path.join(directory, name), info = fs.lstatSync(filename);
  assert.ok(info.isFile() && !info.isSymbolicLink() && info.size > 0 && info.size <= 256 * 1024);
  const bytes = fs.readFileSync(filename);
  assert.equal(typeof expected, 'string');
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
  const filename = path.join(directory, 'roster-gap-row-2.json'), deadline = Date.now() + 3000;
  while (!fs.existsSync(filename)) {
    if (Date.now() > deadline) throw Error('Native gap download did not complete');
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  return {...verifySavedReport(directory, layout.copy), nativeActivation: 'Enter', table: {rows: layout.rows, columns: layout.columns, width: layout.width}};
}
module.exports = {verifySavedReport, verifyGapExport};
