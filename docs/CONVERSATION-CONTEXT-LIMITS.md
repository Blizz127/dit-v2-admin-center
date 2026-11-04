# What the context receipt measures

The owner asked for maximum useful context per reply across games. The local
candidate fixes one known loss point: the shared C# client previously ignored
structured history and extracted only eight legacy trigger facts. That client
now carries structured history/current text when its game is explicitly enabled.
This does not recover history a native producer already discarded.

| Boundary | Current limit or behavior | What remains visible |
| --- | --- | --- |
| Shared C# client, legacy path | Up to eight history facts; default behavior stays unchanged | Existing legacy logs; no new structured coverage claim |
| Shared C# client, selected structured path | Newest 16 whole turns, preserving order and repeats | Optional callback reports supplied/prepared/omitted counts; preparing is not sending |
| Hub reply/group/event HTTP contracts | At most 16 history turns; larger input is rejected | Received input only; upstream history is not reconstructed |
| Structured request type | At most 32 turns and 512 UTF-16 characters per turn/current message; invalid larger values are rejected | Bounded request given to the prompt builder |
| Prompt builder | System + user text at most 24,576 UTF-16 characters; removes whole oldest history turns if needed | Exact input/retained/omitted turn counts and prompt hash |
| Mandatory context | Current message, grounding and correction stay when trimming history | If these still exceed the cap, building fails; it does not silently drop them |
| Model tokenizer/provider | No live token measurement in this work | Token count and actual model understanding remain unknown |

The request type's 32-turn capacity does not enlarge the HTTP contract's 16-turn
limit. Likewise, UTF-16 characters are not tokens, UTF-8 bytes, or the length of
the complete HTTP JSON body. The receipt hashes the actual system/user strings
used by the serializer. It does not prove a model saw, understood or delivered
them, and it does not measure history omitted before that request was built.

The inspector therefore labels the denominator **captured input turns**. A
packet showing 16/16 may have come from a producer that originally held 32 and
prepared only 16. Without the producer's separate report, that earlier omission
count is unknown. A missing native-status source does not erase this captured
conversation; it makes the body's status unknown.

## Separate FFXI Python producer

Read-only inspection of
`/home/blizz/dev/dit-ffxi-bridge-integration-20261029/tools/ffxi/ai_only/ffxi_chat_bridge.r12-candidate.py`
found a 16-entry per-scope ring and a 900-second age bound. Its group request
uses up to 16 recent lines, while several event paths use eight. Its separate
pair history holds up to four exchanges and a six-hour bound. These are
different sources of context, not one guaranteed full transcript.

This is an inspected **candidate source**, not a deployment readback. The bridge
worktree and running producer were not changed. The shared C# client fix does
not change those Python limits, and the ring cannot recover already expired or
evicted lines. Keep that producer's existing scope, stale-history protection,
delivery safeguards and sole-writer ownership.

Two additional source observations matter for interpreting that history:

- `on_heard` builds the group packet before `_on_heard` appends the current
  human line. The inspected path therefore does not automatically duplicate
  that current line into its own history. Do not deduplicate repeated text
  heuristically; a repeated line may be intentional.
- Several bot reply paths append generated text to the in-memory history
  before delayed `deliver` writes the inbox. Superseded replies have a removal
  path, but the append itself is not a native chat-delivery receipt. Inbox
  publication also does not prove the map displayed the line. Keep those
  distinctions when designing longer memory; do not label this ring a fully
  confirmed transcript or promote its activity claims into native status.

An eventual typed turn record should distinguish a native heard line, a pending
draft, a published inbox item and native-confirmed speech, using stable IDs and
scope rather than text equality. Pending/cancelled speech must not be represented
as something another player already heard. This is a proposed producer contract,
not a change to the current bridge or a claim that native receipts exist.
The [producer provenance proposal](CONVERSATION-TURN-PROVENANCE-PROPOSAL.md)
spells out the proposed states, ambiguous outcomes and isolated acceptance cases.

Inspection pin: bridge checkout `4fe1ac1477065d49b17b9b59aaeb81366cd32ef0`;
candidate file SHA-256
`eb703d020b466b73778806d7d46496d57189abdeac9ad25a95d0f282c4174505`.

## Next integration decisions

1. Carry a separate producer coverage receipt through the trusted adapter path
   if the owner needs one end-to-end denominator. Record source scope/time
   range, supplied/retained/omitted counts and why lines were omitted. Do not
   call estimated or missing counts zero.
2. Any transport expansion must update producer and hub bounds together, keep
   bounded payloads, and preserve the native game's thread/recipient scope.
   Raising the prompt type's limit alone changes neither existing transport nor
   history collection. No transport expansion is part of the current patch.
3. Longer-lived memory needs provenance, privacy/scope and invalidation rules.
   A summary or remembered bot claim must not become current native status.
4. Compare natural conversations only in a separately released owner playtest.
   No real model call, game action, live flag change or native-browser run is
   authorized by this source audit or by a full synthetic turn count.

Implementation and verification:
[producer handoff](../handoffs/producer-context-status-20261104/README.md),
[producer evidence dependencies](NATIVE-STATUS-PRODUCER-MAPPING.md), and
[browser checklist](CONTEXT-NATIVE-BROWSER-CHECKLIST.md).
