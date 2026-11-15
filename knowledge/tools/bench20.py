#!/usr/bin/env python3
"""bench20.py — 确定性 20 题检索冒烟（题库冻结，抽样行号固定，勿改）。

题库: knowledge/08-evidence/bench/questions.jsonl（300 题冻结题库）
抽样: 每 15 行取 1 题，共 20 题，**固定行号 1,16,31,46,61,76,91,106,121,136,151,166,181,196,211,226,241,256,271,286**
（= --step 15 --n 20 的默认值；换 step/n 出来的数不可与历史对比）

用法:
    python bench20.py --db <kb.sqlite3> --out <报告.md> [--k 6] [--step 15] [--n 20] [--boost 0]

语料权重在 kb.py 内部（KB_KNOWLEDGE_BOOST=1.25 / KB_CODE_PENALTY=0.8，查询期生效）；
--boost 只在"后处理重排"实验时用（>0 才生效），日常跑不要给。

评分两路（都按"不同文件"去重后的 top-k 算）:
  A 锚点命中: top-k 落在 knowledge/ 文章，且该文章正文包含题库 src 的 basename（src 自带行号时要求 file:line）
  B 答案命中: top-k chunk 正文包含题库 answer 字段（整串优先，退化到首个数字）
另统计: top-k 里落在 knowledge/ 之外的比例（docs/游戏速查、MBO、门禁脚本等）。
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

def split_src(s):
    s = (s or "").strip().replace(chr(92), "/")
    if s.startswith("jar:"):
        s = s.split("#", 1)[1] if "#" in s else s
    if "#" in s:
        s = s.split("#", 1)[0]
    line = ""
    if ":" in s:
        base, tail = s.rsplit(":", 1)
        head = tail.split("-")[0]
        if head.isdigit():
            s, line = base, tail
    return s, line

def first_number(t):
    cur = ""
    for ch in t:
        if ch.isdigit() or ch == ".":
            cur += ch
        elif cur:
            break
    return cur

def load_bank(bank, step, n):
    lines = [l for l in bank.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    out = []
    for i in range(0, len(lines), step):
        if len(out) >= n:
            break
        obj = json.loads(lines[i])
        out.append({"no": i + 1, "q": obj.get("q") or obj.get("question") or "",
                    "answer": obj.get("answer") or "", "src": obj.get("src") or obj.get("srcs") or "",
                    "domain": obj.get("domain") or "", "id": obj.get("id") or ""})
    return out

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bank", default=None)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--step", type=int, default=15)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--boost", type=float, default=0.0,
                    help="0=跟随 kb.py 内建权重（默认）；>1 时对本次结果再做后处理重排，仅供实验")
    ap.add_argument("--k-retrieve", type=int, default=0, help="检索深度，默认 max(k, 40)")
    a = ap.parse_args(argv)

    os.environ["KB_DIR"] = str(Path(a.db).resolve().parent)
    import kb  # noqa: E402  同目录；DB_PATH 由 KB_DIR 决定
    root = Path(kb.ROOT)
    bank = Path(a.bank) if a.bank else root / "knowledge" / "08-evidence" / "bench" / "questions.jsonl"
    items = load_bank(bank, a.step, a.n)

    arts = {}
    for p in (root / "knowledge").rglob("*.md"):
        try:
            arts["knowledge/" + p.relative_to(root / "knowledge").as_posix()] = p.read_text(encoding="utf-8-sig")
        except Exception:
            pass

    t0 = time.time()
    next(iter(kb._embedder().embed(["warmup"])))
    warm = time.time() - t0

    rows = []
    for it in items:
        t1 = time.time()
        depth = a.k_retrieve or max(a.k, 40)
        try:
            res = kb.search(it["q"], k=depth)
            if a.boost > 0:
                def adj(r):
                    p = r.get("path") if isinstance(r, dict) else r[0]
                    s = float(r.get("score") or 0) if isinstance(r, dict) else 0.0
                    if p.startswith("knowledge/"):
                        return s * a.boost
                    if p.startswith("tools/") or p.startswith("tests/"):
                        return s * 0.8
                    return s
                res = sorted(res, key=adj, reverse=True)
        except Exception as e:
            res = []
            it["error"] = repr(e)[:120]
        ms = (time.time() - t1) * 1000
        paths, texts, seen = [], [], set()
        for r in res:
            p = r[0] if isinstance(r, tuple) else r.get("path")
            t = r[3] if isinstance(r, tuple) and len(r) > 3 else ""
            if p in seen:
                continue
            seen.add(p)
            paths.append(p)
            texts.append(t or "")
            if len(paths) >= a.k:
                break
        src, line = split_src(it["src"])
        anchor = src.split("/")[-1]
        gold_art = src if src.startswith("knowledge/") else ""
        needle = (anchor + ":" + line) if line else anchor
        hitA = []
        for p, t in zip(paths, texts):
            body = (t or "") + " " + arts.get(p, "")
            if gold_art:
                ok = (p == gold_art) or p.endswith(gold_art.split("knowledge/")[-1])
            else:
                ok = p.startswith("knowledge/") and (needle in body or anchor in arts.get(p, ""))
            hitA.append(bool(ok))
        ans = it["answer"].strip()
        core = first_number(ans)
        hitB = []
        for p, t in zip(paths, texts):
            body = (t or "") + " " + arts.get(p, "")
            ok = bool(ans) and (ans in body or (len(core) >= 2 and core in body))
            hitB.append(bool(ok))
        rows.append({"no": it["no"], "q": it["q"], "gold": it["src"], "answer": ans, "domain": it["domain"],
                     "top": paths, "hitA": hitA, "hitB": hitB, "ms": round(ms, 1)})

    def acc(flag, n):
        return sum(1 for r in rows if any(r[flag][:n]))

    n = len(rows)
    lat = sorted(r["ms"] for r in rows)
    p50 = lat[len(lat) // 2] if lat else 0
    p90 = lat[min(len(lat) - 1, int(len(lat) * 0.9))] if lat else 0
    outside = sum(1 for r in rows if r["top"] and not r["top"][0].startswith("knowledge/"))
    lines = [
        "# bench 20 题检索冒烟",
        "",
        "- 库: %s" % kb.DB_PATH,
        "- 题库: %s（每 %d 行取 1，共 %d 题；第 %s 行）" % (bank, a.step, n, ",".join(str(r["no"]) for r in rows)),
        "- 预热 %.1fs · 单题 p50=%.0fms p90=%.0fms max=%.0fms" % (warm, p50, p90, lat[-1] if lat else 0),
        ("- A 锚点命中 top1/top3/top" + str(a.k) + " = " + str(acc("hitA", 1)) + "/" + str(acc("hitA", 3)) + "/"
         + str(acc("hitA", a.k)) + "（" + str(100 * acc("hitA", 1) // n) + "%/" + str(100 * acc("hitA", 3) // n) + "%/"
         + str(100 * acc("hitA", a.k) // n) + "%）"),
        "- B 答案命中 top1/top3/top%d = %d/%d/%d" % (a.k, acc("hitB", 1), acc("hitB", 3), acc("hitB", a.k)),
        "- top1 落在 knowledge/ 之外: %d/%d" % (outside, n),
        "",
        "| # | 行 | 域 | 题干 | A@1 | A@3 | B@3 | ms | 首条 | 金标 |",
        "|---:|---:|---|---|---|---|---|---:|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append("| %d | %d | %s | %s | %s | %s | %s | %.0f | %s | %s |" % (
            i, r["no"], r["domain"], r["q"][:44].replace("|", "/"),
            "Y" if r["hitA"][:1] and r["hitA"][0] else "N", "Y" if any(r["hitA"][:3]) else "N",
            "Y" if any(r["hitB"][:3]) else "N", r["ms"],
            (r["top"][0] if r["top"] else "-")[:60], r["gold"][:52]))
    miss = [r for r in rows if not any(r["hitA"][:a.k])]
    lines += ["", "## A 未命中明细（%d）" % len(miss), ""]
    for r in miss:
        lines.append("- [%d] %s" % (r["no"], r["q"]))
        lines.append("    gold=%s" % r["gold"])
        for p in r["top"][:3]:
            lines.append("    top: " + p)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(chr(10).join(lines) + chr(10), encoding="utf-8", newline=chr(10))
    Path(a.out).with_suffix(".json").write_text(json.dumps({"db": str(kb.DB_PATH), "rows": rows, "summary": {
        "n": n, "A1": acc("hitA", 1), "A3": acc("hitA", 3), "Ak": acc("hitA", a.k),
        "B1": acc("hitB", 1), "B3": acc("hitB", 3), "Bk": acc("hitB", a.k),
        "outside_top1": outside, "p50_ms": p50, "p90_ms": p90, "warm_s": round(warm, 1)}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"n": n, "A1": acc("hitA", 1), "A3": acc("hitA", 3), "Ak": acc("hitA", a.k),
                      "B1": acc("hitB", 1), "B3": acc("hitB", 3), "Bk": acc("hitB", a.k),
                      "outside_top1": outside, "p50": p50, "p90": p90}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())