# Proposed hub contract for Admin Center review

**Owner-approved design draft, not implemented.** Blizz approved this draft in the conversation; hub-lead technical review and unresolved contract details remain. This approval does not authorize credential changes or live model writes. Prepared for Blizz and the DIT v2 lead from the lead's `custody/per-bot-model-routing-draft.md` and source inspection of r10 `b089a2c` and candidate `e8c81be`. It does not grant access to a hub, credentials, model calls, writes or rollout. The existing r10 endpoints and separately configured admin listener are described in [API.md](API.md); candidate-only changes and the AX41 historical record must not be conflated with r10 or a current live version.

## Read-only operator data

Every response should identify revision/contract version, environment and instance, observation time, coverage and freshness. Missing, stale, partial or unavailable data remains explicit; an empty result is not proof of health or complete coverage. Registered persona/body listings do not prove presence. Service health does not prove bot health. Observation, intention, adapter outcome and verification are separate facts; correlation alone is not proof of execution. Avoid exposing credentials, prompts, sensitive raw player information or internal paths unnecessarily. Pagination and bounded response costs need agreement.

The intended overview includes roster and verified identity, game/server status, task and learning gaps, dataset provenance, policy validation/delivery/adoption and demonstrated outcomes, action/evidence trace, measured provider usage, and issues. A learning task's verified state does not establish verified policy or adoption. Every record must retain its own source and time; cross-game and environment records cannot be silently combined.

## Candidate FFXI interaction read handoff

Admin Center candidates `143b558`, `bbf5a22` and `0bcf2a7` add the interaction
projection, explicit on-demand read and no-network synthetic freshness preview.
The current [API contract](API.md#get-apiinteraction) maps authenticated local
`GET /api/interaction` to candidate e8c81be Admin-only
`GET /v1/control/interaction?limit=50`. The reviewed source path is
`InteractionAdminApi.Describe` → `FfxiInteraction.Views` → `ActionLedger.Describe`;
it reads state and ledger copies without dispatching actions or changing switches.
This endpoint is absent from r10, and the deployed hub revision remains unverified.

Preserve caller and server-instance scope; do not join interaction actors to a
roster by name. Reported switches, `freshForSeconds`, truncation, fetch time and
coverage remain explicit. Reconciled `fresh` differs from raw `snapshotFresh`:
activity stays unknown unless contract collection and reconciled freshness are
explicitly true, and off/unknown collection yields no current inventory. The
15-second cache retains its original fetch time. Raw orders, requesters,
receipts, chat and state-counter payloads are omitted.

The synthetic preview makes no network request; the optional candidate check
is a separate explicit read and never enables collection or model controls.
The handoff reports six projection checks plus stub, authentication, browser-race
and local-startup checks, with no live hub request. These are reported offline
results, not independently rerun here or evidence of live endpoint availability.
Model controls remain off. This reconciliation grants no activation, deployment,
credential or write authority.

### Generated fixture reconciliation (2026-10-29)

The hub lead supplied `dit-human-behavior-platform` commits `a311fd3` then
`b9e404e`, with nine generated candidate snapshots in
`tools/ffxi/interaction_admin/fixtures`. The adjacent README contains commands,
provenance and limits; `MANIFEST.json` identifies the fixture artifacts and
`consumer-pins.json` pins the actual Admin Center projection, reader and cache.
Those three module hashes match this checkout, and all ten manifest artifact
hashes match (nine snapshots plus the in-process route-check record).

Both freshness directions agree with the existing integration: a fresh mode
can yield `fresh=true` with `snapshotFresh=false`; a newer accepted receipt can
supersede a one-second-old raw snapshot, yielding `snapshotFresh=true` with
`fresh=false`. The latter must keep projected activity unknown. Neither an
accepted receipt nor a fresh raw snapshot establishes execution or delivery.
The existing offline reader fixture already exercises both directions, so no
duplicate fixture suite or consumer implementation is added here.

The hub lead reports seven checks against the hash-pinned consumer modules
passed. This reconciliation checked artifact and consumer hashes and inspected
the coverage; it did not rerun those checks or regenerate the bundle. GET,
Admin authorization and limit checks invoked the candidate request delegate
in-process without a listener. The generator uses unchanged e8c81be endpoint
source with a cached offline library containing separate provenance changes,
not a fresh release build or a deployed HTTP stack. All snapshots are synthetic.
The endpoint remains absent from r10; deployed revision and live availability
remain unverified. No live read, activation, model or control change is
authorized by this handoff.

The subsequent coordinator request `e855ecb641e726ca` adds the nine pinned
snapshots to the existing offline contract harness. The byte-identical import
and provenance are in `tests/fixtures/interaction-generated`; no sister checkout
is needed to run it. Seven contract tests now pass, including one nine-snapshot
matrix through the current reader, projection and cache with sockets forbidden.
This extends local consumer coverage without repeating the upstream generator
or its in-process route authorization checks. No production code changes were
needed. The earlier no-rerun statement describes the initial reconciliation.

## Proposed routing read model

A route is scoped by adapter-verified `(gameId, realmId, nativeBotId, purpose)`. Identity must not be inferred from a display name; a group turn requires a verified selected speaker. A read-only result should distinguish requested and effective provider/model, policy version, source, observed timestamp, readiness and unavailable/stale reason. An unknown rate, allowance, budget, identity, credentials or provider state is not healthy or zero. Treat the following as an illustrative field sketch, not an existing endpoint or agreed wire schema:

```json
{"scope":{"gameId":"example","realmId":"example-realm","nativeBotId":"example-bot","purpose":"conversation"},"identityStatus":"unverified","requested":null,"effective":null,"version":null,"source":"synthetic example","observedAtUtc":null,"availability":"unavailable","reason":"identity unverified"}
```

Resolve an enabled exact override first, then an explicitly configured purpose default. No valid route means unavailable and native safe behavior continues. Native combat, healing, movement and recovery remain local. Never silently select a different paid provider/account; fallback requires explicit approval. No provider policy is accepted as a chat instruction. Existing r10/e8 provider policy is per-purpose/global and does not implement this per-bot read model.

## Future changes, still held

A future separately authorized administrative change requires versioned compare-and-set, actor/time/reason and old/new audit, validated game/realm/native bot binding, and an allowlisted provider/model/account route, budget and approved fallback policy. Changes cannot add credentials, modify access or budgets, authorize fallback, or start a game action. Requests and retries must pass native safety/deadline gates. Each model attempt reserves and settles through the authoritative ledger with request/idempotency key, game, realm, bot or party, purpose, provider/model, latency, cost basis and safe error classification. Unknown rate, allowance, authorization or budget fails closed. Retries are distinct attempts under one request and cannot duplicate native actions. Existing spend attempts lack full game/bot/party attribution; v1 and fresh v2 ledgers remain separate until continuity is proven.

“One model for all bots” needs a precise hub-owned contract. Review must settle the target set and purpose scope, atomicity and concurrency/version checks, precedence with exact per-bot overrides, handling newly registered or unverified bots, failure/partial-success reporting, and individual audit attribution. The local in-memory simulation is an example over a fixed explicit fixture set; it does not define or implement the hub behavior. The UI controls remain disabled.

## Review questions

1. Which revision and read endpoints are approved for each environment, and what are their scope, costs, freshness, pagination and failure semantics?
2. What verified identity and source timestamps can each adapter actually supply, including FFXI group speaker selection?
3. What are the exact versioning, global-scope, compare-and-set, audit, rollback and partial-failure semantics?
4. How are provider/model/account allowlists, budgets and fallback approved without exposing credentials, and how are unknowns handled?
5. Which ledger provides request-to-attempt attribution, and how will version, availability and reconciliation be established without merging separate stores?

No live health polling, tokens or service writes are approved by this draft. Blizz approved the design draft; the owning hub lead must review its unresolved details before any proposed shape is treated as an implemented authoritative contract. Separate authorization is needed for future live changes.
