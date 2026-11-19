---
id: COMBAT.DEFENSE.001
title: "Defenses: stats and resolution order of walls, doors, shields and repair turrets"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "MBO/gamedata/v160.7/gamedata.json blocks[].raw（wall/door/shield/mend 各字段）"
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:1762-1778,467-483,1929"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ShieldWall.java:15-17,44,80,102"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ForceProjector.java:32-45,206-250"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/MendProjector.java:26-31,113"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/OverdriveProjector.java:23-29,110"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ShockwaveTower.java:25-29,87"
data: [00-data/blocks.json]
depends: [COMBAT.ARMOR.001, COMBAT.SUPPORT.001]
tags: [wall, door, shield, force-field, repair, overdrive, defense-block]
tokens: 892
---

## In one line

Vanilla defense is **four layers**: walls (pure hp+armor) → shield walls/force fields (eat damage first, and breaking sends them into cooldown) → repair/overdrive (lifting hp and fire rate back up) → turrets (the actual output); the resolution order is **bullet.damage → armor applyArmor → shield absorption → block hp**, so shields take damage that has **already passed armor**.

## Rules and formulas

### 1. The full order of a bullet against a block

```
1. damage = bullet.type.buildingDamage(bullet)                        // 含 buildingDamageMultiplier
2. if(!pierceArmor) damage = applyArmor(damage, block.armor * t.armorMultiplier * t.blockArmorMultiplier)
3. building.damage(bullet, source, damage)                            // ShieldWall 等在此切走护盾
4. ShieldWall: shieldTaken = broken ? 0 : min(shield, damage); shield -= shieldTaken; 剩余进 hp
5. hp <= 0 → 方块被摧毁（掉落残骸/爆炸）
```

### 2. Walls

Walls provide **hp + armor** only and do not stop bullets from piercing (a bullet with `pierceBuilding = true` passes through). `Block.armor` goes through exactly the same `applyArmor` as units (see [[COMBAT.ARMOR.001]]), so **a tungsten-wall with armor 14 is immune to every single hit ≤15.5 damage** (the knee where `0.9×damage <= armor`).

### 3. Doors

`door`/`door-large`/`blast-door` are `AutoDoor`s: they open as a unit approaches and close when it leaves. An open door **blocks neither bullets nor movement** — a "wall on a timer". blast-door 2×2 has armor 14, making it the toughest passage in the whole game.

### 4. Shield wall ShieldWall

```
shield = clamp(shield + regenSpeed * edelta(), 0, shieldHealth)       // regenSpeed = 2/s
breakCooldown = 600 tick = 10 s                                       // 破盾后 10 秒不回复
```

The shield absorbs the **full** `min(shield, damage)` (no decay), so shielded-wall's effective health is `4160 + 900 = 5060` (against bullets that cannot pierce it in one hit).

### 5. Force projector ForceProjector (3×3)

It is not health but a **buildup pool**:

```
吸收: buildup += bullet.damage（仅当 !broken 且子弹落在六边形半径内）
破碎: buildup >= shieldHealth + phaseShieldBoost*phaseHeat → broken = true, buildup = shieldHealth
回复: buildup -= delta() * scale
      scale = cooldownNormal(1.75)                      // 正常
            × cooldownLiquid(1.5) × (1 + (heatCapacity-0.4)*0.9)  // 有冷却液
      broken 时 scale = cooldownBrokenBase(0.35)
```

- 750 shield, no coolant: refilling takes `750 / (1.75×60) ≈ 7.1 s`;
- after being broken it must refill a full 750 points before broken clears: `750 / (0.35×60) ≈ 35.7 s` (completely non-absorbing during that time);
- with coolant (water heatCapacity 0.4): scale ×1.5 → refills in 4.8 s.

### 6. Overdrive projector OverdriveProjector

```
applyBoost(realBoost(), reload + 1)     // speedBoost = 1.5, speedBoostPhase = 0.75 → 最高 2.25
BuildingComp.delta() = Time.delta * timeScale      // L1929
```

What it speeds up is **a building's delta**, which means: turret reload ticks faster (fire rate ×1.5), factories build faster, repairers heal faster. Blocks with `canOverdrive = false` (walls, cores) are unaffected.

### 7. Repairers and repair turrets

```
MendProjector: heal = maxHealth * (12 + phaseHeat*12)/100 * efficiency   // 每次 reload 250 tick
RepairTurret:  heal = repairSpeed * strength * edelta() * multiplier       // 持续
```

## Numbers

### Walls and doors (v160.7 reflection raw)

| block | size | hp | armor | special |
|---|---|---|---|---|
| copper-wall | 1×1 | 320 | 0 | — |
| titanium-wall | 1×1 | 440 | 0 | — |
| plastanium-wall | 1×1 | 500 | 0 | `absorbLasers = true` (blocks lasers) |
| thorium-wall | 1×1 | 800 | 0 | — |
| phase-wall | 1×1 | 600 | 0 | phases on hit (damage-immunity window) |
| surge-wall | 1×1 | 920 | 0 | `lightningChance = 0.05` counterattack |
| beryllium-wall | 1×1 | 520 | 2 | — |
| tungsten-wall | 1×1 | 720 | 14 | — |
| carbide-wall | 1×1 | 1080 | 16 | toughest 1×1 in vanilla |
| shielded-wall | 2×2 | 4160 | 15 | shieldHealth 900 |
| door | 1×1 | 400 | 0 | AutoDoor |
| door-large | 2×2 | 1600 | 0 | AutoDoor |
| blast-door | 2×2 | 2800 | 14 | AutoDoor |

### Shield/support blocks

| block | size | hp | key parameters |
|---|---|---|---|
| force-projector | 3×3 | 360 | shieldHealth 750, radius 101.7 px, sides 6, phaseUseTime 350, phaseShieldBoost 400, phaseRadiusBoost 80 |
| shield-projector | 3×3 | 360 | BaseShield (shield projector, a movable shield) |
| mender | 1×1 | 80 | range 40, reload 200, heal 12%/event, phaseRangeBoost 20 |
| mend-projector | 2×2 | 320 | range 85, reload 250, heal 12%/event, phaseRangeBoost 50 |
| overdrive-projector | 2×2 | 175 | range 80, reload 60, speedBoost 1.5, speedBoostPhase 0.75, useTime 400 |
| shockwave-tower | 3×3 | 915 | range 170 (v160.7 raw) / 110 (source default), reload 80/90, bulletDamage 160, falloffCount 20 |
| repair-point | 1×1 | 40 | repairSpeed 0.45/s |
| repair-turret | 2×2 | 205 | repairSpeed 3/s |
| radar | 1×1 | 60 | provides vision |

### Cores (losing one loses the game)

| block | size | hp | armor | unitCapModifier |
|---|---|---|---|---|
| core-shard | 3×3 | 1100 | 0 | 8 |
| core-foundation | 4×4 | 3500 | 0 | 16 |
| core-nucleus | 5×5 | 6000 | 0 | 24 |
| core-bastion | 4×4 | 4500 | 5 | 15 |
| core-citadel | 5×5 | 16000 | 10 | 15 |
| core-acropolis | 6×6 | 30000 | 15 | 15 |

## Source anchors

- `BuildingComp.java:1762-1778` `collision(Bullet)`: armor is settled here, then handed to the subclass `damage(...)`.
- `BuildingComp.java:467-483` `applyBoost(intensity, duration)`: timeScale takes the strongest intensity.
- `BuildingComp.java:1929` `delta() = Time.delta * timeScale`.
- `ShieldWall.java:15-17` shieldHealth 900 / breakCooldown 600 / regenSpeed 2.
- `ShieldWall.java:102` `shieldTaken = broken() ? 0f : Math.min(shield, damage)`.
- `ForceProjector.java:32-45` phaseUseTime 350, phaseRadiusBoost 80, phaseShieldBoost 400, radius 101.7, sides 6, shieldHealth 700, cooldownNormal 1.75, cooldownLiquid 1.5, cooldownBrokenBase 0.35, crashDamageMultiplier 2.
- `ForceProjector.java:217-245` buildup accumulation, the break test, and `broken` clearing on `buildup <= 0`.
- `ForceProjector.java:270` `absorb = !broken && Intersector.isInRegularPolygon(sides, x, y, realRadius(), ...)`.
- `MendProjector.java:26-31` reload 250, range 60, healPercent 12, phaseBoost 12, phaseRangeBoost 50.
- `OverdriveProjector.java:110` `other.applyBoost(realBoost(), reload + 1f)`.
- `ShockwaveTower.java:87` `waveDamage = min(bulletDamage, bulletDamage*falloffCount/targets.size)`.

## Measurements and counterexamples

**Counterexample 1: assuming the shield eats damage first and armor reduces it afterwards.**
The order is the opposite: `BuildingComp.collision` calls applyArmor first, then `ShieldWall.damage`. So a 20-damage bullet against shielded-wall (armor 15): 5 points after armor, and the shield loses only 5, not 20.

**Counterexample 2: assuming a force field recovers the instant it is broken.**
Once broken, scale drops to 0.35, and a full 750 must be refilled before broken clears — a **35.7 second dead window**. During it, spectre (428 DPS) can shoot straight through the 3×3's 360 hp.

**Counterexample 3: assuming doors block bullets.**
An open AutoDoor takes no part in collision. To "block movement and bullets" you must use blast-door and keep it closed (which also blocks your own units).

**Counterexample 4: assuming overdrive only affects turrets.**
It affects the delta of every `canOverdrive` building — factories, repairers and drills all speed up; but **walls and cores do not**.

**Recomputable**: thorium-wall 800 hp, armor 0, against dagger (9 per shot, 3 shots/s): `800/9 = 89 shots`, i.e. `89/3 ≈ 29.6 s`. The same wall against spectre (50 per shot, 8.57 shots/s): `16 shots`, `1.87 s`. Switch to carbide-wall (1080 hp, armor 16) against an undefended dagger: per shot `max(9-16,0.9)=0.9` → **1200 shots ≈ 400 s**; but against titan (350 per shot): `334` → 4 shots.

## Common misconceptions

- ❌ "the more expensive the wall, the better". → Against high single-hit damage (titan/malign), carbide-wall's armor 16 is worth only 1080 hp; against dense small calibers, armor is king.
- ❌ "shieldHealth is the shield wall's health". → ShieldWall is an extra 900-point buffer with a 10 s break cooldown; ForceProjector is a **buildup pool** model, not health.
- ❌ "repairers can repair walls". → MendProjector only heals friendly blocks and units with `hasHealth` (`canHeal = !checkSuppression()`), and is subject to `suppression`.
- ❌ "shockwave-tower numbers are the same in both versions". → v160.7 raw: range 170, reload 80; v159.3 source default: range 110, reload 90. v160.7 wins.
- ❌ "a core with high armor is safe". → Core armor tops out at 15, which still lets malign (70 per shot) through for 55 a hit.

## See also

- [[COMBAT.ARMOR.001]] block armor and applyArmor
- [[COMBAT.SUPPORT.001]] repair and shields from the unit side
- [[COMBAT.TURRET.001]] turret numbers (the output layer of defense)
- [[COMBAT.WAVE.001]] which waves will break these four layers
