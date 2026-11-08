# Prepared-reply memory fix: focused build completed

Isolated source `59ab778a2c424762e4064ac42b38730b227250cf` built successfully
and passed **8/8 focused tests**, with zero failures or skips, at
**2026-11-08T02:53:27.748955+00:00**. `focused-tests.txt` preserves the command,
resource measurements and output. `verification.json` pins the resulting local
Debug assemblies and records what was and was not tested.

This supersedes the **build NOT STARTED / tests NOT RUN** next step in the
[earlier source handoff](../release-resume-20261108/README.md). Its patch,
source revision and previous resource-refusal receipt remain unchanged; there
is no new code or fixture generation in this verification increment.

The owner retired the shared `temporary-heavy.lock` admission budget. Fresh
measurements showed 48 CPUs, 17.4% idle CPU, 152.6 GiB available memory, 396
swap pages read and none written over two seconds, memory pressure avg10 0.64%,
and elevated I/O pressure (some 20.04%, full 12.49%). The run used one MSBuild
node, two logical processors, nice 10, I/O priority 7, an 8-GiB GC cap and a
300-second deadline. No restore, compiler fanout, duplicate job, retired lock
or fixed load-40 admission rule was used. Correctness/serialization locks were
unchanged. The single job completed normally; no background job remains.

The four new memory cases verify FFXI and SWTOR with structured context on and
off: preparing an unpublished reply no longer inserts it into spoken memory or
outgoing pair history for selected games; the next request retains supplied
observed turns and existing observations; flag-off behavior remains intact.
The four existing candidate cases verify prepared replies with fresh status and
withholding when status expires during generation. All cases use in-memory
storage, fake providers/status and fictional identities. They instantiate and
exercise the conversation service; no hub HTTP process, live model, native game,
browser or authenticated native receipt was exercised.

## Updated intake for the existing hub integrator

Use the unchanged patch in `../release-resume-20261108/candidate.patch`, on its
pinned e55c7dc7 context/status base, or integrate isolated commit 59ab778a through
the existing source handoffs. This intake supersedes that handoff's pending
compilation step. The Admin-owned candidate is now locally built and narrowly
verified; the owning hub integrator remains the sole live writer/publisher and
must apply it to its current release source and perform its brief startup smoke.
No new coordinator approval or acknowledgement gate is added.

These local Debug hashes are not a published/deployed version. The shared hub,
bridge, live flags and game/server files were not changed. The existing private
owner preview remains the distinct 4fa9e59 release at 00:44:20Z; no duplicate
device copy or empty preview release was made. Actual native body/presence and
speech provenance still need the owning producers. Synthetic delivery exports
remain pinned to e55c7dc7/c301c99 and were not regenerated or relabeled.

Rollback remains the source handoff's isolated increment reversal; no live
runtime rollback is required for code that this lane has not deployed.
