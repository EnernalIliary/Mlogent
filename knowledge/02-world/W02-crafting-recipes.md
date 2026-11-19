---
id: WORLD.CRAFTING.001
title: Recipes and crafting
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/production/GenericCrafter.java:40-77"
  - "Mindustry-Source/core/src/mindustry/world/blocks/production/GenericCrafter.java:203-316"
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:1209-1211, 1933-1947, 2004-2009"
  - "Mindustry-Source/core/src/mindustry/world/consumers/ConsumeItems.java:44-53"
  - "Mindustry-Source/core/src/mindustry/world/consumers/ConsumeLiquid.java:36-52"
  - "Mindustry-Source/core/src/mindustry/game/Schematic.java:126-132"
  - "MBO/gamedata/v160.7/gamedata.json (jar 反射，33 个带 recipe 的方块)"
data: [00-data/blocks.json]
depends: [WORLD.BLOCKS.001]
tags: [recipes, craftTime, crafters, ConsumeItems, ConsumeLiquid, schematics, efficiency]
tokens: 1454
---

## In one sentence

A recipe is assembled from three things: the **input consumers** (ConsumeItems / ConsumeLiquid / ConsumePower / ConsumeCoolant), **craftTime** (how many tick one full cycle takes), and the **outputs** (outputItems / outputLiquids); their dimensions differ — items are "deducted once per completed craft", liquids and power are "deducted once per tick", so any rate conversion must settle this unit boundary first.

## Rules / formulas

### 1. Unit boundaries of the three quantities (the most common mistake)

| Field | Unit | When deducted/given | Conversion |
|---|---|---|---|
| `ConsumeItems.amount` / `outputItems.amount` | items / **craft** | at the instant of completion (`trigger()`) | items/s = amount × 60 / craftTime |
| `ConsumeLiquid.amount` / `outputLiquids.amount` | liquid / **tick** | continuously, every tick | per second = amount × 60 |
| `ConsumePower.usage` | power / **tick** | continuously, every tick | per second = usage × 60 |
| `ConsumeCoolant.amount` | liquid / tick | continuously, every tick | same as liquid |
| `craftTime` | **tick** (1 tick = 1/60 s) | progress accumulation | period = craftTime/60 s; rate = 60/craftTime per second |

`ConsumeLiquid.update()` runs `liquids.remove(liquid, amount * build.edelta() * multiplier)` (every tick), while `ConsumeItems.trigger()` runs `items.remove(Math.round(amount * multiplier))` (once per craft) — two entirely different paths in the source, not a documentation slip [src: ConsumeLiquid.java:37-38, ConsumeItems.java:44-48].

### 2. Progress advance

```
progress += getProgressIncrease(craftTime)      // 每 tick
getProgressIncrease(baseTime) = 1f / baseTime * edelta()
edelta() = efficiency * delta()                 // delta()≈1（60 UPS 归一化）
progress >= 1f  ->  craft(): consume(); 逐个 offload(outputItems); progress %= 1f
```

So **at 100% efficiency one cycle takes exactly craftTime tick**; at 50% efficiency it takes 2×craftTime tick.

`getProgressIncrease` also throttles on "remaining output-liquid capacity": as the output liquid nears full, progress deliberately slows so inputs are not wasted [src: GenericCrafter.java:266-285].

### 3. Who decides efficiency

`efficiency` is the minimum over all **non-optional** consumers [src: BuildingComp.java:1975-1992]:

- `ConsumeItems.efficiency()` = `items.has(need) ? 1 : 0` (present ⇒ full, with no proportional scaling) [src: ConsumeItems.java:51-53]
- `ConsumeLiquid.efficiency()` = `min(current stock / (amount*edelta*mult), 1)` (a liquid can run "half full") [src: ConsumeLiquid.java:42-47]
- `ConsumePower.efficiency()` = the grid's supply/demand ratio (see `WORLD.POWER.001`)

A liquid consumer drags the whole machine's efficiency down while "half full", whereas an item consumer only flips between 0 and 1 — which explains why a factory short of ore stops dead while a factory short of water crawls along.

### 4. Stall conditions (shouldConsume)

`GenericCrafterBuild.shouldConsume()` returns false in the following cases, and the whole factory then neither consumes nor advances progress [src: GenericCrafter.java:203-232]:

1. any `outputItems` has reached `itemCapacity` inside the machine (the product is jammed);
2. any `outputLiquids` is full **and** that output has neither `dumpExtraLiquid` nor `ignoreLiquidFullness` set;
3. `enabled == false` (switched off by a logic processor) or `efficiency == 0`.

Mind the order: **outputs jam first, inputs come second**. A factory with full inputs and a jammed output is not "idle", it is "stuck" — the conveyor back-pressure stops everything upstream too (see the back-pressure section of `WORLD.LOGISTICS.001`).

### 5. Factories vs crafters

Vanilla has **no** block type called "factory"; that is player slang. By `baseClass`, the 33 blocks carrying a `recipe` fall into 5 classes:

| baseClass | Count | Examples | Difference |
|---|---|---|---|
| `GenericCrafter` | 17 | graphite-press, silicon-smelter, phase-weaver | basic crafting, no extra bonus |
| `HeatCrafter` | 5 | carbide-crucible, cyanogen-synthesizer | needs heat, faster the hotter it is (see `WORLD.HEAT.001`) |
| `HeatProducer` | 6 | oxidation-chamber, electric-heater, heat-reactor | the product is heat itself (`heatOutput`), no item output |
| `AttributeCrafter` | 3 | cultivator, vent-condenser, silicon-crucible | efficiency scales with the number of floor attributes |
| `Separator` | 2 | separator, disassembler | picks one output **at random** from a liquid/waste |

What players call a "small factory" = 2×2 no-power or low-power crafters such as `graphite-press`/`kiln`/`silicon-smelter`; a "big factory" = multi-input, power-hungry crafters such as `plastanium-compressor`/`surge-smelter`. The difference lies only in input count and power draw; mechanically there is no second rule set.

### 6. What a schematic contains

`Schematic.Stile` has only 4 fields: `Block block; int x, y; Object config; byte rotation` [src: Schematic.java:126-132]. So a schematic / copy-paste:

- **saves**: block type, relative coordinates, config (such as an unloader's target or a logic processor's code), rotation;
- **does not save**: stock (`items`), liquids (`liquids`), progress (`progress`, `warmup`), heat, stored power;
- **cost**: `Schematic.requirements()` sums each block's `requirements` and deducts them from the core/stock on paste; `Schematic.powerConsumption()` sums `block.consPower.usage`, likewise per tick.

So copying a "factory already full of ore" yields only an empty shell — the most common disappointment when copying factories.

## Numbers

The table below comes from the `recipe` data reflected out of the v160.7 jar (for the same-source fields see the `recipe` subtree of `00-data/blocks.json#id=<name>`). Rates use the 60 UPS conversion: **items ×60/craftTime, liquids ×60, power ×60**.

| Block | craftTime (tick) | per second | Item input (per craft) | Liquid input (per tick) | Output | Power/tick | Power/s |
|---|---|---|---|---|---|---|---|
| graphite-press | 90 | 0.667 | coal 2 | none | graphite 1 (0.667/s) | none | 0 |
| silicon-smelter | 40 | 1.5 | coal 1 + sand 2 | none | silicon 1 (1.5/s) | 0.5 | 30 |
| kiln | 30 | 2.0 | lead 1 + sand 1 | none | metaglass 1 (2/s) | 0.6 | 36 |
| pulverizer | 40 | 1.5 | scrap 1 | none | sand 1 (1.5/s) | 0.5 | 30 |
| multi-press | 30 | 2.0 | coal 3 | water 0.1 (6/s) | graphite 2 (4/s) | 1.8 | 108 |
| plastanium-compressor | 60 | 1.0 | titanium 2 | oil 0.25 (15/s) | plastanium 1 (1/s) | 3.0 | 180 |
| phase-weaver | 120 | 0.5 | thorium 4 + sand 10 | none | phase-fabric 1 (0.5/s) | 5.0 | 300 |
| surge-smelter | 75 | 0.8 | copper 3 + lead 4 + titanium 2 + silicon 3 | none | surge-alloy 1 (0.8/s) | 4.0 | 240 |
| cryofluid-mixer | 120 | 0.5 | titanium 1 | water 0.2 (12/s) | cryofluid 0.2 (12/s) | 1.0 | 60 |
| electrolyzer | 10 | 6.0 | none | water 0.1667 (10/s) | ozone 0.0667 (4/s) + hydrogen 0.1 (6/s) | 1.0 | 60 |
| carbide-crucible | 33.75 | 1.778 | tungsten 2 + graphite 3 | none | carbide 1 (1.778/s) | 2.0 | 120 |
| separator | 35 | 1.714 | none | slag 0.0667 (4/s) | one at random: copper 5 / lead 3 / graphite 2 / titanium 2 (weights) | 1.1 | 66 |

Supplementary counts (the same reflection pass, all 447 blocks):

- **33** blocks carry a `recipe`; the `craftTime` distribution (value × count): 80×6, 120×5, 30×4, 90×2, 40×2, 20×2, 10×2, and 60/75/35/15/50/45/100/480/600/33.75 once each — 17 distinct values covering 33 blocks in total.
- Smallest `craftTime = 10` (melter, electrolyzer), largest `= 600` (heat-reactor, a HeatProducer).
- Consumer-type counts: `ConsumePower` 104 blocks, `ConsumeLiquid` 60, `ConsumeItems` 45, `ConsumeCoolant` 16, `ConsumeItemDynamic` 11, `ConsumeLiquids` / `ConsumeLiquidsDynamic` / `ConsumePayloadDynamic` 3 each, `ConsumeItemFlammable` / `ConsumeItemExplode` / `ConsumePowerCondition` 2 each, `ConsumeItemRadioactive` / `ConsumePowerDynamic` 1 each.
- The electrolyzer passes a mass-conservation self-check: 10/s water in, 4/s ozone + 6/s hydrogen = 10/s out (a 1:1 decomposition).

## Source anchors

- `GenericCrafter.java:40` `public float craftTime = 80f;` —— the default is 80 tick (≈1.33 s), so most factories turn a little more than one cycle per second.
- `GenericCrafter.java:45` `warmupSpeed = 0.019f` —— visual warm-up only, unrelated to throughput.
- `GenericCrafter.java:66` `stats.timePeriod = craftTime` —— the UI uses craftTime to convert "per craft" into "/second".
- `GenericCrafter.java:73` `StatValues.items(craftTime, outputItems)` —— items are converted per craftTime.
- `GenericCrafter.java:77` `StatValues.liquids(1f, outputLiquids)` —— liquids use **1f** as the time basis and then multiply internally by `60/timePeriod` (`StatValues.java:141`), i.e. "amount is per tick".
- `GenericCrafter.java:236-264` `GenericCrafterBuild.updateTile()`: progress accumulation plus output liquid given continuously at `getProgressIncrease(1f)`.
- `GenericCrafter.java:301-316` `craft()`: `consume()` → `offload()` for each `outputItems` → `progress %= 1f`.
- `BuildingComp.java:1209-1211` `getProgressIncrease(baseTime) = 1f / baseTime * edelta()`.
- `BuildingComp.java:1933-1935` `edelta() = efficiency * delta()`; `1928-1930` `delta() = Time.delta * timeScale`.
- `BuildingComp.java:2004-2009` consumer updates are gated by `if(update && efficiency > 0)`.
- `ConsumeItems.java:44-48` / `ConsumeLiquid.java:37-38` the two consumption paths (per craft vs per tick).
- `Schematic.java:126-132` a schematic's `Stile` stores only `block/x/y/config/rotation`.

## Measurements and counter-examples

**Counter-example 1 (craftTime is -1 everywhere in the old table)**: in the old `data/game/*.json`, `craftTime` is `-1` for all 447 blocks — a placeholder from an export script that never reached the reflected field. In the v160.7 jar the **count of -1 is 0** and the real range is 10–600. Anything that reads -1 from the old table must be treated as "field missing", never as "completes instantly". **The defect was fixed in 2026-11**: `tools/dev/dump_game.py` now reads `b.craftTime` directly — the 33 blocks have real values, and the other 414 blocks (conveyors, turrets, walls, floors, …) do not carry the field on their class at all, so they record `null` (not 0, not -1). This is listed in the known-errors section of `VERSION.md`.

**Counter-example 2 (the derived field `recipe.outputLiquidsPerSecond` is wrong)**: gamedata.json has `cryofluid-mixer.outputLiquidsPerSecond = 0.1`, `melter = 1.2`, `electrolyzer = ozone 0.4 + hydrogen 0.6`. It applies the formula `amount / craftTime * 60` (a per-craft conversion), whereas the source at `GenericCrafter.java:243` adds `output.amount * inc` every tick, so the correct value is `amount × 60`: cryofluid 12/s, slag 12/s, ozone 4/s + hydrogen 6/s. Mass conservation settles it at once: the electrolyzer takes 10/s of water in while the derived field's products sum to only 1.0/s, which violates the 1:1 decomposition; the source reading of 4+6=10/s is the right one. **This derived field cannot be taken at face value.**

**Counter-example 3 (changing craftTime does not change liquid consumption proportionally)**: `multi-press` currently has `craftTime=30` and `water 0.1/tick` (6/s). Change it to 60 and item consumption halves (coal falls from 2 craft/s × 3 = 6/s to 1 craft/s × 3 = 3/s, graphite from 4/s to 2/s), but **water stays at 6/s**, because `ConsumeLiquid.update()` deducts every tick, independent of progress. Mixed-recipe factories (items + liquids) change their ratio when you change the speed — the classic trap when reproducing or rebalancing a build.

**Counter-example 4 (craftTime need not be an integer)**: `carbide-crucible` has `craftTime = 33.75` and `cyclesPerSecond = 1.777778`. Any assumption that "craftTime must be an integer number of ticks" breaks here; the UI shows it as 1.78/s.

**Counter-example 5 (a random-output crafter has no static output rate)**: `separator`'s `recipe.resultsSemantics` says outright "one random result per craft, weighted by amount"; the output is one of copper5/lead3/graphite2/titanium2 picked at random (**the amount given is that kind's total, not a probability**). Its gamedata record has neither `outputItems` nor `outputItemsPerSecond` — reading it through `outputItems` gives an empty array and the false conclusion "it produces nothing".

## Common misconceptions

1. **"craftTime is in seconds"** → it is tick. `graphite-press`'s 90 is not 90 s but 1.5 s per cycle (this mistake understates throughput by 60×).
2. **"outputLiquids is given once per craft too"** → it is given continuously every tick. So liquid throughput = `amount × 60`, independent of craftTime (see counter-example 2).
3. **"the usage unit is /s"** → it is /tick. `phase-weaver`'s 5 is 5/tick = 300/s, not 5/s. The "power use" column of the old quick-reference sheet (docs/游戏速查/方块配方.md, deleted 2026-11-17) held per-tick values while labelled /s; the trap is recorded in `VERSION.md`.
   To reverse-look-up "who consumes item X", do not copy by hand: reverse-join `consumers[].items[].item` in `00-data/blocks.json`.
4. **"no power only slows it down, materials are still deducted"** → items are deducted only when `craft()` completes, so efficiency 0 means no completion and no item deduction; liquid consumers, however, are gated by `BuildingComp.java:2005` and deduct only when `efficiency > 0` — when output fullness throttles efficiency you get the waste of "progress slows while liquids are still deducted in full".
5. **"a schematic carries the factory's stock and progress"** → `Schematic.Stile` has only the four fields block/x/y/config/rotation; progress and stock do not enter a schematic (see "What a schematic contains" above).
6. **"factories and crafters are two kinds of block"** → vanilla has only these implementation classes — `GenericCrafter`/`HeatCrafter`/`AttributeCrafter`/`HeatProducer`/`Separator` — and the player slang implies no mechanical difference.

## Related

- `WORLD.BLOCKS.001` (size and layout: a factory's footprint decides where conveyors can connect)
- `WORLD.POWER.001` (the full conversion between `ConsumePower`, usage and usagePerSecond)
- `WORLD.LIQUIDS.001` (liquid properties and jamming for `ConsumeLiquid`)
- `WORLD.HEAT.001` (the `HeatCrafter` bonus formula)
- `WORLD.LOGISTICS.001` (back-pressure from a jammed output)
- Data tables: `00-data/blocks.json` (the `recipe` subtree), `00-data/formulas.json`
- Source: `world/blocks/production/GenericCrafter.java`, `world/consumers/*.java`, `game/Schematic.java`, `entities/comp/BuildingComp.java`
