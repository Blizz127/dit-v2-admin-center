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
not necessarily prevented messages. Native Lua retirement remained separate
and inactive at bridge DONE. Current status is not inferred from this receipt.

## stackd drift provenance

Only the coordinator relay supplies the configuration drift: saved
`STACKD_GAMES` ends `,ffxi`, runtime has six games, persisted configuration five.
Exact lists, differing game identity, unit, host and reconciliation receipt were
not provided. Do not infer which game would disappear or edit a configuration.
The warning calls out the blind-restart risk and leaves reconciliation Unknown.

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
