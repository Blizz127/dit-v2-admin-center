# Forever-style bot baseline: private preview release, 2026-11-08

Released through the existing `alienware-bazzite` strict-host-key batch SSH route.
A new exclusive folder was created, and an independent readback verified both
hashes, sizes and modes at **2026-11-08T16:34:39Z**. No new listener, access rule,
credential, service, browser or game change was made.

Open on Alienware: **Downloads → DIT-Admin-Center-Preview-8db3abe5 →
Admin-Center-Synthetic-Preview.html**, then go to Bots & inspectors.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 291173 | `8db3abe566c1491310ee0181df07d4fbeabf5139d957a4d24dc44588e1a8c1ac` | 600 |
| READ-ME-FIRST.txt | 1191 | `700cca5ab0f1612c4a8426d4d82e841a91923483d33908936a42fcebb88c2a5f` | 600 |

Source `2b903de`, built by `python3 tools/build_inspector_playtest.py`.

**New panels:**
- **Forever-style bot activity:** a synthetic exported WoW Forever bot log, read
  by `forever_botlog.py`. It shows per-bot engine state, what each bot is doing,
  recent decisions with rejected alternatives, and deaths with their last
  decisions.
- **Baseline bot style conformance:** the committed per-game tracker. See
  [the proposal](FOREVER-BASELINE-PROPOSAL.md).

**Checks:**
- Python suite: 454 tests OK.
- All 9 node test files pass.
- The artifact-bound inspector and coverage integration checks pass against
  this build.
- A localhost smoke run and a one-off render of real importer output through
  the panel code passed.
- Native browser: NOT RUN.

The data shown is synthetic. These are not real Forever bots and not live data.
Rollback: close the file and optionally remove only this folder. Earlier
previews are untouched.
