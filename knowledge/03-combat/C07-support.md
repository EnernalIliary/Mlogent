---
id: COMBAT.SUPPORT.001
title: "Healing, shields and repair: heal / shield / mend / repairSpeed"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/comp/HealthComp.java:42-117"
  - "Mindustry-Source/core/src/mindustry/entities/comp/ShieldComp.java:57-81"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/MendProjector.java:26-115"
  - "Mindustry-Source/core/src/mindustry/world/blocks/units/RepairTurret.java:33,74,207"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ForceProjector.java:32-115"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ShieldWall.java:14-80"
  - "MBO/gamedata/v160.7/gamedata.json (mender/mend-projector/force-projector/shielded-wall/repair-* raw)"
data: [00-data/blocks.json]
depends: [COMBAT.DAMAGE.001, COMBAT.ARMOR.001]
tags: [healing, shield, repair, mend, repairSpeed, force-field, shield-wall]
tokens: 705
---

## In one line

Healing comes in **three completely different units**: a unit's `heal(amount)` is **flat HP**, a repair block's `healPercent` is **a percentage of the target's max health per event**, and a repair turret's `repairSpeed` is **HP per second**; shields are always "a separate bar drained before health", and **breaking does not overflow** (only the surplus reaches health).

## Rules and formulas

### 1. Unit healing (HealthComp)

```
heal(amount)      → health += amount; clampHealth()        // 平量，上限 maxHealth
healFract(f)      → heal(f * maxHealth)                    // 比例
heal()            → health = maxHealth（同时清 dead 标记，复活用）
damageContinuous  → amount * Time.delta（每 tick 结算的伤害/治疗）
```

Healing **never** goes past `maxHealth` (`clampHealth`), and it **does not care where the damage came from** — it adds health while ignoring armor.

### 2. Repair projector (MendProjector)

```
每 reload tick 一次：
    range_real = range + phaseHeat * phaseRangeBoost
    对范围内所有友方建筑：
        other.heal(other.maxHealth() * (healPercent + phaseHeat * phaseBoost) / 100 * efficiency)
```

**Key: the heal amount is a percentage of the target's max health**, not a fixed value. So one mend-projector repairs a 3×3 core with far "more numbers" than a 1×1 wall, yet the **fraction of the repair time is the same**.

- `reload = 250` tick (≈4.17 s)
- `healPercent = 12` (12% max health per event)
- equivalent `= 12% / 4.17s ≈ 2.88% maxHP/s`
- `phaseBoost = 12`, `phaseRangeBoost = 50`: at full phase (phase fabric) another 12% and 50px more range

### 3. Repair turret / repair point (RepairTurret)

```
target.heal(repairSpeed * strength * edelta() * multiplier)     // RepairTurret.java:207
每秒修复量 = repairSpeed * 60 * strength * multiplier
```

`repairSpeed` itself is "HP per tick"; the UI multiplies by 60 to show /s: `stats.add(Stat.repairSpeed, repairSpeed * 60f, StatUnit.perSecond)`.

### 4. Shields

```
单位护盾（ShieldComp）: rawDamage 时先扣 shield，剩余才扣 health
                        shield -= min(shield, amount)          // 不溢出、不浪费
方块护盾:
    ForceProjector: shieldHealth，环形拦截子弹（每发按 shieldDamage 累积 buildup）
    ShieldWall:      shieldHealth 900，regenSpeed 恢复
力场被打破 → broken 状态 + breakCooldown 期间不恢复
```

## Numbers

| block / unit | field | value | per-second equivalent |
|---|---|---|---|
| mender | range / reload | 40px / 200 tick | 12% per event (default healPercent) → 3.6%/s |
| mend-projector | range / reload | 85px / 250 tick | 12% / 4.17s = **2.88% maxHP/s** |
| repair-point | repairSpeed | 0.45 /tick | **27 HP/s** |
| repair-turret | repairSpeed | 3.0 /tick | **180 HP/s** |
| force-projector | shieldHealth | 750 (v160.7) | radius radius=101.7px ≈ 12.7 tiles; phaseUseTime 350 |
| shielded-wall | shieldHealth | 900 | 2×2, armor 15, main hp 4160 |
| core-shard / foundation / nucleus | hp | 1100 / 3500 / 6000 | 5.5× spread in healing base |

Phase bonus: `phaseRangeBoost` mender 20, mend-projector 50; at full phase healing rises from 12% to 24% (+phaseBoost 12).

A unit's "built-in shield" comes from the wave: `SpawnGroup.getShield(wave) = max(shields + shieldScaling*(wave-begin), 0)` — unrelated to unit type, granted by the **wave configuration**.

## Source anchors

- `HealthComp.java:42-45` `heal()` full-health revive; `:103-106` `clampHealth`; `:109-117` `heal(amount)` / `healFract`.
- `HealthComp.java:71-79` `damage(amount)` does `health -= amount` directly (armor was already resolved upstream).
- `ShieldComp.java:57-81` `rawDamage`: `shieldDamage = min(max(shield,0), amount)`, the remainder goes to health.
- `MendProjector.java:26-30` `reload=250`, `range=60`, `healPercent=12`, `phaseBoost=12`, `phaseRangeBoost=50`; the heal call at `:113`; UI `repairTime = 100/healPercent*reload/60` seconds at `:62`.
- `RepairTurret.java:33` `repairSpeed = 0.3f` class default (Blocks overrides with 0.45 / 3.0, see `Blocks.java:6389,6401`); the actual heal call at `:207`; the per-second display at `:74`.
- `ForceProjector.java:32-39` `phaseUseTime=350`, `radius=101.7`, `shieldHealth=700` (v160.7 raw is 750); `:59-67` bullet buildup `buildup += bullet.type.shieldDamage(bullet)`.
- `ShieldWall.java:15,44,80` `shieldHealth=900`, `shield = shieldHealth`, `shield += regenSpeed*edelta()`.
- `game/SpawnGroup.java:76-78` `getShield(wave)`.

## Measurements and counterexamples

**Counterexample 1: reading mend-projector's 12 as "12 HP".**
`healPercent = 12` is **12% of the target's max health**. Repairing a 6000 hp nucleus returns **720 HP** per event; repairing a 320 hp copper wall returns only 38.4 HP. Paring a big projector with "small blocks" is a huge waste.

**Counterexample 2: assuming repairSpeed is per second.**
`repairSpeed = 3` is **3 HP per tick** → 180 HP/s. Writing it as 3 HP/s underestimates by 60× (the most common /tick versus /s mix-up in this knowledge base).

**Counterexample 3: assuming a shield break overflows damage.**
`shieldDamage = min(shield, amount)`, `amount -= shieldDamage` — the overflow **does** reach health (that part is right), but the shield itself **never goes negative**, so there is no "extra reflect damage on break".

**Counterexample 4: healing against the damage of high-armor units.**
Healing ignores armor, but its scale is tiny: repair-turret at 180 HP/s versus spectre's 428.6 DPS against 0 armor, **it cannot keep up**; holding that requires shield-type blocks (force-projector's separate 750-point bar).

**Recomputable**: a mend-projector repairing a 3×3 core (3500 HP, core-foundation): `3500 × 12% = 420` per event, once every 4.17 s → 100.7 HP/s. From empty to full takes `3500/100.7 ≈ 34.8 s`.

## Common misconceptions

- ❌ "healing can exceed max health". → `clampHealth` is a hard cap.
- ❌ "shields are deducted after armor reduction". → Shields take the value **already past armor**; the shield itself has no armor.
- ❌ "repair blocks can repair units". → MendProjector repairs **blocks only** (indexer.eachBlock + player.team); units rely on repair-turret/abilities.
- ❌ "a force shield with an hp bar is guaranteed to hold". → Once `buildup` fills, it enters the broken cooldown and is completely down while it lasts.
- ❌ "the shielded status means an added shield". → It is `healthMultiplier = 3` (2/3 damage reduction), not a shield value.

## See also

- [[COMBAT.DAMAGE.001]] shield absorption happens after armor
- [[COMBAT.DEFENSE.001]] the full hp/shield table of defensive blocks
- [[UNIT.ABILITY.001]] the RepairField/ShieldRegen abilities
- [[COMBAT.NUMBERS.001]] comparing healing to DPS
