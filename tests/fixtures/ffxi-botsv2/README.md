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

# c2.10 formats (mounts; c2.10 will not be installed, ships as c2.10.1)

- Source: ffxi handoff `2026-11-09-botsv2-c2.10-frozen` (banshee_bots_v2_exec.lua:59/300/309, banshee_bots_v2.lua:780/803/814).
- **Bot lines:** `mount <bot> why=<w>`, `dismount <bot> why=<w>`, `mount_blocked <bot> why=no_key_item ki=<n> (V2 grants none)`.
- **System line:** `mount_gate off: entity:botMount is not bound (gated off)`.
- These are covered by synthetic tests only. c2.10.1 (frozen 72dbbf89) keeps every c2.10 log template: confirmed by ffxi and by a diff of the log calls in both frozen trees.

# J0a / J0b formats (staged, not live)

- Source: ffxi handoff `2026-11-09-botsv2-j0b-frozen` (1563/0), checked by diffing its log calls against c2.10.1. These formats are covered by synthetic tests only.
- **Sub-job moves** use the existing act line with `apl=sub_<name>`.
- **Profile line:** `profile <bot> to=<id> from=<id> why=default|order|advice`.
- **Advice lines:**
  - `advice <bot> req kind= id= options= default=`;
  - `advice <bot> answer kind= choice= applied=yes|no why=`;
  - `advice <bot>|- drop why=unknown_id|bad_choice|expired|cap`. When the key is `-`, the line is a bot-less system notice.
- **System lines:** `subjob off: … (gated off)` and `advice off: … (gated off)`.

# Bots V2 live log export 4 (regular LSB, canary 2.9.1), 2026-11-09

- `bots-v2-c291-20261109.log`: copied byte-for-byte from ffxi's handoff `2026-11-09-botsv2-log-export-4` (sha256 `4c4a1093dedce6055e3f4e44f6cd8122cea5903cfac23b16f14e6319094b044b`, 591 lines).
- **Coverage:** the live c2.9.1 run, 11-09 10:29Z-11:29Z. No human was online, and the export has no order or levelsync lines.
- **Content:**
  - MP rests: 165→173, 208→213, 246→307, 330→352;
  - two deaths with release and revive: 401/405/408 and 426/438/440;
  - 0 unstick lines.
- Every line is recognized. The preview builder now uses this export.

# Bots V2 live log export 5 (regular LSB, canary 2.10.1), 2026-11-09

- `bots-v2-c2101-20261109.log`: copied byte-for-byte from ffxi's handoff `2026-11-09-botsv2-log-export-5` (sha256 `ce90dc67feb82b5a46cbe6abf3608b3cd88c113ccb31f5d61e7f3dc20105234b`, 575 lines).
- **Coverage:** the live c2.10.1 run, 11-09 11:32:09Z-12:32:55Z. No human was online.
- **Content:** the first live mount lines confirm the c2.10 formats.
  - 14 `mount <bot> why=travel` lines (first at 17/19/21).
  - dismounts why=cast, camp, group and native.
  - 0 deaths.
- The preview builder now uses this export.

# Bots V2 live log export 6 (regular LSB, J0b), 2026-11-09

- `bots-v2-j0b-20261109.log`: copied byte-for-byte from ffxi's handoff `2026-11-09-botsv2-log-export-6` (sha256 `027b96d5a05459815e301cba85fb82d1f32d7cedfed2b883c9323874973b7c01`, 508 lines).
- **Coverage:** the live J0b run, 11-09 12:34:51Z-13:35:12Z. No human was online.
- **Content:**
  - the first live sub-job moves: `apl=sub_nuke` at 152/156/162;
  - one death with release and revive: 163/173/176;
  - 0 profile and 0 advice lines, because the advice flag is off.
- J1-J4 (live 13:35:54Z) adds no new log templates; a diff of the log calls in the j0b and j4 frozen trees confirms it.
- The preview builder now uses this export.

# P2b formats (live 17:16:51Z with C3.1)

- Source: ffxi handoff `2026-11-09-botsv2-p2b-frozen` (2582/0). A diff of the log calls against j4-frozen shows exactly two changes.
- **Order line:** gains an optional ` refused=<why>` suffix. A space in the arg is logged as `_`.
  - The event result is `refused`, and the line still counts as party.
  - The mob name in an `attack` arg is not a person.
- **New line:** `advice <bot> release kind=party_tactic choice=<id> why=ttl|replaced` (an event).
- **Value changes only:** profile why `order` / `order_ended`; advice kind `party_tactic`; answer why `party_changed`.
- These are covered by synthetic tests only.

# Export 7: `bots-v2-j1234-20261109.log` (live J1-J4 run)

- Source: ffxi handoff `2026-11-09-botsv2-log-export-7`. Copied byte for byte; sha256 `fb7b289b4e59bdbe5ab562bdcf4e770d39c8006debf5e0d74a53e5b1f9ec4cd6`, 1818 lines.
- Coverage: 11-09 13:37:10Z-17:10:17Z. The owner was online from 14:33Z to about 16:10Z but elsewhere (Western Adoulin); no human names appear in bot lines.
- All 1818 lines are recognized (0 omitted, 0 unrecognized, 0 ignored).
- Evidence: tomoe dies, releases and revives 3 times (lines 586/590/591, 1090/1094/1095, 1571/1577/1578); 5 group trip starts.
- **Live bug (ffxi fix C5):** shadowtail and fumika end each trip on arrival with `why=bag_full` (3 times each), so they never fight. No J1 THF/WHM kit line and no `apl=sub_*` line is in this run.
- The preview builder now uses this export.

# C3.1 formats (live 17:16:51Z)

- Source: ffxi handoff `2026-11-09-botsv2-c3.1-frozen`. A diff of the log calls against p2b-frozen is empty: no new template.
- New values only: act rules `retreat` and `mate_assist`; defend why `retreat_to_healer`, `retreat_to_mate`, `retreat_to_camp`, `cornered`; no trip why `danger`.
- Covered by a synthetic test only; not yet seen live.

# C4.3 and V2-Q1.1 formats (frozen, not live)

- Sources: ffxi handoffs `2026-11-09-botsv2-c4.3-frozen` and `2026-11-09-botsv2-q1.1-frozen`. A log-call diff against c3.1-frozen shows six new templates:
  - `group party <leader> members=<leader>+<a>[+<b>...]`: goes to every member.
  - `group party <leader> drop <bot> why=<why>`: goes to the dropped bot, with the leader in the detail.
  - `group party <leader> off why=<why>`
  - `slow eval <bot> rule=<r> tier=<t> wallMs=<%.2f> cpuMs=<%.2f|n/a> atomic=yes|no heapKB=<a>-><b>`: a diagnostic, at most one line per 10 s.
  - `progression <bot> level=<n> why=levelup|spawn|periodic -> ok | -> refused <why>`
  - `roe <bot> record=<n> -> ok|refused`
- All six count as other.
- V2-Q1.1 ships dark: no progression or roe line appears unless `BANSHEE_BOTS_V2_PROGRESSION=1`.
- These formats are covered by synthetic tests only.
