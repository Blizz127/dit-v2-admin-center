# Producer context and native status: isolated candidate

This extends the earlier offline context/status integration. Nothing was
applied to the shared hub or game/bridge worktrees. No flags, live services,
credentials, device sessions or model providers were changed.

`combined-producer-context-status.patch` applies to the original archived hub
base in `BASE_REVISION` and includes the earlier candidates. `producer-delta.patch`
instead follows the integration candidate at private revision
`f6f09ed8d01648da48293c3812af5e47598329c3`. Apply one form, not both.
The final isolated source commit is recorded in `ISOLATED_REVISION`.

## Result and limits

- The shared C# client uses structured conversation history/current message
  when its game is selected by `DIT_CONVERSATION_CONTEXT_GAMES`. All 12 fixture
  turns survive reply, group and event transport for FFXI and SWTOR, including
  repeats. The existing wire limit remains 16: over-capacity input keeps the
  newest whole turns and reports supplied/prepared/omitted counts through the
  existing optional callback. A prepared packet is not a successful send.
- The existing FFXI ordered store can feed the projector through an explicit
  trusted body registry and authenticated caller scope. Reads preserve native
  observation/ingress times and refuse superseded full snapshots. They neither
  ingest nor dispatch. JSON cannot supply the internal caller scope.
- The v1 FFXI wire still lacks explicit presence, so this adapter supplies no
  known current body facts. A trusted realm/native-ID mapping is also required;
  none is configured by default. The SWTOR native source remains unavailable.
  These are producer dependencies, not permission to infer status from chat.
- The conversation flags stay unset by default. The native source also checks
  the existing interaction-contract switch; it does not enable that subsystem.

See the [producer mapping and rollout note](../../docs/NATIVE-STATUS-PRODUCER-MAPPING.md)
for exact field/identity dependencies and rollback. The existing hub/game leads
retain integration and runtime ownership, including all player-protection,
source, spending and release holds. This does not demonstrate improved live chat.

## Verification

Completed 2026-11-04 on the isolated source:

- Neuronetwork, Hub and Client incremental component builds: zero warnings/errors.
- **130 core/client tests passed** in the focused 137-test run. Its seven HTTP
  tests were blocked during startup by the shared host's inotify instance limit.
- The synthetic HTTP host was changed to use its temporary content root and
  disable unnecessary configuration reload watching. No host limit or security
  setting changed. **All seven HTTP tests then passed** in a separate focused
  run: group/reply/event caller binding for adapter versus Admin, forged JSON
  caller ignored, unauthorized/wrong-game refusal, and flag-off no-source-read.
- The source tests include actual ordered-store ingestion, newer native reports,
  reconnect/duplicate clocks, concurrent ingress/read coherence, absent identity
  mapping, unsupported SWTOR source, and conservative unknown presence.
- The client tests use an in-memory HTTP handler; no model/game/remote HTTP call
  occurs. Authenticated route checks start only a disposable loopback hub with
  a fake wording provider and synthetic tokens/data.
- Earlier test-setup errors (invalid synthetic native action ID, policy-object
  equality, reflection argument count and a null required test field) were fixed.
  Do not cite those failed attempts as passes.

The focused filter used was:

```sh
dotnet test tests/Dit.HumanBehavior.Neuronetwork.Tests/Dit.HumanBehavior.Neuronetwork.Tests.csproj --filter 'FullyQualifiedName~FfxiConversationStatusSourceTests|FullyQualifiedName~ConversationStatusIngressTests|FullyQualifiedName~ConversationStatusIntegrationTests|FullyQualifiedName~InteractionContractTests|FullyQualifiedName~ConversationProducerContextTests|FullyQualifiedName~HubOnlyWordingTests'
```

Actual incremental commands used `--no-restore -m:2`,
`-p:BuildProjectReferences=false -p:UseSharedCompilation=false`, prebuilt dependency
outputs, a 300-second deadline and a 12-GiB GC limit. Each heavy step waited until
load was at most 40 and available memory at least 40 GiB. No full suite ran.

The final combined patch passed a **read-only** `git apply --check` against
shared hub revision `1bc3ea41a00fdb90333940e89bd273b774acd2a7`.
It was not applied there. `git diff --check` is clean.

## Admin/browser preparation

Admin commit `a7d7e59` supplies a network-blocked standalone panel preview and
the [native-browser checklist](../../docs/CONTEXT-NATIVE-BROWSER-CHECKLIST.md).
Fourteen focused Python checks, the simulated-DOM panel check and authenticated
localhost capture smoke passed. The fixture embeds the unchanged panel code
and six existing synthetic integration captures; it does not authenticate a
native producer. It can exercise loaded, unavailable, invalid and delayed states.

```sh
python3 -m tools.build_context_capture_playtest
```

Native browser execution remains **NOT RUN** under the recorded device/namespace
restrictions. No artifact from this step was launched or deployed on Alienware.
The earlier overview video and integrated preview deliveries remain unchanged.
