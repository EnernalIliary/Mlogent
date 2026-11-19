---
tokens: 558
id: COMBAT.TURRET.103
title: scorch — the 60-world-unit point-blank brazier
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3419"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/scorch"
  - "jar:v160.7#blocks/scorch"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, scorch, point-blank fire wall / melee fuse]
---

## One line

scorch is the turret that pours fire on the doorstep: reach is only 60 world units (7.5 tiles), yet with a 6-tick reload it sprays 10 pyratite shots every second, and 300 per-target DPS is vicious at point-blank range. The problem is that it hits ground only and its reach is so short it must stand on the very front line; once the enemy detours or suppresses from range it is a money-burning ornament. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: C | **Role**: point-blank fire wall / melee fuse
- **Firing mode**: ShootPattern (default) (1 shot per trigger; reload 6 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: ground, buildings
- 1 shot per trigger, reload 6 ticks, 10 shots/s; ground only, air targets are not selected [src: 00-data/turrets.json]
- pyratite 30 per shot → 300 DPS, 1.0 items/s; coal 17 per shot → 170 DPS but needs 3.33 items/s, the "cheap but ammo-hungry" reverse choice [src: 00-data/turrets.json]
- the projectile lives only about 18 ticks (flame type), so the effective reach is even shorter than the 60 world units on the card and it must be placed point-blank [src: 00-data/turrets.json]
- against 22 armor pyratite still has 80 DPS, a rare early turret that does not much fear armor -- because its per-shot damage is heavy enough
- **Strengths**:
  - 300 per-target DPS for a 47-item build cost, one of the most extreme early value plays [src: 00-data/turrets.json]
  - 80 DPS against 22 armor, an order of magnitude above duo graphite (6.8) at the same stage [src: 00-data/turrets.json]
  - 1×1 footprint + short reach make it a natural fit behind walls, in doorways and at conveyor junctions
- **Weaknesses**:
  - a 60-world-unit (7.5 tiles) reach means an enemy standing outside it can dismantle it for free [src: 00-data/turrets.json]
  - ground only, no answer to an airdrop at all
  - burning pyratite costs 1.0 items/s, which looks frugal, but pyratite is a tier-2 product and early production often cannot keep up [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 1 | 00-data/blocks.json |
| Health | 400 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 47 items (copper × 25, graphite × 22) | 00-data/blocks.json |
| Range | 60 world units (7.50 tiles) | 00-data/turrets.json |
| reload | 6 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 1.5 / 50 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| pyratite | 30 | 0 | 1.00 | 10.00 | 300.0 | 300.0 | 1.00 | 80.0 | 00-data |
| coal | 17 | 0 | 1.00 | 10.00 | 170.0 | 170.0 | 3.33 | 17.0 | 00-data |

- "10 shots/s × 30" = 300, scorch's full fire-rate ceiling under this library's metric; in real combat the flame shot's flight time eats part of the output before contact [src: 00-data/turrets.json]
- displayed DPS = per-target DPS: the flame shot has no splash field, so the 0.75 fold does not apply [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3419 — definition line new ItemTurret("scorch")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this turret does not override it)
- 00-data/turret_shots.json#id=scorch — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: putting scorch on the second line as ordinary firepower; a 7.5-tile reach leaves it with no output all game. Reproduce: scorch's range is 60 world units in 00-data/turrets.json, against duo's 160 [src: 00-data/turrets.json]
- Counterexample: picking coal to "save more": 170 DPS yet eating 3.33 items/s actually costs twice the coal per point of DPS. Reproduce: compare the "Items/s" and "DPS/item" columns for pyratite and coal in the table [src: 00-data/turrets.json]

## Common misconceptions

- "flame turrets have long range" wrong: scorch is only 60 world units, one of the shortest in the family
- "scorch cannot hurt heavy armor" wrong: at 30 per shot it still has 80 DPS against 22 armor; the real weakness is reach and target layers

## Related

- [[COMBAT.TURRET.101]]
- [[COMBAT.TURRET.113]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.102]]
- [[COMBAT.TURRET.104]]
