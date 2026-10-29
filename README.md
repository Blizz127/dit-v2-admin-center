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

## Security

- Owner-only token auth for now.
- Binds to localhost or the tailnet only.
- No secrets in git. Use env vars or untracked `.env.local`.
- Read-only against FFXI data until the owner grants more.
