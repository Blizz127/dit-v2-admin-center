# Inspector presence consistency: private preview release

Released **69ab75f** to the existing Alienware private preview path; independent
remote readback verified all five files at **2026-11-08T05:17:02.451238Z**.
Open `Downloads/DIT-Conversation-Overview-20261104-11735c60/Conversation-Panel-69ab75f/Start-Here.html`.
This is a changed offline owner preview, not a deployed hub/server or game client.
The separately queued hub candidate `9c99e01a` was not redispatched or modified.

## Changed behavior

The actual Admin context inspector previously accepted Known/offline presence
alongside known location/activity. A new simulated-DOM regression reproduced
that contradiction before the source fix. The display now follows the shared
API validator: body fields must be Unknown unless presence is Known/online.
Known presence accepts only online/offline. Exact field identities and order
prevent duplicate, missing or rearranged fields from bypassing the rule.
Invalid captures clear the prior packet; valid offline/stale/unknown presence
with unknown body details still retains captured conversation history.

The standalone preview adds **Synthetic presence conflict**. It mutates only a
cloned fixture response, preserving the original captures and delivery examples.
Missing/unavailable captures use an explicitly invalid response shape instead
of invented native status. Choose an ordinary FFXI or SWTOR capture, load it,
select the conflict and load again, then return to Loaded to recover.

## Verification

- Six focused Python checks passed: three preview/artifact cases plus localhost
  startup, authentication-before-read and contradictory-presence API refusal.
- Both actual-app simulated-DOM scripts passed against the built artifact:
  context/presence consistency and delivery-evidence behavior. These include
  both games, valid unknown-status history, invalid field identities, clearing,
  recovery and session-race suppression.
- Two intermediate Node attempts hit the fixture harness's five-second Python
  startup timeout before assertions. Their failed results remain adjacent.
  Test-only commit `72ea428` extends that local fixture helper budget to thirty
  seconds. No production/application deadline or assertion was relaxed. The
  final two scripts completed; no failed attempt is counted as a pass.
- The artifact embeds the exact application and builder from source
  `69ab75f3d4153680c377c60d4ffd3377f295c5c2`; the verification revision differs
  only in that helper deadline. The existing CSP and stub refuse network access.
  No full suite, native browser, live model or game check was run.

The panel HTML is 284,250 bytes with SHA-256
`d302c6043ce602e5b8e100851d2c615f9ed4f3b93271d64e02851fa3108e197f`.
The release metadata and independent readback receipt list every package file.
The new directory is 0700 and files 0600. Existing strict-host-key, batch SSH
was used; no native prompt, access change, service restart or browser launch
occurred. Existing video, previews and all game/server data were unchanged.
Rollback is to close the new files and optionally remove only the new versioned
folder; `Conversation-Panel-4fa9e59` remains available.

## Ownership and continuation

Root reused `/root/admin_context_truth` for the disjoint preview-builder/tests
scope and `/root/native_boundary_review` for read-only delivery preparation.
Both completed; neither ran builds, tests or device commands. Root remained the
sole integrator and private-preview publisher. The shared hub/native owners
retain their own integration/publication boundaries. This follow-up changes
no hub flags, native body mapping or delivery authority. The existing hub intake
is already queued; no acknowledgement is a gate and it must not be duplicated.
