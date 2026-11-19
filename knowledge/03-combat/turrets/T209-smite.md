---
tokens: 502
id: COMBAT.TURRET.209
title: smite — five barrels of heavy hits, the late-game main gun with the best 22-armor retention
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5656"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootMulti.java:30"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/smite"
  - "jar:v160.7#blocks/smite"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, smite, late-game main gun / five-barrel heavy hit]
---

## One line

smite solves "main output against late-game heavy-armor waves", not "crowd clear": shots 5 with ShootMulti at a 100-tick reload gives 3 shots/s, 187.5 per shot → 562.5 single-target DPS, and 496.5 against 22 armor (88%) — the highest armor retention among Erekir's general-purpose towers. The price is 2200 items, 6 items/s of ammo burn and a 5×5 footprint, a deal of "one tower slot for one front". [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: S | **Role**: late-game main gun / five-barrel heavy hit
- **Shoot pattern**: ShootMulti(derived from ShootAlternate(5f)) + shots=barrels=5 (5 shots per trigger; reload 100 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- shots 5 + ShootMulti(ShootAlternate(5f)), reload 100 ticks ⇒ 3 shots/s, 187.5 per shot → 562.5 single-target DPS [src: Mindustry-Source/core/src/mindustry/entities/pattern/ShootMulti.java:30]
- The 5 barrels rotate rather than fire on the same tick; the fire-rate convention is 3 shots/s, not 15 shots/s [src: 00-data/turret_shots.json]
- 496.5 against 22 armor (88%), the highest armor retention among Erekir's general-purpose towers [src: 00-data/turrets.json]
- Ammo burn of 6 items/s (surge-alloy); 5×5, 8750 health, 2200 items, build time 2450 ticks [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5656]
- Covers air and ground with 300 world units (37.50 tiles) of reach, one of the few late-game towers that can take both layers at once [src: 00-data/turrets.json]
- **Pros**:
  - 562.5 DPS + 88% armor retention + air and ground makes it Erekir's steadiest late-game mainstay [src: 00-data/turrets.json]
  - 8750 health + 5×5 lets it hold the front line; it is not a glass cannon in the back [src: 00-data/turrets.json]
- **Cons**:
  - 2200 items + 5×5 footprint: the opportunity cost of one tower slot is very high [src: 00-data/turrets.json]
  - 3 shots/s tolerates fast targets poorly; it relies on heavy single hits, not dense barrage [src: 00-data/turrets.json]
  - surge-alloy at 6 items/s needs its own production line and competes with breach for carbide [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 5 | 00-data/blocks.json |
| Health | 8750 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 2200 items (silicon × 800, phase-fabric × 300, surge-alloy × 400, oxide × 200, carbide × 500) | 00-data/blocks.json |
| Range | 300 world units (37.50 tiles) | 00-data/turrets.json |
| reload | 100 ticks | 00-data/turrets.json |
| shots | 5 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 15 / 30 | 00-data/turrets.json |
| Power | 0/s | 00-data/turrets.json |

| Ammo | Direct damage | Splash | reloadMult | shots/s | Single-target DPS (0 armor) | Panel DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| surge-alloy | 187.5 | 0 | 1.00 | 3.00 | 562.5 | 562.5 | 6.00 | 496.5 | 00-data |

- Panel = single-target (no splash); do not read shots 5 as 5× damage, the fire rate already folds it into 3 shots/s [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5656 — definition line new ItemTurret("smite")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5721 — holds ShootAlternate
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5723 — holds shots / barrels / 5
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootMulti.java:30
- 00-data/turret_shots.json#id=smite — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: five smites against a swarm of small units — 562.5 DPS settles shot by shot at 3 shots/s, slower at clearing than one malign's 1200-DPS barrage [src: 00-data/turrets.json]
- Counter-example: three smites already burn 18 items/s of surge-alloy; the production line collapses before output is even a topic [src: 00-data/turrets.json]

## Common misconceptions

- "5 barrels = 5× DPS" — wrong: ShootAlternate rotates them, the total fire rate is 3 shots/s [src: 00-data/turret_shots.json]
- "2200 items is too expensive" — half wrong: it buys 8750 health + air and ground + 88% retention, which is not expensive per unit of combat power [src: 00-data/turrets.json]
- "smite is weak against air" — wrong: air True, and 187.5 per shot is just as solid against fliers [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.210]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.208]]
