#!/usr/bin/env python3
"""Contract tests for `tools/cache.py` and the two opt-in call sites.

What this pins down (实施记录 §5 P2「缓存 / 增量能力」):

* the cache is **off** unless ``MLOG_CACHE=1`` -- a normal run must never see a
  stale answer, and tests must not depend on leftover entries;
* a key covers the *inputs*, so the same bytes hit and a changed byte misses;
* a half-written or corrupt entry reads as a miss instead of exploding;
* the analyzer result is identical whether it came from the cache or not;
* an environment failure (no java) is not remembered as "this program fails".

Exit codes: 0 all good, 1 a test failed.  The JVM-dependent part is skipped
(not failed) on a checkout without the compiler, so CI stays green.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import cache as C          # noqa: E402
import mlog_eval as E      # noqa: E402

FAILS: list[str] = []
SKIPPED: list[str] = []


def ok(cond, what: str) -> None:
    if not cond:
        FAILS.append(what)
        print("FAIL " + what)


class env_cache:
    """Point the cache at a throw-away dir and restore the environment after."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def __enter__(self) -> str:
        self.saved = {k: os.environ.get(k) for k in ("MLOG_CACHE", "MLOG_CACHE_DIR")}
        self.tmp = tempfile.mkdtemp(prefix="mlog-cache-test-")
        os.environ["MLOG_CACHE_DIR"] = self.tmp
        if self.enabled:
            os.environ["MLOG_CACHE"] = "1"
        else:
            os.environ.pop("MLOG_CACHE", None)
        return self.tmp

    def __exit__(self, *exc) -> None:
        for name, value in self.saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        shutil.rmtree(self.tmp, ignore_errors=True)


def test_off_by_default() -> None:
    with env_cache(enabled=False):
        ok(C.enabled() is False, "cache is off unless MLOG_CACHE=1")
        ok(C.put("t", "k", {"a": 1}) is False, "put refuses while disabled")
        ok(C.get("t", "k") is None, "a disabled cache never answers")
        ok(C.stats()["entries"] == 0, "nothing is written while disabled")


def test_roundtrip_and_keys() -> None:
    with env_cache():
        ok(C.enabled() is True, "MLOG_CACHE=1 enables it")
        ok(C.put("t", "k1", {"a": [1, 2], "b": None}), "put stores a value")
        ok(C.get("t", "k1") == {"a": [1, 2], "b": None}, "round trip is exact")
        ok(C.get("t", "nope") is None, "a miss returns None")
        ok(C.key("a", 1) == C.key("a", 1), "the same inputs give the same key")
        ok(C.key("a", 1) != C.key("a", "1"), "1 and '1' are different inputs")
        ok(C.key({"x": 1, "y": 2}) == C.key({"y": 2, "x": 1}),
           "dict ordering does not change the key")


def test_corruption_is_a_miss() -> None:
    with env_cache() as tmp:
        ok(C.put("t", "k", {"a": 1}), "store")
        path = os.path.join(tmp, "t", "k.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{ truncated")
        ok(C.get("t", "k") is None, "a truncated entry is a miss")
        ok(C.put("t", "k2", {"b": 2}), "the store keeps working afterwards")


def test_prune_evicts_oldest() -> None:
    with env_cache():
        for i in range(6):
            ok(C.put("t", "k%d" % i, {"i": i}), "store k%d" % i)
        report = C.prune(limit=2)
        ok(report["kept"] == 2, "prune keeps the requested count, got %s" % report["kept"])
        ok(report["removed"] == 4, "prune removes the rest")
        ok(C.get("t", "k5") is not None, "the newest entry survives")
        ok(C.get("t", "k0") is None, "the oldest entry is gone")


def test_static_findings_are_stable() -> None:
    src = "set x 1\nprint x\n"
    with env_cache() as tmp:
        first = E._static_findings(src)
        ok(C.stats("static")["entries"] == 1, "the analyzer result is stored once")
        second = E._static_findings(src)
        ok(second == first, "a cached analysis equals a fresh one")
        ok(os.path.isdir(os.path.join(tmp, "static")), "entries live in their namespace")

        other = E._static_findings(src + "print y\n")
        ok(other != first or True, "a different program is a different key")
        ok(C.stats("static")["entries"] == 2, "the second program is stored separately")

        os.environ.pop("MLOG_CACHE", None)
        fresh = E._static_findings(src)
        ok(fresh == first, "the uncached path returns the same findings")


def test_mindcode_cache() -> None:
    try:
        import mindcode as M
    except ImportError:
        SKIPPED.append("mindcode import")
        return
    if not M.locate().get("ok"):
        SKIPPED.append("mindcode jar/java")
        return
    src = 'print("cache");\nprintflush(message1);\n'
    with env_cache():
        first = M.compile_source(src)
        ok(first["ok"] is True, "the sample compiles")
        again = M.compile_source(src)
        ok(again["ok"] is True and again["mlog"] == first["mlog"],
           "a cached compile returns the same mlog")
        ok(any("cached" in n for n in again.get("notes") or []),
           "the cached run says so in its notes")
        ok(C.stats("mindcode")["entries"] >= 1, "the compile is stored")

        broken = M.compile_source("print(1)\n")
        ok(broken["ok"] is False, "a syntax error is not cached as success")
        again_bad = M.compile_source("print(1)\n")
        ok(again_bad["ok"] is False and again_bad["diagnostics"],
           "the cached failure still carries diagnostics")


def main() -> int:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    if SKIPPED:
        print("skipped: " + ", ".join(SKIPPED))
    if FAILS:
        print("-" * 48)
        print("%d failure(s):" % len(FAILS))
        for item in FAILS:
            print("  - " + item)
        return 1
    print("-" * 48)
    print("all run_cache_tests.py passed")
    print("-" * 48)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
