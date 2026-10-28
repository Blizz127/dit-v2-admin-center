# Learning and issues

Planning inventory, not a claim of live capability. No game, dataset, policy or weights were inspected at runtime. The initial Admin Center uses synthetic data only.

## FFXI — first

- Learn game-specific movement and navigation, camps and zones, party and job behavior, missions, combat timing and social conventions from appropriately sourced observations and outcomes. Keep player memory grounded in verified facts and scoped to the game.
- Identify the available datasets, their provenance, consent/authorization, scope, freshness and coverage before displaying them as evidence. Dataset inventory is unknown here. Policy/weight versions, validation, approval, delivery, adoption and demonstrated outcomes must be separate states; current states are unknown.
- The sister project's `docs/operators/FFXI_WORLD_REFERENCE.md` describes a reference and identifies missing live quest-progress and arbitrary quest movement coverage at its time of writing. Confirm current status with its lead; do not infer it from a historical note.

## SWTOR — second

- Establish the native adapter and observation/evidence coverage, then identify game-specific movement, class roles, missions, parties and social behavior to learn. Adapter capability, datasets and policy/weight verification are unknown and require an inventory with the hub lead.
- Preserve SWTOR-specific terminology and mechanics. Never apply an FFXI finding directly as verified SWTOR behavior.

## Cross-game issues and risks

- The hub lead identified r10 and candidate sources; focused review of the updated drafts is pending. Hub coverage and runtime deployment state are unverified. The local mock API is not an upstream contract.
- Native presence needs source, timestamp and expiry; stale or absent data must not become an offline count or fabricated progress.
- The action ledger must distinguish request, result and verification, and surface rejection and missing evidence. Correlation is not proof of execution.
- Model usage and cost, quality evaluation, bake-off methodology and provider routing require real measured data and agreed interfaces. Avoid unapproved providers and spending.
- Bot controls, model changes, audit, kill switches and gates require agreed authorization and reliable upstream behavior; the mock exposes none. Gates are off by default, while unreported state remains unknown.
- Learning references, candidate policies, verified artifacts, delivery, adoption and demonstrated outcomes are different milestones. Avoid mixing environments or implying training changed model weights.
- Before real integration, resolve authentication/session security, credential handling, authorization, audit, availability, active-player safeguards and rollback with the owning project. FFXI access remains read-only.
