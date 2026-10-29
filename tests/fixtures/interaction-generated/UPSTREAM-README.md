# Candidate FFXI interaction fixtures for Admin Center

These synthetic JSON files were produced by the unchanged e8c81be
`InteractionAdminApi` source using the cached offline interaction library.
They are not captured from a live hub or game. The route is absent from the
source-reviewed r10 contract; these checks do not inspect a deployed revision.

The C# harness maps only `/v1/control/interaction` and invokes its request
delegate directly with `?limit=50`. GET-only route metadata, Admin acceptance
and anonymous/Adapter/invalid-token rejection are checked without opening a
listener. Literal fixture credentials exist only in memory. This is not a
test of the deployed HTTP stack, proxy or separate admin listener.

`RuntimeStub.cs` supplies only the group property read by this endpoint. The
normal runtime is never constructed because it schedules provider warmup.
No conversation, model provider, token file, database, game transport or service
is used. Synthetic snapshots and reports populate only in-memory interaction
objects. Each read checks that observable snapshots, state counts, action views
and ledger counts remain unchanged; this does not prove every internal field
immutable or test concurrency. No switches outside the fixture are changed.

## Fixtures

| File | Meaning |
| --- | --- |
| `contract-off-empty.json` | Collection off, no prior state. |
| `contract-on-empty.json` | Collection on but no game state supplied. |
| `fresh-snapshot.json` | Reconciled and raw snapshot freshness both true. |
| `fresh-snapshot-superseded-view.json` | A newer accepted receipt supersedes a one-second-old snapshot without proving current activity: raw snapshot freshness is true, reconciled freshness is false. |
| `fresh-mode-stale-snapshot.json` | A fresh native mode report makes activity current while the raw snapshot is 100 seconds old; raw capabilities remain absent. |
| `stale-mode-and-snapshot.json` | Neither evidence is current; raw hub activity is `unknown`. |
| `contract-off-retained.json` | Collection off after state existed; the hub retains history, which the UI must not present as current inventory. |
| `same-actor-distinct-scopes.json` | The same actor key under three caller/server scopes must remain three separate records. |
| `limit-50-truncated.json` | The explicit 50-bot request truncates a larger inventory. The hub itself has a higher default/max; 50 is the consumer's fixed request. |

`route-check.json` records the in-process authorization check.
`MANIFEST.json` binds outputs to harness and input hashes. `input-pins.json`
pins endpoint/token source, interaction source references and cached assembly
dependencies. The cached library also contains separate offline provenance
changes; this is not a fresh e8c81be release build or a deployable artifact.

## Consume without a hub request

`test_consumer.py` imports the three hash-pinned, read-only Admin Center modules
from `/home/blizz/dev/dit-v2-admin-center` (override with
`DIT_ADMIN_CENTER_CHECKOUT` if that checkout moves). It feeds the JSON files to
the actual projection, checks scoped identities and redaction, verifies the
fixed request arguments with a replaced transport, and checks preservation of
the original fetch time across the 15-second cache. Cache checks use only a
temporary fixture token file and a fake loader. No network is used.

```
timeout -k 3 25 env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/ffxi/interaction_admin -p test_consumer.py -v
```

The UI projection deliberately converts stale raw `activity: "unknown"` to
null. Its `source: "native snapshot"` still names the raw snapshot even when a
newer mode makes `fresh` true. Off or unknown collection yields no current
inventory. Missing fields, raw orders, requesters, receipts and state counters
must not be inferred from that projection. Model controls stay off.

## Regenerate only when needed

The small harness compiles with .NET 10, two build workers, a 4 GiB managed-heap
limit and bounded build/run subprocesses; it does not rebuild the solution.
Inputs must match the pins, and output must be a new directory. Build failures
produce no fixture bundle. Use fresh capacity measurements before compiling.

```
timeout -k 5 70 python3 tools/ffxi/interaction_admin/generate.py --output /tmp/dit-interaction-fixtures-new
```

Generation and seven consumer checks passed on 2026-10-29 UTC after correcting
the harness's ASP.NET implicit imports and its stale-activity test expectation.
No live endpoint availability, native identity, gameplay outcome, provider
authorization or activation is established. Existing holds remain unchanged.
