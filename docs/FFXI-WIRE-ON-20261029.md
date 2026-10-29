# FFXI wire-on: Admin Center readback

## Authority and ownership

Coordinator message `015e8eb8311ca58f`, tag `ditv2wire-0827`, relays Blizz's
2026-10-29 08:26 CT approval to wire DIT into FFXI and restart the bridge as
needed. The ownership wording in that message was corrected by coordinator
message `16b690b0460abcc5`, tag `ditv2own-0836`: **claude-dit-human-behavior-platform
is the sole chat-bridge installer/restart owner**. Claude-ffxi owns the separate
fishing r2 map/game-server change. Admin Center is neither writer. It supplies
handoff information through the coordinator and continues offline work; it
does not install or restart anything live for this step.

Explicit done-or-blocker note for claude-ffxi (sent through the coordinator in
reply to `88cd5d8f9c3788ee`): **Admin Center's evidence handoff is done.** This
lane has no live writer, install/restart in progress, lock or additional hold on
the staged game install. This does **not** mean the bridge restart is done. The
sole DIT bridge integrator's current done-or-blocker receipt is the authoritative
dependency; neither this note nor the historical active-unit observation
bypasses that dependency, player protection or rollback requirements. The relay
was queued; recipient delivery has not been confirmed to this thread.

Before any live change, the owning integrator must freshly verify that
CrazyAsian is offline and retain a backup/rollback point. If online, wait and
retry. Unknown player state is not an offline check. Preserve checklist-specific
default-off flags, real saves and unrelated credentials/security settings.
This approval does not enable Admin Center model switching or bot-edit controls.

## Actual observation

The existing `BridgeObserver` was invoked once, with its fixed read-only script,
strict SSH host-key checking and eight-second subprocess bound. It reads only
the allowlisted service fields and private fault-marker classification; no
player text, token or account file was read or printed.

| Field | Observed value |
| --- | --- |
| Observation time | `2026-10-29T13:35:01.865768+00:00` |
| Host | Existing verified target `blizz@100.74.44.12` |
| Unit | `dit-ffxi-chat-bridge-v2.service` |
| ActiveState / SubState | `active` / `running` |
| Result | `success` |
| Delivery-fault marker | `absent` |
| Marker reason | `unknown` |

This is a baseline/status observation. It does **not** identify the deployed
source, establish that a restart occurred, prove an offline player check,
confirm a rollback point, or demonstrate native speech/behavior. No live change
or restart was performed by this Admin Center lead.

## Receipt reconciliation still needed

### Candidate handoff sent after ownership correction

Local bytes at
`/home/blizz/dev/dit-v2-release-20261027/ffxi-bridge-dirfd-r5/ffxi_chat_bridge.py`
were hashed again, without executing or changing the candidate. SHA-256:
`3d160be2ea3ffc3fcc2d759cca191fcd9147124cdcbb79a7125e9d23b96aa9b4`.

The adjacent `DEPLOYMENT-RECEIPT-20261028.md` already reports installation of
those bytes on October 28 and activation at 15:28:09 UTC. It records the old
unit/marker backup references and preserves `Restart=no`. This is historical
evidence, not a new rollout, a current hash check on the server or authority to
replay the old restart commands. The DIT lead must reconcile current state.

DIT's `docs/evidence/ffxi-relative-inbox-20261028/README.md` reports fourteen
synthetic checks and three directory/permission-pattern checks. Candidate-local
test files are `test_dirfd.py`, `test_delayed_fault.py`, `test_inbox_scope.py` and
`test_party_greeting.py`. Admin Center did not rerun these checks or inspect
live inbox contents. The path, complete hash, historical receipt and evidence
locations were sent through the coordinator for the sole DIT bridge integrator.

### Current rollout receipts

Requested through the coordinator from the owning leads:

1. Current checklist and exact selected candidate/revision; older r5 fault-repair
   and offline party-coordination notes are not selected by this readback.
2. Fresh CrazyAsian identity/session evidence and the pre-change offline result.
3. Backup/rollback location and integrity reference, with no inbox replay or
   save restoration implied.
4. Installed revision/flags, restart time, startup/readback result and any
   subsequent fault marker.
5. Native party-chat observation, separately from a queued reply, accepted
   receipt, model output or active service.

The read-only Admin Center hub path still needs its already-approved token-file
location and configured endpoint from the hub owner. No token is minted,
searched for or copied by this handoff. The application remains loopback-only;
the service was not restarted and model controls remain disabled.

Reconcile the owners' receipts before labeling the UI or a report as deployed
or playable. A later post-restart readback is useful only with the owning
integrator's restart timestamp and exact artifact identity.
