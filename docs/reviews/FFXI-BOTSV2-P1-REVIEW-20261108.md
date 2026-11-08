# Review of ffxi P1 design: FFXI (LSB) Bots V2, 2026-11-08

Target: `~/dev/ffxi/handoffs/2026-11-08-botsv2-p1/DESIGN.md`. Read-only multi-lens review from the Admin Center lane.

- 49 candidate findings came from five lenses: PlayerbotV2 fidelity, DIT conditions and chat, rollout safety, LSB technical, owner decisions.
- Each was checked by three skeptics. 47 were confirmed by at least two of them and 2 were refuted. Duplicates are merged below.

# FFXI P1 design review (confirmed findings only)

Lua paths are under `live-snapshot/modules/custom/lua/` with the `banshee_dit_` prefix dropped. DESIGN.md is cited by line.

## Blocker

**1. Old chat stays live through canary and after the flip.** `BANSHEE_DIT_ALIVE_SPEECH=0` appears only at final flip (DESIGN.md:163, 194). Milestones and perception bypass that split (alive_chatter.lua:992-1030, 1505-1523). This breaks the owner's chat-off decision (DESIGN.md:6). Fix: make chat-off a canary precondition and gate every old speech producer per actor on `xi.botsV2.owns`.

**2. Social queue is a second live chat transport.** DESIGN.md:160 says alive_chatter is "the ONLY transport," but social_queue.lua:107-113 prints rows while QUEUE_DRAIN and BANSHEENET are 1 (container-env-xi.txt:204, 215). The §4 flip omits both flags. Fix: add both to the flip, and prove or remove the template text in ffxi_social_observations.cpp:868-880.

## Major

**3. Zone tick host installed at module load is inert or drops Zone.lua.** DESIGN.md:37 installs "once at module load," but `xi.zones.<Zone>.Zone` exists only after OnZoneInitialize (luautils.cpp:2554). Creating it early makes update_if_empty skip Zone.lua (luautils.cpp:996). Fix: use `addOverride` on `xi.zones.<Zone>.Zone.onZoneTick` (applied at luautils.cpp:1005). Name starterPopulationTick (bot_session_manager.cpp:1223) as the live 1 s driver.

**4. Order authority is misstated, and there are two order parsers.** DESIGN.md:120 gives "party leader, else lowest-id." The live gate requires GM or PARTY_CONTROLLERS (alive_chatter.lua:2036-2050), and onPartyWords acks orders outside any skip (2069, 2075). Fix: restate authority and make V2 the sole parser for owned bodies, with a test that an unrelated leader is rejected.

**5. Owner verb set is too narrow.** owner_order (DESIGN.md:95) omits live wait, stop and resume (alive_chatter.lua:1992), and party_roles pause, camp, puller, tank and healer (banshee_dit_party_roles.lua:70-80). It also omits pull, dismiss and distance (BOT_COMMANDS.md:60-147). Fix: map or explicitly retire each verb, and add an owner-bound roster.

**6. Roles are job-derived and undeclared.** DESIGN.md:114 (PLD/WAR/NIN/RUN) disagrees with party_roles and settings/main.lua:827. Owner tank and healer overrides vanish at cutover. Fix: one declared role table with an owner override, used for threat, heal, formation and speaker choice.

**7. Zone-line following waits silently.** DESIGN.md:122 says a bot "waits at the line and says nothing." A8 (line 232) defers the fix, and §5 has no zone-crossing test, although contract item (2) requires zone transitions. PlayerbotV2 brings the bot after about 15 s (PlayerbotV2.cpp:1361-1419). Fix: make cross-zone follow a P2 requirement with bounded catch-up and a live zone-crossing acceptance test.

**8. Callouts and event kinds are unscheduled and misstated.** DESIGN.md:159 gates pull, low_hp, wipe and revive behind an unscheduled bridge increment, though pull and aggro already flow (alive_chatter.lua:727-745). DESIGN.md:155-156 lists follow, kill and death as outbox kinds, but they are fight-ring entries (1629-1644). Fix: generate the golden kind set from live producers, and schedule bridge work for wipe and revive.

**9. Outbox and speech gates are unbudgeted, and the Zz skip is unlocated.** A.outbox (alive_chatter.lua:1192-1206) checks only bridgeOn, so hub events and milestones bypass the 8/min cap (167-173). The Zz/test:true skip cited at DESIGN.md:160 exists in no live file. Fix: one writer wrapper for all producers with a listener gate, skip and shared budget, plus a P2 test with Zz fixtures.

**10. Inbox replies need offers the design omits.** Say and shout replies are voiced only with a localOffer (alive_chatter.lua:2322-2341). The crowd registers one (adoulin_crowd.lua:487); V2 records do not. Fix: register offers for every say-expecting record.

**11. gm_seen has no owner.** DESIGN.md:156 has V2 emit gm_seen, line 164 keeps gm_sighting writing, and P0 marks it REPLACE. The detector and the gm_sightings.json writer (gm_sighting.lua:125-163), which the bridge reads, have no owner. Fix: name one owner, and keep it as KEEP or port it with a test.

**12. KEEP services lose callers at FIELD_EXCURSION=0.** relationships.record (field_excursion.lua:5364-7360) and the instructions readers (flush at 7998) are field_excursion-only. DESIGN.md:191 and 199 keep both, A4 (228) is open, and DIT C4 requires the callers. Fix: name V2 callers and readers before the flip.

**13. Adoulin crowd AH, planner and say_open are unassigned.** DESIGN.md:99 has only crowd_presence. AH runs at adoulin_crowd.lua:349-432 with no design rule. The C2 planner channel is absent, and say_open stays on the old module (DESIGN.md:164) against line 7. Fix: add an explicit AH rule naming economy_buy and economy_list, and move say_open to V2.

**14. Old drivers ignore the pilot hold.** DESIGN.md:29-31 lists unguarded natives. field_excursion (4241, 4306), party_roles (244) and starter_population (444) call them with no hold check. Fix: add native guards at those sites (dit/ C++, needs DIT review) or a Lua seam, and a canary check that held bodies are left alone.

**15. Budget window uses os.clock.** DESIGN.md:76-77 measures process CPU across all threads (lib_os.c:127; zone.cpp:482). The window owner is undefined, and the global 10 ms conflicts with the 8 ms per-zone budget (lines 213, 229). Fix: use wall-clock buckets, such as the mono clock in banshee_dit_ai_throttle.lua:82-92.

**16. P4 deletion of alive_lines breaks the transport.** alive_chatter.lua:28 requires alive_lines unguarded, and fieldShort is used at line 864. Fix: move the helpers and data to a KEEP module, and add a P4 gate with a golden outbox test.

**17. Flip list and flag table miss live modules.** The env enables ARCANUM_JEUNO, SANDORIA_ACTORS, AMBIENT_PLAYERBOT_V1, TRUSTS and FLEE_V2 (container-env-xi.txt:23-27, 94, 193, 250), and §4 names none of them. roads.lua:127-164 pcall-requires field_flee and npc_walkup, which P4 deletes. The bv2-flags.txt values are defaults, and the env disagrees on 145 of 244 shared keys. Fix: regenerate the flag table from effective values and decide every live REPLACE row.

**18. A6 is unresolved, and Crawler Camp is inert.** Crawler Camp is disabled (banshee_field_adventurers.lua:1692; env line 265). The Jeuno observations gate on presence, not PROXIMITY_OBSERVATION (arcanum_jeuno.lua:2801, 2880). Fix: make a code-level split of greeting, relationships and capture.

**19. The input baseline is not the production set.** DESIGN.md:12 calls the native tree "live," but it has 58 Lua files to live's 114 and no chat writers. P0 inventories a test map. banshee_linkshell_chat (linkshell_chat.lua:220-223, login pearl grant) is unclassified. Fix: pin the production init and env by checksum, then rerun A3 and A7 on that set.

## Minor

- Dead and stuck companions: the native clock homepoints after 300 s regardless of humans (bot_session_manager.cpp:1317). DESIGN.md:94 and 134 overstate the rule. The stuck end state and `come` semantics are undefined.
- Parity: tiers (DESIGN.md:67), order wake (75) and fixed formation (121) differ from PlayerbotV2, and there is no parity table.
- Reserve party scope is silent (DESIGN.md:89, 179, 184). The setting lists 11 names (settings/main.lua:1095), but C2 cites 5.
- Launcher tells are not an outbox producer (launcher_tells.lua:119). Remove them from DESIGN.md:41, 164 and 227.
- Rollback is restart-only (DESIGN.md:201). Each gate should state the player cost.
- Pilot-hold list omits botMount. Unstick should call the gated DitBotHomepoint (luautils.cpp:2033).
- DitBotPastime(id,'status') must pass `{}` (pastime_lua.cpp:851).

## Sound as designed

- The native pilot hold already blocks pathing, engage, transfer, homepoint, rest and non-status pastime ops (pastime_lua.cpp:631; luautils.cpp:2014-2051).
- The conduct-loop ownership skip (field_excursion.lua:8686-8712) covers the sub-drivers, which are not independent timers.
- Per-producer listener gates exist (alive_chatter.lua:337-349, 799-808).
- The milestone record shape keeps C1, and gm_sighting fails closed in the bridge.

## Needs owner or Codex decision

- Owner: does "party companions" include the reserve party? Is chat-off required at canary or only at the final flip?
- Owner: owner-bound roster or GM/controller-only authority? Which live verbs survive? Keep or retire trusts, FLEE_V2, arcanum/sandoria and the social queue? Is ambient population in scope?
- DIT: is model-compiled instructions tuning within contract (4)? Where does the Zz skip live? Which reserve list is authoritative? Who owns gm_sighting? Are native hold guards acceptable under A5?
- Codex: bridge support for wipe and revive. Does turning off the queue flags change Trust party terminal behaviour (player_ko_terminal_authority.cpp:28-40)? Do kept schedulers need a host after FIELD_EXCURSION=0?
