---
id: WORLD.LOGISTICS.001
title: 物流与物品传输（传送带 / 路由 / 交叉 / 桥 / 质量驱动器）
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/Conveyor.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/Duct.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/Junction.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/Router.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/ItemBridge.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/BufferedItemBridge.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/StackConveyor.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/MassDriver.java"
  - "Mindustry-Source/core/src/mindustry/world/blocks/distribution/DirectionalUnloader.java"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java"
data:
  - "00-data/blocks.json#id=conveyor"
  - "00-data/blocks.json#id=junction"
  - "00-data/blocks.json#id=mass-driver"
depends: [WORLD.BLOCKS.001, WORLD.CRAFTING.001]
tags: [物流, 传送带, conveyor, duct, router, junction, bridge, mass-driver, 吞吐, items/s]
tokens: 1837
---

## 一句话

物品在方块之间的移动全靠传送带、管道、路由器、交叉器、桥、质量驱动器这几类方块；源码里所有速率都是 **per tick**（×60 才是 /秒），而三种方块的 `speed` 字段**单位互不相同**（格/tick、tick/件、系数），混用会直接差一个数量级。

## 规则 / 公式

### 1. 三种速率的单位口径（先记这个，否则后面全错）

| 类 | 字段 | 单位 | 换算 | 源码 |
|---|---|---|---|---|
| `Conveyor` | `speed` | **格/tick** | 吞吐 ≈ `speed × 60 / itemSpace`，`itemSpace = 0.4` | Conveyor.java:32、Conveyor.java:27 |
| `Duct` | `speed` | **tick/件** | 显示值 = `60 / speed` | Duct.java:27、Duct.java:61 |
| `Junction` | `speed` | **tick/件** | 过路口等 26 tick | Junction.java:13 |
| `Router` | `speed` | 件/tick 系数 | `time += 1/speed × delta`，8 tick 放一件 | Router.java:13、Router.java:61 |
| `StackConveyor` | `speed` | 格/tick | 吞吐 = `itemCapacity × speed × 60` | StackConveyor.java:38、StackConveyor.java:67 |
| `MassDriver` | `reload` | tick/发 | 发速 = `60/reload`，件速 = `itemCapacity × 60/reload` | MassDriver.java:33、MassDriver.java:66-69 |

`Conveyor` 的吞吐推导：一格最多 3 件（`capacity = 3`，Conveyor.java:28），物品间距 `itemSpace = 0.4`（Conveyor.java:27）以「格」为单位，所以 1 格长度只排得下 2.5 件；每 tick 前进 `speed` 格 ⇒ 每秒通过 `speed × 60 / 0.4` 件。[v160.7] `conveyor` 的 `speed = 0.035` ⇒ 5.25 件/s；[v159.3] 源码 `speed = 0.046`（Blocks.java:2071）⇒ 6.9 件/s。UI 上那个 `displayedSpeed`（v160.7 = 5，v159.3 = 6.5）是**手填近似值**，源码注释原文写着实际移动速度「apparently not linear」（Conveyor.java:59-60），别拿它反推公式。

### 2. 传送带单格模型：3 件、间距 0.4、被前一件卡住

每格是一条长度 1 的「绳子」，物品位置 `ys ∈ [0,1]`，`ys = 1` 表示可以交给下游。每 tick 前移 `moved = speed × edelta`（Conveyor.java:266），但每一件的上限是「前一件位置 − itemSpace」：

```
nextpos = (i == len-1 ? 100 : ys[i+1]) - itemSpace
maxmove = clamp(nextpos - ys[i], 0, moved)   // 不能穿过前一件
ys[i] += maxmove
```

（Conveyor.java:268-272）当 `ys >= 1` 且下游 `acceptItem` 返回真，才真正交付（`pass()`，Conveyor.java:278、Conveyor.java:300-306）；下游不收就停在 1.0，后面的件依次压住——这就是回压（backpressure）。堵塞时 `minitem < itemSpace` 会让 `clogHeat` 每 tick 逼近 1（Conveyor.java:291-295），`clogHeat > 0.5` 时传送带不再推动踩在上面的单位、贴图停帧（Conveyor.java:145、Conveyor.java:229）。

一条 5 格直线传送带最多堆 5×3 = 15 件；堵满**不会丢物品**，只是不再前进。

### 3. 管道 Duct：1 件/格，却比传送带快

Duct 每格只放 1 件（`itemCapacity = 1`，Duct.java:44），`acceptItem` 要求 `current == null && items.total() == 0`（Duct.java:212-220），而且**不接受从背面进来的物品**（Duct.java:219 判 `!= 2`）；ArmoredDuct 反过来只接受正面来货（Duct.java:216-217）。

它的推进不是「每 tick 走一格」，而是积攒进度：

```
progress += edelta() / speed * 2                                   // Duct.java:194
if(progress >= 1 - 1f/speed && moveForward(current)){ ... progress %= 1 - 1f/speed; }
```

（Duct.java:194-201）`speed = 4`（Blocks.java:2180，v160.7 jar 同为 4）⇒ 阈值 0.75、每 tick +0.5，大约 2 件/3 tick ≈ 20 件/s；而 `setStats` 写的是 `60 / speed = 15` 件/s（Duct.java:61）。**两个口径都是源码写死的、互相不等**，所以本篇给区间 15–20 件/s 而不给单值。duct 靠「1 格 1 件 + 便宜」堆密度，不靠单格速度。

### 4. 路由器 / 交叉器 / 分选器：三个「不缓存」的小方块

- **Router**：`itemCapacity = 1`（Router.java:21），只有空槽才收（`acceptItem`，Router.java:79-81）；`time += 1f/speed × delta` 攒满 1 才放行（Router.java:61），`speed = 8` ⇒ 最快 7.5 件/s，且**目标也是 Router 时同样要等满**（Router.java:64）。选目标靠 `rotation` 在 `proximity` 里轮转（Router.java:119-127），是近似轮询而不是精确均分。
- **Junction**（交叉器）：不是「缓存 6 件」，而是**每个方向各 6 件**——`DirectionalItemBuffer(capacity)`，`capacity = 6`（Junction.java:46、Junction.java:14）。物品带时间戳进来，等满 `speed = 26` tick 才朝同方向邻居交付（Junction.java:62-74）。所以一个路口最多压 4×6 = 24 件，任意方向过路口要 26 tick ≈ 0.43 s。
- **Sorter / InvertedSorter**：`sortItem` 是配置项（Sorter.java:37-38），命中的物品走正前方、不命中的走两侧（Sorter.java:96-133）；`instantTransfer = true`（Sorter.java:28）表示「这一格本身不花 tick」，但前后格该等还得等。
- **OverflowGate / UnderflowGate**：`itemCapacity = 0`（不缓存）、`instantTransfer = true`，正面能收就直送，不能收才往两侧分（OverflowGate.java:22-25、OverflowGate.java:51-81）；underflow 只是 `invert = true`（Blocks.java:2209-2216）。两者 `canOverdrive = false`（v160.7 jar 反射），不吃超频加成。

### 5. 桥与相位桥：链式投递

`bridge-conveyor`（BufferedItemBridge）：`range = 4`、`bufferCapacity = 14`、`itemCapacity = 10`、`speed = 74`、`displayedSpeed = 11`（Blocks.java:2105-2113，v160.7 jar 完全一致）；内部一个 `ItemBuffer`，`poll(speed/timeScale)` 取件（BufferedItemBridge.java:41），源码注释承认「移动速度靠实测」（BufferedItemBridge.java:27）。它的 11 件/s 就是这一格的吞吐上限，比传送带的 5 件/s 高一倍多。

`phase-conveyor`（ItemBridge）：`range = 12`、`transportTime = 2`、耗电 `0.30/tick = 18/s`（Blocks.java:2115-2125）。它不缓冲，每 `transportTime` tick 直接 `items.take()` 投一件（ItemBridge.java:355-368）⇒ 上限 60/2 = 30 件/s。链接约束在 `positionsValid`：两端必须**同一行或同一列**且距离 ≤ range，否则直接 `false`（ItemBridge.java:157-165），斜放无效。

### 6. 质量驱动器：两端各留 10 件才开火

`mass-driver`：`range = 440`（px，= 55 格，stats 显示 `range/tilesize`，MassDriver.java:66）、`reload = 200` tick/发、`itemCapacity = 120`、`minDistribute = 10`、`size = 3`（Blocks.java:2166-2173；MassDriver.java:31）。开火是一串「与」条件：

- 自己库存 `>= minDistribute`，且**对面剩余容量** `>= minDistribute`（MassDriver.java:192-193）；
- 对面正处在接收态、且没有别的驱动器在排队（MassDriver.java:204-206）；
- 两端旋转角都对齐到 ±2° 内（MassDriver.java:204-206），否则一直转（`rotateSpeed = 5`，MassDriver.java:29）；
- 有电（`efficiency > 0`，MassDriver.java:169）。

开火时把库存**按物品类型全部打包**发走，单类型上限取 `min(自己库存, 对面剩余容量)`（MassDriver.java:298-303）；接收端最多加到 `itemCapacity × 2 = 240`（MassDriver.java:324）。所以它一发就是 100+ 件级别，`60/reload = 0.3` 发/s × 120 = 36 件/s 的名义件速（MassDriver.java:66-69）。

### 7. 卸载器（取货端）

- `unloader`：从紧邻的存储方块（核心/容器）里取一件推到正面，`speed = 60/11 ≈ 5.4545` tick/件 ⇒ **11 件/s**（Blocks.java:2162；stats 显示 `60/speed`，Unloader.java:61-63），默认 `allowCoreUnload = true`。
- `duct-unloader`（DirectionalUnloader）：`speed = 4` ⇒ **15 件/s**（Blocks.java:2227-2234），`unloadTimer += edelta()` 攒满 `speed` 才搬一件（DirectionalUnloader.java:93-118），且默认 `allowCoreUnload = false`（DirectionalUnloader.java:26）——不能从核心直抽，只能从容器抽。

取货端的存储容量与优先级见 W10。

## 数值

**运输方块全表（v160.7 jar 反射；同名记录在 `00-data/blocks.json#id=<name>`）**

| 方块 | size | itemCapacity | speed 原值 | 吞吐（件/s） | 出处 |
|---|---|---|---|---|---|
| `conveyor` | 1 | 3 | 0.035 格/tick | **5.25**（UI 显示 5）；[v159.3] 0.046 ⇒ 6.9 | Blocks.java:2068-2074 |
| `titanium-conveyor` | 1 | 3 | 0.0801 格/tick | 10 | Blocks.java:2076-2081 |
| `armored-conveyor` | 1 | 3 | 0.08 格/tick | 10（[v159.3] displayedSpeed 11） | Blocks.java:2090-2095 |
| `plastanium-conveyor` | 1 | 10 | 0.0667 格/tick | 40（10×0.0667×60） | Blocks.java:2083-2088 |
| `surge-conveyor` | 1 | 10 | 0.0833 格/tick | 50（10×0.0833×60），耗电 1/tick | Blocks.java:2236-2252 |
| `duct` / `armored-duct` | 1 | 1 | 4 tick/件 | 15（stats）～20（手算） | Blocks.java:2177-2190 |
| `duct-router` | 1 | 1 | 4 tick/件 | 15 | Blocks.java:2192-2199 |
| `duct-bridge` | 1 | 4 | 4 tick/件，range 4 | 15 | Blocks.java:2218-2225 |
| `junction` | 1 | 10（每向缓冲 6） | 26 tick/件 | 13（displayedSpeed） | Junction.java:13-15 |
| `router` / `distributor` | 1 / 2 | 1 | 8 | 7.5（手算） | Router.java:13、Blocks.java:2138-2143 |
| `bridge-conveyor` | 1 | 10（缓冲 14） | 74，range 4 | 11 | Blocks.java:2105-2113 |
| `phase-conveyor` | 1 | 10 | transportTime 2，range 12 | 30（上限），耗电 18/s | Blocks.java:2115-2125 |
| `mass-driver` | 3 | 120 | reload 200 | 0.3 发/s、36 件/s（名义），耗电 105/s | Blocks.java:2166-2173 |
| `unloader` | 1 | 0 | 5.4545 tick/件 | 11 | Blocks.java:2160-2164 |
| `duct-unloader` | 1 | 0 | 4 tick/件 | 15 | Blocks.java:2227-2234 |

**单格缓冲容量（堵住时最多压多少件）**

| 方块 | 每格/每向容量 | 说明 | 出处 |
|---|---|---|---|
| `conveyor` / `titanium-conveyor` / `armored-conveyor` | 3 件/格 | `capacity = 3`、间距 0.4 | Conveyor.java:27-28 |
| `plastanium-conveyor` / `surge-conveyor` | 10 件/整条带 | 存储式传送带 | StackConveyor 默认；Blocks.java:2087 |
| `duct` / `armored-duct` | 1 件/格 | `itemCapacity = 1` | Duct.java:44 |
| `junction` | 6 件 × 4 向 = 24 件 | `DirectionalItemBuffer(capacity)` | Junction.java:14、Junction.java:46 |
| `router` / `distributor` | 1 件 | 只有单槽 | Router.java:21 |
| `bridge-conveyor` | 14 件 | `bufferCapacity` | Blocks.java:2111 |
| `duct-bridge` | 4 件 | jar 反射 `itemCapacity = 4` | 00-data/blocks.json#id=duct-bridge |
| `mass-driver` | 120 件（接收端吃 240） | `itemCapacity × 2` 上限 | MassDriver.java:324 |

**双版本差异（v159.3 源码 vs v160.7 jar）**

| 方块 | 字段 | v159.3 源码 | v160.7 线上 |
|---|---|---|---|
| `conveyor` | `speed` | 0.046（Blocks.java:2071） | 0.035 |
| `conveyor` | `displayedSpeed` | 6.5（Blocks.java:2072） | 5 |
| `armored-conveyor` | `displayedSpeed` | 11（Blocks.java:2094） | 10 |
| `junction` | `speed` / `capacity` | 26 / 6（Blocks.java:2099-2100） | 26 / 6（一致） |
| `bridge-conveyor` | `speed` / `bufferCapacity` | 74 / 14（Blocks.java:2109-2111） | 74 / 14（一致） |

## 源码锚点

- `Conveyor.java:27-28` `itemSpace = 0.4f`、`capacity = 3`；`Conveyor.java:32-33` `speed` / `displayedSpeed`；`Conveyor.java:59-60` 注释「实际速度非线性」。
- `Conveyor.java:265-298` `updateTile`：`nextMax` 对齐、`moved = speed * edelta()`、逐件 clamp、`ys >= 1 && pass()` 交付；`Conveyor.java:291-295` `clogHeat`。
- `Conveyor.java:300-306` `pass()`：`next.acceptItem(this, item)` 才转交。
- `Duct.java:61` stats `60f / speed`；`Duct.java:193-209` `progress` 推进；`Duct.java:212-220` `acceptItem` 与背面禁令。
- `Junction.java:13-15` `speed = 26` / `capacity = 6` / `displayedSpeed = 13`；`Junction.java:54-78` 每向独立队列、`Time.time >= time + speed` 才交付。
- `Router.java:13` `speed = 8`；`Router.java:61` `time += 1f / speed * delta()`；`Router.java:100-129` `getTileTarget` 轮转。
- `StackConveyor.java:64-68` `stats.add(Stat.itemsMoved, round(itemCapacity * speed * 60))`。
- `BufferedItemBridge.java:12-14` `speed = 40`（默认）/ `bufferCapacity = 50` / `displayedSpeed = 11`；`BufferedItemBridge.java:36-47` `buffer.poll` 与 `timer(timerAccept, 4 / timeScale)`。
- `ItemBridge.java:157-165` `positionsValid` 同行/同列约束；`ItemBridge.java:355-368` `updateTransport` 按 `transportTime` 投递。
- `MassDriver.java:29-36` `rotateSpeed/translation/minDistribute/reload`；`MassDriver.java:192-206` 开火条件；`MassDriver.java:290-303` `fire()` 打包全部库存；`MassDriver.java:66-69` 发速 stats。
- `DirectionalUnloader.java:25-26` `speed` / `allowCoreUnload`；`DirectionalUnloader.java:93-118` `unloadTimer` 循环。
- `content/Blocks.java:2068-2267` 所有运输方块的具体赋值（本表数值的源头）。

## 实测与反例

**反例 1（`displayedSpeed` 反推不出真实吞吐）**：`titanium-conveyor` 的 `speed = 0.0801` 格/tick，按 `0.0801 × 60 / 0.4` 应为 **12.0 件/s**，但游戏 UI 写 **10 件/s**（Blocks.java:2080）；`armored-conveyor` 同样 0.08 格/tick 算得 12.0，UI 写 10（v160.7）/ 11（v159.3 源码 Blocks.java:2094）。偏差 17–20%，所以官方自己用 `displayedSpeed` 而不是现算。任何「传送带 = X 件/s」的结论都必须说明是哪个口径。

**反例 2（junction 不是 6 件，是 24 件）**：`capacity = 6` 常被读成「整个路口缓存 6 件」。实际构造是 `DirectionalItemBuffer(capacity)`（Junction.java:46），**每方向一条 6 件队列**，四向共 24 件；而且过路口要等 `speed = 26` tick（Junction.java:62），所以它吞吐只有 `displayedSpeed = 13` 件/s，不是「无限直通」。

**反例 3（`duct` 的 `speed = 4` 不是速度）**：若把 duct 的 4 当成「4 格/tick」，会算出 240 件/s；实际 `Duct.java:194` 是 `progress += edelta()/speed*2`，**speed 越大越慢**，4 对应 15–20 件/s。传送带与管道这两个 `speed` 的单位是反的。

**反例 4（质量驱动器 9 件永远不发）**：`minDistribute = 10`（Blocks.java:2166-2173、MassDriver.java:31），自己库存 9 件、或对面剩余空间 9 格时，条件 `items.total() >= minDistribute && link.block.itemCapacity - link.items.total() >= minDistribute`（MassDriver.java:192-193）不成立，驱动器一直转但不开火。看起来像「坏了」，其实是阈值。

**反例 5（相位桥斜放无语义）**：`positionsValid` 只在 `x1 == x2` 或 `y1 == y2` 时比较距离，其他情况直接 `return false`（ItemBridge.java:157-165）。把两个相位桥对角摆 3 格，距离 4.2 px 看似在 `range = 12` 内，但链接永远不成立。

**反例 6（回压会停单位但不会丢货）**：传送带堵住时 `clogHeat` 升到 1（Conveyor.java:291-295），此时 `unitOn` 直接 return、不再给单位加速度（Conveyor.java:229），但带上的 3 件物品原地不动、不消失。用这招可以「用传送带粘住敌人」，但不会销毁物品。

## 常见误解

1. **「传送带堵住会丢物品」**——不会。`acceptItem` 为假时物品停在 `ys = 1`，内部的 `items` 计数不变（Conveyor.java:278-289），直到下游接收。
2. **「路由器把物品均分到三条支线」**——是近似轮询 `(i + counter) % proximity.size`（Router.java:119-127），单槽 1 件（Router.java:21）、8 tick 放一次（Router.java:61），瞬时脉冲会全走第一条能收的线。
3. **「交叉器 = 十字路口缓存」**——它只缓存自己方向的 6 件（Junction.java:14、46），逆向堵住时整条线停摆，不会把货转到别的方向。
4. **「分选器是零延迟」**——`instantTransfer = true`（Sorter.java:28）只表示「不额外加 tick」，仍受前后格 `acceptItem` 与 8 tick 节拍约束。
5. **「质量驱动器能跨地图」**——`range = 440` px = **55 格**（MassDriver.java:66），超出后 `linkValid` 为假、直接 dump（MassDriver.java:164-166）。
6. **「duct 比传送带慢」**——`duct` 15–20 件/s 明显快于 `conveyor` 的 5.25 件/s（v160.7），代价是 1 件/格、且要吃铍/电。

## 相关

- W01 方块与多格锚点（传送带 `rotate = true`、`underBullets`、size 与格数）
- W02 配方与制造（产线入口输出到本层的传送带）
- W10 存储（核心/容器/`unloader` 的取货优先级与容量）
- W08 载荷（payload 传送带/路由器与物品传送带的区别）
- W04 液体（管道与传送带是两套完全独立的传输系统）
