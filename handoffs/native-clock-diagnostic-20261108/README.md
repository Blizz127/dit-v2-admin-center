# Captured native timing diagnostic

Source `8166a4a8150b5c4667f5f6c239bce4dc667c5335` addresses the coordinator's
bounded Admin display/validation inspection assignment. The existing API
exports observation times and validity deadlines, but the UI previously omitted
them. Existing FFXI/SWTOR captures give presence a 60-second deadline and
location/activity 10 seconds, so packet read time alone hid a useful distinction.

Each field now shows its supplied observation and validity deadline, marks its
state as at captured read, and uses Unknown (not supplied) for absent clocks.
Live native status is explicitly Unknown. No current-clock aging, producer
attestation or promotion of withheld values is performed. Unknown fields may
retain clocks without regaining their values. No retained capture, producer,
shared hub, device browser or runtime flag was changed.

The new DOM assertions first failed against the prior application because the
explicit live-status Unknown card was absent. After the fix, the artifact-bound
script passed with both games and existing offline/unknown/stale/error fixtures,
including recovery and session clearing. Four focused Python checks passed:
exact application/capture embedding, CSP/script validity, authenticated localhost
startup and authentication-before-read. All logs and fresh host pressure are
attached. Native browser, real model/game and actual producer validation were
NOT RUN. No full suite or compiler fanout was used.

Two existing helpers were reused for read-only UI and validator audits; both
completed. Root alone edited, integrated, tested and packaged this increment.
The UI audit identified no additional concrete display defect. The validator
review noted a separate source-level concern: direct standalone validate() only
parses field clocks in Known branches, whereas the API additionally parses every
non-null clock. Stale expiry consistency is also not enforced there. This was
not reproduced by execution and is not changed or presented as verified by this
display fix; no new native freshness contract is inferred. Preserve nullable
Unknown clocks in any later scoped validator work.

## Private artifact

HTML SHA-256: `92470858811d06ccc59ba493db786046e17f41f0a0050e3122d9c9b26a84aad3`
(287,362 bytes). Package contains five files. Transfer timed out after 45 seconds without a completion receipt. The single
read-only follow-up failed with `ssh: connect to host alienware-bazzite port 22:
Connection timed out` (exit 255), recorded at 2026-11-08T06:36:15.629133Z.
At that original attempt, delivery was UNCONFIRMED; no remote hashes or
destination presence were observed. The bounded continuation below records the
newer read-only destination evidence, but still no completed delivery.
The earlier bd3a4f9 remains the latest verified private preview. No blind write
retry was performed. See owner-preview-attempt.json.
The prior bd3a4f9 preview is retained for rollback. The existing 9c99e01a hub
intake was not repeated. No server or game-client deployment is claimed.

## Continuation

This scoped diagnostic increment is implemented and locally checked. Publication
is unable to complete because the existing Alienware SSH endpoint is unreachable;
this is not a discretionary project hold or an approval request. Package:
`build/releases/conversation-panel-8166a4a/`. Intended destination:
`/home/blizz/Downloads/DIT-Conversation-Overview-20261104-11735c60/Conversation-Panel-8166a4a`.
When the existing route is reachable, inspect that directory before any write:
the timed-out attempt may have left no, partial or complete files. Verify exact
hashes before claiming release; do not duplicate the version or blindly overwrite.
No build/test/transfer job remains. Existing native integration and device
validation still belong to their respective owners. No new publisher or intake.

## Bounded delivery continuation, 2026-11-08 07:30Z

The owner-authorized continuation supplied retained evidence of a later
successful SSH retrieval by the Forever lead and authorized one fresh preflight
through the same strict-host-key/BatchMode route. No trust, credential or route
was changed. All five local package hashes and sizes still matched the seal;
no candidate, capture, build or test run was repeated.

The single read-only preflight succeeded at **07:30:32.069137Z**. The exact
`Conversation-Panel-8166a4a` directory was **absent**; its existing parent was a
writable directory. Therefore no matching remote file was rewritten. One
bounded completion transfer was attempted, using exclusive directory/file
creation for the same five-file package. Its SSH connection failed with:

`ssh: connect to host alienware-bazzite port 22: Connection timed out`

Exit **255**, recorded **07:31:04.784948Z**. No remote write completion was
observed. Per the explicit stop-on-unreachable instruction, no further SSH
preflight, transfer or readback was attempted. The final five-file readback was
**NOT RUN**, and delivery remains **UNCONFIRMED**. `bd3a4f9` remains the latest
verified private delivery; its files were untouched. No browser/client launch,
Arena diagnostic interaction, native/game action, new publisher or hub intake
occurred. This attempt is stopped on the actual endpoint failure, with no job
remaining. The two continuation receipts are attached.
