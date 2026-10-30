# DOM engine verification — October 30

Coordinator request `6c2ce06914b1e61a` authorized a DOM-level offline fallback.
Installed jsdom **26.1.0** with 39 dependency packages under the ignored
`build/dom-runtime` directory, using `--ignore-scripts --no-audit --no-fund`.
Only public npm package downloads were involved; no system packages, browser,
service, device, game or account changes were made. The committed package/lock
files in `tools/dom-runtime` pin this tooling independently of application data.

The first run exposed missing jsdom Blob URL support; it failed, not passed.
The runner now explicitly uses Node's in-memory Blob/object URLs and a no-op
`scrollIntoView`. Those shims do not verify browser downloads, scrolling or
layout. Network entry points and DOM resource loading remain blocked.

Observed successful run:

```sh
DIT_JSDOM_MODULE="$PWD/build/dom-runtime/node_modules/jsdom" timeout 15 node tools/run_inspector_playtest.cjs
```

- `status`: `passed`; runtime jsdom 26.1.0, Node v26.12.1.
- `checks`: **100**, executing the generated artifact's full inline script.
- `transportAttempts`: **0**.
- `artifactSha256`: `96d4b70e3450cb17864b207e54017236b07427ccc7e4146681e7322ade93e7f1`.
- `nativeKeyboard`: `not-run`.
- Shims: Node Blob/object URLs; `scrollIntoView` no-op.

This includes draft preview, validation, review of changed/matching/Unknown
baselines, discard and refresh assertions. It is actual DOM-engine execution,
not the minimal simulated-DOM component adapter used earlier. It does **not**
verify native keyboard activation, browser rendering, scrolling, file saving,
CSP enforcement, HTTP transport or deployed-service behavior. Previous blocked
Chromium/device attempts remain blocked; this is a distinct kind of evidence.

To recreate the tool directory when needed (not a default test installation):

```sh
mkdir -p build/dom-runtime
cp tools/dom-runtime/package.json tools/dom-runtime/package-lock.json build/dom-runtime/
npm ci --prefix build/dom-runtime --ignore-scripts --no-audit --no-fund
```

The runner itself never installs packages. Its missing-module check still exits
2 and was verified separately after this change. No browser-isolation denial
was retried or bypassed.

## Follow-on draft focus execution

Checkpoint `8c9ce8e` focuses the first invalid draft field, focuses Goals for an
empty proposal, and preserves preview-button focus after valid submission.
The standalone driver also checks associated labels and validation descriptions.
The same jsdom command then passed **105 checks**, zero transport attempts, on
artifact `524ed94c8f7d1807baf9e80a8d60619b28763fa23c5493a9feaa9c6bf2be6260`
(221537 bytes), with the same two declared shims and `nativeKeyboard: not-run`.
The earlier 100-check receipt remains evidence for its earlier artifact only.
Ten focused Python mock/artifact checks also passed after this source change;
no browser rendering or native input is claimed.

## Sidebar, focus order and Blob export execution

Coordinator request `898e02a832bd569a`; source checkpoint `fde7d05`.
The same pinned jsdom command passed **143 checks**, with **zero transport
attempts**, on `build/inspector-playtest.html` (**225123 bytes**), SHA-256
`ad55e2ea0f8ce53f2ab26d7c70f4c66fd3773b50d61954f4f7f9e956b6e19e3d`.
Seven focused `python3 -m unittest tests.test_inspector_playtest` checks passed.

- All eight sidebar links follow the declared DOM order with zero tabindex;
  programmatic focus reaches each link, DOM click/fragment navigation focuses
  its destination and selects exactly one section, without a fixture fetch.
- The draft details section is opened before focus assertions. Goals,
  personality, preview and discard remain in DOM order; forward/reverse
  programmatic focus and untrusted Tab events do not trap focus or claim native
  navigation. Untrusted Tab/Enter/Space/Escape key events leave the native
  keyboard observer `not-run`.
- The JSON Blob has the expected MIME type and filename `roster-gap-row-2.json`.
  Its exact bytes equal the read-only copy field; parsed data retains both
  ambiguous candidates. Refresh revokes the old object URL.

The earlier intermediate 125-check run passed on artifact
`bece369cfa46a5987f9d7729453c87a6f943e68cdae0a8ae947defb0f572cdcc`;
it preceded the sidebar assertions and is not evidence for this final artifact.

Native visual layout, trusted keyboard/default Tab/Enter behavior and actual
browser file saving remain **NOT RUN**. The request to leave only visual
verification open cannot be supported by jsdom evidence: Node Blob/object URLs
and the scroll no-op are still explicit shims. No service or device changed.
The exact candidate native commands are in `NATIVE-CURRENT-COMMAND.md`; the
previously approved device bundle remains unchanged.
