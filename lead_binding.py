"""Read-only validation of a coordinator-designated Codex lead process.

Process identity is not proof of work, available quota, or an active goal.
Only minimal identity fields leave this module; command lines are never returned.
"""
import json
import sqlite3
import uuid
from local_evidence import read_bytes
from contextlib import closing
from pathlib import Path


def _resume_thread(args):
    """Recognize the explicit resume form used by the coordinator; never match a prompt."""
    if len(args) < 3 or args[1] != b'resume':
        return None
    valued = {b'--model', b'-m', b'--config', b'-c', b'--profile', b'-p',
              b'--cd', b'-C', b'--sandbox', b'-s', b'--ask-for-approval', b'-a'}
    flags = {b'--dangerously-bypass-approvals-and-sandbox', b'--no-alt-screen', b'--full-auto', b'--all'}
    index = 2
    while index < len(args):
        arg = args[index]
        if arg in valued:
            index += 2
        elif arg in flags:
            index += 1
        elif b'=' in arg and arg.split(b'=', 1)[0] in valued:
            index += 1
        elif arg.startswith(b'-'):
            return None
        else:
            return arg
    return None


def current_codex_binding(lane_path, database, project, proc_root=Path('/proc')):
    unknown = {'provider': None, 'thread': None,
               'coverage': 'Current lead process binding is unverified'}
    try:
        raw = read_bytes(lane_path, 262144)
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
        if _resume_thread(args) != thread.encode():
            return unknown
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
            rows = db.execute('SELECT cwd, archived FROM threads WHERE id=?', (thread,)).fetchall()
        if rows != [(str(project), 0)]:
            return unknown
        return {'provider': 'codex', 'thread': thread,
                'coverage': 'Coordinator handoff, native process and thread metadata agree; activity and quota unverified'}
    except (OSError, ValueError, TypeError, AttributeError, RecursionError, sqlite3.Error):
        return unknown
