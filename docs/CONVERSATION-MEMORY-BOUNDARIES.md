# Conversation memory boundaries

Source audit, 2026-11-08: Admin-owned isolated candidate
`build/context-slice/hub-compat-3dd21dc`, inspected at
`9c99e01ab1121b230773f3610f72f21673433920`, extending the earlier
`a3155646` integration. Build/test results are recorded separately in the
[current swarm handoff](../handoffs/context-boundaries-swarm-20261108/README.md).
This describes source behavior, not deployed behavior or authenticated native
delivery. It adds no activation, publisher, or release gate.

Selection means the existing `DIT_CONVERSATION_CONTEXT_GAMES` includes the game.
Status selection is independent. References below are relative to the candidate's
`src/Dit.HumanBehavior.Neuronetwork/` directory; line numbers identify this audit
snapshot.

## Prepared wording and observed input

| Path | Selected FFXI/SWTOR behavior | Source |
| --- | --- | --- |
| Incoming group line | Retains the supplied speaker's line and incoming relationship inputs. These are producer assertions, not proof of an outgoing bot reply. | `Conversation/Arbitration/GroupChat.cs:477–486` |
| Normal group reply | Skips outgoing `Pairs.Said` and `CompanionSaid`, including its bot journal, persona claims, recalled-fact use and follow-up bookkeeping. Supplied structured history remains available. | `GroupChat.cs:733–784`; `Conversation/ConversationService.Companion.cs:518–530` |
| Direct heard-line reply | Keeps the incoming speaker text/place; omits prepared “I said”/“I did” suffixes and `Finish`-generated exchange credit. Previously observed relationships remain. | `Conversation/ConversationService.cs:393–414` |
| Event wording | Keeps supplied non-channel event information without quoting the generated reply as spoken. A channel-start intent adds no event journal entry. | `ConversationService.cs:449–468` |
| Command decision | Records “requested …; completion unconfirmed” for selected games and preserves existing canary behavior. Command selection, returned arguments and execution routing are unchanged. | `ConversationService.cs:268–284` |
| Requested emote | Already returns an emote instruction and reserves the line without writing performed-action memory. No runtime emote fix was added. | `ConversationService.cs:192–203` |

Existing repeat suppression, focus, reservation/cooldown state, decision records
and counters remain. Names such as `Spoken`, `Arbiter.Spoke`, and a decision's
`say` kind do not establish native delivery. Existing stored memory is not
deleted or retroactively certified by these source changes.

`RecordChatEnvelopes` persists incoming player observations when an ingestor is
present; it is more than a diagnostic log. Its payload contains `heard.Text`,
speaker/channel/place and addressing, never generated reply text
(`Conversation/ConversationChatEnvelopes.cs:15–25,45–75`). FFXI's separate
`Games/Ffxi/FfxiFeed.cs:28–33` can classify addressed incoming chat as
`AnsweredBot`; `Dit.HumanBehavior.Neuronetwork.Hub/RelationshipJob.cs:72` consumes
that feed. This existing classification remains outside the `Finish` correction
and is not confirmation of earlier bot speech. The new heard-memory tests
intentionally isolate `Finish` without an envelope ingestor.

## Remaining callsites and reachability

| Remaining write | Reachability in the inspected candidate |
| --- | --- |
| `ConversationService.GroupKnowledge.cs:101–107` | Dormant under current defaults: `KnowledgeAnswers` requires both its backing switch and `AiOnlyChat == false` (`ConversationService.cs:631–643`); `HubRuntime.cs:88` sets it false. FFXI is in the knowledge-game set; SWTOR is not. Deliberately enabling canned knowledge later would reopen prepared pair/journal writes. This audit does not enable it. |
| `GroupChat.cs:557`, TR guide early return | The audit found a conditional cross-game leak: an installed guide could previously reach this write under an FFXI/SWTOR input game. The candidate guard restricts request/stop/accept handling at 555, offer registration at 580, and the `canLead` exemption at 770 to the exact existing `TrLeadExecutor.Game` (`tabula_rasa`). Each check precedes the `TrGuide` getter, including when a guide was explicitly installed. The remaining same-game TR write and execution semantics are outside this increment; no guide is activated. |
| `Games/WarhammerOnline/Chat/WarChatService.cs:788`, `CompanionSaid` | Its companion input is explicitly constructed with `WarChatContract.GameId` at lines 566–568. This caller is outside selected FFXI/SWTOR scope; no WAR delivery claim or change is made. |

The normal GroupChat call and the WAR caller are the two source callsites found
for public `CompanionSaid`. Its public API itself does not verify a receipt;
future callers must not treat passing a reply object as delivery evidence.

## Response identity and status timing

The selected structured client checks reply/group line IDs against the sent
correlation or request ID. Reply decisions must belong to the exact requested
actor key; group decisions cannot contain duplicate choices or case aliases
for that actor. ActorRef requires normalized lowercase keys, and hub responses
echo them unchanged. Raw native registry keys can distinguish case, so a
different spelling cannot be accepted as identity evidence. Event replies
can check only actor identity because that existing contract does not echo a
line ID. A mismatch is withheld before reporting the unrelated text, increments
the existing silence counter and returns `hub_decision=hub_response_mismatch`.
It does not call a local fallback. A rejected shadow comparison preserves the
separate authoritative result and is not described as an unreachable hub.
Flag-off response behavior remains unchanged.

Status binding is distinct from response identity. The candidate rechecks an
older retained fallback against its original request, not a newer rewrite's
view. It also rechecks successful wording after a slower command interpreter
has declined or failed. These guard expiry/change between internal stages;
they do not certify presence or delivery at the later native send. Successful
commands still return their instructions, and status-disabled behavior keeps
its existing path. Native post-response validation remains the adapter's job.

## Verification and producer dependencies

The [59ab778a verification handoff](../handoffs/prepared-memory-verification-20261108/README.md)
is historical: it records 8 focused passes for that exact earlier source. Those
results do not validate later increments. The current source passed all
81 selected C# checks at 2026-11-08T04:52:28Z, including the cases described
below and the authenticated localhost history-flow smoke. Admin presence
validation separately passed 26 Python/API checks. Source auditing itself
used no native game or model calls; the dated handoff retains both earlier
incomplete runs and the successful final run.
The 12 `PreparedActionMemoryTests` command/canary/emote cases use synthetic
catalogs, providers, identities and actions; no native executor or completion
authority is supplied. The four `CrossGameLeadIsolationTests` cases
(FFXI/SWTOR, context selection on/off) install an in-memory recording guide
with a fake executor and use a lead request plus offer-shaped model wording to
check that request handling, eligibility and offer registration cannot reach
that guide; no action is returned or pending offer installed. Existing ordinary
selected/legacy pair-memory behavior remains asserted. This is a game-boundary
guard, not a broader wording filter. No new TR compatibility test uses the
concrete TR executor: `Lead` requires that concrete type at `GroupChat.cs:645`;
TR execution and its existing tests were not exercised by this worker.

Real speech history still needs authenticated native observations bound to the
exact game/realm/instance, caller, body/session, channel/thread, attempt/message
identity and final text, plus observation/receipt timing and coverage/recovery
rules. Inbox publication, prepared decisions and synthetic receipts cannot
substitute. See [delivery evidence](DELIVERY-EVIDENCE-CORRELATION.md) and the
[turn provenance proposal](CONVERSATION-TURN-PROVENANCE-PROPOSAL.md).

Current body facts separately require a verified native-body mapping and explicit
presence lifecycle sharing the body epoch/revision, with field freshness and
gap/reconnect behavior. FFXI v1 has no presence field; SWTOR still needs its own
ordered native status feed. See [native producer mapping](NATIVE-STATUS-PRODUCER-MAPPING.md).
Removing a discretionary policy hold supplies none of these producer inputs.
