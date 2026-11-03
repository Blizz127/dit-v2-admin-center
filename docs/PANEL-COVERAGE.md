# Brief panel coverage — offline review, October 30

This tracks mock UI coverage, not live capability or completion of upstream
contracts. Review follows the nine features in BRIEF.md. Disabled writes remain
intentional; a synthetic UI must not silently activate them.

Reconciled for request `d23b693cabaa01a3`: the final column lists external
contracts/evidence still needed, not unbuilt mock UI or authority to fabricate
results. Row 1's additional offline presence-review slice is complete; rows 2
and 3 retain their contract holds. Continuing down the table finds producer or
measurement dependencies in rows 4–8 and completed offline wiring in row 9.
Native visual/keyboard/save verification remains separate for all rows.

| # | Panel | Existing offline surface | Remaining gap / next action |
| --- | --- | --- | --- |
| 1 | Bots, games, status | Roster filters, exact-ID inspector, ambiguity report and shared synthetic presence-review cases (`7a16041`) | Authoritative native identity, realm/instance scope and fresh presence observations are still missing. Offline review is implemented; live presence remains Unknown. |
| 2 | Per-bot controls | Goals/memory/personality inspection and bounded page-local draft review | Upstream bot-command contract and implementation remain unresolved. No start/stop/pause or draft-save route exists; mock POST remains 405. |
| 3 | LLM choice | Disabled per-bot/global selectors, scoped assignment examples and audit review | Compatible routing/write contract remains unresolved; examples never apply model changes. Controls remain disabled. |
| 4 | Call logging / bake-off | Exact model/purpose/source comparison, bounded finite means, expandable supplied samples, and an off-by-default offline evaluator snapshot import (`DIT_EVALUATOR_SNAPSHOT_FILE`) | No hub bake-off producer exists (hub lead, Nov 3). Evaluator export gaps: (a) run ID and input hash; (b) game/actor attribution; (c) time-to-first-token; (d) rubric name and evaluator version on scores; (e) delivery outcome and fallback eligibility; (f) any live or recorded runs. Live `attempts` has cost/tokens only. Building a producer is a hub-side decision. Imported rows are offline evaluator records, not a measured bake-off. |
| 5 | Action/evidence ledger | Exact scope/correlation filters and separate request/result/verification | Authoritative scoped execution and verification evidence must come from the producer; no synthetic row can close this dependency. |
| 6 | Kill switches/gates | Disabled controls and explicitly synthetic safety records | Authoritative live gate/switch observations and control contracts remain unresolved. Actual state stays Unknown. |
| 7 | Audit log | Local search, partial-data coverage and synthetic model-audit examples | A real admin-action audit producer is not connected. Loaded examples do not establish actual actions or their absence. |
| 8 | Learning/training | Needs/inventories, evidence checklist, draft assessment schema and fixtures | Hub assessment producer and scoped game/outcome evidence remain unresolved. Draft/schema tests are not live assessments. |
| 9 | Issues/risks | Document-backed inventories, filters and exact bot/task links in mock API and preview | Offline inventory wiring is complete. Reconcile authoritative new evidence when supplied; retain native-verification and producer gaps meanwhile. |

Panel 9 records are extracted from the explicitly marked JSON inventory blocks
in those two repository documents. The surrounding prose is not guessed into
incident status. Each document is bounded to 256 KiB, each inventory to sixteen
rows; missing/malformed/ambiguous inventories yield an Unknown coverage card
while the other document remains usable. All document rows state their source,
next verification step and unknown live-observation time. No row is mapped to a
bot based on its display name.

Validation: three Python tests (including an authenticated ephemeral localhost
mock with live collectors forbidden), one actual-app simulated-DOM filter check,
and seven artifact/markup/script checks passed. A localhost HTTP check is not a
browser rendering check. Native rendering, keys and saving remain NOT RUN.

Panel 4 now includes three fictional call samples for two example models in both
the local mock API and standalone preview. Mean supplied latency is descriptive
only; missing cost and quality are counted, not converted to zero or treated as
comparable evaluation scores. Missing identities are excluded from grouping.
A real bake-off remains dependent on agreed tasks, metrics and provider scope.

Panel 2 local drafts are mock-only, page-local and scoped to one unique roster
ID. Both fields are optional but at least one is required; blank is no proposed
change. Goals are bounded to 1000 characters and personality to 500. Control
characters and over-limit input invalidate and remove prior previews. Drafts
are cleared on inspect/selection change, refresh, discard and session reset.
No storage, request, save route, model change or bot command is connected.

A deferred failed-refresh test confirms draft text and preview clear when the
request starts, cannot be previewed during loading, stay cleared on failure,
and allow a fresh draft after a successful mock refresh. This is simulated DOM
evidence, not a native browser typing/focus check.

Panel 2 draft review now adds current/proposed columns with explicit text-change
states and field-level provenance. Unknown current data cannot become an empty
baseline or a verified change; duplicate bot-detail records withhold goal text.
Read-only review retains the existing draft lifecycle and has no apply button.
The review columns have a source-level narrow-width stacking check; native
rendering and keyboard behavior remain unverified.

Panel 4 numeric correction (`538ae44`): three finite `Number.MAX_VALUE` latency
samples previously rounded the sum of divided values to infinity and displayed
Unknown. A running mean now keeps finite nonnegative samples bounded. Focused
actual-app checks cover 3/9/11 equal maxima plus maximum/zero; existing missing
values, zero and scope grouping cases still pass. The rebuilt artifact passes
143 jsdom checks with zero transport attempts. This is a numeric display fix,
not a benchmark, live usage measurement or browser-verification claim.

Panel 4 sample review (`3f8362a`): each exact model/purpose/source group now has a
collapsed disclosure with the supplied observation labels, latency, cost and
quality for its rows. Missing values remain Unknown; row numbers are positions
within the group, not stable call identities. The existing numeric-availability
filter governs both means and sample tables. Refresh replaces the disclosures;
unavailable data clears them. Captions retain group provenance and explicitly
avoid verified freshness. Supplied strings are rendered as text. Tables have
scoped headers and a focusable horizontal scroll region for narrow viewports;
actual visual layout and native disclosure keyboard behavior are unverified.
No provider request, model selection, write control or export was added.

Panel 7 audit coverage (`7b39c48`): mixed lists retain usable object rows and
show an Unknown total. Malformed rows are omitted; missing fields within usable
rows still render Unknown. Search/reset are local and retain partial-coverage
warnings, including zero matches. An all-malformed list is not described as a
known empty log. Missing collections clear old rows; complete snapshots remove
the warning. These are loaded examples, not recorded admin actions.

Panel 3 assignment history (`d1a9e6f`): malformed/unscoped history rows no longer
hide usable rows explicitly keyed to the selected unique bot ID. Paging counts
only these usable matches; every partial page states that the loaded total is
Unknown. Other bots and blank IDs are withheld. Duplicate selected roster IDs
remain ambiguous and cannot display assignments. All-unusable/unavailable
collections clear old pages; complete recovery removes the partial warning.
No model assignments or control actions are issued.

Standalone preview diagnostics (`6cfad70`, `d21042b`) are injected only by the
artifact builder, not into the running Admin Center template. Overview and
assignment history have disclosures showing local check progress, bounded last
check text and elapsed time. Running, completed, check failure, five-second
no-progress timeout and ten-second total timeout are distinct; terminal states
cannot be changed by late progress. “Open check log” opens and focuses the
report. A timeout marks it INCOMPLETE. No bot/service stall, owner/device result,
trusted native input or successful file save is inferred from these views.

Row 1 presence review shares `data/fixtures/presence-examples.json` through the
mock overview and standalone snapshot. Cases explain roster-only status, old
observations and mismatched native identity. The UI accepts only a synthetic
envelope, withholds malformed cases, renders literal text and never associates
a case with the selected bot. Every case retains Live presence: Unknown.
This is explanatory review, not a new hub schema or evidence evaluator.

Row 3 write-contract preparation (`30b8f30`, `7e5c7cf`, `fdfccc1`) now has an
isolated in-process mock request/response interface over the existing routing
simulation. It exercises strict synthetic inputs, explicit target sets, version
conflicts, bounded idempotent retries and audit/readback. It is not registered
with the mock web server: actual HTTP POST remains 405 and UI controls stay
disabled. The hub contract/authority dependency in the table remains open.

Panel 4 offline evaluator snapshot import (task `f5a0a3ffa40b`): when
`DIT_EVALUATOR_SNAPSHOT_FILE` names a local JSON array exported by the hub's
`DialogueWordingHarness compare-fixture`, each record matching the source-pinned
`DialogueProviderEvaluationRecord` shape is appended to `modelCalls` as
`Provider / Model` with latency and caller-supplied cost. Purpose, quality,
observation time, run identity, attribution, rubric, delivery and fallback
eligibility stay Unknown; evaluator scores are listed but never become quality.
Records with renamed, extra or invalid fields are omitted and counted, never
repaired. The file is read with the bounded non-blocking, no-symlink reader; no
hub, token or network access is involved. Unset, nothing is read. This is an
import path that works under either open owner decision, not a choice between them. Snapshot rows appear in the call list but stay
out of the grouped comparison (counted as unattributed) because the export has no
purpose; none is invented.
