# Bots V2 live log export (regular LSB), 2026-11-09

- `bots-v2-20261109.log`: [BOTS-V2] lines exactly as they appear in the live map log (LSB prefix and timestamp kept). It was exported read-only on 11-09 at about 04:24Z.
- **Edits:** only bot lines are kept, and the "tick host live in zone N" boot spam is dropped. The one human character name in bot lines (owner/inviter) is replaced with `<owner>`.
- **Coverage:**
  - 11-09 03:17:39Z-04:23:57Z: c2.7, the full container log since the last restart.
  - A few minutes after each of the c2.5 (01:12Z) and c2.6 (02:15Z) boots, from the watcher boot captures.
  - Earlier 11-09 lines are gone. The map container is recreated at each canary install, which resets docker logs.
- **Content:** act ok and refused (path refusals with dist and tails, "(repeated N times …)"), defend, trip start group, trip end, no trip, stuck, owner/party and budget lines.
- **Not yet in it:** dead / release / return / weak. Those arrive with c2.8; a later export will add them. The parser matches the exact c2.8 format strings from `~/dev/ffxi/handoffs/2026-11-08-botsv2-c2.8-frozen`. Treat those formats as provisional until a live c2.8 export confirms them, before any death or recovery count goes on the scoreboard.
