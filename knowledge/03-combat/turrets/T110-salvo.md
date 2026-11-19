---
tokens: 554
id: COMBAT.TURRET.110
title: salvo — the 320-DPS mainstay in 4-shot bursts
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3731"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/salvo"
  - "jar:v160.7#blocks/salvo"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, salvo, mid-game mainstay / burst single-target]
---

## One line

salvo is the standard answer for a mid-game line: 4-shot bursts, reload 29 ticks, graphite at 320.7 per-target DPS and still 93.1 against 22 armor -- no second turret at that price gives both this number and this penetration. The price is 2.59 items/s of graphite and a 1×1 slot that cannot fit many. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: mid-game mainstay / burst single-target
- **Firing mode**: ShootPattern + shotDelay (4 shots per trigger; reload 29 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- 4 shots per trigger (shots 4, shotDelay spaces them into a burst), reload 29 ticks, hits air and ground [src: 00-data/turrets.json]
- graphite is the main ammo: 31 direct, 10.34 shots/s → 320.7 DPS, and still 93.1 against 22 armor, the best "cheap penetration" in the family [src: 00-data/turrets.json]
- thorium 28 direct but reloadMultiplier 1.00 → 231.7; silicon rm 1.50 pushes the rate down to 5.52 shots/s, leaving 126.9 [src: 00-data/turrets.json]
- a 190-world-unit (23.75 tiles) reach is a step above duo's, so it can sit on the second line and cover the front [src: 00-data/turrets.json]
- **Strengths**:
  - 320.7 per-target DPS plus 93.1 vs 22 armor is the optimum at the 230-item price [src: 00-data/turrets.json]
  - 124 DPS/item (graphite), better supply efficiency than spectre's 160 and higher than swarmer's 72
  - the 4-shot rhythm makes a miss affordable, unlike lancer's all-or-nothing
- **Weaknesses**:
  - 2.59 items/s of graphite, a single full-speed conveyor feeds only about 4 turrets [src: 00-data/turrets.json]
  - a 1×1 footprint (size 1) cannot fit many, and site planning tops out fast
  - 93.1 vs 22 armor is good but still below the spectre/fuse league, so the late game replaces it [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 2 | 00-data/blocks.json |
| Health | 960 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 230 items (copper × 100, graphite × 80, titanium × 50) | 00-data/blocks.json |
| Range | 190 world units (23.75 tiles) | 00-data/turrets.json |
| reload | 29 ticks | 00-data/turrets.json |
| shots | 4 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 8 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| graphite | 31 | 0 | 0.80 | 10.34 | 320.7 | 320.7 | 2.59 | 93.1 | 00-data |
| thorium | 28 | 0 | 1.00 | 8.28 | 231.7 | 231.7 | 2.07 | 49.7 | 00-data |
| pyratite | 25 | 15 | 1.00 | 8.28 | 206.9 | 300.0 | 1.66 | 24.8 | 00-data |
| silicon | 23 | 0 | 1.50 | 5.52 | 126.9 | 126.9 | 1.10 | 12.7 | 00-data |
| copper | 15 | 0 | 1.00 | 8.28 | 124.1 | 124.1 | 1.66 | 12.4 | 00-data |

- 93.1 = 10.34 shots/s × (31 − 22); the armor subtraction is per shot, so a high fire rate gains more against low armor [src: 00-data/turrets.json]
- displayed DPS equals per-target: salvo's ammo has no splash, the 0.75 fold does not apply [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3731 — definition line new ItemTurret("salvo")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3824 — contains shots / 4
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3825 — contains shotDelay / 3
- 00-data/turret_shots.json#id=salvo — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: salvo against 0-armor trash, 320.7 DPS is overkill; two graphite duo (67.5×2) at the same price are cheaper and more ammo-frugal. Reproduce: the cost/DPS columns for salvo and duo in 00-data/turrets.json [src: 00-data/turrets.json]
- Counterexample: treating salvo's 4-shot burst as 4× damage and computing 1282.8; the table's 320.7 already sums the 4 shots. Reproduce: shots 4 and the "Per-target DPS" column in the same table [src: 00-data/turrets.json]

## Common misconceptions

- "burst turret = high DPS" true, but the price is 2.59 items/s of supply; cut the ammo and it is nothing [src: 00-data/turrets.json]
- "graphite is only a stopgap" wrong: on salvo graphite gives 320.7, higher than thorium's 231.7 [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.113]]
- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.109]]
- [[COMBAT.TURRET.111]]
