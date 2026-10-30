# October 29 service-move reconciliation

Coordinator `c501be1fa0be34bf` requested the missing LOTRO/wake handoffs in the
read-only operations view. Existing r2, corrected stackd and E&B cards were not
reimplemented. No live service/device call or control action was performed.

## LOTRO source boundary

Read `/home/blizz/dev/lotro-rust/docs/evidence/owner-tailnet-instance-20261029.md`.
It is an untracked owning-project note, not a committed deployment receipt.
Captured file SHA256:
`adca1885e96dfd8d742af34adbfef9bf0a2c4aa7ceaef641f520f18f8310fc9a`.
The card explicitly labels this weaker provenance. The note reports owner-only
public Banshee HTTP9080/UDP9000,2900, retained tailnet fallback and baseline,
and hostname advertisement updated at14:48Z. Server-side dry-runs used resolver
overrides; public DNS, actual owner reachability and client launch were not
established for that instance. Runtime-only allowlisting does not survive reboot.
No test password, owner public address, ticket or rollback command is exposed.

## Wake staging and Forever correction

Read DIT Git objects `95b32dd:docs/evidence/ax41-retirement-20261029/STAGING-T476U.md`
and `FOREVER-WAKE.md`; transport smoke was introduced in `9f24994`.
The temporary loopback TLS smoke returned401/TLS verification0, then cleaned up.
It is not a deployed replacement, authenticated launcher turn or managed wake.
Existing production8450 remains available; shared8446/8450 still reaches AX41.
Lifecycle/player bindings, renewal, final state and consumer cutover remain open.

The native Forever handback is dated23:5xZ (no more precise time invented),
reports always-on Banshee and no supported sleep/wake. Its staged readiness-only
facade is not connected to production/probes. Updated the older AX41 card to
identify shared transport, rather than imply an active Forever wake lifecycle.

E&B's existing dated move card remains; no fresh runtime status is inferred from
source presence. All cards remain observations with no control or network link.
