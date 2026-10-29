# Learning and issues

Planning inventory, not a claim of live capability. Bot, learning, dataset and policy examples default to synthetic data. The optional read-only hub adapter is tested with a local stub but is not configured for live hub reads. Coordinator panels use read-only local records, and the FFXI bridge panel uses a read-only service and fault-marker observation. Game datasets and policy weights have not been verified here.

## FFXI — first

- Learn game-specific movement and navigation, camps and zones, party and job behavior, missions, combat timing and social conventions from appropriately sourced observations and outcomes. Keep player memory grounded in verified facts and scoped to the game.
- Identify the available datasets, their provenance, consent/authorization, scope, freshness and coverage before displaying them as evidence. Dataset inventory is unknown here. Policy/weight versions, validation, approval, delivery, adoption and demonstrated outcomes must be separate states; current states are unknown.
- The sister project's `docs/operators/FFXI_WORLD_REFERENCE.md` describes a reference and identifies missing live quest-progress and arbitrary quest movement coverage at its time of writing. Confirm current status with its lead; do not infer it from a historical note.
- Candidate interaction freshness now has generated offline coverage: nine hub-owned synthetic snapshots exercise the Admin Center reader, projection and cache. A newer accepted receipt may leave current activity unknown even while the raw snapshot is fresh. This validates presentation semantics, not native presence, learned behavior or action delivery. Live observation coverage, adapter-verified roster identity and demonstrated game outcomes remain unresolved; retain caller/server scope and do not join actors by display name. See the [fixture provenance and checks](../tests/fixtures/interaction-generated/README.md).

### Evidence needed to assess FFXI learning

These are review requirements, not findings that a bot lacks a skill. Current
game evidence is unknown here. An offline fixture passing establishes consumer
behavior only; it cannot close a game-learning gap.

| Question | Evidence needed | What does not answer it |
| --- | --- | --- |
| Which native bot and realm does the observation describe? | Adapter-verified native identity, game/realm scope and observation time; an explicit mapping to any roster record. | Matching display names or actor keys from different caller/server scopes. |
| Can the bot navigate or complete a mission step? | Scoped starting state, intended objective, native result and subsequent observation of position or mission progress, with source/timestamps. | A request, accepted receipt, fresh snapshot or trace correlation alone. |
| Does party/job behavior work under game conditions? | A defined scenario and observable native results for the relevant job/party context, including failures and safe fallback. | A reported personality, service health or successful wording generation. |
| Is a social memory grounded? | The specific verified fact, its source/scope/time, and evaluation of recall without invented events or cross-player attribution. | Plausible dialogue or an unverified memory example. |
| Did a dataset or policy improve behavior? | Dataset provenance and scope, policy version, separate validation and adoption records, and measured outcomes for a defined scenario. | A completed learning task, available weights or deployment alone. |

The workspace learning inspector now exposes these five requirements in the
collapsible “FFXI learning evidence checklist (read-only)”. Assessment states
remain Unknown even for a task marked verified; no manual completion or
automatic outcome inference is connected.

The Unknown state is traceable to the light task-only read, which omits task
evidence. Even a task reporting evidence present lacks the five structured
game assessments. An independent “Preview synthetic evidence mapping” displays
supported, missing and conflicting examples plus absent-assessment Unknowns;
it does not assess the selected task. Restore it with “Show selected need
evidence”. The remaining integration gap is an authoritative, scoped assessment
contract and authorized evidence, not promotion of a verified task status.

Light task rows can separately report a model-answer flag. The inspector keeps
Yes, No and Unknown distinct and never exposes answer text. Handcrafted
candidate fixtures cover that flag alongside omitted, null and opaque evidence;
these tests do not establish the model answer's correctness or game outcomes.

The hub/adapter lead owns the evidence contracts and collection. Admin Center
owns preserving scope, source, freshness and unknown states in its display.
Do not create observations, run gameplay, ingest player records or activate a
policy to fill this table under the current offline scope. Review an authorized
evidence handoff when one arrives; record missing fields rather than infer them.

### Fishing artifact review (2026-10-29)

Reviewed, not imported: `ffxi/handoffs/2026-10-29-fishing-offline-bundle-r1/`
`fishing-study-draft.json` and `SKILLUP_REVIEW.md`. The draft SHA256 is
`d3c8564b5cd4b5f837a6637f8d3e8ce4d4a071c546899592649852acbdb7bae7`.
All three receipt hashes match the local files and consistently identify source
hash `0829b4a157ec032279da5d81277a048056f151550242a8f824fb20a08d131846`.
This verifies local artifact identity and consistency, not source authenticity,
retail correctness or a deployed match.

The four rows fit the current `renderLearningPlan` fields: game, topic, next,
evidence, datasets, policy and source. All three evidence/lifecycle labels stay
Unknown. The envelope explicitly retains preview-only true, automatic study
registration false, retail/deployment verification false and the preferred-bait
skill-20 bonus null. The reported receipts contain 35 skill-up cases, 38 release
and 36 immediate replay cases, and five preview scenarios/six refusals. The
four provenance refusals and renderer smoke are lead-reported; the smoke used
historical Admin code, not the current app. No checks, preview executable or
linker were rerun for this review.

Integration caveat: `renderLearningPlan` displays rows only; it does not display
or enforce envelope hashes, preview-only restrictions or registration flags.
The draft is not a complete overview response or a hub contract. Any future
integration must preserve that provenance and keep the rows separate from live
learning tasks, learned policies and verified outcomes. No registration,
activation, UI import, live access or competing implementation was performed.
Retained emulator roll behavior is not retail odds, and the unknown skill-20
catch benefit must not be inserted into skill-up calculations.

Follow-up artifact review: `STUDY_MODEL.md`, `fishing-study-model.json`,
`fishing-study-local-match.json` and `fishing-study-review.html` now preserve
the four display rows separately from the complete original non-row envelope.
Independent read-only comparisons confirmed that the original draft bytes
still have the hash above, all rows and envelope fields are unchanged, and the
canonical row/draft/model hashes match their bindings. The three local receipt
files still match their byte hashes and recorded source hash. The canonical
draft hash differs from the file-byte hash by design; these identify different
serializations, not different reviewed content.

Static HTML inspection confirmed all four topics and provenance/restriction
fields, with no scripts, forms, controls or resource references. Browser
appearance was not tested. This separate artifact addresses preservation for
offline review; it does not change the current Admin renderer or implement an
import contract. Hashes establish consistency, not authenticity or permission.
Source identity, deployment and retail remain unverified, skill-20 remains
null, and import/registration/activation/game-write restrictions remain false.

The adjacent `reel-outcomes-check.json` records eight boundary cases and 1,000
deterministic grid cells; those checks were not rerun. Its fictional input
partitions are not retail probabilities or proof of RNG independence. Prior
chance calculation, session authorization and client delivery remain outside
that receipt. No FFXI script, preview, compiler, browser, listener or live
service was run for this follow-up; the full-linker hold is unchanged.

## SWTOR — second


- Establish the native adapter and observation/evidence coverage, then identify game-specific movement, class roles, missions, parties and social behavior to learn. Adapter capability, datasets and policy/weight verification are unknown and require an inventory with the hub lead.
- Preserve SWTOR-specific terminology and mechanics. Never apply an FFXI finding directly as verified SWTOR behavior.

## Cross-game issues and risks

- The hub lead identified r10 and candidate sources; the owner approved the per-bot routing design draft, while compatible hub implementation and separate authorization for actual model changes remain outstanding. Hub coverage and runtime deployment state are unverified. The local mock API is not an upstream contract.
- The e8c81be candidate `AdminCenter.cs` supports task-only light learning reads; completed history is bounded, while active and attention tasks are not capped by that history limit. Its overview scans whole stores under shared locks, and its providers view includes the spend ledger; neither is polled by this Admin Center. Source inspection is not evidence of the live revision or runtime safety.
- Native presence needs source, timestamp and expiry; stale or absent data must not become an offline count or fabricated progress.
- The action ledger must distinguish request, result and verification, and surface rejection and missing evidence. Correlation is not proof of execution.
- Model usage and cost, quality evaluation, bake-off methodology and provider routing require real measured data and agreed interfaces. Avoid unapproved providers and spending.
- Bot controls, model changes, audit, kill switches and gates require agreed authorization and reliable upstream behavior; the mock exposes none. Gates are off by default, while unreported state remains unknown.
- Learning references, candidate policies, verified artifacts, delivery, adoption and demonstrated outcomes are different milestones. Avoid mixing environments or implying training changed model weights.
- Before real integration, resolve authentication/session security, credential handling, authorization, audit, availability, active-player safeguards and rollback with the owning project. FFXI access remains read-only.

## Initial-task checkpoint (2026-10-29)

| Initial task | Existing checkpoint | Remaining boundary |
| --- | --- | --- |
| Architecture and API contract | `ARCHITECTURE.md`, `API.md`, `HUB-CONTRACT-DRAFT.md`; generated interaction fixtures integrated in `9deaa51`. | Joint review of unresolved routing details remains open; design approval is not implementation or write authorization. |
| Scaffold with tests | Python server, static UI and focused offline tests; seven contract tests passed at `9deaa51`, including all nine generated snapshots. | No repeated build or test is needed for this documentation update. |
| Learning and issues list | This inventory separates planning needs, consumer coverage and required game evidence. | Real datasets, policy adoption and game outcomes remain unknown. |
| Local mock instance | Loopback-only scaffold and existing mock setup documented in README. | This offline checkpoint did not probe or restart the running instance; current runtime availability is not reverified. |
| Commit and report | Local incremental commits and coordinator checkpoints. | No remote creation, push, live read or control action follows from this checklist. |

No initial setup task needs to be restarted. Further live integration remains
behind the existing access hold; model controls remain off. Evidence handoffs
can still be reconciled offline without changing those holds.

## Offline inspector runtime coverage

Ordering/unavailable-source follow-up: `tests/overview_failure.test.js` passes
for snapshot order through filtering, reordered refresh and filter reset;
unavailable-source synthetic fallback; empty roster/learning Unknown warnings;
and initial 503 login failure. There are no sort controls or pagination state
in this UI, so persistence for those features is not claimed. All matching
loaded rows render in received order; upstream truncation/coverage remains
separate. No production fix was required for these simulated-DOM scenarios.

Snapshot/filter follow-up (`85bcd46`): the focused overview state check now also
passes for persisted filters, same-ID record changes hidden by those filters,
missing selected records and explicit clearing. Inspectors use the current
snapshot rather than retained details. No production change was needed; this
is simulated-DOM coverage, with owner-facing steps in `/playtest#selection-refresh`.

Overview failure-state follow-up: session reset previously cleared selected IDs
but left both inspector DOM panels populated. The panels now reset to selection
prompts, preventing old details from reappearing after a later empty snapshot.
`tests/overview_failure.test.js` passes for labeled previous-snapshot retention
on HTTP 503 / transport / JSON failures, session closure on 401 / rendering
failure, inspector/selection clearing and recovery. The existing async-session
check also passed after this change. These use simulated DOMs, not browsers.

Current connected coverage is in `tests/inspector_integration.test.js`; run it
with the bounded command in README when changing a covered path. The entries
below supersede the older incremental coverage counts farther down this section.
All rows use shipped template IDs, actual UI handlers and in-memory HTTP dispatch.

| View | Connected evidence | Replaced dependency / remaining gap |
| --- | --- | --- |
| Login and learning inspector | Rejected/accepted token, four projected answer/evidence cases, preview/restore/clear. | Overview collector is synthetic; real local collection and browser DOM remain unverified. |
| Trace | Pending/non-final, empty, 401/502/503, validation, recovery and clearing (`cede05d`). | Synthetic reader; no upstream authentication or transport. |
| Interaction | Nine pinned generated snapshots, scoped actors, both freshness directions, empty/off/truncated, errors/recovery (`6b7710d`). | Cache lookup injects actual fixture projection; native identity and runtime revision remain unknown. |
| Hub service health | Game scope, unknown state, empty, 401/502/503, recovery/source reset (`8fbd6df`). | Cache lookup injects projection; no service inspection or bot-presence evidence. |
| FFXI bridge cards | Active/fault state, empty/malformed/denied/timed-out observation, 401 before runner and recovery (`57e339a`). | Real observer uses a fake runner and a fresh instance per exchange; no SSH or TTL validation in this path. |

Collector follow-up (`5c9b160`) adds real `overview` -> handler coverage in
`tests/test_offline_overview_collection.py`, with a temporary synthetic home and
actual SQLite reads. Three focused checks cover populated, missing and malformed
records; rejected auth/query before collection; sensitive summary withholding;
unchanged fixture files; read-only SQLite access and connection cleanup. The
task-inventory connection is now explicitly closed. Quota history is not promoted
to per-lead quota, and configured hub credentials are not read in mock mode.
Network, process probes and subprocesses cannot run. This narrows the mocked
collector gap without reading real coordinator/account records or restarting the
server. Real source compatibility, process binding, native browser execution
and deployed-service behavior remain separate, unverified boundaries.

Worker/handler follow-up: `7ada4a2` covers quota-worker cadence, deduplication,
transient storage failure/recovery and preexisting stop using temporary
synthetic files and an injected wait. Three checks passed without starting a
thread or reading real accounts. `708965f` rejects unsupported bridge-status
parameters before observation; one focused in-memory handler check covers
authentication ordering, rejection, redaction and the unchanged normal request.
No service restart occurred. These checks do not verify real-time scheduling,
concurrent shutdown, host observation or browser rendering.

Parameter audit follow-up: `5fbd612` bounds overview/trace query parsing and
rejects malformed fields, invalid UTF-8 and empty separators before any read.
Three focused checks passed, including valid encoded/default requests and the
existing trace projection/error path. `d157f3d` verifies unknown control paths
and POST/PUT/PATCH/DELETE across all five read APIs cannot reach guarded
dependencies. Its focused check passed; write routes remain absent. These
checks use in-memory request bytes, not a browser or running HTTP listener.

Error-envelope audit (`2aec2ed`) found the standard-library unsupported-method
path returned HTML. API protocol errors now use the same redacted JSON error
shape and cache/privacy headers; HEAD sends no body. Four focused contract
checks passed. The next offline item (`a757e1c`) normalizes JSON decoder recursion
failures to the existing redacted read error. Two byte-response checks passed
for malformed UTF-8/JSON/deep nesting, distinct oversize rejection and recovery.
The first nesting fixture was too shallow to trigger this runtime's decoder
limit; the final check uses 10,000 levels without changing interpreter settings.
The API audit documents expected statuses and successful shapes separately,
including bridge Unknown-on-200 and overview per-feed fallback semantics.
No reader transport, live credential, browser or restarted service was used.

Projection follow-up (`4971821`) fixes the separate inner trace-body decoder
path and finite-number overflow for stored XP rate / synthetic spend fields.
One in-memory handler check and three synthetic numeric/pipeline checks passed.
An unreadable trace body leaves outcome fields null while retaining envelope
metadata; unrepresentable numeric values stay Unknown, not zero. Valid zero,
fractions, game scope and pricing-error behavior remain covered. The spend view
is still synthetic; these fixes do not authorize or establish ledger reads.

Parser follow-up (`934f518`, `9bc2acf`): five focused checks passed for empty,
truncated and interrupted response bodies plus mixed valid/Unknown rows in
trace, health and interaction projections. Interrupted HTTP protocol reads now
produce redacted errors instead of escaping the handler path. Response contexts
close after failure. Unknown fields do not erase valid neighbors, while invalid
record structure/identity rejects the entire projection. Fixtures cover parser
and cleanup behavior only, not actual upstream transport or game evidence.

Recovery follow-up (`d31a909`): one focused reader/cache/merge scenario passed
with a synthetic timeout, truncated JSON and an invalid partial learning list.
Expired rows are replaced with labeled fallback; other successful feeds remain
scoped, and a complete empty roster clears that game's rows. No retries occur
inside the cache window; later expiry permits recovery. The clock and transport
are injected, so elapsed-time behavior and actual hub availability remain
unverified. No pagination contract or continuation requests were introduced.

The extended connected check passed under a 25-second hard timeout. Bridge
observation failures return 200 with Unknown fields; health projection/read
failures return 502/503. These are deliberately different API semantics.
Existing cache and session-race tests retain their separate scope; they were
not repeated for this documentation checkpoint. All model controls remain off.

Headless follow-up (`0123cd5`): the standalone artifact now also exercises health
and both bridge cards with in-memory responses. `tools/run_headless_playtest.py`
requires an existing Chromium executable and working user/network isolation;
it uses a disposable profile and never disables the browser sandbox. The actual
attempt exited 2 because no executable was found, before any browser launch.
Fresh capacity was sufficient (load about 11, available memory about 156 GiB);
the blocker is the runtime, not load. An existing browser path or authorization
to provision one remains requested through the coordinator. No download or
server restart occurred. Eight focused artifact/runner checks and embedded
JavaScript syntax passed; four runner checks use mocked process output and do
not establish DOM execution. Network-namespace support remains untested until
a browser is available. Browser layout and runtime behavior remain unverified.

`tools/build_inspector_playtest.py` builds a standalone, network-blocked browser
harness from the actual static assets and projected synthetic learning fixtures.
It exercises the inspector's real DOM events when opened in a browser; its
initial state is NOT RUN, never a pre-recorded pass. Generator tests and the
existing simulated-DOM checks passed locally. Browser execution remains
unverified because no local browser runtime was found; the artifact can be
opened on the owner's laptop without a tunnel, server or credentials. This
does not establish the running service's status or close game-evidence gaps.

The machine-check runner is `tools/run_inspector_playtest.cjs`. It requires an
installed jsdom module and blocks Node/DOM transports. A missing module exits
2, not a skipped success. The local attempt is blocked because no module was
found; the coordinator has been asked for an existing module path or approval
for a pinned dependency download. Four artifact/runner checks pass, including
the missing-dependency failure case. Actual jsdom execution remains pending.

Four independent in-memory HTTP-handler checks now pass in
`tests/test_offline_inspector_handler.py`. They pass raw request bytes through
the actual handler and verify projected answer flags, evidence availability,
privacy, authentication and rejected queries/methods without a listener. The
overview collector is replaced by a synthetic fixture; sockets, subprocesses,
database connections and live readers are blocked. This covers handler dispatch
and serialization, not real overview collection or browser execution. A bounded
follow-up search of existing local node_modules trees found no reusable jsdom,
happy-dom or linkedom package; no package was downloaded.

The handler suite now has seven passing checks, adding interaction/health read
failures and trace validation/projection. It exposed and fixed a local error
ordering problem: malformed trace values returned 503 when configuration was
missing. They now return 400 before constructing a reader. Authentication still
runs first. Tests preserve non-final trace outcomes and omit raw bodies/private
exception text. These results are in-process only; the running service has not
been restarted or verified with this change.

The inspector now also has one connected browser-free integration check in
`tests/inspector_integration.test.js`: parsed shipped markup -> actual app
login/fetch event -> real in-memory Python handler with projected synthetic
rows -> actual inspector rendering/event handlers in a limited simulated DOM.
Rejected and accepted login, all four learning evidence fixtures and
preview/restore/clear passed without a listener or a new dependency. This
narrows the disconnected-fixture gap; real DOM-engine execution and layout
remain unverified. The standalone HTML now exposes seven source-input hashes
for artifact identification, without claiming deployed-version equivalence.
