---
id: WORLD.STORAGE.001
title: 存储：核心容量口径、容器/保险库与卸载器的搬运优先级
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src: [src: Blocks.java:3127-3260, src: CoreBlock.java:150-158, src: CoreBlock.java:695-735, src: StorageBlock.java:17-140, src: Unloader.java:99-232]
data: [00-data/blocks.json#id=core-shard, 00-data/blocks.json#id=core-nucleus, 00-data/blocks.json#id=container, 00-data/blocks.json#id=vault, 00-data/blocks.json#id=reinforced-container, 00-data/blocks.json#id=unloader, 00-data/blocks.json#id=duct-unloader, 00-data/blocks.json#id=liquid-tank]
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001, WORLD.POWER.001]
tags: [storage, core, container, vault, unloader, itemCapacity, storageCapacity, coreMerge]
tokens: 1711
---

# W10 存储：核心容量、容器与卸载器

## 一句话

核心（CoreBlock）与容器（StorageBlock）用的是两套不同的容量口径：核心把"每种物品各自最多 storageCapacity 件"当作上限，紧贴核心的 coreMerge 容器（container/vault）会把自己的库存数组直接交给核心共享、只把 itemCapacity 数字加进核心总容量；容器单独放置时才是"每种物品各自 itemCapacity、彼此不通"。卸载器（Unloader）是原版唯一会主动在方块之间搬库存的方块，每 speed 个 tick 搬 1 件，用五级比较器同时挑源和目的，目的是配平装载率而不是清空。

## 规则 / 公式

### 1. 三个字段决定了"能存多少"

| 字段 | 声明位置 | 默认值 | 作用 |
|---|---|---|---|
| itemCapacity | Block.java:75 | 10 | 单个方块的容量基数，多格方块不乘 size² |
| separateItemCapacity | Block.java:73 | false | 为 true 时每种物品各占一份容量，否则共享 |
| unloadable | Block.java:106 | true | 能否被卸载器/逻辑当"可取出"的容器 |

StorageBlock 在构造里把另外三个开关定死：separateItemCapacity=true（StorageBlock.java:26）、allowResupply=true（:29）、group=BlockGroup.transportation、flags=storage、envEnabled=Env.any（:19-38），并且 outputsItems()=false（:36-38）——容器不主动输出，只能被拿走。

### 2. 核心容量是算出来的，不是 itemCapacity

CoreBlock.CoreBuild.onProximityUpdate（CoreBlock.java:704-735）每次邻接变化都重算：

1. 同队其它核心先合并库存数组：`this.items = other.items`（:708-712）。
2. 核心自己的 itemCapacity 加上邻接 coreMerge 容器的 itemCapacity：`storageCapacity = itemCapacity + proximity.sum(e -> owns(e) ? e.block.itemCapacity : 0)`（:715）。
3. 这些容器不另存库存，直接把 items 指向核心并登记 linkedCore：`t.items = items; ((StorageBuild)t).linkedCore = this;`（:716-719）。
4. 同队所有核心的容量一起累加（:721-724），所以多核共用同一个池和同一个上限。
5. 每种物品按上限截断：`items.set(item, Math.min(items.get(item), storageCapacity))`（:728）。

关键推论写在 :696-702：`acceptItem` 判断的是 `items.get(item) < getMaximumAccepted(item)`，而 `getMaximumAccepted` 返回 `storageCapacity`——也就是说 4000 是**每种物品**各自的 4000，不是 4000 总量。UI 之所以看起来像总量条，是因为 :150 的分母是 `storageCapacity * content.items().count(unlockedNow)`。

### 3. 容器：独立时按种计容，贴近核心就变成"核心的分隔间"

容器单独放（不邻接核心）时，separateItemCapacity=true 生效：一个 container 的 300 是**每种物品各 300**，vault 的 1000 每种各 1000。一旦被核心 proximity 覆盖（owns 判定见 CoreBlock.java:789-791：必须是 StorageBlock 且 coreMerge 为真且 linkedCore 为空或就是该核心），它的 items 指针被换成核心的数组（:717），容量数字并入核心 storageCapacity（:715）：此时容器不再有自己的库存，只是核心库存的一块可视窗口。

反方向的两个方法是"链接后失能"的证据：`canPickup()` 只有 `linkedCore == null` 才为真（StorageBlock.java:132-134），`allowDeposit()` 在链接后恒为真（:137-139）；getMaximumAccepted 直接转发核心数值（:96），sensor 读 itemCapacity 也返回核心的（:114）。销毁时只有未链接的容器才把旧库存还回去并 clamp（:118-130）。

Erekir 的两个加固容器把 coreMerge 关掉了：`coreMerge = false`（Blocks.java:3244、3252），所以 reinforced-container/reinforced-vault 永远独立计容，哪怕贴着核心。

### 4. 卸载器：一件一周期，五级比较器

周期：`if(((unloadTimer += delta()) < speed) || (possibleBlocks.size < 2)) return;`（Unloader.java:163）——每 speed 个 tick 一个周期，每个周期最多搬 **1 件**。显示速率因此是 60/speed 件/秒（:63 `stats.add(Stat.speed, 60f / speed, StatUnit.itemsSecond)`）。

邻接扫描只收"能参与交易"的方块（:143-158）：
- `canLoad = !(other instanceof CoreBuild || other instanceof StorageBuild)`（:148）——核心与容器"不能主动接收"，只能当来源；
- `canUnload = other.canUnload() && (allowCoreUnload || canLoad || (StorageBuild b && b.linkedCore == null)) && other.items != null`（:149）。

搬运顺序由比较器决定（:99-111），从高到低排序后取**第一个能收的当目的、最后一个能给的当源**（:202-215）：
1. 核心类优先（`!notStorage`）；
2. "能出不能进"的当源优先；
3. "能进不能出"的当目的优先；
4. loadFactor 升序（:108，装载率低者优先当目的）；
5. lastUsed 降序（:110，越久没被用过越优先）。

真正搬运还多一个条件：`dumpingFrom.loadFactor != dumpingTo.loadFactor || !dumpingFrom.canLoad`（:218）——两边装载率一样就不搬，所以卸载器是"配平器"不是"清空器"。成功则 `unloadTimer %= speed`（:228），失败只 clamp 不累积（:230）。

物品选择：设了 sortItem 就只搬该物品（:167-168），否则按 `rotations` 轮转全物品表（:172-180），每个周期换一样，避免单物品堵死。

### 5. 液体存储与"数字是继承默认值"

液体罐是另一条线：liquid-container 700、liquid-tank 1800、reinforced-liquid-container 1000、reinforced-liquid-tank 2700（00-data/blocks.json#id=liquid-tank 等），它们的 hasItems=false、hasLiquids=true，itemCapacity 显示为 10 只是 Block.java:75 的默认值。

同理，核心与普通容器的 liquidCapacity=10（00-data/blocks.json#id=core-shard、#id=container）也是继承值：这两类的 hasLiquids=false，10 永远不会生效。看 00-data 时必须先看 hasLiquids/hasItems 两个布尔，再看容量数字——单看数字会被默认值骗。

### 6. 核心的建造与阵营规则

- core-shard 是唯一 alwaysUnlocked 的核心，且 BuildVisibility.coreZoneOnly（Blocks.java:3128-3129），只能放在核心区里；buildCostMultiplier=2（:3136）表示蓝图复制时成本翻倍。
- Erekir 三核 requiresCoreZone=true、incinerateNonBuildable=true（不能建造的物品投进去直接烧掉）、buildCostMultiplier=0.7 [src: Blocks.java:3167-3223]。
- 核心能否被卸载器取走由 CoreBuild.canUnload 决定：`block.unloadable && state.rules.allowCoreUnloaders`（CoreBlock.java:282-284）——rules 里关掉这个开关，所有卸载器都取不动核心。
- 核心爆炸/摧毁走 onDestroyed（:629-657），coreCapture=true 时只做动态爆炸、不给火，避免刚毁就被立刻反抢。

## 数值

### 表 1 核心（v160.7 jar，00-data/blocks.json 可逐条核对）

| 方块 | size | health | itemCapacity（每种物品） | unitCapModifier | 出生单位 | armor |
|---|---|---|---|---|---|---|
| core-shard | 3 | 1100 | 4000 | 8 | alpha | 0 |
| core-foundation | 4 | 3500 | 9000 | 16 | beta | 0 |
| core-nucleus | 5 | 6000 | 13000 | 24 | gamma | 0 |
| core-bastion | 4 | 4500 | 2000 | 15 | evoke | 5 |
| core-citadel | 5 | 16000 | 3000 | 15 | incite | 10 |
| core-acropolis | 6 | 30000 | 4000 | 15 | emanate | 15 |

unitCapModifier 由 Blocks.java:3138/3150/3163/3185/3202/3220 逐条赋值；armor 见 :3177/3197/3215。health 由 scaledHealth 按格数平方生成（Blocks.java:3229）：container 声明 scaledHealth 55 ⇒ 220；vault 55 ⇒ 495；reinforced-container 声明 120 ⇒ 480（:3243）、reinforced-vault 120 ⇒ 1080（:3251）。

### 表 2 存储方块

| 方块 | size | health | itemCapacity | separate | coreMerge | 备注 |
|---|---|---|---|---|---|---|
| container | 2 | 220 | 300 | true | true | titanium 100（Blocks.java:3226） |
| vault | 3 | 495 | 1000 | true | true | titanium 250 + thorium 125（:3233） |
| reinforced-container | 2 | 480 | 160 | true | false | 永不并核（:3244） |
| reinforced-vault | 3 | 1080 | 900 | true | false | 永不并核（:3252） |
| core-shard | 3 | 1100 | 4000 | false | — | 可卸载（unloadable=1） |
| liquid-container | 2 | 160 | 10（无效） | — | — | liquidCapacity 700 |
| liquid-tank | 3 | 500 | 10（无效） | — | — | liquidCapacity 1800 |
| liquid-router | 1 | 40 | 10（无效） | — | — | liquidCapacity 120，只做中转 |

### 表 3 卸载器与吞吐算例

| 方块 | size | health | speed（tick/件） | 速率 | 特点 |
|---|---|---|---|---|---|
| unloader | 1 | 70 | 60/11≈5.4545 | 11 件/s | allowCoreUnload=true，可取核心 [src: Blocks.java:2160-2164] |
| duct-unloader | 1 | 120 | 4 | 15 件/s | allowCoreUnload=false、solid=false、underBullets=true [src: Blocks.java:2227-2233] |

算例（都用表 1/表 2 的数字）：
- 一个 unloader 从容器搬向另一容器，11 件/s，搬空 1000 件 vault 需 1000/11 ≈ 91 s。
- 单个 duct-unloader 15 件/s [src: Blocks.java:2227-2233]，搬空 1000 件需 66.7 s；两个并联 30 件/s，但前提是源方至少 2 个邻居方块，否则 Unloader.java:163 直接 return。
- 核心 + 4 个 container 全部邻接：storageCapacity = 4000 + 4×300 = 5200（CoreBlock.java:715），此时 4 个容器的 items 已是同一个数组，读数会同步变化。
- 核心单物品满仓需要 4000/11 ≈ 364 s（一个 unloader），而 UI 条显示 4000/(5200×已解锁物品种数)。

## 源码锚点

- world/Block.java:75 `public int itemCapacity = 10;`（默认容量）
- world/Block.java:73 `public boolean separateItemCapacity = false;`
- world/Block.java:106 `public boolean unloadable = true;`
- world/blocks/storage/StorageBlock.java:26 separateItemCapacity=true；:17 coreMerge=true；:29 allowResupply=true
- world/blocks/storage/StorageBlock.java:51 linkedCore 字段；:55 acceptItem 转发；:59-61 canUnload 转发；:96 getMaximumAccepted 转发
- world/blocks/storage/StorageBlock.java:100-103 explosionItemCap = linkedCore!=null ? min(itemCapacity/60, 6) : itemCapacity
- world/blocks/storage/StorageBlock.java:132-139 canPickup / allowDeposit
- world/blocks/storage/CoreBlock.java:150 用量条分母 storageCapacity×物品种数
- world/blocks/storage/CoreBlock.java:282-284 canUnload = unloadable && rules.allowCoreUnloaders
- world/blocks/storage/CoreBlock.java:715-724 storageCapacity 三段累加 + items 指针共享
- world/blocks/storage/CoreBlock.java:789-791 owns() 判定 coreMerge + linkedCore
- world/blocks/storage/Unloader.java:99-111 五级比较器；:163 周期门；:218 配平条件；:228 计时器取余

## 实测与反例

1. **核心 4000 不是总量而是每种物品的上限。** 反证：CoreBlock.java:696-701 的 acceptItem/getMaximumAccepted 只比较 `items.get(item)` 与 storageCapacity，没有减去其它物品占用；:150 的界面条才把 total 除以 (storageCapacity×物品种数)。所以一个 core-shard 能同时装 4000 铜 + 4000 铅 + 4000 硅……而条依然只显示约 1/22 满。
2. **把 container 贴到核心旁边，"300"就消失了。** 反证：CoreBlock.java:715-719 把它的 items 指针替换成核心数组并设 linkedCore；此后 StorageBlock.java:96 的 getMaximumAccepted 返回核心的 storageCapacity，而不是 300。此时再加第 5 个 container，容量涨 300，但库存不会分开记。
3. **加固容器反而是"独立存储"。** 反证：Blocks.java:3244/3252 显式 coreMerge=false，所以 reinforced-container 紧贴核心时 owns() 返回 false（CoreBlock.java:790），容量与库存都不并。
4. **卸载器不会把容器清空。** 反证：Unloader.java:218 要求两端 loadFactor 不同才搬；两个空容器之间永远不搬，一个满一个空时只搬 1 件/周期直到比例相同。
5. **unloader 比 duct-unloader 慢。** 反证：unloader speed=60/11≈5.45 tick/件 = 11 件/s [src: Blocks.java:2162]，duct-unloader speed=4 = 15 件/s [src: Blocks.java:2230]，后者还不需要 titanium。
6. **00-data 里 container 的 liquidCapacity=10 是假数字。** 反证：00-data/blocks.json#id=container 的 hasLiquids 为 false，Block.java:75 的 itemCapacity 默认值 10 与 liquidCapacity 默认值同源，容量字段永远不参与计算。

## 常见误解

- **"核心容量是所有物资共享的一个池子，满了就投不进去。"** 实际上只有 UI 条按总量归一化；投递判定按单物品（CoreBlock.java:696-701），铜满了不影响铅。
- **"容器 300 就是总共 300。"** 容器 separateItemCapacity=true（StorageBlock.java:26），300 是每种物品各自 300，一个 container 理论上能存 300×22 种。
- **"container 放在核心旁边会增加仓库位。"** 它增加的是核心 storageCapacity 的数字（+300），同时失去独立库存；想让两种库存分开，要用 coreMerge=false 的加固容器或不邻接。
- **"卸载器会持续把物品从 A 搬到 B。"** 它是比例配平器（Unloader.java:218），两端比例相同就停手；想强制单向搬运要用传送带/桥或逻辑 setprop。
- **"duct-unloader 是 unloader 的升级版，可以取核心。"** 相反：duct-unloader 的 allowCoreUnload=false，取不出核心；unloader 才允许。
- **"核心 unloadable=1 所以一定能被卸载器取货。"** 还要 rules.allowCoreUnloaders 为真（CoreBlock.java:283），沙盒/Rules 关掉后所有核心都变成只进不出。

## 相关

- WORLD.BLOCKS.001 —— size、itemCapacity 与多格锚点的通用规则
- WORLD.LOGISTICS.001 —— 传送带/路由器/质量驱动器的吞吐，与卸载器的 11/15 件/s 对照
- WORLD.POWER.001 —— 电池（battery）也是存储方块，但存的是电量不是物品
- WORLD.LIQUIDS.001 —— 液体罐 700/1800/1000/2700 与管道容量的量级关系
- WORLD.CRAFTING.001 —— 工厂从核心/容器取料的路径
- WORLD.PAYLOAD.001 —— 载荷方块不与物品库存互通
