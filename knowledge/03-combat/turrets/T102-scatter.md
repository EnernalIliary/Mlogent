---
tokens: 635
id: COMBAT.TURRET.102
title: scatter — the 222 displayed-DPS air sweeper
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3333"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/scatter"
  - "jar:v160.7#blocks/scatter"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, scatter, short-range anti-air / bullet clearing]
---

## One line

scatter is the first turret in the game that genuinely handles an airdrop: air only, two shots per trigger, lead at 222.5 displayed DPS, and the spread trims a whole flock of flying units at once. Its price is written on its target layers -- it does not hit ground, so it is never a "mainstay", only a patch over an anti-air hole; and 3 damage per shot cannot even crack 22 armor. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: B | **Role**: short-range anti-air / bullet clearing
- **Firing mode**: ShootPattern + shotDelay (2 shots per trigger; reload 18 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, buildings
- 2 shots per trigger (shots 2, shoot.shotDelay spaces them out), reload 18 ticks; air only, ground targets are never selected [src: 00-data/turrets.json]
- Almost all the damage is in the splash: scrap is 3 direct + 33 splash per shot, so per-target DPS is only 40 and displayed is 370; lead is 3 + 40.5 for 222.5 displayed, 20 per-target [src: 00-data/turrets.json]
- The ammo is volume of fire, not quality: scrap's reloadMultiplier 0.50 pushes shots/s to 13.33 and costs 2.67 items/s, a fire rate close to pouring water [src: 00-data/turrets.json]
- Effective output against 22 armor is only 4.0 (scrap), which means against heavy flying units it can only stack splash, never rely on the direct hit [src: 00-data/turrets.json]
- **Strengths**:
  - 222.5 displayed DPS for 130 items, the cheapest high number in early anti-air [src: 00-data/turrets.json]
  - the splash radius covers a whole cluster, far more efficient against a ball of flare than single-shot sniping
  - range 220 world units (27.5 tiles) is a bit shorter than hail's at the same stage, but enough to cover the airspace over the core [src: 00-data/turrets.json]
- **Weaknesses**:
  - it never touches ground: a ground wave walks right under it and it does not fire a shot, wasting a turret slot
  - 3 direct damage per shot means any armored unit is immune to its direct hit; only the fixed splash value grinds through
  - 4.0 DPS against 22 armor says it is a trash-clearing turret, not a hard-target turret [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 2 | 00-data/blocks.json |
| Health | 800 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 130 items (copper × 85, lead × 45) | 00-data/blocks.json |
| Range | 220 world units (27.50 tiles) | 00-data/turrets.json |
| reload | 18 ticks | 00-data/turrets.json |
| shots | 2 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 35 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| scrap | 3 | 33 | 0.50 | 13.33 | 40.0 | 370.0 | 2.67 | 4.0 | 00-data |
| metaglass | 3 | 45 | 0.80 | 8.33 | 25.0 | 306.2 | 1.67 | 2.5 | 00-data |
| lead | 3 | 40.5 | 1.00 | 6.67 | 20.0 | 222.5 | 1.67 | 2.0 | 00-data |

- The 0.75 fold in displayed DPS only applies to splash: scrap is 40 per-target vs 370 displayed, a 9× gap, so any evaluation must state which metric it uses [src: 00-data/turrets.json]
- 13.33 shots/s at about 2 items per shot means 2.67 items/s -- a single conveyor reaches its limit at 4 turrets [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3333 — definition line new ItemTurret("scatter")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3402 — contains shotDelay
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3403 — contains shots / 2
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9
- 00-data/turret_shots.json#id=scatter — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: use scatter to stop a heavy ground wave; its 0 ground output means every crawler in the wave must be handled by another turret. Reproduce: scatter's targetGround is false in 00-data/turrets.json [src: 00-data/turrets.json]
- Counterexample: computing "scatter 370 DPS beats salvo 320.7" compares the displayed metric against the per-target metric; with a single target in the wave scatter has 40 and salvo has 320.7. Reproduce: read the "Per-target DPS" and "Displayed DPS" columns of the two tables separately [src: 00-data/turrets.json]

## Common misconceptions

- "high splash DPS so it is a mainstay" wrong: it is air only, its output in a ground wave is 0, and in the wrong place it is completely useless
- "3 direct damage is too low, must be a bug" wrong: scatter's damage lives in the splash, the direct hit is only the trigger
- "spread = poor accuracy" not quite: inaccuracy 17 scatters the impact points, an advantage against groups and a disadvantage against single points

## Related

- [[COMBAT.TURRET.104]]
- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.101]]
- [[COMBAT.TURRET.103]]
