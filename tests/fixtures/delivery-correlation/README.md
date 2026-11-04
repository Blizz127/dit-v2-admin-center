# Synthetic delivery correlation fixtures

`ffxi.json` follows the inspected FFXI decision/inbox field shapes. `swtor.json`
uses that shape only to exercise cross-game scope isolation; no SWTOR producer
contract is claimed. All names, bodies, epochs, times and receipt IDs are invented.

Each has two intentionally identical published sentences with different inbox
and observation IDs, one publication whose inbox row is absent, and a dropped
draft without a publication identity. The optional receipts are fabricated
`dit.synthetic-chat-receipt.v1` records. Without an injected fixture verifier,
none is confirmed; with it, only two synthetic matches appear. Actual delivery
stays unknown in every case.

These are not native logs, an authentication scheme, playback evidence or a
native delivery receipt. The source limits and local input shape are documented
in [the correlator note](../../../docs/DELIVERY-EVIDENCE-CORRELATION.md).
