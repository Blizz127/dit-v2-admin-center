# Admin Center layout redesign — October 29, 2026

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
