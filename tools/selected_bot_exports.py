"""Project explicitly selected offline exports; never use environment defaults."""
import hashlib
import json
import os

from bot_event_v1 import read as read_bot_event
from ffxi_botsv2_log import read as read_ffxi
from forever_botlog import load as read_forever
from vanilla_botlog import read as read_vanilla


SOURCES = (
    ('forever_dir', 'wow-70450-export', 'WoW Forever (70450 predecessor)', read_forever),
    ('ffxi_log', 'ffxi-lsb', 'FFXI (LSB) Bots V2', read_ffxi),
    ('bot_events_dir', 'dit-bot-event-v1', 'DIT bot_event v1 (SWTOR, FFXI Forever)', read_bot_event),
    ('vanilla_log', 'wow-vanilla-playerbots', 'WoW Vanilla / Benilla playerbots', read_vanilla),
)


def read_selected_exports(*, ffxi_log=None, bot_events_dir=None, forever_dir=None, vanilla_log=None):
    """Return the four-source projection, or None when no paths were supplied.

    Missing sources stay Off. A supplied but unreadable source refuses the build;
    accepted partial imports keep the readers' exact coverage and omission counts.
    Digests identify projected data, not raw files or producer authenticity.
    """
    inputs = dict(ffxi_log=ffxi_log, bot_events_dir=bot_events_dir,
                  forever_dir=forever_dir, vanilla_log=vanilla_log)
    if all(value is None for value in inputs.values()):
        return None
    sources = []
    for key, source_id, label, reader in SOURCES:
        value = inputs[key]
        option = '--' + key.replace('_', '-')
        if value is None:
            bots, coverage = [], dict(status='Off', records=0, omitted=0,
                                      reason='No export selected for this source; no example substituted.')
            note = 'No export selected. This source is off; it supplies no evidence about live activity.'
            digest = None
        else:
            # abspath does not resolve symlinks: the existing reader still refuses them.
            path = os.path.abspath(os.path.expanduser(os.fspath(value)))
            bots, coverage = reader(path)
            if coverage.get('status') != 'Loaded':
                raise ValueError(f'Selected {option} export unavailable; no artifact written.')
            projected = json.dumps(dict(bots=bots, coverage=coverage), sort_keys=True,
                                   separators=(',', ':'), allow_nan=False).encode()
            digest = hashlib.sha256(projected).hexdigest()
            note = (f'Explicitly selected offline export ({option}); parsed locally, not live. '
                    'Producer identity, completeness and gameplay outcomes are not independently verified. '
                    'No automatic parity-status change.')
        sources.append(dict(id=source_id, label=label + ' · selected exports', note=note,
                            bots=bots, coverage=coverage, projectionSha256=digest))
    return dict(bots=sources[0]['bots'], coverage=sources[0]['coverage'], sources=sources)
