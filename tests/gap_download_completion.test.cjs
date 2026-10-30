// Local synthetic files only. Timers and fake download progression are not Chromium evidence.
const assert = require('node:assert/strict');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const {spawnSync} = require('node:child_process');
const {verifySavedReport, waitForSavedReport} = require('../tools/verify_gap_export.cjs');
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'dit-download-completion-'));
const filename = path.join(directory, 'roster-gap-row-2.json');
const expected = JSON.stringify({schema:'dit-admin-roster-gap-report-v1', selectedSnapshotRow:2,
  reason:'repeated_loaded_id', candidates:[{snapshotRow:2},{snapshotRow:3}], differingFields:['name','game']});
(async () => {
  try {
    fs.writeFileSync(filename, expected.slice(0, 20));
    const partial = path.join(directory, 'pending.crdownload');
    fs.writeFileSync(partial, 'in progress');
    const completed = setTimeout(() => {
      fs.writeFileSync(filename, expected);
      fs.unlinkSync(partial);
    }, 35);
    try {
      const receipt = await waitForSavedReport(directory, expected, 1000);
      assert.equal(receipt.savedBytes, Buffer.byteLength(expected));
      assert.equal(receipt.nativeActivation, undefined);
    } finally { clearTimeout(completed); }

    for (const contents of ['', '{', expected + '\n']) {
      fs.writeFileSync(filename, contents);
      const start = performance.now();
      await assert.rejects(waitForSavedReport(directory, expected, 55), /within the deadline/);
      assert.ok(performance.now() - start < 1000, 'Incomplete download must finish with a bounded refusal');
    }
    fs.unlinkSync(filename);
    assert.equal(spawnSync('mkfifo', [filename], {timeout:1000}).status, 0);
    const fifoStart = performance.now();
    assert.throws(() => verifySavedReport(directory, expected), /Invalid saved report/);
    assert.ok(performance.now() - fifoStart < 1000, 'FIFO with no writer must not block');
    fs.unlinkSync(filename);
    fs.symlinkSync('/dev/zero', filename);
    assert.throws(() => verifySavedReport(directory, expected));
    fs.unlinkSync(filename);

    // A regular file can grow after fstat. The acquisition must still cap bytes,
    // and close its descriptor when refusing the oversized result.
    fs.writeFileSync(filename, expected);
    const originalStat = fs.fstatSync, originalRead = fs.readSync, originalClose = fs.closeSync;
    let acquired = 0, reportFd;
    const closed = new Set();
    fs.fstatSync = fd => {
      reportFd = fd;
      const info = originalStat(fd);
      fs.appendFileSync(filename, Buffer.alloc(256 * 1024));
      return info;
    };
    fs.readSync = (...args) => { const n = originalRead(...args); acquired += n; return n; };
    fs.closeSync = fd => { closed.add(fd); return originalClose(fd); };
    try {
      assert.throws(() => verifySavedReport(directory, expected), /byte limit/);
      assert.equal(acquired, 256 * 1024 + 1);
      assert.ok(closed.has(reportFd));
    } finally { fs.fstatSync = originalStat; fs.readSync = originalRead; fs.closeSync = originalClose; }
    for (const bad of [0, -1, Infinity, NaN, 3001]) {
      await assert.rejects(waitForSavedReport(directory, expected, bad));
    }
    console.log('PASS: partial completion, bounded incomplete-file refusal, FIFO/symlink refusal and growth cap. Native NOT RUN.');
  } finally { fs.rmSync(directory, {recursive:true, force:true}); }
})().catch(error => { console.error(error); process.exitCode=1; });
