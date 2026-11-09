# cmangos-classic playerbot event log (WoW Vanilla / Benilla)

- `vanilla-bot_events-20261109T1927Z.derived.csv`: the live server run of 2026-11-09 19:27:40Z to 20:52:04Z (release-20261109i), 10,337 rows, 580 bots. Every actor is a random bot.
- Source: `/home/blizz/scratch/cmangos/bot-events-export/vanilla-bot_events-20261109T1927Z.csv`, sha256 `918933543974cbae83f9f1216397def77f8d250089debe3ca29020cd15451d6b`, sent by the cmangos-classic lane.
- **Derived, not byte-exact:** field 8 (info1) is blanked on the 246 `AcceptInvitationAction`, `LeaveGroupAction` and `GuildAcceptAction` rows, because it holds a character or guild name there. Every other byte is unchanged. Derived sha256 `ad510a009cd3a44af973eaa32654552058430fe085eab90498d83ef0cbc20210`.
- Format: CSV, no header, 9 fields: timestamp (`YYYY-MM-DD HH:MM:SS+00`, whole seconds), bot name, playerbot action class, `"POINT(a b)"`, race id, class id, level as a float, info1, info2.
- The log holds milestone actions only (pull, xp gain, loot, equip, sell, quest, hearth, revive, auction), not every spell cast.
- What it shows: 10 bots re-pull one mob 10 or more times with no kill (1,842 of 5,028 pulls). The worst, Tohsha, pulls Makrura Shellhide 562 times from one position over 58 minutes. There are 305 hearthstone escapes from being stuck and 183 deaths.
