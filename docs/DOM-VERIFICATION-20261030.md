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

Follow-on refusal check:

```sh
DIT_JSDOM_MODULE="$PWD/build/dom-runtime/node_modules/jsdom" timeout 35 node tests/inspector_dom_refusals.cjs
```

All three cases passed: a positive sidebar tabindex, wrong JSON filename and
Blob bytes differing from the copy field each caused the real DOM runner to
exit 1 at the relevant assertion, with no success receipt. These were disposable
in-memory artifact mutations, not source edits. The unmodified generated preview
and its hash above remain unchanged. This check does not claim CSP enforcement
(jsdom does not enforce the artifact's script hash).

## Prepared native draft-default assertions

Coordinator follow-up `0a25b1a50738e384`; candidate checkpoint `2f5b971`.
Added a native-input sequence for empty-preview Enter focusing Goals, followed
by Space activation of Discard. Both outcomes are mandatory in candidate
receipt validation. The helper does not simulate default activation with DOM
clicks; it requests input through the existing CDP press function.

Executed offline checks:

```sh
node tests/draft_review_keyboard.test.cjs
python3 -m unittest tests.test_keyboard_runner
```

The actual-app fabricated adapter passed success plus typing/focus/discard,
Space, validation-focus and wrong-baseline refusal cases. All 13 Python runner
checks passed, including missing-field receipt rejection and option composition.
These fabricated input/receipt tests are not native browser evidence. Local
preflight exited 2 (Chromium missing; Node/unshare/true found); native execution
and isolation were not attempted. Exact candidate commands are in
`NATIVE-CURRENT-COMMAND.md`. The prior device bundle remains untouched.

## Finite latency mean follow-on

Coordinator `639067aa0d84a99e`; source `538ae44`. `node
tests/model_comparison.test.cjs` passed the new maximum-value and mixed-zero
regressions. The normal jsdom command passed all **143 checks**, zero transport
attempts, on preview **225233 bytes**, SHA-256
`feb22d78b00929fbfb0452baa8b2b91c19ac100fd28331017b688db8f50c65f2`.
Native status remains `not-run`. No browser installation or namespace retry
was performed: the documented Devbox isolation denial remains independently
unresolved. The current command document pins this new preview; prior receipts
remain tied to their earlier hashes.

## Grouped model sample review

Coordinator `00b2f207c3180b11`; source `3f8362a`. Added a read-only disclosure
table per exact model/purpose/source group. Focused actual-app comparison tests
passed, including distinct groups, missing observations, zeros and Unknown
measurements. Seven artifact checks passed before the final three refresh/text
assertions were added; the final complete artifact then passed **152 jsdom
checks**, with **zero transport attempts**.

Final preview: **230095 bytes**, SHA-256
`a0adae84cc23371f673ad3f65ff0cd91c81e3ed3617e52a42cd3fcfab629b447`.
The DOM run verified disclosure activation, scoped headers, local filtering,
literal markup in source/time labels, removal of old rows on unavailable data
and recovery from a new snapshot. The intermediate 149-check run applied to
`9acfbc62f147b5308f01d51e44daff84b9a65adca0568c48ca26de4ab2b7a5a7`,
not this final artifact. Native rendering, keyboard defaults and file saving
remain NOT RUN; no live services or devices were used.
