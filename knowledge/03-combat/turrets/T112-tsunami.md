---
tokens: 621
id: COMBAT.TURRET.112
title: tsunami — the twin-barrel liquid sprinkler
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3850"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/tsunami"
  - "jar:v160.7#blocks/tsunami"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, tsunami, twin-barrel liquid / debuff and trash clearing]
---

## One line

tsunami is a scaled-up wave: twin barrels, 2 shots per trigger, reload 3 ticks, a 20-trigger/s liquid barrage, 95 DPS on slag, the only liquid turret whose output can be counted. The problem is cost -- 850 items plus 2.5 units of liquid per shot, and a 190-world-unit (23.75 tiles) reach, which makes it a core-area line turret rather than a front-line one. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: B | **Role**: twin-barrel liquid / debuff and trash clearing
- **Firing mode**: ShootAlternate(4f) (2 shots per trigger; reload 3 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- 2 shots per trigger (shots 2, ShootAlternate alternates the twin barrels), reload 3 ticks ⇒ about 20 triggers/s [src: 00-data/turrets.json]
- the ammo is liquid: water 0.2 per shot, slag 4.75, cryofluid 0.2, oil 0.2; each shot consumes 2.5 units of liquid, so 20 triggers/s means 50 liquid/s [src: 00-data/turrets.json]
- the four liquids divide the work exactly as on wave: water/cryofluid extinguish, cryofluid freezes, oil applies oil, and slag is the only option with real damage [src: 00-data/turrets.json]
- it hits air and ground, a rare general target set among liquid turrets
- **Strengths**:
  - 95 DPS on slag, the only option among liquid turrets that works as output [src: 00-data/turrets.json]
  - the density of 20 triggers/s spreads debuffs (freeze/oil/extinguish) extremely fast, faster than wave fills an area
  - 2250 health plus a 3×3 footprint makes it far tougher than wave, so it can sit a little forward
- **Weaknesses**:
  - 850 items plus 50 liquid/s, a supply chain far costlier than a solid-ammo turret of the same DPS [src: 00-data/turrets.json]
  - 95 DPS is no competition for the 405-item cyclone (415.5 displayed), it exists only for debuffs [src: 00-data/turrets.json]
  - the 23.75-tile reach limits it to the core, it cannot cover the outer ring [src: 00-data/turrets.json]
- **Metric**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; displayed DPS then folds splash in at 0.75 per BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 3 | 00-data/blocks.json |
| Health | 2250 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Build cost | 850 items (lead × 400, metaglass × 100, titanium × 250, thorium × 100) | 00-data/blocks.json |
| Range | 190 world units (23.75 tiles) | 00-data/turrets.json |
| reload | 3 ticks | 00-data/turrets.json |
| shots | 2 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 5 / 45 | 00-data/turrets.json |
| Power draw | 0/s | 00-data/turrets.json |

| Ammo | Damage per shot | Shots/s | 0-armor DPS | ammoMultiplier | Source |
|---|---|---|---|---|---|
| water | 0.2 | 20 | 4 | 0.4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3857 |
| slag | 4.75 | 20 | 95 | 0.4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3858 |
| cryofluid | 0.2 | 20 | 4 | 0.4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3859 |
| oil | 0.2 | 20 | 4 | 0.4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3860 |

- ammoMultiplier 0.4 ⇒ 2.5 units of liquid per shot, which is 50 liquid/s at 20 shots/s, far more liquid pressure than wave. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3850]
- shots=2 (ShootAlternate alternates the twin barrels), so 0-armor DPS is 2 × 20 × damage per shot. [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3850]

- tsunami's fact card table: slag 4.75 per shot, 0-armor DPS 95; recomputing 20 × 4.75 gives exactly 95, consistent with this table (counting each barrel as a shot would give 190, this library does not use that metric) [src: 00-data/turrets.json]
- 2.5 units of liquid per shot × 20 triggers/s = 50 liquid/s, the number to remember when planning pipes [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3850 — definition line new LiquidTurret("tsunami")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3902 — contains ShootAlternate
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3903 — contains shots / 2
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29
- 00-data/turret_shots.json#id=tsunami — source-derived record (with evidence lines)

## Measurements and counterexamples

- Counterexample: tsunami as the main output source, 95 DPS is 1.5× a graphite duo (67.5) yet 24× the price. Reproduce: tsunami's MANUAL table in 00-data/turrets.json against duo [src: 00-data/turrets.json]
- Counterexample: assuming twin barrels = double DPS; the 95 against 190 in the table is exactly the difference between counting by trigger and counting by barrel, and this library always counts by trigger. Reproduce: the notes of the MANUAL tsunami table in gen_turrets.py [src: 00-data/turrets.json]

## Common misconceptions

- "liquid turrets deal low damage so they are useless" wrong: tsunami's product is the freeze/oil/extinguish debuffs, not DPS
- "twin barrels double the fire rate" wrong: shots 2 means two shots per trigger, the trigger frequency itself is set by reload

## Related

- [[COMBAT.TURRET.105]]
- [[COMBAT.TURRET.118]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.111]]
- [[COMBAT.TURRET.113]]
