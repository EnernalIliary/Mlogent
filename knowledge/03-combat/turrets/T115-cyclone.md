---
tokens: 535
id: COMBAT.TURRET.115
title: cyclone — the 415 displayed-DPS anti-air core
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4085"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/cyclone"
  - "jar:v160.7#blocks/cyclone"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, cyclone, anti-air group damage / mid-range barrage]
---

## One line

cyclone is the late-game anti-air mainstay: reload 10 ticks, 6 shots/s, 78 per-target and 415.5 displayed on surge-alloy, the natural enemy of an airdrop wave; a 200-world-unit (25 tiles) reach is enough as well. Its weakness is clear -- only 7.8 DPS against 22 armor, so it clears groups peerlessly and chews heavy armor poorly; against heavy flying units bring fuse or spectre to finish the kill. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: anti-air group damage / mid-range barrage
- **Firing mode**: ShootBarrel (1 shot per trigger; reload 10 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- 1 shot per trigger, reload 10 ticks ⇒ 6 shots/s; hits air and ground, ShootBarrel decides the muzzle positions [src: 00-data/turrets.json]
- surge-alloy 13 direct + 75 splash → 78 per-target / 415.5 displayed; metaglass 6 + 45 but rm 0.80 raises the rate to 7.5 shots/s for 298.1 displayed [src: 00-data/turrets.json]
- the damage structure is "a little direct + a lot of splash", so its efficiency against groups is far above its single-target efficiency
- 405 items plus 1305 health, it can be fielded at scale by the mid game
- **Strengths**:
  - 415.5 displayed DPS is top tier among anti-air turrets, and only 405 items [src: 00-data/turrets.json]
  - 6 shots/s of high fire rate keeps splash over the airspace continuously, one miss is not fatal
  - hits air and ground, so a ground wave never wastes the slot
- **Weaknesses**:
  - 7.8 DPS against 22 armor: the 13 direct is eaten by armor, leaving only the fixed splash discount [src: 00-data/turrets.json]
  - surge-alloy at 1.2 items/s needs an alloy line behind it [src: 00-data/turrets.json]
  - a 25-tile reach is still short against very long-range bombers, foreshadow-class pre-emption is needed [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 3 | 00-data/blocks.json |
| Health | 1305 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 405 items (copper × 200, titanium × 125, plastanium × 80) | 00-data/blocks.json |
| Range | 200 world units (25.00 tiles) | 00-data/turrets.json |
| reload | 10 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 30 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| surge-alloy | 13 | 75 | 1.00 | 6.00 | 78.0 | 415.5 | 1.20 | 7.8 | 00-data |
| plastanium | 8 | 37.5 | 1.00 | 6.00 | 48.0 | 216.8 | 1.50 | 4.8 | 00-data |
| blast-compound | 8 | 45 | 1.00 | 6.00 | 48.0 | 250.5 | 1.20 | 4.8 | 00-data |
| metaglass | 6 | 45 | 0.80 | 7.50 | 45.0 | 298.1 | 3.75 | 4.5 | 00-data |

- 415.5 = 6 × (13 + 0.75×75), splash contributes more than nine tenths; taking 415.5 as per-target DPS overestimates it fivefold [src: 00-data/turrets.json]
- the chasm between 7.8 against 22 armor and 415.5 displayed is the pair of numbers to put on the table when judging cyclone [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4085 — definition line new ItemTurret("cyclone")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4166 — contains ShootBarrel
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4167 — contains barrels
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1
- 00-data/turret_shots.json#id=cyclone — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: cyclone against a 22-armor heavy flying unit, 7.8 DPS is as good as not firing. Reproduce: cyclone's "vs 22 armor" column against spectre's 497.1 in 00-data/turrets.json [src: 00-data/turrets.json]
- Counterexample: picking metaglass to be "cheaper"; displayed falls to 298.1 at 3.75 items/s, the hungrier choice. Reproduce: the items/s column of every cyclone ammo row in the same table [src: 00-data/turrets.json]

## Common misconceptions

- "415 displayed so it beats spectre" wrong: per-target is only 78, spectre is 685.7 [src: 00-data/turrets.json]
- "anti-air turrets only hit air" wrong: cyclone hits air and ground, it outputs in a ground wave too

## Related

- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.114]]
