---
id: PATTERN.PERF.001
title: Performance and robustness: budget allocation, downclocking, self-recovery
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:560-580,826"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:18"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41,763"
  - "mindustry-blueprint/PATTERNS.md:496-517,777-804,1126-1149,2134-2149"
data: []
depends: [PATTERN.ARCH.001, PATTERN.STATE.001]
tags: [performance, budget, downclock, rotation, robustness, self-recovery]
tokens: 636
---

## One line

A performance problem in mlog is equivalent to "how many statements this tick are fighting over 2/8/25 statements of budget": downclock first (run every few ticks), then rotate (touch only a small slice each tick), and only then split cores; robustness requires that every external reference (unit, building, target) be liveness-checked before each use, with a cap on retries.

## Rules / formulas

Budget allocation formulas:

```text
单 tick 可用条数 K = ipt * edelta（正常速度下 edelta = 1）
每秒可用条数 = 60 * ipt
需要的轮转周期 T = 语句总数 / ipt   (tick)
```

Four cost-reduction moves (ordered by payoff):

1. Downclock: gate on @second / @time, turning "check every tick" into "check every N ticks".
2. Rotate: handle only 1 link / 1 turret per tick, index it with `op mod i i @links`, and leave the spare budget for logic.
3. Early exit: when a condition fails use end instead of looping with jump, and test the cheapest condition first.
4. Split cores: separate targeting, hauling and display into different processors and exchange conclusions through memory slots (see PATTERN.COMM.001).

The three-part failure detection kit:

- Before each use, test null and test death (null, @dead, @controller — three states).
- Cap retries (the corpus rebinds dead units with try <= 3).
- Self-recovery: on detecting N consecutive rounds without progress, reset the state machine to its initial state instead of retrying in place.

## Numbers

| Quantity | Value | Source |
|---|---|---|
| micro / logic / hyper budget | 2 / 8 / 25 statements per tick (120 / 480 / 1500 per second) | Blocks.java:6849/6856/6867 |
| world budget cap | setrate max 1000 → 60000 statements per second | [src: Blocks.java:6958] |
| Backlog cap | 5 x ipt | [src: LogicBlock.java:45] |
| Hard per-processor statement cap | 1000 | [src: LExecutor.java:41] |
| Rotating 100 turrets once | 100 tick, about 1.7 s | mindustry-blueprint/PATTERNS.md:512 |
| Dead-unit rebind retry cap | 3 times | mindustry-blueprint/PATTERNS.md:777-804 |
| Logic-controlled unit timeout | 10 s (600 frames) | [src: LogicAI.java:18] |

## Source anchors

- LogicBlock.java:560-580 — the accumulator main loop; `wait` takes the yield branch and breaks, discarding this tick's remaining budget.
- LogicBlock.java:826 — `write.s(Mathf.clamp(ipt,1,maxInstructionsPerTick))`, the displayed value is clamped to 40 (1000 for world).
- LExecutor.java:763 — the 30 tick refresh window, meaning "not every sensor is really read every tick".

## Measurements and counter-examples

Standard "rotate + liveness check" skeleton:

```mlog
# 每 tick 只处理一个链接，@links 为链接总数
op mod i i @links
getlink b i
jump 跳过 equal b null
sensor alive b @enabled
jump 跳过 equal alive false
control shoot b target 1
跳过:
op add i i 1
end
```

**Counter-example (full scan of 100 turrets every tick)**: a micro at 2 ipt needs 50 ticks per pass, so the real fire rate is dragged down by logic, and during a stall the backlog grows to the 5 x ipt cap and then bursts all at once. In the corpus 95 logic blocks use rotation (PATTERNS.md:496-517).

**Counter-example (burning the budget in a dead loop)**: `jump 0 equal @unit null` is an in-place dead loop when no unit is bound; it spends the whole per-tick budget and blocks every other piece of logic on the same processor (listed as a real bug in PATTERNS.md:2134-2149). Rule: every binding loop must have an exit for "not found".

**Counter-example (unbounded retries)**: with dead-unit rebinding and no try cap, once no bindable unit exists the code stays stuck in the rebind branch forever; the corpus uses try <= 3 and then gives up and returns to the idle state.

Blueprint reload (conf=U): whether @counter, variables and memory-building contents survive after a processor block is overwritten by a blueprint has not been measured by this library yet; it needs a three-step experiment of "deploy -> run to state X -> overwrite the same processor -> read the state". Until it is verified, engineering practice should assume reload resets everything and perform an explicit initialisation handshake (the init branch of PATTERN.STATE.001).

## Common misconceptions

1. "wait only delays; the budget is paid back later" — wrong, wait takes the yield path, this tick's remaining budget is discarded and does not accumulate.
2. "if the processor displays 40 ipt it really runs 40" — wrong, that is the clamped display cap; the real value is the ipt configured on the block.
3. "once logic controls a unit it can never be lost" — wrong, 10 s without refreshing control returns it to AI (LogicAI.java:18).
4. "downclocking drops events" — it does. Before downclocking, confirm the state is "pollable" rather than "must be captured" (the latter needs event-style code or a shorter period).

## Related

- PATTERN.ARCH.001 architecture overview (where the budget comes from)
- PATTERN.STATE.001 state machines (initialisation handshake)
- PATTERN.TARGET.001 radar and targeting (30 tick cache)
- 08-evidence/idioms.json: original provenance of this article's idiom entries (30 entries, with src/ver)
