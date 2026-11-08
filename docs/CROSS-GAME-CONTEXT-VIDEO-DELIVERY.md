# Cross-game conversation design video delivery

Owner requested a quick video explaining the new conversation design across
games, copied to the Alienware. Delivered and independently hash-checked at
2026-11-04T19:28:32.607911Z through the existing strict-host-key, batch SSH route
`alienware-bazzite`. Hardware readback: Alienware 16X Aurora AC16251.

Open **Downloads → DIT-Conversation-Overview-20261104-11735c60 → Start-Here.html**,
or open `DIT-Cross-Game-Conversation-Overview.mp4` in that folder directly.

Destination:
`/home/blizz/Downloads/DIT-Conversation-Overview-20261104-11735c60`

The silent, captioned video is 90 seconds, 1600 × 900, H.264/yuv420p, 24 fps,
2,160 frames and 940,551 bytes. It explains shared status, intact conversations,
per-bot memory, measured context budgets, game boundaries, delivery and the
Admin inspector. It is labelled as a proposed design throughout.

Video SHA-256:
`11735c602cc477fb21ecaaf22489992ce325fb7a176381c44f408a501bca45fd`

The package also contains the [written design](CROSS-GAME-CONTEXT-DESIGN.md),
`Overview-transcript.txt`, `READ-ME-FIRST.txt`, `Start-Here.html` and `SHA256SUMS`.
The destination was created exclusively; no earlier previews were replaced.
Directory mode is 0700 and files are 0600. A separate remote readback confirmed
all six file hashes and sizes. Local receipt:
`build/cross-game-context-overview/delivery-receipt.json`.

Verification: ffprobe metadata checked, full local video decode completed with
no errors, all ten slide thumbnails and one encoded frame visually inspected.
The renderer is saved at `tools/render_context_overview.py` and passes Python
syntax compilation. Documentation diff has no whitespace errors.

Alienware playback was not launched or tested. No game runtime, live model call,
context behavior or cross-game deployment was tested. Existing hub/bridge
worktrees, in-flight cleanup candidate, access choices and player/release holds
remain unchanged. The native-browser test hold is unrelated and was not retried.

## Implementation preview, 2026-11-04

The video was left unchanged. New offline previews were delivered at
`2026-11-04T19:55:19.766955+00:00` to its child folder
`Implementation-Preview-74b7b6a`:

- `Context-Receipt-Preview.html`: four captured FFXI/SWTOR reply/rewrite prompts,
  each retaining 12 supplied conversation turns; exact prompt and receipt details.
- `Status-Projection-Preview.html`: captured shared status views while fresh,
  after expiry and after a native disconnect. Not wired to live replies.
- `READ-ME-FIRST.txt`: implementation and verification limits.

All three sizes and SHA-256 hashes matched an independent remote readback via
the same existing strict SSH route. The exclusive destination and private file
modes preserve the earlier overview. Local receipt:
`build/context-slice/alienware-preview-delivery.json`.

Local implementation commits are `56924b8` (conversation) and `74b7b6a` (status).
Checks: 101 focused conversation .NET tests, 6 Python preview tests, and 16
status .NET tests passed. The hub candidates have not been integrated or
released. No native browser or Alienware playback was opened for these previews.

## Integrated preview, 2026-11-04

At `2026-11-04T20:31:16.929688+00:00`, the new
`Integrated-Preview-153855b` child folder was created alongside the earlier
previews. It contains `Integrated-Context-Preview.html` and `READ-ME-FIRST.txt`.
Both files' sizes and SHA-256 hashes matched a separate remote readback over
the same strict SSH route. No earlier files were replaced and no viewer opened.

The HTML pairs six actual synthetic service/serializer captures (FFXI/SWTOR
companion, heard reply and intent) with their bound status and prompt receipts.
Local commits: `8c71905` integration; `153855b` inspector. Verification: 92
focused .NET tests and 6 inspector Python tests passed. Production sources,
live flags, model calls, hub HTTP startup and native browser validation remain
absent. The existing video is unchanged.

Local delivery receipt: `build/context-slice/integrated-alienware-delivery.json`.

## Interactive context and delivery preview, 2026-11-08

After owner message `2c41e771389e7f0d` lifted discretionary policy pauses, the
previously prepared, undelivered interactive panel and delivery-evidence preview
were privately released to Alienware. Separate remote readback verified all six
files at **2026-11-08T00:44:20.452381+00:00** over the existing strict-host-key,
batch SSH route. No native prompt occurred. This is an owner-preview release,
not a deployed hub/server or game-client build.

Open **Downloads → DIT-Conversation-Overview-20261104-11735c60 →
Conversation-Panel-4fa9e59 → Start-Here.html**.

Source revision: `4fa9e59529ea011e17fc3c31edd1b90a98f1e174`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `Context-Panel-Playtest.html` | 283035 | `b2e1a140e34a371df546ec4bde83dc17ac637b21f7b5302c307c456a2e90f49d` |
| `Delivery-Evidence-Preview.html` | 38655 | `ca25cb7351b37453a278b1ef9bb9a43d39e1bca398b911cadf0a0bb7d36a1fae` |
| `Start-Here.html` | 1441 | `9af1055c9935a40d2a61703eb8a3e3e04c9a8eb7b96770325164076c1b70b2b6` |
| `READ-ME-FIRST.txt` | 1154 | `5b8f517a9a321074565a4e01aa1e4a6af1af954802c32cae2e9c82877fcba623` |
| `RELEASE.json` | 941 | `b97aa7e3871bbca1f9548fc7c33a4a67a84f07b776c1adfd6fc81bdb35537fd4` |
| `SHA256SUMS` | 436 | `3d9c8337a60b335a461da05bfa34f4b57978d08d49fb18a11b960e8b77dde8ca` |

The interactive file embeds the actual Admin application, twelve existing
synthetic context captures and two delivery examples; these are separate from
the `e55c7dc7` candidate-delivery harness exports. The static delivery page
compares eight evidence states. Four focused Python preview/CLI tests and both
simulated-DOM panel scripts passed immediately before packaging. All actual
delivery remains Unknown. Native rendering, playback, game behavior and real
model calls were NOT RUN; copying and hashing do not establish those results.

The exclusive destination has mode 0700 and each file mode 0600. Existing video,
previews and game/server files were untouched; no viewer, collector or service
was started. Rollback is to close the new files and optionally remove only this
new folder. Local exact readback receipt:
`build/releases/conversation-panel-4fa9e59-delivery.json`.

## Presence-consistency preview, 2026-11-08 05:17Z

A genuinely changed interactive preview, source `69ab75f`, was privately
released through the same existing strict-host-key, batch SSH route. Separate
remote readback verified five file hashes, byte counts and modes at
**2026-11-08T05:17:02.451238Z**. Open **Downloads →
DIT-Conversation-Overview-20261104-11735c60 → Conversation-Panel-69ab75f →
Start-Here.html**.

The inspector rejects known body facts without confirmed online presence,
while valid unknown status retains conversation history. The new Synthetic
presence conflict option exercises rejection and recovery for either game;
original source captures and delivery examples remain unchanged. Six focused
Python/API checks and two artifact-bound simulated-DOM scripts passed. Earlier
fixture-startup timeouts are retained in the
[release handoff](../handoffs/inspector-presence-release-20261108/README.md).

The panel HTML is 284,250 bytes, SHA-256
`d302c6043ce602e5b8e100851d2c615f9ed4f3b93271d64e02851fa3108e197f`.
The handoff includes the full package receipt. Directory/file modes are
0700/0600. No browser or game was launched; native validation remains NOT RUN.
This is not a hub/server or game-client deployment. Earlier preview/video files
remain intact; rollback is to close the new preview and optionally remove only
its new folder. No new copy of the unchanged static delivery page was made.

## Captured scope preview, 2026-11-08 05:43Z

Private preview **b57a9d3** was delivered and independently read back at
**2026-11-08T05:43:57.414657Z**. Open **Downloads →
DIT-Conversation-Overview-20261104-11735c60 → Conversation-Panel-b57a9d3 →
Start-Here.html**. All five package hashes, byte counts and private modes
matched; earlier previews/video remain intact.

The inspector displays the requested bot and captured native body separately,
rejects cross-game or instance mismatches, and retains requested scope/history
when native status is unavailable. Synthetic scope conflict exercises clearing
and recovery without changing source exports or delivery evidence. Seven
Python/API/contract checks and three artifact-bound simulated-DOM scripts passed.
The HTML is 285,480 bytes, SHA-256
`130da88c7353aca10a12f66b59d68b35dec9e742987e6e977506b7ef8abc18ec`.

The [release receipt](../handoffs/inspector-scope-release-20261108/README.md)
records exact source and evidence. No browser/game was launched and no
hub/server/game-client deployment occurred. Native validation remains NOT RUN.
Rollback is to close and optionally remove only the new versioned folder.

## Captured coverage preview, 2026-11-08 06:06Z

Private preview **bd3a4f9** was delivered and independently read back at
**2026-11-08T06:06:24.953673Z**. Open **Downloads →
DIT-Conversation-Overview-20261104-11735c60 → Conversation-Panel-bd3a4f9 →
Start-Here.html**. All five hashes, byte counts and private modes matched;
earlier previews/video remain intact.

Captured prompt receipt displays UTF-16 character usage/cap and the supplied
prompt SHA-256. Inconsistent counts/size are withheld, while valid omitted,
repeated, Unicode and empty conversation inputs remain supported. Token count
and earlier producer omissions stay Unknown. Eight focused Python checks and
four artifact-bound simulated-DOM scripts passed. HTML: 286,965 bytes, SHA-256
`23bf6ae0cbfc19ece46cd39db4a364e6e670587e813e4fc38458db39dc77af3f`.

See the [release receipt](../handoffs/inspector-coverage-release-20261108/README.md).
No browser/game was launched and no hub/server/game-client deployment occurred.
Native validation remains NOT RUN. Rollback is to close and optionally remove
only the new versioned folder.
