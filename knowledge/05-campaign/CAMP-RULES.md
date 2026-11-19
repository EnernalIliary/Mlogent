---
id: CAMP.RULES.001
title: Every field of the Rules object (118 items)
domain: camp
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src: jar:v160.7#mindustry.game.Rules（反射 118 字段）；Mindustry-Source/core/src/mindustry/game/Rules.java:1-260；core/Logic.java:269-374；entities/Units.java:119-125
data: [00-data/rules.json#records, 00-data/rt_list_Rules.json]
depends: [CAMP.WAVES.001]
tags: [rules, custom, waves, multipliers]
tokens: 1216
---

## In one line

`Rules` is the **single rules object** of a game session (118 fields: 58 boolean / 25 float / 7 int / 28 composite); it decides wave rhythm, unit/building/cost multipliers, win and loss conditions, and AI and logic permissions; **changing one field changes one mechanism**, and the coupling between fields (say `winWave` with `waves`) is easier to get wrong than the fields themselves.

## Rules / formulas

### 1. Order of effect (who overrides whom)

1. The built-in `Rules` defaults (the table under [[#Numbers]] in this article, all read by reflection from the v160.7 jar).
2. The map's own `rules` (a rules block inside `saves/*.msav` or `maps`) override.
3. Campaign planet configuration (`PlanetParams` / `SectorPreset`) overrides once more when entering the map, and **the difficulty triple is multiplied on top of rules** (see [[CAMP.DIFFICULTY.001]]).
4. At runtime, logic can change only **the 29 whitelisted fields** through the `logicRule` instruction (the `LogicRule.java` enum); logic processors have no authority over the rest.

**Conclusion**: the same map has completely different effective rules in "campaign" and "custom" mode; when quoting a rule value you must say which layer it came from.

### 2. The wave clock (the most-fumbled one)

- Opening grace: `wavetime = (initialWaveSpacing <= 0 ? waveSpacing × 2 : initialWaveSpacing) × difficulty.waveTimeMultiplier` (`Logic.java:272`).
  Defaults `initialWaveSpacing = 0`, `waveSpacing = 7200` ⇒ first-wave countdown = **14400 tick = 240 s** (not 120 s).
- After every wave: `wavetime = waveSpacing × difficulty.waveTimeMultiplier`, and `wave += 1` at the same time (`Logic.java:319-325`).
- `waveTimer = false` only switches off **the timer display and the automatic advance**; it is not `waveSending = false` — only the latter really stops sending troops.

### 3. Unit cap (0 does not mean unlimited)

The implementation of `getCap(team)` (`Units.java:119-125`):

```
waveTeam 且非 pvp / 战役中的 waveTeam / disableUnitCap / team.ignoreUnitCap → Integer.MAX_VALUE
否则 → max(0, unitCapVariable ? rules.unitCap + team.data().unitCap : rules.unitCap)
```

- With `unitCapVariable = true` (the default) and `rules.unitCap = 0`, the real cap = **the sum of the unitCapModifier values the cores provide** (core-shard +8, core-foundation +16, core-nucleus +24 and so on, `Blocks.java:3138/3150/3163`) — neither 0 nor unlimited.
- Enemies (waveTeam) are **uncapped** by default, so "filling the map with units" never blocks the waves.
- When a block's `unitCapModifier` changes, `TeamData.unitCap` is maintained by difference (`BlockIndexer.java:216/614`); removing a core lowers the cap immediately and triggers over-cap deaths (`Units.unitCapDeath`).

### 4. Win/loss determination (campaign differs from custom)

`Logic.checkGameState()` (`Logic.java:327-374`):

| Mode | Loss | Win |
|---|---|---|
| Campaign (`isCampaign()`) | the player's core count reaches zero → `gameOver` (there is no "victory" state; winning means capturing the sector) | `waves && enemies==0 && winWave>0 && wave>=winWave && !spawner.isSpawning()` → `Call.sectorCapture()` |
| Custom + `attackMode=false` | same as above | the same condition → `GameOverEvent(defaultTeam)` |
| Custom + `attackMode=true` | living teams ≤1 (non-pvp, and the default team has no core) | only one team left alive |

**`winWave = 0` (the default) means there is no victory wave**; in that case there is no ending other than being wiped out. To "survive 30 waves and win" you must set both `winWave=30` and `waves=true`.

### 5. The multiplication chain of the three multiplier families

A single hit or a single entity may be multiplied by three layers in a row:

```
单位血量  = 类型.health      × rules.unitHealthMultiplier × 难度.unitHealthMultiplier(阵营)
单位伤害  = 子弹.damage     × rules.unitDamageMultiplier × 难度.unitDamageMultiplier(阵营)
建筑血量  = 方块.health      × rules.blockHealthMultiplier
建筑受到  = 伤害            × rules.blockDamageMultiplier
建造成本  = 方块.requirements × buildCostMultiplier ；单位成本 × unitCostMultiplier
建造速度  = 建造者.buildSpeed × buildSpeedMultiplier ；单位建造 × unitBuildSpeedMultiplier
```

So `unitHealthMultiplier = 2` stacked with `difficulty.unitHealthMultiplier = 1.5` gives **×3**, not ×2.5. That is where "I set 2× health but it feels like 3×" comes from.

## Numbers

All defaults come from `00-data/rules.json` (v160.7 jar reflection; you can grep on `name` directly).

### int (7 items, all listed)

| Field | Default | Meaning | Source |
|---|---|---|---|
| `winWave` | 0 | victory wave; 0 = no victory wave | 00-data/rules.json |
| `unitCap` | 0 | extra unit cap (affected by `unitCapVariable`, see above) | 00-data/rules.json |
| `env` | 233 | default environment/weather bitmask | 00-data/rules.json |
| `limitX` / `limitY` | 0 / 0 | top-left corner of the buildable area | 00-data/rules.json |
| `limitWidth` / `limitHeight` | 1 / 1 | width and height of the buildable area (only takes effect together with `limitMapArea`) | 00-data/rules.json |

### float (25 items, all listed)

| Field | Default | Meaning | Source |
|---|---|---|---|
| `waveSpacing` | 7200 | wave interval in ticks (=120 s) | 00-data/rules.json |
| `initialWaveSpacing` | 0 | first-wave countdown; 0 = use `waveSpacing×2` | 00-data/rules.json |
| `solarMultiplier` | 1 | solar panel output multiplier | 00-data/rules.json |
| `unitHealthMultiplier` | 1 | unit health multiplier (multiplied with difficulty) | 00-data/rules.json |
| `unitDamageMultiplier` | 1 | unit damage multiplier | 00-data/rules.json |
| `unitBuildSpeedMultiplier` | 1 | unit build-speed multiplier | 00-data/rules.json |
| `unitCostMultiplier` | 1 | unit build-cost multiplier | 00-data/rules.json |
| `unitCrashDamageMultiplier` | 1 | unit crash-damage multiplier | 00-data/rules.json |
| `unitMineSpeedMultiplier` | 1 | unit mining-speed multiplier | 00-data/rules.json |
| `unitFactoryActivationDelay` | 0 | factory activation delay (seconds) | 00-data/rules.json |
| `blockHealthMultiplier` | 1 | building health multiplier | 00-data/rules.json |
| `blockDamageMultiplier` | 1 | building damage-taken multiplier | 00-data/rules.json |
| `buildCostMultiplier` | 1 | build-cost multiplier | 00-data/rules.json |
| `buildSpeedMultiplier` | 1 | build-speed multiplier | 00-data/rules.json |
| `deconstructRefundMultiplier` | 0.5 | deconstruct refund fraction (only half comes back by default) | 00-data/rules.json |
| `objectiveTimerMultiplier` | 1 | objective timer multiplier | 00-data/rules.json |
| `enemyCoreBuildRadius` | 400 | enemy core no-build radius (**px**, = 50 tiles) | 00-data/rules.json |
| `dropZoneRadius` | 300 | drop-zone radius (px) | 00-data/rules.json |
| `itemDepositCooldown` | 0.5 | item deposit cooldown (seconds) | 00-data/rules.json |
| `dragMultiplier` | 1 | unit air-drag multiplier | 00-data/rules.json |
| `musicVolume` | 1 | music volume | 00-data/rules.json |
| `backgroundSpeed` | 27000 | background parallax speed | 00-data/rules.json |
| `backgroundScl` | 1 | background scale | 00-data/rules.json |
| `backgroundOffsetX` / `backgroundOffsetY` | 0.1 / 0.1 | background offset | 00-data/rules.json |

### boolean (58 items: 24 default true / 34 default false)

Default **true**: `waveTimer`, `waveSending`, `wavesSpawnAtCores`, `pvpAutoPause`, `derelictRepair`, `canGameOver`, `reactorExplosions`, `possessionAllowed`, `schematicsAllowed`, `damageExplosions`, `fire`, `unitCapVariable`, `hideSpawns`, `ghostBlocks`, `logicUnitControl`, `logicUnitBuild`, `worldProcessorPlayerLink`, `cleanupDeadTeams`, `allowCoreUnloaders`, `staticFog`, `unitLight`, `coreIncinerates`, `borderDarkness`, `disableOutsideArea`.

Default **false** (the commonly used ones): `allowEditRules`, `infiniteResources`, `coreBuildAndConfig`, `waves` (**custom mode does not spawn waves by default**; campaign maps set it separately), `airUseSpawns`, `pvp`, `pauseDisabled`, `waitEnemies`, `attackMode`, `editor`, `coreCapture`, `randomWaveAI`, `unitPayloadUpdate`, `unitPayloadsExplode`, `logicUnitDeconstruct`, `disableWorldProcessors`, `allowEditWorldProcessors`, `polygonCoreProtection`, `placeRangeCheck`, `onlyDepositCore`, `coreDestroyClear`, `instantBuild`, `disableUnitCap`, `fog`, `lighting`, `alwaysPlayMusic`, `disableMusic`, `allowLogicData`. For all 58 filter `00-data/rules.json` on `type=="boolean"`.

### Composite types (28 items, which cannot be edited as scalars)

| Type | Fields | Meaning |
|---|---|---|
| `Seq`(5) | `spawns` / `loadout` / `weather` / `ambientMusic` / `darkMusic` | wave presets, starting loadout, weather table |
| `ObjectSet`(5) | `bannedBlocks` / `bannedUnits` / `revealedBlocks` / `researched` / `objectiveFlags` | banned/unlocked sets |
| `Color`(4) | `staticColor` / `dynamicColor` / `ambientLight` / `cloudColor` | screen colours (no mechanical effect) |
| `String`(4) | `modeName` / `mission` / `customBackgroundCallback` / `backgroundTexture` | display only |
| `Team`(2) | `defaultTeam` / `waveTeam` | player team and enemy team |
| singletons | `teams`(TeamRules) / `attributes`(Attributes) / `sector`(Sector) / `objectives`(MapObjectives) / `blockLimits` / `tags` / `planet` / `planetBackground` | grouped rules and campaign metadata |

## Source anchors

- `game/Rules.java`: the 118 public fields are the whole configurable surface (`Rules.java:75` `unitCapVariable=true`, `:157` `unitCap=0`).
- `core/Logic.java:269-297` `play()`: opening grace and the injection of the starting loadout `rules.loadout` (clamped by `storageCapacity`).
- `core/Logic.java:319-325` `runWave()`: send troops + `wave++` + reset `wavetime`.
- `core/Logic.java:327-374` `checkGameState()`: win/loss for the three modes (campaign has no "win", only `sectorCapture()`).
- `entities/Units.java:119-125` `getCap()`: the three cap branches (waveTeam / disableUnitCap / core bonuses).
- `ai/BlockIndexer.java:216,614`: difference maintenance of a block's `unitCapModifier` (cores and the like).
- `logic/LogicRule.java`: the whitelist of the 29 rule fields a logic instruction may change.

## Tests and counterexamples

**Counterexample 1: assuming the first wave is 120 seconds away.** Defaults are `waveSpacing=7200` (120 s) and `initialWaveSpacing=0`, which many people read as "the first wave comes after 120 seconds". In fact `Logic.java:272` takes the `waveSpacing × 2 = 14400 tick` path — **the first wave is 240 seconds away**. Read `sensor @wavetime` on tick 1 and you get 14400, not 7200.

**Counterexample 2: assuming `unitCap=0` is unlimited.** `Units.java:124`'s `max(0, 0 + team.data().unitCap)` shows the cap equals the sum of core bonuses (3 core-nucleus = 72). Only `disableUnitCap=true` or the enemy team is unlimited.

**Counterexample 3: assuming `winWave=30` is enough.** `Logic.java:369` requires `waves==true && enemies==0 && winWave>0 && wave>=winWave && !spawner.isSpawning()` to hold at once; setting only `winWave` with `waves=false` never triggers a victory. Campaign maps are even more special: victory goes through `Call.sectorCapture()`, so even when the condition holds no "game won" screen appears.

## Common misconceptions

1. **"rules is a global constant"**: it is a per-session instance, overridden by the map/planet configuration when entering a map and back to defaults when leaving; to change it you must go through `Call.setRules()` or the logic `logicRule`.
2. **"`rules.waves=false` means no enemies"**: it only stops automatic wave spawning; waves already queued in `spawner`, the `attackMode` AI and preset `spawns` still send troops (`Logic.java:337-349` also shows campaign sets it to false automatically when there are no spawn points).
3. **"`infiniteResources` affects every team"**: it applies only to the **player's default team** (building and production cost nothing); enemies still pay.
4. **"Multipliers stack additively"**: they are all multiplication chains, see section 5 above; two ×2 gives ×4.
5. **"The unit cap includes the enemy"**: `getCap` is computed per team and enemies default to MAX_VALUE, so your cap has nothing to do with the enemy's unit count.

## Related

- [[CAMP.WAVES.001]] wave counting and spawn details
- [[CAMP.DIFFICULTY.001]] the difficulty triple and how it stacks with rules multipliers
- [[CAMP.WINLOSE.001]] the full set of win/loss and game-over conditions
- [[CAMP.SPAWN.001]] `spawns` / the SpawnGroup structure
- [[WORLD.POWER.001]] where `solarMultiplier` lands on the generation side
