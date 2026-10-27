"""check_corpus.py -- run the rule engine over an extracted third-party logic corpus.

WHY: 规则精度要么在本地 1421 个存档上量（on-device，会漏掉社区写法），要么在外部蓝图上量。
     本脚本给出后者：每一条 rules/*.json 在 logic-corpus/_procs/ 里命中多少程序、多少条。
WHAT: 对每个程序跑 mlogcheck.analyse（带上蓝图里声明的链接名），按 rule id 聚合；输出表格 + JSON。
用法:
  python tools/corpus/check_corpus.py [--corpus logic-corpus] [--procs _procs] [--jobs 8]
  # 大语料（4 万程序 / 3 千万行）单线程要 ~20 min，--jobs 16 实测 ~2 min；默认 --jobs 1 保持旧行为。
"""
import argparse, collections, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mlogcheck  # noqa: E402


def _work(job):
    """子进程：分析一个程序，返回 (sha, [(rid, sev, line, msg, code)])。"""
    sha, path, links = job
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except Exception:
        return sha, None
    try:
        fs = mlogcheck.analyse(lines, links=links)
    except Exception as e:
        return sha, ("ERR", repr(e)[:100])
    out = []
    for f in fs:
        ln = getattr(f, "line", 0) or 0
        out.append((getattr(f, "rid", None) or "(no-id)", getattr(f, "sev", "?"), ln,
                    (getattr(f, "msg", "") or "")[:200],
                    (lines[ln - 1] if 0 < ln <= len(lines) else "")[:160]))
    return sha, out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.join(ROOT, "logic-corpus"))
    ap.add_argument("--procs", default="_procs", help="程序目录（相对 --corpus）；蓝图包用 _procs，存档地图用 _maps_procs")
    ap.add_argument("--json", default=os.path.join(ROOT, "out", "_crawl", "check-corpus.json"))
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--jobs", type=int, default=1, help="并行进程数；1=串行（旧行为）")
    ap.add_argument("--stride", type=int, default=1, help="按排序后的程序名等间隔抽样（1=全量）")
    ap.add_argument("--limit", type=int, default=0, help="抽样后只跑前 N 个程序（0=全部）")
    ap.add_argument("--fail-on-errors", action="store_true",
                    help="analyse 抛异常时以 1 退出（gate 用；全量跑仍只看统计）")
    a = ap.parse_args(argv)
    metap = os.path.join(a.corpus, a.procs, "_meta.json")
    meta = json.load(open(metap, encoding="utf-8"))
    progs = meta["programs"]
    jobs = []
    for sha, rec in sorted(progs.items()):
        jobs.append((sha, os.path.join(a.corpus, a.procs, sha + ".mlog"), list(rec.get("link_names") or [])))
    if a.stride > 1:
        jobs = jobs[::a.stride]
    if a.limit:
        jobs = jobs[:a.limit]
    rule_n = collections.Counter()
    rule_progs = collections.Counter()
    rule_sev = {}
    sev_n = collections.Counter()
    samples = {}
    errors = 0
    t0 = time.time()
    if a.jobs > 1:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        with ctx.Pool(a.jobs) as pool:
            it = pool.imap_unordered(_work, jobs, chunksize=32)
            results = ((sha, res) for sha, res in it)
            done = _aggregate(results, progs, rule_n, rule_progs, sev_n, samples, rule_sev)
        errors = done
    else:
        def gen():
            for job in jobs:
                yield _work(job)
        errors = _aggregate(gen(), progs, rule_n, rule_progs, sev_n, samples, rule_sev)
    dt = time.time() - t0
    total = sum(rule_n.values())
    print("programs: %d   findings: %d   analyse errors: %d   %.1f s (%.1f ms/program)   jobs=%d%s" % (
        len(jobs), total, errors, dt, 1000.0 * dt / max(1, len(jobs)), a.jobs,
        "" if len(jobs) == len(progs) else "   (sampled: %d of %d)" % (len(jobs), len(progs))))
    print("severity: %s" % dict(sev_n))
    print()
    print("%-34s %6s %6s %7s  %s" % ("rule id", "hits", "progs", "progs%", "sample"))
    for rid, n in rule_n.most_common(a.top):
        s = samples.get(rid, {})
        print("%-34s %6d %6d %6.1f%%  %s" % (rid, n, rule_progs[rid], 100.0 * rule_progs[rid] / max(1, len(jobs)),
                                            (s.get("code") or "")[:60]))
    try:
        corpus_label = os.path.relpath(a.corpus, ROOT)
    except ValueError:          # 语料在工作区外的另一个盘（如 C:），relpath 会抛
        corpus_label = os.path.abspath(a.corpus)
    out = {"corpus": corpus_label, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "programs": len(jobs), "findings": total, "errors": errors, "secs": round(dt, 1), "jobs": a.jobs,
           "stride": a.stride, "limit": a.limit, "corpus_total": len(progs),
           "rule_counts": dict(rule_n), "rule_programs": dict(rule_progs), "sev_counts": dict(sev_n),
           "rule_sev": {rid: dict(v) for rid, v in rule_sev.items()},
           "samples": samples}
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwrote %s" % os.path.relpath(a.json, ROOT))
    if a.fail_on_errors and errors:
        print("FAIL: %d program(s) made the analyzer raise" % errors)
        return 1
    return 0


def _aggregate(results, progs, rule_n, rule_progs, sev_n, samples, rule_sev=None):
    """把 (sha, findings) 流汇总到 counter 里；返回错误数。"""
    errors = 0
    seen_all = set()
    for sha, fs in results:
        if fs is None:
            errors += 1
            continue
        if isinstance(fs, tuple) and fs and fs[0] == "ERR":
            errors += 1
            if errors <= 3:
                print("analyse failed on %s: %s" % (sha, fs[1]))
            continue
        seen = set()
        # 注：Finding.line 是 0-based 语句序号（与 jump N 同一坐标系），文本行号 = line + 1；
        # worker 里按 lines[ln] 取源码，别用 lines[ln-1]（那会显示上一条语句）。
        for rid, sev, ln, msg, code in fs:
            rule_n[rid] += 1
            sev_n[sev] += 1
            rule_sev.setdefault(rid, collections.Counter())[sev] += 1
            if rid not in seen:
                seen.add(rid)
                rule_progs[rid] += 1
                if rid not in samples:
                    samples[rid] = {"sha": sha, "line": ln, "msg": msg, "code": code}
    return errors


if __name__ == "__main__":
    sys.exit(main())
