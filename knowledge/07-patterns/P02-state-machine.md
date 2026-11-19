---
id: PATTERN.STATE.001
title: State machines: enums, transition tables, @counter dispatch
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/logic/LParser.java:112-176"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41"
  - "mindustry-blueprint/PATTERNS.md:313-455"
data: []
depends: [PATTERN.ARCH.001]
tags: [state-machine, jump, label, counter, jump-table]
tokens: 591
---

## One line

An mlog state machine has only two maintainable spellings: enumerated states plus a chain of jump equal (statement count grows linearly with state count, but it stays readable and editable), or fixed-offset @counter dispatch (O(1), but inserting one instruction shifts everything). Choose the former by default; reach for the latter only when the ipt budget is pinned.

## Rules / formulas

Labels are compiled into line numbers at import time (two passes): the first pass scans "name:" recording line numbers and emitting no statements, the second replaces jump targets with numbers. Three corollaries:

1. A label does not occupy a statement slot and does not consume @ipt — it is not an instruction at all.
2. Code parsed out of a blueprint has numeric jump targets; the label names are gone.
3. @counter is writable, so the next address can be computed at runtime.

jump semantics: condition true → @counter = target; false → @counter += 1. Available conditions: equal (1e-6 float tolerance), notEqual, lessThan(Eq), greaterThan(Eq), strictEqual (strict type + value comparison), always (ignores the last two arguments).

### Spelling A: enum + transition table (default, about 3N statements)

```mlog
# state: 0=待机 1=取货 2=返航
jump 待机 equal state 0
jump 取货 equal state 1
jump 返航 equal state 2
set state 0
end
待机:
set state 1
end
取货:
set state 2
end
返航:
set state 0
end
```

At N=10 that is about 30 statements; even a micro processor at 2 ipt completes a full cycle within one tick.

### Spelling B: fixed-offset @counter dispatch (O(1))

```mlog
# state 属于 [0,N)，每个分支恰好占 1 条语句
op add @counter @counter state      # 执行后 @counter 还会自动 +1
jump 20 always 0 false              # state=0 的落点
jump 24 always 0 false              # state=1 的落点
jump 28 always 0 false              # state=2 的落点
```

Two hard constraints: every branch body must be exactly the same length (otherwise scale with op mul; ILI反病毒.msch uses the variant where each slot occupies 2 statements); inserting or deleting any single instruction invalidates all offsets.

## Numbers

| Quantity | Value | Source |
|---|---|---|
| Per-processor statement cap | 1000 statements, excess silently truncated | LExecutor.java:41; PATTERNS.md:295 |
| Label count cap | 500 (maxJumps) | mindustry-blueprint/PATTERNS.md:307 |
| Unresolved label | target = -1, the jump does not jump, equivalent to noop | same |
| @counter trick usage in corpus | 39 places | mindustry-blueprint/PATTERNS.md:405 |

The equal tolerance is 1e-6; object comparison goes through Structs.eq, and null does not equal 0.

## Source anchors

- LParser.java:112-176 — two-pass parsing: jumpLocations.put(label, line) first, backfill afterwards.
- LExecutor.java:41 `maxInstructions = 1000`.
- LStatements.java — JumpI modifies @counter; an unknown instruction lands in InvalidStatement, equivalent to noop.

## Measurements and counter-examples

The 39 @counter computations in the corpus cluster in three blueprints (ILIOS.msch, ILI反病毒.msch, ILI集火逻辑.msch), and not one carries a comment (mindustry-blueprint/PATTERNS.md:453). That is not a style preference; it is the signal that "the author can no longer read it either".

**Counter-example one (label landing in nothing)**: when a label sits at the very end of the file with no instruction below it, its line number equals the statement count, and jumping there overruns @counter and resets it to 0 — effectively jumping back to the start, with unpredictable behaviour. Rule: put at least one instruction under every label, and close branches with end.

**Counter-example two (treating end as optional)**: running off the end behaves the same as end (overrun returns to 0 automatically), but end is the cheapest way to shut down — with the switch off, a single end finishes this tick, far cheaper than looping around with jump.

## Common misconceptions

1. "@counter is unchanged when a jump is false" — wrong, it goes +1 to the next instruction.
2. "a label occupies an instruction slot" — wrong, it is consumed in the first pass; it neither counts as a statement nor toward the 1000 cap.
3. "equal and strictEqual are equivalent" — wrong. To test "is this the same object" you must use strictEqual (such as strictEqual c @unit); equal uses numeric tolerance.
4. "a state machine must use @counter to be fast" — wrong. On a 2 ipt budget a 30-statement enum state machine completes within two ticks; O(1) dispatch only pays off once statement counts reach the thousands.

## Related

- PATTERN.ARCH.001 architecture overview (where the budget comes from)
- PATTERN.PERF.001 performance and robustness (downclocking, debouncing)
- MLOG.FLOW.001 jump and label semantics
- 08-evidence/idioms.json: original provenance of this article's idiom entries (30 entries, with src/ver)
