# SWTOR release kf writer samples

- `swtor-kf-writer-samples.jsonl`: 16 `dit.bot_event.v1` rows, one per shape, sent by the swtor-preservation lane on 2026-11-09. Copied byte for byte; sha256 `4755733618ce570cb7aa1a4b91496751c0d34ad78d8420bd57ff7d848150cfd0`.
- The rows were written by the live writer code (`private_bot_events.py`, release kf) in test runs. Actor ids and timestamps are synthetic. They prove the row shapes, not live play.
- Shapes: advice, callout, chat (voiced and dropped), death, decision (follow, hold, rotation_pick, plain), error, refused (chat, dialogue, focus, pull, rotation_pick), state_change.
- No row has a `text` or `chat_text` key.
- SWTOR logs a dropped non-AI line as a `refused` row with `details.intent` `chat`, not as a `chat` row. The importer counts it in the bot's chat drops.
