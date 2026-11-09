# WoW Forever bots as the DIT v2 baseline: proposal


> **Correction (2026-11-08, later the same day).** The WoW Forever bots the owner
> plays with are **PlayerbotV2** on the 70790 server build:
> `/home/blizz/build/tcf-local/src-70790-0129/src/modules/PlayerbotV2`, 671 files
> and about 248k lines, read at HEAD `c4ab28a47c7`.
> - The `production-70450` `src/server/game/Bots` system pinned below
>   (`fb754788894`) is its **predecessor**. It still sits in the 70790 tree.
>   Sections 1–3 describe that predecessor and are kept as background only.
> - PlayerbotV2 uses a tick scheduler, snapshots, an intent queue and states,
>   with model-worded chat and callouts (`BotChatModel`, `BotCallouts`,
>   `CalloutRules`). It does not write `forever_botlog.bot_event`.
> - The port already exists as the devbox-command-center botport contract
>   (`/home/blizz/scratch/devbox-command-center/botport-contract/CONTRACT-24e9fd68.md`,
>   pinned `0915dec`, FFXI task `5d4040ee3f83`). Its four required behaviors
>   are: owned actor and party; follow and navigation; combat and healing;
>   party coordination plus DIT personality.
> - The owner's FFXI instruction (below) was routed to `ffxi-platform` (Forever
>   Rust map bots), `ffxi` (legacy LSB C++/Lua bots) and devbox-command-center.
> - The hub's draft amendment was told to re-pin.

## Owner direction (2026-11-08, Admin Center terminal)

> lets port the wow forever bots over i like this to be the main baseline bot style

> no the wow forever bots are for the trinitycore wow forever server for world of warcraft froever

> i want the bots to operate the way as the wow forever bots do

> plus with DIT improvements

## What this document is

It proposes adopting the WoW Forever player-bot system as the **reference
implementation** for the body layers of the hub's `docs/architecture/BOT_BRAIN_STANDARD.md`.
DIT's own improvements are layered on top. That standard already uses AzerothCore
mod-playerbots as its reference. Forever's engine follows the same structure,
but it is our own server, measured at scale, and the owner's chosen style.
This document is a delta, not a second standard. The DIT hub lead owns the
standard and decides how it is amended.

**Source pinned:** `~/dev/trinitycore-forever-production-70450` at `fb754788894`.
That covers `src/server/game/Bots/` (162 files, about 45,700 lines) and
`docs/playerbots/` (90 docs, read from git because they are not checked out).
`sql/bots/forever-botlog-setup.sql` defines the bot log. Forever is GPLv2
TrinityCore code. **Design reuse only, no code copied.** Each game's bots are
built natively in that game's server.

**Who builds what.** In this model the bot brain runs inside each game server,
and the hub is the slow brain (chat, goals, knowledge, learning). So:
- The bodies are built by the game-server leads. FFXI goes first, per the brief;
  `FFXI_PLAYERBOTS_V0` ("same as wow bots", 2026-09-04) is already that design.
- The hub lead owns the standard, the slow-brain contracts and the conversation path.
- The Admin Center defines the baseline view and the observability contract (below).

FFXI server changes still need the owner's OK while players are online.

## 1. The Forever operating model (what "operate the way the Forever bots do" means)

**Status key** (from Forever's own docs):
- **Sim-measured:** ran in Forever's 180–1,000-bot simulation realm with
  analysed results.
- **Unit-tested:** pure decision code tested, built, and stated as not run on a
  sim server.
- **Design:** proposal only.

| # | Behavior | How Forever does it | Status |
| --- | --- | --- | --- |
| 1 | Bodies are real player characters | Socketless sessions; normal login, save and logout; bots are visible as players | Sim-measured |
| 2 | One decision engine | Strategy → trigger → action, plus values and multipliers. Three engines: out of combat, combat, dead. Named relevance bands (5–107). One action per tick. Triggers O(1). No database access on map threads | Sim-measured |
| 3 | Everything is a switchable strategy | Per-bot `+strategy/-strategy` at runtime. Every feature behind an off-by-default config switch | Unit-tested and sim-measured, per feature |
| 4 | Pure plans plus thin glue | Each feature's decisions are a pure `…Plan` function over plain data with unit tests. World-thread glue applies them | Practice |
| 5 | The log is part of the engine | `bot_event` rows: `decision` (trigger, action, relevance, rejected alternatives with reasons), `state_change`, `death` (killer, last 8 decisions), `quest` steps, `stuck`, `path_fail`, refusal codes. Per-bot trace switch | Sim-measured |
| 6 | Questing, combat, recovery, rest | Quest accept/progress/reward; class rotations by role; release/corpse run/spirit healer; eat/drink; stuck re-pathing | Sim-measured (XP, deaths, stuck per bot-hour) |
| 7 | Roles | Tank/healer/melee/ranged/caster picked from talents, with per-bot override | Design plus partial |
| 8 | Travel and leveling progression | Zone table by level and faction, route planner (walk, flight, boat), hearth and rebind | Unit-tested |
| 9 | Bots form their own parties | On shared quests within a level spread. Seek a group after repeated deaths or failures on a quest | Unit-tested |
| 10 | Dungeons | Bot-led runs; player-led runs (enter, catch up, raise after the fight, ready notices) | Unit-tested |
| 11 | Town life | Gather at inns, banks and vendors; linger; emote; sit | Unit-tested |
| 12 | Population follows load | Target = (base + per real player) × hour curve, stepped with hysteresis. Never logs out a bot grouped with a real player | Unit-tested |
| 13 | Player control | Group-leader chat orders (`stop`, `pull`, `heal`, `summon`, `revive`…) with selectors, role gates and refusal codes. Control: role, stance, focus, follow distance, "what are you doing?" | Unit-tested |
| 14 | Conversation | Six personalities. Topic templates. Pacing (one in flight, cooldown, typing delay). Command-shaped messages are never treated as conversation | Unit-tested; templates only, no model |
| 15 | Watchdog and loop guards | No progress for `StallSec` → clear goal → hearth → teleport home → stop, with a per-hour cap. XP-stall ladder | Design and rules |
| 16 | Economy and social | Auction house, bank and mail, crafting orders, guilds, duels, battlegrounds | Mixed, per feature |

**The improvement loop is part of the model.** An isolated sim realm (own
databases, shared world data read-only) runs 180–1,000 bots in real time.
- **Protocol:** freeze the build and seed; drop the first 30 minutes. Arms A
  (control) and B (rules on) are split by GUID, `Bot.Rules.ArmPct = 50`.
- **Metrics** per arm, class, hour and level band:
  - XP per bot-hour;
  - deaths per bot-hour and by level gap;
  - stuck and path failures per 1,000 bot-minutes;
  - quest accept versus reward, and quest blockers;
  - level by cohort.
- **Rules:** findings become proposed rules (condition, action, evidence,
  expected effect, risk, rollback). The owner approves, a switch ships, and the
  next run measures it. "A rule that never fired is untested, not good."
- **Example run:** 800 bots, 3.9 h — 2.4k XP and 2.50 deaths per bot-hour,
  mean level 5.1.

## 2. DIT improvements on top

These fill gaps Forever's own docs list ("ideas not done") and carry the brief's
requirements. Existing DIT gates still apply.

| Improvement | Over Forever | Gate that still applies |
| --- | --- | --- |
| Grounded conversation | Model wording grounded in current observations, replacing templates. Keep Forever's personalities, pacing and command-shape exclusion | ADR-0006: wording has no execution authority. Grounding contract. AI budget ($25/month pay-per-use cap). Failure stays silent |
| Memory of people | Per-bot memory of players (relationship ledger); bots never claim fictional progress | Grounding; player-text privacy |
| Hub slow brain | Goals, knowledge sync and learning from the hub; the body keeps the fast loop | Platform boundaries |
| Evidence ledger | Every action is request → result → verify, joined to `bot_event` by correlation | — |
| Per-game learning | Forever's sim/rules loop generalized: each game publishes its metrics; rules and policies are versioned and verified before adoption | Owner approves each rule |
| Model routing and bake-off | Cheap model for moment-to-moment, strong model for planning, rules where enough | Bake-off producer is an open owner decision |
| Kill switches, gates, audit | Forever's off-by-default switches plus DIT kill switches and admin audit | Gates off by default |

## 3. What the Admin Center does

The Admin Center adopts Forever's log as its observability contract. The
`bot_event` columns are id, ts, bot_guid, event_type, severity, reason, summary,
level, map_id, zone_id, position, quest_id, target_entry, details JSON and
session_seq. Each game's bots are asked to emit this shape, so the console works
the same across games. Planned Admin Center increments, offline and off by
default:

1. An importer for exported `bot_event` rows (no direct access to Forever's
   database: another lead's data, and an access change).
2. A bot inspector showing engine state, active strategies, recent decisions
   with rejected alternatives and reason codes, and the "what are you doing?"
   line (current activity plus non-default role, stance, focus and follow).
3. Baseline conformance per game: which of rows 1–16 and which DIT
   improvements each game's bots have, with the status key above.

## 4. Per-game starting point

| Game | Body owner | Against this baseline |
| --- | --- | --- |
| WoW Forever (Classic 1.60, TrinityCore) | Forever server lead | Reference implementation |
| FFXI | `ffxi-platform` | `FFXI_PLAYERBOTS_V0` phase 1 (socketless PC) landed in `b2a7953396` per the hub lead; the Forever rows fold into `FFXI_FOREVER_POPULATION_PLAN`. **First port**, needs the owner's OK while players are online |
| WotLK Forever (AzerothCore) | WotLK lead | mod-playerbots companions; compare after FFXI |
| SWTOR, others | Respective leads | Assess against rows 1–16 |

## Hub lead response (2026-11-08)

The hub Claude session wrote a **proposed** amendment to `BOT_BRAIN_STANDARD` §6
(branch `docs/forever-baseline-amendment-20261108`, commits `d100c15c` and
`e73692bc`, docs only). It takes effect only when Codex (the DIT lead since
11-04) or the coordinator accepts it.

- **Adopted:** §6.1 names WoW Forever at `fb754788894` as the reference for L0–L2
  and the command catalog. That covers the three engines, relevance bands, one
  action per tick, pure plans with glue, off-by-default strategies, the sim/rules
  A/B loop, the watchdog ladder, leader orders with refusal codes and "what are
  you doing?".
- **Not adopted:** row 14's conversation templates. The owner's 11-02 order is AI
  or silence; only the personalities, pacing and command-shape exclusion carry
  over. Population (row 12) is adopted under each game's ramp gates.
- **Observability (§6.3):** a proposed game-neutral export envelope
  `dit.bot_event.v1` (JSONL per game per day), with a Forever mapping. Correction
  sent back to the hub: at `fb754788894`, `recent_decisions` and the killer are on
  the `death` row. `BotAI.cpp:469` says the engine `state_change` row is "slim, the
  enriched payload lives on the death row". The table in `engine-design.md` is
  older than the code.
- **FFXI first:**
  - Body owner is `ffxi-platform`; there is no new track.
  - Order: pure plans and v1 emission offline or in a paper run, then live
    behind default-off switches, then the owner's OK for LSB changes while
    players are online, with the existing player guard.
  - After FFXI comes WotLK Forever, then the rest via the conformance tracker.

## Owner instruction: FFXI first (2026-11-08, Admin Center terminal)

> ok for chagnes thef irst thing i want done is to strip ff11 of all the old bot stuff and replaec it with the new

The owner approves FFXI changes for this work. The first deliverable is FFXI with
its old bot systems removed and replaced by the Forever-style baseline. The
Admin Center lane routes this and does not write FFXI code:
- the FFXI bot work belongs to `ffxi-platform`;
- `claude-ffxi` remains the only live FFXI server integrator;
- DIT/hub glue belongs to the DIT lead (Codex) and the hub session.

What still applies:
- protection of occupied players;
- no loss of player character, inventory or save data;
- each removal is reversible;
- single-writer ownership.

Refinement (owner, minutes later):

> keep the custom ff11 stuff though that we have but the behaviors and chat need to replace

So the instruction is not a wholesale removal:
- **Keep:** custom FFXI content, such as Banshee-specific content, bot characters
  and identities, and existing custom systems.
- **Replace:** bot **behavior**, meaning decision-making, activity, movement and
  combat logic, and bot **chat**, meaning templates and canned lines. Both are
  replaced by the Forever-style baseline, with chat as grounded AI or silence.

## Owner decisions on the FFXI replacement (2026-11-08)

`ffxi` accepted the work and planned it in phases:
- **P0:** read-only inventory, `~/dev/ffxi/handoffs/2026-11-08-botsv2-p0/REPLACE-KEEP.md`
  (71 bot Lua modules, 395 live bot settings).
- **P1:** design of a native `BANSHEE_BOTS_V2` layer.
- **P2:** offline and devbox tests.
- **P3:** one reversible flag cutover.
- **P4:** old code deleted only after the owner accepts.

The owner then answered four questions, verbatim where quoted:

1. **Writers:** "i need it spit between ff11 forever and ff11 original so whatever
   works but ff11 forever is in rust now".
   - FFXI Forever (Rust xi-map) goes to `ffxi-platform`.
   - FFXI original (LSB) goes to `ffxi`: map-side behavior, Lua strip and flags.
     DIT writes the hub wording endpoint and `src/map/dit/` session code.
     DIT's OK on the table and roles is pending.
2. **License:** "re-implement with rust in f11 forever and lsb's native". No
   PlayerbotV2 files are copied.
3. **Adoulin crowd:** keep the crowd's presence and auction-house stocking; give
   it the new behavior and chat.
4. **First cutover:** field play, party companions and chat. Crafting, economy,
   missions and pastimes stay on their current modules, with old chat off,
   until V2 covers them.

**DIT hub review of the FFXI P0 table (2026-11-08, conditional).** The hub
session reviewed `REPLACE-KEEP.md` (sha256 `2cc5363a`). This is not the DIT
lead's sign-off.

Conditions:
- **C1:** V2 keeps the `chat/outbox.jsonl` records that the replaced modules
  emit today (`gm_seen`, `order_ack`, `say_open`, grounding appends), or ships
  a paired bridge version. AI or silence, human-listener gating and the test
  skip all stay.
- **C2:** the owner's `party_reserve.json` lv89 party and the planner crowd
  channel survive.
- **C3:** V2 has its own per-bot chat cooldowns.
- **C4:** the KEEP-listed DIT services keep their callers.
- **C5:** deleting canned modules at P4 is approved.

Writers, revised by the review:
- `ffxi` writes all LSB source, including `src/map/dit/`, under DIT contract
  review.
- DIT keeps the bridge and hub, with Codex as sole bridge integrator.
- No new hub wording endpoint: chat keeps the existing outbox → bridge → hub route.

**Gate:** P1/P2 may proceed offline. The P3 flag flip needs Codex or
coordinator sign-off. The standard's §6.4 records the LSB/Forever split in
hub commit `510b04bc`.

## Canary 1 decisions (owner, 2026-11-08)

`ffxi` P2 estimate: about 01:00Z 2026-11-09. Earliest live canary: about 06:00Z
2026-11-09, then the owner's next play session. Owner answers:
- **City and bots:** the owner wants a different pick from tozizozo, edaddan and
  kelton in Southern San d'Oria / West Ronfaure. The choice is pending.
- **Test character:** Blizz.
- **Go-live:** "I approve; restart when ready". The owner's direct approval for
  canary 1, standing in for the Codex/coordinator sign-off. The restart happens
  only while CrazyAsian is offline, with notice and backup/rollback.
- **Command authority:** the bot's owner, as in WoW Forever. Whoever invites it
  can command it, and the GM override is kept.
- **FFXI Forever:** "i'd like this implemented in ff11 forever also but rust".
  Re-sent to `ffxi-platform`.

The adversarial review of the P1 design is `docs/reviews/FFXI-BOTSV2-P1-REVIEW-20261108.md`.
- **City and bots (decided):** the owner chose option C, then "bots start in windurst plesae thats where i am": 3 starter bots in **Windurst** (from Bastok or
  Windurst, over A (3 of the lv89 reserve) and B (3 Adoulin crowd adventurers).
  `ffxi` picks the city and the non-reserved, non-crafting bots. Canary 1 mainly
  tests autonomous low-level field play.

## Owner direction: Karrz 0.1.33 is the reference for all bots (2026-11-09, Admin Center terminal)

> https://github.com/Karrz1/Karrz-playerbots-wow-forever new version to look atnd use

> this is what i want to see in all bots with dit integration using ai as it can

**What the reference is now.** WoW Forever Bots by Karrz, release **v0.1.33**, published 2026-11-08 16:08Z.
- The GitHub `main` branch and every tag stop at `1d8234b` (2026-10-21), so the only source for 0.1.33 is the release asset `wow-forever-source-0.1.33.zip`.
  - sha256 `8ed3810b3f1b04bdc049b705aaa38ace2311e5830c0f68b3ab8c0d493861c6e0` matches the release's `SHA256SUMS.txt`.
  - Upstream pin: advocaite `forever` `f63ffc12`.
- `src/modules/PlayerbotV2`: 744 files, about 252k C++ lines; add-on 0.6.17.
- License GPL-2.0. Credits: agatho (PlayerbotV2), Karrz, and ike3/cmangos playerbots. For the FFXI Rust and LSB ports this is design reuse only (owner: "re-implement"); no code is copied.

**How the live 70790 tree relates to it.** The live server is not on 0.1.33.
- Karrz bots were merged on 11-02 (`99d8476cbf3`) and updated on 11-04 (`a47a6dd7878`); one fix was cherry-picked from 0.1.31 on 11-07 (`4a8ea5d53c4`).
- The live tree also carries 9 local DIT commits:
  - `.bot persona` (`BotPersona`);
  - AI callouts (`BotCallouts`, `CalloutRules`);
  - AI-only bot chat and DIT chat identity;
  - order replies.
- 0.1.33 does not have those DIT files.
- 0.1.33 adds 13 files: `BotLanguage` and `BotLocaleText`/`BotLocaleRu` (replies in the player's language), `BotSwim`, `TankStill`, `GuildAskText`/`GuildWhisperInvite` (whisper a bot for a guild invite), `PetReviveCheck`, and `zz-0-playerbot-defaults.conf`.
- Release-note changes since then:
  - quick group and `.bot add` give bots at the player's level;
  - healers drink between pulls;
  - long walks no longer stutter;
  - Blackwing Lair positioning;
  - spell-power gear counts;
  - weapon buffs at low level;
  - the City of Dalaran dungeon.
- Moving the live server to 0.1.33 is the `trinitycore-forever` lead's call. The DIT commits have to be kept.

**Upstream AI chat (what "using AI as it can" builds on).**
- `Playerbot.ChatModel.*` points at a local Ollama model (`llama3.2:3b`). It is off by default.
- It covers whispers, party and /say, with an 8-line / 10-minute history, a 3 s per-bot cooldown and a cap of 30 replies a minute.
- `Playerbot.World.Gathering.UseChatModel` makes world-bot gatherings talk in /say, capped at 4 requests a minute.
- The DIT integration replaces the Ollama endpoint with DIT, under hub conditions C1–C5:
  - AI-or-silence;
  - human-listener gating;
  - DIT persona identity;
  - per-bot cooldowns;
  - the outbox contract.

**What "all bots" means for routing.**
- Every game whose bots run under DIT takes the 0.1.33 feature set as its baseline bot style: FFXI LSB (`ffxi`), FFXI Forever Rust (`ffxi-platform`), WoW Forever (`trinitycore-forever`), WotLK Forever and SWTOR.
- On top of that baseline go the DIT improvements, with AI wording every bot line it can: whispers, party, say, callouts, order replies, gatherings.
- The hub (`dit-human-behavior-platform`) owns the standard. devbox-command-center holds the cross-project botport contract. Each game lead builds its own bodies.

**ffxi acknowledgement and owner decision (2026-11-09).**
- `ffxi` adopted v0.1.33 as the FFXI LSB reference. Canary c2.7 went live at 03:17Z.
- Its planned c2.8+ mapping:
  - the healer and nukers rest for MP between pulls;
  - an 8-line / 10-minute chat history goes on outbox records;
  - order replies and callouts are AI-worded, through the outbox only;
  - town groups talk in /say only with a human nearby;
  - language handling stays on the hub side.
- Owner decision on "bots join at the player's level": **level sync to the inviter** while the bots are in that player's party. Stored character levels stay unchanged.
- The outbox record shape change goes to the hub session (`dit-human-behavior-platform`) for confirmation.

**Owner, later the same day (2026-11-09):**

> this is how i want the bots in all games to work with dit but tailored for those games

What this means: every game with DIT bots follows the 0.1.33 operating model (owner-bound companions, follow and zone, combat roles, rest, order verbs, world gatherings, AI-worded chat), translated into that game's own mechanics, classes, chat channels and commands. It is not a literal WoW copy.
- FFXI: level sync, /heal, linkshell and /party.
- Ship games such as Earth & Beyond and EVE: formations and fleet roles in place of tank/healer.
- The hub standard holds the shared model; each game lead writes its own game profile.

DIT games with live leads:
- `ffxi`, `ffxi-platform`: FFXI.
- `trinitycore-forever`: WoW Forever.
- `wotlk-forever`: WotLK.
- `swtor-preservation`: SWTOR.
- `Earth-and-Beyond-DIT`, `earth-and-beyond-rust`: Earth & Beyond.
- `warhammer-online-rust`: Warhammer Online.

The hub has adapters for eve_online, marvel_heroes, minecraft, monster_hunter_frontier and ultima_online, but no matching session is running. Those games reach this direction through the hub standard.

**Owner priorities and requirements (2026-11-09):**

> right now ff11 and ff11 forever adn swtor are the top ones to work on

> but the bots need to knowevery class and their moves and rotations

- **Priority:** FFXI LSB (`ffxi`), FFXI Forever Rust (`ffxi-platform`) and SWTOR (`swtor-preservation`). Earth & Beyond, WAR and the other adapters come later and were not messaged.
- **Every class or job, with its moves and rotations:**
  - FFXI: all 22 jobs.
  - SWTOR: every class, advanced class and discipline.
  - Each job or class gets its own action priority list, abilities by level, and role behaviour.
  - Shared helpers cover heals, status removal, interrupts, crowd control, enmity or threat, skillchains / magic bursts, and pets.
  - The design pattern is Karrz `Combat/ApRotation` + `ApRegistry`: one APL per class/spec, 38 files in `Combat/Apl`.
- **Level, revised:** `ffxi` found that native FFXI level sync only lowers levels. Blizz is WHM 94; the canary bots are 25–26. Options offered:
  - A, down-only sync;
  - B, a temporary raise;
  - C, level-89 reserve bots.

  The owner chose **B: temporarily raise bots to the inviter's level while in the party**, after being told it is not native and needs a guarded C++ path so the level is never saved, plus a 94-level kit and a DIT BotSessionManager review. This replaces the earlier "level sync to inviter" answer.
- **Live report:** the owner said Fumika appeared stalled. It was passed to `ffxi`.
- **Parity notes for ffxi-platform:** `~/dev/ffxi/handoffs/2026-11-09-botsv2-parity-notes/PARITY-NOTES.md` (written by ffxi; read-only reference).

**Correction from `trinitycore-forever` (2026-11-09).**
- The live PlayerbotV2 matches Karrz **0.1.29.1**, not 0.1.31. On CRLF-normalized files it differs from 0.1.29.1 in 19 module files and from 0.1.31 in 68. Its only 0.1.31 content is the Heating Up cherry-pick `4a8ea5d53c4`.
- The port from 0.1.29.1 to 0.1.33 is in progress on `integration/forever-70790-bots-0133` (commit `84aa7bf58f0`). It covers the bots only (the module, `sql/playerbot_v2` and their tests), and carries the 9 DIT commits.
- The AI-only gate is held on the new chat paths (`BotLanguage`, `GuildWhisperInvite`).
- Not deployed yet. Deploy waits behind the existing maintenance hold.

**Owner, later (2026-11-09):**

> yes send the list excellent, one bot died never released, and they need to use their mounts every bot should have a mount and they need to quest and such too like subjobs etc

**FFXI checklist** (sent to `ffxi` and `ffxi-platform`):
1. combat for all 22 jobs;
2. a temporary level raise with job kits;
3. death and recovery (Raise / Reraise, release and rejoin, wipe, weakness);
4. getting bots by job and role, and filling the party;
5. **a mount for every bot**, used with the owner and for long trips;
6. **sub-jobs and quests**: missions, Fields of Valor, job unlocks, Limit Breaks;
7. party controls as in the WoW bots;
8. travel networks;
9. loot and economy;
10. battlefields, NMs and Signet;
11. world population;
12. two-way AI chat.

**Live bug:** a canary bot died and never released. Sent to `ffxi` to investigate.

**Earlier the same night (c2.8a):** Fumika's stall was a combat-assist gap.
- She assisted only when the owner was auto-attack engaged.
- She didn't chase to melee range.
- She didn't protect the party.

The fix is canary c2.8a, queued before MP rest.

## FFXI Forever: five party bots for the owner (2026-11-09)

**Owner, verbatim:**

> can we add 5 bots to ff11 forever? i'd like them to level up do missions quests also if possible

> ai can be integrated in bot rotatoins or decisoins too as we planned earlier

> i'm a rdm on the server so add the bots that match it best for parties

> i'm going to use theb ots as party members do old school part levels

**Owner answers to questions from this terminal:**
- **Era:** "Yes, keep Forever era-correct". Bots use rented chocobos for mounts. Later content stays hidden. The temporary level raise is capped at 60.
- **5 bots go:** "Go on both". That covers one population socket on Forever (while players may be online) and the DIT driver on Banshee for these 5.

**Plan:**
- The 5 bots are the owner's old-school EXP party around his RDM: WAR (tank, later PLD), WHM, BLM, MNK and THF.
- They start in his nation, seeded at his level band.
- The hub revises the roster. It first cut THF/WAR/MNK/BLM/RDM at level 1, sha `c68d2ac1…`; that roster is superseded.
- `ffxi-platform` provisions the bots and turns on the socket; `ffxi` applies the SQL with preimage and rollback; the hub runs the driver in party/assist mode bound to Blizz.

**What already exists:** the population bridge (`auto_pull`, gambits, party invite/accept, follow, assist), all default off.

**Not built yet:**
- cross-zone goto (phase 3);
- quest and mission intents: map `talk`/`trade`, plus a planner in the DIT driver;
- `ffxi-platform` P1, the owner-bound companion core, which is now its top priority.

**AI in decisions:**
- The hub published `dit.decision_advice.v1` as standard §6.5 (commit `ce9cf906`).
- Advice is for goals, party tactics and rotation profiles, chosen only from legal options the bot offers.
- The bot re-validates each choice and never waits on the AI. Every exchange is logged. A kill switch is on each game, default off.
- Both FFXI leads and SWTOR are building to it.

**Other updates:**
- **Shadowtail death:** the native 300 s death clock kept it down for five minutes. After it homepointed, a zone-follow bug left it idle in the wrong zone. The c2.8 fix waits up to 60 s for a raise, then releases, returns to the owner and handles weakness.
- **SWTOR** started a three-lane plan: every class, AC and discipline; behaviour; and AI chat.

**Party bots settled (2026-11-09):**
- **The owner:** a Forever RDM 6 from Windurst, no support job. Read-only SELECT by `ffxi`.
- **Owner's choices:**
  - camp zone "West Sarutabaruta (Recommended)";
  - level "6–9", matching the read.
- **Roster:** `roster-owner-party-windurst-6.tsv` (sha `ff835b76…31e7`), logins P02001–5, all level 6, Windurst.
  - WAR, Elvaan male (tank; PLD from 30)
  - WHM, Hume female
  - BLM, Tarutaru male
  - MNK, Galka male
  - THF, Mithra female
- **Placement:** in zone 115. They can't leave it until `ffxi-platform` phase 3.
- **Open blocker:** the DIT driver (uid 1000) can't reach the population socket in the uid-10001 container. `ffxi-platform` has to provide access.
- **Driver work:** owner-party mode in hub branch `feat/forever-owner-party-20261109` (`fe3c7c24`).

**WoW Forever:** `trinitycore-forever` built the Karrz 0.1.33 bots candidate (`8609da55023`, all bot tests pass, 9 DIT commits carried). It is not deployed. Owner task `c74bdf770f95` ("update forever bots too") is queued for `codex-trinitycore-forever`, which owns the deploy.

**Correction (2026-11-09).** My era question to the owner wrongly listed Signet and two-hour abilities as later content. The owner's answer was "Yes, keep Forever era-correct". Under that rule:
- **Stay, for bots and humans:** Signet (launch-era conquest) and base-job two-hour abilities.
- **Hidden:** SP2-style later abilities, Fields of Valor, Sanction/Sigil and survival guides.

`ffxi-platform` corrected its plan in `ab38936`.
