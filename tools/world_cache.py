"""Small bounded TTL cache for read-only live-world MCP responses."""

from __future__ import annotations

from collections import OrderedDict
import copy
import threading
import time


class ResponseCache:
    def __init__(self, *, ttl: float = 0.75, limit: int = 256):
        if ttl <= 0 or limit < 1:
            raise ValueError("cache ttl must be positive and limit must be at least 1")
        self.ttl = float(ttl)
        self.limit = int(limit)
        self._entries = OrderedDict()
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key):
        now = time.monotonic()
        with self._lock:
            item = self._entries.get(key)
            if item is None:
                self.misses += 1
                return None
            expires, value = item
            if expires <= now:
                self._entries.pop(key, None)
                self.misses += 1
                return None
            self._entries.move_to_end(key)
            self.hits += 1
            return copy.deepcopy(value)

    def put(self, key, value):
        with self._lock:
            self._entries[key] = (time.monotonic() + self.ttl, copy.deepcopy(value))
            self._entries.move_to_end(key)
            while len(self._entries) > self.limit:
                self._entries.popitem(last=False)

    def clear(self):
        with self._lock:
            self._entries.clear()

    def stats(self):
        with self._lock:
            return {"entries": len(self._entries), "hits": self.hits, "misses": self.misses,
                    "ttl_s": self.ttl, "limit": self.limit}
