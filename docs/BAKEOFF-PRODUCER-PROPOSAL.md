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

## Questions for the hub lead

1. Can `inputSha256` be computed at the `DialogueWordingRequest` boundary, before
   provider-specific formatting? Otherwise, hash the formatted payload per provider.
2. Do the providers expose a streaming first-token time (`firstTokenAtUtc`), or only
   completion?
3. Should `purpose` reuse the `attempts.purpose` values?
4. Where do rubrics live, and who versions them?
5. Is `shadow_live` acceptable at all under the FFXI player-protection rules, or
   should bake-offs stay offline/replay only?
