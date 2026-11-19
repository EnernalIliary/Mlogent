---
tokens: 520
id: COMBAT.TURRET.104
title: hail — single-shot artillery at 235 world units
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3463"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/hail"
  - "jar:v160.7#blocks/hail"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, hail, early arcing fire / group suppression]
---

## One line

hail throws firepower 235 world units (29.38 tiles) away from a 57-item gun, the only means at the start of reaching the back line over the front. It fires once every 60 ticks for 25 per-target and 58.8 displayed, which is not a pretty number; the real problem is that the shell flies slowly and lands on a fixed point, so any enemy that steps aside makes it miss entirely. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: B | **Role**: early arcing fire / group suppression
- **Firing mode**: ShootPattern (default) (1 shot per trigger; reload 60 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: ground, buildings
- 1 shot per trigger, reload 60 ticks (1 shot/s); ground only, air targets are not selected [src: 00-data/turrets.json]
- pyratite 25 direct + 45 splash → 58.8 displayed; graphite 20 + 33 → 44.8; silicon's reloadMultiplier 1.20 pushes the fire rate down to 0.83 shots/s for 37.3 displayed [src: 00-data/turrets.json]
- the arcing trajectory (ArtilleryBulletType) crosses walls, so it can hit units massing behind one -- this is its core reason to exist
- the splash radius is the main value: 25 per-target means it was never a sniper turret, it drops rocks into a crowd
- **Strengths**:
  - 235 world units (29.38 tiles) has no rival early on and starts chipping health before the enemy arrives [src: 00-data/turrets.json]
  - arcing over walls reaches ground units shielded by them
  - 57-item cost + 1 shot/s keeps supply pressure tiny (0.25~0.5 items/s) [src: 00-data/turrets.json]
- **Weaknesses**:
  - a 1 shot/s cadence is too slow, a missed shot is a lost shot; accuracy against fast movers is dismal
  - no anti-air, so it sits out airdrop waves entirely
  - 58.8 displayed is no competition for the 130-item scatter (222.5) and only wins on reach [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 1 | 00-data/blocks.json |
| Health | 260 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 57 items (copper × 40, graphite × 17) | 00-data/blocks.json |
| Range | 235 world units (29.38 tiles) | 00-data/turrets.json |
| reload | 60 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 10 / 10 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| pyratite | 25 | 45 | 1.00 | 1.00 | 25.0 | 58.8 | 0.25 | 3.0 | 00-data |
| graphite | 20 | 33 | 1.00 | 1.00 | 20.0 | 44.8 | 0.50 | 2.0 | 00-data |
| silicon | 20 | 33 | 1.20 | 0.83 | 16.7 | 37.3 | 0.28 | 1.7 | 00-data |

- 58.8 displayed = 1 shot/s × (25 + 0.75×45), splash is the bulk; reporting 25 per-target alone badly underestimates it, reporting displayed alone overestimates its duelling ability [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3463 — definition line new ItemTurret("hail")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this turret does not override it)
- 00-data/turret_shots.json#id=hail — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: hail against a single boss, 1 shot/s × 25 direct ≈ 25 DPS, worse than duo copper (27). Reproduce: hail's per-target DPS column in 00-data/turrets.json against duo [src: 00-data/turrets.json]
- Counterexample: treating hail as anti-air; targetAir is false, so a flying unit passes overhead without a shot. Reproduce: the air/ground fields in the same table [src: 00-data/turrets.json]

## Common misconceptions

- "artillery turrets hit hard" wrong: hail is 25 per shot; its value is reach and crossing walls, not the number
- "splash makes up for the single shot" partly right: 58.8 displayed does rest on splash, but only if the enemy clusters [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.114]]
- [[COMBAT.TURRET.101]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.103]]
- [[COMBAT.TURRET.105]]
