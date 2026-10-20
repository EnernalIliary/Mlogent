"""Build the two schematic benches used to pin down mlog semantics.

    python out/scenes/benches/build.py

Writes memory-bench.msch and processor-bench.msch next to this file.
sensor-bench has no schematic: it needs real units, so run.py spawns them.

Link range is `LogicBlock.range = 8 * 10` world units = 10 tiles (LogicBlock.java:49),
so every link below stays within 10 tiles; longer links silently resolve to null.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))

from mschgen import Blueprint, Link  # noqa: E402

# ---------------------------------------------------------------- memory bench
# writer -> cell1[0]=7, cell1[1]=8, declared=42
WRITER = """write 7 cell1 0
write 8 cell1 1
set declared 42
end"""

# reader: written slot / unwritten slot / other cell / another processor's var
READER = """read a cell1 0
read b cell1 3
read c cell2 0
read d writer1 "declared"
print "R "
print a
print "|"
print b
print "|"
print c
print "|"
print d
end"""

# coord: read slot 1, write 99 to slot 2, read it back
COORD = """read e cell1 1
write 99 cell1 2
read f cell1 2
print "C "
print e
print "|"
print f
end"""


def memory_bench() -> Blueprint:
    b = Blueprint("memory-bench", "cross-processor memory: cells, slots, named vars")
    b.add_block("memory-cell", 3, 0)
    b.add_block("memory-cell", 12, 0)
    b.add_logic(WRITER, 0, 0, links=[Link("cell1", 3, 0)])
    b.add_logic(READER, 6, 0, links=[Link("cell1", -3, 0),
                                     Link("cell2", 6, 0),
                                     Link("writer1", -6, 0)])
    b.add_logic(COORD, 9, 0, links=[Link("cell1", -6, 0),
                                    Link("cell2", 3, 0)])
    return b


# ------------------------------------------------------------- processor bench
PROC = """write @ipt cell1 0
read v cell1 0
print @ipt
print "|"
print v
end"""

# same program plus a privileged statement: only a world processor keeps it
WORLD = """setrule unitCap 77
write @ipt cell1 0
read v cell1 0
print @ipt
print "|"
print v
end"""

# the hyper also pokes slot 63 of a 512-slot memory bank 2 tiles away
HYPER = """write @ipt cell1 0
read v cell1 0
write @ipt bank1 63
read w bank1 63
print @ipt
print "|"
print v
print "|"
print w
end"""


def processor_bench() -> Blueprint:
    b = Blueprint("processor-bench", "ipt per block type, links, memory bank slot 63")
    for x, code, block, links in (
            (0, PROC, "micro-processor", [Link("cell1", 2, 0)]),
            (4, PROC, "logic-processor", [Link("cell1", 2, 0)]),
            (8, HYPER, "hyper-processor", [Link("cell1", 2, 0), Link("bank1", 0, 2)]),
            (12, WORLD, "world-processor", [Link("cell1", 2, 0)]),
    ):
        b.add_logic(code, x, 0, block=block, links=links)
    b.add_block("memory-cell", 2, 0)
    b.add_block("memory-cell", 6, 0)
    b.add_block("memory-cell", 10, 0)
    b.add_block("memory-cell", 14, 0)
    b.add_block("memory-bank", 8, 2)
    return b


def main() -> int:
    for name, bp in (("memory-bench", memory_bench()),
                     ("processor-bench", processor_bench())):
        path = HERE / f"{name}.msch"
        bp.write(str(path))
        w, h = bp.bounds()
        print(f"{path.name}: {w}x{h}, {len(bp.tiles)} tiles")
        for msg in bp.link_report():
            print("  WARN", msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
