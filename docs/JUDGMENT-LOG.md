# Judgment-call log

Standing order (Blizz via Devbox Coordinator task 06bc7b7ce847, 2026-11-10 8:05 PM CST):
reversible calls are made by the lane lead and logged here (what, why, how to undo).
Irreversible actions (git push, resets, restarts/deploys, routing/model swaps, lifting holds) still need Blizz.

| When (UTC) | Call | Why | How to undo |
| --- | --- | --- | --- |
| 2026-11-10 | Skipped the Opus `/advisor` audit before commits. | No such skill is available here; the owner's validation default says no routine review gates. Full suite is run instead. | Run an independent review of any commit range on request. |
| 2026-11-11 02:02 | No tracker change and no new build for FFXI `/fb` r84–r101. | The only new `/fb` packets (r97, r101) add Warrior gear, by their names; the cited command list is unchanged. FFXI live is still rc8. | Edit FFXI Forever p-08 in `data/fixtures/baseline-conformance.json` to cite r101 (7562eb70) and cut a build. |
| 2026-11-11 02:02 | Left the SWTOR p-04 cell at release kt although live is now c87/lx. | A text search of release notes after kt found no bot mention. | Add the c87 live time to the p-04 evidence and cut a build. |
