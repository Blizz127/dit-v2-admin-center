# Conversation inspector: pending native-browser check

Status: **NOT RUN**. Prepared 2026-11-04 for the cross-game context work.
The initial Admin implementation was `dc52281`; the current fixture records
the exact application and capture input hashes. The integrated preview was
delivered to Alienware under `Integrated-Preview-153855b`; copying and hashing
that file did not launch a browser or validate rendering.

Owner message `2c41e771389e7f0d`, delivered 2026-11-08, lifts the discretionary
browser/project hold. Devbox still has no installed browser executable and its
earlier namespace operation was denied. Those are concrete runtime/access
limits, not a reason to stop other work or install/bypass isolation. The older
Alienware attempt stopped before browser launch; a separately sequenced attempt
was already dispatched after a reported PATH repair. Do not replay either old
package for this feature. Native execution stays with the existing device lead;
no native check is claimed by building or privately delivering a preview.

## Inputs and isolation

- Record the exact Admin revision, browser executable/version, operating system,
  viewport and zoom, UTC start/end, artifact SHA-256, and each fixture SHA-256.
- Use the existing installed browser and a disposable profile through the
  designated device owner. No downloads, installs, sandbox changes, occupied
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

  It embeds the unchanged current application plus six ordinary, four unavailable-status and two empty-context
  captures from the actual hub prompt builder/serializer, and two synthetic
  delivery-correlation reports with no native verifier.
  Its fixture `fetch` cannot call the network, polling is disabled, and CSP
  explicitly blocks connections. The designated device owner can use this
  exact file for the new check. No server, token file or normal collector is needed. The generic older
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
2. Select **Loaded** and load each of the twelve exact fixtures. Check 12/12 captured input
   turns on the ordinary/unavailable cases and 0/0 on empty intents, matching request and
   status identity, source policy/revision, and exact system/user prompt text.
   Verify **synthetic**, **no model call** and **no delivery** remain visible.
   Missing-source, source-read-error and binding-mismatch captures must retain
   their prompt while showing unknown fields and no invented body/revision. Empty intent packets must
   remain inspectable despite having no recent-conversation section.
   The sequence-gap fixture must show snapshot unavailable with its actual
   policy and no native observation values or revision.
   Inspect **Requested bot scope** separately from **Native body in capture**:
   the actor key and native actor ID legitimately differ. Compare the exact
   game, requested/server instance, realm, native actor ID and session epoch
   with the fixture. Missing-source captures show the requested scope but no
   invented native body. A sequence-gap capture retains its expected body
   binding while all current field values remain Unknown.
   Check **Captured prompt receipt** against the fixture's serialized character
   count, maximum and supplied prompt SHA-256. Units must say UTF-16 characters
   and token count must remain Unknown. Captured turn counts do not measure
   history omitted earlier by the producer or the model's available token window.
3. After a successful load, select **Unavailable**, **Invalid field**, then
   **HTTP error fixture**, pressing the panel load button each time. Every error
   must remove the previous prompt/body values. Return to **Loaded** and verify
   recovery. Changing the fixture selector alone must not reload the panel.
   Also select **Synthetic presence conflict** for an ordinary FFXI capture,
   then a SWTOR capture. This deliberately changes only a cloned response to
   offline presence while retaining body facts; the context panel must clear
   and report unavailable. Delivery evidence must remain unchanged. Missing
   or unavailable captures use an explicitly invalid response shape, without
   inventing a native source. Return to **Loaded** to recover the unchanged
   original capture. This is an error-handling fixture, not a new native export.
   Repeat with **Synthetic scope conflict**. It changes only the cloned body's
   game (or requested game for an unbound capture). The context panel must
   clear and report unavailable for either game, while delivery evidence stays
   unchanged. Returning to **Loaded** must recover the original scope/history.
   Repeat with **Synthetic coverage conflict**, including an empty-intent
   capture. Its cloned retained count exceeds the supplied count, so the context
   panel must clear and report unavailable. Loaded must recover the original
   receipt; delivery evidence must stay unchanged.
4. The actual parser/authentication checks are reproduced separately with
   `python3 -m unittest tests.test_context_capture -v`: truncated/oversized JSON,
   wrong shape, contradictory native facts, missing file, recovery, authentication-before-read, query and
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
8. Use **Load configured delivery evidence** with a FFXI capture selected, then
   a SWTOR capture. Expect four recorded attempts, two publication matches,
   zero synthetic native matches and actual delivery Unknown. Verify the exact
   game/body/thread scope. Roster selection must not change the captured scope.
   The receipt-evidence card must show two rejected or unverified receipts and
   explain that the Admin loader has no native verifier. This count does not
   establish failed game delivery.
9. Repeat Not configured, Unavailable, Invalid field, HTTP error and Delayed
   response/Reset/Release for the delivery button. The invalid fixture falsely
   claims native verification and must be refused. Every failed load clears old
   wording; delayed results cannot reappear after reset. There is no confirm or
   replay control. The separate API test is
   `python3 -m unittest tests.test_delivery_capture_api -v`; this fixture does
   not prove authentication, real file reads or native receipts.

## Receipt and remaining limits

### Prepared delivery-evidence preview

This is a separate static read-only artifact, not the interactive Admin loader.
Build it locally with `python3 -m tools.build_delivery_correlation_preview` and
record the SHA-256 of `build/context-slice/Delivery-Evidence-Preview.html`.
At the original 2026-11-04 checkpoint, no device copy or browser launch had been
performed. Consult the [delivery record](CROSS-GAME-CONTEXT-VIDEO-DELIVERY.md)
for subsequent copies; copying alone never establishes browser execution.
The concrete device ownership and namespace-denial limits above still apply.

For a new designated-device check, record PASS/FAIL/BLOCKED/NOT RUN
for each of these eight sections:

1. **FFXI publication only:** four recorded attempts, two publication matches,
   zero synthetic native matches. Actual game delivery must remain Unknown.
   The two identical sentences must appear as separate sequences (41 and 42).
2. **FFXI synthetic native matches:** exactly two synthetic matches. The native
   and receipt timestamps remain separate; all actual-delivery cells still say
   Unknown, and the banner identifies the entire artifact as synthetic.
3. **FFXI conflicting native observation IDs:** two conflicts, no synthetic
   matches. A receipt identity collision must not look like successful speech.
4. **FFXI conflicting publication records:** sequence 41 must withhold its
   wording/name/verdict and show a publication conflict; no arbitrary competing text
   is chosen. Other independent records keep their own results.
5. **SWTOR synthetic native matches:** the scope is SWTOR, not FFXI, with two
   synthetic matches. Its input shape is explicitly illustrative, not evidence
   of an installed SWTOR producer. Actual delivery remains Unknown.
6. **Disabled reader:** no records or counts are shown. Separate automated tests
   establish that disabled operation performs no file reads or verification.
7. **Unavailable capture:** no old prompt/message values or fabricated zeros.
   Counts are unavailable. The API/CLI input checks are separate Python tests;
   static browser rendering does not prove file handling or authentication.
8. **FFXI repeated observation receipts:** still two synthetic native matches.
   Sequence 41 keeps native observation time `00:00:01Z` and earliest supplied
   receipt time `00:00:11Z`, despite an additional receipt at `00:00:30Z`.
   All times use the fictional 2030-01-01 date. The native observation is counted
   once; this is not a measurement of real first-receipt time or latency.

At 1280 and 390 CSS pixels and 200% zoom, check readable banners, horizontal
table scrolling, keyboard focus on each scroll region and disclosure, literal
text rendering, and no outgoing requests. Compare embedded JSON and source
hashes with the exact artifact. There are no replay, confirm or native action
controls. The observed/receipt timestamps do not assert transcript chronology.
Record this section's result separately from the interactive context panel;
opening this static preview does not pass the panel fetch/session checks.

See [delivery evidence correlation](DELIVERY-EVIDENCE-CORRELATION.md) for the
source pins, duplicate/conflict rules and missing native receipt dependency.

### Validation receipt

Record a separate **PASS / FAIL / BLOCKED / NOT RUN** for every step, attaching
screenshots only where permitted and useful. Record exact console/network
errors without secrets. A blocked launch is not a failed feature assertion or
a pass. A static review does not pass the interactive section.

Existing evidence: the initial 12 focused Python capture/preview checks,
simulated-DOM panel checks and authenticated localhost smoke passed at
`dc52281`. The unavailable-source follow-up adds actual prompt-builder fixtures
and the empty-intent follow-up brought this to 21 focused Python checks plus
simulated-DOM and localhost coverage. The exact-fact follow-up brings the current
focused Python count to 25: duplicate/conflicting native facts and repeated
prompt sections are refused even if their text digest matches, while chat that
merely mentions a section heading stays dialogue. The authenticated localhost
check verifies that a contradictory capture clears previous values and a
corrected file reloads.
Those checks do not establish native rendering, real producer
authenticity, model understanding or chat delivery. The FFXI v1 producer lacks
explicit presence; SWTOR native status wiring remains a producer dependency.

The 2026-11-08 inspector follow-up applies the API's presence/body rule at the
display boundary too. Only confirmed online presence may accompany non-Unknown
body fields. Status fields must have their exact unique contract identities;
duplicate, missing or reordered identities cannot bypass the presence check.
Valid offline, stale or unknown presence with unknown body details still keeps
the captured conversation inspectable. Focused simulated-DOM cases cover both
games and recovery; they do not change this checklist's **NOT RUN** native status.

Rollback for a future released interactive check: close only its disposable
browser profile and retain the receipt. No capture environment variable is set
by the standalone fixture.
The hub's conversation flags and all live game processes remain unchanged.
