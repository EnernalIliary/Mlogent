---
tokens: 528
id: COMBAT.TURRET.113
title: fuse — 540 DPS of point-blank buckshot
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3915"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/fuse"
  - "jar:v160.7#blocks/fuse"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, fuse, close-range endgame / anti-heavy burst]
---

## One line

fuse is the strongest late-game close defence: 3 thorium buckshot per trigger, 5.14 shots/s, 540 per-target DPS, and still 426.9 against 22 armor -- a number only slightly below spectre's 497.1, at the price of a 90-world-unit (11.25 tiles) reach. It is the turret that "lets the enemy in and then kills it"; place it wrong and it equals nothing. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: S | **Role**: close-range endgame / anti-heavy burst
- **Firing mode**: ShootSpread(3, 20f) (3 shots per trigger; reload 35 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- 3 shots per trigger (shots 3, ShootSpread in a 20-degree fan), reload 35 ticks ⇒ 5.14 shots/s; hits air and ground [src: 00-data/turrets.json]
- thorium 105 direct per shot → 540 per-target / 540 displayed (no splash), 426.9 against 22 armor, 1.03 items/s [src: 00-data/turrets.json]
- the fan stacks the three shots on one target at close range and spreads them apart at long range, so its effective DPS decays with distance faster than the table value does
- 1980 health plus a 3×3 footprint, a close-defence physique that survives one wave at point-blank
- **Strengths**:
  - 540 per-target DPS / 426.9 vs 22 armor, the strongest single-target burst at the 550-item price [src: 00-data/turrets.json]
  - 1.03 items/s of thorium is almost unnoticeable on a late-game line [src: 00-data/turrets.json]
  - the 3-shot fan has better real accuracy against point-blank heavy units than single-shot sniping
- **Weaknesses**:
  - a 90-world-unit (11.25 tiles) reach is among the shortest in the family, so it never answers ranged suppression [src: 00-data/turrets.json]
  - fed by thorium, it is unusable without a thorium line early on
  - the fan scatters into empty space at range, so the nominal DPS holds only at point-blank [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 3 | 00-data/blocks.json |
| Health | 1980 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 550 items (copper × 225, graphite × 225, thorium × 100) | 00-data/blocks.json |
| Range | 90 world units (11.25 tiles) | 00-data/turrets.json |
| reload | 35 ticks | 00-data/turrets.json |
| shots | 3 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 30 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Direct dmg | Splash | reloadMult | Shots/s | Per-target DPS (0 armor) | Displayed DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| thorium | 105 | 0 | 1.00 | 5.14 | 540.0 | 540.0 | 1.03 | 426.9 | 00-data |
| titanium | 66 | 0 | 1.30 | 3.96 | 261.1 | 261.1 | 0.99 | 174.1 | 00-data |

- 426.9 = 5.14 × (105 − 22), armor is subtracted once per shot; the gap between 540 and 426.9 is the full cost of 22 armor [src: 00-data/turrets.json]
- displayed DPS equals per-target: fuse's ammo has no splash field

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3915 — definition line new ItemTurret("fuse")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3923 — contains ShootSpread / 3
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9
- 00-data/turret_shots.json#id=fuse — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: positioning fuse to cover a 20-tile approach; an 11.25-tile reach leaves it silent until the enemy is already close. Reproduce: fuse's range 90 against spectre's 260 in 00-data/turrets.json [src: 00-data/turrets.json]
- Counterexample: expecting fuse to clear groups with splash; its 3 shots are fan direct damage with displayed = per-target, so group damage falls well short of cyclone's 415.5 displayed. Reproduce: the "Displayed DPS" column for fuse and cyclone in the same table [src: 00-data/turrets.json]

## Common misconceptions

- "short reach so it is weak" wrong: against units at point-blank in the same wave, 540 DPS is the top tier in the game
- "3 shots = 3× damage" wrong: the 3 shots are already inside the 540 metric, do not multiply again

## Related

- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.106]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.112]]
- [[COMBAT.TURRET.114]]
