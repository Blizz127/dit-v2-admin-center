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
