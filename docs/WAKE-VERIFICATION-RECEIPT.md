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
