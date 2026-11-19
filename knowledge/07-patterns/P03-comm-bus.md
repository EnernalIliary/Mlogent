---
id: PATTERN.COMM.001
title: Communication and buses: memory mailboxes, channel encoding, read/write races
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6875,6881,6967"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:300-322"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:761-763"
  - "mindustry-blueprint/PATTERNS.md:457-582,1057-1140,1673-1745"
data: []
depends: [PATTERN.ARCH.001]
tags: [communication, memory-cell, blackboard, race, multi-core]
tokens: 569
---

## One line

There are only two physical channels for cross-processor communication — memory buildings (read/write + numeric index) and processor variable space (read/write + string variable name, which can hold object references); neither has locks, so a protocol must be hand-built from "single writer + sequence number" and cannot rely on atomicity.

## Rules / formulas

The address argument of read/write has two forms with completely different semantics:

| Address form | Target | What it can hold | Capacity |
|---|---|---|---|
| Numeric index 0..N-1 | memory building (cell / bank) | numbers (references unreliable) | cell 64 slots / bank 512 slots |
| String name | the processor's variable space (by variable name) | number or object reference | limited by variable count |

Three usable topologies:

1. Blackboard (shared memory): many writers, many readers, conflicts avoided by hand-partitioned index segments.
2. Mailbox (point-to-point): fixed index = fixed recipient, a writer only touches its own slot.
3. Direct variable-space link: write a unit reference to processor "slot1", where the dispatcher core stuffs the entity reference straight into a control core's variable — the only way to pass entity references across processors.

Race rules without locks (three, all required):

- One slot allows exactly one writer; multiple writers inevitably overwrite each other.
- Read/write ordering is decided by a sequence column: the writer writes data first, then increments the sequence; the reader compares the sequence with its last recorded value and takes the data only when it changed.
- A write followed immediately by a read within the same tick does not guarantee the new value (processors interleave on their @ipt budgets, and sensor has a 30 tick refresh window).

**Edges get lost, sequence numbers do not**: encoding "there is new data" as a `0 → 1` edge is wrong. The write is visible on the next tick, the other side may sample at any instruction point, and the intermediate state is skipped wholesale ⇒ both sides wait on each other and never advance. A workable protocol is a **monotonic phase number + completion counter**: the sender increments the phase, writes the data, writes the phase; the receiver takes the data only when it sees the phase changed and writes back a completion count; the sender waits for the completion count to catch up.

```mlog
op add t t 1
write r cell1 259
write t cell1 257
read d cell1 258
jump @counter lessThan d t
```

(`259` holds data, `257` holds the phase, `258` holds the completion count; the indices are just an example. The premise is still rule 1 above: one writer per slot, otherwise the sequence number itself is lost.)

## Numbers

| Quantity | Value | Source |
|---|---|---|
| memory-cell slots | 64 | [src: Blocks.java:6875] |
| memory-bank slots | 512 | [src: Blocks.java:6881] |
| Large memory (world-processor side) | 512 | [src: Blocks.java:6967] |
| sensor/radar result refresh window | 30 tick (0.5 s) | [src: LExecutor.java:761-763] |
| read instruction usage in corpus | 8052 | `unigrams` count in tools/corpus/mine_idioms.py |

## Source anchors

- Blocks.java:6875/6881 — memoryCapacity = 64 / 512.
- LogicBlock.java:300-322 — links are stored in the blueprint as (name, dx, dy) and turned into absolute coordinates on load.
- LExecutor.java:761-763 — the comment reads fixed 30 tick interval; timer.get(30f) decides when sensor/radar reads are recomputed.

## Measurements and counter-examples

Blackboard segmentation actually used in the corpus (mindustry-blueprint/PATTERNS.md:1693-1695): the Chinese-chess blueprint (中国象棋.msch) uses index 91 for shooting, 96 for s.team, 99 for t.team in bank1; the overtaking simulator (超车模拟器.msch) uses 30 for dead, 9 for stop-r, 6/7 for run-r/run-l, 1/2 for o1x/o1y in cell1. What they share is segmented indices with gaps (1/2/6/7/9/20/30/39, 91/96/99) rather than a contiguous packing — leaving room for later extension.

**Counter-example (passing references through memory slots)**: a memory slot can reliably carry numbers only. Writing a unit or building reference into a cell and reading it on another processor is not a stable protocol; to pass references, use write reference processor "variable name" instead.

**Counter-example (multiple writers)**: two processors both write their own state into cell1[0]; the reader cannot tell whose slot it is, and the symptom is values jumping randomly and occasional hangs. Fix: one writer per slot, or add a writer-ID column that the reader filters on.

## Common misconceptions

1. "read/write addresses can only be numeric" — wrong, a string address reaches processor variable space and can hold object references, which is the key to dispatcher-core/control-core architectures.
2. "a memory slot is atomic; a write is readable immediately" — wrong, there are no locks or transactions, cross-core visibility depends on tick order, and you must use sequence numbers or double buffering to tell new from old.
3. "a link name is its position" — wrong, link names are recomputed as buildings change (getLinkName()), so after a rename old code silently mismatches.
4. "@controlled tells you which processor is in control" — wrong, every logic-controlled unit returns 1; to determine ownership compare @controller with @this.

## Related

- PATTERN.ARCH.001 architecture overview (dispatcher core + control cores)
- PATTERN.DATA.001 data structures (index layout)
- PATTERN.PERF.001 frame delta and synchronisation
