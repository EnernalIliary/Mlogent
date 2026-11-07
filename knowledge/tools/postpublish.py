#!/usr/bin/env python3
"""postpublish.py — 发布后一条命令校验正式库：dbstat → chunks 对比 → bench20 → 三项 PASS/FAIL。

用法:
    python postpublish.py --db <repo>/out/_kb/kb.sqlite3 --knowledge <repo>/knowledge
    python postpublish.py --db ... --staging <staging>/kb.sqlite3          # 与 staging 构建逐数比对
    python postpublish.py --db ... --expect-chunks 8094 --min-a1 12       # 只给期望值也可

三项判定:
  STRUCT  库可读（无热 journal）；chunks/files > 0；语料里没有 knowledge/_report/、knowledge/_kb/ 等
          工作产物路径（这些文件会自我引用抢 top1，实测过）。
  COUNT   chunks 与 --staging 的构建产物一致（或等于 --expect-chunks）；两者都没给则 SKIP。
  RETRIEVAL  bench20 固定 20 题：A@1 >= --min-a1（默认 12）、top1 落在 knowledge/ 之外 <= --max-outside（默认 4）。

退出码: 0 = 无 FAIL（SKIP 不阻塞）；1 = 有 FAIL。
产物: --out 指定的 markdown 报告（默认 _report/postpublish.md）。
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BAD_PREFIXES = ("knowledge/_report/", "knowledge/_kb/", "knowledge/_raw/", "_report/", "out/")


def _open_ro(db: Path) -> sqlite3.Connection:
    uri = "file:" + str(db).replace(chr(92), "/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def inspect(db: Path) -> dict:
    info = {"path": str(db), "bytes": db.stat().st_size if db.is_file() else 0,
            "chunks": 0, "files": 0, "kinds": {}, "bad_paths": [], "error": ""}
    try:
        conn = _open_ro(db)
        info["chunks"] = conn.execute("select count(*) from chunks").fetchone()[0]
        info["files"] = conn.execute("select count(distinct path) from chunks").fetchone()[0]
        for k, n in conn.execute("select kind, count(*) from chunks group by kind"):
            info["kinds"][k] = n
        info["bad_paths"] = [r[0] for r in conn.execute(
            "select distinct path from chunks")]
        info["bad_paths"] = [p for p in info["bad_paths"] if p.startswith(BAD_PREFIXES)]
        conn.close()
    except Exception as exc:  # 发布瞬间常见：hot journal -> database is locked / readonly
        info["error"] = repr(exc)
    return info


def run_bench(db: Path, out_md: Path) -> dict:
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    # bench20 通过 kb.ROOT 定位知识库根（题库 + 文章），默认取 KB_ROOT 或脚本父目录。
    # 这里由 db 路径反推仓库根（<root>/out/_kb/kb.sqlite3），否则 bench20 会在
    # kb-stage/tools 下找 knowledge/ 而 FileNotFoundError —— 实测发布首次校验就栽在这。
    try:
        cand = Path(db).resolve().parents[2]
        if (cand / "knowledge").is_dir():
            env.setdefault("KB_ROOT", str(cand))
            env.setdefault("KB_KNOWLEDGE", str(cand / "knowledge"))
            if (cand / "out" / "_kblibs311").is_dir():
                env.setdefault("KB_LIBS", str(cand / "out" / "_kblibs311"))
            if (cand / "out" / "_kbmodels").is_dir():
                env.setdefault("KB_MODELS", str(cand / "out" / "_kbmodels"))
    except IndexError:
        pass
    cmd = [sys.executable, str(HERE / "bench20.py"), "--db", str(db), "--out", str(out_md)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, cwd=str(HERE))
    js = out_md.with_suffix(".json")
    if js.is_file():
        try:
            data = json.loads(js.read_text(encoding="utf-8-sig"))
            return data.get("summary", data) if isinstance(data, dict) else data
        except Exception:
            pass
    return {"error": (proc.stdout or "")[-400:] + (proc.stderr or "")[-400:], "returncode": proc.returncode}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--knowledge", default=None, help="仅用于报告里显示，不参与计算")
    ap.add_argument("--staging", default=None, help="staging 构建的 kb.sqlite3，与正式库逐数比对")
    ap.add_argument("--expect-chunks", type=int, default=0)
    ap.add_argument("--min-a1", type=int, default=12)
    ap.add_argument("--max-outside", type=int, default=4)
    ap.add_argument("--out", default=str(HERE.parent / "_report" / "postpublish.md"))
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)

    db = Path(a.db)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    checks = []

    info = inspect(db)
    struct_ok = not info["error"] and info["chunks"] > 0 and not info["bad_paths"]
    why = []
    if info["error"]:
        why.append("库不可读: " + info["error"][:160])
    if info["chunks"] == 0:
        why.append("chunks=0")
    if info["bad_paths"]:
        why.append("语料含工作产物 %d 个: %s" % (len(info["bad_paths"]), ", ".join(info["bad_paths"][:3])))
    checks.append(("STRUCT", "PASS" if struct_ok else "FAIL", "; ".join(why) or "%d chunks / %d files"
                   % (info["chunks"], info["files"])))

    expect = a.expect_chunks
    src = "expect-chunks"
    if a.staging:
        st = inspect(Path(a.staging))
        if st["error"]:
            checks.append(("COUNT", "SKIP", "staging 不可读: " + st["error"][:120]))
            expect = 0
        else:
            expect, src = st["chunks"], "staging(%d files)" % st["files"]
    if expect:
        ok = info["chunks"] == expect
        checks.append(("COUNT", "PASS" if ok else "FAIL",
                       "chunks %d vs %s %d（差 %+d）" % (info["chunks"], src, expect, info["chunks"] - expect)))
    else:
        checks.append(("COUNT", "SKIP", "没给 --staging / --expect-chunks"))

    bench_md = out.with_name(out.stem + "_bench20.md")
    b = run_bench(db, bench_md)
    if "A1" not in b:
        checks.append(("RETRIEVAL", "FAIL", "bench20 失败: " + str(b.get("error"))[:200]))
    else:
        a1, outside = b.get("A1", 0), b.get("outside_top1", 99)
        ok = a1 >= a.min_a1 and outside <= a.max_outside
        checks.append(("RETRIEVAL", "PASS" if ok else "FAIL",
                       "A@1 %d/20 (>=%d) · outside_top1 %d (<=%d) · A@3 %d · p50 %sms"
                       % (a1, a.min_a1, outside, a.max_outside, b.get("A3", -1),
                          b.get("p50_ms", b.get("p50", "-")))))

    code = 1 if any(s == "FAIL" for _, s, _ in checks) else 0
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = ["# 发布后校验", "",
             "- 库: " + str(db) + "  (%d B)" % info["bytes"],
             "- knowledge: " + str(a.knowledge or "-"),
             "- 时间: " + stamp, "",
             "| 项 | 判定 | 依据 |", "|---|---|---|"]
    for name, st, why2 in checks:
        lines.append("| %s | **%s** | %s |" % (name, st, why2))
    lines += ["", "- chunks=%d files=%d kinds=%s" % (info["chunks"], info["files"], info["kinds"]),
              "- 结果: **%s**" % ("PASS" if code == 0 else "FAIL")]
    body = chr(10).join(lines) + chr(10)
    out.write_text(body, encoding="utf-8")
    print(body)
    if a.json:
        Path(a.json).write_text(json.dumps({"checks": checks, "info": info, "bench": b,
                                            "code": code}, ensure_ascii=False, indent=1), encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
