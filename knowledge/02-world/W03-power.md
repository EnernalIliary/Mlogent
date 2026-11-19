---
id: WORLD.POWER.001
title: The power grid
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/PowerGraph.java:86-93, 154-257"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/PowerNode.java:33-35, 60-95"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/PowerDiode.java:48-83"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/PowerGenerator.java:25, 50, 67, 156-158"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/BeamNode.java:29, 79-91"
  - "Mindustry-Source/core/src/mindustry/world/consumers/ConsumePower.java:9-59"
  - "Mindustry-Source/core/src/mindustry/world/Block.java:48-59"
  - "MBO/gamedata/v160.7/gamedata.json (jar 反射，129 个 hasPower 方块)"
data: [00-data/blocks.json]
depends: [WORLD.CRAFTING.001, WORLD.BLOCKS.001]
tags: [power, PowerGraph, batteries, diodes, nodes, laser nodes, overload, powerLoss]
tokens: 1450
---

## In one sentence

Power has no "wire" entity: **nodes connect blocks into one graph (PowerGraph), and the whole graph settles "total demand vs total output" once per tick**, supplying every non-buffered device at the single ratio `coverage = min(1, produced/needed)`; surplus power flows into batteries by percentage and a shortfall is drawn from batteries by percentage — with no transmission loss in between.

## Rules / formulas

### 1. How power gets "wired" up

Five boolean fields decide whether a block can join a grid [src: Block.java:48-59]:

| Field | Meaning |
|---|---|
| `hasPower` | has a PowerModule (a carrier that can store/consume/generate) |
| `consumesPower` | **true** by default; node-type blocks must explicitly set it false, or they are treated as power consumers |
| `outputsPower` | generator |
| `connectedPower` | when false, nodes cannot connect to it |
| `conductivePower` | when true it conducts "through" like a cable (power-layer floors/walls) |

Graph-entry rules live in `PowerGraph.add()` [src: PowerGraph.java:290-299]:

- `outputsPower && consumesPower && !buffered` → goes into both producers and consumers (e.g. `impact-reactor`);
- `outputsPower && consumesPower && buffered` → goes into **batteries** (e.g. `battery`, `beam-node`);
- `outputsPower` only → producers; `consumesPower` only → consumers.

**A node itself is a "graph-building tool"**: `power-node` has only `laserRange` and `maxNodes`; it neither consumes nor produces power (`consumesPower = false, outputsPower = false`).

### 2. Per-tick settlement (the core formula)

```
needed   = Σ requestedPower(consumer) * consumer.delta()      // 每 tick 需求
produced = Σ getPowerProduction(producer) * producer.delta()  // 每 tick 产出
coverage = min(1, produced / needed)                          // 全图统一供电率
```

Non-buffered devices: `consumer.power.status = coverage` (`ConsumePower.efficiency()` returns it directly [src: ConsumePower.java:37-40])
Buffered devices: `status += requestedPower * coverage * delta / capacity` (charged in proportion to capacity [src: PowerGraph.java:195-200])

The key point: **demand is the graph-wide total, not a per-device queue**. So when 10 devices compete for 50% of the power, each gets exactly 50%; there is no "first connected, first fully powered".

### 3. Batteries (capacity units and charge/discharge rules)

- `consPower.capacity` is in "charge" units; a battery's `power.status ∈ [0,1]`, and its actual charge = `status × capacity`.
- Charging: `chargedPercent = min(excess / remaining capacity, 1)`, then per battery `status += (1 - status) × chargedPercent` [src: PowerGraph.java:170-185].
- Discharging: `consumedPercentage = min(1, needed / stored)`, then per battery `status *= (1 - consumedPercentage)` [src: PowerGraph.java:154-168].

Both are **synchronised by percentage** — a large battery and a small one in parallel always hold the same "fill percentage", so "fill one battery fully, then the next" never happens.

Note that `getBatteryCapacity()` returns the **remaining chargeable capacity** `(1 - status) × capacity`, not the total; the total is `getTotalBatteryCapacity()` [src: PowerGraph.java:130-152]. These two names are very easy to read backwards.

### 4. Diodes (one-way valves)

`PowerDiodeBuild.updateTile()` compares the battery percentage of the two grids every tick [src: PowerDiode.java:56-82]:

```
if (backStored/backCapacity <= frontStored/frontCapacity) return;   // 前侧不比后侧空就不动
targetPct = (frontStored + backStored) / (frontCapacity + backCapacity)
amount    = (targetPct * frontCapacity - frontStored) / 2           // 只搬差值的一半
amount    = clamp(amount, 0, frontCapacity - frontStored)           // 不让前侧溢出
backGraph.transferPower(-amount); frontGraph.transferPower(amount);
```

So a diode **only "levels", it does not "pass through"**, and each time it levels only half the gap; both sides must have `hasPower` **and battery capacity** (when `frontCapacity == 0` the amount clamps to 0 and no power is transferred at all).

### 5. Ranges of nodes / laser nodes / beam towers

| Block | Class | Connection | Range (tiles) | Max links |
|---|---|---|---|---|
| power-node | PowerNode | manual link | laserRange 6 | 10 |
| power-node-large | PowerNode | manual link | laserRange 15 | 15 |
| surge-tower | PowerNode | manual link (laser visuals) | laserRange 40 | 2 |
| beam-link | LongPowerNode | long-range link | laserRange 500 | 1 |
| beam-node | BeamNode | **auto-links** in four directions | range 10 | adjacent, automatic |
| beam-tower | BeamNode | auto-links in four directions, 3×3 | range 23 | adjacent, automatic |

`PowerNode`'s field defaults are `laserRange = 6` and `maxNodes = 3` [src: PowerNode.java:33-35]; concrete blocks override them in `Blocks.java` (so "3 links max by default" holds only for custom blocks).

`BeamNode` looks up, down, left and right for the nearest `hasPower` non-node block and links to it; hitting an `isInsulated()` block **breaks** the beam [src: BeamNode.java:79-91]. A diode has `insulated = true` (`PowerDiode.java:22`), so it naturally blocks beams.

### 6. Unit conversion (the easiest place to be off by 60×)

| Field | Unit | Display |
|---|---|---|
| `ConsumePower.usage` | power / **tick** | the UI shows `usage * 60f`, labelled /second [src: ConsumePower.java:47] |
| `PowerGenerator.powerProduction` | power / **tick** | the UI shows `powerProduction * 60f` [src: PowerGenerator.java:67] |
| `power.status` | 0–1 ratio | progress bar |
| `consPower.capacity` | charge (not /s) | battery charge |

1 unit of power/tick × 60 = 1 unit of power/second. Every "XX/s" number is a per-tick value × 60.

### 7. What "overload" means in vanilla

Vanilla has **no** overload burnout or trip, and no `powerLoss` field (it cannot be found in this repository's v159.3 source tree or in the v160.7 reflection data). The only phenomenon called "overload" is this: when `needed > produced`, `coverage < 1` and every device on the grid **loses efficiency proportionally** (a consumer's `efficiency = coverage`), which shows up as factories and turrets slowing down, never as an explosion. Reactor meltdown goes through the heat system (`WORLD.HEAT.001`) and has nothing to do with the grid.

## Numbers

Taken from the v160.7 jar reflection ([src: jar:v160.7#blocks[name=…].power]; for the same-source fields see the `power` subtree of `00-data/blocks.json#id=<name>`).

**Generation (per tick → per second)**

| Block | Type | powerProduction /tick | /second |
|---|---|---|---|
| combustion-generator | ConsumeGenerator | 1 | 60 |
| solar-panel | SolarGenerator | 0.12 | 7.2 |
| solar-panel-large | SolarGenerator | 1.6 | 96 |
| thermal-generator | ThermalGenerator | 1.8 | 108 |
| steam-generator | ConsumeGenerator | 5.5 | 330 |
| rtg-generator | no input | 4.5 | 270 |
| differential-generator | ConsumeGenerator | 18 | 1080 |
| thorium-reactor | NuclearReactor | 15 | 900 |
| impact-reactor | ImpactReactor | 130 | 7800 |
| neoplasia-reactor | VariableReactor | 140 | 8400 |
| flux-reactor | VariableReactor | 300 | 18000 |
| power-source (sandbox) | PowerSource | 16666.67 | ≈1e6 |

**Consumption (per tick → per second)**

| Block | usage /tick | /second |
|---|---|---|
| pyratite-mixer | 0.2 | 12 |
| silicon-smelter | 0.5 | 30 |
| plastanium-compressor | 3 | 180 |
| phase-weaver | 5 | 300 |
| impact-reactor (its own draw) | 25 | 1500 |
| power-void (sandbox, absorbs everything) | Float.MAX_VALUE ≈ 3.4e38 | meaningless |

**Battery capacity**

| Block | capacity | Note |
|---|---|---|
| beam-node | 1000 | 1×1, doubles as a battery |
| battery | 4000 | 1×1 |
| beam-tower | 40000 | 3×3 |
| battery-large | 50000 | 3×3 |

Other counts: **129** blocks have `hasPower = true` (28.9% of the 447 blocks).

## Source anchors

- `PowerGraph.java:216-257` `update()`: compute needed/produced first, then top up or absorb with batteries, and finally `distributePower()`.
- `PowerGraph.java:187-214` `distributePower()`: `coverage = min(1, produced/needed)`, and non-buffered devices simply get `status = coverage`.
- `PowerGraph.java:86-93` `getSatisfaction()` = `clamp(produced / needed)`, the numerator of the UI's power bar.
- `PowerGraph.java:154-185` `useBatteries()` / `chargeBatteries()`: charge and discharge synchronised by percentage.
- `PowerGraph.java:290-299` `add()`: the three-way producer / consumer / battery classification rule.
- `ConsumePower.java:9-14` the comments on the three fields `usage` (per tick), `capacity`, `buffered`.
- `ConsumePower.java:56-59` `requestedPower()`: buffered devices request `(1-status)*capacity`, non-buffered ones request `usage * (shouldConsume ? 1 : 0)`.
- `PowerGenerator.java:156-158` `getPowerProduction() = enabled ? powerProduction * productionEfficiency : 0`.
- `PowerNode.java:60-95` link config: while unlinked, only `linkValid` + `links.size < maxNodes` allows a link; after linking, `addGraph` merges the grids.
- `PowerDiode.java:56-82` the diode's half-gap transfer logic.
- `Block.java:48-59` `hasPower / consumesPower / outputsPower / connectedPower / conductivePower`.

## Measurements and counter-examples

**Counter-example 1 (a field named `powerLoss` does not exist)**: many old references claim "power has a powerLoss overhead, so long distances need relays". A full-tree search of the v159.3 source for `powerLoss` hits 0 places, and the v160.7 reflection data has no such field either. Power is settled **instantly across the whole graph** from production to consumption, regardless of distance; nodes only decide "is it in the same graph", not "how much gets through". What actually matters at long range is whether `laserRange` is big enough and whether `maxNodes` is enough to connect.

**Counter-example 2 (batteries are not "fill one fully, then the next")**: `chargeBatteries()` applies `status += (1-status) * chargedPercent` to **each** battery with `chargedPercent = excess / remaining capacity`. So put a 4000-charge battery and a 50000-charge battery in parallel and both always sit at the same percentage — the large battery's actual charge stays 12.5× the small one's. "Staged storage" is mechanically impossible.

**Counter-example 3 (a diode with no battery on either side transfers nothing at all)**: `amount = clamp(amount, 0, frontCapacity - frontStored)`, so when `frontCapacity == 0` (the front grid has no battery at all) the ceiling is 0 and the diode sends nothing. More subtly, `if(backStored/backCapacity <= frontStored/frontCapacity) return;`: equal percentages mean it does not move at all, so "use a diode to push power from a full battery bank into an empty grid" stops the moment the percentages match — there must be a load continuously pulling the front percentage down.

**Counter-example 4 (`hasPower` ≠ draws power)**: 129 blocks have `hasPower = true`, and the ones with `consumesPower = false` (nodes, beam nodes, pure generators) are not counted into `needed`. Conversely `Block.consumesPower` **defaults to true** — a custom block that forgets to set it false is treated by the grid as a consumer and drags the whole graph's `coverage` down.

**Counter-example 5 (the capacity field is not "how much can be discharged per second")**: `battery`'s `capacity = 4000` is its total charge, not its discharge power. The discharge rate is bounded only by `needed`: 4000 charge can be drained in a single tick if demand is large enough, and there is no "max discharge power" field.

## Common misconceptions

1. **"power is in kW / it is real power"** → it is unitless. 1 power = 1/tick of a resource, and the UI multiplies everything by 60 to show /second. A reactor's 15/tick displays as 900/s, not "900 kW".
2. **"more nodes means stronger transmission"** → nodes do not transport, relay or throttle; they only put blocks into the same graph. The only limits are `maxNodes` (link count) and `laserRange` (distance).
3. **"beam-node is more advanced than power-node, so it is faster"** → there is no "faster". The differences are: a beam-node **needs no manual linking** (it auto-links in four directions up to `range`) and carries 1000 charge of its own; the price is that it only works along the four directions and gets cut by `insulated` blocks.
4. **"batteries are an infinite buffer, the grid can never brown out"** → batteries only charge when "output > demand" and only top up when "demand > output"; when neither suffices, `coverage = produced/needed` and the grid still runs derated.
5. **"overload blows up the grid / burns the wires"** → vanilla has no overload explosion. Explosions come from reactor heat (`NuclearReactor`'s `heat` / `maxTemp`, see `WORLD.HEAT.001`).
6. **"a device with no power consumes no materials at all"** → a consumer's `efficiency = coverage`, so as long as `coverage > 0` it still advances progress proportionally and deducts materials/liquids proportionally; only `coverage = 0` stops everything.

## Related

- `WORLD.CRAFTING.001` (where `ConsumePower` sits in a recipe, and how usage interacts with craftTime)
- `WORLD.STORAGE.001` (how battery priority differs from item/liquid storage)
- `WORLD.HEAT.001` (reactor meltdown, `heatOutput` and thermal generation)
- `WORLD.LOGISTICS.001` (a jam makes `shouldConsume()` false, which drops power draw to zero)
- `WORLD.SANDBOX.001` (`power-source` / `power-void` are sandbox-only)
- Data tables: `00-data/blocks.json` (`power.usage` / `power.usagePerSecond` / `power.capacity` / `power.powerProduction` / `power.productionPerSecond`)
- Source: `world/blocks/power/PowerGraph.java`, `PowerNode.java`, `PowerDiode.java`, `PowerGenerator.java`, `BeamNode.java`, `world/consumers/ConsumePower.java`, `world/Block.java`
