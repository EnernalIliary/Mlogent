#!/usr/bin/env python3
"""smoke_kb.py — MCP/检索 20 题冒烟（复用 tools/kb.py 的 search，模型只加载一次）。

用法:
    set KB_DIR=<库目录>            # 默认 <repo>/out/_kb
    python smoke_kb.py --questions q.jsonl --out _report/smoke.md

题干文件格式（每行一条，JSON 或纯文本）:
    {"q": "护甲减伤公式", "expect": ["C05", "03-combat"], "kind": "doc"}
    {"q": "conveyor 的 items/s"}
    护甲减伤公式

判定: top1 / top3 / top6 是否命中 expect 中任一子串（expect 为空则只记录结果不计分）。
输出: markdown 表 + 同名 .json（含每条命中路径、耗时）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def load_questions(p: Path):
    out = []
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            obj = json.loads(s)
        except Exception:
            obj = {"q": s}
        if isinstance(obj, str):
            obj = {"q": obj}
        q = (obj.get("q") or obj.get("question") or "").strip()
        if not q:
            continue
        out.append({"q": q, "expect": obj.get("expect") or [], "kind": obj.get("kind")})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="检索冒烟")
    ap.add_argument("--questions", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--db", default=None, help="kb.sqlite3 路径（默认用 kb.py 的 KB_DIR 规则）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.db:
        os.environ["KB_DIR"] = str(Path(a.db).resolve().parent)
    import kb  # 同目录；DB_PATH 在 import 时由 KB_DIR 决定
    if not Path(kb.DB_PATH).exists():
        print("smoke: 找不到库 " + str(kb.DB_PATH), file=sys.stderr)
        return 2

    qs = load_questions(Path(a.questions))
    if not qs:
        print("smoke: 题干为空", file=sys.stderr)
        return 2

    t0 = time.time()
    next(iter(kb._embedder().embed(["warmup"])))  # 预热，避免把模型加载算进单题耗时
    warm = time.time() - t0
    rows = []
    for item in qs:
        t1 = time.time()
        try:
            res = kb.search(item["q"], k=a.k, kind=item["kind"])
        except Exception as e:
            res = []
            item["error"] = repr(e)[:120]
        dt = (time.time() - t1) * 1000
        hits = [r[0] if isinstance(r, tuple) else (r.get("path"), r.get("start"), r.get("end")) for r in res]
        paths = [h[0] if isinstance(h, tuple) else str(h) for h in hits]
        # 同一文件会被切成多个 chunk，按"不同文件"去重后再算 top-k
        top, seen_p = [], set()
        for p in paths:
            if p in seen_p:
                continue
            seen_p.add(p)
            top.append(p)
            if len(top) >= a.k:
                break
        exp = item["expect"]

        def hit(n):
            return any(all(e in (p or "") for e in exp) for p in top[:n]) if exp else None

        rows.append({"q": item["q"], "expect": exp, "top": top, "ms": round(dt, 1),
                     "top1": hit(1), "top3": hit(3), "topk": hit(a.k),
                     "error": item.get("error")})

    n = len(rows)
    scored = [r for r in rows if r["expect"]]
    acc1 = sum(1 for r in scored if r["top1"])
    acc3 = sum(1 for r in scored if r["top3"])
    acck = sum(1 for r in scored if r["topk"])
    lat = sorted(r["ms"] for r in rows)
    p50 = lat[len(lat) // 2] if lat else 0
    p90 = lat[min(len(lat) - 1, int(len(lat) * 0.9))] if lat else 0
    lines = [
        "# 检索冒烟",
        "",
        "- 题库: %s（%d 题，其中 %d 题有 expect）" % (a.questions, n, len(scored)),
        "- 库: %s" % kb.DB_PATH,
        "- 模型预热: %.1fs  ·  单题 p50=%.0fms  p90=%.0fms  max=%.0fms" % (warm, p50, p90, lat[-1] if lat else 0),
        "- top1 命中 %d/%d（%.0f%%）  top3 %d/%d（%.0f%%）  top%d %d/%d（%.0f%%）"
        % (acc1, len(scored), 100.0 * acc1 / max(1, len(scored)), acc3, len(scored), 100.0 * acc3 / max(1, len(scored)),
           a.k, acck, len(scored), 100.0 * acck / max(1, len(scored))),
        "",
        "| # | 题干 | top1 | 命中@3 | ms | 首条命中 |",
        "|---:|---|---|---|---:|---|",
    ]
    for i, r in enumerate(rows, 1):
        mark = "—" if r["top1"] is None else ("Y" if r["top1"] else "N")
        mark3 = "—" if r["top3"] is None else ("Y" if r["top3"] else "N")
        first = r["top"][0] if r["top"] else ("ERR " + str(r["error"]) if r["error"] else "(no results)")
        lines.append("| %d | %s | %s | %s | %.0f | %s |" % (i, r["q"].replace("|", "/"), mark, mark3, r["ms"], first.replace("|", "/")))
    bad = [r for r in scored if not r["topk"]]
    if bad:
        lines += ["", "## 未命中明细（%d）" % len(bad), ""]
        for r in bad:
            lines.append("- 题干: %s  ·  expect=%s" % (r["q"], r["expect"]))
            for p in r["top"][:3]:
                lines.append("    - " + p)
    text = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
        Path(a.out).with_suffix(".json").write_text(
            json.dumps({"questions": rows, "summary": {"n": n, "scored": len(scored), "hit1": acc1, "hit3": acc3,
                                                       "hitk": acck, "warm_s": round(warm, 1), "p50_ms": p50, "p90_ms": p90}},
                       ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        print("smoke: %d 题 top1=%d/%d top3=%d/%d -> %s" % (n, acc1, len(scored), acc3, len(scored), a.out))
    if a.json:
        print(json.dumps({"rows": rows}, ensure_ascii=False, indent=2))
    elif not a.out:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
