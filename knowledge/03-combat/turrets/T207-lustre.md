---
tokens: 663
id: COMBAT.TURRET.207
title: lustre — a 360° laser that picks the toughest target
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5147"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/lustre"
  - "jar:v160.7#blocks/lustre"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, lustre, omnidirectional point kill / strongest-target first]
---

## One line

lustre solves "point kill and finishing blows from the middle of a position": shootCone 360 gives it an omnidirectional arc, and unitSort strongest picks the toughest target automatically, so its facing never has to be planned; 590 items, 4×4, 210 per settlement, and 90% retained per settlement against 22 armor. The price is a two-layer supply of 200 power/s plus nitrogen, and one honest gap — this library gives no DPS figure, because ContinuousTurret's settlement interval is not in the reflection table. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]

## Rules / formulas

- **Tier**: A | **Role**: omnidirectional point kill / strongest-target first
- **Shoot pattern**: continuous beam (1 shot per trigger; reload 10 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- PointLaserBulletType, 210 per settlement; shootCone 360 ⇒ omnidirectional arc, no turning needed [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- unitSort strongest ⇒ automatically picks the toughest/most expensive target, which is "priority", not "nearest" [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5157]
- Consumes nitrogen + 200/s of power, a two-layer supply; 4×4, 590 items, 3360 health [src: 00-data/turrets.json]
- Against 22 armor: 210 per settlement leaves 188 (90%), one of the lightest armor penalties of any settlement type [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- 250 world units (31.25 tiles) of coverage; omnidirectional means the real coverage is a circle drawn around it [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5147]
- **Pros**:
  - 360° + strongest placed in the middle of a position covers all four sides at once, with no facing to plan [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5160]
  - 590 items is the cheapest in its tier; the 210-per-settlement hit is instantaneous and ignores projectile travel [src: 00-data/turrets.json]
- **Cons**:
  - This library gives no DPS figure: the settlement interval is not in the reflection table, and writing a DPS anyway would be invention [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
  - 200 power/s + nitrogen: break either supply line and it stops firing [src: 00-data/turrets.json]
  - 31.25 tiles of coverage is short in the late game and gets suppressed by titan's 48.75 [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 4 | 00-data/blocks.json |
| Health | 3360 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 590 items (graphite × 200, silicon × 250, oxide × 50, carbide × 90) | 00-data/blocks.json |
| Range | 250 world units (31.25 tiles) | 00-data/turrets.json |
| reload | 10 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 1 / 360 | 00-data/turrets.json |
| Power | 200/s | 00-data/turrets.json |

| Item | Value | Note | Source |
|---|---|---|---|
| Damage per settlement | 210 | PointLaserBulletType | Mindustry-Source/core/src/mindustry/content/Blocks.java:5148 |
| shootCone | 360 | omnidirectional arc | Mindustry-Source/core/src/mindustry/content/Blocks.java:5160 |
| unitSort | strongest | prioritises the strongest target | Mindustry-Source/core/src/mindustry/content/Blocks.java:5157 |
| Consumption | nitrogen 6/60 per tick + 200/60 power per tick | two-layer supply | Mindustry-Source/core/src/mindustry/content/Blocks.java:5165 |

- Continuous-beam type; the DPS convention depends on ContinuousTurret's settlement interval, so this table gives no DPS figure (the honest gap is noted at the end). [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5147]
- shootCone 360 + strongest sorting ⇒ naturally point-kills the toughest target, which suits the middle of a position. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5147]

- Do not multiply "210 per settlement" by any coefficient and call it DPS: this library has no interval, so 210 is only the magnitude of one hit [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- The 90% against 22 armor is a per-settlement retention, not a DPS retention [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5147 — definition line new ContinuousTurret("lustre")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this tower does not override it)
- 00-data/turret_shots.json#id=lustre — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: reading 210 as "210 DPS" and comparing it with afflict's 216 leads to the wrong conclusion that lustre is slightly weaker; it actually settles several times per second, but this library has no interval to invert [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- Counter-example: putting lustre on the front line, where its 31.25-tile effective distance is suppressed first by titan's 48.75; it belongs in the middle of the second line [src: 00-data/turrets.json]

## Common misconceptions

- "Beam towers have low DPS" — wrong: 210 is a single settlement, the interval is unknown, and it cannot be read as damage per second [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- "360° is only cosmetic" — wrong: unitSort strongest makes it finish the toughest target automatically, saving manual focus fire [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5157]
- "Nitrogen can be skipped" — wrong: nitrogen is its second supply, on the same level as power [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.206]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.TURRET.208]]
