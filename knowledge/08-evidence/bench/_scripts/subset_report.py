# -*- coding: utf-8 -*-
"""分族群评测：把「真正考推导」的题单独拉出来算 hit@6。

输入是 eval_kb.py 的 --per-question 产物（不自己跑检索）：
    python 08-evidence/bench/subset_report.py --per-question tmp_lexical_pq.json \
        --derive-pq tmp_derive_pq.json --out 08-evidence/bench/subset_report.json

三个族群：
  formula  冻结 300 题里 source_kind=公式 的 22 题（必须代公式/算数才能答）
  derive   questions-derive.jsonl 的 24 道跨源题（v2 草案，不进主指标）
  combined 46 题 —— 判断「v2 有没有价值」的唯一指标
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_pq(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return d, {r["id"]: r for r in d["rows"]}


def agg(rows):
    n = len(rows)
    cov = sum(r["covered"] for r in rows)
    hit = sum(r["hit"] for r in rows)
    rr = sum((1.0 / (r["rank"] + 1)) if r["rank"] is not None else 0.0 for r in rows)
    strong = sum(r["strong"] for r in rows)
    return {"n": n, "coverage": round(cov / max(n, 1), 3),
            "hit@6": round(hit / max(cov, 1), 3),
            "mrr@6": round(rr / max(cov, 1), 3),
            "strong@6": round(strong / max(cov, 1), 3),
            "ids": [r["id"] for r in rows]}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Focused-subset hit@k report")
    ap.add_argument("--per-question", required=True, help="冻结 300 题的逐题明细")
    ap.add_argument("--derive-pq", default=None, help="questions-derive 的逐题明细（可选）")
    ap.add_argument("--source-kinds", default=str(HERE / "source_kind.json"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    pq, by_id = load_pq(a.per_question)
    sk = json.loads(Path(a.source_kinds).read_text(encoding="utf-8"))
    kinds = {q["id"]: q["source_kind"] for q in sk["questions"]}

    formula_ids = [i for i in sorted(kinds) if kinds[i] == "公式" and i in by_id]
    formula = agg([by_id[i] for i in formula_ids])

    derive = None
    drows = []
    if a.derive_pq:
        dpq, dby = load_pq(a.derive_pq)
        drows = dpq["rows"]
        derive = agg([dby[i] for i in sorted(dby)])
        derive["engine"] = dpq["engine"]
        derive["note"] = "v2 草案题；gold=每题主源（srcs[0]），不进主指标"

    rep = {
        "meta": {
            "engine": pq["engine"],
            "knowledge": pq["knowledge"],
            "topk": pq["topk"],
            "frozen_questions": len(by_id),
            "note": "subset 指标只回答「推导型题能不能被检索到」，不替代主指标",
        },
        "formula": formula,
        "by_source_kind": {
            k: agg([by_id[i] for i in sorted(kinds) if kinds[i] == k and i in by_id])
            for k in ("源码", "公式", "数据表", "实测")
        },
    }
    if derive:
        fh = sum(by_id[i]["hit"] for i in formula_ids)
        dh = sum(r["hit"] for r in drows)
        rep["derive"] = derive
        rep["combined"] = {
            "n": formula["n"] + derive["n"],
            "formula_part": formula["n"], "derive_part": derive["n"],
            "hit@6_weighted": round((fh + dh) / max(formula["n"] + derive["n"], 1), 3),
            "note": "两段语料快照不同（冻结题跑 knowledge/，derive 跑 kb-stage），仅作量级参考",
        }

    if a.out:
        Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"engine   : {rep['meta']['engine']}")
    print(f"formula  : n={formula['n']:>3}  cov={formula['coverage']:.0%}  hit@6={formula['hit@6']:.1%}  mrr={formula['mrr@6']:.3f}  strong@6={formula['strong@6']:.1%}")
    for k, v in rep["by_source_kind"].items():
        if v["n"]:
            print(f"  {k:<5}: n={v['n']:>3}  hit@6={v['hit@6']:.1%}  cov={v['coverage']:.0%}")
    if derive:
        print(f"derive   : n={derive['n']:>3}  cov={derive['coverage']:.0%}  hit@6={derive['hit@6']:.1%}  (v2 草案)")
        print(f"combined : n={rep['combined']['n']:>3}  hit@6(加权)={rep['combined']['hit@6_weighted']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
