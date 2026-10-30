# Brief panel coverage — offline review, October 30

This tracks mock UI coverage, not live capability or completion of upstream
contracts. Review follows the nine features in BRIEF.md. Disabled writes remain
intentional; a synthetic UI must not silently activate them.

| # | Panel | Existing offline surface | Remaining gap / next action |
| --- | --- | --- | --- |
| 1 | Bots, games, status | Roster filters, coverage, exact-ID inspector and ambiguity report | Live presence remains Unknown without authoritative evidence. |
| 2 | Per-bot controls | Goals, memory and personality inspection; disabled command controls | Writes require upstream contract; no start/stop/pause is implemented here. |
| 3 | LLM choice | Per-bot/global disabled selectors; requested/effective distinctions | Model switching stays disabled; mock audit examples do not apply changes. |
| 4 | Call logging / bake-off | Loaded model-call examples, numeric coverage and filters | Add local comparison of loaded examples; no measured benchmark or provider calls. |
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
