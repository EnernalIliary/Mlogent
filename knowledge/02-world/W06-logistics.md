---
id: WORLD.LOGISTICS.001
title: Item logistics and transport (conveyors / routers / junctions / bridges / mass drivers)
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/Conveyor.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/Duct.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/Junction.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/Router.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/ItemBridge.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/BufferedItemBridge.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/StackConveyor.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/MassDriver.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/DirectionalUnloader.java"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java"
data:
  - "00-data/blocks.json#id=conveyor"
  - "00-data/blocks.json#id=junction"
  - "00-data/blocks.json#id=mass-driver"
depends: [WORLD.BLOCKS.001, WORLD.CRAFTING.001]
tags: [logistics, conveyors, conveyor, duct, router, junction, bridge, mass-driver, throughput, items/s]
tokens: 1837
---

## In one sentence

Items move between blocks only through conveyors, ducts, routers, junctions, bridges and mass drivers; every rate in the source is **per tick** (×60 for per second), and the `speed` field of the three families **uses three different units** (tiles/tick, tick/item, a coefficient) — mixing them up costs you an order of magnitude.

## Rules / formulas

### 1. The unit conventions of the three rates (memorise this first, or everything after is wrong)

| Class | Field | Unit | Conversion | Source |
|---|---|---|---|---|
| `Conveyor` | `speed` | **tiles/tick** | throughput ≈ `speed × 60 / itemSpace`, `itemSpace = 0.4` | Conveyor.java:32, Conveyor.java:27 |
| `Duct` | `speed` | **tick/item** | displayed value = `60 / speed` | Duct.java:27, Duct.java:61 |
| `Junction` | `speed` | **tick/item** | 26 tick to cross the junction | Junction.java:13 |
| `Router` | `speed` | items/tick coefficient | `time += 1/speed × delta`, one item every 8 tick | Router.java:13, Router.java:61 |
| `StackConveyor` | `speed` | tiles/tick | throughput = `itemCapacity × speed × 60` | StackConveyor.java:38, StackConveyor.java:67 |
| `MassDriver` | `reload` | tick/shot | shot rate = `60/reload`, item rate = `itemCapacity × 60/reload` | MassDriver.java:33, MassDriver.java:66-69 |

Deriving `Conveyor` throughput: one tile holds at most 3 items (`capacity = 3`, Conveyor.java:28) and the item spacing `itemSpace = 0.4` (Conveyor.java:27) is measured in tiles, so a 1-tile length fits only 2.5 items; each item advances `speed` tiles per tick ⇒ `speed × 60 / 0.4` items pass per second. [v160.7] `conveyor` has `speed = 0.035` ⇒ 5.25 items/s; [v159.3] the source has `speed = 0.046` (Blocks.java:2071) ⇒ 6.9 items/s. The `displayedSpeed` on the UI (v160.7 = 5, v159.3 = 6.5) is a **hand-filled approximation** — the source comment says outright that the actual movement speed is "apparently not linear" (Conveyor.java:59-60) — so do not reverse-engineer the formula from it.

### 2. The single-tile conveyor model: 3 items, spacing 0.4, blocked by the item ahead

Each tile is a "rope" of length 1 with item positions `ys ∈ [0,1]`, where `ys = 1` means it can be handed downstream. Each tick every item advances `moved = speed × edelta` (Conveyor.java:266), but each item's ceiling is "the position of the item ahead − itemSpace":

```
nextpos = (i == len-1 ? 100 : ys[i+1]) - itemSpace
maxmove = clamp(nextpos - ys[i], 0, moved)   // 不能穿过前一件
ys[i] += maxmove
```

(Conveyor.java:268-272) Delivery happens only when `ys >= 1` and the downstream `acceptItem` returns true (`pass()`, Conveyor.java:278, Conveyor.java:300-306); if the downstream refuses, the item waits at 1.0 and the items behind pile up against it — that is backpressure. While jammed, `minitem < itemSpace` drives `clogHeat` towards 1 each tick (Conveyor.java:291-295), and once `clogHeat > 0.5` the conveyor stops pushing units standing on it and its sprite freezes (Conveyor.java:145, Conveyor.java:229).

A straight 5-tile conveyor holds at most 5×3 = 15 items; when completely jammed it **does not lose items**, it simply stops advancing.

### 3. Ducts: 1 item per tile, yet faster than a conveyor

A Duct holds only 1 item per tile (`itemCapacity = 1`, Duct.java:44); `acceptItem` requires `current == null && items.total() == 0` (Duct.java:212-220) and **does not accept items entering from the back** (Duct.java:219 checks `!= 2`); ArmoredDuct is the reverse and accepts only from the front (Duct.java:216-217).

Its advance is not "one tile per tick" but accumulated progress:

```
progress += edelta() / speed * 2                                   // Duct.java:194
if(progress >= 1 - 1f/speed && moveForward(current)){ ... progress %= 1 - 1f/speed; }
```

(Duct.java:194-201) With `speed = 4` (Blocks.java:2180, and also 4 in the v160.7 jar) ⇒ threshold 0.75, +0.5 per tick, roughly 2 items per 3 tick ≈ 20 items/s; yet `setStats` writes `60 / speed = 15` items/s (Duct.java:61). **Both figures are hard-coded in the source and they do not agree**, which is why this article gives the range 15–20 items/s rather than a single value. A duct gains density from "1 item per tile and cheap", not from per-tile speed.

### 4. Routers / junctions / sorters: three small blocks that "do not buffer"

- **Router**: `itemCapacity = 1` (Router.java:21) and it accepts only into an empty slot (`acceptItem`, Router.java:79-81); `time += 1f/speed × delta` must reach 1 before it releases (Router.java:61), and `speed = 8` ⇒ at most 7.5 items/s, and **if the target is also a Router it still has to wait its full delay** (Router.java:64). Target selection rotates through `proximity` by `rotation` (Router.java:119-127), which is approximate round-robin, not exact even splitting.
- **Junction**: not "6 items buffered", but **6 items per direction** — `DirectionalItemBuffer(capacity)` with `capacity = 6` (Junction.java:46, Junction.java:14). An item enters with a timestamp and is delivered to the same-direction neighbour only after a full `speed = 26` tick (Junction.java:62-74). So one junction holds at most 4×6 = 24 items, and crossing it in any direction takes 26 tick ≈ 0.43 s.
- **Sorter / InvertedSorter**: `sortItem` is a config option (Sorter.java:37-38); a matching item goes straight ahead and a non-matching one goes to the sides (Sorter.java:96-133); `instantTransfer = true` (Sorter.java:28) means "this tile itself costs no tick", but the tiles before and after still wait as usual.
- **OverflowGate / UnderflowGate**: `itemCapacity = 0` (no buffering), `instantTransfer = true`; whatever the front can accept is passed straight through, and only what it cannot accept is split to the sides (OverflowGate.java:22-25, OverflowGate.java:51-81); underflow is simply `invert = true` (Blocks.java:2209-2216). Both have `canOverdrive = false` (v160.7 jar reflection), so they take no overdrive bonus.

### 5. Bridges and phase bridges: chained delivery

`bridge-conveyor` (BufferedItemBridge): `range = 4`, `bufferCapacity = 14`, `itemCapacity = 10`, `speed = 74`, `displayedSpeed = 11` (Blocks.java:2105-2113, identical in the v160.7 jar); internally an `ItemBuffer`, with `poll(speed/timeScale)` taking items (BufferedItemBridge.java:41), and the source comment admits that "movement speed is empirical" (BufferedItemBridge.java:27). Its 11 items/s is this block's throughput ceiling, more than double a conveyor's 5 items/s.

`phase-conveyor` (ItemBridge): `range = 12`, `transportTime = 2`, power draw `0.30/tick = 18/s` (Blocks.java:2115-2125). It does not buffer; every `transportTime` tick it simply does `items.take()` and launches one item (ItemBridge.java:355-368) ⇒ ceiling 60/2 = 30 items/s. The link constraint is in `positionsValid`: the two ends must be **in the same row or the same column** and within `range`, otherwise it returns `false` outright (ItemBridge.java:157-165) — diagonal placement does nothing.

### 6. Mass drivers: 10 items on each side before they fire

`mass-driver`: `range = 440` (px, = 55 tiles; stats show `range/tilesize`, MassDriver.java:66), `reload = 200` tick/shot, `itemCapacity = 120`, `minDistribute = 10`, `size = 3` (Blocks.java:2166-2173; MassDriver.java:31). Firing is a chain of AND conditions:

- its own stock `>= minDistribute`, and **the other end's remaining capacity** `>= minDistribute` (MassDriver.java:192-193);
- the other end is in a receiving state and no other driver is queued (MassDriver.java:204-206);
- both ends' rotations are aligned within ±2° (MassDriver.java:204-206), otherwise it keeps rotating (`rotateSpeed = 5`, MassDriver.java:29);
- it has power (`efficiency > 0`, MassDriver.java:169).

Firing **packs the whole stock by item type** and sends it, with a per-type ceiling of `min(own stock, the other end's remaining capacity)` (MassDriver.java:298-303); the receiver can hold up to `itemCapacity × 2 = 240` (MassDriver.java:324). So one shot is in the 100+ items range, and `60/reload = 0.3` shots/s × 120 = a nominal 36 items/s (MassDriver.java:66-69).

### 7. Unloaders (the pickup side)

- `unloader`: takes one item from the adjacent storage block (core/container) and pushes it to its front face, `speed = 60/11 ≈ 5.4545` tick/item ⇒ **11 items/s** (Blocks.java:2162; stats show `60/speed`, Unloader.java:61-63), with `allowCoreUnload = true` by default.
- `duct-unloader` (DirectionalUnloader): `speed = 4` ⇒ **15 items/s** (Blocks.java:2227-2234); `unloadTimer += edelta()` must reach `speed` before one item moves (DirectionalUnloader.java:93-118), and `allowCoreUnload = false` by default (DirectionalUnloader.java:26) — it cannot pull directly from a core, only from containers.

Storage capacity and priority on the pickup side are covered in W10.

## Numbers

**Full transport-block table (v160.7 jar reflection; same-name records live in `00-data/blocks.json#id=<name>`)**

| Block | size | itemCapacity | raw speed | Throughput (items/s) | Source |
|---|---|---|---|---|---|
| `conveyor` | 1 | 3 | 0.035 tiles/tick | **5.25** (UI shows 5); [v159.3] 0.046 ⇒ 6.9 | Blocks.java:2068-2074 |
| `titanium-conveyor` | 1 | 3 | 0.0801 tiles/tick | 10 | Blocks.java:2076-2081 |
| `armored-conveyor` | 1 | 3 | 0.08 tiles/tick | 10 ([v159.3] displayedSpeed 11) | Blocks.java:2090-2095 |
| `plastanium-conveyor` | 1 | 10 | 0.0667 tiles/tick | 40 (10×0.0667×60) | Blocks.java:2083-2088 |
| `surge-conveyor` | 1 | 10 | 0.0833 tiles/tick | 50 (10×0.0833×60), power 1/tick | Blocks.java:2236-2252 |
| `duct` / `armored-duct` | 1 | 1 | 4 tick/item | 15 (stats) – 20 (hand-calculated) | Blocks.java:2177-2190 |
| `duct-router` | 1 | 1 | 4 tick/item | 15 | Blocks.java:2192-2199 |
| `duct-bridge` | 1 | 4 | 4 tick/item, range 4 | 15 | Blocks.java:2218-2225 |
| `junction` | 1 | 10 (6 buffered per direction) | 26 tick/item | 13 (displayedSpeed) | Junction.java:13-15 |
| `router` / `distributor` | 1 / 2 | 1 | 8 | 7.5 (hand-calculated) | Router.java:13, Blocks.java:2138-2143 |
| `bridge-conveyor` | 1 | 10 (buffer 14) | 74, range 4 | 11 | Blocks.java:2105-2113 |
| `phase-conveyor` | 1 | 10 | transportTime 2, range 12 | 30 (ceiling), power 18/s | Blocks.java:2115-2125 |
| `mass-driver` | 3 | 120 | reload 200 | 0.3 shots/s, 36 items/s (nominal), power 105/s | Blocks.java:2166-2173 |
| `unloader` | 1 | 0 | 5.4545 tick/item | 11 | Blocks.java:2160-2164 |
| `duct-unloader` | 1 | 0 | 4 tick/item | 15 | Blocks.java:2227-2234 |

**Per-tile buffer capacity (how much piles up when jammed)**

| Block | Capacity per tile/direction | Note | Source |
|---|---|---|---|
| `conveyor` / `titanium-conveyor` / `armored-conveyor` | 3 items/tile | `capacity = 3`, spacing 0.4 | Conveyor.java:27-28 |
| `plastanium-conveyor` / `surge-conveyor` | 10 items / whole belt | stacking conveyor | StackConveyor default; Blocks.java:2087 |
| `duct` / `armored-duct` | 1 item/tile | `itemCapacity = 1` | Duct.java:44 |
| `junction` | 6 items × 4 directions = 24 items | `DirectionalItemBuffer(capacity)` | Junction.java:14, Junction.java:46 |
| `router` / `distributor` | 1 item | single slot only | Router.java:21 |
| `bridge-conveyor` | 14 items | `bufferCapacity` | Blocks.java:2111 |
| `duct-bridge` | 4 items | jar reflection `itemCapacity = 4` | 00-data/blocks.json#id=duct-bridge |
| `mass-driver` | 120 items (receiver takes 240) | `itemCapacity × 2` ceiling | MassDriver.java:324 |

**Cross-version differences (v159.3 source vs v160.7 jar)**

| Block | Field | v159.3 source | v160.7 live |
|---|---|---|---|
| `conveyor` | `speed` | 0.046 (Blocks.java:2071) | 0.035 |
| `conveyor` | `displayedSpeed` | 6.5 (Blocks.java:2072) | 5 |
| `armored-conveyor` | `displayedSpeed` | 11 (Blocks.java:2094) | 10 |
| `junction` | `speed` / `capacity` | 26 / 6 (Blocks.java:2099-2100) | 26 / 6 (same) |
| `bridge-conveyor` | `speed` / `bufferCapacity` | 74 / 14 (Blocks.java:2109-2111) | 74 / 14 (same) |

## Source anchors

- `Conveyor.java:27-28` `itemSpace = 0.4f`, `capacity = 3`; `Conveyor.java:32-33` `speed` / `displayedSpeed`; `Conveyor.java:59-60` the comment that actual speed is non-linear.
- `Conveyor.java:265-298` `updateTile`: `nextMax` alignment, `moved = speed * edelta()`, per-item clamp, delivery on `ys >= 1 && pass()`; `Conveyor.java:291-295` `clogHeat`.
- `Conveyor.java:300-306` `pass()`: handover only if `next.acceptItem(this, item)`.
- `Duct.java:61` stats `60f / speed`; `Duct.java:193-209` `progress` advance; `Duct.java:212-220` `acceptItem` and the back-face ban.
- `Junction.java:13-15` `speed = 26` / `capacity = 6` / `displayedSpeed = 13`; `Junction.java:54-78` an independent queue per direction, delivering only once `Time.time >= time + speed`.
- `Router.java:13` `speed = 8`; `Router.java:61` `time += 1f / speed * delta()`; `Router.java:100-129` `getTileTarget` rotation.
- `StackConveyor.java:64-68` `stats.add(Stat.itemsMoved, round(itemCapacity * speed * 60))`.
- `BufferedItemBridge.java:12-14` `speed = 40` (default) / `bufferCapacity = 50` / `displayedSpeed = 11`; `BufferedItemBridge.java:36-47` `buffer.poll` and `timer(timerAccept, 4 / timeScale)`.
- `ItemBridge.java:157-165` `positionsValid` same-row/same-column constraint; `ItemBridge.java:355-368` `updateTransport` delivering per `transportTime`.
- `MassDriver.java:29-36` `rotateSpeed/translation/minDistribute/reload`; `MassDriver.java:192-206` firing conditions; `MassDriver.java:290-303` `fire()` packing the whole stock; `MassDriver.java:66-69` the shot-rate stats.
- `DirectionalUnloader.java:25-26` `speed` / `allowCoreUnload`; `DirectionalUnloader.java:93-118` the `unloadTimer` cycle.
- `content/Blocks.java:2068-2267` the concrete assignments of every transport block (the origin of this table's numbers).

## Measurements and counter-examples

**Counter-example 1 (`displayedSpeed` cannot be reverse-engineered into real throughput)**: `titanium-conveyor` has `speed = 0.0801` tiles/tick, which by `0.0801 × 60 / 0.4` should be **12.0 items/s**, yet the game UI says **10 items/s** (Blocks.java:2080); `armored-conveyor` likewise computes 12.0 from 0.08 tiles/tick while the UI says 10 (v160.7) / 11 (v159.3 source, Blocks.java:2094). The deviation is 17–20%, which is why the game itself uses `displayedSpeed` instead of computing on the fly. Any "conveyor = X items/s" claim must state which convention it uses.

**Counter-example 2 (a junction is not 6 items, it is 24)**: `capacity = 6` is often read as "the whole junction buffers 6 items". The actual construction is `DirectionalItemBuffer(capacity)` (Junction.java:46), i.e. **one 6-item queue per direction**, 24 items across the four; and crossing takes `speed = 26` tick (Junction.java:62), so its throughput is only `displayedSpeed = 13` items/s, not "infinitely straight through".

**Counter-example 3 (`duct`'s `speed = 4` is not a speed)**: treating a duct's 4 as "4 tiles/tick" yields 240 items/s; `Duct.java:194` actually reads `progress += edelta()/speed*2`, so **the larger the speed, the slower it moves** — 4 corresponds to 15–20 items/s. The two `speed` fields of conveyors and ducts point in opposite directions.

**Counter-example 4 (a mass driver with 9 items never fires)**: `minDistribute = 10` (Blocks.java:2166-2173, MassDriver.java:31), so with 9 items in its own stock, or 9 tiles of free space at the other end, the condition `items.total() >= minDistribute && link.block.itemCapacity - link.items.total() >= minDistribute` (MassDriver.java:192-193) fails and the driver rotates forever without firing. It looks "broken", but it is just the threshold.

**Counter-example 5 (a diagonal phase bridge has no meaning)**: `positionsValid` compares distances only when `x1 == x2` or `y1 == y2`, and otherwise returns `false` outright (ItemBridge.java:157-165). Place two phase bridges 3 tiles apart diagonally: the distance 4.2 px looks well inside `range = 12`, yet the link never forms.

**Counter-example 6 (backpressure stops units but loses no cargo)**: when a conveyor jams, `clogHeat` rises to 1 (Conveyor.java:291-295); `unitOn` then returns immediately and no longer accelerates units (Conveyor.java:229), but the 3 items on the belt stay put and do not vanish. This lets you "glue enemies in place with conveyors", and it never destroys items.

## Common misconceptions

1. **"a jammed conveyor loses items"** — it does not. When `acceptItem` is false the item waits at `ys = 1` and the internal `items` count is unchanged (Conveyor.java:278-289) until the downstream accepts.
2. **"a router splits items evenly across three branches"** — it is approximate round-robin `(i + counter) % proximity.size` (Router.java:119-127), with a single slot of 1 item (Router.java:21) released once every 8 tick (Router.java:61), so a burst all goes down the first line that can accept.
3. **"a junction = a crossroads buffer"** — it only buffers 6 items in its own direction (Junction.java:14, 46), so a blockage on the return path stalls the whole line rather than rerouting cargo to another direction.
4. **"a sorter is zero-latency"** — `instantTransfer = true` (Sorter.java:28) only means "adds no extra tick"; it is still bound by the neighbouring `acceptItem` and by the 8-tick cadence.
5. **"a mass driver spans the map"** — `range = 440` px = **55 tiles** (MassDriver.java:66); beyond that `linkValid` is false and items are simply dumped (MassDriver.java:164-166).
6. **"ducts are slower than conveyors"** — a `duct`'s 15–20 items/s is clearly faster than a `conveyor`'s 5.25 items/s (v160.7); the price is 1 item per tile and running on beryllium/power.

## Related

- W01 blocks and the multiblock anchor (conveyors' `rotate = true`, `underBullets`, size versus tile count)
- W02 recipes and crafting (a production line's output feeding this layer's conveyors)
- W10 storage (pickup priority and capacity of cores/containers/`unloader`)
- W08 payloads (how payload conveyors/routers differ from item conveyors)
- W04 liquids (conduits and conveyors are two entirely independent transport systems)
