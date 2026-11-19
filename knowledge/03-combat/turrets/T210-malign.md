---
tokens: 600
id: COMBAT.TURRET.210
title: malign — 2400 power, seventeen rounds per second at random impact points
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5926"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootSummon.java:20"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/malign"
  - "jar:v160.7#blocks/malign"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, malign, endgame barrage / area suppression]
---

## One line

malign solves "endgame clearing and suppression", not "precise point kill": a 3.5-tick reload with 70 direct damage gives 17.14 shots/s and 1200 single-target DPS, and every shot also carries an intervalBullet lightning of 18 and a fragBullet laser of 65, so real total output is above 1200. The price is 2400 power/s (the highest in the game) and ShootSummon's random impact points — it settles by coverage, not by aim. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5941]

## Rules / formulas

- **Tier**: S | **Role**: endgame barrage / area suppression
- **Shoot pattern**: ShootSummon (1 shot per trigger; reload 3.5 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- reload 3.5 ticks ⇒ 17.14 shots/s, 70 direct damage → 1200 single-target DPS [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5941]
- Every shot also carries an intervalBullet lightning of 18 and a fragBullet laser of 65, so real total output is above 1200 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5930]
- ShootSummon lands at random points inside a radius: this is an area barrage, not precise aiming [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5926]
- 2400/s of power is the highest tier in the game; a dedicated grid + storage is mandatory [src: 00-data/turrets.json]
- Against 22 armor: 70 per shot leaves 48 (69%), one tier below smite's 88% — barrage towers work by density, not by single hits [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5941]
- **Pros**:
  - 1200 DPS + two kinds of attached bullets makes it Erekir's most efficient clearing tower [src: 00-data/turrets.json]
  - 410 world units (51.25 tiles) of coverage + random impact points gives a very large suppression area [src: 00-data/turrets.json]
- **Cons**:
  - 2400 power/s makes it the first to go dark when the grid fluctuates, so supply cost belongs in the total [src: 00-data/turrets.json]
  - Random impact points make it less reliable than smite on a single target; boss killing needs a point-kill tower alongside [src: 00-data/turrets.json]
  - 5×5 + 2400 items: only the endgame can afford to place it [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 5 | 00-data/blocks.json |
| Health | 9250 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 2400 items (graphite × 500, silicon × 500, phase-fabric × 200, beryllium × 1000, carbide × 200) | 00-data/blocks.json |
| Range | 410 world units (51.25 tiles) | 00-data/turrets.json |
| reload | 3.5 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 100 | 00-data/turrets.json |
| Power | 2400/s | 00-data/turrets.json |

| Item | Value | Note | Source |
|---|---|---|---|
| Direct damage | 70 | FlakBulletType(8, 70) | Mindustry-Source/core/src/mindustry/content/Blocks.java:5927 |
| shots/s | 17.14 | reload 3.5 ticks | Mindustry-Source/core/src/mindustry/content/Blocks.java:5941 |
| 0-armor DPS | 1200 | 70 × 17.14 | this article's convention |
| Attached bullets | intervalBullet lightning 18 + fragBullet laser 65 | every shot carries two extra bullets | Mindustry-Source/core/src/mindustry/content/Blocks.java:5930 |
| Power | 2400/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:5949 |

- ShootSummon lands at random points inside a radius (Blocks.java:6246), so it is not precise aiming but an area barrage. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5926]
- 2400/s of power is the highest tier in the game; a dedicated grid and storage are mandatory. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5926]

- The 0.75 fold of panel DPS holds only for splash, and malign's 70 is direct damage; the attached bullets (lightning 18 / laser 65) are not counted into 1200 [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5926 — definition line new PowerTurret("malign")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:6246 — holds ShootSummon
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootSummon.java:20
- 00-data/turret_shots.json#id=malign — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: sending malign alone against a 22-armor boss — 70 per shot leaves only 48, and 69% retention plus random impact points makes it less reliable than one smite [src: 00-data/turrets.json]
- Counter-example: building only 1200 power/s of grid: malign drops to half rate whenever other towers draw power [src: 00-data/turrets.json]

## Common misconceptions

- "1200 DPS is precise single-target" — wrong: ShootSummon lands randomly, so expected hits are below the paper figure [src: Mindustry-Source/core/src/mindustry/entities/pattern/ShootSummon.java:20]
- "High power draw means weak" — wrong: what it buys is coverage area, not efficiency [src: 00-data/turrets.json]
- "The attached bullets are just effects" — wrong: lightning 18 + laser 65 come with every shot, real output is above 1200 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5930]

## Related

- [[COMBAT.TURRET.209]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
