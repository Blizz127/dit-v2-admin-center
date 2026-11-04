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
