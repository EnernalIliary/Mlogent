---
tokens: 580
id: COMBAT.TURRET.206
title: afflict — a 368-world-unit, 216-DPS armor-piercing electric gun
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5024"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/afflict"
  - "jar:v160.7#blocks/afflict"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, afflict, medium-caliber electric tower / piercing shot]
---

## One line

afflict solves "pick off two or three targets at range in the mid-game", not "be the endgame mainstay": a 50-tick reload with 180 direct damage = 216 DPS, pierceCap 2 lets it deal double in a dense formation, and 368 world units (46.00 tiles) of coverage comes with 300 power/s. It takes no armor penalty (no armorMultiplier, 158 left against 22 armor, 88%); the price is a slow projectile and absolute dependence on the grid. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5025]

## Rules / formulas

- **Tier**: B | **Role**: medium-caliber electric tower / piercing shot
- **Shoot pattern**: ShootPattern(default) (1 shot per trigger; reload 50 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- reload 50 ticks ⇒ 1.2 shots/s, 180 direct damage → 216 DPS [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5025]
- pierceCap 2 punches through 2 targets; speed 5, lifetime 80 ⇒ slow projectile, so moving targets need leading [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- No armorMultiplier: against 22 armor a shot leaves 158 (88%), which makes it the medium caliber that avoids the armor penalty in Erekir [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5036]
- 300/s of power, 4×4, 590 items, 3520 health [src: 00-data/turrets.json]
- 368 world units (46.00 tiles) is shorter than titan but longer than most Erekir towers [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5024]
- **Pros**:
  - 590 items + 368 of coverage makes it Erekir's cheapest mid-game ranged sniper [src: 00-data/turrets.json]
  - pierceCap 2 doubles its effective output in a dense formation, and it takes no armor penalty [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- **Cons**:
  - 216 DPS is not high at the 590-item tier: smite's 562.5 costs only 3.7× more [src: 00-data/turrets.json]
  - 300 power/s needs a dedicated grid, and a blackout turns it into decoration [src: 00-data/turrets.json]
  - Projectile speed 5 discounts the hit rate against fast fliers and strafing units [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 4 | 00-data/blocks.json |
| Health | 3520 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 590 items (graphite × 250, silicon × 200, surge-alloy × 100, oxide × 40) | 00-data/blocks.json |
| Range | 368 world units (46.00 tiles) | 00-data/turrets.json |
| reload | 50 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 20 | 00-data/turrets.json |
| Power | 300/s | 00-data/turrets.json |

| Item | Value | Note | Source |
|---|---|---|---|
| Direct damage | 180 | BasicBulletType | Mindustry-Source/core/src/mindustry/content/Blocks.java:5025 |
| shots/s | 1.2 | reload 50 ticks | Mindustry-Source/core/src/mindustry/content/Blocks.java:5030 |
| 0-armor DPS | 216 | 180 × 1.2 | this article's convention |
| Power | 300/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:5036 |

- pierceCap 2 (punches through 2 targets), speed 5, lifetime 80 ⇒ a rather slow projectile that needs leading. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5024]
- Erekir's medium-caliber electric tower, positioned like lancer but without the armor penalty (no armorMultiplier). [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5024]

- This library has no afflict ammo[] (shootType is not in bullets.json); 180 and 1.2 shots/s come from the hand-written source table, and 158 is the vs-22-armor per-shot figure computed as max(180−22, 18) [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5025]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5024 — definition line new PowerTurret("afflict")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this tower does not override it)
- 00-data/turret_shots.json#id=afflict — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: using afflict as anti-air — projectile speed 5 cannot catch fast fliers; the 590-item lustre at the same price hits instantly [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- Counter-example: during a blackout 216 DPS goes to zero, and one grid single-point failure kills a 590-item tower [src: 00-data/turrets.json]

## Common misconceptions

- "pierceCap 2 = double DPS" — wrong: it holds only when two targets stand overlapped [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- "Electric towers use no ammo, so they are cheap" — wrong: 300 power/s occupies generation and storage; the cost simply moves from items to power [src: 00-data/turrets.json]
- "180 per shot halves against 22 armor" — wrong: 158 is left, 88% retained [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5036]

## Related

- [[COMBAT.TURRET.106]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.TURRET.205]]
- [[COMBAT.TURRET.207]]
