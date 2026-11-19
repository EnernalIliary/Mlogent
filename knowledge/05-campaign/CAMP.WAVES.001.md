---
id: CAMP.WAVES.001
title: The numeric model of wave rhythm — waveSpacing, the first-wave grace and the countdown
domain: camp
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:31,47,151-157"
  - "Mindustry-Source/core/src/mindustry/core/Logic.java:269-297,315-325,327-345,585-591,617"
  - "Mindustry-Source/core/src/mindustry/core/GameState.java:19"
  - "Mindustry-Source/core/src/mindustry/game/Difficulty.java:5-10"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1772-1780"
data: [00-data/formulas.json, 00-data/constants_rules_difficulty_drill_heat.json]
depends: [COMBAT.WAVE.001]
tags: [waves, timing, waveSpacing, difficulty, logic rules]
tokens: 570
---

## In one line

Waves depend on just two pieces of state: `state.wave` (the current wave number) and `state.wavetime` (ticks left until the next wave); `waveSpacing` defaults to `2 × Time.toMinutes = 7200 tick = 120 s` [src: Rules.java:151], the first wave is **2×** that, and campaign difficulty only multiplies `waveTimeMultiplier` — it never changes the wave number or the composition of a wave.

## Rules / formulas

```
waveSpacing = 2 * Time.toMinutes        // 7200 tick = 120 s                  [Rules.java:151]
首波 wavetime = (initialWaveSpacing <= 0 ? waveSpacing*2 : initialWaveSpacing) * waveTimeMultiplier   [Logic.java:272]
之后 wavetime = waveSpacing * waveTimeMultiplier                                                   [Logic.java:322]
到达第 N 波时刻 T(N) = 首波间隔 + (N - 1) × 间隔                    （N ≥ 1，从开局计时）
```

Countdown advance (every tick):

```
if(rules.waves && rules.waveTimer && !gameOver) wavetime = max(wavetime - Time.delta, 0)   [Logic.java:585-587]
if(wavetime <= 0 && rules.waves) runWave()                                                  [Logic.java:591]
runWave(): spawner.spawnEnemies(); wave++; wavetime = 间隔                                  [Logic.java:319-325]
```

- `waveTimeMultiplier` is read only when `state.isCampaign()` (the planet's campaignRules difficulty); outside campaign it is always 1.
- With `initialWaveSpacing > 0` the first wave is no longer doubled (a map author can set their own grace period).
- `skipWave()` simply calls `runWave()`; it does not change the state of the waveTimer switch.
- With `waitEnemies = true`, or `wave >= winWave > 0`, the countdown **pauses** until the field is clear:
  `(rules.waitEnemies || (wave >= winWave && winWave > 0)) && enemies > 0` [Logic.java:617]
- When a logic processor writes rules, **the unit is seconds**: `set waveSpacing = 120` → `rules.waveSpacing = 120 × 60`; `set currentWaveTime` is ×60 the same way [LExecutor.java:1774,1778]. `enemyCoreBuildRadius`/`dropZoneRadius` on the other hand are ×8 (tiles → world units) [LExecutor.java:1779-1780].

## Numbers

| Difficulty | waveTimeMultiplier | first wave | wave interval | wave 10 | wave 30 | wave 50 | source |
|---|---|---|---|---|---|---|---|
| casual | 2.0 | 480 s | 240 s | 2640 s | 7440 s | 12240 s | [v160.7] |
| easy | 1.5 | 360 s | 180 s | 1980 s | 5580 s | 9180 s | [v160.7] |
| normal | 1.0 | 240 s | 120 s | 1320 s（22 min） | 3720 s（62 min） | 6120 s | [v160.7] |
| hard | 0.8 | 192 s | 96 s | 1056 s | 2976 s | 4896 s | [v160.7] |
| eradication | 0.6 | 144 s | 72 s | 792 s（13 min） | 2232 s（37 min） | 3672 s | [v160.7] |

Every time in the table is computed by substituting `waveSpacing=7200`, `initialWaveSpacing=0` and `waveTimeMultiplier` into T(N) (waveSpacing/initialWaveSpacing/waveTimeMultiplier are all [verified v160.7] reflection values, see DATA.FORMULA.011 and 00-data/constants_rules_difficulty_drill_heat.json).

| Constant | Value | Source |
|---|---|---|
| rules.waveSpacing | 7200 ticks = 120 s | Rules.java:151; [verified v160.7] |
| rules.initialWaveSpacing | 0 ticks | Rules.java:153; [verified v160.7] |
| rules.waveTimer | true | Rules.java:31; [verified v160.7] |
| rules.winWave | 0 (no limit) | Rules.java:155; [verified v160.7] |
| rules.waitEnemies | false | Rules.java:47; [verified v160.7] |
| state.wavetime | float, in ticks | GameState.java:19 |

## Source anchors

- Rules.java:151 `waveSpacing = 2 * Time.toMinutes`, the reflected default 7200 tick = 120 s [verified v160.7].
- Logic.java:272 the first-wave grace × waveTimeMultiplier; :322 the reset after every wave.
- Logic.java:585-591 countdown and trigger; :617 the wait-for-clear test; :315-325 skipWave/runWave.
- Logic.java:327-345 campaign has no wins state, only the "all cores gone" test (win/lose in CAMP.VICTORY.001).
- LExecutor.java:1774,1778 the unit conversions for logic rules (seconds→ticks), :1779-1780 tiles→world units [src: LExecutor.java:1774-1780].

## Tests and counterexamples

**Counterexample 1: reading waveSpacing as seconds.** Writing `rules.waveSpacing = 120` directly turns it into 120 ticks = one wave every 2 s [src: Rules.java:151]; for 120 s you must write 7200. Going through the logic rule `set waveSpacing = 120` is what gives 120 s (it multiplies by 60 internally).

**Counterexample 2: assuming waveTimer=false means no waves.** What switches off is only the automatic countdown; `skipWave()` or the logic `set currentWaveTime = 0` still pushes a wave immediately.

**Counterexample 3: assuming the first wave is also 120 s.** The first wave is fixed at 2×waveSpacing (normal 240 s, eradication 144 s) [src: Logic.java:272] — this is the most direct thing a player feels about difficulty.

**Counterexample 4: assuming "wait until the field is clear" is the default.** `waitEnemies=false` by default, so the next wave arrives even with enemies still alive.

**Recomputable**: normal, `waveTimer` on, no skipping → wave 30 lands at 240 + 29×120 = 3720 s = 62 min; the same map on eradication gives 144 + 29×72 = 2232 s = 37.2 min (straight from T(N), constants in the table above [v160.7]).

## Common misconceptions

- "The wave number is a function of time" → only true when you neither skip waves nor trigger them early; `state.wave` and wavetime are two independently writable states.
- "waveSpacing is measured in seconds" → it is ticks (60 ticks = 1 s) [src: Logic.java:585-591].
- "Difficulty only changes the wave interval" → the interval is only the third term of the triple; for health and numbers see CAMP.DIFFICULTY.001.
- "Campaign maps are won through winWave" → `winWave` only takes effect on non-campaign maps; campaign is won by wiping all cores or capturing sectors [Logic.java:328-329,343].

## Related

- [[COMBAT.WAVE.001]] the combat-side view of waves (spawn points, shockwaves, AI target selection)
- [[CAMP.DIFFICULTY.001]] how the difficulty triple changes health, numbers and interval together
- [[CAMP.SPAWN.001]] how many units each spawn group sends and how much shield they carry
- DATA.FORMULA.011 the wave-timing formula (with the algebra and worked substitutions)
