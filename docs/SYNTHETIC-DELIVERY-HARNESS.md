# Candidate output and synthetic receipt transport

This harness connects captured output from the isolated context/status candidate
to an in-memory fake publisher, observer and receipt receiver. It does not
establish native speech, native status authenticity, client display, or model
quality. Browser/device checks and all live flags remain held and unchanged.

## Boundaries exercised

1. `CandidateDeliveryFixtureTests` invokes the actual candidate group-conversation
   service for FFXI and SWTOR with twelve history turns, a fake wording provider,
   in-memory storage and an injected synthetic status source. The source binds
   a fictional body/epoch and is checked again after generation.
2. The test exports the actual returned decision and its exact prompt/status
   capture. Fresh status produces one wording decision. Status expiring during
   the fake provider call must produce silence, not a publishable draft.
3. `tools/run_candidate_delivery_harness.py` validates those saved exports with
   the existing capture validator. It assigns a **synthetic** inbox sequence to
   publishable output and sends serialized bytes through a bounded worker queue.
4. The fake observer issues a receipt for the exact synthetic body/session/text.
   Before the receipt is received, even an exact copy of that issued receipt
   fails the run-local verifier. Releasing the receipt sends serialized bytes
   back through a separate bounded queue. Each observer run has a fresh
   synthetic session identifier, so identical bytes from an earlier run cannot
   certify a new publication. This identifier is not a native credential.
5. The existing correlator accepts a synthetic match only when the receipt was
   both issued and received in this run and its publication bindings match.
   Duplicate receipt packets count once. Withheld, altered and wrong-session
   packets cannot produce a synthetic confirmation. Expired candidate output
   never starts a publication worker.

The worker queues and verifier are test components, not proposed native wire
interfaces or authentication. The synthetic clocks label events; they are not
latency measurements. This is playback of pinned candidate output, not a live
hub connection. No receipt-ingress endpoint, persistent delivery ledger, native
observer, automatic resend, conversation-history update or new credential is
implemented. The Admin loader continues to supply no receipt verifier.

Read-only inspection of runtime candidate `67488a25`,
`Conversation/Arbitration/GroupChat.cs`, shows an additional history boundary:
its legacy pair store is updated when wording is prepared, before native
publication. With structured context enabled, the candidate takes history from
the supplied room lines and excludes those unscoped legacy pair turns. Receipt
reception in this harness does not alter either source. The caller must still
supply properly scoped observed conversation; a synthetic receipt pass does
not prove that subsequent live prompts contain only delivered speech.

## Run locally

```sh
python3 -m tools.run_candidate_delivery_harness
python3 -m tools.run_candidate_delivery_harness --enable-offline
python3 -m unittest tests.test_candidate_delivery_harness -v
```

The first command returns Disabled without reading exports or starting a
worker. The opt-in command exercises five transport cases plus the candidate
status-refusal case for each game. `Passed` means its explicit local invariants
held; it never means a game delivered a line. Failure to validate or complete
the bounded transport returns Unavailable and exit status 2. It reads only the
four named committed synthetic exports and writes no evidence or game state.
It does not discover or consume later C# export directories. The handoff
describes the separate candidate-export step and the deliberate repinning
required before testing newly exported content.

Every report retains `evidenceKind: synthetic`,
`nativeDeliveryVerified: false`, `deliveredInGame: null` and
`replayAuthorized: false`. Actual delivery in each correlated row stays Unknown,
including after a successful synthetic receipt. Missing receipts do not prove
silence or failed delivery.

## Verification and remaining dependencies

Four focused C# candidate-export cases and eleven Python harness checks passed
again on 2026-11-06. The saved exports now use runtime/exporter checkout
`e55c7dc7`, including the wording serialization fix. The exporter test itself
is unchanged from `2e063438`. The [refresh handoff](../handoffs/candidate-delivery-refresh-20261106/README.md)
records the exact pin, test receipts, reviewed fixture differences and
twelve-case CLI result. The harness verifies
all four exports against its fixed manifest before starting any transport;
changed content or unexpected file names are refused. These local hashes are
not a native authentication mechanism.

The [wording serialization addendum](../handoffs/wording-wire-compat-20261105/README.md)
has separate focused checks at that same isolated revision. Its historical
receipt and the [original harness handoff](../handoffs/candidate-delivery-harness-20261105/README.md)
remain unchanged; the refresh explicitly replaces the fixture pins rather
than relabeling their earlier results. This refresh adds synthetic transport
evidence for `e55c7dc7`, not native delivery evidence.

A follow-up replay regression initially failed: the fixed synthetic session ID
allowed a previous run's identical receipt to pass. Fresh per-run session IDs
correct that behavior; the regression now rejects the replay while retaining
Unknown actual delivery. The candidate runtime and exported fixtures did not
change for this harness-only fix.

The owning native integrators must still supply authenticated body/session
identity, explicit presence and native speech evidence. This harness cannot
satisfy those dependencies with fabricated data. The
[provenance proposal](CONVERSATION-TURN-PROVENANCE-PROPOSAL.md) and
[native producer mapping](NATIVE-STATUS-PRODUCER-MAPPING.md) remain the source of
those open requirements. Native-browser validation remains NOT RUN.

Rollback is to omit `--enable-offline` and stop using the test artifacts. No
running process, production configuration, native save or stored schema changes.
