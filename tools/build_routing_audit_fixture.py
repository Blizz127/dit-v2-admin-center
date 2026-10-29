"""Generate fictional read-only examples from the isolated in-memory simulator.

No import by the server; the server reads only the committed JSON. Times below
are deliberately fictional, not a record of when this generator ran.
"""
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mock_routing import BotKey, MockRouting


def examples():
    a = BotKey('ffxi', 'fixture-realm', 'fixture-a', 'conversation')
    b = BotKey('ffxi', 'fixture-realm', 'fixture-b', 'conversation')
    simulation = MockRouting([a, b], ['fixture-model-one', 'fixture-model-two'])
    simulation.apply([a], 'fixture-model-one', 0, 'fixture-owner', 'Per-bot illustration')
    simulation.apply([a, b], 'fixture-model-two', 1, 'fixture-owner', 'Fixed all-bots illustration')
    rows = []
    for index, event in enumerate(simulation.snapshot()['audit']):
        rows.append(dict(id=f'fixture-routing-{index+1}', scopeKind='bot' if index == 0 else 'all',
                         actor=event['actor'], reason=event['reason'],
                         at=f'2026-01-01T12:0{index}:00Z',
                         expectedVersion=event['version']-1,
                         attemptedModel=event['changes'][0][2],
                         beforeVersion=event['version']-1, afterVersion=event['version'],
                         result='Simulated application',
                         source='Generated in-memory fixture; not an actual admin audit',
                         changes=[dict(scope=asdict(key), beforeRequested=before,
                                       afterRequested=after, effective=None)
                                  for key, before, after in event['changes']]))
    before = simulation.snapshot()
    try:
        simulation.apply([a], 'fixture-model-one', 1, 'fixture-owner', 'Stale version illustration')
    except ValueError:
        pass
    else:
        raise AssertionError('Expected stale fixture request to be rejected')
    if simulation.snapshot() != before:
        raise AssertionError('Rejected fixture request changed state')
    rows.append(dict(id='fixture-routing-rejected', scopeKind='bot', actor='fixture-owner',
                     reason='Stale version illustration', at='2026-01-01T12:02:00Z',
                     expectedVersion=1, beforeVersion=2, afterVersion=2,
                     attemptedModel='fixture-model-one', result='Simulated rejection: stale version',
                     source='Generated rejected-attempt illustration; simulator emits no audit entry for refusals',
                     changes=[dict(scope=asdict(a), beforeRequested=before['policies'][a],
                                   afterRequested=before['policies'][a], effective=None)]))
    return rows


if __name__ == '__main__':
    path = ROOT / 'data/fixtures/routing-audit.json'
    path.write_text(json.dumps(examples(), indent=2) + '\n')
    print(f'Wrote {path}; synthetic examples only, no routing controls connected.')
