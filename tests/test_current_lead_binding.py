import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from lead_binding import current_codex_binding


class CurrentLeadBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project'; self.project.mkdir()
        self.proc = self.root / 'proc'; self.process = self.proc / '123'; self.process.mkdir(parents=True)
        self.executable = self.root / 'codex'; self.executable.touch()
        (self.process / 'exe').symlink_to(self.executable)
        (self.process / 'cwd').symlink_to(self.project)
        self.thread = '11111111-1111-4111-8111-111111111111'
        (self.process / 'cmdline').write_bytes(b'codex\0resume\0' + self.thread.encode() + b'\0private-prompt\0')
        self.lane = self.root / 'lane.json'
        self.record = {'provider': 'codex', 'phase': 'running', 'cwd': str(self.project), 'pid': 123, 'thread': self.thread}
        self.lane.write_text(json.dumps(self.record))
        self.database = self.root / 'native.sqlite'
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE TABLE threads(id TEXT, cwd TEXT, archived INTEGER)')
            db.execute('INSERT INTO threads VALUES (?, ?, 0)', (self.thread, str(self.project)))

    def read(self):
        return current_codex_binding(self.lane, self.database, self.project, self.proc)

    def test_requires_matching_handoff_process_and_native_thread(self):
        result = self.read()
        self.assertEqual(result['provider'], 'codex')
        self.assertEqual(result['thread'], self.thread)
        self.assertIn('activity and quota unverified', result['coverage'])
        self.assertNotIn('private-prompt', str(result))

    def test_rejects_stale_or_wrong_handoff(self):
        for change in ({'provider': 'claude'}, {'phase': 'paused'}, {'cwd': '/other'},
                       {'pid': True}, {'pid': 999}, {'thread': 'not-a-thread'}):
            with self.subTest(change=change):
                self.lane.write_text(json.dumps({**self.record, **change}))
                self.assertIsNone(self.read()['provider'])

    def test_rejects_reused_process_or_wrong_native_metadata(self):
        (self.process / 'cmdline').write_bytes(b'codex\0resume\0other-thread\0')
        self.assertIsNone(self.read()['provider'])
        (self.process / 'cmdline').write_bytes(b'codex\0resume\0' + self.thread.encode() + b'\0')
        with sqlite3.connect(self.database) as db:
            db.execute('UPDATE threads SET archived=1')
        self.assertIsNone(self.read()['provider'])

    def test_missing_database_is_not_created(self):
        self.database.unlink()
        self.assertIsNone(self.read()['provider'])
        self.assertFalse(self.database.exists())


if __name__ == '__main__': unittest.main()
