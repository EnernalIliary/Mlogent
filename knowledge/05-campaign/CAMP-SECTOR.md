---
id: CAMP.SECTOR.001
title: Sectors, the planet map and tech unlocks — what one campaign tile actually is
domain: camp
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src: Mindustry-Source/core/src/mindustry/type/PlanetGrid.java:211-221; type/Planet.java:224-237,98-99,114-117,452-458; type/Sector.java:24,79-85,89-99,101-117,125-151,181-200,219-247; type/SectorPreset.java:13-130; type/SectorDifficulty.java:6-13; content/Planets.java:46-69,107-114,123-153; content/TechTree.java:16-29,45-48,78-139,169-180; content/UnlockableContent.java:272-289; world/generator/PlanetGenerator.java:173-180; game/SectorInfo.java:27-84,118-210; game/Universe.java:20-26,31-36,71-73,151-244; game/CampaignRules.java:8-43; game/Rules.java:179; ui/dialogs/LaunchLoadoutDialog.java:45-92; core/Logic.java:269-297; Vars.java:127-131
data: [00-data/blocks.json]
depends: [CAMP.WINLOSE.001, CAMP.WAVES.001, CAMP.RULES.001]
tags: [planet map, sector, sectorPreset, techTree, tech unlocks, launchLoadout, legacyLaunchPads, sectorInvasion, storageCapacity]
tokens: 1611
---

## In one line

A sector is one tile on a planet's hexagonal grid, and **every tile has its own save slot** (`Sector.save` + `SectorInfo`). The map size comes from `PlanetGrid.tileCount = 10*3^sectorSize + 2` (Serpulo 272 tiles, Erekir 92), not from hand-placed fixed maps [src: type/PlanetGrid.java:211-213]; tech unlocking has two locks — the node requirements of the `TechTree` and a `SectorComplete` objective (`content/TechTree.java:45-48`); and **resources are not shared across sectors by default** — only launch loadouts (bounded by `launchCapacityMultiplier × core capacity`) and Serpulo's legacy launch pads' offline export carry anything over.

## Rules / formulas

### 1. The planet map is computed, not drawn

```java
// type/PlanetGrid.java:211-221
static int tileCount(int size){ return 10 * Mathf.pow(3, size) + 2; }   // 格子总数
static int cornerCount(int size){ return 20 * Mathf.pow(3, size); }     // 角格数
static int edgeCount(int size){ return 30 * Mathf.pow(3, size); }       // 边格数
```

- Every tile is a `Sector`: in the `Planet` constructor, `grid = PlanetGrid.create(sectorSize); sectors.add(new Sector(this, grid.tiles[i]))` [src: type/Planet.java:224-237].
- `sectorSize` is the 4th planet constructor argument: Serpulo 3 ⇒ 10×27+2 = **272**; Erekir / Tantros 2 ⇒ 10×9+2 = **92** [src: content/Planets.java:123,46,107].
- `sector.id = tile.id` (the tile's index in the grid array), and the starting sector is set by `startSector`: Serpulo **170**, Erekir **10**, Tantros **10** [src: content/Planets.java:153,57,114].
- A sector map's side length is not fixed: `getSectorSize(sector) = (int)(sector.rect.radius * 3200)`, raised by 1 when odd to stay even [src: world/generator/PlanetGenerator.java:173-180] (`getSizeScl() = 3200`).

### 2. What it takes to land (three locks)

```java
Sector.unlocked() = hasBase() || (preset != null && preset.alwaysUnlocked)        // type/Sector.java:89-91
hasBase()        = save != null && info.hasCore
                   && !(Vars.state.isGame() && Vars.state.rules.sector == this && state.gameOver)  // :135-137
Sector.isShielded() = preset != null && preset.shieldSectors.size > 0
                      && preset.shieldSectors.contains(s -> !s.isCaptured())      // :125-127
```

1. **Have a base**: `save != null && info.hasCore` (a save exists and the core is still standing).
2. **Tech unlock**: a sector with `preset.requireUnlock = true` must first be unlocked by the tech tree (the field defaults to true) [src: type/SectorPreset.java:28].
3. **Shielded sector**: while any entry of `preset.shieldSectors` is uncaptured, the sector stays under the shield and cannot be landed on [src: type/Sector.java:125-127].

> The comment at `Sector.java:87-88` claims "only tiles adjacent to wave-free sectors can be landed on", but `unlocked()` contains **no such check**: the adjacency gate lives in the `PlanetDialog` UI layer (**speculation**, no specific line verified in the source).

### 3. The sector state machine: five booleans decide everything

| Test | Formula (source line) | Meaning |
| --- | --- | --- |
| `hasBase()` | `save != null && info.hasCore && !(isBeingPlayed() && gameOver)` [src: type/Sector.java:135-137] | this tile holds your core |
| `isBeingPlayed()` | `state.isGame() && rules.sector == this && !gameOver && !net.client()` [src: type/Sector.java:148-151] | you are fighting in this tile right now |
| `isAttacked()` | while playing: `rules.waves \|\| rules.attackMode`; otherwise: `save != null && (info.waves \|\| info.attack) && info.hasCore` [src: type/Sector.java:129-132] | under wave/invasion attack |
| `isFrozen()` | `isAttacked() && !isBeingPlayed()` [src: type/Sector.java:139-141] | attacked but not being played = time frozen |
| `isCaptured()` | while playing: `!waves && !attackMode`; otherwise: `save != null && !info.waves && !info.attack` [src: type/Sector.java:181-184] | captured (no enemies) |

Two inferences that are easy to get backwards:
- **An attacked sector produces nothing while offline** (`Universe.runTurn()` accumulates `info.production` only under `if(!sector.isAttacked())`) [src: game/Universe.java:207-213].
- **`minutesCaptured` is reset when attacked**, so a sector that was just hit must accumulate 20 minutes again before an invasion can be rolled [src: game/Universe.java:200-204] + `invasionGracePeriod = 20` [src: Vars.java:131].

### 4. Tech unlocks: content lock + research lock + sector-completion lock

```java
// content/TechTree.java:45-48 —— 星区节点自动挂一个 SectorComplete 目标
if(context.content instanceof SectorPreset preset && !objectives.contains(o -> o instanceof SectorComplete))
    objectives.add(new SectorComplete(preset));
```

- **Content lock**: `UnlockableContent.unlocked()`; in campaign the client reads `state.rules.researched`, while single player reads the local unlock table [src: content/UnlockableContent.java:277-281]; the unlock flag persists under the key `"<name>-unlocked"` [src: content/UnlockableContent.java:284-289].
- **Research lock**: `TechNode.requirements` (`ItemStack[]`), scaled up tier by tier by `researchCostMultipliers` [src: content/TechTree.java:94-96,118-123]; completed amounts live in `Core.settings` under the key `"req-<content>-<item>"` [src: content/TechTree.java:169-180].
- **Sector-completion lock**: when the parent content is a `SectorPreset`, `TechTree.node()` inserts `SectorComplete(preset)` into the child's objectives ⇒ **finishing that sector is what unlocks its children**, with no extra research [src: content/TechTree.java:45-48].
- Roots: `SerpuloTechTree.java:15`, `ErekirTechTree.java:65`; the third argument of `nodeRoot(name, content, requireUnlock, ...)` decides whether the root itself must be unlocked too [src: content/TechTree.java:19-29].
- A planet attaches its own tree in `init()`: `techTree = TechTree.roots.find(n -> n.planet == this)` [src: type/Planet.java:452-458].

### 5. Resources across sessions: only two and a half channels

**Channel A: sector inventory (not shared by default)** — `SectorInfo.items` is an `ItemSeq` copied back and forth with the core:

```java
// game/SectorInfo.java:199-210 prepare()：进图前把核心物品抄进 info
items.clear();
for(int i = 0; i < content.items().size; i++) this.items.set(content.item(i), items.get(i));
// game/SectorInfo.java:189-195 write()：存档写回时灌回核心，按 entity.storageCapacity clamp
```

While a sector is not being played, `Sector.addItems()` writes to `info.items`, truncated by `info.storageCapacity`; while it is being played it writes `state.rules.defaultTeam.core().items`, truncated by `core.storageCapacity` [src: type/Sector.java:219-232].

**Channel B: launch loadout (the only transfer with a hard cap)**:

```java
// ui/dialogs/LaunchLoadoutDialog.java:60
int cap = lastCapacity = (int)(sector.planet.launchCapacityMultiplier * selected.findCore().itemCapacity);
// :82 max 模式：还要扣掉蓝图（schematic）占用的份额
resources.set(item, Mathf.clamp(sitems.get(item) - schems.get(item), 0, capacity));
```

- `launchCapacityMultiplier` defaults to **0.25** [src: type/Planet.java:98-99]; Serpulo overrides it to **0.5** [src: content/Planets.java:133].
- When the planet (or the preset, after `preset.overrideLaunchDefaults`) has `allowLaunchLoadout = false`, **you may not pick resources**: the map's hard-coded `rules.loadout` is used instead and only items with `isOnPlanet` survive [src: ui/dialogs/LaunchLoadoutDialog.java:69-78]. Erekir never turns this switch on ⇒ default false [src: type/Planet.java:114-117].
- The default is `Rules.loadout = ItemStack.list(Items.copper, 100)` [src: game/Rules.java:179].
- Legality test `valid = sitems.has(total)` with `total = loadout + schematic requirements`, i.e. **a launch consumes the source sector's inventory** [src: ui/dialogs/LaunchLoadoutDialog.java:88-91].

**Channel C: legacy launch pads' offline export (Serpulo only)** — when `planet.campaignRules.legacyLaunchPads = true` (on for Serpulo, off for Erekir) [src: content/Planets.java:136]:

```text
每 turn（turnDuration = 2 分钟 = 7200 tick = 120 s，Vars.java:127）执行一次 Universe.runTurn()
  第一趟：清空所有有基地且不在玩的星区的 lastImported
  第二趟：源星区 hasBase && !isBeingPlayed && !isAttacked && info.destination != null
          转出量 = info.export.mean × newSecondsPassed（newSecondsPassed = turnDuration/60 = 120）
          to.addItems(items); to.info.lastImported.add(items)
  第三趟：info.production.mean × newSecondsPassed 累加进 info.items，cap = storageCapacity - 当前量
```

[src: game/Universe.java:151-229] (:154 `newSecondsPassed`, :183 the transfer, :184 `addItems`, :213 production accumulation, :228 `saveInfo`)

### 6. Offline invasion: the sky changes even if you never fight

```java
// game/Universe.java:232-237
if(sector.planet.campaignRules.sectorInvasion && sector.info.minutesCaptured > invasionGracePeriod && sector.info.hasSpawns){
    int count = sector.near().count(s -> s.hasEnemyBase() && !s.hasBase() && (s.preset == null || !s.preset.requireUnlock));
    if(count > 0 && Mathf.chance(baseInvasionChance * (0.8f + (count - 1) * 0.3f))){ ... }
```

- Every minute `minutesCaptured += turnDuration/60/60` (that is +2 minutes per turn) [src: game/Universe.java:203].
- Only after `invasionGracePeriod = 20` minutes with `count > 0` neighbouring enemy bases is a roll made; chance = `(1/100) × (0.8 + (count-1)×0.3)`, i.e. 0.8% for 1 neighbour, 1.1% for 2, 1.4% for 3 [src: Vars.java:129,131].
- On trigger, `state.rules.winWave = max(winWave, current wave) + random(2,4)×5` [src: game/Universe.java:237].

## Numbers

| Quantity | Value | Source |
| --- | --- | --- |
| Serpulo sector count | 272 (10×3³+2) | PlanetGrid.java:211-213 + Planets.java:123 |
| Erekir sector count | 92 (10×3²+2) | PlanetGrid.java:211-213 + Planets.java:46 |
| starting sector | Serpulo 170 / Erekir 10 / Tantros 10 | Planets.java:153,57,114 |
| sector map side length | `rect.radius × 3200`, +1 when odd | PlanetGenerator.java:173-180 |
| `launchCapacityMultiplier` | Serpulo 0.5 / 0.25 by default elsewhere | Planets.java:133 / Planet.java:98-99 |
| launch loadout cap (Serpulo core-shard) | 4000 × 0.5 = 2000 items | 00-data/blocks.json (core-shard itemCapacity=4000) + Planet.java:99 |
| launch loadout cap (Erekir core-bastion) | 2000 × 0.25 = 500 (but that planet does not enable free loadouts) | 00-data/blocks.json + Planet.java:117 |
| `turnDuration` | 2 minutes = 120 s = 7200 tick | Vars.java:127 |
| `invasionGracePeriod` | 20 minutes | Vars.java:131 |
| `baseInvasionChance` | 1/100 per turn (times the neighbour factor) | Vars.java:129 |
| `captureWave` default | 0 ⇒ `rules.winWave = captureWave` | SectorPreset.java:18-19 |
| `winWave` fallback | 30 when there are waves, no winWave and no attack | SectorInfo.java:174-177 |
| `waveSpacing` | 2 minutes | SectorInfo.java:66 |
| difficulty steps | low 0 / medium 3 / high 5 / extreme 8 / eradication 10 / unreasonable 13 | SectorDifficulty.java:6-13 |
| threat display step | 0.25 (five steps over 0.00-1.00) | Sector.java:79-85 |
| core capacity | shard 4000 / foundation 9000 / nucleus 13000 (Serpulo); bastion 2000 / citadel 3000 / acropolis 4000 (Erekir) | 00-data/blocks.json |

## Source anchors

- Planet map and scale: `type/PlanetGrid.java:211-221`, `type/Planet.java:224-237`, `content/Planets.java:46-153`, `world/generator/PlanetGenerator.java:173-180`.
- Sector state: `type/Sector.java:24` (the five threat steps), `:79-85` (displayThreat), `:89-99` (unlocked / allowLaunch*), `:101-123` (saveInfo/loadInfo/clearInfo), `:125-151` (isShielded/isAttacked/hasBase/isFrozen/isBeingPlayed), `:181-200`, `:219-247` (the two items branches).
- Sector presets: `type/SectorPreset.java:13-130` (`captureWave` :18, `difficulty` :20-21, `addStartingItems` :23, `requireUnlock` :28, `shieldSectors` :43, `init()` :106-113, `isHidden()` :123-125).
- Tech tree: `content/TechTree.java:16-29` (roots/nodeRoot), `:45-48` (automatic SectorComplete insertion), `:78-139` (TechNode fields and constructor), `:169-180` (the req-* persistence); `content/SerpuloTechTree.java:15`, `content/ErekirTechTree.java:65`; `content/UnlockableContent.java:272-289`.
- Sector save data: `game/SectorInfo.java:27-84` (the full field set), `:118-129` (export/import counters), `:125-162` (importRate), `:165-196` (write), `:199-210` (prepare).
- Offline simulation: `game/Universe.java:71-73` (turnCounter ⇒ runTurn), `:151-229` (the three passes of runTurn), `:232-244` (invasion queueing), `Vars.java:127-131` (turnDuration / baseInvasionChance / invasionGracePeriod).
- Loadout: `ui/dialogs/LaunchLoadoutDialog.java:45-92`; `game/Rules.java:179`; `type/Planet.java:98-99,114-117`.
- Difficulty injection: `game/CampaignRules.java:8-43`, `type/SectorDifficulty.java:6-13`; the opening flow `core/Logic.java:269-297`.

## Tests and counterexamples

**Counterexample 1: resources do not cross sessions.** Stockpile 13000 copper in sector A, jump to sector B, and B only gets the launch loadout (Serpulo core capacity × 0.5, minus schematics). A's `info.items` is copied back into its core only by `prepare()` the next time A is entered [src: game/SectorInfo.java:199-210]; it is never shared with B automatically.

**Counterexample 2: `captureWave` does nothing on Serpulo.** In `SectorInfo.write()` the `preset.captureWave` value is written into `winWave` only when `!planet.allowWaves` [src: game/SectorInfo.java:179-181], and Serpulo has `allowWaves = true` [src: content/Planets.java:135]. So "survive N waves in a Serpulo sector and it is captured" does not hold — Serpulo wins by clearing the enemy plus `winWave` (30 waves by default), and only Erekir takes the captureWave route.

**Counterexample 3: finishing a sector is not the same as unlocking tech.** `SectorComplete` is only one objective; nodes also carry a `Research` (material research) objective [src: content/TechTree.java:129-134], and both locks have to be satisfied.

**Counterexample 4: idle production has a cap, and being attacked stops it.** Offline production accumulates `production.mean × 120 s` but caps at `storageCapacity`, and only accumulates while `!isAttacked() && !isBeingPlayed()` [src: game/Universe.java:207-213]; while attacked, `minutesCaptured` drops straight to zero [src: game/Universe.java:200-201], so "leave it idle offline" neither overflows nor heals.

**Counterexample 5: `unlocked()` does not check adjacency.** The comment claims you must be adjacent to a wave-free sector, but the code only has `hasBase() || preset.alwaysUnlocked` [src: type/Sector.java:89-91]; with an `alwaysUnlocked` preset or a save where `hasBase` is true, a distant sector is still landable.

## Common misconceptions

1. **"The planet map is 24 hand-placed sectors"** — wrong. The tile count is computed as `10×3^sectorSize+2` (272 for Serpulo); most tiles simply have no preset and show no name.
2. **"The sector id is a sequence number"** — wrong. The id is the index in the grid array, so the starting sector's id can be 170 [src: content/Planets.java:153].
3. **"The launch loadout cap equals core capacity"** — wrong: it must be multiplied by `launchCapacityMultiplier` (0.25 by default, 0.5 on Serpulo), and the schematic share is subtracted too [src: ui/dialogs/LaunchLoadoutDialog.java:60,82].
4. **"The tech tree only researches materials"** — wrong: it also has `SectorComplete` objectives, i.e. "finish that sector" [src: content/TechTree.java:45-48].
5. **"Difficulty only changes enemy health"** — wrong: `CampaignRules.apply()` also changes `blockHealthMultiplier`/`unitHealthMultiplier`, `unitCostMultiplier = 1/enemySpawnMultiplier`, `unitBuildSpeedMultiplier` and `objectiveTimerMultiplier = difficulty.waveTimeMultiplier` [src: game/CampaignRules.java:23,39-42].
6. **"Offline sectors upgrade themselves or refill their cores"** — they do not. Offline only runs the three things in `runTurn()`: inventory production accumulation, legacy launch pad transfer, and invasion queueing; there is no build/upgrade simulation [src: game/Universe.java:151-229].

## Related

- [[CAMP.WINLOSE.001]]: sector capture and the entry point of `Call.sectorCapture()`.
- [[CAMP.WAVES.001]]: `winWave`, `waveSpacing`, wave generation.
- [[CAMP.RULES.001]]: `CampaignRules` and planet-level rule overrides.
- [[CAMP.DIFFICULTY.001]]: how difficulty steps affect enemy multipliers.
- [[CAMP.SPAWN.001]]: sector seeds and generation.
