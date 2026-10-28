"""Small in-memory single-flight cache for explicitly requested read-only hub views."""
import copy
import threading
import time
from pathlib import Path


class HubViewsCache:
    def __init__(self, loader, clock=time.monotonic, ttl=15):
        self.loader, self.clock, self.ttl = loader, clock, ttl
        self.lock = threading.Lock()
        self.key = None
        self.value = None
        self.ready_at = None

    def get(self, url, token_file):
        with self.lock:
            try:
                info = Path(token_file).stat()
                key = (url, str(token_file), info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
            except OSError:
                # A missing or unreadable token never receives an earlier cached result.
                self.key = self.value = self.ready_at = None
                return self.loader(url, token_file)
            now = self.clock()
            if self.key == key and self.value is not None and self.ready_at is not None and 0 <= now - self.ready_at < self.ttl:
                return copy.deepcopy(self.value)
            # Clear before fetching so a failure cannot expose a previous credential's snapshot.
            self.key = self.value = self.ready_at = None
            result = self.loader(url, token_file)
            self.key, self.value, self.ready_at = key, copy.deepcopy(result), self.clock()
            return copy.deepcopy(result)
