#!/usr/bin/env python3
"""Opcode coverage over a real corpus.

Which instructions does the game actually use, and -- the point of this tool --
which ones never appear in a large body of real programs?  A zero-coverage
instruction is one the simulator, the checks and the runtime probes have never
been exercised against by anybody's code.

Usage:
  python tools/corpus/instr_coverage.py --src C:/Users/lliary/mlog-corpus/anon-corpus/_procs
  python tools/corpus/instr_coverage.py --src logic-corpus/_procs --md out/_crawl/cov.md

Input is a directory of .mlog files (what `classify_schematics.py` and
`extract_maps.py` write).  The canonical instruction list comes from
`tools/instr_semantics.json` (v159.3 source snapshot + `ops`).

Line conventions are the same as everywhere else in this repo: a line starting
with `#` is a comment, a single token ending with `:` is a label, everything
else is `mnemonic arg...`.
"""
import argparse
import collections
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEM = os.path.join(ROOT, "tools", "instr_semantics.json")

# A mnemonic is an ASCII identifier.  Anything else on the statement position
# is mojibake from a mis-decoded blueprint string, not an instruction.
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_canonical():
    with open(SEM, encoding="utf-8") as fh:
        d = json.load(fh)
    instr = d.get("instructions") or {}
    ops = d.get("ops") or {}
    return list(instr), list(ops), d.get("version") or ""


def scan(src, limit=0):
    files = sorted(f for f in os.listdir(src) if f.endswith(".mlog"))
    if limit:
        files = files[:limit]
    stmt = collections.Counter()
    progs = collections.defaultdict(set)
    op_hist = collections.Counter()
    op_progs = collections.defaultdict(set)
    draw_hist = collections.Counter()
    labels = 0
    total_lines = 0
    multi = 0
    junk = 0
    junk_samples = []
    t0 = time.time()
    for n, name in enumerate(files, 1):
        path = os.path.join(src, name)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for line in text.splitlines():
            total_lines += 1
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if ";" in s:
                multi += 1
            for part in s.split(";"):
                part = part.strip()
                if not part:
                    continue
                toks = part.split()
                if len(toks) == 1 and len(toks[0]) > 1 and toks[0].endswith(":"):
                    labels += 1
                    continue
                mn = toks[0]
                if not IDENT.match(mn):
                    junk += 1
                    if len(junk_samples) < 12:
                        junk_samples.append(mn[:40])
                    continue
                stmt[mn] += 1
                progs[mn].add(name)
                if mn == "op" and len(toks) >= 2:
                    op_hist[toks[1]] += 1
                    op_progs[toks[1]].add(name)
                elif mn == "draw" and len(toks) >= 2:
                    draw_hist[toks[1]] += 1
        if n % 5000 == 0:
            print("  %d/%d files  %.1f s" % (n, len(files), time.time() - t0), flush=True)
    return {
        "src": os.path.abspath(src),
        "files": len(files),
        "lines": total_lines,
        "statements": sum(stmt.values()),
        "labels": labels,
        "semicolon_lines": multi,
        "junk": junk,
        "junk_samples": junk_samples,
        "stmt": stmt,
        "progs": progs,
        "op_hist": op_hist,
        "op_progs": op_progs,
        "draw_hist": draw_hist,
        "secs": round(time.time() - t0, 1),
    }


def pct(a, b):
    return (100.0 * a / b) if b else 0.0


def report(r, canonical_instr, canonical_ops, version, top=20):
    stmt, progs = r["stmt"], r["progs"]
    n_stmt, n_files = r["statements"], r["files"]
    known = set(canonical_instr)
    unknown = sorted((k for k in stmt if k not in known and k != "op"), key=lambda k: -stmt[k])
    zero = [k for k in canonical_instr if stmt.get(k, 0) == 0]
    L = []
    L.append("# 指令覆盖率（真实语料）")
    L.append("")
    L.append("语料：`%s`  " % r["src"])
    L.append("程序 %d 个、语句 %d 条、文本行 %d 行、标签 %d 个；扫描 %.1f s。  "
             "指令表：`tools/instr_semantics.json`（%s 快照，%d 条 instruction + %d 条 op）。"
             % (n_files, n_stmt, r["lines"], r["labels"], r["secs"], version or "?",
                len(canonical_instr), len(canonical_ops)))
    L.append("")
    L.append("## 1. 零覆盖指令（真实程序里一次都没出现）")
    L.append("")
    if zero:
        L.append("| instruction | 含义 |")
        L.append("|---|---|")
        for k in zero:
            L.append("| `%s` | 语料 0 次 —— 模拟器 / 规则 / 探针都没被真实代码打到过 |" % k)
    else:
        L.append("无：所有 instruction 都至少出现过一次。")
    L.append("")
    L.append("## 2. op / draw 子命令")
    L.append("")
    zero_ops = [o for o in canonical_ops if op_hist0(r, o) == 0]
    L.append("`op` 子命令零覆盖：%s" % (", ".join("`%s`" % o for o in zero_ops) if zero_ops else "无"))
    L.append("")
    seen = sorted(r["draw_hist"], key=lambda k: -r["draw_hist"][k])
    L.append("`draw` 子命令实际出现：%s" % (", ".join("`%s`(%d)" % (k, r["draw_hist"][k]) for k in seen) or "无"))
    L.append("")
    L.append("## 3. 语料里出现、但指令表不认识的首 token")
    L.append("")
    if unknown:
        L.append("| token | 语句数 | 程序数 |")
        L.append("|---|---:|---:|")
        for k in unknown[:40]:
            L.append("| `%s` | %d | %d |" % (k, stmt[k], len(progs[k])))
    else:
        L.append("无。")
    L.append("")
    L.append("## 4. Top %d 指令" % top)
    L.append("")
    L.append("| instruction | 语句数 | 占比 | 程序数 | 程序占比 |")
    L.append("|---|---:|---:|---:|---:|")
    for k, v in stmt.most_common(top):
        L.append("| `%s` | %d | %.2f%% | %d | %.1f%% |"
                 % (k, v, pct(v, n_stmt), len(progs[k]), pct(len(progs[k]), n_files)))
    L.append("")
    L.append("## 5. 覆盖率总账")
    L.append("")
    hit = [k for k in canonical_instr if stmt.get(k, 0) > 0]
    L.append("- instruction 覆盖：**%d/%d**（%.1f%%）"
             % (len(hit), len(canonical_instr), pct(len(hit), len(canonical_instr))))
    if canonical_ops:
        ohit = [o for o in canonical_ops if op_hist0(r, o) > 0]
        L.append("- op 子命令覆盖：**%d/%d**（%.1f%%）"
                 % (len(ohit), len(canonical_ops), pct(len(ohit), len(canonical_ops))))
    L.append("- 语料里出现过的不同首 token：%d 个" % len(stmt))
    return "\n".join(L) + "\n"


def op_hist0(r, name):
    return r["op_hist"].get(name, 0)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="directory of .mlog programs")
    ap.add_argument("--json", default="out/_crawl/instr-coverage.json")
    ap.add_argument("--md", default="out/_crawl/instr-coverage.md")
    ap.add_argument("--limit", type=int, default=0, help="only first N files (smoke)")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args(argv)

    ci, co, ver = load_canonical()
    r = scan(a.src, a.limit)
    print("scanned %d file(s) / %d statement(s) in %.1f s" % (r["files"], r["statements"], r["secs"]))
    md = report(r, ci, co, ver, a.top)

    data = {
        "src": r["src"], "files": r["files"], "lines": r["lines"],
        "statements": r["statements"], "labels": r["labels"], "secs": r["secs"],
        "semicolon_lines": r["semicolon_lines"], "junk": r["junk"],
        "junk_samples": r["junk_samples"],
        "semantics_version": ver,
        "canonical_instructions": ci, "canonical_ops": co,
        "stmt": dict(r["stmt"]),
        "progs": {k: len(v) for k, v in r["progs"].items()},
        "op_hist": dict(r["op_hist"]),
        "op_progs": {k: len(v) for k, v in r["op_progs"].items()},
        "draw_hist": dict(r["draw_hist"]),
        "zero_instructions": [k for k in ci if r["stmt"].get(k, 0) == 0],
        "zero_ops": [o for o in co if op_hist0(r, o) == 0],
        "unknown_tokens": sorted((k for k in r["stmt"] if k not in set(ci) and k != "op"),
                                 key=lambda k: -r["stmt"][k]),
    }
    for p in (a.json, a.md):
        d = os.path.dirname(os.path.abspath(p))
        if d:
            os.makedirs(d, exist_ok=True)
    with open(a.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    with open(a.md, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print("wrote %s and %s" % (a.json, a.md))
    print("zero-coverage instructions: %d/%d ; unknown tokens: %d"
          % (len(data["zero_instructions"]), len(ci), len(data["unknown_tokens"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
