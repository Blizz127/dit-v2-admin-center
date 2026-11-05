# Synthetic candidate delivery harness

Local follow-up to the [context/voice candidate](../context-voice-compat-20261104/README.md).
No shared hub, bridge, game or device was changed. Live flags remain unchanged;
the held browser step was not run.

`export-test.patch` is test-only and applies after the exact isolated candidate
in `BASE_REVISION`. `TEST_REVISION` records the exporter source. It does not
replace or reapply the earlier combined runtime patch. No runtime code changed.

The four C# cases use the actual candidate group service with a fake provider
and status source for FFXI/SWTOR. Fresh status permits a wording decision;
status expiring during generation must suppress it without another provider
call. Exports contain actual returned decisions plus exact prompt/status
captures, preserving twelve turns and an intentional repeated line.

The Admin-side harness replays those pinned exports through bounded in-memory
publication and receipt queues. A separate worker issues a synthetic receipt;
the local verifier requires both issuance and receipt reception in a fresh
synthetic session for each run. A fabricated
copy of the issued receipt cannot pass before the receiver gets it. Withheld,
duplicate, altered and wrong-session receipts exercise the same correlator.
Candidate-withheld output starts no publication worker. The Admin API itself
still has no native verifier or replay operation.

Verification on 2026-11-05:

- Four focused C# candidate-export cases passed, zero skipped; the incremental
  test build succeeded without reported warnings/errors. See `candidate-tests.txt`.
- Eleven focused Python harness tests passed, including default-off/no-read,
  malformed/scope-changed export refusal, changed content pins, path refusal,
  worker failure cleanup and CLI behavior.
- The follow-up cross-run replay regression first reproduced acceptance of an
  old identical receipt under the original fixed synthetic session. A fresh
  per-run session now rejects it. This changes only the Python harness; the
  runtime candidate, C# exporter and fixture content remain unchanged.
- The opt-in CLI executes twelve synthetic cases with explicit assertions.
  Its saved receipt is `verification-summary.json`.
- No full suite, model call, live HTTP request, native game, native browser or
  device check was run. The C# tests directly invoke the service in process.

Commands, with the existing source checkout and prebuilt dependencies:

```sh
DIT_CANDIDATE_DELIVERY_EXPORT=/absolute/local/output /usr/bin/dotnet test tests/Dit.HumanBehavior.Neuronetwork.Tests/Dit.HumanBehavior.Neuronetwork.Tests.csproj --no-restore -m:2 -p:BuildProjectReferences=false -p:UseSharedCompilation=false --filter FullyQualifiedName~CandidateDeliveryFixtureTests
```

The actual run waited for load at most 40 and at least 40 GiB available memory,
used a 300-second deadline and 12-GiB GC limit, and cleared inherited `DIT_`
variables before setting the export directory. The conversation/status flags
were injected into the synthetic service only. No host configuration changed.

From the Admin repository:

```sh
python3 -m unittest tests.test_candidate_delivery_harness -v
python3 -m tools.run_candidate_delivery_harness --enable-offline
```

See the [harness guide](../../docs/SYNTHETIC-DELIVERY-HARNESS.md) for the exact
claim boundary and default-off operation. `Passed` establishes local synthetic
transport behavior only. Actual game delivery remains Unknown; verified native
presence, body identity and speech receipts remain producer dependencies.
The hub/native leads retain integration ownership and every existing hold.
