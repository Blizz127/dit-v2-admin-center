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
