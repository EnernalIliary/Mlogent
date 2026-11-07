#!/usr/bin/env python
"""把 lexical 与 hybrid 两次评测结果合并成三段式 eval_report.json（lexical / hybrid / comparison）。

用法：
  python merge_report.py --lexical rep_lexical.json --hybrid rep_hybrid.json --out eval_report.json

输出结构：
  {
    "meta": {generated, questions, topk, note},
    "lexical":  <原样 lexical 报告>,
    "hybrid":   <原样 hybrid 报告>,
    "comparison": {
        "overall": {metric: {"lexical": x, "hybrid": y, "delta": y-x}, ...},
        "domains": [{domain, lexical{}, hybrid{}, delta{}}, ...],
        "by_source_kind": [...],          # 若提供 --source-kinds
        "out_of_kb_hits": {...}           # 若提供 --oob
    },
    # 兼容旧读法：顶层保留 lexical 的标量
    "engine": ..., "coverage": ..., "hit@1": ..., ...
  }
题库冻结，本脚本只合并报告，不改题、不改脚本语义。
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
METRICS = ["coverage", "hit@1", "hit@k", "mrr@k", "strong@k"]


def load(p: str):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def delta(a, b):
    if a is None or b is None:
        return None
    return round(b - a, 4)


def by_kind(lex: dict, hyb: dict, kinds_path: Path):
    """按 source_kind 汇总两引擎的 coverage/hit@k/strong@k。"""
    if not kinds_path.exists():
        return []
    kind = {q["id"]: q["source_kind"] for q in load(str(kinds_path))["questions"]}
    out = []
    for label, rep in (("lexical", lex), ("hybrid", hyb)):
        agg = collections.defaultdict(lambda: {"n": 0, "cov": 0, "hit": 0, "strong": 0, "strong_n": 0})
        gaps = {g["id"] for g in rep.get("gaps", [])}
        miss = {m["id"] for m in rep.get("misses", [])}
        for qid, k in kind.items():
            a = agg[k]
            a["n"] += 1
            if qid in gaps:
                continue
            a["cov"] += 1
            if qid not in miss:        # misses 只存前 50，故 hit 为下界
                a["hit"] += 1
        out.append({label: {k: {"n": v["n"], "coverage": round(v["cov"] / max(v["n"], 1), 3),
                               "hit@k_lower_bound": round(v["hit"] / max(v["cov"], 1), 3)}
                             for k, v in sorted(agg.items())}})
    merged = collections.defaultdict(dict)
    for part in out:
        for label, d in part.items():
            for k, v in d.items():
                merged[k][label] = v
    return [{"source_kind": k, **v} for k, v in merged.items()]


def pq_stats(path: str, inside_prefix: str = "knowledge/") -> dict:
    """逐题明细（eval_kb.py --per-question）→ 「命中落在 knowledge 之外」统计。"""
    d = load(path)
    rows = d.get("rows", [])
    slots = outside_slots = 0
    top1_outside = top6_any_inside = covered = hit = 0
    outside_docs = collections.Counter()
    for r in rows:
        cov = int(r.get("covered") or 0)
        if not cov:
            continue
        covered += 1
        hit += int(r.get("hit") or 0)
        top = r.get("top") or []
        if r.get("top1"):
            top = [r["top1"]] if not top else top
        inside = [p for p in top if p.startswith(inside_prefix)]
        out = [p for p in top if not p.startswith(inside_prefix)]
        slots += len(top)
        outside_slots += len(out)
        for p in out:
            outside_docs[p] += 1
        if top and not top[0].startswith(inside_prefix):
            top1_outside += 1
        if inside:
            top6_any_inside += 1
    return {
        "engine": d.get("engine"),
        "questions": len(rows),
        "covered": covered,
        "hit@k_recount": round(hit / max(covered, 1), 4),
        "topk_slots": slots,
        "topk_slots_outside_knowledge": outside_slots,
        "outside_slot_share": round(outside_slots / max(slots, 1), 4),
        "questions_with_top1_outside_knowledge": top1_outside,
        "top1_outside_share": round(top1_outside / max(covered, 1), 4),
        "questions_with_any_knowledge_doc_in_topk": top6_any_inside,
        "any_knowledge_doc_share": round(top6_any_inside / max(covered, 1), 4),
        "top_outside_docs": outside_docs.most_common(12),
        "inside_prefix": inside_prefix,
    }


def by_kind_pq(pq_path: str, kinds_path: Path) -> list:
    """用逐题明细精确算每个 source_kind 的 hit@k（不受 misses 截断影响）。"""
    if not Path(pq_path).exists() or not kinds_path.exists():
        return []
    rows = {r["id"]: r for r in load(pq_path)["rows"]}
    kind = {q["id"]: q["source_kind"] for q in load(str(kinds_path))["questions"]}
    agg = collections.defaultdict(lambda: {"n": 0, "cov": 0, "hit": 0, "hit1": 0})
    for qid, k in kind.items():
        r = rows.get(qid)
        if not r:
            continue
        a = agg[k]
        a["n"] += 1
        if r.get("covered"):
            a["cov"] += 1
            a["hit"] += int(bool(r.get("hit")))
            a["hit1"] += int(r.get("rank") == 0)
    return [{"source_kind": k, "n": v["n"], "coverage": round(v["cov"] / max(v["n"], 1), 3),
             "hit@1": round(v["hit1"] / max(v["cov"], 1), 3),
             "hit@k": round(v["hit"] / max(v["cov"], 1), 3)}
            for k, v in sorted(agg.items())]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lexical", required=True)
    ap.add_argument("--hybrid", required=True)
    ap.add_argument("--out", default=str(HERE / "eval_report.json"))
    ap.add_argument("--source-kinds", default=str(HERE / "source_kind.json"))
    ap.add_argument("--lexical-pq", default=None, help="lexical 的逐题明细（可选，用于精确 by_source_kind）")
    ap.add_argument("--hybrid-pq", default=None, help="hybrid 的逐题明细（可选，用于 knowledge 外命中统计）")
    ap.add_argument("--inside-prefix", default="knowledge/", help="判定「在 knowledge 内」的路径前缀")
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)

    lex, hyb = load(a.lexical), load(a.hybrid)
    overall = {}
    for m in METRICS:
        overall[m] = {"lexical": lex.get(m), "hybrid": hyb.get(m), "delta": delta(lex.get(m), hyb.get(m))}

    doms = []
    keys = sorted(set(lex.get("domains", {})) | set(hyb.get("domains", {})))
    for d in keys:
        l = lex.get("domains", {}).get(d, {})
        h = hyb.get("domains", {}).get(d, {})
        row = {"domain": d, "n": h.get("n") or l.get("n")}
        for m in METRICS:
            row[m] = {"lexical": l.get(m), "hybrid": h.get(m),
                      "delta": delta(l.get(m), h.get(m))}
        doms.append(row)

    rep = {
        "meta": {
            "generated": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "questions": hyb.get("questions") or lex.get("questions"),
            "topk": hyb.get("topk") or lex.get("topk"),
            "note": a.note or "lexical = 纯标准库 BM25（kb-stage 镜像）；hybrid = 仓库 tools/kb.py（dense bge-small-zh + FTS5 + RRF）",
        },
        "lexical": lex,
        "hybrid": hyb,
        "comparison": {
            "overall": overall,
            "domains": doms,
            "by_source_kind": by_kind(lex, hyb, Path(a.source_kinds)),
        },
    }
    if a.hybrid_pq:
        rep["comparison"]["out_of_kb_hits"] = pq_stats(a.hybrid_pq, a.inside_prefix)
    if a.lexical_pq:
        rep["comparison"]["by_source_kind_pq"] = {
            "lexical": by_kind_pq(a.lexical_pq, Path(a.source_kinds)),
            "hybrid": by_kind_pq(a.hybrid_pq, Path(a.source_kinds)) if a.hybrid_pq else [],
        }
    # 兼容旧读法：顶层保留 lexical 标量
    for k in ("engine", "knowledge", "questions", "topk", *METRICS):
        if k in lex:
            rep[k] = lex[k]
    Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {a.out}")
    print(f"{'metric':<10}{'lexical':>10}{'hybrid':>10}{'delta':>9}")
    for m in METRICS:
        v = overall[m]
        fmt = lambda x: ("%.1f%%" % (x * 100)) if x is not None and m != "mrr@k" else ("%.3f" % x if x is not None else "-")
        print(f"{m:<10}{fmt(v['lexical']):>10}{fmt(v['hybrid']):>10}{str(v['delta']):>9}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
