---
id: WORLD.TERRAIN.001
title: Terrain and environment - the three-layer floor / ore / wall structure, movement multipliers, and the land-versus-water test
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src:
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/Floor.java:24-70 [src: Floor.java:24-70]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/OreBlock.java:15-41 [src: OreBlock.java:15-41]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/StaticWall.java:26-37 [src: StaticWall.java:26-37]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/Prop.java:16-22 [src: Prop.java:16-22]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/ShallowLiquid.java:21-31 [src: ShallowLiquid.java:21-31]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/SteamVent.java:19-47 [src: SteamVent.java:19-47]
  - Mindustry-Source/core/src/mindustry/world/Block.java:112-160 [src: Block.java:112-160]
  - Mindustry-Source/core/src/mindustry/world/Tile.java:571-580 [src: Tile.java:571-580]
  - Mindustry-Source/core/src/mindustry/type/Attribute.java:8-20 [src: Attribute.java:8-20]
data:
  - 00-data/blocks.json#id=deep-water
  - 00-data/blocks.json#id=shallow-water
  - 00-data/blocks.json#id=molten-slag
  - 00-data/blocks.json#id=stone-wall
  - 00-data/blocks.json#id=ore-copper
depends: [WORLD.BLOCKS.001, WORLD.DRILLING.001, WORLD.LIQUIDS.001]
tags: [terrain, floor, ore, wall, deep-water, shallow-water, liquid-floor, movement-multiplier]
tokens: 1394
---

## One line

Terrain is not one "layer" but three stacked layers: **floor floor** (decides movement speed, whether the tile is liquid, and whether a pump can draw from it), **ore overlay overlay** (a covering layer such as ore-copper that only affects extraction), and **wall wall / decoration prop** (a solid block that occupies the tile and blocks movement and building). Each carries its own set of numbers, and conflating them is the most common error in this domain.

## Rules / formulas

### 1. Three stacked layers: floor / overlay / wall

- One Tile holds a **floor**, an **overlay** (which is where ore lives) and a **block** (wall, building) at the same time. Ore classes are `OreBlock extends OverlayFloor` (OreBlock.java:15), and construction sets `this.itemDrop = ore`, `variants = 3`, `useColor = true` (OreBlock.java:20-23); it does not change the floor, only this tile's drop. [src: OreBlock.java:15]
- A wall is a real Block: `StaticWall extends Prop` (StaticWall.java:16), with `solid = true` in the constructor (:29); the floor of the same tile still exists, simply covered by the wall. [src: StaticWall.java:16]
- So "this tile is ore" and "this tile is water" can hold at once: an ore layer can sit on a water floor (e.g. shallow-water-plus-ore such as darksand-tainted-water). Extraction reads the overlay (Tile.java:571-580 drop() takes `overlay().itemDrop` first, then falls back to `floor().itemDrop`). [src: Tile.java:571-580]

### 2. The nine terrain fields of Floor and their defaults

Floor.java:24-70 gives each one its semantics and default; only four affect feel directly: [src: Floor.java:24-70]

| Field | Default | Effect | Source |
|---|---|---|---|
| speedMultiplier | 1 | unit movement speed multiplier | Floor.java:28 |
| dragMultiplier | 1 | unit drag multiplier (ice <1 is more slippery) | Floor.java:30 |
| damageTaken | 0 | damage per tick (all vanilla floors are 0) | Floor.java:32 |
| drownTime | 0 | drowning ticks, 0 = never drowns | Floor.java:34 |
| liquidDrop | null | the liquid a pump can draw | Floor.java:48 |
| liquidMultiplier | 1 | pump output multiplier (deep water 1.5) | Floor.java:50 |
| isLiquid | false | whether this is a liquid floor | Floor.java:52 |
| overlayAlpha | 0.65 | liquid overlay opacity | Floor.java:54 |
| shallow | false | shallow-water flag (used by map generation) | Floor.java:58 |
| status / statusDuration | none / 60 | the status applied when stepping on it and its duration | Floor.java:44-46 |
| oreDefault / oreScale / oreThreshold | false / 24 / 0.828 | whether ore spawns by default, plus ore noise scale and threshold | Floor.java:62-64 |

### 3. The land-versus-water test: depth is drownTime, shallowness is the class

- **Deep water** is an ordinary `Floor` plus `isLiquid = true` and `drownTime = 200`; **shallow water** is the `ShallowLiquid` subclass, whose `set()` hard-codes `isLiquid = true` and `shallow = true` and inherits status and liquidDrop from the liquid floor (ShallowLiquid.java:21-31). [src: ShallowLiquid.java:21-31]
- The same water liquid can have two floors: deep-water drowns units (drown 200 ticks ≈ 3.3 s), shallow-water never drowns (drownTime 0), and their movement speeds are 0.2 and 0.5 respectively [src: gamedata.json#deep-water / #shallow-water].
- Pump output is decided by the floor: `liquidMultiplier` is 1.5 on deep water and 1.0 on shallow [src: gamedata.json#deep-water], then multiplied by Pump's pumpAmount (WORLD.LIQUIDS.001).

### 4. Walls and decorations: three kinds of "unbuildable" terrain with completely different behaviour

| Class | Represented by | solid | breakable | unitMoveBreakable | Semantics |
|---|---|---|---|---|---|
| StaticWall | stone-wall / dune-wall | true | false | false | permanent terrain wall, cannot be drilled or pushed down |
| Prop | stone and rock decorations | true (per instance) | true | true | can be smashed by units, can be removed to free the tile |
| TreeBlock | trees | true | true | true | same as above, plus `clipSize = 90` and `customShadow = true` (TreeBlock.java:16-18) |

The deciding code is in the constructors, not in the data table: the `Prop` constructor sets `breakable = true`, `alwaysReplace = true`, `instantDeconstruct = true`, `unitMoveBreakable = true` (Prop.java:16-19); the `StaticWall` constructor overrides the first three back to false and adds `solid = true`, `instantBuild = true`, `placeableLiquid = true`, `ignoreBuildDarkness = true` (StaticWall.java:28-37). [src: Prop.java:16-19]

### 5. Hazard floors: the damage is not in damageTaken

- Every vanilla floor has `damageTaken` 0 [src: gamedata.json#molten-slag]; lava's damage goes through the **status status** instead: molten-slag has `statusDuration = 240`, speed 0.19, drown 230 [src: gamedata.json#molten-slag]; tar is likewise 0.19 / 230 / 240 [src: gamedata.json#tar].
- Heat goes through **Attribute.heat**: hotrock 0.5, magmarock 0.75, molten-slag 0.85 (the Attribute table in WORLD.HEAT.001); thermal-generator generates power directly from the floor's heat attribute.
- Glow is `lightRadius`: hotrock 30, magmarock 50, molten-slag 40 [src: gamedata.json#hotrock]; it only affects visual lighting and enters no production formula.

### 6. Terrain affects building in exactly two ways

- **Solid tiles cannot hold blocks**: walls and decorations occupy the tile, and placement legality is judged by `Build.validPlace` (WORLD.BLOCKS.001 gives the seven-step flow); a solid wall blocks movement and building alike.
- **Liquid floors are buildable by default**: every liquid floor (deep-water, molten-slag, tar, arkycite-floor) has `placeableLiquid = true` in the data table [src: gamedata.json#deep-water], so "you can build blocks on water, you just cannot walk there" is design intent, not a bug.
- Multiblock terrain is the exception: `SteamVent extends Floor` (SteamVent.java:19) assembles a 3×3 vent from 9 relative offsets and carries `BlockFlag.steamVent` (:46) - it is one tile of floor logic and nine tiles of visuals, so do not count it as 9 independent tiles. [src: SteamVent.java:19]

## Numbers

### Table A | 14 representative floors (v160.7 reflection, ids verifiable in 00-data/blocks.json)

| floor | Class | speedMultiplier | dragMultiplier | drownTime | isLiquid | liquid / liquidMultiplier | statusDuration | Source |
|---|---|---|---|---|---|---|---|---|
| deep-water | Floor | 0.2 | 1 | 200 | true | water / 1.5 | 120 | gamedata.json#deep-water |
| shallow-water | Floor | 0.5 | 1 | 0 | true | water / 1 | 90 | gamedata.json#shallow-water |
| tainted-water | Floor | 0.5 | 1 | 0 | true | water / 1 | 90 | gamedata.json#tainted-water |
| deep-tainted-water | Floor | 0.18 | 1 | 200 | true | water / 1.5 | 140 | gamedata.json#deep-tainted-water |
| darksand-water | ShallowLiquid | 0.8 | 1 | 0 | true | water / 1 | 50 | gamedata.json#darksand-water |
| darksand-tainted-water | ShallowLiquid | 0.75 | 1 | 0 | true | water / 1 | 60 | gamedata.json#darksand-tainted-water |
| molten-slag | Floor | 0.19 | 1 | 230 | true | slag / 1 | 240 | gamedata.json#molten-slag |
| tar | Floor | 0.19 | 1 | 230 | true | oil / 1 | 240 | gamedata.json#tar |
| arkycite-floor | Floor | 0.3 | 1 | 200 | true | arkycite / 1 | 60 | gamedata.json#arkycite-floor |
| mud | Floor | 0.6 | 1 | 0 | false | — | 30 | gamedata.json#mud |
| ice | Floor | 0.9 | 0.35 | 0 | false | — | 60 | gamedata.json#ice |
| red-ice | Floor | 0.9 | 0.4 | 0 | false | — | 60 | gamedata.json#red-ice |
| sand-floor / stone / metal-floor / snow | Floor | 1 | 1 | 0 | false | — | 60 | gamedata.json#sand-floor |

### Table B | movement effects at a glance

| Effect | Value | Source |
|---|---|---|
| Deep water is slowest | speed ×0.2, drowns after 200 ticks ≈ 3.3 s | deep-water; Floor.java:28, :34 |
| Ice does not slow you but is slippery | speed ×0.9, drag ×0.35 (lower is more slippery) | ice; Floor.java:30 |
| Slag / tar are stickiest | speed ×0.19, drown after 230 ticks ≈ 3.8 s | molten-slag, tar |
| Shallow water only slows | speed ×0.5–0.8, drown 0 | shallow-water, darksand-water; ShallowLiquid.java:25-30 |
| Deep water pump bonus | pump output ×1.5 | deep-water; Floor.java:50 |

## Source anchors

1. `Floor.java:24-70` - every terrain field and default (speedMultiplier :28, dragMultiplier :30, damageTaken :32, drownTime :34, liquidDrop :48, liquidMultiplier :50, isLiquid :52, overlayAlpha :54, shallow :58, oreScale :64). [src: Floor.java:24-70]
2. `OreBlock.java:15-23` - the ore layer extends OverlayFloor, `itemDrop = ore`, `variants = 3`. [src: OreBlock.java:15-23]
3. `ShallowLiquid.java:21-31` - `set(liquid, floor)` inherits isLiquid / shallow / status / liquidDrop. [src: ShallowLiquid.java:21-31]
4. `StaticWall.java:26-37` - the wall's seven switches: solid / breakable=false / instantBuild / placeableLiquid / ignoreBuildDarkness. [src: StaticWall.java:26-37]
5. `Prop.java:16-19` - the decoration's four switches: breakable / alwaysReplace / instantDeconstruct / unitMoveBreakable. [src: Prop.java:16-19]
6. `TreeBlock.java:16-18` - a tree is solid + clipSize 90 + customShadow. [src: TreeBlock.java:16-18]
7. `SteamVent.java:19-46` - the 9 offsets of the 3×3 vent and BlockFlag.steamVent. [src: SteamVent.java:19-46]
8. `Tile.java:571-580` - drop() reads overlay().itemDrop first and floor().itemDrop second, which is the evidence that "the ore layer does not change the floor". [src: Tile.java:571-580]
9. `Attribute.java:8-20` - the seven environment attributes heat / spores / water / oil / light / sand / steam. [src: Attribute.java:8-20]
10. `Floor.java:62-64` - oreDefault / oreScale 24 / oreThreshold 0.828, the map generation parameters. [src: Floor.java:62-64]

## Measurements and counter-examples

**Counter-example 1 | "Deep water = shallow water × 2" does not hold.** deep-water moves at 0.2 and shallow at 0.5, a ratio of 2.5; but drowning is 0 versus 200 ticks, shallow never drowns at all [src: gamedata.json#shallow-water] - these are not two settings of the same parameter.

**Counter-example 2 | Lava damage does not go through damageTaken.** Across the whole tree `damageTaken = 0` (the Floor.java:32 default, which nobody overrides); losing health on molten-slag comes from its status (statusDuration 240) and Attribute.heat 0.85, not from a per-tick damage field. [src: Floor.java:32]

**Counter-example 3 | A wall is not a decoration.** StaticWall overrides all of Prop's `breakable = true / unitMoveBreakable = true` back to false (StaticWall.java:28), so stone-wall can never be dug away; while a small rock (Prop) on the same map shatters as soon as a unit walks over it - both are called "terrain obstacle", and they behave differently. [src: StaticWall.java:28]

**Counter-example 4 | Ice is not a faster floor.** ice has speedMultiplier 0.9 (slower than stone's 1.0); what it really changes is dragMultiplier 0.35 [src: gamedata.json#ice], and the "slippery" feel comes from drag, not speed.

**Counter-example 5 | Liquid floors are buildable by default.** Many people assume you cannot build on water, yet deep-water / tar / molten-slag all have `placeableLiquid = true` [src: gamedata.json#deep-water], and building a pump on water is a standard opening.

**Positive measurement | Deep-water pump rate.** A 2×2 rotary-pump on deep-water gives `0.2 × 4 tiles × 1.5 = 1.2/tick = 72/s`, while the same pump on shallow water gives only 48/s (the pump table in WORLD.LIQUIDS.001 × liquidMultiplier 1.5 vs 1.0).

## Common misconceptions

1. **"The floor is the terrain and a wall is just another block"** - the three layers stack: an ore layer can sit on any floor, and a wall can stand on water; the three sets of data never replace each other.
2. **"Ore is a special tile type"** - ore is an **overlay**; it does not change floor movement or water properties, only the extraction output through `drop()` (Tile.java:571-580). [src: Tile.java:571-580]
3. **"damageTaken is the source of lava damage"** - that field is constantly 0 on vanilla floors and the damage comes from the status; changing damageTaken in a map does nothing to vanilla lava.
4. **"Shallow water drowns small units"** - ShallowLiquid's drownTime is 0 (inherited from the Floor default, see :34), so shallow water only slows you down.
5. **"lightRadius lights the surroundings and affects production"** - it only affects visuals; production looks at Attribute (heat 0.85 and so on) [src: gamedata.json#molten-slag], and the two are different fields.
6. **"A vent is 9 tiles"** - SteamVent is one Floor plus 9 render offsets (SteamVent.java:20-31) and logically occupies a single tile. [src: SteamVent.java:20-31]

## Related

- WORLD.BLOCKS.001 - multiblock placement legality; terrain's constraints on building live here.
- WORLD.DRILLING.001 - extraction rules for ore layers and hardness, the 16 oreBlocks entries.
- WORLD.LIQUIDS.001 - how pumps multiply the floor's liquidMultiplier.
- WORLD.HEAT.001 - the floor heat attribute and thermal-generator.
- 00-data/blocks.json - every static field of floors / walls / ore (drownTime, dragMultiplier, buildVisibility).
