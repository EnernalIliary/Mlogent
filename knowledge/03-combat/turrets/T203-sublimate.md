---
tokens: 670
id: COMBAT.TURRET.203
title: sublimate — a liquid torch dealing 130 per settlement
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4553"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/sublimate"
  - "jar:v160.7#blocks/sublimate"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, sublimate, sustained flame / ammo swaps range]
---

## One line

sublimate solves "keep burning + one flame line through several targets", not "burst point kill": ozone gives 720 DPS at 60 per settlement, and cyanogen doubles that straight to 1560 at 130, with rangeChange +70 and pierceCap 3 thrown in. The price is an 18/s two-layer liquid supply, and a short 130-world-unit (16.25-tile) arc whenever you do not switch to cyanogen. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4570]

## Rules / formulas

- **Tier**: A | **Role**: sustained flame / ammo swaps range
- **Shoot pattern**: continuous flame (1 shot per trigger; reload 10 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- Continuous-flame type, damageInterval 5 ticks ⇒ ×12 settlements; ozone 60 per settlement → 720 DPS, cyanogen 130 → 1560 DPS [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4570]
- cyanogen carries rangeChange +70, pulling range from 130 to 200 world units (25 tiles), one of the few towers where ammo changes the firing arc [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- pierceCap 2 (ozone) / 3 (cyanogen): one flame line burns through several units at once, so real output in dense formations is above the single-target convention [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- Liquid use of 18/s is hungrier on pipes than item towers: cut the liquid and it stops firing, there is no "empty magazine" state [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4553]
- Against 22 armor: ozone leaves 38 of 60 per settlement (63%), cyanogen leaves 108 of 130 (83%) — the heavier the hit, the lighter the armor penalty [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- **Pros**:
  - 1560 DPS + pierce 3 makes it one of Erekir's highest sustained-output towers; it clears heavy-armor groups by burning, not by barrage density [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
  - Switching to cyanogen brings +70 range for free, which is half a new tower bought with ammo [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
  - The continuous type ignores projectile flight and hit checks, so while the target is in the arc it keeps settling and the number is extremely stable [src: 00-data/turrets.json]
- **Cons**:
  - 18/s of liquid + power/coolant means a two-layer supply, and one broken line stops the whole tower [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4570]
  - The ozone curve is only 720 DPS; if you cannot afford cyanogen it is a mid-table tower [src: 00-data/turrets.json]
  - Without cyanogen, 130 world units (16.25 tiles) is too short to reach ranged waves [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4553]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 3 | 00-data/blocks.json |
| Health | 1890 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 790 items (silicon × 200, beryllium × 400, tungsten × 150, oxide × 40) | 00-data/blocks.json |
| Range | 130 world units (16.25 tiles) | 00-data/turrets.json |
| reload | 10 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 1 / 8 | 00-data/turrets.json |
| Power | 0/s | 00-data/turrets.json |

| Ammo | Damage per settlement | 0-armor DPS | Special | Source |
|---|---|---|---|---|
| ozone | 60 | 720 | ammoMultiplier 1.2, pierceCap 2 | Mindustry-Source/core/src/mindustry/content/Blocks.java:4570 |
| cyanogen | 130 | 1560 | rangeChange +70, pierceCap 3 | Mindustry-Source/core/src/mindustry/content/Blocks.java:4576 |

- Continuous-flame type (damageInterval 5 ticks, ×12 settlements); liquid use of 18/s makes it a two-layer supply (ammo liquid + power/coolant). [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4553]
- cyanogen's rangeChange +70 really does extend the arc; it is one of the few towers where ammo buys range. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4553]

- This library gives no vs-22-armor column (the continuous type has no ammo[] reflection table); 63% / 83% are computed from damage per settlement through max(d−22, 0.1d), see [[COMBAT.NUMBERS.001]] [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4553 — definition line new ContinuousLiquidTurret("sublimate")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this tower does not override it)
- 00-data/turret_shots.json#id=sublimate — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: placing sublimate to wait for enemies inside a 130-world-unit arc, when the enemy stops at 200 tiles away it deals 0 output; only cyanogen reaches 200 world units [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- Counter-example: plumbing half a line for 18/s of liquid, 1560 DPS shrinks linearly with the supply ratio, it is not "a little less" [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4570]

## Common misconceptions

- "Flame towers are useless against armor" — wrong: it settles as ordinary direct damage, and cyanogen still keeps 83% against 22 armor [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- "720 DPS is its ceiling" — wrong: ozone is just the small end, cyanogen is the main curve, and they differ by 2.17× [src: 00-data/turrets.json]
- "Switching ammo only switches damage" — wrong: cyanogen also brings +70 range and pierceCap 3, a three-axis upgrade [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]

## Related

- [[COMBAT.TURRET.118]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.202]]
- [[COMBAT.TURRET.204]]
