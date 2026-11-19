---
id: WORLD.DRILLING.001
title: Drills and resources - drill tiers, the hardness penalty, ore coverage
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src:
  - Mindustry-Source/core/src/mindustry/world/blocks/production/Drill.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/BeamDrill.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/BurstDrill.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/WallCrafter.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/SolidPump.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/Fracker.java
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/OreBlock.java
  - Mindustry-Source/core/src/mindustry/content/Blocks.java
  - Mindustry-Source/core/src/mindustry/world/Tile.java
data:
  - 00-data/blocks.json#id=mechanical-drill
  - 00-data/blocks.json#id=laser-drill
  - 00-data/blocks.json#id=impact-drill
  - 00-data/blocks.json#id=water-extractor
  - 00-data/blocks.json#id=plasma-bore
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001, WORLD.LIQUIDS.001]
tags: [drill, tier, hardness, ore, drillTime, laser-drill, drill-bit, ore-layer, extraction]
tokens: 2010
---

# Drills and resources - drill tiers, the hardness penalty, ore coverage

## One line

Vanilla extraction has four entirely different implementations (`Drill` covers tiles, `BeamDrill` cuts walls, `BurstDrill` hits the centre, `WallCrafter` eats sand-attribute walls); every output rate passes two gates, `tier` (whether it can mine at all) and `hardness` (how slowly it mines), and the "X items/s" shown in the UI is almost always an optimistic figure that ignores hardness.

## Rules / formulas

### 1. Four mining blocks + two liquid blocks

| Class | Criterion | Representative blocks | Key fields |
|---|---|---|---|
| `Drill` | the ore of `tile.drop()` inside the tiles the drill covers | mechanical / pneumatic / laser / blast-drill | `tier`, `drillTime`, `hardnessDrillMultiplier` |
| `BeamDrill` | the first solid wall within `range` tiles in front | plasma-bore, large-plasma-bore | `range`, `tier` |
| `BurstDrill` | the same coverage count as Drill, but everything bursts out at once | impact-drill, eruption-drill | `hardnessDrillMultiplier = 0` |
| `WallCrafter` | sum of the `Attribute.sand` of walls within `size` tiles in front | cliff-crusher, large-cliff-crusher | `attribute`, `output` |
| `SolidPump` | a non-liquid tile under itself + terrain attributes | water-extractor | `pumpAmount`, `baseEfficiency` |
| `Fracker` | terrain `Attribute.oil` + eats sand | oil-extractor | `pumpAmount`, `itemUseTime` |

All six share one precondition: `envEnabled |= Env.space` (Drill.java:86, BeamDrill.java:76), with mechanical-drill as the exception - it writes `envEnabled ^= Env.space` (Blocks.java:2872), so **it cannot be placed on space maps**.

### 2. Drill formula: hardness is added to the time, not multiplied into the speed

The mining time of `Drill` is

```
getDrillTime(item) = (drillTime + hardnessDrillMultiplier * item.hardness) / drillMultipliers.get(item, 1f)
```

(Drill.java:170-172). The default is `hardnessDrillMultiplier = 50f` (Drill.java:28), so hardness-0 ore (sand/scrap/graphite) equals bare `drillTime`, while thorium (hardness 4) on a mechanical-drill waits an extra `50 × 4 = 200` ticks. Note that the denominator is the **per-ore multiplier table** `drillMultipliers` (Drill.java:66); vanilla only writes `2f` for beryllium, on impact-drill/eruption-drill (Blocks.java:3084, Blocks.java:3115).

### 3. Coverage: output scales linearly with the number of "dominant ore tiles"

`DrillBuild.onProximityUpdate` calls `countOre(tile)`, walking `tile.getLinkedTilesAs(this, tempTiles)` (the whole size×size area) and counting how often each `tile.drop()` appears (Drill.java:198-229):

1. Sort by `lowPriority` first (`Boolean.compare(!item1.lowPriority, !item2.lowPriority)`, Drill.java:216) - lowPriority ore is pushed to the **front**;
2. then by covered tiles ascending, then by id ascending;
3. take `itemArray.peek()` (the last entry) = prefer non-lowPriority ore with the largest coverage.

The result lands in two fields, `dominantItem` / `dominantItems` (Drill.java:243-244, Drill.java:275-277). The output rate multiplies `dominantItems` directly:

```
progress += delta() * dominantItems * speed * warmup;
lastDrillSpeed = (speed * dominantItems * warmup) / delay;
```

(Drill.java:303-305). So a 3×3 laser drill covering 9 titanium tiles runs at 9x the one-tile rate; covering 4 tiles gives only 4x - **a multi-tile drill must sit wholly on ore**.

tools/block_sizes.json and data/game/blocks.json only give size; coverage depends on the map, so any "a drill produces X/s" statement must declare its coverage assumption.

### 4. tier is a hardness gate, not "higher tier mines faster"

`canMine` decides three things only (Drill.java:231-235): the tile's `tile.drop() != null`, `drops.hardness <= tier`, and not being in `blockedItems`. The hardness table (the `hardness` field of items, reflected from the v160.7 jar):

| Item | hardness | Drill needed (minimum tier) |
|---|---|---|
| processed goods other than sand / scrap / graphite / coal | 0 | any (every drill with tier >= 1 can mine, but in practice only ore has a drop) |
| copper, lead | 1 | mechanical-drill (`tier = 2`) |
| coal | 2 | mechanical-drill (tier 2, **can** mine) |
| titanium, beryllium | 3 | pneumatic-drill (`tier = 3`) |
| thorium | 4 | laser-drill (`tier = 4`) |
| tungsten | 5 | blast-drill / large-plasma-bore (tier 5) |

tier itself **grants no speed bonus**: pneumatic-drill is faster than mechanical-drill because `drillTime` drops from 600 to 400 (Blocks.java:2869, Blocks.java:2881), not because of the higher tier.

### 5. Liquid boost: 1.6 is a double multiply, the steady state is 2.56x

The upgrade path writes `liquidBoostIntensity = 1.6f` (Drill.java:38); in the actual code it enters **two** factors at once (Drill.java:301-305):

```
float speed = Mathf.lerp(1f, liquidBoostIntensity, optionalEfficiency) * efficiency;
warmup = Mathf.approachDelta(warmup, speed, warmupSpeed);
progress += delta() * dominantItems * speed * warmup;
```

`speed` is boosted to 1.6 and `warmup` approaches `speed`, also reaching 1.6; the product is **2.56x**. That is exactly what the official UI shows: `StatValues.speedBoosters(..., liquidBoostIntensity * liquidBoostIntensity, ...)` (Drill.java:188). blast-drill's 1.8 corresponds to 3.24x.

Boost liquids: mechanical 0.05/tick = 3/s water (Blocks.java:2875), pneumatic 3.5/60 = 3.5/s (Blocks.java:2884), laser 0.08/tick = 4.8/s (Blocks.java:2897), blast 0.1/tick = 6/s (Blocks.java:2918), plasma-bore hydrogen 0.25/60 = 0.25/s (Blocks.java:3050), impact-drill ozone 3/60 = 3/s (Blocks.java:3091). All are `.boost()` optional consumers, so running dry only returns to 1x instead of stopping.

### 6. BeamDrill: walls only, output by the number of faces

`BeamDrillBuild.updateFacing` fires one laser from each of the drill's **size edges**, each travelling up to `range` tiles along `Geometry.d4(rotation)` and stopping at the first solid tile (the same logic as `canPlaceOn`, BeamDrill.java:198-214). Output:

```
time += edelta() * multiplier;
if(time >= drillTime){ for(Tile tile : facing){ ... items.add(drop, 1); } time %= drillTime; }
```

(BeamDrill.java:246-262) - **one item per face per cycle**, so the maximum rate is `facingAmount × 60 / drillTime` with `facingAmount <= size`. getDrillTime here carries no hardness (BeamDrill.java:216-218).

The test is `tile.wallDrop()` (Tile.java:575-580): it returns a value only when `block.solid` and either the wall has its own `itemDrop` or `overlay.wallOre`, so what can be mined are "ore walls" (ore-wall-thorium etc.) rather than ordinary floor ore.

### 7. BurstDrill: the hardness penalty is zeroed, all coverage bursts at once

The constructor hard-codes `hardnessDrillMultiplier = 0f` (BurstDrill.java:39, comment "does not drill in the traditional sense") and overrides `getDrillTime` as `drillTime / drillMultipliers` (BurstDrill.java:53-55). Its progress does not multiply coverage, its **output** does:

```
progress += delta() * speed;
if(progress >= drillTime){ for(int i = 0; i < dominantItems; i++) offload(dominantItem); }
```

(BurstDrill.java:99, BurstDrill.java:106-109). So an impact-drill on full 4×4 coverage is "16 items every 720 ticks", averaging `16 × 60 / 720 = 1.333 items/s`, and that is **independent of ore hardness** (thorium also takes 720 ticks). The price is `blockedItem = Items.thorium` (Blocks.java:3081): tier 6 yet it cannot mine thorium.

### 8. WallCrafter: no ore, it eats the "sand attribute" of walls

`getEfficiency` walks the `size` tiles in front (not size×size), accumulating `other.block().attributes.get(attribute)` for every tile where `other.solid()` (WallCrafter.java:141-181). cliff-crusher / large-cliff-crusher set `attribute = Attribute.sand`, `output = Items.sand` (Blocks.java:3009-3010, 3023-3024).

Measured sand attribute (content/Blocks.java): dune-wall 2, sand-wall 2, yellow-stone-wall 1.5, red-stone-wall 1.5, beryllic-stone-wall 1.2, stone-wall 1, regolith-wall 1, rhyolite-wall 1, carbon-wall 0.7, ferric-stone-wall 0.5 (Blocks.java:597-675). Rate = `eff × 60 / drillTime`, with eff capped at size × the largest attribute.

### 9. Liquid extraction: SolidPump and Fracker

- **water-extractor (SolidPump)**: `pumpAmount = 0.11` (Blocks.java:2924), efficiency `fraction = validTiles + boost + attribute.env()` (SolidPump.java:124), where `boost = sumAttribute(Attribute.water)/size/size` and `validTiles = Σ baseEfficiency/size²` (SolidPump.java:153-159, baseEfficiency defaults to 1). On attribute-free floor fraction = 1 → **6.6 water/s**; a water-attribute floor can double that. It requires `!tile.floor().isLiquid` (SolidPump.java:80-82), so it cannot be built straight on a lake surface.
- **oil-extractor (Fracker)**: `pumpAmount = 0.25` (Blocks.java:2970), `baseEfficiency = 0`, `attribute = Attribute.oil` (Blocks.java:2973-2974), `itemUseTime = 60`, eats 1 sand per 60 ticks plus 3/tick power (Blocks.java:2977-2979), and only `dumpLiquid(result)` to its surroundings (Fracker.java:42). Output follows the same formula as `SolidPump`: **per second = `pumpAmount × 60 × Attribute.oil`**.
  Full darksand (`darksand` 1.5) = `0.25×60×1.5` = **22.5 oil/s**; only a floor with attribute 1.0 gives 15/s (the
  `60×pumpAmount` printed by the game UI is that optimistic value, the same class of trap as the drill UI). Attribute.oil floor values:
  `sand-floor` 0.7, `darksand` **1.5**, `salt` 0.3, `shale` 2.0 (content/Blocks.java).
  Ratio check: the coal centrifuge eats 6 oil/s, so **3 centrifuges (18 oil/s) need only 1 oil extractor**; starting from 15/s you would compute 2.
- **Measured live (v160.7, 2026-11-09)**: `darksand` 1.5 → **22.502 oil/s**, `sand-floor` 0.7 → **10.502**, `shale` 2.0 → **30.002** (0.0% off the formula; the `container delta` and `lastPump×60` readings agree, `boost` measured 1.5); in the same run `coal-centrifuge` ate 5.999 oil/s and made 2.045 coal/s. Probe `MBO/spikes/sim/oil_floor_probe.py`, write-up (`MBO/docs/24-石油钻井地板属性实测.md`).
- **Counter-case**: `Fracker`'s `envRequired` contains `Env.groundOil` (1<<5), and a world produced by `loadGenerator` has no such bit in `rules.env`, so `allowUpdate()` is false, the block never updates at all and `efficiency` stays 0 (it looks like zero output); set `rules.env |= 32|64` before placing one.

### 10. Ore layers (oreBlocks): 16 id → item mappings

gamedata's `environment.oreBlocks` lists every mineable ore layer (MBO/gamedata/v160.7/gamedata.json#environment.oreBlocks):

`ore-copper→copper`, `ore-lead→lead`, `ore-scrap→scrap`, `ore-coal→coal`, `ore-titanium→titanium`, `ore-thorium→thorium`, `ore-beryllium→beryllium`, `ore-tungsten→tungsten`, `ore-crystal-thorium→thorium`, `sand-floor→sand`, `darksand→sand`, plus four **ore walls** `ore-wall-thorium`, `ore-wall-beryllium`, `ore-wall-graphite`, `ore-wall-tungsten` and `graphitic-wall→graphite`.

Ore layers come in two kinds (OreBlock.java:15 onward, the `wallOre` field): floor ore with `wallOre = false` (mined by Drill) and ore walls with `wallOre = true` (mined by BeamDrill).

## Numbers

**Table 1: parameters of the six drill / extraction blocks (v160.7 jar reflection + v159.3 source lines)**

| Block | Class | size | tier | drillTime | hardnessDrillMultiplier | Liquid boost | itemCap | liquidCap | Power (/tick → /s) |
|---|---|---|---|---|---|---|---|---|---|
| mechanical-drill | Drill | 2 | 2 | 600 | 50 | 1.6 (water 0.05) | 10 | 30 | 0 |
| pneumatic-drill | Drill | 2 | 3 | 400 | 50 | 1.6 (water 0.0583) | 10 | 35 | 0 |
| laser-drill | Drill | 3 | 4 | 280 | 50 | 1.6 (water 0.08) | 10 | 48 | 1.1 → 66 |
| blast-drill | Drill | 4 | 5 | 280 | 50 | 1.8 (water 0.1) | 20 | 60 | 3 → 180 |
| impact-drill | BurstDrill | 4 | 6 | 720 | **0** | 1.75 (ozone 0.05) | 40 | 100 | 2.667 → 160 |
| eruption-drill | BurstDrill | 5 | 7 | 281.25 | **0** | 2.0 (cyanogen 0.0125) | 60 | 40 | 6 → 360 |
| plasma-bore | BeamDrill | 2 | 3 | 160 | — (not involved) | 2.5 (hydrogen 0.00417) | 10 | 10 | 0.15 → 9 |
| large-plasma-bore | BeamDrill | 3 | 5 | 100 | — (not involved) | 2.5 (nitrogen 0.05) | 20 | 30 | 0.8 → 48 |
| cliff-crusher | WallCrafter | 2 | — | 110 | — | 1.6 | 10 | 10 | 0.1833 → 11 |
| large-cliff-crusher | WallCrafter | 3 | — | 48 | — | 1.6 (+ graphite item 1.6) | 20 | 10 | 1 → 60 |

Sources: mechanical-drill Blocks.java:2866-2876; pneumatic Blocks.java:2878-2885; laser Blocks.java:2887-2898; blast Blocks.java:2900-2919; impact Blocks.java:3071-3092; eruption Blocks.java:3094-3122; plasma-bore Blocks.java:3039-3051; large-plasma-bore Blocks.java:3053-3069; the cliff pair Blocks.java:3003-3037.

**Table 2: measured output rates (full coverage, no boost liquid; rate = covered tiles × 60 / getDrillTime)**

| Drill | Ore (hardness) | getDrillTime | Coverage | Items/s |
|---|---|---|---|---|
| mechanical-drill | copper(1) | 650 | 4 | **0.369** |
| mechanical-drill | coal(2) | 700 | 4 | 0.343 |
| mechanical-drill | copper(1) + water | 650 | 4 | **0.945** (×2.56) |
| pneumatic-drill | titanium(3) | 550 | 4 | 0.436 |
| laser-drill | titanium(3) | 430 | 9 | **1.256** |
| laser-drill | thorium(4) | 480 | 9 | 1.125 |
| blast-drill | thorium(4) | 480 | 16 | **2.0** |
| blast-drill | copper(1) | 330 | 16 | 2.909 |
| impact-drill | copper(1) | 720 (no hardness term) | 16 | 1.333 |
| impact-drill | beryllium(3) | 720 ÷ 2 | 16 | **2.667** |
| eruption-drill | copper(1) | 281.25 | 25 | 5.333 |
| eruption-drill | beryllium(3) | 281.25 ÷ 2 | 25 | **10.67** |
| plasma-bore | ore wall | 160 | 2 faces | 0.75 |
| large-plasma-bore | ore wall | 100 | 3 faces | **1.8** |
| cliff-crusher | sand-attribute wall | 110 | eff ≤ 2 | ≤ **1.0909** |
| large-cliff-crusher | sand-attribute wall | 48 | eff ≤ 3 | ≤ **3.75** |

**Table 4: liquid extraction blocks**

| Block | pumpAmount | Efficiency source | Full-efficiency output | Power |
|---|---|---|---|---|
| water-extractor | 0.11 | validTiles(≤1) + mean water attribute | 6.6/s (attribute-free floor) | 1.5/tick = 90/s |
| oil-extractor | 0.25 | Attribute.oil (baseEfficiency 0) | **22.5/s** at the 1.5 darksand attribute (`0.25×60×1.5`; attribute 1.0 is 15/s, which is the optimistic value the UI prints); **22.502/s measured live** (sand 10.502, shale 30.002) | 3/tick = 180/s |

## Source anchors

- `Drill.java:28` `hardnessDrillMultiplier = 50f`; `Drill.java:34-36` `tier` and the `drillTime = 300` default; `Drill.java:38` `liquidBoostIntensity = 1.6f`; `Drill.java:40` `warmupSpeed = 0.015f`.
- `Drill.java:170-172` the hardness-additive formula of `getDrillTime(item)`.
- `Drill.java:198-229` `countOre` and the dominant-ore ordering (the lowPriority compare at `:216`); `Drill.java:223-228` taking `peek()`.
- `Drill.java:231-235` `canMine`: `drops.hardness <= tier && !blockedItems.contains(drops)`.
- `Drill.java:287-325` `updateTile`: `speed = lerp(1, liquidBoostIntensity, optionalEfficiency) * efficiency` (:301), `progress += delta() * dominantItems * speed * warmup` (:305), batch output `:315-321`.
- `Drill.java:181-190` stats only give `60f / drillTime * size * size` (**no hardness, no real coverage**), and the boost display uses `liquidBoostIntensity * liquidBoostIntensity` (:188).
- `BeamDrill.java:40-44` `range = 5` / `tier = 1` / `optionalBoostIntensity = 2.5`; `BeamDrill.java:198-214` `canPlaceOn` finds the first solid tile per face; `BeamDrill.java:246-262` one item per face tile per cycle.
- `BurstDrill.java:39` `hardnessDrillMultiplier = 0f`; `BurstDrill.java:53-55` the `getDrillTime` override; `BurstDrill.java:99-109` progress does not multiply coverage while output multiplies `dominantItems`.
- `WallCrafter.java:141-181` `getEfficiency` takes only the `size` tiles in front and accumulates `attributes.get(attribute)`; `WallCrafter.java:213-215` `time += edelta() * eff` emits 1 item per `drillTime`.
- `SolidPump.java:153-159` `boost = sumAttribute(...)/size/size`, `validTiles += baseEfficiency/(size*size)`; `SolidPump.java:124-129` `maxPump = min(liquidCapacity - typeLiquid(), pumpAmount * delta * fraction * efficiency)`.
- `Tile.java:571-580` `drop()` takes `overlay.itemDrop` or `floor.itemDrop`; `wallDrop()` only counts for `block.solid`.
- `Block.java:438` `dumpTime = 5` (try a `dump` into a neighbouring block every 5 ticks, which triggers `offload` downstream).
- `content/Blocks.java:597-675` the `Attribute.sand` value of each wall (dune-wall 2, sand-wall 2, carbon-wall 0.7, ferric-stone-wall 0.5).

## Measurements and counter-examples

**Counter-example 1 (the UI's items/s is optimistic)**: `Drill.setStats` writes `60f / drillTime * size * size` (Drill.java:181), which for laser-drill is `60/280*9 = 1.929 items/s`; but the real rate over 9 copper tiles is `9 × 60 / (280 + 50×1) = 1.636`, and for thorium `9 × 60 / 480 = 1.125`. **Same block, UI 1.93 vs actual 1.13, a 71% gap**. gamedata's `baseRateItemsPerSecond` is that optimistic value (laser-drill 1.928571) and must not be used as output.

**Counter-example 2 (gamedata's BeamDrill rate is off by 2x)**: plasma-bore's `baseRateItemsPerSecond = 1.5`, but `BeamDrill.setStats` itself writes `60f / drillTime * size` (BeamDrill.java:127) = `60/160×2 = 0.75` items/s, because each face emits only 1 item per cycle (BeamDrill.java:253-260). The data table's 1.5 used `size²`, which is wrong for BeamDrill.

**Counter-example 3 (impact-drill cannot mine thorium)**: tier 6 is already >= thorium's hardness 4, but `blockedItem = Items.thorium` (Blocks.java:3081) puts it into `blockedItems` (Drill.java:93-95) and `canMine` returns false outright (Drill.java:234). The advanced drill being unable to mine one basic ore is **deliberate balance**, not a bug.

**Counter-example 4 (water boost is not x1.6)**: a mechanical drill with water goes from 0.369 to 0.945 items/s (×2.56), because `speed` and `warmup` each multiply by 1.6 (Drill.java:301-305), and the UI prints 2.56 too (Drill.java:188). Planning a line at ×1.6 undercounts by 60%.

**Counter-example 5 (ore walls need a laser drill)**: placing a laser-drill on `ore-wall-thorium` shows "requires a higher tier", because `Drill.canMine` requires `!tile.block().isStatic()` (Drill.java:232) and wall tiles are excluded outright. Ore walls can only be mined through the `wallDrop()` path (Tile.java:575-580), that is by BeamDrill.

**Counter-example 6 (BurstDrill ignores hardness)**: impact-drill's `getDrillTime` is 720 for both copper and tungsten (BurstDrill.java:53-55 never looks at hardness), so on low-hardness ore it loses to blast-drill (330 vs 720) and only pays off as ore gets harder.

## Common misconceptions

1. **"A higher tier mines faster"** - tier only gates hardness (Drill.java:234); speed comes from `drillTime` and coverage.
2. **"A drill placed beside ore still mines it"** - `countOre` only scans `getLinkedTilesAs`, i.e. the size×size the block itself covers (Drill.java:205); the edge does not count.
3. **"With sand and copper stacked, the drill mines copper first because it is worth more"** - the ordering key is `lowPriority` and coverage count, not value (Drill.java:215-221); sand's `lowPriority = 1` is what pushes it back.
4. **"More boost liquid, more speed"** - `optionalEfficiency` only interpolates between "has liquid" and "no liquid" (Drill.java:301); once full it does not stack further.
5. **"A Water Extractor is fastest built directly on water"** - it requires `!floor.isLiquid` (SolidPump.java:80-82), so on a water surface it simply cannot be placed.
6. **"cliff-crusher mines ore"** - it eats `Attribute.sand` (Blocks.java:3009), unrelated to ore layers; what it mines is wall.

## Related

- W01 blocks and multiblock anchors (size×size and the tile set of `getLinkedTilesAs`)
- W02 recipes and crafting (where drill output enters the smelting chain)
- W04 liquids (boost liquid enters through `liquidCapacity`)
- W06 logistics (`offload` / `dumpTime = 5` pushes output into neighbouring blocks)
- W10 storage (a drill stalls when itemCapacity is full; `shouldConsume` only checks capacity)
