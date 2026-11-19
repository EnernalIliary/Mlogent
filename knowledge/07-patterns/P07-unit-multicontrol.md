---
id: PATTERN.MULTI.001
title: Unit multi-control: @counter dispatch, @controller liveness checks, hauling loop
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41,119,186-205,252-279,322-340,352,523,539,604-609"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16,18,59-63,70-72"
  - "Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:190"
  - "Mindustry-Source/core/src/mindustry/Vars.java:125"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6849,6856,6867"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:45,48"
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:964-965"
  - "Mindustry-Source/core/src/mindustry/content/UnitTypes.java:1046-1047"
  - "Mindustry-Source/core/src/mindustry/entities/units/AIController.java:383-408"
data: []
depends: [PATTERN.ARCH.001, PATTERN.STATE.001, PATTERN.PERF.001]
tags: [unit-multicontrol, single-processor, @counter, dispatch, refill, hauling, liveness, latency-limit]
tokens: 1400
---

## One line

When one processor controls N units, response speed is decided not by the total statement count but by **statements per unit per round**: compute the next address in one step with @counter (skipping every empty slot), use the three @controller states for liveness checks and atomic claiming, and push refill and building location out of the hot loop — then one round compresses to `3 + N x stride + 1` statements.

## Rules / formulas

Statements and elapsed time per round (ipt = instructions per tick):

```text
一圈条数   = 3 + N x stride + 1        (3 = 热入口，1 = 循环尾门控)
一圈耗时(s) = 一圈条数 / (60 x ipt)
单单位周期(s) = stride / (60 x ipt)
N 的吞吐上限 = 60 x ipt x transferDelay / stride
```

**Dispatch**: @counter increments **before** the instruction's `run()`, so while instruction i executes @counter is always i+1; writing @counter inside an instruction therefore sets the next one exactly [src: LExecutor.java:119].

Two spellings; **relative dispatch** is recommended (default since v27):

```mlog
# ① 相对：槽表末尾只剩一条加法，tmp.hp 在 init 算一次
init:     op mul tmp.hp N -stride
          op sub tmp.hp tmp.hp 3      # 表尾 3 条：时间闸门 / 物品空守卫 / 本加法
...
gate:     jump refill greaterThanEq @time cfg.next
hot:      jump gate strictEqual cfg.item null
          op add @counter @counter tmp.hp
```

```mlog
# ② 绝对：每圈 2 条 + init 2 条（live 架构用，L 会变）
set tmp.base @counter
op add tmp.off tmp.base (4 + slots*stride)
op mul tmp.p N -stride
op add @counter tmp.off tmp.p
```

Slots must be laid out **in descending order** (slot N first, slot 1 last) so that @counter falls from slot N through to slot 1 without jumping mid-way. N is set by `set N`, clamped with `op min N N slots` / `op max N N 1`, so an out-of-range value cannot land outside the program.

> ⚠ Two pitfalls of relative dispatch (both hit in measurements):
> ① Those two op statements must sit at the **end of the slot table**. With them at the head, the moment the add executes @counter = table head A, and `+`N*stride lands on slot slots-N, so slots-N slots run (at slots=N it leaves the table entirely) — written as `op mul tmp.p N stride` and added it looks right, but in practice it "skips N slots".
> ② The displacement variable must not be shared with anything else: the health-check section (the chk dispatch) writes `tmp.p` as -2N every round, the hot dispatch then reads -16, and at N=8 the entry veers into the middle of the slots (the trace shows landing at 604 instead of u8's 457), with not one of the 30 dbg probes set. Give the hot dispatch its own `tmp.hp`.

**Three liveness states** (the @controller return value is the identity):

| @controller | Meaning | Action |
|---|---|---|
| `@this` | alive and owned by this processor | use it directly |
| `null` | unit is dead / never claimed | go to refill |
| any other object | alive but taken by other logic | the next ucontrol rewrites controller and takes it back [src: LExecutor.java:322-340] |

**Refill**: `ubind <type>` -> `sensor tmp.c @unit @controller` -> accept only when `tmp.c == @unit` (a free unit), then `set uK @unit` immediately followed by any ucontrol to stamp it. Every ucontrol executes `la.controller = exec.thisv.building()` [src: LExecutor.java:325], so "claim + stamp" happens in the same stretch of instructions and collisions within one tick are naturally atomic. Refill is gated on `@time` (`jump hot lessThan @time cfg.next`, zero extra cost in steady state) with a 2 s period, well under the 10 s loss-of-control timeout.

**Hauling loop (20 statements per slot, externalised state)** — no bookkeeping; the state is derived from the cargo hold:

```mlog
u8:  ubind u8
     sensor tmp.f @unit @firstItem          # 手里有什么就是什么状态
     jump u8d notEqual tmp.f null           # 有货 -> 投递腿
     ucontrol approach sx sy 6.5            # 空手 -> 去货源
     ulocate building storage 0 0 vx vy tmp.g2 vault   # 顺路容器，此刻离本单位最近
     jump u8k equal vault tmp.lnk           # 容器==投递目标就跳过，防原地倒腾
     ucontrol itemTake vault cfg.item 999
u8k: ucontrol itemTake st cfg.item 999      # 6 格内才生效，远了是 no-op
     sensor tmp.f @unit @firstItem
     jump u8e strictEqual tmp.f null        # 没拿到就别拐弯
u8d: jump u8j notEqual tmp.f cfg.item       # 手里不是该拿的货 -> 杂物腿
     ucontrol approach lx ly 6.5
     ucontrol itemDrop tmp.lnk 999
     sensor tmp.f @unit @firstItem
     jump u8e notEqual tmp.f null           # 没卸掉就留在投递点，别发返回指令
     set tmp.needloc 1                      # 卸空 = 下一个定位时机
     ucontrol approach sx sy 6.5
     jump u8e always
u8j: ucontrol approach cbx cby 6.5
     ucontrol itemDrop cbc 999              # 杂物倒回核心
u8e:
```

## Numbers

| Quantity | Value | Source |
|---|---|---|
| micro / logic / hyper budget | 2 / 8 / 25 statements per tick (120 / 480 / 1500 per second) | [src: Blocks.java:6849,6856,6867] |
| Backlog cap | 5 x ipt (maxInstructionScale) | [src: LogicBlock.java:45] |
| Hard per-processor statement cap | 1000 statements, excess silently truncated | [src: LExecutor.java:41] |
| Display ipt cap | 40, privileged (world processor) only | [src: LogicBlock.java:48] |
| Unit transfer cooldown | 1.5 s (90 tick), itemTake and itemDrop share one timer | [src: LogicAI.java:16] |
| Logic-control loss timeout | 10 s (600 tick) | [src: LogicAI.java:18] |
| Item interaction distance | 45 + size x 4 world units (1x1 = 49 = 6.1 tiles, 3x3 core = 57 = 7.1 tiles) | [src: LExecutor.java:523,539; Vars.java:125] |
| approach stopping distance | moveRad - 7 world units; 6.5 tiles -> 52 - 7 = 45 (5.6 tiles) | [src: LogicAI.java:70-72; LExecutor.java:352] |
| @time unit | milliseconds (state.tick / 60 x 1000) | [src: GlobalVars.java:190] |
| flare cargo / poly cargo | 10 / 36 (automatic formula max(round(hitSize x 4), 10)) | [src: UnitTypes.java:1047; UnitType.java:964-965] |
| One round at N=8, stride=20 | 164 statements = 82 tick = 1.37 s (micro) | [measured: static calculation + mlogsim itrace] |
| 30 slots full on the same program | 987 statements (within the 1000 cap) | [measured: line count before check_kb] |
| N throughput cap on micro | 60 x 2 x 1.5 / 20 = 9 units | [src: formula above + LogicAI.java:16] |

## Source anchors

- LExecutor.java:119 — `instructions[(int)(counter.numval++)].run(this)`; @counter increments before execution, which is the whole basis of the dispatch formula.
- LExecutor.java:186-205 — ubind: the type branch advances a per-processor ring `exec.binds[type.id]`; the object branch only checks same team + logicControllable; if neither holds, `exec.unit.setconst(null)`. Binding into an empty slot does not inherit the previous unit.
- LExecutor.java:322-340 — checkLogicAI: every ucontrol requires `unit.isValid() && exec.unit.obj() == unit`, and on success does `la.controller = exec.thisv.building()`. That is the mechanism behind "any ucontrol re-stamps" and "take back a stolen unit".
- LExecutor.java:252-279 — ulocate building: picks `Geometry.findClosest` by flag only, the ore argument takes no part; the failure branch only writes outFound=0, **not one byte of outX/outY is written**.
- LExecutor.java:523 / :539 — itemDrop / itemTake both first check `unit.within(build, 45 + size*4)`; itemTake also requires the second argument to be `instanceof Item`, so null is a straight no-op.
- LExecutor.java:604-609 — the second argument of getlink is a **0-based index**, not a link name.
- LogicAI.java:59-63 — `controlTimer > 0 && controller != null && controller.isValid()`, otherwise resetController; the refresh comes from every ucontrol.
- LogicAI.java:70-72 — approach = `moveTo(moveRad - 7, 7, keepDistance=true)`.
- AIController.java:383-408 — `length = clamp((dst - circleLength)/smooth, -1, 1)`, and when `length < -0.5` it does `vec.rotate(180)`: entering the inner side of the ring makes it turn and fly back out [src: AIController.java:390,405-408].

## Measurements and counter-examples

Measurement (real Mindustry v160.7 executor, mlogsim) [measured: 8 flares, 8-slot program, 200 tick]: u1..u8 all occupied, sx/sy = 59,59, st = cbc = the core, @counter matches the dispatch prediction; in the itrace consecutive `ubind u8` occurrences are 34~62 tick apart [measured: itrace 500 tick], so 164 statements are only the **full-slot upper bound**; short paths make it shorter.

**Counter-example 1 (ulocate is a unit instruction and is silently skipped when @unit is empty)**: putting `ulocate` before `ubind`, or calling ulocate in a trailing slot after @unit has been bound to null, leaves sx/sy at their init values (often written as @thisx/@thisy) in the former case, and **the whole squad flies to the processor's own tile**. Invisible when N happens to equal the unit count, always visible when N is larger. Fix: in the location section do `ubind <type>` first and then test `@unit != null`, or bind a slot variable already known to be yours.

**Counter-example 2 (unconditionally issuing the return instruction after itemDrop fails)**: `itemDrop` is only an attempt — too much distance or an unfinished 1.5 s cooldown fails silently [src: LogicAI.java:16], and an `approach sx sy` issued later in the same stretch immediately overwrites the preceding `approach lx ly`, so the unit never reaches the drop point. Fix: read `@firstItem` right after the drop and `jump` to stay at the drop point when it is non-empty.

**Counter-example 3 (treating core as a keyword)**: in `ucontrol itemDrop core 999` the `core` is a variable name, not a keyword, so it is null when undefined -> a permanent no-op. You must first fetch the building object into a variable with `ulocate building core ...` and then drop.

**Counter-example 4 (passing a name to getlink)**: `getlink tmp.lnk sorter1` gets parsed by `numi()` as an illegal index and returns null. The correct form is `getlink tmp.lnk 1`.

**Counter-example 5 (the refill section jumping to hot after each slot)**: each refill burst fills only 1 slot, so the table never fills up. After filling, fall through to the next fill label and continue.

**Counter-example 6 (no jump back to the hot loop at the end)**: when the program runs off the end @counter returns to 0, init runs again from the top, and N, sx/sy and cfg.nloc are all reset, which shows up as the units losing their target periodically.

**Counter-example 7 (itemTake right after a unit spawns always fails the first time)**: `ItemTakeI` calls `timeoutDone(unit, transferDelay)` on entry, and `transferDelay = 90 tick` is measured from `Time.time`; when the unit is newborn that timestamp has not advanced far enough, so a single `itemTake` **fails silently** and only succeeds on retry about 30–40 tick later [measured: 2 flares next to the core, @firstItem recorded every tick]. So the hauling section cannot be "bind and take": either retry in a loop until `@firstItem` is non-empty, or keep the pickup section inside the hot loop (it retries every round and self-heals naturally).

## Common misconceptions

1. "a micro can be sped up with setrate" — it cannot; setrate is a privileged instruction that only takes effect on the world processor [src: LogicBlock.java:48].
2. "control is lost as soon as ucontrol stops" — no; any ucontrol within 10 s (even a no-op such as payDrop) refreshes the timer [src: LogicAI.java:18,59-63].
3. "@controller == @this proves the unit is alive" — it proves "alive and mine"; a dead unit and a stolen unit are null and some other object respectively, and the three cases must be handled separately.
4. "move and approach are equivalent" — approach carries keepDistance and turns back outwards once inside `moveRad - 7 - 3.5` [src: LogicAI.java:70-72; AIController.java:405-408]; use move when you want to get close.
5. "fewer statements always means faster response" — as long as one round is under the 1.5 s transfer cooldown [src: LogicAI.java:16], cutting further buys no throughput; at that point what must shrink is "statements per unit per round", not "total statements".
6. "ulocate finds ore by the ore argument" — in the building branch the ore argument takes no part at all; it only finds the nearest friendly/hostile building by flag [src: LExecutor.java:252-256].

## Related

- PATTERN.ARCH.001 architecture overview (budget source and core splitting)
- PATTERN.STATE.001 state machines (initialisation handshake, power-loss recovery)
- PATTERN.PERF.001 performance and robustness (general practice for downclocking, rotation, liveness checks)
- 04-units/U03 unit AI and controllers (where the three @controller states come from)
- 01-execution/E01 execution model and budget (ipt, backlog, @counter semantics)
