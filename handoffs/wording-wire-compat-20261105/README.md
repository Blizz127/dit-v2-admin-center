# Wording serialization compatibility addendum

Local source follow-up to the [context/voice candidate](../context-voice-compat-20261104/README.md).
The shared hub, bridge, running flags, games and devices are unchanged. Browser
validation remains held and NOT RUN.

The hub lead's `4f02b95571b417853c9d5ce0bf171ad169852ced` fixes loss of
`SuppressSharedVoiceGuidance` during wording-request serialization. This
addendum carries that exact runtime annotation into our older isolated
candidate and checks its interaction with status binding and rewrites. It does
not change a routing rule or introduce another suppression policy.

The new assertions serialize with `NeuronetworkJson`, deserialize the wording
request, and compare the full resulting prompt, request identity, current
message, twelve history turns and rewrite correction. They cover FFXI
linkshell/say/shout/tell, Forever shout, SWTOR party, and status-disabled FFXI
shout. Enabled suppression must be present and true; default false stays absent.
The existing route assertion is updated to match the upstream serialization
behavior.

Verification on 2026-11-05:

- Before the annotation change, the seven expanded integration cases built;
  three shout cases failed and four other channel cases passed. See
  `verification-before-fix.txt`.
- Afterward, those seven cases and eleven existing voice-route cases passed:
  **18 passed, zero failed or skipped**. Incremental compilation, including
  project references, succeeded without reported warnings/errors. See
  `verification-after-fix.txt`.
- These are in-process tests with synthetic data and a fake wording provider.
  No full suite, HTTP smoke, delivery-export refresh, native game, real model,
  browser or device check ran for this addendum.

The after-fix command used installed `/usr/bin/dotnet`, `--no-restore -m:2`,
`-p:UseSharedCompilation=false`, and the filter below. The before-fix run used
only the first filter term and added `-p:BuildProjectReferences=false` because
only tests had changed; the after-fix
run rebuilt references for the runtime annotation. Each run observed load at
most 40 and at least 40 GiB available memory, a 300-second deadline and a 12-GiB
GC cap. Inherited `DIT_` variables were cleared for the test process. No SDK,
package, configuration or service was installed or changed.

```text
FullyQualifiedName~Status_binding_and_rewrite_preserve_channel_voice_and_complete_context|FullyQualifiedName~ChatVoiceRouteFixtureTests
```

## Source application

`BASE_REVISION` is the previous isolated exporter checkout (`2e063438`), whose
runtime was `67488a25`. `ISOLATED_REVISION` is the tested follow-up (`e55c7dc7`).
`UPSTREAM_FIX_REVISION` records the hub fix used here.

Use the appropriate path once, in an isolated checkout:

- For the exact older candidate in `BASE_REVISION`, `candidate-wire-compat.patch`
  adds the runtime annotation and the two test-file changes. A temporary-index
  application reconstructed the exact `ISOLATED_REVISION` tree.
- A hub tree already containing the upstream fix needs no duplicate runtime
  annotation or route-test change. After the earlier combined context/status
  patch, `context-status-roundtrip-test.patch` adds only our integration
  assertions. This sequence applied to committed hub `174ab3c0` in a temporary
  index in our isolated repository; its wording model and integration test
  matched the tested candidate. That newer hub tree was **not built or tested**.

The complete hashes and source-only application receipt are recorded in
`SHA256SUMS` and `source-application-check.json`. The shared worktree and index
were never modified. The hub lead remains the sole integrator and must account
for subsequent source changes. A clean patch application does not establish
runtime or deployment compatibility.

## Evidence and rollback boundary

The [delivery harness](../candidate-delivery-harness-20261105/README.md) still
replays its original pinned `67488a25` output. Its four C# export checks,
eleven Python checks and twelve synthetic cases are not verification of this
new revision. No fixture or evidence pin was silently updated.

To discard this local addendum, retain the earlier isolated candidate and its
unchanged artifacts. In a future integration, keep the hub lead's serialization
fix when removing the optional context/status candidate. No live rollback is
needed here because nothing was installed or enabled. Native presence, body
mapping and delivered-speech evidence remain unresolved producer dependencies.
