"""
mine_idioms.py -- mine recurring mlog idioms from the extracted blueprint logic.

Normalizes variable names to placeholders, counts instruction n-grams, and
reports the dominant control-flow/unit-control patterns with real examples.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msch

SCHEM = r"C:\Users\lliary\AppData\Roaming\Mindustry\schematics"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "logic-corpus")

SKIP = {"Linux on mlogv32.msch"}
NUM = re.compile(r"^-?\d+(\.\d+)?$")


def norm_tok(t: str) -> str:
    """Normalise a token so that structurally identical code collides."""
    if NUM.match(t):
        return "N"
    if t.startswith('"'):
        return "S"
    if t.startswith("@"):
        return t  # built-ins are meaningful
    if t == "true" or t == "false":
        return t
    return "v"  # variable / link name


def norm_line(line: str) -> str:
    parts = line.strip().split()
    if not parts:
        return ""
    # jump targets are absolute line numbers -> normalise to J
    if parts[0] == "jump":
        parts = ["jump", "J"] + [norm_tok(p) for p in parts[2:]]
        return " ".join(parts)
    return " ".join([parts[0]] + [norm_tok(p) for p in parts[1:]])


def main() -> None:
    files = sorted(f for f in os.listdir(SCHEM) if f.lower().endswith(".msch"))
    unigrams = collections.Counter()
    bigrams = collections.Counter()
    trigrams = collections.Counter()
    bgram_example: dict[str, tuple[str, str]] = {}

    # single-processor bodies that are short enough to be "templates"
    templates: list[tuple[int, str, str, list[str]]] = []
    bp_count = 0

    for fname in files:
        if fname in SKIP:
            continue
        try:
            sch = msch.parse_file(os.path.join(SCHEM, fname))
        except Exception:
            continue
        lt = sch.logic_tiles()
        if not lt:
            continue
        bp_count += 1

        for t in lt:
            assert t.logic is not None
            raw = t.logic.statement_lines()
            nl = [norm_line(l) for l in raw]
            nl = [x for x in nl if x]
            for x in nl:
                unigrams[x.split(" ", 1)[0]] += 1
            for w in range(len(nl) - 1):
                bg = (nl[w], nl[w + 1])
                bigrams[bg] += 1
                bgram_example.setdefault("\u0000".join(bg), (fname, raw[w] + " / " + raw[w + 1]))
            for w in range(len(nl) - 2):
                trigrams[tuple(nl[w:w + 3])] += 1

            if 3 <= len(raw) <= 30:
                templates.append((len(raw), fname, t.block, raw))

    print("=" * 100)
    print(f"MOST COMMON 2-LINE IDIOMS  (over {bp_count} blueprints)")
    print("=" * 100)
    for bg, c in bigrams.most_common(45):
        exf, ex = bgram_example["\u0000".join(bg)]
        print(f"{c:7,d}  {' | '.join(bg)}")
        print(f"         e.g. {ex}   [{exf}]")

    print()
    print("=" * 100)
    print("MOST COMMON 3-LINE IDIOMS")
    print("=" * 100)
    for tg, c in trigrams.most_common(30):
        print(f"{c:7,d}  {' || '.join(tg)}")

    with open(os.path.join(OUT, "idioms.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "unigrams": dict(unigrams.most_common()),
            "bigrams": [{"count": c, "pattern": list(bg)} for bg, c in bigrams.most_common(400)],
            "trigrams": [{"count": c, "pattern": list(tg)} for tg, c in trigrams.most_common(400)],
        }, fh, ensure_ascii=False, indent=1)

    # short single-processor blueprint templates
    templates.sort()
    with open(os.path.join(OUT, "templates.md"), "w", encoding="utf-8") as fh:
        fh.write("# Short single-processor logic templates\n\n")
        fh.write("Blueprints whose logic is one small processor (<=30 statements) -- "
                 "readable as reusable building blocks.\n\n")
        fh.write(f"Total: {len(templates)}\n\n")
        for n, fname, blk, raw in templates:
            fh.write(f"## {fname}  ({n} stmts, {blk})\n\n```mlog\n")
            fh.write("\n".join(raw))
            fh.write("\n```\n\n")
    print(f"\ntemplates.md: {len(templates)} short templates")
    print(f"wrote {os.path.join(OUT,'idioms.json')}")


if __name__ == "__main__":
    main()
