# Read-only evidence path for the party `Hi!` retest

This prepares the DIT lead's owner retest after the r5-only restart recorded in
`8421f15`. It authorizes no new bridge/map change, model call, test-message
injection, inbox write or restart. DIT remains sole bridge writer; Admin is a
read-only reviewer. Decisions or changes while someone is online remain with
the owner under the standing restriction.

## Known starting point

The restart occurred October 29 at 14:03:39 UTC. The 14:07:59.805 UTC DIT receipt
reports bridge/hub active, unchanged unit/source hashes, marker absent and writer
released. Protected-character/account absence was sampled before and after the
restart; those samples do not remain an execution lock or current player check.
DIT's bounded observations found no post-restart queue rows or outbox events.
Old retained rows, service health and a successful restart are not reply proof.

## One owner-generated attempt

1. **Confirm the scenario with DIT.** Identify the current game/realm, party and
   eligible native bot using authorized evidence. A matching display name or
   roster registration does not establish current presence or party membership.
   Keep the eligibility observation time and its source. Do not enable flags,
   select a model or change a party automatically from Admin.
2. **Owner sends one party `Hi!`.** This is the existing DIT retest request;
   Admin sends nothing. Record the attempt time and the actual channel. Retain
   a reliable supplied correlation/reference and explicit scope if available;
   never manufacture a correlation from similar wording or nearby timestamps.
3. **DIT observes the existing path, read-only.** Use only its existing approved
   bounded outbox/inbox observation route. Record whether a *new* scoped greeting
   and matching queued reply exist after restart and after this attempt. Report
   observation window/coverage and timestamps, without copying player chat,
   credentials or full queues into Admin. Retained queue count alone is not
   enough. Missing reliable correlation remains Unknown.
4. **Owner reports visible speech separately.** Capture the reported speaker,
   party channel, time and whether it matches this attempt. Use a redacted
   scope/reference summary in Admin. An owner confirmation is reported evidence,
   not independently authenticated by the offline tool. An unrelated reply or
   unbound report cannot verify this specific attempt. Missing queue telemetry
   does not erase a well-scoped owner report.
5. **Hand back the stages, not an aggregate pass.** Distinguish greeting observed,
   reply queued, owner-reported speech and model origin. The r5 greeting fallback
   is canned. Model-looking wording, a `final` trace or a reply tag does not prove
   a new AI path or learned behavior.

If a greeting/reply is absent, report the bounded coverage and Unknown outcome;
do not infer inactivity, success or definitive failure. Do not automatically
retry `Hi!`, replay old chat, restore inbox bytes or restart the service. If a
fault or uncertain delivery is observed, return it to DIT for reconciliation
under its player/writer/rollback safeguards.

## Offline review aid

`tools/review_party_greeting.py` assesses a **supplied local review summary**;
it is neither a live collector nor a hub/inbox schema. It authenticates no
claim, establishes no writer lock and changes no state. It emits only fixed
stage labels and caveats, not raw input strings. Input is bounded to 64 KiB.
Duplicate JSON fields, nonfinite constants, unreadable/empty/truncated input and
excessive nesting are rejected with exit 2 and a fixed error, without an
assessment or echoed input. A valid summary with missing evidence instead
produces explicit Unknown stages. Neither result authorizes a live action.

```sh
timeout -k 2 10 python3 tools/review_party_greeting.py tests/fixtures/party-greeting-review.json
timeout -k 2 15 python3 -m unittest tests.test_party_greeting_review tests.test_party_greeting_cli
```

The supplied file is synthetic and describes queue-only evidence: speech and
model origin must remain Unknown. Do not use it as a live receipt. For an
authorized redacted summary, the format is:

- `restartAt`, `observedThrough`: timezone-aware evidence-window timestamps.
- `scope`: exact `game: ffxi`, `realm`, `party`, `botId` review identifiers.
- `eligibility`: the same scope, observation timestamp, explicit boolean
  `identityVerified` and `partyMember` claims.
- `greeting`: the same scope, explicit `ownerGenerated`, observation timestamp
  and a real supplied `correlationId`.
- `queuedReplies`: summaries with the same scope/correlation, observation time
  and boolean `enqueued`. Older, future or uncorrelated rows stay Unknown.
- `ownerSpeech`: optional same-scope/correlation summary with `reporter: owner`,
  boolean `confirmed`, `heardAt` and `reportedAt`; no transcript is needed.

The reviewer checks ordering within the supplied window, not clock accuracy or
source authenticity. Eligibility is not a continuing presence guarantee. A
reported speech result is not proof of AI and is not promoted to game learning,
policy verification, deployment approval or an automatic action.

`queueReview` flags mixed positive/negative enqueue claims within the matching
scope/time window; it does not decide whether they conflict or describe a
legitimate transition. Review chronology and record identity with the owning
lead. Repeated positive reports do not establish distinct replies. Negative
reports alone do not prove absence of a reply. None of these queue cautions
overrides an independently supplied, scoped owner speech report or proves AI.

Eight focused checks cover queue/speech separation, stale/wrong-scope and mixed
evidence, owner-report independence, eligibility, redacted CLI failures and
temporary input-file preservation. No additional files are created by the CLI.
They are consumer-interpretation checks, not a native party test. No historical
DIT suite was rerun and no live source was contacted for this preparation.

## Visual synthetic comparison

Rebuild `build/inspector-playtest.html` with
`python3 tools/build_inspector_playtest.py` and expand **Synthetic party-evidence
comparisons**. Four fictional summaries are assessed by the same review function
and displayed as an escaped static table. It compares queue-only, owner-report
without queue telemetry, mixed enqueue claims and an old retained row. All
model-origin states remain Unknown; no live result or overall pass is inferred.

This section is readable without JavaScript and has no input/upload or network
path. It does not render raw fixture scope/correlation fields. The source and
fixture fingerprints are included in artifact provenance. Three focused artifact
checks passed for the comparison semantics, escaping and resource isolation;
browser appearance and native behavior were not verified by those checks.
