# Architecture

Status: draft for joint review with the DIT v2 hub lead. The hub owns its contracts; this document does not establish or change them. The coordinator has been asked to relay the proposal and identify the current r10 and ledger specifications.

## Boundary

The browser talks only to this application's same-origin backend. An owner token authenticates access to data; hub credentials remain on the backend. The development backend binds exclusively to 127.0.0.1, serves synthetic fixtures by default, and exposes no mutation endpoints. Optional allowlisted read-only hub requests require an explicitly configured trusted loopback tunnel and an existing token file. It must not be treated as a production or tailnet deployment.

The optional hub adapter translates source-reviewed r10-shaped responses into the local presentation contract in [API.md](API.md); it must not invent hub endpoints or imply that a mock field is supported upstream. Game adapters retain authority over game state and validation. The admin center does not access game databases, saves or characters. Start, stop, pause, model changes, gates and kill switches stay unavailable until their upstream contracts, authorization, audit, and safety behavior are established. Gates default off; unknown is never represented as off.

## Operator experience

A cross-game overview presents bots, issues, learning, model telemetry and the evidence ledger. Each item identifies its source, observation time and environment; absent, expired or uninstrumented information is explicitly unknown. Registered personas do not prove presence. Game-specific views should use each game's concepts, beginning with FFXI and then SWTOR. A timeline links observations, requests and adapter outcomes through correlation identifiers. A dispatched request is not completion; show result and verification separately. Refusal is a normal result, with its reason.

Per-bot goals, personality, grounded memory, model routing and controls; global routing; provider-neutral call cost/latency/quality and bake-offs; audit; and learning datasets, policy verification and adoption are planned capabilities, not claims of implementation. Scheduled policy drafting and dialogue wording do not grant model output execution authority. Research and verified policy are distinct from actual adoption and demonstrated game outcomes.

## Security and operation

Owner authentication is mandatory for data. Secrets come from the environment or untracked local files, never git. Do not log tokens, expose provider or hub credentials to the browser, use SBISD accounts/models or the Grok pool. No FFXI writes, real saves or live characters. No connection to the v1 hub. Blizz authorized read-only hub integration; no live write or deployment is authorized. Before live use, design secure sessions, CSRF and origin controls, transport, audit, expiry, rate limits and fail-closed behavior against the agreed hub API.

References read: sister project's `docs/architecture/PLATFORM_BOUNDARIES.md`, `CONTRACTS_V0.md`, `CONTROL_CENTER_INFORMATION_ARCHITECTURE.md`, and `ADMINISTRATOR_MISSION_CONTROL.md`. Those documents contain historical deployment claims; none were checked against a running service. Contract review with the hub lead remains pending.

## Hub lead handoff, 2026-10-28

The source baselines are `dit-v2-release-20261027/baseline-b089a2c` at `b089a2c` (r10) and `dit-v2-release-20261027/hub` at `e8c81be` (integrated candidate). Neither is evidence that it matches the earlier AX41 `f064347` record or any current live deployment. Candidate-only changes include `InteractionAdminApi.cs` and `KnowledgeUseApi.cs`. Identify source revision, environment and store before using any data. That handoff did not authorize live calls or token reads. Blizz later authorized read-only hub calls using an existing token file; verified access and the token-file location remain outstanding. Service writes remain unauthorized.

The r10 provider policy is global/per-purpose, not per bot. A proposed future policy would key game, realm, native bot identity and purpose, expose requested/effective policy, source, timestamp and availability first, and only later permit audited, admin-authorized compare-and-set changes with provider/model, budget and fallback validation. Requests must retain native safety and deadline gates and use the authoritative spend ledger with game/bot/purpose/request attribution. Native combat stays local; model failure must not freeze it. This is a design proposal, not an implemented capability.

The AI spend ledger has provider/model/purpose and accounting details but lacks game/bot/party attribution in its attempts table. Each data directory has a separate ledger; v1 and fresh v2 totals must not be combined as reconciled. Missing rates, quota and evidence are unknown. Do not mint credentials. Read only the existing approved hub access-token file when its path and trusted access are established.

The hub lead's reviewable proposal is `dit-v2-release-20261027/custody/per-bot-model-routing-draft.md`. It specifies adapter-verified `(gameId, realmId, nativeBotId, purpose)` identity; a verified selected speaker for FFXI group turns; exact override then explicit purpose default; and safe unavailability if resolution fails. Requested and effective routing, version, source, freshness and readiness are distinct. Unknown rate, allowance, credentials or budget must fail closed; no implicit paid fallback. Future compare-and-set changes require separate authorization, audit and approved provider/model/account routes. They cannot change credentials, budgets, fallback authorization or start actions. All attempts need reservation and settlement through the authoritative ledger with request and scope attribution. These are proposals, not implemented functionality; Blizz approved the draft; controls remain disabled until the hub implements the reviewed contract and model changes are separately authorized. The lead reports the offline FFXI bake-off covers ambiguous identity and unknown budget without provider calls; we have not independently inspected its results.
