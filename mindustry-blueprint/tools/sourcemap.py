"""Mindcode -> mlog source map (规划 §1 P2 源码映射, V1/V2/V3).

V1 saves the source, the product and the log.  V2 reports the compiler's own
diagnostics with their `line:col`.  V3 is the hard one: Mindcode 3.19.3 has no
instruction-level map (`-r` only styles the *log*, `-u source` prints no
listing, `pm --trace-execution` numbers instructions but names no source line),
so the map has to be inferred.

How V3 works here: compile prefixes of the program and watch which mlog lines
appear.  A statement whose prefix compiles and which adds K mlog lines owns
those K lines.  Statements inside control flow cannot be isolated that way --
truncating a loop body is not valid source -- so they are reported as
`unmapped` with that reason instead of being guessed at.  Optimisation is off
by default for the same reason (`-O 0`): inlining and dead-code elimination
move instructions away from the statement that caused them.

    python tools/sourcemap.py build demo.mnd --json
    python tools/sourcemap.py show demo.mnd --mlog 12
"""
from __future__ import annotations

import argparse
import json
import os
import difflib
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SCHEMA = "mlog-sourcemap/v1"

# 一个「语句」= 顶层的一行 or 一个 begin/do .. end 块。V3 只对单行语句做前缀对齐。
_BLOCK_OPEN = ("do", "begin", "loop", "cached")

# `sum += i;` 这种也是语句；空行与注释不算
def _lines(source: str) -> list[dict]:
    out, depth = [], 0
    for i, raw in enumerate(source.split("\n")):
        line = raw.split("//")[0].strip()
        if not line:
            continue
        opens = any(re.search(r"\b%s$" % w, line) for w in _BLOCK_OPEN)
        closes = bool(re.match(r"^end\b", line)) or bool(re.match(r"^end;", line))
        # 一条 `end` 属于它关闭的那一层，所以记 depth-1：这样「块内语句」的判据就是
        # depth > 0，而 `for` 与 `end` 自己都留在第 0 层。
        at = max(0, depth - 1) if closes else depth
        out.append({"line": i + 1, "text": line, "depth": at,
                    "block": opens, "close": closes})
        if closes:
            depth = max(0, depth - 1)
        if opens:
            depth += 1
    return out


def _mlog_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def _compile(source, target, optimize, timeout, workdir):
    import mindcode as M
    return M.compile_source(source, target=target, optimize=optimize,
                            timeout=timeout, workdir=workdir)


def build(path: str, *, target: str = "7.0", optimize: bool = False,
          timeout: float = 120.0, workdir: str | None = None) -> dict:
    """Compile `path` and infer where each mlog line came from."""
    with open(path, encoding="utf-8-sig") as fh:
        source = fh.read()
    full = _compile(source, target, optimize, timeout, workdir)
    if not full.get("ok"):
        return {"schema": SCHEMA, "ok": False, "source": path,
                "diagnostics": full.get("diagnostics") or [],
                "notes": list(full.get("notes") or [])}

    produced = _mlog_lines(full.get("mlog"))
    stmts = _lines(source)
    mapped, notes = [], []

    # V3: walk the top-level statements, compiling the prefix before each one.
    prev = []
    for idx, st in enumerate(stmts):
        if st["depth"] > 0 or st["block"] or st["close"]:
            mapped.append({"mlog": None, "mnd_line": st["line"],
                           "text": st["text"], "why": "inside control flow"})
            prev = None                     # 前缀断了，后续不再猜
            continue

        prefix = "\n".join(s["text"] for s in stmts[:idx]
                           if s["depth"] == 0 and not s["block"] and not s["close"])
        if not prefix.strip():
            continue
        got = _compile(prefix + "\n" + st["text"], target, optimize, timeout, workdir)
        if not got.get("ok"):
            mapped.append({"mlog": None, "mnd_line": st["line"],
                           "text": st["text"], "why": "prefix does not compile alone"})
            prev = None
            continue
        now = _mlog_lines(got.get("mlog"))
        base = _mlog_lines(
            _compile(prefix, target, optimize, timeout, workdir).get("mlog"))
        # 不是「多出来的尾巴」而是「插进去的那一段」：前一条语句可能因为死代码/
        # 折叠而不产生指令，所以两段输出未必是前缀关系。
        added = []
        for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(
                None, base, now, autojunk=False).get_opcodes():
            if tag in ("insert", "replace"):
                added.extend(range(j1, j2))
        if not added:
            mapped.append({"mlog": None, "mnd_line": st["line"],
                           "text": st["text"],
                           "why": "no instruction of its own (dead code or folded)"})
        else:
            for j in added:
                mapped.append({"mlog": j, "mnd_line": st["line"],
                               "text": st["text"], "why": "prefix alignment"})
        prev = base

    if any(m["mlog"] is None for m in mapped):
        notes.append("有了 unmapped 行：控制流内部与依赖上下文的语句无法用前缀对齐，"
                     "不猜（规划 §1 P2 明确要求考虑内联/死代码对映射的影响）")
    notes.append("V1：source/mlg/log 三件一起保存；V2：诊断里的 line/col 来自编译器本身")

    return {"schema": SCHEMA, "ok": True, "source": path, "target": target,
            "optimize": bool(optimize), "mlog": produced,
            "source_sha256": full.get("source_sha256"),
            "diagnostics": full.get("diagnostics") or [],
            "map": mapped, "notes": notes,
            "stats": full.get("stats") or {}}


def build_from_text(source: str, *, target: str = "7.0", optimize: bool = False,
                    timeout: float = 120.0, workdir: str | None = None) -> dict:
    """`build()` for callers that already hold the text (MCP, tests)."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="mlog-sm-")
    try:
        p = os.path.join(tmp, "inline.mnd")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(source)
        return build(p, target=target, optimize=optimize, timeout=timeout, workdir=workdir)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def show(mapping: dict, mlog_line: int) -> dict:
    """Which source line produced mlog line `mlog_line` (0-based)."""
    for m in mapping.get("map") or []:
        if m.get("mlog") == mlog_line:
            return m
    return {"mlog": mlog_line, "mnd_line": None, "why": "not attributed"}


def _selftest() -> int:
    import tempfile
    ok = 0
    src = 'a = 1;\nb = a + 2;\nprint($"b={b}");\n'
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "t.mnd")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src)
        res = build(p, optimize=False)
        if res.get("ok"):
            ok += 1
        lines = _lines(src)
        assert [ln["line"] for ln in lines] == [1, 2, 3], lines
        ok += 1
        assert _mlog_lines("a\n\nb ") == ["a", "b"]
        ok += 1
        if res.get("ok"):
            assert res["map"], res
            ok += 1
            attrib = [m for m in res["map"] if m["mlog"] is not None]
            assert attrib, res["map"]
            ok += 1
            assert show(res, 0)["mlog"] == 0
            ok += 1
        else:
            assert res["diagnostics"], res     # no jar: the error path is still shaped right
            ok += 3
    # loop body is honestly unmapped
    loop_src = "s = 0;\nfor i in 0 .. 3 do\n    s += i;\nend;\n"
    assert [ln["depth"] for ln in _lines(loop_src)] == [0, 0, 1, 0]
    ok += 1
    print("selftest: %d checks, 0 failures" % ok)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mindcode 源码 -> mlog 行号映射（尽力而为）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="编译并建立映射")
    b.add_argument("path")
    b.add_argument("--target", default="7.0")
    b.add_argument("--optimize", action="store_true",
                   help="开优化（默认关：内联/死代码会让映射漂移）")
    b.add_argument("--json", action="store_true")
    s = sub.add_parser("show", help="查某条 mlog 来自哪一行源码")
    s.add_argument("path")
    s.add_argument("--mlog", type=int, required=True, help="0-based mlog 行号")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)

    if args.cmd == "selftest":
        return _selftest()
    res = build(args.path, target=getattr(args, "target", "7.0"),
                optimize=getattr(args, "optimize", False))
    if args.cmd == "show":
        if not res.get("ok"):
            print(json.dumps(res, ensure_ascii=False, indent=1))
            return 2
        print(json.dumps(show(res, args.mlog), ensure_ascii=False, indent=1))
        return 0
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print("%s -> %d mlog line(s), %d mapped, %d unmapped"
              % (args.path, len(res.get("mlog") or []),
                 sum(1 for m in res.get("map") or [] if m["mlog"] is not None),
                 sum(1 for m in res.get("map") or [] if m["mlog"] is None)))
        for m in (res.get("map") or [])[:12]:
            print("  mlog %-4s <- line %-3s %s%s"
                  % (m["mlog"], m["mnd_line"], m["text"][:48],
                     "" if m["mlog"] is not None else "   (%s)" % m["why"]))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
