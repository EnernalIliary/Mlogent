#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Benchmark runner: 用 300 题（questions.jsonl）评估 knowledge/ 的可检索性。

两种引擎
--------
kb       : 复用仓库 tools/kb.py 的混合检索（dense bge-small-zh + FTS5 BM25 + RRF）。
           需要 out/_kb/kb.sqlite3 与 out/_kblibs / out/_kbmodels（缺失会自动回退 lexical）。
lexical  : 纯标准库 BM25（ASCII 词 + 中文二元组），只索引 knowledge/**/*.md
           与 00-data 下的 JSON，零依赖，可在任何机器上重跑。

评分口径
--------
每题的真源 src（如 logic/LExecutor.java:41）拆成「源文件 basename」作为 gold key
（LExecutor.java）。凡正文里出现过该 key 的文档都算「可能答得出这题」的 gold 文档。
  coverage   : 有 gold 文档的题占比（= KB 对真源的引用覆盖率；没引用的题算 KB 缺口）
  hit@k      : top-k 里命中任一 gold 文档
  mrr@k      : 首个命中位次的倒数均值
  strong@k   : top-k 里命中的文档同时含「文件:行号」完整锚点（仅 src 带行号时统计）
bench 目录自身（questions.jsonl / _gen_*.py）与 _raw/_kb/_report/__pycache__ 不入库，
避免题目文本把答案泄漏进索引。

用法
----
  python eval_kb.py                       # 自动选引擎，跑全部 300 题
  python eval_kb.py --engine lexical -k 5
  python eval_kb.py --limit 40 --out report.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXCLUDE_DIRS = {"_kb", "_raw", "_report", "_kb_build", "__pycache__", "bench", ".git"}


# ---------------------------------------------------------------- 语料
def iter_docs(kb: Path):
    """knowledge 下参与评测的文档：(相对路径, 文本)。排除评测目录与缓存目录。"""
    for p in sorted(kb.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(kb)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if p.suffix.lower() not in (".md", ".json", ".jsonl", ".py", ".txt"):
            continue
        if p.name.startswith("_") or p.name == "questions.jsonl":
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        yield str(rel).replace("\\", "/"), txt


def split_chunks(rel: str, text: str, max_chars: int = 1800):
    """md 按 H2 切；其他文本按固定窗口切。"""
    if rel.endswith(".md"):
        parts = re.split(r"(?m)^##\s+", text)
        head = parts[0]
        out = [head] + ["## " + x for x in parts[1:]]
    else:
        out = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    return [c for c in out if c.strip()]


_TOKEN_ASCII = re.compile(r"[A-Za-z_][A-Za-z0-9_.:\-]{1,63}")
_TOKEN_NUM = re.compile(r"\d+(?:\.\d+)?")
_CJK = re.compile(r"[\u4e00-\u9fff]+")


def tokens(s: str):
    low = s.lower()
    out = [m.group(0).lower() for m in _TOKEN_ASCII.finditer(low)]
    out += _TOKEN_NUM.findall(low)
    for run in _CJK.findall(low):
        out += [run[i:i + 2] for i in range(len(run) - 1)]
        out += list(run)          # 单字也进，短查询兜底
    return out


class BM25:
    def __init__(self, docs, k1=1.2, b=0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.tf = []
        self.df = Counter()
        self.len = []
        for text in docs:
            c = Counter(tokens(text))
            self.tf.append(c)
            self.len.append(sum(c.values()))
            for t in c:
                self.df[t] += 1
        self.N = len(docs)
        self.avg = sum(self.len) / max(self.N, 1)

    def score(self, q: str, limit: int):
        qs = [t for t in tokens(q) if t in self.df]
        if not qs:
            return []
        qs = list(dict.fromkeys(qs))
        idf = {t: math.log(1 + (self.N - self.df[t] + 0.5) / (self.df[t] + 0.5)) for t in qs}
        res = []
        for i, c in enumerate(self.tf):
            s = 0.0
            for t in qs:
                f = c.get(t, 0)
                if not f:
                    continue
                s += idf[t] * f * (self.k1 + 1) / (
                    f + self.k1 * (1 - self.b + self.b * self.len[i] / max(self.avg, 1)))
            if s > 0:
                res.append((i, s))
        res.sort(key=lambda x: -x[1])
        return res[:limit]


# ---------------------------------------------------------------- 引擎
def engine_lexical(kb: Path, topk: int):
    docs, metas = [], []
    for rel, text in iter_docs(kb):
        for ch in split_chunks(rel, text):
            docs.append(ch)
            metas.append(rel)
    index = BM25(docs)

    def search(q: str, k: int):
        return [{"path": metas[i], "text": docs[i], "score": round(s, 4)}
                for i, s in index.score(q, k)]

    return search, f"lexical BM25 over {len(docs)} chunks / {len(set(metas))} files"


def engine_kb(root: Path, topk: int, mode: str | None = None, rerank: bool = False):
    tools_dir = root / "tools"
    if not (tools_dir / "kb.py").exists() or not (root / "out" / "_kb" / "kb.sqlite3").exists():
        return None, "kb.py 或 out/_kb/kb.sqlite3 缺失"
    sys.path.insert(0, str(tools_dir))
    os.environ.setdefault("KB_ROOT", str(root))
    os.environ.setdefault("KB_KNOWLEDGE", str(root / "knowledge"))
    if mode:
        os.environ["KB_MODE"] = mode
    try:
        import kb as K  # noqa: N812
        K.search("warmup", 1)      # 触发模型加载，失败即回退
    except Exception as exc:       # 模型/依赖缺失
        return None, f"kb 引擎不可用: {type(exc).__name__}: {exc}"

    def search(q: str, k: int):
        return K.search(q, k, rerank=rerank)

    legs = {"hybrid": "dense bge-small-zh + FTS5 BM25 + RRF",
            "dense": "dense bge-small-zh only",
            "sparse": "FTS5 BM25 only"}.get(K.MODE, K.MODE)
    return search, "kb.py %s%s" % (legs, " + rerank" if rerank else "")


# ---------------------------------------------------------------- 真源 → gold
def src_parts(src: str):
    """'logic/LExecutor.java:41-48' → ('LExecutor.java', 'LExecutor.java:41', None)
    'tools/block_attrs.json#build' → ('block_attrs.json', None, 'build')
    """
    frag = None
    if "#" in src:
        src, frag = src.split("#", 1)
    m = re.match(r"^(.*?)(?::(\d+)(?:-(\d+))?)?$", src)
    path, l1, l2 = m.group(1), m.group(2), m.group(3)
    name = Path(path).name
    anchor = f"{name}:{l1}" if l1 else None
    return name, anchor, (l1, l2, frag)


def norm(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Benchmark the mlog knowledge base")
    _q_default = HERE.parent / "08-evidence" / "bench" / "questions.jsonl"
    if not _q_default.exists():
        _q_default = HERE / "questions.jsonl"
    ap.add_argument("--questions", default=str(_q_default))
    ap.add_argument("--kb", default=None, help="knowledge 根（默认 <root>/knowledge）")
    ap.add_argument("--root", default=None, help="仓库根（含 knowledge/ tools/ out/）")
    ap.add_argument("--engine", choices=["auto", "kb", "lexical"], default="auto")
    ap.add_argument("--mode", choices=["hybrid", "dense", "sparse"], default=None,
                    help="kb engine leg; sparse never loads a model")
    ap.add_argument("--rerank", action="store_true",
                    help="cross-encoder rerank of the fused candidate list")
    ap.add_argument("-k", "--topk", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 题（调试用）")
    ap.add_argument("--out", default=None, help="JSON 报告落盘路径")
    ap.add_argument("--per-question", default=None, help="逐题命中明细（JSON）落盘路径，供子集分析用")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    root = Path(a.root) if a.root else (HERE.parents[2] if len(HERE.parents) > 2 else HERE)
    kb = Path(a.kb) if a.kb else root / "knowledge"
    qpath = Path(a.questions)
    if not qpath.exists():
        print(f"questions not found: {qpath}", file=sys.stderr)
        return 2
    if not kb.exists():
        print(f"knowledge dir not found: {kb}", file=sys.stderr)
        return 2

    rows = [json.loads(l) for l in qpath.open(encoding="utf-8") if l.strip()]
    if a.limit:
        rows = rows[:a.limit]

    search = None
    engine_note = ""
    if a.engine in ("auto", "kb"):
        search, engine_note = engine_kb(root, a.topk, mode=a.mode, rerank=a.rerank)
        if search is None and a.engine == "kb":
            print(f"kb engine unavailable: {engine_note}", file=sys.stderr)
            return 3
    if search is None:
        search, engine_note = engine_lexical(kb, a.topk)

    # 文档文本（用于判定 gold 与 strong）
    docs = {rel: txt for rel, txt in iter_docs(kb)}
    if not docs:
        print(f"no documents indexed under {kb}", file=sys.stderr)
        return 2

    per_domain = defaultdict(lambda: {"n": 0, "cov": 0, "hit1": 0, "hitk": 0, "rr": 0.0,
                                      "strong": 0, "strong_n": 0, "ndcg": 0.0,
                                      "ms": 0.0, "chars": 0, "queries": 0})
    gaps, misses = [], []
    per_q = []
    for r in rows:
        name, anchor, (l1, l2, frag) = src_parts(r["src"])
        gold = [rel for rel, txt in docs.items() if name in txt]
        d = per_domain[r["domain"]]
        d["n"] += 1
        if not gold:
            gaps.append({"id": r["id"], "domain": r["domain"], "src": r["src"],
                         "note": "knowledge 全库未出现该源文件名"})
            per_q.append({"id": r["id"], "domain": r["domain"], "type": r.get("type"),
                          "src": r["src"], "covered": 0, "rank": None, "hit": 0, "strong": 0,
                          "n_gold": 0, "top1": None, "top": []})
            d["cov"] += 0
            continue
        d["cov"] += 1
        _t0 = time.perf_counter()
        res = search(r["q"].split("\n")[0], a.topk)
        d["ms"] += (time.perf_counter() - _t0) * 1000.0
        d["chars"] += sum(len(x.get("text") or "") for x in res)
        d["queries"] += 1
        paths = [norm(x["path"]) for x in res]
        rank = next((i for i, p in enumerate(paths) if any(p.endswith(g) for g in gold)), None)
        has_anchor = anchor is not None and any(anchor in docs[g] for g in gold)
        if has_anchor:
            d["strong_n"] += 1
        if rank is not None:
            d["hitk"] += 1
            d["rr"] += 1.0 / (rank + 1)
            if rank == 0:
                d["hit1"] += 1
            d["ndcg"] += 1.0 / math.log2(rank + 2)
            if has_anchor:
                d["strong"] += 1
        else:
            misses.append({"id": r["id"], "domain": r["domain"], "src": r["src"],
                           "q": r["q"].split("\n")[0][:70], "top": paths[:3]})
        per_q.append({"id": r["id"], "domain": r["domain"], "type": r.get("type"),
                      "src": r["src"], "covered": 1, "rank": rank,
                      "hit": int(rank is not None), "strong": int(rank is not None and has_anchor),
                      "n_gold": len(gold), "top1": (paths[0] if paths else None),
                      "top": paths[:a.topk]})

    n = len(rows)
    cov = sum(v["cov"] for v in per_domain.values())
    hit1 = sum(v["hit1"] for v in per_domain.values())
    hitk = sum(v["hitk"] for v in per_domain.values())
    strong = sum(v["strong"] for v in per_domain.values())
    strong_n = sum(v["strong_n"] for v in per_domain.values())
    rr = sum(v["rr"] for v in per_domain.values())
    ms = sum(v["ms"] for v in per_domain.values())
    chars = sum(v["chars"] for v in per_domain.values())
    queries = sum(v["queries"] for v in per_domain.values())
    ndcg = sum(v["ndcg"] for v in per_domain.values())
    rep = {
        "engine": engine_note,
        "ms_per_query": round(ms / max(queries, 1), 2),
        "chars_per_query": round(chars / max(queries, 1), 1),
        "ndcg@k": round(ndcg / max(cov, 1), 4),
        "knowledge": str(kb),
        "questions": len(rows),
        "topk": a.topk,
        "coverage": round(cov / max(n, 1), 4),
        "hit@1": round(hit1 / max(cov, 1), 4),
        "hit@k": round(hitk / max(cov, 1), 4),
        "mrr@k": round(rr / max(cov, 1), 4),
        "strong@k": round(strong / max(strong_n, 1), 4),
        "domains": {k: {"n": v["n"], "coverage": round(v["cov"] / max(v["n"], 1), 3),
                        "hit@1": round(v["hit1"] / max(v["cov"], 1), 3),
                        "hit@k": round(v["hitk"] / max(v["cov"], 1), 3),
                        "mrr@k": round(v["rr"] / max(v["cov"], 1), 3),
                        "strong@k": round(v["strong"] / max(v["strong_n"], 1), 3)}
                    for k, v in sorted(per_domain.items())},
        "gaps": gaps,
        "misses": misses[:50],
    }
    if a.out:
        Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.per_question:
        Path(a.per_question).write_text(
            json.dumps({"engine": engine_note, "knowledge": str(kb), "topk": a.topk,
                        "rows": per_q}, ensure_ascii=False, indent=1), encoding="utf-8")

    if not a.quiet:
        print(f"engine   : {rep['engine']}")
        print(f"knowledge: {rep['knowledge']}  ({len(docs)} files)")
        print(f"questions: {rep['questions']}   topk={a.topk}")
        print(f"coverage : {rep['coverage']:.1%}   hit@1={rep['hit@1']:.1%}   "
              f"hit@{a.topk}={rep['hit@k']:.1%}   mrr={rep['mrr@k']:.3f}   "
              f"strong@{a.topk}={rep['strong@k']:.1%}")
        print("")
        print(f"{'domain':<14}{'n':>4}{'cover':>8}{'hit@1':>8}{'hit@k':>8}{'mrr':>7}{'strong':>8}")
        for k, v in rep["domains"].items():
            print(f"{k:<14}{v['n']:>4}{v['coverage']:>8.0%}{v['hit@1']:>8.0%}"
                  f"{v['hit@k']:>8.0%}{v['mrr@k']:>7.2f}{v['strong@k']:>8.0%}")
        if gaps:
            print(f"\nKB 缺口（{len(gaps)} 题：全库没出现过其源文件名）:")
            for g in gaps[:15]:
                print(f"  {g['id']} {g['domain']:<12} {g['src']}")
        if misses:
            print(f"\n未命中样例（{len(misses)} 题）:")
            for m in misses[:10]:
                print(f"  {m['id']} {m['domain']:<12} {m['q']}  → {m['top']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
