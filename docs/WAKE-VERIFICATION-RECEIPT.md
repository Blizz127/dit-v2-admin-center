# Local per-game 8450 readback intake

Admin reads `data/local/wake-verification.json` on each authenticated overview
refresh. No new endpoint, poller, receipt upload, network request or game control
is introduced. The owning DIT lead supplies content-free reviewed metadata through
the existing handoff; the existing Admin integrator places that accepted file
atomically. No actual cutover receipt has been installed for this change.
Deploying this source into an existing running server is separate; no restart
was performed here.

## Example format (synthetic; never copy as real acceptance)

```json
{
  "schema": "dit-admin-wake-readback-v1",
  "cutover": {
    "id": "synthetic-cutover-1",
    "completed": true,
    "destination": "banshee:8450",
    "completedAt": "2026-01-01T00:00:00Z",
    "receipt": "synthetic-cutover-receipt"
  },
  "games": [
    {
      "game": "enb",
      "cutoverId": "synthetic-cutover-1",
      "authenticated": true,
      "result": "ready",
      "observedAt": "2026-01-01T00:01:00Z",
      "receipt": "synthetic-enb-readback"
    }
  ]
}
```

Receipt references and cutover IDs contain 1–96 ASCII letters, digits, dots,
underscores or hyphens. Use content-free commit/receipt identifiers, not URLs,
tokens, response bodies, account names or chat. Times require explicit timezone.
The input is UTF-8 JSON, at most64KiB, with duplicate object fields and non-finite
tokens rejected; at most24 game observations. Invalid/missing input has no cached
fallback and cannot retain a verified claim. Extra fields are not displayed.

Canonical IDs are the twelve in the matrix: wow-vanilla, wow-forever, firefall,
eden, blacklight, tabula-rasa, ffxi, war, enb, planetside, marvel-heroes, rose.
Unknown IDs do not match another game. Duplicate observations for the same ID
withhold that row. Each positive row needs an exact cutover ID, boolean true
authenticated flag, ready result and time between cutover completion and now.
A global cutover flag or401/TLS smoke does not verify any game. A new cutover ID
invalidates old per-game observations until matching readbacks are supplied.

WAR and Marvel remain Held even if a positive row is supplied. This readback
format cannot lift owner restrictions. Readiness of always-on games is not
permission to start/stop them; all lifecycle controls remain absent.

## Meaning and UI behavior

The UI says **Verified readback (reported)**, with observation time and receipt
reference. This trusts the reviewed local handoff; it is not cryptographic
provenance verification or independent authentication of a remote service.
It does not certify current health, managed sleep/wake, gameplay or save safety.
Missing/invalid rows become Unverified on refresh; session reset or failed refresh
also clears displayed readback claims. Date-stamped verified observations do not
expire into a live-health claim: current health remains explicitly unknown.

The standalone preview has no real local receipt reader and no positive production
claim. Synthetic projection/component tests exercise the transition and refusal
paths. The exact approved8eb native-test bundle is unchanged.

E&B's separate deployment note now records coordinator5062dc077f7414a0's report
of the Net-7 empty-slot-fix image d30801c01c39 at8:13PM CT. No fix-specific client
acceptance was supplied, and deployment does not verify the8450 row.

Validation at6fe69a9: five pure projection/file tests, the actual UI renderer
with synthetic projection and refresh failure/reset, two isolated overview
handler checks, two relevant markup checks and two generated-artifact asset/CSP
and JavaScript syntax checks passed. Handler tests prohibit real sockets,
processes/hub access and confine reads to a temporary synthetic home. No native
browser, production receipt installation, service restart or device action ran.

## Reviewed owning-lead sources (October 30 follow-up)

The authenticated overview now includes `operationSources`, separate from
`wakeVerification`. `operation_sources.py` fixes the three owning-lead note
paths and reviewed SHA-256 values. Each refresh reads at most 64 KiB plus an
oversize sentinel per note, compares bytes, and returns only curated summaries,
references and expected hashes. Raw note contents, local paths and account data
are not returned. There is no subprocess, network request or new endpoint.
Matching bytes means the reviewed note is unchanged, not that a service is
currently healthy or that the owning lead's report was independently verified.

The current reviewed sources are:

- DIT `fa843e8`, `READBACK-20261030-0055.md`, in the bridge-integration checkout:
  the October 30 00:55–00:56 UTC observation retained AX41's controller and found
  no Banshee controller. Public HTTP 401 demonstrates transport only. Later
  source preparation (`2ce1940`, `d6ab41b`) is not a completed cutover receipt.
- SandalCore `docs/experimental/BANSHEE_SIGN_IN.md`: October 29 auth deployment
  and 23:01 UTC auto-provisioning update, with separate staging evidence.
  Owner PLAY/client acceptance is not supplied by this note.
- LOTRO's untracked owning-lead `owner-tailnet-instance-20261029.md`: owner-only
  public instance, Banshee dry-run and hostname advertisement. Public-instance
  Alienware client acceptance is not supplied; access rules are runtime-only.

All three matched their reviewed bytes during implementation. These are local
file observations, not live service observations. If a source is changed,
missing or unreadable, its row shows review required or unavailable on the next
refresh; its retained summary is explicitly dated context. A changed file must
be reviewed before updating its pin and summary. No automatic prose parsing can
promote readiness. Standalone builds package the reviewed summaries without
reading any outside source and display **Not checked in standalone preview**.
Session reset and failed overview refresh clear source-check claims.

Remaining restrictions and evidence gaps must not be conflated:

- WAR and Marvel retain their explicit holds. Tabula Rasa's companion hold also
  remains; none can be lifted by these note checks or a transport receipt.
- Ashes and LOTRO are outside the current twelve-game controller manifest.
  Neither has an established 8450 binding here; missing integration evidence is
  not a newly imposed owner hold. Their deployment reports cannot verify one
  of the twelve rows by alias or name similarity.
- The 8450 cutover still needs a completion receipt plus matching authenticated
  per-game readbacks. A shared route change alone cannot verify every game.
  Other per-game lifecycle/readiness gaps remain those listed in the matrix.
- Native browser execution remains with the device lead under the existing
  approved `8eb2c9f` bundle; this newer view has no native result.

Focused checks: two source-reader tests, one real in-memory overview-handler
check, actual UI source-state/duplicate/reset/failure coverage, and the existing
per-game verification UI check passed. Handler checks prohibit external calls
and confine reads to a temporary synthetic home; no production ledger was read.

## Cutover summary and per-game readiness

The repoint card now shows a separate `cutover` projection containing only the
validated ID, destination, completion timestamp and receipt reference. A valid
completion with no game observations displays **Cutover completed (reported)**
while all game rows remain Unverified or Held. This is a dated owning-lead claim,
not a fresh authenticated sign-in, current route observation or lifecycle permit.
The earlier fa843e8 observation remains explicitly historical context.

Absent, incomplete, wrong-destination or future completion claims leave the
summary unavailable. The UI also withholds per-game claims without a valid
cutover projection, and clears both on session reset or failed refresh. Six
projection/file tests and the actual UI synthetic refresh check passed. No
completed production cutover receipt was supplied or installed.

## Nonregular local evidence refusal

A disposable FIFO reproduced a blocked open in both the wake-receipt and
operations-note readers, before their byte limits could apply. They now share
`local_evidence.read_bytes`: open read-only/nonblocking, refuse a symlink at the
final filename, check the opened descriptor is a regular file, and read at most
64 KiB plus the existing oversize sentinel. The descriptor is closed on refusal.
This targets local special-file blocking; it is not a deadline for arbitrary
filesystem I/O or a claim to reject symlinks in parent directories.

FIFOs, directories and final-component symlinks yield the existing defaults:
null cutover and Unverified/Held game rows, or Source unavailable for notes. An
oversized regular note still reports Source changed — review required; an
oversized wake receipt remains invalid. A later regular file recovers normally,
without cached positive claims. No external source is opened by standalone mode.

Thirteen focused reader/handler checks passed, including special-file refusal,
descriptor closure, regular-file recovery and a real in-memory overview request
with two synthetic FIFOs. Handler file-descriptor reads are also confined to the
temporary synthetic home and must be read-only. No live service/device action or
production evidence read was needed to reproduce or fix this issue.


## Newer source preparation, separate from cutover — October 30

A local Git review found DIT `fd18286` (03:37:18 UTC),
`docs/evidence/ax41-retirement-20261029/QUIESCENCE.md`. Its current local bytes in
the bridge-integration checkout matched SHA-256
`26541c4d095d777ad9f58ebf7a68fae0bfa3c4e674e7a872642cef124a39fa07`.
This is a source checkpoint, not a deployment/readback observation. The optional
intake gate remains default-off with no runtime/config/CLI enabling it. Its
local blocker review can report clear while both writer-transfer permission and
runtime verification remain false. The note reports nine offline checks; Admin
did not rerun the owning project's tests or invoke its journal/state readers.

The operations view now includes a fourth reviewed source, `wake-preparation`,
with that provenance and explicit missing runtime/state/snapshot evidence. It
uses the same bounded local-byte check and standalone unchecked label. The
`wake-8450` source remains the separate fa843e8 00:55–00:56 UTC readback; no newer
completed cutover receipt was established by this review. No per-game status or
hold is lifted. Two source-reader checks and the actual UI synthetic check passed,
including a matched preparation note leaving cutover unavailable and games
Unverified/Held. No live service, game state or device was accessed.

## Local readiness filtering

The twelve-row matrix has a labeled acceptance filter: all mapped games,
Unverified, retained holds, or reported ready readbacks. Counts describe the
current projected rows, not live health, the complete launcher catalog or every
restriction mentioned in the row notes. WAR/Marvel retained holds remain
separate from other per-game lifecycle or companion restrictions.

Selection persists across overview refreshes. Only rows with the existing valid
cutover/readback projection appear in the reported-ready filter. Duplicate or
withdrawn observations return to Unverified. Filtering makes no API call. The
renderer retains its most recent accepted/cleared view separately from the
cached overall snapshot, so changing filters after a failed refresh cannot
restore old positive claims. Session reset clears the filter to all games and
removes prior readback claims. An explicit empty message accompanies zero matches.

Offline playtest: the default standalone snapshot has no completed cutover receipt.
All mapped games shows twelve rows, Unverified shows ten, retained holds shows
WAR/Marvel, and reported ready shows no matches. These are presentation states,
not actual service results. A synthetic projection/UI test additionally checks
positive observations, duplicate withdrawal, filter persistence, failed refresh,
filter changes after failure and recovery. Existing verification and two markup
checks passed. Native focus, select keyboard behavior and screen-reader
announcements have not been run for this newer preview.

## Readiness semantic snapshots versus native rendering

`tools/readiness_snapshot.cjs` reads a generated standalone artifact, requires it
to contain the exact current application source, parses that artifact's element
manifest, and runs the matching app in the existing minimal synthetic DOM. It
checks six scenarios and emits a JSON text snapshot of visible game IDs,
acceptance labels, cutover text, counts and empty-state visibility. The report
includes the exact artifact SHA-256 and size, and explicitly marks native
rendering and keyboard NOT RUN. It does not execute the full artifact driver,
CSS layout, browser default actions or a browser engine.

```sh
python3 tools/build_inspector_playtest.py
timeout 15s node tools/readiness_snapshot.cjs build/inspector-playtest.html > build/readiness-semantic-snapshot.json
```

The scenarios are no receipt/all rows, retained holds, no reported matches,
synthetic reported readbacks, duplicate identity withholding, and failed refresh
followed by filtering. Filtering must not add requests. The tool also refused
a temporary artifact with stale application code and one with a missing readiness
row, returning exit 1 without a success report. These refusal checks used copies,
not edits to the built preview.

The current standalone driver's automatic DOM path additionally contains five
readiness assertions for the default twelve rows, the two retained row holds,
counts, the empty reported filter and restoring all rows without requests. This
prepares real-DOM coverage when that newer artifact is actually opened/run; those
new driver assertions have only been compiled, not executed in a browser here.
It does not alter the older approved device bundle. Visual wrapping/clipping,
focus outlines, native select keyboard actions and screen-reader behavior remain
unverified. A semantic text snapshot cannot close those native-rendering gaps.
