# Bake-off data source: proposal for hub review

Task `7bc7b81622e0`, part 2, November 3. **Proposal only.** The DIT hub lead owns
hub contracts. Whether to build a bake-off producer is an open owner decision, and
the hub lead has logged it as a gap without starting work. Nothing here is
implemented on the hub, and no build is requested.

## Why

Brief feature 4 asks for cost, latency and quality per model call, plus a bake-off
comparing models on real tasks. Today:

- **Live `attempts` (`AiSpendLedger.cs`):** cost and tokens per call only.
- **Offline `DialogueProviderEvaluationRecord`:** fixture providers only.

Neither identifies the same input across models, attributes calls to a game or
bot, measures first-token latency, versions its scores, or records delivery. The
gaps, from [the contract draft](HUB-CONTRACT-DRAFT.md), are:
- (a) run ID and input hash;
- (b) game and actor attribution;
- (c) time-to-first-token;
- (d) rubric name and evaluator version;
- (e) delivery outcome and fallback eligibility;
- (f) any recorded runs.

## Proposed records

These follow the hub's JSON conventions (`NeuronetworkJson`): camelCase fields,
snake_case enum values, and null fields omitted. **An absent field means unknown,
never zero or false.** The Admin Center needs no prompt or reply text; hashes are
enough.

### Run manifest: one per comparison run (closes a, f)

| Field | Meaning |
| --- | --- |
| `schema` | `dit-bakeoff-run-v0` |
| `runId` | Opaque unique ID |
| `startedAtUtc`, `completedAtUtc` | Run bounds |
| `environment` | `offline_fixture` \| `recorded_replay` \| `shadow_live` (never acts in game) |
| `caseSet` | `{name, version, sha256}` of the fixed case list |
| `inputCanonicalization` | Version name of the canonical request form hashed into `inputSha256` |
| `candidates` | `[{provider, model, purpose}]` compared in this run |
| `rubrics` | `[{name, version}]` applied |
| `hubRevision` | Producing revision, as reported |

### Attempt: one per case × candidate (closes a–e)

| Field | Gap | Meaning |
| --- | --- | --- |
| `runId`, `caseId` | a | Join to the manifest; `caseId` is stable across runs of a case set |
| `inputSha256` | a | Hash of the exact normalized provider input, so models can be compared on identical inputs |
| `gameId`, `actorKey` | b | Game and bot/persona the case represents; absent when not applicable |
| `purpose` | b | `conversation` \| `planning` \| `action_choice` \| other agreed value; required for grouped comparison |
| `provider`, `model`, `reportedModel` | — | Requested and provider-reported model |
| `sentAtUtc`, `firstTokenAtUtc`, `completedAtUtc` | c | Provider timing; queueing is excluded or reported separately as `queuedMs` |
| `inputTokens`, `outputTokens`, `cacheHitTokens` | — | As in `attempts` |
| `costNusd`, `pricingBasis` | — | Nano-USD integer and basis, matching `attempts`; `attemptId` optionally joins the spend ledger |
| `completionStatus` | — | Existing `DialogueWordingCompletionStatus` values |
| `structuralValidation`, `semanticCompliance` | — | Existing evaluator values |
| `fallbackEligible`, `fallbackUsed` | e | Copied from the provider result and outcome |
| `delivery` | e | `{status: delivered \| not_delivered \| not_applicable, evidence}`; `evidence` is a trace/correlation ID. Absent means unknown |
| `scores` | d | `[{rubric, rubricVersion, evaluator, evaluatorKind: rule \| model \| human, evaluatorVersion, scaleMin, scaleMax, score}]`; empty means not scored |

`offline_fixture` and `recorded_replay` runs never deliver, so `delivery.status` is
`not_applicable` there. Delivery is only meaningful for `shadow_live`, and only with
trace evidence.

## How the Admin Center would ingest it

Alongside `evaluator_snapshot.py`, behind its own off-by-default switch (proposed
`DIT_BAKEOFF_RUN_DIR`: one `manifest.json` plus `attempts.jsonl` per run). It would
use the same strict rules: exact field set, enum pinning, bounded sizes, malformed
rows counted and omitted, no inference.

Comparison rules:
- Only compare attempts sharing `runId`, `caseSet` and `inputSha256`.
- Group by `provider`, `model` and `purpose`.
- Average a score only within one `rubric` + `rubricVersion` + evaluator version. Different scales are never mixed.
- Show time-to-first-token and completion latency separately.
- Show cost as settled nano-USD, with missing values counted as unknown.

It reads exported files only, so it does not depend on the live-read decision.

## Hub lead review (November 3)

The hub lead found the manifest and per-attempt shape right, and answered from code:

1. **Input hash:** compute `inputSha256` at the `DialogueWordingRequest` boundary over a
   canonical form that excludes per-call fields (`requestedAtUtc`, `expiresAtUtc`,
   `correlationId`, `causationId`; `DialogueWordingModels.cs:161-192`). Otherwise two
   runs of the same case never match. Add `inputCanonicalization` (a version name)
   to the run manifest.
2. **First-token time:** not available. Nothing streams today
   (`DeepSeekPromptSerializer` sends `Stream: false`, and the devbox AI worker
   rejects `stream=true`). `firstTokenAtUtc` stays optional and absent; providing it
   needs a streaming path, which is a real change, not a field. The Admin Center
   shows completion latency only.
3. **Purpose:** reuse `attempts.purpose`. Current live values are
   `subscription_chat`, `subscription_planetside_war`,
   `subscription_companion_extract` and `research`. `attemptId` joins
   `attempts.id`; `reported_model` and `basis` already exist there.
4. **Rubrics:** none exist. `DialogueEvaluatorScore` is only (`Evaluator`, `Score`).
   The hub lead would own rubrics, with the owner defining what "good" means. That
   is part of the build decision, so nothing exists to version yet.
5. **`shadow_live`: not allowed without an owner decision.** It reads live player
   chat, and every candidate call spends from the AI budget (pay-per-use is capped
   at $25/month, and subscription lanes have their own limits). `offline_fixture`
   is fine. `recorded_replay` should use already-journalled lines
   (`data/conversations/*.jsonl`), and still needs the owner's OK before player
   text leaves the hub host.

Consequence for this proposal: the default environments are `offline_fixture` and
`recorded_replay`. `delivery` is therefore `not_applicable` until an owner-approved
live mode exists.

Open owner decisions this proposal depends on:
- whether to build the producer;
- what "good" means for rubrics;
- whether recorded player text may leave the hub host;
- whether any live mode is allowed.

## Admin Center ingest: implemented offline (task `c4d9d0b449a4`)

`bakeoff_run.py` reads one recorded run when `DIT_BAKEOFF_RUN_DIR` names an
absolute local directory containing `manifest.json` and `attempts.jsonl`. It is off
when unset. No producer exists, so only `tests/fixtures/bakeoff-run` (synthetic)
has been imported. The importer enforces the review defaults:

- **Environment:** only `offline_fixture` and `recorded_replay` runs are imported.
  A `shadow_live` manifest is refused with an owner-decision reason.
- **Input hash:** `inputSha256` is taken as the producer's hash, named by
  `inputCanonicalization`. It is never recomputed here. A case whose candidates
  report different hashes is dropped as not comparable.
- **Latency:** total only (completed minus sent). `firstTokenAtUtc` is
  format-checked but never shown.
- **Delivery:** any delivery value other than `not_applicable` is refused for
  offline runs.
- **Quality:** set only when the run declares exactly one rubric and every scored
  attempt has one score using the same evaluator name, version, kind and scale.
  These fields are compared separately, so punctuation cannot merge evaluator
  identities. The rubric, evaluator, kind and scale are carried in the row source.
- **Cost:** `costNusd` is converted to USD. A missing value stays unknown.
- **Strictness:** attempts must belong to the run and a declared candidate, with
  the exact allowed fields and enums (snake_case). Malformed, duplicate or
  undeclared attempts are counted and omitted. Coverage reports retained attempts
  against candidate slots for identifiable cases before ambiguity filtering. The
  manifest does not enumerate cases, so the full case-set size remains unknown.
  Omission totals include invalid attempts, duplicate attempts and hash mismatch
  attempts. The latter two counts are reported separately; a duplicate that also
  has a mismatched hash is counted as a duplicate, not twice.
- **Identity:** generated attempt IDs escape each run, case and candidate component
  before joining them, so punctuation in one component cannot create false duplicates.
- **File safety:** reads use the bounded non-blocking, no-symlink reader, with
  size and count limits.

Rows join panel 4's model-call list and grouped comparison. A status line reports
the run, canonicalization, revision and coverage. Checks:
`tests/test_bakeoff_run.py` (9 tests) and a selector assertion for the status line.
