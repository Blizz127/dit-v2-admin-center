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
