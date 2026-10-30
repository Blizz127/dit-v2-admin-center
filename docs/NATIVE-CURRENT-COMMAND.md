# Current local preview verification command

Source checkpoint: `b3ab8f0` (adds scoped current/proposed draft review). Local artifact: `build/inspector-playtest.html`, **220324 bytes**.
SHA-256: `96d4b70e3450cb17864b207e54017236b07427ccc7e4146681e7322ade93e7f1`.

From this checkout, on an authorized host with installed executables selected
through `DIT_CHROMIUM` / `DIT_NODE`:

```sh
python3 tools/run_headless_playtest.py --expected-artifact-sha256 96d4b70e3450cb17864b207e54017236b07427ccc7e4146681e7322ade93e7f1
python3 tools/run_keyboard_playtest.py --routing-audit --gap-export --expected-artifact-sha256 96d4b70e3450cb17864b207e54017236b07427ccc7e4146681e7322ade93e7f1
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

The current artifact also contains automatic draft-review assertions for changed,
matching and Unknown baselines. Component checks against these exact bytes pass,
including same-ID refresh replacing the old baseline/provenance. The narrow
column rule was checked in source; visual appearance remains NOT RUN. These
checks do not certify native typing, review-column geometry or screen readers.
