---
id: WORLD.BLOCKSTATE.001
title: Block state and configuration (config / rotation / enabled / @sensor)
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - mindustry/world/Block.java:93-99
  - mindustry/world/Block.java:258
  - mindustry/world/Block.java:270
  - mindustry/world/Block.java:815-829
  - mindustry/world/Block.java:921-929
  - mindustry/world/Block.java:1651-1680
  - mindustry/entities/comp/BuildingComp.java:71
  - mindustry/entities/comp/BuildingComp.java:388-397
  - mindustry/entities/comp/BuildingComp.java:1419-1442
  - mindustry/entities/comp/BuildingComp.java:1949-1964
  - mindustry/entities/comp/BuildingComp.java:2099-2169
  - mindustry/entities/comp/BuildingComp.java:2259-2280
  - mindustry/logic/LAccess.java:7-94
  - mindustry/logic/LExecutor.java:668-710
  - mindustry/logic/LStatements.java:631
  - mindustry/world/blocks/logic/LogicBlock.java:55
data:
  - 00-data/blocks.json#id=sorter
  - 00-data/blocks.json#id=unloader
  - 00-data/blocks.json#id=payload-router
  - 00-data/blocks.json#id=mass-driver
  - 00-data/blocks.json#id=illuminator
  - 00-data/blocks.json#id=micro-processor
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001]
tags: [block-state, config, rotation, sensor, enabled, logic]
tokens: 1430
---

# Block state and configuration (config / rotation / enabled / @sensor)

## One line

Beyond "what it is" (the Block definition) a block also has "how it is right now": the `rotation` baked in at build time (0–3), the mutable `config` (item / block / coordinates / text, dispatched through `configured()`), and the `enabled` flag that logic or the player can switch off; external reads of state go through exactly two ports - `sense(LAccess)` and `sense(Content)`.

## Rules / formulas

### 1. The four-layer structure of config

- Switch fields: `Block.java:258` declares `public boolean configurable;` (default false); `Block.java:95` `saveConfig = false`, `Block.java:97` `copyConfig = true`, `Block.java:99` `clearOnDoubleTap = false`, `Block.java:270` `logicConfigurable = false`.
- Registering listeners: `Block.java:927-929` `config(Class<T> type, Cons2<E,T> config)` writes "type -> callback" into the `configurations` table; `Block.java:921-924` `configClear(Cons<E>)` registers an empty config on `void.class` (that is the path double-click clearing takes).
- Dispatch: `BuildingComp.java:1419-1442` `configured(Unit builder, Object value)`. Type normalisation is at :1422-1427 - null becomes `void.class`, anonymous classes are resolved to their parent, and Item/Block/Liquid/UnitType each fold to their class itself; a table hit calls back, and on a miss with value being another building it recursively takes that building's `config()` and replays it (copying a block, :1435-1440).
- Initiating and saving: `BuildingComp.java:388-392` `configure(Object value)` sets `block.lastConfig = value` first, then `Call.tileConfig(player, self(), value)`; the server side copies with `configureAny` at :395-397. Reading back on load looks only at `Block.java:815-816`: return lastConfig only if `saveConfig && lastConfig != null`.
- Reading the current value: `BuildingComp.java:2028-2032` `config()` is null by default and each block overrides it (Sorter -> item, MessageBlock :219 -> String, MassDriver -> Point2).
- Logic writing config: `BuildingComp.java:2163-2169` only does `configured(null, p1)` when `type == LAccess.config && block.logicConfigurable && !(p1 instanceof LogicBuild)`; that last clause prevents logic blocks from copying configs off each other into a storm.

### 2. Writing rotation 0–3 and the three ways to read it

- Storage: `BuildingComp.java:71` `transient int rotation`; written at build time by `init(tile, team, shouldAdd, rotation)` at :112-123.
- Direction meaning follows `nearby(rotation)` at `BuildingComp.java:522-529`: 0->(x+1, y), 1->(x, y+1), 2->(x-1, y), 3->(x, y-1). That is 0 right, 1 down (Mindustry's screen y axis points down), 2 left, 3 up.
- Relative direction: `BuildingComp.java:532-545` `relativeTo(Building)` converts a neighbour's bearing back to 0–3, returning -1 when not adjacent.
- Logic read: `BuildingComp.java:2112` `case rotation -> rotation` (LAccess.rotation); writing back is in the settable set at `LAccess.java:94`.
- Network bit packing: `BuildingComp.java:226` `rotation = rot & 0b01111111`, the low 7 bits are reserved for rotation.
- Only 92 of 447 blocks have `rotate = true` and show a rotation UI, but the `rotation` field exists on every Building, constantly 0 on those that cannot rotate.
### 3. enabled is a master switch, not demolition

- Default and persistence: `BuildingComp.java:79` `transient boolean enabled = true`; read and written with the block's save at :193 `write.b(enabled ? 1 : 0)` / :237 `this.enabled = on == 1`.
- Setting it: logic `control(enabled)` goes through :2157-2158 `enabled = !Mathf.zero((float)p1)` (writing 0 is what turns it off); `checkAllowUpdate()` :2259-2263 forces false when `!allowUpdate()` (outside a map area, for example).
- Semantics: in `updateConsumption()` at :1949-1964, `!enabled` sets `potentialEfficiency = efficiency = optionalEfficiency = 0` outright and stops `shouldConsumePower` (:1960-1963); the main loop at :2277 is `if(enabled || !block.noUpdateDisabled) updateTile()` - a block that declares `noUpdateDisabled ` still ticks its effects even when switched off.
- Status display: `:638-641` the first branch of `status()` returns `BlockStatus.logicDisable`.
- Read-out: `:2124` `case enabled -> enabled ? 1 : 0`.

### 4. The two @sensor ports: sense(LAccess) and sense(Content)

- `mindustry/logic/LAccess.java` is logic's Getter/Setter enum with 77 constants: 72 without parameters (sensed variables) + 5 with parameters (:81-85 `enabled("to")`, `shoot("x","y","shoot")`, `shootp(true,"unit","shoot")`, `config(true,"to")`, `color("to")`).
- Static collections at `LAccess.java:90-94`: `all = values()`, `senseable = params.length <= 1`, `controls = params.length > 0`, and `settable` is a fixed 15 entries (x, y, velocityX, velocityY, rotation, speed, armor, health, shield, team, flag, totalPower, payloadType, bulletTime, bulletLifetime). Only shoot / shootp have more than 1 parameter, so the sense surface is 75 entries and the control surface 5.
- `BuildingComp.java:2099-2131` `sense(LAccess)` returns double, and unlisted entries fall to `default -> Float.NaN` (:2129, which becomes null on the logic side); rotation, efficiency, totalItems, totalPower (:2116 uses `power.status * capacity` rather than an accumulated amount) and enabled are all defined here.
- Object-valued readings get their own port, `senseObject(LAccess)` :2133-2142: `type` -> block, `firstItem` -> items.first(), `config` -> `config()` only when `configSenseable()`, `payloadType` -> the current payload.
- `sense(Content)` :2145-2153 is the one that counts by content: Item -> `items.get(i)`, Liquid -> `liquids.get(l)`, UnitType/Block -> `getPayloads().get(...)`; illegal content returns NaN.
- On the mlog side: `LStatements.java:631` uses `LAccess.senseable` to generate the valid sensor options; the SenseI in `LExecutor.java:668-710` calls `senseObject` first to test `noSensed`, then falls back to the numeric `sense`, with a special case for size / bufferSize at :706.
- **Block types** (not building instances) have a Senseable implementation too: `Block.java:1651-1663` only gives color/health/solid/size/itemCapacity/liquidCapacity/powerCapacity/id; and `sense(Content)` at `Block.java:1666-1680` returns, for an Item, the **build requirement** (requirements × `rules.buildCostMultiplier`), not the stock.

### 5. The 54 configurable blocks by type

- Item filters (Item): sorter, inverted-sorter, unloader, duct-unloader, surge-router (`00-data/blocks.json#id=sorter`).
- Payload / build (Block or UnitType): payload-router, reinforced-payload-router, constructor, large-constructor, payload-source.
- Coordinates / target (Point2 or Block): mass-driver, payload-mass-driver, large-payload-mass-driver, launch-pad, landing-pad.
- Text and colour: message, reinforced-message, switch, illuminator (LightBlock stores the colour).
- Unit production (UnitType): ground/air/naval-factory and 8 reconstructor/refabricator blocks; note that tank/ship/mech-fabricator are only in `logicConfigurable`, not in `configurable` (see the numbers table).

### 6. Why a processor can "suddenly become invalid"

`BuildingComp.isValid()` tests `tile.build == self() && !dead()`. Multiblocks are placed centre-aligned (`offset = -(size-1)/2`, see [[WORLD.BLOCKS.001]]), so **the moment a 4×4 landing-pad overlaps the tile a processor sits on, the processor's own `tile.build` is replaced by the landing-pad** ⇒ `isValid()` goes false ⇒ every `read x @this <name>` in the program returns constant null; while `sensor t @this @type` still returns `micro-processor` (`@this` is the object reference `exec.build`, it does not consult the tile). The symptom looks like "the variable was never declared", but the block is actually being judged invalid - troubleshooting order: first `sensor t @this @type` to confirm the object is still there, then check whether the tile under it has been covered by a multiblock.

Do not use `building instanceof LogicBlock` to test "is this a processor" either: the real building is the inner class `LogicBlock$LogicBuild`, so `instanceof` is constantly false (assertion table L2-26). The duck test is "has an `executor` and has a `code`".

## Numbers

Table A: distribution of the configuration fields across the 447 registered blocks (jar v160.7 reflection raw, percentages out of 447, source [src: jar raw 447 条]).

| Field | Blocks set true | Share | Source |
| --- | --- | --- | --- |
| configurable | 54 | 12.1% | [src: Block.java:258 + jar raw] |
| logicConfigurable | 22 | 4.9% | [src: Block.java:270 + jar raw] |
| both true at once | 19 | 4.2% | [src: jar raw 交叉] |
| logicConfigurable only (tank/ship/mech-fabricator) | 3 | 0.7% | [src: jar raw] |
| saveConfig | 17 | 3.8% | [src: Block.java:95 + jar raw] |
| copyConfig (true by default) | 443 | 99.1% | [src: Block.java:97 + jar raw] |
| clearOnDoubleTap | 20 | 4.5% | [src: Block.java:99 + jar raw] |
| editorConfigurable | 6 | 1.3% | [src: Block.java + jar raw] |
| commandable | 24 | 5.4% | [src: jar raw] |
| rotate = true | 92 | 20.6% | [src: Block.java:120 + jar raw] |

- The 17 saveConfig blocks = 6 editor palette blocks (colored-floor / colored-wall / character-overlay / character-overlay-white / rune-overlay / rune-overlay-crux) + 11 gameplay blocks (sorter, inverted-sorter, unloader, duct-router, duct-unloader, surge-router, unit-cargo-unload-point, item-source, liquid-source, target-dummy, illuminator) [src: jar raw].
- Exactly 4 blocks have copyConfig false, and all are bridge classes: bridge-conveyor, phase-conveyor, bridge-conduit, phase-conduit [src: jar raw].

Table B: the logic read/write surface (LAccess, 77 constants).

| Collection | Entries | Test | Source |
| --- | --- | --- | --- |
| parameterless constants | 72 | params.length == 0 | [src: LAccess.java:7-78] |
| parameterised constants | 5 | params.length > 0 | [src: LAccess.java:81-85] |
| senseable | 75 | params.length <= 1 | [src: LAccess.java:92] |
| controls | 5 | params.length > 0 | [src: LAccess.java:93] |
| settable | 15 | explicit whitelist | [src: LAccess.java:94] |

Table C: two critical measures (kept out of the prose because it reads them as synonyms).

| Phenomenon | Measure | Source |
| --- | --- | --- |
| writing `enabled` | `!Mathf.zero(p1)`, only p1 == 0 turns it off | [src: BuildingComp.java:2158] |
| rotation encoding | `rot & 0b01111111`, the low 7 bits | [src: BuildingComp.java:226] |
| powerNetIn / powerNetOut | graph statistic × 60 (per second) | [src: BuildingComp.java:2120-2121] |
| totalPower | `power.status * capacity` (buffer fraction), not a stock | [src: BuildingComp.java:2116] |
## Source anchors

- `mindustry/world/Block.java:93` `public @Nullable Object lastConfig;`; :95 saveConfig, :97 copyConfig, :99 clearOnDoubleTap, the three defaults.
- `mindustry/world/Block.java:258` `public boolean configurable;`; :270 `logicConfigurable = false`.
- `mindustry/world/Block.java:815-816` on load `if(saveConfig && lastConfig != null) return lastConfig;`.
- `mindustry/world/Block.java:921-929` the `configClear` / `config(Class, Cons2)` registration entries.
- `mindustry/world/Block.java:1651-1680` Block's own `sense(LAccess)` and `sense(Content)` (the latter returns build requirements).
- `mindustry/entities/comp/BuildingComp.java:71` `transient int rotation`; :79 `enabled = true`.
- `mindustry/entities/comp/BuildingComp.java:388-397` `configure` / `configureAny`; :1419-1442 `configured` dispatch.
- `mindustry/entities/comp/BuildingComp.java:2028-2032` `config()` defaults to null.
- `mindustry/entities/comp/BuildingComp.java:1949-1964` `enabled` zeroes efficiency.
- `mindustry/entities/comp/BuildingComp.java:2099-2169` `sense` / `senseObject` / `control`.
- `mindustry/entities/comp/BuildingComp.java:2259-2280` `checkAllowUpdate` and the main loop `update()`.
- `mindustry/logic/LAccess.java:7-94` the 77 constants and the three static collections senseable/controls/settable.
- `mindustry/logic/LExecutor.java:668-710` SenseI; `mindustry/logic/LStatements.java:631` the source of the sensor options.
- `mindustry/world/blocks/logic/LogicBlock.java:55` `configurable = true`; :653 `config()` returns `byte[]`.

## Measurements and counter-examples

- **Counter-example 1 (copyConfig does not mean "everything is copied")**: the four bridges bridge-conveyor / phase-conveyor / bridge-conduit / phase-conduit have copyConfig false [src: jar raw], because a bridge's "configuration" is its connection relationship, not a value in the `configurations` table; copying a block only replays objects whose `config()` is non-null (BuildingComp.java:1435-1440).
- **Counter-example 2 (one @sensor, two worlds)**: for a **building**, `sensor ... @copper` returns stock (`BuildingComp.java:2146` `items.get(i)`); for a **block type** it returns the build requirement of that item (`Block.java:1666-1680` `r.amount * state.rules.buildCostMultiplier`). Same instruction, different target, results differ by several hundred.
- **Counter-example 3 (micro-processor's config is code)**: `config()` at `LogicBlock.java:653` returns `byte[]`; it is configurable=true but logicConfigurable=false, so logic's `control(config)` cannot write into it (`BuildingComp.java:2165` requires logicConfigurable, and p1 must not be a LogicBuild).
- **Counter-example 4 (switched off is not the same as not updating)**: `BuildingComp.java:2277` `if(enabled || !block.noUpdateDisabled) updateTile()`; a block that declares noUpdateDisabled still runs updateTile at enabled=false, only its production has been zeroed.
- **Counter-example 5 (config types are not just 4)**: normalisation special-cases only Item/Block/Liquid/UnitType (:1424-1427); message stores a String (`MessageBlock.java:219`), switch stores a Boolean (`SwitchBlock.java:74`), illuminator stores a colour, and all of them hit by `value.getClass()`.
- **Counter-example 6 (rotation=1 is downward)**: `BuildingComp.java:522-529` 0->x+1, 1->y+1; treating it as "an angle of 90°" and converting with trig mirrors everything in a coordinate system whose y axis points down.

## Common misconceptions

1. **"configurable=true means logic can change it"**: wrong. Writing config from logic needs `logicConfigurable` (22 blocks); configurable only governs the player UI (54 blocks) [src: Block.java:258,270 + BuildingComp.java:2165].
2. **"rotation is an angle or 90° clockwise"**: wrong, it is an enumeration 0–3 whose meaning is defined by `nearby(rotation)` (0 right / 1 down / 2 left / 3 up) [src: BuildingComp.java:522-529].
3. **"enabled=false detaches it from the power grid / logistics network"**: wrong, the block is still on the graph, only `efficiency = 0` and `shouldConsumePower = false`; neighbours can still connect to it [src: BuildingComp.java:1960-1963].
4. **"@sensor can read any field"**: wrong, only the 75 senseable entries; an unlisted `case` lands on `Float.NaN` (null in logic) [src: BuildingComp.java:2129].
5. **"config is saved with the map"**: wrong, `saveConfig` is false by default and only 17 of 447 blocks enable it [src: Block.java:95 + jar raw].
6. **"double-click clearing works on every block"**: wrong, `clearOnDoubleTap` covers only 20 blocks, and clearing writes through the `configClear` callback registered on `void.class` [src: Block.java:921-924 + jar raw].

## Related

- [[WORLD.BLOCKS.001]] the block itself, size and anchors (which define the range rotation applies to)
- [[WORLD.LOGISTICS.001]] how sorter/unloader filter configs participate in logistics
- [[WORLD.PAYLOAD.001]] payload-router's Block/UnitType config and the canSort test
- [[WORLD.STORAGE.001]] unloader's config(Item) and storage priority
- logic-layer mechanics live in the sensor/control sections of `knowledge/06-mlog/`