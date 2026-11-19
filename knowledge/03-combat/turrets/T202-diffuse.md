---
tokens: 587
id: COMBAT.TURRET.202
title: diffuse — a 15-shot spread weapon with the highest ammo burn in the library
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4463"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/diffuse"
  - "jar:v160.7#blocks/diffuse"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, diffuse, short-range crowd clear / 15-shot spread]
---

## One line

diffuse solves "a crowd of small units in your face", not "a hard target": 600 items, air and ground alike, and shots 15 with ShootSpread pours oxide's 67.5 per shot into 2025 single-target DPS at 30 shots/s. The price is written in two numbers — a firing arc of only 125 world units (15.62 tiles), and an ammo burn of 45 items/s; on graphite or silicon it keeps only 28% / 16% against 22 armor. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: B | **Role**: short-range crowd clear / 15-shot spread
- **Shoot pattern**: ShootSpread(15, 4f) (15 shots per trigger; reload 30 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- shots 15 + ShootSpread(15, 4f), reload 30 ticks ⇒ 30 shots/s; oxide 67.5 per shot → 2025 single-target DPS [src: 00-data/turrets.json]
- ammoPerShot 3 and 45 items/s are the highest tier in the game — it writes "crowd clear" directly as "ammo burn" [src: 00-data/turrets.json]
- graphite 30.75 and silicon 26.25 per shot are too light: against 22 armor they leave 262.5 / 127.5 DPS (28% / 16%) [src: 00-data/turrets.json]
- 4f is ShootSpread's spread angle, not a shot multiplier; the actual shot count comes from shots 15 [src: Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9]
- Covers air and ground, but 125 world units (15.62 tiles) is 65 shorter than breach, so its role is a point-blank weapon [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4463]
- **Pros**:
  - 600 items + air and ground + 30 shots/s makes it Erekir's cheapest high-shot-count tower, and it pays for itself fast on one wave of small units [src: 00-data/turrets.json]
  - 15-shot spread with shootCone 40 still covers a dispersed air group, so precise aiming is not required [src: 00-data/turrets.json]
- **Cons**:
  - A 125-world-unit (15.62-tile) arc is too short: ranged heavy-armor waves can stand and shoot it [src: 00-data/turrets.json]
  - oxide's 45 items/s throughput needs two full belts, and when the feed stops graphite leaves only 28% against 22 armor [src: 00-data/turrets.json]
  - Light per shot: above 22 armor only oxide holds it up, so changing ammo is changing to a weaker tower [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 3 | 00-data/blocks.json |
| Health | 1890 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 600 items (graphite × 200, silicon × 200, beryllium × 150, tungsten × 50) | 00-data/blocks.json |
| Range | 125 world units (15.62 tiles) | 00-data/turrets.json |
| reload | 30 ticks | 00-data/turrets.json |
| shots | 15 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 15 / 40 | 00-data/turrets.json |
| Power | 0/s | 00-data/turrets.json |

| Ammo | Direct damage | Splash | reloadMult | shots/s | Single-target DPS (0 armor) | Panel DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| oxide | 67.5 | 0 | 1.00 | 30.00 | 2025.0 | 2025.0 | 45.00 | 1365.0 | 00-data |
| graphite | 30.75 | 0 | 1.00 | 30.00 | 922.5 | 922.5 | 90.00 | 262.5 | 00-data |
| silicon | 26.25 | 0 | 1.00 | 30.00 | 787.5 | 787.5 | 90.00 | 127.5 | 00-data |

- Panel DPS equals single-target (all three ammo types have splash 0), but 30 shots/s carries an inaccuracy of 0.2, so real hits land below the paper figure [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4463 — definition line new ItemTurret("diffuse")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4515 — holds ShootSpread / 15
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9
- 00-data/turret_shots.json#id=diffuse — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: running diffuse as the main tower against a 22-armor wave — silicon's 26.25 per shot is eaten by armor and leaves only 127.5 DPS, worse than one 425-item breach on carbide (2272.5); reproduce: 127.5 and 2272.5 in the vs-22-armor column [src: 00-data/turrets.json]
- Counter-example: feeding diffuse from a single 20 items/s belt — oxide's 45 items/s demand is only 44% met, and after the fire-rate discount 2025 DPS drops to about 900 [src: 00-data/turrets.json]

## Common misconceptions

- "shots 15 means one salvo of 15" — wrong: ShootSpread is a spread, the 15 shots are fired within 30 ticks, and 30 shots/s is the fire-rate convention [src: 00-data/turrets.json]
- "It is a splash tower" — wrong: all three ammo types have splash 0, panel = single-target, it works by quantity, not by area [src: 00-data/turrets.json]
- "silicon is cheap, good for farming" — wrong: silicon's DPS/item of 8.8 is the lowest of the three, and every item saved turns into a longer kill time [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.203]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.201]]
