# Captured scope inspector: private preview release

Released **b57a9d3** to the existing Alienware private preview path. Independent
remote readback verified all five file hashes, byte counts and modes at
**2026-11-08T05:43:57.414657Z**. Open
`Downloads/DIT-Conversation-Overview-20261104-11735c60/Conversation-Panel-b57a9d3/Start-Here.html`.
This is a changed offline owner preview, not a deployed hub/server or game client.
The separately queued `9c99e01a` hub intake remains unchanged and was not repeated.

## Changed behavior

The actual inspector now displays Requested bot scope separately from Native
body in capture: game, requested/server instance, actor key, realm, native actor
ID and session epoch. The actor key and native body ID legitimately differ;
realm and instance are also distinct. These labels describe the supplied
capture, not verified native ownership or current presence.

A new simulated-DOM regression reproduced the old acceptance of a body with
the wrong game. The display now applies the existing API contract's exact
lookup/game, body/game and requested/body-instance equalities. Required scope
strings are nonblank and bounded to 128 UTF-16 units without normalization.
Malformed bindings clear the previous packet. Missing-source captures retain
the requested scope and conversation without inventing a native body. Snapshot
unavailable retains its expected body binding while current fields stay Unknown.

Synthetic scope conflict mutates only a cloned response, leaving the original
exports and delivery examples intact. Projected or unavailable-with-view cases
change Body.Game; null-view cases change Lookup.Game. Loaded restores the
original capture. The earlier presence-conflict scenario remains available.

## Verification and release

Seven focused Python checks passed: four artifact cases, authenticated localhost
startup, authentication-before-read, and the existing request/digest/scope
contract check. Three actual-app simulated-DOM scripts then passed against the
built artifact: scope, existing context/presence, and delivery evidence. Cases
cover both games, 22 malformed scope/binding variants, exact separate identity
display, missing-source history, stale-result suppression and corrected loads.
No full suite, browser, live model or native game check was run. Existing native
browser/device ownership and actual access denials were not bypassed.

The HTML is 285,480 bytes, SHA-256
`130da88c7353aca10a12f66b59d68b35dec9e742987e6e977506b7ef8abc18ec`.
Source revision: `b57a9d381a8ab8d3e550afa25af488972e61df7c`.
The exact source is embedded; fixture inputs remain pinned, with networking
blocked by the existing stub and CSP. The adjacent receipt lists all five
package files. Directory/file modes are 0700/0600. Existing strict-host-key,
batch SSH delivered a new exclusive folder without a prompt, new access,
service restart, browser launch, game mutation or credential change.

Rollback: close the new files and optionally remove only the new versioned
folder. `Conversation-Panel-69ab75f` and earlier videos/previews remain intact.
No duplicate copy of the unchanged static delivery page was made.

## Ownership and continuation

Root reused `/root/admin_context_truth` for disjoint preview-builder/test work
and `/root/native_boundary_review` for read-only contract review. Both completed;
neither ran builds, tests, commits, device commands or deployments. Root alone
integrated, checked and published the private preview. Fresh CPU/memory/I/O
pressure is retained with the test result; work stayed sequential and light,
without a retired global admission lock or compiler fanout.

The existing shared hub/native publishers retain their respective ownership.
Their already-dispatched integration is not a local acknowledgement gate.
Native realm/body/presence feeds and authenticated speech observations remain
unverified producer dependencies; these new display labels cannot supply them.
