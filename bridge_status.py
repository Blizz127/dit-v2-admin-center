"""Bounded, read-only observation of the explicitly approved FFXI bridge."""
import json
from datetime import datetime
import subprocess
import threading
import time

# This fixed script executes on the verified host. It emits only service status,
# marker presence and an allowlisted marker classification; it never returns chat.
REMOTE = r'''
import datetime, json, os, stat, subprocess
result = {'observedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'unit': 'unknown', 'substate': 'unknown', 'result': 'unknown', 'marker': 'unknown', 'markerReason': 'unknown'}
try:
    command = subprocess.run(['systemctl', '--user', 'show', 'dit-ffxi-chat-bridge-v2.service', '--property=ActiveState,SubState,Result'], capture_output=True, text=True, timeout=3, check=True)
    fields = dict(line.split('=', 1) for line in command.stdout.splitlines() if '=' in line)
    for dest, key, allowed in [('unit', 'ActiveState', {'active','inactive','failed','activating','deactivating','reloading','maintenance','refreshing'}), ('substate', 'SubState', {'running','dead','failed','start','stop','auto-restart','exited'}), ('result', 'Result', {'success','exit-code','signal','timeout','resources','start-limit-hit'})]:
        if fields.get(key) in allowed: result[dest] = fields[key]
except (OSError, subprocess.SubprocessError, ValueError): pass
path = '/home/blizz/.local/state/dit-ffxi-chat-bridge-v2/delivery-fault.json'
try:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if stat.S_ISREG(info.st_mode) and info.st_size <= 4096:
            result['marker'] = 'present'
            try:
                data = json.loads(os.read(fd, 4097))
                if data == {'state': 'failed', 'reason': 'delayed_delivery_failed'}: result['markerReason'] = 'delayed_delivery_failed'
            except (ValueError, UnicodeError, RecursionError): pass
    finally: os.close(fd)
except FileNotFoundError:
    try:
        if stat.S_ISDIR(os.stat(os.path.dirname(path)).st_mode): result['marker'] = 'absent'
    except OSError: pass
except OSError: pass
print(json.dumps(result))
'''


class BridgeObserver:
    def __init__(self, runner=subprocess.run, clock=time.monotonic):
        self.runner, self.clock = runner, clock
        self.lock = threading.Lock()
        self.cached = None
        self.checked = None

    def read(self):
        with self.lock:
            now = self.clock()
            if self.cached is not None and self.checked is not None and 0 <= now - self.checked < 15:
                return dict(self.cached)
            unknown = {'observedAt': None, 'unit': 'unknown', 'substate': 'unknown', 'result': 'unknown',
                       'marker': 'unknown', 'markerReason': 'unknown', 'source': 'Verified SSH observation unavailable'}
            try:
                result = self.runner(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=3',
                                      'blizz@100.74.44.12', 'python3', '-'], input=REMOTE, capture_output=True,
                                     text=True, timeout=8, check=True)
                if len(result.stdout) > 4096:
                    raise ValueError('oversized response')
                data = json.loads(result.stdout)
                if not isinstance(data, dict):
                    raise ValueError('invalid response')
                # Revalidate remotely supplied values before displaying them.
                allowed = {'unit': {'active','inactive','failed','activating','deactivating','reloading','maintenance','refreshing','unknown'},
                           'substate': {'running','dead','failed','start','stop','auto-restart','exited','unknown'},
                           'result': {'success','exit-code','signal','timeout','resources','start-limit-hit','unknown'},
                           'marker': {'present','absent','unknown'}, 'markerReason': {'delayed_delivery_failed','unknown'}}
                for field, values in allowed.items():
                    if data.get(field) not in values:
                        raise ValueError('unexpected field')
                if not isinstance(data.get('observedAt'), str) or len(data['observedAt']) > 64:
                    raise ValueError('invalid timestamp')
                observed = datetime.fromisoformat(data['observedAt'].replace('Z', '+00:00'))
                if observed.utcoffset() is None:
                    raise ValueError('timestamp lacks timezone')
                if data['marker'] != 'present' and data['markerReason'] != 'unknown':
                    raise ValueError('fault classification without marker')
                self.cached = {key: data[key] for key in ('observedAt', *allowed)}
                self.cached['source'] = 'Read-only Banshee SSH; bridge unit and private fault marker'
            except (OSError, subprocess.SubprocessError, ValueError, TypeError, KeyError, RecursionError):
                self.cached = unknown
            self.checked = now
            return dict(self.cached)
