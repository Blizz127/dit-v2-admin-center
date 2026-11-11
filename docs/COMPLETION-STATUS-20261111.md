# Admin Center completion checkpoint — 2026-11-11

Assignment: owner relay `bb5ec07bb0ebb6fd`, continue autonomously toward the
Admin Center brief while preserving explicit access, data, player and push
restrictions. The application is **not complete as a live control center**.
This checkpoint distinguishes implemented local review from its real upstream
dependencies; synthetic checks cannot close those dependencies.

## Completed in this increment

- Per-game parity review: game, behavior-group and status filters; separate
  counts for Verified live, Partly live, Built, Designed, Unknown and Not
  applicable. Missing evidence and ambiguous identities withhold positive
  statuses. Counts do not certify the full goal.
- Portable export review: explicit CLI paths reuse the four existing bounded
  readers. Unselected sources stay Off; unreadable supplied inputs refuse the
  build. Private output uses exclusive creation and a 16 MiB cap. Paths and
  unparsed lines are omitted. Accepted event details remain private content.
- Eight owner playtest scenarios for FFXI, FFXI Forever and SWTOR, with each
  game's mechanics, required evidence and related tracker citations. These
  plans neither record results nor change statuses or enable advice.

Preview 22566d3e delivered the first two features; **d9bea515** adds the
checklist, verified on Alienware at 19:15:33Z. See
[the release log](BOTS-PARITY-PREVIEW-20261109.md#delivered-preview-d9bea515-source-115f896).
The first export-review package uses existing FFXI export 7, not new post-H1
evidence. No real SWTOR export was supplied. No bot implementation or game
deployment was performed by this lane.

## Current source evidence for remaining dependencies

Read-only inspection used the named hub release-source worktree
`/home/blizz/dev/dit-hub-r5q-20261109` at
`0ce5113effdcf9204874eecb6ea0ffdf88f6ab10` (November 9), with the named
`dit-ffxi-ls-replies-20261101` lineage at `6a0121d6` and standard/driver
worktree `dit-forever-baseline-20261108` at `bde601a6` for context. The old
shared hub checkout is not assumed current. These observations establish
source readiness only; the deployed hub version was not checked.

| Brief capability | Remaining dependency and exact source finding |
| --- | --- |
| Live roster, learning and interaction reads | `HubTokens.cs` defines Reader, but `AdminCenter.cs`, `ControlCenter.cs` and `InteractionAdminApi.cs` still guard control routes with Admin. Those guards are unchanged from November 3 source `043bc4b1`. No reader-only control path or later access-resolution receipt was found in the inspected sources. Preserve the owner access choice; use exported snapshots meanwhile. |
| Per-bot commands and goal changes | A command catalog exists at `GET /v1/games/{gameId}/commands` in `HubApi.cs`, guarded by owning-adapter/admin access. Admin goal POST supports add/pause/resume/remove and adding a goal may invoke planning. These are not an authorized, scoped start/stop/pause adapter for this app. The consumer contract and actual execution receipts remain necessary. |
| Per-bot model choice and audit | `ModelProviders.cs` and `ProviderCommand` remain global purpose-based settings. The scoped game/realm/native-bot/purpose routing proposal remains design-only; no matching compare-and-set and requested/effective per-bot audit contract was found. No model switching is enabled here. |
| Per-bot usage, comparisons and learning outcomes | `AiSpendLedger.cs` records provider/model/purpose and billing/tokens/cost, but lacks game/bot/realm/task/input/quality attribution. Real evaluator/bake-off and game-outcome producers remain needed. Loaded examples cannot establish these measurements. |
| Gates, stop controls and action evidence | Authoritative scoped gate observations, approved command execution and native delivery receipts remain necessary. Existing bot/goals GET handlers call `Goals.ImportProgress()` and stay outside this app's read allowlist; GET does not itself establish absence of side effects. |
| Bot parity acceptance | Real FFXI post-H1 and SWTOR bot-event exports plus the eight documented play sessions are still required. Imported activity never automatically promotes a tracker cell. |
| Native UI acceptance | Browser rendering, native keyboard, downloads and CSP enforcement remain unrun. Earlier runtime/namespace restrictions are not bypassed by simulated-DOM checks. |

The newer `AdviceApi.cs` is a guarded adapter/relay POST for game advice. It is
not an Admin control/readiness API or a routing-audit substitute. No token or
credential/config file was read, no service was queried, and no source was
changed in the hub worktrees during this assessment. This is not a claim that
every uninspected branch lacks a future implementation.

## Next integration boundary

The current unblocked release increment is implemented. A supplied approved
export can now become an owner-readable report without new access. Integrate a
new authoritative contract or native receipt when its owning lead supplies it;
preserve one integrator and existing dispatches. Do not treat this assignment
as permission to provision credentials, activate existing mutation APIs, change
security, enable model routes, or assert live completion. Git pushes still need
the owner's explicit instruction. The local localhost scaffold and private
HTML reviews are not a production hub/game deployment.
