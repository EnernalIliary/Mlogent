---
id: CAMP.DIFFICULTY.001
title: Difficulty conversion card — how the triple becomes health, numbers, cost and wave interval
domain: camp
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/game/Difficulty.java:5-21"
  - "Mindustry-Source/core/src/mindustry/game/CampaignRules.java:39-42"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:85-87,111,302-304,374-384"
  - "Mindustry-Source/core/src/mindustry/ai/WaveSpawner.java:77-82"
  - "Mindustry-Source/core/src/mindustry/game/Waves.java:258-260,299-302,436-441"
  - "Mindustry-Source/core/src/mindustry/maps/planet/SerpuloPlanetGenerator.java:730"
data: [00-data/formulas.json, 00-data/constants_rules_difficulty_drill_heat.json]
depends: [CAMP.WAVES.001, CAMP.SPAWN.001]
tags: [difficulty, campaign, triple, enemy health, spawn multiplier, cost]
tokens: 616
---

## In one line

Difficulty is three floats `(enemyHealthMultiplier, enemySpawnMultiplier, waveTimeMultiplier)`; `CampaignRules` writes them into 4 rule fields **of the enemy team**, so "difficulty" means enemy health ×N, enemy numbers ×M and wave time ×T — and **contains no damage multiplier whatsoever**.

## Rules / formulas

```
Difficulty 枚举 = (enemyHealthMultiplier, enemySpawnMultiplier, waveTimeMultiplier)   [Difficulty.java:5-10]

CampaignRules.apply 时写入 waveTeam：                                                  [CampaignRules.java:39-42]
  team.blockHealthMultiplier    = enemyHealthMultiplier
  team.unitHealthMultiplier     = enemyHealthMultiplier
  team.unitCostMultiplier       = 1 / enemySpawnMultiplier
  team.unitBuildSpeedMultiplier = enemySpawnMultiplier

有效血量 = type.health × max(rules.unitHealthMultiplier × team.unitHealthMultiplier, 1e-6)   [Rules.java:302-304]
每波数量 = round(getSpawned(w) × enemySpawnMultiplier)   （非 boss 组）                          [WaveSpawner.java:80-81]
          = (int)(getSpawned(w) × enemySpawnMultiplier) （boss 组，向下取整，1.5×1 不会变 2 个）
波次间隔 = waveSpacing × waveTimeMultiplier                                                [Logic.java:322]
压力指数 P = enemyHealthMultiplier × enemySpawnMultiplier / waveTimeMultiplier
```

Generated (random) maps add two more layers of difficulty curve:

```
generate(difficulty) → generate(pow(difficulty, 1.12), ...)     [Waves.java:258-260]
开局整体前移 shift = max((int)(difficulty*14 - 5), 0) 波          [Waves.java:436-441]
  d=0.4 → shift 0；d=0.6 → shift 3；d=1.0 → shift 9
```

## Numbers

| Difficulty | enemy health | number multiplier | wave-time multiplier | enemy cost | enemy build speed | pressure index P | source |
|---|---|---|---|---|---|---|---|
| casual | 0.5 | 0.5 | 2.0 | ×2.0 | ×0.5 | 0.125 | [v160.7] |
| easy | 1.0 | 0.75 | 1.5 | ×1.33 | ×0.75 | 0.500 | [v160.7] |
| normal | 1.0 | 1.0 | 1.0 | ×1.0 | ×1.0 | 1.000 | [v160.7] |
| hard | 1.25 | 1.5 | 0.8 | ×0.67 | ×1.5 | 2.344 | [v160.7] |
| eradication | 1.5 | 2.0 | 0.6 | ×0.5 | ×2.0 | 5.000 | [v160.7] |

The triple is [verified v160.7] (checked value by value through jar reflection: 0.5/0.5/2.0, 1.0/0.75/1.5, 1.0/1.0/1.0, 1.25/1.5/0.8, 1.5/2.0/0.6); the cost and build-speed columns follow from the reciprocal and the direct-multiply formulas above, and the pressure index is the three-term arithmetic result for P.

| Same map, same unit | casual | normal | eradication | source |
|---|---|---|---|---|
| An enemy whose unit type health = 200 | 100 | 200 | 300 | substituted into Rules.java:302-304 |
| Actual spawns for a non-boss group with getSpawned = 6 | 3 | 6 | 12 | substituted into WaveSpawner.java:80-81 |
| Time to reach wave 30 | 7440 s | 3720 s | 2232 s | T(N) from CAMP.WAVES.001 |
| attackMode victory wave winWave | — | 10+5×max(d×10,1) | — | SerpuloPlanetGenerator.java:730 |

## Source anchors

- Difficulty.java:5-10 the five triples; :15-21 the fields and constructor order (enemyHealth / enemySpawn / waveTime).
- CampaignRules.java:39-42 the triple → 4 team fields (blockHealth / unitHealth / the reciprocal of unitCost / unitBuildSpeed).
- Rules.java:85,87,111 global multipliers default to 1; :374-384 the three same-named fields of TeamRules; :302-304 `unitHealth(team)` takes the product with a floor of 1e-6.
- WaveSpawner.java:77-82 multiplies the count by difficulty and then `Mathf.round` (bosses use `(int)`).
- Waves.java:258-260 `pow(difficulty,1.12)`; :299-302 the generated map's cap=150, shieldsPerWave=20+d×30; :436-441 shift [src: Waves.java:258-302,436-441].
- SerpuloPlanetGenerator.java:730 attack mode `winWave = 10 + 5×max(d×10,1)`.

## Tests and counterexamples

**Counterexample 1: assuming higher difficulty means harder-hitting enemies.** The difficulty triple has no damage term, and `rules.unitDamageMultiplier` is not rewritten by CampaignRules either (the global default is 1 [verified v160.7]) — under eradication an enemy bullet has the same base damage as on casual; what changes is health (÷1.5) and the number on the field at once (×4).

**Counterexample 2: assuming enemySpawnMultiplier only affects spawning.** It also makes enemy AI units **cheaper (unitCost ÷ M) and quicker to build (unitBuildSpeed × M)**; so on hard the enemy production line actually builds at 1.5× the normal rate.

**Counterexample 3: assuming hard is only "25% more health".** Numbers are also ×1.5 and the interval ×0.8 → P = 1.25×1.5/0.8 ≈ 2.34, so the effective pressure is 2.34× normal, not 1.25×.

**Counterexample 4: assuming difficulty directly changes a SpawnGroup's shields.** In fixed levels the shields come from `shields/shieldScaling`; only randomly generated maps have `shieldsPerWave = 20 + difficulty×30`, which does contain a difficulty term (Waves.java:301) — do not mix the two.

**Recomputable**: take a unit with `type.health=200` and a non-boss group with `getSpawned=6` → on normal 6 spawn with 200 health each; on eradication `round(12)=12` spawn with `200×1.5=300` health each, so the on-screen effective health pool goes 1200 → 3600 (3×); compounding the 0.6× wave interval gives a pressure index of 5.0 (substitutions in 00-data/formulas.json DATA.FORMULA.012/013).

## Common misconceptions

- "Difficulty affects damage" → it does not; it only touches enemy health, enemy numbers, enemy build speed/cost and wave time.
- "casual just spawns fewer enemies" → health is halved too and the wave interval is doubled (P=0.125, one eighth of normal) [v160.7].
- "Difficulty is changed directly in Rules" → campaign writes team fields through `CampaignRules`; editing Rules in sandbox does not move this triple.
- "Difficulty changes the wave cap" → the wave cap is set by `winWave`/the map and is unrelated to difficulty (attack mode is the exception, see SerpuloPlanetGenerator.java:730).

## Related

- [[CAMP.WAVES.001]] wave timing and the full derivation of T(N)
- [[CAMP.SPAWN.001]] SpawnGroup's actual arguments and the per-wave count/shield formulas
- DATA.FORMULA.013 the difficulty triple and its derived fields
- DATA.FORMULA.012 wave health scaling (conclusion: it does not grow with the wave number)
