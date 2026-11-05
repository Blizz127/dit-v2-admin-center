# Captured candidate output for synthetic receipt checks

Four files were exported by the actual isolated group-conversation service with
a fake provider, fake status source, synthetic caller and in-memory store.
The runtime source is `67488a257c1fdedc1fd078ac7f1cf5769728284c`; the test-only
exporter revision is `2e063438b7f84c16c45e6fac58c1c6ff176fa1d2`.

For each of FFXI and SWTOR, `fresh` returns one `say` decision and `expired`
returns silence after status expires during generation. The captured prompt
records the earlier status read, not a current presence guarantee. Twelve
input turns include an intentional repeated sentence. The legacy reply mode
`live` belongs to this in-memory test and does not describe a running game.

`manifest.json` pins the canonical JSON content of all four exports. The harness
checks every pin before starting a worker and cannot select extra paths from the
manifest. `SHA256SUMS` separately records exact file bytes, including whitespace.
These local pins are provenance records, not native authentication.

See the [harness guide](../../../docs/SYNTHETIC-DELIVERY-HARNESS.md) and
[test-only handoff](../../../handoffs/candidate-delivery-harness-20261105/README.md).
No model, game, browser, native transport or real credentials were used.
