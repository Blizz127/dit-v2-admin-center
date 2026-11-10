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

## Update: preview df9c0417 (source 89cc8d4)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-df9c0417**. Readback at **2026-11-09T13:53:13Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 401399 | `df9c0417f0a06c7b90d298649263aa7550f88f422b79202137a560cb762a9876` | 600 |
| READ-ME-FIRST.txt | 552 | `5bdc3fe71f50e551c9dbac59f5eca4c137d485482449c89fb6208d3f801a0a84` | 600 |

**Change:** P2b is now armed (13:51:33Z) in the FFXI LSB p-08 and p-12 evidence; the hub's question is answered. The statuses are unchanged.

**Checks:** conformance and FFXI importer tests OK; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview f4e7a43a (source 4a9c422)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-f4e7a43a**. Readback at **2026-11-09T14:52:14Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 401450 | `f4e7a43ac2a3d8d0f7fae2560b581f35e765cfdc5e292f8eb8406d04b53776d8` | 600 |
| READ-ME-FIRST.txt | 696 | `aad2c0eb0655ccdcece202a048d65b538068dcb8815e5dbff8e5557af6cbc785` | 600 |

**Change:**
- SWTOR p-03 cites release kf (live 14:50:07Z, rotations ON, all 48 disciplines, offline 288 fights). It stays Built because no humans have played since kc.
- SWTOR p-12 notes that kf writes decision/refused rows but issues no decision_advice.v1 request, so it stays Designed.

**Checks:** full Python suite 580 OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 47b73b12 (source 0734fbf)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-47b73b12**. Readback at **2026-11-09T17:22:31Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 429156 | `47b73b12618c52c822195147e6692938996efe098d20ebe8183dfea6ea443f1f` | 600 |
| READ-ME-FIRST.txt | 811 | `616bf09980cbe902e35222fd124e10af2759b5fac6b04af72d50448939f89896` | 600 |

**Change:**
- The FFXI activity section uses ffxi export 7 (the live J1-J4 run, sha `fb7b289b`, 1818 lines, all recognized).
- The FFXI LSB evidence for p-03/p-04/p-05/p-08/p-12 cites export 7 and P2b+C3.1 going live at 17:16:51Z. It also notes the bag_full trip bug (ffxi fix C5). The statuses are unchanged.

**Checks:** full Python suite 582 OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 27804f7b (source 2b85ca8)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-27804f7b**. Readback at **2026-11-09T17:42:58Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 429156 | `27804f7b9be8d1a77b92e3f317365e7c83b27b5adf6c6ab44482977710faa8b3` | 600 |
| READ-ME-FIRST.txt | 661 | `e32fbf75adaaeb286a70ad269b0df48c87e74fcbdd1a94ff1ba4276f90eed5a9` | 600 |

**Change:**
- The importer reads the six new ffxi C4.3 and V2-Q1.1 log templates: group party members/drop/off, slow eval, progression and roe.
- These are frozen, not live. The page content is the same as 47b73b12; only the importer's source hash changed.

**Checks:** full Python suite 583 OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 1fd4ed09 (source 9ab5ac5)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-1fd4ed09**. Readback at **2026-11-09T18:26:51Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 429156 | `1fd4ed095fee843031733829d846e0d7b3f2b7f2da3eb193e200af8e4de78ae6` | 600 |
| READ-ME-FIRST.txt | 556 | `74ee9f8158b373f213bef319024ce57bd297e9571a7d93363e14962cc307903f` | 600 |

**Change:**
- The importer reads the ffxi C5 line `bag full <bot> free=<n> (camping on, no sell path)`, and group trip ends with `why=group_<why>`.
- C5 is frozen, with an install batch staged, so it is not live. The page content is unchanged.

**Checks:** full Python suite 584 OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 5f0938d1 (source 57dbd97)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-5f0938d1**. Readback at **2026-11-09T19:38:47Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 429321 | `5f0938d1cbc61d2b22a4c31788a5f69d983772598b7741177d0c1fae25ab9a6e` | 600 |
| READ-ME-FIRST.txt | 709 | `db451af2a8e2d971c790c438540155c079630d4f38ab1370f6338c89b27b72f2` | 600 |

**Change:**
- FFXI Forever p-07 moves from Designed to Built.
  - The owner party of 5 was created in xiforever at about 19:07Z: ffxi handoff `2026-11-09-forever-cohort0-r2`, `out/bots-cohort0.tsv` sha `0ddd2c31`, readback 15/15 tables ok.
  - The bots are not yet in game.
- The p-01 evidence notes the same SQL apply; the map population install is still pending.

**Checks:** full Python suite 584 OK; 8/8 `tests/*.test.js` pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview df34aad9 (source dde07cf)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-df34aad9**. Readback at **2026-11-09T20:49:28Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 433248 | `df34aad9425a83932fd6ce362256ebf65fff20e49de16867fbcf29318f9d0a5c` | 600 |
| READ-ME-FIRST.txt | 1133 | `797a3203df363cfa35e5277366258c93d3a96b841c04cb3030ff878b9f3f6e2b` | 600 |

**Change (owner-requested DIT v2 review, commits c6e8766, 754f4e7, fa8c624, fbc00d1, dde07cf):**
- Human-feel signals per bot (cadence, group sync, trip schedule), from `human_feel.py`.
- The bot_event importer enforces the hub's chat rule (schema re-pinned to hub ea92d35a) and shows chat totals, bot names, areas and abilities.
- 16 SWTOR release-kf writer rows are a fixture; all are accepted.
- A coverage test holds one sample per FFXI C5 log template (all recognized).
- FFXI LSB p-03/p-04/p-10 evidence cites C5 live at 18:15:22Z; statuses are unchanged.

**Checks:** full Python suite 593 OK; 9 JS tests pass (8 `tests/*.test.js` plus `routing_audit_keyboard.test.cjs`, fixed in c6e8766); native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 6f42aca8 (source b63ba74)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-6f42aca8**. Readback at **2026-11-09T20:52:52Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 433440 | `6f42aca88c1dc5fb769fe4b359f9a8a4b65d31b12fa539ad041b58a06359ff15` | 600 |
| READ-ME-FIRST.txt | 580 | `35a4fca48e1b9452a393044152ae374553b933527ea8dd836aa9325cb7e6243b` | 600 |

**Change:** the WotLK Forever row notes the offline policy library the lead reported on 11-09; it is still Designed.

**Checks:** conformance tests OK (full suite 593 OK at dde07cf); native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 77a95eef (source 8f0dd65)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-77a95eef**. Readback at **2026-11-09T21:06:10Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 544692 | `77a95eef8fa0c2a18ff739a5582a4212573d294c0a5f603a3ec18b03953f63ae` | 600 |
| READ-ME-FIRST.txt | 879 | `46aea08bbe86cc7b2cf52b4337254e51b14c442aae5539d78c75590260a4ab6e` | 600 |

**Change:**
- A fourth bot-activity source: WoW Vanilla / Benilla playerbots, from the cmangos-classic event log (`vanilla_botlog.py`, env `DIT_VANILLA_BOTLOG_CSV`).
- The preview shows the live run of 11-09 19:27Z-20:52Z: 580 bots, 10 of them stuck re-pulling one mob (1,842 of 5,028 pulls; worst 562 pulls from one position).
- The cmangos-classic lane confirmed the cause and is building the fix (playerbots b893cfe9, release-20261109j).

**Checks:** full Python suite 598 OK; 9 JS tests pass. `inspector_integration.test.js` failed twice while the machine load average was over 600, then passed three runs in a row. Native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview 60ce6425 (source de4beef)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-60ce6425**. Readback at **2026-11-09T21:32:28Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 547554 | `60ce6425c7bea04eabc98272fb4ea27eaced80a3ea63d5f0d08ace6194c887a3` | 600 |
| READ-ME-FIRST.txt | 764 | `8bcb5d5654c40670ee01d91f09ce9426d2b2c29e3bb86161e00a6adc5166f83a` | 600 |

**Change:** a "Proven gaps in the loaded exports" list above the per-game sections. With the committed exports it has 16 lines: 10 stuck WoW Vanilla bots, 2 Vanilla bots on a 5 s retry metronome, Tomoe's 3.2 s casting, and the three FFXI bots' fixed departure clock.

**Checks:** full Python suite 598 OK; 9 JS tests pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview e6a77534 (source f229777)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-e6a77534**. Readback at **2026-11-09T22:04:16Z** matched both hashes; both files are mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 542617 | `e6a7753469c0d72430fb8a1d97e19308c046539ab43c9124c26ce531662a0edf` | 600 |
| READ-ME-FIRST.txt | 997 | `9d18bd56b0f1123766d6cdcbad32cf7a9883f67c2243d1d5f5dd7d4a56f77ed0` | 600 |

**Change:**
- The WoW Vanilla playerbot section uses the run after the stuck re-pull fix (cmangos-classic release-20261109j, log sha `3e2e82b5`, 4,149 rows, 449 bots).
- Against the first 33 minutes of the earlier run: runs of 10+ pulls with no kill 6 → 2; share of pulls in such runs 17.8% → 4.7%; longest run 121 → 37; pulls per kill 1.61 → 1.39.
- A loot row now ends a no-kill run. It changes none of these numbers.

**Checks:** full Python suite 600 OK; 9 JS tests pass; native browser NOT RUN.

**Rollback:** remove only that folder.

## Update: preview f0f50cd4 (source f8e24bc, includes 2c9e2cf)

Same route, new exclusive folder **Downloads → DIT-Admin-Center-Preview-f0f50cd4**.
Independent readback at **2026-11-09T23:10:51Z** matched both hashes, sizes and
mode 600. Previous previews remain available.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 544898 | `f0f50cd4d855ea6ddf0d12c78f0b8526b73c588ba0dd4f2446d94770a291838c` | 600 |
| READ-ME-FIRST.txt | 797 | `0b6e3ff53da8b3034151c958754f20d78a6114a43dda7ba5253500d5f85f8761` | 600 |

**Changes:**
- Missing or rejected Vanilla target names end a same-target run, preventing
  unrelated unidentified pulls from creating a false stall finding. Pull totals
  are retained. Both committed real exports keep their previous results.
- Event-list bodies render on first opening; reopening reuses the same body.
  A new snapshot receives new lists. Counts, limits and text escaping remain.
- Preview checks render the full bot exports and parity data at startup and
  restore them for the final owner view. Unrelated inspector scenarios use
  smaller snapshots instead of rebuilding those same imports 30 times. No
  existing assertion or timeout was removed.

**Verification:** the eight focused reader tests passed at `2c9e2cf`; the bot
activity JavaScript checks pass with the deferred list behavior. The generated
artifact passed all 176 simulated-DOM checks with zero transport attempts
(construction 1063 ms, completion wait 7583 ms). Its SHA-256 matches the exact
artifact tested. Native browser rendering and keyboard checks remain NOT RUN.
No full suite was rerun for this increment.

**Earlier failures retained:** the first invocation lacked the existing jsdom
module path. With that path supplied, the original preview timed out twice after
150 checks (18.9 and 20.6 seconds); deferred rendering alone timed out after 153
checks (11.2 seconds). Scenario isolation then passed under the unchanged
10-second check deadline. These timings are local observations, not a native
browser performance claim.

**Rollback:** use the preceding preview `e6a77534`; this release added only its
own private folder. No live hub/game deployment or device/browser execution.

## Update: preview 17e174cb (source 3a02594)

Private folder **Downloads → DIT-Admin-Center-Preview-17e174cb** on Alienware.
Independent readback at **2026-11-09T23:24:37Z** matched hashes, sizes and mode 600.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 545086 | `17e174cb2f6847fbad1323088063d0e1199af72a95aed2263495f19f8b111e1f` | 600 |
| READ-ME-FIRST.txt | 749 | `9001e0138b290b9b152dfcf43c33a38606aab23c665f6e322b8ec006c43c2c2e` | 600 |

**Change:** the Vanilla view labels XP-gain rows and repeated pulls without
recorded XP or loot. Neither a repeated-pull finding nor its absence proves a
bot is stuck or unstuck: low-level kills can produce neither signal, and target
evidence can be missing. The combined list is now **Patterns to review in the
loaded exports**. Measurements, compatibility fields and before/after counts
are unchanged. These labels supersede the earlier previews' stronger wording.

**Checks:** eight focused Python reader tests and the bot activity JavaScript
checks pass, including absent/malformed run evidence. The exact delivered HTML
passed 176 simulated-DOM checks with zero transport attempts (construction
456 ms, completion wait 4570 ms). Native browser rendering and keyboard checks
remain NOT RUN; no full suite or live game/hub action was performed.

**Rollback:** previous preview `f0f50cd4` remains available. Only the new private
folder was added.

## Update: preview b4d2c1d3 (source 1989b18)

Private folder **Downloads → DIT-Admin-Center-Preview-b4d2c1d3** on Alienware.
Independent readback at **2026-11-09T23:45:16Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 544446 | `b4d2c1d315bb52b9cd0551352bdbac6dbd444979aafdef9c6b1f8f9a9086e7c0` | 600 |
| READ-ME-FIRST.txt | 841 | `bb24e71a9a70ddd7d85b64ca206fbaadfffed41cb35ac00ea4a18a2a123dc7a5` | 600 |

The activity preview now uses release k: 4,261 rows, 473 bots, export SHA-256
`1fcc50b793dae1ff83acf8f87bad2cb57c98203086f805c44cdb59f6417c93c6`.
The file and all 120 redacted social rows were verified before copying.
Independent standard-library analysis agrees with the importer and producer:
against the first 1,928 seconds of j, qualifying runs fall 2 → 1, pull share
4.3% → 0.9%, longest 37 → 14, and pulls per XP-gain row 1.39 → 1.28.
The remaining run spans a respawn; differing populations and unlogged kills
prevent stronger causal or stuck-state conclusions. See the fixture README
for provenance, comparison boundaries and limitations.

**Verification:** 10 focused reader tests pass, including an equal-duration
regression. Two simulated startup runs timed out: 154 assertions at 11,452 ms,
then all 176 assertions at 10,444 ms. A diagnostic CPU-profile run of the exact
unchanged artifact passed all 176 assertions at 9,158 ms completion wait
(construction 1,093 ms), zero transport attempts. The ten-second limit was
unchanged. The timing failures remain part of the evidence; no native browser
or keyboard result is claimed. No full suite or live game/hub action.

**Rollback:** preceding preview `17e174cb` retained; only the new private folder
was added. The profile identifies fixed-ID selector tree traversals as a
concrete follow-up performance item, not a gate on this delivered increment.

## Update: preview bb887867 (source b7e2f5c)

Private folder **Downloads → DIT-Admin-Center-Preview-bb887867** on Alienware.
Independent readback at **2026-11-09T23:46:28Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 544446 | `bb887867146d893fc1620a2a64e80d375016f5cd39e709378264e73aa2d443dc` | 600 |
| READ-ME-FIRST.txt | 681 | `1a5dd853cdb3b818cdfc800347f3b3631d70a3bb69e7ceffad9f26b10b9c2e9b` | 600 |

**Change:** snapshot loading uses direct `getElementById` lookups for 14 fixed
IDs instead of selector searches. The previous CPU profile identified repeated
tree traversal in the installed DOM selector engine. This changes no data,
session checks, error handling or timeout. The release-k evidence is retained.

**Checks:** `source_race.test.js` and `overview_failure.test.js` pass, preserving
out-of-order response isolation, source failures, scoped details and recovery.
The exact delivered artifact passed 176 simulated-DOM startup checks with zero
transport attempts (construction 767 ms, completion wait 9,332 ms). Shared-host
timings vary; this is not a measured native-browser speedup claim. Native
browser and keyboard checks remain NOT RUN; no full suite rerun.

**Rollback:** `b4d2c1d3` remains available. No live hub/game action or launcher/feed
publication; only the new private preview folder was added.

## Update: preview acfa9efd (source fd08f4f)

Private folder **Downloads → DIT-Admin-Center-Preview-acfa9efd** on Alienware.
Independent readback at **2026-11-09T23:54:03Z** matched hashes, sizes and mode 600:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546028 | `acfa9efd160b16cdd02d6c010b3efb2021250193a2b8de7e2c5499105440fb26` | 600 |
| READ-ME-FIRST.txt | 733 | `f4f0cb2da2f2ab3d6dfbe20631e27fa908a602897d9b6faa6e885fd3b2bf41ff` | 600 |

**Change:** each imported activity source displays its supplied event range in
UTC, explicitly labeled as an offline export. Missing, invalid, reversed,
unavailable or empty ranges show Unknown. Strict calendar validation refuses
normalized invalid dates, and range ordering preserves microsecond precision.
No current timestamp or live freshness is inferred. Readers and release-k data
are unchanged; older sources without range metadata remain Unknown.

**Checks:** focused bot-activity JavaScript checks pass, including six valid and
30 missing/malformed range cases. The exact delivered preview passes all 177
simulated-DOM startup assertions (construction 549 ms, completion wait
4,695 ms), zero transport attempts. Native browser rendering and keyboard
checks remain NOT RUN; no full suite or live game/hub changes.

**Rollback:** preceding preview `bb887867` remains available; only the new
private folder was added.

## Prepared: preview 693e952a (source 43b2777) — delivery unconfirmed

Checkpoint **2026-11-10T00:06:41Z**. The legacy Forever importer now supplies
the oldest/newest retained event timestamps, before bot/decision display caps
and after malformed/duplicate-ID omissions. These are separate from the
manifest export timestamp. Empty, off and unreadable sources have null bounds.

Local package: `build/DIT-Admin-Center-Preview-693e952a/`.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546398 | `693e952a60ffb96f33ac07d04bf1f4bf605680f16a1ab96689d0bf453e691da9` | 600 |
| READ-ME-FIRST.txt | 695 | `04134bcfd981169ae89eee08da59c75d082eee1a1c24e52fe81aaa5acf555712` | 600 |

**Verification:** 53 focused importer/backend tests passed. The exact artifact
passed 178 simulated-DOM startup assertions (construction 872 ms, completion
wait 6,832 ms), zero transport attempts. No native browser/keyboard verification
or full suite is claimed.

**Delivery blocker:** the exclusive-folder/transfer command timed out connecting
to `alienware-bazzite:22` (exit 255). One subsequent read-only destination check
also timed out (exit 255). Destination creation/partial transfer state is
unknown; no remote hashes or final delivery are claimed. No further write retry,
device wake/restart or alternate publishing route was attempted.

**Next step when reachable:** read back the exact destination
`~/Downloads/DIT-Admin-Center-Preview-693e952a/` before completing any missing
files from the hash-checked local package. Preserve unexpected/mismatched remote
content, and verify both remote hashes/sizes/modes after completion.
Latest confirmed delivered preview remains **acfa9efd**; its rollback is intact.

## Prepared: preview 47db3b9c (source bfc68c7) — next delivery candidate

Checkpoint **2026-11-10T00:34:00Z**. This local candidate supersedes `693e952a`
for the next delivery and includes its Forever event-range update. The earlier
package and any unknown partial destination remain untouched. No Alienware
connection or publication was attempted for this offline increment.

Local package: `build/DIT-Admin-Center-Preview-47db3b9c/`.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546437 | `47db3b9ca714ee6a7cf11dc0c2337244e324d376d33c3926e79bb598aee5119d` | 600 |
| READ-ME-FIRST.txt | 862 | `a917651186e95f46a6bb81af31dfdb84ab1e03e9151febf7f06cab790f46e23b` | 600 |

**Change:** cadence, synchrony and departure labels compare unrounded ratios
against their existing thresholds; cadence ranking also uses the unrounded
share before the sample-count tie-break. Reported ratios retain three decimal
places. Previously, 900/1501 (about 59.96%) rounded to 0.6 and incorrectly
flagged all three signals, and could outrank a genuinely higher 300/500 result.
Regression cases now distinguish below-threshold and exact-threshold values.
Timing text says "near" and discloses rounded grouping instead of claiming
exact intervals. Labels remain heuristic observations, not human-behavior proof.

**Verification:** 20 focused Python checks (human-feel, Vanilla exports and the
FFXI J1-J4 export) and the bot-activity JavaScript checks pass. The exact HTML
passed 178 simulated-DOM startup assertions, zero transport attempts
(construction 1,242 ms, completion wait 9,129 ms). Native browser/keyboard and
full-suite checks were not run.

**Delivery:** blocked on the previously observed private endpoint timeout;
this candidate has not been copied or verified remotely. Once the endpoint is
available, read back its exact new destination before completing the package.
Latest confirmed delivered preview remains **acfa9efd**.

## Prepared: preview e6d43a85 (source 95deaff) — next delivery candidate

Checkpoint **2026-11-10T00:51:06Z**. This local candidate supersedes `47db3b9c`
for the next delivery and includes the pending event-range and timing-threshold
fixes. Earlier packages and any unknown partial destination remain untouched.
No new Alienware connection or publication was attempted.

Local package: `build/DIT-Admin-Center-Preview-e6d43a85/`.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546437 | `e6d43a850ff91e23d1d90f53ef6aaf85862ff83c2d359424cb212326641682b3` | 600 |
| READ-ME-FIRST.txt | 786 | `9740b1c9aea5b5800368ffc9b6bc11b98d5a20e4da70d1f7a63d5d2bb7cfb1c8` | 600 |

**Change:** malformed Vanilla log rows break repeated-pull continuity for all
bots because the rejected contents could have ended a run. Six valid pulls,
an omitted row and six more pulls no longer create a false twelve-pull finding.
Accepted event totals are retained; surviving runs may be shorter, as disclosed
in coverage text. Empty files now report zero omitted rows. The internal
continuity marker and rejected content are not exposed in the returned data.
Existing release i/j/k comparisons are unchanged.

**Verification:** all 14 focused Vanilla reader tests pass, including malformed
rows, multiple bots, reversed/interleaved timestamps, empty input and the real
release comparisons. The exact packaged HTML passed 178 simulated-DOM startup
assertions, zero transport attempts (construction 626 ms, completion wait
5,518 ms). Native browser/keyboard and full-suite checks were not run.

**Delivery:** remains blocked on the previously observed private endpoint
timeout. This package is prepared locally, not copied or verified remotely.
Read back its exact destination before completing any future authorized
delivery. Latest confirmed delivered preview remains **acfa9efd**.

## Prepared: preview c207fbc4 (source e026c1b) — next delivery candidate

Checkpoint **2026-11-10T01:03:00Z**. This local candidate supersedes `e6d43a85`
for the next delivery, retaining the pending event-range, timing-threshold and
malformed-log continuity fixes. Earlier packages and any unknown partial
destination remain untouched. No Alienware retry or publication was attempted.

Local package: `build/DIT-Admin-Center-Preview-c207fbc4/`.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546468 | `c207fbc4f1fa8a344abc493a43ce06b176a845f76994a2f1b61a0a78d54b6052` | 600 |
| READ-ME-FIRST.txt | 778 | `894ce83dfee6592e08448093aabc1ec73a66fce77424464ec452f5825e5daf51` | 600 |

**Change:** the activity count reports actual visible rows under the 200-bot
display cap. Previously, 201 matching bots produced 200 rendered rows but a
"Showing 201 of 201" label. The count now says 200 of 201, preserving the loaded
total and overflow notice. Filtering still operates on all imported bots.

**Verification:** `node tests/bot_activity.test.js` passed with focused cases for
201 imported bots, filtering below the cap, clearing the filter, replacement by
a smaller snapshot and no extra transport requests. The exact packaged HTML
passed 178 simulated-DOM startup assertions, zero transport attempts
(construction 613 ms, completion wait 6,101 ms). No full suite was run.

**Native browser:** a read-only local runtime check found no Chromium, Chrome
or Firefox executable or Playwright browser cache. Native browser/keyboard
checks remain NOT RUN; no installation, namespace-denial bypass or device
execution was attempted.

**Delivery:** blocked by the previously observed Alienware endpoint timeout.
This package is prepared locally, not copied or verified remotely. Latest
confirmed delivered preview remains **acfa9efd**.

## Prepared: preview 5322d9d1 (source 42bcca2) — next delivery candidate

Checkpoint **2026-11-10T01:04:23Z**. This candidate supersedes `c207fbc4` for
the next private delivery, retaining its visible-row count fix and preceding
pending reader/timing changes. Earlier packages and any unknown partial
destination remain untouched. No Alienware retry or publication was attempted.

Local package: `build/DIT-Admin-Center-Preview-5322d9d1/`.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546775 | `5322d9d1b8d270d3e03a868758f6532ebe4cae776d4d3a12b00bfc8ad7279ded` | 600 |
| READ-ME-FIRST.txt | 776 | `307e09555e844d9793bca2f5bf0f929d759b7746dc45bc5776f2acd707f0c443` | 600 |

**Change:** only sources with Loaded coverage display bot rows or contribute
review patterns. Previously, retained rows in an Off, Unavailable or Unknown
source could contradict the source warning by displaying as loaded activity.
Other Loaded sources remain usable; source recovery preserves local filters.
If no review source is loaded, the summary explicitly says Unknown rather than
claiming no patterns were found.

**Verification:** `node tests/bot_activity.test.js` passed with focused retained
row cases for Off, Not configured, Unavailable, Unknown, missing and unrecognized
status; unaffected sources; Loaded recovery and filtering; and missing versus
Loaded-empty review sources. The exact packaged HTML passed 178 simulated-DOM
startup assertions, zero transport attempts (construction 575 ms, completion
wait 7,027 ms). No full suite was run.

**Limits:** native browser/keyboard checks remain NOT RUN because no supported
local browser was found. Private delivery remains blocked by the previously
observed Alienware endpoint timeout. The package is prepared locally, not copied
or verified remotely; latest confirmed delivered preview remains **acfa9efd**.

## Prepared: preview 325142a5 (source 53e43f6) — next delivery candidate

Checkpoint **2026-11-10T01:23:36Z**. This candidate supersedes `5322d9d1` for
the next private delivery and retains preceding pending reader/UI fixes.
Earlier packages and any unknown partial destination remain untouched.
No Alienware retry or publication was attempted.

Local package: `build/DIT-Admin-Center-Preview-325142a5/`.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546775 | `325142a5944e4c2e27b3dcfbfeeb3c48671b9ff2567d563841a1c929f426023a` | 600 |
| READ-ME-FIRST.txt | 779 | `0cc3c1b6ee72a75178dd3870e6dac4146f125be94a81e203f70bcb1faca89596` | 600 |

**Change:** DIT bot-event area labels must come from a row with the last
observed area ID. Previously, a transition from area A to B without a new
readable name returned B's ID alongside A's name, and the UI preferred that
stale name. The new projection leaves B's label unknown until a matching label
exists. Earlier labels for the same ID remain usable, including prior visits;
unscoped labels cannot relabel a known area. With no supplied area ID, a
standalone label retains an unknown ID. No record counts or game state change.

**Verification:** 12 focused reader tests passed: eight new area-attribution
regressions plus existing writer, label, latest-area and timestamp-ordering
cases. The exact packaged HTML passed 178 simulated-DOM startup assertions,
zero transport attempts (construction 851 ms, completion wait 6,498 ms).
No full suite was run. Native browser/keyboard checks remain NOT RUN.

**Delivery:** blocked by the previously observed Alienware endpoint timeout.
The package is prepared locally, not copied or verified remotely; latest
confirmed delivered preview remains **acfa9efd**. No live game, player save,
level-sync, device or push action occurred.

## Prepared: preview 0b5c6a06 (source ec3a734) — next delivery candidate

Checkpoint **2026-11-10T01:39:04Z**. This candidate supersedes `325142a5` for
the next private delivery and retains preceding pending reader/UI fixes.
Earlier packages and any unknown partial destination remain untouched.
No Alienware retry or publication was attempted.

Local package: `build/DIT-Admin-Center-Preview-0b5c6a06/`.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546976 | `0b5c6a065b3acc02712d8f2ccacff9e75a9dab109503e933ac57146ddf9bb039` | 600 |
| READ-ME-FIRST.txt | 755 | `d1346c70fb178229034ced10ae0b29946a4334fc1410794b1913c0b28bb252d8` | 600 |

**Change:** missing or malformed Vanilla hearthstone-escape counts display
Unknown instead of none. An explicit empty or all-zero count map says
"none recorded". Valid positive counts retain their supplied labels; mixed
valid/invalid counts remain Unknown. No source records or game state changed.

**Focused checks:** `node tests/bot_activity.test.js` passed, covering actual
rendered rows for missing/malformed counts, empty/zero maps, positive labels,
mixed counts and recovery, with no extra requests.

**Startup evidence:** the first exact-artifact run hit the unchanged ten-second
deadline after 156 passing assertions (construction 1,006 ms, completion wait
10,460 ms); it recorded no runtime errors or transport attempts. Its receipt
is retained in `build/escape-coverage-startup-smoke-first-timeout.log`.
A resource snapshot showed CPU contention (CPU PSI some avg10 45.18%) with
about 132 GiB available memory; this does not establish the timeout's cause.
One bounded retry of the same artifact passed all 178 assertions, zero transport
attempts (construction 762 ms, completion wait 9,352 ms), recorded in
`build/escape-coverage-startup-smoke.log`. No deadline/assertion was relaxed,
and no full suite or native browser/keyboard check was run.

**Limits:** a single read-only FFXI handoff-directory check found export 7 still
the latest log export; no new post-H1 export was integrated. Private delivery
remains blocked by the previously observed Alienware endpoint timeout.
This package is local only; latest confirmed delivered preview is **acfa9efd**.

## Delivered: preview 0b5c6a06 — endpoint recovered

Independent remote readback at **2026-11-10T01:53:23Z** verified the new private
folder **Alienware → Downloads → DIT-Admin-Center-Preview-0b5c6a06**.
The initial read-only check found that exact destination absent; transfer used
exclusive directory/file creation. Both files then matched on a separate SSH
readback, with mode 600. No earlier destination was modified.

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 546976 | `0b5c6a065b3acc02712d8f2ccacff9e75a9dab109503e933ac57146ddf9bb039` | 600 |
| READ-ME-FIRST.txt | 819 | `2bfd9389a7ea1834590f3f0ac8e804ca98607ca7b8a7d64d19f382fb9a2f3933` | 600 |

The delivered HTML is byte-identical to the already checked artifact above;
no redundant build or test run was performed. The delivery README removes the
preparation-only status and points to the preserved `acfa9efd` rollback. This
pair is retained in `build/DIT-Admin-Center-Preview-0b5c6a06-delivery/`; the
original prepared package and its recorded hashes remain unchanged.

The connection timeout is resolved for this verified delivery. Native browser
and keyboard checks remain NOT RUN. This is an offline private preview, not a
hub/game deployment; no save, player state, live service or access setting was
changed.

## Delivered: preview adfa9a73 (source 9a7fe6b)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-adfa9a73**.
Independent remote readback at **2026-11-10T01:54:34Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 547004 | `adfa9a73d434cf767fb31322dc89952c88f099b4cf74885132d366838bf923c0` | 600 |
| READ-ME-FIRST.txt | 811 | `8fabe58c93bb1604879c08b411860b686811c890c6b146222afbbae8c6d2b55f` | 600 |

Local package: `build/DIT-Admin-Center-Preview-adfa9a73/`.

**Change:** review findings require the same usable bot identity as detail
rows. Missing, null, blank, whitespace and numeric IDs no longer produce
repeated-pull, cadence, departure or synchrony findings while the corresponding
bot detail row is omitted. Valid findings and source recovery remain usable.
Includes the preceding pending reader/UI fixes delivered in `0b5c6a06`.

**Verification:** `node tests/bot_activity.test.js` passed with malformed and
valid identity cases across FFXI, DIT and Vanilla, all four finding types,
source recovery and no extra requests. The exact delivered HTML passed all
178 simulated-DOM startup assertions, zero transport attempts (construction
657 ms, completion wait 5,666 ms). No full suite was run; native browser and
keyboard checks remain NOT RUN.

**Delivery and rollback:** a read-only check found the exact destination absent;
the copy used exclusive directory/file creation and a separate readback checked
hashes, sizes and mode 600. `0b5c6a06` and earlier previews remain available.
No live hub/game deployment, save or player-state change, service operation,
browser launch, credential/access change or public release occurred.

## Delivered: preview 7bc2948e (source 5fb6b7e)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-7bc2948e**.
Independent remote readback at **2026-11-10T02:16:07Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 569729 | `7bc2948e1e99a976b46ac2e0c604cdfc74b678028e690e6311b903f1080cadcb` | 600 |
| READ-ME-FIRST.txt | 995 | `0afb27db9b5d03eeec4e3de017616ad7f99a98f0b22c48cd8f616dc3ec7ea9e2` | 600 |

Local package: `build/DIT-Admin-Center-Preview-7bc2948e/`.

**Change:** the preview's **Bot activity sample** selector switches to
**Synthetic FFXI + SWTOR readiness** after the automatic checks. The two feeds
use the normal readers and activity rendering, with explicit synthetic source
labels, notes and coverage. Switching back restores the original captured
exports/schema examples. Neither mode changes the parity tracker or its evidence.

The new fictional FFXI input has 52 accepted lines, two bots and 28 projected
events each, exercising travel/mounts and all three timing measurements. SHA-256:
`0f723e58925f4ca6dfc3c3141f6208486b0dfc6f1f2902b5b7c6b37607426114`.
It uses existing accepted log shapes; it is not export 8 or an H1 capture.
SWTOR reuses the unchanged 16-row kf writer sample with synthetic actors/times
(SHA-256 `4755733618ce570cb7aa1a4b91496751c0d34ad78d8420bd57ff7d848150cfd0`).
Real exports remain necessary for live conclusions; no parity cell was promoted.

**Verification:** four focused fixture checks passed, including row/event
coverage, constructed timing, sparse SWTOR cadence and producer drops versus
reader omissions. Four focused builder checks passed for sample separation,
source fingerprints, inline asset/CSP binding, JavaScript compilation and
escaping. The exact delivered artifact passed all 182 simulated-DOM startup
assertions, zero transport attempts (construction 951 ms, completion wait
8,801 ms), including selector rendering, sample features, unchanged parity and
restoration without requests. Native browser/keyboard checks remain NOT RUN;
no full suite was run.

**Delivery and rollback:** the exact destination was checked absent before
exclusive creation; a separate readback verified hashes, sizes and mode 600.
`adfa9a73` and earlier previews remain available. No live game/hub deployment,
save/player-state change, browser launch, access change or public release.

## Delivered: preview 36a5fdac (source 842bdf9)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-36a5fdac**.
Independent remote readback at **2026-11-10T02:23:08Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 571364 | `36a5fdac28b07dc06ec68c0aff1c4466757656c2bd77135c5712124af1ee4bc8` | 600 |
| READ-ME-FIRST.txt | 940 | `0afa7c379662db585a957561395bbca90f504c7fa3a6ab8b6c89f45c2c4cc9c8` | 600 |

Local package: `build/DIT-Admin-Center-Preview-36a5fdac/`.

**Change:** accepted DIT `error` / `LOG_DROPPED` rows expose a per-report
`reportedDropped` count, limited to nonnegative integers safely represented in
JavaScript. Missing/invalid counts remain Unknown without discarding the report.
Coverage warns about retained report rows even when bot/event display caps hide
them. Counts may overlap and are never summed or added to reader omissions.

In the synthetic readiness view, SWTOR still has 16 imported rows and zero
reader omissions, but coverage now flags its producer-loss report. Expanding
Events for `bot_events` shows the reported 27 dropped rows. This is a synthetic
writer sample, not a live loss measurement or a daily/export-wide total. The
parity tracker and its evidence remain unchanged.

**Focused verification:** seven selected Python tests passed, covering valid,
invalid and unknown counts, overlapping reports, unrelated event isolation,
caps, writer samples and mapped-field/privacy boundaries. The bot-activity UI
regression script passed, including visible counts, Unknown, source recovery and
unchanged reader omissions with no requests.

**Startup evidence:** the first run reached 156 passing assertions before the
unchanged ten-second deadline (construction 973 ms, completion wait 10,130 ms),
with no runtime errors or transport attempts. That receipt is retained in
`build/producer-loss-startup-smoke-first-timeout.log`. One bounded retry of the
same artifact passed all 183 assertions, zero transport attempts (construction
975 ms, completion wait 7,770 ms), including the visible 27-versus-zero
distinction. No assertions/deadlines were relaxed. Native browser/keyboard
checks and the full suite were not run.

**Delivery and rollback:** exact destination checked absent, then created
exclusively; separate readback verified hashes, sizes and mode 600. `7bc2948e`
and earlier previews remain available. No live game/hub deployment, save/player
change, service operation, access change, browser launch or public release.

## Delivered: preview e132f3c9 (source 69e247c)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-e132f3c9**.
Independent remote readback at **2026-11-10T02:33:41Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 571364 | `e132f3c9810a484902e4d05f685b59207c6b7d753af495770097aabc9588942c` | 600 |
| READ-ME-FIRST.txt | 1081 | `2d219952cf0561e6212622a6eeea572ac3fed5329cb32cebfe45eaf3e0e2427d` | 600 |

Local package: `build/DIT-Admin-Center-Preview-e132f3c9/`.

**Change:** 198 fixed-ID document lookups in the app and 13 in the preview driver
now use `getElementById`. This removes repeated selector scans in rendering and
the assertion reporter without caching elements or changing rendering order.
All 103 distinct targeted app IDs occur exactly once in the template. The diff
was checked to contain only these substitutions; compound/dynamic selectors,
all assertions, and the five-second progress/ten-second total deadlines remain
unchanged. This preview supersedes `36a5fdac` for owner playtesting.

**Diagnostic evidence:** a CPU-profile run of the preceding `36a5fdac` artifact
reached 156 passing checks before the ten-second deadline (construction 1,471 ms,
completion wait 10,529 ms; zero runtime errors or transport attempts). The log
and profile remain at `build/readiness-startup-profile.log` and
`build/readiness-startup-20261110.cpuprofile`. Repeated ID selector/tree traversal
work was prominent in that profile. Profiling overhead and shared-host load
mean this is a diagnostic, not a controlled performance comparison.

**Focused verification:** source-race, overview-failure, partial-assignment and
selector UI scripts passed. Two builder checks passed for embedded assets,
unique IDs, source fingerprints, CSP script binding and JavaScript compilation.
The exact delivered HTML passed all 183 simulated-DOM startup assertions on its
first run, zero transport attempts (construction 750 ms, completion wait
2,478 ms), recorded in `build/direct-id-startup-smoke.log`. Native browser and
keyboard checks and the full suite were not run; no native performance claim.

**Delivery and rollback:** exact destination checked absent, then created
exclusively; a separate connection verified hashes, sizes and mode 600.
`36a5fdac` and earlier previews remain available. No live game/hub deployment,
save/player change, service operation, access change or public release occurred.

## Delivered: preview 532ab9a9 (source 4787e05)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-532ab9a9**.
Independent remote readback at **2026-11-10T02:44:16Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 581481 | `532ab9a9a864e2eacfdd8e389431188f7f75012468d541bc22cecbd381953f29` | 600 |
| READ-ME-FIRST.txt | 1213 | `282c80fe152097c3a9411d3288690eae57f7f3fdf40ee84216d79ebb3f2a989f` | 600 |

Local package: `build/DIT-Admin-Center-Preview-532ab9a9/`.

**Change:** **Bot activity sample → Synthetic SWTOR import with a malformed
row** exposes an incomplete import and its recovery. The builder appends one
unfinished JSON row to a disposable copy of the unchanged kf writer fixture,
then uses the normal bot-event reader. It retains all 16 accepted rows and
seven actors, with one `invalid_json` omission. The existing producer-loss
event still reports 27 dropped rows; those counts remain separate, not summed.
Malformed content is never rendered as an event.

Switching to complete readiness clears the reader omission and restores the
exact complete sample. FFXI readiness, WoW and Vanilla inputs, parity evidence
and transport request counts remain unchanged. Both choices are explicitly
synthetic. Real FFXI post-H1 and SWTOR bot-event exports are still required for
live conclusions. This preview supersedes `e132f3c9` for owner playtesting.

**Focused verification:** five fixture checks and three selected builder checks
passed, including valid-event preservation, observation bounds, producer loss
versus reader omissions, original-file integrity, source separation, unique IDs,
embedded asset/CSP binding and JavaScript compilation. The exact delivered HTML
passed all 187 simulated-DOM startup assertions on its first run, zero transport
attempts (construction 899 ms, completion wait 2,914 ms). Four new assertions
cover the partial view, loss distinction, unaffected sources and recovery.
Receipt: `build/partial-readiness-startup-smoke.log`. Native browser/keyboard
checks and the full suite were not run; no live behavior or native UI claim.

**Delivery and rollback:** exact destination checked absent, then created
exclusively; a separate connection verified hashes, sizes and mode 600.
`e132f3c9` and earlier previews remain available. No live game/hub deployment,
save/player change, service operation, access change or public release occurred.

## Delivered: preview 80f9a6a7 (source 4e7875f)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-80f9a6a7**.
Independent remote readback at **2026-11-10T02:58:27Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 596979 | `80f9a6a759a535028fa2b29f3ddc8bf9da8236c536882b46ff4bdfb981f62845` | 600 |
| READ-ME-FIRST.txt | 1267 | `00b0e3ca7986225f08edfe2762349ee548b4d1d875665a554d7fafda17d0d936` | 600 |

Local package: `build/DIT-Admin-Center-Preview-80f9a6a7/`.

**Change:** **Bot activity sample → Synthetic FFXI import with skipped lines**
shows three different line exclusions. A disposable copy of the unchanged
fictional 52-line FFXI sample receives one malformed `act` line, one unknown
bot-event shape and one unrelated line. The normal reader returns 52 accepted,
one omitted malformed, one unrecognized and one ignored line. The two bots,
their events, timing measurements and accepted event bounds remain unchanged;
the later rejected timestamps do not extend the accepted range.

Returning to complete readiness clears all three counts and restores the exact
source data. SWTOR, WoW, Vanilla and parity evidence stay unchanged from complete
readiness, with no requests. The earlier incomplete SWTOR option remains usable.
These are synthetic cases; real FFXI post-H1 and SWTOR exports remain necessary
for live conclusions. This preview supersedes `532ab9a9` for owner playtesting.

**Focused verification:** six fixture checks and three selected builder checks
passed. They cover exact exclusion categories, accepted-event preservation,
observation bounds, fixture integrity, source separation, unique IDs, embedded
asset/CSP binding and JavaScript compilation. Both original fixture SHA-256s
remain unchanged. The exact delivered HTML passed all 191 simulated-DOM startup
assertions on its first run, zero transport attempts (construction 632 ms,
completion wait 1,505 ms). Four new assertions cover the partial FFXI view,
retained data, unaffected sources and recovery. Receipt:
`build/partial-ffxi-readiness-startup-smoke.log`. Native browser/keyboard checks
and the full suite were not run; no live behavior or native UI claim.

**Delivery and rollback:** exact destination checked absent, then created
exclusively; a separate connection verified hashes, sizes and mode 600.
`532ab9a9` and earlier previews remain available. No live game/hub deployment,
save/player change, service operation, access change or public release occurred.

## Delivered: preview c3283185 (source 0f85db3)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-c3283185**.
Independent remote readback at **2026-11-10T03:12:21Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 597088 | `c32831850dc9dcfdc440117579e495caba9e2dabe90d29f7cf360ce37eabf3d4` | 600 |
| READ-ME-FIRST.txt | 1126 | `8182bcffa74cf205fa7a45dcc5454b9a6836c249cc20c98bd41c942432999191` | 600 |

Local package: `build/DIT-Admin-Center-Preview-c3283185/`.

**Change:** activity coverage now labels its total **Rows omitted on import**.
The previous **Omitted malformed** label incorrectly described DIT rows skipped
at the import row limit, non-event rows, and WoW Forever duplicate event IDs as
malformed input. Counts, source reasons and reader behavior are unchanged.
Refused files remain in their separate notice; their unread row counts are not
inferred. Producer-reported loss and FFXI unrecognized/ignored lines stay
separate. Both incomplete readiness examples remain usable and synthetic.
This preview supersedes `80f9a6a7` for owner playtesting.

**Focused verification:** five selected reader/builder checks passed for the
DIT row cap, byte-budget file exclusions, Forever duplicate-ID handling,
embedded assets/unique IDs/CSP script binding and JavaScript compilation. The
existing bot-activity UI script passed with the corrected labels. The exact
delivered HTML passed all 191 simulated-DOM startup assertions on its first run,
zero transport attempts (construction 998 ms, completion wait 2,668 ms).
Receipt: `build/import-omission-label-startup-smoke.log`. Native browser/keyboard
checks and the full suite were not run.

**Delivery and rollback:** exact destination checked absent, then created
exclusively; a separate connection verified hashes, sizes and mode 600.
`80f9a6a7` and earlier previews remain available. Real FFXI post-H1 and SWTOR
exports are still required for live conclusions. No live game/hub deployment,
save/player change, service operation, access change or public release occurred.

## Reader fix after c3283185: oversized bot-event file (no new preview)

`bot_event_v1.py` now skips a file larger than the per-file limit (8 MiB) as
**oversized** whatever total budget is left. Before, when less than 8 MiB of the
32 MiB total budget remained, such a file was reported as **over the total byte
limit** and ended the read, so older files that would have fit were left unread.
A file that fits the per-file limit but not the remaining total still ends the
read, as before.

**Verification:** the new test failed before the change (1 file, 1 row) and
passes after (2 files, 2 rows, `1 oversized`). Full suite run: 634 Python tests
and every `tests/*.test.js` script passed. The simulated-DOM startup run on
current source passed all 191 assertions with zero transport attempts.

**Preview:** not rebuilt for delivery. Current source builds to
`c4c0b6d9…901eba`, which differs from delivered `c3283185` in one line, the
embedded `bot_event_v1.py` source fingerprint; nothing the owner sees changes.
`c3283185` stays the current delivered preview. Native browser/keyboard checks
were not run. No real FFXI post-H1 or SWTOR export has arrived (one read-only
check of the FFXI handoff directory: export 7 is still the latest).

## Delivered: preview 9462bda2 (source 6dbb8f5)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-9462bda2**.
Separate-connection readback at **2026-11-10T03:57:16Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 597293 | `9462bda2c97bd5316ece9ffc540a4039937cb34b990c1a5157794e85fb508597` | 600 |
| READ-ME-FIRST.txt | 1245 | `7e69d2cecea7c53e9a418e246d8038cf4a86f3f7127df8f6d233c93f39b143a3` | 600 |

Local package: `build/DIT-Admin-Center-Preview-9462bda2/`.

**Change:** in Baseline bot style conformance, the FFXI Forever (Rust) cells
**Owner orders** (p-08) and **Getting bots by class and role** (p-07) now cite
the `/fb` owner menu packet (help, list, summon, dismiss, build-2 orders) at hub
design branch `design/ffxi-fb-menu-r1-20261110`, commit `77bfd593`. Its own
README says PREPARATION ONLY: Rust contracts, no native routing, not live. Both
statuses stay **Built** for the existing driver work; `/fb` is not presented as
wired or working. That packet's tests were not run in this lane. The preview
also carries the oversized-file reader fix `70aa366` (no visible change).
This preview supersedes `c3283185` for owner playtesting.

**Focused verification:** conformance (15), offline overview and bot-activity UI
checks passed after the change; the full suite (634 Python tests and all
`tests/*.test.js`) passed at `70aa366`, before the fixture text change. The
exact delivered HTML passed all 191 simulated-DOM startup assertions, zero
transport attempts (construction 649 ms, completion wait 1,947 ms). Receipt:
`build/fb-prep-evidence-startup-smoke.log`. Native browser/keyboard checks were
not run.

**Delivery and rollback:** destination checked absent, then created with
exclusive file creation; a separate connection verified hashes, sizes and mode
600 (`build/fb-prep-evidence-delivery-readback.txt`). `c3283185` and earlier
previews remain. Real FFXI post-H1 and SWTOR exports are still required for
live conclusions. No live game/hub deployment, save/player change, service
operation, access change or public release occurred.

## Delivered: preview 60d3d2e0 (source 41c448a)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-60d3d2e0**.
Separate-connection readback at **2026-11-10T04:17:48Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 597430 | `60d3d2e0dec208e7613e50320847a0b10b80266d1332be6f40d8a8d8988f5564` | 600 |
| READ-ME-FIRST.txt | 1219 | `31b6ca39ebb4510693e37e19872649ccffe4cb210db5947802030b7dca1f4cbc` | 600 |

Local package: `build/DIT-Admin-Center-Preview-60d3d2e0/`.

**Change:** FFXI Forever (Rust) conformance cells p-01, p-02 and p-07 were
stale ("driver not started", "not yet run on a live map", "not yet in game").
They now cite FFXI handoff `2026-11-10-rc7-live-6579934f` (README and
`RESULT.json`, read once, read-only): v3.77-rc7 live 2026-11-10 03:05:07Z, map
`1458b2d`, five bot logins online 03:05:47Z, cross-zone POP on, zone-115 pin
removed, owner offline, `bots_next_to_owner_confirmed: false`. Statuses stay
**Built**: owner party membership, proximity and cross-zone follow are not
confirmed live. This lane copied those facts and did not test the game.
The tracker's `asOf` stays 2026-11-09; only these cells and the two `/fb`
notes were revisited. This preview supersedes `9462bda2`.

**Verification:** full suite at `41c448a`: 634 Python tests and every
`tests/*.test.js` script passed. The exact delivered HTML passed all 191
simulated-DOM startup assertions, zero transport attempts (construction 963 ms,
completion wait 2,820 ms); receipt `build/rc7-evidence-startup-smoke.log`.
Native browser/keyboard checks were not run.

**Delivery and rollback:** destination checked absent, then created with
exclusive file creation; readback in `build/rc7-evidence-delivery-readback.txt`.
`9462bda2` and earlier previews remain. Real FFXI post-H1 and SWTOR exports are
still required for live conclusions. No live game/hub deployment, save/player
change, service operation, access change or public release occurred.

## Delivered: preview c56ee498 (source 9a153bf)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-c56ee498**.
Separate-connection readback at **2026-11-10T04:30:44Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 597512 | `c56ee4987fcfa48d20d8026521b6aba13201079a8a5fdb83d9c3792b7df9e2b7` | 600 |
| READ-ME-FIRST.txt | 1166 | `fdbf3ef7969f81cafe7eb4539b30b1a4ae510347b685dab24001a8f56490dec9` | 600 |

Local package: `build/DIT-Admin-Center-Preview-c56ee498/`.

**Change:** SWTOR conformance cell p-04 now notes that release kt (c56, live
2026-11-10T04:19:57Z, 0 players at launch) adds per-role reaction delays and
press jitter for invited squads. Sources, read once and read-only in the SWTOR
lane's release folder: `release-kt-c56/VERIFICATION.txt` (live time),
`release-kj-c46/VERIFICATION.txt` (what the change is; timing values are design
estimates) and `ORDER-c56.txt` (the `bot-human-r2` squad-timing patch is in the
live composition). Status stays **Built**: no live squad log line has been
seen. Other SWTOR cells still cite kc/kf, the releases where their behavior
went live; they were not reassessed. This preview supersedes `60d3d2e0`.

**Verification:** full suite at `9a153bf`: 634 Python tests and every
`tests/*.test.js` script passed. The exact delivered HTML passed all 191
simulated-DOM startup assertions, zero transport attempts (construction 824 ms,
completion wait 2,475 ms); receipt `build/swtor-kt-evidence-startup-smoke.log`.
Native browser/keyboard checks were not run; the game was not tested here.

**Delivery and rollback:** destination checked absent, then created with
exclusive file creation; readback in
`build/swtor-kt-evidence-delivery-readback.txt`. `60d3d2e0` and earlier
previews remain. Real FFXI post-H1 and SWTOR exports are still required for
live conclusions. No live game/hub deployment, save/player change, service
operation, access change or public release occurred.

## Delivered: preview bd47f803 (source d3be7b1)

Private folder **Alienware → Downloads → DIT-Admin-Center-Preview-bd47f803**.
Separate-connection readback at **2026-11-10T06:33:49Z** matched both files:

| File | Bytes | SHA-256 | Mode |
| --- | ---: | --- | --- |
| Admin-Center-Synthetic-Preview.html | 597517 | `bd47f803186a025d36fa698e406220f776315b796c8b7a714f9e7bcfd55a0a75` | 600 |
| READ-ME-FIRST.txt | 1376 | `5465935b803036966ca7cf13ea89020e0f99d5fad59fe74499529af2d2e050b9` | 600 |

Local package: `build/DIT-Admin-Center-Preview-bd47f803/`.

**Change:** FFXI Forever (Rust) cells p-01, p-02, p-07 and p-08, from FFXI
handoffs read once and read-only:

- `2026-11-10-rc8-live-09bf10c2` (README, `RESULT.json`): v3.77-rc8 live
  2026-11-10T04:22:29Z, map `fe15066`, cross-zone on, owner offline, no human
  gameplay smoke. It gives no bot login count, so the "5 bot logins online"
  fact stays attributed to rc7.
- `2026-11-10-forever-fb-native-r11-4a79acef` and
  `2026-11-10-forever-fb-orders-r12-054ebebd` (READMEs): `/fb` help, list,
  summon, dismiss (r11) plus follow, stay (r12) exist as native source packets;
  not a runtime kit, not live, and a matching DIT control adapter is required
  before a runtime release. This replaces the earlier "preparation only" note.

All four statuses stay **Built**. Those packets' build and checks are cited
from their READMEs and were not run here. This preview supersedes `c56ee498`.

**Verification:** full suite at `d3be7b1`: 634 Python tests and every
`tests/*.test.js` script passed. The exact delivered HTML passed all 191
simulated-DOM startup assertions, zero transport attempts (construction 726 ms,
completion wait 2,101 ms); receipt `build/rc8-fb-source-startup-smoke.log`.
Native browser/keyboard checks were not run; the game was not tested here.

**Delivery and rollback:** destination checked absent, then created with
exclusive file creation; readback in
`build/rc8-fb-source-delivery-readback.txt`. `c56ee498` and earlier previews
remain. Real FFXI post-H1 and SWTOR exports are still required for live
conclusions (one check at 06:30Z: export 7 still the latest FFXI log export;
the SWTOR export search timed out at 60 s without a result). No live game/hub
deployment, save/player change, service operation, access change or public
release occurred.

## Prepared: preview 939cc496 (source 6584f1b) — not delivered

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Admin-Center-Synthetic-Preview.html | 597620 | `939cc496d5f1cbc79d144ba45ce46fa54ec3c1578aad93a8c57064f18853cd44` |
| READ-ME-FIRST.txt | 1166 | `364e9ceabecd5f3a4c48eee7141ae46317b88846fc5a92b5711629e93c58cfd1` |

Local package: `build/DIT-Admin-Center-Preview-939cc496/`.

**Change:** FFXI Forever (Rust) cells p-08 and p-04 cite the FFXI lane's native
`/fb` source packets through r33 (`074c3640`; READMEs of r13, r14, r25, r29,
r30 and r33 read once, read-only): help, list, summon, dismiss, follow
(cross-zone), stay, attack, assist, pull, rest, role, gear show/scale/bis.
Every packet says source only, no runtime kit or live behavior; the live build
is still v3.77-rc8. Both statuses stay **Built**. Those packets' builds and
checks were not run here.

**Verification:** full suite at `6584f1b`: 634 Python tests and every
`tests/*.test.js` script passed. The exact HTML passed all 191 simulated-DOM
startup assertions, zero transport attempts (construction 592 ms, completion
wait 1,810 ms); receipt `build/fb-r33-startup-smoke.log`. Native
browser/keyboard checks were not run.

**Not delivered:** `ssh alienware-bazzite` returned `Connection timed out` at
about 08:25Z (for the intermediate r25 build `21855c33`, also undelivered and
superseded by this one) and again at 09:30Z. Nothing was written to Alienware.
The latest delivered preview is still **bd47f803**. No real FFXI post-H1 or
SWTOR bot-event export has arrived.
