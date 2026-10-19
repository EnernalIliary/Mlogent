"""
analyze_logic.py -- classify / rank extracted mlog and build a study corpus.

The raw statement count is dominated by auto-generated pixel-art blueprints
(pic*, BADAPPLE) whose processors are enormous unrolled `print {N}` / `draw`
tables. Those contain no algorithms, so we separate them from real logic.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import msch

SCHEM = r"C:\Users\lliary\AppData\Roaming\Mindustry\schematics"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "logic-corpus")

# Instruction set, cross-referenced from core/src/mindustry/logic/LStatements.java
CATEGORY = {
    "print": "output", "printchar": "output", "format": "output",
    "draw": "output", "drawflush": "output", "printflush": "output",
    "localeprint": "output", "message": "output",
    "set": "var", "op": "var", "select": "var", "lookup": "var",
    "packcolor": "var", "unpackcolor": "var", "sync": "var",
    "jump": "flow", "end": "flow", "stop": "flow", "wait": "flow", "noop": "flow",
    "read": "mem", "write": "mem",
    "getlink": "block", "control": "block", "radar": "block",
    "sensor": "block", "setprop": "block", "getblock": "block", "setblock": "block",
    "ubind": "unit", "unbind": "unit", "ucontrol": "unit",
    "uradar": "unit", "ulocate": "unit", "flag": "unit", "build": "unit",
    "deconstruct": "unit", "getBlock": "unit", "within": "unit",
    "spawn": "world", "bullet": "world", "status": "world", "weathersense": "world",
    "weatherset": "world", "spawnwave": "world", "setrule": "world",
    "cutscene": "world", "effect": "world", "explosion": "world",
    "fetch": "world", "getflag": "world", "setflag": "world",
    "playsound": "world", "playmusic": "world", "setmarker": "world",
    "makemarker": "world", "setrate": "world", "query": "world",
    "clientdata": "world",
}

DRAW_PRINT = {"print", "printchar", "draw", "drawflush", "format", "localeprint"}
NOISE_NAME = re.compile(r"(^pic|pic_|^pic|BADAPPLE|涩图|点击|^AKIRA)", re.I)


def first_op(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    return line.split(" ", 1)[0]


def num_tokens(line: str) -> float:
    """Fraction of whitespace tokens that are bare numbers."""
    toks = line.split()[1:]
    if not toks:
        return 0.0
    n = 0
    for t in toks:
        t = t.strip('"')
        try:
            float(t)
            n += 1
        except ValueError:
            pass
    return n / len(toks)


def main() -> None:
    files = sorted(f for f in os.listdir(SCHEM) if f.lower().endswith(".msch"))
    records = []

    for fname in files:
        try:
            sch = msch.parse_file(os.path.join(SCHEM, fname))
        except Exception:
            continue
        lt = sch.logic_tiles()
        if not lt:
            continue

        all_lines: list[str] = []
        ops = collections.Counter()
        for t in lt:
            assert t.logic is not None
            lines = t.logic.statement_lines()
            all_lines.extend(lines)
            for ln in lines:
                ops[first_op(ln)] += 1

        n = len(all_lines)
        dp = sum(ops[k] for k in DRAW_PRINT)
        numeric = [num_tokens(l) for l in all_lines if first_op(l) in DRAW_PRINT]
        high_num = sum(1 for v in numeric if v >= 0.5)
        draw_ratio = dp / n if n else 0.0
        num_ratio = high_num / len(numeric) if numeric else 0.0

        # pixel art: nothing but print/draw of literal numbers, usually with
        # thousands of statements in a single processor
        biggest = max((len(t.logic.statement_lines()) for t in lt), default=0)
        is_art = (
            (draw_ratio > 0.9 and len(numeric) > 200 and num_ratio >= 0.5)
            or (biggest > 4000)
            or (bool(NOISE_NAME.search(fname)) and draw_ratio > 0.6)
        )

        categories = collections.Counter()
        for ln in all_lines:
            categories[CATEGORY.get(first_op(ln), "other")] += 1

        records.append({
            "file": fname,
            "name": sch.name,
            "processors": len(lt),
            "statements": n,
            "biggest": biggest,
            "draw_ratio": round(draw_ratio, 3),
            "is_art": is_art,
            "ops": dict(ops.most_common()),
            "categories": dict(categories.most_common()),
            "blocks": sch.block_counts(),
        })

    art = [r for r in records if r["is_art"]]
    real = [r for r in records if not r["is_art"]]
    real.sort(key=lambda r: -r["statements"])

    print(f"blueprints total     : {len(records)}")
    print(f"  image/pixel-art    : {len(art)}  "
          f"({sum(r['statements'] for r in art):,} statements)")
    print(f"  real logic         : {len(real)}  "
          f"({sum(r['statements'] for r in real):,} statements)")
    print()

    # global opcode histogram over real logic only
    hist = collections.Counter()
    for r in real:
        hist.update(r["ops"])
    print("--- opcode histogram (real logic only) ---")
    for op, c in hist.most_common(45):
        print(f"  {op:16s} {c:8,d}  [{CATEGORY.get(op,'other')}]")

    with open(os.path.join(OUT, "analysis.json"), "w", encoding="utf-8") as fh:
        json.dump({"all": records, "real": real, "art": art}, fh,
                  ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.join(OUT, 'analysis.json')}")


if __name__ == "__main__":
    main()
