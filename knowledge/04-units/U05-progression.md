---
id: UNIT.PROGRESSION.001
title: Unit progression — no experience and no levels, only tiers, wave tables and difficulty multipliers
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:183,759-784"
  - "Mindustry-Source/core/src/mindustry/content/UnitTypes.java:4572,4613"
  - "Mindustry-Source/core/src/mindustry/type/unit/MissileUnitType.java:18"
  - "Mindustry-Source/core/src/mindustry/game/Waves.java:15-130,365-394"
  - "Mindustry-Source/core/src/mindustry/game/SpawnGroup.java:23-73"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:83-88,290-306"
  - "Mindustry-Source/core/src/mindustry/game/CampaignRules.java:39-41"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16-22,49-64"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:179-205,322-352"
  - "Mindustry-Source/core/src/mindustry/logic/LStatements.java:1070-1099"
data: [00-data/units.json]
depends: [UNIT.PRODUCE.001, UNIT.AI.001]
tags: [level, experience, waves, difficulty, ubind, ucontrol, logic control]
tokens: 896
---

## In one line

**Neither v159.3 nor v160.7 has a unit experience or level system** (`UnitType` has no `level/exp` field, a whole-tree grep for "experience" returns 0 hits, and a string scan of the 4842 classes in the v160.7 jar also returns 0); the "growth" players feel comes from four real mechanisms: **the reconstructor chain, the wave unlock table, difficulty multipliers, and logic `ucontrol` takeover (10 s timeout)**.

## Rules / formulas

### 1. Negative evidence (why "there are no levels" can be asserted)

```
UnitType.java      → 无 level / exp / xp / rank / tier 字段（字段区 55-130 行）
Unit.java (gen)    → grep level|exp|lvl|tier|rank 只命中 mineTier / deathExplosionEffect / unitExplode1-3 / dynamicExplosion
v160.7 jar         → mindustry/type/UnitType.class、gen/Unit.class、type/Weapon.class 常量池无 experience 字符串
```

### 2. The real "tier-up": the reconstructor chain

```
T1 dagger(150 hp, 0 armor) → T2 mace(550, 4) → T3 fortress(900, 9) → T4 scepter(9000, **20**) → T5 reign(24000, **30**)
```

Upgrading relies on the `Reconstructor.upgrades` table (see [[UNIT.PRODUCE.001]]); it is **irreversible, needs no experience and no kills**, only items, power and time.

### 3. The wave table: where enemies really get "stronger"

Each `SpawnGroup` has `begin/end/spacing/unitAmount/unitScaling/max/shields/shieldScaling/effect`:

```
getSpawned(wave) = min(unitAmount + floor(((wave - begin)/spacing)/unitScaling), max)   // SpawnGroup.java:67-73
getShield(wave)  = max(shields + shieldScaling*(wave - begin), 0)                        // :75-77
```

Waves getting stronger is not "units levelling up" — it is **stronger new SpawnGroups entering play from some begin wave**.

### 4. Difficulty multipliers (applied to waveTeam)

```
CampaignRules.java:39-41
  waveTeam.unitHealthMultiplier = difficulty.enemyHealthMultiplier
  waveTeam.unitCostMultiplier   = 1 / difficulty.enemySpawnMultiplier
Rules.unitHealth(team) = max(unitHealthMultiplier * team.unitHealthMultiplier, 1e-6)   // :304
```

### 5. `ubind` / `ucontrol` (logic control, from the unit's side)

```
ubind @type
  → 只能绑 logicControllable 单位（UnitType.java:183 默认 true）
  → 只能绑本队（exec.team）或 privileged 执行器（LExecutor.java:200）
  → 同类型按 id 轮询：binds[type.id]++（LExecutor.java:188-195）
ucontrol ...
  → 首次控制把 unit.controller 换成 LogicAI，并清 mineTile / clearBuilding()（:328-336）
  → 每次 ucontrol 刷新 controlTimer = logicControlTimeout = 60*10 = 600 tick（LogicAI.java:18）
  → 10 秒没有新的 ucontrol → resetController() 回默认 AI（LogicAI.java:59-64）
```

**The parameter table for all 21 `ucontrol` types lives in [[MLOG.UNIT.001]] (M07); this article covers only the unit-side semantics.**

## Numbers

### Unit tiers (health / armor / hitSize; hp and hitSize agree across both versions, armor is taken from the v160.7 jar, see the note below)

| Chain | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| ground mech | dagger 150/0/8 | mace 550/4/10 | fortress 900/9/13 | scepter 9000/**20**/22 | reign 24000/**30**/30 |
| flying | flare 70/0/9 | horizon 340/3/11 | zenith 700/5/20 | antumbra 7200/**17**/46 | eclipse 22000/**22**/58 |
| spider | crawler 150/0/8 | atrax 600/3/13 | spiroct 1000/**9**/15 | arkyid 8000/**14**/23 | toxopid 22000/**22**/26 |
| naval | risso 280/2/10 | minke 600/4/13 | bryde 910/7/20 | sei 11000/12/39 | omura 22000/16/58 |

**Version note**: armor comes from the v160.7 jar (`00-data/units.json`); the v159.3 source has lower values under the same field names — spiroct 5 (`UnitTypes.java:746`), arkyid 6(:805), toxopid 13(:909), eclipse 13(:1264), antumbra 9, scepter 10(:194), reign 18(:295). hp and hitSize agree across versions.

**T5 health relative to T1**: reign/dagger = 24000/150 = **160×**; toxopid/crawler = 22000/150 ≈ **146.7×**; omura/risso = 22000/280 ≈ **78.6×**.

### Wave table excerpt (Waves.java:20-130)

| SpawnGroup | begin | end | spacing | unitAmount | unitScaling | max | shields / shieldScaling | effect |
|---|---|---|---|---|---|---|---|---|
| dagger | 0 | 10 | 1 | 1 | 2 | 30 | — | — |
| crawler | 4 | 13 | 1 | 2 | 1.5 | 40 | — | — |
| flare | 12 | 16 | 1 | 1 | 1 | 40 | — | — |
| mace | 7 | 30 | 3 | 1 | 2 | 40 | — | — |
| fortress | 40 | — | — | — | — | — | — | — |
| spiroct | 45 | — | 3 | 1 | 1 | 10 | shields 100 / +30 per wave | overdrive |
| quasar | 82 | — | 3 | 4 | 3 | 40 | +30 per wave | overdrive |
| pulsar | 120 | — | 2 | 5 | 3 | 40 | — | overdrive |

### The five difficulty steps (the Difficulty enum)

| Difficulty | enemyHealthMultiplier | enemySpawnMultiplier | waveTimeMultiplier |
|---|---|---|---|
| casual | 0.5 | 0.5 | 2 |
| easy | 1 | 0.75 | 1.5 |
| normal | 1 | 1 | 1 |
| hard | 1.25 | 1.5 | 0.8 |
| eradication | 1.5 | 2 | 0.6 |

hard vs normal: enemies get **1.25× health**, arrive in **1.5× numbers**, and waves come at **0.8×** the interval.

### Key logic-control constants

| Quantity | Value | Source |
|---|---|---|
| `logicControlTimeout` | **600 ticks = 10 s** | LogicAI.java:18 |
| `transferDelay` | 90 ticks = 1.5 s | LogicAI.java:16 |
| `rules.logicUnitControl` default | **true** | Rules.java:99 |
| `UnitType.logicControllable` default | **true** | UnitType.java:183 |
| units that cannot be logic-controlled | `manifold` (UnitTypes.java:4572), `assemblyDrone` (:4613), every `MissileUnitType` (MissileUnitType.java:18) | — |
| `ubind` round-robin per type | `binds[type.id]++` | LExecutor.java:188-195 |
| boss first wave | `rand(50,70)` | Waves.java:365 |
| final boss wave | `120 + rand(30)` | Waves.java:394 |

## Source anchors

- [src: UnitType.java:183] `logicControllable = true` (a switch in the `UnlockableContent` field block).
- [src: UnitType.java:759-761] `public boolean isBanned(){ return state.rules.isBanned(this); }` — a banned unit fails `canCreate` outright.
- [src: UnitType.java:768] `for(UnitType[] recipe : r.upgrades)` — the reconstructor chain is the **only** path by which a unit gets stronger.
- [src: SpawnGroup.java:23,36] `unitScaling = UnitScaling.never`; `:42` `unitAmount = 1`.
- [src: Waves.java:365-368] `bossWave = rand(50,70) * lerp(1,0.5,diff)`; `bossTier = diff < 0.6 ? 3 : 4`.
- [src: LogicAI.java:18] `logicControlTimeout = 60f * 10f`.
- [src: LogicAI.java:59-64] `controlTimer <= 0` → `unit.resetController()`.
- [src: LExecutor.java:186-205] the three `ubind` branches (UnitType round-robin / a specific Unit / null).
- [src: LExecutor.java:344] a non-privileged executor needs `state.rules.logicUnitControl`.

## Tests and counterexamples

**Counterexample 1: assuming "kills make you level up".**
There is no `experience` field anywhere in the tree; a dagger that kills 1000 crawlers still has 150 hp and 9 damage (`BulletType(2.5, 9)`). To get stronger you must reconstruct into a mace (550 hp) — that is **swapping the unit**, not levelling it.

**Counterexample 2: assuming high-wave enemies are "higher level".**
When spiroct appears at wave 45 its health is still 1000 (fixed in source), but `getShield(45) = 100 + 30*(45-45) = 100` and it grows by 30 per wave after that — the **shield** grows while the body never changes. At wave 60 that group's shield = `100 + 30*15 = 550`.

**Counterexample 3: assuming `ucontrol` can take over permanently.**
`logicControlTimeout = 600` ticks. A logic processor must send at least one `ucontrol` every 10 s or the unit calls `resetController()` — this is the most common cause of "my logic array suddenly stopped working" (destroying the processor or cutting its power breaks control just as fast).

**Counterexample 4: assuming `ubind` can bind enemies.**
`ubind` accepts only units of `exec.team`, or a privileged executor (LExecutor.java:200); a type such as `@enemy` binds to null when it belongs to the enemy team (:198/:204).

**Recomputable**: the spiroct group at wave 60 on hard (begin 45, shields 100, shieldScaling 30):
`getShield(60) = 100 + 30 × (60-45) = 550`; `getSpawned(60) = min(1 + floor(((60-45)/1)/1), 10) = 10` (max=10).
→ 10 spirocts, each 1000 hp + 550 shield = **15500 effective health**, all carrying `overdrive` (StatusEffects' 1.15× attack and move speed).

## Common misconceptions

- ❌ "units have levels/stars". → they do not; star icons come from mods or from memory of older versions.
- ❌ "difficulty only affects enemy health". → it also changes numbers (enemySpawnMultiplier) and wave interval (waveTimeMultiplier).
- ❌ "`unitHealthMultiplier` grows with the wave number". → it is set once, during difficulty setup (CampaignRules.java:40).
- ❌ "every `logicControllable` unit can be `ucontrol`led". → it also needs `exec.privileged || rules.logicUnitControl` (the rule can be switched off).
- ❌ "one `ubind` binds every unit of that type". → each call advances one unit, round-robin via `binds[type.id]++`.

## Related

- [[UNIT.PRODUCE.001]] the reconstructor chain and factory recipes
- [[UNIT.AI.001]] switching between LogicAI and the default AI
- [[UNIT.ABILITY.001]] abilities do not grow with the wave number
- [[COMBAT.WAVE.001]] wave generation and difficulty multipliers
- [[MLOG.UNIT.001]] the complete table of all 21 `ucontrol` parameters (M07)
