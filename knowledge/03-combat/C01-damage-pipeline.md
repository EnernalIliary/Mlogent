---
id: COMBAT.DAMAGE.001
title: "Damage pipeline overview: the full order of a hit from BulletType to health"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:480-521"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:549-576"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:593-612"
  - "Mindustry-Source/core/src/mindustry/entities/comp/ShieldComp.java:26-81"
  - "Mindustry-Source/core/src/mindustry/entities/Damage.java:652-661"
  - "Mindustry-Source/core/src/mindustry/entities/comp/HealthComp.java:42-117"
  - "Mindustry-Source/core/src/mindustry/Vars.java:133"
  - "KB/00-data/rt_values_raw.json (mindustry.Vars.minArmorDamage)"
data: [00-data/rt_values_raw.json]
depends: [COMBAT.ARMOR.001]
tags: [damage, armor, shield, splash, pipeline, minimum-damage]
tokens: 783
---

## In one line

A hit always walks the same 6 stages: **hit test → damage value modifiers (armor piercing / armor multiplier / shield cap) → armor reduction → unit multipliers (healthMultiplier, rules.unitHealth) → shield absorption → health subtraction**; armor reduction always uses `max(damage - armor, 0.1 * damage)`, so **no armor however high can push a single shot below 10%, and never to 0**.

## Rules and formulas

### 1. The full order (unit target)

```
BulletType.hit(b, x, y)                      // 1. 触发效果与范围伤害
  → hitEntity(b, unit)                       // 2. 单体命中
      → 计算护盾（maxDamageFraction 时 cap = maxHealth*fraction + shield）
      → 选择伤害模式（三选一）
      → unit.damage / damagePierce / damageArmorMult
          → ShieldComp.damage(amount, withEffect)
              → rawDamage(applyArmor(amount, armor) / healthMultiplier / rules.unitHealth(team))
                  → shield -= min(shield, amount)   // 3. 护盾先吃
                  → health -= 剩余                   // 4. 再扣血
                      → health <= 0 → kill()         // 5. 死亡
```

**The key point: the shield is consumed after armor and before health.** Reversing that order (shielding before armor, or armor applied to health only) is the most common hand-calculation error.

### 2. The three damage modes (a BulletType field picks the branch)

| Field | Value | Method taken | Armor handling |
|---|---|---|---|
| `pierceArmor = true` | false by default | `damagePierce(amount)` | **armor ignored entirely**, raw value subtracted |
| `armorMultiplier != 1` | 1 by default | `damageArmorMult(amount, mult)` | `applyArmor(amount, armor * mult)` |
| neither (the vast majority of bullets) | — | `damage(amount)` | `applyArmor(amount, armor)` |

The three are mutually exclusive; the source is an `if(pierceArmor) … else if(armorMultiplier != 1) … else …` chain.

### 3. The armor formula (the only one in the KB)

```
applyArmor(damage, armor) = max(damage - armor, minArmorDamage * damage)
minArmorDamage = 0.1                       // Vars.java:133，v160.7 反射确认 const=0.1
```

Equivalent form: **actual damage = max(D - A, 0.1·D)**. Once `A ≥ 0.9·D` the hit is in the floor zone and damage stays at `0.1·D`.

### 4. Unit multipliers (applied after armor)

```
最终扣血 = applyArmor(amount, armor) / healthMultiplier / rules.unitHealth(team)
```

- `healthMultiplier`: the health multiplier accumulated from the unit's current statuses (a **bigger** healthMultiplier means tougher, because it is a divisor). freezing = 0.8 → incoming damage ×1.25.
- `rules.unitHealth(team)`: difficulty / wave scaling. 1 by default.
- Splash carries its own `buildingDamageMultiplier`, **applied to buildings only**; it does not affect units.

### 5. Splash falloff

```
calculateDamage(radius, dist) = lerp(1 - dist/radius, 1, 0.4)     // falloff = 0.4
→ 中心 100%，边缘 40%，与距离线性
```

A radius ≤ 1e-5 counts as a single point and does not fall off. With `scaledSplashDamage = true` the splash damage is multiplied once more by a damage-proportional factor such as `damage / 100` (the `splashDamage * b.damageMultiplier()` branch in the source).

### 6. Continuous damage (lasers / fire / liquid streams)

`damageContinuous(amount)` = `damage(amount * Time.delta)`. **The damage field is damage per tick, not per shot.** At 60 tick/s a ContinuousLaser with `damage=78` deals 78*60 = 4680 per second.

## Numbers

| Quantity | Value | Source |
|---|---|---|
| `Vars.minArmorDamage` | 0.1 | Vars.java:133; `00-data/rt_values_raw.json` reflection const=0.1 |
| `BulletType.damage` default | 1f | BulletType.java:41 |
| `BulletType.splashDamage` default | 0f | BulletType.java:109 |
| `BulletType.statusDuration` default | 480 tick = 8 s | BulletType.java:119 (`60*8`) |
| `BulletType.buildingDamageMultiplier` default | 1.0 | BulletType.java:99 + v160.7 reflection |
| splash falloff | 0.4 | Damage.java:652-656 |
| `Vars.tilesize` | 8 px | Vars.java:135; v160.7 reflection const=8 |
| `Vars.tilePayload` | 64 px² | Vars.java:137 |

## Source anchors

- `entities/bullet/BulletType.java:480-521` `hitEntity`: shield cap, the three damage modes, then `unit.apply(status, statusDuration)` and knockback.
- `entities/bullet/BulletType.java:549-576` execution order of `hit(b,x,y)`: hitEffect/sound → frags → puddles → incend → createUnits → suppression → **createSplashDamage** → lightning.
- `entities/bullet/BulletType.java:593-612` `createSplashDamage`: calls `Damage.damage(..., splashDamage * b.damageMultiplier(), splashDamagePierce, ..., armorMultiplier)` and re-applies status to units inside the radius.
- `entities/comp/ShieldComp.java:26-31` `damage(amount, withEffect)`: `rawDamage(applyArmor(amount, armorOverride >= 0 ? armorOverride : armor) / healthMultiplier / state.rules.unitHealth(team))`.
- `ShieldComp.java:35-43` `damagePierce` goes straight to rawDamage, no armor subtraction.
- `ShieldComp.java:47-55` `damageArmorMult(amount, armorMult)` → `applyArmor(amount, armor * armorMult)`.
- `ShieldComp.java:57-81` `rawDamage`: shield first (`shieldDamage = min(max(shield,0), amount)`), the remainder comes off health; death goes through `kill()`; a shield break plays `Fx.unitShieldBreak`.
- `entities/Damage.java:652-661`: the 0.4 falloff of `calculateDamage` and `applyArmor`.
- `entities/comp/HealthComp.java:71-79` `damage(amount)`: `health -= amount; hitTime = 1f; if(health <= 0 && !dead) kill();`
- `HealthComp.java:109-117` `heal(amount)` and `healFract(amount)` (a 0~1 fraction of maxHealth).

## Measurements and counterexamples

**Counterexample 1: treating armor as a percentage damage reduction.**
Wrong hand calculation: toxopid armor 22 (v160.7 jar; 13 in the v159.3 source), dagger at 9 per shot → expected "9 × (1 - 22%) = 7.02".
Source result: `applyArmor(9, 22) = max(9-22, 0.9) = 0.9`. **A 9-damage shot removes only 0.9 health**; 22 armor eats 90% of the 9 damage (it lands on the 10% floor). This is exactly why small-caliber turrets do almost nothing to heavy armor.

**Counterexample 2: expecting high armor to give full immunity.**
Armor 50 vs 5 per shot: `max(5-50, 0.5) = 0.5`, still 0.5. As long as `damage > 0`, damage stays ≥ 10%. So apart from crawler (0-speed self-destruct bullet) vanilla has no "full immunity" mechanism; real immunity comes from `immunities` (see COMBAT.ARMOR.001).

**Counterexample 3: reading statusDuration as seconds.**
`statusDuration = 480` is ticks, **8 seconds**, not 480 seconds; the `60*8` spelling in the source exists precisely to prevent that misreading.

**A checkable example**: duo vs dagger (armor 0): 9 damage → 9 health; vs fortress (armor 9): `max(9-9, 0.9)=0.9`. The same bullet needs 1000 rounds against a 900-health fortress but only 17 against a 150-health dagger.

## Common misconceptions

- ❌ "shields are computed before armor". → Wrong: armor is settled first, and the shield absorbs a value that **has already been reduced by armor**.
- ❌ "armor piercing (pierceArmor) halves armor". → It **skips** `applyArmor` entirely; not a single point of armor is subtracted.
- ❌ "the splash edge is half of the center". → It is **40%** (falloff 0.4).
- ❌ "`rules.unitHealth` also affects player units". → It is read per team; the player team defaults to 1, and only wave enemies take difficulty scaling.
- ❌ "armor does not apply to splash". → Splash runs the same `damage()` pipeline (`armorMultiplier` is passed along too), so armor applies and the 10% floor applies with it.

## See also

- [[COMBAT.ARMOR.001]] armor formula derivation and armor piercing
- [[COMBAT.BULLET.001]] bullet fields and ballistics
- [[COMBAT.STATUS.001]] status multipliers (healthMultiplier lives in this pipeline)
- [[COMBAT.NUMBERS.001]] hand-computing TTK with this pipeline
