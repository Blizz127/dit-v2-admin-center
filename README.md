# DIT v2 Admin Center

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

A local scaffold is available. Optional read-only hub integration has been implemented and tested against an isolated stub; trusted SSH access to the hub host is verified, but authenticated live reads await the existing plaintext token file location. All operational controls are unavailable. See [architecture](docs/ARCHITECTURE.md), [mock API](docs/API.md), and [learning and issues](docs/LEARNING-AND-ISSUES.md).

Run with Python 3 (no third-party dependencies):

```sh
export ADMIN_TOKEN='choose-a-private-token'
python3 server.py
```

Open `http://127.0.0.1:7391` on the same machine and enter the token. The read-only playtest guide is available at `/playtest` and linked from the login and workspace screens.

For an already established, trusted localhost tunnel to the approved DIT v2 hub, set `HUB_READONLY_URL` to its explicit `http://127.0.0.1:<port>` endpoint and `HUB_TOKEN_FILE` to a readable local file containing the authorized hub token. Do not put its contents in commands, logs or git. The app opens in synthetic mode without reading the hub token. In the workspace, select “Try configured read-only hub” to request the allowlisted roster, light learning and stored game-settings GETs; an explicit evidence search can also request a bounded read-only trace, and the service-health button can request a bounded read-only health snapshot, and the interaction button can explicitly request candidate e8c81be interaction state (absent from r10); failed feeds use per-game synthetic fallback. Select “Synthetic examples” to return to the mock view. Establishing a tunnel or provisioning a local token file is not performed by the app; the approved host key is verified and the plaintext token location still needs confirmation. The hub revision and data coverage are unverified. Set `PORT` to change the port; the bind address is always loopback. The token is kept in browser session storage for the tab. This development server is not a production or tailnet service. Its background collector reads cached Codex account quota observations once a minute and stores pseudonymous history in ignored `data/local/codex-quota.sqlite`; it does not refresh accounts or store emails. Up to 10,000 observations are retained, and the view shows the latest 100. SBISD entries are excluded. Cached observations can be stale and are not attributed to individual leads. Run focused tests with `python3 -m unittest discover -s tests -v`, `node tests/selector.test.js`, and `node tests/source_race.test.js`.

To view the existing localhost instance from a laptop on the tailnet, use an already-authorized SSH login and run this on the laptop, replacing `<ssh-user>` with the normal login name:

```sh
ssh -N -L 7391:127.0.0.1:7391 <ssh-user>@devbox.tail646ff8.ts.net
```

Keep the tunnel open and browse to `http://127.0.0.1:7391` on the laptop. This requires existing SSH access; the app does not configure SSH, tailnet serving or credentials. The app's owner token is still required.

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
after automatic real-DOM inspector, preview, restore and clear checks. Reload
the file to repeat, or use the displayed inspector manually. No token entry,
account or feature activation is needed.

The harness replaces fetch with two in-memory fixture responses, disables
polling, uses temporary in-memory session storage, and blocks network resources
and form submission with CSP. Other requests fail. It does not test the HTTP
server, authentication, a deployed revision or live gameplay. The generated
file is an ignored local artifact; rebuilding incorporates current source.

Generator checks (not browser execution):

```sh
timeout -k 3 20 python3 -m unittest discover -s tests -p test_inspector_playtest.py -v
```

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
Current local result: **BLOCKED — jsdom unavailable**. A dependency path or
approval to obtain one is pending with the coordinator; no DOM-runtime pass is
claimed.

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
The UI has no sort controls or pagination state: all matching loaded rows render,
without requesting later pages. The test also covers unavailable-source fallback,
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
