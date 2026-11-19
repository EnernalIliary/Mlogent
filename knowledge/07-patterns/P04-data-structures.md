---
id: PATTERN.DATA.001
title: Data structures: arrays, queues, ring buffers, and canvas memory layout
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6875,6881"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicDisplay.java:53,118,137"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/TileableLogicDisplay.java:35"
  - "mindustry-blueprint/PATTERNS.md:1673-1800"
data: []
depends: [PATTERN.COMM.001]
tags: [data-structure, array, queue, ring-buffer, memory-layout, canvas]
tokens: 545
---

## One line

mlog has no pointers and no lengths, so every data structure is "a memory building's index plus hand-computed addresses"; the first criterion for choosing a structure is therefore not asymptotic complexity but how many instructions each operation costs (every instruction consumes 1 ipt of budget): array 1, queue 3, ring buffer 4, full canvas 4096.

## Rules / formulas

General cost formula: one data-structure operation = addressing instruction + transfer instruction. Addressing uses op, transfer uses read/write, 1 statement each.

| Structure | Representation | Instructions per operation | Capacity limit | Typical use |
|---|---|---:|---|---|
| Array | base + i | 1 read/write (when i is known) | cell 64 / bank 512 | lookup tables, coordinate cache |
| Queue | head and tail, two indices | 3 (read head, add, write back) | limited by capacity | task assignment, input buffering |
| Stack | top, one index | 3 | same | recursion/backtracking simulation |
| Ring buffer | i = (i+1) mod N | 4 (op mod + read/write) | N set by the mod constant | rotation, dedup, sliding window |
| Bitmap | one number as a 32-bit group | 3 (op and/or + shift) | 32 bits/slot | boolean sets, switch tables |

Memory layout rules:

1. Segment: block by meaning and place from high index down (91/96/99), leaving gaps between.
2. Write segment base and segment length as two set statements, route every access through base+i, and never scatter magic indices.
3. One memory building serves exactly one purpose; to share across purposes, split first, then allocate.

## Numbers

| Quantity | Value | Source |
|---|---|---|
| memory-cell / memory-bank capacity | 64 / 512 slots | Blocks.java:6875 / 6881 |
| Display canvas size | 64 x 64 (32 x 32 for tileable) | LogicDisplay.java:53 / TileableLogicDisplay.java:35 |
| read usage in the 2025 corpus | 8052 | `unigrams` count in tools/corpus/mine_idioms.py |
| Pixel-art blueprint count / statement volume | 18 / about 1.4 million | ../../mindustry-blueprint/PATTERNS.md:1774 |
| Peak draw count in one blueprint | 126,759 (intel corei3.msch) | ../../mindustry-blueprint/PATTERNS.md:1786 |

Canvas cost is computable: 64x64 = 4096 pixels, one draw instruction per pixel → 4096 statements to fill one frame; a hyper-processor at 25 ipt needs 4096/25 = 163.8 tick, i.e. 163.8/60 = 2.73 s per frame.

## Source anchors

- Blocks.java:6875/6881 — capacity of the two memory buildings.
- LogicDisplay.java:53 `displaySize = 64`; :137 `new FrameBuffer(displaySize, displaySize)`; :118 displayWidth/displayHeight are only aliases.
- TileableLogicDisplay.java:35 `displaySize = 32`.

## Measurements and counter-examples

**Counter-example (out-of-range array access reports nothing)**: a cell has only 64 slots, so reads and writes at index 64 and above silently do nothing (reads return 0, writes are dropped). The symptom is "the last few table entries are always 0"; when debugging, print the index range before doubting the logic.

**Counter-example (zeroing a ring buffer with if)**: zeroing via a jump lessThan i N branch needs 3 instructions and unequal branch lengths, while op mod i i N needs only 1 — the 913-statement multi-unit hauling blueprint in the corpus rotates slots with mod (the multi-unit hauling breakdown in BLUEPRINT-ANALYSIS.md).

**Canvas special case**: pixel-art blueprints account for the vast majority of statements in the whole corpus (18 blueprints, about 1.4 million, PATTERNS.md:1774); they are data, not logic — when counting "logic idioms" they must be excluded by is_art, otherwise draw crushes every real instruction with 1,305,167 occurrences (same source, `mine_idioms.py` unigrams count).

## Common misconceptions

1. "a memory slot can serve as a dynamic array" — wrong, there is no length field; you must store the length in a slot yourself.
2. "one read gets the latest value" — wrong, cross-processor tick interleaving exists and a sequence column is mandatory.
3. "display coordinates are 0..64" — wrong, draw coordinates range over 0..displaySize (64) and are clipped outside; the tileable version is 32.
4. "a queue is more flexible than a ring buffer" — in mlog a queue maintains an extra head index, while the ring buffer's mod is cheaper.

## Related

- PATTERN.COMM.001 communication and buses (index segmentation and races)
- PATTERN.PERF.001 performance and robustness (budget allocation)
- MLOG.DRAW.001 drawing instructions
