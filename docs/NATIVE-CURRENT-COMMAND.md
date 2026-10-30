# Current local preview verification commands

UI checkpoint: `8c9ce8e` (draft validation focus and DOM assertions).
Local artifact: `build/inspector-playtest.html`, **221537 bytes**.
SHA-256: `524ed94c8f7d1807baf9e80a8d60619b28763fa23c5493a9feaa9c6bf2be6260`.

## Executed DOM fallback

From this checkout with the pinned local tool dependency:

```sh
DIT_JSDOM_MODULE="$PWD/build/dom-runtime/node_modules/jsdom" timeout 15 node tools/run_inspector_playtest.cjs
```

Actual result: **105 checks passed**, jsdom 26.1.0, zero transport attempts,
artifact hash as above, `nativeKeyboard: not-run`. The runner uses Node
Blob/object URLs and a no-op scroll shim. Checks include draft input labels,
successful-preview focus retention, invalid goals/personality focus, empty-form
focus, changed/matching/Unknown baselines, discard and refresh behavior.
See [DOM verification evidence](DOM-VERIFICATION-20261030.md) for installation,
first failure and first successful run history.

This is real DOM-engine execution with programmatic focus/events. It is **not**
native keyboard activation, browser visual layout, scrolling, file download,
CSP enforcement, HTTP transport or deployed-service verification. Component
checks and the separate temporary localhost mock checks also pass; draft-like
POST requests remain refused with 405. No service/device/game/provider was used.

## Prepared native browser commands — NOT RUN for this artifact

On an authorized host with existing Chromium/Node selected through
`DIT_CHROMIUM` / `DIT_NODE`:

```sh
python3 tools/run_headless_playtest.py --expected-artifact-sha256 524ed94c8f7d1807baf9e80a8d60619b28763fa23c5493a9feaa9c6bf2be6260
python3 tools/run_keyboard_playtest.py --routing-audit --gap-export --draft-review --expected-artifact-sha256 524ed94c8f7d1807baf9e80a8d60619b28763fa23c5493a9feaa9c6bf2be6260
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
