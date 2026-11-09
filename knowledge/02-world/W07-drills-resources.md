---
id: WORLD.DRILLING.001
title: 钻探与资源：钻头等级、硬度惩罚与矿层覆盖
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src:
  - Mindustry-Source/core/src/mindustry/world/blocks/production/Drill.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/BeamDrill.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/BurstDrill.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/WallCrafter.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/SolidPump.java
  - Mindustry-Source/core/src/mindustry/world/blocks/production/Fracker.java
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/OreBlock.java
  - Mindustry-Source/core/src/mindustry/content/Blocks.java
  - Mindustry-Source/core/src/mindustry/world/Tile.java
data:
  - 00-data/blocks.json#id=mechanical-drill
  - 00-data/blocks.json#id=laser-drill
  - 00-data/blocks.json#id=impact-drill
  - 00-data/blocks.json#id=water-extractor
  - 00-data/blocks.json#id=plasma-bore
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001, WORLD.LIQUIDS.001]
tags: [drill, tier, hardness, ore, drillTime, laser-drill, 钻头, 矿层, 采掘]
tokens: 1926
---

# 钻探与资源：钻头等级、硬度惩罚与矿层覆盖

## 一句话

原版采掘有四套完全不同的实现（`Drill` 按格覆盖、`BeamDrill` 打墙、`BurstDrill` 打中心、`WallCrafter` 吃沙属性墙），产出率都被 `tier`（能否采）与 `hardness`（采得多慢）两道闸门控制，而 UI 上的「X 件/s」几乎总是忽略硬度的乐观值。

## 规则 / 公式

### 1. 四种采掘方块 + 两种取液方块

| 类 | 判定依据 | 代表方块 | 关键字段 |
|---|---|---|---|
| `Drill` | 钻头覆盖格内 `tile.drop()` 的矿 | mechanical / pneumatic / laser / blast-drill | `tier`、`drillTime`、`hardnessDrillMultiplier` |
| `BeamDrill` | 朝向前方 `range` 格内第一堵 solid 墙 | plasma-bore、large-plasma-bore | `range`、`tier` |
| `BurstDrill` | 同 Drill 的覆盖计数，但一次爆出全部 | impact-drill、eruption-drill | `hardnessDrillMultiplier = 0` |
| `WallCrafter` | 朝向前方 `size` 格墙的 `Attribute.sand` 之和 | cliff-crusher、large-cliff-crusher | `attribute`、`output` |
| `SolidPump` | 脚下非液体格 + 地形属性 | water-extractor | `pumpAmount`、`baseEfficiency` |
| `Fracker` | 地形 `Attribute.oil` + 吃沙 | oil-extractor | `pumpAmount`、`itemUseTime` |

六者的共同前提：`envEnabled |= Env.space`（Drill.java:86、BeamDrill.java:76），但 mechanical-drill 例外——它写的是 `envEnabled ^= Env.space`（Blocks.java:2872），**在太空图无法放置**。

### 2. 钻头公式：硬度是加在时间上，不是乘在速度上

`Drill` 的取矿时间是

```
getDrillTime(item) = (drillTime + hardnessDrillMultiplier * item.hardness) / drillMultipliers.get(item, 1f)
```

（Drill.java:170-172）。默认 `hardnessDrillMultiplier = 50f`（Drill.java:28），所以硬度 0 的矿（sand/scrap/graphite）等于裸 `drillTime`，而 thorium（hardness 4）在 mechanical-drill 上要多等 `50 × 4 = 200` tick。注意分母是**每种矿的倍率表** `drillMultipliers`（Drill.java:66），原版只有 impact-drill/eruption-drill 给 beryllium 写了 `2f`（Blocks.java:3084、Blocks.java:3115）。

### 3. 覆盖率：产出按「主矿格数」线性放大

`DrillBuild.onProximityUpdate` 里调 `countOre(tile)`，遍历 `tile.getLinkedTilesAs(this, tempTiles)`（即整个 size×size 范围），统计每种 `tile.drop()` 出现次数（Drill.java:198-229）：

1. 先按 `lowPriority` 排（`Boolean.compare(!item1.lowPriority, !item2.lowPriority)`，Drill.java:216）——lowPriority 的矿被排到**前面**；
2. 再按覆盖格数升序、id 升序；
3. 取 `itemArray.peek()`（最后一个）= 优先采非 lowPriority、且覆盖最多的那一种。

结果存在 `dominantItem` / `dominantItems` 两个字段（Drill.java:243-244、Drill.java:275-277）。产出速率直接乘 `dominantItems`：

```
progress += delta() * dominantItems * speed * warmup;
lastDrillSpeed = (speed * dominantItems * warmup) / delay;
```

（Drill.java:303-305）。所以 3×3 激光钻覆盖 9 格钛矿 = 速率为 1 格时的 9 倍；覆盖 4 格只有 4 倍——**多格钻头必须整块压在矿上**。

tools/block_sizes.json 与 data/game/blocks.json 只给 size，覆盖率要看地图，任何「钻头产 X/s」都必须声明覆盖假设。

### 4. tier 是「硬度门槛」，不是「等级越高越快」

`canMine` 只判断三件事（Drill.java:231-235）：格子的 `tile.drop() != null`、`drops.hardness <= tier`、不在 `blockedItems` 里。硬度表（items 的 `hardness` 字段，v160.7 jar 反射）：

| 物品 | hardness | 需要的钻头（最小 tier） |
|---|---|---|
| sand / scrap / graphite / coal 之外的加工品 | 0 | 任意（tier ≥ 1 的 drill 都能采，实际只有矿才有 drop） |
| copper、lead | 1 | mechanical-drill（`tier = 2`） |
| coal | 2 | mechanical-drill（tier 2，**能采**） |
| titanium、beryllium | 3 | pneumatic-drill（`tier = 3`） |
| thorium | 4 | laser-drill（`tier = 4`） |
| tungsten | 5 | blast-drill / large-plasma-bore（tier 5） |

tier 本身**不给速度加成**：pneumatic-drill 比 mechanical-drill 快，是因为 `drillTime` 从 600 降到 400（Blocks.java:2869、Blocks.java:2881），不是因为 tier 高。

### 5. 液体加速：1.6 是「双乘」，稳态是 2.56 倍

升级路径写的是 `liquidBoostIntensity = 1.6f`（Drill.java:38），实际代码里它**同时**进入两个因子（Drill.java:301-305）：

```
float speed = Mathf.lerp(1f, liquidBoostIntensity, optionalEfficiency) * efficiency;
warmup = Mathf.approachDelta(warmup, speed, warmupSpeed);
progress += delta() * dominantItems * speed * warmup;
```

`speed` 被加速到 1.6，`warmup` 又逼近 `speed` 也到 1.6，二者相乘 = **2.56 倍**。官方 UI 就是这么显示的：`StatValues.speedBoosters(..., liquidBoostIntensity * liquidBoostIntensity, ...)`（Drill.java:188）。blast-drill 的 1.8 对应 3.24 倍。

加速液：mechanical 0.05/tick = 3/s 水（Blocks.java:2875）、pneumatic 3.5/60 = 3.5/s（Blocks.java:2884）、laser 0.08/tick = 4.8/s（Blocks.java:2897）、blast 0.1/tick = 6/s（Blocks.java:2918）、plasma-bore 氢气 0.25/60 = 0.25/s（Blocks.java:3050）、impact-drill 臭氧 3/60 = 3/s（Blocks.java:3091）。都是 `.boost()` 可选消费者，断液只是回到 1× 而不是停机。

### 6. BeamDrill：只打墙，按「面对数」出矿

`BeamDrillBuild.updateFacing` 从钻头 **size 条边**各射一条激光，每条沿 `Geometry.d4(rotation)` 方向最多 `range` 格，遇到第一堵 solid 就停（BeamDrill.java:198-214 的 `canPlaceOn` 同逻辑）。产出：

```
time += edelta() * multiplier;
if(time >= drillTime){ for(Tile tile : facing){ ... items.add(drop, 1); } time %= drillTime; }
```

（BeamDrill.java:246-262）——**每面每周期只出 1 件**，所以最大速率 = `facingAmount × 60 / drillTime`，`facingAmount ≤ size`。getDrillTime 也不含硬度（BeamDrill.java:216-218）。

判定用 `tile.wallDrop()`（Tile.java:575-580）：只有 `block.solid` 且（墙自带 `itemDrop` 或 `overlay.wallOre`）才返回值，所以能采的是「矿墙」（ore-wall-thorium 等）而不是普通地板矿。

### 7. BurstDrill：硬度惩罚被清零，一次爆出全部覆盖

构造器直接写死 `hardnessDrillMultiplier = 0f`（BurstDrill.java:39，注释「does not drill in the traditional sense」），并覆写 `getDrillTime` 为 `drillTime / drillMultipliers`（BurstDrill.java:53-55）。它的进度不乘覆盖率，**产出**才乘：

```
progress += delta() * speed;
if(progress >= drillTime){ for(int i = 0; i < dominantItems; i++) offload(dominantItem); }
```

（BurstDrill.java:99、BurstDrill.java:106-109）。所以 impact-drill 在 4×4 全覆盖时是「每 720 tick 爆出 16 件」，平均 `16 × 60 / 720 = 1.333 件/s`，且**与矿的硬度无关**（thorium 也是 720 tick）。它的代价是 `blockedItem = Items.thorium`（Blocks.java:3081）：tier 6 却采不了 thorium。

### 8. WallCrafter：不看矿，吃「墙的沙属性」

`getEfficiency` 沿朝向取前方 `size` 格（不是 size×size），对每格 `other.solid()` 的墙累加 `other.block().attributes.get(attribute)`（WallCrafter.java:141-181）。cliff-crusher / large-cliff-crusher 的 `attribute = Attribute.sand`、`output = Items.sand`（Blocks.java:3009-3010、3023-3024）。

沙属性实测值（content/Blocks.java）：dune-wall 2、sand-wall 2、yellow-stone-wall 1.5、red-stone-wall 1.5、beryllic-stone-wall 1.2、stone-wall 1、regolith-wall 1、rhyolite-wall 1、carbon-wall 0.7、ferric-stone-wall 0.5（Blocks.java:597-675）。速率 = `eff × 60 / drillTime`，eff 上限 = size × 最大属性。

### 9. 采液：SolidPump 与 Fracker

- **water-extractor（SolidPump）**：`pumpAmount = 0.11`（Blocks.java:2924），有效度 `fraction = validTiles + boost + attribute.env()`（SolidPump.java:124），其中 `boost = sumAttribute(Attribute.water)/size/size`、`validTiles = Σ baseEfficiency/size²`（SolidPump.java:153-159，baseEfficiency 默认 1）。无属性地板时 fraction = 1 → **6.6 水/s**；水属性地板可翻倍。它要求 `!tile.floor().isLiquid`（SolidPump.java:80-82），所以不能直接架在湖面上。
- **oil-extractor（Fracker）**：`pumpAmount = 0.25`（Blocks.java:2970）、`baseEfficiency = 0`、`attribute = Attribute.oil`（Blocks.java:2973-2974）、`itemUseTime = 60`、吃 sand 1 件/60 tick 与 3/tick 电（Blocks.java:2977-2979），只往周边 `dumpLiquid(result)`（Fracker.java:42）。产出与 `SolidPump` 同一式子：**每秒 = `pumpAmount × 60 × Attribute.oil`**。
  满黑沙（`darksand` 1.5）= `0.25×60×1.5` = **22.5 油/s**；属性 1.0 的地板才是 15/s（游戏 UI 印的
  `60×pumpAmount` 就是这个乐观值，与钻头 UI 同一类坑）。Attribute.oil 地板值：
  `sand-floor` 0.7、`darksand` **1.5**、`salt` 0.3、`shale` 2.0（content/Blocks.java）。
  配比对照：煤炭分离机吃 6 油/s，**3 台离心机（18 油/s）只需 1 台石油钻井**；按 15/s 会算成 2 台。

### 10. 矿层（oreBlocks）：16 条 id → item 映射

gamedata 的 `environment.oreBlocks` 列出全部可采矿层（MBO/gamedata/v160.7/gamedata.json#environment.oreBlocks）：

`ore-copper→copper`、`ore-lead→lead`、`ore-scrap→scrap`、`ore-coal→coal`、`ore-titanium→titanium`、`ore-thorium→thorium`、`ore-beryllium→beryllium`、`ore-tungsten→tungsten`、`ore-crystal-thorium→thorium`、`sand-floor→sand`、`darksand→sand`，以及四种**矿墙** `ore-wall-thorium`、`ore-wall-beryllium`、`ore-wall-graphite`、`ore-wall-tungsten` 与 `graphitic-wall→graphite`。

矿层分两类（OreBlock.java:15 起，`wallOre` 字段）：地板矿 `wallOre = false`（Drill 采）与矿墙 `wallOre = true`（BeamDrill 采）。

## 数值

**表 1：六种钻头/采掘方块参数（v160.7 jar 反射 + v159.3 源码行号）**

| 方块 | 类 | size | tier | drillTime | hardnessDrillMultiplier | 液体加速 | itemCap | liquidCap | 耗电（/tick → /s） |
|---|---|---|---|---|---|---|---|---|---|
| mechanical-drill | Drill | 2 | 2 | 600 | 50 | 1.6（水 0.05） | 10 | 30 | 0 |
| pneumatic-drill | Drill | 2 | 3 | 400 | 50 | 1.6（水 0.0583） | 10 | 35 | 0 |
| laser-drill | Drill | 3 | 4 | 280 | 50 | 1.6（水 0.08） | 10 | 48 | 1.1 → 66 |
| blast-drill | Drill | 4 | 5 | 280 | 50 | 1.8（水 0.1） | 20 | 60 | 3 → 180 |
| impact-drill | BurstDrill | 4 | 6 | 720 | **0** | 1.75（臭氧 0.05） | 40 | 100 | 2.667 → 160 |
| eruption-drill | BurstDrill | 5 | 7 | 281.25 | **0** | 2.0（氰 0.0125） | 60 | 40 | 6 → 360 |
| plasma-bore | BeamDrill | 2 | 3 | 160 | —（不参与） | 2.5（氢 0.00417） | 10 | 10 | 0.15 → 9 |
| large-plasma-bore | BeamDrill | 3 | 5 | 100 | —（不参与） | 2.5（氮 0.05） | 20 | 30 | 0.8 → 48 |
| cliff-crusher | WallCrafter | 2 | — | 110 | — | 1.6 | 10 | 10 | 0.1833 → 11 |
| large-cliff-crusher | WallCrafter | 3 | — | 48 | — | 1.6（+石墨道具 1.6） | 20 | 10 | 1 → 60 |

出处：mechanical-drill Blocks.java:2866-2876；pneumatic Blocks.java:2878-2885；laser Blocks.java:2887-2898；blast Blocks.java:2900-2919；impact Blocks.java:3071-3092；eruption Blocks.java:3094-3122；plasma-bore Blocks.java:3039-3051；large-plasma-bore Blocks.java:3053-3069；cliff 系 Blocks.java:3003-3037。

**表 2：实测产出速率（全覆盖、无加速液；速率 = 覆盖格数 × 60 / getDrillTime）**

| 钻头 | 矿（hardness） | getDrillTime | 覆盖 | 件/s |
|---|---|---|---|---|
| mechanical-drill | copper(1) | 650 | 4 | **0.369** |
| mechanical-drill | coal(2) | 700 | 4 | 0.343 |
| mechanical-drill | copper(1) + 水 | 650 | 4 | **0.945**（×2.56） |
| pneumatic-drill | titanium(3) | 550 | 4 | 0.436 |
| laser-drill | titanium(3) | 430 | 9 | **1.256** |
| laser-drill | thorium(4) | 480 | 9 | 1.125 |
| blast-drill | thorium(4) | 480 | 16 | **2.0** |
| blast-drill | copper(1) | 330 | 16 | 2.909 |
| impact-drill | copper(1) | 720（无硬度项） | 16 | 1.333 |
| impact-drill | beryllium(3) | 720 ÷ 2 | 16 | **2.667** |
| eruption-drill | copper(1) | 281.25 | 25 | 5.333 |
| eruption-drill | beryllium(3) | 281.25 ÷ 2 | 25 | **10.67** |
| plasma-bore | 矿石墙 | 160 | 2 面 | 0.75 |
| large-plasma-bore | 矿石墙 | 100 | 3 面 | **1.8** |
| cliff-crusher | 沙属性墙 | 110 | eff ≤ 2 | ≤ **1.0909** |
| large-cliff-crusher | 沙属性墙 | 48 | eff ≤ 3 | ≤ **3.75** |

**表 4：采液方块**

| 方块 | pumpAmount | 有效度来源 | 满效产出 | 耗电 |
|---|---|---|---|---|
| water-extractor | 0.11 | validTiles(≤1) + 水属性均值 | 6.6/s（无属性地板） | 1.5/tick = 90/s |
| oil-extractor | 0.25 | Attribute.oil（baseEfficiency 0） | 满黑沙属性 1.5 时 **22.5/s**（`0.25×60×1.5`；属性 1.0 才是 15/s，UI 印的就是这个乐观值） | 3/tick = 180/s |

## 源码锚点

- `Drill.java:28` `hardnessDrillMultiplier = 50f`；`Drill.java:34-36` `tier` 与 `drillTime = 300` 默认值；`Drill.java:38` `liquidBoostIntensity = 1.6f`；`Drill.java:40` `warmupSpeed = 0.015f`。
- `Drill.java:170-172` `getDrillTime(item)` 的硬度加法公式。
- `Drill.java:198-229` `countOre` 与主矿排序（`:216` 的 lowPriority 比较）；`Drill.java:223-228` 取 `peek()`。
- `Drill.java:231-235` `canMine`：`drops.hardness <= tier && !blockedItems.contains(drops)`。
- `Drill.java:287-325` `updateTile`：`speed = lerp(1, liquidBoostIntensity, optionalEfficiency) * efficiency`（:301）、`progress += delta() * dominantItems * speed * warmup`（:305）、批量出货 `:315-321`。
- `Drill.java:181-190` stats 只给 `60f / drillTime * size * size`（**不含硬度、不含真实覆盖**），加速显示用 `liquidBoostIntensity * liquidBoostIntensity`（:188）。
- `BeamDrill.java:40-44` `range = 5` / `tier = 1` / `optionalBoostIntensity = 2.5`；`BeamDrill.java:198-214` `canPlaceOn` 逐面找第一堵 solid；`BeamDrill.java:246-262` 每周期按 `facing` 每格 1 件。
- `BurstDrill.java:39` `hardnessDrillMultiplier = 0f`；`BurstDrill.java:53-55` 覆写 `getDrillTime`；`BurstDrill.java:99-109` 进度不乘覆盖率、产出乘 `dominantItems`。
- `WallCrafter.java:141-181` `getEfficiency` 只取前方 `size` 格并累加 `attributes.get(attribute)`；`WallCrafter.java:213-215` `time += edelta() * eff` 达 `drillTime` 出 1 件。
- `SolidPump.java:153-159` `boost = sumAttribute(...)/size/size`、`validTiles += baseEfficiency/(size*size)`；`SolidPump.java:124-129` `maxPump = min(liquidCapacity - typeLiquid(), pumpAmount * delta * fraction * efficiency)`。
- `Tile.java:571-580` `drop()` 取 `overlay.itemDrop` 或 `floor.itemDrop`；`wallDrop()` 只对 `block.solid` 生效。
- `Block.java:438` `dumpTime = 5`（每 5 tick 尝试向邻近方块 `dump` 一次，触发 `offload` 下游）。
- `content/Blocks.java:597-675` 各墙的 `Attribute.sand` 具体值（dune-wall 2、sand-wall 2、carbon-wall 0.7、ferric-stone-wall 0.5）。

## 实测与反例

**反例 1（UI 的件/s 是乐观值）**：`Drill.setStats` 写 `60f / drillTime * size * size`（Drill.java:181），对 laser-drill 是 `60/280*9 = 1.929 件/s`；但真实 copper 覆盖 9 格的速率是 `9 × 60 / (280 + 50×1) = 1.636`，thorium 是 `9 × 60 / 480 = 1.125`。**同一个方块，UI 1.93 vs 实际 1.13，差 71%**。gamedata 的 `baseRateItemsPerSecond` 就是这个乐观值（laser-drill 1.928571），不能当产出。

**反例 2（gamedata 的 BeamDrill 速率错 2 倍）**：plasma-bore 的 `baseRateItemsPerSecond = 1.5`，但 `BeamDrill.setStats` 自己写的是 `60f / drillTime * size`（BeamDrill.java:127）= `60/160×2 = 0.75` 件/s，因为每面每周期只出 1 件（BeamDrill.java:253-260）。数据表的 1.5 用了 `size²`，对 BeamDrill 是错的。

**反例 3（impact-drill 采不了 thorium）**：tier 6 已经 ≥ thorium 的硬度 4，但 `blockedItem = Items.thorium`（Blocks.java:3081）把它写进 `blockedItems`（Drill.java:93-95），`canMine` 直接返回 false（Drill.java:234）。进阶钻头反而不能采一种基础矿是**故意的平衡**，不是 bug。

**反例 4（水加速不是 ×1.6）**：机械钻加水后实际速率 0.369 → 0.945 件/s（×2.56），因为 `speed` 与 `warmup` 各乘一次 1.6（Drill.java:301-305），UI 也印 2.56（Drill.java:188）。按 ×1.6 建产线会少算 60%。

**反例 5（矿墙要用激光钻）**：`ore-wall-thorium` 用 laser-drill 盖上去会显示「需要更高等级」，因为 `Drill.canMine` 要求 `!tile.block().isStatic()`（Drill.java:232），墙格直接排除。矿墙只能由 `wallDrop()` 路径采（Tile.java:575-580），即 BeamDrill。

**反例 6（BurstDrill 与硬度无关）**：impact-drill 采 copper 与采 tungsten 的 `getDrillTime` 都是 720（BurstDrill.java:53-55 不看 hardness），所以它在低硬度矿上反而不如 blast-drill（330 vs 720），只有矿越硬越划算。

## 常见误解

1. **「tier 越高采得越快」**——tier 只做硬度门槛（Drill.java:234），速度来自 `drillTime` 与覆盖率。
2. **「钻头放在矿边上也能采」**——`countOre` 只扫 `getLinkedTilesAs`，即方块自身覆盖的 size×size（Drill.java:205），边缘不算。
3. **「sand 和 copper 叠在一起，钻头会先采 copper 因为更值钱」**——排序依据是 `lowPriority` 与覆盖数，不是价值（Drill.java:215-221）；sand 的 `lowPriority = 1` 才让它排到后面。
4. **「加速液越多越快」**——`optionalEfficiency` 只在「有液」与「无液」之间插值（Drill.java:301），给满后不再叠加。
5. **「Water Extractor 直接架在水上最快」**——它要求 `!floor.isLiquid`（SolidPump.java:80-82），架在水面直接不可放。
6. **「cliff-crusher 采的是矿」**——它吃 `Attribute.sand`（Blocks.java:3009），与矿层无关，采的是墙。

## 相关

- W01 方块与多格锚点（size×size 与 `getLinkedTilesAs` 的格集合）
- W02 配方与制造（钻头产出进入冶炼链的入口）
- W04 液体（加速液从管道进入 `liquidCapacity`）
- W06 物流（`offload` / `dumpTime = 5` 把产物推到邻近方块）
- W10 存储（itemCapacity 满时钻头自动停，`shouldConsume` 只判容量）
