---
id: PATTERN.COUNTER.001
title: "@counter advanced architectures and name tables: dispatch, shrink, building variable table"
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41,119,143-156,604-609,910-921,1247-1263"
  - "Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:228-236"
  - "Mindustry-Source/core/src/mindustry/logic/LAssembler.java:139-149"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:45,48,607-636,644-650"
  - "Mindustry-Source/core/src/mindustry/entities/comp/UnitComp.java:316-328"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6872-6881"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16"
data: []
depends: [PATTERN.MULTI.001, PATTERN.ARCH.001, PATTERN.PERF.001, EXEC.MEM.001]
tags: [@counter, dispatch, fixed-stride-slot, building-variable, name-table, unit-multicontrol, architecture]
tokens: 1609
---

## One line

@counter is the only primitive in mlog that can "compute the next address": make each controlled object's body a **fixed-stride slot**, compute the offset once and fall from slot N down to slot 1, so one round = `3 + N x stride + 1` statements; and the building variable space (`read`/`write @this <name>`) is the only table that can hold **objects** — using a runtime-computable string (a unit type name) as the row key lets you walk units without hard-coding any type literal. What it buys is maintainability, not a higher ceiling.

## Rules / formulas

### 1. Fixed-stride dispatch

```text
一圈条数      = 3 + N x stride + 1        (3 = 热入口/守卫，1 = 循环尾)
单对象周期(s)  = stride / (60 x ipt)
一圈耗时(s)    = 一圈条数 / (60 x ipt)
```

@counter increments **before** the instruction's `run()`, so while instruction i executes it is always i+1; writing @counter inside an instruction therefore sets the next one exactly [src: LExecutor.java:119]. Slots must be laid out **in descending order** (slot N first, slot 1 last) so the pointer walks forward the whole way without a mid-way jump.

**Relative dispatch** is recommended (1 statement per round; the displacement is computed once at init):

```mlog
init:  op mul tmp.hp N -stride
       op sub tmp.hp tmp.hp 3        # 表尾 3 条：时间闸门 / 判空守卫 / 本加法
...
uN:    ...                          # 槽 N
...
u1:    ...                          # 槽 1
gate:  jump refill greaterThanEq @time cfg.next
hot:   jump gate strictEqual cfg.item null
       op add @counter @counter tmp.hp
```

**Absolute dispatch** (use when the table length changes, as in the live architecture below):

```mlog
init:  set tmp.base @counter
       op add tmp.off tmp.base (4 + slots*stride)
       op mul tmp.p N -stride
hot:   op add @counter tmp.off tmp.p
```

### 2. The stride account

`stride` is the fixed statement count per slot; changing any statement inside a slot means changing it too:

```text
stride = 12 (ubind / 判空 / 取货 / 投递 / 杂物 基本体)
       + 3  (顺路容器：ulocate storage + 判重 + itemTake)
       + 2  (短路径：拿到货才拐弯的 sensor + jump)
       + 1  (卸空标记 set tmp.needloc 1)
```

### 3. The health-check section dispatches too

If the "per-slot liveness check" before refill is written as one `jump ... greaterThan K N` guard per slot, the larger N gets the worse it is. Compute the entry address instead [src: LExecutor.java:119]:

```mlog
chk:   set tmp.cbk @counter
       op mul tmp.p N -2
       op add tmp.cbo tmp.cbk (3 + 2*n)
       op add @counter tmp.cbo tmp.p
```

chk is stored in descending order with 2 statements per slot (`sensor tmp.c @controller` + jump to fill when empty), saving N guards.

### 4. Table length = live count (live architecture)

The waste in a fixed slot table is the empty slots. Let L = the number of slots actually occupied, change the hot entry to `op mul tmp.p L -stride`, and shrink on death:

```text
收缩段（每槽 4 条，降序 shN..sh1）
shK:  jump sh(K-1) notEqual L K        # L != K，本级和我无关
      sensor tmp.c uK @controller      # 活着且归我？
      jump sh(K-1) equal tmp.c @this
      op sub L L 1                     # L 减 1 后正好匹配下一级，一趟连续收缩
```

The shrink entry uses `op mul tmp.p L -4` to compute @counter straight to level L, so only live levels run and the whole table is not scanned. Refill needs two guards: `jump hot greaterThan K N` (the user cap) and `jump hot lessThan L K-1` (density: only fill when K <= L+1), and after filling `op max L L K`.

### 5. Dual-speed ring (deprecated, kept for the criterion)

The fast ring costs 2 statements per object (cache the target coordinates, steer only), and the slow ring rotates 1 object per round for a full decision. It looks cheap but is pinned by the "slow block statement count":

```text
单对象周期(慢环) = (N x stride_slow + 快环条数) / (60 x ipt)
                = (8 x 22 + 23) / 120 ≈ 1.66 s   >   单环全判 1.06 s
```

The 22-statement slow block already exceeds one object's whole block in the single-ring architecture, so rotating decisions can never catch up with full decisions; it can only win when N is tiny. **Conclusion: the single ring (1) wins.**

### 6. Name table (the building variable space used as a table)

The table is the processor's own variable space; the row key is a **runtime-computable string**, the row value is any object (units and buildings both work).

```mlog
hot:  set tmp.i 0
row:  lookup unit tmp.ty tmp.i        # i -> 单位类型（内容注册表，非实例）
      sensor tmp.nm tmp.ty @name      # 类型 -> 名字字符串，这就是行键
      read u @this tmp.nm             # 按行键取行值
      jump next strictEqual u null    # 空行：6 条 / 3 tick
      ubind u                         # 拿到对象入口，只绑这一只
      ...
next: op add tmp.i tmp.i 1
      jump row lessThan tmp.i 50
```

Writing works the same way: `write @unit @this tmp.nm`. The row key must **exist** in the program (be referenced by some statement) to enter the variable table [src: LAssembler.java:139-149], so either `set` it once at init or declare it at the end with `draw`:

```mlog
jump hot always
draw triangle dagger mace fortress scepter reign nova   # 不可达，仅声明（一行 6 个键）
```

The fallback order of `read @this <name>`: look in program variables first, and only when that fails treat it as a **link name** to find a building, where the last character must be a digit, otherwise null [src: LogicBlock.java:607-636]. `write @this <name>` only takes effect when a program variable matches; otherwise it is silently dropped [src: LogicBlock.java:644-650].

## Numbers

| Quantity | Value | Source |
|---|---|---|
| micro / logic / hyper budget | 2 / 8 / 25 statements per tick | [src: Blocks.java:6849,6856,6867] |
| Hard statement cap | 1000, excess silently truncated | [src: LExecutor.java:41] |
| Unit transfer cooldown | 1.5 s (90 tick), shared by take and drop | [src: LogicAI.java:16] |
| Fixed-stride slot stride (hauling body) | 20 statements (12 basic + 3 en-route + 2 short path + 2 empty test + 1 mark) | [measured: mlogc generator assertion] |
| One round at N=8 (relative dispatch program) | 155 statements = 1.29 s | [measured: static calculation + itrace] |
| Health-check dispatch | 2 statements per slot + 4 at the entry | [measured: mlogc --dispatch] |
| live architecture capacity | 29 slots in 999 statements; 30 slots exceeds 1000 | [measured: generator statistics] |
| memory-cell / memory-bank capacity | 64 / 512 slots | [src: Blocks.java:6875,6881] |
| What one slot can hold | any object (v160 has the objectMemory array) or a number; out of range returns null | [measured: write @unit cell1 0 reads back a Unit] |
| Unit type registry | @unitCount 56, 49 non-empty names | [measured: probe_names full-table scan] |
| Row table empty / full row | 6 statements (3 tick) / 17 statements (8.5 tick) | [measured: itrace of both the 16-row and 51-row versions] |
| 50 rows + 5 units full scan | static 6x50+11x5+3 = 358 statements ≈ 179 tick; measured median 173 tick = 2.88 s | [measured: out/r50.itrace 800 tick] |
| 16 rows + 5 units | static 6x16+11x5+3 = 154 statements ≈ 77 tick; measured median 71 tick = 1.18 s | [measured: out/r16.itrace 300 tick] |
| Row table time budget | 6R + 11N <= 180 (R rows, N units) | [src: formula above + LogicAI.java:16] |
| Empty rows affordable within 1000 statements | about 130 rows | [measured: generator statistics] |

Where `6R + 11N <= 180` comes from: an empty row costs 6 statements and a full row adds 11, and one round must stay under the 1.5 s transfer cooldown (at 120 statements per second 1.5 s = 180 statements) [src: LogicAI.java:16].

## Source anchors

- LExecutor.java:119 — `instructions[(int)(counter.numval++)].run(this)`: increment first, execute second, the basis of every dispatch formula.
- LExecutor.java:41 — `maxInstructions = 1000`; loading and the editor both truncate by it.
- LExecutor.java:143-156 — `optionalVar`: looks a name up in `vars` and returns null when absent; both the read and the write of @this use it to decide "is the name a program variable".
- LExecutor.java:604-609 — the second argument of getlink is a 0-based index returning `exec.links[address]`; that is also the semantics of `read @this <number>`.
- LExecutor.java:910-921 — all 6 arguments of DrawI are LVars: every name in `draw` is treated as a variable, which is why it is also a declaration statement.
- LExecutor.java:1247-1263 — LookupI: `dest.setobj(logicVars.lookupContent(type, from.numi()))`.
- GlobalVars.java:228-236 — `lookupContent`: indexes the content registry, returns null when out of range or on an empty slot; team is handled separately.
- LAssembler.java:139-149 — `putVar`: any name referenced by a statement enters the variable table, defaulting to a null object.
- LogicBlock.java:607-636 — reading @this: `optionalVar` first, and only on null does it fall through to `optionalLink` (the last character of the name must be a digit).
- LogicBlock.java:644-650 — writing @this: if `optionalVar` is null or a constant it returns, dropping the write silently.
- UnitComp.java:316-328 — senseObject: `type` always, `name` only returns a name under player control, `controller` has three states; there is **no id branch**, so it falls to `default -> noSensed`.
- Blocks.java:6875,6881 — memory-cell 64 slots, memory-bank 512 slots [src: Blocks.java:6875,6881].

## Measurements and counter-examples

**Measurement 1 (dispatch probes)**: inserting `set dbg.sK 1` at each slot entry sets exactly 1 / 8 / 30 probes for N=1 / 8 / 30; `set N 40` is clamped to 31 slots by `op min N N 31` [measured: mlogsim 900 tick].

**Measurement 2 (live shrink)**: the numeric trace shows `96 jump 100 notEqual L 8` -> `97 sensor u8` -> `99 op sub` (L=7) -> `100 guard` -> `101 sensor u7` -> `103 op sub` (L=6) … a continuous shrink in one pass, with 8 units ending at L=8 [measured: out/probe_w.mlog 80 tick].

**Measurement 3 (row table)**: a 50-row table with 6 polys, 5 rows filled (dagger/mace/fortress/scepter/reign = Unit#212..#216), sx=59, st=the core, whole round median 173 tick (2.88 s); the same code with the row count cut to 16 gives a whole-round median of 71 tick (1.18 s) [measured: mlogsim v160.7, 800/300 tick].

**Counter-example 1 (relative dispatch placed at the table head)**: if the two op statements sit right at the start of the slot table, then when the add executes @counter = table head A and `+N*stride` lands on slot `slots-N`, so `slots-N` slots actually run (at slots=N it leaves the table entirely). They must go at the table end.

**Counter-example 2 (reusing the displacement variable)**: the health-check section writes `tmp.p` as `-2N` every round; if the hot dispatch also reads it, at N=8 the entry veers into the middle of the slots and all 30 probes stay empty. The hot dispatch needs a dedicated variable (such as `tmp.hp`).

**Counter-example 3 (taking @name / @id from a unit instance)**: both are null. `@name` only returns a player name when the unit is player-controlled [src: UnitComp.java:317], and `@id` has no branch at all; you must `sensor ty @unit @type` first and then `sensor nm ty @name`.

**Counter-example 4 (undeclared row key)**: a name that is neither `set` nor `draw`n makes `write` drop silently and `read` return null forever; more insidiously, `read @this <name>` degrades into a link-name building lookup, which returns null only if the last character is not a digit — if it is, you may read a completely unrelated building.

**Counter-example 5 (end-of-file declaration placed after the signature)**: the aigenerated id hash covers every statement except the signature statement, so appending draw after the signature line makes `verify` report body changed; the correct order is `strip` (remove the signature in place) -> `post` (re-sign), and draw must sit before the signature slot.

**Counter-example 6 (live architecture starting L at 0)**: `op mul tmp.p L -stride` with L=0 sends @counter spinning into the gate before the entry, so you must `set L 1` at startup and `op max L L 1` as a backstop.

**Counter-example 7 (expecting the row table to raise the ceiling)**: the row table does not change the time budget `6R + 11N <= 180`; with R=N it holds only 10 units. What it buys is "swapping unit types needs no recompile, row names are readable, rows can be sparsely trimmed".

## Common misconceptions

1. "lookup can find a building/unit by instance id" — it cannot. It indexes the **content registry**, and the only addressable key for an instance is the getlink index.
2. "@counter can be written with an expression" — it can only be assigned an arithmetic result; compute into a variable first and then `op add @counter <var> <var>`.
3. "draw only draws" — it is also a variable declaration, its arguments are the variables; but it does execute when reachable (drawing shapes, spending instructions), so declarations belong in unreachable code.
4. "the name given to @this must be a literal" — a runtime string variable works too (`read u @this tmp.nm`); only names that do not exist in the program degrade into link names.
5. "more slots is always better" — slot count is limited only by the 1000 statements, throughput by the transfer cooldown; beyond that, extra slots just queue.

## Related

- PATTERN.MULTI.001 unit multi-control (fixed-stride slots + the three @controller states + the hauling loop, the practical form of this article)
- PATTERN.ARCH.001 architecture overview (budget source and core splitting)
- PATTERN.PERF.001 performance and robustness (downclocking, rotation, liveness checks)
- EXEC.MEM.001 variables and memory boundaries (variable space, memory slots, object storage)
- MLOG.FLOW.001 control flow (jump semantics and @counter)
- MLOG.DRAW.001 drawing and text (draw's arguments are variables)
