# Captured candidate output for synthetic receipt checks

Four files were exported by the actual isolated group-conversation service with
a fake provider, fake status source, synthetic caller and in-memory store.
The runtime and exporter checkout is
`e55c7dc75d01d88c8fbc6866ff9aca04eed52055`. The exporter test introduced at
`2e063438` is unchanged; these files were regenerated on 2026-11-06 after the
wording serialization fix. Only the two request-ID fields in each export
changed from the previous captures. Prompts, history, status and decisions
remain identical. See the [refresh receipt](../../../handoffs/candidate-delivery-refresh-20261106/README.md).

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
