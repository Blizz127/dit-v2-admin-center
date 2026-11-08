# Swarm result: speech memory and one hub source intake

The owner directly requested in-session swarming within the existing DIT Admin
goal. Root reused `/root/native_boundary_review`; no additional worker, retired
provider, other project or competing publisher was launched. Root owns this
package and remains the sole Admin integrator. The worker owned only the
isolated conversation-service increment and its new focused tests; it did not
build, test, commit, publish, contact a device or modify shared source.

## Consolidated reference candidate

`hub-context-candidate.patch` replaces the prior multi-patch assembly for an
integrator starting at committed hub `6a0121d6`. It includes the context/status
candidate, wording serialization integration assertions, synthetic candidate
exporter, and the group prepared-reply memory fix through `59ab778a`. It
preserves the hub's existing serialization fix and all other upstream files.
Do not also apply the older combined context/voice, roundtrip-test, exporter
or group-memory patches.

Composition used a temporary index in the Admin-owned isolated repository; the
shared hub worktree and index were untouched. All 31 changed files match the
compiled reference candidate byte-for-byte. The reference's eight latest
focused tests passed in the
[verification handoff](../prepared-memory-verification-20261108/README.md).
This composed tree on the newer hub base has **not** itself been built or run;
source equality/application is not a deployment or startup claim. The existing
hub integrator must apply to its own current release source and do the focused
build/startup smoke, accounting for intervening changes.

## Further source increment, separate verification boundary

The adjacent-path review found that event wording could still enter the bot's
journal as “I said” before publication, despite the earlier group-path fix.
For selected structured-context games, the event increment keeps supplied
ordinary event details/place/nearby observations without generated speech;
channel-start intents add no observation journal entry. Legacy behavior and
cooldowns remain intact. It introduces no native receipt endpoint or authority,
and does not erase existing memory.

The direct heard-line `Finish` path had the same memory defect and also credited
`Chatted`/`AnsweredBot` from a prepared response. Its selected path now preserves
heard player text/place without outgoing speech/emote claims and skips those
response-dependent relationship updates. Existing observations, relationship
records, duplicate-request suppression, selection/focus and cooldowns remain.
Flag-off behavior is unchanged. Command and requested-emote branches that
bypass `Finish` are outside this increment.

`RecordChatEnvelopes` still persists incoming player observations, never the
generated response. The independent FFXI relationship feed can classify an
addressed incoming observation as `AnsweredBot`; this patch and its tests do
not remove or claim to cover that separate classification.

Root reviewed and committed the worker's two increments as `95f2defd` and
`efbbf699`. `PENDING_CANDIDATE_REVISION` pins the latter. Eight new regression
cases are written: FFXI/SWTOR, flag on/off, for event and heard-line paths.
They check next-request memory, preservation of supplied/repeated history,
existing event/relationship evidence and deduplication. **Build NOT STARTED;
new tests NOT RUN.** Do not inherit the reference's eight-test pass.

Fresh measurements at 03:20:28Z on 2026-11-08 showed only 0.4% idle CPU across
48 CPUs, CPU pressure avg10 34.97%, and 3,575 swap pages read over two seconds.
Available memory was 113.63 GiB. No compiler was launched under that CPU
saturation; `capacity-observation.json` preserves the complete sample. No
retired admission lock or fixed load threshold was used, and no background
resource wait remains. Next verification is one bounded job sized to fresh
CPU/memory/swap/I/O capacity, using the four-class filter in `verification.json`
(16 focused cases total, not a full suite).

`pending-speech-memory.patch` is the incremental delta from 59ab778a to
efbbf699. In an Admin-owned temporary index it reconstructs the exact candidate
tree. Applying it after the consolidated reference patch also succeeds; all
33 changed files then match efbbf699 byte-for-byte. This verifies packaging
only. Neither that new candidate nor the composed hub tree has been compiled
or run in this wave.

## Existing integrator ownership and evidence

This is one actionable replacement intake for the existing hub integrator,
superseding the scattered assembly instructions in the context/voice,
wording-wire and release-resume handoffs. Their past results and source pins
remain valid historical records. Use the reference patch only on its stated
hub base; an integrator already on 59ab778a needs only a later incremental
patch, not this consolidated reference patch again. Keep the pending increment
separate until its focused build/checks run; do not make it a new hold on the
already-verified reference increment.

| Starting source | Source intake | Verification boundary |
| --- | --- | --- |
| Hub 6a0121d6 without this candidate | `hub-context-candidate.patch` | Changed files match verified 59ab778a; composed hub still needs its own focused build/startup smoke |
| Isolated 59ab778a, or hub after the reference patch | `pending-speech-memory.patch` | New event/heard increments are uncompiled; run the recorded filter before release |

Source rollback is to reverse only the applied increment in the integrator's
isolated checkout; do not remove the hub's already-existing serialization fix.
There is no live rollback action for source this lane has not deployed.

No shared hub/bridge source, live flag, game data, service or device was changed
by the swarm. Native body/presence and speech provenance remain producer
dependencies. The separate e55/c301 delivery fixtures were not regenerated.
The owner preview already delivered at 00:44:20Z was not copied or republished.
No routine approval, independent-review release gate or acknowledgement wait
is added. Do not apply an unrun increment as though it were a verified runtime.
