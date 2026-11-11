# Judgment-call log

Standing order (Blizz via Devbox Coordinator task 06bc7b7ce847, 2026-11-10 8:05 PM CST):
reversible calls are made by the lane lead and logged here (what, why, how to undo).
Irreversible actions (git push, resets, restarts/deploys, routing/model swaps, lifting holds) still need Blizz.

| When (UTC) | Call | Why | How to undo |
| --- | --- | --- | --- |
| 2026-11-10 | Skipped the Opus `/advisor` audit before commits. | No such skill was available then; the owner's validation default says no routine review gates. Superseded 2026-11-11: an `advisor` tool is now available and is used before commits. | Run an independent review of any earlier commit range on request. |
| 2026-11-11 02:02 | No tracker change and no new build for FFXI `/fb` r84–r101. | The only new `/fb` packets (r97, r101) add Warrior gear, by their names; the cited command list is unchanged. FFXI live is still rc8. | Edit FFXI Forever p-08 in `data/fixtures/baseline-conformance.json` to cite r101 (7562eb70) and cut a build. |
| 2026-11-11 02:02 | Left the SWTOR p-04 cell at release kt although live was c87/lx. | Corrected 13:55Z: the 02:02 text search printed nothing, so it was inconclusive, not evidence. Superseded by the c127 check below. | n/a |
| 2026-11-11 13:55 | Updated SWTOR p-04 to cite live c102 client heal rows; built preview 69810fda. | Squad modules are byte-identical kt (c56) to c127, but `private_squad.py` takes `heal_amount` from `private_companion_roles`, which reads the client standard-healing row since c102 (switch `True` in c127). Other changed shared modules not traced. | Revert commit 8ae0267 and keep preview 7dc8b10f. |
| 2026-11-11 13:55 | Did not switch this session's model. | The session resumed on Opus 5.5 after the 05:41 CST restart; the owner set Fable 5.2 medium, and model changes are owner-only. Reported to the coordinator once. New commits carry the Opus 5.5 trailer. | Blizz or the coordinator restarts the lane on Fable 5.2 medium. |
| 2026-11-11 13:56 | Recorded preview 69810fda as prepared, not delivered. | `ssh alienware-bazzite` timed out; no polling, per standing policy. | Deliver the same folder when Alienware is reachable, or let a later build supersede it. |
