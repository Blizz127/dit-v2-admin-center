# Cross-game conversation boundary swarm

The owner clicked **Swarm it** for the current DIT goal. Root reused
`/root/native_boundary_review` and started `/root/producer_context_boundary`
and `/root/admin_context_truth`. All three ran concurrently in the supported
native team, filling the three helper slots exposed to this lead. Later work
reused the same helpers with disjoint files. Root alone reviewed, committed,
packaged and ran builds. No other project owner, provider or publisher was
started, resumed or replaced.

Candidate `9c99e01ab1121b230773f3610f72f21673433920` extends the previously
verified `a3155646` source in the Admin-owned isolated checkout. The source
changes address concrete defects found during the swarm:

- Selected client responses must match their line and exact actor key. Ambiguous
  decisions are withheld before their text reaches diagnostics or wording;
  a mismatch does not invoke a local fallback. Rejected shadow comparisons do
  not replace a valid authoritative reply or claim the hub was unreachable.
  The final review caught case-alias acceptance. The client now rejects those
  aliases before legacy group selectors can choose them, with ten added cases
  covering ordinary replies, events and either group ordering. Flag-off
  matching behavior is preserved.
- Selected command decisions record a request with completion unconfirmed,
  retaining the existing canary rule. Command execution, deduplication and
  flag-off behavior remain intact. Requested emotes already avoided completed
  action memories and required no runtime change.
- All three optional TR-guide accesses require the exact TR game first.
  Installing a guide elsewhere cannot route FFXI/SWTOR requests, offers or
  eligibility through it. The guide is not activated; same-game execution is
  unchanged by this guard.
- A retained fallback draft keeps its own request/status binding and rechecks
  it before use, even if a later rewrite captured different status.
- Wording that finished before a slower command interpreter is rechecked
  after that interpreter declines or fails. Expired or changed body status
  cannot become a normal reply from that earlier result.

Admin commit `a9971907e3e3824bffaf30da4db805e1ad5145a4` separately fixes the
shared capture validator. Offline, Stale or Unknown presence cannot coexist
with known body details, even when the supplied facts and prompt hash agree.
Valid Unknown captures keep their conversation history. **26 focused Python
checks passed**, including authenticated localhost startup, rejection and file
recovery; the adjacent log records that result.

## Integration intake

This is one replacement intake for the existing hub integrator/publisher.
The coordinator CLI accepted and queued this superseding intake after final
verification (`intake-dispatch.json`). That confirms queueing only, not hub
receipt, application or deployment. Do not repeat it while waiting for a
receipt; no acknowledgement is a gate on independent authorized work.
Choose exactly one patch based on the source already present:

| Starting source | Patch |
| --- | --- |
| Verified conversation candidate `a3155646` | `from-a3155646.patch` |
| Hub `6a0121d6` without the conversation candidate | `current-hub-candidate.patch` |

Both applications reconstructed the exact candidate tree in an Admin-owned
temporary index. The shared hub worktree/index was untouched. The full patch
replaces the previous full patch in `../speech-memory-verified-20261108/` and
the older scattered assemblies; do not apply them in addition. If integration
already progressed or the hub source moved, reconcile that existing work
through its sole integrator. Do not restart an already-dispatched integration.

Publication belongs to that existing private hub publisher. There is no new
coordinator acknowledgement, independent-review or full-suite gate. Retain the
previous artifact/configuration for rollback, keep concrete occupied-player,
data, native-permission and access safeguards, and do not infer activation of
an optional source or game adapter from source packaging.

## Verification and limits

The selected C# check set contains 81 cases: 12 command/emote memory, 28 client
response-boundary, four cross-game guide, eight retained-fallback status,
12 slow-interpreter status, 13 existing producer-context and four authenticated
localhost history-flow cases. All **81 passed**, with none skipped, at **2026-11-08T04:52:28Z**.
Client and test builds passed with zero warnings/errors. Core and Hub had
already built successfully in the recorded earlier stages; their unchanged
DLL hashes match the test outputs, as does the newly rebuilt Client. This is
a focused incremental Debug build, not a clean rebuild of every dependency.
The four localhost cases cover 12/12 turns and the latest 16/32 whole turns
for each game, including reported omissions; history is not unlimited.

The first bounded job at `ad872d36` built Core and Client with zero warnings or
errors but reached its 600-second overall limit during Hub compilation. The
resume built Hub and the test assembly; it reached its time limit after seven
reported test passes, before a complete result. Both logs and results are
preserved. These are incomplete runs, not a green test set. The final
`9c99e01a` follow-up only changes Client and its test source, reuses hash-checked
Core/Hub outputs, and gives test execution a separate budget after compilation.

All jobs use one CPU/MSBuild node, I/O priority 7, no restore or reference
rebuild. The first job used nice 19 and a 6-GiB GC cap; resumed work uses nice 10
and a 3-GiB cap. Fresh CPU, memory, swap and I/O samples are adjacent. At the
last sample the host had 0.57% idle CPU, load 463, 46.95 GiB available memory
and active swap; no compiler fanout or retired admission lock was used.

All checks use synthetic identities, temporary or in-memory stores and fake
providers, sources, interpreters or guide executors. No real model, native game,
device or stored player data is used. The event response contract has only an
actor identity, so that path cannot yet validate an echoed line ID. Flag-off
client behavior remains legacy behavior. Native receipt provenance and body
presence feeds remain separate producer dependencies.

The private owner preview already delivered as `4fa9e59` was not copied again.
The existing synthetic delivery captures were not regenerated or relabeled.
Native browser, actual game delivery and deployment remain unverified by this
swarm. Local candidate artifacts are not a published/deployed version.

See [memory boundaries](../../docs/CONVERSATION-MEMORY-BOUNDARIES.md) for dormant
or other-game writers that this work does not activate or certify. Root's
read-only delivery-correlator review found its existing conflict, scope,
duplicate and synthetic-only safeguards adequate; no speculative changes were
made there.
