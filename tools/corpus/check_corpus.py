
"""check_corpus.py -- run the rule engine over an extracted third-party logic corpus.

WHY: 规则精度要么在本地 1421 个存档上量（on-device，会漏掉社区写法），要么在外部蓝图上量。
     本脚本给出后者：每一条 rules/*.json 在 logic-corpus/_procs/ 里命中多少程序、多少条。
WHAT: 对每个程序跑 mlogcheck.analyse（带上蓝图里声明的链接名），按 rule id 聚合；输出表格 + JSON。
用法:
  python tools/dev/check_corpus.py [--corpus logic-corpus] [--json out/_crawl/check-corpus.json]
"""
import argparse, collections, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import mlogcheck  # noqa: E402

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.path.join(ROOT, "logic-corpus"))
    ap.add_argument("--procs", default="_procs", help="程序目录（相对 --corpus）；蓝图包用 _procs，存档地图用 _maps_procs")
    ap.add_argument("--json", default=os.path.join(ROOT, "out", "_crawl", "check-corpus.json"))
    ap.add_argument("--top", type=int, default=30)
    a = ap.parse_args(argv)
    metap = os.path.join(a.corpus, a.procs, "_meta.json")
    meta = json.load(open(metap, encoding="utf-8"))
    progs = meta["programs"]
    rule_n = collections.Counter()
    rule_progs = collections.Counter()
    sev_n = collections.Counter()
    samples = {}
    t0 = time.time()
    errors = 0
    for sha, rec in sorted(progs.items()):
        path = os.path.join(a.corpus, a.procs, sha + ".mlog")
        try:
            lines = open(path, encoding="utf-8").read().split("\n")
        except Exception:
            errors += 1
            continue
        try:
            fs = mlogcheck.analyse(lines, links=list(rec.get("link_names") or []))
        except Exception as e:
            errors += 1
            if errors <= 3:
                print("analyse failed on %s: %s" % (sha, repr(e)[:100]))
            continue
        seen = set()
        for f in fs:
            rid = getattr(f, "rid", None) or ("(no-id)")
            rule_n[rid] += 1
            sev_n[getattr(f, "sev", "?")] += 1
            if rid not in seen:
                seen.add(rid)
                rule_progs[rid] += 1
                if rid not in samples:
                    samples[rid] = {"sha": sha, "line": getattr(f, "line", 0),
                                    "msg": getattr(f, "msg", "")[:200],
                                    "code": (lines[getattr(f, "line", 1) - 1] if 0 < getattr(f, "line", 1) <= len(lines) else "")[:160]}
    dt = time.time() - t0
    total = sum(rule_n.values())
    print("programs: %d   findings: %d   analyse errors: %d   %.1f s (%.1f ms/program)" % (
        len(progs), total, errors, dt, 1000.0 * dt / max(1, len(progs))))
    print("severity: %s" % dict(sev_n))
    print()
    print("%-34s %6s %6s %7s  %s" % ("rule id", "hits", "progs", "progs%", "sample"))
    for rid, n in rule_n.most_common(a.top):
        s = samples.get(rid, {})
        print("%-34s %6d %6d %6.1f%%  %s" % (rid, n, rule_progs[rid], 100.0 * rule_progs[rid] / max(1, len(progs)),
                                            (s.get("code") or "")[:60]))
    out = {"corpus": os.path.relpath(a.corpus, ROOT), "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "programs": len(progs), "findings": total, "errors": errors, "secs": round(dt, 1),
           "rule_counts": dict(rule_n), "rule_programs": dict(rule_progs), "sev_counts": dict(sev_n),
           "samples": samples}
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nwrote %s" % os.path.relpath(a.json, ROOT))
    return 0

if __name__ == "__main__":
    sys.exit(main())
