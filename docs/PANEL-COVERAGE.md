# Brief panel coverage — offline review, October 30

This tracks mock UI coverage, not live capability or completion of upstream
contracts. Review follows the nine features in BRIEF.md. Disabled writes remain
intentional; a synthetic UI must not silently activate them.

| # | Panel | Existing offline surface | Remaining gap / next action |
| --- | --- | --- | --- |
| 1 | Bots, games, status | Roster filters, coverage, exact-ID inspector and ambiguity report | Live presence remains Unknown without authoritative evidence. |
| 2 | Per-bot controls | Goals, memory and personality inspection; bounded local goal/personality draft preview; disabled command controls | Writes require upstream contract; no start/stop/pause is implemented here. |
| 3 | LLM choice | Per-bot/global disabled selectors; requested/effective distinctions | Model switching stays disabled; mock audit examples do not apply changes. |
| 4 | Call logging / bake-off | Loaded model-call examples, numeric coverage and filters | Local comparison groups loaded samples by exact model/purpose/source, preserves numeric coverage and shares the availability filter. No measured benchmark or provider calls. |
| 5 | Action/evidence ledger | Exact scope/correlation filtering, request/result/verification, Unknown outcomes | Live action verification needs source evidence. |
| 6 | Kill switches/gates | Disabled controls and synthetic safety records | Current live state remains Unknown; no control routes. |
| 7 | Audit log | Searchable examples and scope/outcome model-audit filters | No real admin actions or write audit claimed. |
| 8 | Learning/training | Needs, dataset/policy inventory examples and evidence checklist | Authoritative assessment producer and game evidence unresolved. |
| 9 | Issues/risks | Scope/status/search, bot/task links and historical observations | Now includes curated records from LEARNING-AND-ISSUES.md and NATIVE-VERIFICATION-GAP.md in mock API and standalone preview. |

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
