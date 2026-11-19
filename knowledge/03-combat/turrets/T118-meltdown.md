---
tokens: 598
id: COMBAT.TURRET.118
title: meltdown — the 936-DPS cutting laser
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4315"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/meltdown"
  - "jar:v160.7#blocks/meltdown"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, meltdown, short-range sustained laser / high-power area clear]
---

## One line

meltdown is the other late-game answer for close defense: a continuous laser deals 78 every 5 ticks — 936 DPS instantaneous — runs for 230 ticks, then enters a 90-tick cooldown, averaging 672.75. It turns 1020/s of power into a whole corridor of ground and air being burned through, at the price of having to sit almost against the enemy, and of dying the moment the grid does. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: S | **Role**: short-range sustained laser / high-power area clear
- **Shoot pattern**: continuous laser (shootDuration 230) (1 shot per trigger; reload 90 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- ContinuousTurret + ContinuousLaserBulletType: 78 damage per damageInterval of 5 ticks ⇒ 936 DPS instantaneous [src: 00-data/turrets.json]
- Ceases fire after shootDuration 230 ticks, reload 90 ticks: 936 × 230/(230+90) averages 672.75 DPS [src: 00-data/turrets.json]
- 1020/s of power is the highest in the game; a dedicated grid + battery bank is mandatory [src: 00-data/turrets.json]
- 195-world-unit (24.375-tile) arc, hits air and ground, one of the few short-range towers that clears both layers at once [src: 00-data/turrets.json]
- **Pros**:
  - 936 DPS instantaneous is the highest paper sustained output in the game, and it covers air and ground [src: 00-data/turrets.json]
  - The 672.75 average stays just below spectre's 685.7, yet costs only 2500 items [src: 00-data/turrets.json]
  - The beam has no projectile travel time, damage lands on hit, so there is no lead problem against fast targets
- **Cons**:
  - 1020/s of power: the grid collapses and it turns into a brick, the most power-sensitive tower in the game [src: 00-data/turrets.json]
  - It has to close to 24.375 tiles; when the enemy suppresses from range it cannot shoot back [src: 00-data/turrets.json]
  - 936 is instantaneous, 30% of the time is cooldown, so plan firepower with 672.75 [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 4 | 00-data/blocks.json |
| Health | 3200 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 2500 items (copper × 1200, lead × 350, graphite × 300, silicon × 325, surge-alloy × 325) | 00-data/blocks.json |
| Range | 195 world units (24.38 tiles) | 00-data/turrets.json |
| reload | 90 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 1 / 40 | 00-data/turrets.json |
| Power | 1020/s | 00-data/turrets.json |

| Item | Value | Note | Source |
|---|---|---|---|
| Damage per tick | 78 | ContinuousLaserBulletType(78) | Mindustry-Source/core/src/mindustry/content/Blocks.java:4316 |
| damageInterval | 5 ticks | settles once every 5 ticks ⇒ ×12 | Mindustry-Source/core/src/mindustry/content/Blocks.java:4317 |
| 0-armor DPS | 936 | 78 × 12 | this article's convention |
| shootDuration | 230 ticks | duration of one firing | Mindustry-Source/core/src/mindustry/content/Blocks.java:4325 |
| Power | 1020/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:4321 |

- Continuous type: as long as the target stays in the arc it keeps settling, with no hit check, so the number is extremely stable. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4315]
- Applies the melting status with incendChance 0.4; coolant use of 0.5/s is on the high side for its class. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4315]

- This library gives both numbers: instantaneous 936 (936 = 78 × 12, 12 = 60/5) and average 672.75 (including the 90-tick cooldown); when comparing, always state which one you mean [src: 00-data/turrets.json]
- The derivation of 672.75 can be checked in source: Blocks.java:4323 reload=90f, :4325 shootDuration=230f, :4331 ContinuousLaserBulletType(78) [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4315 — definition line new LaserTurret("meltdown")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this tower does not override it)
- 00-data/turret_shots.json#id=meltdown — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: comparing 936 with spectre's 685.7 and ignoring the 90-tick cooldown overstates it by 39%; reproduce: recompute 936 × 230/320 = 672.75 [src: 00-data/turrets.json]
- Counter-example: assuming meltdown is a ranged tower — 195 world units (24.375 tiles) is shorter than spectre's 260; reproduce: the range field of both in 00-data/turrets.json [src: 00-data/turrets.json]

## Common misconceptions

- "936 is what it deals per second" — true only for the first 230 ticks; the long-run average must use 672.75 [src: 00-data/turrets.json]
- "Laser towers use no power" — wrong: 1020/s is the highest tier in the game, it is the most grid-dependent tower there is [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.105]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
