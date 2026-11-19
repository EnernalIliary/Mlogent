---
tokens: 573
id: COMBAT.TURRET.108
title: parallax — the air puller with 16 traction
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3641"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/parallax"
  - "jar:v160.7#blocks/parallax"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, parallax, air displacement control / pull-in]
---

## One line

parallax is not a kill turret, it is a displacement turret: air only, using a base traction of 16 to drag flying units **towards itself**, with only 30/s of incidental damage. It solves "a flying unit parked on the core" -- pulling the target out of the core area and into other turrets' reach, at the cost of almost no kills of its own; use it as anti-air DPS and you will be very disappointed. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: air displacement control / pull-in (drag the target towards itself)
- **Firing mode**: no firing cycle (continuous traction) (1 shot per trigger; no reload (continuous / tractor type)) [src: 00-data/turret_shots.json]
- **Target layers**: air
- air only (targetAir true, targetGround false); a 300-world-unit (37.5 tiles) reach is the longest among anti-air turrets [src: 00-data/turrets.json]
- traction 16 and a distance-scaled component 9, **stronger the closer it gets**: the impulse direction is `turret position − target position`, so the core effect is dragging the target towards itself rather than shooting it down [src: Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/TractorBeamTurret.java:133]
- the incidental damage is 0.5/tick, i.e. 30/s -- that number is a bonus and cannot kill any mid or late unit [src: 00-data/turrets.json]
- power draw 198/s; it must be paired with real output turrets, alone on a line it equals no output [src: 00-data/turrets.json]
- **Strengths**:
  - the 37.5-tile reach lets it start pulling from far away: a flying unit that enters 37.5 tiles is dragged towards the turret, i.e. pulled out of the core area [src: 00-data/turrets.json]
  - against flying units it is a "hook": pulling them in drags bombers and bombing units off their drop position, suppression far beyond the 30/s of damage [src: 00-data/turrets.json]
  - one turret slot noticeably changes where an airdrop wave lands
- **Weaknesses**:
  - 30/s means it can hardly finish a kill alone, output turrets are mandatory [src: 00-data/turrets.json]
  - completely useless against ground units, a blank card in a ground wave
  - 198/s buys no kills, which makes it easy to misjudge as an "anti-air turret" when planning [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 2 | 00-data/blocks.json |
| Health | 640 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 320 items (graphite × 50, titanium × 110, silicon × 160) | 00-data/blocks.json |
| Range | 300 world units (37.50 tiles) | 00-data/turrets.json |
| reload | — ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 1 / 6 | 00-data/turrets.json |
| Power draw | 198/s | 00-data/turrets.json |

| Item | Value | Notes | Source |
|---|---|---|---|
| force | 16 | traction force | Mindustry-Source/core/src/mindustry/content/Blocks.java:3642 |
| scaledForce | 9 | scales with distance | Mindustry-Source/core/src/mindustry/content/Blocks.java:3643 |
| damage | 0.5/tick | setStats displays ×60 = 30/s | Mindustry-Source/core/src/mindustry/content/Blocks.java:3644 |
| Power draw | 198/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:3653 |

- air only (targetAir=true, targetGround=false); the impulse `Tmp.v1.set(this).sub(target)` points at the turret, i.e. it drags flying units towards itself; the closer the target, the larger the extra term `(1 − d/range) × scaledForce`. This is displacement control, not lethality. [src: Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/TractorBeamTurret.java:133]
- the 30/s of damage is a bonus only, expecting it to shoot things down is misuse. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3641]

- this library does not rank parallax by DPS: 30/s is incidental damage, its product is displacement (traction 16) and the two do not convert [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3641 — definition line new TractorBeamTurret("parallax")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this turret does not override it)
- Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/TractorBeamTurret.java:133 — `target.impulseNet(Tmp.v1.set(this).sub(target).limit((force + (1f - target.dst(this) / range) * scaledForce) * edelta))`, the impulse points at the turret = pull-in
- 00-data/turret_shots.json#id=parallax — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: parallax alone guarding against airdrops; 30/s cannot kill any mid or late flying unit, it only delays. Reproduce: the MANUAL parallax table in gen_turrets.py (force 16 / damage 0.5 per tick) [src: 00-data/turrets.json]
- Counterexample: place it on a ground wave route; targetGround is false, so zero output for the whole wave. Reproduce: parallax's targetGround field in 00-data/turrets.json [src: 00-data/turrets.json]

## Common misconceptions

- "parallax is an anti-air gun" wrong: it is a displacement tool, kills come from other turrets
- "more traction means more damage" wrong: force 16 and 0.5/tick are two independent parameter sets [src: 00-data/turrets.json]
- "parallax pushes units away" wrong: the impulse is "turret − target", it **pulls in**, and the closer the target the stronger [src: Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/TractorBeamTurret.java:133]

## Related

- [[COMBAT.TURRET.109]]
- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.107]]
