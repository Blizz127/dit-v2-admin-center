# Empty conversation input captures

These synthetic FFXI and SWTOR intent packets were produced by the actual
`ConversationService.WordIntentAsync` path with a fake provider, then checked
against the actual DeepSeek serializer. Their context has no history/current
player message, so the serializer correctly emits no recent-conversation
section. Their status source is absent and all native fields remain unknown.

No model/game/remote call or delivery occurred. Both focused export cases passed.
The test-only export source is isolated revision
`7798788ca2a7aa3a32005f91aa30df04b48bc284`; `export-test.patch` follows
`2b23f81c3d879b8b37ee36c3fe7483d91900f52f`. Runtime source is unchanged.

To reproduce in that isolated checkout:

```sh
DIT_EMPTY_CONTEXT_FIXTURE_OUTPUT=/absolute/path/to/output dotnet test tests/Dit.HumanBehavior.Neuronetwork.Tests --filter 'FullyQualifiedName~Empty_intent_context_is_a_valid_packet'
```

Fresh captures may have different generated request IDs. `SHA256SUMS` pins
this captured set and the test source delta. Zero captured input turns does
not establish that no conversation existed upstream.
