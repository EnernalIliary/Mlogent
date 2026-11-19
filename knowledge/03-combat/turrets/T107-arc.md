---
tokens: 539
id: COMBAT.TURRET.107
title: arc — 34 DPS from a chain lightning
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3602"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/arc"
  - "jar:v160.7#blocks/arc"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, arc, chain lightning / interrupt control]
---

## One line

arc's per-target numbers are ugly: 20 direct damage, 1.71 shots/s, 34.3 DPS at 0 armor; what it buys is chain lightning -- one discharge jumps to adjacent targets and applies the shocked status that interrupts them. So it is a turret that is strong when the crowd is thick and useless in a duel, and it never fires at air at all. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: B | **Role**: chain lightning / interrupt control
- **Firing mode**: ShootPattern (default) (1 shot per trigger; reload 35 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: ground, buildings
- 1 shot per trigger, reload 35 ticks (1.71 shots/s), 20 direct damage, chain length 25 world units [src: 00-data/turrets.json]
- collidesAir=false: no anti-air at all, a flying unit overhead gets no shot [src: 00-data/turrets.json]
- chain damage is the compensation for groups: 34.3 per-target DPS is only the floor, the denser the enemy the higher the total output [src: 00-data/turrets.json]
- applies the shocked status (interrupt/weaken), value that is not in the numbers; 198/s of power is its only heavy cost [src: 00-data/turrets.json]
- **Strengths**:
  - 100-item cost plus chain damage makes it a very cost-effective trash clearer in dense ground waves [src: 00-data/turrets.json]
  - the shocked status interrupts enemy actions, extra value against a melee charge
  - 1×1 footprint, easy to slot into any gap in a line
- **Weaknesses**:
  - 34.3 per-target DPS is bottom tier in the game, it cannot move any hard target in a duel [src: 00-data/turrets.json]
  - no anti-air, absent from airdrop waves altogether
  - the 90-world-unit (11.25 tiles) reach is very short, it must hug the front line [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 1 | 00-data/blocks.json |
| Health | 260 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 100 items (copper × 50, lead × 50) | 00-data/blocks.json |
| Range | 90 world units (11.25 tiles) | 00-data/turrets.json |
| reload | 35 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 30 / 40 | 00-data/turrets.json |
| Power draw | 198/s | 00-data/turrets.json |

| Item | Value | Notes | Source |
|---|---|---|---|
| Direct damage | 20 | LightningBulletType | Mindustry-Source/core/src/mindustry/content/Blocks.java:3603 |
| lightningLength | 25 | chain length (world units) | Mindustry-Source/core/src/mindustry/content/Blocks.java:3604 |
| Shots/s | 1.71 | reload 35 ticks | Mindustry-Source/core/src/mindustry/content/Blocks.java:3626 |
| 0-armor DPS | 34.3 | 20 × 1.71 | this article's metric |
| Power draw | 198/s | consumePower(3.3) | Mindustry-Source/core/src/mindustry/content/Blocks.java:3631 |

- collidesAir=false ⇒ no anti-air at all; chain lightning jumps to adjacent targets, so the real total output is above the per-target DPS. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3602]
- applies the shocked status (interrupt/weaken), value above the numbers. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3602]

- 34.3 = 20 × 1.71, one target only; with chain hits on N targets the real output is roughly × N (not modelled in this library, an estimate) [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3602 — definition line new PowerTurret("arc")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this turret does not override it)
- 00-data/turret_shots.json#id=arc — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: arc against a boss, 34.3 DPS is under half a graphite duo (67.5). Reproduce: arc has no ammo[] table in 00-data/turrets.json, the values are in the MANUAL block [src: 00-data/turrets.json]
- Counterexample: the common layout that assumes arc covers air; flying units pass straight through its reach. Reproduce: collidesAir=false in the notes of the MANUAL arc table [src: 00-data/turrets.json]

## Common misconceptions

- "power turrets all hit hard" wrong: arc's 20 direct damage is one of the lowest in the game, it earns from chains and status
- "chain lightning can hit air" wrong: collidesAir is false, air targets are filtered out

## Related

- [[COMBAT.TURRET.106]]
- [[COMBAT.TURRET.108]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
