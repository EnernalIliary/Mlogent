"""Measure the `ir` dead-store signal over the whole blueprint corpus.

Purpose: decide whether `mlog.py ir` is usable as a linter *at its default
verbosity*. The number that matters is ``reported per block`` -- anything the
reader has to triage by hand is a bug in the tool, not in the blueprint.

The three tiers are the ones `mlog.py` itself uses:
  reported    -- a computed value dropped on the floor. This is the signal.
  slot        -- a multi-output statement whose unread slot is unavoidable.
  declaration -- `set x <literal>`, i.e. the author's own note-keeping.

Emulator / VM blueprints are counted separately and excluded from the headline
number: they dead-store by design (a VM writes every register slot on each
dispatch and only reads back the ones the next instruction needs), so including
them measures the emulator's instruction decoder, not the author's mistakes.

Run: python tools/_sweep_deadstores.py
"""

from __future__ import annotations

import collections
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
# Structural fallback: a real schematic never has this many dropped values in a
# single processor. A VM does, because it is a dispatch loop over register slots.
EMULATOR_DEADSTORE_FLOOR = 80


class Bucket:
    """Counters for one subset of the corpus."""

    def __init__(self) -> None:
        self.files = 0
        self.blocks = 0
        self.tiers: collections.Counter[str] = collections.Counter()
        self.by_instr: collections.Counter[str] = collections.Counter()
        self.by_var: collections.Counter[str] = collections.Counter()
        self.unreachable = 0
        self.unknown: collections.Counter[str] = collections.Counter()
        # The mean is not the experience: one code-generated blueprint with 200
        # dropped values moves it a lot. Keep the shape of the distribution.
        self.counts: list[int] = []
        self.by_file: collections.Counter[str] = collections.Counter()

    @property
    def reported(self) -> int:
        return self.tiers["reported"]

    def per_block(self) -> float:
        return self.reported / max(self.blocks, 1)

    def report(self, title: str) -> None:
        print(f"--- {title}")
        print(f"  files             : {self.files}")
        print(f"  logic blocks      : {self.blocks}")
        print(f"  blocks w/ unreach.: {self.unreachable} "
              f"({self.unreachable / max(self.blocks, 1):.1%})")
        for k in ("reported", "slot", "declaration", "annotation"):
            n = self.tiers[k]
            print(f"  {k:<17}: {n:>7}  ({n / max(self.blocks, 1):.3f} per block)")
        if self.counts:
            s = sorted(self.counts)
            p50 = s[len(s) // 2]
            p90 = s[int(len(s) * 0.9)]
            p99 = s[int(len(s) * 0.99)]
            print(f"  per-block p50/p90/p99: {p50} / {p90} / {p99}")
            clean = sum(1 for c in self.counts if c == 0)
            print(f"  clean blocks       : {clean} "
                  f"({clean / max(self.blocks, 1):.1%})")
            print("  worst files:")
            for k, v in self.by_file.most_common(5):
                print(f"    {v:>5}  {k}")
        print()
        print("  reported, by instruction:")
        for k, v in self.by_instr.most_common(10):
            print(f"    {k:<14} {v:>6}")
        print("  reported, by variable:")
        for k, v in self.by_var.most_common(10):
            print(f"    {k:<22} {v:>6}")
        if self.unknown:
            print("  UNKNOWN instructions (semantics table gaps):")
            for k, v in self.unknown.most_common(10):
                print(f"    {k:<30} {v:>6}")
        print()


def main() -> int:
    files = sorted(CORPUS.glob("*.msch"))
    real = Bucket()
    emu = Bucket()

    for path in files:
        try:
            sch = msch.parse_file(str(path))
        except Exception as exc:                      # noqa: BLE001
            print(f"!! {path.name}: {exc}")
            continue
        name = ((sch.name or "") + " " + path.name).lower()
        hint = any(h in name for h in EMULATOR_HINTS)

        # Parse the file's blocks first: the structural test needs the data.
        # `classify_dead_stores()` recomputes liveness, and it *is* the runtime,
        # so call it exactly once per block and reuse the result.
        blocks: list[tuple[object, list]] = []
        for tile in sch.logic_tiles():
            if tile.logic is None:
                continue
            prog = mlogir.parse(tile.logic.code.split("\n"))
            blocks.append((prog, prog.classify_dead_stores()))

        worst = max((len(ds) for _, ds in blocks), default=0)
        emulator = hint or worst >= EMULATOR_DEADSTORE_FLOOR
        bucket = emu if emulator else real
        bucket.files += 1

        for prog, dead_stores in blocks:
            bucket.blocks += 1
            for s in prog.stmts:
                if s.unknown:
                    bucket.unknown[s.mnemonic] += 1
            if prog.dead():
                bucket.unreachable += 1
            block_reported = 0
            for i, var, kind in dead_stores:
                tier = mlog._ir_tier(prog, i, var, kind)
                bucket.tiers[tier] += 1
                if tier != "reported":
                    continue
                block_reported += 1
                bucket.by_instr[prog.stmts[i].mnemonic] += 1
                bucket.by_var[var] += 1
            bucket.counts.append(block_reported)
            bucket.by_file[path.name] += block_reported

    print(f"corpus: {CORPUS}  ({len(files)} .msch files)")
    print(f"emulator-like files excluded: {emu.files}, blocks: {emu.blocks}\n")
    real.report("real blueprints -- the number that matters")
    print(f"HEADLINE reported per block : {real.per_block():.3f}\n")
    emu.report("emulator / VM blueprints -- excluded from the headline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
