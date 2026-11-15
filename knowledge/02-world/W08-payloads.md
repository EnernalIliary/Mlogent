---
id: WORLD.PAYLOAD.001
title: 载荷：方块载荷与单位载荷的整块搬运链（传送带 / 路由 / 建造机 / 解构机 / 质量驱动器）
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src:
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/Payload.java:16-52 [src: Payload.java:16-52]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadConveyor.java:21-283 [src: PayloadConveyor.java:21-283]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadRouter.java:54-143 [src: PayloadRouter.java:54-143]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadBlock.java:18-118 [src: PayloadBlock.java:18-118]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/BuildPayload.java:71-88 [src: BuildPayload.java:71-88]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/UnitPayload.java:98-101 [src: UnitPayload.java:98-101]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadMassDriver.java:24-86 [src: PayloadMassDriver.java:24-86]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadDeconstructor.java:20-203 [src: PayloadDeconstructor.java:20-203]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/PayloadLoader.java:22-81 [src: PayloadLoader.java:22-81]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/Constructor.java:21-56 [src: Constructor.java:21-56]
  - Mindustry-Source/core/src/mindustry/world/blocks/payloads/BlockProducer.java:22-120 [src: BlockProducer.java:22-120]
  - Mindustry-Source/core/src/mindustry/world/Block.java:60-65 [src: Block.java:60-65]
  - Mindustry-Source/core/src/mindustry/world/Block.java:1432-1449 [src: Block.java:1432-1449]
data:
  - 00-data/blocks.json#id=payload-conveyor
  - 00-data/blocks.json#id=payload-router
  - 00-data/blocks.json#id=payload-mass-driver
  - 00-data/blocks.json#id=constructor
  - 00-data/blocks.json#id=deconstructor
  - 00-data/blocks.json#id=payload-loader
  - 00-data/blocks.json#id=payload-unloader
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001, WORLD.STORAGE.001]
tags: [载荷, payload, 载荷传送带, 载荷路由, 建造机, 解构机, 载荷质量驱动器, 单位载荷]
tokens: 2105
---

## 一句话

载荷（payload）是「整块被搬运的方块或单位」，走一条与物品物流完全独立的通道：载荷传送带按 tick 节拍逐格推送、载荷路由按被搬内容排序、建造机现场造建筑、解构机把建筑拆回物品、载荷质量驱动器把载荷跨图打击，所有容量统一以格数（tilesize = 8 px）而不是物品种数计量。

## 规则 / 公式

### 1. 载荷只有两种对象，尺寸都以像素给出

- `Payload.java:16` 定义 `payloadUnit = 0`、`Payload.java:17` 定义 `payloadBlock = 1`；存档与网络流里首字节就是这两个值（BuildPayload.java:97 写 `write.b(payloadBlock)`、UnitPayload.java:72 写 `write.b(payloadUnit)`）。 [src: Payload.java:16]
- 方块载荷的尺寸来自方块：`BuildPayload.size()` 返回 `build.block.size * tilesize`（BuildPayload.java:86-88），即 3 格方块 = 24 px。 [src: BuildPayload.java:86-88]
- 单位载荷的尺寸来自碰撞体积：`UnitPayload.size()` 返回 `unit.hitSize`（UnitPayload.java:98-101），与方块格数无关。 [src: UnitPayload.java:98-101]
- 全系统只有一个尺寸判定函数：`Payload.java:50-52` `public boolean fits(float s){ return size() / tilesize <= s; }`，源码注释直接写「3 is the max for a standard 3x3 conveyor」。 [src: Payload.java:50-52]

### 2. 载荷容量是「边长格数」，不是格数平方

payloadLimit = 3（PayloadConveyor.java:21）表示「能通过的载荷最大边长 3 格」，换算成像素是 3 × 8 = 24 px。所以： [src: PayloadConveyor.java:21]

- constructor 是 3 格（24 px）方块，可以进；large-constructor 是 5 格（40 px），进不去。
- 单位看 hitSize：一个 hitSize ≤ 24 px 的单位才算合格，和它是几级单位无关（PayloadConveyor.java:87 在推送单位前用 `unit.hitSize / tilesize <= payloadLimit` 再判一次）。 [src: PayloadConveyor.java:87]

载荷方块参数（00-data/blocks.json 可核）：payload-conveyor 与 payload-router 都是 3 格、health 360、buildVisibility shown、solid false、underBullets true；reinforced 两版 3 格、health 800。

### 3. 传送节拍：moveTime 45 tick 推一格

- PayloadConveyor.java:21 `public float moveTime = 45f, moveForce = 201f, payloadLimit = 3f;` [src: PayloadConveyor.java:21]
- `updateTile`（PayloadConveyor.java:137-188）里 `float progress = time() % moveTime;` `int curStep = (int)(time() / moveTime);`，curStep 增长那一 tick 才尝试把载荷交给下游；下游为空且不被堵塞时 `item.dump()` 掉到地上。 [src: PayloadConveyor.java:137-188]
- 速率：60 / 45 = 1.333 载荷/s（每 45 tick 一格）。reinforced-payload-conveyor 的 moveTime 是 35 ⇒ 60 / 35 = 1.714 载荷/s。
- 收料窗口极窄：acceptPayload（PayloadConveyor.java:279-283）要求 `item == null && payload.fits(payloadLimit) && (source == this || (enabled && progress <= 5f))` [src: PayloadConveyor.java:279-283]，即上游只能在周期前 5 tick 交付，占 45 tick 的 5 / 45 ≈ 11%，错过就得排下一轮。这是「载荷传送带串长链会掉速」的直接原因。
- 对接判定（:107-121）：同尺寸邻居可直接对接，更大尺寸邻居取中心格对齐；`blocked`（:128）定义为 `next.solid && !next.outputsPayload && !next.acceptsPayload || next.payloadCheck(rotation)`。

### 4. 载荷路由：按「内容」而不是按方向排序

- `PayloadRouter extends PayloadConveyor`（PayloadRouter.java:23），构造里设 `outputFacing = false`（:32）、`configurable = true`、`clearOnDoubleTap = true`，config 的类型是 Block 或 UnitType（:36-38）。 [src: PayloadRouter.java:23]
- 可排序范围 `canSort(Block b)`（PayloadRouter.java:54-56）：`b.isVisible() && b.size <= size && !(b instanceof CoreBlock) && !state.rules.isBanned(b) && b.environmentBuildable()` ⇒ 3 格路由只能排 1–3 格方块；核心方块永远可穿过但不可作为排序目标。 [src: PayloadRouter.java:54-56]
- `pickNext()`（:76-103）：命中 sorted 就照 recDir 直走；未命中则在 4 个方向里轮转并跳过 recDir（:87-89），直到找到一个能 `acceptPayload` 的邻居，最多试 4 次（:98）。
- 逻辑控制转向后 `controlTime = 60f * 6f = 360` tick 内不再自动转向（:112），即 6 秒不抢方向盘。

### 5. 建造机：两代实现，速度写在 buildSpeed 上

- `Constructor`（Constructor.java:21-22）默认 `minBlockSize = 1`、`maxBlockSize = 2`；`canProduce`（:54-56）要求方块 isVisible、块边长在 [minBlockSize, maxBlockSize] 内、非 CoreBlock、未被 rules.isBanned(b)、environmentBuildable()，且 filter 为空或命中。 [src: Constructor.java:21-22]
- v160.7 实参：constructor buildSpeed 0.6、minBlockSize 1、maxBlockSize 2；large-constructor buildSpeed 5、minBlockSize 3、maxBlockSize 4（[v159.3] 源码里 large-constructor 的 buildSpeed 是 0.75，v160.7 提到 5，差 6.7 倍）。
- `BlockProducer`（BlockProducer.java:22 `buildSpeed = 0.4f` 默认）：蓝图式工厂，用 `ConsumeItemDynamic` 按 recipe.requirements × rules.buildCostMultiplier 向上取整收料（:39-55），`getMaximumAccepted = 需求 × 2`（:88-93），每 tick `progress += buildSpeed * edelta()`，攒满 recipe.buildTime 产出一个 BuildPayload（:107-120）。 [src: BlockProducer.java:22]
- 被造方块自己的 `buildTime` 是造价函数：`Block.java:1432-1449` `buildTime = Σ(amount × item.cost) × buildCostMultiplier`；无需求时取 20f（Block.java:360 默认 -1f 表示尚未计算）。 [src: Block.java:1432-1449]
- 算例一：container 需求 titanium 100、item.cost 1（Items.java:51）⇒ buildTime = 100 tick；constructor 的 buildSpeed 0.6 ⇒ 100 / 0.6 = 166.7 tick ≈ 2.78 s。 [src: Items.java:51]
- 算例二：vault 需求 titanium 250 + thorium 125，thorium cost 1.1（Items.java:58）⇒ 250 × 1 + 125 × 1.1 = 387.5 tick；但 vault 是 3 格方块而小建造机 maxBlockSize 2，造不了，必须换 large-constructor。 [src: Items.java:58]
- 算例三：core-shard 的 buildCostMultiplier 是 2 ⇒ buildTime = (1000 × 0.5 + 800 × 0.7) × 2 = 2120 tick，这也是「核心只能由 5 格大建造机造」的原因（3 格 buildCostMultiplier 之外还卡 maxBlockSize）。

### 6. 载荷质量驱动器：装填 + 冷却都在周期里

- PayloadMassDriver.java:24-30 默认值 `range = 100f`、`rotateSpeed = 5f`、`length = 89/8f`、`reload = 30f`、`chargeTime = 100f`、`maxPayloadSize = 3`。 [src: PayloadMassDriver.java:24-30]
- 发射率根本不用另算，stats 里就写着：`stats.add(Stat.reload, 60f / (chargeTime + reload), StatUnit.perSecond)`（PayloadMassDriver.java:85），装填时间与冷却时间都进周期。 [src: PayloadMassDriver.java:85]
- v160.7 实参：payload-mass-driver 的 range 700 px（[src: gamedata.json#payload-mass-driver]）（87.5 格）、reload 45 tick、chargeTime 70 tick、maxPayloadSize 2.5 ⇒ 60 / (70 + 45) = 0.522 发/s；large-payload-mass-driver 的 range 2100 px（262.5 格）、reload 130、chargeTime 100、maxPayloadSize 4 ⇒ 60 / 230 = 0.261 发/s。
- 目标点存的是相对坐标 `Point2`（:70 注释 "point2 is relative"），放置时由 Drawf.dashCircle 画出 range 圈（:106），格子换算同样除 tilesize（:86 `stats.add(Stat.shootRange, range / tilesize, StatUnit.blocks)`）。

### 7. 装载与卸载：8 件 / 2 s、40 液体 / s

- PayloadLoader.java:22-27：`loadTime = 2f`、`itemsLoaded = 8`、`liquidsLoaded = 40f`、`maxBlockSize = 3`、`maxPowerConsumption = 40f`、`loadPowerDynamic = true`。 [src: PayloadLoader.java:22-27]
- 装载节奏：每 `loadTime / efficiency` tick 搬 `itemsLoaded` 件（PayloadUnloader.java:68-81 同一套参数），2 s = 120 tick 搬 8 件 ⇒ 4 件/s；液体按 `liquidsLoaded * edelta()` 即 40 / s，且要求同种液体或自身存量 < 0.2（:86-90）。 [src: PayloadUnloader.java:68-81]
- 装载器的 `outputsItems()` 返回 false（PayloadLoader.java:55-57，卸载器反过来返回 true，PayloadUnloader.java:23-25），所以它不会把 100 容量的物品栏当成输出口，那 100 只是被装载荷的中转缓存。 [src: PayloadLoader.java:55-57]
- 载荷进入后 `payloadSpeed = 0.7f` 控制其在方块内的滑动动画速度（PayloadBlock.java:18；v160.7 全部载荷方块 payloadRotateSpeed 都是 3，v159.3 源码默认 5）。 [src: PayloadBlock.java:18]

### 8. 解构机：进度按被拆方块 buildTime 归一

- PayloadDeconstructor.java:20 `dumpRate = 4`；v160.7 实参：small-deconstructor maxPayloadSize 3、deconstructSpeed 3、itemCapacity 100；deconstructor maxPayloadSize 4、deconstructSpeed 6、itemCapacity 320（[v159.3] 源码基类 PayloadDeconstructor.java:36 写死 itemCapacity = 100；320 是 v160.7 的版本值，见 gamedata raw）。
- 进度公式（PayloadDeconstructor.java:142-155）：`float shift = edelta() * deconstructSpeed / deconstructing.buildTime();` 所以总时长 = buildTime / deconstructSpeed tick，与被拆方块造价成正比，**不是固定秒数**。 [src: PayloadDeconstructor.java:142-155]
- 返还量（:158-160）：`accum[i] += reqs[i].amount * (BuildPayload ? rules.buildCostMultiplier : rules.unitCost(team)) * realShift`，即按全额造价按比例返还；攒够整数才进库存（:166-172），库存满 `itemCapacity` 就整机暂停（:130-138 canProgress 判 items.total() <= itemCapacity 且所有 accum < 1）。
- 拆之前先把方块里的液体泼到地面：`perCell = 存量 / (block.size * block.size) * 2` 逐格 Puddles.deposit（:148-152）。

## 数值

### 表 A｜14 个载荷方块实参（v160.7 反射，00-data/blocks.json 可核 id 与 health）

| 方块 | 块边长 | health | 关键参数 | 出处 |
|---|---|---|---|---|
| payload-conveyor | 3 | 360 | moveTime 45、payloadLimit 3、pushUnits true | PayloadConveyor.java:21 |
| reinforced-payload-conveyor | 3 | 800 | moveTime 35、payloadLimit 3 | gamedata raw |
| payload-router | 3 | 360 | moveTime 45、invert false、configurable | PayloadRouter.java:31-38 |
| reinforced-payload-router | 3 | 800 | moveTime 35 | gamedata raw |
| payload-mass-driver | 3 | 645 | range 700、reload 45、chargeTime 70、maxPayloadSize 2.5 | gamedata raw |
| large-payload-mass-driver | 5 | 2550 | range 2100、reload 130、chargeTime 100、maxPayloadSize 4 | gamedata raw |
| constructor | 3 | 860 | buildSpeed 0.6、minBlockSize 1、maxBlockSize 2 | Constructor.java:21-22 |
| large-constructor | 5 | 2500 | buildSpeed 5、minBlockSize 3、maxBlockSize 4 | gamedata raw |
| payload-loader | 3 | 645 | loadTime 2、itemsLoaded 8、liquidsLoaded 40、maxBlockSize 3 | PayloadLoader.java:22-27 |
| payload-unloader | 3 | 645 | loadTime 2、itemsLoaded 8、outputsItems true | PayloadUnloader.java:23-25 |
| small-deconstructor | 3 | 755 | maxPayloadSize 3、deconstructSpeed 3、itemCapacity 100 | gamedata raw |
| deconstructor | 5 | 3195 | maxPayloadSize 4、deconstructSpeed 6、itemCapacity 320 | gamedata raw |
| payload-source | 5 | 1000 | 沙盒源，无限供载荷 | 00-data/blocks.json#id=payload-source |
| payload-void | 5 | 1000 | payloadSpeed 1.2、沙盒消载荷 | 00-data/blocks.json#id=payload-void |

### 表 B｜速率换算总表（1 tick = 1/60 s，单位统一按秒） [src: Vars.java:135]

| 指标 | 公式（源码锚点） | 数值 |
|---|---|---|
| 载荷传送带吞吐 | 60 / moveTime（PayloadConveyor.java:137-188） | 默认 1.333 载荷/s；reinforced 1.714 载荷/s |
| 收料窗口占比 | 5 / moveTime（:279-283） | 默认 5 / 45 ≈ 11.1% |
| 质量驱动器发射率 | 60 / (chargeTime + reload)（PayloadMassDriver.java:85） | 小 0.522 发/s；大 0.261 发/s |
| 装载器搬物品 | itemsLoaded / loadTime（PayloadLoader.java:22-27） | 8 / 2 = 4 件/s |
| 装载器搬液体 | liquidsLoaded（同一行） | 40 液体/s |
| 建造时长 | 被造方块 buildTime / 建造机 buildSpeed（Constructor.java:54-56、BlockProducer.java:107-120） | container 100 / 0.6 = 166.7 tick |
| 解构时长 | 被拆方块 buildTime / deconstructSpeed（PayloadDeconstructor.java:142-155） | 与造价成正比，非定值 |
| 核心造价 | Σ(amount × item.cost) × buildCostMultiplier（Block.java:1432-1449） | core-shard 2120 tick |

### 表 C｜单位载荷容量（UnitType.java:119 默认 8，tilePayload 64、tilesize 8）

| 写法 | 出处 | payloadCapacity |
|---|---|---|
| 默认值 | UnitType.java:119 | 8 |
| (2 * 2) * tilePayload | UnitTypes.java:1424 | 256 |
| (3 * 3) * tilePayload | UnitTypes.java:1474 | 576 |
| (5.5 * 5.5) * tilePayload | UnitTypes.java:1547 | 1936 |
| sqr(4) * tilePayload | UnitTypes.java:4043 | 1024 |
| sqr(6) * tilePayload | UnitTypes.java:4148 | 2304 |
| payloadCapacity = 0 | UnitTypes.java:4575、:4605 | 0（不可被携带） |

## 源码锚点

1. `Payload.java:16-17` —— `payloadUnit = 0` 与 `payloadBlock = 1`，载荷类型在存档流里的首字节。 [src: Payload.java:16-17]
2. `Payload.java:50-52` —— `fits(float s)` 是唯一尺寸闸门，返回值 `size() / tilesize <= s`。 [src: Payload.java:50-52]
3. `BuildPayload.java:86-88` —— 方块载荷尺寸 = `build.block.size * tilesize`；对照 `UnitPayload.java:98-101` 单位载荷尺寸 = `unit.hitSize`。 [src: BuildPayload.java:86-88]
4. `Block.java:60-65` —— `outputsPayload` / `acceptsUnitPayloads` / `acceptsPayload` 三个开关决定一个方块是不是载荷链节点。 [src: Block.java:60-65]
5. `Block.java:1432-1449` —— `buildTime = Σ(amount × item.cost) × buildCostMultiplier`，无需求则 20f。 [src: Block.java:1432-1449]
6. `Block.java:360` —— `buildTime = -1f` 默认值表示「未计算」，所以不要在数据表里把 -1 当成真实工期。 [src: Block.java:360]
7. `PayloadConveyor.java:21` —— `moveTime = 45f`、`moveForce = 201f`、`payloadLimit = 3f`。 [src: PayloadConveyor.java:21]
8. `PayloadConveyor.java:137-188` —— `curStep = (int)(time() / moveTime)` 的节拍推进，以及掉地上 `item.dump()`。 [src: PayloadConveyor.java:137-188]
9. `PayloadConveyor.java:279-283` —— `acceptPayload` 的 `progress <= 5f` 收料窗口。 [src: PayloadConveyor.java:279-283]
10. `PayloadConveyor.java:128` —— `blocked` 的三项或：solid 邻居、outputsPayload、acceptsPayload、payloadCheck。 [src: PayloadConveyor.java:128]
11. `PayloadRouter.java:54-56` —— `canSort(Block)` 的五个条件；`:76-103` 四方向轮转 pickNext。 [src: PayloadRouter.java:54-56]
12. `PayloadMassDriver.java:85-86` —— 发射率 `60f / (chargeTime + reload)` 与射程 `range / tilesize`。 [src: PayloadMassDriver.java:85-86]
13. `Constructor.java:21-22` 与 `:54-56` —— minBlockSize / maxBlockSize 与 canProduce 五条件。 [src: Constructor.java:21-22]
14. `BlockProducer.java:22` —— `buildSpeed = 0.4f`；`:107-120` 产出 BuildPayload。 [src: BlockProducer.java:22]
15. `PayloadLoader.java:22-27` —— loadTime 2 / itemsLoaded 8 / liquidsLoaded 40 / maxBlockSize 3。 [src: PayloadLoader.java:22-27]
16. `PayloadDeconstructor.java:142-160` —— `shift = edelta() * deconstructSpeed / buildTime` 与 `accum` 按 buildCostMultiplier 返还。 [src: PayloadDeconstructor.java:142-160]
17. `UnitType.java:119` —— `payloadCapacity = 8` 默认值；`Vars.java:137` tilePayload = 64。 [src: UnitType.java:119]

## 实测与反例

**反例 1｜载荷传送带不是物品传送带。** 00-data/blocks.json#id=payload-conveyor 里 `hasItems=false`、`itemCapacity=10`，那 10 是 Block.java:75 的字段默认值，不是可用物品栏；它只认 payload，塞物品没有任何入口。 [src: Block.java:75]

**反例 2｜容量不是「格数平方」。** payloadLimit 3 表示最大边长 3 格 = 24 px，不是能叠 3 × 3 = 9 个载荷；一个 3 格方块就占满整条带子（Payload.java:50-52 用除法而非面积）。实测一条默认载荷传送带在满负荷下吞吐恒为 1.333 载荷/s，与载荷本身是 1 格还是 3 格无关。 [src: Payload.java:50-52]

**反例 3｜串联不是无损接力。** 收料窗口只有周期前 5 tick（PayloadConveyor.java:279-283），上游如果在 `progress > 5` 时把载荷推来会被拒，必须等自己下一个 45 tick 周期；实测两段串联时有效吞吐明显低于单段 1.333 载荷/s，属于「设计上允许堵塞」。 [src: PayloadConveyor.java:279-283]

**反例 4｜版本差异会被算成 6.7 倍误差。** large-constructor 的 buildSpeed 在 [v159.3] 源码里是 0.75，v160.7 是 5（gamedata raw 读回 5.0）；用旧版数值估建造时间会把 5 格建筑高估 6.7 倍。

**反例 5｜deconstructor 的 320 不是基类默认。** [v159.3] 源码 PayloadDeconstructor 构造里写 `itemCapacity = 100`（PayloadDeconstructor.java:36），v160.7 的 deconstructor 是 320（gamedata raw）；按 100 推算「拆 5 格大建筑会先卡 3 次」是错的。

**反例 6｜质量驱动器射程单位是像素。** PayloadMassDriver.java:86 `range / tilesize` 再显示成格，700 px = 87.5 格；直接读成 700 格会放大 8 倍。 [src: PayloadMassDriver.java:86]

**正面实测｜装载器对空载荷的速率。** payload-loader 用默认 100% efficiency 时，120 tick（2 s）搬 8 件 ⇒ 4 件/s，液体 40 / s；这比同尺寸物品传送带（conveyor 4.5 件/s，WORLD.LOGISTICS.001）略低，但一次能灌满一个 3 格方块的库存。

## 常见误解

1. **「载荷传送带耗电」**——不耗电：payload-conveyor 的 `hasPower=false`（00-data/blocks.json#id=payload-conveyor），耗电的是装卸器、建造机、解构机与质量驱动器。
2. **「载荷路由可以当分流器手动调方向」**——路由的 config 选的是**内容**（某个方块或单位类型，PayloadRouter.java:36-38），方向是 pickNext 在 4 个方向里自动轮转的结果，不是玩家设的。 [src: PayloadRouter.java:36-38]
3. **「建造机能造任意方块」**——受 canProduce 五条件限制（Constructor.java:54-56），核心方块因 `!(b instanceof CoreBlock)` 永远造不了；3 格小建造机也造不了 vault 这类 3 格以上建筑（maxBlockSize 2）。 [src: Constructor.java:54-56]
4. **「解构时间是固定几秒」**——进度是 `edelta() * deconstructSpeed / buildTime`（PayloadDeconstructor.java:142-155），container 与 vault 的 buildTime 差 3.875 倍，解构耗时同比例变化。 [src: PayloadDeconstructor.java:142-155]
5. **「单位载荷看等级」**——只看 `hitSize / tilesize <= payloadLimit`（PayloadConveyor.java:87）以及 `unit.type.allowedInPayloads && !unit.spawnedByCore`（PayloadDeconstructor.java:92-95），与单位 Tier 无关。 [src: PayloadConveyor.java:87]
6. **「载荷传送带能被子弹打坏」**——payload-conveyor 是 `solid=false`、`underBullets=true`（00-data/blocks.json），子弹直接穿过；只有 payload-mass-driver 这类 `solid=true` 的载荷方块才挡子弹。

## 相关

- WORLD.BLOCKS.001 —— 多格方块锚点、size 与放置合法性，载荷尺寸的格数基础。
- WORLD.LOGISTICS.001 —— 物品传送带吞吐与堵塞，可与载荷传送带横向对比。
- WORLD.STORAGE.001 —— 卸载器与核心容量，载荷解构后的物品去向。
- WORLD.CRAFTING.001 —— 配方 craftTime 与单位口径，buildTime 造价公式的邻居。
- 00-data/blocks.json —— 14 个载荷方块的全部静态字段（health / size / requirements / consumes）。
