# Native Admin Center verification handoff

Status at 2026-10-29: all five initial source/setup tasks are complete. The open
dependency is native execution, not another implementation of those tasks.
Coordinator request `654f7a27` tracks a separately scoped Alienware run. No
authorization or completion is inferred from that request being queued.

## Versions must remain distinct

| Artifact | Status |
| --- | --- |
| Alienware `236cd862` | Original preview, owner viewed and supplied design feedback; retained unchanged |
| Alienware `691f6c5d` | Redesigned layout, delivery hash verified; native checks not run by Admin |
| Local `41b1b3a6` | Latest synthetic preview including selected-section cue, Blob export and cross-panel focus, not delivered |

Latest local file: `build/inspector-playtest.html`, 174749 bytes, generated from
UI source checkpoint `b307e85`.
SHA-256: `41b1b3a6b7dcf4eaa0ed7a4d9bfd8197ca84f1afb91559dca7d8b62a21a4616f`.
Do not apply a result from an older file to this version. The native runner now
includes `artifactSha256` in its successful result, computed from the exact
temporary HTML it generated before launch.

## Ready native command

From this repository on an authorized host with installed Chromium, Node, Python
and functioning user/network namespaces:

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

1. The full native command's real result and saved download.
2. Actual wrapping/clipping, visible focus outlines, table scrolling and mobile
   layout at owner window sizes, including zoom.
3. Screen-reader announcements and browser/device-specific interactions.

Devbox Chromium was missing; its previous user-namespace setup was denied.
Neither prerequisite was bypassed or repeatedly probed. REA requires an existing
executable/CDP endpoint and supplied no alternate browser runtime. The Alienware
session remains untouched by Admin. Once a valid host/run is available, retain
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
