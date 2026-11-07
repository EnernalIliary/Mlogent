---
id: CAMP.RULES.001
title: Rules 规则对象全字段（118 项）
domain: camp
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src: jar:v160.7#mindustry.game.Rules（反射 118 字段）；Mindustry-Source/core/src/mindustry/game/Rules.java:1-260；core/Logic.java:269-374；entities/Units.java:119-125
data: [00-data/rules.json#records, 00-data/rt_list_Rules.json]
depends: [CAMP.WAVES.001]
tags: [rules, 规则, 自定义, 波次, 倍率]
tokens: 1216
---

## 一句话

`Rules` 是一局游戏的**唯一规则对象**（118 个字段：58 boolean / 25 float / 7 int / 28 复合），它决定波次节奏、单位/建筑/成本倍率、胜负条件、AI 与逻辑权限；**改一个字段就等于改一条机制**，而字段之间的耦合（如 `winWave` 与 `waves`）比字段本身更容易出错。

## 规则/公式

### 1. 生效顺序（谁覆盖谁）

1. 内置 `Rules` 默认值（本文[[#数值]]表，全部来自 v160.7 jar 反射）。
2. 地图自带的 `rules`（`saves/*.msav` 或 `maps` 里的规则块）覆盖。
3. 战役星图配置（`PlanetParams` / `SectorPreset`）在进入地图时再覆盖一次，并且**难度三元组会乘在 rules 之上**（见 [[CAMP.DIFFICULTY.001]]）。
4. 运行时逻辑只能通过 `logicRule` 指令改**白名单内的 29 个字段**（`LogicRule.java` 枚举），其余字段逻辑处理器无权改。

**结论**：同一张图在"战役"与"自定义"两种模式下，rules 的实际值可以完全不同；引用规则数值时必须说清是哪一层。

### 2. 波次时钟（最常被误算的一条）

- 开局宽限：`wavetime = (initialWaveSpacing <= 0 ? waveSpacing × 2 : initialWaveSpacing) × 难度.waveTimeMultiplier`（`Logic.java:272`）。
  默认 `initialWaveSpacing = 0`、`waveSpacing = 7200` ⇒ 首波倒计时 = **14400 tick = 240 s**（不是 120 s）。
- 每波结束：`wavetime = waveSpacing × 难度.waveTimeMultiplier`，同时 `wave += 1`（`Logic.java:319-325`）。
- `waveTimer = false` 只关掉**计时器显示与自动推进**，不等于 `waveSending = false`；后者才是真的不再派兵。

### 3. 单位上限（0 不等于无限）

`getCap(team)` 的实现（`Units.java:119-125`）：

```
waveTeam 且非 pvp / 战役中的 waveTeam / disableUnitCap / team.ignoreUnitCap → Integer.MAX_VALUE
否则 → max(0, unitCapVariable ? rules.unitCap + team.data().unitCap : rules.unitCap)
```

- `unitCapVariable = true`（默认）时，`rules.unitCap = 0` 的真实上限 = **核心提供的 unitCapModifier 之和**（core-shard +8、core-foundation +16、core-nucleus +24 等，`Blocks.java:3138/3150/3163`），不是 0 也不是无限。
- 敌人（waveTeam）默认**无上限**，所以"堆满单位"永远堵不住波次。
- 方块 `unitCapModifier` 变动时会差分维护 `TeamData.unitCap`（`BlockIndexer.java:216/614`），拆核心会立刻降上限并触发超额死亡（`Units.unitCapDeath`）。

### 4. 胜负判定（campaign 与自定义不同）

`Logic.checkGameState()`（`Logic.java:327-374`）：

| 模式 | 失败 | 胜利 |
|---|---|---|
| 战役（`isCampaign()`） | 玩家核心数归零 → `gameOver`（没有"胜利"状态，胜利是占领星区） | `waves && enemies==0 && winWave>0 && wave>=winWave && !spawner.isSpawning()` → `Call.sectorCapture()` |
| 自定义 + `attackMode=false` | 同上 | 同一条件 → `GameOverEvent(defaultTeam)` |
| 自定义 + `attackMode=true` | 存活队伍 ≤1（非 pvp 且默认队无核心） | 只剩一队存活 |

**`winWave = 0`（默认）表示没有胜利波**，此时除了被打爆没有别的结局；想"守满 30 波获胜"必须同时设 `winWave=30` 与 `waves=true`。

### 5. 三类倍率的乘法链

同一发伤害/同一个实体可能被三层倍率连续乘：

```
单位血量  = 类型.health      × rules.unitHealthMultiplier × 难度.unitHealthMultiplier(阵营)
单位伤害  = 子弹.damage     × rules.unitDamageMultiplier × 难度.unitDamageMultiplier(阵营)
建筑血量  = 方块.health      × rules.blockHealthMultiplier
建筑受到  = 伤害            × rules.blockDamageMultiplier
建造成本  = 方块.requirements × buildCostMultiplier ；单位成本 × unitCostMultiplier
建造速度  = 建造者.buildSpeed × buildSpeedMultiplier ；单位建造 × unitBuildSpeedMultiplier
```

所以 `unitHealthMultiplier = 2` 与 `难度.unitHealthMultiplier = 1.5` 叠加后是 **×3**，不是 ×2.5。这是"我调了 2 倍血但感觉像 3 倍"的由来。

## 数值

默认值全部来自 `00-data/rules.json`（v160.7 jar 反射，可直接 grep `name`）。

### int（7 项，全列）

| 字段 | 默认 | 含义 | 来源 |
|---|---|---|---|
| `winWave` | 0 | 胜利波次；0 = 没有胜利波 | 00-data/rules.json |
| `unitCap` | 0 | 额外单位上限（受 `unitCapVariable` 影响，见上） | 00-data/rules.json |
| `env` | 233 | 环境/天气相关位掩码默认值 | 00-data/rules.json |
| `limitX` / `limitY` | 0 / 0 | 可建造区域左上角 | 00-data/rules.json |
| `limitWidth` / `limitHeight` | 1 / 1 | 可建造区域宽高（配合 `limitMapArea` 才生效） | 00-data/rules.json |

### float（25 项，全列）

| 字段 | 默认 | 说明 | 来源 |
|---|---|---|---|
| `waveSpacing` | 7200 | 波间隔 tick（=120 s） | 00-data/rules.json |
| `initialWaveSpacing` | 0 | 首波倒计时；0 = 用 `waveSpacing×2` | 00-data/rules.json |
| `solarMultiplier` | 1 | 太阳能板输出倍率 | 00-data/rules.json |
| `unitHealthMultiplier` | 1 | 单位血量倍率（与难度相乘） | 00-data/rules.json |
| `unitDamageMultiplier` | 1 | 单位伤害倍率 | 00-data/rules.json |
| `unitBuildSpeedMultiplier` | 1 | 单位建造速度倍率 | 00-data/rules.json |
| `unitCostMultiplier` | 1 | 单位建造成本倍率 | 00-data/rules.json |
| `unitCrashDamageMultiplier` | 1 | 单位坠毁伤害倍率 | 00-data/rules.json |
| `unitMineSpeedMultiplier` | 1 | 单位采矿速度倍率 | 00-data/rules.json |
| `unitFactoryActivationDelay` | 0 | 工厂激活延迟（秒） | 00-data/rules.json |
| `blockHealthMultiplier` | 1 | 建筑血量倍率 | 00-data/rules.json |
| `blockDamageMultiplier` | 1 | 建筑受伤倍率 | 00-data/rules.json |
| `buildCostMultiplier` | 1 | 建造成本倍率 | 00-data/rules.json |
| `buildSpeedMultiplier` | 1 | 建造速度倍率 | 00-data/rules.json |
| `deconstructRefundMultiplier` | 0.5 | 拆除返还比例（默认只退一半） | 00-data/rules.json |
| `objectiveTimerMultiplier` | 1 | 目标计时倍率 | 00-data/rules.json |
| `enemyCoreBuildRadius` | 400 | 敌核心禁建半径（**px**，= 50 tile） | 00-data/rules.json |
| `dropZoneRadius` | 300 | 空投区半径（px） | 00-data/rules.json |
| `itemDepositCooldown` | 0.5 | 投物冷却（秒） | 00-data/rules.json |
| `dragMultiplier` | 1 | 单位空中阻力倍率 | 00-data/rules.json |
| `musicVolume` | 1 | 音乐音量 | 00-data/rules.json |
| `backgroundSpeed` | 27000 | 背景视差速度 | 00-data/rules.json |
| `backgroundScl` | 1 | 背景缩放 | 00-data/rules.json |
| `backgroundOffsetX` / `backgroundOffsetY` | 0.1 / 0.1 | 背景偏移 | 00-data/rules.json |

### boolean（58 项：默认 true 的 24 个 / 默认 false 的 34 个）

默认 **true**：`waveTimer`、`waveSending`、`wavesSpawnAtCores`、`pvpAutoPause`、`derelictRepair`、`canGameOver`、`reactorExplosions`、`possessionAllowed`、`schematicsAllowed`、`damageExplosions`、`fire`、`unitCapVariable`、`hideSpawns`、`ghostBlocks`、`logicUnitControl`、`logicUnitBuild`、`worldProcessorPlayerLink`、`cleanupDeadTeams`、`allowCoreUnloaders`、`staticFog`、`unitLight`、`coreIncinerates`、`borderDarkness`、`disableOutsideArea`。

默认 **false**（挑常用的）：`allowEditRules`、`infiniteResources`、`coreBuildAndConfig`、`waves`（**自定义模式默认不刷波**，战役图另置）、`airUseSpawns`、`pvp`、`pauseDisabled`、`waitEnemies`、`attackMode`、`editor`、`coreCapture`、`randomWaveAI`、`unitPayloadUpdate`、`unitPayloadsExplode`、`logicUnitDeconstruct`、`disableWorldProcessors`、`allowEditWorldProcessors`、`polygonCoreProtection`、`placeRangeCheck`、`onlyDepositCore`、`coreDestroyClear`、`instantBuild`、`disableUnitCap`、`fog`、`lighting`、`alwaysPlayMusic`、`disableMusic`、`allowLogicData`。完整 58 项见 `00-data/rules.json` 过滤 `type=="boolean"`。

### 复合类型（28 项，不能当标量改）

| 类型 | 字段 | 说明 |
|---|---|---|
| `Seq`(5) | `spawns` / `loadout` / `weather` / `ambientMusic` / `darkMusic` | 波次预设、开局物资、天气表 |
| `ObjectSet`(5) | `bannedBlocks` / `bannedUnits` / `revealedBlocks` / `researched` / `objectiveFlags` | 禁用/已解锁集合 |
| `Color`(4) | `staticColor` / `dynamicColor` / `ambientLight` / `cloudColor` | 画面色（不影响机制） |
| `String`(4) | `modeName` / `mission` / `customBackgroundCallback` / `backgroundTexture` | 显示用 |
| `Team`(2) | `defaultTeam` / `waveTeam` | 玩家队与敌军队 |
| 单例 | `teams`(TeamRules) / `attributes`(Attributes) / `sector`(Sector) / `objectives`(MapObjectives) / `blockLimits` / `tags` / `planet` / `planetBackground` | 分组规则与战役元数据 |

## 源码锚点

- `game/Rules.java`：118 个 public 字段即全部可配置项（`Rules.java:75` `unitCapVariable=true`、`:157` `unitCap=0`）。
- `core/Logic.java:269-297` `play()`：开局宽限与开局物资 `rules.loadout` 的灌入（会按 `storageCapacity` 截断）。
- `core/Logic.java:319-325` `runWave()`：派兵 + `wave++` + 重置 `wavetime`。
- `core/Logic.java:327-374` `checkGameState()`：三种模式的胜负判定（campaign 无"胜"，只有 `sectorCapture()`）。
- `entities/Units.java:119-125` `getCap()`：上限的三条分支（waveTeam / disableUnitCap / 核心加成）。
- `ai/BlockIndexer.java:216,614`：核心等方块的 `unitCapModifier` 差分维护。
- `logic/LogicRule.java`：逻辑指令可改的 29 个规则字段白名单。

## 实测与反例

**反例 1：以为首波是 120 秒。** 默认 `waveSpacing=7200`（120 s）、`initialWaveSpacing=0`，很多人据此说"第一波 120 秒后来"。实际 `Logic.java:272` 走的是 `waveSpacing × 2 = 14400 tick`，**首波 240 秒**。用 `sensor @wavetime` 在第 1 tick 读即可验证：14400，不是 7200。

**反例 2：以为 `unitCap=0` 是不限。** `Units.java:124` 的 `max(0, 0 + team.data().unitCap)` 说明上限=核心加成之和（如 3 个 core-nucleus = 72）。只有 `disableUnitCap=true` 或敌人队才是无限。

**反例 3：以为 `winWave=30` 就够。** `Logic.java:369` 要求 `waves==true && enemies==0 && winWave>0 && wave>=winWave && !spawner.isSpawning()` 同时成立；只设 `winWave` 而 `waves=false` 永远不触发胜利。战役图更特殊：胜利走 `Call.sectorCapture()`，即使条件成立也不会弹"游戏胜利"。

## 常见误解

1. **"rules 是全局常量"**：它是每局实例，进图时被地图/星图覆盖，退出后回到默认；改它必须通过 `Call.setRules()` 或逻辑 `logicRule`。
2. **"`rules.waves=false` 就没有敌人"**：只停自动刷波；`spawner` 里已排队的波、`attackMode` 的 AI、预设 `spawns` 仍会出兵（`Logic.java:337-349` 也说明战役会因"没有刷新点"自动置 false）。
3. **"`infiniteResources` 影响所有队"**：只对**玩家默认队**生效（建造/生产不扣资源），敌人该用还是用。
4. **"倍率是加法叠加"**：全部是乘法链，见上文第 5 节；两个 ×2 就是 ×4。
5. **"单位上限包含敌方"**：`getCap` 按队伍算，敌人默认 MAX_VALUE，所以你的 cap 与敌人数无关。

## 相关

- [[CAMP.WAVES.001]] 波次计数与生成细节
- [[CAMP.DIFFICULTY.001]] 难度三元组与 rules 倍率的叠加
- [[CAMP.WINLOSE.001]] 胜负与游戏结束的完整条件
- [[CAMP.SPAWN.001]] `spawns` / SpawnGroup 结构
- [[WORLD.POWER.001]] `solarMultiplier` 在发电侧的落点
