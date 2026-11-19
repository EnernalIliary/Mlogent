---
tokens: 661
id: COMBAT.TURRET.101
title: duo — the 35-item sustained-fire baseline
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3258"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/duo"
  - "jar:v160.7#blocks/duo"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, duo, early all-rounder / cheap sustained-fire baseline]
---

## One line

duo answers "no firepower at the start", not "cannot kill in the late game": 35 items, a 1×1 footprint, and copper ammo alone spreads 3 shots/s out to 160 world units (20 tiles), hitting both air and ground. The price is 9~18 per shot and almost no armor penetration -- on graphite it keeps only 6.8 DPS against 22 armor, so past the mid game it is only good for guarding the rear or shooting trash. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: B | **Role**: early all-rounder / cheap sustained-fire baseline
- **Firing mode**: ShootAlternate(3.5f) (1 shot per trigger; reload 20 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- 1 shot per trigger, reload 20 ticks; ShootAlternate(3.5f) only alternates the two barrels, it does not add shots, so the fire rate is 60/20 = 3 shots/s (copper) [src: 00-data/turrets.json]
- The three ammo curves are completely different: graphite 67.5, copper 27, silicon 24 single-target DPS; graphite uses reloadMultiplier 0.80 to lift the table's shots/s to 3.75, 18 per shot [src: 00-data/turrets.json]
- Silicon buys ammo economy and homing: 60 DPS/item against copper's 18; its 24 DPS is lower than copper's, but 0.4 items/s barely taxes supply [src: 00-data/turrets.json]
- Coolant multiplier 10 is the top tier among early turrets, so hooking up water raises the effective fire rate noticeably; but on a 1×1 turret a slot is often scarcer than coolant
- Hits air and ground (air True / ground True), the only cheap turret early on that also covers an airdrop
- **Strengths**:
  - 35 items and 17.5 ticks to build: two or three go up within the first tens of seconds and pay back extremely fast [src: 00-data/turrets.json]
  - 1×1 footprint fits any gap; graphite at 67.5 DPS is the ceiling at that price point (about 1.9 DPS/item) [src: 00-data/turrets.json]
  - Copper, graphite and silicon are available all game, so a changed ore line never starves it
- **Weaknesses**:
  - Armor penetration is the family weakness: graphite keeps only 6.8 DPS against 22 armor, while salvo graphite is 93.1 at the same caliber [src: 00-data/turrets.json]
  - 160 world units (20 tiles) of reach does not last into the mid game; once enemy long-range fire arrives it can only take hits [src: 00-data/turrets.json]
  - Per-shot damage is light, so it stacks damage by count; squeeze the slots and a few duo's output thins out to nothing worth watching [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 1 | 00-data/blocks.json |
| Health | 250 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 35 items (copper × 35) | 00-data/blocks.json |
| Range | 160 world units (20.00 tiles) | 00-data/turrets.json |
| reload | 20 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 10 / 15 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| graphite | 18 | 0 | 0.80 | 3.75 | 67.5 | 67.5 | 0.94 | 6.8 | 00-data |
| copper | 9 | 0 | 1.00 | 3.00 | 27.0 | 27.0 | 1.50 | 2.7 | 00-data |
| silicon | 12 | 0 | 1.50 | 2.00 | 24.0 | 24.0 | 0.40 | 2.4 | 00-data |

- duo's ammo has no splash, so displayed DPS equals per-target DPS and the 0.75 fold does not apply to it (compare scatter's 370 displayed against 40 per-target) [src: 00-data/turrets.json]
- 72 DPS/item means graphite at full fire rate only eats 0.94 items/s; supply was never duo's bottleneck, position is [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3258 — definition line new ItemTurret("duo")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3300 — contains ShootAlternate
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29
- 00-data/turret_shots.json#id=duo — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: 4 graphite duo against a 22-armor heavy wave total 27.2 DPS, worse than one lancer's single-shot penetration -- against 22 armor duo's 67.5 falls to 6.8. Reproduce: the "vs 22 armor" column of duo's graphite row in 00-data/turrets.json, × 4 [src: 00-data/turrets.json]
- Counterexample: place duo as a long-range turret at the outer edge of its 160 world units; an enemy that stops outside its reach and retargets makes its 27 DPS exactly 0. Reproduce: compare the range field in 00-data/turrets.json against real enemy cease-fire distances [src: 00-data/turrets.json]

## Common misconceptions

- "4 barrels = 4 shots" wrong: ShootAlternate only alternates barrels, shots stays 1, and the fire rate is set by reload 20 ticks alone [src: 00-data/turrets.json]
- "cheap therefore weak" wrong: graphite duo's 67.5 DPS is the ceiling at its price; what is weak is armor penetration and reach, not the number [src: 00-data/turrets.json]
- "silicon is the strongest" wrong: silicon is only 24 DPS; it buys ammo economy (0.4 items/s) and homing, not damage [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.110]]
- [[COMBAT.TURRET.102]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
