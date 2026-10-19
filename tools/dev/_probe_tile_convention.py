"""
Determine whether a schematic's Stile position for a multi-tile block is the
block's CORNER or its CENTER, by looking at real blueprints.

Method: for blocks of odd size (3x3, 5x5), if the stored position is the CORNER
then a parked layout can sit anywhere; but if there is a real structural clue it
is the parity of the processor->dome offset in blueprints that were clearly laid
out adjacently. Better clue: Mindustry writes the schematic from the map with
`tile.tileX()`, and setBlock()/getLinkedTilesAs() treat that as the block's
origin. We test empirically by checking whether any 3x3 block in the corpus ever
appears at a position where its footprint would overlap another block -- which
would be impossible if the convention were consistent.
"""
import glob
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msch

SCHEM = r"C:\Users\lliary\AppData\Roaming\Mindustry\schematics"

# odd-sized blocks: their stored coord is the most diagnostic
INTERESTING = {"overdrive-dome": 3, "hyper-processor": 3, "vault": 3,
               "core-nucleus": 5, "large-logic-display": 6, "canvas": 2,
               "memory-bank": 2, "core-foundation": 4, "core-shard": 3}

occ = collections.Counter()
overlap_corner = 0
overlap_center = 0
samples = collections.defaultdict(list)

files = sorted(glob.glob(os.path.join(SCHEM, "*.msch")))
parsed = 0
for f in files:
    try:
        sch = msch.parse_file(f)
    except Exception:
        continue
    parsed += 1
    # build a set of all occupied tiles under BOTH conventions and see which
    # one produces fewer collisions among multi-tile blocks
    for conv in ("corner", "center"):
        cells = {}
        clash = False
        for t in sch.tiles:
            sz = INTERESTING.get(t.block, 1)
            if sz <= 1:
                cells[(t.x, t.y)] = t.block
                continue
            if conv == "corner":
                x0, y0 = t.x, t.y
            else:
                half = (sz - 1) // 2
                x0, y0 = t.x - half, t.y - half
            for dx in range(sz):
                for dy in range(sz):
                    k = (x0 + dx, y0 + dy)
                    if k in cells and cells[k] != t.block:
                        clash = True
                    cells[k] = t.block
        if clash:
            if conv == "corner":
                overlap_corner += 1
            else:
                overlap_center += 1

    for t in sch.tiles:
        if t.block in INTERESTING:
            occ[t.block] += 1
            if len(samples[t.block]) < 5:
                samples[t.block].append((os.path.basename(f), t.x, t.y))

print(f"parsed {parsed} blueprints")
print()
print("blueprints with a multi-tile/other block overlap:")
print(f"   if position = CORNER : {overlap_corner}")
print(f"   if position = CENTER : {overlap_center}")
print("   (the convention with fewer overlaps is the correct one)")
print()
print("occurrences of interesting blocks:")
for b, n in occ.most_common():
    print(f"   {b:22} x{n:<5} e.g. {samples[b][:3]}")
