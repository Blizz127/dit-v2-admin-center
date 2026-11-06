# Synthetic delivery evidence refresh

The saved delivery fixtures now match the isolated candidate containing the
[wording serialization fix](../wording-wire-compat-20261105/README.md).
`ISOLATED_REVISION` pins both runtime and exporter checkout to `e55c7dc7`.
No runtime source, exporter logic, shared worktree, live flag or device changed
for this refresh. The browser check remains held and NOT RUN.

On 2026-11-06, four existing `CandidateDeliveryFixtureTests` cases passed with
zero failures or skips. The incremental build included project references and
reported no warnings/errors. The command and resource guard are in
`candidate-tests.txt`. Testing started only after load fell to 38.18, below the
existing maximum of 40, with 132.80 GiB available, above the 40-GiB floor. The
run used installed dotnet, no restore, a 300-second deadline and a 12-GiB GC
cap. Inherited `DIT_` variables were cleared; fixture flags were injected only
inside the synthetic service.

The output directory was explicitly reviewed and copied into
`tests/fixtures/candidate-delivery`. `fixture-delta.json` records the comparison:
only the matching request IDs in the context receipt and status binding changed
in each of the four files. Every other JSON value, including prompts, history,
status, returned text and expiry refusal, was identical. The harness runtime
pin, manifest content hashes and fixture byte hashes were deliberately updated.
The exporter source originally added at `2e063438` is unchanged.

The existing eleven Python checks passed against these refreshed exports; see
`python-tests.txt`. The opt-in CLI passed twelve synthetic scenarios across
FFXI and SWTOR; `verification-summary.json` records the new revision and hashes.
Default-off behavior, receipt reception, duplicate handling, corruption,
cross-run replay rejection and candidate expiry refusal remain covered. This
refresh adds no new transport or receipt endpoint.

These results use an in-memory store, fake provider/status source and synthetic
receipt worker. Actual delivery remains Unknown. No full suite, real model,
HTTP, native game, browser or device check ran. Native presence, body/session
identity and speech evidence remain unresolved producer dependencies.

The [original harness receipt](../candidate-delivery-harness-20261105/README.md)
retains its earlier `67488a25` runtime and `2e063438` exporter evidence. The
serialization addendum's earlier statement that fixtures were not refreshed
describes its own checkpoint; this new receipt supersedes that limitation.
Neither earlier test result has been relabeled. To revert this evidence
refresh, restore the fixture set, manifest and harness pin together from
Admin commit `6efe1fc`; simply omit `--enable-offline` to leave the harness
disabled. There is no live rollback action.
