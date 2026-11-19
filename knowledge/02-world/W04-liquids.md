---
id: WORLD.LIQUIDS.001
title: The liquid system
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:920-984"
  - "Mindustry-Source/core/src/mindustry/world/blocks/liquid/Conduit.java:30, 240-257"
  - "Mindustry-Source/core/src/mindustry/world/blocks/liquid/LiquidRouter.java:23-43"
  - "Mindustry-Source/core/src/mindustry/world/blocks/liquid/LiquidJunction.java:43-53"
  - "Mindustry-Source/core/src/mindustry/world/blocks/liquid/LiquidBlock.java:20-28"
  - "Mindustry-Source/core/src/mindustry/world/blocks/production/Pump.java:19-20, 160-170"
  - "Mindustry-Source/core/src/mindustry/type/Liquid.java:27-70"
  - "Mindustry-Source/core/src/mindustry/entities/Puddles.java:16, 37-98"
  - "Mindustry-Source/core/src/mindustry/entities/comp/PuddleComp.java:47-66"
data: [00-data/liquids.json, 00-data/blocks.json]
depends: [WORLD.BLOCKS.001, WORLD.CRAFTING.001]
tags: [liquids, conduits, pumps, viscosity, heatCapacity, puddles, jamming]
tokens: 1929
---

## In one sentence

A liquid is a resource with "one `LiquidModule` stock per block + one pressure-difference transfer per tick": **there is no flow-rate field, and how much moves is decided entirely by "this block's fill ratio" minus "the downstream fill ratio", times this block's `liquidCapacity`**; if any segment in a pipeline fills up, or a second liquid gets in, flow stops right there.

## Rules / formulas

### 1. Where liquids live

Every `hasLiquids = true` block has a `LiquidModule` (107 of them in v160.7), internally **a float array holding one slot per each of the 11 liquids** [src: LiquidModule.java:23-24]. But almost every behaviour in the game is driven by `current()` (the liquid most recently received/set) and `currentAmount()`:

```
currentAmount() = liquids[current.id]      // 只算"当前那种"，不是总量
```

So **only one liquid actually matters per block** — the array is headroom left for special logic such as reactors, not for the player to mix liquids.

### 2. The transfer formula (the one core)

All passive flow goes through `BuildingComp.moveLiquid(next, liquid)` [src: BuildingComp.java:944-984]:

```
ofract = next.liquids.get(liquid) / next.liquidCapacity     // 下游充满度
fract  = 本块.liquids.get(liquid) / 本块.liquidCapacity * 本块.liquidPressure
flow   = clamp(fract - ofract) * 本块.liquidCapacity         // 按压差比例搬
flow   = min(flow, 本块存量, 下游剩余容量)
if (flow > 0 && ofract <= fract && next.acceptLiquid(...)) 才真的搬
```

Three immediate consequences:

1. **If the downstream is not emptier than this block, not a drop moves** (`ofract <= fract` is a hard condition).
2. Throughput is proportional to "this block's capacity": the larger the capacity, the more a block can push per tick.
3. `liquidPressure` is the default `1f` everywhere in vanilla (`Block.java:79`; no vanilla block changes it in v159.3).

### 3. Conduits / routers / junctions / bridges

| Block | Class | Liquid capacity | Special behaviour |
|---|---|---|---|
| conduit | Conduit | 20 | pushes only towards `rotation`; **leaks** |
| pulse-conduit | Conduit | 40 | same, double capacity |
| plated-conduit | ArmoredConduit | 50 | `leaks = false`, does not leak |
| reinforced-conduit | ArmoredConduit | 50 | does not leak |
| liquid-junction | LiquidJunction | 10 | **passes straight** to the opposite side, no splitting |
| liquid-router | LiquidRouter | 120 | `dumpLiquid` to all four sides |
| liquid-container | LiquidRouter | 700 | large container that also routes |
| liquid-tank | LiquidRouter | 1800 | same as above |
| bridge-conduit | LiquidBridge | 100 | spans 4 tiles |
| phase-conduit | LiquidBridge | 100 | spans 12 tiles |
| reinforced-bridge-conduit | DirectionLiquidBridge | 120 | spans 4 tiles, directional |

`Conduit` calls `moveLiquidForward` towards its front face once per tick (`timer(timerFlow, 1)` [src: Conduit.java:251]), so its **per-tick transfer ceiling is its own capacity**: conduit 20/tick (≈1200/s), pulse-conduit 40/tick (2400/s). This explains a common confusion — "conduit capacity" and "conduit throughput" are numerically the same number.

`LiquidJunction` uses `getLiquidDestination` to redirect "the building asking me for liquid" to the tile on the opposite side [src: LiquidJunction.java:43-53]; the `straight-through` behaviour is not splitting, which is why junctions never mix liquids.

`Conduit`'s `acceptLiquid` also carries a geometric constraint: **liquid cannot come in through its own back face** (`(source.relativeTo(...) + 2) % 4 != rotation` [src: Conduit.java:241-245]), so conduits do not flow backwards.

### 4. Pumps

`PumpBuild` scans the `size × size` floor tiles it covers every tick and sums `floor.liquidMultiplier` [src: Pump.java:160-170]:

```
amount  = Σ(所覆盖地板.liquidMultiplier)            // 液体地板个数 × 倍率
maxPump = min(liquidCapacity - 当前库存, amount * pumpAmount * edelta)
```

So **a pump's output = per-tile pump rate × liquid tile count × floor multiplier**. A mechanical pump (1×1) on ordinary water: `1 × 0.1167 = 0.1167/tick = 7/s`; a rotary pump (2×2 = 4 tiles): `4 × 0.2 = 0.8/tick = 48/s`; an impulse pump (3×3 = 9 tiles): `9 × 0.22 = 1.98/tick = 118.8/s`.

`water-extractor` is a `SolidPump` (it does not depend on floor water) with `pumpAmount = 0.11/tick = 6.6/s`.

Floor multipliers (v160.7 reflection `raw.liquidMultiplier`): deep-water **1.5**, shallow-water / tainted-water **1**, pooled-cryofluid **0.5**, arkycite-floor **1**, tar (oil) / molten-slag (slag) **1**. Deep water yields 50% more than shallow — that is the entire benefit of placing pumps in deep water.

### 5. Mixing, jamming and reactions

**Mixing is stopped by two gates**:

1. `acceptLiquid(source, liquid)`: both the conduit and router implementations are `liquids.current() == liquid || liquids.currentAmount() < 0.2f` [src: LiquidRouter.java:41-43] — they only accept blocks holding "the same kind" or "almost empty".
2. Consumers (`ConsumeLiquid` / `ConsumeLiquidFilter`) only accept liquids in their own filter list and return false for everything else.

Hence **two liquids can never mix inside one conduit segment**: whichever arrives first occupies it and the other is turned away at the source. Merging lines requires emptying first (drain the conduit below 0.2 before a different liquid is allowed).

If two **reactive** liquids meet in adjacent blocks (both `blockReactive = true`), a reaction fires [src: BuildingComp.java:959-981]:

- one side has `flammability > 0.3` and the other has `temperature > 0.7` → both take `damageContinuous(1)` with a 10%/tick chance of catching fire;
- one side has `temperature > 0.7` and the other has `temperature < 0.55` → the hot liquid is consumed at `0.7 × delta/tick` with a 20%/tick chance of venting steam.

That is the mechanism behind "pouring water into a slag conduit blows the pipe" — it is **the block taking damage**, not the liquid being destroyed.

### 6. The eleven liquids and their five properties

Field semantics of `Liquid` [src: Liquid.java:27-70]:

| Field | Meaning | Who uses it |
|---|---|---|
| `viscosity` | 0.5=water, 1=tar; **only affects puddle evaporation/spread speed** | `PuddleComp.java:60` |
| `heatCapacity` | 0.4=water; the core of the coolant multiplier | turret cooling, reactors, shields |
| `temperature` | 0.5=room temperature, >0.7 counts as "hot" | liquid reaction checks |
| `flammability` | only >0.3 can be ignited | fire, explosions, reactions |
| `explosiveness` | tendency to explode when heated | explosion strength when the block is destroyed |
| `coolant` | false means **it cannot serve as coolant** (only gallium = false in vanilla) | coolant filtering |
| `gas` | a gas, creates no puddles, forces `boilPoint` to -1 | visuals and conduit animation |
| `boilPoint` | vaporisation temperature threshold (default 2 = never) | reactor overheat vaporisation |

**Viscosity does not affect conduit flow rate** — the most common misconception, see the counter-examples below.

### 7. Puddles

Liquid leaking onto the ground (a conduit with `leaks = true` and no solid ahead) spawns a Puddle in the target tile [src: BuildingComp.java:936-940]:

```
leakAmount = 本块存量 / 1.5          // 每次漏掉 2/3
Puddles.deposit(...)
```

The puddle ceiling is `Puddles.maxLiquid = 70` [src: Puddles.java:16]. Decay every tick [src: PuddleComp.java:60-63]:

```
amount -= delta * (1 - liquid.viscosity) / (5 + addSpeed)
amount  = min(amount, maxLiquid)
```

Water's `viscosity = 0.5` → decays `0.5 / 5 = 0.1` per tick, so 70 units evaporate in about 700 tick (≈11.7 s); oil's `viscosity = 0.75` → 0.05 per tick, twice as slow. **Higher viscosity = puddles last longer = easier to ignite**, and it has nothing to do with "flowing slower".

Above `maxLiquid / 1.5 ≈ 46.7` a puddle spreads to its four neighbours, at most `0.3 × delta` (0.3/tick) each time.

## Numbers

**Liquid property table (all 11)**

The values come from the per-entry field assignments of `new Liquid("..."){{ }}` in the source `Mindustry-Source/core/src/mindustry/content/Liquids.java:13-95`, not from memory; any field not assigned takes the default from `type/Liquid.java` — temperature 0.5 (Liquid.java:40), heat capacity 0.5 (Liquid.java:42), viscosity 0.5 (Liquid.java:44), flammability 0 (Liquid.java:38), explosiveness 0 (Liquid.java:46), `coolant = true` (Liquid.java:50), `blockReactive = true` (Liquid.java:48). `00-data/liquids.json` holds the same values, but it is only a data table: the body text must spell out the numbers itself, otherwise a retrieval hit on the table still cannot answer the question.

| Liquid | Source `Liquids.java` lines | temperature | heatCapacity | viscosity | flammability | explosiveness | coolant | gas | hidden | boilPoint |
|---|---|---|---|---|---|---|---|---|---|---|
| water | 13-19 | 0.5 | **0.4** | 0.5 | 0 | 0 | ✔ (Liquid.java:50 default) | – | – | 0.5 (`:16`) |
| slag | 21-26 | **1.0** (`:22`) | 0.5 | **0.7** (`:23`) | 0 | 0 | ✔ | – | – | 2 |
| oil | 28-38 | 0.5 | **0.7** (`:32`) | **0.75** (`:29`) | **1.2** (`:30`) | **1.2** (`:31`) | ✔ | – | – | 0.65 (`:35`) |
| cryofluid | 40-47 | **0.25** (`:42`) | **0.9** (`:41`) | 0.5 | 0 | 0 | ✔ | – | – | 0.55 (`:45`) |
| neoplasm | 49-63 | **0.54** (`:51`) | **0.4** (`:50`) | **0.85** (`:52`, the highest of all liquids) | **0** (`:53`) | 0 | ✔ | – | – | 2 |
| arkycite | 65-69 | 0.5 | 0.5 | **0.7** (`:67`) | **0.4** (`:66`) | 0 | ✔ | – | – | 2 |
| gallium | 71-74 | 0.5 | 0.5 | 0.5 | 0 | 0 | **✘ (`coolant=false`, `:72`)** | – | **✔ (`hidden=true`, `:73`)** | 2 |
| ozone | 76-81 | 0.5 | 0.5 | 0.5 | **1** (`:80`) | **1** (`:79`) | ✔ | ✔ (`:77`) | – | -1 |
| hydrogen | 83-86 | 0.5 | 0.5 | 0.5 | **1** (`:85`) | 0 | ✔ | ✔ (`:84`) | – | -1 |
| nitrogen | 88-90 | 0.5 | 0.5 | 0.5 | 0 | 0 | ✔ | ✔ (`:89`) | – | -1 |
| cyanogen | 92-95 | 0.5 | 0.5 | 0.5 | **2** (`:94`, the highest of all liquids) | 0 | ✔ | ✔ (`:93`) | – | -1 |

Three points that are easy to get wrong: ① `water`'s heat capacity is **0.4, not 0.5** (Liquids.java:14 explicitly overrides the default), so "water is the baseline coolant" does not mean it is the median heat capacity; ② `gallium` has `coolant = false` (Liquids.java:72) and `hidden = true` (Liquids.java:73), so it is not shown in game and can never act as a coolant; ③ `neoplasm` is the only liquid that is simultaneously `moveThroughBlocks = true` (`:56`), `capPuddles = false` (`:54`), `blockReactive = false` (`:58`) and `incinerable = false` (`:57`), so it passes through blocks, spreads without limit, and never reacts with other liquids.

**Pump output (per tick → per second, standing on ordinary shallow water)**

| Block | pumpAmount | Tiles covered | /tick | /second |
|---|---|---|---|---|
| mechanical-pump | 0.1167 | 1 | 0.1167 | 7 |
| rotary-pump | 0.2 | 4 | 0.8 | 48 |
| impulse-pump | 0.22 | 9 | 1.98 | 118.8 |
| reinforced-pump | 0.3333 | 4 | 1.333 | 80 |
| water-extractor | 0.11 (solid) | 4 | 0.44 | 26.4 |

**Liquid container capacities**

| Block | liquidCapacity |
|---|---|
| liquid-junction | 10 |
| conduit | 20 |
| pulse-conduit | 40 |
| plated-conduit / reinforced-conduit | 50 |
| bridge-conduit / phase-conduit | 100 |
| liquid-router | 120 |
| reinforced-bridge-conduit | 120 |
| liquid-container | 700 |
| reinforced-liquid-container | 1000 |
| liquid-tank | 1800 |
| reinforced-liquid-tank | 2700 |
| landing-pad | 3000 |
| liquid-source / liquid-void (sandbox) | 10000 |

## Source anchors

- `BuildingComp.java:944-984` `moveLiquid`: the pressure-difference formula and the "ofract <= fract" hard condition, including the liquid-reaction branch.
- `BuildingComp.java:929-942` `moveLiquidForward`: pushes towards rotation; when the tile ahead is neither solid nor liquid it leaks `stock/1.5` into a Puddle.
- `BuildingComp.java:920-927` `transferLiquid`: clamp to the downstream's remaining capacity first, then validate with `acceptLiquid`.
- `Conduit.java:251` `timer(timerFlow, 1)`: pushes once per tick; `Conduit.java:30` `timerFlow = timers++`.
- `Conduit.java:241-245` `acceptLiquid`: same kind or <0.2, and **no liquid may enter through the back face**.
- `LiquidRouter.java:25-27` `dumpLiquid(liquids.current())`: a router only "pours to all four sides".
- `LiquidJunction.java:43-53` `getLiquidDestination`: straight-through redirection.
- `LiquidBlock.java:20-28` the liquid block base class: `hasLiquids = true`, `outputsLiquid = true`, `solid = true`.
- `Pump.java:19-20` `pumpAmount` (per tile); `Pump.java:162` `maxPump = min(capacity-stock, amount*pumpAmount*edelta)`.
- `content/Liquids.java:13-95` the **full per-field assignments** of the 11 liquids (`water` 13-19, `slag` 21-26, `oil` 28-38, `cryofluid` 40-47, `neoplasm` 49-63, `arkycite` 65-69, `gallium` 71-74, `ozone` 76-81, `hydrogen` 83-86, `nitrogen` 88-90, `cyanogen` 92-95) — `Liquids.java` is the first source of truth for liquid numbers; the `.json` is only its dump.
- `type/Liquid.java:38-50` field defaults: `flammability = 0`, `temperature = 0.5`, `heatCapacity = 0.5`, `viscosity = 0.5`, `explosiveness = 0`, `blockReactive = true`, `coolant = true`; `Liquid.java:27-70` also has `gas/moveThroughBlocks/incinerable/boilPoint`.
- `Puddles.java:16` `maxLiquid = 70`; `Puddles.java:37-98` `deposit()` and spreading.
- `PuddleComp.java:47-66` puddle burn coefficients and viscosity decay.

## Measurements and counter-examples

**Counter-example 1 (viscosity does not control flow rate)**: intuitively "oil at viscosity 0.75 should flow slower than water at 0.5", but `moveLiquid`'s formula has no `viscosity` term at all — water and oil move through a conduit of the same capacity at **exactly the same speed**, 20/tick (conduit). Viscosity shows up in only three places: puddle decay (`PuddleComp.java:60`), certain status effects, and UI data. Making oil flow slower is mechanically impossible.

**Counter-example 2 (conduit "capacity" is the throughput ceiling, not 20/s)**: `liquidCapacity = 20` is often read as "20 per second". It actually means **at most 20 per tick**, i.e. 1200/s; and that ceiling is practically unreachable — a mechanical pump only produces 0.117/tick. The real bottleneck is usually "too few pumps" or "one segment blocked by a second liquid", never conduit speed.

**Counter-example 3 (different liquids do not mix, they only block each other)**: once a conduit segment holds 5 units of water, oil is rejected by `acceptLiquid` (`currentAmount() < 0.2f` fails). What players experience as "mixed liquid" usually comes from **branch points**: a liquid-router with a water pool on one side and an oil pool on the other calls `dumpLiquid(current())` in turn, so different downstream branches end up with different liquids rather than one segment holding a blend.

**Counter-example 4 (a junction is not a splitter)**: `liquid-junction` exists to let liquid "coming from side A" go straight to "the opposite side B"; the middle tile itself has only 10 capacity and `update = false` (it does not push on its own). Using it as a "liquid router" leaves one side permanently unsupplied.

**Counter-example 5 (water on slag is "block explosion", not "liquid destruction")**: the reaction branch at `BuildingComp.java:966-973` fires only when both sides are `blockReactive`, and its effect is `damageContinuous(1)` on the **block**. The liquids themselves stay in their own stocks; only vaporisation through heat (`boilPoint`) makes them disappear.

## Common misconceptions

1. **"vn value / pressure is needed"** → vanilla `liquidPressure` is 1 everywhere, and there is no concept of a "booster pump" or "pressure decay"; distance only affects "how many conduit segments you need in between", never flow rate.
2. **"a conduit splits liquid evenly between two outlets"** → `dumpLiquid` pours **sequentially** (rotating in proximity order), not evenly; even distribution requires a liquid-router with enough two-way stock to smooth the difference, or precise logic control.
3. **"liquid stock = the sum of all liquids"** → `currentAmount()` returns only `liquids[current.id]`. After putting two liquids into one block, the UI liquid bar shows only the `current` one.
4. **"deep water is only visual"** → deep water has `liquidMultiplier = 1.5`, `speedMultiplier = 0.2`, `drownTime = 200`, and all three are real: pump output +50%, unit speed cut to 20%, non-aquatic units drown in 200 tick.
5. **"gases can also be pumped into puddles"** → a liquid with `gas = true` creates no puddles and has `boilPoint` forced to -1 (always vaporises), so ozone/hydrogen/nitrogen/cyanogen exist only inside conduits and blocks.
6. **"leaking is only a visual effect"** → conduit / pulse-conduit / reinforced-conduit with `leaks = true` pour `stock/1.5` (about 66.7%) onto empty floor ahead every tick; only plated-conduit and the armored line do not leak.

## Related

- `WORLD.BLOCKS.001` (where `hasLiquids` / `liquidCapacity` sit in a block definition)
- `WORLD.CRAFTING.001` (`ConsumeLiquid`: liquids are charged **per tick**, and efficiency can run half full by stock ratio)
- `WORLD.HEAT.001` (the full use of `heatCapacity` as a coolant multiplier)
- `WORLD.POWER.001` (liquid generators: steam-generator / differential-generator / impact-reactor)
- `WORLD.TERRAIN.001` (deep/shallow water and tar terrain with `liquidDrop` / `drownTime`)
- `WORLD.LOGISTICS.001` (solid logistics versus the liquid-conduit jamming model)
- Data tables: `00-data/liquids.json` (`viscosity/heatCapacity/temperature/flammability/explosiveness/coolant`), `00-data/blocks.json` (`liquidCapacity`, `hasLiquids`)
- Source: `world/blocks/liquid/*.java`, `world/blocks/production/Pump.java`, `entities/Puddles.java`, `world/modules/LiquidModule.java`
