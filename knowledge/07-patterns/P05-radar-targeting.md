---
id: PATTERN.TARGET.001
title: Radar and targeting: filter/sort/order combinations and range checks
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:761-763"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:18"
  - "mindustry-blueprint/PATTERNS.md:1250-1323,936-960,2027-2043"
data: []
depends: [PATTERN.COMM.001]
tags: [radar, targeting, focus-fire, range, uradar, target]
tokens: 532
---

## One line

A single radar instruction already does "filter + sort + take the first", so correct targeting is "use filter to exclude impossible targets, use sort to set priority, use order to set direction" rather than pulling every unit into an array and sorting it yourself; the price is that radar results sit in a 30 tick cache window, so range must be checked again by hand.

## Rules / formulas

Instruction signature (7 arguments):

```text
radar <target1> <target2> <target3> <sort> <order> <source> <output>
```

- target1/2/3: three filters, logically ANDed, may be any to mean no filtering; common values are enemy, ally, player, attacker, flying, ground, boss, spawn.
- sort: distance, health, shield, armor, maxHealth.
- order: 1 = near to far (take the nearest), 0 = far to near. This is the argument people most often get backwards.
- source: the radar source building (a turret/unit/radar linked to the processor), which must itself be radar-scannable; output is a single target reference, not an array.

Combined filters are best used by exclusion: first work out what you do not want (no flying, no player), then write the filter — more reliable than enumerating what you do want.

## Numbers

| Quantity | Value | Source |
|---|---|---|
| Radar result refresh window | 30 tick = 0.5 s | LExecutor.java:761-763 (comment: fixed 30 tick interval) |
| Logic-controlled unit timeout | 600 frames = 10 s | LogicAI.java:18 logicControlTimeout = 60f*10f |
| radar argument count | 7 | mindustry-blueprint/PATTERNS.md:1250-1284 |

Note: around mindustry-blueprint/PATTERNS.md:1300 the text says the radar/uradar result cache is 40 tick, which disagrees with the 30 tick in source at LExecutor.java:761 — take the 30 tick from source (see "Common misconceptions").

## Source anchors

- LExecutor.java:761 comment `//timers update on a fixed 30 tick interval`; :763 `timer.get(30f)` — the refresh criterion for sensor/radar style results.
- LogicAI.java:18 `logicControlTimeout = 60f * 10f`; :22 `controlTimer = logicControlTimeout` — as long as control keeps being refreshed, the unit stays logic-controlled.

## Measurements and counter-examples

Standard targeting skeleton (paste directly, range checked by hand):

```mlog
# 需要：处理器已链接炮塔 tower1（或直接用链接的雷达建筑）
radar enemy any any distance tower1 1 target
jump 无目标 equal target null
sensor tx target x
sensor ty target y
sensor px tower1 x
sensor py tower1 y
op sub dx tx px
op sub dy ty py
op len d dx dy
jump 无目标 greaterThan d 40     # 40 格射程，按实际方块改
control shoot tower1 target 1
end
无目标:
control shoot tower1 0 0
end
```

**Counter-example (treating the cache as live)**: radar results are recomputed only every 30 tick, so a target that moves or dies within 0.5 s leaves you holding a stale reference. Always test for null before use, and add a fallback for "target is dead" (ucontrol has no effect on a dead target; see PATTERN.PERF.001).

**Counter-example (uradar drops control)**: uradar does not refresh controlTimer, so after more than 10 s (600 frames) of continuous use the unit falls out of logic control back to AI. Fix: insert one instruction per round that refreshes the control timer (any ucontrol action, for instance), or rebind periodically.

**Counter-example (fake distance)**: using dx + dy as the distance (listed as a high-frequency bug in PATTERNS.md:2027-2043) treats a square equidistant line as a circle, so diagonal directions fire early or miss; you must use op len.

## Common misconceptions

1. "order 1 takes the farthest" — wrong, 1 = nearest.
2. "target3 is an optional argument" — you may fill it with any, but all 7 arguments are still required.
3. "ground means ground units" — it means "has landed", so flying units are also selected while they are landed.
4. "radar can return several targets" — it returns exactly 1; for multiple targets you must call it several times with a different sort or a different source.

## Related

- PATTERN.COMM.001 communication and buses (splitting targeting across cores)
- PATTERN.PERF.001 failure detection and self-recovery
- COMBAT.TURRET.001 turret control
- 08-evidence/idioms.json: original provenance of this article's idiom entries (30 entries, with src/ver)
