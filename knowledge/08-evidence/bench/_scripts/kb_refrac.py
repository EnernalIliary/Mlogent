# -*- coding: utf-8 -*-
"""对照实验：如果不改知识库、只改「检索结果的呈现方式」，hybrid 能涨到多少？

不动仓库代码：只把 kb.py 的 top-N chunk 结果做后处理，再按 eval_kb.py 同口径评分。

四种呈现：
  as-is            原样 top-k（= 现在的口径）
  dedup            按文件去重（一个文件只占一槽）
  knowledge-only   只保留 knowledge/ 下的文件
  dedup+knowledge  两者都做

用法：
  python kb_refrac.py --root <repo> --questions questions.jsonl --kb <repo>/knowledge \
      --fetch 50 --k 6 --out refrac.json
"""
import argparse, collections, json, os, sys
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
    ap.add_argument("--root", required=True)
    ap.add_argument("--kb", required=True)
    ap.add_argument("--questions", default=str(HERE / "questions.jsonl"))
    ap.add_argument("--fetch", type=int, default=50, help="每次检索取多少个 chunk 再做后处理")
    ap.add_argument("--k", type=int, default=6, help="评测截断")
    ap.add_argument("--inside-prefix", default="knowledge/")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    root = Path(a.root)
    sys.path.insert(0, str(root / "tools"))
    os.environ.setdefault("KB_ROOT", str(root))
    os.environ.setdefault("KB_KNOWLEDGE", str(root / "knowledge"))
    import kb as K  # noqa: N812
    K.search("warmup", 1)

    qs = [json.loads(l) for l in Path(a.questions).open(encoding="utf-8") if l.strip()]
    texts = load_docs(Path(a.kb))
    pre = a.inside_prefix

    variants = ("as_is", "dedup", "knowledge_only", "dedup_knowledge")
    cnt = {v: {c: 0 for c in CUTS} for v in variants}
    strong = {v: 0 for v in variants}
    strong_n = 0
    dom = collections.defaultdict(lambda: {v: {c: 0 for c in CUTS} for v in variants})
    per_q = []
    for q in qs:
        gold = [rel for rel, t in texts.items() if basename_of_src(q["src"]) in t]
        anchor_name = basename_of_src(q["src"])
        line = None
        s = q["src"].split("#")[0]
        parts = s.rsplit(":", 1)
        if len(parts) == 2 and parts[1].split("-")[0].isdigit():
            line = parts[1].split("-")[0]
        has_anchor = bool(line) and any((anchor_name + ":" + line) in texts[g] for g in gold)
        if has_anchor:
            strong_n += 1
        res = K.search(q["q"].split("\n")[0], a.fetch)
        paths = [p.replace("\\", "/").lstrip("./") for p in (x["path"] for x in res)]
        sets = {
            "as_is": paths,
            "dedup": dedup(paths),
            "knowledge_only": [p for p in dedup(paths) if p.startswith(pre)],
            "dedup_knowledge": [p for p in dedup(paths) if p.startswith(pre)],
        }
        rank = {}
        for v in variants:
            rk = first_rank(sets[v], gold)
            rank[v] = rk
            for c in CUTS:
                if rk is not None and rk < c:
                    cnt[v][c] += 1
                    dom[q["domain"]][v][c] += 1
            if rk is not None and rk < a.k and has_anchor:
                strong[v] += 1
        per_q.append({"id": q["id"], "domain": q["domain"], "rank": rank})

    n = len(qs)
    rep = {
        "meta": {"engine": "kb.py hybrid, post-processed", "fetch": a.fetch, "k": a.k,
                 "questions": n, "knowledge": str(a.kb)},
        "variants": {v: {str(c): round(cnt[v][c] / max(n, 1), 4) for c in CUTS} | {
            "strong@%d" % a.k: round(strong[v] / max(strong_n, 1), 4)} for v in variants},
        "domains": {d: {v: {str(c): round(x[c] / 25, 3) for c in CUTS} for v, x in dv.items()}
                    for d, dv in sorted(dom.items())},
        "per_question": per_q,
    }
    if a.out:
        Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"fetch={a.fetch} k={a.k} n={n}")
    print(f"{'variant':<18}" + "".join(f"{('hit@' + str(c)):>9}" for c in CUTS) + f"{'strong':>9}")
    for v in variants:
        print(f"{v:<18}" + "".join(f"{cnt[v][c] / max(n, 1):>8.1%}" for c in CUTS)
              + f"{strong[v] / max(strong_n, 1):>8.1%}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
