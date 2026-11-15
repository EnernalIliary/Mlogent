---
id: WORLD.SANDBOX.001
title: 沙盒与编辑器（buildVisibility / inEditor / instantBuild / rules）
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

# 沙盒与编辑器（buildVisibility / inEditor / instantBuild / rules）

## 一句话

“能不能建”由三层决定：方块自带的 `buildVisibility`（一个按运行时条件求值的可见性对象）、`inEditor` / `placeablePlayer` / `instantBuild` 三个布尔字段，以及当前地图的 `rules`（`infiniteResources` / `editor` / `instantBuild`）；沙盒方块本身没有任何特殊，只是可见性条件与零造价配方的组合。

## 规则 / 公式

### 1. buildVisibility 是 12 个条件对象，不是枚举

- `mindustry/world/meta/BuildVisibility.java:7-31` 是 `class BuildVisibility`，字段只有一个 `Boolp visible`，`visible()`（:25-27）每次调用重新求值。
- 12 个静态常量（`:10-21`）：hidden = 恒 false、shown = 恒 true、debugOnly = false、editorOnly = `rules.editor`、coreZoneOnly = 地图含 core-zone 方块、worldProcessorOnly = `rules.editor || rules.allowEditWorldProcessors`、sandboxOnly = `Vars.state == null || rules.infiniteResources`、campaignOnly = 非游戏或战役、legacyLaunchPadOnly / notLegacyLaunchPadOnly = 战役规则 legacyLaunchPads 开关、lightingOnly = 有光照或战役或无限资源、fogOnly = 有迷雾或编辑器或非游戏。
- 判定入口：`Block.java:1093` `isVisible() = buildVisibility != hidden && buildVisibility != debugOnly`；`Block.java:1535` 未解锁判定 `!buildVisibility.visible() && !state.rules.revealedBlocks.contains(this)`。
- 建造侧：`Build.java:185` 在非编辑器模式才检查 `type.isPlaceable()` 与环境；`Block.java:1019/1023` 建造菜单按 `rules.editor` / `rules.hideBannedBlocks` 过滤。
- 默认值：`Block.java:362` `buildVisibility = BuildVisibility.hidden`，所以忘写 `requirements(...)` 的方块默认不出现在菜单。

### 2. 三个布尔的默认与含义

- `Block.java:88` `inEditor = true`：编辑器里是否出现；24/447 为 false（remove-wall、remove-ore、cliff、build1–build16、legacy-mech-pad、legacy-unit-factory 系列、command-center）[src: jar raw]。
- `Block.java:154` `placeablePlayer = true`：玩家手动放置（447 个全部 true，0 个 false）[src: jar raw]。
- `Block.java:156` `placeableOn = true`：能否盖在地板/方块上；`Block.java:148` `privileged = false`：只有 4 个（world-processor、world-cell、world-message、world-switch）为 true，普通处理器不能放。
- `Block.java:370` `instantBuild = false`：被放置后是否跳过建造进度；139/447 为 true，绝大多数是地板与墙（`Floor.java:113`、`RemoveWall.java:18` 显式置 true）[src: jar raw]。

### 3. rules 侧：三个开关决定沙盒

- `Rules.java:27` `infiniteResources`（默认 false）：建造不扣核心物品（`ConstructBlock.java:371`）、进度直接满足（`:308`）、拆除也不看阈值（`:382`）、`Block.sense(Content)` 直接返回 0（`Block.java:1668`）。
- `Rules.java:143` `instantBuild`（默认 false）：建造队列里的方块立刻完成，`Build.java:129` 检查 `result.instantBuild`。
- `Rules.java:51` `editor = false`：为 true 时绕过`Block.java:1019` 的菜单过滤与 `Build.java:185` 的可见性/环境检查。
- 乘数默认：`Rules.java:115` `buildCostMultiplier = 1f`、`:117` `buildSpeedMultiplier = 1f`（两者都会进 `ConstructBlock` 的进度与花费计算）。
### 4. 14 个沙盒/编辑器专属方块

- sandboxOnly 9 个（`Blocks.java:6704-6761`）：power-source、power-void、item-source、item-void、liquid-source、liquid-void、payload-source、payload-void、heat-source，配方全部是 `requirements(cat, BuildVisibility.sandboxOnly, with())`，即**零造价**。
- 参数：power-source `powerProduction = 1000000f/60f`（16666.7/tick = 100 万/s）[src: Blocks.java:6706]；heat-source `heatOutput = 1000`、`warmupRate = 1000`、size 1、itemCapacity 0；payload-source / payload-void `size = 5`；liquid-source / liquid-void `floating = true`。
- editorOnly 2 个：shield-projector（`Blocks.java:2049`，size 3，`consumePower(5f)` = 300/s）[src: Blocks.java:2053] 与 large-shield-projector（`:2057`，size 4，`radius = 400f`）。
- 其他可见性专供：illuminator 是 lightingOnly（`:6765`，brightness 0.75、radius 140、`consumePower(0.05f)` = 3/s）[src: Blocks.java:6765-6768]；core-zone 是 coreZoneOnly（`:3128`）；world-processor 等 4 个是 worldProcessorOnly（`:6950-6979`）；2 个 debugOnly（`:1555`、`:1688`）。

## 数值

表 A：编辑器/沙盒相关布尔字段在 447 个方块里的分布（jar v160.7 反射 raw）[src: jar raw 447 条]。

| 字段 | 为特殊值 | 占比 | 出处 |
| --- | --- | --- | --- |
| inEditor = false | 24 | 5.4% | [src: Block.java:88 + jar raw] |
| placeablePlayer = false | 0 | 0% | [src: Block.java:154 + jar raw] |
| instantBuild = true | 139 | 31.1% | [src: Block.java:370 + jar raw] |
| placeableLiquid = true | 139 | 31.1% | [src: Block.java:158 + jar raw] |
| privileged = true | 4 | 0.9% | [src: Block.java:148 + jar raw] |

表 B：BuildVisibility 的 12 个条件与默认 rules 下的结果（单人无规则）。

| 常量 | 条件（BuildVisibility.java:10-21） | 默认 rules 下可见 |
| --- | --- | --- |
| hidden | 恒 false | 否 |
| shown | 恒 true | 是 |
| debugOnly | 恒 false | 否 |
| editorOnly | `rules.editor` | 否 |
| sandboxOnly | `state == null || rules.infiniteResources` | 否 |
| campaignOnly | 非游戏或战役 | 否（普通局） |
| lightingOnly | 光照/战役/非游戏/无限资源 | 否 |
| fogOnly | 迷雾/编辑器/非游戏 | 否 |
| coreZoneOnly | 地图含 core-zone 或非游戏 | 否 |
| worldProcessorOnly | 编辑器或 allowEditWorldProcessors | 否 |
| legacyLaunchPadOnly | 战役 legacyLaunchPads 且高级发射台已解锁 | 否 |
| notLegacyLaunchPadOnly | 非游戏/无限资源/非 legacy 战役 | 视模式 |

表 C：三个 rules 开关（Rules.java 默认值）[src: Rules.java:27,51,143]。

| 字段 | 默认 | 打开后影响 |
| --- | --- | --- |
| infiniteResources | false | 建造免费、瞬间满足、拆除免阈值、sense(Item) 归 0 |
| instantBuild | false | 建造队列立即完成（Build.java:129） |
| editor | false | 绕过菜单过滤与放置环境检查（Block.java:1019、Build.java:185） |
## 源码锚点

- `mindustry/world/meta/BuildVisibility.java:7-31` 类本身与 12 个常量；:25-27 `visible()` 每次求值。
- `mindustry/world/Block.java:88` inEditor、:148 privileged、:154 placeablePlayer、:156 placeableOn、:158 placeableLiquid、:362 buildVisibility 默认 hidden、:370 instantBuild。
- `mindustry/world/Block.java:1093` `isVisible()`；:1535 `unlocked()` 用 `visible()` 判未解锁方块。
- `mindustry/world/Block.java:1019-1023` 菜单过滤：`rules.editor` 与 `rules.hideBannedBlocks`。
- `mindustry/game/Rules.java:27` infiniteResources；:51 editor；:115-117 buildCostMultiplier / buildSpeedMultiplier；:143 instantBuild。
- `mindustry/world/Build.java:129` `result.instantBuild`；:185 非编辑器才做可见性/环境检查。
- `mindustry/world/blocks/ConstructBlock.java:294-308` 无限资源下进度与花费短路；:371 不扣核心物品；:382 拆除阈值。
- `mindustry/content/Blocks.java:6704-6761` 九个 sandboxOnly 方块与参数；:2049/:2057 两个 editorOnly；:6765 lightingOnly。
- `mindustry/world/blocks/environment/Floor.java:113` 与 `RemoveWall.java:18` 显式 `instantBuild = true`（地板/清除工具不参与建造进度）。

## 实测与反例

- **反例 1（sandboxOnly 与“地图类型”无关）**：条件是 `Vars.state == null || rules.infiniteResources`（`BuildVisibility.java:16`）。普通地图只要在规则里勾无限资源，九个沙盒方块立刻出现在建造菜单；反过来战役图关掉无限资源后它们消失，而不是靠“沙盒模式”这个地图属性。
- **反例 2（沙盒方块不是“作弊方块”，是零造价方块）**：九个方块都写 `requirements(..., with())`（`Blocks.java:6705-6750`）——空需求列表，所以造价 0；它们没有任何特权代码，power-source 也只是 `powerProduction = 1000000f/60f`（:6706）。
- **反例 3（inEditor=false 不等于不能建）**：remove-wall、remove-ore、cliff、build1–build16 等 24 个方块编辑器里不显示（`Block.java:88 + jar raw`），但它们仍可存在于地图存档里，且 remove-wall 的 `instantBuild = true`（`RemoveWall.java:18`）。
- **反例 4（placeablePlayer 全 true 不代表到处能建）**：447 个方块 placeablePlayer 无一为 false，真正拦人的是 `Build.java:185` 的 `isPlaceable()` 与环境检查、以及 `Build.validPlace` 的合法性（见 W01）。
- **反例 5（instantBuild 有两个来源）**：方块字段（`Block.java:370`）只影响“这一种方块”，rules 字段（`Rules.java:143`）影响整局；测试时只改前者会发现建造进度仍然存在。
- **反例 6（privileged 是硬门）**：world-processor / world-cell / world-message / world-switch 四个 `privileged = true`（`Block.java:148`），普通 `micro-processor` 里无法放置它们（`Block.java:784` 直接 return false）。

## 常见误解

1. **“沙盒方块是模组内容”**：不是，全部在原版 `mindustry.content.Blocks` 里（:6704-6761），只靠 buildVisibility 门控 [src: Blocks.java:6704-6761]。
2. **“infiniteResources 只是不花钱”**：还会让建造进度立刻满足（`ConstructBlock.java:308`）、拆除不看阈值（:382），并让 `Block.sense(Item)` 恒为 0（`Block.java:1668`）。
3. **“buildVisibility 是个布尔值”**：是带 `Boolp` 的类，`visible()` 每次重新求值，所以同一存档里切换 rules 会即时改变菜单（`BuildVisibility.java:25-27`）。
4. **“编辑器能放所有方块”**：inEditor=false 的 24 个不会出现（`Block.java:88 + jar raw`）。
5. **“instantBuild 会跳过建造进度动画”**：它影响的是建造是否立刻完成；地板类方块设 true 是因为它们本来就不参与建造（`Floor.java:113`）。
6. **“placeableOn=false 就是不能建”**：它只表示不能覆盖已有地板/方块，能否建造还取决于 `placeableLiquid` 与 `Build.validPlace`。

## 相关

- [[WORLD.BLOCKS.001]] 放置合法性、size 与锚点（编辑器里同样是这套判定）
- [[WORLD.BLOCKSTATE.001]] configurable / enabled 与 `rules.editor` 的关系
- [[WORLD.POWER.001]] power-source 这类发电方块的电网行为
- 逻辑与特权处理器见 `knowledge/06-mlog/`；
- 战役规则（legacyLaunchPads 等）见 `knowledge/05-campaign/`