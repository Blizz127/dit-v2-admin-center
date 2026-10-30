// Local standalone-check observation only; never a bot/service health signal.
function installPreviewProgress({document, now = () => performance.now(),
  schedule = callback => globalThis.setInterval(callback, 250), cancel = id => globalThis.clearInterval(id)}) {
  const start = now();
  let lastProgress = start, checks = 0, lastCheck = '', state = 'running', timer, endedAt;
  const labels = {running:'Running', passed:'Completed', failed:'Check failed',
    'progress-timeout':'Stalled: no assertion progress for 5 seconds',
    'total-timeout':'10-second total check limit reached'};
  function snapshot() { return {state, checks, lastCheck, elapsedMs:Math.max(0, Math.round((endedAt ?? now()) - start))}; }
  function render() {
    const data = snapshot();
    for (const id of ['preview-progress-overview', 'preview-progress-assignment']) {
      const panel = document.getElementById(id);
      panel.dataset.state = state;
      panel.dataset.checks = String(checks);
      panel.textContent = `${labels[state]} · ${checks} completed checks · ${data.elapsedMs} ms elapsed. Last check: ${lastCheck || 'None yet'}. Local synthetic checks only; native keyboard, rendering and saving remain unverified.`;
      const label = document.getElementById(id.replace('preview-progress-', 'preview-progress-label-'));
      if (label) label.textContent = `Local preview checks: ${labels[state]}`;
    }
  }
  function stop(next) { state = next; endedAt = now(); if (timer !== undefined) cancel(timer); render(); }
  function sample() {
    if (state === 'running') {
      if (now() - start >= 10000) stop('total-timeout');
      else if (now() - lastProgress >= 5000) stop('progress-timeout');
      else render();
    }
    return snapshot();
  }
  timer = schedule(sample); render();
  return {
    record(name) {
      sample();
      if (state !== 'running') return;
      checks++; lastCheck = String(name).slice(0, 240); lastProgress = now();
    },
    finish() { sample(); if (state === 'running') stop('passed'); return state === 'passed'; },
    fail() { if (state === 'running') stop('failed'); },
    sample, snapshot,
  };
}
if (typeof module !== 'undefined') module.exports = {installPreviewProgress};
