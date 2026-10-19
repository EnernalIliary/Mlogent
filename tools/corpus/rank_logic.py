"""
rank_logic.py -- rank blueprints by *game logic* content, excluding:
  * auto-generated pixel art (pic*, BADAPPLE, ...)
  * the mlogv32 RISC-V emulator project ("Linux on mlogv32") -- excluded on request
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

# Explicitly excluded on user request
EXCLUDE_FILES = {"Linux on mlogv32.msch"}

# Image / pixel-art generators
ART_PAT = re.compile(r"(^pic|pic_|BADAPPLE|涩图|^AKIRA|picturebigger|吃吃B)", re.I)

# Meaningful game-logic opcodes (things that actually interact with the world)
GAMEPLAY_OPS = {
    "ucontrol", "ubind", "unbind", "uradar", "ulocate", "flag", "build",
    "deconstruct", "getBlock", "within",
    "sensor", "control", "radar", "getlink", "setprop", "getblock", "setblock",
    "read", "write",
    "spawn", "bullet", "status", "weathersense", "weatherset", "spawnwave",
    "setrule", "fetch", "getflag", "setflag", "effect", "explosion",
    "query", "setmarker", "makemarker", "cutscene",
    "print", "printflush", "format", "drawflush",
}

CATEGORY_HINT = [
    ("兵控/单位控制", {"ucontrol", "ubind", "unbind", "uradar", "ulocate", "flag"}),
    ("建筑交互/物流", {"sensor", "control", "getlink", "read", "write", "setprop"}),
    ("建造/拆除", {"build", "deconstruct", "getBlock", "getblock", "setblock"}),
    ("武器/战斗", {"bullet", "radar", "within", "status", "explosion"}),
    ("世界/规则", {"setrule", "spawn", "spawnwave", "weatherset", "effect",
                   "setmarker", "makemarker", "query", "setrate"}),
    ("显示/输出", {"print", "printflush", "format", "drawflush", "draw"}),
]


def first_op(line: str) -> str:
    line = line.strip()
    return line.split(" ", 1)[0] if line else ""


def main() -> None:
    files = sorted(f for f in os.listdir(SCHEM) if f.lower().endswith(".msch"))
    recs = []
    for fname in files:
        if fname in EXCLUDE_FILES:
            continue
        try:
            sch = msch.parse_file(os.path.join(SCHEM, fname))
        except Exception:
            continue
        lt = sch.logic_tiles()
        if not lt:
            continue

        lines: list[str] = []
        per_proc = []
        for t in lt:
            assert t.logic is not None
            ls = t.logic.statement_lines()
            per_proc.append((len(ls), t.block, t.x, t.y, ls))
            lines.extend(ls)

        n = len(lines)
        ops = collections.Counter(first_op(l) for l in lines)
        gameplay = sum(ops[k] for k in GAMEPLAY_OPS)

        # score: gameplay instructions, with a penalty for pure print/draw bulk
        output_only = sum(ops[k] for k in ("draw", "print", "printchar", "format"))
        score = gameplay * 1.0 + n * 0.05 - output_only * 0.8
        if ART_PAT.search(fname):
            score -= 5000

        hints = [name for name, keys in CATEGORY_HINT
                 if sum(ops[k] for k in keys) > 0]

        recs.append({
            "file": fname,
            "name": sch.name,
            "processors": len(lt),
            "statements": n,
            "gameplay": gameplay,
            "output_only": output_only,
            "score": round(score, 1),
            "biggest": max((p[0] for p in per_proc), default=0),
            "hints": hints,
            "top_ops": ops.most_common(8),
            "labels": sch.labels,
        })

    recs.sort(key=lambda r: -r["score"])

    print("=" * 96)
    print("GAME-LOGIC BLUEPRINTS, ranked (pixel-art and mlogv32 excluded)")
    print("=" * 96)
    print(f"{'#':>3} {'stmts':>7} {'game':>6} {'proc':>4} {'big':>5}  {'file':<46} hints")
    print("-" * 96)
    for i, r in enumerate(recs[:60], 1):
        print(f"{i:>3} {r['statements']:>7} {r['gameplay']:>6} {r['processors']:>4} "
              f"{r['biggest']:>5}  {r['file'][:46]:<46} {','.join(r['hints'][:2])}")

    with open(os.path.join(OUT, "ranking.json"), "w", encoding="utf-8") as fh:
        json.dump(recs, fh, ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.join(OUT,'ranking.json')}  ({len(recs)} blueprints)")


if __name__ == "__main__":
    main()
