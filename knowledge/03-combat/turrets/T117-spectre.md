---
tokens: 540
id: COMBAT.TURRET.117
title: spectre — the 685-DPS endgame main gun
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4248"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/spectre"
  - "jar:v160.7#blocks/spectre"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, spectre, late-game mainstay / all-target point kill]
---

## One line

spectre is the late-game answer for a defense line: reload 7 ticks, 8.57 shots/s, 685.7 single-target DPS on thorium, 497.1 against 22 armor, air and ground alike, with a 260-world-unit (32.5-tile) firing arc. Its only problem is ammo burn — 4.29 items/s of thorium means one dedicated line feeds only two of them, and the 1875-item cost makes it come online very late. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: S | **Role**: late-game mainstay / all-target point kill
- **Shoot pattern**: ShootAlternate(8f) (1 shot per trigger; reload 7 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- 1 shot per trigger, reload 7 ticks ⇒ 8.57 shots/s; ShootAlternate alternates the two barrels and hits both air and ground [src: 00-data/turrets.json]
- thorium 80 direct damage → 685.7 single-target/panel, 497.1 against 22 armor; pyratite 70 + 20 splash → 600 / 728.6 panel [src: 00-data/turrets.json]
- coolantMult 0.5: with coolant the reload drops to 3.5 ticks, and that is where its real ceiling lies [src: 00-data/turrets.json]
- graphite mode rm 1.70 pushes the fire rate down to 5.04 shots/s and DPS to 252.1, showing how sensitive it is to ammo quality [src: 00-data/turrets.json]
- **Pros**:
  - 685.7 single-target / 497.1 against 22 armor is the strongest sustained air-and-ground output [src: 00-data/turrets.json]
  - 8.57 shots/s makes a missed shot nearly free, so the output is extremely stable [src: 00-data/turrets.json]
  - 32.5-tile arc + 2560 health lets it sit on the second line and absorb stray return fire [src: 00-data/turrets.json]
- **Cons**:
  - 4.29 items/s of thorium: the supply line breaks and DPS drops to zero immediately [src: 00-data/turrets.json]
  - 1875-item cost + 4×4 footprint makes the window in which it comes online very late
  - Against 0 armor it is not as cheap as fuse's 540; its advantage is armor and firing arc [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 4 | 00-data/blocks.json |
| Health | 2560 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 1875 items (copper × 900, graphite × 300, thorium × 250, plastanium × 175, surge-alloy × 250) | 00-data/blocks.json |
| Range | 260 world units (32.50 tiles) | 00-data/turrets.json |
| reload | 7 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 0.5 / 24 | 00-data/turrets.json |
| Power | 0/s | 00-data/turrets.json |

| Ammo | Direct damage | Splash | reloadMult | shots/s | Single-target DPS (0 armor) | Panel DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| thorium | 80 | 0 | 1.00 | 8.57 | 685.7 | 685.7 | 4.29 | 497.1 | 00-data |
| pyratite | 70 | 20 | 1.00 | 8.57 | 600.0 | 728.6 | 2.86 | 411.4 | 00-data |
| graphite | 50 | 0 | 1.70 | 5.04 | 252.1 | 252.1 | 1.26 | 141.2 | 00-data |

- 497.1 = 8.57 × (80 − 22); under thorium it is 27.5% below 685.7, so armor still has to be counted [src: 00-data/turrets.json]
- The gain from coolantMult 0.5 is not in this table's DPS: the values are uncooled, and the real figure with coolant is higher, so do not compare them directly [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4248 — definition line new ItemTurret("spectre")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4302 — holds ShootAlternate
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29
- 00-data/turret_shots.json#id=spectre — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: assuming spectre has the highest panel and therefore beats everything — its 728.6 is the pyratite splash convention, and single-target is only 600, below thorium's 685.7; reproduce: the single-target/panel columns of the spectre ammo rows in 00-data/turrets.json [src: 00-data/turrets.json]
- Counter-example: taking spectre into early waves — 4.29 items/s of thorium cannot be supplied early, so real DPS is far below the nominal figure; reproduce: the ips column of the same table against the 550-item fuse [src: 00-data/turrets.json]

## Common misconceptions

- "Panel DPS is combat DPS" — wrong: three premises are required at once — no coolant, zero armor, full ammo supply
- "Two barrels = double fire rate" — wrong: 8.57 shots/s is already the reload-7 convention; the barrel count only affects the model and the projectile path [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.113]]
- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.118]]
