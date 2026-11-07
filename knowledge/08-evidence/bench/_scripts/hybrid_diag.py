# -*- coding: utf-8 -*-
"""hybrid 诊断：拆开「宽文档/代码库污染」与「检索器本身不行」两件事。

kb.py 返回的是 **chunk** 级结果（同一个文件的多个 chunk 会各占一个 top 槽），而本评测的
gold 只认 knowledge/ 里的文章。于是同一份 top-k 有四种读法：

  as-is          原样（= eval_kb.py 的官方口径）
  dedup          按文件去重后再排（一个文件只占一个槽）
  restricted     只保留 knowledge/ 内的文件（剔掉 tools/、docs/、mindustry-blueprint/ 等）
  dedup+restr    两者都做

差值回答两个问题：污染占了多少分（as-is → restricted）、chunk 重复占了多少分（as-is → dedup）。

用法：
  python hybrid_diag.py --pq tmp_hybrid_k20_pq.json --questions questions.jsonl \
      --kb <repo>/knowledge --out hybrid_diag.json [--inside-prefix knowledge/]
注意 --pq 的 k 建议 ≥ 10：restricted/dedup 后的名次会被压缩，k=6 看不出污染的真实大小。
"""
import argparse, collections, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CUTS = (1, 3, 6, 10)


def basename_of_src(src):
    s = src.split("#")[0]
    for sep in ("\\", "/"):
        s = s.rsplit(sep, 1)[-1]
    return s.split(":")[0].strip()


def load_docs(kb: Path):
    texts = {}
    for f in sorted(kb.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in (".md", ".json", ".txt", ".jsonl"):
            continue
        rel = f.relative_to(kb)
        if any(p.startswith("_") or p == "bench" for p in rel.parts):
            continue
        try:
            texts[rel.as_posix()] = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    return texts


def dedup(paths):
    seen, out = set(), []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def first_rank(paths, gold_docs):
    for i, p in enumerate(paths):
        if any(p.endswith(g) for g in gold_docs):
            return i
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pq", required=True)
    ap.add_argument("--questions", default=str(HERE / "questions.jsonl"))
    ap.add_argument("--kb", required=True, help="knowledge 目录（按正文判定 gold，与 eval_kb.py 同口径）")
    ap.add_argument("--inside-prefix", default="knowledge/")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    d = json.loads(Path(a.pq).read_text(encoding="utf-8"))
    rows = d["rows"]
    qs = {json.loads(l)["id"]: json.loads(l) for l in Path(a.questions).open(encoding="utf-8") if l.strip()}
    texts = load_docs(Path(a.kb))
    gold = {qid: [rel for rel, t in texts.items() if basename_of_src(q["src"]) in t] for qid, q in qs.items()}
    doms = {qid: q["domain"] for qid, q in qs.items()}
    pre = a.inside_prefix

    stats = {k: {c: 0 for c in CUTS} for k in ("as_is", "dedup", "restricted", "dedup_restricted")}
    dom = collections.defaultdict(lambda: {k: {c: 0 for c in CUTS} for k in ("as_is", "dedup_restricted")})
    outside = collections.Counter()
    slots = outside_slots = 0
    distinct = []
    n = 0
    miss_detail = []
    for r in rows:
        qid = r["id"]
        gd = gold.get(qid) or []
        top = r.get("top") or ([r["top1"]] if r.get("top1") else [])
        u = dedup(top)
        ins = [p for p in u if p.startswith(pre)]
        n += 1
        slots += len(top)
        out = [p for p in top if not p.startswith(pre)]
        outside_slots += len(out)
        for p in out:
            outside[p] += 1
        distinct.append(len(dedup(top[:6])))
        ranks = {"as_is": first_rank(top, gd), "dedup": first_rank(u, gd),
                 "restricted": first_rank([p for p in top if p.startswith(pre)], gd),
                 "dedup_restricted": first_rank(ins, gd)}
        for k, rk in ranks.items():
            for c in CUTS:
                if rk is not None and rk < c:
                    stats[k][c] += 1
        for c in CUTS:
            if ranks["as_is"] is not None and ranks["as_is"] < c:
                dom[doms.get(qid, "?")]["as_is"][c] += 1
            if ranks["dedup_restricted"] is not None and ranks["dedup_restricted"] < c:
                dom[doms.get(qid, "?")]["dedup_restricted"][c] += 1
        if ranks["dedup_restricted"] is None:
            miss_detail.append({"id": qid, "domain": doms.get(qid), "gold": gd[:3],
                                "top": [p.split("/")[-1] for p in u[:6]]})

    rep = {
        "engine": d.get("engine"),
        "questions": n,
        "topk_of_pq": max((len(r.get("top") or []) for r in rows), default=0),
        "hit_by_cutoff": {k: {str(c): round(v[c] / max(n, 1), 4) for c in CUTS} for k, v in stats.items()},
        "chunk_duplication": {
            "questions_with_dup_in_top6": sum(1 for r in rows if len(dedup((r.get("top") or [])[:6])) < len((r.get("top") or [])[:6])),
            "mean_distinct_docs_in_top6": round(sum(distinct) / max(n, 1), 2),
        },
        "outside_knowledge": {
            "topk_slots": slots,
            "outside_slots": outside_slots,
            "outside_slot_share": round(outside_slots / max(slots, 1), 4),
            "top_outside_docs": outside.most_common(12),
        },
        "domains": {k: {kk: {str(c): round(vv[c] / 25, 3) for c in CUTS} for kk, vv in v.items()}
                    for k, v in sorted(dom.items())},
        "dedup_restricted_misses": miss_detail,
    }
    if a.out:
        Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"engine  : {rep['engine']}   (pq k={rep['topk_of_pq']})")
    print(f"{'读法':<18}" + "".join(f"{('hit@' + str(c)):>9}" for c in CUTS))
    names = {"as_is": "as-is（官方口径）", "dedup": "按文件去重", "restricted": "只留 knowledge/", "dedup_restricted": "去重 + 只留 knowledge/"}
    for k, label in names.items():
        print(f"{label:<18}" + "".join(f"{rep['hit_by_cutoff'][k][str(c)]:>8.1%}" for c in CUTS))
    cd = rep["chunk_duplication"]
    print(f"\nchunk 重复：top6 内有重复文件的题 {cd['questions_with_dup_in_top6']}/{n}，"
          f"top6 平均不同文件数 {cd['mean_distinct_docs_in_top6']}")
    o = rep["outside_knowledge"]
    print(f"knowledge 外占用：{o['outside_slots']}/{o['topk_slots']} 槽 = {o['outside_slot_share']:.1%}")
    print("最占位的库外文档：" + ", ".join(f"{p}({c})" for p, c in o["top_outside_docs"][:6]))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
