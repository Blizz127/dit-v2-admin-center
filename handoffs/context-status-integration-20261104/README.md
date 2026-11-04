# Conversation + shared status integration (offline)

This candidate integrates the two earlier source proposals inside an isolated
hub build. It does not modify the shared hub worktree or any live game.

## Enabled behavior

`DIT_CONVERSATION_CONTEXT_GAMES` selects structured history independently of
`DIT_CONVERSATION_STATUS_GAMES`, which selects status binding. Each is an exact,
case-insensitive comma-separated game allowlist; both are unset by default.
Unselected games retain their existing behavior and do not call the status source.

Companion replies (including rewrites), heard-line replies and social intent
requests use the same `IConversationStatusSource` boundary and projector. The
source must be explicitly registered in process. It returns the authenticated
caller mapping plus an atomic expectation/cursor, snapshot and expiry policy
from the existing ordered store. The source is not supplied by an HTTP request,
chat line or bot. No production adapter source is registered by this candidate.

The enabled path replaces current-body facts with the projection. Old loose
location/activity/job/level facts and the old verified-live-state trigger cannot
remain as competing truth. Explicit reference facts and the native guide outcome
are retained; the latter keeps its existing no-extra-consultation route. Other
legacy facts require a typed provenance mapping before adoption. This is a
conservative migration tradeoff, not a claim to preserve all legacy context.

Each field includes its known/stale/unknown state. Only known fields carry a
value. Unknown activity never becomes idle. Source failures and scope mismatches
produce unknown status instead of falling back to old body facts. Source error
text is withheld from prompts. Each new attempt rereads the source and clock.

After successful wording, the service rereads the bound status before returning
the result. Changed identity/epoch, regressed sequence, changed known values,
expired fields, source failure or a disabled flag withholds the line without
another model call. A newer snapshot with the same still-fresh field values can
proceed; ordinary heartbeats do not silence every reply. The original receipt
continues to describe the prompt actually sent. This check is not a native
delivery acknowledgement or a substitute for the adapter's final validation.

`StatusBindingFor(request)` exposes the exact immutable status view used by that
request, bound to the recomputed request ID. It can be paired with the actual
wording serializer's context receipt. This adds neither a live Admin endpoint
nor a persistent log. The weak association lasts while the request is retained.

## Rollout and rollback

1. Apply the combined patch in an isolated checkout of the pinned base. The
   delta patch instead follows both earlier candidates; do not apply both forms.
2. Keep both flags unset for the first build/startup check. Register only an
   authenticated, scoped source with explicit per-field expiry policy. No native
   IDs, realms, epochs or observation times may be invented from display names.
3. For synthetic FFXI/SWTOR checks only, set both allowlists to `ffxi,swtor` and
   inspect the actual captured provider prompts and their matching status bindings.
4. Runtime adoption stays with the DIT integrator, with the existing source,
   access, spending, active-player and release holds. This patch grants no live
   flag change, game call, model call or deployment. Real producer mappings and
   natural conversation quality remain unverified.
5. Roll back the candidate behavior by unsetting both allowlists and returning
   to the legacy path. Unregister the injected source when no requests use it.
   No persisted status or game data is migrated. Retain the existing binary
   rollback procedure for any future integrated build.

Native membership/action checks and delivery acknowledgements remain owned by
the game/adapter. Prompt capture is not delivery evidence. No native browser,
real provider or live owner playtest is part of this offline check.

## Reproduce focused validation

```sh
dotnet test tests/Dit.HumanBehavior.Neuronetwork.Tests --filter 'FullyQualifiedName~ConversationStatusIntegrationTests|FullyQualifiedName~ConversationStatusProjectionTests|FullyQualifiedName~StructuredConversationTests|FullyQualifiedName~FfxiRecentContextTests|FullyQualifiedName~FfxiSurroundingsPromptTests'
```

Set `DIT_INTEGRATION_FIXTURE_OUTPUT` to an empty local directory to capture six
synthetic FFXI/SWTOR prompts (companion, heard, intent). The tests execute those
service paths with a fake provider and compare against the actual DeepSeek JSON
serializer, without HTTP. The captures are saved in `tests/fixtures/context-status-integration`.
Prompt hashes, matching request/status IDs, retained turn counts and bound status
revision strings were independently checked in all six captures. These checks
prove internal consistency, not producer authenticity or model understanding.


Final validation, 2026-11-04: **92 focused tests passed**, zero failed/skipped.
The component build completed with zero warnings/errors. The final incremental
build reused already-built dependency outputs; the first integration run built
through the normal project graph. Six service/serializer fixture paths passed.
No full suite, HTTP hub startup, native browser or real provider/game test ran.

`git diff --check` is clean. The combined patch passes a read-only
`git apply --check` against shared hub revision
`189e6cc8fb424d3aa3f7cfdea801cc2ab3d242e4`; it was not applied there. Both patch
hashes are in `SHA256SUMS`. Original source base is recorded in `BASE_REVISION`.

## Offline inspector preview

The Admin artifact builder pairs each captured request with its own status view:

```sh
python3 -m unittest tests.test_integrated_context_preview -v
python3 tools/build_integrated_context_preview.py tests/fixtures/context-status-integration/*.json --output build/context-slice/Integrated-Context-Preview.html
```

Six focused Python checks cover the six actual captures, mismatched request or
prompt digest, scope mismatch, unavailable/expired status falsely marked known,
invented live/delivery claims, field omissions and escaped display metadata.
The generated static HTML makes no network requests. It checks artifact
consistency and explicitly does not authenticate producer evidence. No live
Admin route or native browser check is added.
