---
tokens: 563
id: COMBAT.TURRET.109
title: swarmer — a missile rain in 4-shot volleys
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3656"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/swarmer"
  - "jar:v160.7#blocks/swarmer"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, swarmer, missile group damage / mid-range anti-air]
---

## One line

swarmer is the most comfortable "one trigger, many missiles" turret of the mid game: 4 missiles per trigger rotating through 8 launch barrels, 126 per-target and 309.8 displayed on surge-alloy. The problem is that ammo quality decides everything -- on pyratite per-target falls to 84, and against 22 armor even surge has only 12.6: strong at clearing groups, weak at chewing hard targets. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: missile group damage / mid-range anti-air
- **Firing mode**: ShootBarrel(barrels=8) (4 shots per trigger; reload 34.29 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- 4 shots per trigger (shots 4, ShootBarrel rotates 8 barrels), reload 34.29 ticks, hits air and ground [src: 00-data/turrets.json]
- surge-alloy 18 direct + 35 splash → 126 per-target / 309.8 displayed; pyratite 12 + 45 → 84 / 320.3; blast-compound 10 + 45 → 70 / 306.3 [src: 00-data/turrets.json]
- missiles are homing projectiles, so accuracy against moving targets beats arcing fire, but flight time still costs distant targets a few hits [src: 00-data/turrets.json]
- against 22 armor surge keeps only 12.6, which says it is a group clearer: once armor is high the missile's 18 direct damage is eaten [src: 00-data/turrets.json]
- **Strengths**:
  - 309.8 displayed DPS for 145 items, excellent mid-game value [src: 00-data/turrets.json]
  - 4-shot volleys plus splash strip health in sheets off clustered air or ground units
  - the 30-tile reach covers a mid-game airdrop wave well enough [src: 00-data/turrets.json]
- **Weaknesses**:
  - 12.6 DPS against 22 armor, close to no answer for a heavy push [src: 00-data/turrets.json]
  - 1.75 items/s (surge) forces a lower fire rate when mid-game production lags [src: 00-data/turrets.json]
  - missile flight time plus inaccuracy 10 push real accuracy against fast targets below the table value [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 2 | 00-data/blocks.json |
| Health | 1200 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 145 items (graphite × 35, titanium × 35, silicon × 30, plastanium × 45) | 00-data/blocks.json |
| Range | 240 world units (30.00 tiles) | 00-data/turrets.json |
| reload | 34.29 ticks | 00-data/turrets.json |
| shots | 4 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 8 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| surge-alloy | 18 | 35 | 1.00 | 7.00 | 126.0 | 309.8 | 1.75 | 12.6 | 00-data |
| pyratite | 12 | 45 | 1.00 | 7.00 | 84.0 | 320.3 | 1.40 | 8.4 | 00-data |
| blast-compound | 10 | 45 | 1.00 | 7.00 | 70.0 | 306.3 | 1.40 | 7.0 | 00-data |

- the gap between 309.8 displayed and 126 per-target comes from the 0.75 splash fold: judge group clearing by displayed, single-target kills by per-target [src: 00-data/turrets.json]
- 72 DPS/item (surge) means it is more ammo-frugal than spectre, but per-shot quality is far worse

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3656 — definition line new ItemTurret("swarmer")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3706 — contains ShootBarrel
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3712 — contains shots / 4
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3713 — contains shotDelay
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1
- 00-data/turret_shots.json#id=swarmer — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: swarmer against a 22-armor boss, 12.6 DPS is worse than one lancer's 39 and still needs 1.75 items/s of surge. Reproduce: the "vs 22 armor" column for swarmer and lancer in 00-data/turrets.json [src: 00-data/turrets.json]
- Counterexample: assuming a volley = 4× damage; all 4 shots each take the armor subtraction, so against high armor 4 light shots lose to 1 heavy one. Reproduce: swarmer vs fuse on vs-22-armor, 12.6 vs 426.9 [src: 00-data/turrets.json]

## Common misconceptions

- "missile turrets are anti-air only" not quite: in this library's data swarmer selects air and ground, it is a general group-damage turret
- "4 shots = 4×" wrong: 4 shots mean 4 independent armor subtractions, and the return falls off steeply against high armor

## Related

- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.108]]
- [[COMBAT.TURRET.110]]
