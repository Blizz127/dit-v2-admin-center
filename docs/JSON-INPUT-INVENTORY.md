# JSON input inventory — November 4 offline review

This inventory describes the Admin Center checkout. It does not cover the
separately owned hub, authenticate producers, or establish native-browser results.
Limits are per input; a rejected or incomplete input is not proof of an empty or
healthy source.

| Readers | Input and handling |
| --- | --- |
| `local_evidence.py`; `server.py` capacity/watcher; `lead_timeline.py`; `quota_history.py` | Bounded regular-file JSON reads; invalid, ambiguous, oversized or deeply nested snapshots return Unknown/unavailable. Quota history is a separate read-only SQLite projection. |
| `lead_binding.py`; `session_markers.py` handoff/session metadata | Bounded local JSON; bad or ambiguous identity remains unverified. |
| `session_markers.py`; `resume_signal.py` | Bounded JSONL tail; incomplete or invalid complete lines make coverage unavailable, not a claim that no event exists. The initial fragment of a truncated tail is discarded. |
| `presence_examples.py`; `routing_audit.py`; `server.py` model-call fixture | Bounded committed synthetic JSON; unavailable examples remain Unknown. A bad model-call fixture withholds the combined model-call list. |
| `project_issues.py`; `wake_verification.py`; `evaluator_snapshot.py`; `bakeoff_run.py`; `hub_snapshot.py` | Existing bounded local inputs and type/shape checks; malformed input produces the reader's documented Unknown, unavailable, or counted-omission state. |
| `live_hub.py`; `bridge_status.py` | Existing bounded external-response parsers and unavailable fallbacks. This review made no live call. |
| `mock_routing_api.py` | Bounded synthetic in-process request body, invalid JSON refused; not a registered HTTP write route. |
| `static/app.js` | Five API response readers share a 16 MiB streamed-byte bound, object-root check and depth limit. Errors follow each panel's unavailable or refresh-failure path. Native browser execution remains unverified. |
| `tools/check_learning_assessment_schema.py`; `tools/check_wake_verification_schema.py`; `tools/check_offline_contracts.py` | Bounded synthetic schema, fixture and checker-report inputs; invalid checks fail rather than pass. |
| `tools/build_inspector_playtest.py`; `tools/review_party_greeting.py` | Bounded synthetic fixture or explicitly supplied review metadata; bad build inputs fail without writing an artifact, and the metadata CLI returns unavailable. |
| `tools/review_native_attempt.py`; `tools/run_keyboard_playtest.py` | Previously bounded receipt parsers; invalid receipts do not establish a pass. No device or browser was run in this review. |
| `tools/keyboard_cdp.cjs`; `tools/verify_gap_export.cjs`; `tools/readiness_snapshot.cjs`; `tools/inspector_playtest.js` | Bounded browser-pipe/report inputs or JSON produced by the offline synthetic harness; failures do not establish native success. These tools were inventoried, not executed against a native browser. |

Focused checks include `tests/test_runtime_json_inputs.py`, the existing reader
and receipt suites, schema-validator checks and simulated-DOM tests. The
JSONL and browser tests do not prove behavior for every concurrent writer or
native-browser implementation. Leaf symlinks and non-regular files are refused
by the bounded local-file helper.
