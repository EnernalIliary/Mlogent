---
id: COMBAT.WAVE.001
title: "Enemies and attack waves: spawn points, wave composition, difficulty scaling and AI targets"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/ai/WaveSpawner.java:62-160"
  - "Mindustry-Source/core/src/mindustry/game/SpawnGroup.java:26-78"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:151-152,302-306"
  - "Mindustry-Source/core/src/mindustry/game/Difficulty.java:5-21"
  - "Mindustry-Source/core/src/mindustry/game/Waves.java:356-400"
  - "Mindustry-Source/core/src/mindustry/entities/Units.java:114-125,307-310"
  - "Mindustry-Source/core/src/mindustry/core/Logic.java:272,322"
data: [00-data/rt_list_WaveSpawner.json, 00-data/rt_list_Difficulty.json]
depends: [COMBAT.ARMOR.001, UNIT.AI.001]
tags: [waves, enemy-base, spawning, difficulty, boss, attack-mode]
tokens: 752
---

## In one line

Attack waves are driven by a list of `SpawnGroup`s in `rules.spawns`, with the count formula **`min(unitAmount + ⌊((wave−begin)/spacing)/unitScaling⌋, max)`**; strength grows through three independent channels — **count (unitScaling), health (difficulty enemyHealthMultiplier → team.unitHealthMultiplier), shields (shieldScaling)** — which multiply rather than add.

## Rules and formulas

### 1. How many units each wave spawns

```
getSpawned(wave):
    if(spacing == 0) spacing = 1
    if(wave < begin || wave > end || (wave - begin) % spacing != 0) return 0
    return min(unitAmount + (int)(((wave - begin) / spacing) / unitScaling), max)

默认: unitAmount = 1, max = 40, spacing = 1, unitScaling = never(Integer.MAX_VALUE)
```

- `spacing = 1` → spawns every wave; `spacing = 5` → once every 5 waves.
- `unitScaling = never` → the count **never grows** (vanilla default); `unitScaling = 10` → one extra unit per 10 "spacing periods".
- Cap `max = 40`: at most 40 units per group.

### 2. Shields

```
getShield(wave) = max(shields + shieldScaling * (wave - begin), 0)
```

boss groups use `shieldScaling = shieldsPerWave`, so late-game bosses arrive with a shield of their own.

### 3. Campaign difficulty scaling (three multipliers)

| difficulty | enemyHealthMultiplier | enemySpawnMultiplier | waveTimeMultiplier |
|---|---|---|---|
| casual | 0.5 | 0.5 | 2.0 |
| easy | 1.0 | 0.75 | 1.5 |
| normal | 1.0 | 1.0 | 1.0 |
| hard | 1.25 | 1.5 | 0.8 |
| eradication | 1.5 | 2.0 | 0.6 |

- **Count**: `spawned *= enemySpawnMultiplier`; boss groups floor with `(int)` (1.5×1 boss does not become 2), non-boss uses `Mathf.round`.
- **Health**: `CampaignRules` writes `difficulty.enemyHealthMultiplier` into `rules.teams.get(waveTeam).unitHealthMultiplier`, and finally `unitHealth(team) = rules.unitHealthMultiplier × team.unitHealthMultiplier`, which acts as a **divisor** in the damage pipeline → 1.5× health means "incoming damage ÷1.5".
- **Time**: `state.wavetime = waveSpacing × waveTimeMultiplier`.

### 4. Wave spacing

```
rules.waveSpacing = 2 * Time.toMinutes = 7200 tick = 120 s
首波: wavetime = (initialWaveSpacing <= 0 ? waveSpacing*2 : initialWaveSpacing)   // 默认 240 s
```

### 5. Spawn points and the shockwave

```
eachGroundSpawn: 遍历 state.rules.spawns 的落点（地图上的敌基 spawn 标记）
   → doShockwave: 范围内 waveTeam 单位受 99999999 伤害（清场，保证落点空出）
地面 spread = tilesize * 2 = 16 px；飞行 spread = margin / 1.5
attackMode / wavesSpawnAtCores: 从敌方核心 "指挥点" 生成，距玩家核心 coreMargin = 16 格
```

### 6. AI target selection

```
Units.bestTarget(team, x, y, range, ...):
    if(dst2 < range² && (result == null || dst2 < cdist || e.type.targetPriority > cpriority) && e.type.targetPriority >= cpriority)
```

Units claim priority through `UnitType.targetPriority` (larger = more preferred) while also being constrained by distance. Most vanilla units default to 0; units with `targetPriority = -2` (UnitTypes.java:4348/4413/4493) are "builder/support" types that do not get targeted first.

## Numbers

| quantity | value | source |
|---|---|---|
| `rules.waveSpacing` | 7200 tick = **120 s** | Rules.java:151; v160.7 reflection default 7200 |
| first-wave delay | 240 s (normal) | Logic.java:272 |
| `SpawnGroup.max` | 40 | SpawnGroup.java:34; reflection default 40 |
| `SpawnGroup.unitAmount` | 1 | SpawnGroup.java:42 |
| `SpawnGroup.unitScaling` | never = Integer.MAX_VALUE | SpawnGroup.java:23,36 |
| `WaveSpawner.coreMargin` | 16.0 tiles | WaveSpawner.java:38; reflection const=16.0 |
| ground spawn spread | 16 px | WaveSpawner.java:95 |
| shockwave damage | 99999999 | WaveSpawner.java:118 |
| first boss wave | `random(50,70)×lerp(1,0.5,difficulty)` → normal 50~70 / eradication 25~35 | Waves.java:365 |
| boss interval | `random(25,40)×lerp(1,0.5,difficulty)` → normal every 25~40 waves | Waves.java:366 |
| boss group cap | max = 16 | Waves.java:376 |
| final boss start | `120 + random(30)` = waves 120~150 | Waves.java:394 |
| boss strength | `StatusEffects.boss` (damageMultiplier 1.3, healthMultiplier 1.5, permanent) | StatusEffects.java:178-183 |

## Source anchors

- `WaveSpawner.java:62-109` `spawnEnemies`: shockwave → walk spawns → difficulty multipliers → air/ground split spawn → `Time.run(121f, spawning=false)`.
- `WaveSpawner.java:111-113` `spawnUnit`: faces the map center, passes `state.wave - 1` as wave (Spawning counts from 0).
- `WaveSpawner.java:116-119` `doShockwave`: `Damage.damage(waveTeam, x, y, dropZoneRadius, 99999999f, true)`.
- `WaveSpawner.java:125-160` `eachGroundSpawn`: spawn markers + core landing points when `wavesSpawnAtCores && attackMode` (`coreMargin + size*tilesize/2*sqrt2`).
- `SpawnGroup.java:67-78` `getSpawned` / `getShield`.
- `Rules.java:151` `waveSpacing = 2*Time.toMinutes`; `:302-306` `unitHealth(team)`.
- `CampaignRules.java:39-40` writes difficulty into `blockHealthMultiplier/unitHealthMultiplier` of `waveTeam`.
- `Difficulty.java:5-10` the five difficulty presets.
- `Waves.java:356-400` wave scripting: start at 5~5+rand(5), one tier up every `rand(15,30)×lerp(1,0.5,difficulty)` waves, `curTier` capped at 3 (4 for bosses).
- `Units.java:114-125` `canCreate/getCap` (wave team cap = MAX_VALUE outside pvp campaigns).
- `Units.java:307-310` the targetPriority comparison inside `bestTarget`.

## Measurements and counterexamples

**Counterexample 1: assuming a higher wave always means more enemies.**
Vanilla `unitScaling = never`, so ordinary group counts are **constant**. Wave progression works mainly by "unlocking higher-tier unit types" (Waves' curTier stepping up), not by count.

**Counterexample 2: assuming difficulty only affects health.**
hard is `1.25 hp × 1.5 count × 0.8 interval`, all three at once — real pressure lands near `1.25×1.5/0.8 ≈ 2.34×`.

**Counterexample 3: assuming the shockwave is a visual effect.**
`doShockwave` deals 99999999 damage to **waveTeam units** inside `dropZoneRadius` (default 300px) — it "clears the landing zone", and it also kills wounded enemies that just spawned there.

**Counterexample 4: assuming a boss is "whatever arrives at wave 50".**
Boss waves are random 50~70, then one every 25~40 waves, and there are **two independent tracks** (the main boss plus a substitute boss offset by `rand(3,5)×bossSpacing`), so chained boss waves do happen.

**Recomputable**: on normal, the first wave at `t=240s`, then one every 120 s; reaching wave 10 takes `240 + 9×120 = 1320 s = 22 min`. If a logic processor sets waveSpacing to 60 (`value.numf()*60` at `LExecutor.java:1778`), it becomes one wave every 60 s.

## Common misconceptions

- ❌ "`spacing` is seconds". → It is an interval in **waves**.
- ❌ "`max=40` is the enemy cap for the whole map". → It is the cap **per group**.
- ❌ "enemy health rises linearly with wave number". → Vanilla **does not rise with wave number**, only with difficulty (team.unitHealthMultiplier) and unit tier.
- ❌ "air units also spawn from ground spawn points". → Air uses `eachFlyerSpawn` with spread `margin/1.5`, unlike the ground 16px.
- ❌ "the wave passed in is the current wave number". → `spawnUnit` passes `state.wave - 1`, and being off by 1 miscalculates the first-wave scaling.

## See also

- [[UNIT.AI.001]] how units pick targets and path
- [[UNIT.PRODUCE.001]] the unit cap versus the enemy having none
- [[COMBAT.DEFENSE.001]] what to hold waves with
- [[COMBAT.STATUS.001]] the boss status's 1.3 damage / 1.5 health
