// Observe real key defaults without replacing them. Tests of this observer are
// separate from native-browser evidence; untrusted dispatched events are ignored.
function installAssignmentKeyboardCheck({document, prepare, page, requests, schedule = setTimeout}) {
  const start = document.getElementById('keyboard-start');
  const status = document.getElementById('keyboard-status');
  const steps = [
    ['Tab', false, 'keyboard-start', 'assignment-prev', 1, 1],
    ['Enter', false, 'assignment-prev', 'assignment-prev', 1, 1],
    [' ', false, 'assignment-prev', 'assignment-prev', 1, 1],
    ['Tab', false, 'assignment-prev', 'assignment-next', 1, 1],
    ['Enter', false, 'assignment-next', 'assignment-next', 1, 2],
    [' ', false, 'assignment-next', 'assignment-next', 2, 3],
    ['Enter', false, 'assignment-next', 'assignment-next', 3, 3],
    [' ', false, 'assignment-next', 'assignment-next', 3, 3],
    ['Tab', true, 'assignment-next', 'assignment-prev', 3, 3],
    ['Enter', false, 'assignment-prev', 'assignment-prev', 3, 2],
    [' ', false, 'assignment-prev', 'assignment-prev', 2, 1],
    ['Tab', true, 'assignment-prev', 'keyboard-start', 1, 1],
  ];
  let index = 0, generation = 0, baseline = 0, pending = null, running = false;
  const state = value => { document.documentElement.dataset.keyboardPlaytest = value; };
  const instruction = () => {
    const [key, shift] = steps[index];
    status.textContent = `Step ${index + 1}/${steps.length}: press ${shift ? 'Shift+' : ''}${key === ' ' ? 'Space' : key}. Use the keyboard; do not click a pager button.`;
  };
  const fail = reason => {
    running = false; pending = null; state('failed');
    status.textContent = 'FAIL — ' + reason + ' Start the keyboard check again to retry.';
  };
  state('not-run'); start.disabled = false;
  start.addEventListener('click', async () => {
    const current = ++generation;
    running = false; pending = null; index = 0; state('not-run'); start.disabled = true;
    status.textContent = 'Preparing synthetic assignment pages…';
    try {
      await prepare();
      if (current !== generation) return;
      baseline = requests();
      if (page() !== 1) throw new Error('Fixture did not start on page one');
      start.disabled = false; start.focus(); running = true; state('running'); instruction();
    } catch {
      if (current === generation) { start.disabled = false; fail('Could not prepare the offline fixture.'); }
    }
  });
  document.addEventListener('keydown', event => {
    if (!running || !event.isTrusted || event.repeat || ['Shift', 'Control', 'Alt', 'Meta'].includes(event.key)) return;
    if (event.key === 'Escape' && !event.ctrlKey && !event.altKey && !event.metaKey) {
      running = false; pending = null; state('cancelled'); start.focus();
      status.textContent = 'CANCELLED — keyboard check stopped. Focus returned to Start; assignment data is unchanged.';
      return;
    }
    const [key, shift, from, , before] = steps[index];
    if (pending || event.key !== key || !!event.shiftKey !== shift || event.ctrlKey || event.altKey || event.metaKey ||
        document.activeElement?.id !== from || page() !== before || requests() !== baseline) {
      fail('Unexpected key, focus, page or request before activation.'); return;
    }
    pending = {key, generation};
    // No preventDefault, focus change, click or page mutation here.
  }, true);
  document.addEventListener('keyup', event => {
    if (!running || !event.isTrusted || !pending || event.key !== pending.key) return;
    const captured = pending;
    schedule(() => {
      if (!running || captured.generation !== generation || pending !== captured) return;
      const [, , , target, , after] = steps[index];
      if (document.activeElement?.id !== target || page() !== after || requests() !== baseline) {
        fail('Native key activation or focus did not match the expected page; no extra requests are allowed.'); return;
      }
      pending = null;
      index++;
      if (index === steps.length) {
        running = false; state('passed');
        status.textContent = 'PASS — trusted keyboard input verified Tab/Shift+Tab order, Enter/Space paging and focus at both boundaries. Synthetic artifact only.';
      } else instruction();
    }, 0); // Observe after the browser's Space keyup activation.
  }, true);
}
