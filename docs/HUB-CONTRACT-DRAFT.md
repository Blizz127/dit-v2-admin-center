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

## Proposed learning-assessment envelope — offline draft v1

This first source slice addresses the five learning-evidence questions in
[Learning and issues](LEARNING-AND-ISSUES.md#evidence-needed-to-assess-ffxi-learning).
It is a new proposal for review, **not part of the previously owner-approved
routing draft, an implemented hub endpoint or an authoritative assessment**.
The JSON Schema proposal is
[`learning-assessment-draft-v1.schema.json`](../schemas/learning-assessment-draft-v1.schema.json).
The isolated Python reference reviewer is
[`learning_assessment_draft.py`](../learning_assessment_draft.py). Neither server
nor UI imports it; no runtime, preview or model-control behavior changes.

| Field | Draft rule |
| --- | --- |
| `schema`, `contractStatus`, `environment` | Exact draft-v1 identifier, `draft`, `synthetic`; production/approved envelopes are refused |
| `scope` | Exact `gameId`, `realmId`, `callerId`, `serverInstanceId`, `nativeBotId`, `taskId`; no display-name join or cross-instance merge |
| `generatedAt` | UTC second-resolution timestamp; calendar-valid and not future-dated |
| `assessments` | At most one each: native identity, navigation/missions, party/social behavior, grounded memory, measured policy benefit; missing rows remain Unknown |
| `claim` | `unknown`, `supported` or `contradicted`; support/contradiction requires evidence IDs, Unknown requires none |
| `evidence` | At most 32 unique opaque IDs, each with identical scope, opaque source/receipt IDs and its own observation time |

Identifiers are bounded ASCII tokens (96 characters); they are never interpreted
as paths, URLs or executable instructions. Unknown fields, raw bodies/prompts,
duplicate kinds/IDs, duplicate/dangling references and cross-scope records refuse
the whole envelope. A current report cannot freshen an old observation: each
observation must predate its report and both must satisfy the explicit reviewer
freshness policy. This first prototype accepts a caller-supplied maximum age
between zero and one day (exclusive of zero); **no default or authoritative hub
TTL is proposed**. Hub review must settle that policy and clock skew tolerance.

The reviewer takes an already-decoded object, an exact expected scope, aware
`now`, and `max_age_seconds`. It returns a fixed five-row result. Successful
consistency checking is labeled `reviewed-synthetic`; supported/contradicted
claims remain **Reported ... (synthetic)**. Source authenticity stays unverified
and policy adoption stays Unknown, even if every assessment reports support.
Exact scope matching is necessary isolation, not adapter identity proof.
Validation, delivery, adoption, deployment and measured benefit must remain
separate; this envelope does not implement the policy lifecycle or an identity
attestation system. It does not authenticate an arbitrary supplied receipt ID.

Committed fictional examples under `tests/fixtures/learning-assessment-draft/`:
`mixed.json` separates support, contradiction and Unknown; `partial.json` leaves
all outcomes Unknown; `cross-instance-refusal.json` deliberately mixes one
evidence instance and must be withheld. They contain no real observation or
player record. Six focused checks pass, including mismatches in every scope
dimension, duplicate/dangling records, stale/future/invalid timestamps, wrong
types, private extra fields and no promotion of policy adoption. Network,
subprocess and database access are forbidden during review tests.

The JSON Schema artifact expresses structure; unique kinds/IDs, reference
resolution, scope equality and temporal ordering are additional semantic rules
checked by the reference reviewer. At the first checkpoint only vocabulary
consistency had been checked: the default Python lacked the checked validators.
The follow-up located the already-installed **jsonschema 4.19.2** under
`/usr/bin/python3` and ran its `Draft202012Validator`, including `check_schema`:

```sh
/usr/bin/python3 tools/check_learning_assessment_schema.py
```

The engine run passed for schema SHA-256
`2fe3ae95d1e2d877657997471704a2c0bbfb0b7241a0f9e449f06442abb0bf80`.
All three fixtures pass structure; the cross-instance fixture must additionally
fail semantic review. Nine structural refusals and four structurally valid
semantic refusals passed. The script reports schema/fixture hashes, engine
version and the distinction between these checks. The distribution lacks the
optional date-time checker, so the run explicitly registers the draft's strict
calendar-valid UTC-second format checker; date-time validation is not silently
skipped. Network calls are blocked during the checks. A missing engine returns
BLOCKED/exit 2, not a skipped pass. No dependency was installed or downloaded.
This validates a proposed synthetic contract, not source authenticity, hub
acceptance or live observations. The reference reviewer remains an already-
decoded-object checker, not a raw-JSON or transport parser or an input endpoint.

Review requests for the owning hub/adapter lead: establish the authoritative
scope/binding source, allowed observation and receipt provenance, freshness and
clock-skew policy, partial-envelope refusal policy, and assessment ownership.
Only after that review should a separately versioned live contract or consumer
integration be considered. The existing native-device intake checklist and
verifier remain [NATIVE-RECEIPT-INTAKE.md](NATIVE-RECEIPT-INTAKE.md); this learning
proposal cannot fill, replace or validate a device execution receipt.

### Admin lead's proposed answers for hub/adapter review

These are concrete proposals, not a record of hub agreement. They add no live
fields, endpoint, credentials or controls; the current synthetic draft remains
unchanged and the reference reviewer continues to require an explicit policy.

| Review topic | Proposed answer | Producer responsibility / current limit |
| --- | --- | --- |
| Authoritative scope and binding | The adapter owns native bot, realm and instance identity; the hub owns caller registration and the learning task association. Build the expected six-field scope from that established binding, independently of the assessment payload. Never join by name, reuse a restarted instance's evidence or infer presence from identity. | Hub/adapter must identify the actual binding record and revision/instance lifecycle. The draft compares supplied values only; it cannot prove their authority. A future binding revision would need an explicit versioned contract addition. |
| Evidence and receipt provenance | Allow only registered source IDs owned by the relevant adapter/evaluator. Receipt IDs must resolve to immutable records under the same complete scope and retain original observation times. Generation and queue acceptance are context, never native outcome evidence. | The hub owns the source registry and receipt lookup/retention semantics. An arbitrary matching opaque receipt ID is insufficient. The draft does not resolve IDs, create a registry or authenticate a source. |
| Freshness and clock skew | For a first live-summary pilot, propose a **300-second** maximum age for both report and observations, supplied explicitly by the caller, with **zero future-clock tolerance**. A newer report never refreshes older evidence. A malformed, future or expired record yields Unknown. | This is a proposed pilot value, not an implemented default or agreed TTL. Producers must document clock basis. Historical assessment archives need separate retention/validity semantics; expiration here means unavailable current evidence, not erased learning or disproved history. |
| Partial and conflicting data | Keep the draft's all-or-nothing refusal for malformed structure, scope mismatches, duplicates, dangling refs or invalid temporal ordering. Missing assessment kinds are valid and remain Unknown. A well-formed contradictory claim stays distinct from support. Do not collapse all dimensions into an overall verified badge. | This favors withholding over a misleading partial success. If producers need row-level recovery, propose a new version with explicit per-row coverage/error fields; do not silently change draft-v1 semantics. |
| Assessment ownership | Adapters produce native observations; a named hub evaluator owns the reported assessment and its referenced scenario/evaluation. Admin validates consistency and displays source-qualified claims, without promoting them to independent verification. | The hub must define evaluator identity and evaluation records. Current source authenticity remains unverified even when structure and scope match. |

Proposed minimum evidence behind each kind (criteria for the producer's referenced
record, **not fields already present in the envelope**):

- `nativeIdentity`: adapter binding record with native bot/realm/instance and
  observation time. This answers identity only, never online presence.
- `navigationAndMissions`: defined starting state/objective and subsequent native
  position or mission-milestone result, including failure. An accepted action
  request does not satisfy it.
- `partyAndSocial`: a defined party/job/social scenario, scoped participants,
  native outcome and failure/safe-fallback observations. Generated wording alone
  does not establish native delivery or successful party behavior.
- `groundedMemory`: permitted source fact, scope and fact/version provenance,
  with a defined recall evaluation. Do not send raw player memory or chat to
  Admin as proof; use the access-controlled receipt's permitted metadata.
- `measuredPolicyBenefit`: dataset/policy versions, baseline/comparison scenario
  and measured native outcome. Keep policy validation, delivery, adoption and
  measured benefit as independent records. A supported benefit claim never
  populates the currently Unknown adoption field.

Recommended first integration candidate after producer agreement: a bounded,
explicit read of one already-selected task's scope with the same evidence limits
as the draft, returning only permitted metadata. Do not add a poll loop, use an
overview/store scan as a substitute, or connect mutable model/game controls.
No URL or implemented route is asserted here. Producer acceptance, source
authenticity and deployment/readback remain distinct from the passing schema and
synthetic checks. The review can now respond to explicit choices rather than an
open-ended request to design the contract.

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
