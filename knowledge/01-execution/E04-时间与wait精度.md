---
id: EXEC.TIME.001
title: 'Time and wait precision: tick, seconds, and the frame delta'
domain: exec
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1206-1234
  - Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1236-1245
  - Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:564-579
data:
  - 06-mlog/instructions.json#instructions
  - 08-evidence/claims.jsonl#L1-29
  - 08-evidence/claims.jsonl#L1-30
depends: [EXEC.MODEL.001]
tags: [wait, tick, frame delta, time, precision]
tokens: 610
---

# E04 Time and wait precision

## In one sentence

The game clock has only **tick** (60 tick/s); `wait` takes its argument in **seconds**, but the real resolution is **1 tick** — so `wait 0.05` is not a precise 0.05 s wait, it is "stop for 3 tick". [src: knowledge/VERSION.md:1]

## Rules / formulas

### 1. The three WaitI branches (verbatim)

```java
// LExecutor.java:1218-1232
if(value.num() <= 0){          // wait 0 / 负数
    exec.yield = true;         //   让出本 tick
    curTime = 0f;              //   不 counter--，下 tick 重试同一条
}else if(curTime >= value.num()){
    curTime = 0f;              //   等待结束，继续下一条
}else{
    exec.counter.numval--;     //   回到自己
    exec.yield = true;
    curTime += Time.delta / 60f;  // 每 tick 累加 1/60 秒 [src: knowledge/VERSION.md:1]
}
```

| Branch | Condition | Budget | Next tick |
|---|---|---|---|
| Empty yield | v <= 0 | **not consumed** (yield breaks before `accumulator--`) | retries the same instruction |
| Wait finished | curTime >= v | normal | runs the next instruction |
| Keep waiting | anything else | not consumed | retries the same instruction |

### 2. Converting seconds → tick

Each tick adds 1/60 ⇒ **stop N tick ⇔ argument v ∈ ((N−1)/60, N/60]**, i.e. `tick count = ceil(v × 60)`.

| Form | Actual stop | Source (L1-29, measured) |
|---|---|---|
| `wait 0` | 1 tick (yield) | see L1-30 |
| `wait 0.001` / `wait 0.01` / `wait 0.0166` | **1 tick** | all three behave byte for byte identically |
| `wait 0.02` | 2 tick | measured: done first set at t4 |
| `wait 0.05` | 3 tick | t5 |
| `wait 0.1` | 6 tick | t8 |
| `wait 1` | **60 tick ≈ 1 s** | source conversion |

Measurement setup: the probe is `wait X` followed by `set done 1`, recording the tick at which done is first set (`out/_scratch/_wq_*.mlog`; the starting tick carries 2 tick of boot overhead). [src: knowledge/VERSION.md:1]

### 3. Frame delta (Time.delta)

- `Time.delta` is **this frame's game-time step** (in tick), = 1 at a normal 60 fps.
- When the server is paused or the main loop does not call `Time.update`, delta = 0 ⇒ `curTime` does not advance ⇒ **wait never finishes** (the same root as L3-06, "a paused world needs a manual Time.update or turrets will not fire").
- At a low frame rate the same `wait` spans fewer ticks (the 1/60 per tick is a constant while wall-clock time is longer) ⇒ the logic beat **slows down** during a stall.

### 4. stop / end

| Instruction | Behaviour | Difference |
|---|---|---|
| `stop` | `counter--; yield; stop=true` | halts at **this** instruction until resumed from outside |
| `end` | counter back to 0 | restarts from instruction 0 |
| `wait 0` | yield | continues at the next one (it does not halt in place) |

### 5. Lower bound on delay

- The minimum gap between any two instructions = 1 tick (16.7 ms), unless the pool has leftover points within the same tick. [src: knowledge/VERSION.md:1]
- Cross-processor sync: the execution order within one tick is **undetermined** (L3-05, open) ⇒ do not assume a handshake-free "A writes, B reads right after".

## Numbers

| Quantity | Value | Source |
|---|---|---|
| tick rate | 60 /s (client) | conversion convention |
| 1 tick | 1/60 s ≈ 16.7 ms | VERSION.md unit convention |
| wait unit | seconds | LExecutor.java:1231 |
| wait resolution | 1 tick | L1-29, measured |
| Accumulation step | Time.delta/60 | LExecutor.java:1231 |

## Source anchors

| Location | Content |
|---|---|
| LExecutor.java:1218-1232 | WaitI.run's three branches (as in the table above) |
| LExecutor.java:1236-1245 | StopI: counter-- + yield + stop |
| LExecutor.java:1224 | the idle branch resets curTime (comment: value may be changed by another processor) |
| LogicBlock.java:564-579 | yield breaks before accumulator-- |
| Time.java (engine) | delta is the unit time step; it is not updated while paused |

## Measurements and counter-examples

- ✅【E】`wait 0.001/0.01/0.0166` behave identically (1 tick), and `0.02→2`, `0.05→3`, `0.1→6` (L1-29). [measured: assertion table (docs/断言表.md)]
- ✅【E】`wait 0` only yields and does not `counter--` (L1-30); the next execution is still this instruction, and no budget is spent.
- Counter-example (a boundary that does not hold): **"wait 0 loops forever without stalling" is false** — it still takes one instruction's scheduling slot per tick, and after the yield the rest of this tick's pool is not executed (yield breaks immediately).
- Counter-example: **"wait is a precise sleep" is false** — while paused or at a low frame rate curTime does not advance, and wait "oversleeps".
- 【U】The real wall-clock duration of wait on a multiplayer server below 60 tick/s is unmeasured; a dedicated-server timing experiment is needed.

## Common misconceptions

1. "wait 1 is 1 tick" — it is **1 second = 60 tick**; for 1 tick write `wait 0.0166`.
2. "the wait unit is tick" (an old manual / some documents) — both `curTime += Time.delta/60f` and the comparison value are in seconds in the source, and L1-29 confirmed it by measurement.
3. "wait 0 is a no-op" — it carries yield semantics and affects the rest of that tick's budget.
4. "logic keeps running while the game is paused" — with delta=0, wait and every time-dependent instruction stall.

## Related

- M03 Control flow (using wait inside loops)
- M08 Performance and limits (latency and throughput)
- E01 Execution model and budget
