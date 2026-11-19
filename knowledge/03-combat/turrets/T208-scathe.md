---
tokens: 572
id: COMBAT.TURRET.208
title: scathe — a 1350-world-unit missile rack, one shot every ten seconds
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5212"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/scathe"
  - "jar:v160.7#blocks/scathe"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, scathe, cross-screen missile / strategic strike]
---

## One line

scathe is not a gun, it is a launcher: the tower's projectile BulletType(0,0) only spawns a unit, and the real damage is the missile weapon's 1000 splash, so computing DPS from the tower panel gives 0. It solves "hit beyond the screen" — 1350 world units (168.75 tiles) of coverage, one shot every 10 seconds, 3 shots per magazine; the price is 1650 items, ground only, and a 30-second window of risk. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5218]

## Rules / formulas

- **Tier**: A | **Role**: cross-screen missile / strategic strike
- **Shoot pattern**: launches a MissileUnitType missile unit (1 shot per trigger; reload 600 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: ground, buildings
- The tower's shootType is BulletType(0,0) + a spawnUnit missile: the tower deals 0 damage, the real damage is the missile weapon's 1000 splash [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5218]
- reload 600 ticks ⇒ one shot every 10 seconds; maxAmmo 45 / ammoPerShot 15 ⇒ 3 shots per magazine [src: 00-data/turrets.json]
- 1350 world units (168.75 tiles) is the longest in the game, which makes it a cross-screen strategic weapon [src: 00-data/turrets.json]
- Ground only (air False); the rm 0.80 / 0.90 / 1.00 of the three ammo types phase-fabric / surge-alloy / carbide only changes the reload rhythm, not the damage [src: 00-data/turrets.json]
- Splash 1000 leaves 978 against 22 armor (98%), so it barely feels armor [src: 00-data/turrets.json]
- **Pros**:
  - 168.75 tiles of coverage lets it destroy the enemy position before that enemy enters any arc, the only opening strike Erekir has [src: 00-data/turrets.json]
  - Splash 1000 keeps 98% against 22 armor, so heavy-armor units are just as fragile in front of it [src: 00-data/turrets.json]
- **Cons**:
  - 1650 items + one shot per 10 seconds: a single tower's sustained output is negligible, what it buys is "one shot, one patch cleared" [src: 00-data/turrets.json]
  - Ground only, so it is completely silent during an air wave [src: 00-data/turrets.json]
  - 3 shots per magazine at ammoPerShot 15: break the supply and it is a 30-second window of silence [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 4 | 00-data/blocks.json |
| Health | 3520 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 1650 items (graphite × 400, silicon × 450, tungsten × 500, oxide × 100, carbide × 200) | 00-data/blocks.json |
| Range | 1350 world units (168.75 tiles) | 00-data/turrets.json |
| reload | 600 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 15 / 1 | 00-data/turrets.json |
| Power | 0/s | 00-data/turrets.json |

| Ammo | Direct damage | Splash | reloadMult | shots/s | Single-target DPS (0 armor) | Panel DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| phase-fabric | 0 | 0 | 0.80 | 0.12 | 0.0 | 0.0 | 0.38 | 0.0 | 00-data |
| surge-alloy | 0 | 0 | 0.90 | 0.11 | 0.0 | 0.0 | 1.67 | 0.0 | 00-data |
| carbide | 0 | 0 | 1.00 | 0.10 | 0.0 | 0.0 | 1.50 | 0.0 | 00-data |

- This is a missile launcher rather than a gun: damage is settled when the missile lands, so DPS cannot be computed from the tower's shootType. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5212]
- Range 1350 world units (about 169 tiles) is the longest in the game, which makes it a cross-screen strategic weapon. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5212]

- Never compute DPS from the tower's 0 direct damage: that is the spawnUnit placeholder projectile, and the real damage is scathe-missile-weapon1's 1000 splash [src: 00-data/bullets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5212 — definition line new ItemTurret("scathe")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5224 — holds MissileUnitType
- 00-data/turret_shots.json#id=scathe — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: computing scathe's DPS from the tower panel gives 0, which would rate it the worst tower; the real figure is 1000 splash × 3 shots per magazine [src: 00-data/bullets.json]
- Counter-example: taking scathe into an air wave — air False means 0 output outright [src: 00-data/turrets.json]

## Common misconceptions

- "0 damage = useless tower" — wrong: the tower is only the launcher, the damage is in the projectile [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5218]
- "One shot per 10 seconds is too slow" — half wrong: its value is the 168.75-tile opening strike and 1000 splash, not DPS [src: 00-data/turrets.json]
- "carbide hits harder" — wrong: the tower's damage is 0 on all three ammo types; rm only changes the reload speed [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.207]]
- [[COMBAT.TURRET.209]]
