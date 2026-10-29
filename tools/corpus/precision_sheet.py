"""precision_sheet.py -- turn rule hits into a sample sheet a human can judge.

WHY: 规则精度不能靠脚本自证。本脚本只做两件机器擅长的事：把命中按规则分组、
     给每条样本附上能一眼判读的旁证（名字在程序里出现几次 / 有没有被赋值 / 是不是本蓝图的链接名），
     然后把「这条算不算误报」留空交人填。
WHAT: 对语料目录里每个程序跑 mlogcheck.analyse，按 rule id 收集至多 --per-rule 条样本，
      输出 markdown（顶部汇总表 + 每条规则一节，节末 `判读（待填）`）+ JSON。
用法:
  python tools/corpus/precision_sheet.py --corpus logic-corpus --procs _procs --label blueprint
  python tools/corpus/precision_sheet.py --corpus C:/Users/lliary/mlog-corpus/anon-corpus --procs _procs --label anon --stride 8 --jobs 12
  # 判读结果回填后，用 --verdicts 指向一个 {rid: "TP"|"FP"|"mixed"} 的 JSON，脚本会把结论算成比例
"""
import argparse, collections, json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mlogcheck  # noqa: E402

BT = chr(96)
NAME_RE = re.compile(BT + "([^" + BT + "]+)" + BT)
WRITE2 = {"set", "op", "read", "sensor", "getlink", "radar", "uradar", "lookup", "packcolor", "fetch"}


def _facts(name, lines, links, toks):
    """机器旁证：名字出现次数 / 是否被赋值 / 是否在本程序的链接表里。"""
    if not name:
        return {}
    occ = toks.get(name, 0)
    assigned = False
    for ln in lines:
        t = ln.split()
        if not t:
            continue
        head = t[0].lower()
        if head == "op" and len(t) > 2 and t[2] == name:
            assigned = True
            break
        if head in WRITE2 and len(t) > 1 and t[1] == name:
            assigned = True
            break
    return {"name": name, "occ": occ, "assigned": assigned, "in_links": name in links}


def _work(job):
    sha, path, links, want = job
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except Exception:
        return sha, None
    try:
        fs = mlogcheck.analyse(lines, links=links)
    except Exception as e:
        return sha, ("ERR", repr(e)[:120])
    toks = collections.Counter()
    for ln in lines:
        for t in ln.split():
            toks[t] += 1
    out = []
    for f in fs:
        rid = getattr(f, "rid", None) or "(no-id)"
        if rid not in want:
            continue
        ln = getattr(f, "line", 0) or 0
        code = (lines[ln] if 0 <= ln < len(lines) else "")[:160]
        msg = getattr(f, "msg", "") or ""
        m = NAME_RE.search(msg)
        out.append([rid, getattr(f, "sev", "?"), ln, code, msg[:240],
                    _facts(m.group(1) if m else "", lines, links, toks), len(lines), len(links)])
    return sha, out
def _rule_table():
    """rules/*.json -> {id: {severity, kind, why}}。"""
    out = {}
    d = os.path.join(ROOT, "rules")
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        try:
            r = json.load(open(os.path.join(d, fn), encoding="utf-8"))
        except Exception:
            continue
        rid = r.get("id") or fn[:-5]
        out[rid] = {"severity": r.get("severity") or r.get("sev") or "?",
                    "kind": r.get("kind") or "", "why": (r.get("why") or "").strip()}
    return out


def _cell(s, n=180):
    """表格单元：竖线转实体、空白折叠、截断。"""
    s = (s or "").replace("|", "&#124;")
    s = re.sub("\\s+", " ", s)
    return s[:n]


def _markdown(data, table, verdicts):
    B = BT
    L = []
    L.append("# 规则精度判读表 · " + data["label"])
    L.append("")
    L.append("语料 " + B + data["corpus"] + B + "（%d 个程序，本次跑 %d 个%s），%s 生成，耗时 %.1f s，分析异常 %d。" % (
        data["corpus_total"], data["programs"],
        "" if data["programs"] == data["corpus_total"] else "，stride=%d" % data["stride"],
        data["generated_at"], data["secs"], data["errors"]))
    L.append("")
    L.append("判读方法：每条规则看下面几条样本的「代码」和「机器旁证」，在节末的 " + B + "判读（待填）" + B +
             " 里写 **TP**（分析器说得对）/ **FP**（这条是误报）/ **mixed**（同一规则两种都有）。"
             "旁证含义：" + B + "occ" + B + "=这个名字在程序里出现几次；" + B + "assigned" + B +
             "=程序有没有给它赋值；" + B + "in_links" + B + "=它是不是本蓝图里声明的链接名。")
    L.append("")
    L.append("## 0. 汇总")
    L.append("")
    L.append("| 规则 | 严重度 | 命中 | 程序 | 程序占比 | 判读 |")
    L.append("|---|---|---|---|---|---|")
    for rid, c in sorted(data["hits"].items(), key=lambda kv: -kv[1]):
        L.append("| " + B + rid + B + " | %s | %d | %d | %.1f%% | %s |" % (
            table.get(rid, {}).get("severity", "?"), c, data["programs_per_rule"].get(rid, 0),
            100.0 * data["programs_per_rule"].get(rid, 0) / max(1, data["programs"]),
            verdicts.get(rid, "")))
    L.append("")
    for rid, c in sorted(data["hits"].items(), key=lambda kv: -kv[1]):
        t = table.get(rid, {})
        L.append("## " + B + rid + B + " — %s，%d 条 / %d 个程序" % (
            t.get("severity", "?"), c, data["programs_per_rule"].get(rid, 0)))
        L.append("")
        if t.get("kind"):
            L.append("kind=" + B + t["kind"] + B + "。")
            L.append("")
        if t.get("why"):
            why = re.sub("\\s+", " ", t["why"])
            L.append("> 规则自述：" + (why[:400] + ("…" if len(why) > 400 else "")))
            L.append("")
        L.append("| # | 程序 | 行 | 代码 | 旁证 | 分析器说法 |")
        L.append("|---|---|---|---|---|---|")
        for i, s in enumerate(data["samples"].get(rid, []), 1):
            fa = s.get("facts") or {}
            if fa.get("name"):
                facts = B + fa["name"] + B + " occ=%d assigned=%s in_links=%s" % (
                    fa["occ"], "yes" if fa["assigned"] else "no", "yes" if fa["in_links"] else "no")
            else:
                facts = "lines=%d links=%d" % (s.get("lines", 0), s.get("links", 0))
            L.append("| %d | " % i + B + s["sha"] + B + " | %d | " % (s["line"] + 1) + B +
                     _cell(s.get("code")) + B + " | " + facts + " | " + _cell(s.get("msg")) + " |")
        L.append("")
        L.append("**判读（待填）**：" + verdicts.get(rid, ""))
        L.append("")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--procs", default="_procs")
    ap.add_argument("--label", required=True, help="产物名标签，如 blueprint / maps / anon")
    ap.add_argument("--per-rule", type=int, default=6, help="每条规则收多少条样本")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", default="")
    ap.add_argument("--md", default="")
    ap.add_argument("--verdicts", default="", help="JSON {rid: TP|FP|mixed}，回填判读结论")
    a = ap.parse_args(argv)
    progs = json.load(open(os.path.join(a.corpus, a.procs, "_meta.json"), encoding="utf-8"))["programs"]
    jobs = [(sha, os.path.join(a.corpus, a.procs, sha + ".mlog"), list(rec.get("link_names") or []))
            for sha, rec in sorted(progs.items())]
    if a.stride > 1:
        jobs = jobs[::a.stride]
    if a.limit:
        jobs = jobs[:a.limit]
    want = set(_rule_table().keys())
    jobs = [(sha, p, l, want) for sha, p, l in jobs]

    hits = collections.Counter()
    prog_of = collections.defaultdict(set)
    sev_of = collections.defaultdict(collections.Counter)
    samples = collections.defaultdict(list)
    errors = 0
    t0 = time.time()
    pool = None
    if a.jobs > 1:
        import multiprocessing as mp
        pool = mp.get_context("spawn").Pool(a.jobs)
        it = pool.imap_unordered(_work, jobs, chunksize=16)
    else:
        it = map(_work, jobs)
    for sha, res in it:
        if res is None or (isinstance(res, tuple) and res and res[0] == "ERR"):
            errors += 1
            continue
        for rid, sev, ln, code, msg, facts, nlines, nlinks in res:
            hits[rid] += 1
            sev_of[rid][sev] += 1
            prog_of[rid].add(sha)
            if len(samples[rid]) < a.per_rule and all(s["sha"] != sha for s in samples[rid]):
                samples[rid].append({"sha": sha, "line": ln, "code": code, "msg": msg,
                                     "facts": facts, "lines": nlines, "links": nlinks})
    if pool is not None:
        pool.close()
        pool.join()
    dt = time.time() - t0

    table = _rule_table()
    verdicts = json.load(open(a.verdicts, encoding="utf-8")) if a.verdicts else {}
    n = len(jobs)
    data = {"corpus": os.path.abspath(a.corpus), "label": a.label,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "programs": n, "corpus_total": len(progs), "stride": a.stride, "limit": a.limit,
            "secs": round(dt, 1), "errors": errors, "findings": sum(hits.values()),
            "hits": dict(hits), "programs_per_rule": {k: len(v) for k, v in prog_of.items()},
            "sev": {k: dict(v) for k, v in sev_of.items()}, "samples": samples}
    jp = a.json or os.path.join(ROOT, "out", "_crawl", "precision-%s.json" % a.label)
    os.makedirs(os.path.dirname(jp), exist_ok=True)
    json.dump(data, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    mdp = a.md or os.path.join(ROOT, "out", "_crawl", "precision-%s.md" % a.label)
    open(mdp, "w", encoding="utf-8", newline="").write(_markdown(data, table, verdicts))
    print("programs %d (%d of %d)  findings %d  rules fired %d  %.1f s  errors %d" % (
        n, n, len(progs), sum(hits.values()), len(hits), dt, errors))
    for rid, c in hits.most_common():
        print("  %-42s %5d hits / %4d progs  %s" % (rid, c, len(prog_of[rid]), dict(sev_of[rid])))
    print("wrote " + os.path.relpath(jp, ROOT))
    print("wrote " + os.path.relpath(mdp, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
