# Exported hub snapshot import

Task `7bc7b81622e0`, November 3. This is the Admin Center side of option (b) in the
live-read hold (see [hub contract draft](HUB-CONTRACT-DRAFT.md)). It does not choose
between the owner's options: it makes either answer a short finish.

- **Option (a), reader token:** the existing live path (`HUB_READONLY_URL` +
  `HUB_TOKEN_FILE`) is used unchanged.
- **Option (b), snapshots:** set `HUB_SNAPSHOT_DIR` to an absolute local directory
  in the layout below. Setting it together with either live variable is refused as
  an invalid configuration.

## What it does

`hub_snapshot.SnapshotReader` has the same read interface as `live_hub.HubReader`,
so snapshots go through the existing size limit, duplicate-key/non-finite JSON
refusal, roster/learning/server-status/health/interaction validation and
projections. It never contacts the hub, reads a token or uses the network.

- Every feed is labeled `Exported snapshot`, never `Live response`. Times read
  `<exportedAtUtc> (exported snapshot, not live; reported hub revision …)`. The
  revision is as reported by the export, not verified.
- The banner says the data is as of its export time and not live, including for a
  partial export where other views use synthetic fallback.
- Row IDs keep the existing hub-identity namespace (`live:<game>:<key>`) so bot and
  learning links work unchanged. The prefix names the hub as the identity source;
  it is not a freshness claim. Feeds, times, sources and the banner carry the
  snapshot label.
- A missing or invalid view file falls back to synthetic data for that game/view
  only. An invalid manifest withholds every view.
- Files are read with the bounded non-blocking, no-symlink reader. FIFOs and
  symlinked leaves are refused.
- Trace lookups are per correlation ID and are not served from snapshots
  (`/api/trace` returns 503).
- The manifest is re-validated on every read, so a replaced export is never shown
  under an earlier label.

## Layout

Each view file is the exact JSON body of the named hub GET (shapes checked against
hub `043bc4b1`). Games without files fall back per view.

| File | Hub GET |
| --- | --- |
| `manifest.json` | — `{"kind": "dit-hub-control-export", "version": 1, "exportedAtUtc": "YYYY-MM-DDTHH:MM:SSZ", "hubRevision": optional}` |
| `<game>/bots.json` | `/v1/control/bots?gameId=<game>` |
| `<game>/learning.json` | `/v1/control/learning?gameId=<game>&light=true&tasksOnly=true` |
| `<game>/server-status.json` | `/v1/control/server-status?gameId=<game>` |
| `health.json` | `/v1/control/health` |
| `interaction.json` | `/v1/control/interaction?limit=50` |

The manifest allows only those four fields. `exportedAtUtc` must be UTC with `Z`
and no more than five minutes in the future. `hubRevision` is a short token.

## Producing an export

**Not done here.** Every `/v1/control/*` GET needs the hub administrator token,
which this lane must not hold. Who exports, how often, and where files are copied
is part of the owner's decision and the hub lead's operation. A tool on the hub
side only needs to save the six response bodies above and write the manifest. The
`server-status` response includes configured source paths, which this app drops.
Hub lead (November 3): the exporter should omit them by default. They are not
secrets, but they are host layout with no use off the hub host.

## Checks

`tests/test_hub_snapshot.py` covers:
- views projecting through the existing validation with snapshot labels;
- per-view fallback for missing SWTOR files;
- invalid manifests (kind, version, boolean version, time format, future time, revision, extra field, missing);
- duplicate roster keys, duplicate JSON keys, FIFO and symlinked files;
- path traversal and relative directories;
- source selection, including the both-configured refusal, with live reads forbidden;
- the health, interaction and trace endpoints.

`tests/source_race.test.js` checks that the banner never says "Hub reads available"
for snapshot feeds and still says "not live" for a partial export. A localhost smoke run against `tests/fixtures/hub-snapshot`
showed the labeled FFXI feeds, SWTOR fallback, health served from the snapshot and
trace 503.
