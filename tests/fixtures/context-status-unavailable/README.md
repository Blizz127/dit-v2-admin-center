# Synthetic unavailable-status packets

These four captures come from the actual `ConversationService.CompanionRequest`
builder and DeepSeek serializer in the isolated hub candidate. They use a fake
clock, synthetic history and an injected source; no provider/game/network call
or delivery occurred. Request IDs, prompt hashes and status bindings describe
the same built request. They are not hand-edited copies of a successful packet.

| Capture | Bound state | View |
| --- | --- | --- |
| `ffxi-missing.json` | source unavailable | null |
| `ffxi-error.json` | source read failed | null; source exception text withheld |
| `ffxi-binding.json` | source binding mismatch | null |
| `ffxi-gap.json` | snapshot unavailable | scoped expectation/policy, no source/revision, all fields unknown |

The test-only export change is `export-test.patch`, following isolated producer
revision `d15786e9d7191554829367909005a29afbab3838`. Its commit is
`2b23f81c3d879b8b37ee36c3fe7483d91900f52f`. It changes no runtime code and is
separate from the already packaged producer candidate.

Reproduction in that isolated checkout:

```sh
DIT_STATUS_FAILURE_FIXTURE_OUTPUT=/absolute/path/to/output dotnet test tests/Dit.HumanBehavior.Neuronetwork.Tests --filter 'FullyQualifiedName~Status_failure_or_disconnect_never_falls_back'
```

All ten focused failure/disconnect cases passed in the capture run. Four of
them export the packets here. A fresh run may produce different request IDs;
regenerate input fingerprints when intentionally replacing these captures.
`SHA256SUMS` pins this captured set and its export source patch.
