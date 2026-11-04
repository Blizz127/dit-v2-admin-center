# Conversation inspector: pending native-browser check

Status: **NOT RUN**. Prepared 2026-11-04 for the cross-game context work.
The current Admin implementation is `dc52281`. The integrated preview was
delivered to Alienware under `Integrated-Preview-153855b`; copying and hashing
that file did not launch a browser or validate rendering.

This checklist does not resume the blocked browser step. Devbox's missing
browser and denied namespace operation remain binding. The earlier Alienware
executor stopped before browser launch because prerequisites were missing from
PATH. Do not rerun its older pinned package for this new feature. Device
execution stays with the designated device lead and its existing holds.

## Inputs and isolation

- Record the exact Admin revision, browser executable/version, operating system,
  viewport and zoom, UTC start/end, artifact SHA-256, and each fixture SHA-256.
- Use the existing installed browser and a disposable profile only when the
  device step is released. No downloads, installs, sandbox changes, occupied
  profile, cookies, credentials, game access, or real provider calls.
- For static layout review, use
  `build/context-slice/Integrated-Context-Preview.html` (or its independently
  hashed delivered copy). It contains six synthetic FFXI/SWTOR captures, has
  no scripts or network requests, and does not test the Admin fetch handlers.
- For actual Admin panel interaction checks, build the dedicated fixture:

  ```sh
  python3 -m tools.build_context_capture_playtest
  sha256sum build/context-slice/Context-Panel-Playtest.html
  ```

  It embeds the unchanged current application plus all six validated captures.
  Its fixture `fetch` cannot call the network, polling is disabled, and CSP
  explicitly blocks connections. Open this file only on the released device
  step. No server, token file or normal collector is needed. The generic older
  inspector preview has no context-capture response; do not substitute it.
- The fixture's token and HTTP-error response are synthetic. File parsing and
  authentication remain separate automated localhost checks, not browser claims.

## Static preview review

1. At 1280 and 390 CSS pixels, then at 200% zoom, read all six captures.
   Confirm headings, field states, prompt text and hashes remain readable;
   long prompt text stays inside its own scroll area without hiding controls.
2. Compare each displayed request ID, status binding, prompt SHA-256 and
   retained-turn count against its exact fixture. All six current captures
   retain 12/12 turns; that is synthetic fixture evidence, not live-game proof.
3. Confirm FFXI and SWTOR captures retain their own body identity, epoch and
   instance. Unknown/stale fields show no old activity/location value.
4. Tab through links and native disclosure controls, activate with Enter/Space,
   and inspect visible focus, readable labels and scroll behavior. Record
   observed behavior; CSS declarations and simulated DOM tests do not prove it.

## Interactive Admin review

1. Select **Not configured** in the fixture response selector. Confirm the panel displays **No offline capture configured** after its load button is pressed.
   Loading a capture is explicit and independent of roster selection.
2. Select **Loaded** and load each of the six exact fixtures. Check 12/12 turns, matching request and
   status identity, source policy/revision, and exact system/user prompt text.
   Verify **synthetic**, **no model call** and **no delivery** remain visible.
3. After a successful load, select **Unavailable**, **Invalid field**, then
   **HTTP error fixture**, pressing the panel load button each time. Every error
   must remove the previous prompt/body values. Return to **Loaded** and verify
   recovery. Changing the fixture selector alone must not reload the panel.
4. The actual parser/authentication checks are reproduced separately with
   `python3 -m unittest tests.test_context_capture -v`: truncated/oversized JSON,
   wrong shape, missing file, recovery, authentication-before-read, query and
   write refusal. Attach that receipt separately. The browser fixture does not
   prove HTTP authentication or filesystem behavior.
5. Select **Delayed response**, click load, then **Reset panel session**, then
   **Release delayed response**. Old results must not reappear. Use the normal
   refresh control to reopen the workspace as needed. A second ordinary load
   must work after reset.
6. Inspect exact prompt rendering as text, not executable markup. The invalid
   field marker `BAD_WITHHELD_VALUE` must never appear as an approved fact.
   Record the network panel: no request may leave the file. The error selector
   simulates an HTTP error and makes no HTTP request.
7. Repeat keyboard, narrow viewport and zoom checks on the real panel. Verify
   loading/status text is announced as applicable; do not call screen-reader
   behavior passed without actually using one.

## Receipt and remaining limits

Record a separate **PASS / FAIL / BLOCKED / NOT RUN** for every step, attaching
screenshots only where permitted and useful. Record exact console/network
errors without secrets. A blocked launch is not a failed feature assertion or
a pass. A static review does not pass the interactive section.

Existing evidence: 12 focused Python capture/preview checks, simulated-DOM
panel checks, and authenticated localhost startup/API smoke passed at
`dc52281`. Those checks do not establish native rendering, real producer
authenticity, model understanding or chat delivery. The FFXI v1 producer lacks
explicit presence; SWTOR native status wiring remains a producer dependency.

Rollback for a future released interactive check: close only its disposable
browser profile and retain the receipt. No capture environment variable is set
by the standalone fixture.
The hub's conversation flags and all live game processes remain unchanged.
