# Offline delivery evidence correlation

The owner wants conversation history to reflect which messages actually reached
chat. This local consumer joins synthetic decision and inbox records and
exercises a separate native-receipt boundary. It does **not** establish live
delivery, define an accepted native contract, or alter any hub, bridge or game.

## Existing evidence and the remaining gap

Read-only source inspection of the FFXI bridge candidate establishes these
field meanings:

- `dit.chat.decision.v1` / `v2`: `game`, `scope`, `channel`, and each reply's
  `actor_key`, `bot`, `text_final`, `verdict`, `inbox_seq`.
- `inbox.jsonl`: `seq`, `ts`, `channel`, `actorKey`, `bot`, `text`, optional
  `replyTo`. Publication uses an atomic replacement and the bounded inbox keeps
  only recent rows.
- `sent` or `trimmed` plus a matching inbox sequence/content establishes a
  publication match within the supplied capture. It does not establish native
  chat display. Missing/rotated logs do not establish absence or failure.

Inspection pin: bridge checkout `4fe1ac1477065d49b17b9b59aaeb81366cd32ef0`,
`tools/ffxi/ai_only/ffxi_chat_bridge.r12-candidate.py` SHA-256
`eb703d020b466b73778806d7d46496d57189abdeac9ad25a95d0f282c4174505`.
This is candidate source evidence, not a runtime readback. No real chat log was
collected. SWTOR fixtures use the same field shape solely as a synthetic
cross-game example; an actual SWTOR native log/receipt contract is still missing.

The bridge lane already owns `queue_metrics/DeliveryView` and
`SyntheticDelivery`, which distinguish prepared/queued and fabricated delivery
receipts. This work neither repeats that ledger implementation nor edits or
invokes it. It adds an Admin-side, read-only join of supplied log records. The
inspected modules' SHA-256 values were
`262bf56aa49698eee75b29b6251b67f6912e1b4be0f481a1391ff564741eed3e`
and `a612838f34cc59dd02f94ddcc358c5fd0fa892f7abea37f4471914cac6c2d7e4`.

## Local input and output

`delivery_correlation.py` defaults to disabled and performs no file read or
verification in that state. An enabled file read is bounded to 256 KiB, rejects
duplicate JSON keys, oversized/deep/truncated JSON and leaf symlinks, and never
writes the input. At most 256 decision rows, inbox rows, receipts and correlated
attempts are accepted. Invalid capture structure returns `Unavailable` with no
records or counts; malformed/nonmatching receipts are counted as rejected.

The local wrapper is `dit.delivery-correlation-fixture.v1`, with `synthetic:true`,
an explicit scope and bridge session, and arrays named `decisions`, `inbox` and
`receipts`. It accepts no file paths embedded in the JSON and scans no log
directories. One bundle describes one actor/thread. Its scope contains game,
realm, instance, thread, channel, actor key, native body ID and body epoch.
These are asserted **fixture** bindings; a manifest cannot authenticate them.
The legacy logs alone do not supply all these fields or a durable native turn ID.

Publication matching requires sequence, actor key, bot label, channel and exact
final text. Text equality alone never correlates messages. A repeated sentence
with two different sequences remains two attempts. Identical duplicate records
do not inflate counts; conflicting records under one sequence withhold a result.
Conflicting publication records also withhold wording/name, rather than letting
their input order choose a sentence for the inspector.
Drafts without a sequence are labelled by their capture positions, which are
not promoted to native identities. A dropped draft is not evidence that no other
attempt or message reached chat.

The optional **synthetic-only** receipt shape is `dit.synthetic-chat-receipt.v1`:
receipt/observation IDs, the same complete scope and bridge session, inbox
sequence, SHA-256 of exact UTF-8 final text, native observation time and receipt
time. It is a fixture shape, not a deployed producer API. A callback supplied by
the offline caller must return exactly `True` for immutable receipt data.
Self-declared `trusted` fields have no effect. No verifier is present by default.

Only a matching publication, identity, epoch, text and noncontradictory timing
can produce `fixtureConfirmation: Synthetic match`. Receipt/observation ID
collisions or multiple observation identities for one publication produce a
conflict. Arrival order never replaces native observation time. The tool does
not reorder the transcript or claim a global chronology across producers.

Every output, including a synthetic match, retains:

```json
{"evidenceKind":"synthetic","nativeDeliveryVerified":false,
 "deliveredInGame":null,"replayAuthorized":false}
```

Every row's `actualDelivery` stays `Unknown`. Counts describe supplied records
only; zero fixture confirmations is not zero actual deliveries. There is no
durable receipt store, resend, model call, native action, memory update, server
endpoint, polling, environment configuration or production toggle.

## Run the bounded offline checks and preview

From the Admin repository:

```sh
python3 -m unittest tests.test_delivery_correlation tests.test_delivery_correlation_preview -v
python3 -m tools.correlate_delivery
python3 -m tools.correlate_delivery --enable-offline --capture tests/fixtures/delivery-correlation/ffxi.json
python3 -m tools.correlate_delivery --enable-offline --simulate-native-receipts --capture tests/fixtures/delivery-correlation/swtor.json
python3 -m tools.build_delivery_correlation_preview
```

The simulation option fabricates verifier authority and is restricted to the
synthetic input format; it never upgrades the actual-delivery fields. CLI exit
2 means invalid arguments or unavailable input. Errors do not echo the file
path or its contents. The preview is static HTML, blocks connections, embeds no
script, and includes source/fixture hashes. It is built locally, not copied to
or launched on Alienware. The [browser checklist](CONTEXT-NATIVE-BROWSER-CHECKLIST.md)
contains seven ready-to-run cases; execution remains NOT RUN under existing holds.

Initial verification at `0273b68` on 2026-11-04: all 14 focused tests in the two test modules
passed, including duplicate/conflict and scope cases, file corruption/recovery,
CLI default-off behavior and escaped static output. The preview was built with
SHA-256 `247a31e9ccd9f545cbf071967eddef6d20257c6cdf56f324640209ea04e31991`.
This is artifact/source validation, not a browser run. No full suite or live
producer check was run for this addition.

The wording-conflict follow-up passes 15 focused tests, including reversed
record order. Its seven-section preview SHA-256 is
`3cba663047bd39fb42306b2755882d737bdd3be2db88f1d3f2672c42c3440e15`;
conflicting publication wording/name is withheld. Native browser remains NOT RUN.

## What a real integration still needs

The owning integrators must supply authenticated native speech observations,
verified body/session/thread identity, stable message/attempt references,
receipt provenance and coverage/recovery rules. A successful inbox rename or
matching text in an unbound chat log cannot substitute. Private-room visibility
and cross-game identity rules apply before any conversation history update.
See the [turn provenance proposal](CONVERSATION-TURN-PROVENANCE-PROPOSAL.md).

This component is local analysis only. Rollback is simply to omit its offline
opt-in and stop using the generated artifact; no persistent game state or
runtime service changes. The sole integrator, active-player protection,
source/access/spending and native-browser holds are unchanged.
