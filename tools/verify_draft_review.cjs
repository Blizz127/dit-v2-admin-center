// Run only inside the disposable, isolated synthetic-artifact browser session.
const assert = require('node:assert/strict');
async function verifyDraftReview({command,evaluate,press,waitFor}) {
  await evaluate("document.getElementById('bot-draft-section').open = true; document.getElementById('bot-draft-cancel').focus(); true");
  await press('Enter');
  assert.equal(await evaluate("document.getElementById('bot-draft-fields').disabled"), false);
  await evaluate("document.getElementById('bot-draft-goals').focus(); true");
  await command('Input.insertText', {text:'Fixture goal'});
  await press('Tab');
  await waitFor("document.activeElement.id === 'bot-draft-personality'");
  await command('Input.insertText', {text:'Synthetic patient draft'});
  await press('Tab');
  await waitFor("document.activeElement.id === 'bot-draft-preview'");
  await press('Enter');
  await waitFor("document.getElementById('bot-draft-status').textContent.includes('Preview ready')");
  const review = await evaluate("document.getElementById('bot-draft-result').textContent");
  assert.match(review, /Local draft · offline-inspector-bot · FFXI/);
  assert.match(review, /Matches loaded text/);
  assert.match(review, /Proposed personality[\s\S]*Comparison unavailable: current value Unknown/);
  assert.match(review, /Synthetic patient draft/);
  await waitFor("document.activeElement.id === 'bot-draft-preview'");
  await press('Tab');
  await waitFor("document.activeElement.id === 'bot-draft-cancel'");
  await press('Enter');
  await waitFor("document.getElementById('bot-draft-result').textContent === '' && document.getElementById('bot-draft-goals').value === '' && document.getElementById('bot-draft-personality').value === '' && document.activeElement.id === 'bot-draft-cancel'");
  for (const id of ['bot-draft-preview','bot-draft-personality','bot-draft-goals']) {
    await press('Tab', true);
    await waitFor(`document.activeElement.id === '${id}'`);
  }
  return {status:'passed', targetId:'offline-inspector-bot', traversal:'Tab/Shift+Tab', activation:'Enter',
    textInput:'Input.insertText', unknownBaseline:'personality', matchesLoadedGoal:true,
    discardCleared:true, focusRetained:true,
    limitations:'Synthetic local draft only; no save, live bot action, visual or screen-reader certification'};
}
module.exports = {verifyDraftReview};
