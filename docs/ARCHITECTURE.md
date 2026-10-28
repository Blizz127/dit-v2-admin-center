# Architecture

Status: draft for joint review with the DIT v2 hub lead. The hub owns its contracts; this document does not establish or change them. The coordinator has been asked to relay the proposal and identify the current r10 and ledger specifications.

## Boundary

The browser talks only to this application's same-origin backend. An owner token authenticates access to data; future hub credentials remain on the backend. The initial development backend binds exclusively to 127.0.0.1, serves synthetic fixtures, has no connection to the hub or games, and exposes no mutation endpoints. It must not be treated as a production or tailnet deployment.

A future hub adapter translates confirmed, versioned hub responses into the local presentation contract in [API.md](API.md); it must not invent hub endpoints or imply that a mock field is supported upstream. Game adapters retain authority over game state and validation. The admin center does not access game databases, saves or characters. Start, stop, pause, model changes, gates and kill switches stay unavailable until their upstream contracts, authorization, audit, and safety behavior are established. Gates default off; unknown is never represented as off.

## Operator experience

A cross-game overview presents bots, issues, learning, model telemetry and the evidence ledger. Each item identifies its source, observation time and environment; absent, expired or uninstrumented information is explicitly unknown. Registered personas do not prove presence. Game-specific views should use each game's concepts, beginning with FFXI and then SWTOR. A timeline links observations, requests and adapter outcomes through correlation identifiers. A dispatched request is not completion; show result and verification separately. Refusal is a normal result, with its reason.

Per-bot goals, personality, grounded memory, model routing and controls; global routing; provider-neutral call cost/latency/quality and bake-offs; audit; and learning datasets, policy verification and adoption are planned capabilities, not claims of implementation. Scheduled policy drafting and dialogue wording do not grant model output execution authority. Research and verified policy are distinct from actual adoption and demonstrated game outcomes.

## Security and operation

Owner authentication is mandatory for data. Secrets come from the environment or untracked local files, never git. Do not log tokens, expose provider or hub credentials to the browser, use SBISD accounts/models or the Grok pool. No FFXI writes, real saves or live characters. No connection to the v1 hub. No live integration or deployment is authorized by this mock scaffold. Before live use, design secure sessions, CSRF and origin controls, transport, audit, expiry, rate limits and fail-closed behavior against the agreed hub API.

References read: sister project's `docs/architecture/PLATFORM_BOUNDARIES.md`, `CONTRACTS_V0.md`, `CONTROL_CENTER_INFORMATION_ARCHITECTURE.md`, and `ADMINISTRATOR_MISSION_CONTROL.md`. Those documents contain historical deployment claims; none were checked against a running service. Contract review with the hub lead remains pending.
