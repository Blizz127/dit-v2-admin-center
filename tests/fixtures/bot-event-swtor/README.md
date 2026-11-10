# SWTOR release kf writer samples

- `swtor-kf-writer-samples.jsonl`: 16 `dit.bot_event.v1` rows, one per shape, sent by the swtor-preservation lane on 2026-11-09. Copied byte for byte; sha256 `4755733618ce570cb7aa1a4b91496751c0d34ad78d8420bd57ff7d848150cfd0`.
- The rows were written by the live writer code (`private_bot_events.py`, release kf) in test runs. Actor ids and timestamps are synthetic. They prove the row shapes, not live play.
- Shapes: advice, callout, chat (voiced and dropped), death, decision (follow, hold, rotation_pick, plain), error, refused (chat, dialogue, focus, pull, rotation_pick), state_change.
- No row has a `text` or `chat_text` key.
- SWTOR logs a dropped non-AI line as a `refused` row with `details.intent` `chat`, not as a `chat` row. The importer counts it in the bot's chat drops.

The standalone preview also offers **Synthetic SWTOR import with a malformed
row**. Its builder reads this unchanged sample, appends one deliberately
unfinished JSON row to a disposable copy, and passes that directory through the
normal reader. The copy is removed after projection. It retains the 16 valid
rows and seven actors while reporting one `invalid_json` reader omission. The
separate producer `LOG_DROPPED` report still says 27; the two counts are never
added. This is a synthetic import/recovery case, not a real partial export or a
measurement of live loss. The original sample and its hash remain unchanged.
