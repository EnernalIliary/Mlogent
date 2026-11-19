---
id: WORLD.BLOCKS.001
title: The block model and the multiblock anchor
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/Vars.java:135"
  - "Mindustry-Source/core/src/mindustry/world/Block.java:112-160"
  - "Mindustry-Source/core/src/mindustry/world/Build.java:237-270"
  - "Mindustry-Source/core/src/mindustry/world/Tile.java:219-279"
  - "MBO/gamedata/v160.7/gamedata.json (jar 反射，447 blocks)"
data: [00-data/blocks.json]
depends: []
tags: [blocks, multiblock, anchor, placement, tileSize]
tokens: 1175
---

## In one sentence

A Mindustry map is 8px to a tile; a block's `size` says how many n×n tiles it covers, and placement takes **the tile under the cursor as the anchor** and expands by `offset = -(size-1)/2` (integer division) — an odd size is centred on the cursor, an **even size sits up-left**, and the n² tiles share a single `Building` entity.

## Rules / formulas

### 1. Tiles and pixels

```
tilesize = 8                          // px / tile  [src: Vars.java:135]
tilePayload = tilesize * tilesize     // = 64 px², 载荷面积单位  [src: Vars.java:137]
blockPx = size * 8                    // 方块视觉/碰撞边长
bounds(x,y) = Rect(size*8) 中心 (x*8+offset, y*8+offset)   // [src: Block.java:1010-1012]
```

### 2. The multiblock anchor (the easiest one to get wrong)

```
offset = -(size - 1) / 2      // Java int 除法，向零取整  [src: Build.java:237-238, Tile.java:256]
覆盖格 = [x + offset, x + offset + size - 1] × 同 y
```

| size | offset | Columns covered, relative to the cursor | Centred | Pixel edge |
|---|---|---|---|---|
| 1 | 0 | x | centred | 8px |
| 2 | 0 | x … x+1 | **up-left** | 16px |
| 3 | -1 | x-1 … x+1 | centred | 24px |
| 4 | -1 | x-1 … x+2 | up-left | 32px |
| 5 | -2 | x-2 … x+2 | centred | 40px |
| 6 | -2 | x-2 … x+3 | up-left | 48px |

The even-size shift up-left is not a bug: `-(size-1)` gives -1 for size=2, and `-1/2` is `0` in Java, so the cursor tile is **row 0, column 0** of the covered block. The editor applies the same logic at `[src: MapEditor.java:228-231]`.

### 3. One Building, n² proxy tiles

```java
// Tile.java:254-279  放置多格方块时
if(block.isMultiblock()){
    int offset = -(block.size - 1) / 2;
    Building entity = this.build;
    for(int pass = 0; pass < 2; pass++){          // 两遍：先清场，再填充
        for(int dx = 0; dx < block.size; dx++)
          for(int dy = 0; dy < block.size; dy++){
            if(!(worldx == x && worldy == y)){
                if(pass == 0) other.setBlock(Blocks.air);   // 清场
                else { other.build = entity; other.block = block; }  // 代理
            }
        }
    }
}
```

- A covered tile's `tile.block` is that block as well (rendering and occupancy agree), but `tile.build` points at the **centre** entity.
- `tile.centerX()/centerY()` return the centre tile coordinates for a covered tile `[src: Tile.java:219-225]` — when iterating tiles and you want "this multiblock", use center rather than `tile.x`.
- `isMultiblock()` only tests `size > 1` `[src: Block.java:1014-1016]`.

### 4. Placement validity (order is the semantics)

`validPlace` checks the following in order `[src: Build.java:183-270]`:

| Order | Check | Fails when |
|---|---|---|
| 1 | `type.environmentBuildable()` / `isPlaceable()` | building is forbidden, or the environment disallows it |
| 2 | core protection (`polygonCoreProtection`, or inside an enemy core's build radius) | nothing may be built near an enemy core |
| 3 | `type.canPlaceOn(tile, team, rotation)` | the floor refuses it (deep water unless floating/placeableLiquid) |
| 4 | campaign darkness `world.getDarkness(x,y) >= 3` | unexplored territory refuses it |
| 5 | `requiresWater` / `placeableLiquid` / shallow-water contact | water is required but absent |
| 6 | loop over every n×n tile: deep water, derelict, `interactable`, same block and rotation, `canReplace` | any single tile is invalid |
| 7 | enemy overlap when `placeRangeCheck` is on (`placeOverlapRange` defaults to 50f) | too close to an enemy building |

### 5. What the four boolean fields really mean

| Field | Definition | Meaning | Not |
|---|---|---|---|
| `solid` | Block.java:112 | the collision body for unit/ground movement, units path around it | does not stop bullets |
| `underBullets` | Block.java:118 | bullets draw **under** this block and pass over it | does not mean "it cannot be hit" |
| `squareSprite` | Block.java:160 | the sprite is an axis-aligned square, rotation turns it without shearing | unrelated to hit tests |
| `rotate` | Block.java:120 | allows 4-way rotation (0..3, `Mathf.mod(rotation,4)`) | does not guarantee the player may rotate it (team/editor limits apply separately) |

## Numbers

| id | size | Tiles | Pixel edge | health | Note |
|---|---|---|---|---|---|
| duo | 1 | 1 | 8px | 250 | smallest turret, rotatable |
| graphite-press | 2 | 4 | 16px | 160 | 2×2 fabricator, not rotatable |
| laser-drill | 3 | 9 | 24px | 360 | 3×3 drill, mines tier-4 ore |
| core-shard | 3 | 9 | 24px | 1100 | 3×3 core, itemCapacity 4000 |
| core-nucleus | 5 | 25 | 40px | 6000 | 5×5 core |
| core-acropolis | 6 | 36 | 48px | 30000 | 6×6, the largest core |
| interplanetary-accelerator | 7 | 49 | 56px | 3920 | 7×7 |
| tetrative-reconstructor | 9 | 81 | 72px | 5830 | one of the largest placeable blocks in vanilla |

The health/size figures above come from the v160.7 jar reflection `[src: jar:v160.7#blocks[name=…].size/health]`, i.e. the same-source fields as `00-data/blocks.json#id=<name>`.

Size distribution (447 blocks, including internal placeholders such as `air`/`spawn`/`build1..build16`):

| size | Count | Share |
|---|---|---|
| 1 | 251 | 56.2% |
| 2 | 64 | 14.3% |
| 3 | 77 | 17.2% |
| 4 | 19 | 4.3% |
| 5 | 19 | 4.3% |
| ≥6 | 17 | 3.8% |

Other counts from the same reflection pass: `rotate=true` 92, `solid=true` 257, `underBullets=true` 40, `squareSprite=false` 0 (in v160.7 every block has a square sprite).

### Do not mix the three block conventions (447 / 253 / 446)

The repository holds three "block lists" with different entry counts; mixing them yields wrong shares:

| File | Entries | Content | When to use |
|---|---|---|---|
| `data/game/blocks.json` | **447** entries (list) | every block the game registers (including internal/historical items such as `air`, `spawn`, `build1..build16`, `legacy-*`) | use it for "how many blocks does vanilla have" |
| `tools/block_attrs.json` | **253** entries (the `blocks` subtree) | only the subset carrying `accepts/build/inputs/power` and similar attributes | use it to look up logic/power interaction attributes |
| `tools/block_sizes.json` | **446** entries (name → size map) | stores a single integer, `name: size` | use it to look up "how many tiles this block takes" |

The 446 vs 447 in `tools/block_sizes.json` is not simply a one-entry gap: it **omits** 6 registered blocks (`target-dummy`, `legacy-mech-pad`, `legacy-unit-factory`, `legacy-unit-factory-air`, `legacy-unit-factory-ground`, `command-center`) while **adding** 5 unregistered keys (`reinforced-` as an empty name, `scathe-missile`, `scathe-missile-phase`, `scathe-missile-surge`, `scathe-missile-surge-split`), hence 447 − 6 + 5 = 446.

The `size` field means "the block occupies **size×size** tiles": `core-shard` size=3 → 9 tiles / 24px; `battery-large` size=3; `power-node-large` size=2 → 4 tiles / 16px; `conduit` size=1 → 1 tile / 8px; `duo` size=1; `tetrative-reconstructor` size=9 → 81 tiles / 72px. The source declares it as `public int size = 1;` in `world/Block.java` (Block.java:215), and placement expands it to n×n per `Build.java:237-242`.

**Do not back out the "1×1 share" from the `block_sizes.json` distribution**: its 446 entries hold 265 1×1 blocks, while the 447 registered blocks give 251 — the 14-entry gap comes from the 6 missing blocks and the 5 scathe keys above, not from a real distribution. To report a share, use the 447-entry list.

## Source anchors

- `Vars.java:135` `public static final int tilesize = 8;` —— the single source of truth for tile width in the whole project.
- `Block.java:213-219` the `size`/`offset`/`sizeOffset` declarations; the comment says outright "changing size often leads to catastrophic issues" (changing size at runtime wrecks saves).
- `Block.java:1010-1012` `bounds()`: `Rect(size*8).setCenter(x*8+offset, y*8+offset)` — the collision/hit box.
- `Build.java:237-242` placement's `offsetx/offsety = -(size-1)/2` and the n×n loop.
- `Build.java:248` adds a darkness check inside the loop only for **size==2**: `type.size == 2 && getDarkness(...) >= 3`.
- `Tile.java:254-279` the multiblock "two-pass" method: first `setBlock(Blocks.air)` to clear, then assign the `build`/`block` proxies.

## Measurements and counter-examples

**Counter-example 1 (even sizes are not centred)**: to build a 2×2 graphite press, put the cursor on the **top-left tile** of the intended 2×2; putting it on the "apparent centre" shifts the whole block one tile right and one tile down. Work it out by hand with the `Build.java:237` formula: size=2 → offset=0, covering x..x+1. In the UI the sprite is drawn down-right from the anchor, so players routinely misjudge it as centred.

**Counter-example 2 (placement swallows existing blocks)**: the first pass of `Tile.setBlock` calls `other.setBlock(Blocks.air)` outright `[src: Tile.java:270-274]`, with **no canReplace check**. A player building by hand is stopped by step 6 of `validPlace`, but the editor and payload drops (`checkVisible=false`) take another path and silently destroy the blocks underneath. Whether a block may be flattened depends on `Block.canReplace` / `replaceable`.

**Boundary (the size=2 darkness check)**: `Build.java:229` checks darkness only at the anchor tile, while `Build.java:248` additionally checks every tile when size==2. So a 3×3 block only needs its centre lit, while a 2×2 needs all 4 lit — the asymmetry is existing source behaviour, not a data error.

## Common misconceptions

1. **"a size=2 block is centred on the mouse"** → wrong. The anchor is always the cursor tile and even sizes sit up-left (`offset=0`); only odd sizes are centred (size=3 → offset=-1).
2. **"solid means it stops bullets"** → wrong. `solid` governs ground passage; stopping bullets/lasers comes from another group of fields (`underBullets`, `absorbLasers`, …); a conveyor with `solid=false, underBullets=true` is the typical case.
3. **"hitting a corner tile of a multiblock does no damage"** → wrong. All n² tiles share one `build` entity (`Tile.java:277`), so hitting any tile hits the whole block.
4. **"`rotate=true` means 4 sprites"** → not necessarily. With `rotateDraw=false` the sprite does not turn with the direction (`Block.java:122`); only the logical facing changes.
5. **"8px is a rendering detail"** → 8px is the **logic tile**, independent of screen zoom; 1 tile in world coordinates = 8 world units.

## Related

- `WORLD.CRAFTING.001` (size affects factory layout and schematic copying)
- `WORLD.LOGISTICS.001` (a conveyor is size=1; what `underBullets` is for)
- `WORLD.PAYLOAD.001` (payload blocks use `size` to compute payload area)
- `WORLD.SANDBOX.001` (`placeablePlayer`/`inEditor` decide editor visibility)
- Data tables: `00-data/blocks.json` (the `size`/`health`/`solid`/`underBullets`/`rotate` fields)
- Chinese/English name mapping: [[WORLD.NAMES.001]] / [[WORLD.NAMES.002]] / [[WORLD.NAMES.003]] (covers all 447 blocks; the UI shows only names)
- Source: `Mindustry-Source/core/src/mindustry/world/Block.java`, `world/Build.java`, `world/Tile.java`, `Vars.java`
