# Native Admin Center verification handoff

Status at 2026-10-29: all five initial source/setup tasks are complete. The open
dependency is the separately sequenced device execution/result, not another
implementation of those tasks. Coordinator ece1ccc9149873b9 reports installed
Alienware Chromium found and its Node symlink repaired; Admin has not polled the
device. The new one-run handoff remains with the sole device lead. The approved device attempt already ran once and returned
BLOCKED (exit 2) at 2026-10-29T23:20:30Z, before browser launch.
Owner decision `654f7a27-9461-4342-b15b-3ac086e79af6`, reference `a67509c69867`,
was explicitly ALLOWED at 18:08:28 CDT on October 29. Execution belongs only to
existing launcher/device lead `852bb105-8f9d-4a3f-a986-89a7981756dc`, with an
installed headless browser, separate temporary profile and synthetic artifact.
No occupied session, live/model call, install, public listener or denied-namespace
bypass is authorized. Approval is not an execution pass. See the exact pinned
[handoff](NATIVE-RUN-HANDOFF-8eb2c9f.md); no newer runner is substituted.

## Versions must remain distinct

| Artifact | Status |
| --- | --- |
| Alienware `236cd862` | Original preview, owner viewed and supplied design feedback; retained unchanged |
| Alienware `691f6c5d` | Redesigned layout, delivery hash verified; native checks not run by Admin |
| Handoff `ef740241` | Exact approved runner/UI pin `8eb2c9f`; executed once at 23:20:30Z, BLOCKED rc2: Chromium aliases and Node missing from PATH; browser not launched. Separate attempt requested after coordinator runtime inventory/repair; result pending |
| Local `867b7ca6` | Refreshed provenance includes nonblocking local evidence reader; source context remains unchecked in standalone; native pin and delivered previews unchanged |

Latest local file: `build/inspector-playtest.html`, 196734 bytes, generated at source
checkpoint `2249ea6`, including the regular-file evidence reader in source fingerprints.
SHA-256: `867b7ca62d7e6a310d2fa620c372275749ef9b1b7b0a5e75be421d547ceb57d0`.
Do not apply a result from an older file to this version. The native runner now
includes `artifactSha256` in its successful result, computed from the exact
temporary HTML it generated before launch.

## Ready native command

For the approved device run, use the separate pinned bundle from the handoff,
not this newer checkout. It requires installed Chromium, Node, Python and
functioning user/network namespaces:

```
python3 tools/run_keyboard_playtest.py --gap-export
```

This generates a private temporary artifact/profile, uses anonymous debugging
pipes, and has a 30-second process deadline. It checks sidebar Tab/Shift+Tab,
Enter-to-section focus/fragment at 1280 and 390 pixels, page horizontal overflow,
and measured coverage-card bounds (three non-overlapping columns at 1280, one
stack at 390, all within the horizontal viewport). Coverage geometry is required
in the validated receipt; source breakpoint declarations alone cannot satisfy it.
The same command also checks
assignment pager Enter/Space/boundaries, Escape cancellation, and native JSON
download with saved-file/copy equality. Exit 2 is blocked; exit 1 is incomplete or
failed. Neither is a pass. `--screenshots` additionally captures the existing
synthetic comparison examples; captured pixels still need review.

The current export uses a JSON Blob object URL. The native runner requires a
`blob:` link before Enter activation and saved-file/copy comparison. Real Node
Blob bytes and disposable-file equality pass offline, but do not establish that
a browser saved a file. Replaced/refreshed/reset reports revoke their old URLs;
the copy field remains available if Blob creation fails. No alternate browser flags,
sandbox removal, new listener or occupied-profile reuse is part of this handoff.

## Evidence already available

- Template/accessible-name/disabled-control and CSP/JavaScript artifact checks.
- Actual UI handlers in a minimal DOM: focus destinations, filters, exact-ID
  isolation, Unknown states, local-only navigation and refresh focus preservation.
- Named CSS declaration contracts at mobile/tablet/wide breakpoint boundaries.
- Export schema/types, differing fields, allowlisted values, copy/link parity.
- Fabricated native-protocol and file-refusal tests; receipt fields must be
  complete. These tests validate the runner, not a real keyboard or browser.
- Coverage-geometry validation tested with fabricated rectangles, including
  missing/zero/non-finite/out-of-bounds/overlapping cards and the wrong desktop
  arrangement. Passing these refusal tests does not establish real page geometry.

The cross-panel follow-up in `f5ef79e` covers FFXI shortcuts, issue observation and
owner-summary links, exact-bot ledger links, and roster-gap detail/return links.
Focused navigation/gap tests passed without extra reads. Rebuilt artifact CSP and
JavaScript checks also passed. The runner's artifact-hash receipt check passed
using a fabricated browser result; that does not upgrade native status.

## Still unverified

1. Native browser checks and saved download. The command result is known:
   exit 2 before browser launch, not pending execution.
2. Actual wrapping/clipping, visible focus outlines, table scrolling and mobile
   layout at owner window sizes, including zoom.
3. Screen-reader announcements and browser/device-specific interactions.

Devbox Chromium was missing; its previous user-namespace setup was denied.
Neither prerequisite was bypassed or repeatedly probed. REA requires an existing
executable/CDP endpoint and supplied no alternate browser runtime. The Alienware
session remains untouched by Admin. The saved Alienware receipt confirms missing
Chromium aliases and Node in PATH, with Python 3.14.8 and unshare 2.41.5 present.
Pre/rebuild/post manifests each matched 21/21; the original artifact reproduced.
See [the reconciled executor receipt](NATIVE-RUN-HANDOFF-8eb2c9f.md). No new run,
installation or substitution follows from this blocker. For any separately
authorized future host/run, retain
the complete receipt with artifact hash and distinguish automated results from
the owner's visual review. No game, live hub, model or security change is needed.

## Malformed receipt width follow-up

An offline reproducer found that a 401-digit integer width raised `OverflowError`
in the export validator's float conversion. Export width now must be a numeric
value greater than zero and no greater than 1280 (the workflow's largest fixed
viewport). The bounded comparison rejects huge integers, booleans, non-numbers,
NaN and infinities without conversion or a crash. Malformed native-output fixtures
return CLI exit 1 with no success receipt and no raw output disclosure.

All six focused runner tests pass, including the malformed-width cases through
the CLI's mocked browser boundary. No real browser was launched, no unchanged
artifact was rebuilt, and no native verification status changed.

## Ambiguous JSON receipt follow-up

A separate offline reproducer showed that `json.loads` silently kept the last of
two contradictory `status` keys, allowing that malformed receipt to validate.
The parser now rejects duplicate keys at every depth (even identical duplicates),
non-finite tokens and overflowing decimal/exponent numbers. It limits parsed
receipt input to 64 KiB of UTF-8; this is a parser bound, not a claim about process
output acquisition. Nested receipt validation still requires the existing fields.

Seven focused runner tests pass, including contradictory top-level/nested keys,
non-finite/overflowing numbers in otherwise ignored fields, the exact size boundary
and multibyte oversize input. The CLI rejects each invalid receipt with exit 1,
no success JSON and no raw-output disclosure. Existing width tests now expect
non-finite JSON to be rejected by the parser before geometry validation. All of
this evidence is offline/fabricated; no native run or device action occurred.

## Bounded process output acquisition

The shared subprocess runner now reads both pipes incrementally under a single
deadline. Native receipt stdout and stderr each have a 64 KiB acquisition budget;
the separate DOM-dump runner allows 2 MiB stdout. Exceeding either budget fails
with a generic error without returning captured content. UTF-8 decoding occurs
after collection, so split multibyte sequences remain valid.

Cleanup kills the owned process group, closes both pipes without draining them,
and allows up to three seconds to reap the parent. A descendant retaining an open
pipe cannot extend the acquisition deadline. This is process-group cleanup, not
a claim to contain descendants that deliberately escape their group.

Twenty focused capture/keyboard/headless-runner tests passed. Capture tests used
disposable local Python processes for exact byte limits, overflow on either pipe,
invalid UTF-8, closed-pipe timeouts and an inherited-pipe descendant. The latter
check establishes that the descendant stopped executing; host orphan reaping is
outside the runner. Browser-boundary tests remain mocked. No native browser,
device action, live call or artifact rebuild was performed for this change.

## Exact saved-file comparison

An offline file fixture demonstrated that invalid UTF-8 decoded to a replacement
character could pass the previous parsed-JSON comparison. The saved report must
now equal the copy field's UTF-8 bytes before JSON/schema checks. This matches the
UI's contract: its Blob and copy field use the same string. Encoding damage,
added duplicate keys and even added whitespace fail that exact-file check; valid
multibyte text still passes. The focused fixture runner checks this with temporary
local files and fabricated protocol calls, not a native browser download.

## Keyboard observer cancellation and release coverage

Focused fake-event checks cover Escape after keyup but before the scheduled
default-action observation, untrusted or mismatched key releases, unexpected
Ctrl/Alt/Meta/Shift modifiers and repeat events. Cancellation retains Start focus
and cannot be overwritten by the pending callback. An untrusted/mismatched release
cannot advance the step; a subsequent matching trusted release can. These exercise
the observer's state transitions only, not native event trust, Tab order or browser
default actions. The focused keyboard-observer check passed without a browser.

## Optional exact-artifact guard in the current runner

The current source runner accepts `--expected-artifact-sha256 HASH`. It writes
explicit UTF-8 bytes and compares the generated artifact before launching the
browser. A mismatch fails without browser execution or a success receipt;
temporary artifact/profile files are removed by the existing owned-directory
cleanup. Malformed hashes fail before runtime checks. A matching hash does not
skip keyboard, layout or requested export validation.

This option is for a separately scoped future run of the current runner. It is
**not available in the approved 8eb2c9f bundle**, and is not a reason to replace
that bundle or expand the device lead's current assignment. Its returned evidence
must still be attributed only to its pinned artifact, not this newer preview.
Three focused mocked runner checks passed, including mismatch/cleanup, matching
hash with incomplete receipt refusal and existing artifact attribution. Neither
a native run nor device delivery occurred.


## Source-only PATH preflight follow-up

The existing device result stays BLOCKED. Missing aliases in the recorded PATH
are not proof that a PATH edit can fix the run, nor evidence that compatible
executables exist elsewhere. No device discovery or retry was performed.

The **current source candidate**, separate from the immutable approved 8eb2c9f
bundle, now supports:

```
python3 tools/run_keyboard_playtest.py --preflight-only
```

This resolves Chromium, Node, unshare and true only. It launches no subprocess,
namespace or browser, writes no artifact/profile, and reports `nativeRun: NOT RUN`
and `isolation: NOT CHECKED`. Exit 0 means executables found; exit 2 means one or
more are missing. It does not check versions or promise compatibility.

`DIT_CHROMIUM` and new `DIT_NODE` can select already-installed executable paths,
including paths containing spaces. Defaults use the recorded PATH; there is no
shell startup, PATH mutation, cache scan, package lookup, installation or runtime
substitution. An explicit invalid, empty or non-executable selection is blocked
without falling back to another binary. Diagnostics name missing dependencies
without echoing the override values. A normal run still requires network
isolation and all existing receipt checks; no denial bypass is added.

Fourteen focused preflight/runner tests passed with fake executable files and
mocked launch boundaries. They cover the recorded missing Chromium/Node case,
explicit paths outside PATH, non-executable paths, invalid-override refusal,
preflight-only nonexecution, exact Node argument selection, namespace refusal,
and existing hash/receipt checks. No native browser was run. This code is not in
the approved bundle; do not silently replace its files or claim a rerun is ready
on Alienware until a scoped handoff identifies actual available runtimes and the
exact intended runner/artifact. The old run is completed and blocked, not queued.


## Host-specific runtime resolution — October 30

Coordinator request `e77a8c5237cbc11d` asks for runtime resolution, including
user-local installation if needed. This is a later request than the original
installed-runtime-only decision, but does not explicitly transfer Alienware
execution ownership from device lead `852bb105` to Admin. Admin returned the
specific host/ownership conflict through the coordinator; no new execution was
started and no dependency was installed.

Read-only Devbox inventory and current-source preflight:

| Host / evidence | Node | Chromium | Isolation | Run status |
| --- | --- | --- | --- | --- |
| Devbox, current nonexecuting preflight | `/home/blizz/.local/bin/node` found and executable | Missing from PATH; no candidate in checked locations below | Not checked now; previously denied, not retried | No browser run |
| Alienware, saved 23:20:30Z executor receipt | Missing from checked PATH | Four supported aliases missing from checked PATH | Never reached by that run | Attempt completed, BLOCKED rc2 |

Checked Devbox locations only: `~/.cache/ms-playwright`, `~/.cache/puppeteer`,
`~/.local/share/puppeteer`, `/opt/google/chrome` (all absent), and `~/.local/bin`
(no Chromium candidate). This is not an exhaustive filesystem inventory and says
nothing about Alienware's files outside its recorded PATH. Node installation on
Devbox is unnecessary and would not resolve the Alienware blocker. A browser
installation alone would not remove Devbox's recorded isolation denial.

The current-source `--preflight-only` result was:

```json
{"preflight":"blocked","executables":{"Chromium":"missing","Node":"found","unshare":"found","true":"found"},"nativeRun":"NOT RUN","isolation":"NOT CHECKED"}
```

The immutable approved **8eb2c9f** runner implements `DIT_CHROMIUM`, but neither
`DIT_NODE` nor `--preflight-only`. Do not pass the new flag to that pin or assume
DIT_NODE changes its Node selection. It resolves Node from its process PATH. Any
newly scoped device handoff must identify the intended host, existing executor,
actual installed executable locations and exact runner/artifact. No user profile
or global PATH edit, runtime substitution, namespace bypass or silent replacement
of the bundle follows from this documentation. The saved blocked attempt must
remain distinct from any future separately sequenced attempt.

All five initial source tasks are complete. There is no remaining implementation
in that list that would establish native browser evidence; repeating fixtures or
creating more UI features cannot resolve this host/runtime dependency.


## New bazzite runtime evidence and sequenced attempt

Coordinator `ece1ccc9149873b9` supersedes the unresolved host/ownership question
above: the same device lead is to make one separately sequenced attempt on bazzite.
The reported dangling Node symlink was repaired to
`/home/linuxbrew/.linuxbrew/bin/node` (v26.12.1), with rollback recorded in
`~/.local/bin/.node-symlink-change.txt` on that host. Existing Chromium was found
at `/home/blizz/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`
(Chrome for Testing 151.0.7922.34); the existing headless-shell alternative is
`/home/blizz/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell`.
No runtime installation was reported. These are coordinator observations, not
Admin live checks. Devbox remains excluded as a run host.

The [exact new handoff](NATIVE-RUN-HANDOFF-8eb2c9f.md) uses the first Chromium
path via DIT_CHROMIUM and process-local PATH=/home/blizz/.local/bin:/usr/bin:/bin.
It retains the original archive, runner, artifact and all safeguards. No newer
flags or files are mixed in. Namespace support remains untested on Alienware;
a failure is a new narrow blocker, never a reason to retry or bypass isolation.
The original 23:20:30Z BLOCKED receipt remains historical evidence; the second
attempt is requested, not claimed executed or passed. Admin's local archive
hash still matches a0bc47b1530d54ebb29b300e913f00a3ab6db434fca2007f0acabbafa1192ca7.


## Offline returned-evidence verifier

The [receipt intake guide](NATIVE-RECEIPT-INTAKE.md) provides a local reviewer for
the separately sequenced `ece1ccc9149873b9` attempt. It consumes existing returned
files plus reviewer-prepared identity metadata, checks the exact approved pin and
legacy fields, and distinguishes incomplete/blocked/failed/reported-pass. It makes
no device call and does not request another execution. Internally consistent
reports are not independently authenticated; the trusted executor handoff remains
necessary. Synthetic tests are not an actual native result.
