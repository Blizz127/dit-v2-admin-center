"""Read-only validation of a coordinator-designated Codex lead process.

Process identity is not proof of work, available quota, or an active goal.
Only minimal identity fields leave this module; command lines are never returned.
"""
import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path


def current_codex_binding(lane_path, database, project, proc_root=Path('/proc')):
    unknown = {'provider': None, 'thread': None,
               'coverage': 'Current lead process binding is unverified'}
    try:
        with lane_path.open('rb') as stream:
            raw = stream.read(262145)
        if len(raw) > 262144:
            return unknown
        lane = json.loads(raw)
        if (lane.get('provider') != 'codex' or lane.get('phase') != 'running'
                or lane.get('cwd') != str(project)):
            return unknown
        pid, thread = lane.get('pid'), lane.get('thread')
        if type(pid) is not int or pid <= 1 or not isinstance(thread, str):
            return unknown
        if str(uuid.UUID(thread)) != thread:
            return unknown
        process = proc_root / str(pid)
        if ((process / 'exe').resolve(strict=True).name != 'codex'
                or (process / 'cwd').resolve(strict=True) != project.resolve(strict=True)):
            return unknown
        with (process / 'cmdline').open('rb') as stream:
            command = stream.read(65537)
        if len(command) > 65536:
            return unknown
        args = command.rstrip(b'\0').split(b'\0')
        if b'resume' not in args or thread.encode() not in args:
            return unknown
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
            rows = db.execute('SELECT cwd, archived FROM threads WHERE id=?', (thread,)).fetchall()
        if rows != [(str(project), 0)]:
            return unknown
        return {'provider': 'codex', 'thread': thread,
                'coverage': 'Coordinator handoff, native process and thread metadata agree; activity and quota unverified'}
    except (OSError, ValueError, TypeError, AttributeError, sqlite3.Error):
        return unknown
