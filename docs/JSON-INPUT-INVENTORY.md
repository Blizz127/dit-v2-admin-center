# JSON input inventory — November 4 offline review

This inventory describes the Admin Center checkout. It does not cover the
separately owned hub, authenticate producers, or establish native-browser results.
Limits are per input; a rejected or incomplete input is not proof of an empty or
healthy source.

| Readers | Input and handling |
| --- | --- |
| `context_capture.py`; `tools/build_integrated_context_preview.py` | Optional 256 KiB synthetic context/status capture; validates scope, prompt digest, request binding, field states and captured freshness. Valid unavailable-source packets retain context with unknown status; contradictory values/revisions and malformed packets are refused. Default off; invalid file clears the API capture. Extra file fields are not exported. No live producer access. |
| `delivery_correlation.py`; `tools/correlate_delivery.py`; `tools/build_delivery_correlation_preview.py` | Optional 256 KiB synthetic log bundle, bounded record lists, exact publication/receipt bindings and explicit unknown/conflict states. Disabled operation reads nothing. Invalid files clear records/counts; malformed or unverified receipts are counted without confirming them. The authenticated Admin loader never supplies a native verifier. Default-off file setting; no live-log scanner or writes. |
| `tools/run_candidate_delivery_harness.py` | Default-off playback of four named 256 KiB synthetic candidate exports, with a bounded 4 KiB manifest and exact content pins checked before transport. Invalid scope, prompt receipt, action, file set or digest is refused. Bounded in-memory queues carry generated synthetic packets only; no native/network access or persisted delivery state. |
| `local_evidence.py`; `server.py` capacity/watcher; `lead_timeline.py`; `quota_history.py` | Bounded regular-file JSON reads; invalid, ambiguous, oversized or deeply nested snapshots return Unknown/unavailable. Quota history is a separate read-only SQLite projection. |
| `lead_binding.py`; `session_markers.py` handoff/session metadata | Bounded local JSON; bad or ambiguous identity remains unverified. |
| `session_markers.py`; `resume_signal.py` | Bounded JSONL tail; incomplete or invalid complete lines make coverage unavailable, not a claim that no event exists. The initial fragment of a truncated tail is discarded. |
| `presence_examples.py`; `routing_audit.py`; `server.py` model-call fixture | Bounded committed synthetic JSON; unavailable examples remain Unknown. A bad model-call fixture withholds the combined model-call list. |
| `project_issues.py`; `wake_verification.py`; `evaluator_snapshot.py`; `bakeoff_run.py`; `hub_snapshot.py` | Existing bounded local inputs and type/shape checks; malformed input produces the reader's documented Unknown, unavailable, or counted-omission state. |
| `live_hub.py`; `bridge_status.py` | Existing bounded external-response parsers and unavailable fallbacks. This review made no live call. |
| `mock_routing_api.py` | Bounded synthetic in-process request body, invalid JSON refused; not a registered HTTP write route. |
| `static/app.js` | API response readers share streamed-byte bounds, object-root checks and a depth limit. Context and delivery capture readers use 512 KiB; existing readers use 16 MiB. Delivery counts must agree with its rows and real-delivery/replay claims are refused. Errors follow each panel's unavailable or refresh-failure path. Native browser execution remains unverified. |
| `tools/check_learning_assessment_schema.py`; `tools/check_wake_verification_schema.py`; `tools/check_offline_contracts.py` | Bounded synthetic schema, fixture and checker-report inputs; invalid checks fail rather than pass. |
| `tools/build_inspector_playtest.py`; `tools/review_party_greeting.py` | Bounded synthetic fixture or explicitly supplied review metadata; bad build inputs fail without writing an artifact, and the metadata CLI returns unavailable. |
| `tools/review_native_attempt.py`; `tools/run_keyboard_playtest.py` | Previously bounded receipt parsers; invalid receipts do not establish a pass. No device or browser was run in this review. |
| `tools/keyboard_cdp.cjs`; `tools/verify_gap_export.cjs`; `tools/readiness_snapshot.cjs`; `tools/inspector_playtest.js` | Bounded browser-pipe/report inputs or JSON produced by the offline synthetic harness; failures do not establish native success. These tools were inventoried, not executed against a native browser. |

Focused checks include `tests/test_runtime_json_inputs.py`, the existing reader
and receipt suites, schema-validator checks and simulated-DOM tests. The
JSONL and browser tests do not prove behavior for every concurrent writer or
native-browser implementation. Leaf symlinks and non-regular files are refused
by the bounded local-file helper.

Additional deterministic mutation checks exercise selected truncated prefixes
and wrong root types across snapshot manifests, evaluator and wake imports,
quota and issue inputs, fake hub and bridge responses, mock routing and reported
native receipts. Existing reader tests cover size limits and other malformed
inputs; fake CDP pipes and synthetic saved-report checks cover selected malformed
and oversized responses. The internally generated readiness and preview-driver
JSON paths also have synthetic mutation checks; the latter uses the existing
local jsdom runtime, not a browser. These are bounded examples, not exhaustive
fuzzing. No real hub, native browser or device was used.
