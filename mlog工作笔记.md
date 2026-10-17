# mlog 工作笔记(持续更新)

> 为 **Iliary艾铭** 的游戏环境编写 mlog 时积累的规则、参数、模式和踩过的坑。
> **每次交流后追加一节**,不覆盖旧内容;如果旧结论被推翻,在原处标注 `【修正】` 并写清依据。
>
> 源码依据:workspace 内 `Mindustry-Source`(游戏版本 **159.1**)+ `Logic-Docs-v1.1.0`。
> 工具:[tools/msch.py](tools/msch.py)(解析蓝图)、[tools/mlogsearch.py](tools/mlogsearch.py)(检索逻辑)。

---

## 0. 写代码的铁律(最重要,先看这里)

这几条是我反复犯错之后定下来的,优先级高于任何"优化直觉"。

### 0.1 不要自己发明阈值

**不要**用"我算了一下余量不够"来改判据。游戏机制只要求某个下限,**满足下限就是满效率**,不需要额外缓冲。

- ✗ 自己加"满载才发车""留 30% 余量"这类门槛
- ✓ 用**标准答案**的判据(`need ≥ 1` 就补)

### 0.2 不要做可行性推算

**不要**用理论速度×距离去论证"这做不到"。实际战场有阻挡、有堵车、有帧率波动,而且:

- 单位 `speed()` 还要乘 `floorSpeedMultiplier()`、boost 等系数,裸值不是实际速度
- 游戏里"够不够用"是**实测**出来的,不是算出来的

> **这条是明确的教训**:我曾用往返时间推出"单个星辉跑不了 100 格",
> 但鱼冰无线超实测就是能跑 100 格。**我的前提(必须留缓冲)本身就不成立。**

### 0.3 优先找标准答案

遇到经典题型(无线运输、集火、多控搬运),**先翻蓝图里的成熟实现**,再动手写。

| 题型 | 标准答案 |
|---|---|
| 无线超(单星辉搬运) | `最简鱼冰无线超.msch` |
| 无线超(带单位避让+信息板) | `鱼冰无线超(单位避让版).msch` |
| 单位归属判定 | `GetBlock点阵钍反替换防炸房逻辑1.2.msch` L0–L7 |
| 多控槽位搬运 | `多单位搬运物品至核心.msch` |
| 蜂群无 flag 分配 | `反病毒.msch` |
| 世界处理器工程 | `MCV.msch` |

### 0.4 遇到不确定的机制,翻源码而不是猜

已纠正过多次"我以为"。**`LExecutor.java` 和 `LStatements.java` 是唯一权威。**

### 0.5 ⭐ 控制单位前必须先 `ubind`(我漏过这条)

`ucontrol` / `uradar` / `ulocate` **全部只对当前 `@unit` 生效**。

源码 [LExecutor.java:323](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L323):

```java
if(unitObj instanceof Unit unit && unit.isValid()
    && exec.unit.obj() == unit            // ← 必须是当前 @unit
    && (unit.team == exec.team || exec.privileged)
    && unit.controller().isLogicControllable()){
```

而 **`@unit` 初始值是 `null`** —— **不 `ubind` 的话,所有控制语句静默无效**(不报错)。

```mlog
# ❌ 我的错误:只检查归属,没有任何路径真正 ubind
sensor d @unit @dead
jump 0 notEqual d 1
sensor c @unit @controller
jump 0 notEqual c @unit
... ucontrol ...
# @unit 永远是 null → ucontrol 全部无效,而且 jump 0 是死循环

# ✅ 正确:每轮先绑
ubind @flare
sensor d @unit @dead
...
```

**两个要点**:

1. **`ubind` 不需要单位空闲**,环形推进,所以**循环里每轮绑一次是标准做法**(`最简鱼冰无线超` 就是这么写的)
2. `ubind` 是 `@unit = 下一个同类单位`,单单位场景下每次都是它

**推广到所有"我以为自动就有"的东西**:

| 我以为自动有 | 实际必须显式获取 |
|---|---|
| `@unit` | **`ubind`** |
| `core`(核心建筑引用) | **`ulocate` 第 8 参输出** |
| 链接建筑 | 处理器上真的连着才行,或 `getlink` |

**教训**:mlog 里**没有任何"隐式上下文"**。要用什么,先取什么。

---

---

### 0.6 ⚠️ 元组/字典赋值不能用"两个 `r.utf()`"

**我踩过的坑,而且它骗过了我自己的测试。**

```python
# ❌ 错的:Python 先算右边,再算下标键
tags[r.utf()] = r.utf()
# → 把 value 当成了 key,整个字典键值对调

# ✅ 对的:拆成两条
key = r.utf()
tags[key] = r.utf()
```

**后果**:我的解析器把**全部 625 个蓝图的 name/description/labels 都读反了**,
`sch.name` 永远返回 `'unknown'`,labels 永远是空 —— 而**方块和逻辑完全没受影响**,所以一直没暴露。

**为什么我的往返测试没抓到**:`mschgen --selftest` 是"解析→重建→再解析",**两边用的是同一个读函数**,
所以系统性错误在两边同时出现、互相抵消,比较结果依然"一致"。**只有 429/429 全绿。**

> **教训:自洽的往返测试抓不到"读和写同时错"的 bug。必须拿真实文件做地面真值比对。**
> 这次的发现方式就是:生成蓝图后检查 `sch.name`,发现是 `'unknown'` 而不是我设的名字 ——
> **一个"输出不对"的直觉比 429 个通过的自测更有用。**

修复后重新生成了 `logic-corpus/`,**403/430 个蓝图恢复了 labels**(之前是 0)。

### 0.7 ⭐ 预算按"执行到几条语句"算,不按语句种类算

**`jump` 不额外花钱 —— 它和 `op`、`print` 一样就是 1 条。**

`runOnce()` 里 **`counter` 先自增再执行**,**不看指令类型**([LExecutor.java:111-121](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L111-L121)):

```java
instructions[(int)(counter.numval++)].run(this);   // ← 无条件 +1
```

⇒ **钱花在"循环圈数 × 循环体语句数"上,不花在 `jump` 这个字上。**
⇒ 也别指望"用 `jump` 跳过一段能省钱":跳过去的行确实不执行(不花钱),但**跳转自己仍然收 1 条**。

**每 tick 的额度**由 [LogicBlock.java:564-578](Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java#L564-L578) 的 accumulator 循环发放,`ipt = instructionsPerTick`:

| 处理器 | ipt | 每秒 |
|---|---|---|
| 微型 | **2** | 120 |
| 逻辑 | **8** | 480 |
| 超级 | **25** | 1500 |
| 世界 | **8**(上限 1000) | 480 |

**只有 `wait` / `stop` / `printflush @wait` 会 `yield`,提前结束这一 tick**;
**`jump 0 always` 没有这个机制,会在一个 tick 内把额度烧光。**
改写循环前先用 `mlog.py check --cost` 看最坏路径(§15.11、§15.12 有完整机制)。


## 1. 链接与命名

### 1.1 链接名规则

**内部名按 `-` 切分,永远取最后一段 + 序号(从 1 开始)。**

| 建筑内部名 | 链接名 |
|---|---|
| `overdrive-dome` | `dome1`、`dome2` |
| `overdrive-projector` | `projector1` |
| `mass-driver` | `driver1` |
| `hyper-processor` | `processor1` |
| `micro-processor` | `processor1` |
| `large-logic-display` | `display1`(不是 `logic1`) |
| `phase-conveyor` / `conveyor` | `conveyor1` |

源码 [LogicBlock.getLinkName()](Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java#L123) 里另有一句"最后一段是 `large` 或纯数字时取倒数第二段"的分支,
但**在本环境下结论就是"永远取最后一段"**,已由 Iliary 确认。

### 1.2 ⭐ `core` 是**变量**,不是内置关键字【重要修正】

**vanilla 源码里没有 `core` 这个内置变量。** 它只是一个普通变量名,
**由 `ulocate` 的第 8 个输出参数赋值得来。**

```mlog
ulocate building core 0 @copper cx cy found core
                                        ↑     ↑
                                      outFound  outBuild ← 这里输出到名为 core 的变量
ucontrol itemTake core @silicon 10 0 0     # 用这个变量取货
ucontrol itemDrop core 999 0 0 0           # 用这个变量投料
```

**所以"能不能用 `core`"取决于你自己有没有把它赋值。**

> **⚠️ 我犯的错**:我以为 `core` 是内置关键字,于是在 `ulocate` 里把第 8 参写成 `0`
> (丢弃建筑引用),然后直接用 `core` 当建筑用。**结果 `core` 是个未定义变量(等于 0),
> `itemTake`/`itemDrop` 的目标无效,静默失败。**

**标准答案的完整写法**(`最简鱼冰无线超.msch` 与"单位避让版"都是这个模式):

```mlog
ulocate building core 0 @copper bx by 0 core      # ← 核心引用存进 core
ucontrol itemTake core cfg need.it.amo 0 0        # 用 core 变量取货
ucontrol itemDrop core 999 0 0 0                  # 用 core 变量投料
```

**变量名随便取**(`core`、`corea`、`核心` 都行),关键是**必须接住 ulocate 的输出**。

**注意坐标语义**:`ulocate` 输出的 outX/outY 是**建筑左上角格子**,outBuild 是**建筑引用**。
`itemTake`/`itemDrop` 用建筑引用(判定半径从中心算),`move` 才需要坐标。

### 1.3 两套坐标,不要混用

| 写法 | 含义 | 出处 |
|---|---|---|
| `core`(ulocate 输出的变量) | **建筑引用** | `ulocate` 第 8 参 |
| `ulocate ... outX outY` | 建筑**左上角**格子 | `World.conv(res.build.x)` |
| `sensor x <建筑> @x` | 建筑**中心** | `LAccess.x` |

- `itemTake` / `itemDrop` 用**建筑引用**(判定半径从中心算)
- 想"飞到某处"才需要坐标

**特例**:`ucontrol move core 8 0 0 0` 这种写法里,如果 `core` 是 ulocate 输出的建筑引用,
**第三参 `8` 仍然是无效占位**(`move` 不读它),单位会飞到核心建筑的位置。

---

## 2. sensor / null 语义

### 2.1 ⭐ null 会传染给所有参数

**变量为 `null` 时,读它的所有 `sensor` 参数都返回 `null`。**

```mlog
sensor bx dome1 @x        # dome1 没了 → bx = null
sensor by dome1 @y        # 同样 null
```

所以判"建筑还在不在"只需判一个:

```mlog
jump 0 strictEqual by null       # 一个就够,不用两个都判
```

> 这条是 Iliary 明确指出并确认的。我原本赌"可能是 null",现在确定。

### 2.2 `@pingX` 无 ping 时也返回 null

`UnitComp` 源码写的是 `Float.NaN`,但**在本环境里 NaN 统一以 `null` 返回**。

**所以 `jump X equal px null` 是有效判断**,我之前对 `ILI集火逻辑` 的质疑不成立。

### 2.3 我一律用 `strictEqual` 判 null

对象引用比较必须精确,`equal` 走 `Structs.eq`、带浮点容差。**判 null 和判对象归属一律 `strictEqual`。**

---

## 3. 物品搬运(核心章节)

### 3.1 容量:单堆叠,不是分类型

**⭐ 单位只能带一种物品。** `itemCapacity` 是**堆叠上限**,不是"每种物品的上限"。

| 对象 | 容量 | 说明 |
|---|---|---|
| 星辉 `@flare` | **10** | 只能带 10 个**某一种**物品 |
| 超速穹顶 `overdrive-dome` | **10** | `@totalItems` 是**合计**,硅+相织布之和 |

源码:`UnitComp` 的 `case itemCapacity -> type.itemCapacity`([:267](Mindustry-Source/core/src/mindustry/entities/comp/UnitComp.java#L267));
`Block.itemCapacity` 默认 10([:75](Mindustry-Source/core/src/mindustry/world/Block.java#L75))。

> **这是我的第一个大错**:我让它 `itemTake` 两次(硅+相织布),实际各只能拿 5 个。
> **正确做法是"一次只带一种,按缺口选带哪种"。**

### 3.2 `itemTake` 的请求量给大无害

[LExecutor.java:540](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L540):

```java
int taken = Math.min(build.items.get(item), Math.min(amount, unit.maxAccepted(item)));
```

三重截断:源库存、请求量、单位容量。**所以要多少给多少,超了会被自动截断。**

### 3.3 传输冷却 `transferDelay = 1.5 秒`

`itemDrop` / `itemTake` / `payDrop` / `payTake` 共用 1.5 秒(90 帧)冷却。
`LogicAI.java:16`:`transferDelay = 60f * 1.5f`。

**后果**:对同一个建筑反复发指令,1.5 秒内只有第一条生效。
**所以原地"停一下再取"必须真的等**(`wait 1.6`),光发指令没用。

### 3.4 投料距离

`logicItemTransferRange + 建筑尺寸 × tileSize / 2`,**`logicItemTransferRange = 45px`**([Vars.java:125](Mindustry-Source/core/src/mindustry/Vars.java#L125))。

| 建筑 | 判定距离 |
|---|---|
| 超速穹顶(3×3) | 45 + 12 = **57px ≈ 7.1 格** |
| 核心(3×3) | 同上 |

### 3.5 `itemDrop @air <数量>` = 清空

```mlog
ucontrol itemDrop @air 999 0 0 0     # 把手上的物品直接扔掉
```

`@air` 走 `unit.clearItem()` 分支,不经过建筑判定。

### 3.6 ⭐ 用"货不对就倒掉"来换货

星辉一次只能带一种,所以要换货必须先清空。标准做法:

```mlog
select cfg lessThanEq ph si @phase-fabric @silicon   # 先定"该带哪种"
jump <下一个> equal fi cfg                            # 已经带对了,跳过
ucontrol itemDrop core 999 0 0 0                      # 带错了 → 丢进核心
```

**注意**:`@firstItem` 空手时是 `null`,所以 `fi != cfg` 在**空手时也成立**。
标准答案没判这一点(会白跑一次 `itemDrop`,无害);要严谨可以加 `jump <跳过> equal fi null`。

---

## 4. 超速穹顶(overdrive-dome)专章

### 4.1 消耗与效率

源码 [OverdriveProjector.java](Mindustry-Source/core/src/mindustry/world/blocks/defense/OverdriveProjector.java):

```java
overdriveDome = new OverdriveProjector("overdrive-dome"){{
    consumePower(10f);                                 // 10 电力
    range = 200f;                                      // 200px = 25 格
    speedBoost = 2.5f;                                 // +150%
    useTime = 300f;                                    // 5 秒一个消耗周期
    hasBoost = false;                                  // 没有 phaseFabric 加成
    consumeItems(with(Items.phaseFabric, 1, Items.silicon, 1));   // 每周期各 1 个
}};
```

### 4.2 ⭐ 效率判据:只要有 ≥1 个就满效率

`ConsumeItems.efficiency()`([:52](Mindustry-Source/core/src/mindustry/world/consumers/ConsumeItems.java#L52)):

```java
return build.consumeTriggerValid() || build.items.has(items, multiplier.get(build)) ? 1f : 0f;
```

**只有 0 和 1 两种结果——不是"够不够扣一次",而是"有没有"。**

> **这推翻了我原来的理解。** 我曾以为 `efficiency` 是部分效率(算余量、算续航天数),
> 并据此推算"单星辉跑不到 100 格"。**实际上只要有 1 硅 + 1 相织布就是满效率,不需要我算的缓冲。**

### 4.3 扣料是周期性的,不是每帧

[:117](Mindustry-Source/core/src/mindustry/world/blocks/defense/OverdriveProjector.java#L117):

```java
if(useProgress >= useTime){ consume(); useProgress %= useTime; }
```

**每 5 秒扣 1 硅 + 1 相织布。**

### 4.4 关键参数速查

| 项 | 值 |
|---|---|
| 电力 | 10/s |
| 消耗 | 1 硅 + 1 相织布 / 5 秒 |
| 物品容量 | 10(合计) |
| 范围 | 200px = 25 格 |
| 加速 | +150%(`speedBoost = 2.5f`) |
| 接受投料 | ✅ `acceptsItems = true`(由 `ConsumeItems` 自动设置,[:25](Mindustry-Source/core/src/mindustry/world/consumers/ConsumeItems.java#L25)) |

---

## 5. `ulocate` 完整参数(源码 + 文档双核对)

**9 个参数,顺序固定,导出时永远全部写出**([LStatements.java:1195](Mindustry-Source/core/src/mindustry/logic/LStatements.java#L1195),文档 L1331):

```
ulocate <locate> <flag> <enemy> <ore> <outX> <outY> <outFound> <outBuild>
```

| 位置 | 参数 | 类型 | 取值 / 说明 |
|---|---|---|---|
| p1 | `locate` | LLocate | `building` / `ore` / `spawn` / `damaged` |
| p2 | `flag` | BlockFlag | `core` `storage` `generator` `turret` `factory` `repair` `battery` `reactor` `drill` `shield` |
| p3 | `enemy` | 数值 | **`1`/`true` = 搜敌方;`0`/`false` = 搜己方**。⚠️ 编辑器默认 `true`! |
| p4 | `ore` | Content | **只有 `locate ore` 才读**,其他模式填合法矿物即可(`@copper`) |
| p5 | `outX` | 输出 | 目标 **X 坐标(tile)**,`World.conv` 后是**左上角** |
| p6 | `outY` | 输出 | 目标 **Y 坐标(tile)** |
| p7 | `outFound` | 输出 | `1` = 找到,`0` = 未找到 |
| p8 | `outBuild` | 输出 | ⭐ **建筑引用**。仅 `building`/`damaged` 模式有效 |

### 5.1 ⭐ 第 8 参必须接住

```mlog
ulocate building core 0 @copper bx by 0 core
                                        ↑
                              这里输出建筑引用到 core 变量
```

**填 `0` = 丢弃建筑引用**,后面就没法用 `core` 取货/投料。**这是我犯过的错(见 §1.2)。**

### 5.2 距离规则(反直觉,重要)

| 模式 | 范围限制 |
|---|---|
| `building` + `enemy=0`(友方) | **无范围限制**,始终返回最近的符合条件的友方建筑 |
| `building` + `enemy=1`(敌方) | `outX/outY/outFound` 始终输出;但 **`outBuild` 只在 `max(unit.range(), 27.5格)` 内才输出**,否则为 `null` |
| `ore` | 返回最近指定矿脉 |
| `spawn` | 返回最近的**敌方**出生点 |
| `damaged` | 返回最近的**己方**受损建筑 |

**推论**:无线运输用 `building core 0` / `building storage 0`(搜己方)→ **不受距离限制**,100 格外也能拿到引用。

### 5.3 三条容易踩的

1. **第 2 参不能填 `0`** —— `ore`/`spawn`/`damaged` 模式下 `flag` 虽不参与运算,但解析时仍会取值,填 `0` 会变成**灰色积木**(文档 L1341/L1349)
2. **40 tick 缓存** —— 重复执行相同参数的 `ulocate` 返回缓存结果。参数不同则缓存互不干扰
3. **会刷新 10 秒控制计时器** —— 和 `uradar` 不同(`uradar` **不刷新**,见 §6.4)

### 5.4 标准写法

```mlog
ulocate building core 0 @copper bx by 0 core       # 找己方核心,接住引用
ulocate building storage 0 @copper 0 0 f st        # 找己方仓库
```

---

## 6. ⭐ `move` vs `approach`:取货点必须用 `move`

### 6.1 我原来的错误

我以为 `ucontrol move x y <半径>` 的第三个参数是半径,写出了 `ucontrol move core 8 0 0 0`。

**实际上 `move` 不读第 3 个参数**([LExecutor.java:358](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L358),文档 L405):

```java
case move, stop, approach, pathfind -> {
    ai.control = type;
    ai.moveX = x1;
    ai.moveY = y1;
    if(type == LUnitControl.approach){        // ← 只有 approach 读半径
        ai.moveRad = d1;
    }
    ...
}
```

### 6.2 两者的精确差异(文档 L479–L487)

| 特性 | `move x y 0 0 0` | `approach x y radius 0 0` |
|---|---|---|
| 停止位置 | **精确到目标点** | 距离目标 `radius` 内 |
| 到达精度 | **1 格** | 7 格 |
| 减速范围 | 30 格 | 7 格 |
| 实际停止距离 | 目标点 | **`radius - 7`**(源码 `moveRad - 7f`) |
| 适用 | 需要精确到达 | 靠近但不必到达 |

**另外**:`move` 只设置目标就立即返回,**不等待到达**(文档 L431)。

### 6.3 ⭐ 为什么取货必须用 `move`(Iliary 的解释)

**无线运输要优先从贴核仓库取货。**

`itemTake` / `itemDrop` 的判定半径是 `45px + 建筑尺寸×4`,**不同建筑尺寸不同**:

| 建筑 | 判定半径 |
|---|---|
| 核心(3×3) | 45 + 12 = 57px ≈ **7.1 格** |
| 仓库(3×3) | 同上 |
| 小型建筑(1×1) | 45 + 4 = 49px ≈ **6.1 格** |

**如果用 `approach` + 较大半径,单位停在半径外,可能够不到仓库。**
而 `itemTake` 不满足 `within` 时**只是静默跳过、不报错**([LExecutor.java:539](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L539)),
所以表现为"单位空手跑一趟"——极难排查。

**→ 取货点一律用 `move`,飞到精确坐标,保证进范围。**

```mlog
ucontrol move cx cy 0 0 0        # ✅ 精确飞到核心坐标
ucontrol move cx cy 10 0 0       # ❌ 停在 10 格外,可能够不到;而且 move 不读这个 10
```

### 6.4 投料点

投料可以 `move` 直飞中心 —— `itemDrop` 判定半径(≥6 格)远大于 `move` 的停止精度(1 格),飞中心必然进范围。

> **原版 `鱼冰无线超(单位避让版)` 里的 `ucontrol move bx by 3 0 0` / 最简版 `5`,那两个数字在 `move` 下都是无效占位,不是半径。**

### 6.5 `uradar` 不刷新控制计时器(补)

| 指令 | 刷新 10 秒 `controlTimer` |
|---|---|
| `ucontrol *`(除 uradar) | ✅ |
| `ulocate` | ✅ |
| **`uradar`** | ❌ **不刷新** |

**后果**:只用 `uradar` 索敌、不再下发任何 `ucontrol` 的话,单位 10 秒后会自动脱离控制。
**修正**:循环里至少留一条实质性 `ucontrol`(哪怕 `ucontrol idle`)。

---

## 7. 单位归属判定(标准片段)

**不要用 `@controlled` 判断"是不是我在控制"** —— 它返回 1/2/3/0,**所有逻辑控制都是 1,无法区分是哪个处理器**。

**正确写法**(来自 `GetBlock点阵钍反替换防炸房逻辑1.2.msch` L0–L7):

```mlog
sensor d @unit @dead
jump <重新绑定> strictEqual d 1
sensor c @unit @controller
jump <ok> strictEqual c @this        # 控制器是本处理器
jump <ok> strictEqual c @unit        # 默认 AI(控制器指向自身)
<重新绑定>:
ubind @flare
set myUnit @unit
<ok>:
```

**三个要点**:
1. `@unit` 死了/为空 → 重新绑
2. `c == @this` → 是我控的
3. `c == @unit` → 默认 AI,可以接管
4. 其他(玩家、别的逻辑)→ 放弃,重绑

`@controller` **没有出现在 sensor 属性总表**里,属于能用但未文档化。

---

## 8. 已被推翻的旧结论(留档,防止我再犯)

| 我曾断言 | 实际情况 | 依据 |
|---|---|---|
| `op abs` / `op floor` 等"多写一个参数是错误" | **多出的 token 不参与执行,行为完全正常** | LParser 按各语句声明的参数个数读取 |
| `@pingX` 返回 NaN,判 null 是死判断 | **NaN 在本环境统一返回 null**,判断有效 | Iliary 确认 |
| 超速穹顶 `efficiency` 是部分效率,要算余量 | **只有 0/1**,有 ≥1 个就满效率 | [ConsumeItems.java:52](Mindustry-Source/core/src/mindustry/world/consumers/ConsumeItems.java#L52) |
| 单星辉跑不了 100 格 | **实测能跑**,我的前提就是错的 | Iliary 确认 |
| 星辉能带 10 硅 + 10 相织布 | **单堆叠,只能带一种 10 个** | [UnitComp.java:267](Mindustry-Source/core/src/mindustry/entities/comp/UnitComp.java#L267) |
| `ucontrol move` 第 3 参是半径 | **`move` 不读第 3 参**,只有 `approach` 读 | [LExecutor.java:362](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L362) |
| `large-logic-display` → `logic1` | **永远取最后一段 → `display1`** | Iliary 确认 |
| **`core` 是内置关键字** | **是变量,必须由 `ulocate` 第 8 参赋值** | 源码无 `core` 内置;`ulocate outBuild` 输出 |
| `ulocate` 第 8 参可以填 `0` | **填 0 就丢掉了建筑引用**,后面没法取货/投料 | 同上 |
| 归属检查写完就能控制单位 | **必须先 `ubind`**,否则 `@unit` 是 `null`,所有 `ucontrol` 静默无效 | [LExecutor.java:323](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L323) 要求 `exec.unit.obj() == unit` |

**共同教训**:我倾向于用"通用编程直觉 + 理论计算"去补我不知道的东西,然后当成结论。
**以后遇到不确定的,要么翻源码,要么查 `Logic-Docs`,要么问,不要推算。**

### 8.1 反面案例:我为什么会漏掉 `ulocate` 的输出

我写 `ulocate building core 0 @copper cx cy 0 core` 时,把第 7 参(`outFound`)填了 `0`、
第 8 参(`outBuild`)也填了 `0` —— **因为我当时以为 `core` 是关键字,不需要变量接**。

正确写法是**至少给 `outBuild` 一个变量名**:

```mlog
ulocate building core 0 @copper cx cy found core
```

**教训**:一个指令有多个输出参数时,**不要把某个输出直接写 `0` 当占位**——
先确认它是不是你后面要用的东西。

---

## 9. 排版与注释约定

- **`print` 是 mlog 唯一的注释机制**(`#` 注释导入时被 `LParser` 清除)
- **`print` 本身不输出**,只往缓冲区追加;必须 `printflush` 才显示([LExecutor.java:1054](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L1054) / [:1171](Mindustry-Source/core/src/mindustry/logic/LExecutor.java#L1171))
- **`printflush null`** = 丢弃缓冲区(目标不是消息块 → 不显示,但缓冲区被清空)
- 所以:**要游戏内可见** → `print` + `printflush message1`;**只备忘** → 放 `end` 之后

变量命名:Iliary 主流用 `.` 分隔(`crush.damage(/tiles*s)`),也有中文名和 `?` 后缀(`crushAir?`)。

---

## 10. 附录 A:sensor 属性总表(源码 `LAccess.java` 全文)

**这就是权威清单** —— [LAccess.java](Mindustry-Source/core/src/mindustry/logic/LAccess.java) 是 `sensor` 能读的全部属性。
`@名字` 就是枚举名原样(小驼峰),**所以 `@totalItems`、`@firstItem`、`@itemCapacity` 是准确的,不用猜。**

### 10.1 纯读取属性(`senseable`,无参数)

| 行 | 属性 | 行 | 属性 |
|---|---|---|---|
| 7 | `@totalItems` | 35 | `@shootX` |
| 8 | `@firstItem` | 36 | `@shootY` |
| 9 | `@totalLiquids` | 37 | `@cameraX` |
| 10 | `@totalPower` | 38 | `@cameraY` |
| 11 | `@itemCapacity` | 39 | `@cameraWidth` |
| 12 | `@liquidCapacity` | 40 | `@cameraHeight` |
| 13 | `@powerCapacity` | 41 | `@displayWidth` |
| 14 | `@powerNetStored` | 42 | `@displayHeight` |
| 15 | `@powerNetCapacity` | 43 | `@bufferSize` |
| 16 | `@powerNetIn` | 44 | `@operations` |
| 17 | `@powerNetOut` | 45 | `@size` |
| 18 | `@ammo` | 46 | `@solid` |
| 19 | `@ammoCapacity` | 47 | `@dead` |
| 20 | `@currentAmmoType` | 48 | `@range` |
| 21 | `@memoryCapacity` | 49 | `@shooting` |
| 22 | `@health` | 50 | `@boosting` |
| 23 | `@maxHealth` | 51 | `@mineX` |
| 24 | `@heat` | 52 | `@mineY` |
| 25 | `@shield` | 53 | `@mining` |
| 26 | `@armor` | 54 | `@buildX` |
| 27 | `@efficiency` | 55 | `@buildY` |
| 28 | `@progress` | 56 | `@pingX` |
| 29 | `@timescale` | 57 | `@pingY` |
| 30 | `@rotation` | 58 | `@pingText` |
| 31 | `@x` | 59 | `@building` |
| 32 | `@y` | 60 | `@breaking` |
| 33 | `@velocityX` | 61 | `@speed` |
| 34 | `@velocityY` | 62 | `@team` |

继续:`@type`(63)、`@flag`(64)、`@flying`(65)、`@controlled`(66)、`@controller`(67)、`@name`(68)、
`@payloadCount`(69)、`@payloadType`(70)、`@totalPayload`(71)、`@payloadCapacity`(72)、
`@maxUnits`(73)、`@id`(74)、`@selectedBlock`(75)、`@selectedRotation`(76)、`@bulletLifetime`(77)、`@bulletTime`(78)

### 10.2 带参数 / 可写的属性

**`LAccess.java:80-85`** —— 这些参数个数 > 0,所以**既是控制指令,也能被 `control` 使用**:

```java
enabled("to"),                    // control enabled <建筑> <0/1>
shoot("x", "y", "shoot"),         // control shoot
shootp(true, "unit", "shoot"),    // control shootp
config(true, "to"),               // control config
color("to")                       // control color
```

### 10.3 ⭐ `setprop` 能改哪些属性(权威清单)

**`LAccess.java:94`** —— 这个数组就是 `setprop` 的**全部合法目标**:

```java
settable = {x, y, velocityX, velocityY, rotation, speed, armor,
            health, shield, team, flag, totalPower,
            payloadType, bulletTime, bulletLifetime};
```

| 能 setprop 的 | 用途举例 |
|---|---|
| `@x` `@y` | **远程移动单位**(MCV 移动核心就靠这个) |
| `@velocityX` `@velocityY` | 直接给速度 |
| `@rotation` | 改朝向 |
| `@speed` | **改移动速度**(MCV 的 `MCV.speed`) |
| `@armor` `@health` `@shield` | 改生存属性 |
| `@team` | **改队伍**(`换队伍器`) |
| `@flag` | 远程改单位标记 |
| `@totalPower` | 改电力 |
| `@payloadType` `@bulletTime` `@bulletLifetime` | 载荷/子弹 |

> **实用推论**:`setprop @x/@y` 是世界上处理器"移动任意单位"的唯一手段
> —— 普通处理器只能 `ucontrol move` 动自己 `ubind` 的那个单位。

### 10.4 我笔记里之前提到的名字,现在有出处了

| 名字 | 出处行 | 备注 |
|---|---|---|
| `@heat` | LAccess:24 | 原版就有 |
| `@efficiency` | LAccess:27 | **0 或 1**,不是部分效率 |
| `@progress` | LAccess:28 | 生产/重构进度 |
| `@timescale` | LAccess:29 | |
| `@displayWidth` / `@displayHeight` | LAccess:41/42 | 显示屏尺寸 |
| `@operations` | LAccess:44 | |
| `@totalItems` | LAccess:7 | **合计**,不是分类型 |
| `@derelict` | 不在 LAccess | **是队伍名**(`setblock` 的 team 参数),不是 sensor 属性 |

---

## 11. 待确认清单

- [ ] 超速穹顶以外,**贴核仓库(storage)离穹顶多远**?这决定"优先从仓库取"的实际路径
- [ ] 多个星辉时,**flag 分配约定**是什么(语料里见过 `11011`、`9001..9005`、坐标式)
- [ ] 内存索引有没有**分配表**规范

---

## 12. 附:`ulocate` 之后标准答案的完整数据流(背下来)

```mlog
# ① 拿到核心引用(第 8 参接到变量里)
ulocate building core 0 @copper bx by 0 core

# ② 用引用取货/投料 —— 不需要坐标
ucontrol itemTake core @silicon 10 0 0
ucontrol itemDrop core 999 0 0 0

# ③ 需要"飞过去"才用坐标
ucontrol move bx by 0 0 0
```

| 需要什么 | 用哪个 |
|---|---|
| 取货 / 投料 | **建筑引用**(`ulocate` 第 8 参的输出变量) |
| 飞过去 | `ulocate` 的 outX/outY(左上角格子) |
| 建筑中心 | `sensor <建筑> @x` / `@y` |

---

## 13. 附录 B:全部 86 个命令的格式索引

**来源**:`Logic-Docs-v1.1.0` 的 86 个命令章节(每章一个命令),已脚本化提取到 [tools/cmd_index.json](tools/cmd_index.json)。
**格式说明**:`<...>` 是占位符;导出时**每条指令的参数个数固定,没用到的位置填 `0`**。

### 13.1 单位控制(23 条)

| 命令 | 格式 |
|---|---|
| `ubind` | `ubind <type>` |
| `ucontrol idle` | `ucontrol idle 0 0 0 0 0` |
| `ucontrol stop` | `ucontrol stop 0 0 0 0 0` |
| `ucontrol move` | `ucontrol move x y 0 0 0` |
| `ucontrol approach` | `ucontrol approach x y radius 0 0` |
| `ucontrol pathfind` | `ucontrol pathfind x y 0 0 0` |
| `ucontrol autoPathfind` | `ucontrol autoPathfind 0 0 0 0 0` |
| `ucontrol boost` | `ucontrol boost enable 0 0 0 0` |
| `ucontrol target` | `ucontrol target x y shoot 0 0` |
| `ucontrol targetp` | `ucontrol targetp unit shoot 0 0 0` |
| `ucontrol itemDrop` | `ucontrol itemDrop to amount 0 0 0` |
| `ucontrol itemTake` | `ucontrol itemTake from item amount 0 0` |
| `ucontrol payDrop` | `ucontrol payDrop 0 0 0 0 0` |
| `ucontrol payTake` | `ucontrol payTake takeUnits 0 0 0 0` |
| `ucontrol payEnter` | `ucontrol payEnter 0 0 0 0 0` |
| `ucontrol mine` | `ucontrol mine x y 0 0 0` |
| `ucontrol flag` | `ucontrol flag value 0 0 0 0` |
| `ucontrol build` | `ucontrol build x y block rotation config` |
| `ucontrol deconstruct` | `ucontrol deconstruct x y 0 0 0` |
| `ucontrol getBlock` | `ucontrol getBlock x y type building floor` |
| `ucontrol within` | `ucontrol within x y radius result 0` |
| `ucontrol unbind` | `ucontrol unbind 0 0 0 0 0` |
| `uradar` | `uradar target1 target2 target3 sort 0 order output` |
| `ulocate` | `ulocate locate flag enemy ore outX outY outFound outBuild` |

> 注意 `uradar` 的参数:第 5 位是**固定占位 `0`**(原版就是 `0 0 0 0 0` 里的那个),第 6 位才是 `order`。

### 13.2 流程控制(5 条)

| 命令 | 格式 |
|---|---|
| `noop` | `noop` |
| `wait` | `wait <value>` (秒) |
| `stop` | `stop` |
| `end` | `end` |
| `jump` | `jump <dest> <op> <value> <compare>` |

### 13.3 变量运算(6 条)

| 命令 | 格式 |
|---|---|
| `set` | `set <result> <value>` |
| `op` | `op <op> <result> <a> <b>` |
| `select` | `select <result> <op> <comp0> <comp1> <a> <b>` |
| `lookup` | `lookup <type> <result> <id>` |
| `packcolor` | `packcolor <result> <r> <g> <b> <a>` |
| `unpackcolor` | `unpackcolor <r> <g> <b> <a> <value>` |

### 13.4 内存与输出(6 条)

| 命令 | 格式 |
|---|---|
| `read` | `read <result> <cell> <index>` |
| `write` | `write <value> <cell> <index>` |
| `draw` | 多子命令(clear/color/line/rect/poly/print/…),见文档 §703 |
| `print` | `print <value>` |
| `printchar` | `printchar <code>` |
| `format` | `format <template>` |

### 13.5 建筑交互(6 条)

| 命令 | 格式 |
|---|---|
| `getlink` | `getlink <output> <index>` |
| `control` | `control <type> <building> <p1> <p2> <p3> <p4>` |
| `radar` | `radar <target1> <target2> <target3> <sort> <building> <order> <output>` |
| `sensor` | `sensor <output> <from> <type>` |
| `drawflush` | `drawflush <building>` |
| `printflush` | `printflush <building>` |

### 13.6 世界处理器专属(26 条,privileged)

| 命令 | 格式 |
|---|---|
| `setrate` | `setrate <amount>` |
| `getblock` | **`getblock <result> <x> <y> <layer>`** ← 注意顺序! |
| `setblock` | **`setblock <x> <y> <block> <team> <rotation> <layer>`** |
| `spawn` | `spawn <type> <x> <y> <rotation> <team> <result> <effect>` |
| `bullet` | `bullet <result> <from> <index> <x> <y> <rotation> <team> <owner> …` |
| `status` | `status <apply\|clear> <effect> <unit> <duration>` |
| `weathersense` | `weathersense <weather> <result>` |
| `weatherset` | `weatherset <weather> <state>` |
| `spawnwave` | `spawnwave <natural> <x> <y>` |
| `setrule` | `setrule <rule> <value> <p1> <p2> <p3> <p4>` |
| `message` | `message <type> <duration> <outSuccess>` |
| `cutscene` | `cutscene <action> <p1> <p2> <p3> <p4>` |
| `effect` | `effect <type> <x> <y> <sizerot> <color> <data>` |
| `explosion` | `explosion <team> <x> <y> <radius> <damage> <air> <ground> <pierce>` |
| `fetch` | `fetch <type> <result> <team> <index> <extra>` |
| `getflag` | `getflag <result> <flag>` |
| `setflag` | `setflag <flag> <value>` |
| `setprop` | `setprop <type> <of> <value>` |
| `playsound` | `playsound <positional> <id> <volume> <pitch> <pan/x> <y> <limit>` |
| `playmusic` | `playmusic <name> <interrupt>` |
| `setmarker` | `setmarker <type> <id> <p1> <p2> <p3>` |
| `makemarker` | `makemarker <type> <id> <x> <y> <replace>` |
| `localeprint` | `localeprint <value>` |
| `sync` | `sync <variable>` |
| `query` | `query <shape> <type> <team> <x> <y> <w> <h>` |
| `clientdata` | `clientdata <channel> <value> <reliable>` |

> ⚠️ **`getblock` 和 `ucontrol getBlock` 参数顺序不同**:
> - `getblock <result> <x> <y> <layer>` —— 输出在**第 1 位**
> - `ucontrol getBlock x y type building floor` —— 输出在**后 3 位**

---

## 14. 生成蓝图工具 `tools/mschgen.py`

**把 mlog 源码打包成可直接拖进游戏的 `.msch`。** 格式已用 429 个真实蓝图做**逐字节往返验证**。

```bash
# 从文件生成,带链接
python tools/mschgen.py 逻辑.mlog -o 输出.msch \
    --name "蓝图名" --description "说明" --label "[cyan]蓝标签" \
    --block micro-processor --at 0,0 --link dome1@3,1

# 直接写代码
python tools/mschgen.py --code "ubind @flare" -o out.msch

# 往返验证(改完工具必跑)
python tools/mschgen.py --selftest
```

| 参数 | 说明 |
|---|---|
| `--block` | `micro-processor` / `logic-processor` / `hyper-processor` / `world-processor` |
| `--at x,y` | 处理器在蓝图里的格子坐标 |
| `--link name@dx,dy` | **可重复**。`dx,dy` 是**相对处理器的偏移**,不是绝对坐标 |
| `--name` / `--description` / `--label` | 蓝图的 name/description/labels 标签 |

**验证状态**:`--selftest` → **429/429 逻辑逐字节往返一致**。

**两个已知限制**:

1. **链接目标建筑不在蓝图里** —— 链接只是坐标+名字,玩家贴下去后要自己在那个位置放穹顶/仓库。
   工具的 `size` 会把链接位置也算进包围盒,免得看起来是个孤零零的处理器。
2. **复杂方块的 config 不能重建**(如 `power-node` 的链接列表) —— 但我们只生成处理器蓝图,不影响。

### 14.1 生成代码前必查的清单

1. **`ubind` 了吗?**(§0.5) —— 否则 `@unit` 为 null,所有控制无效
2. **`ulocate` 的输出接住了吗?**(§1.2/§5.1) —— 第 8 参别写 `0`
3. **取货点用 `move` 了吗?**(§6) —— `approach` 可能够不到仓库
4. **`jump` 目标行号对了吗?** —— 蓝图存的是行号,加/删一行全盘偏移,生成前逐条数一遍
5. **`end` 用对地方了吗?**(§8 第 4 条) —— `end` 是**跳回开头**,不能用来"结束一个分支后继续往下"

---


## 15. 静态检查工具 `tools/mlogcheck.py`

**不是模拟器**,是在生成蓝图前抓"我犯过的那类错"。已经把两个真实 bug 的判据固化进去了。

```bash
# 直接查 .mlog
python tools/mlogcheck.py 逻辑.mlog

# 查蓝图(会从蓝图里读出链接名,不会误报 dome1/message1)
python tools/mlogcheck.py --blueprint out/无线超.msch
```

| 等级 | 含义 |
|---|---|
| `ERR` | 确定有问题 |
| `SUSPECT` | 强烈怀疑(目前只用于 `@dead` 反用) |
| `WARN` | 可能有风险 |
| `INFO` | 提示 |

### 15.1 实测有效的检查

| 检查 | 抓到过什么 |
|---|---|
| **`@dead` 反用** | ✅ **实际抓出我写错的 `jump 0 notEqual d 1`** |
| `jump` 目标越界 | 结构性错误 |
| `op` 参数个数 | 全语料 567 处 |
| `ulocate` 第 2 参填 `0` | 会让整条指令变灰积木 |
| `ulocate` 丢 `outBuild` 却要用它取货 | 我犯过的错 |
| 丢了 `outX/outY` 却又 `move` 过去 | 我犯过的错 |
| 完全没有 `ubind` 就用 `ucontrol` | 我犯过的错 |
| 变量**全程序从未被赋值** | 拼写错误类 |

### 15.2 ⚠️ 已知局限(实测约 2 个误报/块)

在你**成熟的蓝图**上跑,`ERR` 约 2 个/块 —— **基本都是误报**。原因:

- mlog **没有声明**,`@counter` 相对跳转、跳转表、循环内初始化都让静态分析跟不上
- 某些内容名/链接名没有数字后缀(如 `source`、`arc`),无法和变量区分
- `draw` 的各种子命令参数形态不一

**结论:把它当"提示器"而不是"编译器"。** `SUSPECT` 级别的输出可信度最高,
`ERR` 里的"变量从未赋值"要自己判断是否真的是笔误。

> **不要为了让它全绿去改正确的代码。** 这条同样适用:工具是辅助,Iliary 的实测才是标准。

### 15.3 评估过的外部项目(结论:不适用)

按建议爬了一圈,记录结论避免重复调研:

| 项目 | 语言 | 为什么不用 |
|---|---|---|
| [cardillan/mindcode](https://github.com/cardillan/mindcode) | Java | 168★,高质量**编译器**(ML 风格 → mlog),不是模拟器;需 JDK,且无独立 content ID 表 |
| [mlogjs/mlogjs](https://github.com/mlogjs/mlogjs) | TS | JS→mlog **编译器**;npm 上有,但只做编译不做执行 |
| [BalaM314/mlogx](https://github.com/BalaM314/mlogx) | TS | mlog 转译器 |
| [Vilsol/go-mlog](https://github.com/Vilsol/go-mlog) | Go | Go→mlog 编译器 + **WIP 反编译器**;本机有 Go,但目标是生成不是验证 |
| [bend-n/mindus](https://github.com/bend-n/mindus) | **Rust** | ⭐ 唯一"逻辑执行 + 蓝图解析"方向对口的,但要装 Rust 工具链 |
| [KosmosPrime/plandustry](https://github.com/KosmosPrime/plandustry) | Rust | **已归档**(README 还自称 "the" 工具——就是 mindus 的**父项目**)。详见 §15.4 |

### 15.4 `plandustry` 到底是什么(核实结论)

- **Rust 写的命令行蓝图编辑器**,两个子命令:`print`(打印名字/标签/造价/方块)和 `edit`(交互式增删改)
- **已归档**,且 **0 个 release**(无预编译二进制,只能自己编译 Rust)
- 它有**完整的方块数据库**:`src/block/content.rs` + 按类分的 `base/defense/transport/…`
  —— 每个方块带**尺寸和造价**,`overdrive-dome`、`world-processor` 都收录了
- **但它是「按名字」索引的**:**[src/registry.rs](https://github.com/KosmosPrime/plandustry/blob/master/src/registry.rs) 只有 `by_name: HashMap<&str, &E>`,完全没有数字 ID 字段**

> **⭐ 这从第二个独立实现反证了 content ID 的结论**:
> 一个能完整读写蓝图、重构造价的项目,**根本不需要 content ID** ——
> 因为蓝图按名字存方块,**ID 是游戏加载时按自己的注册顺序重新解析的**。
> **所以"外部工具提供 content ID"这条路在原理上就不成立。**

- 名字来源是**硬编码枚举**(`OverdriveDome => "overdrive-dome"`),不跟随游戏版本
- **不做 mlog 执行**:`src/block/logic.rs` 里有 `ProcessorLogic` / `ProcessorState` / `ProcessorLink`
  和 `CodeError`,说明它能**解析和往返逻辑代码**,但**没有 mlog 解释器** —— 它和我的工具做的是同一层的事
- 对**你的环境没用**:不认识 MindustryX 的新方块,也没有 ID

**`mindus` 是它的 fork**,README 说明分工:
「`mindus/` 目录做蓝图与地图的渲染/反序列化,`lemu/` 目录做 **mlog 执行**」
—— **真正能跑 mlog 的部分叫 `lemu`**。如果将来要试本地执行,应该直接看 `lemu`,而不是整个 mindus。

### 15.5 想要方块 ID 的办法(在游戏里查)

工具给不出你这套环境的 ID,但**用一个处理器就能把整张表读出来**:

```mlog
set i 0
loop:
lookup block b i            # 按 ID 取方块类型
jump end equal b null       # 越界返回 null → 停止
sensor nm b @name           # 读它的名字
print i
print " = "
print nm
print "\n"
printflush message1
op add i i 1
jump loop always 0 false
end:
```

**丢进世界处理器(或普通处理器)、接一个消息块,就能看到 `<ID> = <方块名>` 的完整清单。**

要单个 ID 更简单:

```mlog
sensor id dome1 @id
print id
printflush message1
```

### 15.6 ⭐ 两个 wiki 和 MindustryX 源码(实测结论)

**① 官方英文 wiki:`mindustrygame.github.io/wiki/`**

- 版本:160.5
- **内容页 URL 的 slug 带内容 ID**:`content/blocks/crafting/181-graphite-press/`
- mkdocs 有搜索索引,**一次就能抓全**:`search/search_index.json`
- 我写了 [tools/fetch_wiki_ids.py](tools/fetch_wiki_ids.py) 抓下来 → [tools/wiki_block_ids.json](tools/wiki_block_ids.json)
  **422 个方块,ID 1–446**

关键 ID:

| ID | 方块 |
|---|---|
| **248** | `overdrive-dome` |
| 247 | `overdrive-projector` |
| 426–429 | launch-pad / advanced-launch-pad / landing-pad / interplanetary-accelerator |
| 430 / 431 | message / switch |
| 432–438 | micro / logic / hyper-processor、memory-cell / bank、logic-display / large-logic-display |
| **439–446** | `tile-logic-display`、**`canvas`**、`large-canvas`、`reinforced-message`、**`world-processor`**、**`world-cell`**、**`world-message`**、**`world-switch`** |

> ⚠️ **这份表里混进了 MindustryX 内容**(`world-cell`/`world-message`/`world-switch`/`canvas` 都不是原版)。
> 说明**写 wiki 的人也在用 mod**,所以这张表**只对"和 wiki 作者相同的环境"有效**。

**② MDT 中文 wiki:[mdtwiki.top](https://mdtwiki.top/)** —— 你指的那个

- 版本标的是 **v159.7**(和你 159.1 最接近)
- 有 [隐藏建筑](https://mdtwiki.top/index.php?title=%E9%9A%90%E8%97%8F)、[逻辑](https://mdtwiki.top/index.php?title=%E9%80%BB%E8%BE%91) 等专门页
- 首页列的"**MindustryX官方文档**"指向飞书 `my.feishu.cn/wiki/MofAwk3A2iRTzBk7XBwc9EF6nQb`
  —— **需要登录,抓不到**(重定向到 accounts.feishu.cn)
- 还列了实用工具:**[图片转逻辑工具](https://buibiu.github.io/imageToMLogicPage/)**、蓝图档案馆、资源站

**③ MindustryX 源码:[TinyLake/MindustryX](https://github.com/TinyLake/MindustryX)**(338★,Java)

- 它是**补丁型 mod**:`patches/arc/` + `patches/client/`(81 个补丁)逐条改 Arc 和 Mindustry 源码
- 和逻辑相关的补丁:

| 补丁 | 作用 |
|---|---|
| `0038-FC-LogicExt-limitUpdate` | 逻辑更新限流 |
| `0039-FC-LogicExt-terrainSchematic` | 地形蓝图 |
| `0040-FC-LogicExt-worldCreator-allUnlocked` | 世界创建器全解锁 |
| `0046-UI-ARC-logic-Support` | **逻辑编辑器 UI 增强**(注释切换、JUMP 跳转按钮)——**不是语法扩展** |
| `0064-FC-paste-logicCode-from-schematic` | 从蓝图粘贴逻辑代码 |
| `0069-HC-LogicExt-noUpdatePlayerMovement` | 不更新玩家移动 |

### 15.7 ⭐⭐ 结论:content ID 可以**从源码推导**,已交叉验证

**结论:`overdrive-dome` 的 `Content.id` = 248。两个独立来源一致。**

#### 完整链条(源码级)

1. **ID 是构造顺序号** —— [Content.java:21](../../Mindustry-Source/core/src/mindustry/ctype/Content.java#L21)
   ```java
   this.id = (short)Vars.content.getBy(getContentType()).size;
   ```
2. **原版先构造,mod 后追加** —— [ContentLoader.java:57-81](../../Mindustry-Source/core/src/mindustry/core/ContentLoader.java#L57)
   ```java
   public void createBaseContent(){ ... Blocks.load(); }   // ← 原版方块 ID 在此固定
   public void createModContent(){ mods.loadContent(); }   // ← mod 只能往后追加
   ```
3. **游戏自检 ID 必须连续递增** —— [ContentLoader.java:86-93](../../Mindustry-Source/core/src/mindustry/core/ContentLoader.java#L86)
   ```java
   if(id != i) throw new IllegalArgumentException("Out-of-order IDs for content ...");
   ```

> **⭐ 由 2+3 推出两条重要结论:**
> - **mod 加方块不会让原版方块的 ID 偏移** —— mod 内容只能追加在原版之后
> - **所以原版方块的 ID 是"版本函数",与你装什么 mod 无关**

#### 推导方法:数 `Blocks.load()` 里的构造顺序

[Blocks.java](Mindustry-Source/core/src/mindustry/content/Blocks.java) 的 `load()` 里,
每执行一次 `new XxxBlock("name")` 就占一个 ID。
工具:[tools/block_ids_from_source.py](tools/block_ids_from_source.py)

**⚠️ 两个容易漏掉的坑(我踩了):**

| 坑 | 代码 | 为什么漏 |
|---|---|---|
| **批量构造** | `for(int i=1;i<=Vars.maxBlockSize;i++) new ConstructBlock(i);` | 无变量名,名字是 `build1`..`build16`(`Vars.maxBlockSize = 16`) |
| **用内容对象构造** | `oreCopper = new OreBlock(Items.copper){{` | 参数是 `Items.copper` 而非字符串,名字是 `ore-copper` |

#### 交叉验证结果

| 方块 | 源码推导 | 官方 wiki |
|---|---|---|
| **`overdrive-dome`** | **248** | **248** ✅ |
| `overdrive-projector` | 247 | 247 ✅ |
| `ore-copper` | 167 | 167 ✅ |
| `spawn` | 1 | 1 ✅ |

**前 348 个方块偏移全部为 +0**(完全吻合)。之后出现 24 个缺口 —— 那是**版本差异**
(我的源码快照比 wiki 记录的 160.5 新),不影响穹顶这个靠前的方块。

#### 对"放方块"的实际意义

- **原版方块**:可直接用推导出的 ID(超速穹顶 248),**不受你的 mod 影响**
- **mod 方块**:ID 取决于 mod 加载顺序,**必须实测**

**所以"连穹顶一起放"是可以做到的。** 唯一待确认:你的 **159.1** 与我的快照在这 248 之前
有没有差异 —— 我做过检查:**没有系统性的重复计数**(`set` 去重正常)。
最快的验证仍是游戏内 `sensor id dome1 @id` 读一次。

---

### 15.8 ⭐ 方块坐标是「中心格」,不是左上角【生成器必须遵守】

**这是 Iliary 实测抓出的 bug:我按左上角放超速穹顶,结果和逻辑之间空了一格。**

**双重验证结论:Stile 里存的是方块的「中心格」。**

**① 源码** —— [Tile.java:255](../../Mindustry-Source/core/src/mindustry/world/Tile.java#L255)

```java
//set up multiblock
if(block.isMultiblock()){
    int offset = -(block.size - 1) / 2;      // 3×3 → -1
    ...
    int worldx = dx + offset + x;            // 以 (x,y) 为中心铺开
```

[Block.java:761](../../Mindustry-Source/core/src/mindustry/world/Block.java#L761) 同样:`sizeOffset = -((size - 1) / 2)`

**② 实证(决定性)** —— 拿 624 个真实蓝图,两种解释各算一遍方块重叠数:

| 解释 | 出现重叠的蓝图数 |
|---|---|
| 位置 = **角** | **11** ❌ |
| 位置 = **中心** | **0** ✅ |

**"中心"是唯一自洽的解释。**

#### 换算公式

一个尺寸 N 的方块,中心在 `(cx, cy)` 时:

```
占据范围:(cx - (N-1)/2, cy - (N-1)/2)  到  (cx - (N-1)/2 + N - 1, ...)
```

| 方块 | 尺寸 | 中心 → 占据 |
|---|---|---|
| 超速穹顶 | 3×3 | 中心 (4,2) → 占据 (3,1)–(5,3) |
| 大型逻辑显示器 | 6×6 | 中心 (x,y) → 占据 (x-2,y-2)–(x+3,y+3) |
| 处理器 | 1×1 | 中心 = 占据 |

#### 教训

**我当时是"读源码 + 凭直觉"得出"角"的**,而源码里 `offset`(`-(size-1)/2`)和 `sizeOffset` 写法相似、容易被当成"像素偏移"忽略掉。
**是 Iliary 在游戏里一眼看出来"空了一格",我才回去用真实蓝图做的实证。**

> **方法论:源码能读出"怎么实现的",但"坐标语义"这种约定,用真实数据做统计验证最可靠。**
> 具体做法:对同一个量提出两种假设,分别在全量语料上算"会不会出现不可能的情况"(这里是方块重叠),**哪个不产生矛盾就是哪个**。

### 15.9 结论:content ID 这条线的最终判定

**✅ 原版方块的 content ID 是可以确定的** —— 两条独立途径互相验证:

| 途径 | 做法 | 结果 |
|---|---|---|
| **源码推导** | 数 `Blocks.load()` 里的构造顺序 | `overdrive-dome` = 248 |
| **官方 wiki** | `mindustrygame.github.io/wiki/` 内容页 slug 带 ID | `overdrive-dome` = 248 |

**而且原版方块 ID 是"版本函数",与 mod 无关** —— 因为
[ContentLoader](../../Mindustry-Source/core/src/mindustry/core/ContentLoader.java#L57) 先 `createBaseContent()`、
后 `createModContent()`,且游戏自检 ID 必须连续递增,**mod 内容只能追加在原版之后**。

⚠️ **唯一残余风险是版本差异**:wiki 记的是 160.5,我的源码快照更新,你的游戏是 159.1。
若某版本在穹顶之前新增了原版方块,ID 会整体后移。
**验证办法(一次即可)**:游戏里 `sensor id dome1 @id` 读一下,是 248 就完全一致。

**❌ 拿不到的是"mod 方块"的 ID** —— 那取决于 mod 加载顺序。

**但这件事优先级不高**:蓝图本来就按**方块名**存方块,游戏加载时按名字重新解析。
**所以只生成处理器 = 完全不依赖任何 content ID。**
只有像"连穹顶一起放"这种**要把方块作为内容值写进 config** 时才需要 ID。

---

### 15.10 两个配套结论(从外部工具调研得到的)

**① 没有一个可用的 mlog 模拟器/执行器** —— 查过 8 个项目(§15.3),全是编译器/转译器,
唯一方向对口的 [bend-n/mindus](https://github.com/bend-n/mindus) 要装 Rust,且其执行部分在 `lemu/` 子目录。
**所以"本地跑一遍验证"走不通**,只能靠静态分析(§15.1)+ Iliary 实测。

**② 蓝图本身不存 content ID** —— `contentMap` 只列被 config 引用的那几个,
且游戏加载时**按方块名重新解析**。所以放原版方块**只要名字对**(§15.7),
真正需要 ID 的只有"把方块当内容值写进 config"的场景。

---

### 15.11 ⭐ 成本分析:`--cost`(可达性 + 最坏指令数)

**动机**:评估另一 AI 的 159 行租约程序时,我是**手写脚本**算的"死代码"和"最坏多少条指令"。
这两件事应该自动化 —— 而且**也能用来审我自己**。

```bash
python tools/mlog.py check 逻辑.mlog --cost
python tools/mlog.py check --msch 蓝图.msch --cost     # 直接查蓝图内的逻辑
```

输出四组信息:

| 字段 | 含义 |
|---|---|
| `statements` | 语句数,>1000 会**被静默截断**(`LExecutor.maxInstructions`) |
| `reachability` | 永远跑不到的语句(**死代码**) |
| `loop heads` | 循环起始行 + 推定圈数(`?` = 看不到常量边界) |
| `worst-case path` | 一次完整决策的最坏指令数 + 三档处理器的耗时 |

#### 关键语义(实现时踩的坑)

**① `end` 是回边,不是终止符**
`end` 把 `@counter` 设为程序长度,**等于回到第 0 条**。若当成终止符,所有循环体都会被误判成死代码。
真正的 sink 只有 `stop`。`jump -1` 不跳,只顺序下落。

**② 循环圈数靠"守卫里的常量"推定**
mlog 没有声明式循环边界,只能推断:

```
op   lessThan idx CONST              ← op 形式
jump <tgt> lessThan idx CONST        ← jump 形式(本项目代码用这个!)
```

**两种都要认**。只认 `op` 形式会漏掉全部循环。
边界不可见的循环(用 `idiv`/传感器算的)按一圈算**并给出警告**。

**③ 回到第 0 行的回边 = 主循环,只算一圈**
mlog 每 tick 重跑整个程序。若把这条回边也乘圈数,再与内部循环相乘,**结果会膨胀几个数量级**。

**④ 嵌套循环不能重复计费**(最容易错的一步)
走了三条错路,每次都实测出来了:

| 错误做法 | 症状 |
|---|---|
| 普通最长路 DP | 循环上有环,数学上无定义 |
| 只在回边乘圈数 | 头依赖 latch、latch 依赖头,**谁都长不大**,循环体只算 1 次 → 报 78 条(真值 ~2494) |
| 全局松弛传播 | 内层循环抬高其后再被外层乘一次 → 报 **643686** 条 |

**正确做法**:按 head **降序**处理循环(**内层先解**),每个循环只定价一次:

```
loop_cost(h) = min( bound(h) × (循环体内最坏前向路径), 1000 )
```

外层循环测量时,内层的 `loop_cost` 已算好,**只加一次**。

**⑤ `float('inf')` 当"未访问"哨兵会静默失效**
`dist[i] + step > dist[s]` 中若 `dist[s]` 是 `float('inf')`,比较**返回 False**,
于是永不松弛,**每个程序都报成本 1**。改用负数哨兵(`-1`)。

**⑥ 单循环成本要 clamp 到 1000**
1000 是每 tick 硬上限。不 clamp 时两个嵌套 ×80 循环报 80 万条 —— 算术上"可能",操作上无意义。

#### 实测校准

| 输入 | 手算 | 工具 |
|---|---|---|
| `out\other-ai.mlog`(159 行,3 个 ×80 循环) | ~2494 | **2001** |
| `out\无线超2.mlog`(32 行,无内循环) | 32 | **27** |
| 简单单循环 ×80 测试 | ~480 | **481** |
| 嵌套 ×4/×5 测试 | ~50 | **51** |

**误差方向偏保守**,量级可信。**批量冒烟:4151 个真实逻辑块,0 失败。**

#### 用它审出来的真实问题

**审我自己的 `out\无线超2.mlog` 报了 6 条 UNREACHABLE**:

```
L26 sensor bx dome1 @x
L27 sensor by dome1 @y
L28 jump 0 strictEqual by null
L29 ucontrol move bx by 0 0 0
L30 ucontrol itemDrop dome1 999 0 0 0
L31 jump 0 always 0 false
```

原因是 L25 是 `end`,且**全程序没有任何 jump 指向 26** ⇒ 这段尾码永远不执行
(程序实际靠 `end` 重启去跑下半段)。
**教训:给用户写逻辑要删掉 `end` 之后的残留。**

### 15.12 ⭐ 指令预算:一条语句 = 一条指令,`jump` 不额外花钱

**问题**:`jump` 占用 `@ipt` 吗?
**答**:**占,而且和 `op` / `print` 完全一样,就是 1 条。** 但它**不额外花钱**。

**机制(`LExecutor.runOnce()`,L111–121)**:

```java
public void runOnce(){
    if(counter.numval >= instructions.length || counter.numval < 0) counter.numval = 0;
    if(counter.numval < instructions.length){
        counter.isobj = false;
        instructions[(int)(counter.numval++)].run(this);   // ← 计数器无条件 +1,不看指令类型
    }
}
```

**`counter` 先自增再执行,跳转只是把 `counter` 写成了别的值。** 所以账很清楚:

| 写法 | 消耗 |
|---|---|
| `op add a b c` | 1 条 |
| `print x` | 1 条 |
| **`jump 5 always 0 false`** | **1 条** |
| `jump 0 lessThan i 80` | 1 条 |
| **`jump` 走回头路再执行一次循环体** | **每次迭代再花循环体的语句数** |

⇒ **决定预算的不是"语句种类",是"实际执行到了几条语句"。** 循环圈数才是成本,`jump` 本身不是。
⇒ 写 `--cost` 时**按每条被执行的语句 +1** 就是对的,不用给 `jump` 加权。

**每 tick 的预算怎么来的(`LogicBlock.java` L45 / L564–578)**:

```java
public int maxInstructionScale = 5;

if(accumulator > maxInstructionScale * ipt) accumulator = maxInstructionScale * ipt;
while(accumulator >= 1f){
    executor.runOnce();
    if(executor.yield){ executor.yield = false; break; }   // ← wait / stop 提前结束
    accumulator --;
}
accumulator += edelta() * ipt;
```

| 处理器 | `instructionsPerTick` | 每秒额度 |
|---|---|---|
| 微型处理器 micro-processor | **2** | 120 条/s |
| 逻辑处理器 logic-processor | **8** | 480 条/s |
| 超级处理器 hyper-processor | **25** | 1500 条/s |
| 世界处理器 world-processor | **8**(`maxInstructionsPerTick = 1000`) | 480 条/s,可用 `setrate` 拉满 |

出处:`Blocks.java:6849`(micro)、`:6856`(logic)、`:6867`(hyper)、`:6954`+`:6958`(world);
`LogicBlock.java:46`(默认 1)、`:48`(`maxInstructionsPerTick = 40`)。

**三个容易漏的点**:

**① 那个"跑不完"的后果正是 `--cost` 预测的东西。**
微型处理器 2 条/tick ⇒ 一次决策 2000 条要 **1000 tick ≈ 16.7 秒**。这就是 159 行租约程序的病 → `--cost` 报 ~2001。

**② 欠账会攒,但有上限。**
`accumulator` 是浮点(tick 级,`edelta()` 是秒 × 60),落后时下一 tick 多跑,**封顶 `maxInstructionScale * ipt` = 5 ticks 的量**。所以启动时补一次,但别指望攒着追。

**③ 只有 `wait` 和 `stop` 会提前让出这一 tick。**
`yield = true` 会 `break` 掉 `while`,这一 tick 剩下的额度作废:
`wait` 在自己的行上挂起(`WaitI`,`counter.numval--` 后 yield);`stop` 卡在自己那一行(`StopI`,同样 `counter.numval--` 再 yield);`printflush ... @wait` 等 HUD 空位时也是这个行为。
⇒ **`jump` 没有这个机制**,所以 `jump 0 always` 会在**一个 tick 内**把额度烧光(每次都算 1 条)。

**④ `setrate` 是唯一能改 ipt 的指令,也是唯一能超过方块默认值的办法。**
`exec.build.ipt = Mathf.clamp(amount.numi(), 1, ((LogicBlock)exec.build.block).maxInstructionsPerTick)`(`LExecutor.java:2031-2034`)
⇒ 微型处理器最高 **40 条/tick**(`LogicBlock.java:48`),世界处理器最高 **1000**。
`@ipt` 立即变成新值,但**这一 tick 的循环边界早已固定**,下一个 tick 才生效。

---

## 15.13 ⭐ 死存储分析:`mlog.py ir`(CFG + 活跃变量不动点)

`--cost` 只看**规模**(跑得完吗),`ir` 看**值**(算出来的东西有人用吗)。
核心是 `mindustry-blueprint/tools/mlogir.py`:`Program.liveness()` 在 CFG 上做**后向 worklist 至最小不动点**,`dead_stores()` 报"写了却没人读"的位置。

**为什么这能一箭双雕**:`end` 的 successor 是 `[0]`(重启),所以图**自带环**,"末行写、首行读"这种跨周期的值会**自动被判活**,不需要额外规则。反过来,`set x 0` 之后再没人读 `x`,就是真的白写。

### 分四层,而不是全报

| 层 | 判据 | 为什么这样分层 |
|---|---|---|
| `reported` | 计算出来却被覆盖 | **信号**:作者真把结果丢了 |
| `slot` | `ulocate`/`ucontrol`/`radar`/`sensor` 等多输出槽 | 语法**强制**你给每个槽起名,不读不算错 |
| `declaration` | `set x <字面量>` 且全程序没人读 | 作者的"变量声明/备注" |
| `annotation` | 变量名**纯标点**(`//`、`--`) | 见下,mlog 没有行尾注释 |

### 三条容易踩的语言事实

**① `//` 不是注释 —— `#` 才是。**
`LParser.java:98-99` `if(c == '#'){ comment(); }`。所以 `set // lastPos` 是**真语句**,变量名就叫 `//`。
作者拿它当行尾注释用,游戏照样执行 ⇒ 这些是**真死存储**,但报出来纯噪声,归 `annotation` 层(全语料 285 条)。

**② 跳转标签不占指令槽位。**
`LParser.java:117-125` 把 `label:` 收进 `jumpLocations`,记的是**"已解析的语句数"**,不是指令索引。
所以 `main:` 只是给"下一条语句"起名;`jump main` 里的 `main` 在解析期被换成行号。不建模这一条,`reset:`/`state->halt:` 会被当成未知指令(我第一版就是这样,几万条 `unknown` 全来自标签)。

**③ `@counter` 写的是控制流,不是值。**
必须排除,否则每个循环都被报"写了没人读"(曾贡献 18266 条假阳性)。

### 实测:信号是真的,但要按"分布"读,别按均值

抽样 28 个 `reported` 站点**逐条人工核对,全部为真**(典型形态):

- **半交换写反**:`set d.h temp` 出现在 `set d.h d.w` **之前** ⇒ 用旧 `temp` 砸掉了 `d.h`
- **跳转落点错**:`set color @coal` / `jump 116 equal odd 0` / **L116 又是** `set color @blast-compound` ⇒ 第一行必死
- **连写两次**:`op or eo cyo cf` 紧跟 `op or eo cyo enemy`(同一个 `eo`)
- **守卫失效**:`1v1.msch:400` `op sub eguardamount eguardamount 1` 递减,全程序无人读
- **IME 打错字**:变量名 `cy！`(全角感叹号)本意 `cy!` ⇒ 静默造出一个新变量
- **重算前没画**:`1v1.msch` 的 `yset = rand(...) + 83`,到 L367 被重算,中间一次都没 `draw`

全语料统计(626 个 `.msch`,**排除 8 个模拟器/VM 蓝图共 3365 块** —— 它们按设计就是"写满寄存器槽、只回读下一指令需要的",不排除只会测到解释器解码器):

| 指标 | 真实蓝图(617 文件 / 2409 块) |
|---|---|
| `reported` | **1998(0.829 / 块)** |
| 每块 p50 / p90 / p99 | **0 / 1 / 19** |
| 完全干净(0 报告) | **1950 块 = 80.9%** |
| `slot` / `declaration` / `annotation` | 138 / 210 / 285 |

**结论:均值 0.829 是错的读法。** 五分之四的处理器**一条都不报**、90 分位只有 1 条;总数被约 20 个**代码生成式**蓝图(每份 60–78 条,如 `睡大觉大核触控采矿`、`触控版`、`超车模拟器`)拉高。**决定可用性的是"干净块占比 80.9%",不是均值。**

**`stale-write` 这一层带来的变化(1566 → 1998,+27.6%)**:多出的 432 条全部是「同一个槽写两次、全程序无读」。它们原先被 `slot`(340 条)和 `declaration`(92 条)藏住 —— 写**一次**的未读输出槽确实只是语法逼你起名,但同一个槽写**两次**时,第一次写可证被丢弃,那是真 bug。代价是干净块从 82.0% 掉到 80.9%(降 1.1 个百分点),换来 432 条可证的白算,这笔交易划算。

### 已知边界(别拿它当证明)

- **不跨处理器**:用 `read result cell1 "名字"` 按字符串读另一个处理器的变量,静态分析看不见。实测全语料**被解释的只有 0 条**,所以暂不建模 —— 但这意味着"报 `never-read` 时,先想想有没有别的处理器在读它"。
- **单次写入的 `ulocate` 输出槽默认隐藏**:`f`、`found` 这类是槽位强制的,`ir --all` 才列。
- **只判"值有没有人用",不判"值对不对"**:`op add dx dy dx` 想算距离却写成加法,`ir` 不会报(那是值域分析的事)。

---

## 15.14 `wait` 的节拍成本:一条 ipt 都不烧,却常常是节拍本身

### 为什么必须单独算

`--cost` 只数"执行到几条语句"。但 `wait` 在 `WaitI.run()` 里把 `counter` **减 1** 再 yield,
所以它连一条 ipt 都不花,却在整整 N 个 tick 里一个字都不执行。一个循环是
`op + op + wait 0.5` 还是 `op + op + wait 0`,指令数完全一样,实际周期差 30 倍。
只报指令数,等于把最贵的那个参数藏起来了。

### 源码事实(`LExecutor.java`)

```java
// :1219-1233  WaitI.run()
if(value.num() <= 0){ exec.yield = true; curTime = 0f; }
else if(curTime >= value.num()){ curTime = 0f; }
else { exec.counter.numval--; exec.yield = true; curTime += Time.delta / 60f; }
```

- **参数单位是"秒"**,每 tick 累加 `Time.delta/60f` ⇒ **60 tick = 1 秒**,`wait 0.5` = 30 tick。
- **`wait 0` 或负数不阻塞**,只是 yield 一次(让出本 tick 剩余额度,下一 tick 从自己重跑)。
  所以 `wait 0` 的真实作用是"每 tick 只跑一遍循环",不是"睡 0 秒"。
- `StopI`(`:1236-1245`)同样 `counter.numval--; yield = true; stop = true;`。
- `printflush` 的**旧写法**`printflush <变量名> @wait` 也会 `counter--; yield`(`:1916-1919`),
  等价于 `wait 0`;用 `message` 传 `@wait` 才是"刷完就停"。

### 三个把数字算错的坑(都已修,`mlogcheck.py`)

| 坑 | 症状 | 修法 |
|---|---|---|
| 标签行当语句 | 所有 `main:` 风格循环报 `L0(?)` = 无上界 | `prepare()` 先摘掉标签行、把 `jump 标签` 换成索引(标签不占槽,§15.13 已证) |
| 内层常量外泄 | 外层 `i<3` 里套内层 `j<10`,外层被报成 ×10 | `find_loop_bounds` **优先用回边自身的条件**,取到就不再扫循环体 |
| 循环被自己的出口路径乘了一遍 | `_wait1`(4 次循环、每次 3 条)报 113 条;内层循环在外层里只算一遍 | ①出口候选算进 `cnt` **之前**先取 `body`;②进入内层循环头时直接加 `loop_cost[inner]`;③最后一遍扫描**不再走回边**(循环已被计价过) |

修完后与手算对齐:`_wait1` **16**(手算 16)、`_wait2` **77**(手算 74,多的 3 是出口那一步的保守加一)。
改之前这两个数分别是 **113** 和 **1241** —— 也就是说旧模型能把一个 16 条的程序说成 113 条。

### 输出长什么样

```
  worst-case path : ~16 instructions per full cycle (approximate)
      micro-processor  @ipt=2        248 ticks (    4.1 s) per cycle
      logic-processor  @ipt=8        242 ticks (    4.0 s) per cycle
      hyper-processor  @ipt=25       241 ticks (    4.0 s) per cycle
  ⏸ blocking      : 2 wait statement(s), ~240 ticks (4.0 s) blocked per cycle, added above
      L3: wait -> ~120 ticks
      L5: wait -> ~120 ticks
```

`blocked` 已经加进三种处理器的 tick 数里;每条 `wait` 的 tick 数**乘上了包含它的所有循环上界**
(`wait 0.5` 在 4 次循环里 = 30×4 = 120)。参数不是字面量时报 `UNBOUNDED`,不编数字。

### 边界

- 仍然 **approximate**:分支按最坏路径取,max 而非期望值;`min(bound*body, 1000)` 会截断超大循环
  (遇到 `~1001` 就是"被截断了,真实值 ≥1001")。
- 循环上界只认**常量比较**(`lessThan i 10`),`while(@links 变化)` 这种没有上界的按"一趟"算。
- `wait` 与 `@wait` 语义不同,别混:`wait 0` 是"每 tick 一遍",不是"无限等"。

---

## 15.15 ⭐ 值域分析:`mlog.py values`(常量分支 + 可证 null)

`--cost` 数的是**指令**,`ir` 看的是**变量有没有人读**。这两样都看不见一件事:
某个分支的**条件永远成立**。`values` 就是补这一块的 —— 它跑前向不动点,给每条语句处
每个变量算一个抽象值,于是能说出 token 流里根本没有任何字面信息的话。

### 三条语言事实(全部是值域分析的地基)

源码都在 `Mindustry-Source/core/src/mindustry/logic/LVar.java`:

```java
public double num(){ return isobj ? objval != null ? 1 : 0 : invalid(numval) ? 0 : numval; }
public static boolean invalid(double d){ return Double.isNaN(d) || Double.isInfinite(d); }
// setnum() 里:
if(invalid(value)){ objval = null; isobj = true; }   // ← NaN / ±Infinity 一律变 null
```

1. **null 当数字用就是 0**,非 null 对象是 1。
2. **NaN 和 ±Infinity 会被静默归一成 null** —— 所以 `-Infinity` 不是"一个很大的负数",是 null。
3. `bool()` 是 `isobj ? objval != null : Math.abs(numval) >= 0.00001`。

第 2 条正是「按位剥离循环」能退出的全部原因:`op logn inputID lowbit 2` 在
`lowbit == 0` 时得 `-Infinity` → 变成 null → `strictEqual inputID null` 成立。
**写这段逻辑的人没有在任何地方"判断是否还有位",他靠的是数学**。值域分析能证明它。

### `==` 与 `===` 不是一回事(这条踩过)

`ConditionOp.test()`(`ConditionOp.java:31-40`)只有在**两边都是对象**时才走
`objFunction`,否则一律按数字比:

```java
if(objFunction != null && va.isobj && vb.isobj) return objFunction.get(va.obj(), vb.obj());
return function.get(va.num(), vb.num());
```

于是 **`equal x null` ⇔ `x.num() == 0`**,而"从未赋值过的变量"就是数字 0 ⇒
**用 `==` 判"这个变量有没有值"恒为真,永远进不去 else 分支**。只有 `===` 才区分
null 与 0。全语料 288 条被解析出来的分支里,大半都是这个形态 —— 它们不是工具猜的,
是作者写了恒真的判断。工具现在会在这种分支后面直接标一句
`[== against null is numeric: an unset variable is 0, so only === tells null from 0]`。

### 实测(617 真实蓝图 / 2396 块,排除 1 个模拟器文件 3354 块)

| 指标 | 数 |
| --- | --- |
| 有信号的块 | 98 / 2396 = **4.1%** |
| 常量分支 | 288(0.120/块) |
| 可证 null | 144(0.060/块),集中在 10 块 |
| 未收敛 | **0** |
| 速度 | 39 ms/块,全量 94 秒 |

样例(`无线四厄兆.msch` micro @(5,8),238 条语句,12 条常量分支):

```
L37    always  taken   `jump 39 equal Cth:Core null`   (cond = 1)
L42    never   taken   `jump 84 equal Cth:Key1 1`      (cond = 0)
L118   never   taken   `jump 96 notEqual Cth:Unit:1 null`   (cond = 0)
```

### 三个自己踩的坑(都已成为回归样例)

- **`op rand` 被当成"必定 null"** —— 最初把 `rand`/`noise` 的实现写成 `math.nan`,
  而 `setnum()` 会把 NaN 变 null ⇒ `1v1.msch` 一次报了 10 条假阳性。
  **教训:在这个域里 NaN 不是"不知道"的哨兵,它就是 null。** 现在这两个算子
  直接落到 `TOP`(不知道),不再猜。
- **入口状态留空 → 回边的值直接冒充初值** —— `ILOS.test.msch` 因此报
  `L28 jump 29 strictEqual message null`,而 `message` 只在 L29 才被置 null
  (第一遍是 0、第二遍才是 null,诚实的答案是"0 或 null")。
  修法:pc 0 的入口状态预置 `NUM0`(`new LVar(name)` 本来就是 `numval = 0`)。
- **`null` 字面量被当成变量名**,`strictEqual x null` 永远不解析;以及算子名
  大小写不匹配(`strictEqual` vs `strictequal`)导致所有比较静默失效 ——
  这类 bug 的表现是"报告里什么都没有",比报错难查得多。

### 边界

- 外部输入一律 `TOP`:`sensor` / `getlink` / `ulocate` / `@` 内置量拿到的都是运行期
  状态,不猜。**所以它只在"纯计算链"上说话** —— 这恰好也包括
  `set` → `op` → `jump` 的计数器与状态机。
- 变量连改 3 轮后按变量丢精度到 `TOP`(widen),保证收敛;`unstable` 目前是 0。
- 不跨处理器,不判断值**算得对不对**,只判断"它是不是必然为 null / 条件是不是必然成立"。
- 报告只给前 20 条,多的自己用 `--trace VAR` 追。

### 15.16 ⭐ 打包配置识别:`mlog.py pack`(字段布局 + 容量上限)

把多个字段塞进一个数字(`data = status*1e8 + outputID*1e6 + inputMask`),
再用 `op idiv` / `op mod` 一层层剥开,是**高级写法但很冷门**的惯用法:

```
op idiv status   data 100000000      # 1e8 -> status
op idiv outputID data 1000000        # 1e6 -> outputID
op mod  mask     data 1000000        # 1e6 -> inputMask
```

`mlog.py pack` 干两件事:**画出字段布局**,以及**算出低位字段能装多少个 id**。
后者是本项目唯一能直接给出"这段代码有 bug"结论的分析:

```
low field `1e6` holds 0..999999  =>  20 usable bit positions (ids 0..19)
!! 22 items exist but only 20 fit: ids 20..21 overflow into the next field
   (raise the separator, e.g. 1e6 -> 1e7)
```

**为什么 20 而不是 21**:mask 是 `data % 1e6`,取值 `0..999999`,`(10**6-1).bit_length() == 20`。
原版 22 个物品里 `fissile-matter` 是 id 20、`dormant-cyst` 是 21 ⇒ **放不进 20 位**。
(这也是 §15.7 那张物品 ID 表的用处之一。)

**两类"看起来像 bug、其实不是"的情况,都被实测逼出来了**:

1. **自我配对**:`op idiv flag- flag 1e6` 在一个程序里出现两次(同一个跳板变量复用),
   朴素实现会把每一对 idiv 互相配对,打出 `` `flag-` also contains 1x `flag-` `` 这种废话。
   修法:每个**不同指数**只取一个代表做配对。
2. **正确的掩码被当成漏判**:`op mul flag- tokey 10000000` + `op sub flag- flag flag-`
   是先减掉高位再除,解码完全正确。修法:检测这个范式(高位商 × `10**hi.exp`,
   再 `op sub` 回源值),命中就改报 `ok: ... decode is correct`,不再报警。

**校准(全语料 626 文件 / 2420 块 / 86.9 秒 / 35.9 ms/块)**:只有 **3 块(0.1%)**
出现这个惯用法 —— `[#ffff00]水滴网0.9.3+公测版.msch`(micro @(1,0))、
`全图自动送布逻辑.msch`(micro @(1,0))、`无线网络通信服务器主机.msch`(hyper @(2,1))。
三个都人工核对过,布局与告警都真。

**结论:它不是一个 linter,是一个"点开就说话"的专用检查。** 0.1% 的出现率意味着
拿它扫描整个语料几乎什么都看不到;但一旦命中,它给出的是**具体的容量数字**,
而不是"这里可能有问题"。这跟 `ir`(死存储,0.829/块)是两种完全不同的工具形态:
前者高频低置信,后者低频高置信。

### 边界

- 只认 `op idiv|mod <dst> <src> 10**exp` 这个形状,且**同一个 `src` 上至少两个不同指数**
  才算一个 pack site(单独一个分隔符只是一次除法)。
- 它**不重建表达式**,只报站点、字段布局和容量;想知道"这个值到底对不对"要人工读。
- 10^3 以下的数不算字段分隔(`MIN_EXP = 3`)。
- 不跨处理器;`op mul`/`op sub` 掩码检测是全程序的文本匹配,不做数据流 —— 一个程序里
  别处存在同形的 `mul`+`sub` 就可能让真漏判静默通过(当前语料里未出现)。

---

### 15.17 批量扫描:当一个蓝图包成为测试语料

拿 `非mod+像素工厂蓝图【彩末整合】160+v-30.zip`(926 份 `.msch`)当回归语料跑一遍,
**最大的产出不是关于那批蓝图的结论,而是我自己工具里的四个错误。**

#### 规模分布:一个包其实是两批东西

| | 文件 | 逻辑块 | 语句 | 硬错 | 死存储 |
|---|---|---|---|---|---|
| 全包 | 926 | 1698 | 359,131 | 883 | 2156 |
| 排除 `⭐不正经的东西⭐`+`🎯逻辑小游戏🎯` | 817 | 902 | 45,722 | 761 | 1777 |

**109 份"不正经"的文件占了 87% 的语句**(29.5 万条),内容是多控热舞、坏苹果、香蕉君
这类**动画/演示程序**:它们的 16,561 个"无界自旋"是设计意图,不是缺陷。
任何按总量算出来的指标都会被这批东西淹没 —— 所以下面所有比率都按严肃子集算。

- 严肃子集:硬错 **16.6 条 / 千语句**,死存储 **4.0% 的语句**,干净块 **74.6%**。
- 每块语句数中位 41、p90 902、**上限 1000**(`LogicBlock.maxInstructions`,
  p90 900 说明不少程序已经贴着硬顶写)。

#### 四个工具 bug(全部由这个包逼出来)

1. **`0x`/`0b`/`%rrggbb` 不是变量**:`LAssembler.java:87-99` 的 `parseDouble` 认十六进制、
   二进制、颜色字面量。修前把 `0xFF` 当变量名 ⇒ 硬错 **1100 → 883**。
2. **`op rand g 255 b` 只读一个操作数**:`rand` 是一元算子,`LAssembler` 解析整行但
   `UnaryOp` 只拿 `a`。同类警告 182 条(`floor`、`rand`)全部消失。
3. **`jump T always x false` 的 `x`/`false` 是补齐位**:生成器/派发表把每条 jump 都写成
   四 token,`always` 一个操作数都不读。把它们当读取 ⇒ **276 个块凭空多出未定义变量 `x`**。
4. **`op add @counter @counter id` 是派发表**:下一句是第 id 行,静态可达性完全失效。
   修前 9,384 条"不可达"里 **8,533 条是假的**(质驱系列每块 584 条其实是一张 388 行的
   `jump` 表)。现在 `Program.writes_counter()` 为真时直接不报不可达,并说明原因。
5. **`jump -1 always` 是 nop 不是终止**:`JumpI.run()` 有 `if(address != -1)` 保护,
   负地址啥也不做、**继续往下走**。修前 `坦克大战.msch` 190 条里报 182 条不可达。
   修后全包不可达 9,384 → **495**。

方法论:**"每个块报几条"这种数字,在换一份语料之前都只是关于你自己解析器的数字。**

#### 这批蓝图里的横切发现

- **`equal X null` 恒真**:166 处守卫写在从未赋过值的变量上。因为 `equal` 走数值比较
  (`ConditionOp.test`),未赋值变量是 0,`null.num()` 也是 0 ⇒ **恒真**。
  `obv超射程 大.msch`(678 语句)里 72 处 `jump 588 equal 单位获取 null` 全部成立,
  **第 37–587 行约 550 条语句从不执行**。同一误解在别的文件里换了变量名重复出现
  (`跳过用` 40、`查表完成` 23、`执行结束` 11)。
- **把链接名当变量名用**:87 个块引用 `message1`(22)、`switch1`(19)、`sorter1`(11)、
  `projector1`(9)这类名字,但那些方块**没被链接** ⇒ `printflush`/`control` 指向不存在的
  方块,静默无效果。
- **`print` 不带引号**:`print by:NOSB(hghg`(34 处)。`LAssembler.java:67-69` 只有首尾都是
  `"` 才生成字符串常量,否则当变量读 ⇒ **永远打印空**。
- **换行丢失只有 1 处**(`control config unloader4 null 0 0 0sensor`):这个包的搬运不是
  批量机械损坏。

#### 边界

- 这里所有结论都建立在"变量名 = 存储位置"上。mlog 的 `read`/`write` 可以按**字符串名**
  访问别的处理器的变量,本扫描没有建那个模型 ⇒ 跨处理器读写看不见。
- 派发表(`@counter`)一旦出现,该块的可达性就不报,**这也意味着真正的死代码会被一起放过**。
- 死存储 4.0% 里有一半来自 `质驱` 系列同一份模板的复制,不能当"作者平均犯错率"。

---

## 16. ⚠️ 我写错的逻辑清单(生成前对照)

这一节记录**实际被抓到的逻辑错误**,不是猜测。

### 16.1 `@dead` 语义用反

**`@dead` 死亡返回 `1`。** 所以"死了就重绑"必须写 **`equal`**:

```mlog
# ❌ 我写错的
sensor d @unit @dead
jump 0 notEqual d 1          # d=1 表示已死,我却让"活着"才跳 → 死单位被留下

# ✅ 正确
sensor d @unit @dead
jump 0 equal d 1             # 死了 → 回开头重新 ubind
```

**附带好处**:`@dead` 对 `null` 目标也返回 `1`(null 视为已死),所以这一条**同时兼作"单位不存在"的判断**,不用再单独判 null。

### 16.2 把传感器行当跳转目标 + 覆盖了还要用的变量

```mlog
# ❌ 我的错误结构
ulocate building core 0 @copper cx cy 0 core      # 只在"要取货"时才执行
...
sensor bx dome1 @x          # ← 把 bx 覆盖成穹顶坐标,而 bx/by 是重绑时用的变量
sensor by dome1 @y
jump 0 strictEqual by null
```

**叠了三个问题**:

1. **`ulocate` 放进条件分支** → "要回核心"的路径上 `cx cy` 可能从未被赋值,
   拿旧值/null 去 `ucontrol move`,**单位飞向 (0,0) 或原地卡死**
2. **跳转目标算错,掉进传感器块** → 控制流穿透到不该去的地方
3. **变量被覆盖** → `bx/by` 既当核心坐标又当穹顶坐标

**✅ 正确做法**:

- **`ulocate` 无条件放在前面**,每轮都执行,保证任何路径下坐标都有效
- **取货和投料做成两条互斥路径**,各以 `end` 结束
- **投料路径用条件守住**(`jump 0 strictEqual fi cfg`),不能顺着落下来

### 16.3 跳转行号必须逐条数

蓝图里 `jump` 存的是**绝对语句索引**。改一行,后面全部偏移。

**生成前自查**:

```
1. 写出完整代码,从第 0 行开始编号
2. 对每条 jump,回查目标行号指向的是哪条指令
3. 重点检查:目标是不是落在 sensor/set/ubind 这类"有副作用"的行上
```

**我这次的错误就是第 3 条**:跳转目标落在一个 `sensor` 上,还把要用的变量覆盖了。

### 16.4 结构模板(照这个写不会犯上面两个错)

```mlog
# ① 绑定 + 存活(注意 equal)
ubind @flare
sensor d @unit @dead
jump 0 equal d 1
# ② 归属(失败一律回开头,不留落空分支)
jump 5 strictEqual @unit null
sensor c @unit @controller
jump 0 notEqual c @this
jump 0 notEqual c @unit
# ③ 读状态
sensor fi @unit @firstItem
...
# ④ 无条件定位(不要放进分支!)
ulocate building core 0 @copper cx cy 0 core
jump 0 strictEqual cx null
# ⑤ 两条互斥路径,各自收尾
... 取货 ... end
... 投料 ... jump 0 always 0 false
```

### 16.5 蓝图只有处理器时的链接真相

**schematic 里的链接只存"名字 + 相对坐标",目标建筑必须真实存在于地图上。**

所以只放处理器的话,`dome1` 这个名字**解析不到任何东西** —— 这是正常的,
贴下去之后在那两个格子放上真的穹顶即可。

生成器现在会明确提示这一点(`link_report`),而不是假装画了个框。

> 想让工具**连目标方块一起放**也可以,但需要该方块的 **content ID**
> (`ContentType.block` 里的索引,受 mod 影响)。
> 游戏里用 `sensor id <那个方块> @id` 可以读出来,告诉我我就能加进工具。

---

## 17. ⭐ Skill 整合包 `mindustry-blueprint/`

把工具、规范、参考数据整理成了一个 **DSH skill**,方便随时调用。

**位置**:`mindustry-blueprint/`(18 个文件,426 KB,纯标准库零依赖)

```
mindustry-blueprint/
├── SKILL.md                 规范:铁律 + 标准流程 + 坐标约定(agent 读这个)
├── README.md                安装与用法
├── REFERENCE.md             完整知识库(本文件的副本)
├── PATTERNS.md              逻辑模式库
├── BLUEPRINT-ANALYSIS.md    蓝图层逐类精讲
├── .gitignore
└── tools/
    ├── mlog.py              ⭐ 统一 CLI 入口
    ├── msch.py              蓝图解析库
    ├── mschgen.py           蓝图生成库
    ├── mlogcheck.py         静态检查库
    ├── mlogsearch.py        语料检索
    ├── block_ids_from_source.py / block_sizes.py   从源码推导
    ├── fetch_wiki_ids.py / build_cmd_index.py      从 wiki/文档抓取
    ├── wiki_block_ids.json  422 个方块 → content ID
    ├── block_sizes.json     446 个方块尺寸
    └── cmd_index.json       86 条指令格式
```

### 17.1 统一 CLI

```bash
python tools/mlog.py parse  <file.msch>       # 解析蓝图
python tools/mlog.py gen    <logic.mlog> ...  # 生成蓝图码
python tools/mlog.py check  <logic.mlog>      # 静态检查
python tools/mlog.py id     [名称]             # 方块 ID / 尺寸
python tools/mlog.py cmd    [关键字]           # 指令格式
python tools/mlog.py selftest                 # 429 个蓝图往返校验
```

**`gen` 的确定性保证**:先 `build` → 再 `parse` 验证(code 与 name 一致)→ **通过才输出**。
验证失败会拒绝输出,不会给出坏蓝图。

### 17.2 打包注意

- `SKILL.md` 的 frontmatter 必须有 `name` / `description` / `whenToUse`
- **不要提交 `__pycache__`**(已加 `.gitignore`)
- `selftest` 的 schematics 路径**已改为自动发现**:`$MINDUSTRY_SCHEMATICS` → `%APPDATA%/Mindustry/schematics` → Linux/macOS 常见位置。**不再硬编码任何用户路径**
- 装到 `$DSH_HOME/skills/` 即可被自动加载
- 发 GitHub:仓库打 `dsh-pack` 话题 + 根 manifest + **正式** Release(`.dspack` + `.sha256` 侧车,64 位小写 hex)

### 17.3 遗留

- **工具现在有两份**:工作目录根的 `tools/`(开发用)和 skill 内的 `tools/`(分发用)。
  改代码时要同步,后续可考虑把根 `tools/` 做成指向 skill 的转发。

---

### 17.4 ⭐ 安装位置与 skill 库路径表

**已安装到本项目的专有 skill 库**:

```
F:\OneDrive\桌面\AtomicStates\.dsh\skills\mindustry-blueprint\    ← 生效位置
F:\OneDrive\桌面\AtomicStates\mindustry-blueprint\                ← 开发位置
```

**Skills Manager 插件**(`@michengai/dsh-skills-manager`)的路径表(README 原文):

| 来源 | 全局目录 | **项目目录** |
|---|---|---|
| **DSH** | `~/.dsh/skills` | **`<project>/.dsh/skills`** ← 用的这个 |
| Project Skills | — | `<project>/skills` |
| Claude Code | `~/.claude/skills` | `<project>/.claude/skills` |
| Codex | `~/.codex/skills` | `<project>/.codex/skills` |
| Cursor | `~/.cursor/skills` | `<project>/.cursor/skills` |
| Copilot | `~/.copilot/skills` | `<project>/.github/skills` |

**关键规则**:

- **项目副本优先于全局副本**;两者独立,禁用一份另一份会接管
- "Current project only":Git 仓库用**最近的 Git 根**;**非 Git 目录用当前会话工作目录,不需要 `git init`**
- 所以同一个 skill 可以在不同项目各存一份不同版本

> ⚠️ **`~/.dsh/skills` 是个 junction**,指向 `~/.dsh/.dsh-pack/skills/<当前 profile>`。
> 直接往里写会写进当前 profile 的库,**换 profile 后会失效**。
> **项目专有 skill 要写 `<project>/.dsh/skills`**,不要写全局。

**验证**:写进去后目录会立即出现在可用 skill 列表里(DSH 会重新扫描)。

### 17.5 ⚠️ 相对链接必须"位置无关"

文档里的相对链接会**随安装深度变化**:

| skill 位置 | 到工作目录根需要 |
|---|---|
| `<root>/mindustry-blueprint/` | `../` |
| `<root>/.dsh/skills/mindustry-blueprint/` | `../../../` |

**踩过的坑**:我按固定层数改了三轮才全对(先多一层、又少一层、再发现新位置又变了)。
**做法修正**:[tools/fix_skill_links.py](../tools/fix_skill_links.py)
**向上找 `Mindustry-Source` 定位工作目录根**,再按实际相对深度重写所有链接。
**以后再搬位置,重跑一次这个脚本即可。**

---

## 18. 更新日志

| 日期/轮次 | 内容 |
|---|---|
| 第 1 次整理 | 建立本文件;收录链接名规则、null 传染、单堆叠容量、`move`/`approach` 取舍、`ulocate` 参数、单位归属片段、7 条被推翻的旧结论;补 `LAccess.java` 完整 sensor 总表 + `setprop` 合法清单(附录 A) |
| 第 2 次整理 | **重大修正:`core` 不是内置关键字,是 `ulocate` 第 8 参输出的变量**(§1.2 / §5.1 / §8.1);补 `ulocate` 完整 9 参数表与距离规则(§5);补 `move`/`approach` 精确差异表与判定半径计算(§6);补 `uradar` 不刷新计时器(§6.5);补 `itemDrop`/`itemTake` 的完整传输条件与静默失败风险(§3)|
| 第 3 次整理 | 通读 `Logic-Docs` 全部 86 个命令章节,建成**附录 B 全命令格式索引**(§13);新增脚本 [tools/build_cmd_index.py](tools/build_cmd_index.py) → [tools/cmd_index.json](tools/cmd_index.json);记录 `getblock` 与 `ucontrol getBlock` **参数顺序不同**的坑 |
| 第 4 次整理 | **新增铁律 §0.5:控制单位前必须先 `ubind`**,否则 `@unit` 为 null、所有控制语句静默无效;归纳"mlog 没有隐式上下文"这条通用教训(要用什么先取什么);订正 `corea` 为笔误,正确是 `core` |
| 第 5 次整理 | 新增工具 **[tools/mschgen.py](tools/mschgen.py) 蓝图生成器**(§14),429/429 逐字节往返验证通过;新增"生成代码前必查清单"(§14.1),把之前犯的 4 个错变成 4 条检查项 |
| 第 6 次整理 | **新增铁律 §0.6:`tags[r.utf()] = r.utf()` 这种写法会把键值对调**(Python 先算右边)。这个 bug 让全部 625 个蓝图的 name/labels 读反,而往返自测完全抓不到(读写同错互相抵消)。修复后重新生成语料,恢复 403/430 个 labels。**教训:自洽的往返测试必须配真实文件地面真值比对。** 工具改为默认输出可直接粘贴的 base64 蓝图码(`-f code`,另有 `file`/`both`) |
| 第 7 次整理 | **新增 §16「我写错的逻辑清单」**(由 Iliary 实测抓出):① **`@dead` 用反**——死亡返回 1,重绑必须写 `equal`;② **`ulocate` 放进了条件分支** + 跳转目标掉进 `sensor` 块 + 覆盖了还要用的变量,导致单位飞向 null 核心坐标。给出 §16.4 结构模板和 §16.5 链接真相(链接只存名字+相对坐标,目标方块必须在地图上) |
| 第 8 次整理 | **新增工具 `tools/mlogcheck.py` 静态检查器**(§15):把两个真实 bug 的判据固化成检查项,**实测能抓出我写错的 `@dead` 反用**,修正版则干净。同时调研了 8 个外部 mlog 项目(§15.3),结论:**没有可用的模拟器**(唯一对口的 mindus 需要 Rust),**content ID 无法从外部获取** |
| 第 9 次整理 | 核实 **`plandustry` 是什么**(§15.4):已归档的 Rust 蓝图编辑器(print/edit),有完整方块库(含尺寸/造价)但**`registry.rs` 只有 `by_name` HashMap、零数字 ID** —— **从第二个独立实现反证"外部工具给不出 content ID"**;并指出 **mindus 的真正执行部分是 `lemu/` 子目录**。新增 §15.5:用 `lookup block` + `@name` **在游戏里一次性导出全部方块 ID 表**的现成代码 |
| 第 10 次整理 | 抓到**官方 wiki 的完整方块 ID 表**(§15.6):`mindustrygame.github.io/wiki/` 的内容页 slug 带 ID,从 mkdocs 搜索索引一次抓全 → [tools/wiki_block_ids.json](tools/wiki_block_ids.json),422 个方块、ID 1–446,**`overdrive-dome` = 248**。同时确认该表**混入了 MindustryX 内容**(`world-cell` 等),故只对"同款环境"有效;MDT 中文 wiki([mdtwiki.top](https://mdtwiki.top/),v159.7)指向的 MindustryX 飞书文档**需登录抓不到**;MindustryX 源码([TinyLake/MindustryX](https://github.com/TinyLake/MindustryX))是 81 个补丁,`0046-UI-ARC-logic-Support` 经查是**编辑器 UI 增强、非语法扩展**。新增 **§15.7:编号体系不止一套**——`Content.id`=248 vs 建筑分类序号=#38,**别混用** |
| 第 11 次整理 | **修正 §15.8「方块坐标是中心格」**:Iliary 实测抓出"穹顶与逻辑空一格"。双重验证 —— 源码 `Tile.setBlock()` 的 `offset = -(block.size-1)/2`;**624 个真实蓝图里按"角"解释产生 11 处重叠、按"中心"解释 0 处**。生成器 `bounds()` / `link_report()` 同步修正。**方法论:坐标语义这类约定,用全量语料做"哪种假设不产生矛盾"的统计验证最可靠。** |
| 第 12 次整理 | **把工具+规范+数据打包成 DSH skill** `mindustry-blueprint/`(§17),统一 CLI `mlog.py`(parse/gen/check/id/cmd/selftest),`gen` 内置自验证(解析回来不一致就拒绝输出);**去掉全部硬编码路径**(schematics 目录自动发现);安装到**项目专有 skill 库 `.dsh/skills/`**(§17.4 记了各 agent 的路径表;`~/.dsh/skills` 是 junction,**写全局会随 profile 失效**);新增位置无关的 [tools/fix_skill_links.py](tools/fix_skill_links.py)(向上找 `Mindustry-Source` 定根,§17.5 —— 我按固定层数改了三轮才全对) |
| 第 13 次整理 | **新增 `check --cost` 成本分析**(§15.11):可达性(死代码)+ 循环圈数推定 + 最坏指令数与三档处理器耗时。实现中踩了 6 个坑,其中三个是**同一份代码连续三次算错**(78 → 643686 → 2001):只在回边乘圈数会让循环体只算 1 次;全局松弛会**重复计费嵌套循环**;**`float('inf')` 当哨兵会让比较静默返回 False、所有程序都报 1**。最终用"按 head 降序、内层先解、每循环只定价一次 + clamp 1000"解决。**实测校准**:另一 AI 的 159 行程序手算 ~2494 → 工具 2001;**批量 4151 个真实逻辑块 0 失败**;并用它审出我自己的 `out\无线超2.mlog` 有 6 条 `end` 之后的死代码(教训进 §16 与 SKILL 铁律 12) |
| 第 15 次整理 | **答「`jump` 占不占 ipt」并落成 §15.12 指令预算**:`runOnce()` 里 `counter` **先自增再执行、不看指令类型**(`LExecutor.java:111-121`)⇒ **`jump` 和 `op`/`print` 一样就是 1 条,不额外花钱;真正的成本是"实际执行到几条语句"**(循环圈数才是钱)。补全每 tick 预算机制:`LogicBlock.java:45` `maxInstructionScale = 5`、`:564-578` 的 accumulator 循环与 **`yield` 提前 break**(只有 `wait`/`stop`/`printflush @wait` 有);四张卡 ipt 表(**微型 2 / 逻辑 8 / 超级 25 / 世界 8**,`Blocks.java:6849/6856/6867/6954`,世界卡 `maxInstructionsPerTick = 1000`);`setrate` 是唯一能改 ipt 的指令且上限是 `maxInstructionsPerTick`(逻辑卡 **40**,`LogicBlock.java:48`),**`@ipt` 立即变但本 tick 循环边界已固定** |
| 第 14 次整理 | 评完那份 159 行「flag 位域租约」程序:**四路单位选择器是正确的**(我一度误判为死代码,根因是把跳转目标当成下一行执行)。真实缺陷:① `jump 28 always` 无条件回跳使 `end` 前的 `control enabled resetSwitch 0` 永不执行(复位开关卡死);② 缺 `@unit` 判空;③ 硬编码扫描上限 80 与"`ubind` 计数器按单位类型推进"语义不匹配;④ 每 10 秒全体同时换代;⑤ 每轮重复写 flag 使单位永不自然脱控。**用户结论:"工程上标准,但是不适合游戏"** —— 错不在工程化,而在**把通用协议当起点而非终点**。值得留的三个想法:让 `0` 天然表示空闲(ID 加 1)、用容器坐标派生模块 ID(不依赖 `@thisx/@thisy`)、租约容忍一代重叠 |
| 第 16 次整理 | **死存储分析落地 `mlog.py ir`**(§15.13):CFG + 后向活跃变量不动点,`end` 的回边让"跨周期写读"自动判活。四层分级(`reported`/`slot`/`declaration`/`annotation`)。**三条语言事实**:`//` 不是注释(`#` 才是,`LParser.java:98-99`)⇒ 那些是**真死存储**;跳转标签**不占指令槽**(`LParser.java:117-125` 记的是"已解析语句数");`@counter` 必须排除(否则 18266 条假阳性)。**实测 626 个 `.msch`**:排除 8 个模拟器蓝图(3365 块)后,真实 617 文件 / 2409 块,`reported 1566 = 0.650/块`,但 **p50=0、p90=1、82.0% 的块一条都不报**,均值被约 20 个代码生成式蓝图拉高 ⇒ **"干净块占比"才是可用性指标,均值不是**。抽样 28 个站点**逐条人工核对全部为真**(半交换写反 / 跳转落点错 / 连写两次 / 守卫递减无人读 / 全角 `cy！` 打错字 / 重算前没 `draw`)。**方法论:先量误报再谈可用;分层比压噪声有效。** |
| 第 17 次整理 | **`--cost` 接上 `wait` 的节拍成本 + 修掉循环计价的三处系统性错误**(§15.14)。`wait` 在 `WaitI.run()` 里 `counter--` 再 yield,**一条 ipt 都不烧**,却常常是真实周期的全部 —— 只报指令数等于把最贵的参数藏起来。源码定案:`wait` 参数是**秒**(`curTime += Time.delta/60f` ⇒ 60 tick = 1 秒),`wait 0` 不阻塞、只是"每 tick 跑一遍"。顺带发现旧模型严重高估:`_wait1`(4 次循环 × 3 条)报 **113**(真值 16)、`_wait2` 报 **1241**(真值 74)。三处根因:①出口候选先写回 `cnt` 再取循环体长度 ⇒ **循环被自己的出口路径乘一遍**(4×3 变 4×14);②外层循环只按"内层跑一遍"算;③到底后再走一遍回边 ⇒ 循环二次计费。修法:先取 `body` 再算出口、进内层头时直接加 `loop_cost[inner]`、末轮不再走回边;`find_loop_bounds` 改为**优先用回边自身条件**(内层常量原本会外泄,外层 ×3 被报成 ×10)。修后与手算对齐 **16 / 77**。另修 `strip_comment` 的 BOM(`\ufeffset` 认不出助记符)。**方法论:一个"近似"数字也要能对上两个手算样例,否则它只是看起来像数字。** |
| 第 18 次整理 | **新增值域分析 `mlog.py values`(§15.15):常量分支 + 可证 null**。`--cost` 数指令、`ir` 看谁读,两者都看不见「这个条件永远成立」。三条源码事实打底(`LVar.java`):`num()` 里 **null 当数字用就是 0**;`invalid()` 的 NaN / ±Infinity 在 `setnum()` 里**静默变成 null**;`ConditionOp.test()` 只在两边都是对象时才走对象比较,否则一律按数字比 —— 于是 **`equal x null` ⇔ `x == 0`,对未赋值变量恒真,只有 `===` 才区分 null 与 0**(全语料 288 条常量分支里大半是这个形态,工具现在会在这种行后面标出来)。全量 617 文件 / 2396 块(排除 1 个模拟器文件 3354 块):**4.1% 的块有信号**、常量分支 288(0.120/块)、可证 null 144(0.060/块)、**未收敛 0**、39 ms/块。三个自己踩的坑:①把 `rand`/`noise` 写成 `math.nan` ⇒ NaN 被归一成 null ⇒ `1v1.msch` 报 10 条假阳性(**在这个域里 NaN 不是「不知道」的哨兵,它就是 null**);②入口状态留空 ⇒ 回边的值冒充初值(`ILOS.test.msch` 报 `strictEqual message null`,而它只在下一行才被置 null);③`null` 字面量被当变量名 + 算子名大小写不匹配 ⇒ 所有比较静默失效(表现是「报告里什么都没有」,比报错难查)。**方法论:一个分析工具的第一次全量运行,主要产出是它自己的 bug 列表。** |
| 第 19 次整理 | **新增打包配置识别 `mlog.py pack`(§15.16):字段布局 + 容量上限**。`data = status*1e8 + outputID*1e6 + inputMask` 这一族用 `op idiv`/`op mod` 层层剥离,`pack` 把字段画出来并算出**低位字段能装几个 id** —— 这是全套工具里唯一能直接给出"这段代码有 bug"的地方:`1e6` ⇒ `(10**6-1).bit_length() == 20` ⇒ **原版 22 个物品里 `fissile-matter`(20)、`dormant-cyst`(21)放不进**,告警直接给出 `raise the separator, e.g. 1e6 -> 1e7`。全语料 **626 文件 / 2420 块 / 86.9 秒**:只有 **3 块(0.1%)** 出现这个惯用法,三个都人工核对为真。两个自己被实测逼出来的误报:①**自我配对**(同一跳板变量 `flag-` 被 idiv 两次 ⇒ 打出 `` `flag-` also contains 1x `flag-` `` 的废话,修法:每个不同指数只取一个代表);②**正确的掩码被当成漏判**(`op mul t hi 1eN` + `op sub u src t` 是先减高位再除,解码完全正确 ⇒ 改报 `ok: ... decode is correct`)。**方法论:出现率 0.1% 的分析不是 linter,是"点开就说话"的专用检查 —— 高频低置信(`ir` 0.650/块)和低频高置信(`pack`)是两种工具形态,不能拿同一把尺子量。** |
| 第 20 次整理 | **把六种分析打包成独立技能 `mlogagent`**:一个 `report` 命令依次跑 `check`/`cost`/`ir`/`values`/`pack`,再按**证据强弱**给出「先看这里」(check 报错 → 死存储 → 不可达 → 常量分支 → 可证 null → 打包配置 → 未知助记符),末尾一行机器可读的 VERDICT。**退出码只有 `check` 能影响**(`ir`/`values`/`pack` 是建议性输出,永不让脚本失败)—— 因为 `ir` 一个错平均要陪着 0.65 条噪声,让它失败等于让脚本天天失败。技能**自带 13 个工具文件副本 + MANIFEST.sha256**(拷到 `%TEMP%` 单独跑通验证过),由 `tools/sync_mlogagent.py` 单向生成,`--check` 只比对不动文件。**三个自己踩的坑**:①`_targets()` 按内容而不是后缀判断 `.msch` ⇒ 蓝图被当 UTF-8 读,`UnicodeDecodeError: 'utf-8' codec can't decode byte 0xda in position 6`;②同步脚本一度把**蓝图技能的 SKILL.md 覆盖到 mlogagent 上**,症状不是报错而是**该技能从可用技能目录里整条消失**(front matter 变成另一个名字)⇒ payload 永不含 SKILL.md;③PowerShell 的 here-string 会把反引号 r / t 变成 CR/TAB,把一行注释劈成两半 —— **含反引号的正文只能用写文件的工具落地,不要塞进 shell 字符串**。**方法论:工具集的最后一层不是分析能力,是「哪一条结论值得先信」的排序。** |
| 第 21 次整理 | **新增 `stale-write` 层:把「写两次从不读」从 `slot` 里救出来**。起因是 `mlogagent report` 对一份已人工确认的蓝图报 `dead-store 0(+3 hidden)` —— `17十七硫幽灵四熔毁四油海啸组.msch` 的 micro-processor @(16,8) 里 `found` 在 `L6` 与 `L61` 各被 `ulocate` 写一次、全程序无读,却被归进 `slot`(语法强制的输出槽)隐藏了。**判据的修正**:写**一次**的未读输出槽,确实只是语法逼你起个名字(`ulocate` 必须写出 4 个变量),降级为 `slot` 合理;但同一个槽**写两次**且从没人读时,**第一次写可证被丢弃** —— 单次未读可能是声明,第二次不可能是别的。实现:`classify_dead_stores()` 增加第三种 kind(统计每变量写次数,`>1` 且无读 ⇒ `stale-write`),`_ir_tier` 把 `overwritten` 与 `stale-write` 一起返回 `reported`,**刻意放在 `slot`/`declaration` 之前**。全语料重测:真实蓝图 `reported` **1566 → 1998(+27.6%)**,多出的 432 条全部是「同一槽写两次、无读」;`slot` 478 → 138、`declaration` 302 → 210;干净块只从 **82.0% 掉到 80.9%**(−1.1 个百分点),p99 15 → 19。**方法论:噪声不可怕,可怕的是把真 bug 降级成噪声 —— 分层的每一层都要能说出"为什么这一层不用管",说不出就该并回上一层。** |
| 第 22 次整理 | **批量扫描反噬:926 份蓝图包逼出五个工具 bug**。①`0x`/`0b`/`%rrggbb` 是字面量不是变量(`LAssembler.java:87-99`),修前硬错 1100→883;②`op rand g 255 b` 里 `b` 从不被读(一元算子只取 `a`),182 条假警告清零;③`jump T always x false` 的 `x`/`false` 是补齐位,修前 276 个块凭空多出未定义变量;④`op add @counter @counter id` 是**派发表**,静态可达性失效 —— 9,384 条「不可达」里 8,533 条是假的(质驱系列每块 584 条其实是一张 388 行 jump 表),现在 `Program.writes_counter()` 为真时不报;⑤`jump -1 always` 是 nop 不是终止(`JumpI.run()` 有 `if(address != -1)` 保护),修前 `坦克大战.msch` 190 条报 182 条不可达,修后全包 9,384→495。横向发现:`equal X null` 在 166 处守卫上恒真(未赋值变量=0、`null.num()`=0),`obv超射程 大.msch` 因此有约 550 条语句从不执行;87 个块引用`message1`/`switch1` 这类**未链接**的方块名。**方法论:每个块报几条这种数字,在换一份语料之前都只是关于你自己解析器的数字。** |
