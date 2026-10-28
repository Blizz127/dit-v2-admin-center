# Admin Center API

Status: local mock contract only, draft pending coordination with the DIT v2 lead. These are endpoints of this scaffold, not claims about hub r10 or its ledger. The browser never calls the hub directly.

All responses are JSON and `Cache-Control: no-store`. Requests to `/api/*` require `Authorization: Bearer <owner token>`; absent or incorrect tokens receive 401. The token must be provided to the process as `ADMIN_TOKEN` and is never included in responses. No mutation endpoints exist. Unknown API paths return 404. No CORS access is provided.

## GET /api/overview

Returns `{ "mode": "mock", "generatedAt": <UTC ISO timestamp>, "bots": [...], "ledger": [...], "learning": [...], "issues": [...] }`. All examples are synthetic, not hub observations. Each bot has `id`, `name`, `game`, `status`, `source`, and `observedAt`. Ledger records have `correlationId`, `bot`, `request`, `result`, and `verification`; `pending` or `unknown` must not be rendered as success. Learning entries have `game`, `topic`, `status`, and `evidence`; issues have `title` and `detail`.

The mock is intentionally small; it is not a substitute for upstream schemas, pagination, complete roster coverage, audit, usage metrics or actual policy verification. Before integration, agree with the hub lead on endpoint versions, authentication, source and freshness, pagination, correlation, error behavior, authorization, audit, and command idempotency. Treat unavailable values as unknown and unavailable actions as disabled.
