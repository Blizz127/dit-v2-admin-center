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

A local scaffold is available. Optional read-only hub integration has been implemented and tested against an isolated stub; actual hub access remains blocked by SSH host-key verification. All operational controls are unavailable. See [architecture](docs/ARCHITECTURE.md), [mock API](docs/API.md), and [learning and issues](docs/LEARNING-AND-ISSUES.md).

Run with Python 3 (no third-party dependencies):

```sh
export ADMIN_TOKEN='choose-a-private-token'
python3 server.py
```

Open `http://127.0.0.1:7391` on the same machine and enter the token.

For an already established, trusted localhost tunnel to the approved DIT v2 hub, set `HUB_READONLY_URL` to its explicit `http://127.0.0.1:<port>` endpoint and `HUB_TOKEN_FILE` to a readable local file containing the authorized hub token. Do not put its contents in commands, logs or git. The app reads only the allowlisted roster and light learning GETs on refresh, with per-game synthetic fallback. Establishing a tunnel or provisioning a local token file is not performed by the app; the approved host key and token location still need to be confirmed. The hub revision and data coverage are unverified. Set `PORT` to change the port; the bind address is always loopback. The token is kept in browser session storage for the tab. This development server is not a production or tailnet service. Its background collector reads cached Codex account quota observations once a minute and stores pseudonymous history in ignored `data/local/codex-quota.sqlite`; it does not refresh accounts or store emails. Up to 10,000 observations are retained, and the view shows the latest 100. SBISD entries are excluded. Cached observations can be stale and are not attributed to individual leads. Run focused tests with `python3 -m unittest discover -s tests -v` and `node tests/selector.test.js`.

To view the existing localhost instance from a laptop on the tailnet, use an already-authorized SSH login and run this on the laptop, replacing `<ssh-user>` with the normal login name:

```sh
ssh -N -L 7391:127.0.0.1:7391 <ssh-user>@devbox.tail646ff8.ts.net
```

Keep the tunnel open and browse to `http://127.0.0.1:7391` on the laptop. This requires existing SSH access; the app does not configure SSH, tailnet serving or credentials. The app's owner token is still required.

## Security

- Owner-only token auth for now.
- Binds to localhost or the tailnet only.
- No secrets in git. Use env vars or untracked `.env.local`.
- Read-only against FFXI data until the owner grants more.
