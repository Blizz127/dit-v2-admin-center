# Conversation turn provenance: proposed producer handoff

Status: design proposal, not an agreed wire contract or implemented runtime.
No new endpoint, live flag, native hook, permission, model call or delivery is
authorized here. The hub/bridge/game integrators keep their existing ownership
and all source, player-protection, spending and release holds.

The source audit in [context limits](CONVERSATION-CONTEXT-LIMITS.md) found that
the inspected FFXI bridge candidate records some generated replies in its
history before delayed inbox publication. It has supersession cleanup, but an
in-memory history entry is not a native delivery receipt. Longer context must
preserve that distinction instead of expanding a possibly unconfirmed transcript.

## Proposed states and context treatment

| Evidence | What it establishes | Proposed use in a reply packet |
| --- | --- | --- |
| Native heard line | This scoped adapter observed that speaker's line | Conversation history, retaining speaker and native scope |
| Prepared wording | A draft was generated for a selected bot | Separate pending intent for the relevant bot; never “X said” |
| Inbox publication | The bridge completed its publication step | Still pending native outcome; do not certify visible chat |
| Native-confirmed speech | Native evidence identifies the same message/body/scope as spoken | Conversation history once, keyed by native identity |
| Confirmed cancellation before publication | This exact pending attempt was superseded/cancelled | Exclude from confirmed history; retain a bounded cancellation record |
| Outcome unknown | Timeout, crash, missing receipt or conflicting evidence | Keep delivery unknown; no automatic resend or claim of silence |

Pending context can prevent overlapping responses, but only when the receiving
bot is allowed to see it. Private drafts are not global room observations. If
the model sees a pending draft, label its meaning explicitly: a possible future
line, not something the human already heard or accepted.

The current string-only history cannot certify these states. Until an agreed
producer supplies them, its delivery provenance remains unknown. Neither
pattern matching nor a model's interpretation upgrades those strings.

## Minimum binding to resolve with the producer

Field names below are illustrative and must not be treated as an accepted API:

- A stable turn/attempt identifier. The producer must keep it across retries;
  text equality is not identity. Two intentional identical messages remain two
  turns. A duplicate receipt for one message remains one turn.
- Exact game, realm, server instance, channel/thread and native speaker/body
  identity. Bind the adapter caller at the authenticated boundary, not from a
  `trusted: true` flag or display name in JSON.
- Session epoch and native message/sequence identity, where supported. An old
  session's receipt must not certify a new body's speech after reconnect.
- Source observation time, publication time and receipt time as separate facts.
  A late receipt must not move a turn to the time its acknowledgment arrived.
- The explicit evidence type/state and the identifier it acknowledges or
  cancels. A cancellation names the pending attempt, not every matching text.
- Producer coverage: source scope/time interval, included/omitted counts and
  reasons when known. Missing counts stay unknown. A bounded snapshot/recovery
  mechanism is needed when revisions are missing or the producer restarts.

These bindings are conversation evidence, not authorization for movement,
orders, account actions, or current activity claims. Native body status remains
on its separate observed-state path with its own identity and freshness checks.

## Three concrete sequences

**A reply is superseded before publication.** A human asks H1. The model prepares
D1. Before D1 is published, the human adds H2 and the bridge supersedes D1 with
D2. The next packet contains H1/H2 and, if appropriate, D2 as pending. D1 must
not appear as something the bot already said. A later duplicate cancellation
of D1 must not remove D2 or another intentionally repeated sentence.

**Publication succeeds but native outcome is unknown.** The bridge publishes
D1 and then loses its receipt connection. A successful file replacement proves
publication only. Keep D1's native outcome unknown. Do not resend it, claim it
was spoken, or claim the bot stayed silent based solely on the missing receipt.
Native reconciliation, if supported and separately authorized, resolves it.

**A late native receipt arrives after a new human line.** A human says H1, the
bot actually says D1, then the human says H2. The receipt for D1 reaches the hub
after H2. Use the native message identity/order to insert D1 in its actual place;
do not append it as if it happened after H2. If that order cannot be established,
retain the uncertainty rather than manufacture a precise conversation order.

## Focused acceptance cases for an isolated producer candidate

1. Human observed → draft → published → native confirmed: exactly one confirmed
   bot turn, with the same body/session/thread all the way through.
2. Draft superseded before publication: no false confirmed turn; only the named
   attempt is cancelled.
3. Publication/crash ambiguity: unknown outcome remains unknown, with no retry
   or new model call caused by the receipt checker.
4. Wrong caller/game/realm/instance/thread/body/session receipt: rejected without
   overwriting the current turn or exposing another conversation.
5. Duplicate receipt and intentional identical messages: deduplicate by identity
   only. Conflicting contents under one native identity become a conflict.
6. Out-of-order receipt or reconnect gap: no invented ordering or freshness;
   require the producer's agreed reconciliation/snapshot behavior.
7. Private-room or cross-game context: no implicit raw-chat sharing merely
   because personas are shared. Keep existing visibility rules.
8. Default-off and rollback: legacy path unchanged; no new ingress reads,
   native hooks, deliveries, persistent migration or model spending.

Use synthetic fixtures and a fake provider first. Source-level tests can prove
consumer behavior; they cannot establish that a native game emits these
receipts. Real producer mapping and native delivery confirmation remain the
owning integrator's unresolved dependencies. This proposal does not unblock
any held device, live-game or rollout step.
