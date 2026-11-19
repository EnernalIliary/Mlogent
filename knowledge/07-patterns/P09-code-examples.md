---
id: PATTERN.CODE.001
title: "Production logic code library: multi-control hauling, multi-control mining, row table, landing-pad scheduling"
domain: pattern
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src:
  - "knowledge/07-patterns/code/p09-haul-31slot-v27.mlog:1-988"
  - "knowledge/07-patterns/code/p09-mine-30slot-v3.mlog:1-966"
  - "knowledge/07-patterns/code/p09-haul-8slot-research.mlog:1-313"
  - "knowledge/07-patterns/code/p09-rows-v2.mlog:1-71"
  - "knowledge/07-patterns/code/p09-luozi-v6-micro8.mlog:1-463"
  - "knowledge/07-patterns/code/p09-luozi-v52-micro8.mlog:1-149"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41,119"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16,18"
  - "Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:190"
data: []
depends: [PATTERN.MULTI.001, PATTERN.COUNTER.001, PATTERN.PERF.001, MLOG.UNIT.001]
tags: [production, code-example, unit-multicontrol, hauling, mining, landing-pad, fixed-stride-slot]
tokens: 793
---

## One line

Six pieces of production logic you can paste straight into a processor (two versions of multi-control hauling, multi-control mining, the name row table, two versions of landing-pad scheduling) share one skeleton: **fixed-stride slots + relative dispatch + `@controller` liveness checks + a 2 s refill burst**; switching product only replaces the 18~20 statements inside a slot, while dispatch and refill stay untouched.

## Rules / formulas

Skeleton formulas (micro, `ipt` statements/tick):

```text
一圈条数 = 3 + N x stride          # 3 = 表尾时间闸门 + 位移加法
一圈时间 = 一圈条数 / (60 x ipt)    # micro ipt=2 => 120 条/s
tmp.hp   = -(N x stride + 3)       # init 一次，表尾 op add @counter @counter tmp.hp
```

- The dispatch displacement goes at the **table end**: `@counter` has already incremented to i+1 while instruction i executes [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:119], so putting it at the head lands on "slot slots−N" instead of slot N.
- Slot count x stride must not exceed the 1000 statement cap [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41].
- Two hard gates bound N: the unit interaction cooldown of 90 tick (1.5 s) [src: Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16] and logic-control loss at 600 tick (10 s) [src: Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:18]. Hauling is bound by the former (N ≤ 9), mining only by the latter (N can reach the slot limit).
- The refill period is 2 s, accumulated from `@time` (milliseconds), never `wait` (`wait` works in **seconds**) [src: Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:190].

Hot entry (identical in all six products, verbatim from v27):

```mlog
jump gate strictEqual cfg.item null
op mul tmp.hp N -19
op add @counter @counter tmp.hp
```

A single slot (hauling version, 19 statements) is ordered "test empty-handed → en-route pickup → pickup → test got-it → deliver → test emptied → turn back", and `ucontrol` always comes after `ubind`; the mining version swaps the delivery leg for `ucontrol mine ox oy` and adds one `ucontrol boost 1` during refill.

## Numbers

| File | Lines | Slots | stride | One round at N=8 | Product | Source |
|---|---|---|---|---|---|---|
| `code/p09-haul-31slot-v27.mlog` | 988 | 31 | 19 | 155 statements ≈1.29 s | unit multi-control hauling (flagship) | this library's code/ |
| `code/p09-mine-30slot-v3.mlog` | 966 | 30 | 18 | 147 statements ≈1.23 s | multi-control mining + boost | this library's code/ |
| `code/p09-haul-8slot-research.mlog` | 313 | 8 | 20 | 164 statements, upper bound | 8-slot research version | this library's code/ |
| `code/p09-rows-v2.mlog` | 71 | 50-row table | 6/empty row | see counter-example 4 | name-table traversal | this library's code/ |
| `code/p09-luozi-v6-micro8.mlog` | 463 | 8 pads | — | 408 statements ≈3.40 s | landing-pad scheduling (hard-coded) | this library's code/ |
| `code/p09-luozi-v52-micro8.mlog` | 149 | dynamic pad count | — | linear in pad count | landing-pad scheduling (loop) | this library's code/ |

Line counts include the header `print` and the signature slot; "one round at N=8" is the full-slot upper bound, and shorter when a short path hits [measured: knowledge/07-patterns/code/p09-haul-31slot-v27.mlog:1-988].

## Source anchors

- `LExecutor.java:41` `maxInstructions = 1000`: excess statements are dropped at load time, not truncated at runtime.
- `LExecutor.java:119` `instructions[(int)(counter.numval++)].run(this)`: increment first, execute second, which is why writing `@counter` inside an instruction means "set the next one".
- `LogicAI.java:16` `transferDelay = 60f*1.5f`: `itemTake`/`itemDrop` share this per-unit timer [src: Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16].
- `LogicAI.java:18` `logicControlTimeout = 600`: on timeout `resetController()` returns the unit to the game AI.
- `GlobalVars.java:190` `varTime.numval = state.tick / 60.0 * 1000.0`: `@time` is milliseconds [src: Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:190].

## Measurements and counter-examples

1. **Dispatch at the table head ⇒ slots−N slots actually run**. When the two `op` statements sit right at the start of the slot table, `@counter` has already incremented, so after the add it lands on slot (slots−N) of the descending table; only slots=2N happens to be correct [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:119].
2. **A return leg issued right after a failed `itemDrop` ⇒ overwrites the outbound leg**. `itemDrop` is only an attempt (it fails silently when the distance is too large or the 90 tick cooldown has not expired) [src: Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16], and an `approach sx sy` right after it means the unit never reaches the drop point; the fix is to `sensor @firstItem` after the drop and decide about turning back only then.
3. **The mining version's `loc` section uses `ubind u1`**: u1 is the last slot of the refill chain and is always empty when the unit count is < N ⇒ the whole `ulocate ore` section is skipped ⇒ the ore-field coordinates stay null forever ⇒ the squad never mines.
4. **Landing-pad quota as "ship one when the accumulator is full" ⇒ pads are under-filled**: when `npad` does not divide evenly the sum of floor quotas is less than the pad count; measured, 9 pads received only 8 units and the 9th sat idle; with the cumulative rounding `tk = floor(npad x cu / sum)` all 9 pads get one [measured: knowledge/07-patterns/code/p09-luozi-v52-micro8.mlog:1-149].
5. **Measured closed loop of the hauling flagship**: with 8 polys at N=8, itemTake 55 times / itemDrop 48 times, all slots occupied, and the core and the drop point both being the same `core-shard` variable `st`/`cbc` [measured: knowledge/07-patterns/code/p09-haul-31slot-v27.mlog:1-988].

## Common misconceptions

- **"more slots means controlling more units"**: on a micro a hauling round of 155 statements ≈1.29 s is already pressed against the 1.5 s cooldown, so 31 slots merely leave headroom for N; in practice only ≈9 units can be on an effective beat at once [measured: knowledge/07-patterns/code/p09-haul-31slot-v27.mlog:1-988].
- **"`core` is a keyword"**: it is a variable name; you must assign it with `ulocate building core ... core` first, otherwise `ucontrol itemDrop core 999` is a permanent no-op.
- **"`sensor x @unit @type` stores the type object"**: it stores the **type content** (`flare`); taking `@name`/`@id` from a unit instance is always null, and it must be routed through `@type`.
- **"the signature slot can be skipped"**: the last line `jump N always 0 "aigenerated:…"` is an integrity marker; deleting it does not affect execution but makes the file's provenance unverifiable, and changing any statement requires re-signing.

## Related

- Architecture and liveness checks: [PATTERN.MULTI.001](P07-unit-multicontrol.md)
- Dispatch and tables: [PATTERN.COUNTER.001](P08-counter-architectures.md)
- Budget and frame slicing: [PATTERN.PERF.001](P06-performance.md), [MLOG.PERF.001](../06-mlog/M08-性能与限制.md)
- Unit control semantics: [MLOG.UNIT.001](../06-mlog/M07-单位与逻辑控制.md)
- Code directory: [code/](code/)
