# FFXI wire-on: Admin Center readback

## Authority and ownership

Coordinator message `015e8eb8311ca58f`, tag `ditv2wire-0827`, relays Blizz's
2026-10-29 08:26 CT approval to wire DIT into FFXI and restart the bridge as
needed. The current assignment names dit-human as DIT owner and claude-ffxi as
game-server/bridge owner. Admin Center supplies readback and reconciles their
receipts through the coordinator; it does not start a competing deployment.

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
