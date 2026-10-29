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

The hub/adapter lead owns the evidence contracts and collection. Admin Center
owns preserving scope, source, freshness and unknown states in its display.
Do not create observations, run gameplay, ingest player records or activate a
policy to fill this table under the current offline scope. Review an authorized
evidence handoff when one arrives; record missing fields rather than infer them.

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
