# Context/status compatibility with the newer chat voice candidate

Local isolated source candidate only. No shared checkout, running flag,
service, device, game, model provider or native source was changed.

## Why this follow-up exists

The original [producer context/status handoff](../producer-context-status-20261104/README.md)
passed a read-only application check against hub `1bc3ea41`. By committed hub
revision `3dd21dc7b57e141199a45b2aff31522a490c4df8`, later chat voice changes
overlapped `DialogueWordingPromptText.cs` and `ConversationService.Companion.cs`;
the original combined patch no longer applied directly. This is source drift,
not a failure of a deployed feature.

The new isolated checkout starts at that exact committed revision. The hub
lead's then-uncommitted `ShoutOriginTrace` work was excluded and left untouched.
No live or device artifact was read to construct this candidate.

## Merge choices

- Preserve the newer voice allowlist, actual FFXI say/linkshell wording channel,
  private tell scope, and existing FFXI/Forever shout exclusion.
- Add the bounded structured conversation and native-status candidate alongside
  those behaviors. Its flags remain separate and default off.
- Preserve `SuppressSharedVoiceGuidance` when status binding reconstructs a
  wording request. Without this, enabling status could drop the shout exclusion
  on a request whose legacy wording channel is `party`.
- Keep structured history/current text and the status binding on initial and
  rewritten requests. A rewrite must keep its correction as well.
- Include the earlier authenticated HTTP tests and the subsequent empty-context
  and unavailable-status fixture tests from isolated revision `925c1dc`.

No channel routing, producer field, status trust rule, delivery verifier or
history limit is expanded. Native presence/body mapping and real speech evidence
remain producer dependencies. Prepared text and inbox publication still cannot
prove delivered speech. The source-side shout diagnostic described by the hub
lead likewise does not provide an authenticated native delivery receipt.

## Verification

The isolated source revision is `67488a257c1fdedc1fd078ac7f1cf5769728284c`,
recorded in `ISOLATED_REVISION`. The patch includes runtime and test changes from
`BASE_REVISION`, including the prior HTTP test follow-up; apply it once.

- The initial seven-case regression run built successfully but **failed two
  cases**: shared status dropped shout protection for `ffxi` and `ffxi_forever`.
  The exact receipt is [verification-before-fix.txt](verification-before-fix.txt).
- After preserving the flag, **all 83 focused tests passed**, with zero skipped:
  context/status integration, current chat-voice routes, authenticated HTTP
  ingress and structured prompt/serializer behavior. The seven new cases cover
  initial and rewritten requests, 12 retained turns, channel context,
  status-off behavior and prompt receipts with/without voice guidance. See
  [verification-after-fix.txt](verification-after-fix.txt).
- Incremental compilation succeeded without reported warnings/errors. Restore
  used the existing local package cache and an empty local package feed; no
  package download or SDK installation was needed. Tests use fake wording and
  synthetic data; HTTP tests start only their disposable loopback host.
- The combined patch passed read-only `git apply --check` against the shared
  checkout at `0d762a4bd8f86ca92c12f32977e5dc7ce35ae736`. That later commit contains
  the hub lead's shout diagnostic. It was **not** part of this candidate's build
  or tests; application compatibility does not validate that later code.

The test command used the installed `/usr/bin/dotnet`, `--no-restore -m:2`,
`-p:UseSharedCompilation=false` and this filter:

```text
FullyQualifiedName~ConversationStatusIntegrationTests|FullyQualifiedName~ChatVoiceRouteFixtureTests|FullyQualifiedName~ConversationStatusIngressTests|FullyQualifiedName~StructuredConversationTests
```

The existing load/memory guard was observed before each heavy step, with a
300-second command deadline and 12-GiB GC limit. No full suite or live game/model
check ran. Native browser execution remains NOT RUN under the existing holds.

## Integration and rollback

The hub lead remains the sole integrator. Verify `SHA256SUMS`, then use
`combined-context-status-voice.patch` instead of the original combined patch and
its separate test follow-up; never apply both versions. Check it against the
integrator's exact current source before applying in
an isolated checkout, including any intervening source work. A clean patch check
alone is not build or runtime proof.

Both conversation allowlists remain unset. No producer registry or live source
registration is installed by this handoff. Rollback for a later separately
released integration remains the original plan: unset the conversation flags
and remove optional source registration, without changing native game data or
credentials. This handoff releases no live, player-protection or device hold.
