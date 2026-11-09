# Bots V2 live log export (regular LSB), 2026-11-09

- `bots-v2-20261109.log`: [BOTS-V2] lines exactly as they appear in the live map log (LSB prefix and timestamp kept). It was exported read-only on 11-09 at about 04:24Z.
- **Edits:** only bot lines are kept, and the "tick host live in zone N" boot spam is dropped. The one human character name in bot lines (owner/inviter) is replaced with `<owner>`.
- **Coverage:**
  - 11-09 03:17:39Z-04:23:57Z: c2.7, the full container log since the last restart.
  - A few minutes after each of the c2.5 (01:12Z) and c2.6 (02:15Z) boots, from the watcher boot captures.
  - Earlier 11-09 lines are gone. The map container is recreated at each canary install, which resets docker logs.
- **Content:** act ok and refused (path refusals with dist and tails, "(repeated N times …)"), defend, trip start group, trip end, no trip, stuck, owner/party and budget lines.
- **Not yet in it:** dead / release / return / weak. Those arrive with c2.8; a later export will add them. The parser matches the exact c2.8 format strings from `~/dev/ffxi/handoffs/2026-11-08-botsv2-c2.8-frozen`. Treat those formats as provisional until a live c2.8 export confirms them, before any death or recovery count goes on the scoreboard.

# Bots V2 live log export 2 (regular LSB, canary 2.8), 2026-11-09

- `bots-v2-c28-20261109.log`: copied byte-for-byte from ffxi's handoff `2026-11-09-botsv2-log-export-2` (sha256 `be2eea13e43c196a06bef51cc580b9a4ff2bbde6ede624eb7cb608b03a1740fc`, 377 lines). It is every [BOTS-V2] line of the live c2.8 run, 11-09 07:15Z-08:13:41Z. No human was online, so nothing is masked. Two non-bot lines from the export (container wake notes) are ignored.
- **Confirmed live:** the c2.8 `rest` / `rest end` formats (V.restLog in banshee_bots_v2.lua). The importer recognizes every bot line in this export.
- **Death formats:** dead / release / revived were confirmed against live lines that ffxi reported on 11-09 10:08-10:09Z (test_live_death_lines_reported_by_ffxi_parse). return / weak are still unconfirmed.
- The private preview builder now uses this export for the FFXI activity section.

# c2.9 formats (not live yet)

- From ffxi's frozen c2.9 code (handoff `2026-11-09-botsv2-c2.9-frozen`, banshee_bots_v2.lua:781/788/816/821/1426 and exec E.revertSync). Covered by synthetic tests only, until a live export exists.
- **Order line:** `order <bot> verb=<v>[ arg=<a>] by=<speaker> channel=<c>`.
  - `by=` must be `<owner>`, or the line is omitted.
  - A focusheal `arg` other than `<owner>` or `off` is shown as `<member>`, because it can be a human name.
- **Level sync lines:** `levelsync <bot> to=N from=N`, `levelsync <bot> off why=<w>`, `levelsync <bot> off why=external cur=N`. These are events.
- **System line:** `levelsync off: entity:levelRestriction is not bound (gated off)`. It carries no bot name.

# Bots V2 live log export 3 (regular LSB, canary 2.8.1), 2026-11-09

- `bots-v2-c281-20261109.log`: copied byte-for-byte from ffxi's handoff `2026-11-09-botsv2-log-export-3` (sha256 `a53acf46d5076eaaf1b83690237e4081825f2169ae6baeedf4e661139a0185cc`, 436 lines).
- **Coverage:** the live c2.8.1 run, 11-09 09:26:44Z-10:27:21Z. No human was online.
- **Content:** it has the first live deaths: dead (lines 350, 364), release (366, 371) and revived at the home point (368, 372). Every line is recognized.
- The private preview builder now uses this export.

# c2.10 formats (mounts; frozen, not live)

- Source: ffxi handoff `2026-11-09-botsv2-c2.10-frozen` (banshee_bots_v2_exec.lua:59/300/309, banshee_bots_v2.lua:780/803/814).
- **Bot lines:** `mount <bot> why=<w>`, `dismount <bot> why=<w>`, `mount_blocked <bot> why=no_key_item ki=<n> (V2 grants none)`.
- **System line:** `mount_gate off: entity:botMount is not bound (gated off)`.
- These are covered by synthetic tests only.
