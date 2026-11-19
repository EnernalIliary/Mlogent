---
id: PATTERN.ARCH.001
title: Blueprint architecture overview: budget, layering, topology
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:45,48,560-580"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6849,6856,6867,6954,6958"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41"
  - "mindustry-blueprint/PATTERNS.md:114-311"
data: []
depends: []
tags: [architecture, processor, ipt, budget, layering]
tokens: 587
---

## One line

The capability ceiling of a single processor is the "ipt x edelta" instruction budget (backlog never exceeds 5 x ipt), so architecture has exactly one main line: first squeeze "state size x rounds per second" into the budget; only when that fails do you split processors — and after splitting, communication overhead is necessarily larger than compute overhead.

## Rules / formulas

The number of statements actually executed per tick is not a fixed value but a budget accumulated from the time delta (LogicBlock.java:560-580):

```text
accumulator += edelta() * ipt
if (accumulator > 5 * ipt) accumulator = 5 * ipt   // backlog cap
while (accumulator >= 1) { runOnce(); accumulator--; }
```

Three computable rules:

1. Throughput: rated statements/second = 60 x ipt (1 tick = 1/60 s).
2. Acceleration: when the game runs faster, edelta() grows and more statements run in the same tick — logic behaviour changes with speed.
3. Split criterion: if "total statements x rounds per second required" > 60 x ipt, you must split across processors.

Layering (four layers, each doing one thing):

| Layer | Carrier | Responsibility | Invariant |
|---|---|---|---|
| Compute | processor (micro/logic/hyper/world) | runs logic only | statement count <= 1000 |
| Shared | memory-cell / memory-bank, or processor variable space | exchanges state across processors | indices hand-assigned, non-overlapping |
| Human | switch1 + @enabled | manual start/stop | shutting down costs one end, the cheapest ipt |
| Output | display / message block | write only, never read | committed by drawflush / printflush |

Only three topologies are maintainable: single-core monolith, dispatcher core + N control cores, and world-processor driven. Point-to-point mutual @counter writes and ring multi-master sit in the unmaintainable range.

## Numbers

| Processor | Default @ipt | Rated statements/s | Link radius | Size | Note |
|---|---:|---:|---|---|---|
| micro-processor | 2 | 120 | 10 tiles | 1x1 | cheapest, suits small state machines |
| logic-processor | 8 | 480 | 22 tiles | 2x2 | medium hauling / unit control |
| hyper-processor | 25 | 1500 | 42 tiles | 3x3 | needs coolant, carries heavy compute |
| world-processor | 8 | 480 (60000 after setrate 1000) | whole map | 1x1 | privileged: build/rules/cross-team |

@ipt is verified against source (Blocks.java:6849/6856/6867/6954); link radius and size come from mindustry-blueprint/PATTERNS.md:139-142, which cites no source line and is second-hand data — hence @ipt is conf=S while radius is conf=I.

## Source anchors

- LogicBlock.java:45 `maxInstructionScale = 5` — backlog cap multiplier.
- LogicBlock.java:48 `maxInstructionsPerTick = 40` — default cap; only the world processor is raised.
- LogicBlock.java:560-580 — the budget accumulate/clamp/consume main loop; wait breaks here.
- Blocks.java:6958 `worldProcessor.maxInstructionsPerTick = 1000`.
- LExecutor.java:41 `maxInstructions = 1000` — hard per-processor statement cap.

## Measurements and counter-examples

Processor distribution in the real corpus (../../logic-corpus/_index.json: 430 blueprints, 5774 logic blocks, 3,719,102 statements):

| Processor | Logic blocks | Share |
|---|---:|---:|
| micro-processor | 4823 | 83.5% |
| world-processor | 545 | 9.4% |
| logic-processor | 352 | 6.1% |
| hyper-processor | 54 | 0.9% |

After dropping pure pixel art, 1081 real logic blocks remain (the same scan scope recorded in mindustry-blueprint/PATTERNS.md:1933). In other words: 83.5% of logic blocks run on a micro with only 2 ipt — the first goal of architecture is not to compute fast, but to compute only a little each tick.

**Counter-example (miscalculated budget)**: a micro-processor (2 ipt) linked to 100 turrets and iterating all of them every tick needs 100 statements/tick against a budget of 2 statements/tick, so one pass takes 50 ticks. The fix is rotating links (touch 1 per tick, one pass in 100 ticks is about 1.7 s); see PATTERN.PERF.001.

## Common misconceptions

1. "@ipt is a fixed number of statements per frame" — wrong, it is a per-tick budget scaled by edelta(); after a stall at most the equivalent of 5 ticks is made up at once.
2. "setrate works on any processor" — wrong, setrate is a privileged instruction that only takes effect on the world processor and is clamped to clamp(v,1,1000).
3. "1000 statements is just a guideline" — wrong, parsing stops at 1000 and the excess is silently dropped without an error.
4. "splitting processors is always faster" — wrong, cross-core exchange only goes through read/write (one instruction per value plus sync latency), and @controlled cannot tell which processor is in control (see PATTERN.COMM.001).

## Related

- PATTERN.STATE.001 state machine (@counter dispatch)
- PATTERN.COMM.001 communication and bus
- PATTERN.PERF.001 performance and robustness
- EXEC.MODEL.001 execution model
- 08-evidence/idioms.json: original provenance of this article's idiom entries (30 entries, with src/ver)
