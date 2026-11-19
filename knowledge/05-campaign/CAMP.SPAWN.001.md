---
id: CAMP.SPAWN.001
title: The spawn-group data model — how SpawnGroup's 8 fields become each wave's count and shields
domain: camp
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/game/SpawnGroup.java:26-42,67-77,92"
  - "Mindustry-Source/core/src/mindustry/game/Waves.java:13,17-256,271-444"
  - "Mindustry-Source/core/src/mindustry/ai/WaveSpawner.java:62-109"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:177"
data: [00-data/formulas.json, 00-data/constants_rules_difficulty_drill_heat.json]
depends: [CAMP.WAVES.001, CAMP.DIFFICULTY.001]
tags: [SpawnGroup, spawning, shields, waves, level data]
tokens: 733
---

## In one line

Each spawn group (SpawnGroup) is nothing but 8 numeric fields; "does this wave spawn", "how many spawn" and "how much shield they carry" are three **independent** calculations. In fixed levels these fields are hard-coded in `Waves.get()`, while random maps build them on the spot with `Waves.generate()`.

## Rules / formulas

```
w = state.wave - 1                                     // WaveSpawner.java:74

刷不刷: begin <= w <= end 且 (w - begin) % spacing == 0   // 不满足则本波 0 只
数量:   getSpawned = min(unitAmount + (int)(((w - begin) / spacing) / unitScaling), max)   // SpawnGroup.java:72
        （(w-begin)/spacing 是整数除法；外层再除 unitScaling 后截断，故 spacing>1 时增长被稀释）
护盾:   getShield  = max(shields + shieldScaling × (w - begin), 0)                        // SpawnGroup.java:77
战役实际数量 = max(1, round(getSpawned × enemySpawnMultiplier))    // 非 boss 组        WaveSpawner.java:79-81
             = max(1, (int)(getSpawned × enemySpawnMultiplier))   // boss 组，向下取整
```

Field defaults [src: SpawnGroup.java:26-42]: `begin=0`, `end=never(Integer.MAX_VALUE)`, `spacing=1`, `max=40`, `unitScaling=never`, `shields=0`, `shieldScaling=0`, `unitAmount=1`. Because `unitScaling` defaults to `never`, a default group only ever spawns `unitAmount` units.

## Numbers

Representative groups of a fixed level (`Waves.get()` inlines 28 groups; the table gives the raw source values, and any field not listed is at its default):

| Group | begin | end | spacing | unitAmount | unitScaling | max | shields | shieldScaling | source |
|---|---|---|---|---|---|---|---|---|---|
| dagger | 0 | 10 | 1 | 1 | 2 | 30 | 0 | 0 | [v159.3] |
| crawler | 4 | 13 | 1 | 2 | 1.5 | 40 | 0 | 0 | [v159.3] |
| mace | 7 | 30 | 3 | 1 | 2 | 40 | 0 | 0 | [v159.3] |
| spiroct | 45 | never | 3 | 1 | 1 | 10 | 100 | 30 | [v159.3] |
| fortress | 40 | never | 5 | 2 | 2 | 20 | 0 | 30 | [v159.3] |
| scepter | 41 | never | 30 | 1 | 1 | 40 | 0 | 30 | [v159.3] |
| corvus | 145 | never | 35 | 1 | 1 | 40 | 100 | 30 | [v159.3] |
| toxopid | 210 | never | 35 | 1 | 1 | 40 | 1000 | 35 | [v159.3] |

Substituting into the formulas gives the key waves (w is the group's 0-based wave number, `state.wave = w + 1`):

| Group | w | Count | Shields | Working | source |
|---|---|---|---|---|---|
| dagger | 0 / 2 / 10 | 1 / 2 / 6 | 0 | 1 + w/2, the last wave w=10 hits end | formula substitution |
| spiroct | 45 / 46 / 48 / 54 | 1 / 0 / 2 / 4 | 100 / 130 / 190 / 370 | 46 fails spacing, but shields keep growing | formula substitution |
| fortress | 40 / 45 / 50 | 2 / 2 / 3 | 0 / 150 / 300 | count 2+w/10 floored, shield 30×(w-40) | formula substitution |
| scepter | 41 / 71 / 101 | 1 / 2 / 3 | 0 / 900 / 1800 | spacing=30, +1 unit every 30 waves | formula substitution |
| corvus | 145 / 180 / 215 | 1 / 2 / 3 | 100 / 1150 / 2200 | 100+30×(w-145) | formula substitution |
| toxopid | 210 / 245 / 280 | 1 / 2 / 3 | 1000 / 2225 / 3450 | 1000+35×(w-210) | formula substitution |

Where the numbers come from: the group fields are the source's actual arguments ([src: Waves.java:20-252]); the count/shield columns are computed by substituting into the two formulas above, with no external data.

Random (generated) maps build groups on the spot with `Waves.generate()`:

| Parameter | Value | Source [v159.3] |
|---|---|---|
| total wave cap | 150 | Waves.java:299 |
| first shield wave | 30 | Waves.java:301 |
| per-wave shield increment | 20 + difficulty×30 | Waves.java:301 |
| main group initial count | `6 / (int)scaling[tier]` → 6/3/2/1/1 | Waves.java:319 |
| secondary group initial count | `3 / (int)scaling[tier]` → 3/1/1/0/0 (tier≥4 never appears) | Waves.java:331 |
| per-group cap | main max=13, secondary max=6 | Waves.java:323-339 |
| group length | `rand(8,16) + (int)lerp(5,0,difficulty) + tier×4` waves | Waves.java:311 |
| growth rate | `(d<0.4 ? rand(2.5,5) : rand(1,4)) × scaling[tier]` | Waves.java:323 |
| boss first wave | `(int)(rand(50,70) × lerp(1,0.5,difficulty))` | Waves.java:365 |

## Source anchors

- SpawnGroup.java:72 `getSpawned` (integer division plus truncation); :77 `getShield` (independent of spawning); :92 `unit.shield = getShield(wave)`.
- Waves.java:13 `waveVersion = 7` (the save-format wave version); :17-256 the 28 fixed groups of `get()`; :271-444 `generate()`.
- WaveSpawner.java:74 `getSpawned(state.wave - 1)`; :79-81 campaign difficulty multiplies the count (bosses truncate); :86-105 flying spread=margin/1.5, ground spread=8px×2=16px [src: WaveSpawner.java:74-105].
- Rules.java:177 `spawns` is a `Seq<SpawnGroup>`, i.e. the level data is this object list (it is not hard-coded in code) [v160.7].

## Tests and counterexamples

**Counterexample 1: assuming every wave after begin spawns.** spiroct has `begin=45, spacing=3` → it only appears at w=45,48,51…; w=46 and 47 spawn 0 [src: SpawnGroup.java:69].

**Counterexample 2: assuming "no spawn" means "this wave changes nothing".** Shields grow linearly with `w - begin`, regardless of whether anything spawned: spiroct spawns 0 at w=46, but the 2 it spawns at w=48 arrive carrying 190 shields (not 160) [see the getShield formula].

**Counterexample 3: assuming max is a cumulative cap.** It is a **per-wave** cap: once spiroct reaches 10 (w≥72) it still spawns 10 every 3 waves and never stops [src: SpawnGroup.java:72].

**Counterexample 4: assuming unitScaling is measured in waves.** What it divides is the number of spacing periods already passed: spiroct gains +1 only every 3 waves, so going from 1 to 10 takes 27 waves (w=45→72) [src: SpawnGroup.java:72].

**Counterexample 5: assuming low difficulty drops groups to 0 units.** The campaign branch has `Math.max(1, ...)`, so `round(1×0.5)=0` is lifted to 1 [src: WaveSpawner.java:79-81]; a "1 unit" group stays at 1 under casual, and the halving shows up in multi-unit groups (6 → 3).

**Recomputable**: toxopid (begin=210, spacing=35, shields=1000, shieldScaling=35) at w=245: count = 1 + (int)((35/35)/1) = 2, shields = 1000 + 35×35 = 2225 → that wave is 2 T4 units with 2225 shields each [see the formulas].

## Common misconceptions

- "The spawn table is a JSON data file" → logically it is a sequence of SpawnGroup objects, but fixed levels write it in Waves.java (28 groups), not in an external data table [src: Waves.java:17-256].
- "Shields are armor" → shields are the `unit.shield` pool, drained before health, while `armor` reduces damage; they are two separate mechanisms [src: SpawnGroup.java:92].
- "A larger spacing means weaker" → spacing controls both appearance frequency and growth rate (see the formulas); corvus with its 40-wave spacing suppresses the whole battle once it appears [see the formulas].
- "The number multiplier applies to bosses too" → it does, but rounded down, so 1.5×1 is still 1 unit [src: WaveSpawner.java:78-81].

## Related

- [[CAMP.WAVES.001]] wave rhythm, waveSpacing and T(N)
- [[CAMP.DIFFICULTY.001]] how enemySpawnMultiplier reaches this point
- [[COMBAT.WAVE.001]] the combat-side view: spawn points, shockwaves, boss-only effects
- DATA.FORMULA.009 / DATA.FORMULA.010 the per-wave count and shield formulas
