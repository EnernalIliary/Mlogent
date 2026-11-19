---
tokens: 622
id: COMBAT.TURRET.111
title: segment — the 225-per-second projectile sweeper
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3836"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/segment"
  - "jar:v160.7#blocks/segment"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, segment, projectile interception / anti-air bullet clearing]
---

## One line

segment is the only turret that "kills nothing, clears projectiles": it aims at enemy bullets rather than units, 30 bullet damage per shot at 7.5 shots/s for 225/s of interception throughput. It turns an airdrop wave from a threat into arithmetic, at the price of 480/s of power and exactly zero lethality -- if the enemy brings no barrage, it simply holds a turret slot for nothing. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: projectile interception / anti-air bullet clearing
- **Firing mode**: point defence (intercepts 1 projectile per trigger) (1 shot per trigger; reload 8 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: (not marked in the table)
- PointDefenseTurret class: the target filter keeps enemy projectiles only (units are never selected), so it never adds output on behalf of other turrets [src: 00-data/turrets.json]
- reload 8 ticks ⇒ 7.5 shots/s, the 30 bulletDamage per shot settles against projectiles only, 225/s of interception throughput [src: 00-data/turrets.json]
- interception is probabilistic: the faster the bullets and the more arrive at once, the higher the leak rate; 225/s is a ceiling, not a guarantee [src: 00-data/turrets.json]
- a 180-world-unit (22.5 tiles) reach means it must cover in front of the threatened direction, not hug the core [src: 00-data/turrets.json]
- **Strengths**:
  - intercepting 225/s of projectile damage effectively erases enemy ranged output, extremely effective against artillery and missile waves [src: 00-data/turrets.json]
  - it consumes no item ammo, only 480/s of power, so once the late-game grid is comfortable supply pressure is zero [src: 00-data/turrets.json]
  - 22.5 tiles of coverage puts one turret over a whole section of line [src: 00-data/turrets.json]
- **Weaknesses**:
  - zero damage against units: when the enemy stays outside its barrage or pushes with melee units it contributes nothing all game [src: 00-data/turrets.json]
  - 480/s is a real power price in the mid game, needing a dedicated grid or battery buffer [src: 00-data/turrets.json]
  - 225/s is only a ceiling, and against fast surge-type projectiles it still leaks [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 2 | 00-data/blocks.json |
| Health | 1000 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 290 items (titanium × 40, thorium × 80, silicon × 130, phase-fabric × 40) | 00-data/blocks.json |
| Range | 180 world units (22.50 tiles) | 00-data/turrets.json |
| reload | 8 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 2 / 5 | 00-data/turrets.json |
| Power draw | 480/s | 00-data/turrets.json |

| Item | Value | Notes | Source |
|---|---|---|---|
| bulletDamage | 30 | damage against projectiles | Mindustry-Source/core/src/mindustry/content/Blocks.java:3837 |
| Shots/s | 7.5 | reload 8 ticks | Mindustry-Source/core/src/mindustry/content/Blocks.java:3843 |
| Interception throughput | 225/s | holds against projectiles only, never units | this article's metric |
| Power draw | 480/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:3849 |

- a point-defence turret: it shoots down incoming bullets and shells and deals no damage to units or buildings; its "DPS" is interception throughput, not lethality. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3836]
- its value against barrage enemies far exceeds the number; against pure laser or melee enemies it is near zero. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3836]

- this library gives segment no "DPS" ranking: 30 is projectile damage, it does not enter unit damage statistics, and 225/s is interception throughput rather than lethality [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3836 — definition line new PointDefenseTurret("segment")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this turret does not override it)
- 00-data/turret_shots.json#id=segment — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: segment against a pure melee wave (crawler/risser); it does not select units, zero output for the whole wave. Reproduce: segment's target fields in 00-data/turrets.json and the MANUAL table notes "hits projectiles only, not units" [src: 00-data/turrets.json]
- Counterexample: computing "30 × 7.5 = 225 DPS so it can hit units" from the 30 per shot; a 225/s figure is only mid-pack as real DPS, and it never lands on a unit at all [src: 00-data/turrets.json]

## Common misconceptions

- "a point-defence turret equals an anti-air turret" wrong: it intercepts bullets, the flying unit itself is not in its target set
- "interception rate is 100%" wrong: 225/s is a throughput ceiling, denser or faster incoming fire leaks [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.108]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.110]]
- [[COMBAT.TURRET.112]]
