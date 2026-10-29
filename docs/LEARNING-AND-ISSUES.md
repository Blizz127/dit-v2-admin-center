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

### Ambiguity comparison and offline report — 2026-10-29

The gap detail now compares every row sharing the exact selected loaded ID across
the full snapshot, ignoring game/name filters. Candidate columns use snapshot row
numbers; differing allowlisted fields are labeled. Missing IDs remain isolated to
the selected row and are never grouped by name. No candidate is chosen as correct.

The local JSON download and read-only copy field contain the same versioned report:
reported snapshot time, selected row, reason, candidate rows, differing fields and
explicit limits. Included fields are ID, name, game, status, character, level,
body kind, source and observation time. Missing/malformed values become null;
nonnegative integer level zero is preserved. Nested or unrelated fields such as
tokens, goals, memory and reply evidence are omitted. This is a snapshot report,
not authenticated provenance, an identity mapping or a portable routing instruction.

Focused synthetic comparison/export and existing exact-row navigation checks
passed. They cover game-hidden candidates, case-sensitive IDs, missing-ID
isolation, equal fields, numeric zero, malformed values, excluded fields, JSON
copy/download parity and refresh cleanup. Dynamic table header scopes and the named keyboard-focusable scroll region were checked structurally. The connected in-memory handler test also verifies candidate rows and differing fields in the rendered export. The artifact scripts report-content
checks without initiating a download. Native browser rendering and download
behavior remain unrun under the existing runtime/isolation limitation.

### Per-record roster gap details — 2026-10-29

`1934d0d` adds record details for missing/repeated roster IDs and links each usable
gap record to its exact row in the current snapshot. Missing/malformed records
without an object have no inferred entity link. Details show only supplied name,
ID, game, source and observation time; no goal/reply/learning/metric evidence is
joined. Bot inspection remains disabled for unresolved identities.

Exact-row navigation clears game/name filters, selects identity gaps and labels
the pinned snapshot row. Manual roster filters, Clear roster filters and the FFXI
shortcut remove the pin. Successful refresh and session reset clear gap details;
retained buttons from prior snapshots cannot retarget a new row at the same index.
This is a snapshot locator, not an entity identifier or persisted mapping.

Focused gap-detail and identity-filter checks passed, including same-name rows,
missing IDs, exact-row isolation, unchanged bot selection, request-free navigation,
stale links and session reset. The connected coverage test also passes the gap fixture through real in-memory HTTP handler bytes into the UI, checks exact duplicate-row navigation without another request, and verifies authorization reset clears details. Static naming/disabled-control checks passed. The
artifact scripts the new navigation and leaves four fictional roster records
(one unique, two repeated, one missing ID) for manual review. Native browser
execution remains unrun for the documented missing runtime/isolation limitation.

### Connected coverage runtime and roster triage — 2026-10-29

`e7129f8` connects projected fixtures to real in-memory handler bytes and then the
shipped coverage/inspector UI in a template-backed simulated DOM. The focused test
checks overview navigation, learning evidence inspection, bot detail recovery,
three unavailable/partial collections and authorization reset. Socket, subprocess
collector, database and live reader guards remain in the Python adapter. No listener
or browser is launched; this narrows integration coverage, not native verification.

`8db120c` adds a local roster ID filter for unique versus missing/repeated IDs.
Uniqueness is checked across the full snapshot, including records hidden by game
or name filters. Filter changes make no request; refresh retains the choice, while
Clear roster filters, the FFXI shortcut and session reset clear it. The focused
filter check and static naming/disabled-control checks passed. The offline artifact
scripts cross-game duplication and missing identity, then restores its baseline.
Native browser runtime remains unavailable; the prior isolation denial is unchanged.

### Loaded data coverage overview — 2026-10-29

A read-only overview summarizes the current roster, learning and metric collections
before local filters. It distinguishes unavailable, empty, partial and loaded list
shapes. It counts rows without usable IDs and rows with repeated IDs separately;
metric rows with any missing numeric field are also counted. Neither list shape
nor field presence authenticates observations, establishes freshness or verifies
outcomes. Review buttons navigate to existing cards without requests or changing
filters. Session reset removes the previous summary.

Focused component checks cover malformed collections, repeated/missing identity,
zero-valued versus unknown metrics, filter-independent counts, request-free
navigation and reset. Static naming/control checks passed. The artifact scripts
summary updates during unavailable roster/learning scenarios and metric gaps.
Native DOM/browser checks remain unrun: local browser/DOM runtime is missing and
the prior namespace-isolation denial has not been bypassed or retried. No model
switch, provider call, live observation or restart is part of this feature.

### Roster collection failure recovery — 2026-10-29

The adjacent root-roster check reproduced the same workspace-closing failure.
Missing or mixed bot lists now preserve the workspace and valid rows with Unknown
totals. Non-string names/statuses display Unknown; missing or non-string IDs no
longer reach string-only operations, and inspection remains disabled for unusable
identity. Missing selected bots clear scoped details without inferring absence;
unique returning IDs restore selection. Duplicate-ID safeguards remain unchanged.
Focused roster, identity and reply-scope checks passed; synthetic artifact scenarios
cover unavailable, partial and restored rosters. Native execution remains unrun.

### Learning collection failure recovery — 2026-10-29

A focused synthetic case reproduced a workspace-closing error when the top-level
learning collection was null. Learning list, filter and coverage rendering now
handle missing/malformed collections without closing the workspace. Valid rows
remain usable, incomplete totals stay Unknown, and a selected need can recover
when its unique ID returns. Identity ambiguity is still checked against the full
supplied list. A known empty list counts zero loaded rows, not zero actual needs.
The regression and existing duplicate-identity checks passed. The offline artifact
scripts unavailable, mixed and restored collections; native execution is unrun.

### Model metric coverage — 2026-10-29

The read-only model-call card now counts supplied finite, nonnegative numeric
latency/cost/quality fields and filters rows with all three supplied or at least
one unknown. Zero remains a supplied value. Counts always describe all usable
loaded rows, independently of the row filter; malformed entries leave the total
Unknown. This is not live instrumentation, a cost total or quality evaluation.
No provider, spend ledger or account is queried. Source and observation labels
remain attached to each row.

Focused synthetic component checks passed for zero/invalid values, incomplete
lists, filters without requests, refresh persistence, empty results, recovery and
session reset. Existing partial-metric checks and static labels/disabled-control
checks also passed. The artifact includes two fictional examples to exercise the
view. Native browser verification stays unrun for the documented missing local
runtime and prior namespace-isolation restriction; neither was bypassed or retried.

### Ledger finder boundaries and counts — 2026-10-29

`28c0ea2` exercises reply-to-ledger navigation while an older synthetic trace is
pending. Late successes, denials, failures and delayed JSON cannot repopulate the
trace panel after navigation; a subsequent explicit trace recovers. A separate
source-transition check confirms a failed source load retains the labeled prior
scoped snapshot and a successful change clears its pin before displaying new data.
These are fixture calls in a minimal simulated DOM, not live trace observations.

`8bc62fd` adds a visible loaded-ledger count. Missing/malformed lists show an
Unknown total, valid empty arrays show zero loaded rows, and ambiguous bot identity
withholds scoped counts. The offline artifact now includes shared-correlation
examples: Party-1 pins one pending/Unknown row out of three; Party-10 has no match.
Other-bot and unscoped rows are not attributed to the selected bot. No count is a
claim about the complete audit history or actual game outcomes.

Focused race/source-transition, ledger scope and static markup checks passed.
Native browser execution remains unrun for the documented missing runtime and
namespace-isolation limitation; no denied setup was retried. Model controls remain
disabled, and no live calls, ledger reads or restarts were performed.

### Reply evidence browsing — 2026-10-29

`1432b6c` adds an exact, case-sensitive correlation filter scoped to the selected
bot. It persists across refreshes and clears on a bot change or new session.
`960a2bc` retains valid scoped rows alongside an Unknown coverage notice when
the list includes malformed or unscoped entries. Empty arrays report zero loaded
examples; unavailable lists report an Unknown total. Neither establishes actual
reply coverage. Generated wording, queued delivery and verification stay separate.

`bc5b613` links a reply to the loaded ledger using both bot ID and correlation.
It shares the existing inspector navigation path, clears stale hub trace results,
and makes no request. Missing or duplicate roster identities prevent attribution;
blank or non-string correlation IDs cannot broaden the search. No matching ledger
row is explicitly inconclusive.

Focused reply and identity checks, the existing scoped-ledger regression and
static label/control checks passed. The offline artifact includes two fictional
reply examples (`Party-1` and `Party-10`) and scripted local filter/navigation
checks. Its assembly/CSP and JavaScript syntax checks are separate from native
execution, which remains unrun: an installed browser/DOM runtime is absent and
the prior namespace-isolation denial has not been bypassed or retried. No live
calls, ledger reads, service restarts or model-control changes were made.

### Model-switch audit examples — 2026-10-29

`47a0a42` adds a read-only card for generated per-bot and fixed all-bots model
change examples. A scope filter distinguishes the two; targets show explicit
fictional game/realm/native-bot/purpose, actor/reason/time, version and before/after
requested models. Effective state remains Unknown, including when an input claims
an effective value. Missing/malformed events show Unknown coverage; incomplete
or repeated target identities withhold requested-change attribution. Controls
remain disabled and filtering makes no routing request.

`4acd908` adds a rejected stale-version example. Attempted model is separate from
unchanged requested model and unchanged stored version. The offline generator
checks that the rejected call did not mutate the isolated simulator. It explicitly
labels this as a generated attempt illustration because the simulator does not
emit rejected-attempt audit entries. No authoritative hub audit contract is implied.

Component checks (actual app in a minimal simulated DOM), two fixture checks,
three static naming/control checks and the focused real in-memory overview-handler
check passed. The handler test copies the committed fixture into its synthetic
home and preserves its file/socket/process guards. The generator is never invoked
by the server. The standalone artifact includes the committed examples; the running
service was not restarted. jsdom/native rendering is still unavailable, so these
component results are not a native DOM, keyboard or browser appearance pass.

Follow-up `8c6a76e` withholds requested changes for unknown event scope or a per-bot
event containing multiple targets. `3ce29b1` and `b521ad0` add combined scope/outcome
filters, a clear control and visible outcome classification separate from result
text. Missing or wrongly typed outcome tags stay Unknown. Focused component checks
cover filter persistence, empty results, missing-data recovery and zero additional
requests from filtering; the fixture and static markup checks also passed.

A fresh local inventory found no Chromium/Firefox executable, supported Node DOM
or browser package, or standard Playwright/Puppeteer browser cache. The capture
tool also requires an existing browser executable or CDP target. No download,
browser launch or retry of the denied namespace setup was performed. Native DOM,
keyboard and visual verification remain unrun.

### Interaction scope and artifact assembly — 2026-10-29

`a293c05` fixes a reproduced presentation gap: an interaction row marked fresh
could show activity even with a missing actor key, caller or server instance.
Activity now requires a complete, unique tuple across the full returned list.
Repeated tuples withhold activity rather than selecting a first record; the same
actor key in distinct adapter/server scopes remains separate. Reported freshness
is still shown independently, and even a usable tuple does not authenticate a
native identity. No roster join or delivery inference is added.

`fe27ccc` closes the matching backend gap for whitespace-only identity fields.
Such a payload is rejected rather than projected as activity. Valid key bytes are
preserved; trimming is used only to detect blank values, never to merge identities.
The focused async loader check, seven projection checks, selector regression and
all nine pinned generated snapshots through the reader/cache passed offline.

`db3b3da` adds a parse-only check of the complete generated JavaScript, including
actual app source, driver and embedded fixtures. It passed using `node --check`,
without executing the script or claiming a DOM pass. This complements the existing
asset/CSP/fingerprint checks. Missing Chromium/jsdom and denied namespace setup
remain recorded runtime blockers; none was retried or bypassed at this checkpoint.
The five initial source tasks remain implemented. Further synthetic checks do
not replace runtime availability, native keyboard or screen-reader evidence.

### Scoped ledger navigation and linked issues — 2026-10-29

`984c577` fixes reproduced cross-bot broadening of an inspector's ledger link:
matching only correlation ID could include another bot's rows or rows without
bot identity. Inspector links now pin both the fixture-local bot ID and the
correlation. The pin is shown in the ledger filter, requires a unique ID in the
full loaded roster, and stays pinned when another bot is selected. Ambiguous or
missing roster identity withholds scoped evidence. An explicit manual search
clears the pin and searches across loaded rows; Show all, the FFXI evidence
shortcut, session reset and a successful source change also clear it. The link
itself makes no hub call and does not authenticate identity or establish delivery.

`1c55feb` fixes missing/malformed ledger arrays closing the workspace and keeps
valid scoped rows with Unknown coverage. Blank correlations offer no evidence
link. `b1bce8e` applies partial-list handling to the issue list, its coverage and
both linked inspector views. Malformed rows are omitted with Unknown total
coverage, valid rows survive search, and missing metadata is typed Unknown text.
Issue navigation flags require actual booleans; they enable only local navigation.

The focused `ledger_scope.test.cjs` and `issues_snapshot.test.cjs` passed with
synthetic snapshots, including shared correlations across bots, unscoped rows,
identity ambiguity, explicit broad search, session reset, partial lists, filters
and recovery. Selector/overview regression checks passed after the issue change;
the source-race check passed after the ledger change. No real ledger, coordinator
record, hub endpoint or game was accessed. Native rendering remains unverified.

### Ambiguous inspector identities — 2026-10-29

`1030c4f` fixes a reproduced first-match attribution bug: two roster rows with
the same ID could select the first bot and attach scoped goals, memory, safety,
reply, assignment or issue records. Inspection now requires a unique nonempty
string ID across the entire loaded roster. Duplicate rows remain visible with
disabled Inspect buttons; a previously selected identity becomes ambiguous and
its scoped panels clear. Explicit network safety examples remain separate. Game
or search filters cannot resolve the ambiguity, and a later unique snapshot can
restore the selection. This does not authenticate an upstream identity.

`aefa60b` applies the same rule to learning details, linked issues and the
selected-need evidence checklist. Duplicate task IDs across either the same or
different games select no first record. `8281bab` replaces absent or wrongly
typed learning metadata with Unknown/Not reported text, keeping model-answer
availability distinct from outcome evidence.

The focused `identity_snapshot.test.cjs` passed using actual refresh/inspector
code and synthetic records: duplicate bot/learning IDs, cross-game duplicates,
filter changes, existing selections, disabled buttons, scoped-panel clearing,
partial text and unique-ID recovery. Existing overview and selector regression
checks also passed. The selector assertions were updated for previous Unknown
capitalization and coverage-row insertion, retaining their behavioral assertions.
No actual roster, task, game or ledger records were read; native rendering remains
unverified. Core collection-schema permutations remain non-exhaustive.

### Loader partial-data and text audit — 2026-10-29

`d31c3ee` fixes a reproduced mixed-row failure in the async health, trace and
interaction cards: a malformed row previously erased usable observations.
Valid rows now remain with Unknown coverage. Missing lists do not become known
zero counts; non-object payloads remain unavailable. Trace finality accepts only
booleans; interaction switches/freshness remain strict flags, and nonfinite or
negative ages are Unknown. No service presence, identity join or delivery is
inferred. The focused async partial check and connected in-memory handler check
passed. `d1972d9` fixes missing learning-plan/artifact arrays closing the workspace;
its focused snapshot check passed for missing/mixed/partial records, game
filtering, independent validation/adoption/outcome values and recovery.

All five HTTP loader paths have offline coverage; this is not an exhaustive
claim about every possible field or payload combination:

| Loader | Partial/error coverage and source |
| --- | --- |
| Overview | `metrics_snapshot.test.cjs`, `coordinator_snapshot.test.cjs`, `learning_inventory_snapshot.test.cjs`, and `overview_failure.test.js`: actual refresh with synthetic snapshots; missing/mixed metadata, filters, selection clearing and recovery. Core roster/learning row schema permutations are not exhaustively covered. |
| Trace | `async_partial_panels.test.cjs`: partial/mixed rows, unknown count, strict finality and recovery; `inspector_integration.test.js`: real in-memory handler, validation and 401/502/503. |
| Interaction | Partial loader check plus connected integration with nine pinned generated snapshots, both freshness directions, off/empty/error/recovery. Native identity and deployment remain outside these checks. |
| Hub health | Partial loader check plus connected empty/401/502/503/recovery checks. Reported state does not establish bot presence. |
| Bridge | `bridge_view.test.js` and connected integration: partial fields, unknown/error clearing, stale-session rejection and recovery. No SSH is used. |

`7c9969c` adds three passing static markup checks: unique IDs and valid reference
targets, form-control names and card headings, nonpositive tabindex values,
announcement markup for async results/login errors, and disabled model/stop
controls. These checks inspect shipped HTML only. Text assertions in the focused
loader tests reject `undefined` and object-string leakage while preserving
Unknown caveats. Screen-reader announcements, keyboard defaults, focus visibility,
visual layout and cross-panel navigation behavior still need native verification;
this is not accessibility certification. No browser attempt was repeated.

### Coordinator and bridge partial records — 2026-10-29

`b52937e` keeps both bridge cards readable when a response is partial or has
wrongly typed fields. Valid supplied strings remain visible; other fields show
unknown. Non-object responses clear both observations through the unavailable
path, and a later valid response recovers. The focused bridge simulated-DOM
check passed, including existing session/visibility, error and stale-response
guards. No new bridge observation was collected.

`9cedcb7` fixes reproduced workspace failures from absent or malformed lead,
monitoring, activity, timeline, nudge, session-marker and quota lists. Missing
or invalid nested event/history arrays also stay local to their cards. Usable
rows survive with an Unknown coverage notice. Numeric quota is bounded to
0–100%; reply/heuristic timings require finite nonnegative numbers and preserve
zero. Heuristic records still do not establish work or causality. `87b792b`
extends that handling to game settings and overview service summaries, including
typed XP rates; reported settings remain separate from liveness and freshness.

The focused coordinator snapshot check exercises actual overview refresh with
synthetic fixtures, including missing/empty/mixed records, malformed nested
histories, bounds, recovery and timeline filtering. It passed, as did the shared
metrics snapshot and overview regression checks after the coordinator change.
Two regression assertions were updated for the previous feed-coverage wording;
their Unknown/fallback assertions remain. No real coordinator records were read.
The shared harness is `tests/overview_snapshot_harness.cjs`; these are simulated
DOM checks, not native browser or current-service verification.

### Partial telemetry follow-up — 2026-10-29

The same focused overview check subsequently reproduced missing/malformed
`hubFeeds` closing the workspace. Feed rendering now keeps valid supplied rows,
shows Unknown coverage for missing or incomplete metadata, and suppresses the
all-available banner when any row is malformed or lacks game/view/status.
The FFXI feed card retains its coverage warning even when one valid FFXI row
exists. Missing, mixed, empty and recovery cases passed offline; no upstream
request or current availability was verified.

`d17a31d` and `003e044` fix two reproduced overview failures: absent model-call
lists and absent spend summaries previously threw during rendering and closed
the workspace. Each panel now handles missing data locally. Mixed model rows
keep usable examples with an incomplete-coverage notice; empty lists do not
establish zero usage. Nonfinite, negative or incorrectly typed numeric metrics
are Unknown; explicit zero is preserved. No monetary units or quality scale are
invented for model-call metrics.

`tests/metrics_snapshot.test.cjs` exercises actual overview refresh with shipped
template IDs, synthetic snapshots and a minimal DOM. Missing, malformed, mixed,
zero and recovery cases passed; each missing-field failure was reproduced before
its fix. This is not native browser execution. The offline artifact includes the
updated app; `/playtest` describes what to look for without enabling controls.

`4c3c1f2` also rejects exponent overflow such as `1e999` in local greeting-review
JSON, including nested values. Two focused CLI checks passed, covering redacted
failure with no assessment and unchanged valid-fixture separation of queue,
owner-reported speech and model origin. No evidence was collected from services.

### Current render checkpoint — 2026-10-29

`570ad1c` adds `--screenshots` to the isolated native runner. It checks comparison
table content, vertical/horizontal viewport bounds and rightmost-column access
at desktop and narrow widths, then retains three PNGs only when the complete run
succeeds. Published receipts identify the generated HTML and image bytes by
SHA-256. Geometry assertions and PNG header checks do not replace human image
inspection or establish live evidence.

Six focused Python wrapper/publication checks and the Node capture protocol
fixture check passed. Those tests use fake protocol data, including fake PNG
headers; they produced no browser screenshots. The actual screenshot command
exited 2 before launch because Chromium is absent. Separately, the namespace
probe failed with `unshare: write failed /proc/self/uid_map: Operation not
permitted`. This supersedes the earlier statement that namespace operation was
untested. Neither blocker was bypassed; no packages or browsers were downloaded.

The next meaningful runtime step is to run the documented command in an existing
environment with Chromium and permitted isolation, then inspect its images for
clipping and readability. Native input, appearance and screen-reader behavior
remain unverified. Repeating fixture checks cannot resolve those gaps. Initial
source tasks remain implemented; authoritative learning evidence and native
party speech remain separate evidence dependencies, not inferred successes.

Keyboard-runner pipe follow-up: non-object JSON replies now close the protocol
connection through its redacted failure path rather than throwing in the stream
callback. EOF, pipe closure and synchronous write failures reject outstanding
commands, clear timers and reject future commands without writing. Focused fake-
pipe checks passed for null/array/scalar replies, EOF/close and write exceptions.
No browser was started; native input execution remains blocked on Chromium.

Native-input runner follow-up (`1d41f1a`) uses installed Chromium's anonymous
debugging pipes and `Input.dispatchKeyEvent`, not synthetic DOM events or click
substitution. It focuses Start initially, then requires native Enter start,
Escape cancellation/focus return, restart and all twelve guided key steps. Node
and Chromium run under the existing network-namespace requirement with temporary
artifact/profile files, bounded commands and process-group cleanup. The guide
is inline; no modal-dialog semantics are claimed. Cancellation has its own state.

Observer cancellation/restart tests, fake-pipe key encoding/framing/error checks
and four wrapper contracts passed. The actual runner attempt stopped before
browser launch because Chromium was absent; Node and namespace tools were found
but browser sandbox/namespace operation remains untested in this run. No runtime
was downloaded. This does not close the native-keyboard evidence gap. The five
initial source tasks in the checkpoint above remain implemented; pending live/model approvals and
browser provisioning are not replaced by further synthetic tests.

Native-keyboard harness follow-up (`d31e242`) adds a guided twelve-step check to
the offline artifact. It observes trusted Tab/Shift+Tab and Enter/Space events,
checks page/focus after native defaults (including Space keyup), and rejects
unexpected focus, pages or requests. It does not synthesize activation, move
focus during the sequence or prevent default keys. Start prepares synthetic
pages and establishes initial focus; restarting invalidates pending callbacks.

The observer test passed with fake events for sequence completion, untrusted
input refusal, delayed default observation, wrong focus/missing activation,
extra requests, incomplete runs, preparation failure and restart races. These
are logic checks, not native-keyboard evidence. Artifact isolation/escaping and
embedded syntax checks passed. Runner reports now expose native keyboard status
separately; two focused report-contract checks passed without launching a browser.
Actual browser execution remains NOT RUN pending an available runtime. Owner
steps are in `/playtest#assignment-keyboard`; no installation, live calls,
service restarts, ledger reads or control changes occurred.

Assignment paging follow-up (`528c95b`) adds local ten-row pages over loaded
examples, with no upstream pagination or write capability. The shared synthetic
fixture has 23 matching rows plus a different-bot row, empty/unavailable/partial
states. Focused actual-app simulated-DOM checks passed for exact-ID counts/order,
page boundaries, no requests, refresh preservation/clamping, HTTP 503 retention,
unknown/empty counts and selection/session resets. Disabled-selector checks also
passed. Native buttons keep document order and their DOM nodes across page
changes, use `aria-disabled` with guarded activation, and describe the live count.
Simulated focus ownership and shipped markup were checked; browser focus visuals,
screen-reader announcements and native Tab/Enter/Space execution remain unverified.

The offline artifact embeds the same fixture with a source fingerprint and adds
programmatic focus/paging assertions. Regeneration does not execute those checks;
open `build/inspector-playtest.html` locally and follow `/playtest#selection-refresh`.
No runtime is installed or downloaded, and no live source or service is accessed.

Safety metadata follow-up (`fce4687`) isolates absent/null/malformed collections
without closing the workspace. Explicit `botId: null` denotes a network example;
missing, blank or malformed identity is withheld with an Unknown scope warning.
Partial fields remain Unknown, and valid empty lists retain the actual-state
warning. The focused overview check passed for these cases, selection without
requests, clearing, prior-text removal and recovery. No live ledger was read.

The offline artifact driver now includes synthetic bot detail, safety, reply and
assignment unavailable/partial/empty/recovery scenarios and verifies disabled
model selectors. Artifact resource/CSP/inline-escaping checks and embedded JS
syntax passed. These new driver assertions have not executed in a browser or
jsdom; the separate simulated-DOM overview check is the runtime evidence so far.
Rebuild with `python3 tools/build_inspector_playtest.py`, open the file locally,
and read its runtime result; generation alone starts at NOT RUN.

Bot-detail follow-up (`99906b7`) keeps missing/null/malformed detail collections
and duplicate exact-ID records Unknown instead of throwing or choosing the first
record. Goals and memories are assessed separately; usable rows in a partial
list remain visible with a coverage warning, and missing fields stay Unknown.
The same offline check covers missing/malformed reply and assignment collections,
valid empty lists, incomplete reply metadata, prior-text clearing and recovery.
Selecting details makes no request. Model/bot editing and save paths remain off.
`tests/overview_failure.test.js` passed after both fixes; the disabled-selector
check also passed after the goals/memory fix. These execute actual UI code in a
simulated DOM, not a browser. No live calls, ledger reads or service restarts.
Playtest expectations are at `/playtest#selection-refresh`; the generated offline
artifact contains the updated app, but native browser execution remains parked.

Audit metadata follow-up (`6aa8dfc`) distinguishes absent/null/malformed lists
from valid empty lists, keeping count and coverage Unknown locally. Incomplete
row fields render explicit unknown values. The focused UI check passes for
prior-row clearing, other-panel availability, local search/reset and recovery.
Malformed collections do not display a valid prefix as complete. No live audit
data or browser runtime was accessed, and no audit actions are created.

Decision-summary follow-up (`8a73941`) fixes an optional-summary failure that
previously closed the workspace. Missing/null/malformed lists now show Unknown
coverage locally; valid empty lists retain the incomplete-inventory warning.
Missing row fields/timestamps are explicit unknowns. The focused overview test
passes for prior-row clearing, keeping other panels available and recovery.
No approval is inferred or changed, and no coordinator or ledger read occurred.

FFXI readiness follow-up (`a2ac08c`) replaces blank/missing summary fields with
explicit Unknown. The focused overview UI check passes for source attribution,
partial and absent summaries replacing prior text, and SWTOR-only feeds not
becoming FFXI coverage. The behavior is display-only, adds no toggle and does not
establish readiness, deployment, presence or delivered game behavior.

Audit filtering (`e2f7026`) adds local actor/action/scope/result search, counts
and reset over loaded synthetic examples. Focused overview and source-race
checks passed: case/space handling, empty-match coverage warning, no requests,
no fabricated actions, refresh persistence and reset. What’s-new and playtest
instructions describe the controls. Live audit collection remains unconnected.

Audit follow-up (`de91d84`): an empty example list previously left the panel
blank. It now states that no examples/live audit source are available and makes
no inference about real actions. The focused overview check passes for populated
rows, unknown timestamps, source labels, failed-refresh retention, subsequent
empty clearing and no fabricated audit events or service requests from bot
selection. This is synthetic rendering coverage, not a real audit ledger read.

Detail isolation follow-up (`a12e6bf`): a same-name bot fixture exposed orphan
bot-specific safety examples after the selected roster entry disappeared. The
safety panel now requires that exact selected ID to exist, consistent with the
other detail panels; network-wide examples remain. Focused overview/detail and
existing selector checks passed for ID isolation, missing-record clearing and
no service request on selection. These synthetic IDs do not establish native
identity. Bot-edit forms remain unavailable; no write validation was invented.

Ordering/unavailable-source follow-up: `tests/overview_failure.test.js` passes
for snapshot order through filtering, reordered refresh and filter reset;
unavailable-source synthetic fallback; empty roster/learning Unknown warnings;
and initial 503 login failure. There are no sort controls or pagination state
in the roster/learning lists, so persistence for those features is not claimed. All matching
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
