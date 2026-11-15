---
id: WORLD.LIQUIDS.001
title: 液体系统
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:920-984"
  - "Mindustry-Source/core/src/mindustry/world/blocks/liquid/Conduit.java:30, 240-257"
  - "Mindustry-Source/core/src/mindustry/world/blocks/liquid/LiquidRouter.java:23-43"
  - "Mindustry-Source/core/src/mindustry/world/blocks/liquid/LiquidJunction.java:43-53"
  - "Mindustry-Source/core/src/mindustry/world/blocks/liquid/LiquidBlock.java:20-28"
  - "Mindustry-Source/core/src/mindustry/world/blocks/production/Pump.java:19-20, 160-170"
  - "Mindustry-Source/core/src/mindustry/type/Liquid.java:27-70"
  - "Mindustry-Source/core/src/mindustry/entities/Puddles.java:16, 37-98"
  - "Mindustry-Source/core/src/mindustry/entities/comp/PuddleComp.java:47-66"
data: [00-data/liquids.json, 00-data/blocks.json]
depends: [WORLD.BLOCKS.001, WORLD.CRAFTING.001]
tags: [液体, 管道, 泵, viscosity, heatCapacity, 水坑, 堵塞]
tokens: 1929
---

## 一句话

液体是"每方块一个 `LiquidModule` 库存 + 每 tick 一次压差搬运"的资源：**没有流速字段，能搬多少完全由"本块库存占比"与"下游库存占比"的差 × 本块 `liquidCapacity`"决定**；一套管道里任何一段装满了、或者灌进了第二种液体，流动就停在那里。

## 规则 / 公式

### 1. 液体存在哪里

每个 `hasLiquids = true` 的方块有一个 `LiquidModule`（v160.7 共 107 个），内部是**按 11 种液体各存一份的 float 数组** [src: LiquidModule.java:23-24]。但游戏里几乎所有行为的依据都是 `current()`（最近一次收到/设置的那种液体）与 `currentAmount()`：

```
currentAmount() = liquids[current.id]      // 只算"当前那种"，不是总量
```

所以**一个方块实际上只有一种液体在起作用**——数组是给反应堆这类特殊逻辑留的余量，不是给玩家混装的。

### 2. 搬运公式（唯一的核心）

所有被动流动都走 `BuildingComp.moveLiquid(next, liquid)` [src: BuildingComp.java:944-984]：

```
ofract = next.liquids.get(liquid) / next.liquidCapacity     // 下游充满度
fract  = 本块.liquids.get(liquid) / 本块.liquidCapacity * 本块.liquidPressure
flow   = clamp(fract - ofract) * 本块.liquidCapacity         // 按压差比例搬
flow   = min(flow, 本块存量, 下游剩余容量)
if (flow > 0 && ofract <= fract && next.acceptLiquid(...)) 才真的搬
```

三个直接推论：

1. **下游不比本块空，就一滴都不动**（`ofract <= fract` 是硬条件）。
2. 流量与"本块容量"成正比：容量越大的方块，单 tick 能推的量越大。
3. `liquidPressure` 原版全部为默认 `1f`（`Block.java:79`，v159.3 里没有任何原版方块改过它）。

### 3. 管道 / 路由器 / 交叉器 / 桥

| 方块 | 类 | 液体容量 | 特殊行为 |
|---|---|---|---|
| conduit | Conduit | 20 | 只朝 `rotation` 方向推；**漏液** |
| pulse-conduit | Conduit | 40 | 同上，容量翻倍 |
| plated-conduit | ArmoredConduit | 50 | `leaks = false`，不漏 |
| reinforced-conduit | ArmoredConduit | 50 | 不漏 |
| liquid-junction | LiquidJunction | 10 | **直穿**到对面，不分流 |
| liquid-router | LiquidRouter | 120 | 向四周 `dumpLiquid` |
| liquid-container | LiquidRouter | 700 | 大容器，兼做路由 |
| liquid-tank | LiquidRouter | 1800 | 同上 |
| bridge-conduit | LiquidBridge | 100 | 跨 4 格 |
| phase-conduit | LiquidBridge | 100 | 跨 12 格 |
| reinforced-bridge-conduit | DirectionLiquidBridge | 120 | 跨 4 格，方向性 |

`Conduit` 每 tick（`timer(timerFlow, 1)` [src: Conduit.java:251]）朝正面调用一次 `moveLiquidForward`，因此它的**单 tick 搬运上限就是自身容量**：conduit 20/tick（≈1200/s）、pulse-conduit 40/tick（2400/s）。这解释了一个常见困惑——"管道容量"与"管道吞吐"在数值上是同一个数。

`LiquidJunction` 用 `getLiquidDestination` 把"从我这里要液体的建筑"重定向到对面那格 [src: LiquidJunction.java:43-53]，`"直行"` 行为不是分流，所以交叉处不会混液。

`Conduit` 里 `acceptLiquid` 还有一条几何约束：**不能从自己的背面来液**（`(source.relativeTo(...) + 2) % 4 != rotation` [src: Conduit.java:241-245]），所以管道不会倒流。

### 4. 泵

`PumpBuild` 每 tick 扫描自己覆盖的 `size × size` 格地板，累加 `floor.liquidMultiplier` [src: Pump.java:160-170]：

```
amount  = Σ(所覆盖地板.liquidMultiplier)            // 液体地板个数 × 倍率
maxPump = min(liquidCapacity - 当前库存, amount * pumpAmount * edelta)
```

所以**泵的产出 = 单格泵速 × 液体格数 × 地板倍率**。机械泵 1×1 站在普通水上：`1 × 0.1167 = 0.1167/tick = 7/s`；旋转泵 2×2 = 4 格：`4 × 0.2 = 0.8/tick = 48/s`；冲击泵 3×3 = 9 格：`9 × 0.22 = 1.98/tick = 118.8/s`。

`water-extractor` 是 `SolidPump`（不依赖地板水），`pumpAmount = 0.11/tick = 6.6/s`。

地板倍率（v160.7 反射 `raw.liquidMultiplier`）：deep-water **1.5**、shallow-water / tainted-water **1**、pooled-cryofluid **0.5**、arkycite-floor **1**、tar（oil）/ molten-slag（slag）**1**。深水比浅水多 50% 产出——这是"泵摆深水"的全部收益来源。

### 5. 混合、堵塞与反应

**混合被两道闸拦住**：

1. `acceptLiquid(source, liquid)`：管道与路由器的实现都是 `liquids.current() == liquid || liquids.currentAmount() < 0.2f` [src: LiquidRouter.java:41-43]——只接"同种"或"几乎空"的块。
2. 消费端（`ConsumeLiquid` / `ConsumeLiquidFilter`）只接受自己过滤表里的液体，其余一律返回 false。

于是**两种液体永远不会在同一段管道里混合**：先到的占住管道，后到的被挡在源头。想并线必须先清空（把管道抽干到 < 0.2 才允许换液）。

如果两种**有反应性**的液体在相邻方块里相遇（都 `blockReactive = true`），会发生反应 [src: BuildingComp.java:959-981]：

- 一方 `flammability > 0.3` 且另一方 `temperature > 0.7` → 双方 `damageContinuous(1)`，10%/tick 概率起火；
- 一方 `temperature > 0.7` 且另一方 `temperature < 0.55` → 热液按 `0.7 × delta/tick` 被消耗，20%/tick 概率冒蒸汽。

这就是"水泼进熔渣管道会炸管"的机制——它是**方块受伤**，不是液体被销毁。

### 6. 十一种液体及其五个属性

`Liquid` 的字段语义 [src: Liquid.java:27-70]：

| 字段 | 含义 | 谁在用 |
|---|---|---|
| `viscosity` | 0.5=水，1=焦油；**只影响水坑的蒸发/扩散速度** | `PuddleComp.java:60` |
| `heatCapacity` | 0.4=水；冷却液倍率的核心 | 炮塔冷却、反应堆、护盾 |
| `temperature` | 0.5=室温，>0.7 算"热" | 液体反应判定 |
| `flammability` | >0.3 才可能被点燃 | 火、爆炸、反应 |
| `explosiveness` | 被加热时的爆炸倾向 | 方块被毁时的爆炸强度 |
| `coolant` | false 表示**不能当冷却液**（原版只有 gallium = false） | 冷却液过滤 |
| `gas` | 气体，不产生水坑，`boilPoint` 自动设 -1 | 视觉与管道动画 |
| `boilPoint` | 汽化温度阈值（默认 2 = 永不） | 反应堆过热汽化 |

**粘度不影响管道流速**——这是最常见的误解，见下文反例。

### 7. 水坑（puddle）

液体漏到地上（管道 `leaks = true` 且前方不是固体），会在目标格生成 Puddle [src: BuildingComp.java:936-940]：

```
leakAmount = 本块存量 / 1.5          // 每次漏掉 2/3
Puddles.deposit(...)
```

水坑上限 `Puddles.maxLiquid = 70` [src: Puddles.java:16]。每 tick 衰减 [src: PuddleComp.java:60-63]：

```
amount -= delta * (1 - liquid.viscosity) / (5 + addSpeed)
amount  = min(amount, maxLiquid)
```

水的 `viscosity = 0.5` → 每 tick 衰减 `0.5 / 5 = 0.1`，约 700 tick（≈11.7 秒）蒸发完 70 单位；油的 `viscosity = 0.75` → 每 tick 0.05，慢一倍。**粘度高 = 水坑留得久 = 更容易被点燃**，与"流得慢"无关。

水坑超过 `maxLiquid / 1.5 ≈ 46.7` 时会向四邻扩散，每次最多 `0.3 × delta`（0.3/tick）。

## 数值

**液体属性表（11 种全量）**

数值来源是源码 `Mindustry-Source/core/src/mindustry/content/Liquids.java:13-95` 里逐条 `new Liquid("..."){{ }}` 的字段赋值，不是凭记忆；没写到的字段取 `type/Liquid.java` 的默认值——温度 0.5（Liquid.java:40）、热容 0.5（Liquid.java:42）、粘度 0.5（Liquid.java:44）、可燃 0（Liquid.java:38）、爆 0（Liquid.java:46）、`coolant = true`（Liquid.java:50）、`blockReactive = true`（Liquid.java:48）。`00-data/liquids.json` 有同样的值，但它只是数据表，正文必须自己写数字，否则检索命中表却答不出题。

| 液体 | 源码 `Liquids.java` 行 | 温度 | 热容 | 粘度 | 可燃 | 爆 | 冷却液 | 气体 | hidden | boilPoint |
|---|---|---|---|---|---|---|---|---|---|---|
| water | 13-19 | 0.5 | **0.4** | 0.5 | 0 | 0 | ✔（Liquid.java:50 默认） | – | – | 0.5（`:16`） |
| slag | 21-26 | **1.0**（`:22`） | 0.5 | **0.7**（`:23`） | 0 | 0 | ✔ | – | – | 2 |
| oil | 28-38 | 0.5 | **0.7**（`:32`） | **0.75**（`:29`） | **1.2**（`:30`） | **1.2**（`:31`） | ✔ | – | – | 0.65（`:35`） |
| cryofluid | 40-47 | **0.25**（`:42`） | **0.9**（`:41`） | 0.5 | 0 | 0 | ✔ | – | – | 0.55（`:45`） |
| neoplasm | 49-63 | **0.54**（`:51`） | **0.4**（`:50`） | **0.85**（`:52`，全液体最高） | **0**（`:53`） | 0 | ✔ | – | – | 2 |
| arkycite | 65-69 | 0.5 | 0.5 | **0.7**（`:67`） | **0.4**（`:66`） | 0 | ✔ | – | – | 2 |
| gallium | 71-74 | 0.5 | 0.5 | 0.5 | 0 | 0 | **✘（`coolant=false`，`:72`）** | – | **✔（`hidden=true`，`:73`）** | 2 |
| ozone | 76-81 | 0.5 | 0.5 | 0.5 | **1**（`:80`） | **1**（`:79`） | ✔ | ✔（`:77`） | – | -1 |
| hydrogen | 83-86 | 0.5 | 0.5 | 0.5 | **1**（`:85`） | 0 | ✔ | ✔（`:84`） | – | -1 |
| nitrogen | 88-90 | 0.5 | 0.5 | 0.5 | 0 | 0 | ✔ | ✔（`:89`） | – | -1 |
| cyanogen | 92-95 | 0.5 | 0.5 | 0.5 | **2**（`:94`，全液体最高） | 0 | ✔ | ✔（`:93`） | – | -1 |

三个容易记错的点：① `water` 的热容是 **0.4 而不是 0.5**（Liquids.java:14 显式覆盖了默认值），所以"水是基准冷却液"不代表它是中位热容；② `gallium` 的 `coolant = false`（Liquids.java:72）且 `hidden = true`（Liquids.java:73），它在游戏里不显示、也永远当不了冷却液；③ `neoplasm` 是唯一同时 `moveThroughBlocks = true`（`:56`）、`capPuddles = false`（`:54`）、`blockReactive = false`（`:58`）、`incinerable = false`（`:57`）的液体，所以它既能穿过方块又会无限铺开、还不会和别的液体反应。

**泵产出（per tick → per second，站在普通浅水上）**

| 方块 | pumpAmount | 覆盖格 | /tick | /秒 |
|---|---|---|---|---|
| mechanical-pump | 0.1167 | 1 | 0.1167 | 7 |
| rotary-pump | 0.2 | 4 | 0.8 | 48 |
| impulse-pump | 0.22 | 9 | 1.98 | 118.8 |
| reinforced-pump | 0.3333 | 4 | 1.333 | 80 |
| water-extractor | 0.11（固化） | 4 | 0.44 | 26.4 |

**液体容器容量**

| 方块 | liquidCapacity |
|---|---|
| liquid-junction | 10 |
| conduit | 20 |
| pulse-conduit | 40 |
| plated-conduit / reinforced-conduit | 50 |
| bridge-conduit / phase-conduit | 100 |
| liquid-router | 120 |
| reinforced-bridge-conduit | 120 |
| liquid-container | 700 |
| reinforced-liquid-container | 1000 |
| liquid-tank | 1800 |
| reinforced-liquid-tank | 2700 |
| landing-pad | 3000 |
| liquid-source / liquid-void（沙盒） | 10000 |

## 源码锚点

- `BuildingComp.java:944-984` `moveLiquid`：压差公式与"ofract <= fract"硬条件，含液体反应分支。
- `BuildingComp.java:929-942` `moveLiquidForward`：朝 rotation 推；前方非固体非液体时按 `存量/1.5` 漏进 Puddle。
- `BuildingComp.java:920-927` `transferLiquid`：先按下游剩余容量 clamp，再 `acceptLiquid` 校验。
- `Conduit.java:251` `timer(timerFlow, 1)`：每 tick 推一次；`Conduit.java:30` `timerFlow = timers++`。
- `Conduit.java:241-245` `acceptLiquid`：同种或 <0.2，且**不能从背面进液**。
- `LiquidRouter.java:25-27` `dumpLiquid(liquids.current())`：路由器只是"往四周倒"。
- `LiquidJunction.java:43-53` `getLiquidDestination`：直穿重定向。
- `LiquidBlock.java:20-28` 液体方块基类：`hasLiquids = true`、`outputsLiquid = true`、`solid = true`。
- `Pump.java:19-20` `pumpAmount`（per tile）；`Pump.java:162` `maxPump = min(容量-库存, amount*pumpAmount*edelta)`。
- `content/Liquids.java:13-95` 11 种液体的**全部逐项赋值**（`water` 13-19、`slag` 21-26、`oil` 28-38、`cryofluid` 40-47、`neoplasm` 49-63、`arkycite` 65-69、`gallium` 71-74、`ozone` 76-81、`hydrogen` 83-86、`nitrogen` 88-90、`cyanogen` 92-95）——`Liquids.java` 是液体数值的第一真源，`.json` 只是它的转储。
- `type/Liquid.java:38-50` 字段默认值：`flammability = 0`、`temperature = 0.5`、`heatCapacity = 0.5`、`viscosity = 0.5`、`explosiveness = 0`、`blockReactive = true`、`coolant = true`；`Liquid.java:27-70` 还有 `gas/moveThroughBlocks/incinerable/boilPoint`。
- `Puddles.java:16` `maxLiquid = 70`；`Puddles.java:37-98` `deposit()` 与扩散。
- `PuddleComp.java:47-66` 水坑燃烧系数与粘度衰减。

## 实测与反例

**反例 1（粘度不控制流速）**：直觉上"oil 粘度 0.75 应该比水 0.5 流得慢"，但 `moveLiquid` 的公式里根本没有 `viscosity` 项——同容量管道里水与油的搬运速度**完全相同**，都是 20/tick（conduit）。粘度只在三处出现：水坑衰减（`PuddleComp.java:60`）、某些状态效果与 UI 数据。想让油流得慢在机制上做不到。

**反例 2（管道"容量"就是吞吐上限，不是 20/s）**：`liquidCapacity = 20` 常被读成"每秒 20"。实际是**每 tick 最多搬 20**，也就是 1200/s；而且这个上限几乎不可能达到——机械泵只产 0.117/tick。真正常见的瓶颈是"泵太少"或"某段管道被第二种液体卡住"，不是管道速度。

**反例 3（不同液体不会混，只会互相堵）**：一节管道里已有 5 单位水时，油会被 `acceptLiquid` 拒绝（`currentAmount() < 0.2f` 不成立）。玩家的"混液"现象通常来自**分支点**：一个 liquid-router 两侧分别接了水池与油池，它会先后 `dumpLiquid(current())`，导致下游不同分支装不同液体，而不是同一节管道里混合。

**反例 4（junction 不是分流器）**：`liquid-junction` 的作用是让"来自 A 侧"的液体直达"对面 B 侧"，中间那格自身只有 10 容量且 `update = false`（不主动推）。把它当"液体路由器"用会导致一侧永远不供液。

**反例 5（水泼熔渣是"炸方块"，不是"销毁液体"）**：`BuildingComp.java:966-973` 反应分支只在双方都 `blockReactive` 时触发，效果是 `damageContinuous(1)` 打到**方块**身上。液体本身仍在各自库存里，靠热量汽化（`boilPoint`）才会消失。

## 常见误解

1. **"vn 值 / 需要加压"** → 原版 `liquidPressure` 全为 1，没有任何"增压泵"或"压力衰减"概念；距离只影响"中间要摆几节管道"，不影响流量。
2. **"管道会自动把液体均分给两个出口"** → `dumpLiquid` 是**顺序**倾倒（按 proximity 顺序轮转），不是平均分配；想要均分需要 liquid-router 的双向存量大到足以抹平差异，或用逻辑精确控制。
3. **"液体储量 = 所有液体之和"** → `currentAmount()` 只返回 `liquids[current.id]`。把两种液体灌进同一方块后，UI 液体条只显示 `current` 那种。
4. **"深水只是视觉"** → 深水 `liquidMultiplier = 1.5`、`speedMultiplier = 0.2`、`drownTime = 200`，三项都是实际数值：泵产出 +50%，单位移动减速到 20%，非水生单位 200 tick 淹死。
5. **"气体也能抽成水坑"** → `gas = true` 的液体不生成水坑，`boilPoint` 被强制为 -1（永远汽化），所以 ozone/hydrogen/nitrogen/cyanogen 只存在于管道与方块里。
6. **"漏液只是视觉效果"** → `leaks = true` 的 conduit / pulse-conduit / reinforced-conduit 每 tick 把 `存量/1.5`（约 66.7%）倒进前方空地板；只有 plated-conduit 与 armored 系列不漏。

## 相关

- `WORLD.BLOCKS.001`（`hasLiquids` / `liquidCapacity` 在方块定义中的位置）
- `WORLD.CRAFTING.001`（`ConsumeLiquid`：液体按 **per tick** 扣费，效率按库存比例可半饱）
- `WORLD.HEAT.001`（`heatCapacity` 作为冷却液倍率的完整用法）
- `WORLD.POWER.001`（液体发电机：steam-generator / differential-generator / impact-reactor）
- `WORLD.TERRAIN.001`（深水/浅水/焦油地形与 `liquidDrop` / `drownTime`）
- `WORLD.LOGISTICS.001`（固体物流与液体管道的堵塞模型对比）
- 数据表：`00-data/liquids.json`（`viscosity/heatCapacity/temperature/flammability/explosiveness/coolant`）、`00-data/blocks.json`（`liquidCapacity`、`hasLiquids`）
- 源码：`world/blocks/liquid/*.java`、`world/blocks/production/Pump.java`、`entities/Puddles.java`、`world/modules/LiquidModule.java`
