---
id: COMBAT.BULLET.001
title: "Bullets and ballistics: lifetime/speed/drag, piercing, splash, lightning and fragments"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:33-63"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:109-220"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414-440"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:480-612"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:832"
  - "MBO/gamedata/v160.7/gamedata.json (28 turret raw)"
data: [00-data/bullets.json]
depends: [COMBAT.DAMAGE.001, COMBAT.TURRET.001]
tags: [bullet, ballistics, range, pierce, splash, lightning, fragments, drag]
tokens: 746
---

## In one line

A bullet's **real range = speed × lifetime (px/tick × tick)**, a separate number from the turret `range` — the turret only "looks for a target inside range", while the bullet disappears once lifetime runs out; also `splashDamageRadius` defaults to **-1 meaning no splash** (not a 0 radius), and `pierceCap = -1` means piercing is **unlimited**.

## Rules and formulas

### 1. Range

```
无阻力:  bulletRange = speed * lifetime                      // 单位 px
有阻力:  bulletRange = speed * (1 - pow(1 - drag, lifetime)) / drag
实际:    最终射程 = max(bulletRange, maxRange)                 // 若 maxRange > 0
```

- `speed` is in **px/tick** (1 tile = 8px, 60 tick = 1s). Speed 3.5 → 210 px/s ≈ 26 tiles/s.
- `lifetime` is in **tick**. dagger's basic bullet: speed 2.5, life 60 → 150px ≈ 18.75 tiles.
- **With drag > 0 the range saturates at `speed/drag`** and speed×lifetime is never reached: speed=2.5, drag=0.1, life=60 → `2.5*(1-0.9^60)/0.1 = 24.96px` (≈3.1 tiles), whereas drag=0 with the same parameters gives 150px. A 6× range gap, so "range = lifetime×speed" holds only for bullets with drag=0.

### 2. Piercing

```
pierce = false           → 命中首个目标后消失
pierce = true            → 继续飞
pierceCap = -1（默认）   → 贯穿数无上限；>0 则命中 N 个后停止
pierceDamageFactor > 0   → 每穿一个目标，伤害按 initialHealth * factor 递减
removeAfterPierce = true → damage 归零即移除
```

reign's bullet has `pierce cap 10`: a single shot can punch through at most 10 units.

### 3. Splash

```
splashDamageRadius = -1（默认）→ 无溅射（>0 才结算）
溅射伤害 = Damage.damage(..., splashDamage * b.damageMultiplier(), ...)
边缘衰减 = lerp(1 - dist/radius, 1, 0.4)   // 边缘 40%
splashDamagePierce = true → 溅射无视护甲
scaledSplashDamage = true → 溅射按子弹伤害缩放
```

**The splash radius is in pixels** (divide by 8 for tiles): fortress's artillery `splash 80 r35` = 35px ≈ 4.4 tiles.

### 4. Lightning and fragments (secondary damage after a hit)

```
lightning > 0 → 命中时在落点生成 lightning 条闪电
lightningDamage < 0 → 用子弹自身 damage（默认 -1，即"等于弹伤"）
lightningLength = 5（默认），lightningLengthRand = 0
fragBullets = 9（默认）→ 命中/消失时炸出 9 个碎片
fragVelocityMin/Max = 0.2 / 1.0；fragLifeMin/Max = 1.0
```

**fragBullets already defaults to 9**, so any bullet that has a non-null `fragBullet` and never sets fragBullets bursts into 9 fragments — this is where the "handy 9× damage" derails most often.

### 5. Collision switches

`collidesTiles = true`, `collidesAir = true`, `collidesGround = true`, `collidesTeam = false`, `collides = true`, `collideTerrain/collideFloor = false`, `hittable = true`, `absorbable = true` (can be absorbed by shields/force fields), `reflectable = true`.

## Numbers

| Field | Default | Note |
|---|---|---|
| `lifetime` | 40 tick | BulletType.java:33 |
| `speed` | 1f px/tick | :37 |
| `damage` | 1f | :41 |
| `hitSize` | 4f | :43 (collision size, not damage) |
| `drag` | 0f | :49 |
| `pierce` | false | :53 |
| `pierceCap` | -1 | :57 (-1 = unlimited) |
| `pierceDamageFactor` | 0f | :59 |
| `maxDamageFraction` | -1f | :61 (per-shot cap = target maxHP × this value) |
| `removeAfterPierce` | true | :63 |
| `splashDamage` | 0f | :109 |
| `splashDamageRadius` | -1f | :301 (≤0 = no splash) |
| `splashDamagePierce` | false | :303 |
| `scaledSplashDamage` | false | :111 |
| `statusDuration` | 480 tick = 8 s | :119 |
| `ammoMultiplier` | 2f | :95 |
| `lightning` | 0 | :333 |
| `lightningLength` | 5 | :335 |
| `lightningDamage` | -1 | :339 (-1 = use this bullet's damage) |
| `fragBullets` | 9 | :212 |
| `pierceArmor` / `armorMultiplier` | false / 1f | :187 / :189 |

Typical turret bullets in v160.7 (speed, damage, range):
duo+copper Basic(2.5, 9, life60=150px); hail+graphite Artillery(3, 20, life? the Artillery default life is computed by code); spectre+thorium Basic(8, 80, life?); foreshadow uses rail; meltdown's `ContinuousLaserBulletType(78)` — the 78 is **damage per tick**.

## Source anchors

- `BulletType.java:33-63` core field defaults (lifetime=40, speed=1, damage=1, hitSize=4, drag=0, pierceCap=-1).
- `BulletType.java:414-432` `estimateDPS()`: `(damage + splashDamage*0.75) * (pierce ? (pierceCap==-1?2:clamp(pierceCap,1,2)) : 1)`, then adds `fragBullet.estimateDPS()*fragBullets/2`. **This is where the in-game DPS display comes from, and why it reads systematically high** (it assumes every splash hits and pierces 2 targets).
- `BulletType.java:435-440` `calculateRange()`: without drag it uses `speed*lifetime`, with drag it uses `speed*(1-pow(1-drag,lifetime))/drag`, then takes the max with `maxRange`.
- `BulletType.java:480-521` `hitEntity`: shield cap → the three damage modes → status/knockback.
- `BulletType.java:523-532` `handlePierce`: `sub = max(initialHealth*pierceDamageFactor, 0)`, `b.damage -= min(b.damage, sub)`.
- `BulletType.java:549-576` execution order of `hit` (frags → puddles → incend → createUnits → suppression → splash → lightning).
- `BulletType.java:594-600` splash: only `splashDamageRadius > 0` calls `Damage.damage`, after which `Damage.status` applies status over the same area.
- `BulletType.java:574` lightning: `lightningDamage < 0 ? damage : lightningDamage`.

## Measurements and counterexamples

**Counterexample 1: using the turret range as the bullet range.**
duo range=160, but the copper bullet is 2.5×60 = 150px. A target standing at the 155–160px edge draws fire while the **bullet dissipates early**, which looks like "it cannot hit".

**Counterexample 2: reading `splashDamageRadius = -1` as "radius of 1px".**
The source condition is `splashDamageRadius > 0`, so -1 **turns splash off**. Conversely, a bullet with `splashDamage > 0` but no radius set also does **not** splash.

**Counterexample 3: reading `pierceCap = -1` as "does not pierce".**
-1 means **no cap**; `pierce = false` is what disables piercing. They are independent fields: pierce=true + pierceCap=-1 = unlimited penetration.

**Counterexample 4: ignoring that fragBullets defaults to 9.**
metaglass's scatter bullet sets `frag Basic(3,5)` without fragBullets → it actually bursts 9 fragments of 5 damage = 45 potential damage, 15× the main bullet.

**Recomputable**: meltdown's `ContinuousLaserBulletType(78)`, continuous damage applied as `damage * Time.delta` → 78×60 = **4680 DPS** per second (single target, no armor). Against a target with armor 13: `max(78-13, 7.8)=65`/tick → 3900 DPS.

## Common misconceptions

- ❌ "speed is tiles/s". → It is **px/tick**; conversion: speed × 60 / 8 = tiles/s.
- ❌ "lifetime is seconds". → tick, 60 tick = 1 s.
- ❌ "fragment damage gets some multiplier beyond fragBullets". → Each fragment independently runs the whole damage pipeline (each one eats armor).
- ❌ "drag only affects appearance". → drag directly sets the range saturation value (of order `speed/drag`).
- ❌ "lightning damage is fixed". → With `lightningDamage = -1` it equals this bullet's damage; only a hard-coded number overrides that.

## See also

- [[COMBAT.DAMAGE.001]] the armor/shield order after a hit
- [[COMBAT.TURRET.001]] how turrets load and fire these bullets
- [[COMBAT.STATUS.001]] how `status`/`statusDuration` resolve
- [[COMBAT.NUMBERS.001]] recomputing DPS with this page's formulas
