---
id: WORLD.CRAFTING.001
title: 配方与制造
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/production/GenericCrafter.java:40-77"
  - "Mindustry-Source/core/src/mindustry/world/blocks/production/GenericCrafter.java:203-316"
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:1209-1211, 1933-1947, 2004-2009"
  - "Mindustry-Source/core/src/mindustry/world/consumers/ConsumeItems.java:44-53"
  - "Mindustry-Source/core/src/mindustry/world/consumers/ConsumeLiquid.java:36-52"
  - "Mindustry-Source/core/src/mindustry/game/Schematic.java:126-132"
  - "MBO/gamedata/v160.7/gamedata.json (jar 反射，33 个带 recipe 的方块)"
data: [00-data/blocks.json]
depends: [WORLD.BLOCKS.001]
tags: [配方, craftTime, 制造机, ConsumeItems, ConsumeLiquid, 蓝图, 效率]
tokens: 1454
---

## 一句话

一个配方由三样东西拼成：**输入消费者**（ConsumeItems / ConsumeLiquid / ConsumePower / ConsumeCoolant）、**craftTime**（多少 tick 走满一圈）、**产出**（outputItems / outputLiquids）；三者量纲不同——物品是"每次完工扣一次"，液体和电力是"每 tick 扣一次"，所以任何速率换算必须先分清这个单位边界。

## 规则 / 公式

### 1. 三个量的单位边界（最常错的一条）

| 字段 | 单位 | 何时扣/给 | 换算 |
|---|---|---|---|
| `ConsumeItems.amount` / `outputItems.amount` | 个 / **craft** | 完工瞬间（`trigger()`） | 个/秒 = amount × 60 / craftTime |
| `ConsumeLiquid.amount` / `outputLiquids.amount` | 液体 / **tick** | 每 tick 连续扣/给 | 每秒 = amount × 60 |
| `ConsumePower.usage` | 电力 / **tick** | 每 tick 连续扣 | 每秒 = usage × 60 |
| `ConsumeCoolant.amount` | 液体 / tick | 每 tick 连续扣 | 同液体 |
| `craftTime` | **tick**（1 tick = 1/60 s） | 进度累加 | 周期 = craftTime/60 秒；速率 = 60/craftTime 次/秒 |

`ConsumeLiquid.update()` 里是 `liquids.remove(liquid, amount * build.edelta() * multiplier)`（每 tick），而 `ConsumeItems.trigger()` 里是 `items.remove(Math.round(amount * multiplier))`（每次完工）——这是源码里两条完全不同的路径，不是文档笔误 [src: ConsumeLiquid.java:37-38, ConsumeItems.java:44-48]。

### 2. 进度推进

```
progress += getProgressIncrease(craftTime)      // 每 tick
getProgressIncrease(baseTime) = 1f / baseTime * edelta()
edelta() = efficiency * delta()                 // delta()≈1（60 UPS 归一化）
progress >= 1f  ->  craft(): consume(); 逐个 offload(outputItems); progress %= 1f
```

所以**一个方块在效率 100% 下，完成一圈正好用 craftTime 个 tick**；效率 50% 时用 2×craftTime 个 tick。

`getProgressIncrease` 还有一层"输出液体剩余容量"限速：输出液体快满时进度会主动放慢，避免浪费输入 [src: GenericCrafter.java:266-285]。

### 3. 谁决定效率

`efficiency` 是所有**非 optional** 消费者效率的最小值 [src: BuildingComp.java:1975-1992]：

- `ConsumeItems.efficiency()` = `items.has(需求) ? 1 : 0`（有就给满，不做比例）[src: ConsumeItems.java:51-53]
- `ConsumeLiquid.efficiency()` = `min(当前库存 / (amount*edelta*mult), 1)`（液体可以"半饱"跑）[src: ConsumeLiquid.java:42-47]
- `ConsumePower.efficiency()` = 电网供需比（详见 `WORLD.POWER.001`）

液体消费者会"半饱"地拖低整机效率，物品消费者只会 0/1 跳变——这解释了为什么缺矿的工厂是"完全停"，而缺水的工厂会"慢速爬"。

### 4. 停摆条件（shouldConsume）

`GenericCrafterBuild.shouldConsume()` 在以下情况返回 false，整个工厂不进食也不涨进度 [src: GenericCrafter.java:203-232]：

1. 任一 `outputItems` 在机器内的存量已到 `itemCapacity`（产物堵死）；
2. 任一 `outputLiquids` 已满 **且** 该输出未设 `dumpExtraLiquid` / `ignoreLiquidFullness`；
3. `enabled == false`（逻辑处理器关掉）或 `efficiency == 0`。

注意顺序：**先堵输出再谈输入**。输入满、输出堵的工厂不是"待机"，是"卡死"——传送带会把上游一起顶停（见 `WORLD.LOGISTICS.001` 的回压）。

### 5. 工厂 vs 制造机

原版**没有**叫"工厂"的方块类型，这是玩家俗称。按 `baseClass` 分，带 `recipe` 的 33 个方块是 5 类：

| baseClass | 数量 | 代表 | 差别 |
|---|---|---|---|
| `GenericCrafter` | 17 | graphite-press, silicon-smelter, phase-weaver | 基础制造，无额外加成 |
| `HeatCrafter` | 5 | carbide-crucible, cyanogen-synthesizer | 需要 heat，热量越高越快（见 `WORLD.HEAT.001`） |
| `HeatProducer` | 6 | oxidation-chamber, electric-heater, heat-reactor | 产物是热量本身（`heatOutput`），无物品产出 |
| `AttributeCrafter` | 3 | cultivator, vent-condenser, silicon-crucible | 效率随地板属性数量放大 |
| `Separator` | 2 | separator, disassembler | 从液体/废料里**随机**挑一种产出 |

玩家口中的"小工厂"= `graphite-press`/`kiln`/`silicon-smelter` 这类 2×2 无电或低电制造；"大工厂"= `plastanium-compressor`/`surge-smelter` 这类多输入高电耗制造。区别只在输入端数量与功耗，机制上没有第二套规则。

### 6. 蓝图里有什么

`Schematic.Stile` 只有 4 个字段：`Block block; int x, y; Object config; byte rotation` [src: Schematic.java:126-132]。因此蓝图/复制粘贴：

- **保存**：方块种类、相对坐标、配置（如卸载器目标、逻辑处理器代码）、朝向；
- **不保存**：库存（`items`）、液体（`liquids`）、进度（`progress`、`warmup`）、热量、电力储量；
- **成本**：`Schematic.requirements()` 把每个方块的 `requirements` 累加，粘贴时从核心/库存里扣；`Schematic.powerConsumption()` 用 `block.consPower.usage` 累加，单位同样是 per tick。

所以复制一座"已经装满矿的工厂"只会得到一个空壳——这是复制工厂最常见的失望点。

## 数值

以下取自 v160.7 jar 反射的 `recipe`（同源字段见 `00-data/blocks.json#id=<name>` 的 `recipe` 子树）。速率按 60 UPS 换算：**物品 ×60/craftTime、液体 ×60、电力 ×60**。

| 方块 | craftTime (tick) | 次/秒 | 物品输入（每 craft） | 液体输入（每 tick） | 产出 | 电耗/tick | 电耗/秒 |
|---|---|---|---|---|---|---|---|
| graphite-press | 90 | 0.667 | coal 2 | 无 | graphite 1（0.667/s） | 无 | 0 |
| silicon-smelter | 40 | 1.5 | coal 1 + sand 2 | 无 | silicon 1（1.5/s） | 0.5 | 30 |
| kiln | 30 | 2.0 | lead 1 + sand 1 | 无 | metaglass 1（2/s） | 0.6 | 36 |
| pulverizer | 40 | 1.5 | scrap 1 | 无 | sand 1（1.5/s） | 0.5 | 30 |
| multi-press | 30 | 2.0 | coal 3 | water 0.1（6/s） | graphite 2（4/s） | 1.8 | 108 |
| plastanium-compressor | 60 | 1.0 | titanium 2 | oil 0.25（15/s） | plastanium 1（1/s） | 3.0 | 180 |
| phase-weaver | 120 | 0.5 | thorium 4 + sand 10 | 无 | phase-fabric 1（0.5/s） | 5.0 | 300 |
| surge-smelter | 75 | 0.8 | copper 3 + lead 4 + titanium 2 + silicon 3 | 无 | surge-alloy 1（0.8/s） | 4.0 | 240 |
| cryofluid-mixer | 120 | 0.5 | titanium 1 | water 0.2（12/s） | cryofluid 0.2（12/s） | 1.0 | 60 |
| electrolyzer | 10 | 6.0 | 无 | water 0.1667（10/s） | ozone 0.0667（4/s）+ hydrogen 0.1（6/s） | 1.0 | 60 |
| carbide-crucible | 33.75 | 1.778 | tungsten 2 + graphite 3 | 无 | carbide 1（1.778/s） | 2.0 | 120 |
| separator | 35 | 1.714 | 无 | slag 0.0667（4/s） | 随机一种：copper 5 / lead 3 / graphite 2 / titanium 2（权重） | 1.1 | 66 |

补充计数（同一次 jar 反射，447 个方块全体）：

- 带 `recipe` 的方块 **33 个**；`craftTime` 分布（值×个数）：80×6、120×5、30×4、90×2、40×2、20×2、10×2、60/75/35/15/50/45/100/480/600/33.75 各 ×1，共 17 个不同取值、合计 33 个方块。
- 最小 `craftTime = 10`（melter、electrolyzer），最大 `= 600`（heat-reactor，属 HeatProducer）。
- 消费者类型计数：`ConsumePower` 104 个方块、`ConsumeLiquid` 60、`ConsumeItems` 45、`ConsumeCoolant` 16、`ConsumeItemDynamic` 11、`ConsumeLiquids` / `ConsumeLiquidsDynamic` / `ConsumePayloadDynamic` 各 3、`ConsumeItemFlammable` / `ConsumeItemExplode` / `ConsumePowerCondition` 各 2、`ConsumeItemRadioactive` / `ConsumePowerDynamic` 各 1。
- 电解器可做质量守恒自检：进水 10/s，出 ozone 4/s + hydrogen 6/s = 10/s（1:1 分解）。

## 源码锚点

- `GenericCrafter.java:40` `public float craftTime = 80f;` —— 默认 80 tick（≈1.33 s），所以多数工厂"一秒多一点一圈"。
- `GenericCrafter.java:45` `warmupSpeed = 0.019f` —— 视觉预热，与产能无关。
- `GenericCrafter.java:66` `stats.timePeriod = craftTime` —— UI 用 craftTime 把"每 craft"折算成"/秒"。
- `GenericCrafter.java:73` `StatValues.items(craftTime, outputItems)` —— 物品按每条 craftTime 折算。
- `GenericCrafter.java:77` `StatValues.liquids(1f, outputLiquids)` —— 液体用 **1f** 作时间基准，再内部乘 `60/timePeriod`（`StatValues.java:141`），即"amount 是每 tick"。
- `GenericCrafter.java:236-264` `GenericCrafterBuild.updateTile()`：进度累加 + 输出液体按 `getProgressIncrease(1f)` 连续给。
- `GenericCrafter.java:301-316` `craft()`：`consume()` → 逐 `outputItems` 调 `offload()` → `progress %= 1f`。
- `BuildingComp.java:1209-1211` `getProgressIncrease(baseTime) = 1f / baseTime * edelta()`。
- `BuildingComp.java:1933-1935` `edelta() = efficiency * delta()`；`1928-1930` `delta() = Time.delta * timeScale`。
- `BuildingComp.java:2004-2009` 消费者更新被 `if(update && efficiency > 0)` 门控。
- `ConsumeItems.java:44-48` / `ConsumeLiquid.java:37-38` 两种扣费路径（per craft vs per tick）。
- `Schematic.java:126-132` 蓝图的 `Stile` 只存 `block/x/y/config/rotation`。

## 实测与反例

**反例 1（旧表的 craftTime 全是 -1）**：旧 `data/game/*.json` 里 447 个方块的 `craftTime` 一律是 `-1`，那是导出脚本没进反射字段的占位值。v160.7 jar 实测 **-1 的数量为 0**，真实区间是 10–600。凡是从旧表读到 -1 的，一律视为"该字段缺失"而不是"瞬间完成"。这条已记入 `VERSION.md` 的已知错误清单。

**反例 2（`recipe.outputLiquidsPerSecond` 这个派生字段是错的）**：gamedata.json 里 `cryofluid-mixer.outputLiquidsPerSecond = 0.1`、`melter = 1.2`、`electrolyzer = ozone 0.4 + hydrogen 0.6`。它把公式写成了 `amount / craftTime * 60`（按 per-craft 折算）。而源码 `GenericCrafter.java:243` 是每 tick 加一次 `output.amount * inc`，正确值应是 `amount × 60`：cryofluid 12/s、slag 12/s、ozone 4/s + hydrogen 6/s。用质量守恒立刻能判：电解器进水 10/s，派生字段的产物总和只有 1.0/s，违反 1:1 分解；源码口径 4+6=10/s 才对。**该派生字段不可直接采信。**

**反例 3（改 craftTime 不会等比改液体消耗）**：`multi-press` 现在是 `craftTime=30`、`water 0.1/tick`（6/s）。若把它改到 60，物品消耗减半（coal 由 2 craft/s × 3 = 6/s 降到 1 craft/s × 3 = 3/s，graphite 由 4/s 降到 2/s），但**水仍然是 6/s 不变**，因为 `ConsumeLiquid.update()` 每 tick 扣一次、与进度无关。混配方（物品+液体）的工厂改速度后会改变配比，这是复刻/平衡改动的经典坑。

**反例 4（craftTime 不必是整数）**：`carbide-crucible` 的 `craftTime = 33.75`，`cyclesPerSecond = 1.777778`。任何"craftTime 必须是整数 tick"的假设都会在这里崩；UI 上它显示成 1.78/s。

**反例 5（随机制造机没有静态产出率）**：`separator` 的 `recipe.resultsSemantics` 明写 "one random result per craft, weighted by amount"，产出是 copper5/lead3/graphite2/titanium2 里随机挑一种（**给的是该种的总量，不是概率**）。它的 gamedata 记录里既没有 `outputItems` 也没有 `outputItemsPerSecond`——用 `outputItems` 读它会得到空数组，误判为"不产出"。

## 常见误解

1. **"craftTime 是秒"** → 是 tick。`graphite-press` 的 90 不是 90 秒而是 1.5 秒一圈（这个错会把产能算小 60 倍）。
2. **"outputLiquids 也是每次完工给一次"** → 是每 tick 连续给。所以液体产率 = `amount × 60`，与 craftTime 无关（见反例 2）。
3. **"耗电 usage 单位是 /s"** → 是 /tick。`phase-weaver` 的 5 是 5/tick = 300/s，不是 5/s。旧速查表（`docs/游戏速查/方块配方.md`，2026-11-17 已删）的"耗电"列就是每 tick 值却标了 /s，这个坑已记入 `VERSION.md`。
   反查「谁消耗某物品」时不要手抄：对 `00-data/blocks.json` 的 `consumers[].items[].item` 做反向 join 即可。
4. **"缺电只是变慢，材料照扣"** → 物品在 `craft()` 完工时才扣，效率 0 就不完工、不扣物品；但液体消费者由 `BuildingComp.java:2005` 门控，仅当 `efficiency > 0` 才扣——效率被输出满限速时会出现"进度变慢、液体照满额扣"的浪费。
5. **"蓝图会带上工厂里的库存和进度"** → `Schematic.Stile` 只有 block/x/y/config/rotation 四个字段，进度与库存不进蓝图（详见上文「蓝图里有什么」）。
6. **"工厂和制造机是两类方块"** → 原版只有 `GenericCrafter`/`HeatCrafter`/`AttributeCrafter`/`HeatProducer`/`Separator` 这几种实现类，玩家俗称不构成机制差异。

## 相关

- `WORLD.BLOCKS.001`（size 与布局：工厂占地决定传送带接入点）
- `WORLD.POWER.001`（`ConsumePower` 与 usage/usagePerSecond 的完整换算）
- `WORLD.LIQUIDS.001`（`ConsumeLiquid` 的液体属性与堵塞）
- `WORLD.HEAT.001`（`HeatCrafter` 的加成公式）
- `WORLD.LOGISTICS.001`（输出堵死导致的回压）
- 数据表：`00-data/blocks.json`（`recipe` 子树）、`00-data/formulas.json`
- 源码：`world/blocks/production/GenericCrafter.java`、`world/consumers/*.java`、`game/Schematic.java`、`entities/comp/BuildingComp.java`
