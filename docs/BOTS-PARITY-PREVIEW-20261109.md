# Bots parity scoreboard and bot activity views: private preview release, 2026-11-09

Released through the existing `alienware-bazzite` strict-host-key batch SSH route, into a new exclusive folder. An independent readback verified both hashes, sizes and modes at **2026-11-09T05:20:50Z**. No listener, access rule, credential, service, browser or game change was made.

Open on Alienware: **Downloads → DIT-Admin-Center-Preview-2fb57117 → Admin-Center-Synthetic-Preview.html**, then go to Bots & inspectors.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 379711 | `2fb57117168ffdb1207e2ae3ba7990eae9e7a4496782028d4533007ebc1004eb` | 600 |
| READ-ME-FIRST.txt | 857 | `fd7075e2bf4667e210befb19b9587e82370113bd4c6c47070c18a032d2ce7b95` | 600 |

Source `1f843fa`, built by `python3 tools/build_inspector_playtest.py`.

**Checks:**
- 568 Python tests OK.
- 8/8 `tests/*.test.js` pass.
- Four `tests/*.cjs` files fail the same way at the previous HEAD (pre-existing).
- Native browser: NOT RUN.

**Data:**
- FFXI section: the real exported `[BOTS-V2]` log, owner masked.
- bot_event section: the hub's schema examples.
- WoW section: synthetic.

**Rollback:** close the file and remove only this folder.

## Update: preview 12439623 (source da8f914)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-12439623**. Readback at **2026-11-09T08:54:33Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 379946 | `124396233bdb9409585c11defc44bc8870e9508824d1b804223a708efea5b078` | 600 |
| READ-ME-FIRST.txt | 704 | `4d0be4b59b22042323d0c7faf6e81cfeec023655b99f79d3b60e9c9cdaa1f807` | 600 |

**Change:** FFXI Forever p-10 (Quests and progression) goes from Not started to Built. Evidence: ffxi-platform da14962 (talk/trade intents), kit v3.74 5be9158. It has not been installed or run live yet.

**Checks:** 568 Python tests OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 10bae052 (source 1a2ba9b)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-10bae052**. Readback at **2026-11-09T09:35:56Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 379643 | `10bae0527d1e7696c74975b653f809460a21bc1f1fad57912642acf496269a18` | 600 |
| READ-ME-FIRST.txt | 847 | `4e1bc433bbb0b90f22dd8ccf287e81ce78cf1073f7a5e3317d6ff31679879b73` | 600 |

**Change:**
- The FFXI activity section uses ffxi's export 2 (the live c2.8 run, sha `be2eea13`). The importer now reads the `rest` lines, so every bot line is recognized.
- FFXI LSB p-05 is now Partly live. p-03 and p-04 have new evidence.

**Checks:** 570 Python tests OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 7d576aae (source fe1c968)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-7d576aae**. Readback at **2026-11-09T09:55:38Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 379689 | `7d576aaee6e00be4d57bda61092a6cc7e13c128e7071e13ed95250d3daae6e49` | 600 |
| READ-ME-FIRST.txt | 998 | `5ab70b555d7094863af8678ef3b63215fb603e52f02765dede0b8b427cf8ed4a` | 600 |

**Change:**
- The importer reads the c2.9 order and level sync lines (from the frozen code; not live yet).
- FFXI LSB p-09 is now Built (inert at current levels). p-08 has new evidence.

**Checks:** full Python suite OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview c5743410 (source 627a749)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-c5743410**. Readback at **2026-11-09T10:22:15Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 379711 | `c5743410d6d58e8fedb4e62e2c9b6a7fed8568cad3243689a8d0e6909492d574` | 600 |
| READ-ME-FIRST.txt | 854 | `108caf121f26cb6a5c6d3285e8152f5cb612b2a1762d22fa44f8ec719078efb5` | 600 |

**Change:**
- The dead / release / revived formats are confirmed against ffxi's live lines from 10:08-10:09Z (regression test).
- FFXI LSB p-05 and p-03 cite the live death recovery, Sneak Attack, a weapon skill, a nuke and critical cures. p-05 stays Partly live, because return and weak have not been seen.

**Checks:** 573 Python tests OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 27b0d956 (source 8cf440d)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-27b0d956**. Readback at **2026-11-09T10:34:17Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 391586 | `27b0d956edaaa88a19d4a7cadf1b13b0c751ab046f175ed64394812d4a21047c` | 600 |
| READ-ME-FIRST.txt | 915 | `ea7509cb3ca19ccd07aaeeedbf18e25d44c33860b05811ca764d80d553866943` | 600 |

**Change:**
- The FFXI activity section uses ffxi export 3 (the live c2.8.1 run with two deaths, sha `a53acf46`). The page is larger because there are more events.
- The importer reads the c2.10 mount lines.
- FFXI LSB p-06 Mounts is now Built. p-03 and p-05 cite export 3 line numbers.

**Checks:** full Python suite OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 44c97512 (source 8f9bfbb)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-44c97512**. Readback at **2026-11-09T10:35:01Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 391592 | `44c9751230dd2bc2f598300a6c27e8b1ea783d65a51b9a5c04b0efccc313317e` | 600 |
| READ-ME-FIRST.txt | 723 | `6edffeb0c458d461889c8dba4af167d3ac6a5fbce4810e33de5e222020638f31` | 600 |

**Change:** only the evidence wording for FFXI LSB p-06. c2.10 will not be installed; the mounts ship as c2.10.1, which is pending. The status stays Built.

**Checks:** conformance and FFXI importer tests OK; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview bafffe06 (source cf18663)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-bafffe06**. Readback at **2026-11-09T10:43:27Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 391575 | `bafffe066002dd84f2af908f678aef4b6129f09354bb64e5571a74d35720f492` | 600 |
| READ-ME-FIRST.txt | 612 | `df37ad8aa63871176b233d16230b162000e431f8bb900a40372b2697e1966e1e` | 600 |

**Change:**
- FFXI LSB p-06 evidence: c2.10.1 is frozen (72dbbf89, 1370/0) and armed at 10:42:54Z.
- The mount log templates are unchanged from c2.10, confirmed by diffing the log calls in both frozen trees.

**Checks:** conformance and FFXI importer tests OK; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview f20cd94a (source 945aaa4)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-f20cd94a**. Readback at **2026-11-09T10:51:08Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 391508 | `f20cd94a823ae5711bfa80aaf991131f6b2f9f0cdb7a38aab14f210766260cb9` | 600 |
| READ-ME-FIRST.txt | 840 | `2dd3ee84aa05988e67f8343dfd888fbf24d2448f7f03cdabab0bc8980e00b640` | 600 |

**Change:** SWTOR release kc went live at 10:48:48Z (swtor-preservation, integrator 072376da).
- p-01 to p-05, p-08 and p-11 are now Built.
- p-06 and p-12 stay Designed, with updated evidence.
- No SWTOR cell is Partly live or Verified live: the bot event log has no rows yet, because no human has played with a squad.

**Checks:** full Python suite OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 49d6f942 (source b3b6c8d)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-49d6f942**. Readback at **2026-11-09T11:26:38Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 391732 | `49d6f942928be7f9fbb90b3a3da4c92cda3e805530b0bc76c9f59f1d1e402747` | 600 |
| READ-ME-FIRST.txt | 892 | `ea3965294a88bab375dcad09a506730d55a4a02f534b132a9d4deb2abee5a4a5` | 600 |

**Change:**
- The importer reads the J0a/J0b lines (profile, advice, gate notices).
- FFXI LSB p-12 is now Built: the seam is staged, not live, and its flag is off.
- The p-03 evidence notes that J0a is staged.

**Checks:** full Python suite OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview c2accf5c (source 5ffcd1f)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-c2accf5c**. Readback at **2026-11-09T11:40:30Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 415652 | `c2accf5cd3388924f442fb5ddb4f69a556cc3653a25212899dbef031d9147865` | 600 |
| READ-ME-FIRST.txt | 870 | `e291f4028ac062379f86d8121b7b51e5b6dcab64b9411b8959bbc24a7e0bb08a` | 600 |

**Change:**
- The FFXI activity section uses ffxi export 4 (the live c2.9.1 run, sha `4c4a1093`, 591 lines, all recognized). The page is larger because there are more events.
- FFXI LSB p-06 Mounts is now Partly live (c2.10.1 live; mount why=travel at 11:33Z, from ffxi's report).
- p-05 cites export 4 lines.

**Checks:** 577 Python tests OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview b1bc2e4b (source 9f18388)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-b1bc2e4b**. Readback at **2026-11-09T12:41:47Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 413993 | `b1bc2e4b7d5c3d64e0f5c8d166c8746a85a388337eeb868159926ebc771a7fc2` | 600 |
| READ-ME-FIRST.txt | 813 | `7064c420f4532ee0d29d315d623a4348cdd1bd0a3b1d8fe2d4d666f4fd6ce590` | 600 |

**Change:**
- The FFXI activity section uses ffxi export 5 (the live c2.10.1 run, sha `ce90dc67`, 575 lines, all recognized).
- The p-06 evidence cites the export 5 mount and dismount lines.
- J0b is live: p-03 notes that J0a is live, and p-12 says installed, flag off.

**Checks:** full Python suite OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 61035a76 (source 8af41da)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-61035a76**. Readback at **2026-11-09T13:22:29Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 414013 | `61035a7642e9822d40f64c718f78c89773102bcdc1bea4162c233970293679ab` | 600 |
| READ-ME-FIRST.txt | 644 | `2278af14775925a995c4c2b28d6a450d85d265221b81459909d227572685f5a0` | 600 |

**Change:**
- FFXI LSB p-03 cites the first live sub-job move: `apl=sub_nuke` Aero at 12:50:01Z (ffxi report; export 6 due).
- The J1-J3 batch (2267/0) is armed. Its log templates are unchanged from J0b, confirmed by diffing the frozen trees.

**Checks:** full Python suite OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 561cf2b9 (source def2205)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-561cf2b9**. Readback at **2026-11-09T13:43:51Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 401301 | `561cf2b999029916de41d2e4c84707942b6cff2638d1a108605df7087826216c` | 600 |
| READ-ME-FIRST.txt | 787 | `345c17d1854c48d98d0bcfb735f610309243ea7084cdc4246c9e556bb70d9ae4` | 600 |

**Change:**
- The FFXI activity section uses ffxi export 6 (the live J0b run, sha `027b96d5`, 508 lines, all recognized).
- The FFXI LSB p-03 evidence says all 22 job kits are live (J1-J4, FROZEN 9cbc76b7, 2445/0) and cites the export 6 sub_nuke lines. The status stays Partly live.

**Checks:** full Python suite OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 3a3bead0 (source f8766d7)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-3a3bead0**. Readback at **2026-11-09T13:52:38Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 401381 | `3a3bead0c3853559968e312feae76b5a4440bfbdc8f34be8510bdaa9b807513b` | 600 |
| READ-ME-FIRST.txt | 777 | `edcba1ded2456df6a9bb91b917dd94919489a0c8767a71eec99590efc45e1b31` | 600 |

**Change:**
- The importer reads the P2b formats (the order refusal suffix and the party_tactic release line).
- The FFXI LSB p-08 and p-12 evidence is updated; their statuses are unchanged.

**Checks:** full Python suite OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.
