# Release resume: owner preview and prepared-reply memory fix

Owner message `2c41e771389e7f0d` lifts discretionary project policy pauses.
This handoff records actual resumed work, with two distinct results.

## Released private owner preview

`owner-preview-receipt.json` records the six-file Alienware release and separate
hash/mode readback at **2026-11-08T00:44:20.452381+00:00**. Source is Admin
`4fa9e59529ea011e17fc3c31edd1b90a98f1e174`; the package is under
`Downloads/DIT-Conversation-Overview-20261104-11735c60/Conversation-Panel-4fa9e59`.
Open `Start-Here.html` there. The release contains the interactive Admin context
and delivery panel plus eight static delivery-evidence scenarios, all synthetic.

Four focused Python preview/CLI tests and two simulated-DOM scripts passed
before packaging. The existing private, strict-host-key, batch SSH route was
used; no new access, native prompt, browser launch, service restart, credential
change or game mutation occurred. Earlier previews and the video are unchanged.
This is a private owner-preview release, **not** a deployed server/game client,
native-browser pass or proof of real game delivery. Rollback is to close the
files and optionally remove only the new folder.

## Source candidate: do not remember a prepared reply as speech

The existing GroupChat companion path calls `CompanionSaid` before returning
its generated decision. That method records “I said” in bot memory, updates
claims and relationship usage, and journals speech. The next prompt can recall that
draft even though no native publication or speech receipt exists. Excluding
legacy pair turns from structured history did not close this separate memory
path.

`candidate.patch` applies to isolated base `e55c7dc7`; `ISOLATED_REVISION` pins
the resulting source candidate. For games selected by the existing
`DIT_CONVERSATION_CONTEXT_GAMES` flag, the normal companion decision path now
skips `CompanionSaid` and outgoing `Pairs.Said`. Arbitration cooldown still
reserves the selected turn. Supplied observed history remains intact, including
repeated lines. Flag-off calls retain the original effects and their order.

No native receipt API, inferred confirmation, replacement trust source or
memory cleanup is added. Old stored memories are not rewritten. Other decision
paths are outside this focused fix. Actual observations must still come from
the native producer; this change does not supply the missing native provenance.

Four synthetic regression cases are written for FFXI/SWTOR with the flag on
and off. They generate a reply without publication/receipt, inspect persisted
memory and pair turns, then check the next request's memories and supplied
history. Existing observations remain visible; the unpublished draft must not
become “I said” in the selected path. Source review found no compile/API issue;
that review is not compilation evidence.

**Build NOT STARTED; tests NOT RUN.** The existing capacity guard refused the
single focused .NET job at load 64.67 (maximum 40), with 135.77 GiB available
(minimum 40). No compiler fanout or background wait remains. `verification.json`
records the exact intended filter. The next useful action is that focused run
under the shared heavy-work budget: installed dotnet, no restore, a 300-second
deadline, 12-GiB GC cap, inherited `DIT_` variables cleared, one job. Do not
publish this uncompiled source candidate as a tested runtime build.

The separate c301c99 delivery fixtures remain pinned to e55c7dc7; they were not
regenerated or relabeled as evidence for this newer source.
The packaged patch was applied to e55 in a temporary index owned by this
isolated checkout and produced the exact candidate tree. That verifies patch
packaging only, not compilation or behavior. Source rollback is to revert this
increment in the isolated checkout; no live rollback is needed for unshipped
runtime code.

## One intake for the existing hub integrator

This supersedes the old *hold/wait* next-step language for the context/status
candidate. It adds this incremental patch to the existing
`context-voice-compat-20261104` and `wording-wire-compat-20261105` source handoffs;
their source pins, past test results and prerequisites remain historical facts.
Apply only in the owning integrator's isolated checkout after its prior context
candidate. Run the narrow filter above when capacity permits. The integrator
retains the only live hub writer/publisher; this Admin lane has not changed the
shared hub/bridge worktrees or any live flags.

Independent producer inputs are still missing: authenticated native
realm/body/session mapping and explicit presence with epoch/revision/freshness,
plus speech observations bound to exact attempt/text/body/channel/thread. A
configured display label or synthetic receipt cannot supply that authority.
Admin live control reads also still lack an authorized read-only credential;
do not substitute the hub administrator token. These are concrete technical
and access boundaries, not restored project-policy pauses.
