# Current local preview verification commands

UI checkpoint: `fde7d05` (sidebar/draft focus order and Blob export assertions).
Local artifact: `build/inspector-playtest.html`, **225123 bytes**.
SHA-256: `ad55e2ea0f8ce53f2ab26d7c70f4c66fd3773b50d61954f4f7f9e956b6e19e3d`.

## Executed DOM fallback

From this checkout with the pinned local tool dependency:

```sh
DIT_JSDOM_MODULE="$PWD/build/dom-runtime/node_modules/jsdom" timeout 15 node tools/run_inspector_playtest.cjs
```

Actual result: **143 checks passed**, jsdom 26.1.0, zero transport attempts,
artifact hash as above, `nativeKeyboard: not-run`. The runner uses Node
Blob/object URLs and a no-op scroll shim. Checks include draft input labels,
successful-preview focus retention, invalid goals/personality focus, empty-form
focus, changed/matching/Unknown baselines, discard and refresh behavior.
Additional checks cover all eight sidebar links and fragment destinations, draft
DOM Tab-order candidates in both directions, untrusted key events staying
`not-run`, the exact JSON download filename, Blob/copy byte equality and object
URL revocation after refresh. Programmatic focus and DOM clicks do not test
browser Tab/Enter defaults; the Blob assertion does not save a file.
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

On an authorized host with existing Chromium/Node selected through
`DIT_CHROMIUM` / `DIT_NODE`:

```sh
python3 tools/run_headless_playtest.py --expected-artifact-sha256 ad55e2ea0f8ce53f2ab26d7c70f4c66fd3773b50d61954f4f7f9e956b6e19e3d
python3 tools/run_keyboard_playtest.py --routing-audit --gap-export --draft-review --expected-artifact-sha256 ad55e2ea0f8ce53f2ab26d7c70f4c66fd3773b50d61954f4f7f9e956b6e19e3d
```

The previous Chromium attempt against artifact `96d4b70e` exited 2 before browser
launch because Chromium was unavailable. No namespace operation or localhost
browser session started. That blocker was not turned into a native pass by the
jsdom result. The native runner uses the isolated standalone file, not an HTTP
page. Draft input helper `f014678` requires its own complete receipt; eight option
combinations have offline orchestration coverage, not native evidence.

The approved `8eb2c9f` device bundle and delivered Alienware previews are
unchanged. These commands do not authorize a device run, browser install,
namespace bypass or substitution of that bundle. No real draft-review browser
success receipt is recorded.
