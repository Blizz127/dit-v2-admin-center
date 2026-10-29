# Imported synthetic candidate fixtures

Copied byte-for-byte from `dit-human-behavior-platform` commit `b9e404e`
(following `a311fd3`), directory `tools/ffxi/interaction_admin`, on 2026-10-29.
Nine snapshots, the route-check record and MANIFEST are from its `fixtures/`
directory; input and consumer pins and `UPSTREAM-README.md` preserve provenance.
No live data, real credentials or runtime artifacts are included.

Run from the Admin Center checkout:

```sh
timeout -k 3 20 python3 -m unittest discover -s tests -p test_interaction_contract.py -v
```

The existing test harness passes all nine snapshots through the current reader,
projection and cache using an in-memory HTTP response and forbidden sockets.
It validates snapshot hashes before use. It needs neither the sister checkout
nor .NET. The original handcrafted fixture remains useful for malformed values
and privacy canaries.

`consumer-pins.json` records the hub lead's tested consumer versions; it does
not freeze our implementation or replace tests of current code. The original
MANIFEST also references harness files that remain upstream. `route-check.json`
is historical in-process authorization evidence, not a local authorization test
or a deployed HTTP check. Commands and relative paths in UPSTREAM-README refer
to the upstream repository; no regeneration is part of this import.

For a future refresh, explicitly review the source revision, generator and input
pins, import matching artifacts, and review expected semantics before accepting
changed hashes. Neither fixture success nor accepted receipts prove game action
delivery. r10 lacks this endpoint; deployed revision remains unverified. Model
controls remain off.
