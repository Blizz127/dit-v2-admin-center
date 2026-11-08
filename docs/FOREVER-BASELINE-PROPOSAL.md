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
