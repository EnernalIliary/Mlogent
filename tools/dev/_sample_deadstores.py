"""Print real `reported` dead-store sites with context, so the number can be judged.

The sweep says 0.650 reported per block. That is only meaningful if a human
reads the actual sites and agrees they are dropped computations. This dumps a
sample of them, per instruction, with two lines of surrounding code.

Run: python tools/_sample_deadstores.py [--instr set] [--limit 40]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent / "mindustry-blueprint" / "tools"
sys.path.insert(0, str(SKILL))

import mlog          # noqa: E402
import mlogir        # noqa: E402
import msch          # noqa: E402

CORPUS = Path(r"C:\Users\lliary\AppData\Roaming\Mindustry\schematics")
EMULATOR_HINTS = ("mlogv32", "linux", "riscv", "risc-v", "vm")
EMULATOR_DEADSTORE_FLOOR = 80


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instr", default=None, help="only this mnemonic")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    shown = 0
    for path in sorted(CORPUS.glob("*.msch")):
        if shown >= args.limit:
            break
        try:
            sch = msch.parse_file(str(path))
        except Exception:                             # noqa: BLE001
            continue
        name = ((sch.name or "") + " " + path.name).lower()
        if any(h in name for h in EMULATOR_HINTS):
            continue

        blocks = []
        for tile in sch.logic_tiles():
            if tile.logic is None:
                continue
            prog = mlogir.parse(tile.logic.code.split("\n"))
            blocks.append((prog, prog.classify_dead_stores()))
        worst = max((len(ds) for _, ds in blocks), default=0)
        if worst >= EMULATOR_DEADSTORE_FLOOR:
            continue

        for prog, dead_stores in blocks:
            if shown >= args.limit:
                break
            for i, var, kind in dead_stores:
                if shown >= args.limit:
                    break
                if mlog._ir_tier(prog, i, var, kind) != "reported":
                    continue
                stmt = prog.stmts[i]
                if args.instr and stmt.mnemonic != args.instr:
                    continue
                shown += 1
                print(f"\n=== {path.name}  L{i + 1}  var={var!r}  kind={kind}  "
                      f"{stmt.mnemonic} ===")
                for k in range(max(0, i - 2), min(len(prog.stmts), i + 3)):
                    mark = ">>" if k == i else "  "
                    print(f" {mark} L{k + 1:<4} {prog.stmts[k].raw}")
    print(f"\nshown: {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
