---
tokens: 821
id: COMBAT.TURRET.002
title: "Vanilla turret evaluation overview and selection decision table (per-turret index of 28)"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3258"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.NUMBERS.001]
tags: [turret, evaluation, selection, index]
---

## In one line

The 28 turrets should be chosen along two dimensions — "tier (the era in which you get it)" and "role (what you are short of)" — rather than ranked by single-target DPS: the highest-DPS turret in a tier is usually the one that most taxes supply and positioning, while a low-DPS turret is often the only one that solves a specific problem.

## Rules and formulas

- **Convention**: single-target DPS = 60/(reload × reloadMultiplier) × shots × direct damage, counting one target, zero armor, no cooling, no supply stalls. It is not field output; it is a comparable price.
- **Tier letters**: S = long-term front-line mainstay ｜ A = strong but specialized (only for specific enemies/situations) ｜ B = transitional or supplementary ｜ C = only in specific situations ｜ D = better options exist. This is a judgement of "worth building in a long campaign", not a numeric ranking.
- **Armor correction**: against a target with armor A use 60/(reload × rm) × shots × max(direct damage − A, 0.1 × direct damage) (minArmorDamage 0.1, see [[COMBAT.TURRET.001]]). [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]
- **Supply constraint**: the items/second column is the ammo consumption at full fire rate; above your production it automatically slows down, so the "DPS/item" column is what decides sustained output.
- **Tier is not strength**: Serpulo and Erekir are two independent tech lines; comparing numbers across the lines is meaningless.

## Numbers

| turret | tier | role | best ammo | single-target DPS(0 armor) | cost(items) | DPS/item | range(tiles) | target | source |
|---|---|---|---|---|---|---|---|---|---|
| COMBAT.TURRET.101 duo | B | early all-rounder / cheap burst baseline | graphite | 67.5 | 35 | 1.93 | 20.0 | air+ground | 00-data |
| COMBAT.TURRET.102 scatter | B | short-range AA / clearing bullet walls | scrap | 40.0 | 130 | 0.31 | 27.5 | air | 00-data |
| COMBAT.TURRET.103 scorch | C | point-blank fire wall / melting melee | pyratite | 300.0 | 47 | 6.38 | 7.5 | ground | 00-data |
| COMBAT.TURRET.104 hail | B | early arcing fire / group suppression | pyratite | 25.0 | 57 | 0.44 | 29.4 | ground | 00-data |
| COMBAT.TURRET.105 wave | A | status control / firefighting and knockback | liquid/special | see main text | 145 | - | 13.8 | air+ground | 00-data |
| COMBAT.TURRET.106 lancer | A | anti-heavy-armor / single-shot piercing | liquid/special | see main text | 220 | - | 20.6 | ground | 00-data |
| COMBAT.TURRET.107 arc | B | chain shock / interrupt control | liquid/special | see main text | 100 | - | 11.2 | ground | 00-data |
| COMBAT.TURRET.108 parallax | A | air displacement control / pull-in (drags the target toward itself) | liquid/special | see main text | 320 | - | 37.5 | air | 00-data |
| COMBAT.TURRET.109 swarmer | A | missile group damage / mid-range AA | surge-alloy | 126.0 | 145 | 0.87 | 30.0 | air+ground | 00-data |
| COMBAT.TURRET.110 salvo | A | mid-game mainstay / burst single-target kill | graphite | 320.7 | 230 | 1.39 | 23.8 | air+ground | 00-data |
| COMBAT.TURRET.111 segment | A | projectile interception / AA bullet clearing | liquid/special | see main text | 290 | - | 22.5 | - | 00-data |
| COMBAT.TURRET.112 tsunami | B | liquid double-barrel / debuffs and trash clearing | liquid/special | see main text | 850 | - | 23.8 | air+ground | 00-data |
| COMBAT.TURRET.113 fuse | S | short-range endgame / anti-heavy-armor burst | thorium | 540.0 | 550 | 0.98 | 11.2 | air+ground | 00-data |
| COMBAT.TURRET.114 ripple | A | long-range arcing suppression | pyratite | 96.0 | 345 | 0.28 | 36.2 | ground | 00-data |
| COMBAT.TURRET.115 cyclone | A | AA group damage / mid-range barrage | surge-alloy | 78.0 | 405 | 0.19 | 25.0 | air+ground | 00-data |
| COMBAT.TURRET.116 foreshadow | A | extreme-range sniping / anti-heavy-armor opener | surge-alloy | 405.0 | 2700 | 0.15 | 62.5 | air+ground | 00-data |
| COMBAT.TURRET.117 spectre | S | late-game mainstay / all-round single-target kill | thorium | 685.7 | 1875 | 0.37 | 32.5 | air+ground | 00-data |
| COMBAT.TURRET.118 meltdown | S | short-range continuous laser / high-power clearing | liquid/special | see main text | 2500 | - | 24.4 | air+ground | 00-data |
| COMBAT.TURRET.201 breach | B | opening mainstay / high per-shot rapid fire | carbide | 2437.5 | 425 | 5.74 | 23.8 | air+ground | 00-data |
| COMBAT.TURRET.202 diffuse | B | short-range group clearing / 15-shot spread | oxide | 2025.0 | 600 | 3.38 | 15.6 | air+ground | 00-data |
| COMBAT.TURRET.203 sublimate | A | sustained flame / ammo swaps trade range | liquid/special | see main text | 790 | - | 16.2 | air+ground | 00-data |
| COMBAT.TURRET.204 titan | A | long-range bombardment / ground only | carbide | 285.3 | 950 | 0.30 | 48.8 | ground | 00-data |
| COMBAT.TURRET.205 disperse | A | dedicated AA / four-barrel flak | thorium | 2117.6 | 650 | 3.26 | 38.8 | air | 00-data |
| COMBAT.TURRET.206 afflict | B | medium-caliber electric tower / piercing shots | liquid/special | see main text | 590 | - | 46.0 | air+ground | 00-data |
| COMBAT.TURRET.207 lustre | A | omnidirectional single-target kill / best target priority | liquid/special | see main text | 590 | - | 31.2 | air+ground | 00-data |
| COMBAT.TURRET.208 scathe | A | cross-screen missile / strategic strike | phase-fabric | 0.0 | 1650 | 0.00 | 168.8 | ground | 00-data |
| COMBAT.TURRET.209 smite | S | late-game main gun / five-barrel heavy hit | surge-alloy | 562.5 | 2200 | 0.26 | 37.5 | air+ground | 00-data |
| COMBAT.TURRET.210 malign | S | endgame barrage / blanket suppression | liquid/special | see main text | 2400 | - | 51.2 | air+ground | 00-data |

## Source anchors

- Mindustry-Source/core/src/mindustry/content/Blocks.java — the definitions, shootType and ammo tables of all 28 turrets
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 — shots defaults to 1
- Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414 — estimateDPS (the panel convention)
- 00-data/turret_shots.json — the source-derived shots/pattern table (which jar reflection cannot provide)

## Measurements and counterexamples

- Looking only at single-target DPS leads to the conclusion "breach at 2437.5 is the strongest", but breach on carbide fires 7.5 shots/s × 2 items = 15 items/s, which a single full-speed conveyor (11 items/s) cannot feed at all; with supply cut off it is no different from a 300-item turret. [src: 00-data/turrets.json + 00-data/blocks.json]
- The reverse example: wave's 0-armor DPS is 0 (water deals no damage), yet it is the only turret that can put out fires and knock units back, and its value in burning/melee waves cannot be expressed in DPS.

## Common misconceptions

- "the pricier the stronger": foreshadow costs 2700 items for 405 single-target DPS; spectre gives 685.7 DPS for 1875 items. What the extra money buys is range and armor piercing, not numbers. [src: 00-data/turrets.json]
- "the conventions can be mixed": older tables mixed "per-shot damage" with "per-shot damage × shots", so duo's 27 and salvo's 31 in the same table were not comparable. This knowledge base recomputes everything with the convention above; the old numbers are void.

## See also

- [[COMBAT.TURRET.001]] turret mechanics (reload / coolant / overheat / target layer)
- [[COMBAT.NUMBERS.001]] the three DPS formulas and the three-layer conventions
- [[COMBAT.TURRET.101]] duo
- [[COMBAT.TURRET.102]] scatter
- [[COMBAT.TURRET.103]] scorch
- [[COMBAT.TURRET.104]] hail
- [[COMBAT.TURRET.105]] wave
- [[COMBAT.TURRET.106]] lancer
- [[COMBAT.TURRET.107]] arc
- [[COMBAT.TURRET.108]] parallax
- [[COMBAT.TURRET.109]] swarmer
- [[COMBAT.TURRET.110]] salvo
- [[COMBAT.TURRET.111]] segment
- [[COMBAT.TURRET.112]] tsunami
- [[COMBAT.TURRET.113]] fuse
- [[COMBAT.TURRET.114]] ripple
- [[COMBAT.TURRET.115]] cyclone
- [[COMBAT.TURRET.116]] foreshadow
- [[COMBAT.TURRET.117]] spectre
- [[COMBAT.TURRET.118]] meltdown
- [[COMBAT.TURRET.201]] breach
- [[COMBAT.TURRET.202]] diffuse
- [[COMBAT.TURRET.203]] sublimate
- [[COMBAT.TURRET.204]] titan
- [[COMBAT.TURRET.205]] disperse
- [[COMBAT.TURRET.206]] afflict
- [[COMBAT.TURRET.207]] lustre
- [[COMBAT.TURRET.208]] scathe
- [[COMBAT.TURRET.209]] smite
- [[COMBAT.TURRET.210]] malign
