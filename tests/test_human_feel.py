"""human_feel: measurements of machine-regular timing. Too few samples is None, never a pass."""
import unittest
from datetime import datetime, timedelta, timezone

import human_feel

T0 = datetime(2026, 11, 9, 14, 0, 0, tzinfo=timezone.utc)


def at(*seconds):
    return [T0 + timedelta(seconds=s) for s in seconds]


class HumanFeelTests(unittest.TestCase):
    def test_cadence_finds_the_most_regular_action_and_ignores_gaps_between_fights(self):
        nukes = at(*[i * 3.2 for i in range(12)], *[500 + i * 3.2 for i in range(4)])  # two fights
        varied = at(0, 4, 9.5, 12, 19, 21, 30, 33.3, 41, 44, 52, 57, 61)
        result = human_feel.cadence({'combat nuke': nukes, 'travel path': varied})
        # 11 gaps in the first fight and 3 in the second; the 464.8 s gap between fights is not a cadence gap.
        self.assertEqual(result, {'action': 'combat nuke', 'gaps': 14, 'modalGapS': 3.2, 'modalCount': 14,
                                  'modalShare': 1.0, 'metronomic': True})
        human = human_feel.cadence({'travel path': varied})
        self.assertEqual((human['action'], human['metronomic']), ('travel path', False))
        self.assertLess(human['modalShare'], human_feel.METRONOMIC_SHARE)

    def test_cadence_with_too_few_gaps_is_unknown(self):
        self.assertIsNone(human_feel.cadence({}))
        self.assertIsNone(human_feel.cadence({'combat nuke': at(*[i * 3.2 for i in range(human_feel.MIN_GAPS)])}))
        self.assertIsNotNone(human_feel.cadence({'combat nuke': at(*[i * 3.2 for i in range(human_feel.MIN_GAPS + 1)])}))

    def test_cadence_rounds_millisecond_jitter_to_the_step(self):
        result = human_feel.cadence({'a': at(*[i * 3.2 + (0.004 if i % 2 else 0) for i in range(12)])})
        self.assertEqual((result['modalGapS'], result['modalShare']), (3.2, 1.0))

    def test_sync_counts_group_actions_within_a_second_of_another_bot(self):
        own = {'mount': at(0, 100, 200, 300), 'dismount': at(50, 150)}
        others = {'mount': at(0.4, 100.9, 201.5), 'dismount': at(49.2), 'tripEnd': at(300)}
        # Together: mounts at 0 and 100, dismount at 50. Not: mount 200 (1.5 s), mount 300 (another kind), dismount 150.
        self.assertEqual(human_feel.sync(own, others),
                         {'actions': 6, 'together': 3, 'share': 0.5, 'synchronized': False})
        tight = human_feel.sync({'mount': at(0, 10, 20, 30, 40)}, {'mount': at(0.001, 10.4, 20.8, 30, 41.5)})
        self.assertEqual((tight['together'], tight['synchronized']), (4, True))
        self.assertIsNone(human_feel.sync({'mount': at(0, 1)}, {'mount': at(0, 1)}))
        self.assertEqual(human_feel.sync({'mount': at(0, 10, 20, 30, 40)}, {})['together'], 0)

    def test_schedule_labels_a_fixed_clock(self):
        fixed = human_feel.schedule(at(0, 2317, 2317 + 3456, 2317 + 2 * 3456, 2317 + 3 * 3456 + 0.4))
        self.assertEqual(fixed, {'intervals': 4, 'modalIntervalS': 3456.0, 'modalCount': 3, 'modalShare': 0.75,
                                 'fixed': True})
        loose = human_feel.schedule(at(0, 1800, 4100, 5200, 9000))
        self.assertEqual((loose['modalCount'], loose['fixed']), (1, False))
        self.assertIsNone(human_feel.schedule(at(0, 3456, 6912)))


if __name__ == '__main__':
    unittest.main()
