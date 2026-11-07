---
id: CAMP.SECTOR.001
title: 星区、星图与科技解锁——战役的一个格子到底是什么
domain: camp
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src: Mindustry-Source/core/src/mindustry/type/PlanetGrid.java:211-221; type/Planet.java:224-237,98-99,114-117,452-458; type/Sector.java:24,79-85,89-99,101-117,125-151,181-200,219-247; type/SectorPreset.java:13-130; type/SectorDifficulty.java:6-13; content/Planets.java:46-69,107-114,123-153; content/TechTree.java:16-29,45-48,78-139,169-180; content/UnlockableContent.java:272-289; world/generator/PlanetGenerator.java:173-180; game/SectorInfo.java:27-84,118-210; game/Universe.java:20-26,31-36,71-73,151-244; game/CampaignRules.java:8-43; game/Rules.java:179; ui/dialogs/LaunchLoadoutDialog.java:45-92; core/Logic.java:269-297; Vars.java:127-131
data: [00-data/blocks.json]
depends: [CAMP.WINLOSE.001, CAMP.WAVES.001, CAMP.RULES.001]
tags: [星图, sector, sectorPreset, techTree, 科技解锁, launchLoadout, legacyLaunchPads, sectorInvasion, storageCapacity]
tokens: 1611
---

## 一句话

星区 = 星球六边形网格上的一个格子，**每格一个独立存档槽**（`Sector.save` + `SectorInfo`）。星图大小由 `PlanetGrid.tileCount = 10*3^sectorSize + 2` 决定（Serpulo 272 格、Erekir 92 格），不是手摆的固定地图 [src: type/PlanetGrid.java:211-213]；科技解锁是 `TechTree` 的节点需求 + `SectorComplete` 目标两把锁（`content/TechTree.java:45-48`）；**资源默认不跨星区共享**——只有发射装载（受 `launchCapacityMultiplier × 核心容量` 限制）和 Serpulo 旧式发射台的离线导出两条通道。

## 规则/公式

### 1. 星图是算出来的，不是画出来的

```java
// type/PlanetGrid.java:211-221
static int tileCount(int size){ return 10 * Mathf.pow(3, size) + 2; }   // 格子总数
static int cornerCount(int size){ return 20 * Mathf.pow(3, size); }     // 角格数
static int edgeCount(int size){ return 30 * Mathf.pow(3, size); }       // 边格数
```

- 每格一个 `Sector`：`Planet` 构造器里 `grid = PlanetGrid.create(sectorSize); sectors.add(new Sector(this, grid.tiles[i]))` [src: type/Planet.java:224-237]。
- `sectorSize` 是星球构造参数第 4 位：Serpulo 3 ⇒ 10×27+2 = **272**；Erekir / Tantros 2 ⇒ 10×9+2 = **92** [src: content/Planets.java:123,46,107]。
- `sector.id = tile.id`（即格子在网格数组里的下标），起始星区由 `startSector` 指定：Serpulo **170**、Erekir **10**、Tantros **10** [src: content/Planets.java:153,57,114]。
- 星区地图边长不是固定值：`getSectorSize(sector) = (int)(sector.rect.radius * 3200)`，奇数会 +1 取偶 [src: world/generator/PlanetGenerator.java:173-180]（`getSizeScl() = 3200`）。

### 2. 什么条件才能降落（三把锁）

```java
Sector.unlocked() = hasBase() || (preset != null && preset.alwaysUnlocked)        // type/Sector.java:89-91
hasBase()        = save != null && info.hasCore
                   && !(Vars.state.isGame() && Vars.state.rules.sector == this && state.gameOver)  // :135-137
Sector.isShielded() = preset != null && preset.shieldSectors.size > 0
                      && preset.shieldSectors.contains(s -> !s.isCaptured())      // :125-127
```

1. **有基地**：`save != null && info.hasCore`（存过档且核心还在）。
2. **科技解锁**：`preset.requireUnlock = true` 的星区必须先被科技树解锁（字段默认值就是 true）[src: type/SectorPreset.java:28]。
3. **护盾星区**：`preset.shieldSectors` 里任一未被占领 ⇒ 该星区仍在护盾下、不可降落 [src: type/Sector.java:125-127]。

> 注意 `Sector.java:87-88` 的注释写着「只有与无波次星区相邻的才能降落」，但 `unlocked()` 里**没有这段判断**，相邻性门禁在 `PlanetDialog` 的 UI 层（**推测**，未在源码内验证到具体行）。

### 3. 星区状态机：五个布尔量决定一切

| 判据 | 公式（源码行） | 含义 |
| --- | --- | --- |
| `hasBase()` | `save != null && info.hasCore && 非「正在玩且已 gameOver」` [src: type/Sector.java:135-137] | 这格有你的核心 |
| `isBeingPlayed()` | `state.isGame() && rules.sector == this && !gameOver && !net.client()` [src: type/Sector.java:148-151] | 正在这格里打 |
| `isAttacked()` | 在玩：`rules.waves \|\| rules.attackMode`；不在玩：`save != null && (info.waves \|\| info.attack) && info.hasCore` [src: type/Sector.java:129-132] | 被波次/入侵攻击 |
| `isFrozen()` | `isAttacked() && !isBeingPlayed()` [src: type/Sector.java:139-141] | 被攻击但没在玩 = 时间冻结 |
| `isCaptured()` | 在玩：`!waves && !attackMode`；不在玩：`save != null && !info.waves && !info.attack` [src: type/Sector.java:181-184] | 已占领（无敌人）|

两条容易搞反的推论：
- **被攻击的星区离线不算产能**（`Universe.runTurn()` 里 `if(!sector.isAttacked())` 才累计 `info.production`）[src: game/Universe.java:207-213]。
- **`minutesCaptured` 被攻击时清零**，所以刚被打过的星区要重新攒 20 分钟才有入侵判定 [src: game/Universe.java:200-204] + `invasionGracePeriod = 20` [src: Vars.java:131]。

### 4. 科技解锁：内容锁 + 研究锁 + 星区完成锁

```java
// content/TechTree.java:45-48 —— 星区节点自动挂一个 SectorComplete 目标
if(context.content instanceof SectorPreset preset && !objectives.contains(o -> o instanceof SectorComplete))
    objectives.add(new SectorComplete(preset));
```

- **内容锁**：`UnlockableContent.unlocked()`，战役里客户端读 `state.rules.researched`；单机看本地解锁表 [src: content/UnlockableContent.java:277-281]；解锁标记落盘 key 是 `"<name>-unlocked"` [src: content/UnlockableContent.java:284-289]。
- **研究锁**：`TechNode.requirements`（`ItemStack[]`）按 `researchCostMultipliers` 逐级放大 [src: content/TechTree.java:94-96,118-123]；已完成量存在 `Core.settings`，key 为 `"req-<content>-<item>"` [src: content/TechTree.java:169-180]。
- **星区完成锁**：`TechTree.node()` 在父内容是 `SectorPreset` 时给子节点自动插入 `SectorComplete(preset)` ⇒ **打完那个星区才解锁它的子节点**，不需要额外研究 [src: content/TechTree.java:45-48]。
- 根节点：`SerpuloTechTree.java:15`、`ErekirTechTree.java:65`；`nodeRoot(name, content, requireUnlock, ...)` 的第三参决定根节点自己是否也要解锁 [src: content/TechTree.java:19-29]。
- 星球在 `init()` 时挂上自己的树：`techTree = TechTree.roots.find(n -> n.planet == this)` [src: type/Planet.java:452-458]。

### 5. 资源跨局：只有两条半通道

**通道 A：星区库存（默认不共享）**——`SectorInfo.items` 是一份 `ItemSeq`，与核心之间来回拷贝：

```java
// game/SectorInfo.java:199-210 prepare()：进图前把核心物品抄进 info
items.clear();
for(int i = 0; i < content.items().size; i++) this.items.set(content.item(i), items.get(i));
// game/SectorInfo.java:189-195 write()：存档写回时灌回核心，按 entity.storageCapacity clamp
```

不在玩时 `Sector.addItems()` 写的是 `info.items` 并按 `info.storageCapacity` 截断；在玩时写 `state.rules.defaultTeam.core().items` 并按 `core.storageCapacity` 截断 [src: type/Sector.java:219-232]。

**通道 B：发射装载（唯一有明确上限的转移）**：

```java
// ui/dialogs/LaunchLoadoutDialog.java:60
int cap = lastCapacity = (int)(sector.planet.launchCapacityMultiplier * selected.findCore().itemCapacity);
// :82 max 模式：还要扣掉蓝图（schematic）占用的份额
resources.set(item, Mathf.clamp(sitems.get(item) - schems.get(item), 0, capacity));
```

- `launchCapacityMultiplier` 默认 **0.25** [src: type/Planet.java:98-99]；Serpulo 覆盖成 **0.5** [src: content/Planets.java:133]。
- 星球（或 preset.overrideLaunchDefaults 后的 preset）`allowLaunchLoadout = false` 时**不允许自选资源**，改用目标星区地图写死的 `rules.loadout`，且只保留 `isOnPlanet` 的物品 [src: ui/dialogs/LaunchLoadoutDialog.java:69-78]。Erekir 没开这个开关 ⇒ 默认 false [src: type/Planet.java:114-117]。
- 默认 `Rules.loadout = ItemStack.list(Items.copper, 100)` [src: game/Rules.java:179]。
- 合法性判定 `valid = sitems.has(total)`，`total = loadout + schematic 需求`，即**发射消耗的是源星区库存** [src: ui/dialogs/LaunchLoadoutDialog.java:88-91]。

**通道 C：旧式发射台离线导出（仅 Serpulo）**——`planet.campaignRules.legacyLaunchPads = true` 时（Serpulo 开了，Erekir 没开）[src: content/Planets.java:136]：

```text
每 turn（turnDuration = 2 分钟 = 7200 tick = 120 s，Vars.java:127）执行一次 Universe.runTurn()
  第一趟：清空所有有基地且不在玩的星区的 lastImported
  第二趟：源星区 hasBase && !isBeingPlayed && !isAttacked && info.destination != null
          转出量 = info.export.mean × newSecondsPassed（newSecondsPassed = turnDuration/60 = 120）
          to.addItems(items); to.info.lastImported.add(items)
  第三趟：info.production.mean × newSecondsPassed 累加进 info.items，cap = storageCapacity - 当前量
```

[src: game/Universe.java:151-229]（:154 `newSecondsPassed`、:183 转出、:184 `addItems`、:213 产能累加、:228 `saveInfo`）

### 6. 离线入侵：不打也会变天

```java
// game/Universe.java:232-237
if(sector.planet.campaignRules.sectorInvasion && sector.info.minutesCaptured > invasionGracePeriod && sector.info.hasSpawns){
    int count = sector.near().count(s -> s.hasEnemyBase() && !s.hasBase() && (s.preset == null || !s.preset.requireUnlock));
    if(count > 0 && Mathf.chance(baseInvasionChance * (0.8f + (count - 1) * 0.3f))){ ... }
```

- 每分钟 `minutesCaptured += turnDuration/60/60`（即每 turn +2 分钟）[src: game/Universe.java:203]。
- 过了 `invasionGracePeriod = 20` 分钟且邻近敌基地数 `count > 0` 才有机会；概率 = `(1/100) × (0.8 + (count-1)×0.3)`，即 1 个邻居 0.8%、2 个 1.1%、3 个 1.4% [src: Vars.java:129,131]。
- 触发后 `state.rules.winWave = max(winWave, 当前波) + random(2,4)×5` [src: game/Universe.java:237]。

## 数值

| 量 | 值 | 来源 |
| --- | --- | --- |
| Serpulo 星区数 | 272（10×3³+2）| PlanetGrid.java:211-213 + Planets.java:123 |
| Erekir 星区数 | 92（10×3²+2）| PlanetGrid.java:211-213 + Planets.java:46 |
| 起始星区 | Serpulo 170 / Erekir 10 / Tantros 10 | Planets.java:153,57,114 |
| 星区地图边长 | `rect.radius × 3200`，奇数 +1 | PlanetGenerator.java:173-180 |
| `launchCapacityMultiplier` | Serpulo 0.5 / 其它默认 0.25 | Planets.java:133 / Planet.java:98-99 |
| 发射装载上限（Serpulo core-shard）| 4000 × 0.5 = 2000 件 | 00-data/blocks.json（core-shard itemCapacity=4000）+ Planet.java:99 |
| 发射装载上限（Erekir core-bastion）| 2000 × 0.25 = 500（但该星不开自选装载）| 00-data/blocks.json + Planet.java:117 |
| `turnDuration` | 2 分钟 = 120 s = 7200 tick | Vars.java:127 |
| `invasionGracePeriod` | 20 分钟 | Vars.java:131 |
| `baseInvasionChance` | 1/100 每 turn（乘邻居系数）| Vars.java:129 |
| `captureWave` 默认 | 0 ⇒ `rules.winWave = captureWave` | SectorPreset.java:18-19 |
| `winWave` 兜底 | 有波次、无 winWave、未被打 ⇒ 30 | SectorInfo.java:174-177 |
| `waveSpacing` | 2 分钟 | SectorInfo.java:66 |
| 难度档位 | low 0 / medium 3 / high 5 / extreme 8 / eradication 10 / unreasonable 13 | SectorDifficulty.java:6-13 |
| 威胁显示步长 | 0.25（0.00-1.00 五档）| Sector.java:79-85 |
| 核心容量 | shard 4000 / foundation 9000 / nucleus 13000（Serpulo）；bastion 2000 / citadel 3000 / acropolis 4000（Erekir）| 00-data/blocks.json |

## 源码锚点

- 星图与规模：`type/PlanetGrid.java:211-221`、`type/Planet.java:224-237`、`content/Planets.java:46-153`、`world/generator/PlanetGenerator.java:173-180`。
- 星区状态：`type/Sector.java:24`（threats 五档）、`:79-85`（displayThreat）、`:89-99`（unlocked / allowLaunch*）、`:101-123`（saveInfo/loadInfo/clearInfo）、`:125-151`（isShielded/isAttacked/hasBase/isFrozen/isBeingPlayed）、`:181-200`、`:219-247`（items 双分支）。
- 星区预设：`type/SectorPreset.java:13-130`（`captureWave` :18、`difficulty` :20-21、`addStartingItems` :23、`requireUnlock` :28、`shieldSectors` :43、`init()` :106-113、`isHidden()` :123-125）。
- 科技树：`content/TechTree.java:16-29`（roots/nodeRoot）、`:45-48`（SectorComplete 自动插入）、`:78-139`（TechNode 字段与构造）、`:169-180`（req-* 落盘）；`content/SerpuloTechTree.java:15`、`content/ErekirTechTree.java:65`；`content/UnlockableContent.java:272-289`。
- 星区存档数据：`game/SectorInfo.java:27-84`（字段全集）、`:118-129`（export/import 计数）、`:125-162`（importRate）、`:165-196`（write）、`:199-210`（prepare）。
- 离线模拟：`game/Universe.java:71-73`（turnCounter ⇒ runTurn）、`:151-229`（runTurn 三趟）、`:232-244`（入侵排队）、`Vars.java:127-131`（turnDuration / baseInvasionChance / invasionGracePeriod）。
- 装载：`ui/dialogs/LaunchLoadoutDialog.java:45-92`；`game/Rules.java:179`；`type/Planet.java:98-99,114-117`。
- 难度注入：`game/CampaignRules.java:8-43`、`type/SectorDifficulty.java:6-13`；开局 `core/Logic.java:269-297`。

## 实测与反例

**反例 1：资源不跨局共享。** 在 A 星区攒了 13000 件铜，跳到 B 星区后 B 只能拿到发射装载量（Serpulo 核心容量 × 0.5，且扣蓝图）。A 的 `info.items` 只会在 A 下次进图时被 `prepare()` 抄回核心 [src: game/SectorInfo.java:199-210]，不会自动分给 B。

**反例 2：`captureWave` 对 Serpulo 无效。** `SectorInfo.write()` 里 `preset.captureWave` 只在 `!planet.allowWaves` 时才写进 `winWave` [src: game/SectorInfo.java:179-181]，而 Serpulo `allowWaves = true` [src: content/Planets.java:135]。所以「Serpulo 星区打满 N 波就占领」不成立——Serpulo 靠清空敌军 + `winWave`（默认 30 波）判胜，Erekir 才走 captureWave 路线。

**反例 3：打完星区不等于解锁科技。** `SectorComplete` 只是 objective 之一，节点还挂着 `Research`（材料研究）目标 [src: content/TechTree.java:129-134]，两把锁都要满足。

**反例 4：挂机产能有上限，且被打就停。** 离线产能按 `production.mean × 120 s` 累加但 cap 到 `storageCapacity`，且仅当 `!isAttacked() && !isBeingPlayed()` 才累计 [src: game/Universe.java:207-213]；被攻击时 `minutesCaptured` 直接归零 [src: game/Universe.java:200-201]，所以「离线放着不管」既不会溢出也不会自愈。

**反例 5：`unlocked()` 不检查相邻性。** 注释声称要与无波次星区相邻，但代码只有 `hasBase() || preset.alwaysUnlocked` [src: type/Sector.java:89-91]；如果你用 `alwaysUnlocked` 的 preset 或存档里 `hasBase` 为真，远处星区照样可落。

## 常见误解

1. **「星图是手工摆的 24 个星区」** —— 错。格子数由 `10×3^sectorSize+2` 算出（Serpulo 272），只是大部分格子没 preset、不显示名字。
2. **「sector id 是序号」** —— 错。id 是网格数组下标，起始星区 id 可以是 170 [src: content/Planets.java:153]。
3. **「发射装载上限 = 核心容量」** —— 错，要乘 `launchCapacityMultiplier`（默认 0.25，Serpulo 0.5），还要扣蓝图份额 [src: ui/dialogs/LaunchLoadoutDialog.java:60,82]。
4. **「科技树只研究材料」** —— 错，还有 `SectorComplete` 这种「打完某星区」的目标 [src: content/TechTree.java:45-48]。
5. **「难度只改敌人血量」** —— 错，`CampaignRules.apply()` 同时改 `blockHealthMultiplier`/`unitHealthMultiplier`、`unitCostMultiplier = 1/enemySpawnMultiplier`、`unitBuildSpeedMultiplier`、`objectiveTimerMultiplier = difficulty.waveTimeMultiplier` [src: game/CampaignRules.java:23,39-42]。
6. **「离线星区会自己升级/自动补核心」** —— 不会。离线只跑 `runTurn()` 的三件事：库存产能累加、legacy 发射台转运、入侵排队；没有建造/升级模拟 [src: game/Universe.java:151-229]。

## 相关

- [[CAMP.WINLOSE.001]]：星区占领与 `Call.sectorCapture()` 的判定入口。
- [[CAMP.WAVES.001]]：`winWave`、`waveSpacing`、波次生成。
- [[CAMP.RULES.001]]：`CampaignRules` 与星球级规则覆盖。
- [[CAMP.DIFFICULTY.001]]：难度档位对敌人倍率的影响。
- [[CAMP.SPAWN.001]]：星区种子与生成。
