"""Synthetic numeric edge cases; no live reader, accounts or spend ledger."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from live_hub import project_server_status, project_spend, read_views


class OfflineNumericProjectionTests(unittest.TestCase):
    def setUp(self):
        for name in ('socket.socket', 'socket.create_connection'):
            guard = patch(name, side_effect=AssertionError('Network forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def test_unrepresentable_rates_are_unknown_without_losing_other_feeds(self):
        for value in (10**400, -1, True, float('inf'), float('nan'), '2', None):
            with self.subTest(type=type(value).__name__):
                def get(view, game):
                    payload = {'bots': [], 'learning': {'gameId': game, 'tasks': []},
                               'server-status': {'gameId': game, 'status': {'xpRate': value}}}[view]
                    return payload, 'fixture-time'
                data = read_views(SimpleNamespace(get=get), games=('ffxi',))
                self.assertIsNone(data['gameStatus']['ffxi']['xpRate'])
                self.assertEqual(data['gameStatus']['ffxi']['liveness'], 'Unknown')
                self.assertEqual(data['bots']['ffxi'], [])
                self.assertEqual(data['learning']['ffxi'], [])
                self.assertEqual(len(data['feeds']), 3)

    def test_unrepresentable_money_is_unknown_not_zero(self):
        for value in (10**400, -1, True, float('inf'), float('nan'), '2', None):
            with self.subTest(type=type(value).__name__):
                row = project_spend({'configured': True, 'settledUsd': value,
                                     'reservedOpenUsd': value, 'budgetUsd': value}, 'fixture-time')
                for field in ('settledUsd', 'reservedOpenUsd', 'budgetUsd'):
                    self.assertIsNone(row[field])

    def test_valid_zero_and_fraction_preserved_with_pricing_and_scope_gates(self):
        for value in (0, 0.25, 123):
            row = project_server_status({'gameId': 'ffxi', 'status': {'xpRate': value}}, 'ffxi', 'fixture-time')
            self.assertEqual(row['xpRate'], value)
            spend = project_spend({'configured': True, 'settledUsd': value,
                                   'budgetUsd': value, 'pricingError': 'synthetic unknown'}, 'fixture-time')
            self.assertEqual(spend['settledUsd'], value)
            self.assertIsNone(spend['budgetUsd'])
        with self.assertRaises(ValueError):
            project_server_status({'gameId': 'swtor'}, 'ffxi', 'fixture-time')
        self.assertIsNone(project_spend({'configured': False, 'settledUsd': 0}, 'fixture-time')['settledUsd'])


if __name__ == '__main__':
    unittest.main()
