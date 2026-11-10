"""Small offline preview inputs: fictional FFXI timing and unchanged SWTOR writer samples."""
from collections import Counter
import json
from pathlib import Path
import unittest

import bot_event_v1
import ffxi_botsv2_log
from tools.build_inspector_playtest import parity_partial_readiness_source, parity_partial_ffxi_readiness_source


FIXTURES = Path(__file__).resolve().parent / 'fixtures'
FFXI = FIXTURES / 'ffxi-botsv2' / 'synthetic-post-h1-readiness.log'
SWTOR = FIXTURES / 'bot-event-swtor'


class ParityReadinessFixtureTests(unittest.TestCase):
    def test_ffxi_readiness_rows_project_without_loss_or_display_truncation(self):
        self.assertEqual(len(FFXI.read_text().splitlines()), 52)
        bots, coverage = ffxi_botsv2_log.read(FFXI)
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertEqual(tuple(coverage[key] for key in ('records', 'omitted', 'unrecognized', 'ignored', 'budget', 'system')),
                         (52, 0, 0, 0, 0, 0))
        self.assertEqual((coverage['from'], coverage['to']),
                         ('2026-01-01T10:00:00.000Z', '2026-01-01T10:14:57.000Z'))
        self.assertEqual([bot['actorId'] for bot in bots], ['readya', 'readyb'])
        for bot, char_id, last_stamp in zip(bots, [900001, 900002], ['50', '57']):
            with self.subTest(bot=bot['actorId']):
                self.assertEqual((bot['game'], bot['charId'], bot['zoneId']), ('ffxi-lsb', char_id, 241))
                self.assertEqual({key: value for key, value in bot['counts'].items() if value},
                                 {'ok': 11, 'tripStart': 4, 'tripEnd': 4, 'mount': 4, 'other': 1})
                self.assertEqual(Counter(event['type'] for event in bot['events']),
                                 {'owns': 1, 'tripStart': 4, 'mount': 4, 'dismount': 4, 'tripEnd': 4, 'act': 11})
                self.assertEqual(len(bot['events']), 28)
                self.assertEqual((bot['refusals'], bot['deaths']), ([], []))
                self.assertEqual((bot['doing'], bot['lastEventAt']),
                                 ('tripEnd home', f'2026-01-01T10:14:{last_stamp}.000Z'))
                stamps = [event['ts'] for event in bot['events']]
                self.assertEqual(stamps, sorted(stamps, reverse=True))
        # Each of four shared departure lines is attributed to both bots.
        self.assertEqual(sum(len(bot['events']) for bot in bots), coverage['records'] + 4)

    def test_ffxi_constructed_timing_is_measured_not_missing_evidence(self):
        bots, _ = ffxi_botsv2_log.read(FFXI)
        for bot, modal_gap in zip(bots, [2.0, 3.0]):
            with self.subTest(bot=bot['actorId']):
                self.assertEqual(bot['feel']['cadence'],
                                 {'action': 'combat banish', 'gaps': 10, 'modalGapS': modal_gap,
                                  'modalCount': 1, 'modalShare': 0.1, 'metronomic': False})
                self.assertEqual(bot['feel']['sync'],
                                 {'actions': 12, 'together': 0, 'share': 0.0, 'synchronized': False})
                self.assertEqual(bot['feel']['schedule'],
                                 {'intervals': 3, 'modalIntervalS': 180.0, 'modalCount': 1,
                                  'modalShare': 0.333, 'fixed': False})

    def test_swtor_writer_sample_inventory_and_sparse_measurement_stay_distinct(self):
        bots, coverage = bot_event_v1.read(str(SWTOR))
        self.assertEqual((coverage['status'], coverage['files'], coverage['records'], coverage['omitted']),
                         ('Loaded', 1, 16, 0))
        self.assertEqual(coverage['omittedByReason'], {})
        self.assertEqual(coverage['games'], ['swtor'])
        self.assertEqual((coverage['from'], coverage['to']),
                         ('2026-11-09T14:24:08.097Z', '2027-01-16T08:00:00.000Z'))
        self.assertEqual(len(bots), 7)
        projected = [event for bot in bots for event in bot['events']]
        self.assertEqual(Counter(event['type'] for event in projected),
                         {'advice': 1, 'callout': 1, 'chat': 2, 'death': 1, 'decision': 4,
                          'error': 1, 'refused': 5, 'state_change': 1})
        self.assertEqual(len(projected), 16)
        self.assertEqual(sum(sum(bot['counts'].values()) for bot in bots), 16)
        self.assertTrue(all(bot['feel']['cadence'] is None for bot in bots),
                        'the writer shape samples cannot establish regular or varied combat timing')
        raw_rows = [json.loads(line) for line in (SWTOR / 'swtor-kf-writer-samples.jsonl').read_text().splitlines()]
        self.assertEqual([row['details']['dropped'] for row in raw_rows if row['reason'] == 'LOG_DROPPED'], [27])
        self.assertEqual(sum(event['reason'] == 'LOG_DROPPED' for event in projected), 1,
                         'producer-reported drops remain an event, not fabricated reader omissions')

    def test_fixture_provenance_explicitly_disclaims_live_verification(self):
        provenance = (FFXI.parent / 'README.md').read_text().split('# Synthetic post-H1 readiness sample', 1)[1]
        self.assertIn(FFXI.name, provenance)
        self.assertIn('Synthetic fixture, not a live export.', provenance)
        self.assertIn('does not verify H1', provenance)
        self.assertIn('not export 8', provenance)
        self.assertIn('Actor ids and timestamps are synthetic.', (SWTOR / 'README.md').read_text())
        self.assertNotIn('<owner>', FFXI.read_text(), 'this fictional fixture supplies no owner relationship')

    def test_partial_swtor_copy_keeps_valid_events_and_separates_reader_loss(self):
        original = (SWTOR / 'swtor-kf-writer-samples.jsonl').read_bytes()
        clean_bots, clean_coverage = bot_event_v1.read(str(SWTOR))
        partial = parity_partial_readiness_source()
        self.assertEqual(partial['id'], 'dit-bot-event-v1')
        self.assertIn('synthetic incomplete export', partial['label'])
        self.assertIn('Real bot-event export still required.', partial['note'])
        coverage = partial['coverage']
        self.assertEqual((coverage['status'], coverage['records'], coverage['omitted'], coverage['files']),
                         ('Loaded', 16, 1, 1))
        self.assertEqual(coverage['omittedByReason'], {'invalid_json': 1})
        self.assertTrue(coverage['reason'].startswith('Synthetic incomplete readiness sample; not live evidence.'))
        self.assertEqual((coverage['from'], coverage['to']), (clean_coverage['from'], clean_coverage['to']))
        self.assertEqual(partial['bots'], clean_bots)
        self.assertEqual(len(partial['bots']), 7)
        losses = [event for bot in partial['bots'] for event in bot['events'] if event['reason'] == 'LOG_DROPPED']
        self.assertEqual([event['reportedDropped'] for event in losses], [27])
        self.assertNotIn('OMITTED_SYNTHETIC_ROW', json.dumps(partial))
        self.assertEqual((SWTOR / 'swtor-kf-writer-samples.jsonl').read_bytes(), original)
        self.assertEqual(bot_event_v1.read(str(SWTOR)), (clean_bots, clean_coverage),
                         'the complete source recovers without inheriting the synthetic omission')

    def test_partial_ffxi_copy_separates_skipped_lines_without_changing_events(self):
        original = FFXI.read_bytes()
        clean_bots, clean_coverage = ffxi_botsv2_log.read(FFXI)
        partial = parity_partial_ffxi_readiness_source()
        self.assertEqual(partial['id'], 'ffxi-lsb')
        self.assertIn('synthetic incomplete export', partial['label'])
        self.assertIn('Real post-H1 export still required.', partial['note'])
        coverage = partial['coverage']
        self.assertEqual(coverage['status'], 'Loaded')
        self.assertEqual(tuple(coverage[key] for key in ('records', 'omitted', 'unrecognized', 'ignored', 'budget', 'system')),
                         (52, 1, 1, 1, 0, 0))
        self.assertEqual(sum(coverage[key] for key in ('records', 'omitted', 'unrecognized', 'ignored')),
                         len(original.splitlines()) + 3)
        self.assertTrue(coverage['reason'].startswith('Synthetic incomplete readiness sample; not live evidence.'))
        self.assertEqual((coverage['from'], coverage['to']), (clean_coverage['from'], clean_coverage['to']))
        self.assertEqual(partial['bots'], clean_bots, 'omitted lines cannot change identity, events or timing measurements')
        self.assertNotIn('synthetic_unknown', json.dumps(partial))
        self.assertNotIn('synthetic unrelated fixture line', json.dumps(partial))
        self.assertEqual(FFXI.read_bytes(), original)
        self.assertEqual(ffxi_botsv2_log.read(FFXI), (clean_bots, clean_coverage),
                         'the complete source recovers without inherited skipped-line counts')


if __name__ == '__main__':
    unittest.main()
