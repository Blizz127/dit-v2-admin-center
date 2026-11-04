# Native status producer mapping: integration candidate

This is local integration work for the shared cross-game conversation design,
not a deployed producer contract. Both conversation allowlists remain unset.
The shared hub, bridge, SWTOR source and game processes were not modified.

## Implemented boundary

The isolated hub candidate reads the existing FFXI `ObservedStateStore` through
`FfxiInteraction`. It does not call the report route, ingest a new snapshot,
create an order, dispatch an action or contact a device. Snapshot, actual ingress
receipt time and ledger high-water are read under the interaction ingest gate.
Duplicate/out-of-order snapshots cannot refresh the recorded receipt time.
If an action report has superseded the snapshot, the reader requests a new
full snapshot instead of combining fields from different revisions.

The authenticated adapter scope travels separately from JSON through group
companion replies, heard-line replies and event/intent wording. `NativeScope`
is ignored by JSON serialization/deserialization. Existing route permissions
are preserved: administrator access does not attest native ownership, and a
relay does not become a native adapter. Unauthenticated or wrong-game callers
remain refused by their existing routes.

`HubRuntime` accepts an optional in-process `statusBodies` registry keyed by
`(InteractionScope, actorKey)`. The integrator must supply a verified mapping to
`(game, realm, instance, nativeActorId)`; no registry is supplied by default.
The candidate validates and copies it, with a 5,000-entry bound. It does not
guess native IDs from persona/display names or use instance as an invented
realm. Registration itself enables no flag. The source also refuses reads when
the existing `DIT_FFXI_INTERACTION_CONTRACT` switch is off.

`DIT_CONVERSATION_STATUS_GAMES` still gates every service read and final status
recheck. `DIT_CONVERSATION_CONTEXT_GAMES` independently gates structured
history. Direct in-process callers must supply their trusted scope explicitly;
calls without it receive unavailable status, not somebody else's native body.

## Producer evidence still missing

| Input | Inspected implementation | Candidate behavior | Dependency |
| --- | --- | --- | --- |
| FFXI identity | v1 `actorKey`, authenticated caller, server instance | Exact caller/instance/actor match plus explicit trusted body registry | Verified realm/native-body mapping from the owning integrator |
| FFXI presence | No explicit presence/disconnect field in `ObservedState` v1 | Presence unknown; all current body values withheld by projection | Native presence lifecycle evidence tied to the same body and epoch |
| FFXI body observations | Full snapshots with epoch/sequence, source observation time, zone, job, level and native activity inputs | Reads existing ordered store; preserves observation/receipt times; ignores assigned pastime as current activity | Real producer/bridge deployment and outcome remain unverified |
| FFXI later action receipts | May supersede the full snapshot | New snapshot required; no clock borrowing from a mode heartbeat | Next authoritative full snapshot |
| SWTOR | Inspected hub module/relay has no equivalent ordered native-status feed | Source unavailable; no FFXI fallback or chat-derived presence | Owning SWTOR integrator's native feed and identity binding |

The FFXI reader maps existing raw fields but deliberately emits **no presence
observation**. The projector consequently supplies no known location/activity
facts, even for a fresh v1 snapshot. A source label or revision digest is not
proof that a body is online. This conservative plumbing is not a claim that
real producer integration is complete or that live chat is fixed.

For time handling, the existing native store tolerates some positive clock
skew. This candidate refuses snapshots observed after their recorded receipt
time rather than rewriting those clocks. That can withhold additional facts;
it does not establish a new agreed producer clock policy.

## Proposed producer evidence, for the owning integrators

Supply the following from an authenticated native boundary, never chat, bot
memory, plans or an Admin display configuration:

1. A stable native body ID and realm binding for the exact adapter caller,
   instance and actor key. Explain reconnect/transfer behavior and whether the
   mapping changes when a body is replaced.
2. Explicit online/offline/unknown presence with observation time and deadline,
   tied to that same body, session epoch and revision. Define what a native
   disconnect, despawn, producer loss or missed heartbeat means. Receipt time
   alone must not certify online presence.
3. A full-snapshot revision boundary shared by presence and body fields, or a
   separately specified reconciliation rule. A process crash between two files
   or two messages must not combine a new presence claim with old activity.
4. Field-specific freshness policy and unknown semantics. Missing activity
   never means idle; goals such as leveling/crafting never mean observed action.
5. Synthetic fixtures for fresh, disconnected, expired, replaced-body,
   wrong-caller, out-of-order and gap/reconnect cases. Native runtime/delivery
   receipts remain separate from consumer tests and model prompt receipts.

No new wire fields or policy above are agreed merely by writing this note.
The candidate does not add them to the existing producer contract, mint a
presence observation, or enable either game. Hub and game leads keep their
existing single-writer ownership and release/active-player holds.

## Rollout and rollback

1. Review/apply the candidate only in the integrator's isolated checkout. Keep
   both allowlists unset and do the focused build/startup checks.
2. Exercise only synthetic fixtures with the flags selected locally. Verify
   caller isolation, absent mappings, missing presence, superseded snapshots,
   original clocks, and no source reads when the status flag is off.
3. Preserve the producer dependencies above. A later native presence mapping
   needs its own focused checks before any known body facts can be used.
   Actual live flags, device work and delivery remain behind their existing
   owner/source/spending/player-protection gates.
4. Roll back by unsetting the conversation allowlists and removing the optional
   source registration. The existing interaction switch retains its original
   behavior. No database schema, stored game data or credential is migrated.
