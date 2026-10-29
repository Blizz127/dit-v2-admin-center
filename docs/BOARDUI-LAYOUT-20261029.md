# Admin Center layout redesign — October 29, 2026

Current version map, pending native dependency and exact runner handoff:
[Native verification gap](NATIVE-VERIFICATION-GAP.md).

Owner task `4e9c2ab65b28`. The owner actually opened the earlier Alienware preview
and reported that it looked good but needed a layout similar to BoardUI, while
keeping the current color scheme. This is owner-reported visual feedback on
`236cd862`, not an automated rendering, keyboard, download or controls pass.

## Reference and design

The exact requested URL, https://designeer.xyz/resources/boardui, was inaccessible
through the web tool; a direct read also failed. We did not view or reproduce that
page. The following official BoardUI resources were accessible:

- https://www.boardui.com/components/home-dashboard — dashboard structure and responsive navigation.
- https://www.boardui.com/components/sidebar — navigation structure.
- https://www.boardui.com/og_image.png — retrieved and visually inspected: navigation rail, compact filters, bordered rows, rounded cards and separated summaries.

The new layout is original HTML/CSS in this repository. No BoardUI source, image,
font, logo or other asset is bundled. Existing background `#09111e`, panel
`#111e2e`, teal `#80d7d1` / `#a2e4e0` and amber `#f2ce8f` are retained.

- Desktop navigation stays in a rounded left rail. Native section links work
  without adding another routing layer or hiding evidence destinations.
- Eight sections separate Overview, Bots & inspectors, FFXI, Learning & issues,
  Evidence & audit, Network & operations, Models & safeguards, and Workspace notes.
- Coverage is presented in three cards. The roster sits beside its inspector on
  wide screens, with filters grouped into consistent toolbars.
- Intermediate and narrow widths stack panels. Mobile navigation stays visible
  in two columns; wide comparisons scroll within their named table region.
- The file preview labels all data synthetic, hides the unnecessary token form,
  labels simulated hub responses explicitly and collapses the long check report.
  Automatic fixture navigation returns to the dashboard when finished.

## Scope and focused verification

Existing panel/control IDs, record matching, coverage wording and read-only
behavior are retained. The application data logic is unchanged. No endpoints,
model controls, credentials or live services were added or enabled. The artifact
continues to embed its own CSS/JS/data with CSP `connect-src 'none'`.

Passed before packaging: existing markup/accessible-name/disabled-control checks;
embedded-asset, CSP hash and assembled-JavaScript checks; connected in-memory
handler/overview/inspector scenarios; exact-ID comparison/JSON parity scenarios.
An additional static comparison found no removed original IDs and no broken
new section anchors. These checks do not establish native rendering or keyboard
behavior. No full suite or live request was needed.

Native Devbox rendering remains unavailable: Chromium was missing and the prior
namespace setup was denied. No denial was bypassed. Alienware rendering, keyboard,
native JSON download and responsive appearance for this redesign are **NOT RUN**
by the agent. Owner viewing of the previous build does not verify this version.

## Owner review

Open the new versioned HTML file from Downloads. No login is required. Try the
left navigation, resize the window, inspect a uniquely identified bot, and expand
Overview → Roster identity gap details to compare duplicate records. Evidence and
Unknown labels should remain visible. Model controls remain disabled.

The prior `DIT-Admin-Center-Preview-236cd862` folder is retained as rollback.
## Verified Alienware delivery

Source commit: `2ebe87f`. Built with `python3 tools/build_inspector_playtest.py`.
Transferred through existing `alienware-bazzite` strict-host-key, batch SSH access
into a new private folder. Input bytes were checked before exclusive file writes;
remote readback and a subsequent independent SSH `sha256sum` / `wc -c` matched.

Exact owner path:
`/home/blizz/Downloads/DIT-Admin-Center-Preview-691f6c5d/Admin-Center-Synthetic-Preview.html`

Resolved path:
`/var/home/blizz/Downloads/DIT-Admin-Center-Preview-691f6c5d/Admin-Center-Synthetic-Preview.html`

Open from the file manager, or paste this into the Alienware browser:
`file:///home/blizz/Downloads/DIT-Admin-Center-Preview-691f6c5d/Admin-Center-Synthetic-Preview.html`

| Delivered file | Bytes | SHA-256 |
| --- | ---: | --- |
| Admin-Center-Synthetic-Preview.html | 171378 | `691f6c5d68fdd429b216ce1942e50d85ebe972e51b2ee277f37bea908f7cdd70` |
| READ-ME-FIRST.txt | 1742 | `0bbbaf3f27dd0cd7841dd60d5afd30560f1db15492ad11677f27be176c94795d` |

Before transfer, the prior HTML independently read back as the unchanged rollback
SHA `236cd862def35155295d0df707f86649e4a40e228798f6b3a204d329234f79c7`.
No device GUI input, browser launch, restart, game/save access, new listener or
access-control change was performed. File delivery is verified; new-version
native visual/keyboard/download behavior remains for owner review.

## Follow-up: section focus and loaded coverage

Sidebar links now focus their named section while retaining native fragment
navigation. Destinations use `tabindex="-1"`, so the normal Tab order does not
gain eight extra stops. Modified/cancelled clicks and hidden-workspace clicks do
not steal focus. Coverage-card Review buttons focus and scroll to the existing
loaded list; local filters and source selection remain unchanged.

`tests/workspace_focus.test.cjs`, `tests/data_coverage.test.cjs` and the existing
card markup checks passed. Coverage already uses the current snapshot; no second
fixture source was added. Missing/partial collections, zero-valued metrics and
duplicate IDs retain their existing semantics. These are synthetic handler/DOM
and static checks, not trusted Tab/Enter input or rendered-width verification.
Desktop/narrow CSS and naturally wrapping filter bars remain in place; actual
responsive appearance and native key defaults still require a browser pass.
The delivered `691f6c5d` file is immutable; these follow-up source changes are not
silently substituted into that delivery.

## Follow-up: inspector return path

Explicit bot/learning Inspect actions now focus their detail panel. Rendering a
selected record during refresh does not move focus. Bot inspector has a Back to
roster button that returns focus to the current list without clearing game/name
filters or selection. Missing/repeated IDs remain disabled; no identity rule was
relaxed. Focused targets retain the amber focus outline.

Passed: `tests/inspector_focus.test.cjs` (same-name records with distinct linked
goals, filter retention, local-only inspection/return, refresh focus preservation),
existing connected coverage/inspector and gap-export checks, card markup checks,
and regenerated artifact CSP/JavaScript checks. The first new test incorrectly
expected an ID label in existing inspector text; its assertion was corrected to
check uniquely linked goal evidence, without changing the production display.

The regenerated local `build/inspector-playtest.html` includes these changes.
It has not replaced any delivered Alienware file. Actual native Tab/Enter/Space,
narrow viewport layout and JSON download remain unverified; do not treat these
component checks as a browser pass.

## Breakpoint and export contracts

`tests/test_responsive_contract.py` checks the actual stylesheet's named rules
at 320/390 pixels and either side of 760, 1100 and 1350 pixel boundaries. It checks
sidebar space release, one-column coverage/panels, mobile toolbar wrapping and
local comparison overflow. This is an exact-selector declaration check, not a
complete CSS cascade/layout engine, screenshot or measured viewport pass.

The export test now checks every top-level and candidate key, allowed value types,
positive unique snapshot-row indices, selected-row inclusion, differing-field
consistency and the limits array. Fixtures include Unicode, malformed fields,
non-finite/negative levels and whitespace-only snapshot timestamps. Blank timestamp
metadata now exports as null (Unknown). Download URI and copy JSON remain identical.
Three breakpoint contracts and the focused export test passed. Native save-file
behavior, wrapping/clipping and trusted keyboard input remain unverified.

The following BoardUI slice makes the narrow comparison table use fixed columns
with a minimum width derived from its actual candidate count. It retains the
named, focusable horizontal-scroll region and `overflow-wrap:anywhere` cells;
long identifiers therefore have an explicit column width to wrap within, rather
than requesting their full unbroken intrinsic width. Sidebar link labels can also
wrap within their navigation cells. Focused static/table contracts pass; this is
a CSS implementation change, not evidence that a browser rendered it correctly.

## Headless shell and export automation

The existing isolated native runner now includes `verify_shell_navigation.cjs`:
at widths 1280 and 390, it sends native Tab and Shift+Tab through all eight sidebar
links, uses Enter to activate each, and requires the named section to receive
focus and the matching fragment to be set. It also rejects page-level horizontal
overflow. The receipt validator requires this shell result in addition to the
existing assignment pager's Enter/Space/boundary and Escape-cancellation checks.

Run on a host with the prerequisites already available:

```
python3 tools/run_keyboard_playtest.py --gap-export
```

At the original runner checkpoint the JSON export used a data-URI link; the
subsequent Blob export change below supersedes that implementation.
The existing native path activates it with Enter and compares the saved file to
the displayed copy payload in a disposable directory. Standalone disk validation
no longer labels itself native activation; that field is added only by the
activation workflow. File-only verification cannot prove an Enter key occurred.

Current evidence: synthetic shell-protocol tests reject wrong traversal,
activation and overflow; export protocol/file tests reject missing, malformed,
extra or symlinked files; Python tests reject incomplete native receipts and
preserve runtime/isolation gates. All passed. These fabricated protocol results
are **not** native browser evidence. No new artifact build was necessary for
these runner-only changes.

REA's connected browser-tool schema was also inspected using the
`reverse-engineer-anything` runtime-observation guidance. It requires a
caller-supplied executable or existing CDP endpoint; it does not supply an isolated
browser here. No REA session, listener or browser was launched. The known missing
Chromium / denied namespace setup was not retried or bypassed.

Still needed on a suitable native host: the complete scripted keyboard/download
run and actual appearance review (wrapping, clipping, focus visibility, desktop
and narrow layouts). Alienware's occupied browser session has not been touched.

## Blob export follow-up

`45b8836` changes the report download to a UTF-8 JSON Blob object URL. The exact
allowlisted report is still shown in the copy field. The previous URL is revoked
when a different report is rendered, the snapshot refreshes or the session resets.
If Blob creation is unavailable, a plain explanatory message replaces the link
and the read-only JSON copy field remains usable. No error internals are shown.

Focused checks use real Node Blob bytes, Unicode data and a disposable saved file
to verify equality with the copy payload. Replacement/refresh/reset revocation,
copy fallback, strict report shape and connected handler/inspector checks pass.
The native runner now requires a `blob:` URL before its Enter/download sequence;
its fabricated protocol/file checks also pass. Rebuilt artifact CSP/JavaScript
checks pass without changing network or script restrictions. These checks do not
establish browser-specific Blob download behavior. The exact local artifact is
recorded in [the native handoff](NATIVE-VERIFICATION-GAP.md); Alienware files remain
unchanged and the native request is still pending.
