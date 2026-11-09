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
