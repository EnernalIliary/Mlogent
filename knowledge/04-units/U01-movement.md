---
id: UNIT.MOVE.001
title: Unit types and movement — the real unit of speed, hitSize, terrain and boost
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:55-110,116-129,177,203-245,540-541,892-903,924-927"
  - "Mindustry-Source/core/src/mindustry/content/UnitTypes.java:357-916,1042-1550"
  - "MBO/gamedata/v160.7/units_production.json（70 单位 health/flying/hitSize）"
data: [00-data/units.json]
depends: [COMBAT.ARMOR.001]
tags: [unit, movement, speed, hitSize, boost, terrain, flying, naval]
tokens: 809
---

## In one line

`UnitType.speed` is measured in **world units/tick (px/tick)**, not tiles/s — `speed × 60 ÷ 8 = tiles/s`; so dagger's `0.5` equals **3.75 tiles/s**, flare's `2.7` equals **20.25 tiles/s**, and across the whole table the fastest is alpha (22.5 tiles/s) while the slowest is corvus (2.25 tiles/s).

## Rules / formulas

### 1. The unit of speed (the easiest one to get wrong)

```
UnitType.speed  单位: world units per tick（1 格 = tilesize = 8 px）
tiles/s = speed × 60 / 8 = speed × 7.5
px/s    = speed × 60
```

The source comment says it plainly: `/** movement speed (world units/t) */` (UnitType.java:55).

Movement then takes three layers of correction:

```
实际速度 = speed × boostMultiplier(若 boost) × floorMultiplier(地形) × 转向/加速度影响
```

- `drag = 0.3`: velocity decays proportionally every tick, which produces the "coast after you let go" feel;
- `accel = 0.5`: acceleration as a fraction of speed;
- `rotateSpeed = 5` (degrees/tick): body turn rate, which decides how tight it can circle at point-blank range;
- `strafePenalty = 0.5`: speed penalty when moving opposite the facing direction.

### 2. Movement type (decided by the class, not a hand-written field)

| Type | Implementation | Example units | Key fields |
|---|---|---|---|
| Flying | `flying = true` | flare / horizon / zenith / eclipse | `lowAltitude`, `riseSpeed 0.08`, `descentSpeed 0.08` |
| Tracks | default ground | dagger / fortress / reign | `drag`, `accel` |
| Mech legs | `legCount` (MechComp/LegsComp) | atrax 4 / spiroct 6 / toxopid 8 | `legCount`, `stepShake`, `rippleScale` |
| Naval | `naval` (`naval = true; canDrown = false; omniMovement = false` in init) | risso / minke / omura | water only; pathing uses `Pathfinder.costNaval` |
| Hover | `hovering = true` | spider types can cross terrain | no terrain slowdown, but `muddy`-class statuses still apply |

Note the `naval` field comment: `/** if true, this unit is detected as naval - do NOT assign this manually! Initialized in init() */` (UnitType.java:244-245) — it is derived from the class (`UnitWaterMove`), not configured by hand.

### 3. hitSize

```
/** size of one side of the hitbox square */   // UnitType.java:69-70
该值同时决定：碰撞体尺寸、寻路可通行宽度、被子弹命中的难易
```

- Small: dagger 8, nova 8, flare 9;
- Medium: risso 10, minke 13, toxopid 26;
- Large: reign 30, conquer 46, eclipse 58.

### 4. Terrain and leaving the map

- `floorMultiplier = 1`: how strongly terrain speed applies to this unit (1 = fully affected).
- `canDrown = true`: entering deep water drowns the unit; a larger `drownTimeMultiplier` means a slower death.
- `envDisabled = Env.scorching`: explodes/fails in a "scorching" environment; `envRequired`/`envEnabled` decide whether it can work at all.
- Water slowdown: water surfaces have a lower `floor.speedMultiplier`; naval units use `UnderwaterMoveComp/WaterMoveComp` instead.

### 5. boost

```
canBoost = true → 飞行/机甲可按下"加速"，速度 × boostMultiplier
```

Vanilla `canBoost` units and their multipliers: nova 1.5, pulsar 1.6, quasar 2.0, vela 2.4 (several other boost units also set `canBoost = true`). Boost usually comes with a higher power/liquid draw, or needs the `boost` key.

## Numbers

### Speed table (raw speed → tiles/s)

| Unit | speed(px/t) | tiles/s | hitSize | Type | hp / armor |
|---|---|---|---|---|---|
| alpha | 3.0 | **22.5** | 8 | flying | 150 / 0 |
| gamma | 3.55 | **26.6** | 11 | flying | 220 / 0 |
| flare | 2.7 | 20.25 | 9 | flying | 70 / 0 |
| poly | 2.6 | 19.5 | 9 | flying | 400 / 0 |
| mega | 2.5 | 18.75 | 16.05 | flying | 460 / 3 |
| zenith | 1.7 | 12.75 | 20 | flying | 700 / 5 |
| horizon | 1.65 | 12.4 | 11 | flying | 340 / 3 |
| mono | 1.5 | 11.25 | 0 | flying | 100 / 0 |
| quad | 1.2 | 9.0 | 36 | flying | 6000 / 10 |
| risso | 1.1 | 8.25 | 10 | naval | 280 / 2 |
| crawler | 1.0 | 7.5 | 8 | ground | 150 / 0 |
| dagger | 0.5 | 3.75 | 8 | ground | 150 / 0 |
| toxopid | 0.5 | 3.75 | 26 | spider (8 legs) | 22000 / **22** |
| omura | 0.62 | 4.65 | 58 | naval | 22000 / 16 |
| eclipse | 0.54 | 4.05 | 58 | flying | 22000 / **22** |
| reign | 0.4 | 3.0 | 30 | ground | 24000 / **30** |
| corvus | 0.3 | **2.25** | 29 | spider (4 legs) | 18000 / **14** |

Spread: alpha 22.5 vs corvus 2.25 = **10×**. Crossing a 100-tile map takes alpha about 4.4 s and corvus about 44 s.

### Leg-count distribution (v159.3 UnitTypes.java)

| legCount | Unit |
|---|---|
| 4 | atrax, merui, cleroi, corvus |
| 6 | spiroct, arkyid, merui (some), tecta, anthicus |
| 8 | toxopid, collaris |

## Source anchors

- `UnitType.java:55-56`: `/** movement speed (world units/t) */ public float speed = 1.1f`
- `UnitType.java:57-110`: `boostMultiplier=1f`, `floorMultiplier=1f`, `rotateSpeed=5f`, `drag=0.3f`, `accel=0.5f`, `hitSize=6f`, `riseSpeed=0.08f`, `descentSpeed=0.08f`, `fallSpeed=0.018f`, `wreckHealthMultiplier=0.25f`, `drownTimeMultiplier=1f`, `strafePenalty=0.5f`.
- `UnitType.java:177` `canBoost = false`; `:203` `canDrown = true`; `:205` `useUnitCap = true`; `:213` `lowAltitude = false`; `:221` `hovering = false`; `:223` `omniMovement = true`.
- `UnitType.java:244-245` naval is derived in init; `:924-927` `naval = true; canDrown = false; omniMovement = false;`.
- `UnitType.java:892-903`: picks `Pathfinder.costNaval / costHover / costGround` by type.
- `UnitTypes.java:357/388/447`, `:503-508` and elsewhere: the assignment sites for `canBoost = true` / `lowAltitude = true`.
- `UnitType.java:540-541`: `naval` → databaseTag `"unit-naval"`.

## Tests and counterexamples

**Counterexample 1: treating speed as tiles/s.**
If dagger's `0.5` were tiles/s, crossing 100 tiles would take 200 s; it is actually 3.75 tiles/s → **26.7 s**. Off by 7.5× (exactly 60/8). This is the most common conversion error in this knowledge base.

**Counterexample 2: thinking hitSize is just "how big the sprite is".**
It is also the hitbox side length: hitSize 58 (eclipse) is 7.25× larger than hitSize 8 (dagger), presents 52× the hit area, and cannot fit through a 1-tile gap.

**Counterexample 3: thinking flying units ignore terrain.**
`floorMultiplier` defaults to 1, so flying over `muddy`/`tarred` ground takes the same `speedMultiplier` penalty (statuses land as well, see [[COMBAT.STATUS.001]]).

**Counterexample 4: thinking naval units can beach.**
`naval` is decided by the class and sets `canDrown = false` — amphibious units do not exist in vanilla (`UnitWaterMove` only recognises water).

**Counterexample 5: treating `ucontrol stop` as a brake.**
stop only stops applying thrust; velocity then decays exponentially with `drag = 0.3`. After 120 ticks (2 s) there is still about **0.1 tile** of residual displacement [measured: flare at full speed, then stop, sampling the position every tick]. To stop precisely you must wait it out yourself (or approach the target with `move`); every tile-quantised piece of logic (centering, delivery, docking) has to leave that 0.1 tile of margin.

**Recomputable**: flare speed 2.7 → `2.7 × 60 = 162 px/s`; the map is 264×264 tiles = 2112 px, so crossing takes `2112/162 ≈ 13.0 s`. After boost (e.g. vela ×2.4): `0.44×2.4 = 1.056 px/t = 63.4 px/s`.

## Common misconceptions

- ❌ "Higher speed means better mobility." → drag/accel/rotateSpeed decide the feel; corvus has high drag and slow turning, so it feels clumsier than its speed number suggests.
- ❌ "hovering equals flying." → hovering still hugs the ground (`isGrounded()` is true, ground statuses apply); flying does not hug the ground and ignores ground statuses.
- ❌ "unit speed grows with level." → there is no level system (see [[UNIT.PROGRESSION.001]]).
- ❌ "hitSize can be used directly as a radius." → it is a **square side length**.
- ❌ "all unit numbers changed in v160.7." → across the 70 units only nova's health changed, 120→200; the rest are identical.

## Related

- [[UNIT.PRODUCE.001]] how these units get built
- [[UNIT.AI.001]] which AIs take over movement
- [[UNIT.ABILITY.001]] boost and shield-class abilities
- [[COMBAT.UNITWEAPON.001]] the weapons on these same units
- [[UNIT.NAMES.001]] English/Chinese names of the 70 units (blueprints and wave tables only know ids)
