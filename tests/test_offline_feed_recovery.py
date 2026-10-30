"""Reader -> cache -> overview merge with synthetic transport bytes and clock."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from hub_cache import HubViewsCache
from live_hub import HubReader, merge_views, read_views


def snapshot():
    return {'bots': [{'game': game, 'name': 'Synthetic bot', 'source': 'Synthetic fallback'} for game in ('FFXI', 'SWTOR')],
            'learning': [{'game': game, 'id': 'synthetic-' + game, 'source': 'Synthetic fallback'} for game in ('FFXI', 'SWTOR')],
            'issues': [], 'gameStatus': [{'game': game, 'xpRate': None, 'source': 'Synthetic fallback'} for game in ('FFXI', 'SWTOR')]}


class OfflineFeedRecoveryTests(unittest.TestCase):
    def test_timeout_and_partial_feeds_expire_without_stale_rows_or_hidden_retries(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch('socket.socket', side_effect=AssertionError('Network forbidden')), \
                patch('socket.create_connection', side_effect=AssertionError('Network forbidden')):
            token = Path(directory) / 'token'
            token.write_text('synthetic-token')
            reader = HubReader('http://127.0.0.1:1', token)
            clock, phase, calls = [0], ['initial'], []

            def response(request, timeout):
                url = urlsplit(request.full_url)
                view = url.path.removeprefix('/v1/control/')
                query = parse_qs(url.query)
                game = query['gameId'][0]
                self.assertEqual(request.get_method(), 'GET')
                self.assertEqual(timeout, 3)
                self.assertIn(view, ('bots', 'learning', 'server-status'))
                self.assertEqual(set(query), {'gameId', 'light', 'tasksOnly'} if view == 'learning' else {'gameId'})
                calls.append((phase[0], game, view))
                task = {'id': phase[0] + '-task', 'gameId': game, 'topic': 'Synthetic task', 'status': 'unverified'}
                data = {'bots': [{'key': phase[0] + '-bot', 'name': phase[0] + ' bot'}],
                        'learning': {'gameId': game, 'tasks': [task]},
                        'server-status': {'gameId': game, 'status': {'xpRate': 2}}}[view]
                if phase[0] == 'ambiguous':
                    if (game, view) == ('ffxi', 'bots'):
                        return io.BytesIO(b'[{"key":"first","key":"last","name":"OMIT_PRIVATE_AMBIGUITY"}]')
                    if (game, view) == ('ffxi', 'learning'):
                        return io.BytesIO(b'{"gameId":"swtor","gameId":"ffxi","tasks":[]}')
                    if (game, view) == ('swtor', 'server-status'):
                        return io.BytesIO(b'{"gameId":"swtor","status":{"xpRate":1e999}}')
                if phase[0] == 'partial':
                    if (game, view) == ('ffxi', 'bots'):
                        raise TimeoutError('OMIT_PRIVATE_TIMEOUT')
                    if (game, view) == ('ffxi', 'learning'):
                        return io.BytesIO(b'{"tasks":[{"private":"OMIT_PRIVATE_TRUNCATED"')
                    if (game, view) == ('swtor', 'bots'):
                        data = []  # A complete empty collection, not a failure.
                    if (game, view) == ('swtor', 'learning'):
                        data['tasks'].append(None)  # Reject the entire invalid collection.
                return io.BytesIO(json.dumps(data).encode())

            reader.opener = Mock()
            reader.opener.open.side_effect = response
            cache = HubViewsCache(lambda *_: read_views(reader), clock=lambda: clock[0])
            def load():
                return merge_views(snapshot(), cache.get(reader.base, token))

            initial = load()
            self.assertEqual(len(calls), 6)
            self.assertTrue(all(row['name'] == 'initial bot' for row in initial['bots']))
            initial_feeds = copy.deepcopy(initial['hubFeeds'])
            phase[0], clock[0] = 'partial', 14
            self.assertEqual(load()['hubFeeds'], initial_feeds)
            self.assertEqual(len(calls), 6)
            clock[0] = 15
            partial = load()
            self.assertEqual(len(calls), 12, 'One attempt per feed; no automatic retry')
            self.assertEqual(partial['bots'], [{'game': 'FFXI', 'name': 'Synthetic bot', 'source': 'Synthetic fallback'}])
            self.assertTrue(all(row['source'] == 'Synthetic fallback' for row in partial['learning']))
            self.assertTrue(all(row['xpRate'] == 2 and row['liveness'] == 'Unknown' for row in partial['gameStatus']))
            failed = [feed for feed in partial['hubFeeds'] if feed['status'] == 'Unavailable']
            self.assertEqual({(feed['game'], feed['view']) for feed in failed},
                             {('FFXI', 'bots'), ('FFXI', 'learning'), ('SWTOR', 'learning')})
            self.assertTrue(all(feed['at'] is None for feed in failed))
            self.assertNotIn('OMIT_PRIVATE', json.dumps(partial))
            self.assertNotIn('initial bot', json.dumps(partial))
            self.assertNotIn('partial-task', json.dumps(partial), 'No valid prefix from an invalid page')
            clock[0], phase[0] = 29, 'recovered'
            self.assertEqual(load()['hubFeeds'], partial['hubFeeds'])
            self.assertEqual(len(calls), 12, 'Partial failures share the normal cache lifetime')
            clock[0] = 30
            recovered = load()
            self.assertEqual(len(calls), 18)
            self.assertTrue(all(row['name'] == 'recovered bot' for row in recovered['bots']))
            self.assertTrue(all(row['id'].endswith('recovered-task') for row in recovered['learning']))
            self.assertTrue(all(feed['status'] == 'Live response' for feed in recovered['hubFeeds']))
            self.assertTrue(all(row['status'] == 'Unknown' for row in recovered['bots']))
            phase[0], clock[0] = 'ambiguous', 45
            ambiguous = load()
            self.assertEqual(len(calls), 24, 'Invalid JSON is not retried within the refresh')
            failed = {(feed['game'], feed['view']) for feed in ambiguous['hubFeeds'] if feed['status'] == 'Unavailable'}
            self.assertEqual(failed, {('FFXI', 'bots'), ('FFXI', 'learning'), ('SWTOR', 'server-status')})
            for field in ('bots', 'learning'):
                ffxi = [row for row in ambiguous[field] if row['game'] == 'FFXI']
                self.assertEqual(ffxi, [row for row in snapshot()[field] if row['game'] == 'FFXI'])
            self.assertEqual([row for row in ambiguous['gameStatus'] if row['game'] == 'SWTOR'],
                             [row for row in snapshot()['gameStatus'] if row['game'] == 'SWTOR'])
            self.assertNotIn('recovered', json.dumps(ambiguous), 'Previous positive rows must not survive invalid refresh')
            self.assertNotIn('OMIT_PRIVATE', json.dumps(ambiguous))
            self.assertTrue(all(feed['at'] is None for feed in ambiguous['hubFeeds'] if feed['status'] == 'Unavailable'))
            phase[0], clock[0] = 'final', 59
            self.assertEqual(load()['hubFeeds'], ambiguous['hubFeeds'])
            self.assertEqual(len(calls), 24)
            clock[0] = 60
            final = load()
            self.assertEqual(len(calls), 30)
            self.assertTrue(all(feed['status'] == 'Live response' for feed in final['hubFeeds']))
            self.assertTrue(all(row['name'] == 'final bot' for row in final['bots']))


if __name__ == '__main__':
    unittest.main()
