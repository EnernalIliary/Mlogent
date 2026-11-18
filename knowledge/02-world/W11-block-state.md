---
id: WORLD.BLOCKSTATE.001
title: 方块状态与配置（config / 旋转 / enabled / @sensor）
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - mindustry/world/Block.java:93-99
  - mindustry/world/Block.java:258
  - mindustry/world/Block.java:270
  - mindustry/world/Block.java:815-829
  - mindustry/world/Block.java:921-929
  - mindustry/world/Block.java:1651-1680
  - mindustry/entities/comp/BuildingComp.java:71
  - mindustry/entities/comp/BuildingComp.java:388-397
  - mindustry/entities/comp/BuildingComp.java:1419-1442
  - mindustry/entities/comp/BuildingComp.java:1949-1964
  - mindustry/entities/comp/BuildingComp.java:2099-2169
  - mindustry/entities/comp/BuildingComp.java:2259-2280
  - mindustry/logic/LAccess.java:7-94
  - mindustry/logic/LExecutor.java:668-710
  - mindustry/logic/LStatements.java:631
  - mindustry/world/blocks/logic/LogicBlock.java:55
data:
  - 00-data/blocks.json#id=sorter
  - 00-data/blocks.json#id=unloader
  - 00-data/blocks.json#id=payload-router
  - 00-data/blocks.json#id=mass-driver
  - 00-data/blocks.json#id=illuminator
  - 00-data/blocks.json#id=micro-processor
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001]
tags: [block-state, config, rotation, sensor, enabled, logic]
tokens: 1430
---

# 方块状态与配置（config / 旋转 / enabled / @sensor）

## 一句话

方块除了“是什么”（Block 定义）还有“现在怎样”：建造时固化的 `rotation`（0–3）、可变的 `config`（物品 / 方块 / 坐标 / 文本，经 `configured()` 分派）、以及可被逻辑或玩家关掉的 `enabled`；外部读状态只走两个口 —— `sense(LAccess)` 与 `sense(Content)`。

## 规则 / 公式

### 1. config 的四层结构

- 开关字段：`Block.java:258` 定义 `public boolean configurable;`（默认 false）；`Block.java:95` `saveConfig = false`、`Block.java:97` `copyConfig = true`、`Block.java:99` `clearOnDoubleTap = false`、`Block.java:270` `logicConfigurable = false`。
- 注册监听：`Block.java:927-929` 的 `config(Class<T> type, Cons2<E,T> config)` 把“类型 → 回调”写进 `configurations` 表；`Block.java:921-924` 的 `configClear(Cons<E>)` 把空配置注册在 `void.class` 上（双击清除走这条）。
- 分派：`BuildingComp.java:1419-1442` 的 `configured(Unit builder, Object value)`。类型归一化在 :1422-1427 —— null 当 `void.class`、匿名类取父类、Item/Block/Liquid/UnitType 各自折到类本身；命中表就回调，没命中且 value 是另一栋建筑时，递归拿它的 `config()` 重放（复制方块，:1435-1440）。
- 发起与存档：`BuildingComp.java:388-392` `configure(Object value)` 先 `block.lastConfig = value` 再 `Call.tileConfig(player, self(), value)`；服务器侧复制用 :395-397 `configureAny`。读档回灌只看 `Block.java:815-816`：`saveConfig && lastConfig != null` 才返回 lastConfig。
- 读当前值：`BuildingComp.java:2028-2032` `config()` 默认 null，由各方块覆写（Sorter → 物品，MessageBlock :219 → String，MassDriver → Point2）。
- 逻辑写 config：`BuildingComp.java:2163-2169` 只在 `type == LAccess.config && block.logicConfigurable && !(p1 instanceof LogicBuild)` 时 `configured(null, p1)`，最后一条是防逻辑方块互相复制配置造成风暴。

### 2. 旋转 0–3 的写入与三种读法

- 存储：`BuildingComp.java:71` `transient int rotation`；建造时 `:112-123` `init(tile, team, shouldAdd, rotation)` 写入。
- 方向含义以 `BuildingComp.java:522-529` 的 `nearby(rotation)` 为准：0→(x+1, y)、1→(x, y+1)、2→(x-1, y)、3→(x, y-1)。即 0 右、1 下（Mindustry 屏幕 y 轴向下）、2 左、3 上。
- 相对方向：`BuildingComp.java:532-545` `relativeTo(Building)` 把邻居方位换算回 0–3，不贴边返回 -1。
- 逻辑读数：`BuildingComp.java:2112` `case rotation -> rotation`（LAccess.rotation）；写回在 `LAccess.java:94` 的 settable 集合里。
- 网络位打包：`BuildingComp.java:226` `rotation = rot & 0b01111111`，低 7 位留给旋转。
- 只有 `rotate = true` 的 92/447 个方块会显示旋转 UI，但 `rotation` 字段在所有 Building 上都存在，不可旋转的恒为 0。
### 3. enabled 是一道总闸，不是拆迁

- 默认与持久化：`BuildingComp.java:79` `transient boolean enabled = true`；随方块写读存档 `:193` `write.b(enabled ? 1 : 0)` / `:237` `this.enabled = on == 1`。
- 置位：逻辑 `control(enabled)` 走 `:2157-2158` `enabled = !Mathf.zero((float)p1)`（写 0 才关）；`checkAllowUpdate()` `:2259-2263` 在 `!allowUpdate()`（例如地图区域外）时强制置 false。
- 语义：`:1949-1964` 的 `updateConsumption()` 里，`!enabled` 直接把 `potentialEfficiency = efficiency = optionalEfficiency = 0` 并停 `shouldConsumePower`（:1960-1963）；主循环 `:2277` 是 `if(enabled || !block.noUpdateDisabled) updateTile()` —— 声明了 `noUpdateDisabled ` 的方块即使关掉仍会 tick 特效。
- 状态展示：`:638-641` `status()` 第一分支就返回 `BlockStatus.logicDisable`。
- 读出：`:2124` `case enabled -> enabled ? 1 : 0`。

### 4. @sensor 的两个口：sense(LAccess) 与 sense(Content)

- `mindustry/logic/LAccess.java` 是逻辑的 Getter/Setter 枚举，共 77 个常量：72 个无参（感知变量）+ 5 个带参（`:81-85` `enabled("to")`、`shoot("x","y","shoot")`、`shootp(true,"unit","shoot")`、`config(true,"to")`、`color("to")`）。
- 静态集合在 `LAccess.java:90-94`：`all = values()`、`senseable = params.length <= 1`、`controls = params.length > 0`、`settable` 固定 15 项（x, y, velocityX, velocityY, rotation, speed, armor, health, shield, team, flag, totalPower, payloadType, bulletTime, bulletLifetime）。参数 >1 的只有 shoot / shootp，故感知面 75 项、控制面 5 项。
- `BuildingComp.java:2099-2131` `sense(LAccess)` 返回 double，未列出的项 `default -> Float.NaN`（:2129，逻辑侧会变成 null）；rotation、efficiency、totalItems、totalPower（:2116 用 `power.status * capacity` 而非累计量）、enabled 都在这里定义。
- 对象型读数另开 `senseObject(LAccess)` `:2133-2142`：`type` → block、`firstItem` → items.first()、`config` → 仅 `configSenseable()` 时返回 `config()`、`payloadType` → 当前载荷。
- `sense(Content)` `:2145-2153` 才按内容计数：Item → `items.get(i)`、Liquid → `liquids.get(l)`、UnitType/Block → `getPayloads().get(...)`；非法内容返回 NaN。
- mlog 侧：`LStatements.java:631` 用 `LAccess.senseable` 生成 sensor 的合法选项；`LExecutor.java:668-710` 的 SenseI 先 `senseObject` 判 `noSensed`，再退回数值 `sense`，`:706` 对 size / bufferSize 特判。
- 对**方块类型**（不是建筑实例）也有 Senseable 实现：`Block.java:1651-1663` 只给 color/health/solid/size/itemCapacity/liquidCapacity/powerCapacity/id；`Block.java:1666-1680` 的 `sense(Content)` 对 Item 返回的是**建造需求**（requirements × `rules.buildCostMultiplier`），不是库存。

### 5. 54 个可配置方块的类型划分

- 物品过滤（Item）：sorter、inverted-sorter、unloader、duct-unloader、surge-router（`00-data/blocks.json#id=sorter`）。
- 载荷/建造（Block 或 UnitType）：payload-router、reinforced-payload-router、constructor、large-constructor、payload-source。
- 坐标/目标（Point2 或 Block）：mass-driver、payload-mass-driver、large-payload-mass-driver、launch-pad、landing-pad。
- 文本与颜色：message、reinforced-message、switch、illuminator（LightBlock 存颜色）。
- 单位生产（UnitType）：ground/air/naval-factory 与 8 个 reconstructor/refabricator；其中 tank/ship/mech-fabricator 只在 `logicConfigurable` 里，不在 `configurable` 里（见数值表）。

### 6. 处理器为什么会「突然无效」

`BuildingComp.isValid()` 的判据是 `tile.build == self() && !dead()`。多格建筑按中心对齐放置（`offset = -(size-1)/2`，见 [[WORLD.BLOCKS.001]]），所以 **4×4 的着陆台一旦压到处理器所在的那一格，处理器自己的 `tile.build` 就被换成了着陆台** ⇒ `isValid()` 变假 ⇒ 程序里所有 `read x @this <名字>` 恒 null；而 `sensor t @this @type` 仍然返回 `micro-processor`（`@this` 是 `exec.build` 的对象引用，不查 tile）。症状看起来像「变量没声明」，其实是方块被判无效 —— 排查顺序：先 `sensor t @this @type` 确认对象还在，再查它脚下有没有被多格建筑覆盖。

判「这是不是处理器」也不要用 `building instanceof LogicBlock`：真实建筑是内部类 `LogicBlock$LogicBuild`，`instanceof` 恒假（断言表 L2-26）。鸭子判据是「有 `executor` 且有 `code`」。

## 数值

表 A：配置类字段在 447 个注册方块里的分布（jar v160.7 反射 raw，占比按 447 计）[src: jar raw 447 条]。

| 字段 | 为 true 的方块数 | 占比 | 出处 |
| --- | --- | --- | --- |
| configurable | 54 | 12.1% | [src: Block.java:258 + jar raw] |
| logicConfigurable | 22 | 4.9% | [src: Block.java:270 + jar raw] |
| 两者同时为 true | 19 | 4.2% | [src: jar raw 交叉] |
| 仅 logicConfigurable（tank/ship/mech-fabricator） | 3 | 0.7% | [src: jar raw] |
| saveConfig | 17 | 3.8% | [src: Block.java:95 + jar raw] |
| copyConfig（默认 true） | 443 | 99.1% | [src: Block.java:97 + jar raw] |
| clearOnDoubleTap | 20 | 4.5% | [src: Block.java:99 + jar raw] |
| editorConfigurable | 6 | 1.3% | [src: Block.java + jar raw] |
| commandable | 24 | 5.4% | [src: jar raw] |
| rotate = true | 92 | 20.6% | [src: Block.java:120 + jar raw] |

- saveConfig 的 17 个 = 6 个编辑器调色方块（colored-floor / colored-wall / character-overlay / character-overlay-white / rune-overlay / rune-overlay-crux）+ 11 个玩法方块（sorter、inverted-sorter、unloader、duct-router、duct-unloader、surge-router、unit-cargo-unload-point、item-source、liquid-source、target-dummy、illuminator）[src: jar raw]。
- copyConfig 为 false 的正好 4 个，全是桥类：bridge-conveyor、phase-conveyor、bridge-conduit、phase-conduit [src: jar raw]。

表 B：逻辑读写面（LAccess，77 常量）。

| 集合 | 项数 | 判定条件 | 出处 |
| --- | --- | --- | --- |
| 无参常量 | 72 | params.length == 0 | [src: LAccess.java:7-78] |
| 带参常量 | 5 | params.length > 0 | [src: LAccess.java:81-85] |
| senseable | 75 | params.length <= 1 | [src: LAccess.java:92] |
| controls | 5 | params.length > 0 | [src: LAccess.java:93] |
| settable | 15 | 显式白名单 | [src: LAccess.java:94] |

表 C：两条关键口径（写进正文会被误读成同义，故单列）。

| 现象 | 口径 | 出处 |
| --- | --- | --- |
| `enabled` 写入 | `!Mathf.zero(p1)`，p1 为 0 才关 | [src: BuildingComp.java:2158] |
| 旋转编码 | `rot & 0b01111111`，低 7 位 | [src: BuildingComp.java:226] |
| powerNetIn / powerNetOut | 图统计量 × 60（每秒） | [src: BuildingComp.java:2120-2121] |
| totalPower | `power.status * capacity`（缓冲比例），不是存量 | [src: BuildingComp.java:2116] |
## 源码锚点

- `mindustry/world/Block.java:93` `public @Nullable Object lastConfig;`；:95 saveConfig、:97 copyConfig、:99 clearOnDoubleTap 三个默认值。
- `mindustry/world/Block.java:258` `public boolean configurable;`；:270 `logicConfigurable = false`。
- `mindustry/world/Block.java:815-816` 读档时 `if(saveConfig && lastConfig != null) return lastConfig;`。
- `mindustry/world/Block.java:921-929` `configClear` / `config(Class, Cons2)` 注册入口。
- `mindustry/world/Block.java:1651-1680` Block 自身的 `sense(LAccess)` 与 `sense(Content)`（后者返回建造需求）。
- `mindustry/entities/comp/BuildingComp.java:71` `transient int rotation`；:79 `enabled = true`。
- `mindustry/entities/comp/BuildingComp.java:388-397` `configure` / `configureAny`；:1419-1442 `configured` 分派。
- `mindustry/entities/comp/BuildingComp.java:2028-2032` `config()` 默认 null。
- `mindustry/entities/comp/BuildingComp.java:1949-1964` `enabled` 归零 efficiency。
- `mindustry/entities/comp/BuildingComp.java:2099-2169` `sense` / `senseObject` / `control`。
- `mindustry/entities/comp/BuildingComp.java:2259-2280` `checkAllowUpdate` 与主循环 `update()`。
- `mindustry/logic/LAccess.java:7-94` 77 个常量与 senseable/controls/settable 三个静态集合。
- `mindustry/logic/LExecutor.java:668-710` SenseI；`mindustry/logic/LStatements.java:631` sensor 选项来源。
- `mindustry/world/blocks/logic/LogicBlock.java:55` `configurable = true`；:653 `config()` 返回 `byte[]`。

## 实测与反例

- **反例 1（copyConfig 不是“都复制”）**：四个桥 bridge-conveyor / phase-conveyor / bridge-conduit / phase-conduit 的 copyConfig 为 false [src: jar raw]，因为桥的“配置”是连接关系，不是 `configurations` 表里的值；复制方块时 `BuildingComp.java:1435-1440` 只重放 `config()` 非 null 的对象。
- **反例 2（同一个 @sensor 两种世界）**：对**建筑** `sensor ... @copper` 返回库存（`BuildingComp.java:2146` `items.get(i)`）；对**方块类型**返回该物品的建造需求量（`Block.java:1666-1680` `r.amount * state.rules.buildCostMultiplier`）。同一条指令、目标不同，结果差到几百。
- **反例 3（micro-processor 的配置是代码）**：`LogicBlock.java:653` 的 `config()` 返回 `byte[]`；它 configurable=true 但 logicConfigurable=false，所以逻辑的 `control(config)` 写不进去（`BuildingComp.java:2165` 要求 logicConfigurable，且 p1 不能是 LogicBuild）。
- **反例 4（关掉 ≠ 不更新）**：`BuildingComp.java:2277` `if(enabled || !block.noUpdateDisabled) updateTile()`；声明了 noUpdateDisabled 的方块在 enabled=false 时仍跑 updateTile，只是生产量已归零。
- **反例 5（config 类型不止 4 种）**：归一化只特判 Item/Block/Liquid/UnitType（`:1424-1427`）；message 存 String（`MessageBlock.java:219`）、switch 存 Boolean（`SwitchBlock.java:74`）、illuminator 存颜色，都靠 `value.getClass()` 命中。
- **反例 6（rotation=1 是向下）**：`BuildingComp.java:522-529` 0→x+1、1→y+1；把它当“角度 90°”再用三角函数换算，会在 y 轴向下的坐标系里整体镜像。

## 常见误解

1. **“configurable=true 就能被逻辑改”**：错。逻辑写配置要 `logicConfigurable`（22 个），configurable 只管玩家 UI（54 个）[src: Block.java:258,270 + BuildingComp.java:2165]。
2. **“rotation 是角度或顺时针 90°”**：错，是 0–3 的枚举，语义由 `nearby(rotation)` 定义（0 右 / 1 下 / 2 左 / 3 上）[src: BuildingComp.java:522-529]。
3. **“enabled=false 会从电网/物流网摘掉”**：错，方块仍在图上，只是 `efficiency = 0`、`shouldConsumePower = false`，邻居仍能连它 [src: BuildingComp.java:1960-1963]。
4. **“@sensor 能读任意字段”**：错，只有 75 个 senseable 项；未列出的 `case` 落到 `Float.NaN`（逻辑里变 null）[src: BuildingComp.java:2129]。
5. **“配置会跟着存档”**：错，`saveConfig` 默认 false，447 个方块里只有 17 个开启 [src: Block.java:95 + jar raw]。
6. **“双击清除对所有方块有效”**：错，`clearOnDoubleTap` 仅 20 个方块，且清除写的是 `void.class` 的 `configClear` 回调 [src: Block.java:921-924 + jar raw]。

## 相关

- [[WORLD.BLOCKS.001]] 方块本体、size 与锚点（rotation 的生效范围由它决定）
- [[WORLD.LOGISTICS.001]] sorter/unloader 的过滤器配置怎么参与物流
- [[WORLD.PAYLOAD.001]] payload-router 的 Block/UnitType 配置与 canSort 判定
- [[WORLD.STORAGE.001]] unloader 的 config(Item) 与存储优先级
- 逻辑层机制见 `knowledge/06-mlog/` 的 sensor/control 章节