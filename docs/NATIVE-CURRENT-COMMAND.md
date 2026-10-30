# Current local preview verification command

Source checkpoint: `2c7bec4` (adds panel 2 local goal/personality draft previews). Local artifact: `build/inspector-playtest.html`, **216385 bytes**.
SHA-256: `3739d331bd9a8c0caec799f08792bf4a07803128108b652865d7d4262f2405f8`.

From this checkout, on an authorized host with installed executables selected
through `DIT_CHROMIUM` / `DIT_NODE`:

```sh
python3 tools/run_headless_playtest.py --expected-artifact-sha256 3739d331bd9a8c0caec799f08792bf4a07803128108b652865d7d4262f2405f8
python3 tools/run_keyboard_playtest.py --routing-audit --gap-export --expected-artifact-sha256 3739d331bd9a8c0caec799f08792bf4a07803128108b652865d7d4262f2405f8
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

Draft validation, ID isolation and pending/failed-refresh clearing passed in the
actual-app simulated DOM against this artifact. Localhost mock checks confirm
the new form is served and a draft-like POST is still refused with 405. The
standalone script includes automatic draft preview/validation/discard assertions.
The native-key runner currently covers sidebar, assignment and optional audit
keys; it does not yet certify typing/focus behavior in the draft form.
