---
id: WORLD.TERRAIN.001
title: 地形与环境：地板 / 矿层 / 墙三层结构、移动倍率与水陆判定
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src:
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/Floor.java:24-70 [src: Floor.java:24-70]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/OreBlock.java:15-41 [src: OreBlock.java:15-41]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/StaticWall.java:26-37 [src: StaticWall.java:26-37]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/Prop.java:16-22 [src: Prop.java:16-22]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/ShallowLiquid.java:21-31 [src: ShallowLiquid.java:21-31]
  - Mindustry-Source/core/src/mindustry/world/blocks/environment/SteamVent.java:19-47 [src: SteamVent.java:19-47]
  - Mindustry-Source/core/src/mindustry/world/Block.java:112-160 [src: Block.java:112-160]
  - Mindustry-Source/core/src/mindustry/world/Tile.java:571-580 [src: Tile.java:571-580]
  - Mindustry-Source/core/src/mindustry/type/Attribute.java:8-20 [src: Attribute.java:8-20]
data:
  - 00-data/blocks.json#id=deep-water
  - 00-data/blocks.json#id=shallow-water
  - 00-data/blocks.json#id=molten-slag
  - 00-data/blocks.json#id=stone-wall
  - 00-data/blocks.json#id=ore-copper
depends: [WORLD.BLOCKS.001, WORLD.DRILLING.001, WORLD.LIQUIDS.001]
tags: [地形, 地板, floor, 矿石, 墙, 深水, 浅水, 移动倍率]
tokens: 1394
---

## 一句话

地形不是一个「层」而是三层叠加：**地板 floor**（决定移动速度、是否液体、能否被泵抽）、**矿层 overlay**（ore-copper 这类只影响采掘的覆盖层）、**墙 wall / 装饰 prop**（占据格子、阻挡移动与建造的固体方块），三者各自带一套数值，混为一谈是这一域最常见的错。

## 规则 / 公式

### 1. 三层叠加：floor / overlay / wall

- 一个 Tile 同时持有 **地板**、**覆盖层**（overlay，矿石就挂在这里）和 **方块**（wall、建筑）。矿石类 `OreBlock extends OverlayFloor`（OreBlock.java:15），构造时 `this.itemDrop = ore`、`variants = 3`、`useColor = true`（OreBlock.java:20-23），它不改地板，只改这一格的掉落。 [src: OreBlock.java:15]
- 墙是真正的 Block：`StaticWall extends Prop`（StaticWall.java:16），构造里 `solid = true`（:29）；同格的地板仍然存在，只是被墙盖住。 [src: StaticWall.java:16]
- 因此「这格是矿」和「这格是水」可以同时成立：矿层可以叠在水地板上（例如 darksand-tainted-water 这类浅水配矿）。采掘读 overlay（Tile.java:571-580 的 drop() 先取 `overlay().itemDrop`，再退到 `floor().itemDrop`）。 [src: Tile.java:571-580]

### 2. Floor 的九个地形字段与默认值

Floor.java:24-70 逐个给了语义与默认值，直接影响手感的只有四个： [src: Floor.java:24-70]

| 字段 | 默认值 | 作用 | 出处 |
|---|---|---|---|
| speedMultiplier | 1 | 单位移速乘数 | Floor.java:28 |
| dragMultiplier | 1 | 单位阻力乘数（冰面 <1 更滑） | Floor.java:30 |
| damageTaken | 0 | 每 tick 受伤（原版地板全为 0） | Floor.java:32 |
| drownTime | 0 | 溺水 tick 数，0 = 不会淹 | Floor.java:34 |
| liquidDrop | null | 泵能抽到的液体 | Floor.java:48 |
| liquidMultiplier | 1 | 泵产出倍率（深水 1.5） | Floor.java:50 |
| isLiquid | false | 是否液体地板 | Floor.java:52 |
| overlayAlpha | 0.65 | 液体覆盖层不透明度 | Floor.java:54 |
| shallow | false | 浅水标记（地图生成用） | Floor.java:58 |
| status / statusDuration | none / 60 | 踩上去挂的状态与时长 | Floor.java:44-46 |
| oreDefault / oreScale / oreThreshold | false / 24 / 0.828 | 是否默认生成矿、矿噪声尺度与阈值 | Floor.java:62-64 |

### 3. 水陆判定：深度靠 drownTime，浅水靠类

- **深水**是普通 `Floor` 加上 `isLiquid = true` 与 `drownTime = 200`；**浅水**是 `ShallowLiquid` 子类，`set()` 里写死 `isLiquid = true`、`shallow = true`，并从液体地板继承 status 与 liquidDrop（ShallowLiquid.java:21-31）。 [src: ShallowLiquid.java:21-31]
- 同一个 water 液体可以有两种地板：deep-water 会淹死人（drown 200 tick ≈ 3.3 s），shallow-water 完全不淹（drownTime 0），移速分别是 0.2 与 0.5 [src: gamedata.json#deep-water / #shallow-water]。
- 泵的水量由地板决定：`liquidMultiplier` 深水 1.5、浅水 1.0 [src: gamedata.json#deep-water]，再乘 Pump 的 pumpAmount（WORLD.LIQUIDS.001）。

### 4. 墙与装饰：三种「不能建」的地形，行为完全不同

| 类 | 代表 | solid | breakable | unitMoveBreakable | 语义 |
|---|---|---|---|---|---|
| StaticWall | stone-wall / dune-wall | true | false | false | 永久地形墙，挖不动也推不倒 |
| Prop | 石头、岩石装饰 | true（视实例） | true | true | 可被单位推碎、可被拆掉换格子 |
| TreeBlock | 树 | true | true | true | 同上，且有 `clipSize = 90`、`customShadow = true`（TreeBlock.java:16-18） |

判据在构造器里，不在数据表里：`Prop` 构造设 `breakable = true`、`alwaysReplace = true`、`instantDeconstruct = true`、`unitMoveBreakable = true`（Prop.java:16-19）；而 `StaticWall` 构造把前三个覆盖回 false 并加 `solid = true`、`instantBuild = true`、`placeableLiquid = true`、`ignoreBuildDarkness = true`（StaticWall.java:28-37）。 [src: Prop.java:16-19]

### 5. 危害地板：伤害不写在 damageTaken 上

- 原版所有地板的 `damageTaken` 都是 0 [src: gamedata.json#molten-slag]，熔岩的伤害走的是 **status 状态**：molten-slag 的 `statusDuration = 240`、speed 0.19、drown 230 [src: gamedata.json#molten-slag]；tar 同为 0.19 / 230 / 240 [src: gamedata.json#tar]。
- 热度则走 **Attribute.heat**：hotrock 0.5、magmarock 0.75、molten-slag 0.85（WORLD.HEAT.001 的 Attribute 表），thermal-generator 直接用地板 heat 属性发电。
- 发光是 `lightRadius`：hotrock 30、magmarock 50、molten-slag 40 [src: gamedata.json#hotrock]，这一项只影响视觉照明，不参与任何产能公式。

### 6. 地形对建造的影响只有两条

- **solid 格不能放**：墙与装饰占格，放置合法性由 `Build.validPlace` 判（WORLD.BLOCKS.001 已给七步流程），solid 墙挡路也挡建造。
- **液体地板默认可建**：所有液体地板（deep-water、molten-slag、tar、arkycite-floor）在数据表里都是 `placeableLiquid = true` [src: gamedata.json#deep-water]，所以「水上能建方块、只是不能走」是设计意图，不是 bug。
- 多格地形例外：`SteamVent extends Floor`（SteamVent.java:19），用 9 个相对偏移拼出 3×3 的喷气口，并挂 `BlockFlag.steamVent`（:46）——它是一格地板逻辑、九格视觉，别按 9 个独立地块算。 [src: SteamVent.java:19]

## 数值

### 表 A｜14 种代表地板（v160.7 反射，00-data/blocks.json 可核 id）

| 地板 | 类 | speedMultiplier | dragMultiplier | drownTime | isLiquid | 液体 / liquidMultiplier | statusDuration | 出处 |
|---|---|---|---|---|---|---|---|---|
| deep-water | Floor | 0.2 | 1 | 200 | true | water / 1.5 | 120 | gamedata.json#deep-water |
| shallow-water | Floor | 0.5 | 1 | 0 | true | water / 1 | 90 | gamedata.json#shallow-water |
| tainted-water | Floor | 0.5 | 1 | 0 | true | water / 1 | 90 | gamedata.json#tainted-water |
| deep-tainted-water | Floor | 0.18 | 1 | 200 | true | water / 1.5 | 140 | gamedata.json#deep-tainted-water |
| darksand-water | ShallowLiquid | 0.8 | 1 | 0 | true | water / 1 | 50 | gamedata.json#darksand-water |
| darksand-tainted-water | ShallowLiquid | 0.75 | 1 | 0 | true | water / 1 | 60 | gamedata.json#darksand-tainted-water |
| molten-slag | Floor | 0.19 | 1 | 230 | true | slag / 1 | 240 | gamedata.json#molten-slag |
| tar | Floor | 0.19 | 1 | 230 | true | oil / 1 | 240 | gamedata.json#tar |
| arkycite-floor | Floor | 0.3 | 1 | 200 | true | arkycite / 1 | 60 | gamedata.json#arkycite-floor |
| mud | Floor | 0.6 | 1 | 0 | false | — | 30 | gamedata.json#mud |
| ice | Floor | 0.9 | 0.35 | 0 | false | — | 60 | gamedata.json#ice |
| red-ice | Floor | 0.9 | 0.4 | 0 | false | — | 60 | gamedata.json#red-ice |
| sand-floor / stone / metal-floor / snow | Floor | 1 | 1 | 0 | false | — | 60 | gamedata.json#sand-floor |

### 表 B｜移动影响汇总

| 现象 | 数值 | 出处 |
|---|---|---|
| 深水最慢 | 移速 ×0.2、drown 200 tick ≈ 3.3 s 后溺水 | deep-water；Floor.java:28、:34 |
| 冰面不减速但更滑 | 移速 ×0.9、阻力 ×0.35（越低越滑） | ice；Floor.java:30 |
| 熔渣/焦油最黏 | 移速 ×0.19、drown 230 tick ≈ 3.8 s | molten-slag、tar |
| 浅水只减速不淹 | 移速 ×0.5–0.8、drown 0 | shallow-water、darksand-water；ShallowLiquid.java:25-30 |
| 深水抽水加成 | 泵产出 ×1.5 | deep-water；Floor.java:50 |

## 源码锚点

1. `Floor.java:24-70` —— 全部地形字段与默认值（speedMultiplier :28、dragMultiplier :30、damageTaken :32、drownTime :34、liquidDrop :48、liquidMultiplier :50、isLiquid :52、overlayAlpha :54、shallow :58、oreScale :64）。 [src: Floor.java:24-70]
2. `OreBlock.java:15-23` —— 矿层继承 OverlayFloor，`itemDrop = ore`、`variants = 3`。 [src: OreBlock.java:15-23]
3. `ShallowLiquid.java:21-31` —— `set(liquid, floor)` 继承 isLiquid / shallow / status / liquidDrop。 [src: ShallowLiquid.java:21-31]
4. `StaticWall.java:26-37` —— 墙的七个开关：solid / breakable=false / instantBuild / placeableLiquid / ignoreBuildDarkness。 [src: StaticWall.java:26-37]
5. `Prop.java:16-19` —— 装饰的四个开关：breakable / alwaysReplace / instantDeconstruct / unitMoveBreakable。 [src: Prop.java:16-19]
6. `TreeBlock.java:16-18` —— 树是 solid + clipSize 90 + customShadow。 [src: TreeBlock.java:16-18]
7. `SteamVent.java:19-46` —— 3×3 喷气口的九个偏移与 BlockFlag.steamVent。 [src: SteamVent.java:19-46]
8. `Tile.java:571-580` —— drop() 先读 overlay().itemDrop 再读 floor().itemDrop，这是「矿层不改地板」的证据。 [src: Tile.java:571-580]
9. `Attribute.java:8-20` —— heat / spores / water / oil / light / sand / steam 七个环境属性。 [src: Attribute.java:8-20]
10. `Floor.java:62-64` —— oreDefault / oreScale 24 / oreThreshold 0.828，地图生成参数。 [src: Floor.java:62-64]

## 实测与反例

**反例 1｜「深水 = 浅水 × 2」不成立。** deep-water 移速 0.2、浅水 0.5，比值 2.5；但溺水一条是 0 vs 200 tick，浅水完全不会淹 [src: gamedata.json#shallow-water]，不是同一参数的不同档位。

**反例 2｜熔岩伤害不走 damageTaken。** 全树地板 `damageTaken = 0`（Floor.java:32 的默认值，无人覆盖），站在 molten-slag 掉血来自它挂的 status（statusDuration 240）与 Attribute.heat 0.85，而不是 per-tick 伤害字段。 [src: Floor.java:32]

**反例 3｜墙不等于装饰。** StaticWall 把 Prop 的 `breakable = true / unitMoveBreakable = true` 全部覆盖回 false（StaticWall.java:28），所以 stone-wall 永远挖不动；而同一地图上的小石头（Prop）被单位走过去就碎——两条都叫「地形障碍」，行为不同。 [src: StaticWall.java:28]

**反例 4｜冰面不是更快的地板。** ice 的 speedMultiplier 是 0.9（比石头 1.0 更慢），它真正改变的是 dragMultiplier 0.35 [src: gamedata.json#ice]，手感「滑」来自阻力而非速度。

**反例 5｜液体地板默认可建。** 很多人以为水上不能造建筑，实际 deep-water / tar / molten-slag 全部 `placeableLiquid = true` [src: gamedata.json#deep-water]，水上建抽水泵是标准开局。

**正面实测｜深水抽水速率。** 2×2 的 rotary-pump 在 deep-water 上是 `0.2 × 4 格 × 1.5 = 1.2/tick = 72/s`，而同一台泵在浅水上只有 48/s（WORLD.LIQUIDS.001 的泵表 × liquidMultiplier 1.5 vs 1.0）。

## 常见误解

1. **「地板就是地形，墙是另一种方块」**——三层是叠加关系：矿层可以叠在任何地板上，墙也可以立在水上，三者的数据互不替代。
2. **「矿石是一格特殊地形」**——矿是 **overlay**，不改地板移动/水属性，只通过 `drop()` 改采掘产出（Tile.java:571-580）。 [src: Tile.java:571-580]
3. **「damageTaken 是熔岩伤害来源」**——原版地板该字段恒为 0，伤害来自 status；调地图时改 damageTaken 对原版熔岩无效。
4. **「浅水会淹死小单位」**——ShallowLiquid 的 drownTime 是 0（继承 Floor 默认，见 :34），浅水只减速。
5. **「lightRadius 会照亮周围并影响产能」**——它只影响视觉；产能看 Attribute（heat 0.85 等）[src: gamedata.json#molten-slag]，两者字段不同。
6. **「喷气口是 9 个地块」**——SteamVent 是一个 Floor + 9 个绘制偏移（SteamVent.java:20-31），逻辑上只占一格。 [src: SteamVent.java:20-31]

## 相关

- WORLD.BLOCKS.001 —— 多格方块放置合法性，地形对建造的约束在这里。
- WORLD.DRILLING.001 —— 矿层与硬度的采掘规则，oreBlocks 16 条。
- WORLD.LIQUIDS.001 —— 泵与地板 liquidMultiplier 的相乘关系。
- WORLD.HEAT.001 —— 地板 heat 属性与 thermal-generator。
- 00-data/blocks.json —— 地板/墙/矿的全部静态字段（drownTime、dragMultiplier、buildVisibility）。
