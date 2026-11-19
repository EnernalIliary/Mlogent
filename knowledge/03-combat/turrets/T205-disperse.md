---
tokens: 549
id: COMBAT.TURRET.205
title: disperse — an anti-air gun at 310 world units, air only
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4840"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/disperse"
  - "jar:v160.7#blocks/disperse"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, disperse, dedicated anti-air / quad-barrel flak]
---

## One line

disperse solves "how to stop an air wave", not "how to fight on the ground": on thorium its 4 alternating barrels fire 31.37 shots/s × 67.5 = 2117.6 DPS, with 310 world units (38.75 tiles) covering a large piece of sky. The price is targetGround False — during a ground wave it deals 0 all game — and a 31.37 items/s throughput that already sits at the limit of a single full belt. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: dedicated anti-air / quad-barrel flak
- **Shoot pattern**: ShootAlternate(4f) + shots/barrels (4 shots per trigger; reload 9 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, buildings
- shots 4 + ShootAlternate(4f), reload 9 ticks: thorium rm 0.85 ⇒ 31.37 shots/s × 67.5 = 2117.6 DPS [src: 00-data/turrets.json]
- Air only (ground False): ground units inside its arc still draw no fire [src: 00-data/turrets.json]
- surge-alloy buys 1733.3 DPS for 11.85 items/s, 951.1 against 22 armor; tungsten buys 1300.0 for 8.89 items/s and is the lean version [src: 00-data/turrets.json]
- silicon 27.75 per shot leaves only 153.3 against 22 armor (21%) — AA towers are bitten by armor too, they just normally shoot low-armor aircraft [src: 00-data/turrets.json]
- 310 world units (38.75 tiles) of coverage; 4×4, 650 items, 4480 health [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4840]
- **Pros**:
  - 2117.6 DPS + 310 of coverage makes it Erekir's only dedicated anti-air; without it an air wave leaks through [src: 00-data/turrets.json]
  - 31.37 shots/s across four alternating barrels forgives misses, so a dispersed air group rarely slips by [src: 00-data/turrets.json]
  - thorium keeps 67% against 22 armor, more respectable than the low-tier ammo curves of most Erekir towers [src: 00-data/turrets.json]
- **Cons**:
  - ground False: during a ground wave a 650-item tower deals 0, so ground firepower has to be built separately [src: 00-data/turrets.json]
  - 31.37 items/s is close to the full-belt limit; the feed stops and it drops at once to tungsten's 26.67 shots/s [src: 00-data/turrets.json]
  - The silicon curve keeps only 21% against 22 armor, so do not use it on heavy-armor fliers [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 4 | 00-data/blocks.json |
| Health | 4480 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 650 items (thorium × 50, silicon × 200, beryllium × 350, oxide × 50) | 00-data/blocks.json |
| Range | 310 world units (38.75 tiles) | 00-data/turrets.json |
| reload | 9 ticks | 00-data/turrets.json |
| shots | 4 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 6.25 / 30 | 00-data/turrets.json |
| Power | 0/s | 00-data/turrets.json |

| Ammo | Direct damage | Splash | reloadMult | shots/s | Single-target DPS (0 armor) | Panel DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| thorium | 67.5 | 0 | 0.85 | 31.37 | 2117.6 | 2117.6 | 31.37 | 1427.5 | 00-data |
| surge-alloy | 48.75 | 0 | 0.75 | 35.56 | 1733.3 | 1733.3 | 11.85 | 951.1 | 00-data |
| tungsten | 48.75 | 0 | 1.00 | 26.67 | 1300.0 | 1300.0 | 8.89 | 713.3 | 00-data |
| silicon | 27.75 | 0 | 1.00 | 26.67 | 740.0 | 740.0 | 6.67 | 153.3 | 00-data |

- Panel = single-target (no splash); the four barrels rotate rather than fire as one salvo of four, and the fire-rate convention is 31.37 shots/s [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4840 — definition line new ItemTurret("disperse")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5001 — holds ShootAlternate
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5003 — holds shots / 4
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5004 — holds barrels / 4
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29
- 00-data/turret_shots.json#id=disperse — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: holding a ground wave with disperse — targetGround False gives it 0 output all game [src: 00-data/turrets.json]
- Counter-example: feeding it only silicon against heavy-armor fliers — 153.3 DPS against 22 armor is 10.7% of thorium; reproduce: 1427.5 and 153.3 in the vs-22-armor column [src: 00-data/turrets.json]

## Common misconceptions

- "AA towers do not care about armor" — wrong: thorium keeps 67% against 22 armor, silicon only 21% [src: 00-data/turrets.json]
- "shots 4 means a burst of four" — wrong: ShootAlternate rotates four barrels, and 31.37 shots/s is the total fire rate [src: 00-data/turrets.json]
- "surge is always strongest" — wrong: surge is 18% below thorium in DPS; what it buys is lower throughput (11.85 items/s) [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.102]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.204]]
- [[COMBAT.TURRET.206]]
