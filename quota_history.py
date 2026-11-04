"""Read cached Codex quota observations; persist only a local, minimal history."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3

WINDOWS = ('unified5h', 'unified7d')
MAX_ROWS = 10000


def finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def observations(path):
    try:
        if path.stat().st_size > 1_000_000:
            return []
        data = json.loads(path.read_text())
        accounts = data.get('accounts', {})
        if not isinstance(accounts, dict):
            return []
        result = []
        for key, entry in accounts.items():
            if not isinstance(key, str) or not isinstance(entry, dict):
                continue
            email = entry.get('email')
            # The project excludes SBISD accounts; ambiguous entries are omitted.
            if not isinstance(email, str) or not email.strip() or 'sbisd' in email.lower():
                continue
            usage = entry.get('usage')
            if not isinstance(usage, dict) or usage.get('error'):
                continue
            stamp = usage.get('checked_at')
            if not finite_number(stamp) or stamp <= 0:
                continue
            try:
                datetime.fromtimestamp(stamp, timezone.utc)
            except (ValueError, OverflowError, OSError):
                continue
            rows = usage.get('rows')
            if not isinstance(rows, list):
                continue
            account = hashlib.sha256(('dit-admin-codex:' + key).encode()).hexdigest()[:16]
            for row in rows:
                quota = row.get('quota') if isinstance(row, dict) else None
                if not isinstance(quota, dict):
                    continue
                for window in WINDOWS:
                    used = quota.get(window)
                    if finite_number(used) and 0 <= used <= 1:
                        result.append((account, float(stamp), window, float(used)))
        return result
    except (OSError, ValueError, TypeError, AttributeError):
        return []


def collect(source, root):
    samples = observations(source)
    if not samples:
        return 0
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = root / 'codex-quota.sqlite'
    # Create private on first use without changing permissions on existing files.
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        pass
    else:
        os.close(fd)
    with closing(sqlite3.connect(path, timeout=2)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS samples (account TEXT, observed REAL, window TEXT, used REAL, PRIMARY KEY(account, observed, window))')
        before = db.total_changes
        db.executemany('INSERT OR IGNORE INTO samples VALUES (?,?,?,?)', samples)
        inserted = db.total_changes - before
        db.execute('DELETE FROM samples WHERE rowid IN (SELECT rowid FROM samples ORDER BY observed DESC, rowid DESC LIMIT -1 OFFSET ?)', (MAX_ROWS,))
        return inserted


def history(root):
    path = root / 'codex-quota.sqlite'
    try:
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)) as db:
            rows = db.execute('SELECT account, observed, window, used FROM samples ORDER BY observed DESC LIMIT 100').fetchall()
        return [{'account': account, 'observedAt': datetime.fromtimestamp(at, timezone.utc).isoformat(),
                 'window': window, 'remainingPercent': round((1 - used) * 100, 1)}
                for account, at, window, used in rows]
    except (OSError, sqlite3.Error, ValueError, OverflowError):
        return []
