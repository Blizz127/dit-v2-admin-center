# Structured conversation: offline hub candidate

Prepared for the DIT hub lead, 2026-11-04. This patch is an implementation
proposal in an isolated source snapshot. It has **not** been applied to the
shared hub worktree, deployed, or enabled. The hub lead remains the integrator.

## Behavior

With `DIT_CONVERSATION_CONTEXT_GAMES=ffxi,swtor`, the selected games carry
conversation history separately from the 16 trigger-fact slots. Unset means
the existing path. Game names match whole allowlist entries, case-insensitively.
This changes neither provider selection nor spending permissions.

The optional request section accepts at most 32 speaker-labelled turns of 512
UTF-16 characters each and a separate current message of at most 512 characters.
Room chronology and legitimate repeated text survive; unscoped pair history is
not appended as if it were newer room conversation. Properly scoped pair memory
is future work. These legacy strings are not authenticated event IDs.

The common wording builder keeps its existing 24,576-character limit. If needed,
it removes whole oldest turns, retaining the current input and required facts.
Its receipt records supplied/included/omitted counts, request identity, exact
system-plus-user character count and SHA-256. The digest input is UTF-8 encoding
of `system.Length + ":" + system + user.Length + ":" + user`, with invariant
decimal UTF-16 lengths. This is a prompt consistency check, not model-token
accounting, provenance authentication, comprehension or delivery evidence.

The consultation wrapper also receives retained history in its conversation
field rather than facts. Its legacy eight-turn limit remains for old requests;
structured requests permit 32 and retain a bounded serialized-input check.
The common wording receipt is **not** a receipt of the consultation wire payload.
The consultation delegate was checked, but its full HTTP payload was not captured.

## Source and verification

`BASE_REVISION` pins the source archived from `dit-ffxi-ls-replies-20261101`.
The isolated build is under `build/context-slice/hub-source`; generated output
and dependencies are not included in this handoff. Cached packages were restored
with package sources cleared and NuGet audit disabled, without provider calls.

Focused checks on the isolated candidate:

| Check | Result |
| --- | --- |
| StructuredConversationTests + FfxiRecentContextTests + FfxiSurroundingsPromptTests | 38 passed |
| DialogueWordingRegistryEvaluationAndContractTests + PersonaVoiceTests | 30 passed |
| ConsultingDialogueWordingProviderTests + ConsultQuestionTests | 33 passed |
| Admin receipt preview tests | 6 passed |
| Patch whitespace | clean |
| Read-only `git apply --check` against shared hub `4eb8d94e255fb6dc775160449940c459e0178f49` | passed; not applied |

No full suite, native browser, live model, native gameplay or owner playtest was
run for this candidate. The four synthetic captures in
`tests/fixtures/context-captures` come from the actual companion request builder
and DeepSeek JSON serializer: FFXI/SWTOR, reply/rewrite. Each retains all 12
supplied turns. The saturation test separately verifies whole-turn omissions.

To reproduce after applying in an authorized isolated hub checkout:

```sh
dotnet test tests/Dit.HumanBehavior.Neuronetwork.Tests --filter 'FullyQualifiedName~StructuredConversationTests|FullyQualifiedName~FfxiRecentContextTests|FullyQualifiedName~FfxiSurroundingsPromptTests'
dotnet test tests/Dit.HumanBehavior.DialogueWording.Tests --filter 'FullyQualifiedName~DialogueWordingRegistryEvaluationAndContractTests|FullyQualifiedName~PersonaVoiceTests'
dotnet test tests/Dit.HumanBehavior.DialogueWording.DeepSeek.Tests --filter 'FullyQualifiedName~ConsultingDialogueWordingProviderTests|FullyQualifiedName~ConsultQuestionTests'
```

Set `DIT_CONTEXT_FIXTURE_OUTPUT` to an empty local directory to capture the four
synthetic prompts during the first command. In this Admin repo:

```sh
python3 -m unittest tests.test_context_receipt_preview -v
python3 tools/build_context_receipt_preview.py tests/fixtures/context-captures/*.json --output build/context-slice/Context-Receipt-Preview.html
```

## Remaining integration boundaries

- Upstream producer count limits still apply; the receipt covers only history
  supplied to this builder. It does not claim the entire channel was retained.
- The native client `NeuronetConversationWordingProvider` still has its legacy
  fact extraction/eight-turn limit. This candidate creates structured context
  inside the hub; a later producer rollout must address that client separately.
- There is no shared status projection, epoch/sequence protocol, scoped memory,
  delivery acknowledgement or token measurement in this slice.
- The new optional constructor parameter is source-compatible; already compiled
  consumers may need rebuilding. No external producer contract is agreed here.
- The static preview is an explicit synthetic artifact, not a live Admin tab.
- Natural conversation quality and screenshot causality remain unverified.

Default-off rollback is to leave/unset the new allowlist and use the existing
code path. Any eventual integration or release follows the hub lead's existing
rollback procedure and active-player, source, access and release holds. This
handoff authorizes no live flag change or deployment.
