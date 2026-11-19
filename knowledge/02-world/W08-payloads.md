---
id: WORLD.PAYLOAD.001
title: Payloads - the whole-block haul chain for block and unit payloads (conveyor / router / constructor / deconstructor / mass driver)
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src:
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/Payload.java:16-52 [src: Payload.java:16-52]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadConveyor.java:21-283 [src: PayloadConveyor.java:21-283]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadRouter.java:54-143 [src: PayloadRouter.java:54-143]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadBlock.java:18-118 [src: PayloadBlock.java:18-118]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/BuildPayload.java:71-88 [src: BuildPayload.java:71-88]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/UnitPayload.java:98-101 [src: UnitPayload.java:98-101]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadMassDriver.java:24-86 [src: PayloadMassDriver.java:24-86]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadDeconstructor.java:20-203 [src: PayloadDeconstructor.java:20-203]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadLoader.java:22-81 [src: PayloadLoader.java:22-81]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/Constructor.java:21-56 [src: Constructor.java:21-56]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/BlockProducer.java:22-120 [src: BlockProducer.java:22-120]
  - Mindustry-Source/core/src/mindustry/world/Block.java:60-65 [src: Block.java:60-65]
  - Mindustry-Source/core/src/mindustry/world/Block.java:1432-1449 [src: Block.java:1432-1449]
data:
  - 00-data/blocks.json#id=payload-conveyor
  - 00-data/blocks.json#id=payload-router
  - 00-data/blocks.json#id=payload-mass-driver
  - 00-data/blocks.json#id=constructor
  - 00-data/blocks.json#id=deconstructor
  - 00-data/blocks.json#id=payload-loader
  - 00-data/blocks.json#id=payload-unloader
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001, WORLD.STORAGE.001]
tags: [payload, payload-conveyor, payload-router, constructor, deconstructor, payload-mass-driver, unit-payload, block-payload]
tokens: 2105
---

## One line

A payload is "a block or unit hauled whole", and it travels on a channel completely separate from item logistics: payload conveyors push it one tile per tick beat, payload routers sort by what is being carried, constructors build blocks on the spot, deconstructors tear blocks back into items, payload mass drivers fling payloads across the map - and every capacity is measured in edge tiles (tilesize = 8 px) rather than in item kinds.

## Rules / formulas

### 1. Payloads are two object kinds, and sizes are given in pixels

- `Payload.java:16` defines `payloadUnit = 0`, `Payload.java:17` defines `payloadBlock = 1`; the first byte in saves and network streams is one of these two values (BuildPayload.java:97 writes `write.b(payloadBlock)`, UnitPayload.java:72 writes `write.b(payloadUnit)`). [src: Payload.java:16]
- A block payload's size comes from the block: `BuildPayload.size()` returns `build.block.size * tilesize` (BuildPayload.java:86-88), so a 3-tile block is 24 px. [src: BuildPayload.java:86-88]
- A unit payload's size comes from its hitbox: `UnitPayload.size()` returns `unit.hitSize` (UnitPayload.java:98-101), unrelated to block tiles. [src: UnitPayload.java:98-101]
- The whole system has exactly one size test: `Payload.java:50-52` `public boolean fits(float s){ return size() / tilesize <= s; }`, and the source comment says it outright: "3 is the max for a standard 3x3 conveyor". [src: Payload.java:50-52]

### 2. Payload capacity is an edge length in tiles, not tiles squared

payloadLimit = 3 (PayloadConveyor.java:21) means "the largest payload that can pass has an edge of 3 tiles", which is 3 × 8 = 24 px in pixels. So: [src: PayloadConveyor.java:21]

- constructor is a 3-tile (24 px) block and gets through; large-constructor is 5 tiles (40 px) and does not.
- Units are judged by hitSize: only a unit with hitSize ≤ 24 px qualifies, regardless of its unit tier (PayloadConveyor.java:87 tests `unit.hitSize / tilesize <= payloadLimit` once more before pushing a unit). [src: PayloadConveyor.java:87]

Payload block parameters (verifiable in 00-data/blocks.json): payload-conveyor and payload-router are both 3 tiles, health 360, buildVisibility shown, solid false, underBullets true; the two reinforced versions are 3 tiles, health 800.

### 3. Conveyor beat: moveTime 45 ticks pushes one tile

- PayloadConveyor.java:21 `public float moveTime = 45f, moveForce = 201f, payloadLimit = 3f;` [src: PayloadConveyor.java:21]
- `updateTile` (PayloadConveyor.java:137-188) computes `float progress = time() % moveTime;` and `int curStep = (int)(time() / moveTime);`; only on the tick curStep increments does it try to hand the payload downstream; when downstream is empty and unblocked, `item.dump()` drops it on the ground. [src: PayloadConveyor.java:137-188]
- Rate: 60 / 45 = 1.333 payloads/s (one tile per 45 ticks). reinforced-payload-conveyor has moveTime 35 ⇒ 60 / 35 = 1.714 payloads/s.
- The accept window is very narrow: acceptPayload (PayloadConveyor.java:279-283) requires `item == null && payload.fits(payloadLimit) && (source == this || (enabled && progress <= 5f))` [src: PayloadConveyor.java:279-283], so upstream may deliver only in the first 5 ticks of a cycle, 5 / 45 ≈ 11% of the 45 ticks; miss it and the payload waits for the next round. That is the direct cause of "payload conveyors lose throughput on long chains".
- Docking ( :107-121 ): a neighbour of the same size docks directly, a larger neighbour is aligned by centre tile; `blocked` (:128) is defined as `next.solid && !next.outputsPayload && !next.acceptsPayload || next.payloadCheck(rotation)`.

### 4. Payload router: sorts by content, not by direction

- `PayloadRouter extends PayloadConveyor` (PayloadRouter.java:23); the constructor sets `outputFacing = false` (:32), `configurable = true`, `clearOnDoubleTap = true`, and the config type is Block or UnitType (:36-38). [src: PayloadRouter.java:23]
- Sortable set `canSort(Block b)` (PayloadRouter.java:54-56): `b.isVisible() && b.size <= size && !(b instanceof CoreBlock) && !state.rules.isBanned(b) && b.environmentBuildable()` ⇒ a 3-tile router can only sort 1-3 tile blocks; core blocks always pass through but can never be a sort target. [src: PayloadRouter.java:54-56]
- `pickNext()` (:76-103): on a sorted hit it walks straight along recDir; on a miss it rotates through the 4 directions, skipping recDir (:87-89), until it finds a neighbour that can `acceptPayload`, trying at most 4 times (:98).
- Once logic has steered it, `controlTime = 60f * 6f = 360` ticks pass before it auto-steers again (:112), i.e. 6 seconds without fighting for the wheel.

### 5. Constructors: two generations, speed written on buildSpeed

- `Constructor` (Constructor.java:21-22) defaults `minBlockSize = 1`, `maxBlockSize = 2`; `canProduce` (:54-56) requires the block to be isVisible, its edge within [minBlockSize, maxBlockSize], not a CoreBlock, not banned by rules.isBanned(b), environmentBuildable(), and the filter empty or matching. [src: Constructor.java:21-22]
- v160.7 actuals: constructor buildSpeed 0.6, minBlockSize 1, maxBlockSize 2; large-constructor buildSpeed 5, minBlockSize 3, maxBlockSize 4 ([v159.3] source gives large-constructor buildSpeed 0.75, v160.7 raises it to 5, a 6.7x gap).
- `BlockProducer` (BlockProducer.java:22 `buildSpeed = 0.4f` default): the blueprint-style factory, collecting recipe.requirements × rules.buildCostMultiplier rounded up through `ConsumeItemDynamic` (:39-55), with `getMaximumAccepted = demand × 2` (:88-93), `progress += buildSpeed * edelta()` per tick, producing one BuildPayload per full recipe.buildTime (:107-120). [src: BlockProducer.java:22]
- The built block's own `buildTime` is a cost function: `Block.java:1432-1449` `buildTime = Σ(amount × item.cost) × buildCostMultiplier`; with no requirements it is 20f (Block.java:360 default -1f means not yet computed). [src: Block.java:1432-1449]
- Worked example 1: container needs titanium 100, item.cost 1 (Items.java:51) ⇒ buildTime = 100 ticks; constructor buildSpeed 0.6 ⇒ 100 / 0.6 = 166.7 ticks ≈ 2.78 s. [src: Items.java:51]
- Worked example 2: vault needs titanium 250 + thorium 125, thorium cost 1.1 (Items.java:58) ⇒ 250 × 1 + 125 × 1.1 = 387.5 ticks; but vault is a 3-tile block and the small constructor has maxBlockSize 2, so it cannot build one - you must switch to large-constructor. [src: Items.java:58]
- Worked example 3: core-shard has buildCostMultiplier 2 ⇒ buildTime = (1000 × 0.5 + 800 × 0.7) × 2 = 2120 ticks, which is also why "cores can only be built by the 5-tile large constructor" (besides buildCostMultiplier, maxBlockSize also blocks the 3-tile one).

### 6. Payload mass driver: charge and cooldown both sit in the cycle

- PayloadMassDriver.java:24-30 defaults `range = 100f`, `rotateSpeed = 5f`, `length = 89/8f`, `reload = 30f`, `chargeTime = 100f`, `maxPayloadSize = 3`. [src: PayloadMassDriver.java:24-30]
- The fire rate needs no extra derivation, it is written into stats: `stats.add(Stat.reload, 60f / (chargeTime + reload), StatUnit.perSecond)` (PayloadMassDriver.java:85) - charge time and cooldown both enter the cycle. [src: PayloadMassDriver.java:85]
- v160.7 actuals: payload-mass-driver range 700 px ([src: gamedata.json#payload-mass-driver]) (87.5 tiles), reload 45 ticks, chargeTime 70 ticks, maxPayloadSize 2.5 ⇒ 60 / (70 + 45) = 0.522 shots/s; large-payload-mass-driver range 2100 px (262.5 tiles), reload 130, chargeTime 100, maxPayloadSize 4 ⇒ 60 / 230 = 0.261 shots/s.
- The target point is stored as relative coordinates in a `Point2` (:70 comment "point2 is relative"); when placed, Drawf.dashCircle draws the range circle (:106), and the tile conversion again divides by tilesize (:86 `stats.add(Stat.shootRange, range / tilesize, StatUnit.blocks)`).

### 7. Loading and unloading: 8 items / 2 s, 40 liquid / s

- PayloadLoader.java:22-27: `loadTime = 2f`, `itemsLoaded = 8`, `liquidsLoaded = 40f`, `maxBlockSize = 3`, `maxPowerConsumption = 40f`, `loadPowerDynamic = true`. [src: PayloadLoader.java:22-27]
- Load beat: every `loadTime / efficiency` ticks it moves `itemsLoaded` items (PayloadUnloader.java:68-81 uses the same parameter set), 2 s = 120 ticks for 8 items ⇒ 4 items/s; liquid goes at `liquidsLoaded * edelta()`, i.e. 40 / s, and it requires the same liquid type or its own stock < 0.2 (:86-90). [src: PayloadUnloader.java:68-81]
- The loader's `outputsItems()` returns false (PayloadLoader.java:55-57; the unloader returns true, PayloadUnloader.java:23-25), so it never treats its 100 item slot as an output port; that 100 is only the transit buffer of the payload being loaded. [src: PayloadLoader.java:55-57]
- Once a payload is inside, `payloadSpeed = 0.7f` controls its slide animation speed within the block (PayloadBlock.java:18; in v160.7 every payload block has payloadRotateSpeed 3, the v159.3 source default is 5). [src: PayloadBlock.java:18]

### 8. Deconstructor: progress normalised by the deconstructed block's buildTime

- PayloadDeconstructor.java:20 `dumpRate = 4`; v160.7 actuals: small-deconstructor maxPayloadSize 3, deconstructSpeed 3, itemCapacity 100; deconstructor maxPayloadSize 4, deconstructSpeed 6, itemCapacity 320 ([v159.3] source base class PayloadDeconstructor.java:36 hard-codes itemCapacity = 100; 320 is the v160.7 version value, see gamedata raw).
- Progress formula (PayloadDeconstructor.java:142-155): `float shift = edelta() * deconstructSpeed / deconstructing.buildTime();` so total time = buildTime / deconstructSpeed ticks, proportional to the cost of the deconstructed block, **not a fixed number of seconds**. [src: PayloadDeconstructor.java:142-155]
- Refund (:158-160): `accum[i] += reqs[i].amount * (BuildPayload ? rules.buildCostMultiplier : rules.unitCost(team)) * realShift`, i.e. a proportional refund of the full cost; only whole units enter the inventory (:166-172), and when inventory reaches `itemCapacity` the whole machine pauses (:130-138 canProgress checks items.total() <= itemCapacity and all accum < 1).
- Before deconstructing, the block's liquid is splashed onto the ground: `perCell = stock / (block.size * block.size) * 2` per tile via Puddles.deposit (:148-152).

## Numbers

### Table A | 14 payload block actuals (v160.7 reflection, ids and health verifiable in 00-data/blocks.json)

| Block | edge tiles | health | Key parameters | Source |
|---|---|---|---|---|
| payload-conveyor | 3 | 360 | moveTime 45, payloadLimit 3, pushUnits true | PayloadConveyor.java:21 |
| reinforced-payload-conveyor | 3 | 800 | moveTime 35, payloadLimit 3 | gamedata raw |
| payload-router | 3 | 360 | moveTime 45, invert false, configurable | PayloadRouter.java:31-38 |
| reinforced-payload-router | 3 | 800 | moveTime 35 | gamedata raw |
| payload-mass-driver | 3 | 645 | range 700, reload 45, chargeTime 70, maxPayloadSize 2.5 | gamedata raw |
| large-payload-mass-driver | 5 | 2550 | range 2100, reload 130, chargeTime 100, maxPayloadSize 4 | gamedata raw |
| constructor | 3 | 860 | buildSpeed 0.6, minBlockSize 1, maxBlockSize 2 | Constructor.java:21-22 |
| large-constructor | 5 | 2500 | buildSpeed 5, minBlockSize 3, maxBlockSize 4 | gamedata raw |
| payload-loader | 3 | 645 | loadTime 2, itemsLoaded 8, liquidsLoaded 40, maxBlockSize 3 | PayloadLoader.java:22-27 |
| payload-unloader | 3 | 645 | loadTime 2, itemsLoaded 8, outputsItems true | PayloadUnloader.java:23-25 |
| small-deconstructor | 3 | 755 | maxPayloadSize 3, deconstructSpeed 3, itemCapacity 100 | gamedata raw |
| deconstructor | 5 | 3195 | maxPayloadSize 4, deconstructSpeed 6, itemCapacity 320 | gamedata raw |
| payload-source | 5 | 1000 | sandbox source, infinite payload supply | 00-data/blocks.json#id=payload-source |
| payload-void | 5 | 1000 | payloadSpeed 1.2, sandbox payload sink | 00-data/blocks.json#id=payload-void |

### Table B | rate conversion summary (1 tick = 1/60 s, all units per second) [src: Vars.java:135]

| Metric | Formula (source anchor) | Value |
|---|---|---|
| Payload conveyor throughput | 60 / moveTime (PayloadConveyor.java:137-188) | default 1.333 payloads/s; reinforced 1.714 payloads/s |
| Accept window share | 5 / moveTime (:279-283) | default 5 / 45 ≈ 11.1% |
| Mass driver fire rate | 60 / (chargeTime + reload) (PayloadMassDriver.java:85) | small 0.522 shots/s; large 0.261 shots/s |
| Loader item transfer | itemsLoaded / loadTime (PayloadLoader.java:22-27) | 8 / 2 = 4 items/s |
| Loader liquid transfer | liquidsLoaded (same line) | 40 liquid/s |
| Build duration | built block buildTime / constructor buildSpeed (Constructor.java:54-56, BlockProducer.java:107-120) | container 100 / 0.6 = 166.7 ticks |
| Deconstruct duration | deconstructed block buildTime / deconstructSpeed (PayloadDeconstructor.java:142-155) | proportional to cost, not a constant |
| Core cost | Σ(amount × item.cost) × buildCostMultiplier (Block.java:1432-1449) | core-shard 2120 ticks |

### Table C | unit payload capacity (UnitType.java:119 default 8, tilePayload 64, tilesize 8)

| Form | Source | payloadCapacity |
|---|---|---|
| default | UnitType.java:119 | 8 |
| (2 * 2) * tilePayload | UnitTypes.java:1424 | 256 |
| (3 * 3) * tilePayload | UnitTypes.java:1474 | 576 |
| (5.5 * 5.5) * tilePayload | UnitTypes.java:1547 | 1936 |
| sqr(4) * tilePayload | UnitTypes.java:4043 | 1024 |
| sqr(6) * tilePayload | UnitTypes.java:4148 | 2304 |
| payloadCapacity = 0 | UnitTypes.java:4575, :4605 | 0 (cannot be carried) |

## Source anchors

1. `Payload.java:16-17` - `payloadUnit = 0` and `payloadBlock = 1`, the payload type as the first byte of the save stream. [src: Payload.java:16-17]
2. `Payload.java:50-52` - `fits(float s)` is the only size gate; it returns `size() / tilesize <= s`. [src: Payload.java:50-52]
3. `BuildPayload.java:86-88` - block payload size = `build.block.size * tilesize`; compare `UnitPayload.java:98-101`, unit payload size = `unit.hitSize`. [src: BuildPayload.java:86-88]
4. `Block.java:60-65` - the three switches `outputsPayload` / `acceptsUnitPayloads` / `acceptsPayload` decide whether a block is a payload chain node. [src: Block.java:60-65]
5. `Block.java:1432-1449` - `buildTime = Σ(amount × item.cost) × buildCostMultiplier`, or 20f when there are no requirements. [src: Block.java:1432-1449]
6. `Block.java:360` - the `buildTime = -1f` default means "not computed", so never read -1 in a data table as a real build time. [src: Block.java:360]
7. `PayloadConveyor.java:21` - `moveTime = 45f`, `moveForce = 201f`, `payloadLimit = 3f`. [src: PayloadConveyor.java:21]
8. `PayloadConveyor.java:137-188` - the beat advance `curStep = (int)(time() / moveTime)` and the ground drop `item.dump()`. [src: PayloadConveyor.java:137-188]
9. `PayloadConveyor.java:279-283` - the `progress <= 5f` accept window of `acceptPayload`. [src: PayloadConveyor.java:279-283]
10. `PayloadConveyor.java:128` - `blocked` as the or of three items: solid neighbour, outputsPayload, acceptsPayload, payloadCheck. [src: PayloadConveyor.java:128]
11. `PayloadRouter.java:54-56` - the five conditions of `canSort(Block)`; `:76-103` the four-direction rotation of pickNext. [src: PayloadRouter.java:54-56]
12. `PayloadMassDriver.java:85-86` - fire rate `60f / (chargeTime + reload)` and range `range / tilesize`. [src: PayloadMassDriver.java:85-86]
13. `Constructor.java:21-22` and `:54-56` - minBlockSize / maxBlockSize and the five conditions of canProduce. [src: Constructor.java:21-22]
14. `BlockProducer.java:22` - `buildSpeed = 0.4f`; `:107-120` emits the BuildPayload. [src: BlockProducer.java:22]
15. `PayloadLoader.java:22-27` - loadTime 2 / itemsLoaded 8 / liquidsLoaded 40 / maxBlockSize 3. [src: PayloadLoader.java:22-27]
16. `PayloadDeconstructor.java:142-160` - `shift = edelta() * deconstructSpeed / buildTime` and the `accum` refund scaled by buildCostMultiplier. [src: PayloadDeconstructor.java:142-160]
17. `UnitType.java:119` - the `payloadCapacity = 8` default; `Vars.java:137` tilePayload = 64. [src: UnitType.java:119]

## Measurements and counter-examples

**Counter-example 1 | A payload conveyor is not an item conveyor.** In 00-data/blocks.json#id=payload-conveyor, `hasItems=false` and `itemCapacity=10`; that 10 is the field default from Block.java:75, not a usable item slot. The block only accepts payloads, and there is no entry point for stuffing items in. [src: Block.java:75]

**Counter-example 2 | Capacity is not "tiles squared".** payloadLimit 3 means a maximum edge of 3 tiles = 24 px, not room for 3 × 3 = 9 payloads; one 3-tile block fills the whole belt (Payload.java:50-52 divides rather than taking an area). Measured, a default payload conveyor at full load holds a constant 1.333 payloads/s regardless of whether the payload is 1 tile or 3 tiles. [src: Payload.java:50-52]

**Counter-example 3 | Chaining is not a lossless relay.** The accept window is only the first 5 ticks of the cycle (PayloadConveyor.java:279-283); upstream pushing a payload in while `progress > 5` is rejected and must wait for its own next 45-tick cycle; measured, two chained segments run clearly below the single-segment 1.333 payloads/s - it is "blocking by design". [src: PayloadConveyor.java:279-283]

**Counter-example 4 | Version drift becomes a 6.7x error.** large-constructor's buildSpeed is 0.75 in the [v159.3] source and 5 in v160.7 (gamedata raw reads back 5.0); estimating build time from the old value overestimates 5-tile construction by 6.7x.

**Counter-example 5 | deconstructor's 320 is not the base-class default.** The [v159.3] source writes `itemCapacity = 100` in the PayloadDeconstructor constructor (PayloadDeconstructor.java:36), while v160.7's deconstructor is 320 (gamedata raw); deriving "deconstructing a 5-tile block jams 3 times first" from 100 is wrong.

**Counter-example 6 | Mass driver range is in pixels.** PayloadMassDriver.java:86 does `range / tilesize` before showing tiles, so 700 px = 87.5 tiles; reading it directly as 700 tiles inflates it 8x. [src: PayloadMassDriver.java:86]

**Positive measurement | Loader rate on an empty payload.** A payload-loader at the default 100% efficiency moves 8 items in 120 ticks (2 s) ⇒ 4 items/s, and 40 / s for liquid; that is slightly below an item conveyor of the same size (conveyor 4.5 items/s, WORLD.LOGISTICS.001), but one load fills the whole inventory of a 3-tile block.

## Common misconceptions

1. **"Payload conveyors consume power"** - they do not: payload-conveyor has `hasPower=false` (00-data/blocks.json#id=payload-conveyor); the power consumers are the loaders, constructors, deconstructors and mass drivers.
2. **"A payload router is a splitter whose direction you set by hand"** - the router's config picks the **content** (a block or unit type, PayloadRouter.java:36-38); the direction is whatever pickNext rotates to among the 4 directions, not a player setting. [src: PayloadRouter.java:36-38]
3. **"A constructor can build any block"** - it is bounded by the five canProduce conditions (Constructor.java:54-56); core blocks are never buildable because of `!(b instanceof CoreBlock)`, and the 3-tile small constructor cannot build 3-tile-plus structures such as vault either (maxBlockSize 2). [src: Constructor.java:54-56]
4. **"Deconstructing takes a fixed number of seconds"** - progress is `edelta() * deconstructSpeed / buildTime` (PayloadDeconstructor.java:142-155); container and vault differ 3.875x in buildTime, and deconstruct time scales the same way. [src: PayloadDeconstructor.java:142-155]
5. **"Unit payloads depend on unit tier"** - only `hitSize / tilesize <= payloadLimit` (PayloadConveyor.java:87) and `unit.type.allowedInPayloads && !unit.spawnedByCore` (PayloadDeconstructor.java:92-95) matter, never the unit's tier. [src: PayloadConveyor.java:87]
6. **"Payload conveyors can be shot apart"** - payload-conveyor is `solid=false`, `underBullets=true` (00-data/blocks.json), so bullets pass straight through; only payload blocks with `solid=true`, such as payload-mass-driver, stop bullets.

## Related

- WORLD.BLOCKS.001 - multiblock anchors, size and placement legality, the tile basis of payload size.
- WORLD.LOGISTICS.001 - item conveyor throughput and blocking, for a side-by-side comparison with payload conveyors.
- WORLD.STORAGE.001 - unloaders and core capacity, where deconstructed payload items go.
- WORLD.CRAFTING.001 - recipe craftTime and unit conventions, neighbours of the buildTime cost formula.
- 00-data/blocks.json - every static field of the 14 payload blocks (health / size / requirements / consumes).
