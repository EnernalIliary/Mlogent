---
tokens: 566
id: COMBAT.TURRET.204
title: titan — a siege cannon at 390 world units that barely notices armor
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4639"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/titan"
  - "jar:v160.7#blocks/titan"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, titan, long-range bombardment / ground only]
---

## One line

titan solves "dismantle a position from outside the enemy's arc", not "kill a single target": 390 world units (48.75 tiles) of range, carbide 525 per shot + 750 splash, 285.3 single-target and 591.0 panel, and still 273.4 (96%) against 22 armor. The price is ground-only (air False) and a slow 0.54 shots/s rhythm — during an air wave it is a 950-item ornament. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: long-range bombardment / ground only
- **Shoot pattern**: ShootPattern(default) (1 shot per trigger; reload 138 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: ground, buildings
- reload 138 ticks, carbide rm 0.80 ⇒ 0.54 shots/s, 525 per shot + 750 splash: 285.3 single-target, 591.0 panel [src: 00-data/turrets.json]
- Ground only (targetAir False): air units inside its arc still draw no fire [src: 00-data/turrets.json]
- 390 world units (48.75 tiles) is the longest tier among Erekir's regular towers; 4×4, 950 items, 4000 health [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4639]
- ammoPerShot 4, maxAmmo 12 ⇒ 3 shots per magazine; carbide's 2.17 items/s throughput is not expensive on a 950-item tower [src: 00-data/turrets.json]
- Against 22 armor: carbide 273.4 (96%), oxide 126.1 (90%), thorium 104.6 (92%) — high-damage splash towers are barely bitten by armor [src: 00-data/turrets.json]
- **Pros**:
  - 591.0 panel DPS + 750 splash clears a patch from 48.75 tiles away, the only regular Erekir tower that can open fire first [src: 00-data/turrets.json]
  - Keeps 96% against 22 armor, the least armor-sensitive tower in the game on the carbide curve [src: 00-data/turrets.json]
  - 4000 health + 4×4 lets it stand in front as a half-tank battery [src: 00-data/turrets.json]
- **Cons**:
  - Cannot hit air at all: 0 output during an air wave, anti-air has to come from disperse [src: 00-data/turrets.json]
  - At 0.54 shots/s a single target is settled only once every two seconds or more, and it whiffs easily against high-mobility units [src: 00-data/turrets.json]
  - The 4×4 footprint demands sight lines and a meat shield up front; placement decides whether it is good far more than its numbers do [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 4 | 00-data/blocks.json |
| Health | 4000 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 950 items (thorium × 400, silicon × 300, tungsten × 250) | 00-data/blocks.json |
| Range | 390 world units (48.75 tiles) | 00-data/turrets.json |
| reload | 138 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 3.75 / 8 | 00-data/turrets.json |
| Power | 0/s | 00-data/turrets.json |

| Ammo | Direct damage | Splash | reloadMult | shots/s | Single-target DPS (0 armor) | Panel DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| carbide | 525 | 750 | 0.80 | 0.54 | 285.3 | 591.0 | 2.17 | 273.4 | 00-data |
| oxide | 225 | 180 | 0.70 | 0.62 | 139.8 | 223.6 | 2.48 | 126.1 | 00-data |
| thorium | 262.5 | 350 | 1.00 | 0.43 | 114.1 | 228.3 | 1.74 | 104.6 | 00-data |

- Panel 591.0 is 2.07× single-target 285.3: never compare the panel against single-target when judging it; the 0.75 splash fold is the BulletType.estimateDPS convention [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4639 — definition line new ItemTurret("titan")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this tower does not override it)
- 00-data/turret_shots.json#id=titan — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: using titan during an air wave — targetAir False means that wave's output is 0; for the same 950 items you can place one disperse (650 items) plus one breach [src: 00-data/turrets.json]
- Counter-example: reading "titan 591.0 is above smite 562.5" and treating it as a single-target tower — against one target it has only 285.3; reproduce: 285.3 in the single-target column and 591.0 in the panel column [src: 00-data/turrets.json]

## Common misconceptions

- "Splash towers need no prediction" — wrong: inaccuracy 0 but 0.54 shots/s, the impact point is fixed yet still has to be led [src: 00-data/turrets.json]
- "Long range means main-tower material" — wrong: ground only and one shot per 5.4 seconds; a main slot wants sustained coverage, not a single heavy hit [src: 00-data/turrets.json]
- "4×4 is a drawback" — half wrong: 4×4 buys 4000 health and 390 of coverage; placed well it is an advantage [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.205]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.203]]
