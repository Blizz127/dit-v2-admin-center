# Current-hub conversation candidate

Candidate `a315564614bc14853e00ea45d8c650ff68021e2a` combines the structured
conversation/status work and all three prepared-speech memory fixes with hub
`6a0121d6cf243957d44cd3e1533cdbd1f1540513`. It preserves the newer hub shout
diagnostics and its existing wording serialization fix. This candidate was
assembled only in the Admin-owned isolated checkout. Runtime source is
unchanged from integration `53a501ad`; the final increment fixes two synthetic
HTTP fixtures.

Verification completed at **2026-11-08T03:56:40Z**: the Hub build passed,
the unchanged runtime passed **16 memory/status cases**, and the final test
assembly passed **13/13 authenticated localhost HTTP checks**, with no skipped
checks. The runtime cases ran at `53a501ad`; the test-only follow-up kept those
runtime sources and DLL hashes unchanged. This is a verified local Debug
candidate, **not a published or deployed runtime**.

The group, ordinary-event and direct heard-line paths retain supplied
observations without treating an unpublished generated reply as something the
bot already said. The selected heard-line path also avoids awarding
response-dependent relationship credit for that prepared reply. Existing
memory and independent relationship evidence are preserved; there is no stored
memory cleanup. These behaviors use the existing structured-context opt-in;
flag-off behavior remains intact.

## Source intake for the existing hub integrator

`current-hub-candidate.patch` is the single replacement intake for a hub starting
at the revision in `SOURCE_BASE_REVISION`. It supersedes both patches in
`../swarm-speech-memory-20261108/` and the earlier multi-patch assembly. Do not
apply those older patches in addition to this one. An integrator that already
applied part of the candidate should reconcile that existing work rather than
reapply the whole patch.

`source-composition.json` records the exact candidate tree and patch hash.
Application in a temporary Admin-owned index reconstructed that tree exactly.
The 34 changed files include the existing speech-memory work and the two
HTTP fixture adjustments. The complete tree preserves the current hub's
unrelated source. No shared worktree or index was changed. Intervening hub changes belong to the existing integrator.

Publish an eligible increment through that existing hub publisher, preserving
its concrete player, data, native-permission and rollback safeguards. There is
no added coordinator acknowledgement, independent-review or full-suite gate.
This handoff does not establish that publication happened. No live flags,
shared service, game data or device were changed here.

## Verification boundaries

The event/heard candidate `efbbf699` rebuilt the changed Neuronetwork library
and its test assembly, then passed 16 focused cases at 03:38:12Z on 2026-11-08.
The test output's runtime DLL hash matches the newly rebuilt library. Unchanged
referenced projects reused the outputs verified at `59ab778a`; this was not a
full clean build. See `efbbf699-verification.json` and the adjacent log.

The first current-hub integration `53a501ad` kept that exact library source and
rebuilt the changed Hub and test assemblies. The Hub build passed with zero
warnings/errors; **19/22 checks passed, three failed**. All 16 memory/status
cases passed. One history case counted the asynchronous startup warmup as
conversation traffic; two shout startup cases exhausted shared inotify
instances. `53a501ad-run-result.json` and its log preserve that failed run.

The final test-only increment uses concurrent provider recorders, excludes
only the exact known warmup identity, and retains assertions on the number and
identity of actual requests. The fixed shout fixture disables configuration
reload in its own temporary app, matching the existing ingress fixture, and
disables asynchronous model extraction. No host limit or production
configuration was changed. The successful rerun rebuilt only the test assembly
and used the unchanged, hash-checked Hub/library artifacts; its separate log and result
record the outcome. The two affected classes include 13 HTTP cases, including
the existing caller/role/forged-identity checks; the 16 already-passing runtime
cases are not needlessly repeated.

An intermediate test rebuild at `4c5c2e3d` stopped on analyzer rule xUnit2031;
no tests ran in that attempt. The final test source uses `Assert.Single`'s
predicate overload. Its earlier log and result are retained separately.

The jobs use one logical processor/MSBuild node, nice 19, I/O priority 7, a
6-GiB GC cap, no restore, no project-reference rebuild and a 600-second bound.
The fresh integration sample measured 23.6% idle CPU, 129.69 GiB available
memory, 142 swap pages read and none written over two seconds, with low memory
and I/O pressure. The retired shared admission lock was not used.

Checks use synthetic identities, fake wording/status sources and disposable
storage. The HTTP cases start and stop a temporary loopback application with
fixture authentication. The history assertions cover 12 supplied turns and
32 supplied turns for each game: 12/12 are retained in the first case, and the
existing 16-turn producer limit retains the latest 16/32 in the second, with
the omission count reported. This is not unlimited history retention.

Command/requested-emote branches that bypass `Finish` and the independent
FFXI incoming-observation relationship classifier remain outside this memory
increment. No native speech receipt or body/presence source is established.
Actual native delivery stays Unknown. Native browser checks remain NOT RUN;
the earlier actual namespace denial is not bypassed. These missing native
observations are not a new policy hold on publishing the guarded source.

The separate e55/c301 synthetic delivery captures were not regenerated or
relabeled. The private owner preview `4fa9e59`, delivered to Alienware at
00:44:20Z, remains a distinct artifact; no duplicate preview was published.

## Rollback and continuity

The integrator should retain its previous release and configuration before
publication. Source rollback reverses this increment in its own isolated
checkout, preserving the hub's pre-existing serialization/diagnostic work.
No live rollback was performed for source this lane has not deployed.

The owner-requested swarm reused `/root/native_boundary_review` for the two
bounded event/heard source/test increments and the ingress-fixture follow-up.
That worker completed its work;
root reviewed, committed, integrated and ran the focused checks. No additional
worker, other lane, publisher or compiler fanout was launched. Historical
handoffs retain their original unrun/pending evidence; this dated receipt
supersedes their next-step status without rewriting those old results.
