# Owner goal (2026-11-09): FFXI, FFXI Forever and SWTOR bots at WoW Forever level, with DIT and AI

## Owner's words (Admin Center terminal, 2026-11-08/09)

> this is what i want to see in all bots with dit integration using ai as it can
> this is how i want the bots in all games to work with dit but tailored for those games
> right now ff11 and ff11 forever adn swtor are the top ones to work on
> but the bots need to knowevery class and their moves and rotations
> they need to use their mounts every bot should have a mount and they need to quest and such too like subjobs etc
> ai can be integrated in bot rotatoins or decisoins too as we planned earlier
> i'm going to use theb ots as party members do old school part levels
> make them so they can follow me through zones too
> do the same for the SWTOR bots too
> then write a goal for me or make a goal to get this fix

## The goal in one sentence

The owner can play FFXI, FFXI Forever and SWTOR with bot party members that behave like the WoW Forever bots (Karrz WoW Forever Bots v0.1.33):
- they are bound to him and follow him everywhere;
- they know every class or job and play it properly;
- they rest, die and recover, mount up, and quest;
- they take orders;
- they talk and choose tactics through DIT AI.

Each game is tailored to its own mechanics and era.

## Reference and rules (apply to every game)

- **Reference:** Karrz WoW Forever Bots v0.1.33, release asset `wow-forever-source-0.1.33.zip`, sha256 `8ed3810b3f1b04bdc049b705aaa38ace2311e5830c0f68b3ab8c0d493861c6e0`.
- **Design reuse only:** each game re-implements natively, with GPL-2.0 attribution and no copied code.
- **DIT standard:** hub branch `forever-baseline-amendment`.
  - §6.1a: per-game profiles.
  - §6.5: `dit.decision_advice.v1`, AI advice on goals, party tactics and rotation profiles. The body offers only legal options and re-validates them; it never waits on the AI; every exchange is logged; a kill switch defaults off.
- **Chat:** AI-or-silence through DIT. No canned lines; bots speak only when a human is listening; per-bot budgets apply.
- **Unchanged rules:**
  - occupied-player protection;
  - player data stays untouched;
  - backups and rollback for every live change;
  - one live integrator per game;
  - live installs only through each game's normal path.

## Who owns what

| Game | Builds the bots | Applies live | DIT side |
|---|---|---|---|
| FFXI (regular LSB) | `ffxi` | `ffxi` | hub: chat records, advice |
| FFXI Forever (Rust) | `ffxi-platform` | `ffxi` (SQL), `ffxi-platform` (map) | hub: roster, owner-party driver, advice |
| SWTOR | `swtor-preservation` (bot-rotations, bot-behavior, bot-chat lanes) | `swtor-preservation` | hub: standard, advice |
| Scoreboard | `dit-v2-admin-center`: parity tracker and bot activity views | — | — |

## Done means: the 12 parity areas, each verified live

An area counts as **done** for a game only when:
1. it works in a live session with the owner, or with a recorded bot session on the live server;
2. there is a log line or event that proves it;
3. the parity tracker in the Admin Center shows it as **Verified live**, with that evidence.

"Built" or "tests pass" counts as progress, not done.

| # | Area | FFXI (LSB) | FFXI Forever (era 2002-03, cap 60) | SWTOR |
|---|---|---|---|---|
| 1 | Bound to the owner, party | owner invite; only the owner commands | the same | invite-only squad |
| 2 | Follow everywhere | zone lines, Home Point warps, survival guides, outposts, chocobo, airship, boat, Warp | zone lines, return to Home Point after death, chocobo, boat (era-correct) | every area transfer: taxi, shuttle, ship, Fleet, flashpoint, relog |
| 3 | Every class and its rotation | all 22 jobs, each with an action priority list (abilities, weapon skills, skillchains and magic bursts, spells by level, sub-job) | the 11 era jobs (WAR MNK WHM BLM RDM THF PLD DRK BST BRD RNG) | 8 classes, 16 advanced classes, 48 disciplines |
| 4 | Party roles and helpers | tank/enmity, heals, -na/Erase/Raise, buffs, debuffs, crowd control, pets | the same, era spells | tank/guard/taunt, heals, cleanse, interrupt, CC, defensives |
| 5 | Rest, death, recovery | /heal between pulls; accept a Raise or Reraise; release, return and rejoin; wipe; weakness | the same | rest; revive; regroup after death |
| 6 | Mounts | chocobo for every bot | rented chocobo | the class mount / speeder |
| 7 | Getting bots | add by job and role; fill the party's missing tank/healer/DPS; roster with call/save/dismiss | the same (owner party of 5 first) | add by class and role; squad fill |
| 8 | Owner orders | stances, hold, stop, flee, focus, focus heal, save MP / burst, AoE, formation, rally, who/stats/gear/help | the same | the same, via `.squad` and DIT |
| 9 | Level match | temporary raise to the owner's level while in his party, never saved | the same, capped at 60 | — (SWTOR scales) |
| 10 | Quests and progression | quests, missions, Fields of Valor, sub-job and job unlocks, Limit Breaks | quests and missions (`talk`/`trade` intents plus a DIT planner) and rank | class story and planet quests alongside the owner |
| 11 | AI chat | two-way: tells and party replies with memory and the player's language; callouts; town gatherings | the same | party, say, whisper through ChatGateway |
| 12 | AI decisions | `decision_advice.v1` for goals, tactics and rotation profiles | the same | the same |

Later, after 1-12: loot etiquette and economy, battlefields and NMs (era-gated on Forever), world population, flashpoints/ops autopilot (SWTOR).

## Order of work (from each lead's own plan)

**FFXI (`ffxi`):**
1. c2.8: party assist and melee range (Fumika); death and recovery (Shadowtail).
2. c2.9: MP rest; party controls, part 1.
3. c2.10: mounts.
4. J0: job-kit framework, sub-jobs, the AI advice seam.
5. J1: THF, WHM and BLM kits.
6. Level raise (guarded C++ plus a DIT review).
7. J2: PLD WAR RDM BRD NIN SAM, plus getting bots.
8. J3: MNK DRK DRG RNG COR DNC RUN BLU, plus travel networks and owner questions.
9. J4: BST SMN PUP SCH GEO, plus loot and economy, and quests and missions.
10. J5: content and population.

**FFXI Forever (`ffxi-platform`):**
1. The owner's 5-bot party: WAR, WHM, BLM, MNK and THF, level 6, from Windurst, starting in West Sarutabaruta.
2. Socket access for the DIT driver.
3. **Cross-zone follow (owner priority).**
4. P1: the owner-bound companion core.
5. P2: APL framework and the 11 era jobs.
6. `talk`/`trade` intents for quests and missions.
7. P3: chat cutover.
8. P4: personas and population.

**SWTOR (`swtor-preservation`):** three parallel lanes:
- bot-rotations: every class, AC and discipline from client ability data;
- bot-behavior: follow and travel across every transfer, roles, rest, orders;
- bot-chat: AI through DIT.

It builds on the live Python server (c30) first; Rust sw-squad mirrors it.

## Owner acceptance tests (one play session each, per game)

1. **Invite and follow.** Invite the bots. Change zone or area three times, by walking and by one teleport or transport. All bots arrive within 30 s each time, and the party never drops.
2. **A camp.** Fight 10 pulls at an appropriate camp.
   - The tank holds hate.
   - The healer keeps the party up and rests for MP between pulls.
   - Every bot uses abilities that fit its job and level (checked in the bot activity view).
3. **Death.** A bot dies.
   - It accepts a Raise if one comes within 60 s.
   - Otherwise it releases and is back with the party within 5 minutes.
   - It does not pull while weakened.
4. **Orders.** stay, follow, assist, attack, pull, rest, a stance, focus heal and dismiss each get the right action and an AI-worded acknowledgement (or silence).
5. **Mount.** The owner mounts or travels far, and the bots mount too; they dismount to fight.
6. **Quest.** A quest or mission step done together with the bots present and helping.
7. **Talk.** A /tell and a party message to a bot get a relevant AI reply that remembers the last few lines.
8. **AI tactics.** With advice switched on, the activity view shows at least one applied advice record (goal, tactic or rotation) and its reason. With advice off, the bots still play correctly.

## How progress is shown

- **Parity tracker** (Admin Center): one row per area, one column per game, with status Not started / Designed / Built / Verified live, and evidence for every cell.
- **Bot activity views** (Admin Center):
  - what each bot did and why, from FFXI `[BOTS-V2]` log lines and from DIT `bot_event` / `decision_advice` records for FFXI Forever and SWTOR;
  - refusals, deaths and recoveries, zone changes, applied advice.
- **Status on request:** ask this lane for the 12 areas per game, the next milestone, and anything blocked on the owner.

## Owner decisions already made (don't re-ask)

- **FFXI level:** temporary raise to the inviter's level, never saved (option B).
- **FFXI Forever:**
  - era-correct: rented chocobo; raise capped at 60; base-era features stay (two-hour abilities, Signet/conquest); only later content is hidden (SP2-style abilities, Fields of Valor, Sanction/Sigil, survival guides);
  - camp zone West Sarutabaruta;
  - the party is WAR, WHM, BLM, MNK and THF around the owner's RDM;
  - go on the population socket and the DIT driver.
- **Commands:** only the bot's owner, like WoW Forever.
- **Keep:** the custom FFXI content; replace only behaviours and chat.
