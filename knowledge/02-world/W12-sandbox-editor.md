---
id: WORLD.SANDBOX.001
title: Sandbox and editor (buildVisibility / inEditor / instantBuild / rules)
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - mindustry/world/Block.java:88
  - mindustry/world/Block.java:148
  - mindustry/world/Block.java:154-156
  - mindustry/world/Block.java:362
  - mindustry/world/Block.java:370
  - mindustry/world/Block.java:1019-1023
  - mindustry/world/Block.java:1093
  - mindustry/world/Block.java:1535
  - mindustry/world/meta/BuildVisibility.java:10-27
  - mindustry/game/Rules.java:27
  - mindustry/game/Rules.java:51
  - mindustry/game/Rules.java:115-117
  - mindustry/game/Rules.java:143
  - mindustry/world/Build.java:129
  - mindustry/world/Build.java:185
  - mindustry/world/blocks/ConstructBlock.java:294-308
  - mindustry/content/Blocks.java:6704-6761
data:
  - 00-data/blocks.json#id=power-source
  - 00-data/blocks.json#id=item-source
  - 00-data/blocks.json#id=liquid-source
  - 00-data/blocks.json#id=payload-source
  - 00-data/blocks.json#id=heat-source
  - 00-data/blocks.json#id=illuminator
depends: [WORLD.BLOCKS.001, WORLD.BLOCKSTATE.001]
tags: [sandbox, editor, buildVisibility, instantBuild, rules]
tokens: 1177
---

# Sandbox and editor (buildVisibility / inEditor / instantBuild / rules)

## One line

"Can it be built" is decided by three layers: the block's own `buildVisibility` (a visibility object evaluated against runtime conditions), the three booleans `inEditor` / `placeablePlayer` / `instantBuild`, and the current map's `rules` (`infiniteResources` / `editor` / `instantBuild`); the sandbox blocks themselves have nothing special about them, they are just a visibility condition combined with a zero-cost recipe.

## Rules / formulas

### 1. buildVisibility is 12 condition objects, not an enumeration

- `mindustry/world/meta/BuildVisibility.java:7-31` is `class BuildVisibility`, with a single field `Boolp visible`, and `visible()` (:25-27) re-evaluates on every call.
- The 12 static constants (:10-21): hidden = constantly false, shown = constantly true, debugOnly = false, editorOnly = `rules.editor`, coreZoneOnly = the map contains a core-zone block, worldProcessorOnly = `rules.editor || rules.allowEditWorldProcessors`, sandboxOnly = `Vars.state == null || rules.infiniteResources`, campaignOnly = not in game or in campaign, legacyLaunchPadOnly / notLegacyLaunchPadOnly = the campaign rule legacyLaunchPads switch, lightingOnly = lighting present or campaign or infinite resources, fogOnly = fog present or editor or not in game.
- Decision entry points: `Block.java:1093` `isVisible() = buildVisibility != hidden && buildVisibility != debugOnly`; `Block.java:1535` treats a block as locked when `!buildVisibility.visible() && !state.rules.revealedBlocks.contains(this)`.
- Build side: `Build.java:185` only checks `type.isPlaceable()` and the environment when not in editor mode; `Block.java:1019/1023` filters the build menu by `rules.editor` / `rules.hideBannedBlocks`.
- Default: `Block.java:362` `buildVisibility = BuildVisibility.hidden`, so a block that forgets `requirements(...)` never shows up in the menu by default.

### 2. The three booleans, their defaults and meanings

- `Block.java:88` `inEditor = true`: whether it appears in the editor; 24/447 are false (remove-wall, remove-ore, cliff, build1–build16, the legacy-mech-pad and legacy-unit-factory family, command-center) [src: jar raw].
- `Block.java:154` `placeablePlayer = true`: manual placement by the player (all 447 true, 0 false) [src: jar raw].
- `Block.java:156` `placeableOn = true`: whether it can be placed over floors/blocks; `Block.java:148` `privileged = false`: only 4 are true (world-processor, world-cell, world-message, world-switch); an ordinary processor cannot place them.
- `Block.java:370` `instantBuild = false`: whether building progress is skipped after placement; 139/447 are true, overwhelmingly floors and walls (`Floor.java:113`, `RemoveWall.java:18` set it true explicitly) [src: jar raw].

### 3. The rules side: three switches make the sandbox

- `Rules.java:27` `infiniteResources` (default false): building does not consume core items (`ConstructBlock.java:371`), progress is satisfied immediately (:308), deconstruction ignores the threshold (:382), and `Block.sense(Content)` returns 0 outright (`Block.java:1668`).
- `Rules.java:143` `instantBuild` (default false): blocks in the build queue complete at once, checked as `result.instantBuild` in `Build.java:129`.
- `Rules.java:51` `editor = false`: when true it bypasses the menu filter at `Block.java:1019` and the visibility/environment checks at `Build.java:185`.
- Multiplier defaults: `Rules.java:115` `buildCostMultiplier = 1f`, :117 `buildSpeedMultiplier = 1f` (both enter ConstructBlock's progress and cost arithmetic).
### 4. The 14 sandbox / editor-only blocks

- 9 sandboxOnly (`Blocks.java:6704-6761`): power-source, power-void, item-source, item-void, liquid-source, liquid-void, payload-source, payload-void, heat-source, all with `requirements(cat, BuildVisibility.sandboxOnly, with())`, i.e. **zero cost**.
- Parameters: power-source `powerProduction = 1000000f/60f` (16666.7/tick = 1000000/s, the source writes this as 100 万/s) [src: Blocks.java:6706]; heat-source `heatOutput = 1000`, `warmupRate = 1000`, size 1, itemCapacity 0; payload-source / payload-void `size = 5`; liquid-source / liquid-void `floating = true`.
- 2 editorOnly: shield-projector (`Blocks.java:2049`, size 3, `consumePower(5f)` = 300/s) [src: Blocks.java:2053] and large-shield-projector (:2057, size 4, `radius = 400f`).
- Other visibility-only cases: illuminator is lightingOnly (:6765, brightness 0.75, radius 140, `consumePower(0.05f)` = 3/s) [src: Blocks.java:6765-6768]; core-zone is coreZoneOnly (:3128); world-processor and 4 such blocks are worldProcessorOnly (:6950-6979); 2 are debugOnly (:1555, :1688).

## Numbers

Table A: distribution of the editor/sandbox boolean fields across the 447 blocks (jar v160.7 reflection raw, source [src: jar raw 447 条]).

| Field | Special value | Share | Source |
| --- | --- | --- | --- |
| inEditor = false | 24 | 5.4% | [src: Block.java:88 + jar raw] |
| placeablePlayer = false | 0 | 0% | [src: Block.java:154 + jar raw] |
| instantBuild = true | 139 | 31.1% | [src: Block.java:370 + jar raw] |
| placeableLiquid = true | 139 | 31.1% | [src: Block.java:158 + jar raw] |
| privileged = true | 4 | 0.9% | [src: Block.java:148 + jar raw] |

Table B: the 12 BuildVisibility conditions and their result under default rules (single player, no rules).

| Constant | Condition (BuildVisibility.java:10-21) | Visible under default rules |
| --- | --- | --- |
| hidden | constantly false | no |
| shown | constantly true | yes |
| debugOnly | constantly false | no |
| editorOnly | `rules.editor` | no |
| sandboxOnly | `state == null || rules.infiniteResources` | no |
| campaignOnly | not in game or campaign | no (ordinary game) |
| lightingOnly | lighting / campaign / not in game / infinite resources | no |
| fogOnly | fog / editor / not in game | no |
| coreZoneOnly | map has core-zone or not in game | no |
| worldProcessorOnly | editor or allowEditWorldProcessors | no |
| legacyLaunchPadOnly | campaign legacyLaunchPads and the advanced launch pad is unlocked | no |
| notLegacyLaunchPadOnly | not in game / infinite resources / non-legacy campaign | depends on mode |

Table C: the three rules switches (Rules.java defaults) [src: Rules.java:27,51,143].

| Field | Default | Effect once enabled |
| --- | --- | --- |
| infiniteResources | false | building free, instantly satisfied, deconstruction threshold-free, sense(Item) reads 0 |
| instantBuild | false | the build queue completes immediately (Build.java:129) |
| editor | false | bypasses the menu filter and the placement environment checks (Block.java:1019, Build.java:185) |
## Source anchors

- `mindustry/world/meta/BuildVisibility.java:7-31` the class itself and the 12 constants; :25-27 `visible()` evaluates every time.
- `mindustry/world/Block.java:88` inEditor, :148 privileged, :154 placeablePlayer, :156 placeableOn, :158 placeableLiquid, :362 buildVisibility defaults to hidden, :370 instantBuild.
- `mindustry/world/Block.java:1093` `isVisible()`; :1535 `unlocked()` uses `visible()` to judge locked blocks.
- `mindustry/world/Block.java:1019-1023` menu filtering: `rules.editor` and `rules.hideBannedBlocks`.
- `mindustry/game/Rules.java:27` infiniteResources; :51 editor; :115-117 buildCostMultiplier / buildSpeedMultiplier; :143 instantBuild.
- `mindustry/world/Build.java:129` `result.instantBuild`; :185 visibility/environment checks only outside the editor.
- `mindustry/world/blocks/ConstructBlock.java:294-308` progress and cost short-circuit under infinite resources; :371 no core items consumed; :382 the deconstruction threshold.
- `mindustry/content/Blocks.java:6704-6761` the nine sandboxOnly blocks and their parameters; :2049/:2057 the two editorOnly ones; :6765 lightingOnly.
- `mindustry/world/blocks/environment/Floor.java:113` and `RemoveWall.java:18` set `instantBuild = true` explicitly (floors / the removal tool do not take part in building progress).

## Measurements and counter-examples

- **Counter-example 1 (sandboxOnly has nothing to do with "map type")**: the condition is `Vars.state == null || rules.infiniteResources` (`BuildVisibility.java:16`). On an ordinary map, ticking infinite resources in the rules makes the nine sandbox blocks appear in the build menu immediately; conversely, turning infinite resources off on a campaign map makes them vanish - it is not the "sandbox mode" map attribute that does it.
- **Counter-example 2 (the sandbox blocks are not "cheat blocks", they are zero-cost blocks)**: all nine write `requirements(..., with())` (`Blocks.java:6705-6750`) - an empty requirement list, hence cost 0; they carry no privileged code either, and power-source is nothing but `powerProduction = 1000000f/60f` (:6706).
- **Counter-example 3 (inEditor=false does not mean unbuildable)**: remove-wall, remove-ore, cliff, build1–build16 and others, 24 blocks, do not show in the editor (`Block.java:88 + jar raw`), but they can still exist in a map save, and remove-wall has `instantBuild = true` (`RemoveWall.java:18`).
- **Counter-example 4 (placeablePlayer all true does not mean you can build anywhere)**: none of the 447 blocks has placeablePlayer false; what actually stops you is `isPlaceable()` and the environment checks at `Build.java:185`, plus the legality rules of `Build.validPlace` (see W01).
- **Counter-example 5 (instantBuild has two sources)**: the block field (`Block.java:370`) only affects "this one block", the rules field (`Rules.java:143`) affects the whole game; testing by changing only the former will show building progress still present.
- **Counter-example 6 (privileged is a hard gate)**: world-processor / world-cell / world-message / world-switch, four `privileged = true` blocks (`Block.java:148`), cannot be placed from an ordinary `micro-processor` (`Block.java:784` returns false outright).

## Common misconceptions

1. **"The sandbox blocks are mod content"**: no, they are all in vanilla `mindustry.content.Blocks` (:6704-6761), gated purely by buildVisibility [src: Blocks.java:6704-6761].
2. **"infiniteResources only means building is free"**: it also satisfies building progress instantly (`ConstructBlock.java:308`), removes the deconstruction threshold (:382), and makes `Block.sense(Item)` constantly 0 (`Block.java:1668`).
3. **"buildVisibility is a boolean"**: it is a class holding a `Boolp`, with `visible()` re-evaluated every call, so flipping rules inside the same save changes the menu immediately (`BuildVisibility.java:25-27`).
4. **"The editor can place every block"**: the 24 with inEditor=false never appear (`Block.java:88 + jar raw`).
5. **"instantBuild skips the building progress animation"**: what it affects is whether building completes at once; floor blocks set it true because they never took part in building in the first place (`Floor.java:113`).
6. **"placeableOn=false means unbuildable"**: it only means existing floors/blocks cannot be covered; whether you may build still depends on `placeableLiquid` and `Build.validPlace`.

## Related

- [[WORLD.BLOCKS.001]] placement legality, size and anchors (the editor uses the same decisions)
- [[WORLD.BLOCKSTATE.001]] configurable / enabled and their relationship to `rules.editor`
- [[WORLD.POWER.001]] power-grid behaviour of generators such as power-source
- logic and privileged processors are in `knowledge/06-mlog/`;
- campaign rules (legacyLaunchPads and so on) are in `knowledge/05-campaign/`