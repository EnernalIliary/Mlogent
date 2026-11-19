---
tokens: 532
id: COMBAT.TURRET.114
title: ripple — four-shell artillery beyond 290 world units
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3955"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/ripple"
  - "jar:v160.7#blocks/ripple"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, ripple, long-range arcing suppression]
---

## One line

ripple is the only mid-game ground fire that can reliably reach beyond 290 world units (36.25 tiles): 4 shots per trigger, 2 shots/s, 96 per-target and 231 displayed on pyratite, its splash covering a whole staging area. It cannot hit air, and a 0.5 trigger/s cadence means it barely reacts to a fast push -- it is the "chip health in advance" turret, not the "put out the fire" one. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: long-range arcing suppression
- **Firing mode**: ShootPattern (4 shots per trigger; reload 120 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: ground, buildings
- 4 shots per trigger (shots 4), reload 120 ticks ⇒ 0.5 triggers/s, 2 shots/s; ground only [src: 00-data/turrets.json]
- ammoPerShot 2: each reload eats 2 items of ammo, which is why its ammo draw looks doubled [src: 00-data/turrets.json]
- pyratite 48 direct + 90 splash → 96 per-target / 231 displayed; graphite 40 + 70 → 80 / 185 but 2.0 items/s is the hungrier option [src: 00-data/turrets.json]
- the arcing trajectory crosses walls, so it can hit ground staging areas shielded by them
- **Strengths**:
  - 36.25-tile reach plus arcing over walls: no ground turret in the mid game replaces its coverage [src: 00-data/turrets.json]
  - 231 displayed of splash is very efficient against clustered ground waves
  - pyratite still has 52 DPS against 22 armor, far better than hail's 25 per-target
- **Weaknesses**:
  - no anti-air, absent from airdrop waves altogether [src: 00-data/turrets.json]
  - 0.5 triggers/s is too slow, it barely hits fast pushers [src: 00-data/turrets.json]
  - blast-compound and plastanium both stop at 215 displayed, showing the ceiling is pinned by reload and ammo swaps buy little [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 3 | 00-data/blocks.json |
| Health | 1170 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 345 items (copper × 150, graphite × 135, titanium × 60) | 00-data/blocks.json |
| Range | 290 world units (36.25 tiles) | 00-data/turrets.json |
| reload | 120 ticks | 00-data/turrets.json |
| shots | 4 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 8 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| pyratite | 48 | 90 | 1.00 | 2.00 | 96.0 | 231.0 | 1.00 | 52.0 | 00-data |
| graphite | 40 | 70 | 1.00 | 2.00 | 80.0 | 185.0 | 2.00 | 36.0 | 00-data |
| plastanium | 40 | 90 | 1.00 | 2.00 | 80.0 | 215.0 | 2.00 | 36.0 | 00-data |
| blast-compound | 40 | 90 | 1.00 | 2.00 | 80.0 | 215.0 | 1.00 | 36.0 | 00-data |
| silicon | 40 | 70 | 1.20 | 1.67 | 66.7 | 154.2 | 1.11 | 30.0 | 00-data |

- 231 = 2 shots/s × (48 + 0.75×90), splash is six tenths of it; reporting 96 per-target alone underestimates group clearing, reporting displayed alone overestimates single-target kills [src: 00-data/turrets.json]
- ammoPerShot 2 means the real ammo draw is 2 shots/s × 2 = 4 items/s (in the pyratite metric the 1.0 items/s is already counted per shot) [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3955 — definition line new ItemTurret("ripple")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4065 — contains shots / 4
- 00-data/turret_shots.json#id=ripple — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: ripple against a single boss, 96 per-target DPS is 1/5 of fuse's, at 345 versus 550 items. Reproduce: the "Per-target DPS" column for ripple and fuse in 00-data/turrets.json [src: 00-data/turrets.json]
- Counterexample: assuming blast-compound raises DPS; displayed stays 215 and items/s 1.0, the gain is only in the splash structure. Reproduce: every ammo row of ripple in the same table [src: 00-data/turrets.json]

## Common misconceptions

- "arcing turrets have long reach so they replace front-line turrets" wrong: a 0.5 trigger/s cadence does not stop a push [src: 00-data/turrets.json]
- "4 shots = 4×" wrong: 2 shots/s is already the fire rate with the 4 shots averaged

## Related

- [[COMBAT.TURRET.104]]
- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.113]]
- [[COMBAT.TURRET.115]]
