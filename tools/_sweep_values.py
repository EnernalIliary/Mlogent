"""Measure the `values` signal over the whole blueprint corpus.

The question this answers: **how often can a value analysis say something the
token stream does not already say?** Two outputs count as signal:

  resolved branches -- a conditional whose two sides are both exact, so the
                       branch is always/never taken and one side is dead code.
  provably null     -- a variable that is exactly `null` at a statement that
                       reads it, i.e. `op logn 0 2` feeding `strictEqual null`.

Everything else degrades to `?` because the value came from a sensor, a link,
a cell read or a unit query. That is the documented ceiling of this analysis:
half of every real program's variables are external state.

Run: python tools/_sweep_values.py [--limit N] [--verbose]
"""

from __future__ import annotations

import collections
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent / "mindustry-blueprint" / "tools"
sys.path.insert(0, str(SKILL))

import mlogir        # noqa: E402
import mlogval       # noqa: E402
import msch          # noqa: E402

CORPUS = Path(r"C:\Users\lliary\AppData\Roaming\Mindustry\schematics")

EMULATOR_HINTS = ("mlogv32", "linux", "riscv", "risc-v", "vm")


def is_emulator(name: str) -> bool:
    low = name.lower()
    return any(h in low for h in EMULATOR_HINTS)


def main(argv: list[str]) -> int:
    limit = None
    verbose = "--verbose" in argv
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])

    files = sorted(CORPUS.glob("*.msch"))
    if limit:
        files = files[:limit]

    blocks = 0
    with_signal = 0
    branch_blocks = 0
    null_blocks = 0
    branches = 0
    nulls = 0
    rounds: collections.Counter[int] = collections.Counter()
    unstable = 0
    by_branch_file: collections.Counter[str] = collections.Counter()
    by_null_var: collections.Counter[str] = collections.Counter()
    by_inst: collections.Counter[str] = collections.Counter()
    skipped_emu_files = 0
    skipped_emu_blocks = 0
    t0 = time.time()

    for path in files:
        emu = is_emulator(path.name)
        try:
            sch = msch.parse_file(str(path))
        except Exception:
            continue
        if emu:
            skipped_emu_files += 1
        for t in sch.logic_tiles():
            if t.logic is None:
                continue
            if emu:
                skipped_emu_blocks += 1
                continue
            lines = t.logic.code.split("\n")
            prog = mlogir.parse(lines)
            if not prog.stmts:
                continue
            blocks += 1
            st = mlogval.analyze(prog)
            rounds[st.rounds] += 1
            if not st.stable:
                unstable += 1
            if st.branches:
                branch_blocks += 1
                branches += len(st.branches)
                by_branch_file[path.name] += len(st.branches)
                for i, _mode, _cond in st.branches:
                    by_inst[prog.stmts[i].mnemonic] += 1
            if st.nulls:
                null_blocks += 1
                nulls += len(st.nulls)
                for _i, v in st.nulls:
                    by_null_var[v] += 1
            if st.branches or st.nulls:
                with_signal += 1
                if verbose:
                    print(f"{path.name} @({t.x},{t.y})  "
                          f"branches={len(st.branches)} nulls={len(st.nulls)}")

    dt = time.time() - t0
    print()
    print(f"files           : {len(files)}  ({skipped_emu_files} emulator,"
          f" {skipped_emu_blocks} blocks skipped)")
    print(f"blocks          : {blocks}")
    print(f"elapsed         : {dt:.1f}s  ({dt / max(blocks, 1) * 1000:.0f} ms/block)")
    print(f"blocks w/ signal: {with_signal} "
          f"({with_signal / max(blocks, 1) * 100:.1f}%)")
    print(f"  branches      : {branches} in {branch_blocks} blocks "
          f"({branches / max(blocks, 1):.3f}/block)")
    print(f"  provably null : {nulls} in {null_blocks} blocks "
          f"({nulls / max(blocks, 1):.3f}/block)")
    print(f"unstable        : {unstable}")
    print(f"rounds          : {dict(sorted(rounds.items()))}")
    if by_inst:
        print(f"branch by instr : {by_inst.most_common(8)}")
    if by_null_var:
        print(f"null by var     : {by_null_var.most_common(12)}")
    if by_branch_file:
        print("worst files     :")
        for name, n in by_branch_file.most_common(6):
            print(f"    {n:>4}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
