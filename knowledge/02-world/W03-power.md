---
id: WORLD.POWER.001
title: 电力网络
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/PowerGraph.java:86-93, 154-257"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/PowerNode.java:33-35, 60-95"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/PowerDiode.java:48-83"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/PowerGenerator.java:25, 50, 67, 156-158"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/BeamNode.java:29, 79-91"
  - "Mindustry-Source/core/src/mindustry/world/consumers/ConsumePower.java:9-59"
  - "Mindustry-Source/core/src/mindustry/world/Block.java:48-59"
  - "MBO/gamedata/v160.7/gamedata.json (jar 反射，129 个 hasPower 方块)"
data: [00-data/blocks.json]
depends: [WORLD.CRAFTING.001, WORLD.BLOCKS.001]
tags: [电力, PowerGraph, 电池, 二极管, 节点, 激光节点, 过载, powerLoss]
tokens: 1450
---

## 一句话

电力没有"线路"实体：**节点把方块连成一张图（PowerGraph），整张图每 tick 做一次"总需求 vs 总产出"结算**，用 `coverage = min(1, 产出/需求)` 这个统一比例给所有非缓冲设备供电，多余的电按百分比灌进电池、不足的电按百分比从电池抽——中间没有任何传输损耗。

## 规则 / 公式

### 1. 电力是怎么"连"起来的

五个布尔字段决定一个方块能不能进网 [src: Block.java:48-59]：

| 字段 | 含义 |
|---|---|
| `hasPower` | 有 PowerModule（能存/用/发电的载体） |
| `consumesPower` | 默认 **true**；节点类方块必须显式置 false，否则会被当成耗电设备 |
| `outputsPower` | 发电机 |
| `connectedPower` | 为 false 时节点不能连它 |
| `conductivePower` | 为 true 时可像电缆一样"穿过"传导（电力层地板/墙体） |

入图规则在 `PowerGraph.add()` [src: PowerGraph.java:290-299]：

- `outputsPower && consumesPower && !buffered` → 同时进 producers 和 consumers（如 `impact-reactor`）；
- `outputsPower && consumesPower && buffered` → 进 **batteries**（如 `battery`、`beam-node`）；
- 只有 `outputsPower` → producers；只有 `consumesPower` → consumers。

**节点本身是"建图工具"**：`power-node` 只有 `laserRange` 与 `maxNodes`，它不消耗也不产出电（`consumesPower = false, outputsPower = false`）。

### 2. 每 tick 结算（核心公式）

```
needed   = Σ requestedPower(consumer) * consumer.delta()      // 每 tick 需求
produced = Σ getPowerProduction(producer) * producer.delta()  // 每 tick 产出
coverage = min(1, produced / needed)                          // 全图统一供电率
```

非缓冲设备：`consumer.power.status = coverage`（`ConsumePower.efficiency()` 直接返回它 [src: ConsumePower.java:37-40]）
缓冲设备：`status += requestedPower * coverage * delta / capacity`（按容量比例充 [src: PowerGraph.java:195-200]）

关键点：**需求是"全图总和"，不是逐台排队**。所以 10 台设备抢 50% 的电时，每台都恰好拿到 50%，不存在"先连的先满电"。

### 3. 电池（容量单位与充放规则）

- `consPower.capacity` 是"电量"单位；电池的 `power.status ∈ [0,1]`，实际电量 = `status × capacity`。
- 充电：`chargedPercent = min(excess / 剩余容量, 1)`，然后每块电池 `status += (1 - status) × chargedPercent` [src: PowerGraph.java:170-185]。
- 放电：`consumedPercentage = min(1, needed / stored)`，每块电池 `status *= (1 - consumedPercentage)` [src: PowerGraph.java:154-168]。

两条都是**按百分比同步**——并联的大电池和小电池永远保持相同的"充满度百分比"，不会出现"先充满一块再充下一块"。

注意 `getBatteryCapacity()` 返回的是**剩余可充容量** `(1 - status) × capacity`，不是总容量；总容量是 `getTotalBatteryCapacity()` [src: PowerGraph.java:130-152]。这两个方法名字极易看反。

### 4. 二极管（单向阀）

`PowerDiodeBuild.updateTile()` 每 tick 比较两侧电网的电池百分比 [src: PowerDiode.java:56-82]：

```
if (backStored/backCapacity <= frontStored/frontCapacity) return;   // 前侧不比后侧空就不动
targetPct = (frontStored + backStored) / (frontCapacity + backCapacity)
amount    = (targetPct * frontCapacity - frontStored) / 2           // 只搬差值的一半
amount    = clamp(amount, 0, frontCapacity - frontStored)           // 不让前侧溢出
backGraph.transferPower(-amount); frontGraph.transferPower(amount);
```

所以二极管**只是"拉平"，不是"穿透"**，而且每次只拉平一半差距；两侧都必须 `hasPower` 且**都有电池容量**（`frontCapacity == 0` 时 amount 被 clamp 到 0，完全不输电）。

### 5. 节点 / 激光节点 / 光束塔的范围

| 方块 | 类 | 连接方式 | 范围（格） | 最大连线数 |
|---|---|---|---|---|
| power-node | PowerNode | 手动连线 | laserRange 6 | 10 |
| power-node-large | PowerNode | 手动连线 | laserRange 15 | 15 |
| surge-tower | PowerNode | 手动连线（视觉是激光） | laserRange 40 | 2 |
| beam-link | LongPowerNode | 远距离连线 | laserRange 500 | 1 |
| beam-node | BeamNode | 四方向**自动连** | range 10 | 相邻自动 |
| beam-tower | BeamNode | 四方向自动连，3×3 | range 23 | 相邻自动 |

`PowerNode` 字段默认值是 `laserRange = 6`、`maxNodes = 3` [src: PowerNode.java:33-35]，具体方块在 `Blocks.java` 里覆盖（所以"默认只能连 3 条"只在自定义方块里成立）。

`BeamNode` 沿上下左右四方向找最近的一个 `hasPower` 非节点方块并连上，遇到 `isInsulated()` 的方块会**中断**光束 [src: BeamNode.java:79-91]。二极管 `insulated = true`（`PowerDiode.java:22`），所以它天然挡光束。

### 6. 单位换算（最容易差 60 倍）

| 字段 | 单位 | 显示 |
|---|---|---|
| `ConsumePower.usage` | 电 / **tick** | UI `usage * 60f`，标 /秒 [src: ConsumePower.java:47] |
| `PowerGenerator.powerProduction` | 电 / **tick** | UI `powerProduction * 60f` [src: PowerGenerator.java:67] |
| `power.status` | 0–1 比例 | 进度条 |
| `consPower.capacity` | 电量（不是 /s） | 电池电量 |

1 单位电/tick × 60 = 1 单位电/秒。所有"XX/s"的数字都是 per-tick 值 × 60 得来的。

### 7. "过载"在原版是什么

原版**没有**过载烧毁/跳闸，也没有 `powerLoss` 字段（本仓库 v159.3 源码树与 v160.7 反射数据里都搜不到）。所谓"过载"只有一种表现：`needed > produced` 时 `coverage < 1`，全图设备**等比降效**（耗电设备 `efficiency = coverage`），表现为工厂变慢、炮塔变慢，不会爆炸。反应堆熔毁走的是热量系统（`WORLD.HEAT.001`），与电网无关。

## 数值

以下取自 v160.7 jar 反射（[src: jar:v160.7#blocks[name=…].power]，同源字段见 `00-data/blocks.json#id=<name>` 的 `power` 子树）。

**发电（per tick → per second）**

| 方块 | 类型 | powerProduction /tick | /秒 |
|---|---|---|---|
| combustion-generator | ConsumeGenerator | 1 | 60 |
| solar-panel | SolarGenerator | 0.12 | 7.2 |
| solar-panel-large | SolarGenerator | 1.6 | 96 |
| thermal-generator | ThermalGenerator | 1.8 | 108 |
| steam-generator | ConsumeGenerator | 5.5 | 330 |
| rtg-generator | 无输入 | 4.5 | 270 |
| differential-generator | ConsumeGenerator | 18 | 1080 |
| thorium-reactor | NuclearReactor | 15 | 900 |
| impact-reactor | ImpactReactor | 130 | 7800 |
| neoplasia-reactor | VariableReactor | 140 | 8400 |
| flux-reactor | VariableReactor | 300 | 18000 |
| power-source（沙盒） | PowerSource | 16666.67 | ≈1e6 |

**耗电（per tick → per second）**

| 方块 | usage /tick | /秒 |
|---|---|---|
| pyratite-mixer | 0.2 | 12 |
| silicon-smelter | 0.5 | 30 |
| plastanium-compressor | 3 | 180 |
| phase-weaver | 5 | 300 |
| impact-reactor（自身耗电） | 25 | 1500 |
| power-void（沙盒，吸收一切） | Float.MAX_VALUE ≈ 3.4e38 | 无意义 |

**电池容量**

| 方块 | capacity | 备注 |
|---|---|---|
| beam-node | 1000 | 1×1，兼作电池 |
| battery | 4000 | 1×1 |
| beam-tower | 40000 | 3×3 |
| battery-large | 50000 | 3×3 |

其它计数：`hasPower = true` 的方块 **129 个**（447 个方块中占 28.9%）。

## 源码锚点

- `PowerGraph.java:216-257` `update()`：先算 needed/produced，再用电池补/吸收，最后 `distributePower()`。
- `PowerGraph.java:187-214` `distributePower()`：`coverage = min(1, produced/needed)`，非缓冲设备直接 `status = coverage`。
- `PowerGraph.java:86-93` `getSatisfaction()` = `clamp(produced / needed)`，UI 电力条的分子。
- `PowerGraph.java:154-185` `useBatteries()` / `chargeBatteries()`：按百分比同步充放。
- `PowerGraph.java:290-299` `add()`：producer / consumer / battery 三分类规则。
- `ConsumePower.java:9-14` `usage`（per tick）、`capacity`、`buffered` 三个字段的注释。
- `ConsumePower.java:56-59` `requestedPower()`：缓冲设备按 `(1-status)*capacity` 请求，非缓冲按 `usage * (shouldConsume ? 1 : 0)`。
- `PowerGenerator.java:156-158` `getPowerProduction() = enabled ? powerProduction * productionEfficiency : 0`。
- `PowerNode.java:60-95` 连线配置：未连线则 `linkValid` + `links.size < maxNodes` 才允许；连线后 `addGraph` 合并电网。
- `PowerDiode.java:56-82` 二极管的半差搬运逻辑。
- `Block.java:48-59` `hasPower / consumesPower / outputsPower / connectedPower / conductivePower`。

## 实测与反例

**反例 1（`powerLoss` 这个字段不存在）**：很多旧资料写"电力有 powerLoss 损耗，长距离要加中继"。v159.3 源码树全树搜 `powerLoss` 命中 0 处，v160.7 反射数据里也没有这个字段。电从生产到消费是**瞬时全图结算**，与距离无关；节点只决定"是否在同一张图里"，不决定"输多少"。长距离真正要担心的是 `laserRange` 够不够、`maxNodes` 够不够连。

**反例 2（电池不是"先充满一块再充下一块"）**：`chargeBatteries()` 用 `chargedPercent = excess / 剩余容量` 对**每块**电池做 `status += (1-status) * chargedPercent`。所以并一块 4000 电量的小电池和一块 50000 的大电池，两块永远同步在同一个百分比上——大电池的实际电量始终是小电池的 12.5 倍。想"分批储能"在机制上做不到。

**反例 3（二极管两侧没电池就完全不传）**：`amount = clamp(amount, 0, frontCapacity - frontStored)`，当 `frontCapacity == 0`（前侧电网没有任何电池）时上限是 0，二极管一点电都不送。更隐蔽的是 `if(backStored/backCapacity <= frontStored/frontCapacity) return;`：两侧百分比相等就完全不动，所以"想用二极管把满电电池组的电送进空电网"在百分比相等那一刻就停，必须有负载持续拉低前侧百分比。

**反例 4（`hasPower` ≠ 会耗电）**：`hasPower = true` 的方块 129 个，其中 `consumesPower = false` 的（节点、光束节点、纯发电机）不会被算进 `needed`。反之 `Block.consumesPower` **默认 true**——自定义方块若忘了置 false，会被电网当成耗电设备而拉低全图 `coverage`。

**反例 5（电池容量字段不是"每秒能放多少"）**：`battery` 的 `capacity = 4000` 是"总电量"，不是放电功率。放电速率只受 `needed` 约束：4000 电量在一 tick 内可被抽干（如果需求足够大），没有"最大放电功率"字段。

## 常见误解

1. **"电力单位是 kW / 有真实功率"** → 无单位。1 电 = 1/tick 的资源量，UI 全部 ×60 显示为 /秒。核电站 15/tick 显示 900/s，不是"900 kW"。
2. **"节点越多输电越强"** → 节点不传输、不中转、不限流，只负责把方块放进同一张图。限制只有 `maxNodes`（连线数）与 `laserRange`（距离）。
3. **"beam-node 比 power-node 高级所以更快"** → 没有"更快"。差别是：beam-node **不用手动连线**（按 `range` 四方向自动连）且自带 1000 电量容量；代价是只能沿四方向、会被 `insulated` 方块截断。
4. **"电池能当无限缓冲，电网永不 brownout"** → 电池只在"产出 > 需求"时充、在"需求 > 产出"时补；两者都不够时 `coverage = produced/needed`，仍然降额。
5. **"过载会炸电网 / 烧电线"** → 原版无过载爆炸。爆炸来自反应堆热量（`NuclearReactor` 的 `heat` / `maxTemp`，见 `WORLD.HEAT.001`）。
6. **"设备断了电就完全不消耗材料"** → 耗电设备 `efficiency = coverage`，`coverage > 0` 时仍按比例推进进度、按比例扣材料/液体；只有 `coverage = 0` 才全停。

## 相关

- `WORLD.CRAFTING.001`（`ConsumePower` 在配方里的位置、usage 与 craftTime 的相互作用）
- `WORLD.STORAGE.001`（电池与物品/液体存储的优先级差异）
- `WORLD.HEAT.001`（反应堆熔毁、`heatOutput` 与热力发电）
- `WORLD.LOGISTICS.001`（堵料导致 `shouldConsume()` 变 false，耗电随之归零）
- `WORLD.SANDBOX.001`（`power-source` / `power-void` 是沙盒专用）
- 数据表：`00-data/blocks.json`（`power.usage` / `power.usagePerSecond` / `power.capacity` / `power.powerProduction` / `power.productionPerSecond`）
- 源码：`world/blocks/power/PowerGraph.java`、`PowerNode.java`、`PowerDiode.java`、`PowerGenerator.java`、`BeamNode.java`、`world/consumers/ConsumePower.java`、`world/Block.java`
