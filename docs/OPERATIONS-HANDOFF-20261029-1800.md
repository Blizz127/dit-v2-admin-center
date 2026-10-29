# Model-only bridge and stackd drift observations

Coordinator message `73cd4a8af5d05a7c` at October 29, 2026, 6:00 PM CT
requested these read-only Network & operations cards. No live service was read.

## DIT bridge provenance

Read `ce66285` and `9ba4ccb` from the DIT repository's Git objects.
`ce66285` is staging, not activation evidence. The actual activation receipt is
`9ba4ccb:tools/ffxi/model_only/EXECUTION-RECEIPT.md`.

That receipt reports r2 ready at 22:53:01.404 UTC, active/running, Result success,
NRestarts 0, fault marker absent. Its diagnostic poll at 22:53:00.474 UTC reports
auditErrors 0, offset 6635353, off=false. The immediate trace window contains one
poll and zero input/hub/queue rows. The model-only flag was placed inside `env -i`;
the earlier proposed unit's systemd Environment setting would have been discarded.

The receipt does not exercise retirement counters or establish post-rollout
generation/delivery. Counter values remain Unknown, not zero. Source names are
`legacy_courtesy_retired`, `legacy_fallback_retired`, `legacy_dispute_ack_retired`
and `ls_legacy_starter_retired`; they count attempts to enter retired methods,
not necessarily prevented messages. Native Lua retirement was inactive at bridge
DONE, but that observation is superseded by the later coordinator handoff:
`6ad8732c` live at 22:56:51 UTC, tasks `b1d3a7b7ad5b`/`c1033fca7a37`,
`ALIVE_CHATTER=1`, scripts retired. This later fact is attributed to the relay;
Admin did not independently read a native runtime. Owner conversation acceptance
remains not observed. Bridge source `47a9e064`, wrapper `e02ce9e5` and corrected
unit `35f7d587` remain the activation identities; proposed `e7cd6e42` was not
installed. Current status is not inferred from these dated observations.

## Latest stackd receipt and precedence correction

Admin read `4d41cdd:docs/evidence/ax41-retirement-20261029/PLANETSIDE-WAKE.md`
from DIT Git objects. Its 23:02:04.167 UTC readback supersedes the earlier counts.
The operative EnvironmentFile overrides base-unit Environment and matched the
running six-game list before this change. The previous `de8c612` FFXI suffix edit
at 22:56:28 UTC removed only a stale fallback base-unit entry (unit SHA
`82fb6334` → `b2951878`); operative configuration already excluded FFXI.
The older raw-unit comparison is not evidence of current operative drift.

PlanetSide was removed from operative `STACKD_GAMES` and `STACKD_SLEEP_GAMES`,
then one stackd-only restart applied it. Readback: PID1953169, active/running,
NRestarts0, health200, PlanetSide404. Enabled set exactly firefall, blacklight,
eden, war, rose (five); other five endpoints200/asleep, initial human samples
Unknown. The sleep list is a separate setting, not the enabled-game count.
AX41 catcher is stopped/masked/PID0 and UDP51000/51001 unbound. No game or
database restart/wake was dispatched by that rollout, per the receipt.

Shared Banshee edge8446/8450 still reaches AX41. The remaining five controller
entries mean shared migration is incomplete; cutting the forward is not
authorized by these retirement facts. Current state beyond the receipt remains
Unknown. Admin performed no live poll, restart or configuration change.

The cards add no polling, mutation controls, live endpoint, restart, provider
switch or Alienware action. Static markup checks verify the evidence distinctions
and no action controls; they do not verify runtime services or browser rendering.

Six markup checks passed. The overview's dated FFXI readiness summary now cites
the same activation receipt rather than presenting the old r5 baseline as latest;
its focused in-memory handler check passed against a temporary synthetic home,
with real sockets/processes/hub reads forbidden. Two generated-artifact asset/CSP
and JavaScript syntax checks passed after rebuilding the local preview at
`75309cc`. The artifact hash is in `NATIVE-VERIFICATION-GAP.md`; no delivered
Alienware file changed and no native browser pass is claimed.

Freshness correction validation at `76fab1f`: six markup checks plus the isolated
overview handler check passed; the regenerated artifact passed its two asset/CSP
and JavaScript syntax checks. The tests reject the stale current five-game count
and suffix claim. Receipt-time facts remain separate from current service status.
