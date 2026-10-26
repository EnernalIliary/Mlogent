
"""classify_schematics.py -- decode downloaded .msch packs and extract every logic program.

WHY: fetch_schematics.py 只拿到二进制蓝图；规则精度需要的是「程序文本」+「它来自哪个蓝图/哪个方块」，
     这样才能在第三方语料上跑 mlogcheck 并与本地 1421 存档的结果对照。
WHAT: 解析 logic-corpus/ 下全部 .msch，把去重后的逻辑源码写到 logic-corpus/_procs/<sha1>.mlog，
      并写 _procs/_meta.json（每个程序的来源、方块类型、行数、链接数）。
HOW:  用仓库自己的 tools/msch.py（与 mlog.py 同一个解析器），不引入新依赖。

用法:
  python tools/dev/classify_schematics.py [--dest logic-corpus]
"""
import argparse, hashlib, json, os, sys, time, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import msch  # noqa: E402

LOGIC_BLOCKS = ("micro-processor", "logic-processor", "hyper-processor", "memory-cell", "memory-bank")

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=os.path.join(ROOT, "logic-corpus"))
    a = ap.parse_args(argv)
    src = a.dest
    files = []
    for dirpath, dirnames, filenames in os.walk(src):
        if os.path.basename(dirpath).startswith("_"):
            continue
        for fn in filenames:
            if fn.lower().endswith(".msch"):
                files.append(os.path.join(dirpath, fn))
    files.sort()
    outdir = os.path.join(src, "_procs")
    os.makedirs(outdir, exist_ok=True)
    progs, unreadable, no_logic, tiles_total = {}, [], 0, 0
    for path in files:
        rel = os.path.relpath(path, src)
        try:
            sch = msch.parse_file(path)
        except Exception as e:
            unreadable.append([rel, "%s: %s" % (type(e).__name__, str(e)[:120])])
            continue
        lt = sch.logic_tiles()
        tiles_total += len(lt)
        if not lt:
            no_logic += 1
            continue
        labels = list(sch.labels or [])
        blocks = sorted(set(t.block for t in sch.tiles))
        for t in lt:
            stmts = t.logic.statement_lines()
            if not stmts:
                continue
            code = "\n".join(stmts)
            h = hashlib.sha1(code.encode("utf-8")).hexdigest()[:16]
            rec = progs.get(h)
            if rec is None:
                progs[h] = {"sha": h, "block": t.block, "lines": len(stmts),
                            "links": len(t.logic.links),
                            "link_names": [lk.name for lk in t.logic.links],
                            "labels": labels, "blocks": blocks,
                            "sources": [rel], "code": code}
            else:
                if rel not in rec["sources"]:
                    rec["sources"].append(rel)
                for lb in labels:
                    if lb not in rec["labels"]:
                        rec["labels"].append(lb)
                for bk in blocks:
                    if bk not in rec["blocks"]:
                        rec["blocks"].append(bk)
    for h, rec in progs.items():
        with open(os.path.join(outdir, h + ".mlog"), "w", encoding="utf-8", newline="\n") as f:
            f.write(rec["code"] + "\n")
    meta = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "schematic_files": len(files),
            "unreadable": unreadable, "schematic_without_logic": no_logic,
            "logic_tiles": tiles_total, "unique_programs": len(progs),
            "programs": {h: {k: v for k, v in rec.items() if k != "code"} for h, rec in progs.items()}}
    with open(os.path.join(outdir, "_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    by_block = collections.Counter(rec["block"] for rec in progs.values())
    by_lines = collections.Counter()
    for rec in progs.values():
        n = rec["lines"]
        by_lines[("1-9" if n < 10 else "10-49" if n < 50 else "50-199" if n < 200 else "200+")] += 1
    total_lines = sum(rec["lines"] for rec in progs.values())
    print("schematic files : %d" % len(files))
    print("unreadable      : %d" % len(unreadable))
    print("no logic        : %d" % no_logic)
    print("logic tiles     : %d" % tiles_total)
    print("unique programs : %d (%d lines)" % (len(progs), total_lines))
    print("by block        : %s" % dict(by_block.most_common()))
    print("by size         : %s" % {k: by_lines[k] for k in ("1-9", "10-49", "50-199", "200+")})
    withl = sum(1 for rec in progs.values() if rec["links"])
    print("with links      : %d / %d" % (withl, len(progs)))
    print("dupe sources    : %d program(s) appear in >1 schematic file" % sum(1 for rec in progs.values() if len(rec["sources"]) > 1))
    if unreadable:
        print("first unreadable: %s" % unreadable[0])
    return 0 if progs else 3

if __name__ == "__main__":
    sys.exit(main())
