---
id: WORLD.STORAGE.001
title: Storage - the core capacity measure, containers / vaults, and unloader transfer priority
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src: [src: Blocks.java:3127-3260, src: CoreBlock.java:150-158, src: CoreBlock.java:695-735, src: StorageBlock.java:17-140, src: Unloader.java:99-232]
data: [00-data/blocks.json#id=core-shard, 00-data/blocks.json#id=core-nucleus, 00-data/blocks.json#id=container, 00-data/blocks.json#id=vault, 00-data/blocks.json#id=reinforced-container, 00-data/blocks.json#id=unloader, 00-data/blocks.json#id=duct-unloader, 00-data/blocks.json#id=liquid-tank]
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001, WORLD.POWER.001]
tags: [storage, core, container, vault, unloader, itemCapacity, storageCapacity, coreMerge]
tokens: 1711
---

# W10 Storage: core capacity, containers and unloaders

## One line

Cores (CoreBlock) and containers (StorageBlock) use two different capacity measures: a core treats "each item type up to storageCapacity" as its ceiling, and a coreMerge container (container/vault) pressed against a core hands its own inventory array straight over for the core to share, contributing only its itemCapacity figure to the core's total capacity; only a container placed on its own is "each item type up to itemCapacity, mutually isolated". The unloader (Unloader) is the only vanilla block that actively moves inventory between blocks, moving 1 item every speed ticks and using a five-level comparator to pick both source and destination at once - its job is to level the load ratio, not to empty anything.

## Rules / formulas

### 1. Three fields decide "how much can it hold"

| Field | Declared at | Default | Effect |
|---|---|---|---|
| itemCapacity | Block.java:75 | 10 | per-block capacity base; multiblocks do not multiply by size² |
| separateItemCapacity | Block.java:73 | false | when true each item type gets its own slice, otherwise the capacity is shared |
| unloadable | Block.java:106 | true | whether unloaders / logic may treat it as an "extractable" container |

StorageBlock hard-codes three more switches in its constructor: separateItemCapacity=true (StorageBlock.java:26), allowResupply=true (:29), group=BlockGroup.transportation, flags=storage, envEnabled=Env.any (:19-38) - and outputsItems()=false (:36-38), so a container never pushes anything out, it can only be taken from.

### 2. Core capacity is computed, not itemCapacity

CoreBlock.CoreBuild.onProximityUpdate (CoreBlock.java:704-735) recomputes on every adjacency change:

1. Other same-team cores merge their inventory arrays first: `this.items = other.items` (:708-712).
2. The core's own itemCapacity plus the itemCapacity of adjacent coreMerge containers: `storageCapacity = itemCapacity + proximity.sum(e -> owns(e) ? e.block.itemCapacity : 0)` (:715).
3. Those containers keep no inventory of their own; they point items at the core and register linkedCore: `t.items = items; ((StorageBuild)t).linkedCore = this;` (:716-719).
4. The capacity of all same-team cores is summed together (:721-724), so multiple cores share one pool and one ceiling.
5. Each item type is truncated to the ceiling: `items.set(item, Math.min(items.get(item), storageCapacity))` (:728).

The key corollary is written at :696-702: `acceptItem` tests `items.get(item) < getMaximumAccepted(item)`, and `getMaximumAccepted` returns `storageCapacity` - meaning 4000 is **per item type**, 4000 each, not 4000 in total. The UI bar only looks like a total because the denominator at :150 is `storageCapacity * content.items().count(unlockedNow)`.

### 3. Containers: per-type capacity when alone, a "core compartment" when adjacent

With a container placed on its own (not adjacent to a core), separateItemCapacity=true applies: one container's 300 is **300 of each item type**, and vault's 1000 is 1000 of each. Once it is covered by a core's proximity (the owns test is in CoreBlock.java:789-791: must be a StorageBlock with coreMerge true and linkedCore null or that very core), its items pointer is swapped for the core's array (:717) and its capacity figure is folded into the core's storageCapacity (:715) - at that point the container holds no inventory of its own, it is a viewing window onto a slice of the core's stock.

Two methods in the other direction are the evidence of "disabled after linking": `canPickup()` is true only when `linkedCore == null` (StorageBlock.java:132-134), `allowDeposit()` is constantly true once linked (:137-139); getMaximumAccepted forwards the core's figure directly (:96), and a sensor read of itemCapacity also returns the core's (:114). On destruction, only an unlinked container returns its old inventory and clamps it (:118-130).

Erekir's two reinforced containers turn coreMerge off: `coreMerge = false` (Blocks.java:3244, 3252), so reinforced-container/reinforced-vault always count capacity independently, even pressed against a core.

### 4. Unloader: one item per cycle, five-level comparator

Cycle: `if(((unloadTimer += delta()) < speed) || (possibleBlocks.size < 2)) return;` (Unloader.java:163) - one cycle every speed ticks, at most **1 item** moved per cycle. The displayed rate is therefore 60/speed items/s (:63 `stats.add(Stat.speed, 60f / speed, StatUnit.itemsSecond)`).

The adjacency scan only picks up blocks that can trade (:143-158):
- `canLoad = !(other instanceof CoreBuild || other instanceof StorageBuild)` (:148) - cores and containers "cannot actively receive", they are sources only;
- `canUnload = other.canUnload() && (allowCoreUnload || canLoad || (StorageBuild b && b.linkedCore == null)) && other.items != null` (:149).

The transfer order is decided by the comparator (:99-111); after sorting high to low it takes **the first that can receive as destination and the last that can give as source** (:202-215):
1. core-like blocks first (`!notStorage`);
2. "can output but not accept" blocks prefer to be sources;
3. "can accept but not output" blocks prefer to be destinations;
4. loadFactor ascending (:108, the lower loaded block prefers to be the destination);
5. lastUsed descending (:110, the longest unused gets priority).

The actual transfer has one more condition: `dumpingFrom.loadFactor != dumpingTo.loadFactor || !dumpingFrom.canLoad` (:218) - equal load ratios mean no transfer, which is why the unloader is a balancer, not an emptier. On success `unloadTimer %= speed` (:228); on failure it only clamps without accumulating (:230).

Item choice: with sortItem set it moves only that item (:167-168), otherwise it rotates through the full item table by `rotations` (:172-180), switching type every cycle so a single item cannot jam it.

### 5. Liquid storage, and "the number is an inherited default"

Liquid tanks are a separate line: liquid-container 700, liquid-tank 1800, reinforced-liquid-container 1000, reinforced-liquid-tank 2700 (00-data/blocks.json#id=liquid-tank and so on); their hasItems=false and hasLiquids=true, and the itemCapacity reading of 10 is just the Block.java:75 default.

Likewise, cores and ordinary containers having liquidCapacity=10 (00-data/blocks.json#id=core-shard, #id=container) is also an inherited value: both classes have hasLiquids=false, so that 10 never takes effect. When reading 00-data you must check the two booleans hasLiquids/hasItems before the capacity figures - reading the number alone gets you fooled by defaults.

### 6. Core building and team rules

- core-shard is the only alwaysUnlocked core, and it is BuildVisibility.coreZoneOnly (Blocks.java:3128-3129), placeable only inside the core zone; buildCostMultiplier=2 (:3136) means blueprint copies cost double.
- Erekir's three cores have requiresCoreZone=true, incinerateNonBuildable=true (items that cannot be built are burned outright when thrown in), buildCostMultiplier=0.7 [src: Blocks.java:3167-3223].
- Whether an unloader may take from a core is decided by CoreBuild.canUnload: `block.unloadable && state.rules.allowCoreUnloaders` (CoreBlock.java:282-284) - switch that rule off and no unloader can pull from any core.
- Core explosion / destruction goes through onDestroyed (:629-657); with coreCapture=true it only does a dynamic explosion and does not start fires, so a just-destroyed core is not immediately re-captured.

## Numbers

### Table 1 | cores (v160.7 jar, each row verifiable in 00-data/blocks.json)

| Block | size | health | itemCapacity (per item type) | unitCapModifier | spawned unit | armor |
|---|---|---|---|---|---|---|
| core-shard | 3 | 1100 | 4000 | 8 | alpha | 0 |
| core-foundation | 4 | 3500 | 9000 | 16 | beta | 0 |
| core-nucleus | 5 | 6000 | 13000 | 24 | gamma | 0 |
| core-bastion | 4 | 4500 | 2000 | 15 | evoke | 5 |
| core-citadel | 5 | 16000 | 3000 | 15 | incite | 10 |
| core-acropolis | 6 | 30000 | 4000 | 15 | emanate | 15 |

unitCapModifier is assigned line by line at Blocks.java:3138/3150/3163/3185/3202/3220; armor at :3177/3197/3215. health comes from scaledHealth squared by tile count (Blocks.java:3229): container declares scaledHealth 55 ⇒ 220; vault 55 ⇒ 495; reinforced-container declares 120 ⇒ 480 (:3243), reinforced-vault 120 ⇒ 1080 (:3251).

### Table 2 | storage blocks

| Block | size | health | itemCapacity | separate | coreMerge | Notes |
|---|---|---|---|---|---|---|
| container | 2 | 220 | 300 | true | true | titanium 100 (Blocks.java:3226) |
| vault | 3 | 495 | 1000 | true | true | titanium 250 + thorium 125 (:3233) |
| reinforced-container | 2 | 480 | 160 | true | false | never merges (:3244) |
| reinforced-vault | 3 | 1080 | 900 | true | false | never merges (:3252) |
| core-shard | 3 | 1100 | 4000 | false | — | unloadable (unloadable=1) |
| liquid-container | 2 | 160 | 10 (unused) | — | — | liquidCapacity 700 |
| liquid-tank | 3 | 500 | 10 (unused) | — | — | liquidCapacity 1800 |
| liquid-router | 1 | 40 | 10 (unused) | — | — | liquidCapacity 120, relay only |

### Table 3 | unloaders and throughput worked examples

| Block | size | health | speed (ticks/item) | Rate | Notes |
|---|---|---|---|---|---|
| unloader | 1 | 70 | 60/11≈5.4545 | 11 items/s | allowCoreUnload=true, may take from cores [src: Blocks.java:2160-2164] |
| duct-unloader | 1 | 120 | 4 | 15 items/s | allowCoreUnload=false, solid=false, underBullets=true [src: Blocks.java:2227-2233] |

Worked examples (all using the figures from Table 1 / Table 2):
- One unloader moving from a container to another container at 11 items/s empties a 1000-item vault in 1000/11 ≈ 91 s.
- A single duct-unloader at 15 items/s [src: Blocks.java:2227-2233] empties 1000 items in 66.7 s; two in parallel give 30 items/s, but only if the source side has at least 2 neighbouring blocks, otherwise Unloader.java:163 returns immediately.
- A core plus 4 adjacent containers: storageCapacity = 4000 + 4×300 = 5200 (CoreBlock.java:715); at that point the 4 containers' items are already the same array, so readings change in lockstep.
- A core filling one item type to full takes 4000/11 ≈ 364 s (single unloader), while the UI bar shows 4000/(5200 × number of unlocked item types).

## Source anchors

- world/Block.java:75 `public int itemCapacity = 10;` (default capacity)
- world/Block.java:73 `public boolean separateItemCapacity = false;`
- world/Block.java:106 `public boolean unloadable = true;`
- world/blocks/storage/StorageBlock.java:26 separateItemCapacity=true; :17 coreMerge=true; :29 allowResupply=true
- world/blocks/storage/StorageBlock.java:51 linkedCore field; :55 acceptItem forwarding; :59-61 canUnload forwarding; :96 getMaximumAccepted forwarding
- world/blocks/storage/StorageBlock.java:100-103 explosionItemCap = linkedCore!=null ? min(itemCapacity/60, 6) : itemCapacity
- world/blocks/storage/StorageBlock.java:132-139 canPickup / allowDeposit
- world/blocks/storage/CoreBlock.java:150 the usage bar denominator storageCapacity×item type count
- world/blocks/storage/CoreBlock.java:282-284 canUnload = unloadable && rules.allowCoreUnloaders
- world/blocks/storage/CoreBlock.java:715-724 the three-part storageCapacity sum + shared items pointer
- world/blocks/storage/CoreBlock.java:789-791 owns() tests coreMerge + linkedCore
- world/blocks/storage/Unloader.java:99-111 the five-level comparator; :163 the cycle gate; :218 the balancing condition; :228 the timer modulo

## Measurements and counter-examples

1. **A core's 4000 is a per-item-type ceiling, not a total.** Proof: acceptItem/getMaximumAccepted at CoreBlock.java:696-701 compare `items.get(item)` with storageCapacity only, never subtracting what other items occupy; only the UI bar at :150 divides total by (storageCapacity × item type count). So one core-shard can hold 4000 copper + 4000 lead + 4000 silicon at once... while the bar still reads about 1/22 full.
2. **Put a container next to a core and its "300" disappears.** Proof: CoreBlock.java:715-719 replaces its items pointer with the core array and sets linkedCore; afterwards getMaximumAccepted at StorageBlock.java:96 returns the core's storageCapacity, not 300. Add a 5th container now and capacity grows by 300, but the inventory is not recorded separately.
3. **Reinforced containers turn out to be "independent storage".** Proof: Blocks.java:3244/3252 explicitly set coreMerge=false, so when reinforced-container is pressed against a core owns() returns false (CoreBlock.java:790), and neither capacity nor inventory merges.
4. **An unloader does not empty a container.** Proof: Unloader.java:218 requires the two ends to differ in loadFactor before moving; two empty containers never trade, and one full plus one empty moves 1 item/cycle until the ratios match.
5. **unloader is slower than duct-unloader.** Proof: unloader speed=60/11≈5.45 ticks/item = 11 items/s [src: Blocks.java:2162], duct-unloader speed=4 = 15 items/s [src: Blocks.java:2230], and the latter does not even need titanium.
6. **container's liquidCapacity=10 in 00-data is a fake number.** Proof: 00-data/blocks.json#id=container has hasLiquids false, and Block.java:75's itemCapacity default of 10 and the liquidCapacity default come from the same source - the capacity field never enters a calculation.

## Common misconceptions

- **"Core capacity is one pool shared by all resources, full means you cannot deliver."** Only the UI bar normalises by total; the delivery test is per item (CoreBlock.java:696-701), and full copper does not block lead.
- **"A container's 300 means 300 in total."** Containers have separateItemCapacity=true (StorageBlock.java:26): 300 is 300 of each item type, so one container can in principle hold 300×22 types.
- **"Putting a container next to a core adds storage slots."** What it adds is the number in the core's storageCapacity (+300), while losing its independent inventory; to keep the two stocks separate use a coreMerge=false reinforced container, or do not place it adjacent.
- **"An unloader keeps moving items from A to B."** It is a ratio balancer (Unloader.java:218) and stops once both ends match; forcing one-way movement needs conveyors/bridges or a logic setprop.
- **"duct-unloader is the upgraded unloader and can take from cores."** The reverse: duct-unloader has allowCoreUnload=false and cannot pull from a core; only unloader may.
- **"A core's unloadable=1 means unloaders can always take from it."** It also needs rules.allowCoreUnloaders true (CoreBlock.java:283); with that off in sandbox / Rules, every core becomes input-only.

## Related

- WORLD.BLOCKS.001 - size, itemCapacity and the general rules of multiblock anchors
- WORLD.LOGISTICS.001 - throughput of conveyors / routers / mass drivers, to set against the unloader's 11/15 items/s
- WORLD.POWER.001 - batteries are storage blocks too, but they store charge rather than items
- WORLD.LIQUIDS.001 - liquid tanks at 700/1800/1000/2700 and how they relate to pipe capacity
- WORLD.CRAFTING.001 - how factories pull materials from cores / containers
- WORLD.PAYLOAD.001 - payload blocks do not interchange with item inventories
