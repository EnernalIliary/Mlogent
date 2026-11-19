---
tokens: 527
id: COMBAT.TURRET.116
title: foreshadow — a 405-damage hammer at 500 world units
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4203"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/foreshadow"
  - "jar:v160.7#blocks/foreshadow"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [turret, foreshadow, extreme-range sniping / anti-heavy-armor opener]
---

## One line

foreshadow spends 2700 items on a gun that reaches 500 world units (62.5 tiles): 0.3 shots/s, 1350 direct damage per shot, 405 DPS, and still 398.4 against 22 armor — armor barely affects it. It is the tower that chips the enemy down before that enemy enters any other tower's firing arc, at the price of 600/s of power, 5 items per shot and a very slow rhythm. [src: 00-data/turrets.json]

## Rules / formulas

- **Tier**: A | **Role**: extreme-range sniping / anti-heavy-armor opener
- **Shoot pattern**: ShootPattern(default) (1 shot per trigger; reload 200 ticks) [src: 00-data/turret_shots.json]
- **Target layers**: air, ground, buildings
- 1 shot per trigger, reload 200 ticks ⇒ 0.3 shots/s; the 500-world-unit (62.5-tile) firing arc is the longest in the game [src: 00-data/turrets.json]
- surge-alloy 1350 direct damage per shot → 405 DPS, 398.4 against 22 armor: one shot is enough to crack armor, armor is close to non-existent against it [src: 00-data/turrets.json]
- ammoPerShot 5 + maxAmmo 40: each shot eats 5 items, the magazine holds only 8 shots, so the feed must keep up
- 600/s of power is one of the highest tiers in the game; without a dedicated grid it cannot run at all [src: 00-data/turrets.json]
- **Pros**:
  - 62.5-tile firing arc + 405 single-target DPS lets it fire at a distance where every other tower is silent [src: 00-data/turrets.json]
  - 398.4 against 22 armor makes it the most effective single tower against heavy armor (lancer 39; fuse 426.9 but with an 11.25-tile arc) [src: 00-data/turrets.json]
  - 1350 per shot is the most efficient burst against high-health single targets
- **Cons**:
  - 0.3 shots/s: one missed shot loses more than 3 seconds, and hit rate against high-mobility targets is a hard flaw [src: 00-data/turrets.json]
  - 2700 items + 600/s power + 5 items per shot is the most expensive upkeep in the family [src: 00-data/turrets.json]
  - 4×4 footprint + extremely slow fire rate: completely unusable early [src: 00-data/turrets.json]
- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage; panel DPS further folds splash in at 0.75 through BulletType.estimateDPS (see [[COMBAT.NUMBERS.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## Numbers

| Item | Value | Source |
|---|---|---|
| Size | 4 | 00-data/blocks.json |
| Health | 2400 | 00-data/blocks.json |
| Armor | 0 | 00-data/blocks.json |
| Cost | 2700 items (copper × 1000, metaglass × 600, silicon × 600, plastanium × 200, surge-alloy × 300) | 00-data/blocks.json |
| Range | 500 world units (62.50 tiles) | 00-data/turrets.json |
| reload | 200 ticks | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| Coolant multiplier / shootCone | 0.4 / 2 | 00-data/turrets.json |
| Power | 600/s | 00-data/turrets.json |

| Ammo | Direct damage | Splash | reloadMult | shots/s | Single-target DPS (0 armor) | Panel DPS | Items/s | DPS vs 22 armor | Source |
|---|---|---|---|---|---|---|---|---|---|
| surge-alloy | 1350 | 0 | 1.00 | 0.30 | 405.0 | 405.0 | 1.50 | 398.4 | 00-data |

- 398.4 = 0.3 × (1350 − 22), only 1.6% below 405 — the best illustration that armor can be ignored once the single shot is heavy enough [src: 00-data/turrets.json]
- 1.5 items/s = 0.3 shots/s × 5 items/shot; use this number when planning the feed [src: 00-data/turrets.json]

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4203 — definition line new ItemTurret("foreshadow")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1 (this tower does not override it)
- 00-data/turret_shots.json#id=foreshadow — source-derived record (with evidence line)

## Measurements and counter-examples

- Counter-example: firing foreshadow at a crawler swarm, 0.3 shots/s kills one per round, far worse value than cyclone's 415.5 panel DPS; reproduce: the panel DPS column for foreshadow and cyclone in 00-data/turrets.json [src: 00-data/turrets.json]
- Counter-example: assuming it clears swarms with splash — 1350 is pure direct damage, panel = single-target, so its group damage is zero; reproduce: the foreshadow row of the same table [src: 00-data/turrets.json]

## Common misconceptions

- "Longest range means strongest" — wrong: the 0.3 shots/s rhythm leaves it with almost no output in a close-range melee [src: 00-data/turrets.json]
- "It cannot hurt high-armor targets" — wrong: it still has 398.4 against 22 armor, one of the best armor-resistant towers in the game [src: 00-data/turrets.json]

## Related

- [[COMBAT.TURRET.106]]
- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.115]]
