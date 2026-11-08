# Captured prompt coverage: private preview release

Released **bd3a4f9** through the existing Alienware private preview path.
Independent remote readback verified all five hashes, sizes and modes at
**2026-11-08T06:06:24.953673Z**. Open
`Downloads/DIT-Conversation-Overview-20261104-11735c60/Conversation-Panel-bd3a4f9/Start-Here.html`.
This is an offline owner preview, not a deployed hub/server or game client.
The already-queued `9c99e01a` hub intake was not modified or repeated.

## Changed behavior

The actual context inspector now shows a Captured prompt receipt card with
serialized UTF-16 character count, its 24,576-unit application cap, and the
supplied prompt SHA-256. Token count and earlier producer omissions remain
Unknown. This cap does not measure the provider's token capacity or establish
that a model saw or understood the packet.

A new simulated-DOM regression reproduced the old display of 13/12 retained
turns. The UI now refuses invalid or inconsistent supplied/included/omitted
counts, count/history-length disagreements, excessive or malformed history,
blank prompt strings, character-count disagreement, an unexpected cap and
invalid digest shape. Valid omissions, repeated lines, supplementary Unicode,
zero-history and missing-native-source captures remain inspectable.

These browser checks are intentionally narrower than Python validation. They
check arithmetic, units, bounds and digest format; they do not recompute SHA-256
or compare every retained prompt line. The existing Python reader performs
those additional checks. Neither layer establishes native provenance.

Synthetic coverage conflict changes only a cloned retained-turn count to exceed
the supplied count. Original captures, prompts and delivery examples remain
unchanged. Loaded restores the original response, including empty-intent cases.

## Verification and release

Eight focused Python checks passed: five artifact cases, localhost startup,
authentication-before-read and the existing request/digest/scope contract case.
Four actual-app simulated-DOM scripts passed against the built artifact:
coverage, scope, context/presence and delivery. Coverage cases exercise both
games, invalid counts/history, valid omission, preserved repeats, 32 turns of
512 UTF-16 units, supplementary Unicode counting, the inclusive 24,576-unit
cap, empty intent and missing native source. No full suite, native browser,
live model, game or actual native producer check was run.

Source revision: `bd3a4f9f9590b881e2950f33263aca6ad19634a1`.
HTML: 286,965 bytes, SHA-256
`23bf6ae0cbfc19ece46cd39db4a364e6e670587e813e4fc38458db39dc77af3f`.
The artifact embeds the exact application and pinned fixture inputs; existing
CSP and fixture stub block networking. The receipt lists all five package files.
A new exclusive folder was delivered through existing strict-host-key, batch
SSH without a prompt or access change. Directory/file modes are 0700/0600.
No service, browser or game was started or changed.

Rollback: close the new files and optionally remove only this new versioned
folder. The `b57a9d3` preview and earlier videos/previews remain available.
No duplicate copy of the unchanged static delivery page was made.

## Ownership and continuation

Root reused `/root/admin_context_truth` for the disjoint preview-builder/tests
scope and `/root/native_boundary_review` for read-only receipt-contract review.
Both completed; neither ran builds/tests, commits, network or device actions.
Root alone integrated, checked and published this preview. Fresh pressure is
recorded with the focused Python result; all execution stayed sequential and
light, without compiler fanout or a retired admission lock.

The current documented local inspector visibility gaps (presence, scope and
captured prompt receipt) are now closed. No additional concrete unbuilt local
inspector item was identified in this pass; do not create empty releases or
repeat completed checks to satisfy a timer. The next consequential work is the
existing hub integration and verified native presence/speech producers, through
their current owners. Producer coverage receipts and any transport expansion
remain separately documented integration decisions, not claims made by this UI.
New owner feedback, authoritative captures or a scoped assignment can supply
the next local increment; no discretionary project pause is introduced.
