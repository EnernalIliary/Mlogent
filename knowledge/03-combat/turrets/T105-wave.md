---
tokens: 623
id: COMBAT.TURRET.105
title: wave — the 20-shot-barrage fire extinguisher
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3529"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/wave"
  - "jar:v160.7#blocks/wave"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, wave, status control / extinguishing and knockback]
---

## One line

wave's DPS is close to zero (water deals 0, slag only 80), but it does what DPS cannot express: a 20 shots/s liquid barrage carrying 0.7 knockback pins melee units in place, and water and cryofluid carry the extinguisher mark, the only means of suppressing a burn wave. It does not buy output; it buys "do not let the enemy close in". [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: status control / extinguishing and knockback
- **Firing mode**: ShootPattern (default) (1 shot per trigger; reload 3 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- reload 3 ticks ⇒ 20 shots/s, one of the highest fire rates in the game; the ammo is not items but liquids, fed by pipes/containers, and a cut flow stops the fire [src: 00-data/turrets.json]
- the four liquids have clear jobs: water 0 damage, pure knockback plus extinguishing; slag 4 damage (80 DPS, the only one with damage); cryofluid 0 damage, freeze plus extinguishing; oil 0 damage, applies the oil status only
- knockback 0.7 is the core: against melee/self-destruct units, pressing their advance down buys time for the back line [src: 00-data/turrets.json]
- a 110-world-unit (13.75 tiles) reach is on the short side, which makes it a second-line / core-hugging turret, not a front-line one [src: 00-data/turrets.json]
- **Strengths**:
  - 20 shots/s of knockback is the strongest soft control in the family and outstanding against point-blank units like crawler [src: 00-data/turrets.json]
  - the extinguisher mark suppresses burning ground and burning units, insurance on defense maps
  - slag mode still has 80 DPS, so output is not entirely absent
- **Weaknesses**:
  - water/cryofluid/oil have 0 direct damage, pure control, so against a high-health push they only delay
  - once the liquid supply chain is cut or the flow breaks, the turret goes mute at once
  - a 13.75-tile reach means it cannot protect the outer ring, only the core [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 2 | 00-data/blocks.json |
| Health | 1000 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 145 items (copper × 25, lead × 75, metaglass × 45) | 00-data/blocks.json |
| Range | 110 world units (13.75 tiles) | 00-data/turrets.json |
| reload | 3 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 50 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Damage per shot | Shots/s | 0-armor DPS | Mechanism | Source |
|---|---|---|---|---|---|
| water | 0 | 20 | 0 | knockback 0.7 and the extinguisher mark only | Mindustry-Source/core/src/mindustry/content/Blocks.java:3536 |
| slag | 4 | 20 | 80 | the only ammo that deals damage | Mindustry-Source/core/src/mindustry/content/Blocks.java:3541 |
| cryofluid | 0 | 20 | 0 | freeze plus extinguishing, no direct damage | Mindustry-Source/core/src/mindustry/content/Blocks.java:3544 |
| oil | 0 | 20 | 0 | applies the oil (flammable) status only | Mindustry-Source/core/src/mindustry/content/Blocks.java:3547 |

- reload 3 ticks ⇒ 20 shots/s, one of the highest fire rates in the game; every advantage is in status and knockback, not in damage. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3529]
- a liquid turret's ammo is not items: it needs pipes/containers for supply, and a cut flow stops the fire (it does not empty a magazine). [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3529]

- this library gives liquid turrets no "DPS ranking": water's 0 damage is by design, not missing data; to compare, use 0.7 knockback and the extinguisher mark [src: 00-data/turrets.json]
- slag's 80 DPS is 4 damage × 20 shots/s, do not plan firepower around it as an output turret

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3529 — definition line new LiquidTurret("wave")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this turret does not override it)
- 00-data/turret_shots.json#id=wave — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: put wave on the first row to stop heavy armor; 80 DPS barely scratches 22 armor and it dies first instead. Reproduce: wave has no ammo[] table in 00-data/turrets.json, the values are in the MANUAL block of gen_turrets.py [src: 00-data/turrets.json]
- Counterexample: feed wave oil and use it as an output turret; 0 direct damage means it kills nothing, it only applies oil. Reproduce: the oil row of the MANUAL table, 0 direct damage [src: 00-data/turrets.json]

## Common misconceptions

- "wave ranks first because it is the strongest" wrong: it is strong at control and extinguishing; on pure output it loses to any turret of its tier
- "liquid turrets need no supply" wrong: a cut flow stops it instantly, deadlier than an empty magazine

## Related

- [[COMBAT.TURRET.112]]
- [[COMBAT.TURRET.118]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.104]]
- [[COMBAT.TURRET.106]]
