# DIT v2 Admin Center

**Current release policy (2026-11-08):** the owner lifted earlier discretionary
project holds and requests useful ready releases immediately, at most 45 minutes
apart while an increment is available. [Standing notes](docs/PROJECT-STANDING-NOTES.md)
supersede policy-stop wording in older dated handoffs. Actual access denials,
native approvals, occupied-player safeguards and sole-writer ownership remain;
source candidates and private previews are not deployed game/server versions.

**October 29 layout preview:** the workspace now has a persistent desktop sidebar,
eight clearly grouped sections, coverage cards, aligned filters, and a paired
roster/inspector layout. Narrow screens use a compact two-column navigation menu
and single-column panels. The existing navy, teal and amber colors are retained.
The standalone preview opens on the dashboard; its detailed verification report
is expandable at the bottom. See [design and delivery notes](docs/BOARDUI-LAYOUT-20261029.md).

**2026-10-29 FFXI rollout update:** Blizz authorized DIT/FFXI wiring and the
necessary bridge restart through the owning leads. DIT receipt `8421f15` records
the r5-only restart at 14:03:39 UTC after fresh player checks and a current-unit
backup. Its 14:07:59 UTC readback confirms bridge/hub active, unchanged hashes
and no fault marker; DONE/writer release is recorded. New queued replies and
native speech remain unverified. See [the reconciled handoff](docs/FFXI-WIRE-ON-20261029.md).
Admin model controls remain disabled; startup success is not gameplay proof.

**New offline preview:** “Model-switch audit examples” shows per-bot, fixed
all-bots and rejected stale-version cases in `build/inspector-playtest.html`.
Combine its scope and outcome filters to compare examples; Clear filters restores
all examples without a request. Missing outcome tags show Unknown. Requested before/after values, attempted
model and effective state are separate; effective state remains Unknown. No model
switch is enabled. The running service has not been restarted for this feature.
Generate the artifact with `python3 tools/build_inspector_playtest.py`.

**Native export check prepared, not run:** the existing isolated Chromium runner
accepts `--gap-export` to check the ambiguity table and activate its JSON download
with native Enter. It requires a saved file matching the displayed report in a
disposable directory. Offline protocol/file/receipt checks pass; missing runtime
and the prior namespace-isolation restriction still block native execution.

**Roster gap details:** expand Roster identity gap details in Loaded data coverage
to inspect a missing/repeated-ID record and jump to its exact loaded roster row.
A side-by-side table compares all exact-ID candidates and marks differing fields;
download or copy the allowlisted JSON gap report locally. Row links expire on
refresh; ambiguous bot inspection stays disabled. The offline
artifact leaves fictional gaps visible. See [playtest steps](static/playtest.html#roster-gap-guide).

**Roster identity triage:** filter the loaded roster to unique IDs or missing/repeated
IDs. Game filters cannot turn a duplicated ID into a unique one; inspection stays
disabled for ambiguous records. See [playtest steps](static/playtest.html#roster-identity-guide).

**Loaded data coverage:** a new overview summarizes roster, learning and metric
collections, including unavailable/partial lists, unusable or repeated IDs and
missing numeric fields. Review buttons navigate to the detail cards without
requests or filter changes. See [playtest steps](static/playtest.html#data-coverage-guide).

**Metric coverage:** Model call metrics now counts supplied latency, cost and quality
fields and filters examples with missing values. Zeros remain supplied values;
Unknown is never counted as zero. These are synthetic field counts, not a usage
or model-quality report. See [playtest steps](static/playtest.html#metric-coverage-guide).

**Reply evidence browsing:** the per-bot card now filters loaded examples by exact,
case-sensitive correlation ID. Clear reply filter restores all examples; choosing
another bot clears it. Generated wording, queued delivery and verification remain
separate. Try `Party-1` in the offline artifact; see [playtest steps](static/playtest.html#reply-evidence-guide).

The [party greeting evidence checklist](docs/PARTY-GREETING-VERIFICATION.md) and
`/playtest#party-greeting` separate owner input, a correlated queued reply and
owner-reported native speech. Its review tool consumes local metadata only; it
does not poll FFXI or authenticate a reported result.

A web Admin Center for **DIT v2**, the platform for human-like game bots (the "neural network"). It manages the network and every bot from one place:

- bot status, controls, goals, personality and memory
- the model used per bot, or one model for all bots
- cost, latency and quality logging, plus model bake-offs
- the action and evidence ledger
- kill switches and audit
- per-game learning status
- issues and risks

- Owner: Blizz.
- Hub: DIT v2 at `127.0.0.1:7390` on bansheerealm. Its contracts are owned by the `dit-human-behavior-platform` project.
- Game order: FFXI first, then SWTOR.

See [docs/BRIEF.md](docs/BRIEF.md) for the full brief, security rules and first tasks.

## Status

A local scaffold is available. Optional read-only hub integration has been implemented and tested against an isolated stub; trusted SSH access to the hub host is verified. Live reads lack an authorized read-only credential (hub lead, November 3): every hub `/v1/control/*` route accepts only the hub administrator token, which also authorizes writes. Lifting project policy pauses does not authorize substituting that token or changing access. A reader token accepted on control GETs would require the owning hub lead's access work; exported snapshots/offline copies already work without it. Do not configure the administrator token for this app. Exported snapshots can be reviewed instead by setting `HUB_SNAPSHOT_DIR` (off when unset; feeds and times are labeled as an export, not live; see [snapshot import](docs/HUB-SNAPSHOT-IMPORT.md)). All operational controls are unavailable. See [architecture](docs/ARCHITECTURE.md), [mock API](docs/API.md), and [learning and issues](docs/LEARNING-AND-ISSUES.md).

Run with Python 3 (no third-party dependencies):

```sh
export ADMIN_TOKEN='choose-a-private-token'
python3 server.py
```

Open `http://127.0.0.1:7391` on the same machine and enter the token. The read-only playtest guide is available at `/playtest` and linked from the login and workspace screens.

For an already established, trusted localhost tunnel to the approved DIT v2 hub, set `HUB_READONLY_URL` to its explicit `http://127.0.0.1:<port>` endpoint and `HUB_TOKEN_FILE` to a readable local file containing the authorized hub token. Do not put its contents in commands, logs or git. The app opens in synthetic mode without reading the hub token. In the workspace, select “Try configured read-only hub” to request the allowlisted roster, light learning and stored game-settings GETs; an explicit evidence search can also request a bounded read-only trace, and the service-health button can request a bounded read-only health snapshot, and the interaction button can explicitly request candidate e8c81be interaction state (absent from r10); failed feeds use per-game synthetic fallback. Select “Synthetic examples” to return to the mock view. To review an exported offline dialogue-wording evaluator run in the model-call panel, set `DIT_EVALUATOR_SNAPSHOT_FILE` to its local JSON file; it is off when unset and is not live hub data or a bake-off (see [panel coverage](docs/PANEL-COVERAGE.md)). A recorded offline bake-off run in the [proposed format](docs/BAKEOFF-PRODUCER-PROPOSAL.md) can be imported the same way with `DIT_BAKEOFF_RUN_DIR` (off when unset; live bake-off runs are refused). The **Forever-style bot activity** panel reads an exported WoW Forever bot log (`bot_event` and `bot` rows) when `DIT_FOREVER_BOTLOG_DIR` is set (off when unset; exported, not live): per-bot engine state, what it is doing, recent decisions with rejected alternatives, and deaths with their last decisions. **Baseline bot style conformance** tracks which Forever behaviors and DIT improvements each game's bots have ([proposal](docs/FOREVER-BASELINE-PROPOSAL.md)). Establishing a tunnel or provisioning a local token file is not performed by the app; the approved host key is verified. No read-only hub token exists yet (see Status), so this path remains unused. The hub revision and data coverage are unverified. Set `PORT` to change the port; the bind address is always loopback. The token is kept in browser session storage for the tab. This development server is not a production or tailnet service. Its background collector reads cached Codex account quota observations once a minute and stores pseudonymous history in ignored `data/local/codex-quota.sqlite`; it does not refresh accounts or store emails. Up to 10,000 observations are retained, and the view shows the latest 100. SBISD entries are excluded. Cached observations can be stale and are not attributed to individual leads. Run focused tests with `python3 -m unittest discover -s tests -v`, `node tests/selector.test.js`, and `node tests/source_race.test.js`.

In the model-call panel, an offline bake-off import without `attemptsSha256` is
labeled **manifest/attempts consistency unverified**: the app cannot establish
that its two files belong together. A digest mismatch makes the run unavailable.
The digest checks file bytes, not the producer's identity or the completeness of
the results; see the [import and recovery note](docs/BAKEOFF-PRODUCER-PROPOSAL.md).
Quota history omits malformed stored observations; visible rows are a partial
local cache, not proof of complete history or current per-lead usage.

To view the existing localhost instance from a laptop on the tailnet, use an already-authorized SSH login and run this on the laptop, replacing `<ssh-user>` with the normal login name:

```sh
ssh -N -L 7391:127.0.0.1:7391 <ssh-user>@devbox.tail646ff8.ts.net
```

Keep the tunnel open and browse to `http://127.0.0.1:7391` on the laptop. This requires existing SSH access; the app does not configure SSH, tailnet serving or credentials. The app's owner token is still required.

## Automatic offline schema checks

The normal Python test discovery now includes `tests/test_offline_contracts.py`.
To run only this focused contract gate:

```sh
python3 -m unittest discover -s tests -p test_offline_contracts.py -v
```

It runs the real JSON Schema engine in the current Python when available, or the
already-installed `/usr/bin/python3` on this devbox. Set `DIT_SCHEMA_PYTHON` to an
explicit installed validator Python to override that choice; an unusable override
does not fall back. No installation or dependency download occurs. Missing engine
or runtime is a failed check with an explicit blocker, never a silent skip.
The direct command is `/usr/bin/python3 tools/check_offline_contracts.py`.

Every `schemas/**/*.schema.json` must have a registered checker. For the learning
draft, `schemas/learning-assessment-draft-v1.cases.json` declares structural and
semantic expectations and must exactly match all JSON files in its fixture tree.
New/unregistered schemas or fixtures, missing fixtures and expectation mismatches
fail. Structural validity alone cannot pass cross-scope or stale evidence.
The wake-readback profile is also registered, with
`schemas/wake-verification-v1.cases.json` and five synthetic fixtures. Its checker
compares the real projection's cutover, per-game readbacks and retained holds,
including a deliberately malformed row. The direct check command emits one JSON
report containing results for both contracts; it does not mix separate JSON
documents or report overall success if either checker fails.
Historical JSON fixtures without a declared schema keep their existing specialized
checks; this does not claim a schema for every JSON document in the repository.
The checks are synthetic and never wire a draft into a live API or UI.

## Offline interaction contract check

Run the focused reader check without any network access:

```sh
timeout 20s python3 -m unittest discover -s tests -p test_interaction_contract.py -v
```

It uses a synthetic candidate fixture and rejects socket connections. It checks the reconciled f95fe8a interaction handoff, including scoped identity, freshness, cache timestamps and omitted private fields. Proposed model-routing payloads remain sketches, not implemented endpoints. See [API.md](docs/API.md#offline-interaction-contract-verification) for the verification limits.

The same command also runs all nine hub-generated candidate snapshots through
the reader, projection and cache. The [pinned fixture bundle](tests/fixtures/interaction-generated/README.md)
includes provenance and needs no sister checkout, hub, listener or .NET build.

## Offline inspector browser playtest

Build a standalone HTML file without starting or contacting a server:

```sh
python3 tools/build_inspector_playtest.py
```

Open `build/inspector-playtest.html` locally in a browser. It embeds the actual
workspace HTML, CSS and JavaScript plus Python-projected synthetic learning
fixtures. Its header starts at **NOT RUN**, then reports **PASS** or **FAIL**
after automatic real-DOM inspector, preview, restore and clear checks. It also
exercises synthetic bot goals/memory, safety, reply and assignment cards through
unavailable, partial, empty and recovered snapshots. Missing safety identities
must not become network-wide examples, and both model selectors stay disabled.
The artifact also leaves 23 matching assignment examples available for manual
paging. Tab to Previous/Next assignment page, then use Enter or Space. Controls
remain focusable at unavailable boundaries; activation there does nothing.
Automatic artifact assertions check programmatic focus retention and page counts,
not native keyboard activation. Reload
the file to repeat, or use the displayed inspector manually. No token entry,
account or feature activation is needed.

Expand **Synthetic party-evidence comparisons** near the top to compare four
fictional review summaries. Queue-only evidence leaves speech Unknown; a scoped
owner report remains visible without queue telemetry; mixed claims carry a
review warning; an old retained row cannot establish a new reply. Model origin
stays Unknown in every row. This table is computed by the offline reviewer at
generation, remains readable without JavaScript, and is not a browser-test pass
or a live receipt. Its fixture and reviewer source hashes are in the provenance
panel. Collapse the summary to hide it; no request or game action is triggered.

The harness replaces fetch with allowlisted in-memory fixture responses, disables
polling, uses temporary in-memory session storage, and blocks network resources
and form submission with CSP. Other requests fail. It does not test the HTTP
server, authentication, a deployed revision or live gameplay. The generated
file is an ignored local artifact; rebuilding incorporates current source.

For native keyboard behavior, use **Start native assignment keyboard check**
inside the artifact's assignment section after the automatic checks complete.
Follow its twelve trusted-key prompts; the observer checks Tab/Shift+Tab order,
Enter/Space paging, both boundaries and retained focus after browser defaults.
It never synthesizes activation or prevents default key behavior. An incorrect
step fails; Start prepares a fresh synthetic run. The `nativeKeyboard` runner
field is separate from automatic DOM success; neither headless dump mode nor
jsdom sends native keys. See `/playtest#assignment-keyboard` for the sequence.

A separate native-input runner now sends the keys through Chromium debugging
pipes (no TCP debugging listener), including Enter to start and Escape to cancel
and return focus, followed by the complete twelve-step sequence. It requires an
already-installed Chromium executable and isolates Node/Chromium in a network
namespace with a disposable profile and hard time limits:

```sh
timeout -k 3 40 python3 tools/run_keyboard_playtest.py
# Current source only: inspect executable availability without launching a process.
python3 tools/run_keyboard_playtest.py --preflight-only
# DIT_CHROMIUM and DIT_NODE may select already-installed executable paths.
# This does not change or replace the separately approved 8eb2c9f device bundle.
```

Exit 2 means missing runtime/tooling or denied namespace isolation; exit 1 means
failed/incomplete execution. No download or sandbox bypass is attempted. A pass
requires automatic DOM success, native keyboard success, all twelve steps and
Escape cancellation. The actual attempt at this checkpoint stopped with missing
Chromium before browser launch. Source/protocol tests are not a native pass.
There are no guided dialogs: Escape cancels the inline walkthrough, preserves
the current assignment page and returns focus to its Start button.

To capture the expanded synthetic evidence comparisons after those checks:

```sh
timeout -k 3 40 python3 tools/run_keyboard_playtest.py --screenshots
```

This requests desktop (1280×1000) and narrow (390×844, left and right scroll
positions) PNGs. It checks the four comparison rows, Unknown model origins,
horizontal viewport bounds and access to the rightmost columns. A complete run
publishes a unique directory under `build/screenshots/` with image hashes,
artifact hash and a receipt. Failed or partial runs publish nothing. PNG headers
and dimensions are checked; this is not an image decoder or a pixel-baseline
comparison. Inspect the resulting images separately for clipping, readability
and appearance. No screenshot is itself proof of live data or native speech.

The October 29 attempt remains blocked: no local Chromium/rendering engine was
found, and the independent isolation probe failed with
`unshare: write failed /proc/self/uid_map: Operation not permitted`.
No isolation bypass or download was attempted. Screenshot transport/publication
fixtures pass, but **no screenshots or browser appearance pass exist** for this
checkpoint. Use an environment with an installed browser and permitted isolation
to run the command; these local fixture tests do not remove either blocker.

Observer logic can be checked without a browser:

```sh
timeout -k 2 15 node tests/assignment_keyboard.test.js
```

That test supplies fake events and default actions. Its pass is **not** evidence
that native keyboard navigation ran. The artifact still needs actual browser
input, and screen-reader announcements and visual focus review remain separate.

Generator checks (not browser execution):

```sh
timeout -k 3 20 python3 -m unittest discover -s tests -p test_inspector_playtest.py -v
```

For changes to partial coordinator or status-card handling, focused offline
checks use the real app with synthetic fetch responses and a minimal DOM:

```sh
timeout -k 2 15 node tests/coordinator_snapshot.test.cjs
timeout -k 2 15 node tests/bridge_view.test.js
```

These cover missing/mixed records, nested histories, numeric bounds, recovery
and stale bridge response handling. They read no coordinator ledger or service
status and do not verify native browser appearance. The generated artifact
contains the updated app; its empty histories now show Unknown coverage.

Additional focused checks for partial async responses, learning inventories and
the shipped cards' static naming/announcement markup:

```sh
timeout -k 2 15 node tests/async_partial_panels.test.cjs
timeout -k 2 15 node tests/learning_inventory_snapshot.test.cjs
timeout -k 2 15 python3 -m unittest tests.test_card_markup -v
```

The loader coverage map and remaining native accessibility boundaries are in
`docs/LEARNING-AND-ISSUES.md`. Passing these checks is not a browser, screen-reader
or live-data result.

The artifact generator tests also parse the fully assembled JavaScript with
`node --check`. This checks syntax across app, driver and embedded fixtures;
it does not execute the DOM or verify browser behavior.

For roster/learning identity changes, run
`timeout -k 2 15 node tests/identity_snapshot.test.cjs`. It checks duplicate IDs
within/across games, filter independence, existing-selection clearing, disabled
inspection and unique-ID recovery using synthetic snapshots only. Identity is
resolved against the full loaded list; display names do not establish a match.

Inspector evidence navigation and partial linked records have focused checks:

```sh
timeout -k 2 15 node tests/ledger_scope.test.cjs
timeout -k 2 15 node tests/issues_snapshot.test.cjs
```

Inspector episode links pin the bot ID as well as the correlation, with the pin
shown above the ledger. Submitting a manual correlation search explicitly removes
the pin; Show all restores the loaded examples. These are synthetic local view
filters, not proof of live attribution or delivery.

No local browser runtime was found during this checkpoint, so only generator,
JavaScript syntax and simulated-DOM checks were run here. A browser PASS in the
artifact is still needed to establish its real-browser runtime result.

An offline jsdom runner also executes the generated artifact and its DOM
assertions without a browser or listener. It requires an already installed
jsdom module:

```sh
timeout -k 3 20 node tools/run_inspector_playtest.cjs
```

If the module is outside this checkout's resolution path, set
`DIT_JSDOM_MODULE` to its existing absolute package path. The runner never
downloads dependencies. Missing jsdom exits **2 (BLOCKED)**; assertion failures,
runtime errors and attempted transports exit nonzero. Success prints JSON with
the completed check count and zero transport attempts. It always regenerates
from current source in memory, rather than relying on a stale build artifact.

Node and DOM network transports are blocked independently of the HTML CSP.
jsdom checks DOM events and rendering logic; it does not establish browser
layout or CSP enforcement, HTTP authentication, or running-service behavior.
This workspace's installed module is `build/dom-runtime/node_modules/jsdom`;
use `DIT_JSDOM_MODULE="$PWD/build/dom-runtime/node_modules/jsdom"` when running
the command above. The recorded check for delivered preview `c3283185` passed
all 191 assertions with zero transport attempts. See the
[release receipt](docs/BOTS-PARITY-PREVIEW-20261109.md#delivered-preview-c3283185-source-0f85db3)
for the exact artifact hash and verification limits. Native browser and keyboard
checks remain NOT RUN.

The preview's **Bot activity sample** selector can switch to **Synthetic FFXI +
SWTOR readiness** after the automatic checks finish. It uses a fictional FFXI
post-H1 timing/travel stub and the existing SWTOR kf writer samples, both through
the normal readers and activity view. Source labels and coverage identify them
as synthetic. Switching back restores the original recorded exports and schema
examples; the parity tracker is unchanged in every mode. These samples test
import/display readiness, not live bot behavior. Real reviewed exports must
replace the captured inputs and provenance before any new live-evidence claim.

**Synthetic SWTOR import with a malformed row** retains the same valid events
while showing one reader omission separately from the producer's 27-row loss
report. Returning to the complete readiness sample clears that omission;
FFXI readiness and the other games' source data remain unchanged.

**Synthetic FFXI import with skipped lines** shows one malformed, one
unrecognized and one unrelated line separately while retaining the 52 accepted
lines and their event range. Returning to complete readiness clears all three
counts. The other source data and parity evidence remain unchanged.

Activity coverage labels its count **Rows omitted on import**: exclusions may
include malformed or non-event rows, row limits, or duplicate IDs depending on
the source. The supplied reason explains them. Refused files have a separate
notice; their unread row counts are not inferred or added to this total.

DIT bot-event coverage also flags retained `LOG_DROPPED` report rows separately
from rows omitted by the reader. Each report's event shows its
producer-reported dropped count, or Unknown if the count is missing or invalid.
Reports may overlap and are never summed into a loss total or reader omissions.

The HTTP-handler portion can be checked independently of jsdom:

```sh
timeout -k 3 20 python3 -m unittest discover -s tests -p test_offline_inspector_handler.py -v
```

This feeds HTTP request bytes to the actual handler using in-memory streams,
with its overview collector replaced by the projected synthetic fixture. It
checks authentication, query rejection, method rejection, response headers and
learning-field serialization. Sockets, subprocesses, databases and live readers
are forbidden. It starts no listener and does not verify the real overview
collectors, a deployed service or a browser. Ten checks passed locally, including
interaction/health failure redaction, trace validation/projection, and bridge
authentication, permission denial, timeout and cache recovery. Malformed
trace values now return 400 before configuration lookup, instead of being
misreported as an unavailable hub. The running service was not restarted.

## Offline bridge UI checks

```sh
timeout -k 3 20 node tests/bridge_view.test.js
```

This runs the actual bridge-display function with a minimal simulated DOM and
deferred synthetic responses. It checks both bridge cards, visibility/token
guards, one in-flight request, failure redaction, Unknown states and recovery.
Late results are discarded while the workspace is hidden or its token differs
from the request token. It uses no network, listener or real browser; layout and
deployed runtime remain unverified.

## Offline panel session checks

```sh
timeout -k 3 20 node tests/panel_session.test.js
```

The actual application runs against a minimal simulated DOM and deferred
fixture responses. Coverage includes all five asynchronous paths: overview,
interaction, hub health, trace and bridge. Sixty cases combine workspace hiding,
token changes or same-token login with success, rejection, HTTP denial or delayed
JSON. Five current-response paths and eight request-start guards are also
checked. This is not a headless browser or deployed-service test.

Login and a workspace-closing load failure invalidate the previous session's
pending views and selected snapshot. Late replies cannot render data, replace
errors or update token storage for the newer session. Existing source/correlation
request-version guards still apply. Initial login may load while the workspace
is hidden; optional panel reads require a visible workspace and a token.

## Headless offline artifact check

For an actual installed Chromium runtime, a separate headless artifact check is
available (no server or running mock is contacted):

```sh
DIT_CHROMIUM=/path/to/installed/chromium timeout -k 3 30 python3 tools/run_headless_playtest.py
```

It creates a temporary profile and inline synthetic artifact, isolates the
browser in a user/network namespace, and checks the resulting DOM report. No
sandbox-disabling option or dependency download is used. Missing Chromium or
denied isolation exits 2; unsuccessful or incomplete checks exit 1. Locally,
execution is **blocked: no Chromium executable was found**. Runner contract
tests used fabricated browser output and are not a browser pass.

What's new in the artifact: health empty/401/502/503/recovery states and both
bridge cards' Unknown/error/recovery states. “Hub” selection inside this artifact
is an in-memory fixture switch, never a live hub request. The checks run on file
open/reload; close the file to stop. To regenerate the manually viewable file,
run `python3 tools/build_inspector_playtest.py`. Look for the result banner and
individual checks; a newly generated file starts NOT RUN. Actual browser
execution, visual appearance and deployed-service behavior remain unverified.

## Browser-free inspector integration

The inspector and coverage integration checks can use a built preview's parsed
markup while requiring it to embed the current application source:

```sh
DIT_TEST_ARTIFACT=build/inspector-playtest.html node tests/inspector_integration.test.js
DIT_TEST_ARTIFACT=build/inspector-playtest.html node tests/coverage_integration.test.cjs
```

Both passed against local preview `1759671c` on October 30. A focused Python
check verifies that stale inspector artifacts fail before the template/handler
fixture subprocess runs. This binds the simulated-DOM check to markup/current
app source; it does not execute the standalone driver, CSS layout, native
keyboard defaults or browser download behavior. No preview is rebuilt or
delivered by these commands.

Overview failure and inspector reset checks:

```sh
timeout -k 2 15 node tests/overview_failure.test.js
```

What's new: a session reset now clears bot and learning inspector details as
well as selected IDs. A 401 or malformed snapshot that interrupts rendering
closes the workspace; re-login with an empty snapshot cannot show old details.
An ordinary failed refresh instead retains the previous snapshot with its
explicit stale-source banner. This uses actual app code, shipped template IDs
and synthetic responses in a simulated DOM. No runtime toggle is added; the
behavior applies on session reset. Browser rendering remains unverified.

The same focused check covers filters surviving a changed snapshot: updated
selected records refresh their inspector even when hidden by filters; removed
records replace old details with a missing-selection message. Explicit Clear
removes that warning. `/playtest#selection-refresh` describes what to look for.

Ordering checks preserve received snapshot order through filtering and refresh.
Roster and learning lists have no sort controls or pagination state: all matching
loaded rows render, without requesting later pages. Assignment examples now use
local ten-row pages, preserving supplied order without fetching more history. The test also covers unavailable-source fallback,
empty roster/learning warnings and an initial 503 that leaves login visible.
No browser appearance or upstream completeness is established by these checks.

The detail check also selects two synthetic bots with the same display name.
Goals, memory, evidence, issues, assignment and reply examples join by exact
record ID. When a selected bot disappears, orphan bot-specific safety examples
are hidden along with its other details; network-wide safety examples remain.
Selection itself makes no service request. These are read-only examples, not
bot-edit validation or proof of native identity; editing remains disabled.

Audit checks cover synthetic rows, unknown timestamps, failed-refresh labeling
and an explicit empty state. Bot selection never creates an audit event. No live
audit source is connected, so an empty panel cannot establish that no actions
occurred. These checks use the same offline overview command above.

The audit panel now offers local search by actor, action, scope or result, with
a loaded-example count and Clear audit filter. Matching ignores case and
surrounding spaces. Search persists through refresh, makes no service request
and does not create audit events. No pagination or live audit integration is added.

FFXI playtest focus now renders explicit Unknown readiness for absent summaries
and missing fields. The focused overview check covers source labels, replacement
of old summaries and exclusion of SWTOR-only feeds from FFXI coverage. The offline
artifact's default fixture has no readiness summary, so it shows this new empty
state; no readiness or deployment authorization follows from it.

Needs Blizz now isolates missing or malformed decision-summary metadata to that
card instead of closing the workspace. Unknown coverage differs from a valid
empty list; incomplete fields show unknown values. The overview UI check covers
prior-row clearing, other-panel availability and later recovery. This changes
display only and neither records nor grants an approval.

The audit card likewise distinguishes unavailable metadata (Unknown count) from
a valid empty list (0 loaded examples). Missing row fields remain Unknown.
Search/reset stay local and usable while the list is unavailable; a later valid
snapshot replaces the coverage warning. The focused overview check covers this
without accessing an audit ledger or a browser runtime.

To check timeout/partial-feed recovery through the reader, cache and merge:

```sh
timeout -k 2 10 python3 -m unittest discover -s tests -p test_offline_feed_recovery.py -v
```

Synthetic response bytes and an injected clock cover cache expiry, scoped
fallback, empty collections, no automatic retries and later recovery. No hub,
server, ledger or real credential is used; wall-clock timeouts are not measured.

The quota background loop has a separate synthetic scheduling check:

```sh
timeout -k 2 10 python3 -m unittest discover -s tests -p test_quota_worker.py -v
```

It invokes the real worker with temporary account-state fixtures and an injected
stop/wait object: no thread, sleep, account refresh or service starts. Checks
cover 60-second retry requests, deduplication, subsequent samples, storage-error
recovery, and a stop set before collection. Source data stays unchanged during
recovery; stored records omit fixture secrets. This is not wall-clock scheduling
or shutdown-race verification of the running worker.

The actual overview collector has a separate offline handler check:

```sh
timeout -k 2 15 python3 -m unittest discover -s tests -p test_offline_overview_collection.py -v
```

It uses a temporary synthetic home and coordinator/quota SQLite records, rather
than replacing `overview`. It checks populated/missing/malformed sources,
read-only access, unchanged fixture files, connection cleanup, summary redaction,
unknown per-lead quota and auth/query rejection before collection. Process probes,
commands and hub access are blocked; missing command evidence stays unknown.
This exposed and fixed a task-inventory connection leak. No real records or
running service are inspected, and no UI/browser claim follows from this test.

```sh
timeout -k 3 25 node tests/inspector_integration.test.js
```

This dependency-free check connects the synthetic candidate fixture, actual
Python projection, in-memory HTTP handler, and actual `app.js` inspector.
Element IDs, initial visibility and select defaults come from the shipped HTML;
missing selectors fail instead of silently creating test elements. The check
exercises wrong-token and accepted login, four learning evidence rows, and
preview/restore/clear with no extra reads. The overview collector and bridge
observation are synthetic; real sockets, subprocess-backed collectors, databases
and live readers are blocked in the Python fixture adapter.

The same command also drives the trace form through the actual handler and
`project_trace` using an injected synthetic reader. It checks pending/non-final
evidence, empty results, invalid response data (502), unavailable or unconfigured
reads (503), and an expired owner token (401 before the reader). Invalid
correlations are rejected locally with no request; later successful reads and
Clear replace the previous state. Raw evidence and exception canaries never
reach the UI. Fixture scenario selection is test-only, not an API parameter.

Interaction coverage uses all nine pinned generated snapshots, verifying each
artifact hash before projection. It checks both freshness directions, scoped
actors, empty/off collection and truncation through the real handler and UI.
The cache lookup is replaced with a pure fixture projection; this connected
check does not exercise cache timing or HTTP transport. It also covers
401/502/503 responses, recovery, no-request synthetic preview and clearing the
panel on source change. Existing offline contract tests cover reader/cache
behavior separately. No live endpoint is contacted by either test path.

Service-health scenarios use the actual projection with an injected cache lookup:
FFXI/SWTOR filtering, unknown service states, empty results, 401 before lookup,
502/503 errors, recovery and source-change clearing. Every error replaces prior
service data with Unknown. Synthetic private log/environment fields are omitted;
service health is never promoted to bot presence. No service inspection or real
cache timing is exercised by this path.

Bridge scenarios connect the real `BridgeObserver`, in-memory handler and both
UI cards using a fake command runner. Active state, a delayed-delivery fault,
empty/malformed output, permission denial, timeout, owner-token rejection and
recovery are checked. Observation failures produce HTTP 200 with Unknown state;
401 is reserved here for the owner-token rejection, before the fake runner.
Each exchange uses a fresh observer, so this does not test cache lifetime or SSH.
The overview-triggered bridge refresh is allowed to settle before manual clicks.

This uses a deliberately limited simulated DOM, not jsdom or a browser engine.
It verifies data flow and event-handler behavior, not HTML layout, CSS, browser
security or deployed collectors. It passed locally without a listener or any
new package. Browser/jsdom execution remains parked.

The standalone HTML artifact now has an expandable **Artifact source
fingerprints** section. It records SHA256 hashes of its seven local source and
fixture inputs at generation. Include those hashes when sharing a playtest
result; they identify the artifact inputs, not a deployed version or a test pass.

## Security

- Owner-only token auth for now.
- Binds to localhost or the tailnet only.
- No secrets in git. Use env vars or untracked `.env.local`.
- Read-only against FFXI data until the owner grants more.

### Review returned native-device evidence offline

After the separately sequenced bazzite attempt returns through the trusted device
lead, use the [receipt intake guide](docs/NATIVE-RECEIPT-INTAKE.md) to prepare a
local review directory from its existing files and identity metadata:

```sh
python3 tools/review_native_attempt.py /path/to/local/returned-attempt
```

This command launches nothing and writes nothing. It distinguishes incomplete,
blocked, failed and reported-pass evidence for the exact approved `8eb2c9f` pin.
A reported pass is a consistency result, not independent device authentication
or verification of newer previews. Do not invent missing values or request a
new device run just to populate reviewer metadata. The original 23:20:30Z blocked
attempt remains separate. See the guide for required files and exit codes.

### Readiness text snapshots without a browser

For a source-level readiness check against the generated artifact:

```sh
python3 tools/build_inspector_playtest.py
timeout 15s node tools/readiness_snapshot.cjs build/inspector-playtest.html > build/readiness-semantic-snapshot.json
```

Exit 0 means six semantic scenarios passed using parsed artifact markup and the
matching app code in a synthetic DOM. The report pins the HTML hash and records
visible rows/counts. It is not a screenshot, full-driver run, native layout or
keyboard verification. Stale app bytes or missing readiness elements fail. See
[the evidence guide](docs/WAKE-VERIFICATION-RECEIPT.md) for scope and remaining gaps.

### Isolated synthetic write-contract checks

```sh
python3 -m unittest tests.test_mock_routing_api tests.test_mock_routing
```

These exercise an in-process routing proposal, exact fixture scope, atomic
version checks, bounded retries, concurrent conflicts and audit copies. They
also confirm the real HTTP handler still refuses the mock dispatch path with
405. No write listener, UI control, provider call or live change is enabled.
See [the proposed contract](docs/HUB-CONTRACT-DRAFT.md#isolated-mock-routing-write-proposal--october-30).

### Inspect one synthetic conversation/status packet

The Bots workspace includes **Load configured offline capture**. It is off until
`DIT_CONTEXT_CAPTURE_FILE` points to a captured fixture, for example
`tests/fixtures/context-status-integration/ffxi-companion.json` (resolve the path
from the server's working directory). Use the existing local development startup
and authentication; no new token or live hub access is needed. The endpoint is
`GET /api/context-capture`, under the existing Admin Bearer check.

The view pairs the exact prompt, retained history count and status binding from
one offline integration test. It is independent of roster selection. Malformed
or missing input clears the view; it never substitutes old or live data. See the
[integration handoff](handoffs/context-status-integration-20261104/README.md) for
source candidates, rollout/rollback and verification limits.

A valid packet whose native source is unavailable still displays its captured
conversation with unknown status fields. It does not invent a body identity or
revision. The [native-browser checklist](docs/CONTEXT-NATIVE-BROWSER-CHECKLIST.md)
and `python3 -m tools.build_context_capture_playtest` provide an offline preview
of the panel using six ordinary, four unavailable-status and two empty-context captures. Native
browser execution remains pending under the recorded device restrictions.

### Inspect offline delivery evidence

The Bots workspace also has **Load configured delivery evidence**. Its setting
`DIT_DELIVERY_CAPTURE_FILE` is unset by default; for a local synthetic example,
use `tests/fixtures/delivery-correlation/ffxi.json` or `swtor.json` relative to
the development server's working directory. The existing Admin authentication
protects `GET /api/delivery-capture` before file access. Nothing scans live logs,
confirms native speech, updates conversation history or replays a message.

The report matches decision/inbox publication records and withholds conflicting
wording. Every actual-delivery value stays Unknown. The API has no native verifier
or simulation control. See [source limits and focused checks](docs/DELIVERY-EVIDENCE-CORRELATION.md).
Unset the setting to disable reads again; no migration or service change is
performed by this feature.

`python3 -m tools.build_context_capture_playtest` embeds the actual loader with
two synthetic reports and network disabled. The separate
`python3 -m tools.build_delivery_correlation_preview` produces a static preview
of eight publication/receipt states, including explicitly fabricated native
matches. Both remain local artifacts with native browser NOT RUN; the
[checklist](docs/CONTEXT-NATIVE-BROWSER-CHECKLIST.md) preserves device and live-game holds.
