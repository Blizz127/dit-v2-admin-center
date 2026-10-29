# Admin Center API

Status: local presentation contract, draft pending coordination with the DIT v2 lead. Optional live reads use the source-reviewed r10 shapes; actual deployed revision is unverified. These are endpoints of this scaffold, not claims about hub r10 or its ledger. The browser never calls the hub directly. Blizz authorized read-only live hub calls; trusted SSH access has been verified; authenticated reads await the existing plaintext token file location. No live hub call has been made.

All responses are JSON and `Cache-Control: no-store`. Requests to `/api/*` require `Authorization: Bearer <owner token>`; absent or incorrect tokens receive 401. The token must be provided to the process as `ADMIN_TOKEN` and is never included in responses. No mutation endpoints exist. Optional upstream reads are restricted to `/v1/control/bots`, `/v1/control/learning` with `light=true` and `tasksOnly=true`, `/v1/control/server-status`, and explicit `/v1/control/trace`, `/v1/control/health`, and candidate-only `/v1/control/interaction?limit=50` queries; each game/view has independently labeled synthetic fallback. Read-only overview requests share an in-memory snapshot for up to 15 seconds, retaining original fetch times; token-file metadata changes invalidate it. Unknown API paths return 404. No CORS access is provided.

## GET /api/hub-health

Requires the owner token and configured hub access. On explicit request, reads the upstream service-health snapshot; the r10 route may invoke read-only Docker and systemd inspection and can take time. Projects up to 50 FFXI/SWTOR records, omitting internal paths, environment and log data; service state does not establish bot presence. Shares a short 15-second cache and fails closed to unknown on errors. No automatic polling is performed.

## GET /api/trace?gameId=&correlationId=

Requires the owner token and an explicitly configured hub URL and token file. Fetches an allowlisted read-only upstream trace only on explicit request. Accepts FFXI or SWTOR and a bounded identifier. Returns envelope kind, type, occurrence time and outcome classification/disposition/finality when reported; raw envelope bodies are omitted. At r10 the hub scans a bounded recent window and returns at most 250 records, so an empty result does not prove absence or delivery. Hub access is currently unconfigured pending the token-file decision.

### Local trace validation and error ordering

Owner authentication is checked first (401 on failure). The local trace route
then requires exactly one `gameId` (`ffxi` or `swtor`) and one `correlationId`
(1–128 ASCII letters, digits, underscore, dot, colon or hyphen), with no other
query keys. Invalid requests return 400 before configuration lookup or reader
construction, including when the hub is unconfigured. A valid request with
missing configuration returns 503. Reader unavailability returns 503; malformed
trace response data returns 502. Error bodies omit upstream exception text,
token paths and raw evidence. These are local Admin Center statuses, not a claim
about deployed upstream behavior.

## GET /api/interaction


Owner authentication and configured hub access are required. On explicit request only, calls candidate e8c81be `GET /v1/control/interaction?limit=50`, an Admin-only route absent from r10. Source inspected: `InteractionAdminApi.Describe`, `FfxiInteraction.Views`, and `ActionLedger.Describe`; these read in-memory state and ledger copies without dispatch or switching. This does not establish the deployed revision. A 15-second cache preserves the original fetch time. The local route accepts no parameters or writes.

Returns reported `switches` (contract, natural orders, self claims), `freshForSeconds`, `truncated`, FFXI `bots`, `fetchedAt` and coverage. Actor identity retains caller and server-instance scope and is not joined to the roster. Reconciled `fresh` and `snapshotFresh` are distinct; activity is unknown unless contract collection and reconciled freshness are explicitly true. Off or unknown collection yields no current inventory. Raw orders, requesters, receipts, chat and state-counter payloads are omitted. Unknown fields stay unknown. This endpoint has only been tested offline; the UI offers a separately labeled synthetic preview that makes no network request.

### Offline interaction contract verification

`tests/test_interaction_contract.py` validates the f95fe8a handoff in `HUB-CONTRACT-DRAFT.md` using `tests/fixtures/interaction-e8c81be.json`, a synthetic fixture shaped from the recorded candidate DTOs. It drives `HubReader.interaction`, the projection and the 15-second cache through an in-memory HTTP response. Socket connection attempts fail the test; no hub credential or live response is used. Coverage includes the exact GET/limit, scope preservation, independent freshness, off/unknown collection, omission of private fields, original cache fetch time, copy isolation, duplicate identity rejection, malformed timing values and refusal of proposed routing endpoints. Oversized timing integers remain unknown rather than raising an overflow. This verifies the local reader only, not live endpoint availability, deployment, or an agreed model-write contract.

## Local response and error envelope audit

Expected API errors return `application/json` with exactly one nonempty string
field, `{"error":"..."}`, plus `Cache-Control: no-store`, `nosniff` and a matching
Content-Length. Messages are fixed local descriptions; no upstream exception,
token path, request method/query or raw evidence is reflected. Unsupported API
methods now use this envelope too, rather than the standard library HTML page.
HEAD retains the error status/headers and representation length but sends no body.
This describes recognized error paths, not a blanket catch of programming errors.

| Read endpoint | Successful response | Expected failure states |
| --- | --- | --- |
| `/api/overview` | 200 overview object with explicit per-feed fallback labels | 401 auth; 400 query. Missing/failed optional feeds can remain 200 with synthetic fallback, never implied live success. |
| `/api/trace` | 200 `records`, `fetchedAt`, `coverage` | 401 auth; 400 scope or reader configuration validation; 503 missing configuration/read failure; 502 invalid trace payload. |
| `/api/hub-health` | 200 `services`, `fetchedAt`, `coverage`, `source` | 401 auth; 400 query; 503 missing configuration/read failure; 502 invalid response/configuration. |
| `/api/interaction` | 200 projected switches, freshness, truncation, scoped bots, fetch time and coverage | 401 auth; 400 query; 503 missing configuration/read failure; 502 invalid response/configuration. |
| `/api/bridge-status` | 200 observation object, including Unknown fields when observation fails | 401 auth; 400 query. Observer failure is represented as Unknown with null observation time, not fabricated 502/503. |

Unknown authenticated API GET paths return 404; unsupported methods return 501.
The method rejection occurs before route authentication or dependencies, as in
the existing standard-library dispatch. GET authentication remains first.
Trace's existing configuration-validation status differs from the two cached
views; consumers must use the status and error envelope, not parse message text.

Offline reader decoding checks also cover malformed UTF-8/JSON and a 10,000-level
nesting fixture: decoding failures become redacted `HubReadError`. The one-MB
response limit still produces the distinct `HubResponseTooLarge` class; a later
valid read recovers. These tests inject byte streams and synthetic credentials,
not HTTP transports. Runtime decoder limits are not an agreed JSON depth contract.

Trace envelopes can themselves contain a JSON string body. If that inner body
is malformed or exceeds the decoder's nesting limit, the existing tolerant
projection retains valid envelope metadata and returns null classification,
disposition and finality. It never returns the raw body or infers success. This
differs from failure to decode the entire upstream response, which is a read
error. An in-memory handler check covers the deeply nested inner-body case.

Stored XP rate and synthetic spend projections treat values that overflow the
finite-number check as null (Unknown), alongside non-numeric, boolean, negative
and non-finite values. Valid zero and positive finite numbers remain values.
Pricing/scope checks still apply. Synthetic pipeline checks verify that an
invalid rate does not abort other game feeds; no live spend route is enabled.

Empty/whitespace-only or truncated upstream response bytes are read failures,
not empty service collections. Interrupted HTTP responses (`IncompleteRead`
and other HTTP protocol exceptions) become the same redacted read error, with
the response context closed. A later complete JSON response can recover.
Empty inner trace-body strings are different: valid envelope metadata remains
with null outcome fields, as described above.

Mixed-row fixture coverage confirms valid trace outcomes and interaction
activities remain alongside Unknown rows. Health excludes out-of-scope games
and retains Unknown for unsupported states or missing labels/timestamps.
Malformed record structures or missing interaction identity reject the whole
projection; a valid prefix is not presented as a complete successful response.

### Timeout, partial-feed and recovery semantics

`tests/test_offline_feed_recovery.py` connects the real reader, cache and overview
merge using synthetic byte streams and an injected clock. Each refresh makes
one attempt for each of the six game/view reads; no automatic retries or page
continuations are implemented. Each opener call receives the existing three-second
timeout; the test raises a synthetic timeout rather than measuring elapsed time.

At 15-second cache expiry, a timeout, truncated JSON or malformed collection
replaces that feed's old rows with explicitly synthetic fallback. Successful
game/view slices survive independently. A complete empty roster clears that
game's previous examples, while an invalid collection never returns its valid
prefix as a complete page. Partial-feed results use the normal cache lifetime;
a later explicit refresh after expiry can recover. Cached fetch timestamps are
preserved; unavailable feeds have no fetch timestamp. These fixture checks do
not establish upstream availability, pagination support or bot presence.

## Query and method rejection

Overview accepts at most one `source` field; trace requires exactly one `gameId`
and one `correlationId`. Both parse UTF-8 strictly and reject bare fields, empty
separators and excess fields with 400 before collection/configuration reads.
Valid percent-encoded values and either trace-field order remain supported.
An absent overview query still selects mock data. Authentication precedes
query validation, including malformed requests.

Unknown `/api/` GET paths require owner authentication and then return 404.
POST/PUT/PATCH/DELETE are not implemented and return 501 before dependencies
are reached. They do not enable control actions or parse a write payload.
Focused in-memory checks cover this behavior across all five read APIs; no
running service was contacted or restarted for this source change.

## GET /api/bridge-status

Takes no query parameters. After owner authentication, any nonempty query
returns 400 before the observer is called; rejected tokens still return 401
first. The normal parameter-free UI request is unchanged. This is verified
through the in-memory handler; the running service has not been restarted.

Requires the owner token. Returns a bounded read-only observation of the FFXI bridge unit and private fault marker via verified SSH to Banshee. The observer caches results for 15 seconds, reports unavailable or unexpected data as unknown, and never reads chat, restarts a service, modifies a marker or returns credentials. The browser refreshes while the workspace is visible. Marker absence does not establish successful delivery; service and marker states may change between observations.

### Bridge observation failures

The owner token is checked before the observer runs: missing or wrong tokens
return 401, and unsupported POST requests return 501 without invoking it.
An authenticated bridge observation that encounters a local permission error,
SSH failure or timeout returns HTTP 200 with all observation fields Unknown
and `observedAt: null`. HTTP success here does not mean service health or
successful SSH access. Raw command output, stderr and exception text are omitted.

The observer uses an eight-second runner timeout and a fifteen-second cache.
When an expired healthy snapshot fails to refresh, Unknown replaces it; the
old healthy state and timestamp are not returned as current. Unknown is cached
until the next eligible request, which may recover. In-memory tests inject a
fake runner and clock through the real handler/observer; they do not make an
SSH connection, verify a host or observe a real service.

The bridge UI clears prior healthy text from both cards after rejected HTTP,
malformed JSON or transport failures. It allows only one bridge request in
flight and starts none without a token or while the workspace is hidden. Late
successes and failures are discarded if the workspace is hidden or the token
has changed since the request. `tests/bridge_view.test.js` checks this with
deferred responses and a simulated DOM; no browser or live bridge is used.

## GET /api/overview?source=mock|hub


The source defaults to `mock`; `hub` explicitly requests optional allowlisted upstream reads, and unrecognized parameters return 400. Mock mode never reads the hub token file. Returns `{ "mode": "mock" | "mixed", "hubFeeds": [...], "generatedAt": <UTC ISO timestamp>, "ownerAttention": {...}, "ffxiFocus": {...}, "bots": [...], "gameStatus": [...], "serviceHealth": [...], "leads": [...], "leadMonitoring": [...], "leadActivity": [...], "leadTimeline": [...], "nudgeHistory": [...], "sessionMarkers": [...], "quotaHistory": [...], "assignmentHistory": [...], "safetyRecords": [...], "botDetails": [...], "replyEvents": [...], "modelCalls": [...], "audit": [...], "ledger": [...], "learningArtifacts": [...], "learningPlan": [...], "learning": [...], "issues": [...] }`. `ffxiFocus` is a dated project-evidence and coordinator-approval summary, not a deployment receipt or proof of delivery; operational toggles are not connected. Owner attention reads only unexpired, pending, owner-sourced coordinator approval records scoped to the two DIT projects; it cannot capture decisions tracked elsewhere. Bot and learning records may be live or synthetic per game/view, identified by `hubFeeds` and record sources. Ledger and network/bot issue examples are synthetic; lead coverage and watcher issues use coordinator data. `gameStatus` projects a stored settings snapshot with observation time and XP rate where available; server liveness and freshness are unknown, and internal paths and MOTD are omitted. The roster and service-health examples include offline projections of synthetic r10-shaped records; duplicate roster keys invalidate that game roster feed and retain labeled synthetic fallback; registration is not presence and service status is not bot health. One FFXI learning task is passed through the offline r10 projection using a synthetic task-only fixture, and its unverified status appears as a learning attention item. Leads are a narrow read-only coordinator task-board projection. Each bot has `id`, `name`, `game`, `status`, `source`, and `observedAt`; a hub roster can include bounded `character`, `level`, `bodyKind`, and `personalitySummary` metadata, which do not establish presence or demonstrated behavior; an optional synthetic `routing` example separates `purpose`, `requested`, `effective`, `version`, `source`, `observedAt`, `availability`, and `reason`. This is an illustrative local shape, not an agreed hub contract or a real configuration. `leadActivity` contains the latest tracked coordinator task status, bounded summary and timestamp, plus checkout HEAD commit time; the latter is not attributed to a lead. Summaries resembling credential material are withheld. Missing data is unknown. Lead records have `name`, `scope`, `status`, `source`, and `observedAt`. The hub lead shows the latest tracked task status and its update timestamp if available; the Admin Center lead is unknown until board data exists. A task record does not establish current activity. `leadMonitoring` provides per-lead stall and quota states and reasons; stall is the latest exact matching coordinator watcher classification with its check time when unambiguous, otherwise unknown; quota is unknown without a connected per-lead quota source. For a known lead provider, `poolCapacity` may display the coordinator’s cached shared-provider estimate when at most 180 seconds old, with its check time; it is not an individual lead quota or a guarantee of availability. The nudge history shows up to 20 scoped coordinator watcher records or heuristic stall-watch text matches per project, without message text; elapsed reply time starts at creation and is not time to resume. A separate optional `resumeSignal` reports the first observed tool request after delivery before the next matching nudge, only for the exact unique active Codex thread and sufficient bounded-rollout coverage. It is a heuristic, not proof of resumption or causality; absent, ambiguous, truncated or unsupported cases are unknown. A past watcher classification may be stale. `leadTimeline` contains up to ten recent task events and ten attributed watcher alerts per lead, plus available current watcher and tmux session-activity timestamps, and up to ten checkout HEAD ancestry commits, with source and timestamps, without task text. Checkout commits are not attributed to leads and other branches are not covered. Session activity does not establish a stall or a stopped goal. `sessionMarkers` scans at most the latest 256 KiB of the uniquely identified Admin Center Codex rollout for narrowly matched native system-event markers, returning timestamp and classification only, not text. These are historical heuristics; missing matches do not prove an active goal or available quota. The hub/behavior-platform lead is matched through one live Claude native session with exact cwd, tmux and protocol, or through a unique coordinator Codex handoff marker and matching thread metadata. Handoff binding alone does not prove a live process. Unavailable or ambiguous bindings remain unknown with a reason. Missing watcher coverage is unknown; task events are not stall classifications. No per-lead quota history is available, and the separate pool value is a snapshot. `quotaHistory` contains up to 100 cached Codex account-window observations, pseudonymous account identifier, observed timestamp and remaining percentage; it does not attribute accounts to leads or establish current quota. A background collector reads only cached state, stores no emails or credentials, excludes SBISD entries, deduplicates and retains at most 10,000 window observations in ignored local SQLite; it never refreshes accounts. `sessionActivity` is the tmux session activity timestamp for the identified hub lead session, not a measure of progress or a stall; unverified sessions remain unknown. `safetyRecords` are synthetic examples; they do not establish actual gate or kill-switch state. `botDetails` contains only synthetic per-bot goals and memories. No live bot-detail call is wired because the r10 GET can import progress. `replyEvents` are synthetic per-bot examples of wording origin, fallback, generation status, delivery and verification; no live reply source is wired. A generated wording result alone is not delivery evidence. `assignmentHistory` is synthetic, keyed by fixture-local bot ID, with requested/effective state and recorded time; it is not real audit or routing history. `spendExample` is a synthetic single-ledger projection; missing budget, rates and attribution remain unknown, and separate ledgers are not reconciled. `modelCalls` are synthetic examples; null cost or quality means unknown, not zero. Audit records are synthetic examples only; no admin action is recorded. Ledger records have `correlationId`, `botId` (fixture-local identity), `bot`, `request`, `result`, and `verification`; `pending` or `unknown` must not be rendered as success. `learningArtifacts` are synthetic examples of dataset or policy validation, adoption and outcome states; they do not establish real weights or artifact verification. `learningPlan` is a static project planning checklist, not a live finding or verified gap; it is independent of live tasks. Learning entries have `id`, `game`, `topic`, `status`, `evidence`, `datasets`, `policy`, and `source`; r10-shaped tasks can also include `phase`, `escalation`, and `retryAt`, with missing values unknown; Synthetic network/bot examples, the dated historical FFXI bridge evidence, and read-only coordinator lead and pending-decision issues have `title`, `detail`, `status`, `scope`, `source`, and optional `updatedAt`; absent update times are unknown. A hub-binding coverage issue includes a read-only `suggestedFix` when its session cannot be identified. A watcher STOPPED classification concerns a session, not a goal; goal status remains unknown without a source. A fixture issue can carry `botId` for exact matching to a bot; absent matches do not establish health. A task-derived issue can carry a `learningId` linking to the corresponding fixture-local learning item.

The mock is intentionally small; it is not a substitute for upstream schemas, pagination, complete roster coverage, audit, usage metrics or actual policy verification. Before integration, agree with the hub lead on endpoint versions, authentication, source and freshness, pagination, correlation, error behavior, authorization, audit, and command idempotency. Treat unavailable values as unknown and unavailable actions as disabled.

`leadMonitoring` includes `provider`, `binding`, and `bindingObservedAt`. A Codex provider is shown only when the coordinator handoff, native process executable/working directory/explicit resume thread, and native thread database agree. Command lines and handoff prompts are never returned. This is an observed process identity, not proof of work, goal state, or account quota. Watcher classifications require an exact project/provider/thread match and a timestamp within the last 180 seconds; missing or stale observations remain unknown. Provider-pool estimates stay separate from individual lead quota. Unsupported provider or resume forms remain unverified.

## Source-reviewed hub surface (r10, b089a2c)

This is a source reading guide; Blizz has authorized read-only live calls, but access and deployed revision remain unverified. `AdminCenter.cs`, `ControlCenter.cs`, `CompanionApi.cs`, `HubApi.cs`, `HubTokens.cs` and `Program.cs` in the identified baseline are authoritative for the source revision. The listed `/v1/control/*` GET routes explicitly require an Admin Bearer and return 403 on missing/invalid authorization: `overview`, `health`, `bots?gameId=`, `bot?gameId=&key=`, `providers`, `ai-spend`, `goals?gameId=`, `learning?gameId=`, `relationships?gameId=`, `server-status?gameId=`, `companion`, and `trace?gameId=&correlationId=`. A separately configured admin listener requires Admin for `/v1/*` and returns 401 before routing. The earlier handoff reported no approved admin listener or admin token; the later owner authorization permits use of the existing hub access token for read-only calls. Keep hub credentials server-side; an existing approved token file is needed and its path remains unverified.

The source's main listener leaves `/v1/health`, `/v1/games`, `/v1/status`, `/v1/jobs`, `/v1/personas` and `/v1/scorecards` open. Knowledge list and history return metadata without the document payload's adapter-private check; individual adapter-private document payload access requires Admin or a same-game Adapter. Review exact access semantics before integration; do not assume metadata is confidential.

`bots` lists persona/body records, not confirmed presence. `trace` searches envelopes by game and correlation ID (invalid or over-128-character IDs return 400; unknown games return 404); correlation alone does not prove game outcome. `learning` caps query text at 128 characters, reports a 120-item history limit, and its light/task-only options omit evidence or other panels. `ai-spend` calls a ledger `Open()` routine that can initialize SQLite schema and WAL; it is not wired under read-only authorization. `overview` caches slow aggregates for 20 seconds; its source notes full-table scans and lock contention. `health` inspects services. Notably, `bot` and `goals` call `ImportProgress` even though they are GET routes; do not assume a GET is side-effect-free. Route fields, costs and behavior must be checked against the selected revision before any authorized integration. Only allowlisted reads are wired; health is on-demand and is not polled automatically.

The e8c81be candidate adds interaction and knowledge-use APIs; their presence is candidate-only and does not establish live deployment. Per-bot model switching and complete spend attribution are not implemented in either handoff revision.

The proposed per-bot routing contract is in `dit-v2-release-20261027/custody/per-bot-model-routing-draft.md`. It is design only: no read or write endpoint has been agreed or implemented. Future UI must preserve verified identity and requested versus effective state, report unavailable/stale reasons, and never infer per-bot routing or attributed cost from current global provider and ledger data. Blizz approved the design draft; model controls remain disabled pending the hub implementation and separate authorization for live changes.

## Learning evidence checklist display

The learning inspector includes a collapsible, read-only FFXI evidence checklist.
It uses the selected loaded learning record for game, topic, source, update time
and evidence availability. Five evidence states remain Unknown because no structured native
identity, navigation/mission outcome, party/job evaluation, grounded-memory
evaluation or policy-outcome assessment is connected. A task marked verified
does not change those states. Other games show an explicit non-applicable
message, and missing or cleared selections remove the prior context.

This is client-side review guidance: it adds no endpoint, storage, request,
mutation or inferred link to a bot. Filtering the task list retains the selected
inspector as before; its existing hidden-selection notice still applies.

### Why verified tasks still have Unknown game assessments

`HubReader.get('learning', game)` sends `light=true&tasksOnly=true`. Candidate
e8c81be `AdminCenter.cs` maps that response through `LightTask`, explicitly
omitting evidence. `r10_projection.project_learning` preserves task status and
reports evidence as `Not included`, `Present` or `Unknown`; it does not forward
raw evidence or arbitrary assessment fields. Dataset and policy states remain
Unknown. The UI now explains omitted evidence separately from evidence reported
present without a structured assessment. Neither state supplies the five
game-evidence assessments. Full-task reads are not added by this change.

The projected `hasModelAnswer` field preserves a literal boolean from the light
task payload; missing values and non-booleans become null. The inspector labels
this “Model answer reported: Yes / No / Unknown”. This is an upstream flag, not
the answer body, an outcome, model availability or authorization to call one.
It does not change any checklist assessment. The synthetic route-evidence task
reports Yes while its task remains unverified and its evidence is omitted.

`tests/fixtures/learning-evidence-e8c81be.json` is a handcrafted synthetic fixture
based on candidate e8c81be `AdminCenter.cs:LightTask` and
`Store/AdministratorLearningStore.cs:AdministratorLearningTask` (source checkout
and these files inspected read-only). Its four cases cover verified tasks with
an answer flag and omitted evidence, false with null evidence, true with opaque
full-task evidence, and a missing flag. The opaque evidence object is a privacy
canary, not a defined gameplay-outcome schema. Tests additionally reject string,
numeric and container values as flags. No full-task read is enabled; even if
such evidence is supplied offline, only its presence is projected.

### Offline synthetic mapping example

“Preview synthetic evidence mapping” replaces the checklist display with an
independent local fixture, without changing task selection or fetching data.
“Show selected need evidence” restores the selected record. The fixture models
`identity`, `navigation`, `party`, `memory` and `policy` criteria. Each explicit
example needs matching game/task scope, one assessment per criterion, an
allowlisted state (`supported`, `missing`, `conflicting`), nonempty source and
evidence text, and a parseable observation time. Missing, duplicate, invalid or
mismatched entries remain Unknown. All mapped states are labeled synthetic;
observation time does not imply current freshness. No assessment is derived from
task status, counts, acceptance or presence of raw evidence.

This fixture shape is local UI test data, not a proposed or implemented hub
contract. A compatible authoritative evidence contract remains unresolved. The
preview never reads a review object from a loaded task or enables any controls.

## Connected trace fixture coverage

`tests/inspector_integration.test.js` now covers the trace form end to end
within the offline harness: shipped template IDs and actual app handlers,
in-memory Python HTTP dispatch, injected synthetic reader, real trace
projection, JSON serialization and simulated-DOM rendering. Pending outcomes
remain non-final, empty results do not establish absence of actions, and error
states replace previous trace data. Cases cover 401 before reader invocation,
502 invalid response, 503 read failure/missing configuration, local correlation
validation, recovery and Clear. No transport, token file, hub, database or
listener is used. The overview collector remains stubbed, and browser-engine
execution/layout remains unverified.

## Connected interaction fixture coverage

The browser-free integration command also passes the nine generated candidate
snapshots through `project_interaction`, the actual in-memory HTTP handler and
the actual interaction UI renderer with shipped-template IDs. The fixture
adapter verifies each snapshot against its imported manifest before using it.
Its cache lookup is injected; no real cache, token file or transport is used by
this connected path. Reader/cache timing has separate offline contract coverage.

Assertions preserve a fresh reconciled view with stale raw snapshot and an
unknown reconciled activity with fresh raw snapshot, three distinct caller/server
scopes for the same actor key, empty collection, hidden retained inventory when
off, and the 50-actor truncation flag. Additional scenarios cover 401 before
lookup, malformed projection (502), failed/missing configuration (503), recovery,
no-request synthetic preview and source-change clearing. Raw requester data and
private error canaries are omitted. These checks do not establish native roster
identity, outcome delivery, a deployed revision or real-browser behavior.

## Connected service-health fixture coverage

The browser-free integration command also drives `/api/hub-health` through the
real handler and `project_hub_health`, injecting only the cache lookup. It checks
FFXI/SWTOR scope, unsupported state -> Unknown, timestamps, empty coverage,
401 before lookup, malformed payload (502), failed/missing configuration (503),
recovery and source reset. Each denial/failure replaces previously displayed
service records. Private log/environment canaries and other-game records are
omitted. Mock-source refresh makes no request. These are synthetic fixture
results, not service observations, cache-timing tests or browser-engine results.

## Connected bridge fixture coverage

The same connected harness exercises `/api/bridge-status` using the actual
`BridgeObserver` with an injected command runner. Active/absent-marker and
failed/delayed-delivery-marker observations reach both bridge cards. Empty or
malformed output, permission denial and timeout produce HTTP 200 with Unknown
fields and no observation time; they are not fabricated 502/503 responses.
Owner-token rejection returns 401 before the runner. Both cards discard prior
observations on failure and recover after a later successful read, retaining
the warnings that marker absence and service state do not prove delivery.
Private payload/exception canaries are omitted. No SSH command runs; each
exchange creates a fresh observer, leaving TTL behavior to the separate offline
handler test. This does not verify a running bridge, browser layout or delivery.

## Client asynchronous response audit (2026-10-29)



The browser uses a local session counter as well as each request's captured
token. Login submission increments the counter even if the token text is the
same. A load failure that closes the workspace also increments it. Both events
clear the prior selected snapshot, bot/learning selections and optional read
panels. This is client display isolation, not a change to server authorization.

| Async view | Existing ordering guard | Session isolation |
| --- | --- | --- |
| Overview (all overview-backed panels) | Latest overview request wins. | Token/counter must match; a refresh started in a visible workspace cannot render after it becomes hidden. Initial login may open the hidden workspace. |
| Interaction | Source changes, new request and synthetic preview invalidate prior replies. | Visible workspace plus matching token/counter required for success and failure. |
| Hub health | Source changes and newer health requests invalidate prior replies. | Visible workspace plus matching token/counter required for success and failure. |
| Trace | Source or search-scope changes and newer trace requests invalidate prior replies. | Visible workspace plus matching token/counter required for success and failure. |
| Bridge and FFXI bridge summary | One request in flight. | Visible workspace plus matching token/counter required, including same-token re-login. |

Optional panel reads start only with a token and visible workspace. Old requests
are ignored on completion; this does not cancel an already dispatched read.
Synchronous filters, inspectors and synthetic previews have no independent
network response to audit. Offline deferred-response cases cover each async
path's success and failure behavior plus normal rendering and initial login.
Actual browser/DOM-package execution and deployed-service verification remain
parked; no live requests or restarts were used for this audit.
