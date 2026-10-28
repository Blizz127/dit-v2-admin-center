import tempfile
import threading
import unittest
from pathlib import Path
from hub_cache import HubViewsCache


class HubCacheTests(unittest.TestCase):
    def test_concurrent_calls_share_fetch_and_return_isolated_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            token = Path(directory) / 'token'; token.write_text('fixture')
            calls = []; entered = threading.Event(); release = threading.Event()
            def load(url, path):
                calls.append(1); entered.set(); release.wait(2)
                return {'feeds': [{'at': 'original-time'}]}
            cache = HubViewsCache(load, clock=lambda: 10)
            results = []
            first = threading.Thread(target=lambda: results.append(cache.get('url', token)))
            second = threading.Thread(target=lambda: results.append(cache.get('url', token)))
            first.start(); self.assertTrue(entered.wait(1)); second.start(); release.set(); first.join(); second.join()
            self.assertEqual(len(calls), 1)
            self.assertEqual(results[1]['feeds'][0]['at'], 'original-time')
            results[0]['feeds'][0]['at'] = 'changed'
            self.assertEqual(cache.get('url', token)['feeds'][0]['at'], 'original-time')

    def test_expiry_and_token_file_change_invalidate(self):
        with tempfile.TemporaryDirectory() as directory:
            token = Path(directory) / 'token'; token.write_text('fixture')
            now = [10]; calls = []
            cache = HubViewsCache(lambda *_: calls.append(1) or {'feeds': []}, clock=lambda: now[0])
            cache.get('url', token); cache.get('url', token)
            self.assertEqual(len(calls), 1)
            now[0] = 26; cache.get('url', token)
            self.assertEqual(len(calls), 2)
            token.write_text('different-fixture'); cache.get('url', token)
            self.assertEqual(len(calls), 3)
            token.unlink(); cache.get('url', token)
            self.assertEqual(len(calls), 4)


if __name__ == '__main__': unittest.main()
