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
The delivery receipt below will identify the exact source commit and bytes sent.
