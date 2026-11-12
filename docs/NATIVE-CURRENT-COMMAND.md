# Current local preview verification commands

UI checkpoint: `a1840aa` (bot event correlation, target and exact login-generation context; prior features retained).
Delivered preview: `40bb2489`, **618515 bytes**.
Local artifact: `build/DIT-Admin-Center-Preview-40bb2489/Admin-Center-Synthetic-Preview.html`.
SHA-256: `40bb248996e8342a0db89d4b147cddfb16f9ba8da8e55ebf726f3117e444ff58`.
Private copy: Alienware → Downloads → `DIT-Admin-Center-Preview-40bb2489`.

## Executed DOM fallback

From this checkout with the pinned local tool dependency:

```sh
DIT_JSDOM_MODULE="$PWD/build/dom-runtime/node_modules/jsdom" timeout 30 node tools/run_inspector_playtest.cjs --artifact "$PWD/build/DIT-Admin-Center-Preview-40bb2489/Admin-Center-Synthetic-Preview.html"
```

Actual result: **193 checks passed**, zero transport attempts,
artifact hash as above, `nativeKeyboard: not-run`.
Measured DOM construction: 1032 ms; completion wait: 3542 ms. The command reads
the exact packaged HTML. Without --artifact the runner generates current source
in memory; a later source change then produces a different hash.
The exact packaged HTML passed before the 2026-11-12T06:49:25Z delivery.
The companion Admin-Center-Export-Review.html passed 195 checks using FFXI export 7;
its separate hash and receipt are recorded below. See the
[delivery receipt](BOTS-PARITY-PREVIEW-20261109.md#delivered-preview-40bb2489-source-a1840aa)
for focused checks and independent delivery hash readback. These timings are not a native-browser
benchmark. Runner checkpoints
`68af3bb`, `95afcee`, `a3034f6` use a monotonic five-second no-assertion-progress
limit and ten-second total completion limit, with the outer 30-second process
limit in the command above. Failures report bounded progress/hash diagnostics;
parse errors are not mislabeled as timeouts. The prior five-second total wait
was replaced after a measured timeout with 145 completed checks and no errors. The runner uses Node
Blob/object URLs and a no-op scroll shim. Checks include draft input labels,
successful-preview focus retention, invalid goals/personality focus, empty-form
focus, changed/matching/Unknown baselines, discard and refresh behavior.
Additional checks cover all eight sidebar links and fragment destinations, draft
DOM Tab-order candidates in both directions, untrusted key events staying
`not-run`, the exact JSON download filename, Blob/copy byte equality and object
URL revocation after refresh. Programmatic focus and DOM clicks do not test
browser Tab/Enter defaults; the Blob assertion does not save a file.
Grouped sample review also checks DOM disclosure, exact group rows, zero versus
Unknown, scoped table headers, filtering, text-only provenance and stale-row
removal/recovery.
Preview-only diagnostics in Overview and assignment history display their local
check state/count/last check. A five-second stall or ten-second total timeout
remains terminal; “Open check log” focuses the report without a request. These
are not imported executor receipts or bot/service health observations.
See [DOM verification evidence](DOM-VERIFICATION-20261030.md) for installation,
first failure and first successful run history.

This is real DOM-engine execution with programmatic focus/events. It is **not**
native keyboard activation, browser visual layout, scrolling, file download,
CSP enforcement, HTTP transport or deployed-service verification. Component
checks and the separate temporary localhost mock checks also pass; draft-like
POST requests remain refused with 405. No service/device/game/provider was used.

## Prepared native browser commands — NOT RUN for this artifact

Candidate runner checkpoint: `2f5b971`. The draft helper now uses Enter on an
empty proposal and requires focus to move to Goals with no preview. It then
uses browser typing/Tab/Enter to review a proposal and Space to discard it.
A current candidate receipt must include `emptySubmissionFocus: "goals"` and
`discardActivation: "Space"`; older receipts cannot satisfy this new coverage.
This changes the candidate helper, not the approved `8eb2c9f` device bundle.

Latest local `python3 tools/run_keyboard_playtest.py --preflight-only` exited 2:
Chromium missing; Node, unshare and true found. Native run NOT RUN; isolation
NOT CHECKED. No browser launch, device action, install or bypass occurred.
Coordinator follow-up `639067aa0d84a99e` allowed a local browser install as an
option. The separately recorded Devbox namespace denial remains unresolved:
`unshare: write failed /proc/self/uid_map: Operation not permitted` (historical
observation, not retried). Installing Chromium alone would not clear it, so the
lead selected the authorized offline-backlog alternative. No install occurred.

On an authorized host with existing Chromium/Node selected through
`DIT_CHROMIUM` / `DIT_NODE`:

```sh
python3 tools/run_headless_playtest.py --expected-artifact-sha256 40bb248996e8342a0db89d4b147cddfb16f9ba8da8e55ebf726f3117e444ff58
python3 tools/run_keyboard_playtest.py --routing-audit --gap-export --draft-review --expected-artifact-sha256 40bb248996e8342a0db89d4b147cddfb16f9ba8da8e55ebf726f3117e444ff58
```

The previous Chromium attempt against artifact `96d4b70e` exited 2 before browser
launch because Chromium was unavailable. No namespace operation or localhost
browser session started. That blocker was not turned into a native pass by the
jsdom result. The native runner uses the isolated standalone file, not an HTTP
page. Draft input helper `f014678` requires its own complete receipt; eight option
combinations have offline orchestration coverage, not native evidence.

These current-source commands do not replace the approved `8eb2c9f` device
bundle or modify any earlier delivered files. They do not authorize a device run, browser install,
namespace bypass or substitution of that bundle. No real draft-review browser
success receipt is recorded.
