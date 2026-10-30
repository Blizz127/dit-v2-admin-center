# Offline native-attempt receipt intake

`tools/review_native_attempt.py` checks consistency of the returned evidence for
one separately sequenced bazzite attempt: coordinator `ece1ccc9149873b9`, device
lead `852bb105-8f9d-4a3f-a986-89a7981756dc`, original source `8eb2c9f` and artifact
`ef740241`. It does not connect to the device, execute the supplied package,
launch a browser, collect accounts, change state or authenticate the executor.
Use it only after obtaining the evidence through the existing trusted handoff.
A forged set of internally consistent reports cannot be detected by this tool.

## Local input directory

Preserve the original returned evidence. In a separate local review directory,
copy these files from that single attempt, without combining different runs:

- `SHA256SUMS` from the unchanged extracted package.
- `pre-sums.txt`, `build-sums.txt`, `post-sums.txt` from the three manifest checks.
- `artifact-sha256.txt`, `native-exit.txt`, `post-manifest-exit.txt`.
- `started-at.txt`, `finished-at.txt` (UTC/timezone-qualified timestamps).
- `native-result.json` (raw stdout, including an empty file for a blocked run)
  and `native-stderr.txt` (raw stderr).

Also create `attempt.json` locally from the trusted returned identity and version
reports. This is reviewer metadata, not a new executor protocol or reason to
repeat the device run. Required fixed values:

```json
{
  "schema": "dit-admin-native-attempt-v1",
  "sequence": "ece1ccc9149873b9",
  "executor": "852bb105-8f9d-4a3f-a986-89a7981756dc",
  "host": "bazzite",
  "sourceRevision": "8eb2c9f51dfbf0302b0a924b8075f039fed1b6ee",
  "bundleSha256": "a0bc47b1530d54ebb29b300e913f00a3ab6db434fca2007f0acabbafa1192ca7",
  "artifactSha256": "ef740241746a1d9609b0c1fe41855d46931f2d01e99ceb493d335eb0678e77c2",
  "startedAt": "COPY ACTUAL RETURNED TIMESTAMP",
  "finishedAt": "COPY ACTUAL RETURNED TIMESTAMP",
  "versions": {
    "browser": "COPY ACTUAL RETURNED VERSION",
    "node": "COPY ACTUAL RETURNED VERSION",
    "python": "COPY ACTUAL RETURNED VERSION",
    "unshare": "COPY ACTUAL RETURNED VERSION"
  }
}
```

The placeholders are not a usable receipt. Do not turn expected versions into
observed versions, invent timestamps or synthesize missing successful manifest
output. Missing evidence means incomplete. Compare the reported archive hash to
the trusted handoff before preparing metadata; the verifier checks the supplied
value against the pin but does not reread an archive or contact the executor.
Versions are required for a success claim; a runtime-blocked attempt may omit
versions of executables that could not run.

## Review command and outcomes

```sh
python3 tools/review_native_attempt.py /path/to/local/returned-attempt
```

The tool emits one redacted JSON summary, with the pinned source/artifact and an
explicit supplied-evidence limitation. It does not store or publish the summary.

| Status | CLI exit | Meaning |
| --- | --- | --- |
| `reported-pass` | 0 | Identity, manifest reports, exit 0 and required legacy keyboard/download fields agree; not independent device observation |
| `blocked` | 2 | Matching attempt reports exit 2, empty stdout and one of the pin's exact runtime/isolation blockers |
| `failed` | 1 | Matching attempt reports a nonzero exit other than the recognized blocked case; timeout/partial success is not a pass |
| `incomplete` | 1 | Missing, malformed, contradictory, oversized or mismatched evidence; no success claim |

Both timestamps must match their captured files, be ordered and not future-dated,
and start at or after the new sequencing checkpoint (October 30 at 02:32 UTC).
The original October 29 23:20:30Z blocked attempt cannot be relabeled as this one.
The manifest file must match the pinned SHA-256, and all three check reports must
contain every expected entry exactly once with OK, without extra/failed lines.
The artifact report and post-manifest exit must also match.

Success requires the approved pin's eight-section Tab/Shift+Tab/Enter result,
1280/390 widths, twelve assignment steps, Escape cancellation, automatic DOM and
saved JSON result. It does not require newer fields absent from that pin, such as
shell coverage geometry or stdout artifactSha256. If an artifactSha256 is supplied
in stdout, it must not contradict the pinned identity. No success applies to
newer previews, Blob exports, exact UTF-8 equality, human visual acceptance or
live game behavior. A blocker is not authorization for a retry or installation.

Only fixed filenames are opened, each at most 64 KiB plus an oversize sentinel.
Symlinks and nonregular files are refused; FIFO reads do not block. JSON rejects
duplicate keys, malformed UTF-8 and non-finite/overflowing numeric tokens. Raw
stderr, metadata values, paths and exceptions are not reflected in the summary.
These are local intake safeguards, not remote provenance guarantees.

Six focused synthetic tests passed: legacy success/read-only handling;
blocked/failure/timeout classification; pin/executor/time refusal; manifest and
artifact mismatches; incomplete keyboard/export evidence; strict bounded files,
symlink/FIFO refusal and redacted CLI output. Network/process launch is forbidden
in those tests. No actual second-attempt result has been ingested or claimed.
