# Earth & Beyond host reconciliation

Source: coordinator message `d6fec0c7467dc466`, October 29, 2026,
5:29 PM CT. This is a relayed deployment observation, not an Admin poll.

- New Banshee host: `37.27.113.160`, named `enb.bansheerealm.com`.
- The coordinator reports that `enb` stack control is now local there.
- The AX41 copy is reported stopped and retained as rollback, not an active target.
- No exact unit names, ports or successful launcher control readback were supplied.

The Network & operations card preserves these distinctions and shows current
service status as Unknown. It contains no links to live services or action controls.
Neither this page nor a synthetic preview establishes DNS resolution, reachability,
player presence, successful migration or current service health.

The launcher owns Server Operations. Its inspected source already has an `enb`
entry in `GameStackCatalog.cs`, introduced in `4ce69118`, using the historical `e2`
Compose project and container aliases. That existing entry is not proof that its
mapping matches the new deployment. The launcher integrator and E&B lead must
reconcile the current target and exact service definitions through their existing
handoff. Admin must not start the stopped AX41 rollback to make a status card green.

Validation: focused markup checks cover placement, provenance, Unknown status and
absence of controls. No DNS/SSH/service call, restart, live status check or Alienware
delivery is part of this reconciliation. Native appearance remains unverified.

Four markup checks passed. The local standalone preview was regenerated with
the dated card; its asset/CSP contract and JavaScript syntax checks passed (two
focused checks). Runtime fixtures remain synthetic; deployment handoffs are
explicitly labeled separately. See `NATIVE-VERIFICATION-GAP.md` for the new local
artifact hash. Previously delivered Alienware files remain unchanged.
