#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contract tests for the debug-world pair: tools/world_server.py + world_mcp.py.

Both files are big (a 3.7k-line daemon and a 49-tool MCP shell) and neither had
a single test.  Nothing here starts a JVM or opens a port -- what is worth
pinning down without a running world is:

1. the feed reader -- a feed is the only contract between `mlogsim --push` and
   the daemon, and every "scenes come from the feed" feature hangs off
   `feed_scene()`/`scenes_from_feeds()`;
2. the text channel -- `parse_tsv()`/`coerce()`/`units_table()` turn the java
   side's TSV into the numbers an agent reasons about, and `TRUNC`/`ERR` are
   protocol, not cosmetics;
3. the MCP surface -- 43 tools whose schemas are what an agent actually reads.
   A tool listed but unhandled (or handled but unlisted) is a dead end at call
   time, and only a test notices.

No pytest: plain prints, exit 0 = all passed, 1 = a failure.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import world_server as W  # noqa: E402
import world_mcp as MCP  # noqa: E402

FAILS: list[str] = []


def ok(cond, what: str) -> bool:
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        FAILS.append(what)
    return bool(cond)


def _tmp(name: str, payload) -> str:
    d = os.path.join(ROOT, "out", "_world_tests")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    with io.open(p, "w", encoding="utf-8") as fh:
        if isinstance(payload, str):
            fh.write(payload)
        else:
            json.dump(payload, fh, ensure_ascii=False)
    return p


def _scene_file() -> str:
    return os.path.join(ROOT, "scenes", "scenarios", "unit-control.json")


# ------------------------------------------------------------------ feeds
def test_feed_readers() -> None:
    print("feeds")
    ok(W.feed_age(os.path.join(ROOT, "out", "_world_tests", "nope.json")) is None,
       "a feed that is not there has no age")
    p = _tmp("feed-fresh.json", {"units": []})
    age = W.feed_age(p)
    ok(age is not None and age < 30, "a feed just written is young")
    old = os.path.join(ROOT, "out", "_world_tests", "feed-old.json")
    with io.open(old, "w", encoding="utf-8") as fh:
        fh.write('{"units": []}')
    stamp = time.time() - 120
    os.utime(old, (stamp, stamp))
    age = W.feed_age(old)
    ok(age is not None and age > 100, "an untouched feed ages")

    ok(W.feed_world(None) is None, "no path, no world size")
    ok(W.feed_world(_tmp("f-world.json", {"world": [64, 96]})) == [64, 96],
       "world size comes back as ints")
    ok(W.feed_world(_tmp("f-world-str.json", {"world": ["64.0", "96.0"]})) == [64, 96],
       "world size tolerates the floats the js side writes")
    ok(W.feed_world(_tmp("f-list.json", [1, 2, 3])) is None,
       "the old array-shaped feed has no world size")
    ok(W.feed_world(_tmp("f-bad.json", "{not json")) is None,
       "a half-written feed is not a crash")

    ok(W.feed_anchor(_tmp("f-anchor.json", {"anchor": [32.5, 18]})) == [32.5, 18.0],
       "anchor keeps its fractions")
    ok(W.feed_anchor(_tmp("f-noanchor.json", {"units": []})) is None,
       "no anchor key, no anchor")
    ok(W.feed_bbox(_tmp("f-noanchor.json", {"units": []})) is None,
       "no units, no bounding box")


def test_feed_scene() -> None:
    print("feed scene")
    scene = _scene_file()
    ok(os.path.isfile(scene), "the fixture scenario exists")
    got = W.feed_scene(_tmp("f-scene.json", {"scene": scene, "label": "unit-control"}))
    ok(got == {"path": scene, "label": "unit-control"},
       "a feed that names a real scene hands it over")
    ok(W.feed_scene(_tmp("f-scene-nolabel.json", {"scene": scene}))["label"] is None,
       "a missing label stays None instead of empty string")
    ok(W.feed_scene(_tmp("f-scene-gone.json", {"scene": scene + ".gone"})) is None,
       "a scene that no longer exists is treated as no scene")
    ok(W.feed_scene(_tmp("f-scene-none.json", {"units": []})) is None,
       "an old feed without a scene key stays old")
    ok(W.feed_scene(_tmp("f-scene-list.json", [1, 2])) is None,
       "an array-shaped feed has no scene")

    good = _tmp("f-scene.json", {"scene": scene, "label": "A"})
    plain = _tmp("f-scene-none.json", {"units": []})
    got = W.scenes_from_feeds([good, plain])
    ok(got == [scene, scene],
       "a feed without a scene borrows the first one, so slots stay aligned")
    ok(W.scenes_from_feeds([plain]) == [],
       "if no feed carries a scene, there is nothing to build")
    ok(W.scenes_from_feeds([]) == [], "no feeds, no scenes")


def test_tsv_channel() -> None:
    print("text channel")
    ok(W.coerce("149.0") == 149 and isinstance(W.coerce("149.0"), int),
       "149.0 from js is the integer 149")
    ok(W.coerce("149.5") == 149.5, "149.5 stays fractional")
    ok(W.coerce("-3.0") == -3, "negative whole numbers collapse too")
    ok(W.coerce("flare") == "flare", "names are left alone")
    ok(W.coerce("1e3") in ("1e3", 1000), "exponent forms do not raise")

    got = W.parse_tsv(["1\tpoly\t10\t21", "2\tmono\t11\t22"], ["id", "type", "x", "y"])
    ok(got["count"] == 2 and got["truncated"] is False, "two rows, not truncated")
    ok(got["rows"][0] == {"id": 1, "type": "poly", "x": 10, "y": 21},
       "columns are zipped with the requested names")
    got = W.parse_tsv(["TRUNC", "1\tpoly\t10\t21"], ["id", "type", "x", "y"])
    ok(got["truncated"] is True and got["count"] == 1,
       "TRUNC is a flag, not a row")
    try:
        W.parse_tsv(["ERR\tboom"], ["id"])
        ok(False, "ERR raises")
    except RuntimeError as exc:
        ok(str(exc) == "boom", "ERR raises the message after the tab")

    ok(W.units_table([]) == "(no units)", "an empty unit list says so in words")
    text = W.units_table([{"id": 7, "type": "flare", "x": 10, "y": 20,
                           "controller": "LogicAI", "controlled": 1,
                           "item": "copper", "carry": 5, "itemCapacity": 10,
                           "flag": 0, "mining": 1, "boosting": 0,
                           "health": 40, "maxHealth": 100}])
    ok("LogicAI" in text and "logic" in text, "the table names the controller and the ctrl class")
    ok("copper 5/10" in text and "40/100" in text, "carrying and health are shown as a/b")
    ok(text.splitlines()[0].split() == ["id", "type", "tile", "controller", "items",
                                       "flag", "ctrl", "mine", "boost", "hp"],
       "the header is stable -- agents key on these columns")


# -------------------------------------------------------------------- MCP
def test_tool_surface() -> None:
    print("mcp surface")
    names = [t["name"] for t in MCP.TOOLS]
    ok(len(names) == len(set(names)), "tool names are unique")
    ok(all(t.get("description") for t in MCP.TOOLS), "every tool explains itself")
    bad = [t["name"] for t in MCP.TOOLS
           if (t.get("inputSchema") or {}).get("type") != "object"]
    ok(not bad, "every inputSchema is an object (%s)" % (bad or "ok"))
    unhandled = [n for n in names if n not in MCP.HANDLERS]
    ok(not unhandled, "every listed tool has a handler (%s)" % (unhandled or "ok"))
    unlisted = [n for n in MCP.HANDLERS if n not in names]
    ok(not unlisted, "every handler is listed (%s)" % (unlisted or "ok"))

    props = {t["name"]: (t.get("inputSchema") or {}).get("properties") or {}
             for t in MCP.TOOLS}
    ok("feed" in props["world_arm"], "world_arm takes the feed the director watches")
    ok("radius" in props["world_spawn"] and "count" in props["world_spawn"],
       "world_spawn takes what the scene writer would pass")
    ok(props["world_status"] == {}, "world_status needs no arguments")
    ok("createdAt" not in props.get("world_projstat", {}),
       "projstat stays an argument-free read")


def test_protocol() -> None:
    print("mcp protocol")

    class Fake:
        def __init__(self):
            self.buf = io.StringIO()

        def write(self, s):
            self.buf.write(s)

        def flush(self):
            pass

        def getvalue(self):
            return self.buf.getvalue()

    real = sys.stdout
    fake = Fake()
    try:
        sys.stdout = fake
        MCP.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        MCP.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        MCP.handle({"jsonrpc": "2.0", "id": 3, "method": "nope"})
        MCP.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                    "params": {"name": "world_nope", "arguments": {}}})
        MCP.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
    finally:
        sys.stdout = real
    lines = [json.loads(x) for x in fake.getvalue().splitlines() if x.strip()]
    ok(len(lines) == 4, "notifications get no reply")
    ok(lines[0]["result"]["protocolVersion"] == "2024-11-05", "initialize reports the protocol")
    ok(len(lines[1]["result"]["tools"]) == len(MCP.TOOLS),
       "tools/list is the same list the tests just audited")
    ok(lines[2]["error"]["code"] == -32601, "an unknown method is -32601")
    ok(lines[3]["error"]["code"] == -32602, "an unknown tool is -32602")

    real_call = MCP._wc.call
    real_stdout = sys.stdout
    fake = Fake()
    try:
        MCP._wc.call = lambda *a, **k: {"ok": False, "error": "世界没起"}
        sys.stdout = fake
        MCP.handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                    "params": {"name": "world_status", "arguments": {}}})
        MCP.handle({"jsonrpc": "2.0", "id": 6, "method": "tools/call",
                    "params": {"name": "world_units", "arguments": {}}})
    finally:
        MCP._wc.call = real_call
        sys.stdout = real_stdout
    lines = [json.loads(x) for x in fake.getvalue().splitlines() if x.strip()]
    ok(lines[0]["result"]["isError"] is True, "a failed daemon call becomes isError")
    ok("世界没起" in lines[0]["result"]["content"][0]["text"],
       "the daemon's reason survives into the tool result")


def main() -> int:
    test_feed_readers()
    test_feed_scene()
    test_tsv_channel()
    test_tool_surface()
    test_protocol()
    print("-" * 56)
    if FAILS:
        print("%d failure(s)" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        return 1
    print("all run_world_tests.py passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
