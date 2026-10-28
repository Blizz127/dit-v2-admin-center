# Admin Center API

Status: local mock contract only, draft pending coordination with the DIT v2 lead. These are endpoints of this scaffold, not claims about hub r10 or its ledger. The browser never calls the hub directly.

All responses are JSON and `Cache-Control: no-store`. Requests to `/api/*` require `Authorization: Bearer <owner token>`; absent or incorrect tokens receive 401. The token must be provided to the process as `ADMIN_TOKEN` and is never included in responses. No mutation endpoints exist. Unknown API paths return 404. No CORS access is provided.

## GET /api/overview

Returns `{ "mode": "mock", "generatedAt": <UTC ISO timestamp>, "bots": [...], "ledger": [...], "learning": [...], "issues": [...] }`. All examples are synthetic, not hub observations. Each bot has `id`, `name`, `game`, `status`, `source`, and `observedAt`. Ledger records have `correlationId`, `bot`, `request`, `result`, and `verification`; `pending` or `unknown` must not be rendered as success. Learning entries have `game`, `topic`, `status`, and `evidence`; issues have `title` and `detail`.

The mock is intentionally small; it is not a substitute for upstream schemas, pagination, complete roster coverage, audit, usage metrics or actual policy verification. Before integration, agree with the hub lead on endpoint versions, authentication, source and freshness, pagination, correlation, error behavior, authorization, audit, and command idempotency. Treat unavailable values as unknown and unavailable actions as disabled.

## Source-reviewed hub surface (r10, b089a2c)

This is a reading guide for future integration, not permission to call it. `AdminCenter.cs`, `ControlCenter.cs`, `CompanionApi.cs`, `HubApi.cs`, `HubTokens.cs` and `Program.cs` in the identified baseline are authoritative for the source revision. The listed `/v1/control/*` GET routes explicitly require an Admin Bearer and return 403 on missing/invalid authorization: `overview`, `health`, `bots?gameId=`, `bot?gameId=&key=`, `providers`, `ai-spend`, `goals?gameId=`, `learning?gameId=`, `relationships?gameId=`, `server-status?gameId=`, `companion`, and `trace?gameId=&correlationId=`. A separately configured admin listener requires Admin for `/v1/*` and returns 401 before routing. The fresh v2 configuration described in the handoff has no approved admin listener or admin token. Keep hub credentials server-side; do not obtain them now.

The source's main listener leaves `/v1/health`, `/v1/games`, `/v1/status`, `/v1/jobs`, `/v1/personas` and `/v1/scorecards` open. Knowledge list and history return metadata without the document payload's adapter-private check; individual adapter-private document payload access requires Admin or a same-game Adapter. Review exact access semantics before integration; do not assume metadata is confidential.

`bots` lists persona/body records, not confirmed presence. `trace` searches envelopes by game and correlation ID (invalid or over-128-character IDs return 400; unknown games return 404); correlation alone does not prove game outcome. `learning` caps query text at 128 characters, reports a 120-item history limit, and its light/task-only options omit evidence or other panels. `overview` caches slow aggregates for 20 seconds; its source notes full-table scans and lock contention. `health` inspects services. Notably, `bot` and `goals` call `ImportProgress` even though they are GET routes; do not assume a GET is side-effect-free. Route fields, costs and behavior must be checked against the selected revision before any authorized integration. No polling is authorized now.

The e8c81be candidate adds interaction and knowledge-use APIs; their presence is candidate-only and does not establish live deployment. Per-bot model switching and complete spend attribution are not implemented in either handoff revision.
