# Shared status read projection: offline candidate

Prepared for the DIT hub lead, 2026-11-04. This is an unwired source proposal,
not a replacement producer contract, live store, or deployed status feed.

The existing FFXI `Interaction/ObservedStateStore.cs` remains the owner of native
snapshot ordering and retired epochs. The generic `ObservationEnvelope` also
already carries observation/validity times; this candidate does not redefine its
historical-observation semantics. Neither existing implementation is modified.

## What this slice implements

One pure `ConversationStatusProjection.Build` produces the same read view for
bot context and an Admin consumer. It requires an authorized body identity
(game, realm, instance, native actor), the current epoch and sequence, a native
snapshot, and a versioned expiry policy. A trusted integration boundary must
obtain the cursor and snapshot atomically from its existing ordered store.

The view records source, snapshot digest, policy version, read time and each
field's observation/deadline. Supported current-body fields are presence,
location, activity, party, job and level. Missing data stays unknown. This is
not a durable inventory/progress model or an action-execution contract.

- Wrong body, epoch, revision, source, incomplete frame or a pending sequence
  gap produces unknown fields without leaking values or a foreign revision.
- Conversation text and plans cannot be passed as native evidence. The source
  allowlist is supplied by the trusted caller, never by the chat input.
- Each field expires at the earlier of its native deadline and its explicit
  configured maximum age. A heartbeat/duplicate receipt does not renew it.
- A confirmed disconnect keeps the native offline observation while withholding
  other current body facts. Missing or expired presence also withholds them.
- Only known values enter `ApprovedFacts`. Stale/unknown values are null; the
  reason and available timestamps remain inspectable.
- Snapshot digests bind canonical sorted fields, identity, source, epoch and
  sequence. Receipt time is excluded. Digest equality is not authentication or
  proof of the producer's honesty.

Test expiry values are synthetic, **not** proposed production timeouts. The
candidate requires every supported field to have an explicit positive lifetime
bounded to one day. Policies are copied and versioned; values are not read from
a mutable caller dictionary after construction.

## Integration still required

No code calls the projector in the runtime; no configuration switch can enable
it. The patch only adds a component and tests. There is no route, native status
producer, new persistent store, or live Admin endpoint. No real game data was read.

The hub lead needs to choose a trusted adapter mapping for identity/source,
field observation times and expiry policy, then wire both consumers to one
atomic store read. The expectation/cursor is **not** an input to accept from a
bot, chat message or untrusted HTTP payload. The projector itself provides no
authentication, membership checks, delta ordering, epoch advancement or conflict
resolution. Existing stores must enforce those and signal gaps before projecting.
An Admin view may inspect an authorized actor; one bot does not automatically
receive another bot's or another game's private status.

FFXI's existing full snapshots can support a first mapping only for fields they
actually observe. SWTOR still needs its real adapter mapping. Do not infer a
native actor ID or field timestamp from a display name, heartbeat or goal.
Multi-source conflict resolution, typed per-game durable progress, scoped memory,
pre-delivery revalidation and native delivery acknowledgement remain later slices.

## Handoff and verification

`BASE_REVISION` is the pinned hub source. This patch only adds two new files and
is independent of the structured-conversation patch. It was built in the same
isolated source snapshot, with the first patch present. The shared hub worktree
was not edited. Preserve its current owner, player, source and release holds.

Run the focused test after applying in an authorized isolated checkout:

```sh
dotnet test tests/Dit.HumanBehavior.Neuronetwork.Tests --filter 'FullyQualifiedName~ConversationStatusProjectionTests'
```

Set `DIT_STATUS_FIXTURE_OUTPUT` to an empty local directory to export two
synthetic FFXI/SWTOR captures. Each contains the same snapshot read when fresh,
after activity/location expiry, and after a native disconnect. No HTTP, model
or game call is made.

Validation on 2026-11-04: **16 focused tests passed**, none failed or skipped.
The exported captures are committed under `tests/fixtures/status-captures`.
The patch passes `git diff --check`; read-only `git apply --check` passes against
shared hub revision `4eb8d94e255fb6dc775160449940c459e0178f49`. It was not applied
there. No full suite, native browser, live provider or game check was run.

Rollback before integration is simply not to wire or apply this isolated
component. Any future integration must supply its own default-off rollout and
preserve the existing store and runtime rollback procedure.
