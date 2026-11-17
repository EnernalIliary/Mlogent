#!/usr/bin/env python3
"""五组对照实验：基线(1FB23F2A) / +去重 / +硬过滤 / +ASCII / 三者全开.

每组跑同一份冻结 300 题（+ 24 题跨源 v2 草案），口径与 tools/eval_kb.py 完全一致：
gold = knowledge 正文里出现过 src basename 的文档；hit@k/mrr 以 coverage 为分母；
strong@k 要求命中文档同时含「文件:行号」锚点。

额外列：库外占比（top-k 槽位里不在 knowledge/ 也不在 00-data/ 的比例）、
data 槽占比（00-data 摘要块）、公式题 hit@6（source_kind.json 标签）。
"""
from __future__ import annotations

import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根

import argparse
import importlib.util
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
STAGE = HERE.parents[1]
STAGE_TOOLS = STAGE / "tools"
REPO = Path(__file__).resolve().parents[4]   # _scripts -> 仓库根
KNOW = Path(os.environ.get("KS_KNOW") or (REPO / "knowledge"))
DB_BASE = Path(os.environ.get("KS_DB_BASE") or (STAGE / "out" / "_kb_base" / "kb.sqlite3"))
DB_SCOPE = Path(os.environ.get("KS_DB_SCOPE") or (STAGE / "out" / "_kb_scope" / "kb.sqlite3"))

EXCLUDE_DIRS = {"_kb", "_raw", "_report", "_kb_build", "__pycache__", "bench", ".git"}


def iter_docs(kb: Path):
    for p in sorted(kb.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(kb)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        # 只把「文章 + 00-data 摘要表」当 gold：跳过 out/ 与 _ 前缀缓存目录
        if any(part == "out" or part.startswith("_") for part in rel.parts):
            continue
        if p.suffix.lower() not in (".md", ".json", ".jsonl", ".py", ".txt"):
            continue
        if p.name.startswith("_") or p.name == "questions.jsonl":
            continue
        try:
            yield str(rel).replace("\\", "/"), p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue


def src_parts(src: str):
    frag = None
    if "#" in src:
        src, frag = src.split("#", 1)
    m = re.match(r"^(.*?)(?::(\d+)(?:-(\d+))?)?$", src)
    path, l1, l2 = m.group(1), m.group(2), m.group(3)
    return Path(path).name, (Path(path).name + ":" + l1 if l1 else None), (l1, l2, frag)


def norm(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def load_base():
    os.environ["KB_ROOT"] = str(REPO)
    os.environ["KB_KNOWLEDGE"] = str(KNOW)
    if str(STAGE_TOOLS) not in sys.path:
        sys.path.insert(0, str(STAGE_TOOLS))
    spec = importlib.util.spec_from_file_location("kb_base_mod", STAGE_TOOLS / "kb.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.DB_PATH = DB_BASE
    mod._open = lambda: __import__("sqlite3").connect(DB_BASE)
    return mod


def load_scope():
    spec = importlib.util.spec_from_file_location("kb_scope_mod", STAGE_TOOLS / "kb_scope.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default=str(HERE / "questions.jsonl"))
    ap.add_argument("--derive", default=str(HERE / "questions-derive.jsonl"))
    ap.add_argument("--source-kinds", default=str(HERE / "source_kind.json"))
    ap.add_argument("--out", default=str(HERE / "scope_ab.json"))
    ap.add_argument("--per-question", default=str(HERE / "scope_ab_pq.json"))
    ap.add_argument("-k", type=int, default=6)
    ap.add_argument("--candidates", type=int, default=40)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--variants", default="")
    a = ap.parse_args(argv)

    rows = [json.loads(l) for l in open(a.questions, encoding="utf-8") if l.strip()]
    derive = [json.loads(l) for l in open(a.derive, encoding="utf-8") if l.strip()] \
        if Path(a.derive).exists() else []
    if a.limit:
        rows = rows[:a.limit]
        derive = derive[:max(2, a.limit // 4)]
    kinds = json.loads(Path(a.source_kinds).read_text(encoding="utf-8"))
    kind_of = {q["id"]: q.get("source_kind") for q in kinds.get("questions", [])}
    formula_ids = {i for i, v in kind_of.items() if v == "公式"}

    docs = {rel: txt for rel, txt in iter_docs(KNOW)}
    print("docs:", len(docs), "questions:", len(rows), "derive:", len(derive), file=sys.stderr)

    base = load_base()
    scope = load_scope()

    def v_base(q, k):
        return base.search(q, k, candidates=a.candidates)

    def v_dedup(q, k):
        return scope.search(q, k, dedupe=True, candidates=a.candidates, db=DB_BASE)

    def v_scope(q, k):
        return scope.search(q, k, dedupe=False, candidates=a.candidates, db=DB_SCOPE)

    def v_scope_dedup(q, k):
        return scope.search(q, k, dedupe=True, candidates=a.candidates, db=DB_SCOPE)

    def v_ascii(q, k):
        return scope.search(q, k, ascii_boost=True, dedupe=False,
                            candidates=a.candidates, db=DB_BASE)

    def v_all(q, k):
        return scope.search(q, k, dedupe=True, ascii_boost=True,
                            candidates=a.candidates, db=DB_SCOPE)

    variants = [("baseline", v_base), ("dedup", v_dedup), ("scope", v_scope),
                ("scope_dedup", v_scope_dedup), ("ascii", v_ascii), ("all", v_all)]
    if a.variants:
        want = {x.strip() for x in a.variants.split(",") if x.strip()}
        variants = [v for v in variants if v[0] in want]
    report = {}
    pq_all = {}
    for name, fn in variants:
        per_dom = defaultdict(lambda: {"n": 0, "cov": 0, "hit1": 0, "hitk": 0,
                                       "rr": 0.0, "strong": 0, "strong_n": 0})
        pq = []
        slots = outside = data_slots = 0
        distinct_files = 0
        for r in rows:
            nm, anchor, _ = src_parts(r["src"])
            gold = [rel for rel, txt in docs.items() if nm in txt]
            d = per_dom[r["domain"]]
            d["n"] += 1
            if not gold:
                pq.append({"id": r["id"], "domain": r["domain"], "covered": 0,
                           "rank": None, "hit": 0, "strong": 0, "top": []})
                continue
            d["cov"] += 1
            res = fn(r["q"].split("\n")[0], a.k)
            paths = [norm(x["path"]) for x in res]
            for p, x in zip(paths, res):
                slots += 1
                inside = p.startswith("knowledge/") or p.startswith("00-data/")
                if not inside:
                    outside += 1
                if x.get("kind") == "data" or p.startswith("00-data/"):
                    data_slots += 1
            distinct_files += len(set(paths))
            rank = next((i for i, p in enumerate(paths) if any(p.endswith(g) for g in gold)), None)
            has_anchor = anchor is not None and any(anchor in docs[g] for g in gold)
            if has_anchor:
                d["strong_n"] += 1
            if rank is not None:
                d["hitk"] += 1
                d["rr"] += 1.0 / (rank + 1)
                if rank == 0:
                    d["hit1"] += 1
                if has_anchor:
                    d["strong"] += 1
            pq.append({"id": r["id"], "domain": r["domain"], "covered": 1, "rank": rank,
                       "hit": int(rank is not None),
                       "strong": int(rank is not None and has_anchor),
                       "top": paths[:a.k]})
        # 跨源 24 题
        dv_hit = dv_n = dv_cov = 0
        for r in derive:
            nm, _anchor, _ = src_parts(r["src"])
            golds = [rel for rel, txt in docs.items() if nm in txt or
                     any(Path(s.split(":")[0]).name in txt for s in r.get("srcs", []))]
            if not golds:
                continue
            dv_cov += 1
            dv_n += 1
            res = fn(r["q"].split("\n")[0], a.k)
            paths = [norm(x["path"]) for x in res]
            if any(any(p.endswith(g) for g in golds) for p in paths[:a.k]):
                dv_hit += 1
        cov = sum(v["cov"] for v in per_dom.values())
        n = len(rows)
        rep = {
            "n": n,
            "coverage": round(cov / max(n, 1), 4),
            "hit@1": round(sum(v["hit1"] for v in per_dom.values()) / max(cov, 1), 4),
            "hit@k": round(sum(v["hitk"] for v in per_dom.values()) / max(cov, 1), 4),
            "mrr": round(sum(v["rr"] for v in per_dom.values()) / max(cov, 1), 4),
            "strong@k": round(sum(v["strong"] for v in per_dom.values())
                              / max(sum(v["strong_n"] for v in per_dom.values()), 1), 4),
            "outside_slot_share": round(outside / max(slots, 1), 4),
            "data_slot_share": round(data_slots / max(slots, 1), 4),
            "avg_distinct_files_topk": round(distinct_files / max(cov, 1), 2),
            "formula_hit@k": round(sum(1 for x in pq if x["id"] in formula_ids
                                       and x.get("hit")) / max(1, sum(1 for x in pq if x["id"] in formula_ids)), 4),
            "formula_n": sum(1 for x in pq if x["id"] in formula_ids),
            "derive_hit@k": round(dv_hit / max(dv_n, 1), 4),
            "derive_n": dv_n,
            "domains": {k2: {"n": v["n"],
                             "hit@1": round(v["hit1"] / max(v["cov"], 1), 3),
                             "hit@k": round(v["hitk"] / max(v["cov"], 1), 3),
                             "mrr": round(v["rr"] / max(v["cov"], 1), 3),
                             "strong": round(v["strong"] / max(v["strong_n"], 1), 3)}
                        for k2, v in sorted(per_dom.items())},
        }
        report[name] = rep
        pq_all[name] = pq
        print(name, json.dumps({k2: v for k2, v in rep.items() if k2 != "domains"},
                               ensure_ascii=False), file=sys.stderr)

    Path(a.out).write_text(json.dumps({"k": a.k, "candidates": a.candidates,
                                       "questions": str(a.questions), "variants": report},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    Path(a.per_question).write_text(json.dumps(pq_all, ensure_ascii=False, indent=1),
                                    encoding="utf-8")

    hdr = ("variant", "hit@1", "hit@6", "mrr", "strong@6", "库外%", "data%", "文件数", "公式", "跨源")
    print("%-10s %7s %7s %7s %8s %7s %6s %7s %6s %6s" % hdr)
    for name, _ in variants:
        r = report[name]
        print("%-10s %6.1f%% %6.1f%% %7.3f %7.1f%% %6.1f%% %5.1f%% %7.2f %5.0f%% %5.0f%%" % (
            name, r["hit@1"] * 100, r["hit@k"] * 100, r["mrr"], r["strong@k"] * 100,
            r["outside_slot_share"] * 100, r["data_slot_share"] * 100,
            r["avg_distinct_files_topk"], r["formula_hit@k"] * 100, r["derive_hit@k"] * 100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
