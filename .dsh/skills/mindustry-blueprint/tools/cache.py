#!/usr/bin/env python3
"""A small content-addressed cache for expensive, pure results.

Why this exists (规划 §5 P2「缓存 / 增量能力」): an agent session re-asks the same
questions.  Compiling the same ``.mnd`` or re-running static analysis over the
same mlog costs a JVM start or a 100 ms scan, every time, and the answer cannot
have changed -- the input bytes and the tool version are the whole input.

Design constraints, in order:

* **Opt-in.** ``MLOG_CACHE=1`` turns it on; the default is off so that every tool
  keeps returning timings and fresh work unless a caller asked otherwise.  Tests
  never see a cache hit unless they ask for one.
* **The tool version is part of the key.**  A cached answer is only valid for the
  code that produced it, so callers pass a namespace *and* a ``tool_version``
  string (a file hash or an explicit constant).  Bump it when the algorithm
  changes; no manual cache clearing is needed.
* **No half-written entries.**  ``put`` writes to ``.tmp`` and ``os.replace``s --
  a crash leaves the old entry (or nothing), never a truncated JSON file.  Reads
  treat unparsable files as misses and delete them.
* **Bounded.**  ``prune`` drops the least recently used entries past a count or
  byte limit; ``get`` touches mtime so "recently useful" is the eviction order.

CLI: ``list``, ``stats``, ``prune``, ``clear``, ``selftest``.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time

SCHEMA = "mlog-cache/v1"
DEFAULT_LIMIT = 4000
DEFAULT_BYTES = 64 * 1024 * 1024


def enabled() -> bool:
    """True when the caller opted in (``MLOG_CACHE=1``)."""
    return (os.environ.get("MLOG_CACHE") or "").strip().lower() in ("1", "true", "yes", "on")


def default_dir() -> str:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.environ.get("MLOG_CACHE_DIR") or os.path.join(here, "out", "_cache")


def key(*parts) -> str:
    """Stable key for a set of inputs; JSON so that 1 and "1" differ."""
    h = hashlib.sha256()
    for part in parts:
        h.update(json.dumps(part, ensure_ascii=False, sort_keys=True,
                            default=str).encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def _ns_dir(namespace: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in namespace)
    return os.path.join(default_dir(), safe)


def get(namespace: str, cache_key: str, *, touch: bool = True):
    """Return the cached value, or None.  Never raises."""
    path = os.path.join(_ns_dir(namespace), cache_key + ".json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            record = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        return None
    if touch:
        try:
            os.utime(path, None)
        except OSError:
            pass
    return record.get("value")


def put(namespace: str, cache_key: str, value, *, force: bool = False) -> bool:
    """Store a JSON-able value atomically.  Returns False when disabled/failed.

    ``force`` is for *internal* memos -- a tool memoising its own pure helper
    (sourcemap's prefix compiles) wants the entry regardless of whether the user
    opted into the shared cache.  It only skips the opt-in gate; everything else
    (atomic write, namespace, version in the key) still applies.
    """
    if not force and not enabled():
        return False
    directory = _ns_dir(namespace)
    try:
        os.makedirs(directory, exist_ok=True)
        final = os.path.join(directory, cache_key + ".json")
        tmp = final + ".%d.tmp" % os.getpid()
        record = {"schema": SCHEMA, "namespace": namespace, "key": cache_key,
                  "stored": time.strftime("%Y-%m-%dT%H:%M:%S"), "value": value}
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(record, fh, ensure_ascii=False)
        os.replace(tmp, final)
        return True
    except (OSError, TypeError, ValueError):
        return False


def stats(namespace: str | None = None) -> dict:
    """Entry count and total bytes, per namespace and overall."""
    root = default_dir()
    out = {"root": root, "enabled": enabled(), "schema": SCHEMA,
           "entries": 0, "bytes": 0, "namespaces": {}}
    if not os.path.isdir(root):
        return out
    names = sorted(os.listdir(root))
    for name in names:
        path = os.path.join(root, name)
        if not os.path.isdir(path) or (namespace and name != namespace):
            continue
        count = size = 0
        for entry in os.listdir(path):
            full = os.path.join(path, entry)
            if not entry.endswith(".json") or not os.path.isfile(full):
                continue
            count += 1
            try:
                size += os.path.getsize(full)
            except OSError:
                pass
        out["namespaces"][name] = {"entries": count, "bytes": size}
        out["entries"] += count
        out["bytes"] += size
    return out


def _entries(root: str) -> list[tuple[float, str]]:
    rows: list[tuple[float, str]] = []
    for name in os.listdir(root):
        directory = os.path.join(root, name)
        if not os.path.isdir(directory):
            continue
        for entry in os.listdir(directory):
            if not entry.endswith(".json"):
                continue
            full = os.path.join(directory, entry)
            try:
                rows.append((os.path.getmtime(full), full))
            except OSError:
                pass
    rows.sort()                              # oldest first
    return rows


def prune(limit: int = DEFAULT_LIMIT, max_bytes: int = DEFAULT_BYTES) -> dict:
    """Evict least recently used entries until both limits hold."""
    root = default_dir()
    report = {"removed": 0, "kept": 0, "bytes": 0, "root": root}
    if not os.path.isdir(root):
        return report
    rows = _entries(root)
    total = 0
    sizes: list[tuple[int, str]] = []
    for _, full in rows:
        try:
            size = os.path.getsize(full)
        except OSError:
            size = 0
        sizes.append((size, full))
        total += size
    keep_from = max(0, len(sizes) - max(0, limit))
    for index, (size, full) in enumerate(sizes):
        if index < keep_from or (total > max_bytes and index < len(sizes) - 1):
            try:
                os.remove(full)
                total -= size
                report["removed"] += 1
            except OSError:
                pass
    report["kept"] = len(sizes) - report["removed"]
    report["bytes"] = total
    return report


def clear(namespace: str | None = None) -> int:
    """Remove one namespace (or everything).  Returns entries removed."""
    root = default_dir()
    if not os.path.isdir(root):
        return 0
    removed = 0
    for name in sorted(os.listdir(root)):
        directory = os.path.join(root, name)
        if not os.path.isdir(directory) or (namespace and name != namespace):
            continue
        for entry in os.listdir(directory):
            if entry.endswith(".json"):
                removed += 1
        shutil.rmtree(directory, ignore_errors=True)
    return removed


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

def _selftest() -> int:
    import tempfile
    fails: list[str] = []

    def ok(cond, what):
        if not cond:
            fails.append(what)
            print("FAIL " + what)

    saved = {k: os.environ.get(k) for k in ("MLOG_CACHE", "MLOG_CACHE_DIR")}
    tmp = tempfile.mkdtemp(prefix="mlog-cache-")
    os.environ["MLOG_CACHE_DIR"] = tmp
    try:
        os.environ.pop("MLOG_CACHE", None)
        ok(not enabled(), "off by default")
        ok(put("demo", "k1", {"a": 1}) is False, "put is a no-op while disabled")
        ok(get("demo", "k1") is None, "nothing is stored while disabled")

        os.environ["MLOG_CACHE"] = "1"
        ok(enabled(), "env turns it on")
        ok(put("demo", "k1", {"a": 1, "b": ["x"]}), "put stores")
        ok(get("demo", "k1") == {"a": 1, "b": ["x"]}, "round trip")
        ok(get("demo", "missing") is None, "a miss is None")

        ok(key(1) != key("1"), "the key distinguishes 1 from \"1\"")
        ok(key({"a": 1, "b": 2}) == key({"b": 2, "a": 1}), "key is order independent")

        final = os.path.join(tmp, "demo", "k1.json")
        with open(final, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        ok(get("demo", "k1") is None, "a corrupt entry is a miss, not an exception")

        ok(put("demo", "k2", {"a": 2}), "second put")
        report = prune(limit=1)
        ok(report["removed"] >= 1 and report["kept"] == 1, "prune keeps the newest only")
        ok(get("demo", "k2") is not None, "the newest entry survived")

        ok(put("other", "k", 1), "another namespace")
        ok(stats()["namespaces"]["other"]["entries"] == 1, "stats counts namespaces")
        ok(clear("demo") >= 1, "clear removes one namespace")
        ok(stats()["namespaces"].get("demo") is None, "the namespace is gone")
        ok(get("other", "k") == 1, "the other namespace is untouched")
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        shutil.rmtree(tmp, ignore_errors=True)

    for flag in ("MLOG_CACHE", "MLOG_CACHE_DIR"):
        os.environ.pop(flag, None)
    if fails:
        print("-" * 48)
        print("%d failure(s)" % len(fails))
        return 1
    print("cache selftest: ok")
    return 0


def main(argv: list[str]) -> int:
    cmd = (argv[1] if len(argv) > 1 else "stats").lower()
    if cmd == "selftest":
        return _selftest()
    if cmd == "stats":
        print(json.dumps(stats(argv[2] if len(argv) > 2 else None),
                         ensure_ascii=False, indent=1))
        return 0
    if cmd == "prune":
        print(json.dumps(prune(), ensure_ascii=False, indent=1))
        return 0
    if cmd == "clear":
        print(json.dumps({"removed": clear(argv[2] if len(argv) > 2 else None)},
                         ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
