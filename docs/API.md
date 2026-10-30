# Admin Center API

Status: local presentation contract, draft pending coordination with the DIT v2 lead. Optional live reads use the source-reviewed r10 shapes; actual deployed revision is unverified. These are endpoints of this scaffold, not claims about hub r10 or its ledger. The browser never calls the hub directly. Blizz authorized read-only live hub calls; trusted SSH access has been verified; authenticated reads await the existing plaintext token file location. No live hub call has been made.

All responses are JSON and `Cache-Control: no-store`. Requests to `/api/*` require `Authorization: Bearer <owner token>`; absent or incorrect tokens receive 401. The token must be provided to the process as `ADMIN_TOKEN` and is never included in responses. No mutation endpoints exist. Optional upstream reads are restricted to `/v1/control/bots`, `/v1/control/learning` with `light=true` and `tasksOnly=true`, `/v1/control/server-status`, and explicit `/v1/control/trace`, `/v1/control/health`, and candidate-only `/v1/control/interaction?limit=50` queries; each game/view has independently labeled synthetic fallback. Read-only overview requests share an in-memory snapshot for up to 15 seconds, retaining original fetch times; token-file metadata changes invalidate it. Unknown API paths return 404. No CORS access is provided.

## Request limits at a glance

These are implemented local-source limits, not pending write-endpoint features
or claims about the currently running service.

| Resource | Limit/policy | Outcome |
| --- | --- | --- |
| Request line | 65,536 bytes including line ending | Redacted 414 beyond limit |
| Entire header block | 65,536 bytes including final blank line; stdlib line/count checks also apply | Redacted 431 beyond limit |
| Combined line and headers | At most 131,072 accepted bytes; at most one excess detection byte | 414 or 431 according to the section exceeding its limit |
| Application body consumption | Zero; GET body framing rejected, write methods unsupported | GET 400 / write 405; no body parser or drain |
| Idle socket I/O | Five seconds | Attempt 408 while acquiring request; otherwise close |
| Total line/header acquisition | Ten seconds, monotonic and never reset by progress | Attempt redacted 408, close |
| Active handlers | 16, no application waiting queue | Excess accepted connection closes before parsing; no HTTP response |

Size, timeout and method failures close the connection. Socket buffering/kernel
reception is separate from application consumption. Collector runtime, response
size and requests per second are not bounded by the acquisition-size/deadline
policy; do not describe it as a universal process-memory or execution-time cap.

The combined-boundary check passed alongside the existing oversized-body refusal
check: exactly 65,536 + 65,536 bytes reached ordinary authenticated unknown-route
handling (404); one extra request-line byte returned 414 after 65,537 consumed
bytes, and one extra header byte returned 431 after 131,073 consumed bytes.
Trailing body bytes remained unread in every case and no collector ran. These
two focused checks were in-memory, not new socket timing or browser evidence.
Detailed measured socket/refusal/admission evidence appears later in this document.

## Synthetic routing audit field in GET /api/overview

`routingAudit` contains committed examples from `data/fixtures/routing-audit.json`.
It is a local presentation shape, not a hub endpoint or agreed audit contract.
The server only reads this file; it never imports or invokes the routing simulator.
Missing/invalid fixture data is null and the UI reports Unknown coverage.

Each event has `scopeKind` (`bot` or `all`), actor, reason, fictional time, attempted
model, expected/before/after version and a result explicitly labeled simulated.
The explicit `outcome` tag is `applied` or `rejected`; absent or other values are
displayed and filtered as Unknown, independently of the result text. Scope and
outcome filters combine locally and persist across snapshot refreshes.
Its `changes` list contains explicit fictional game/realm/native-bot/purpose
tuples, before/after requested models and null effective state. The UI does not
join these keys to roster identities or infer effective routing. The all-bots
example covers exactly its two listed fixture targets, not future registrations.
Unknown scope kinds and per-bot events with anything other than one target withhold
requested-change attribution. This is a presentation safeguard, not audit authentication.

The third example is a rejected stale-version attempt with unchanged requested
model and version. It is generated separately from the simulator's success-only
audit list and labeled accordingly. Actual rejection logging, rollback,
partial-success semantics, authorization and authoritative audit provenance remain
hub-contract work. No write route, model call or actual admin audit is added.

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

Unknown authenticated API GET paths return 404. POST/PUT/PATCH/DELETE return
405 with Allow: GET; other unimplemented methods retain 501.
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
POST/PUT/PATCH/DELETE have no write routes and return 405 before dependencies
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
return 401, and unsupported POST requests return 405 without invoking it.
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

## Local reply evidence navigation

The per-bot reply card filters the existing synthetic `replyEvents` list by exact,
case-sensitive correlation ID. It makes no API request. Missing or malformed rows
leave total coverage Unknown while usable scoped rows remain visible. A valid
empty list reports zero loaded examples, not zero actual replies.

“Find loaded ledger evidence” pins the existing ledger view to both the selected
bot ID and correlation ID, without fetching a hub trace. Duplicate or missing
roster identity withholds attribution. This navigation adds no reply-history
endpoint, queue observation, speech verification or provider call.

The ledger count describes returned example rows only. A bot pin filters the
visible numerator while the denominator counts all usable loaded ledger rows.
Missing or malformed list entries make that denominator Unknown; missing or
ambiguous pinned-bot identity withholds the count. A source-load failure retains
the labeled previous snapshot; successful source changes clear the old pin.

## Local model metric coverage

The metric coverage summary derives only from the existing synthetic `modelCalls`
list. A supplied field is a finite, nonnegative JSON number; booleans and numeric
strings remain Unknown. Zero counts as supplied. The local availability filter
changes rows displayed, not the summary denominator. Malformed list entries leave
the loaded total Unknown. No metric endpoint, cost aggregation, quality calibration
or provider call is added. Counts of supplied fields do not verify their provenance
or establish real usage.

## Loaded data coverage overview

The overview derives from existing `bots`, `learning` and `modelCalls` fields
without another endpoint or request. Counts precede local detail filters. A
non-array collection is unavailable; malformed entries make the loaded total
Unknown, while usable rows remain counted. Roster/learning identity counts use
exact nonblank string IDs across the full collection. A repeated-ID count is a
count of affected rows, not distinct IDs or confirmed distinct bots. This is a
presentation summary, not source authentication or completeness verification.

The local roster ID filter checks exact nonblank string IDs against the full
loaded `bots` collection before game/name filters. “Unique” means only one loaded
row has that ID; it is not verified native identity. Filtering adds no API request
or routing operation and cannot make a repeated ID inspectable.

## Roster gap record details

Gap details use positions in the current loaded roster, never display-name or
ambiguous-ID joins. Navigation pins that snapshot row locally; successful refresh
and session reset invalidate it and any retained buttons. No new endpoint, entity
identity mapping, evidence join or routing operation is added. Missing-ID and
repeated-ID records remain unavailable for bot inspection. Malformed non-object
rows report unavailable details and offer no roster link.

## Local roster gap JSON export

`dit-admin-roster-gap-report-v1` is generated from the loaded snapshot only. The
local data-URL download and read-only copy field contain identical JSON. No export
endpoint, filesystem write, upload or fetch occurs. Fields are
`snapshotGeneratedAt`, `selectedSnapshotRow`, `reason`, `differingFields`,
`candidates` (each with `snapshotRow` and allowlisted `fields`) and `limits`.
Candidate fields: `id`, `name`, `game`, `status`, `character`, `level`, `bodyKind`,
`source`, `observedAt`. Nonblank strings are retained; `level` also accepts
nonnegative safe integers. Other values become null. Differences compare these
normalized included fields only; excluded or malformed fields are not compared.
A missing ID yields one candidate, never a display-name join. Row positions and
reported time are not persistent identity or authenticated provenance. A saved
report remains a copy of its original snapshot after the workspace refreshes.
## Local wake verification metadata

Overview responses now include `wakeVerification`, projected from
`data/local/wake-verification.json` on each refresh. This is an owning-lead
supplied local receipt, not an8450 call, credential file or mutation route.
See [receipt format and trust boundary](WAKE-VERIFICATION-RECEIPT.md).
The projection has `schema: dit-admin-wake-readback-v1`, `coverage`, `cutover`
and exactly twelve rows with `game`, `status`, `observedAt` and `receipt`. Status is Unverified, Held or Verified readback (reported).
Per-game authenticated ready evidence must match a completed Banshee8450
cutover; the global cutover flag alone never verifies every game. Held rows
cannot be cleared through this metadata. No actual receipt or live acceptance
was installed as part of the source change.


### Cutover projection

`cutover` is null when the local envelope cannot establish a valid completed
Banshee 8450 cutover. Otherwise it contains only `id`, `destination`
(`banshee:8450`), timezone-qualified `completedAt`, and `receipt`. The source
completion flag must be literal true, the completion time cannot be in the
future, and IDs/references use the bounded content-free format described in
[the receipt contract](WAKE-VERIFICATION-RECEIPT.md). Extra source fields are not
returned. This is a reviewed local report, not remote authentication by Admin.

A valid cutover with an empty game-observation list is still a valid cutover
report, with all twelve rows Unverified or Held. Per-game `observedAt` and
`receipt` are null unless that exact game has one valid matching authenticated
ready readback. A duplicate game observation withholds only that game's claim;
unknown IDs cannot match by name or alias. WAR and Marvel remain Held. An
invalid cutover withholds all per-game positives. Reported readiness cannot lift
lifecycle restrictions, establish current health or certify gameplay/save safety.

Missing, unreadable, oversized or invalid local receipt input yields the default
projection in the existing 200 overview, not a new HTTP error or cached success.
These local reads run on each overview collection and do not use the optional
upstream hub cache. The client clears cutover/readback claims on session reset or
failed refresh. No upload, cutover request, write endpoint or real 8450 request
exists. The standalone preview does not read the local receipt file.

## Reviewed operations-source metadata in GET /api/overview

`operationSources` has schema `dit-admin-operation-sources-v1` and four rows,
with fixed IDs `wake-8450`, `ashes`, `lotro`, and `wake-preparation`. Each row contains:

| Field | Meaning |
| --- | --- |
| `id`, `title` | Fixed source identity and display label; not a roster or controller-ID join |
| `reference` | Reviewed owning-lead document/commit attribution |
| `sha256` | Expected digest of the reviewed note; not an observed service or installed binary hash |
| `reported` | Curated dated summary, retained as historical context even if the file changes |
| `missing` | Evidence not established by that reviewed note; not a new owner hold |
| `state` | Local source-check result below |

The fixed paths and expected hashes live in `operation_sources.py`; requests
cannot choose a path or add a source. Each overview collection reads at most
64 KiB plus one oversize sentinel per note. `state` is one of:

- `Reviewed bytes match`: the local bytes match the reviewed hash.
- `Source changed — review required`: the bytes differ or exceed the limit.
- `Source unavailable`: the local file cannot be read.
- `Not checked in standalone preview`: packaged dated context without any
  external file read during standalone generation/execution.

No raw note text, filesystem path, account information or read-error details are
returned. The reader makes no subprocess, network or service call. An unchanged
note does not prove its reported deployment remains current. Changed sources
require human review and a source update; arbitrary new prose is never parsed
into readiness. Missing/changed source checks remain in the 200 overview and
cannot promote `wakeVerification`. The client clears source-check claims on
session reset/failed refresh and withholds duplicate source identities.

Ashes and LOTRO are outside the twelve-game wake-controller manifest; these
rows describe their owning-lead evidence separately. Neither a deployment note
nor a successful local hash check creates an 8450 binding or verifies a game.
The field is local Admin presentation metadata, not a new upstream hub contract.

Both local evidence readers open nonblocking and require a regular file on the
opened descriptor. FIFO/directory inputs and a symlink at the final filename
produce their existing unavailable/unverified defaults in the 200 overview;
there is no wait for a FIFO writer and no cached positive fallback. Parent-path
symlink resolution is not prohibited by this check. Existing regular-file byte
limits and oversize semantics remain unchanged.


`wake-preparation` is a separate source-only staging row for DIT `fd18286`'s
intake gate and local blocker review. It is not the `wake-8450` transport receipt
and cannot supersede that dated runtime observation. Even a clear staged local
review grants neither writer transfer nor runtime verification. No gate status,
journal contents, player count or save acknowledgement is collected by Admin.

The wake-readiness filter and displayed counts are browser-local derivatives of
`wakeVerification`; they add no API field or request. Selection survives refresh
but resets with the session. Failure-cleared readbacks cannot be recovered from
the cached overview by changing the filter. Count labels explicitly describe the
twelve mapped rows, not current service health or all retained game restrictions.

## Malformed GET request-target parsing

A malformed bracketed authority in an absolute-form GET target could make
`urlsplit` raise before the handler sent any response. The handler now catches
that parser failure, closes the connection and returns 400 with the fixed JSON
body `{"error":"invalid request target"}`, no-store/nosniff headers and a correct
Content-Length. It never reflects the target, embedded user information or
parser exception, and does not invoke a collector or upstream dependency.

This protocol-level rejection occurs before a route can be identified, including
with absent, wrong or valid Authorization headers. Once the target parses,
existing API authentication still precedes query validation/collection. The
parsed target is reused for route/query dispatch; valid encoded queries and
default overview behavior are unchanged. This is not a blanket catch of handler
programming errors or a new policy for every unusual URI form.

Five focused in-memory handler checks passed: malformed authorities and subsequent
valid-request recovery, unauthorized refusal, malformed query refusal, valid
encoded/default queries and existing redacted error envelopes. Sockets, real
collectors, databases and subprocesses were forbidden. No listener, token read,
service restart or device action occurred; the standalone artifact is unchanged.


## POST/PUT body refusal on read-only surfaces

The server has no mutation endpoints or accepted write-payload schema.
POST/PUT/PATCH/DELETE now return **405 Method Not Allowed** with the fixed JSON
body `{"error":"method not allowed"}`, `Allow: GET`, `Connection: close`,
no-store/nosniff and the correct response length. This includes the admin and
bridge APIs, unknown targets and static resources. The rejection precedes
route authentication and dependencies, as did the previous generic 501 refusal;
GET authentication and access rules are unchanged. Other unimplemented methods,
including the existing HEAD behavior, retain their documented 501 response.

The handler does not read, decode or drain the body. Oversized actual payloads,
huge declared lengths, missing bodies, non-JSON bytes, invalid UTF-8, arrays,
nulls, strings, numbers and object payloads all receive the same method-level
4xx. The body cannot become a follow-up request because the connection closes.
Chunked/contradictory framing does not cause a body wait or JSON parse. This is
not a new accepted POST route or a payload-validation contract for future writes.

Six focused in-memory handler checks passed, covering POST/PUT payload refusal
across all five read API endpoints, declared/chunked/absent bodies, explicit
connection closure and unchanged unknown-method/HEAD behavior. Body read/JSON
parse attempts and live dependencies were forbidden in the new payload check;
no listener, credential read, service restart or device action was used.
Existing socket-suite status expectations were aligned to 405, but that broader
suite was not run for this focused change. Standalone preview bytes are unchanged.

Protocol errors raised before write dispatch also use fixed JSON errors. The
handler no longer depends on an already-assigned `/api/` path to redact parser
errors: malformed request syntax can fail before path assignment, and
absolute-form API targets previously missed that check. Parser status codes
remain unchanged (including 400 and 431); unknown methods retain 501. Messages
are `request rejected`, or `method not supported` for 501, without request,
header or parser details. This policy also applies to non-API protocol errors.
HEAD still omits the body; the HTTP parser's framing behavior is unchanged.

A focused memory-only regression reproduced all three HTML error paths before
the fix. Five checks then passed covering those cases, POST/PUT body refusal,
HEAD and API error envelopes. No live dependency or listener was used; no native
browser verification or running-service update is claimed.

## Request headers and idle clients

GET requests reject repeated Host, Authorization, Content-Length or
Transfer-Encoding fields (case-insensitively), parser-reported malformed headers,
any Transfer-Encoding, and any Content-Length other than an ASCII decimal zero.
These return fixed redacted JSON 400 before authentication or collection, close
the connection and never read a body. GET bodies are unsupported; repeated list
headers such as Accept remain allowed. Write methods still take their existing
405 path without parsing or consuming payloads, even with invalid body framing.

The existing 65,536-byte request-line limit returns redacted 414; the standard
library's header-line and header-count limits return redacted 431. The entire
header block also has a 65,536-byte limit, including line endings and the final
blank line but excluding the request line. Acquisition consumes at most one
additional byte to detect an oversized block, then returns redacted 431 without
draining further headers or a body. This prevents multiple individually valid
header lines from combining into a multi-megabyte block. A five-second
socket inactivity timeout now bounds stalled reads and writes. A request-line or
header read timeout attempts a fixed JSON 408 and closes the connection. If
output has already started, no second response is appended; if the peer cannot
receive the timeout response, the connection simply closes.

A separate ten-second monotonic deadline spans the request line and all headers.
It is checked between buffered bytes, with each socket read allowed only the
smaller of the idle timeout and the remaining total time. Thus receiving a byte
or finishing a line does not reset the total deadline. Body bytes are not
consumed by this guard. Timeout responses and ordinary output regain the full
five-second write allowance; collectors are outside the acquisition deadline.

Eight focused offline checks passed for ambiguous/framing headers, valid zero
length and repeated Accept headers, request/header limits, simulated read/write
timeouts, existing write-body refusal and HEAD/protocol errors. The memory
connection records the configured socket timeout; those tests inject TimeoutError
without sleeping or opening sockets. At that checkpoint actual socket timing was
not measured; the local socket-pair checks below now cover it. No service restart,
device run or artifact change.

The aggregate-header follow-up passed five focused checks: exact 64 KiB
acceptance, oversized-block refusal and acquisition bounds, existing line/count
limits, header timeout handling, body refusal and GET framing behavior (the
boundary scenarios share one check). No socket timing or native rendering claim.

Measured local socket-pair checks (no listener or live collector) observed the
default idle timeout at **5.006 seconds**. Request-line and header trickles every
40 ms returned redacted 408 at **0.651 and 0.652 seconds** with test-only limits
of 0.35 seconds idle / 0.65 seconds total. The production ten-second total value
was not separately waited out. Both senders and handlers terminated; responses
had correct JSON lengths and omitted private input. Six focused checks passed,
including aggregate-header bounds, body refusal and response-write separation.
These results establish local socket behavior, not deployed-service or browser
verification.

EOF while acquiring headers is also a refusal: an unfinished line, or complete
header lines without the terminating blank line, returns fixed JSON 400 before
collection. The standard parser previously treated these EOF cases as complete
authenticated requests; a regression reproduced three such collector calls.
An entirely empty connection still closes without a response. Five focused
checks passed after the fix, including valid authenticated requests, aggregate
size bounds, simulated idle timeouts and measured trickle-deadline behavior.

## Write bodies: immediate refusal, no ingestion contract

POST and PUT have no accepted payload schema, body parser, chunk decoder or
drain phase. Their application-level body allowance is zero: after bounded,
deadline-protected headers, they return redacted 405 immediately and close.
This is not a 413 size-validation endpoint. A Content-Length/Transfer-Encoding
conflict, duplicate lengths, huge/invalid lengths and incomplete chunk streams
remain method-level 405 refusals; header acquisition errors retain 400/408/431.
No separate slow-body deadline is needed because the handler never waits for a
body byte. A future write endpoint must define its own bounded ingestion policy
before accepting any payload; this refusal is not permission to add writes.

Four focused checks passed. Local socket pairs measured **24** POST/PUT cases
across admin and bridge routes, withholding every promised body while leaving
the sending side open: the maximum refusal time was **0.006 seconds**, versus
the five-second idle limit. Every response was complete JSON 405 with Allow: GET
and Connection: close, with no 100 Continue. Partial chunks and a trailing
authenticated GET produced one refusal and no reader calls. Existing in-memory
checks additionally forbid body reads/JSON parsing, including actual payloads
over 1 MiB. Socket buffering may prefetch bytes; zero ingestion refers to
application consumption, not a claim that the kernel receives no body bytes.
No listener, live service, token-file access or device action was used.

If an aborted upload disconnects during request acquisition or while the refusal
is being sent, BrokenPipeError/ConnectionResetError now close the handler without
retrying output or propagating a peer-disconnect traceback. No delivered response
is claimed when the peer cannot receive it. The regression first reproduced both
write failures and a read reset; four focused checks passed after the fix,
including partial-body/pipelined refusal, response timeout handling and measured
trickle deadlines. Other unexpected exception types are not blanket-suppressed.

### Measured header-limit follow-up

The existing limits were tested over local socket pairs without changing their
policy or starting a listener. Oversized request lines returned redacted 414 in
**0.142 seconds**; oversized individual headers, aggregate headers and excess
header counts returned redacted 431 in **0.125, 0.115 and 0.005 seconds**.
All responses were complete and contained no request details; unread input was
not drained and no reader ran. A separate stream sending a complete header line
every 40 ms hit the test-only 0.65-second total deadline at **0.654 seconds**
after 16 lines, demonstrating that line completion does not reset the budget.
Three focused checks passed, including partial-body/pipelined refusal regression.
The test helper now joins the handler before inspecting its captured errors so
late worker failures cannot be mistaken for a clean refusal.

The header/body acquisition backlog is covered by `acebe96` (GET framing/idle
guard), `8c2a19b` (aggregate bytes), `fdec05e` (total deadline and measured idle/
trickle sockets), `1825ad3` (truncated headers), `7bc2e5f` (immediate write refusal)
and `1f2472a` (aborted clients), plus the measured checks above. New write-body
parsing, drains or alternative size/time limits are not pending implementations.
These are local handler checks; running-service deployment, external-network
load behavior and native browser verification remain outside this evidence.

**Completed-header deadline outcome: PASS, not an open defect.** A stream that
keeps sending header lines without terminating the block must eventually receive
408. Conversely, a block completed inside the total budget proceeds to ordinary
authentication. The complementary socket-pair check sent eight header lines and
the final blank line at 40 ms intervals: it received the expected unauthenticated
401 at **0.367 seconds**, exceeding the test idle interval of 0.25 seconds while
remaining inside its 0.8-second total budget. No collector ran. Both this check
and the over-budget completed-header check passed. There is no requested or
pending relaxation of the total deadline; further changes need a concrete new
failure or requirement, rather than treating this successful refusal as a gap.

## Concurrent request admission

The local server now admits at most **16 active handlers**, across API and static
requests. Previously ThreadingHTTPServer could start a new thread for every
accepted connection despite the per-request deadlines. Admission is nonblocking:
when full, an additional accepted connection is closed before parsing,
authentication, collection or thread creation. There is no application waiting
queue and no HTTP overload response; a client may observe EOF/reset and must
retry later. This avoids blocking the accept loop on a slow client's refusal
write. The operating system's existing listen backlog remains separate.

Slots are released when handlers finish, including handler failures and aborted
connections. Failed thread creation/start also returns its reserved slot.
Loopback binding, token authentication and read-only method policy are unchanged.
The cap bounds concurrent handlers, not requests per second, total collector
runtime or global process memory; a blocked collector retains its slot until it
returns. No running service has been restarted to apply this source change.

Three focused checks passed using real worker threads/socket pairs and an unbound
server (never listening), with a two-handler test cap: saturation/refusal and
recovery, handler failure recovery, and repeated thread-start failure recovery.
No real collector, device, external host or service was accessed.

A separate socket-pair integration check also passed with the actual HTTP
handler and shortened test deadlines: two idle requests filled admission, an
excess socket closed without dispatch, both admitted clients received 408, and
a subsequent request reached normal token validation (401 without a token).
No collector ran. This verifies timeout-to-capacity recovery, not just semaphore
behavior with a synthetic handler; it does not measure production load capacity.

### Ambiguous or non-finite hub JSON

The shared read-only hub response decoder rejects duplicate object fields
(including identical duplicates and escaped spellings of the same key), NaN,
Infinity and numeric exponents that overflow to infinity. This applies to roster,
learning, stored server status, health, interaction and trace reads. A conflicting
field is not resolved by choosing its last value. The existing redacted
`Hub read unavailable` error and per-feed fallback/cache behavior apply; paths,
response bodies and tokens are not returned in the error. Finite numbers and
repeated field names in distinct objects remain valid. These are source changes
checked with synthetic response bytes, not observations of a deployed hub.

Trace records may carry a JSON-encoded outcome `body` inside the outer response.
That embedded body uses the same strict decoder. If it has duplicate keys or
non-finite/overflowing numbers, the envelope's kind, type and observation time
remain available, but classification, disposition and finality are all `null`
(Unknown). Other valid records in the response remain usable. Raw body text is
never returned, and a malformed body does not become a positive outcome by
selecting its last field value. Focused in-memory handler checks cover this
behavior without connecting to a hub.

### Repository planning issues

`issues` also includes curated inventories embedded in
`docs/LEARNING-AND-ISSUES.md` and `docs/NATIVE-VERIFICATION-GAP.md`. These have
`documentIssue: true`, document-qualified IDs, `Documented gap` or `Verification
pending` status and `updatedAt: null`. Their source names the repository document;
they are not live incidents or native pass receipts. Missing or invalid document
inventories produce an Unknown placeholder. The same reader feeds the offline
standalone preview without a hub, coordinator database or service observation.
