---
tokens: 580
id: COMBAT.TURRET.106
title: lancer — the 140-direct-damage heavy-armor can opener
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3561"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/lancer"
  - "jar:v160.7#blocks/lancer"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, lancer, anti-heavy-armor / single-shot penetration]
---

## One line

lancer is the "one shot, one target" turret: 140 direct damage, 0.75 shots/s, 105 DPS at 0 armor; but its real selling point is armorMultiplier 4 -- against 22 armor the target's armor counts as 88, the shot keeps 52 and DPS falls to 39, still one of the steadiest anti-heavy turrets in the game. The price is 360/s of continuous power and a very slow cadence: a miss wastes 80 ticks. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: anti-heavy-armor / single-shot penetration
- **Firing mode**: ShootPattern + firstShotDelay (1 shot per trigger; reload 80 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: ground, buildings
- 1 shot per trigger, reload 80 ticks (0.75 shots/s); it runs on power, and 360/s is an order of magnitude above turrets of its tier [src: 00-data/turrets.json]
- armorMultiplier 4: the target's armor enters the subtraction ×4, so its damage falls off more slowly against high-armor targets than other turrets do -- but it gains nothing against 0 armor [src: 00-data/turrets.json]
- pierceCap 4 means one laser can thread 4 targets, so enemies lined up take the full load [src: 00-data/turrets.json]
- buildingDamageMultiplier 0.25: only a quarter damage against buildings, so it is not a demolition turret [src: 00-data/turrets.json]
- **Strengths**:
  - 39 DPS against 22 armor, the most reliable single turret against heavy armor at that stage [src: 00-data/turrets.json]
  - pierces 4 targets, so real output on a full line far exceeds 105 [src: 00-data/turrets.json]
  - a 165-world-unit (20.62 tiles) reach is longer than duo's, so it can sit on the second line [src: 00-data/turrets.json]
- **Weaknesses**:
  - 360/s means a dedicated grid, which is unaffordable early [src: 00-data/turrets.json]
  - a 0.75 shots/s cadence is a disaster against fast movers, and one missed shot costs 80 ticks [src: 00-data/turrets.json]
  - only 0.25× against buildings, so bring separate demolition tools for a hard push [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 2 | 00-data/blocks.json |
| Health | 1120 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 220 items (copper × 60, lead × 70, titanium × 30, silicon × 60) | 00-data/blocks.json |
| Range | 165 world units (20.62 tiles) | 00-data/turrets.json |
| reload | 80 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 8 | 00-data/turrets.json |
| Power draw | 360/s | 00-data/turrets.json |

| Item | Value | Notes | Source |
|---|---|---|---|
| Direct damage | 140 | LaserBulletType | Mindustry-Source/core/src/mindustry/content/Blocks.java:3566 |
| armorMultiplier | 4 | the target's armor enters the subtraction ×4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3567 |
| Shots/s | 0.75 | reload 80 ticks | Mindustry-Source/core/src/mindustry/content/Blocks.java:3568 |
| 0-armor DPS | 105 | 140 × 0.75 | this article's metric |
| Power draw | 360/s | consumePower(6) | Mindustry-Source/core/src/mindustry/content/Blocks.java:3573 |

- Against a 22-armor target: effective armor 22 × 4 = 88, the shot keeps 52 and DPS falls to 39. This is the turret that suffers most from the armor penalty in the game. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3561]
- pierceCap 4; buildingDamageMultiplier 0.25 (a quarter damage against buildings). [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3561]

- 105 DPS holds only at 0 armor; against 22 armor compute (140 − 22×4) × 0.75 = 39, a 2.7× gap between the two numbers [src: 00-data/turrets.json]
- pierceCap 4's gain does not enter per-target DPS; when firing down a line, multiply by the number of targets yourself

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3561 — definition line new PowerTurret("lancer")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3565 — contains firstShotDelay / 40
- 00-data/turret_shots.json#id=lancer — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: lancer against a 0-armor crawler pack; 105 DPS is only worth two graphite duo (67.5×2) yet needs 360/s of power. Reproduce: compare lancer's per-target DPS with duo in 00-data/turrets.json [src: 00-data/turrets.json]
- Counterexample: assuming lancer can raze bases -- buildingDamageMultiplier 0.25 cuts 140 direct damage to 35 against buildings. Reproduce: the notes of the MANUAL lancer table in gen_turrets.py [src: 00-data/turrets.json]

## Common misconceptions

- "armorMultiplier 4 = damage ×4" wrong: it multiplies the target's armor by 4 before subtracting, so it adds nothing against a 0-armor target
- "lancer is an all-rounder" wrong: slow fire rate plus low building damage, it only excels at a single high-armor target

## Related

- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.107]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.105]]
