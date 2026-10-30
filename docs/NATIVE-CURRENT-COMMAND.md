# Current local preview verification command

Source checkpoint: `587bca5` (panel 9 document-fed issues and panel 4 loaded-call
comparison). Local artifact: `build/inspector-playtest.html`, **210403 bytes**.
SHA-256: `1103de1e028e381fc32643391e803889b6cbcfcc7d4e6f4da787e6b7c21412c6`.

From this checkout, on an authorized host with installed executables selected
through `DIT_CHROMIUM` / `DIT_NODE`:

```sh
python3 tools/run_headless_playtest.py --expected-artifact-sha256 1103de1e028e381fc32643391e803889b6cbcfcc7d4e6f4da787e6b7c21412c6
python3 tools/run_keyboard_playtest.py --routing-audit --gap-export --expected-artifact-sha256 1103de1e028e381fc32643391e803889b6cbcfcc7d4e6f4da787e6b7c21412c6
```

These commands were **NOT RUN**. Devbox browser/isolation limitations remain as
recorded in NATIVE-VERIFICATION-GAP.md. There is no permission here to retry a
denied namespace operation, install a runtime, substitute a device bundle or
contact Alienware. Existing approved `8eb2c9f` handoff and delivered previews are
unchanged. Automatic DOM execution, native keys/downloads and human visual
review are separate evidence; component tests do not establish any of them.

Observed checks: authenticated temporary localhost mock requests with live
collectors forbidden; document inventory validation/fallback tests; actual-app
simulated-DOM issue filters and model comparison checks, also against this
artifact; generated markup/CSP and JavaScript compilation checks. All passed.
No live service, provider, account, game or device was accessed. The loopback
mock test server was shut down after its requests.
