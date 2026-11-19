---
tokens: 610
id: COMBAT.TURRET.201
title: breach — 325 per shot, the densest opening gun in the game
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4351"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/breach"
  - "jar:v160.7#blocks/breach"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, breach, opening mainstay / high-damage rapid fire]
---

## One line

breach solves "how do I survive Erekir's first wave", not "how do I fight in the late game": 425 items, 3×3 footprint, carbide multiplies the 40-tick reload by 0.20 down to 8 ticks, and 7.5 shots/s × 325 direct damage is 2437.5 single-target DPS, still 2272.5 (93%) against 22 armor. There are two prices: a short 190-world-unit (23.75-tile) firing arc, and carbide's 7.5 items/s throughput — a single belt cannot feed it, and when the feed stops it falls back to the tungsten curve at 1.5 shots/s. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: B | **Role**: opening mainstay / high-damage rapid fire
- **Shoot pattern**: ShootPattern(default) (1 shot per trigger; reload 40 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- carbide's 40-tick reload is pressed to 8 ticks by rm 0.20: 7.5 shots/s × 325 direct damage = 2437.5 single-target DPS, 2272.5 against 22 armor [src: 00-data/turrets.json]
- The three ammo types are two curves: carbide runs high frequency (7.5 shots/s, 7.5 items/s), while tungsten and beryllium are both on the slow 1.5 shots/s line [src: 00-data/turrets.json]
- No splash, so panel DPS equals single-target DPS; the 0.75 fold does not apply to it [src: 00-data/turrets.json]
- Covers air and ground (air True / ground True); 425 items, 3×3, build time 540 ticks makes it the earliest firepower Erekir can add [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4351]
- coolantMult 15 is Erekir's high-end coolant, but a 3×3 slot usually lacks ammo and power first, so coolant is not the first bottleneck [src: 00-data/turrets.json]
- **Pros**:
  - 425 items for 2437.5 DPS is a value density nothing else at that price matches: the 950-item titan has only 285.3 single-target [src: 00-data/turrets.json]
  - Keeps 93% against 22 armor, one of the few Erekir towers that can fight heavy armor on any ammo [src: 00-data/turrets.json]
  - Covers air and ground at 3×3, so it fits any gap in a formation and no layout change is needed early [src: 00-data/turrets.json]
- **Cons**:
  - 190 world units (23.75 tiles) is too short; from mid-game on, enemy ranged fire can grind it down from outside its arc [src: 00-data/turrets.json]
  - carbide's 7.5 items/s is one of the highest throughputs in the game; the feed breaks and it falls back to tungsten's 106.9 DPS [src: 00-data/turrets.json]
  - beryllium is the cheapest and the weakest: 95.6 DPS, DPS/item 31.9 is the lowest of the three [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 3 | 00-data/blocks.json |
| Health | 1620 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 425 items (graphite × 125, silicon × 150, beryllium × 150) | 00-data/blocks.json |
| Range | 190 world units (23.75 tiles) | 00-data/turrets.json |
| reload | 40 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 15 / 3 | 00-data/turrets.json |
| Power | 0/s | 00-data/turrets.json |

| Ammo | Direct damage | Splash | reloadMult | shots/s | Single-target DPS (0 armor) | Panel DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| carbide | 325 | 0 | 0.20 | 7.50 | 2437.5 | 2437.5 | 7.50 | 2272.5 | 00-data |
| tungsten | 71.25 | 0 | 1.00 | 1.50 | 106.9 | 106.9 | 1.50 | 73.9 | 00-data |
| beryllium | 63.75 | 0 | 1.00 | 1.50 | 95.6 | 95.6 | 3.00 | 62.6 | 00-data |

- Do not read the 40-tick reload as the fire rate: the carbide curve actually fires every 8 ticks, 40 ticks is the base value in the table [src: 00-data/turrets.json]
- maxAmmo 30 ÷ 7.5 items/s ≈ 4 seconds: the magazine is a buffer, not endurance [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4351 — definition line new ItemTurret("breach")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this tower does not override it)
- 00-data/turret_shots.json#id=breach — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: feeding breach from a single carbide belt sized at exactly 7.5 items/s, it empties maxAmmo 30 within 4 seconds and then goes shot-for-shot; continuous 2437.5 DPS needs a second line or a buffer [src: 00-data/turrets.json]
- Counter-example: taking breach against 22 armor on tungsten — 71.25 per shot leaves only 73.9 DPS against 22 armor, 1/30 of the same tower on carbide; reproduce: the 2272.5 and 73.9 rows of the vs-22-armor column [src: 00-data/turrets.json]

## Common misconceptions

- "breach is an early tower, useless later" — wrong: carbide's 2437.5 DPS is still top-tier for a single tower at the endgame; it loses on range, not on numbers [src: 00-data/turrets.json]
- "325 per shot must be slow" — wrong: rm 0.20 gives it 7.5 shots/s, denser than many "rapid-fire towers" [src: 00-data/turrets.json]
- "beryllium is the best value" — wrong: 3.0 items/s buys 95.6 DPS, DPS/item 31.9 is the lowest of the three [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.209]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.202]]
