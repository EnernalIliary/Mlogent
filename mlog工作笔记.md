# mlog 工作笔记(持续更新)

> 为 **Iliary艾铭** 的游戏环境编写 mlog 时积累的规则、参数、模式和踩过的坑。
> **每次交流后追加一节**,不覆盖旧内容;如果旧结论被推翻,在原处标注 `【修正】` 并写清依据。
>
> 源码依据:workspace 内 `Mindustry-Source`(游戏版本 **159.1**)+ `Logic-Docs-v1.1.0`。
> 工具:[tools/msch.py](tools/msch.py)(解析蓝图)、[tools/mlogsearch.py](tools/mlogsearch.py)(检索逻辑)。

---

## 目录

本文件按「先规则、后工具、最后留档」排列。§0–§13 是语言与玩法规则，§14–§15 是工具（§15.x 按时间累积，越靠后越新），§16 是错误留档，§18 是逐次整理的日志。

- **§0** 写代码的铁律（先看这里）
- **§1** 链接与命名
- **§2** sensor / null 语义
- **§3** 物品搬运（核心章节）
- **§4** 超速穹顶专章
- **§5** ulocate 完整参数（源码 + 文档双核对）
- **§6** move vs approach：取货点必须用 move
- **§7** 单位归属判定（标准片段）
- **§8** 已被推翻的旧结论（留档，防止再犯）
- **§9** 排版与注释约定
- **§10** 附录 A：sensor 属性总表
- **§11** 待确认清单
- **§12** 附录：ulocate 之后标准答案的完整数据流
- **§13** 附录 B：全部 86 个命令的格式索引
- **§14** 生成蓝图工具 mschgen.py
- **§15** 静态检查工具 mlogcheck.py（§15.1–§15.21 是工具演进史）
- **§16** 我写错的逻辑清单（生成前对照）
- **§17** Skill 整合包 mindustry-blueprint/
- **§18** 更新日志

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
| 38 | 2026-10-18 | 交叉验证：装上 mindcode（JDK 22 + 预编译 jar），用它的模拟器跑八条探针，六条与我的规则一致、一条 unsupported、一条（跨处理器 read/write）新增蓝图级探针；结论写进 `mindustry-blueprint/EMULATOR-CROSSCHECK.md` 与本节。方法论：**能跑的第二个实现，比多读一遍源码有用** —— 它不读你的注释，也不认同你的假设。 |
| 39 | 2026-10-18 | 第三方实现对照：`A4-Tacks/mindustry_logic_bang_lang` 的 `tools/logic_lint` 证实了我的指令/算子表（theirs-only 为 ∅、45 个 op 双向零差集），并抓出我漏报的 `no-target-jump`（`jump <不存在标签>` 在游戏里变成 -1、静默落下）；顺带补进六条语言事实（`@ipt × @timescale`、`@counter` 隐含 +1 与越界未定义、解析失败变 `noop`、1000 行、`1.2e3` 不合法、变量名宽度）。方法论：**一个第三方实现不需要比你强，只要它独立** —— 它证实的部分给你底气，它多抓的部分给你缺口。 |
| 10 | `@totalPower` | 38 | `@cameraY` |
| 11 | `@itemCapacity` | 39 | `@cameraWidth` |
| 12 | `@liquidCapacity` | 40 | `@cameraHeight` |
| 41 | 2026-10-18 | 单位表补细：武器切分修好（5→35 个带武器）、新增 abilities 与 immune_to、`unit` 精确名优先 |
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
| 28 | 2026-10-18 | **回歸測試落地** `tests/run_tests.py`（12 條 golden digest，覆蓋 check / ir / values / pack / cost / gate / cross），合成用例從 `out/` 移到 `tests/cases/`；`mlog.odd_names()` 從打印塊抽成函數以便斷言。方法論：「用眼睛比對輸出」不是驗證，只是延後發現錯誤。 |
| 29 | 2026-10-18 | **`values` 接 `cross`**：`read` 到别的处理器不再一律 ⊤，两遍分析、刻意不做不动点；`slot_values()` 改按坐标建键（按展示标签建键时「接上了但什么都没发生」）。方法论：「接线失败最安静的样子，是它什么都没做，而不是它做错了。」 |
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

1. **ID 是构造顺序号** —— [Content.java:21](Mindustry-Source/core/src/mindustry/ctype/Content.java#L21)
   ```java
   this.id = (short)Vars.content.getBy(getContentType()).size;
   ```
2. **原版先构造,mod 后追加** —— [ContentLoader.java:57-81](Mindustry-Source/core/src/mindustry/core/ContentLoader.java#L57)
   ```java
   public void createBaseContent(){ ... Blocks.load(); }   // ← 原版方块 ID 在此固定
   public void createModContent(){ mods.loadContent(); }   // ← mod 只能往后追加
   ```
3. **游戏自检 ID 必须连续递增** —— [ContentLoader.java:86-93](Mindustry-Source/core/src/mindustry/core/ContentLoader.java#L86)
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

**① 源码** —— [Tile.java:255](Mindustry-Source/core/src/mindustry/world/Tile.java#L255)

```java
//set up multiblock
if(block.isMultiblock()){
    int offset = -(block.size - 1) / 2;      // 3×3 → -1
    ...
    int worldx = dx + offset + x;            // 以 (x,y) 为中心铺开
```

[Block.java:761](Mindustry-Source/core/src/mindustry/world/Block.java#L761) 同样:`sizeOffset = -((size - 1) / 2)`

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
[ContentLoader](Mindustry-Source/core/src/mindustry/core/ContentLoader.java#L57) 先 `createBaseContent()`、
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
- **`print` 不带引号 —— 起初判错,已按用户纠正改判**:`print by:NOSB(hghg`(34 处)。
  `LAssembler.java:67-69` 只有首尾都是 `"` 才生成字符串常量,否则当变量读 ⇒ 打印出
  `null`。**但从没赋值的变量会出现在游戏逻辑编辑器的变量列表里**,所以"写一个自己的
  名字当变量"是常见的**署名手法**,不是错误 —— 打印出什么根本无所谓,作者要的是那个
  名字出现在列表里。同理"写了不读"的变量也可能只是为了列表可见。
  **改判后的证据分级**(`mlogcheck.py` 的"NEVER defined"块):
  - 只出现在 `print` 里 ⇒ **INFO**,文案 `signature only (it shows up in the editor's
    variable list; print outputs null)`;
  - 只出现在 `jump … equal/notEqual X null` 里 ⇒ **WARN**,恒真但无害
    (未赋值 = 0,`null` 读成 0,只有 `===` 才会假);
  - 其余(参与 `op`/`control`/`sensor` 等)⇒ 仍是 **ERR**,因为算术里它静默当 0。
  效果:全包硬错 **883 → 416**(只改这一处判级)。
- **`set // 说明文字` 是 mlog 的"注释"写法**:变量名用纯标点,右侧是散文。mlog 只有 `#`
  起注释(`LParser.java:98-99`),作者想让注释在变量列表里可见就这么写。原先把右侧散文
  当变量读,`障碍躲避.msch` 一个文件就报 58 条假错。`mlogcheck._comment_stmt()` 现在整行
  跳过 ⇒ 硬错 **416 → 367**。
- **超过声明参数个数的 token 是惰性的**:`LParser` 按下标填语句字段,多的 token 解析完
  就丢。`mlogcheck` 现在按 `instr_semantics.json` 的 `arity` 截断(`defs_of`/`uses_of`),
  这样 `op rand g 255 b` 的 `b`、`jump T always x false` 的 `x`/`false` 都不会被当成读。
  **例外**:署名若写在这些参数槽**内部**(`control enabled reactor enable 0 by bicker`
  的 `by`/`bicker` 正好落在 p3/p4),游戏确实会读它们,仍算 ERR —— 这类约占残余 367 条
  里的 60~70 条。
- **换行丢失只有 1 处**(`control config unloader4 null 0 0 0sensor`):这个包的搬运不是
  批量机械损坏。

#### 边界

- 这里所有结论都建立在"变量名 = 存储位置"上。mlog 的 `read`/`write` 可以按**字符串名**
  访问别的处理器的变量,本扫描没有建那个模型 ⇒ 跨处理器读写看不见。
- 派发表(`@counter`)一旦出现,该块的可达性就不报,**这也意味着真正的死代码会被一起放过**。
- 死存储 4.0% 里有一半来自 `质驱` 系列同一份模板的复制,不能当"作者平均犯错率"。

---

### 15.18 ⭐ 「未定义变量」的五个层:一个检查器的判级是被社区校准出来的

926 份蓝图包(481 份有逻辑 / 1698 块 / 359,131 条语句)作为语料,把最初 **883 条**硬错逐条核对到 **77 条**。中间掉的每一条都不是"漏报",而是**判级被用户纠正**。

| 层 | 含义 | 条数 | 改不改 |
|---|---|---:|---|
| **A 真错** | 名字被读的地方,值真的改变行为 | 77 | 要改 |
| B 恒真守卫 | `jump` 两侧都是常量 ⇒ 分支固定 | 55 | 一般不用 |
| C 无效参数 | 名字落在指令读不到的参数位上 | 944 | 不用 |
| D 死引用 | 形如链接名,但这块处理器没有这个链接 | 788 | 要改(静默失效) |
| E 署名 | 只为出现在编辑器变量列表里 | 5540 | 不用 |

用户给的三条判词构成了这五层的骨架:

1. 「游戏内部的逻辑编辑器会对变量列表,使用自己的名字作为变量名并且不定义是很常见的署名方法」⇒ E 层。`print by:NOSB(hghg`、`set Madeby mineqwwe`、`jump 21 equal colour ender`、`control config Carrot 0914 0 0 0` 全是署名。
2. 「不要判断无效参数。control 的有效参数只有三个」⇒ C 层。
   用户后来补了一句判据:「并不会,最多就会用无效参数」—— **无效参数最坏的结果就是被忽略**,所以 C 层可以放心地不报为错。这句话也是 C 层的全部理由,不必再逐条验证。
   我自己在这层犯过一个**展示**错误:表格的"按变量"一节把 `op rand`/`op floor`/`op abs` 当成变量名列了出来(`op` 的第二个 token 是**运算符号**,不是变量)。成因是 `var_table` 取消息里第一对反引号的内容,而 `op rand g 255 b` 那条警告的文案正好是 `` `op rand` given 3 args `` ⇒ 把 `op rand` 当名字。修法:C 层拆成两节 —— 按变量(真名字落在读不到的参数位)、按语句(参数给多了,列算子名)。
`control` 的 p2–p4 虽被 `num()` 求值,但各方块类型的 `control()` 忽略;`ucontrol` 每个子命令按 `semantic_uses` 算(`flag`/`payTake` 只有一个语义参数);一元 `op` 的第三位永远丢掉。
3. 「所有布尔值的未赋值降级到 warn」⇒ 布尔参数表(`payTake`/`boost`/`control enabled`/`ulocate building` 的 enemy/`status`/`setflag`/`spawnwave`):未赋值 ⇒ 恒 false。

**语言事实(每条都曾让我误判)**

- **`true`/`false` 是注册常量(1 / 0),不是普通变量** —— 这条我判错过一次,而且是当着用户的面判错:`GlobalVars.init()` 的 `GlobalVars.java:54-55` 是 `putEntry("false", 0)` / `putEntry("true", 1)`,而 `LAssembler.var()` 第一步 `Vars.logicVars.get(symbol, privileged)` 就把它们接走了,**根本走不到后面的 `putVar()`**。我只看 `var()` 的字符串/数字分支,就断定 `"true"` 会落成未赋值变量,凭空造出 **653 条假警告**(还写进了文档、给用户解释了"条件反向")。用户一句「Mlog 里面 true/false 是关键字」才纠回来。
  **可控的教训**:判一个名字是不是内建,要查**注册表**(`putEntry` / `logicVars`),不是查**解析函数的分支**;`var()` 先查注册表这一点藏在第一行,最容易只读后半段。
- `lookup` 的结果在**第 2 参**(`LStatements.java:875-909`,第 0 位是 `ContentType` 关键字)。我把它当第 1 参,导致 `ubind u` 全族 23 条假错。
- `ucontrol getBlock x y a b c` 有**三个输出**(`LExecutor.java:491-509`,p3/p4/p5);`within` 的第 4 个值参数才是结果。
- `jump -1 always` 是 **nop** 不是终止(`JumpI.run()` 的 `if(address != -1)`),当成终止会误报整片不可达(`坦克大战.msch` 190 条里报 182 条)。
- `0x`/`0b`/`%rrggbb` 是字面量(`LAssembler.java:87-99`),不是变量。
- **跨處理器 `read`/`write` 必須提前聲明**:目標處理器里那個名字的槽必須先存在,遊戲不會按需新建 ⇒ 寫給不存在的槽是靜默空操作。已實現檢查(`mlog.py ir --msch`,按 link 的相對偏移精確解析目標方塊)。實測(**2026-10 重測,舊數字作廢**):我的庫 625 份里**只有 9 份**的目標真的是另一個處理器、**0 處**未聲明;彩末包 926 份里 13 份、也 0 處。早先記的「586 份」是**把 `read`/`write` 整體算進去了**(絕大多數指向記憶格,格子的地址可以是變量名,不是處理器變量),已作廢。
- `printflush you` / `printflush log` 是**清空 `print` 緩衝**的寫法(作者自己的習慣,不是老版本限制):`PrintFlushI.run` 在 `LExecutor.java:1174-1178` 先判目標是不是有效的 message 方塊,然後**無條件** `exec.textBuffer.setLength(0)` ⇒ 目標是未賦值變量時,緩衝照樣被清掉,只是沒有顯示。所以它不是空操作,是「丟棄待打印的文本」⇒ 已降級成 INFO。
- `format` 是 147 之後才加入的,`select` 更新(`noop` 同理)。用它們可以給藍圖打版本指紋:我的庫 `format` 146 條 / 26 份、`select` 41 條 / 15 份、`noop` 0;彩末包 `format` 5 條 / 1 份、`select` 51 條 / 5 份、`noop` 1 條 / 1 份。
- **跨處理器按名讀寫**:用户指出 `read`/`write` 可以按**名字**访问另一个处理器的变量(高版本特性)。老蓝图库里看不到这种写法,所以对老库「这个变量从未赋值」的判断是可靠的;新库里它是一条合法的"别处赋值"路径 —— 报 A 层之前先确认两份逻辑是不是同一代产物。
- **`noop` = `InvalidStatement`**:`LStatements.java:48-59` 的类名就叫 `InvalidStatement`,`build(LAssembler)` 返回 `NoopI`(空 `run`)。游戏把**解析不了的语句**替换成它,所以 `noop` 不是空行,是**丢失语句的墓碑**。用户给的原因最准确:「可能是版本更新导致的逻辑语句丢失,这也比较常见。特别是高版本逻辑在低版本被使用的时候」。**判 ERR,不是 WARN** —— 用户又纠了一次:「很多时候低版本用高版本语句有 noop 程序基本就死了,这个是特例」。丢掉的正是干活的那条,后面的 `jump` 还照旧指向错位置,所以不是「看一眼就好」而是「必须修」。全包 926 份里只出现 1 次(`死星自动进攻.msch` hyper-processor 第 17 行),那一个恰好是能跑的特例 —— **这就是为什么不能按「我见到的样本」定级**:一次抽样里唯一的一例是良性,而常态是死。
- 形如链接名的名字**不等于**存在这个链接:`control shootp scatter1` 只会被 `validLink(b)` 挡掉,不报错、不崩溃 —— 只有 `.msch` 有链接表可查。

**判级原则**:一个检查器报出的「错误」里,哪些是错误取决于这个社区的写作习惯,不取决于语言规范。所以低置信层会一直存在,关键是每一层都要能说出"为什么这一层不用管" —— 说不出就该并回上一层。`tools/corpus/_err_table.py` 就是把这条原则产物化:同一批 finding,按五层重排给用户看。

**另**:分层的诱惑是"再加一层"。这次多出来的 E 层(真假字面量)是假的 —— 它不来自用户的判词,而来自我读源码时漏了一步。**用户没纠正过的层,要先假设它是我的 bug。**

#**基线是 146，判据是"比基线新"**：`BASELINE_BUILD = 146`（7.0 Build 146，
2023-09-04 发布）—— 在它里面就有的语句属于基线，**永不报告**；只有基线之后新增的
才可能让一份蓝图在别人机器上跑不了。代码写 `floor > BASELINE_BUILD`，
不硬编码 147。基线内的代表性条目：`read`/`write` 按名字访问处理器或 message、
`effect`、`sync`、`ucontrol autoPathfind`、内容 ID 传感器（`sensor x b @id`）。

## 15.19 版本闸门:一份蓝图能跑在哪个 build 上

蓝图**不存版本号**,所以只能从「它用了哪些语句」倒推。`check` 现在会打两行:

```
[INFO] L0   version gate: uses select -- needs build >= 150; on anything
            older the line is replaced by noop and silently does nothing
```

`mlogagent report` 的 VERDICT 末尾也会多一截 `| build >=150`。

**能锚定的只有六条**(出处都写在 `mindustry-blueprint/BUILDS.md`):

| 语句 | 首次出现 | 发布说明原话 |
|---|---|---|
| `effect` / `sync` | 146 | "Added logic particle effect instruction" / "Added logic sync instruction" |
| `format` | 147 | "Instructions for displaying text and applying drawing transformations for logic processors" |
| `select` | 150 | "Added 'select' (ternary) logic operation" |
| `bullet` | 157 | "Added a processor instruction for spawning bullets"(157.3) |
| `getblock` | 157 | "Added a world logic spatial query instruction"(157.4) |

146 是分水岭:大部分人在这版停了一年,所以「什么都不用」的下限就是 146,**低于 147
不报告**,否则每一份老逻辑都要响一次。

**`noop` + 新语句 = 版本漂移**(这是这条闸门真正的用途):同时满足「用了 ≥147 的语句」
和「有 `noop` 行」时,不再分两条报,直接把原来那条通用 `noop` 错误替换成结论:

> N noop line(s) plus statements that need build >= 150 -- this is version drift,
> not a typo: a line written for a newer build was replaced by InvalidStatement
> when opened on an older one, so it now runs as nothing and whatever it did is
> gone.

单看 `noop` 时仍报 **WARN** 并列出三个成因(比「版本不一致」更全):解析异常
(`LParser.java:143-147`)、特权语句落在普通处理器里(`:150-152`)、mod 语句但 mod 没装
(`:166-173`)。

**为什么 `format`=147 值得单独记**:它是「文本显示」那一代工具链的入口,`{}` 占位符
语法从 147 到 159 没变过(用户确认),所以看到 `format` 就能断定「这份逻辑 ≤147 的客户端
一定跑不了」。

### 15.20 跨處理器讀寫:`mlog.py cross`(讀到的到底是什麼)

`read`/`write` 按**名字**訪問另一個處理器的變量:

```
set  count 42            # 處理器 A 自己聲明
read n     proc1 "count" # 處理器 B 讀 A 的變量
```

**關鍵理解(我先前搞錯過)**:可讀的那個槽就是**目標處理器自己的變量** —— 所以
`write` 不是必須的,`set` 就夠;而這正是"必須先聲明"的原因。另一側的
`write v proc1 "count"` 只是給這個槽多加一個可能的值。

所以 `(P, 名字)` 的值 = **join(P 自己對該名字的所有賦值, 所有外部 `write` 進來的值)**。
處理器各跑各的節拍,join 是唯一誠實的答案:兩個處理器寫不同常量、或寫在條件分支裡,
結果就退化成 ⊤。

`mlog.py cross <blueprint.msch>` 輸出四類:

| 類別 | 意思 |
|---|---|
| `never assigned` | 目標處理器從沒給這個名字賦值 ⇒ 讀到的**恆為 null** |
| `always null` | 有寫入,但每個寫入都是 null |
| `constant` | 所有寫入同一個值(分支折疊就有依據了) |
| `written, never read` | 有人寫、沒人讀 |

**實測(626 份我的庫 / 926 份彩末包)**:

- 我的庫:2420 塊里只有 **3 個藍圖**(28 個 cross read)真的跨處理器讀;`never assigned` 8、
  `dead-writes` 20、`constant` 0。
- 彩末包:1698 塊里 **0 個**藍圖有 cross read。
- 所以這條分析**命中率極低(0.5%)** —— 它屬於「點開就說話」的專用檢查,不是 linter。
  真正普遍的 `read`/`write` 是**記憶格**:`read x cell1 "slot"`,那裡的字符串是
  **地址變量名**,不是處理器變量。**這兩者必須分清**(我先前把兩者混為一談,把
  「586 份用跨處理器」寫進了筆記,已作廢)。

**版本**:按名字讀寫另一個處理器 / message 方塊是 **v7(build 146)** 才有的;v6 的 `read` 只能拿數字下標訪問記憶格 ⇒ 一份用它讀寫處理器的藍圖**不可能跑在 v6 上**(但 146 低於 147 基線,不進 version gate,只在 `cross` 的統計行提示)。

邊界:連結必須落在**另一個邏輯方塊**上才算跨處理器(指向記憶格/顯示器的 link 直接跳過,
否則會憑空造出邊);`read`/`write` 的字符串若不是字面量(是變量)則不解析;不建模
「誰先跑」——時間差一律用 join 吸收。

## 15.21 `values` 吃 `cross` 的知识：跨处理器的读不再一律 ⊤

`cross` 回答的是"另一个处理器里这个槽到底是多少"，`values` 之前完全不知道这件事 ——
`read x processor1 "name"` 一律当未知写者（⊤），于是在多处理器地图上一半变量不可知。
两者接上以后，`values --msch` 走**两遍**：

1. 第一遍：对每个处理器跑 `analyze()`（此时它的跨处理器读仍是 ⊤），再用
   `mlogcross.slot_values()` 把「某处理器 `read` 某链接的某槽」解析成具体值；
2. 第二遍：同一程序带着这张表重跑，`read` 就落到真实值上。

**只迭代一次，刻意不做不动点**：第一遍里那些读本身是 ⊤ 算出来的，再迭代会把
"上一轮的猜测"当成"这一轮的事实"，报出模型没有的置信度。

### 为什么未声明的槽是 null 而不是 0

```java
// LogicBlock.java  (Readable.read)
LVar ret = executor.optionalVar(varName);
if(ret == null){
    output.setobj(optionalLink(varName));
    return;
}
```

`optionalVar` 只查**已存在**的变量；查不到就退化成 `optionalLink(名字)` ——
那是个**链接查找**，没有同名方块就是 `null`。这也解释了为什么 `write` 到未声明的名字
静默无效（`at == null -> return`），以及为什么必须先声明。

### 实测（`ILOS.test.msch`，micro-processor @(0,2)）

`read MX processor1 "Mxp"` / `read MY processor1 "Myp"`，而整张蓝图里没人给这两个槽赋值：

| | 之前 | 之后 |
|---|---|---|
| folded | 0 | 9 条 `read`（对 7 个槽） |
| resolved branches | 0 | 8（`jump 64 lessThan MY 0` → never …） |
| provably null | 0 | 8（`MY`、`MX`） |

### 接口坑

`slot_values()` 一开始按 **Unit.label** 建键，而 `cmd_values` 拼的标签是
`f"{p} [{t.block} @({x},{y})]"` —— 两边永远对不上，于是"接上了但什么都没发生"，
输出里连 `cross knowledge` 那行都不打印。改成按**方块坐标** `(x, y)` 建键后立刻生效。
教训：**分析结果不要用展示字符串当键**。

### 边界

- 只在 `--msch` 时可用：单个 `.mlog` 没有同伴可读。
- 蓝图得是**完整**的。别人地图上的处理器不在这个蓝图里 ⇒ 它的槽看不到 ⇒ 报 null
  可能只是"没一起存下来"，输出里那句 caveat 写的就是这个。
- 只迭代一次（见上）；`write` 的**时序**不建模（谁先跑不确定，取 join）。

## 15.22 写逻辑前查什么:`unit` / `block` / `find`

**起因**:用户问「如果我要你写逻辑,你还缺什么」。我列了四样,其中三样是"游戏事实"(单位属性、方块配方、找参考实现),用户说「大部分情况下都是跑起来没问题,我对你的要求不高。现在先能跑再说。然后你把三样加上吧」。所以验收线是**能跑**,不是效率 —— 数据表的取舍也按这个来:只求"写之前不用猜",不求穷尽。

### 三条命令

| 命令 | 回答的问题 | 数据来源 |
|---|---|---|
| `mlog.py unit flare` | 速度/血量/护甲/体积/载货/会不会飞/武器 | `tools/units_from_source.py` → `unit_attrs.json`(39 单位) |
| `mlog.py block silicon-smelter` | 吃什么、产什么、装多少、多少电、几×几 | `tools/blocks_from_source.py` → `block_attrs.json`(200 方块,16 条完整配方) |
| `mlog.py find "wireless overdrive"` | **别人怎么解决的** | 扫游戏存档里的全部蓝图,按名字/描述/信息板/变量名/指令打分 |

`find` 之前不存在,而它正是上次写无线超时唯一救了我的动作(去读那份标准答案)——当时只能靠我想起来。

### 抽数据时踩的四个坑(都写进脚本注释了)

1. **默认值正则会把下一个字段的值当自己的**:`UnitType.java` 是 `float speed = 1.1f, boostMultiplier = 1f;` 这样成组声明,逐字段匹配会得到 `health -> 1f`。必须先按逗号拆组。
2. **块体结尾是 `}};` 不是 `};`**(双花括号初始化),且缩进因文件而异。硬编码 8 空格 ⇒ 抽出 **0 个单位**,而且不报错。
3. **配方有两种写法**:`consumeItems(with(...))` 与 `consumeItem(Items.x, n)`(单物品,`graphite-press`/`silicon-arc-furnace` 这类)。只认前者时"完整配方"只有 10 条,加上后者是 16 条。
4. **物品名是 Java 字段名**:`phaseFabric`/`surgeAlloy`。必须转 kebab(`phase-fabric`)才和 content 名对得上——写错的表看着完全正常,只是查不到。

### `find` 的性能:33 秒 → 0.7 秒

| 阶段 | 耗时 | 原因 |
|---|---|---|
| 直接扫全部 626 份 | 152 s | `BADAPPLE!!.msch` 一个块 **56 万条语句**,`mlogir.parse` 就要 24 秒;`Linux on mlogv32.msch` 是 **16 MB** |
| 只跳过超大块 | 33 s | 仍是 `msch.parse_file` 在 16MB / 7.6MB 像素画上花时间 |
| 加 `--max-stmts 5000` + `--max-bytes 2M` | **9.4 s** | 生成式艺术与模拟器镜像不是参考逻辑 |
| 加 mtime 缓存 | **0.7 s** | 命中缓存后只做打分 |

顺带把 `mlogir.parse` 换成 `_cheap_profile()`(逐行取助记符/标识符/引号串,不建 IR):搜索只需要"这些词在不在",不需要语法树。

### 物品接受规则:五档,不是「收 / 不收」

写物流逻辑最容易静默失败的一条是「搬错地方」——屏幕上什么都不发生。规则全部落在
`BuildingComp.acceptItem` 与 `Block.consumesItem` 两行:

```java
// BuildingComp.java
public boolean acceptItem(Building source, Item item){
    return block.consumesItem(item) && items.get(item) < getMaximumAccepted(item);
}
// Block.java -- itemFilter 是 afterPatch() 里按消费者填出来的布尔数组
public boolean consumesItem(Item item){ return itemFilter[item.id]; }
```

推论:**没有物品消费者的方块,默认谁都拒收**。于是 `block_attrs.json` 的 `accepts` 分五档:

| 值 | 判据 | 含义 | 例 |
|---|---|---|---|
| `any` | 覆写 `acceptItem` 只比容量 | 什么都收 | `core-shard`、`container` |
| `recipe` | 继承默认 + 有 `inputs` | **只收配方里的** | `silicon-smelter` 只收煤和沙 |
| `ammo` | `ItemTurret` 的 `ammo(...)` 列表 | 只收弹药 | `duo` 收铜/石墨/硅 |
| `custom` | 覆写里有路由/状态条件 | 收,但要看配置/热量/是否空 | `sorter`、`incinerator`、`launch-pad` |
| `none` | `acceptItem` 就是 `return false;` | 一律不收 | `landing-pad`、`item-source` |

- **别用 `itemCapacity` 推**:多数工厂根本不写 `itemCapacity`(默认 10),我第一版拿它判「容量 0 ⇒ 不收」,把 `silicon-smelter` 判成 `none`。
- **`custom` 只回答「可能收」**,「现在收不收」取决于运行时状态(sorter 配置、router 是否空、焚化炉是否通电),静态查不出来 —— 这与「不判值对错」是同一条边界。
- **`unclassified()` 守卫**:手写的三张集合(any/custom/none)靠扫描 `core/src/mindustry` 里所有 `acceptItem` 覆写来兜底,游戏加了新方块类时会警告「这个类没分类」,防止表悄悄过期。
- 反查:`mlog.py block --accepts coal` 分组列出「配方输入 / 弹药 / 什么都收 / 有条件」。

### 边界(写在 SKILL 里)

- `unit`/`block` **只列源码写了的字段**,缺的是引擎默认值(`unit` 会标 `(default X)`)。不要凭记忆补。
- `block` 没有"每种方块接受哪些物品"的过滤器表(`itemFilter` 只在少数方块上设),这一条仍未做。
- `find` 的打分**故意粗糙且可解释**:输出带 `(text N, name N, opcode N)` 拆解,匹配错了能看出为什么错,而不是给一个神秘数字。
- 缓存里存的是"文件 mtime + 每块的 profile",蓝图改了会自动失效;`--rebuild` 强制重扫。


### 15.23 自动打标签:标签到底能不能从内容推出来

标签是分面的:颜色=维度、私有区图标=值的身份、末尾文字=值名。70 个值 / 14 个维度,
`000标签排序.msch` 把 69 个值全挂在一份蓝图里当配色卡。**全部手打** —— 所以问题是
"哪些值的出现与否,其实是内容的函数"。

做法不是手写规则,是**学一半、测另一半**:把 625 份按文件名的 sha1 分成两半,
在一半上学 `值 -> 方块/逻辑记号`(`train`),在另一半上量精确率(`precision`)。
一个方块能当签名,要同时满足:出现在该值 ≥75% 的文件里、全语料占比 ≤20%、
lift ≥0.45。**`UBIQUITOUS = 0.20` 这一条是关键** —— `micro-processor` 在每份带逻辑的
蓝图里都有,不排掉的话「含微处理器」这条规则会在几乎全语料上开火(实测平均精确率
44% → 5% 那次就是它)。同理只保留**单个**签名:`cryofluid-mixer` 作为 冲反/温差/冷冻
的第二签名会把三条规则同时污染到 6%~27%。

**结果:43 个值能学到规则,其中 24 个留出集精确率 ≥70%**,可以直接用:
t5厂、世处、冲反、分裂、力墙、厄兆、塑钢、大硅、小超、幽灵、抽水、核心蓝图、气旋、
水炮、涡轮、温差、熔毁、着陆、窑炉、自冷、蜂群、质驱、钍反、雷光。
剩下的(<70%)是判断题,或者根本不是内容的函数:

- `数量`(`1…9` / `10~19` / `20~29` / `极多`):高段确实等于「同一种方块的最大重复数」
  的中位数 16 / 31 / 44,低段 1–9 与核心数、超频数、逻辑块数都不相关 ⇒ 不可推;
- `品质`(`常用` / `未分类或低效`)、`系列`(`ILI`)、`实用`:主观判断;
- `无线`、`火控`、`兵控`:逻辑形态能提示(`ulocate`+`ucontrol`+`ubind`、`radar`),
  但同一份蓝图常常三种都沾 ⇒ 精确率 15%~24%,不建议自动;
- `冷冻`、`串联`、`绿带`、`白沙`、`黑沙`、`硫化`:要么是地形/布局,要么是作者的
  组织习惯,方块层面留不下签名。

**写回是外科手术式的**:`.msch` 的正文是 zlib 流,标签只是 tags 里的一个 JSON 字符串。
所以 `rewrite_labels()` 解压 → 走到 tags 结束的位置(`Reader.pos`)→ 只重写 tags 段 →
**把剩下全部字节原样接回去**再压缩。这样非逻辑方块的配置(连线数组等)一个字节都不会动,
也不会踩到导出工具「226 skipped」那个坑。实测往返 66 方块 / 1 逻辑块 / 16 标签无损。

命令:`python tools/corpus/label_auto.py`(学习+留出集报表)、`--suggest F.msch`(只出可信建议)、
`--apply F.msch --out DIR`(写回副本,永不覆盖原件)。

### 15.24 作者标签约定:我产出的蓝图打 `[blue]DeepSeek`

用户在自己的标签体系里新开了一类 **`[blue]DeepSeek`**,用来标记"这是 DeepSeek 做的"。
以后我用 `mschgen` 生成蓝图,`labels=` 一律写这一条:

```python
mschgen.Blueprint(name=..., description="...逻辑 by [#8abcd1]DeepSeek[]",
                  labels=["[blue]DeepSeek"])
```

已落到 `tools/gen_thorium_guard.py`(钍反防爆 v1),并配 `tools/install_thorium_guard.py`
(生成 → 断言标签与署名 → 复制进 `%APPDATA%/Mindustry/schematics` → 回读校验)。

和 ILI 的区别:ILI 是**作者身份**(谁的库),这个类是**作品来源**(谁写的逻辑);
一份蓝图可以两条都有,不冲突。

### 15.25 生成蓝图一律走 `mlog.py gen`,不要自己拼 base64

`mlog.py gen` **默认就把 paste-ready 的 base64 打到 stdout**,`--out` 还能存成文件;
`mschgen.py:582` 同样是 `print(base64.b64encode(data).decode())`。
所以在聊天里贴蓝图码的正确做法是:跑 gen,把它打印的那一行原样贴出去。

我犯过的错:自己写 `"bXNjaAF4n" + b64[8:]` —— 前缀 9 个字符却只砍 8 个,长度变成
`4k+1`,游戏报 *Length of Base64 encoded input string is not a multiple of 4*。
**文件本身没问题,坏的是拼字符串那一步。**

顺带弄清的两件事:

* 蓝图码前缀**不一定是 `bXNjaAF4n`**。它取决于 zlib 压缩等级:游戏自己写出来是
  `78 9c`(默认),本仓库的 `mschgen` 用最高压缩 `78 da`,于是第 11 个字符不同
  (`bXNjaAF42mPg...`)。**两种都合法**,游戏只认解码后的 `msch` 魔数。
* `--with-block block@dx,dy` 的 `dx,dy` 是**相对处理器**的**方块中心**,和 `--link`
  同一套约定。帮助文本原来写成 "CENTER coords",容易读成绝对坐标 —— 已经改掉。
  传绝对坐标会让方块整体偏移,`link_report()` 于是警告
  `link target ... is not covered by any placed block`(那个警告本身是对的)。

### 15.26 写逻辑的取舍:枚举 vs 跳表 vs 内存格

用户问「为什么用枚举」之后查清的一件事:**枚举不是语法逼出来的,是"造表不比摊开便宜"**。

先纠正我原来的错觉。我以为 `sensor` 的第三个参数必须是字面量,所以"每个物品一行"是强制的。实际:

```java
// LExecutor.java:668-719  SenseI.run()
Object target = from.obj();
Object sense  = type.obj();
if(target instanceof Senseable se){
    if(sense instanceof Content co){ to.setnum(se.sense(co)); }
```

`sense` 是**运行时对象** ⇒ `sensor n core it`(`it` 里装 `@copper`)合法,循环读是能写的。

不能写的是"按下标取内容物":`@copper` 是常量对象,没有 `@[i]` 这种写法。所以要按序号取表项,必须自己造表 —— 而造表的价格和摊开写基本相等:

| 写法 | 每项成本 | 选定条件 |
|---|---|---|
| 枚举(摊开) | 2 行:`sensor` + 比较 | 列表固定、每项只比一个值、要一眼复查 |
| 跳转表 `op add @counter @counter i` | 也是 2 行:`set it @x` + `jump` | 列表 >20,或每项还要顺带做好几件事 |
| 内存格存对象 | 1 块 + N 次 init `write` + 每圈 `read` | 列表要运行时可改;**对象入格子只有 build 160+** |

实测账(着陆调度,13 种物品):枚举 26 行 / 跳表 30+ / 格子 14+10,**一个都没省**,而枚举的状态最少(`i`、`best`、出口全都不用)。

另外三条非价格因素:

1. **平局要有确定的解**。枚举用严格比较保序(`jump s greaterThanEq n mn`);循环版照样得把这条规则写出来,省不掉。
2. **列表要能一眼复查**。13 个物品摊在代码里,扫一遍就知道"考虑哪些资源";藏进格子就得靠注释。
3. **列表由生成器持有**。物品数组是一个 Python list(`tools/gen_*.py`),加一项 = 改一行 + 重新生成;手改 mlog 清单一定会漂。

反面条件:**物品 >20**、**列表要别人在游戏里配**、**每项还要顺带做别的事** —— 这三条成立时才该上表。

## 15.27 死循环:`@this` 守卫的自旋(极性决定一切)

**一句话**:`jump <head> strictEqual ctrl @this` 这种"守卫恒真"的自旋,现在 `check` 会报 ERR;但**判定必须看守卫的极性**,不看极性就会把整个语料报一遍。

### 语言事实
- `@this` 是处理器建筑对象;`@controller` 读到的是"当前控制这个单位的处理器建筑"(`UnitComp.java:319`)。
- 全树只有两处写 `controller = `:`LExecutor.java:325` 与 `:329`,**都属于 `ubind`** ⇒ `ucontrol` 永远不会把单位认领给本处理器。
- 所以 `ubind @flare` 一执行,`@controller == @this` 立刻成立,并且**一直**成立。

### 于是极性决定结论

| 守卫 | 体内有 `ubind <类型>` | 结论 |
|---|---|---|
| `equal` / `strictEqual … @this` | 有 | 第一遍就恒真 ⇒ **永不退出**,其后所有语句都是死的。ERR |
| `notEqual … @this` | 有 | 第一遍就恒假 ⇒ 循环一遍就结束,是"不要抢别人已绑的单位"的标准写法。**不报** |
| 任意 | 无(或只有 `ubind null`) | 单位永远不会被认领,跳转成不成立取决于运行时状态。**不报** |

### 三次误报(这条规则的学费)
1. 首版把 `ubind` 当"环内无推进" ⇒ 报 10 处 ERR。实际 `ubind` 每轮换一台,循环会退出。
2. `ubind_real` 算好却没存进元组,报告循环读到上一轮的残留值 ⇒ 该报的没报。
3. 剩下 9 处 WARN 全是 `notEqual` 极性 —— 用 `ubind` 认领后守卫立刻变假,那正是能工作的"防抢单位"写法。

**最终量测**:真实语料 627 文件 / 900 块(1521 块因 >5000 语句跳过),**该形状 ERR 0 处**;唯一命中是我审的那份 AI 生成逻辑(`out/_ai-wireless.mlog` L6)。`tests/cases/spin.mlog` 与 `tests/cases/spin-ok.mlog` 把两种极性钉住。

### 顺带修掉的一个系统性漏洞
`analyse()` 自己拼语句表,**只认数字跳转**;`loop:` 这种标签跳转所有 CFG 规则都看不见(`prepare()` 只在 `--cost` 那条路上做解析)。现在 `analyse()` 入口先把 `jump <标签>` 改写成 `jump <下标>`,所有规则一起受益 —— 手写逻辑终于和生成逻辑受同一套检查。

### 边界
- 只覆盖"守卫里出现 `@this`"这一种;`jump loop notEqual on 0` 这类"等外部状态"的自旋不报(真实语料 0.33 条/块,报了只会淹没真结论)。
- 模拟也不免检:要复现这条,得先构造"地图上有某台单位、且已被本处理器认领"的世界状态;喂不到场景时模拟器会报一切正常。

## 15.28 第二实现交叉验证：mindcode 的模拟器

我一直说「mlog 语义只有 `LExecutor.java` 一个权威」——这句话现在可以说得更好：
另一份**独立实现**存在，而且能跑。

`cardillan/mindcode`（Java、MIT、172★、持续维护到 2026-10-17）是 Python 那样
"高级语言 → mlog"的编译器，自带一个**处理器模拟器**。它不读我这份源码，
所以它对同一段 mlog 的结果是独立的第二个声音。

```sh
# 代码
java -jar mindcode.jar pm probe.mlog --run true
# 整张蓝图（处理器之间用 read/write 通信，要真的有两个处理器才测得到）
java -jar mindcode.jar ps probe.msch --run true --run-steps 2000
```

需要 **JDK 22**（jar 的 class file 是 66.0，JDK 17 直接 `UnsupportedClassVersionError`），
预编译 jar 在 GitHub Releases（31.6 MB），**不需要 Maven 构建**。

八条探针的结果（`out/probes/p1..p8`，见 `mindustry-blueprint/EMULATOR-CROSSCHECK.md`）：

| # | 断言 | 结果 |
|---|---|---|
| P1 | `equal <未赋值> null` 恒真 | ✅ 跳了 |
| P2 | `op logn r 0 2` → null | ✅ |
| P3 | `1/0` → null | ✅ |
| P4 | `sensor @unit @dead`（null 单位）→ 1 | ✅ 打印 1 |
| P5 | `print <未声明>` → `null` | ✅ |
| P6 | 记忆格未写过 → 0（不是 null） | ✅ |
| P7 | `ubind` 后 `@controller == @this` | ⏸ 模拟器不支持 `ubind` |
| P8 | `read` 只读得到对方**已声明**的变量；`write` 到未声明名字不建槽 | ✅ `A=7 B=null C=null` |

P8 是新加的蓝图级探针：一个处理器 `set declared 7`，另一个
`read a processor1 "declared"` / `read b processor1 "nope"` /
`write 99 processor1 "fresh"` / `read c processor1 "fresh"`，
输出 `A=7|B=null|C=null|`。**`write` 到未声明的槽确实什么也不做** ——
这条正是 `mlogcross` 与 `mlogcheck` 那句 "the slot must be declared there first" 的依据。

**方法论**：一致的六条从"我读源码得出的结论"升级成"两个独立实现都这么算"，
文档里可以标 **双实现确认**；不一致时以 `LExecutor.java` 为准，再查是谁没跟上版本。
模拟器**不能**替我看世界：没有单位、没有战场、`ubind`/`ucontrol` 不支持、
`sensor` 只支持少数属性 —— 凡是要"真有一台 flare 被本处理器认领"才会发生的 bug
（比如 §15.27 那条死循环），它和我一样瞎。

## 15.29 第三方实现的两件事：证实了指令表，抓出了 no-target-jump

`A4-Tacks/mindustry_logic_bang_lang`（Rust，GPL-3.0，2023-07 起，`tools/logic_lint` 是一个独立的 mlog linter）里的 `lints.rs` 有一张按语句形态写的变量位表（`LINE_PAT`，下标 0 是助记符本身）。拿它和我的 `instr_semantics.json` 对了一遍：

- **指令：他们有的我全有**（theirs-only = ∅）。
- **算子：45 个名字双向零差集**；我多 6 条 —— `bullet`、`clientdata`、`noop`、`playmusic`、`printchar`、`query`。
- 他们的 `draw print v v _` 把第三参标成常量对齐，与我的 `draw col` / `draw print` 序数碰撞处理一致。

这是我的指令/算子表第一次被**独立实现**证实（mindcode 的模拟器只证实了语义，没证实表）。

**他们抓到我一个真缺口**：`jump nowhere always`（跳到一个不存在的标签）在我这里报 `no issues found`。原因：`jump` 的 arg0 是跳转目标、不是变量，我把它排除在 `uses` 之外，于是**无法解析的标签对我是隐形的** —— 而这正是他们 `NoTargetJump` 那条要抓的。

游戏里的行为：`LParser.java:195-198` 用 `jumpLocations.get(location, -1)`，标签不存在就是 **-1**；而 `JumpI.run()` 有 `if(address != -1)` 保护 ⇒ **这一跳什么也不做，继续往下执行**。所以它不崩、不报错，只是"少跳了一次"。

已加 `WARN  no-target-jump`（`mindustry-blueprint/tools/mlogcheck.py` 的 `analyse()`，紧接 `n = len(stmts)` 之后）：

```
`nowhere` is not a label in this program, so the game turns this into a
jump to -1, which does nothing; execution just falls through
```

### 教程里值得补进去的六条语言事实

来源 `examples/learn.md` / `examples/reference.md`（取事实，不取原文 —— 对方是 GPL-3.0）。

| 事实 | 不记住会怎样 |
|---|---|
| 每 tick 有效预算 = `@ipt × @timescale`（`sensor $ @this @timescale`） | 只看 `@ipt` 会把调速后的产能算低一倍 |
| 写 `@counter` 生效的是**下一次**位置，所以 `op add @counter @counter n` 的入口在 **n+1 行** | 派发表整体偏移一行 |
| `@counter` 越界（N<0 / N≥行数 / 非整数）是**未定义行为** | 派发表不自己钳制，表项少一行就跳进不可知处 |
| 解析失败的语句**整行变 `noop`**（编辑器显示 Invalid），不是"忽略某个参数" | 会把"整行失效"误诊成"参数无效" |
| 逻辑上限 1000 行；`1e4` 合法、`1.2e3` 不合法 | 生成器写出游戏解析不了的数字 |
| 变量名几乎任意（除空白与 `"`、`#`、`;` 外都能入名） | 按 C 标识符规则写 parser 会切错 |

另有两条工程事实：连发两次 `printflush message1` 是"清文本缓冲 + 清 message"的惯用法（与已记录的 `PrintFlushI` 无条件清缓冲一致）；多处理器指令级无原子性，读-改-写会丢更新。

方法论：**一个第三方实现不需要比你强，只要它独立 —— 它证实的部分给你底气，它多抓的部分给你缺口。**

### 15.30 逻辑书校正了什么(A4-Tacks《learn-mindustry-logic》)

书在 `C:\Users\lliary\src\learn-mlog`(`pages/` 32 篇)。吸收方式:**只取事实和判据,不搬原文**(书是 CC 系协议,我的仓库是 MIT)。

#### a. 三个算子各不相同 —— 我原来只写对了一个

`Mindustry-Source/core/src/mindustry/logic/LogicOp.java:12-14` 逐字:

```java
idiv("//", (a, b) -> Math.floor(a / b));
mod ("%",  (a, b) -> a % b);              // Java 截断取余
emod("emod", (a, b) -> ((a % b) + b) % b); // 结果非负
```

我的 `mlogval._BIN_EXACT` 原来把 `idiv` 写成 `trunc`(对负数错)、`emod` 写成 `fmod`(对负数错)。修后:

| 表达式 | 之前 | 现在 | 判据 |
|---|---|---|---|
| `idiv -7 3` | -2 | **-3** | floor |
| `mod -7 3` | -1 | -1 | 截断(不变) |
| `emod -7 3` | -1 | **2** | floor-mod |

恒等式 `a == (a idiv b) * b + (a emod b)` 现在成立(`-3*3+2 == -7`),用 `mod` 则不成立 —— **这条恒等式就是选对算子的判据**。

#### b. `emod` / `ushr` 是 v150 新增 ⇒ 版本闸门要看算子名

书脚注 2、4。`instr_semantics.json` 的 `ops.emod/ushr.min_build = 150`,而 `build_floor()` 原来只看助记符 ⇒ `op emod` 被算成基线 146。修法:新增 `_load_op_builds()` 读 `ops[*].min_build`,在 `build_floor()` 里 `if mnem == "op"` 时按第二个 token 查。

教训:**"`op` 是一条语句"是过期的抽象** —— 它是 45 个算子共享的语法外壳,版本属性挂在算子上。

#### c. `ucontrol` 也会认领单位 —— 我的死循环规则改了一半

书 `17-unit-control.md` 说"任何控制命令都会把单位标记为被当前逻辑控制"。查 `LExecutor.java:304-340` 的 `UnitControlI.checkLogicAI()`:`la.controller = exec.thisv.building()`(`:325`/`:329`),而 **`ubind`(`:186-199`)与每条 `ucontrol`(`:347`)都会调它**。所以旧注释"`ucontrol` never claims a unit"是错的。

规则改成三条同时成立才报 `ERR`:

1. 守卫比较里有 `@this`,极性是 `equal`/`strictEqual`(否则一认领就为假,循环一遍就退出 —— 那正是手写"防抢单位"的样子);
2. 环内出现 claimer:`ubind <非null>`,或 `ucontrol <除 unbind/within 外>`;
3. **顺序**:认领发生在守卫读取之后(`j < last_sense`)—— 先读后认领 ⇒ 守卫为假 ⇒ 正常退出;先认领后读 ⇒ 恒真 ⇒ 永不退出。

全语料(627 文件 / 900 块)仍是 **0 处**,唯一命中是那份 AI 生成的无线超逻辑。

#### d. 编辑器显示名与文本名错位

`LogicOp.java:32` `not("flip", a -> ~(long)(a))` ⇒ **文本写 `not`,编辑器显示 `flip`**;而 `notEqual` 在编辑器里显示为 `not`。工具解析的是文本,内部不受影响;但**用户照着编辑器念名字**、或**把编辑器里看到的 `not` 写回去**,就会变成另一个算子(浮点比大小 vs 按位取反)。

#### e. 还没落盘、但值得记的

- `@counter` = "当前行之后将要执行的行号";`@thisx/@thisy` ≡ `sensor @this @x/@y`;`π` ≡ `@pi`;`@degToRad`/`@radToDeg`。
- **控制命令间隔 > 10 秒会丢控制状态**。
- `ucontrol within` 也算控制命令;纯测距用 `op len`。
- `@ctrlFormation` 已删,值被 `@ctrlCommand` 复用。
- `ucontrol build` 的第 5 参可传一个建筑,把它的配置复制过去(自我复制逻辑的写法)。
- `pingX/pingY/pingText` 约 >157.4 才有。
- 多控互换 `@unit` 的惯用法:`set tmp @unit; ubind unit2; set unit2 tmp`。

### 15.31 「语料里的写法」：把风格变成一条命令

`find` 只回答「谁做过」,不回答「写成了什么样」。要写出像人写的东西,缺的是后者:变量怎么起名、循环用哪种形状、一圈几条指令、最后怎么收尾。这些全在语料里,但以前只能靠人翻。

`mlog.py style <关键词...>` 把六个可模仿的维度打出来:`naming`(作者的私有词汇)、`flavour`(dotted/underscored/中文/普通)、`shape`(派发表、`select`、`wait` 节拍、命名跨处理器槽、`ubind`+`ucontrol`、消息板)、`cost`、`links`、`opens`/`closes`。

三个实现上的坑,都值得记:

- **枚举槽不是变量**。第一版把 `parts[1:]` 全当名字收集,于是 `naming` 的头几名是 `strictEqual`、`always`、`greaterThan`、`add` —— 全是 op 名和跳转条件。修法是按助记符跳过关键字位(`op`/`ucontrol`/`draw`/`control`/`ulocate`/`getblock`/`lookup`/`radar`/`uradar`/`status`/`fetch` 跳第 1 位,`jump` 跳第 2 位,`jump N always x false` 再跳 3、4 的补位)。
- **文件名必须进检索**。语料文件名是中文描述,只搜描述和信息板时 `钍反 防爆` 命中 0;把 `path.lower()` 拼进 `hay` 之后 41 条。
- **同一文件的多个处理器会霸占前几名**。`Phase-Bridge 15 Landing Pads` 两个处理器写同一份程序,top3 里出现两次。改成按文件去重、标注 `(+N more block(s) in this file)`。

`--code N` 可以连源码一起看 —— 命名和收尾习惯光看统计是学不到的。

## 15.32 补数据：sensor 属性表、单位武器明细、版本基线

上一节列的四条缺口里，数据占了两条。这一节是补的过程与结论。

### sensor 的 75 个属性

`LAccess.java` 的 enum 体里 75 条，其中 3 条带参数（`shoot`/`shootp`/`config`），
这些也正是 `control` 能写的。脚本 `tools/sensor_from_source.py` 抽结构，
**说明是我手写的** —— 官方文档只给名字，而猜错名字的含义是这个项目最贵的一类错误。

两条当年真踩过的：`@heat` 在力墙投影上是"已损失的盾量"（不是热）、
`@size` 对字符串返回 UTF-16 长度（不是方块边长）。

### 单位武器明细

旧解析只读 `bullet = new XBulletType(a, b)` 的**构造参数**，而 `quad` 写的是
`bullet = new BasicBulletType(){{ ... }}`，数字全在 bullet 自己的块里 ⇒ 表里只剩"1 weapon, reload 55t"。
现在按 `new Weapon()` 切块、在块内找 `bullet`，再在 bullet 之后的文本里找
`damage`/`speed`/`lifetime`/`pierce`/`shots`。`flare` 于是从"1 weapon"变成
"BasicBulletType 2.5 speed / 9 damage, reload 80t, 3 shot(s)"。

**教训**：解析器只认"参数"时，会静默丢掉"字段"。判断依据不是"我看到了什么写法"，
而是"这个类还能怎么被赋值"。

### 版本基线 146

`min_build` 从 6 条补到 46 条，其余按 v7 基线 146 标，七条查不到出处的留空。
闸门判据因此从 `>= 147` 变成 `> 146`：**等于基线不报**。
这条不是洁癖 —— 146 是一年里所有人都在用的版本，把基線语句报成"版本太新"等于让工具失去可信度。

### 15.33 单位表补细：武器 / 技能 / 免疫

这轮补的是「选单位」这一步。原来的表 39 个单位里只有 5 个带武器，因为拆分用的是字面量
`"new Weapon()"`，而 v7 的写法是 `new Weapon("large-weapon"){{` —— 72 处里有 67 处没被切到。
改成 `re.split(r"new Weapon\s*\(", ...)` 之后变成 35 个带武器。

新增两项：
- `abilities`：`abilities.add(new RepairFieldAbility(10f, 60f*4, 60f))` → `{ability, args}`，
  `args` 保留源码原文（里面有算式）。10 个单位有主动技能：scepter/bryde/pulsar/quasar 的护盾、
  oct 的力场+修复、nova/poly 的修复场、oxynoe 的过载领域、aegires 的能量场、navanax 的压制场。
- `immune_to`：`immunities(StatusEffects.x)` → 名字列表。**原版 39 个单位一个都没声明**，
  所以这一项在数据里是空的 —— 而这本身就是答案：别去猜「它抗不抗燃烧」。

顺带修了 `mlog.py unit` 的两个读法毛病：精确名优先（`unit oct` 原来同时命中 `spiroct`，
细节就不打了），以及 `bullet_speed` 缺失时摘要行打出 `Nonesp/23dmg` 的丑格式。

## 15.34 补方块表：建造配方、液体、可选加速物

上一版的方块表只回答「这个方块**收**什么」，写产线时真正要查的是三件别的事：造它花什么、它喝什么液体、它吃的哪样东西只是加速。

### 三处解析修复

| 源代码写法 | 出现次数 | 旧解析 | 现在 |
|---|---|---|---|
| `consumeLiquid(Liquids.water, 12f/60f)` | 55 | **完全没解析** | `liquids water:12/s` |
| `consumeCoolant(Liquids.x)` | 14 | 没解析 | `coolant x` |
| `consumeLiquids(with(...))` / `consumeLiquids(LiquidStack.with(...))` | 3 | 只认第一种 | 两种都认 |
| `requirements(Category.crafting, with(...))` | — | 从没采集 | `build lead:65 + silicon:40 + ... (crafting)` |

`consumeItem/consumeItems` 统一走一个 `_put(pair, suffix)`：后缀含 `boost`/`damp`/`optional` ⇒ 记 `booster`（**可选**加速物），否则记 `inputs`。`mender` 以前被记成「只收硅」，其实是「硅可选，给了修得快」。

### 单位换算：源码是每 tick，人是每秒

`consumeLiquid(Liquids.water, 12f / 60f)` 里的 `12f/60f` 是**每 tick**的量。`_rate()` 把它折成每秒（`12/s`），因为 wiki、游戏内 UI、玩家说话都用每秒。折不了的（带布尔的重载之类）**原样保留**，不猜。

### 汇总结论（为什么值得做）

- 有 facts 的方块 219 → **253**；75 个「有 consume 调用」的方块里，缺配方的从 **47 → 1**。
- 剩下那 1 个是 `landing-pad`：它命中的是字段 `consumeLiquidAmount = 1500f`，不是 consume 调用 —— 假阳性，不必修。
- `body_facts` 现在还认 `consume(new ConsumeItemRadioactive())` 这类「烧整类物品」的消耗器（`rtg-generator`、`steam-generator`），标注成「没有固定物品清单」，而不是编一个清单。

### 教训

**「没解析到」和「不存在」看起来一模一样。** 上一版把这 47 个方块显示成「收任何物品」（`accepts any` 的兜底），而真相是「我的正则只认一种写法」。凡是解析器有兜底分支的地方，都要能回答一句「这个兜底是真的，还是我没认出来」 —— 这里靠的是把源码里 `consume*` 的**调用形式逐个计数**（55 处单数 `consumeLiquid` 摆在面前，就没法再自欺）。

## 15.35 `check` 与 `ir` 对标签的两种理解（2026-10-18）

**现象**：拿一份自己写的、带 `main:` / `find:` / `c1:..c16:` / `idle:` 的程序跑 `mlog.py check`，报 6 条

```
[ERR] L7  jump 89 equal item null        jump target 89 out of range (0..79)
```

程序只有 59 条语句，89 明显不是语句号。

**原因**：同一个文件里有两份标签解析，语义不同。

| 位置 | 标签映射到 | 谁在用 |
|---|---|---|
| `mlogcheck.prepare()` | **语句序号**（`labels.setdefault(name, len(stmts))`） | `--cost`、`mlog.py ir` |
| `mlogcheck.analyse()` 自己那份 | **行号**（`labels[t[0][:-1]] = i`，`i` 是 `enumerate(code)` 的下标） | `check` 的全部规则 |

游戏里是语句序号：`LParser.java:117-125` 记的是「已解析语句数」，标签本身不占指令位。
行号只有在**没有注释行和空行**时才等于语句序号——而这两样恰恰是手写逻辑的常态（`#` 注释会被
`strip_comment` 变成空串，仍然占 `code` 的一个下标）。于是 `idle:` 在第 89 行、程序只有 80 个非空行，
`jump idle` 就被改写成 `jump 89`，再被越界检查抓个正着。

**修法**：`analyse()` 改用 `prepare()`，删掉自己那份标签表：

```python
def analyse(lines, links=None):
    # Labels are resolved by prepare(), the only place that knows a label is not
    # a statement. ...
    stmts = prepare(lines)
    out: list[Finding] = []
    n = len(stmts)
```

`prepare()` 直接丢掉标签行、把 `jump <label>` 改写成语句序号，`(行号, 代码)` 的形状和 `analyse()`
原来要的完全一致，所以后面所有规则一行没动。

**回归**：`tests/cases/labels-check.mlog`——标签前面放 5 行注释和 1 个空行（标签在第 7 行、程序只有
6 条语句），修复前必然越界、修复后 `[]`。`tests/run_tests.py` 17/17。

**教训**：同一个语法在两处各实现一遍，两处一定会分叉，而且分叉只在边角输入上现形（这里是「标签 +
注释 + 空行」三件同时成立）。`--cost` 当年正是因为把标签行算成了语句，才把所有 `main:` 循环报成
`L0(?)`；那次只修了 `prepare()`，`analyse()` 里同样的错误又活了半年。

## 15.36 读存档里的逻辑：`.msav` 的三种瓦片布局

`mlog.py map <save.msav>` 把一个存档里所有处理器连同链接名和源码提取出来，然后
对每一块跑正常的 `check`。做这件事之前我以为「存档格式只有一个」，实际是**三种**
瓦片布局，按存档版本号分：

| 存档版本 | 类 | 每格的字节 |
|---|---|---|
| 7–9 | `ShortChunkSaveVersion.readMap` | `block i16` + `packed` 字节（bit0 实体 / bit1 旧数据 1 字节 / bit2 新数据 7 字节），**chunk 只在「有实体且是中心格」时出现** |
| 10–13 | `SaveVersion.readMap` | `block i16` + `packed` 字节（bit0 实体 / bit2 数据 7 字节）+ 实体格的 `isCenter` 布尔 |
| ≤6 | `LegacySaveVersion.readMap` | 只有 `block i16`，建筑与否由 `block.hasBuilding()` 决定 —— 现网一个没有，没做 |

三处踩过的坑，都是同一个形状：**`else if` 挂错了层**。

- 现代布局：源码是 `if(hadEntity){ if(isCenter){chunk} } else if(hasData){...} else {consecutives}`。
  我先写成 `if(hadEntity and isCenter){chunk} elif hasData {...} else {consecutives}` ——
  于是「多格建筑的非中心格」（有实体、不是中心）掉进 `else`，多吃一个 consecutive 字节，
  从此整张图 desync。表现是 `map region has 8292 byte(s) left over`，
  而单独看 walk 的 `left=0`（因为我的调试脚本和解析器各写了一遍，只有后者错）。
- 7–9 布局：同一个错误，只是这次掉进 `else` 的是 `isCenter` 为假的实体格，
  于是 `tetrative-reconstructor` 之后 4 字节周期被读成 `01 7e 01`。
- **调试脚本必须 import 被测模块，不能自己抄一遍**。中间有一版 `_sweep_saves.py`
  把 `sys.path` 指向了根 `tools/`，读到的是没打补丁的旧副本，于是 1404 个失败"稳定复现"。

另外两条：`556.msav-backup.msav` 报 6621 个处理器不是解析错误，那是一张逻辑计算机
的图（6616 个 micro-processor，86 万条链接）；存档是 `zlib.decompress(整文件)`，
**`MSAV` 头也在压缩流里**，先读 `data[4]` 当版本号只会拿到压缩字节。

## 15.37 存档里的逻辑：103,787 个处理器，其实只有 4,366 份程序

`mlog.py map` 能读一个存档；把它乘上整个 `saves/` 目录，就是这个游戏里
「真实存在的逻辑」的全貌。1421 个 `.msav`（v7 289 / v8 149 / v9 61 / v10 45 /
v11 877）全部解析成功，**103,787 个处理器、963 万行代码**。

按**源码文本**的 sha1 去重（不含 links —— 同一段程序贴到四十个处理器上，是
一个 bug，不是四十个）：

| 指标 | 数值 |
| --- | --- |
| 处理器 | 103,787 |
| 不同程序 | **4,366** |
| 完全相同的副本 | 99,421（**95.8%**） |
| 被复制最多的一份 | 9,699 份（22 行，`236.msav`） |
| 发现总数 | 10,544（ERR 839 / SUSPECT 97 / WARN 3,306 / INFO 6,302） |

硬错里最大的一类还是「读了从没赋过值的变量」（814 条），其次是 `@dead` 极性
（97）、链接名拼错（约 500）、无出口死循环（11）、`noop`（9）。

三个教训：

1. **去重改变分母。** 不去重时，9,699 份同一个 22 行程序的错误会把
   「每处理器错误率」变成「副本数统计」。凡是要说「这个游戏里逻辑质量如何」，
   分母必须是**不同的程序**。
2. **聚合要按「规则」，不能按「出问题的那一行」。** `Finding.code` 字段装的是
   **源码行**（方便打印 `[ERR] L12 jump 99 always 0 0: ...`），直接拿它分组会得到
   5,023 个类 —— 等于没分组。按消息把数字和反引号名字归并掉，才得到 24 条规则。
3. **一张图 = 一份程序 + 一万份实例。** 95.8% 的处理器是复制品，说明这类地图
   （逻辑计算机、像素屏、塔防）的写法是「写一次，铺满地图」，而不是「每格单独写」。
   所以查这类图要抽样，不能逐个看。


## 15.38 给匿名的程序起一个「像什么」的名字

存档里的处理器**没有名字**。mlog 语言里不存在名字字段——只有蓝图（`.msch`）有 `name`/`description`/`labels`；存档里唯一的名字是地图名（`meta.mapname`），不是程序的。所以 4,367 份不同的程序全是匿名的，判用途只能读代码。

但「用途」可以不靠名字推。三个廉价信号就够：

| 信号 | 为什么有信息量 | 例子 |
| --- | --- | --- |
| 链接名 | 链接名默认就是方块名+序号，作者通常不改 | `display1`/`dome1`/`sorter…` |
| 指令直方图 | 每个领域有专属指令 | `draw`=显示、`ubind`=单位、`control config`=物流、`setrule`=世界规则 |
| 代码里的字符串 | 全程序往往只有一两段给人看的字 | `'队伍'`、`'黑名单'`、`'一键生成空辅路辅'` |

跑出来的分桶（`tools/corpus/_label_programs.py` → `out/saves_programs.md`）：

| 桶 | 程序数 | 语句数 | 副本数 |
| --- | ---: | ---: | ---: |
| 像素画(逐格 draw) | 2,022 | 1,917,828 | 6,285 |
| 单位 | 830 | 65,137 | 19,866 |
| 物流 | 630 | 30,209 | 24,199 |
| 规则/世界 | 384 | 36,349 | 22,684 |
| 显示/UI | 177 | 19,393 | 11,321 |
| 计算/内存 | 151 | 9,216 | 2,152 |
| 其他 | 129 | 2,049 | 10,330 |
| 通信 | 44 | 1,403 | 8,359 |

三条教训：

1. **第一版分类全塞进「显示」**——因为把「出现过一次 `draw`」当成了显示程序。改成「draw 占语句一半以上 = 逐格画的像素图」之后，2,209 份里分出 2,022 份是真像素画。**阈值要比「存在性」更严**。
2. **中文只在两处**：给人看的 `print` 文字，和少数人拿中文当变量名。所以「语言混杂」的真实形态不是中英混排，而是**三套命名体系并存**：序号流（`a/b/c`）、拼音缩写（`anwser`/`tims`/`spe`）、点号字段（`d.h`）。三套之间没有可推断的对应关系。
3. **别把桶当标签**。每一行都在右边写了证据（链接、指令、字符串），所以打印出来的是「像什么 + 凭什么」，不是「是什么」。

## 15.39 钍反保护:`@heat` 不是温度计,响应时间才是

`NuclearReactor.java:95-125` 的三段式,决定了「用 @heat 做开关」这个写法的全部边界:

```java
if(fuel > 0 && enabled){ heat += fullness * heating * Math.min(delta(), 4f); ... }
else{ heat = Math.max(0f, heat - Time.delta / ambientCooldownTime); }
if(heat > 0){ float maxUsed = Math.min(liquids.currentAmount(), heat / coolantPower);
              heat -= maxUsed * coolantPower; }
if(heat >= 0.999f) kill();
```

常量:`heating = 0.01`、`coolantPower = 0.5`、`ambientCooldownTime = 60*20 = 1200 tick`。

### 推论一:有冷却液时 `@heat` 恒为 0

`maxUsed = min(液量, heat/0.5)` ⇒ 只要有一滴冷却液,`heat -= heat`,**一个 tick 清零**。稳态每 tick 只烧 `0.02` 液(约 1.2 液/秒)。
所以 `@heat` 不是温度计,是「上一个 tick 有没有饿到冷却液」的探测器 —— 它只会是 0(没饿)或尖峰(饿了)。

### 推论二:单阈值不会震荡,迟滞是多余的

开关 `enabled` 不改变冷却液供给,没有反馈回路;`@heat` 抖动幅度是 1 tick 且没有成本。
**所以「缺迟滞」不是缺陷** —— 这条规则我提过、后来撤掉了。

### 推论三:`control enabled 0` 不是灭火

停堆后走 ambient 分支:`0.00083/tick` ⇒ 从 0.999 到 0 要 **1200 tick(20 秒)**,期间不产电。
而恢复冷却液是 **1 tick 清 0**。要救,先供液;要停,才停堆。

### 推论四:真正的约束是检查间隔

满料发热 `0.01/tick` ⇒ `0 → 0.999` 要 **100 tick(1.67 秒)**;填到 `T` 时只剩 `(0.999-T)/0.01` tick。
检查间隔 = 循环体语句数 ÷ 处理器 ipt ⇒ 阈值越高,留给循环的余量越小。

这条做成了规则(`mlogcheck.py` 的 `reactor guard is too slow`):找 `sensor <res> <reactor> @heat` + 同名的 `control enabled`,
取程序里对该变量的比较阈值,算出窗口 tick 数和最内层回边跨度换算的间隔,间隔 > 窗口才报。

### 实测

1421 个存档里,碰反应堆且读 `@heat` 的程序 528 份,按源码哈希去重后 51 份,
其中报「保护太慢」的 11 份。典型是阈值 0.71、循环 131 句 / ipt 2 ⇒ 每 66 tick 才看一眼,
而 0.71 → 0.999 只有 29 tick。

教训:**「同一个量用两种方式算」是最容易发现矛盾的地方** —— 阈值说的是「还剩多少余量」,
循环体说的是「多久看一次」,两者相乘才知道会不会炸。

### 钍反和冲反共用链接名,所以只有"证明类型"才敢判

`reactor1` 这个名字既可能是 `thorium-reactor`、也可能是 `impact-reactor`,两者的热曲线不同
(只有钍反是 0.01/tick 的线性升温),所以光看「`@heat` 阈值 + 循环长度」推不出任何结论 ——
2026-10-18 用户纠正的正是这一点:我最初把这 11 处报成 WARN,其中大部分是他自己写的冲反逻辑。

规则改成三档:

| 程序里能看到什么 | 报什么 |
|---|---|
| `sensor x <link> @type` 且比对 `@thorium-reactor` | **WARN**,可以直接引用这条规则 |
| 出现 `@impact-reactor` | 不报(冲反有自己的热规则) |
| 都没有 | **INFO**,写成疑问句:「如果这个链接是钍反,那么…」 |

实测(1421 个存档):碰反应堆且用 `@heat` 的程序 528 个、去重后 51 份、间隔过长的 11 份,
**改成 INFO 后抽查仍是 INFO**,没有一条能自证类型 —— 说明这个校验不是多余的礼貌,是这条规则唯一的证据来源。

两个都叫「反应堆」,`@heat` 却是两件不同的事:

| | `thorium-reactor` | `impact-reactor` |
|---|---|---|
| `@heat` 是 | 温度 | **warmup(预热度)** |
| 源码 | `NuclearReactor.java:95-125` | `ImpactReactor.java:117-120`,`sense(LAccess.heat) → warmup` |
| 涨多快 | 0.01/tick(100 tick 满) | `warmupSpeed = 0.001` 向 1 逼近,**约 6908 tick ≈ 115 秒** |
| 满值后果 | `heat >= 0.999` 即 `kill()` | **不出电率的惩罚**:`productionEfficiency = warmup^5` |
| 会不会炸 | 会 | **不会**(`explosionMinWarmup = 0.3` 只管被打爆时的爆炸动画) |

所以「用 `@heat` 做开关」在两台机器上是相反的意思:钍反是**保护**,冲反是**自残** ——
`warmup^5` 意味着卡在 0.5 只有 3.1% 出力,卡在 0.8 是 32.8%,卡在 0.9 是 59.0%,要 0.99 才有 95%。

规则因此分成两支(都要求程序自证类型):

- `@thorium-reactor` + 检查间隔 > 上升时间 → **WARN**(会炸)
- `@impact-reactor` + 有 `control enabled <link> 0` + 阈值 < 0.99 → **WARN**(自己把出力砍了)

第二支是用户 2026-10-18 纠正后补的:我原来只写了「冲反有不同的热规则,跳过」,
但他指出**冲反满热不炸、是以最大出力运行**,所以跳过等于放过另一半错误。


## 15.40 并行：worker 数由「最大的那个文件」定，不由平均定

跑 1,421 个存档要 280 秒，很自然地想按核数开进程。第一次这么做直接把机器拖死了：13 个
worker，10 分钟只做完 40 个大文件里的 2 个。

原因不是 CPU，是**内存的长尾**。存档平均 95 KB，但 `556.msav` 有 4.5 MB、里面 6,616 个
处理器、86 万条链接 —— 一个这样的文件在 worker 里峰值就是几百 MB。按平均值算 worker
（可用内存 ÷ 256 MB）会对每个 worker 都低估，然后它们同时撞上最大的那批文件。所以：

- **worker 数 = min(核数-2, (可用-预留) ÷ 单worker内存, 文件数)**，而「单worker内存」在
  **重文件段**要按 `200 + 120 × 最大文件MB` 重算；
- **两段跑**：`< 1 MB` 的轻文件用常规 worker 数，`>= 1 MB` 的重文件单独用 2–3 个；
- **长的先开工**（`order_by_size`），尾巴才短；
- **45 秒没有新结果就打印还卡着的最大三个文件名** —— 卡住之所以让人恼火，是因为看不出来
  它在动。

实测：解析 1,421 个存档 280 s → **34 s**（8.2×）；带六种分析的 359 s → **127 s**（2.8×，
分析段是 CPU 密集，收益自然小）。

教训：「按系统资源自动分块」里的资源不是核数，是**每个任务最坏情况要占多少**。用平均值算，
分配器一定会在长尾上崩。

## 15.41 病毒逻辑：一行就能认出来

用户给的名字：圈内叫**病毒逻辑**，判据只有一行 —— `ucontrol build <x> <y> <块> <朝向> @this`。
`build` 的最后一个参数是**要写进新方块 config 的值**，`@this` 就是这个处理器自己的程序，
于是它造出来的处理器跑一模一样的代码、继续造。这不是错误（自我复制是一种设计），但它是
打开别人地图时最该先看到的一行，所以给它单独一类检查 `virus-logic`，而不是塞进
`ucontrol build` 的普通告警里。`@this` 常常经变量中转（`set cfg @this` → `ucontrol build … cfg`），
两种都认。

实测（1,421 个存档 + 两个蓝图库）：

| 语料 | 程序数 | 用 `ucontrol build` | 病毒逻辑 | 去掉副本后 |
|---|---|---|---|---|
| 我的 1,421 个存档 | 103,787 | 9,232 | **9,151** | **2 份** |
| 我的蓝图库 | 5,751 | 11 | 2（`更强的病毒`、`复制炸弹`） | 2 |
| 彩末包 | 1,680 | 2 | 1（`空辅自动复制病毒`） | 1 |

存档里那 9,151 个只来自**两份程序**：`556.msav`（1,033，备份 6,616）与 `538.msav`（1,432）。
换句话说 `556.msav` 里那 6,616 个 micro-processor **不是我以为的"逻辑计算机"，是一窝病毒** ——
16 行：

```
set link1 @links
ubind @mega
op rand xv 14 b
op rand yv 14 b
op add x @thisx xv
op sub x x 7
op add y @thisy yv
op sub y y 7
ucontrol approach x y 10 0 0
ucontrol getBlock x y 0 b 0
jump 1 notEqual b null
ucontrol build x y @micro-processor 0 @this
set link2 @links
jump 12 lessThanEq link2 link1
set link1 link2
jump 1 always x false
```

读法：在自身周围 ±7 格里随机挑一点 → 叫 mega 过去 → `getBlock` 看那格空不空（不空就重挑）
→ 空就造一台装着这份程序的 micro → 用 `@links` 的数量变化判断造成功没有 → 无限循环。
它把自己铺满整张图的空地，指数增长。

教训：把「处理器多」当成「算力强」是错的。6,616 个处理器可能只是**一条 16 行的繁殖循环**；
数量不是复杂度的证据，去重后的程序数才是（4,366 份程序对应 103,787 个处理器）。

## 15.42 声明的参数个数 ≠ 有效的参数个数

用户看报告时直接指出来:`ucontrol move` 应该是 4 个参数。对 —— 我表里写的是 6,因为那是**解析器保留的槽位数**,不是**指令真正读的个数**。

| 指令 | 我原来的 `arity` | 屏幕上写几个字段 | 真正读几个 |
|---|---|---|---|
| `ucontrol move x y` | 6 | 4 | 2（`ai.moveX = x1; ai.moveY = y1`） |
| `ucontrol pathfind x y` | 6 | 4 | 2 |
| `ucontrol stop` | 6 | 2 | 0 |
| `op floor a b` | 2 | 3 也行 | 1（第二个操作数被丢弃） |

为什么表里会写成 6:`LExecutor.java:352` 在分派之前**无条件**把 `p1,p2,p3` 转成数字,所以「读」集合永远是 `1,2,3`;而 `case move, stop, approach, pathfind -> { ai.control = type; ai.moveX = x1; ai.moveY = y1; if(type == approach) ai.moveRad = d1; }` 里只有 `x1,y1` 参与语义。两件事都对,但不能混成一个数字。

改法:

- `instr_semantics.json` 里同时存 `arity`(解析器)与 `args`/`semantic_uses`(语义),`explain` 两个都打:`move  reads 1=x, 2=y  writes -  effective arity 4`。
- 一元算子多写一个操作数(9 张图里 1,121 条: `op floor fx x b` 443、`op abs dx+ dx b` 422、`op sin y+ angle 90` 111、`op cos` 110)从 WARN 降成 INFO。运行时那个 token 被 `LParser` 丢掉,程序行为不变;但 `op sin y+ angle 90` 里那个 `90` 说明作者以为它吃角度(sin 吃弧度),所以值得留一条 INFO,不值得叫错误。
- 降级后这 9 张图的 WARN 从 1,121 + 46 掉到 38 —— **报告里出现频率最高的那一类,先怀疑它,不要先怀疑被测代码**。

## 15.43 让审计变成一条条能判的清单

规则有了（`rules/` 25 条），噪声也有了数字（`out/rule_audit.md`），但那些数字是**按规则**的，
不是**按人**的：用户面对的是 182 条具体发现，不是「unary-op-extra-operand 673 条」。
所以加了一层 `tools/review.py`，它只做三件事：

1. **压**：同一份程序里同一条规则只留一行（`rule_audit.py --rows`，`ROW_CAP = 3`），
   182 行而不是 1,600 行。
2. **定案**：每行一个稳定 id（`sha1(rule|源码哈希|行号|该行源码)[:10]`），
   四个词 —— `ok` / `bad` / `unsure` / `skip` —— 追加到 `out/verdicts.csv`。
3. **反过来算**：`stats` 按规则算「你判了几条、错了几条」，`export` 生成
   `out/audit.md`（按规则分组、可判项打勾的表）。

为什么 id 要带源码哈希：存档会重下、文件会改名、行号会因为作者改一行而漂移，
但「这段程序 + 这一行」的组合不会自己变。id 稳定，判定才能累积。

第一个真用出来的结论：`jump 18 equal colour ender` 被判成 `constant-null-guard`
（WARN，恒定比较）。但这行是**署名**——`colour` 和 `ender` 是作者的 ID，
两个都没被赋过值，比较恒为真，于是整段等于"无条件跳 18"。
按用户早就定过的规矩（署名是 INFO 不是错），这条规则该在**两侧都没被赋值**时降成 INFO。
规则不懂语境，人会；所以审计表才是必需品，而不是可有可无的仪表盘。

教训：**报告的价值不在条数，在每条都能被一个人判成「对/错/不知道」**。
不能判的报告，等于没写。

## 15.44 报错里的行号必须是代码里的行号

用户拿 `review.py show f2a6e68568` 去核对，说了两句话，各自对应一个独立的错：

> `jump 13` 第 13 行不是 jump always 呀，而且，我看这段代码你的判定行多了一行

### 错一：两套编号系统

- `jump N` 里的 N 是**语句序号**（0 起），标签行、空行、纯注释行都不算语句。
- 我们报的 `Finding.line` 原来是**文件行号**（1 起），`prepare()` 返回的原始下标 `+1`。

程序没标签没注释时两者只差 1；一旦有标签，就变成「差 1 + 标签行数」。用户按代码里的 13 去找，
落在我算的第 14 行上 —— 于是他说"多了一行"。

修法：`analyse()` 末尾统一把 `Finding.line` 从文件行号映射成语句序号，
`{原始行 + 1: 语句下标}`；`review.py show` 也用同一张表打印左侧行的编号。
按 `jump` 的编号读我们的话，才是唯一读得通的方式。

钉住它的 fixture：`tests/cases/label-index.mlog`（`main:` 在第 1 行，三条语句），
digest 是 `[['INFO', 0], ['INFO', 1]]` —— 若有人把编号改回文件行号，会变成 `1, 2` 立刻失败。

### 错二：规则条件写松了

`jump-to-jump-chain` 原来的条件是「目标是 jump 且源不是 always」：

```python
if stmts[tgt][1].startswith("jump ") and m.group(2) != "always":
```

这条把**条件跳转落到另一条跳转上**也算成链。那不是浪费：条件不成立时你直接往下走，
目标那条跳转根本不会被执行 —— 那是普通的分派三角。

真正白花的只有一种：**无条件跳到无条件**，第二次跳转必然执行，每次循环白付一条指令。

20 张地图上的效果：456 → 115（去掉 341 条假阳性），可判行从 37 降到 10，总行数 182 → 133。

### 教训

1. **报错里的数字必须和代码里的数字是同一个编号系统**，否则用户每次核对都要先做一次心算。
2. 精确率 100% 救不了「整类都不是问题」：这 456 条每一句描述都是对的（目标确实是跳转），
   但整类结论是错的。审计表里 `prec 100%` 只说明"我们说的是事实"，不说明"这件事值得报"。

## 15.45 审计的载体：markdown，不是游戏

`review.py` 第一版把每条发现做成一张单处理器蓝图，让人在游戏里看。用户否掉了：

> 我感觉如果你不保留它链接的建筑，你把逻辑直接粘贴在MD里面，让我在MD里面审计之后你看我最舒服

理由成立：判一条发现只需要三样东西 —— 被指的**那一行**、它所在的**完整程序**、以及这台
处理器**自己的链接名**。三样都是文本。蓝图额外要求开游戏、还要记住它是第几条，反而是负担。
而且我本来就不复制链接目标（要判的正是「名字有没有指对」），所以蓝图那一半是空的。

现在的形态：`review.py md` 生成 `out/audit_review.md`，每条一份：

    ### `a5928f1c49`
    - 出处：`mindustrytop-25774` · (125,137) · logic-processor · 141 条语句
    - 处理器自己的链接：`message1`, `pad1`, ...
    - 被指行：语句序号 **71**
    - 规则说：`op sqrt` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

    ```
    >>>>  71  op sqrt d d 0
          72  ...
    ```

    判定: 
    备注: 

填完 `python tools/review.py ingest` 读回 `out/verdicts.csv`（`判定:` 只认四个词，
填别的会单独列出来；`备注:` 跟着那条规则的历史走）。`--window N` 控制上下各给几行 ——
678 句的程序全列出来没人看。

教训：**给人审东西，输出格式要贴着人的阅读工具。** 他要的是编辑器里滚一滚、在行尾打一个词，
不是「开游戏 → 蓝图菜单 → 拖出来 → 数第几条」。


## 15.46 用户判了 55 条：三条规则被砍、一条门被拆

用户把 `out/audit_review.md` 里前 55 条判完了。**没有一条是「这行代码写错了」**，全是「你这条规则不该存在」：

| 判定 | 我改了什么 |
|---|---|
| `unary-op-extra-operand` 29 条全 ok / 「不再审计 op 的无效参数」 | 这条 INFO 直接删掉，规则记成 `state: silent` |
| `version-gate` 「为什么是第零行，不应该指向 format 吗」 | finding 的 `line` 改成真正用到该特性的那一行，不再恒为 L0 |
| 「146 就已经有 getblock 了，这个门应该去掉」 | `getblock.min_build` 157 → 146（157.4 加的是 `query` 不是 `getblock`） |
| 「状态效果改版，裸名变 null」+「你去查证代码」 | 核实 `StatusEffects.java:14` 确有 `unmoving`；新增 `status_names.json` + INFO |
| 「A 是无效参数，不影响」（`fetch unitCount … 1 A @oct`） | 核实 `FetchI` 的 count 分支只读 `extra`；`uses_of` 不再把 `index` 当变量 |

**三个可以带走的结论**：

1. **100% 精确率的规则可能是纯噪声**。`unary-op-extra-operand` 29 条、精确率 100%，但每一条都是「我知道，
   懒得删」。精确率衡量的是「我有没有说错」，不衡量「说了有没有用」——后者只能由人判。
2. **报错里的行号必须和代码里的数字同一个编号系统**（上一节踩过），**并且要指在能动手改的那一行**。
   程序级的 finding 标 L0 等于告诉人「你自己去找」。
3. 用户说「你去查证代码」时，那就是字面意思：他记的是版本印象，不是结论。核实完再改，
   核实不了就留成 `notsure` 并在规则里写「未证实」。

第 53 次整理之后，这是第 54 次。


## 15.47 用户自己跑：把审计做成一条命令

用户说「你直接把这套工具打包成脚本让我自己跑吧，我电脑性能比较低」。之前那套 `build`/`md`/`ingest`
能用，但要人记住四个命令、还得先自己抓图——**能跑和愿意跑之间隔着一层**。

现在 `review.py run --pages 2` 一条命令走完抓图→分析→写清单，`--serial` 给慢机器，`--pages 0` 只
分析本地已有的图。填完 `ingest && stats` 就出准确率。

两个坑，都出在「工具重写输入文件」上：

1. **`md` 会覆盖掉用户刚填的判定**。我重建清单时把用户填的 55 条判定冲掉了——因为 `md` 是
   「根据 rows 重新生成整份文件」，而判定只存在这份文件里。现在 `md`/`run` 开头先 `ingest` 一遍
   旧文件，判定进 `out/verdicts.csv` 之后再重写，填过的不会丢。**任何「重新生成用户编辑过的文件」
   的工具，第一件事是把用户改过的部分读回来**，这条对配置、对清单、对笔记都成立。
2. 判定是**行 id**（`sha1(规则|程序哈希|行号|代码)`）。`build` 重新扫描会换 id，所以顺序必须是
   `ingest` → `build`，反过来旧判定会全部变成「不在清单里」。

第 54 次整理之后，这是第 55 次。

## 15.48 一条规则被判 11/11 全错,就该整条删掉

用户 m15434 的原话:「没看懂这个报错，这个逻辑使用 notequal 没问题呀，反向了而已」。

`@dead` 极性那条规则报的是「`sensor d @unit @dead` 之后用 `notEqual` 比较」。
我当时的意思是「1 = 死了，你用 notEqual 会在活着的时候跳」，但那**只是其中一半写法**:

```mlog
sensor d @unit @dead
jump rebind notEqual d 0   # 死了 → 跳到重新绑定的分支
jump work   equal    d 0   # 活着 → 掉到干活的分支
```

两行都是正常代码,哪一行对取决于**跳转目标干什么**(重新绑定 vs 干活),不取决于算子。
而且我只看了算子、没看比较的那个值 —— 连「和 0 比还是和 1 比」都没读出来就报了。

处理:整条删掉(不是降级)。`rules/dead-polarity.json` 留 `state: "silent -- no longer reported"`
和上面这段推理,免得以后有人重新发明它。清单从 97 行降到 86 行,7 条规则。

教训:**一条规则的「claim」如果写不出一句不含"如果"的判据,它就不该存在**。
这条的 claim 是"notEqual 会在活着的时候跳" —— 缺了"且比较值是 1"这个前提,而那前提我根本没解析。


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
**做法修正**:[tools/fix_skill_links.py](tools/fix_skill_links.py)
**向上找 `Mindustry-Source` 定位工作目录根**,再按实际相对深度重写所有链接。
**以后再搬位置,重跑一次这个脚本即可。**

---

## 18. 更新日志

- **第 32 次整理**:新增 §15.23。方法论:**一个标签值是不是"内容的函数",可以用留出法量出来;量不出来的,就是人给的定义,别假装能推。**

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
| 第 23 次整理 | **用户纠正:「未定义变量」常常是署名,不是错误**。原话:「游戏内部的逻辑编辑器会对变量列表，使用自己的名字作为变量名并且不定义是很常见的署名方法，因为可以在变量列表看到。这同样也适用于不被读但是也会在变量列表显示的例子，不算很大的错误。」据 `LAssembler.java:67-69`(首尾都是 `"` 才成字符串常量)和编辑器行为,改判三档:只出现在 `print` 里 ⇒ INFO 署名;只出现在 `jump … equal/notEqual X null` 里 ⇒ WARN 恒真但无害;其余仍是 ERR。再加上两个同源发现:`set // 说明文字` 是 mlog 的注释写法(`#` 之外没有注释语法),整行跳过,`障碍躲避.msch` 一个文件就少 58 条假错;`LParser` 按 `arity` 填字段,多余 token 惰性丢弃,`mlogcheck` 据此截断。全包硬错 **883 → 416 → 367**。**方法论:一个检查器报出的「错误」里,哪些是错误取决于这个社区的写作习惯,不取决于语言规范 —— 这类知识只能从用户嘴里得到,测不出来。** |
| 第 24 次整理 | **判级是被用户校准出来的,不是从规范里推出来的**。883 条硬错逐条核对到 77 条,中间掉的全是判级调整而非漏报:署名(`print`/`set`/`jump equal A B` 里的名字)归 E、`control` 只认三个参数归 C、布尔参数恒 false 归 warn、链接名不在链接表里归 D。同一次整理里**我自己判错一格**:只看 `LAssembler.var()` 就宣称 `true`/`false` 不是关键字,造出 653 条假警告 —— 真相是 `GlobalVars.java:54-55` 用 `putEntry` 把它们注册成常量 1/0。方法论:**一个检查器报出的「错误」,哪些是错误取决于社区写作习惯,不取决于语言规范;而判「这个名字是不是内建」要查注册表,不是查解析函数的分支。** |
| 第 25 次整理 | **最后三处纠正,全是"我把一个东西当成了另一个东西"**。①`noop` 从 WARN 改判 **ERR**:它是 `LStatements.InvalidStatement`,低版本跑高版本逻辑时丢的正是干活那条,程序基本就死;我曾按"我抽到的唯一一例能跑"判成良性 —— 用户一句"这个是特例"纠正。②错误表 C 层把 `op rand`/`op floor`/`op abs` 当成变量名列出来 —— `op` 的第二个 token 是**运算符号**,成因是取消息里第一对反引号当名字,而 `op rand g 255 b` 那条警告的文案正好是 `` `op rand` given 3 args ``。③E 层混进了两个不相干的东西:`?` 2325 条其实是"jump 指向 jump",`i`/`n`/`x` 一千多条是"变量有 N 个到达赋值"——循环变量本来就反复赋值,这条**纯噪声,已整块删除**。方法论:**INFO 不是一种东西;分层要按"这条结论想让读者做什么"分,不能按严重程度分。** |
| 第 26 次整理 | **版本闸门:蓝图不存版本号,只能从语句倒推**。锚定六条 (`effect`/`sync` 146、`format` 147、`select` 150、`bullet`/`getblock` 157),146 当基线因此低于 147 不报;`noop` 与新语句同时出现时不再分两条,直接替换成「版本漂移」的结论。方法论:**没有元数据时,元数据要从内容的最稀有的那个特征反推** —— 挑特征的标准是「出现晚、出现少、一眼能认」,不是「重要」。 |
| 第 27 次整理 | **跨處理器讀寫:可讀的槽就是目標自己的變量,`write` 不是必須的**。先前把「按名讀寫」與「記憶格按變量尋址」混為一談,寫出「586 份用跨處理器」這種虛高數字;重測後我的庫只有 **9/625** 份、彩末包 13/926。新增 `mlog.py cross` 把四類結果(never assigned / always null / constant / dead write)分開報。方法論:**當一個特性的命中率從 94% 掉到 1.4%,先懷疑統計口徑,再懷疑世界**。 |
| 第 30 次整理 | **`unit` / `block` / `find` 三条命令:单位属性、方块配方、找参考实现**。`find` 从 152 秒压到 0.7 秒(跳过生成式艺术与 16MB 像素画 + mtime 缓存),抽数据时踩了四个坑:成组声明的默认值、`}};` 结尾与缩进、`consumeItem` 单物品配方、Java 字段名要转 kebab。方法论:**写逻辑缺的不是语法,是目标和游戏事实 —— 目标问人,游戏事实进数据表。** |
| 第 31 次整理 | **物品接受规则:五档(any / recipe / ammo / custom / none),不是「收不收」**。判据是 `BuildingComp.acceptItem` = `consumesItem && 容量`,而 `consumesItem` 是消费者填的布尔数组 ⇒ 没有消费者的方块默认拒收一切;别用 `itemCapacity` 推(工厂大多不写它)。方法论:**「能不能收」和「现在收不收」是两个问题,静态分析只能回答前者 —— 分不清这一点,工具就会开始撒谎。** |
| 第 33 次整理 | 署名识别扩展:小号「鱼破了冰 / 鱼冰 / 鱼梦醒时」并入 ILI;全库 240/626 份带 ILI 标签(逐份备份+校验,只重写 tags 段)。**署名是谁做的,用途是干什么的——前者能扫出来,后者只能问人。** |
| 第 34 次整理 | 作者标签约定:我产出的蓝图默认打 `[blue]DeepSeek`(生成器写入);钍反防爆 v1 已导入游戏目录。**作者身份和作品来源是两个维度,可以同时挂。** |
| 第 35 次整理 | 生成蓝图一律用 `mlog.py gen`(它自己打印 base64),不要手拼前缀;`--with-block` 的 dx,dy 是相对处理器的中心坐标。**工具已经会做的事,再手写一遍只会多出一个 bug 的位置。** |
| 第 36 次整理 | **写逻辑的取舍:枚举 vs 跳表 vs 内存格**。`sensor` 第三参是运行时对象(`LExecutor.java:668-719` `Object sense = type.obj()`),所以枚举不是语法强制;但 mlog 没有「按下标取内容物」的原语,造表的价格≈摊开写(枚举 26 / 跳表 30+ / 格子 14+10),差的是状态数量与可复查性。方法论:**「为什么不用更聪明的写法」的答案经常是「这里没有更便宜的写法」—— 说清价格,比说清偏好有用。** |
| 第 37 次整理 | **死循环规则按守卫极性判定**。`@this` 只能被 `ubind` 认领(`LExecutor.java:325`/`:329`),所以 `equal … @this` + `ubind` 是永不退出,而 `notEqual … @this` + `ubind` 是标准「防抢单位」写法。**同一条语句,极性反了就从不报变成全报;规则的价值不在「能发现」,在「敢不报」。** |
| 第 38 次整理 | **一个算子不等于一条语句**：`op` 是 45 个算子共用的语法外壳，版本属性挂在算子上（`emod`/`ushr` = v150，其余回 v6），所以版本闸门必须按算子名查。同一段源码里 `idiv`=floor、`mod`=截断、`emod`=floor-mod，三者不能互换，判据是 `a == (a idiv b)*b + (a emod b)` 恒成立。书还纠正了我一条：`ucontrol` 也会把单位认领给本处理器（`UnitControlI.checkLogicAI` 里设 controller=@this），所以死循环规则要按「认领 vs 读取」的**顺序**判定，不是按指令种类。**语法是一层壳，语义挂在壳里的那个词上。** |
| 第 39 次整理 | **`style`：把「像人写的」拆成六个可量维度**(命名/风格/形状/成本/链接/收尾)。坑:枚举槽不是变量(否则 `naming` 头几名是 `op` 名);语料文件名必须进检索(中文文件名);同文件多处理器要去重 |
- 第 40 次整理：补数据（sensor 75 条 / 武器明细 / min_build 46 条 + 基线 146）。方法论：**「没找到出处」也是数据 —— 留空比编一个数字更省后面的人的时间。**
- 第 41 次整理：补方块表 —— 建造配方(`requirements`)、液体(单数 `consumeLiquid` 55 处)、可选加速物(`boost`/`damp` 后缀)。75 个消耗器里缺配方 47→1，只剩 `landing-pad`（命中字段名 `consumeLiquidAmount`，假阳性）。方法论：**解析器的兜底分支要能自证「是真的，还是我没认出来」—— 把源码里的调用形式逐个计数，数量摆出来就没法自欺。**
- 第 42 次整理：`check` 的标签解析从「行号」改成「语句序号」（复用 `prepare()`）。方法论：**同一个语法只准有一份解析**——两处各写一遍，分叉只是时间问题，而且它只在边角输入（标签 + 注释 + 空行同时出现）上现形，语料再大也扫不出来。
- 第 43 次整理：读存档里的逻辑（`.msav` 三种瓦片布局）。方法论「同一个 walk 只准有一份实现 —— 调试脚本自己抄一遍，就会和被测代码一起错，或者只错一个、让你怀疑数据」；以及「多格建筑的非中心格是`else if` 最容易挂错的那一格」。
- 第 44 次整理：把 `mlog.py map` 乘以整个 `saves/`（1421 个存档、103,787 个处理器），按源码哈希去重后发现只有 4,366 份不同的程序、95.8% 是副本。方法论：「聚合的单位决定了你能看见什么 —— 按行分组看见的都是行，按规则分组才看得见规则。」
- 第 45 次整理：给匿名的程序分桶（`tools/corpus/_label_programs.py` → `out/saves_programs.md`）。方法论：**没有名字的语料不是没用的语料，是要求你从结构里读用途**；但判类阈值要比「存在性」严（一次 `draw` 不算显示程序，一半语句是 `draw` 才算）。
- 第 46 次整理：钍反保护规则（@heat 是布尔量不是温度计 / control enabled 0 不是灭火 / 满料 100 tick 爆）的方法论「阈值说的是余量，循环体说的是频率，相乘才知道会不会炸」。

- 第 47 次整理：并行化（`parallel.py`）。第一次按平均值算 worker 把机器拖死 —— 教训写进
  §15.40：worker 数由最大的文件定，不由平均定；重文件单独一段，45 秒无进展就报出还在跑
  的是哪几个，别让人盯着一个不动的进度条。

- 第 48 次整理：病毒逻辑（`ucontrol build … @this`）单独成类。用户给了圈内的名字和判据；
  实测存档里 9,151 个"病毒"只来自两份 16 行程序 —— 数量不是复杂度的证据，去重后才是。
- 第 49 次整理：SKILL.md 按工作流重排（查→写→查错→批量→事实），六段挂错位置的 \###\ 提升为 \##\，加目录与「工具索引」。教训：文档按时间追加，三个月后结构就是「后写的在最下面」——内容没错，位置全错。
- 第 50 次整理：参数个数分两层（解析器槽位 vs 语义读取），并把「一元算子多写一个操作数」从 WARN 降成 INFO（9 张图 1,121 条噪声 → 38 条）。方法论：**报告里最多的那一类先怀疑报告自己**。
- 第 51 次整理：把「规则噪声表」再往下压成「逐条可判清单」（`tools/review.py`：压行 / 稳定 id / ok-bad-unsure 四词定案 / 反过来按规则算准确率）。方法论：报告的价值不在条数，在每条都能被一个人判成对、错、或不知道。
- 第 52 次整理：行号统一成语句序号（与 `jump` 一致）+ jump-to-jump-chain 收紧成「无条件→无条件」（456 → 115）。方法论「报错里的数字必须和代码里的数字是同一个编号系统」。
- 第 53 次整理：审计改成 markdown（`review.py md` / `ingest`）—— 判一条发现只需要那一行、整段程序、和它自己的链接名，三样都是文本。

- 第 56 次整理：按用户判定删掉 `@dead` 极性规则（11/11 全错）。方法论：「一条规则的 claim 如果写不出一句不含『如果』的判据，它就不该存在」——这条的 claim 缺了「且比较值是 1」，而那一步我根本没解析。

- 第 57 次整理：作者通读 86 行全部判 ok（20 张社区地图、7 类规则零假阳性）。方法论：「精确率 100% 只说明这批语料上没假阳性，不说明规则的证明是对的」——样本换了就要重跑。唯一被整条删掉的 `@dead` 极性规则记在 §15.48。

- 第 58 次整理：**真执行器跑通了**（`tools/mlogsim.py`）。不装 JDK、不编译、不做 mod：起官方 `server-release.jar`，用控制台自带的 `js`（Rhino）放方块、`updateCode`、手动逐条 `runOnce()`，再读回 `LExecutor.vars` 与 `textBuffer`。当前默认 **v159.3 server jar + Temurin JRE 21**（Steam 的 jlink 运行时缺 `java.logging`，v159 起不来；v146 的 9.6 MB jar 用 Steam jre 就能跑）。`p1`–`p8` 在 v159 上与 mindcode 模拟器结论全部一致，`_sim_a.mlog` 10 步得 `result=43 / print 4343`，`p8-cross.msch` 得 `a=7 / b=null / c=null`。三个必须记住的坑：①**v146 的 `LogicBlock.LogicBuild` 没有 `readable/read`**，跨处理器按名读恒 null —— p8 在 v146 的 null 是版本缺功能，不是驱动 bug；②世界 `pause` 后 `updateTile` 不跑，`executor.team` 停在 `Team.derelict`，跨处理器读会因 team 不等全 null，必须手动 `b.executor.team = Team.sharded`；③Java 子进程不能写 `%TEMP%`（`config\rules.hjson (拒绝访问。)`），workdir 必须放 `out/_sim` 并预建 `config/logs`。方法论：**模拟器的结论要拿真执行器复核一遍，因为「语言层一致」不代表「世界层一致」——而版本差异会伪装成你的驱动 bug。**

﻿- 第 59 次整理：**tick 时钟 + 世界需求清单**。`mlogsim.py --ticks N` 不再逐条 `runOnce`，而是按游戏自己的节奏驱动 `LogicBlock.updateTile()`：设 `Time.delta = 1.0`，每 tick 由 `accumulator += edelta() * ipt` 攒指令，`while(accumulator >= 1)` 逐条执行，`yield`（wait）立刻跳出。所以 `--ticks` 数的是 tick、`--steps` 数的是指令；微处理器 `ipt=2`、逻辑处理器 8、超处理器 25，`wait 0.5` ≈ 30 ticks。两个必须记住的坑：①**`setBlock` 放下的方块 `efficiency == 0`**，`edelta()=0`，accumulator 永远不涨，`updateTile()` 静默什么都不做——先 `b.efficiency = 1`；②`jump N` 的 N 是 **0 基语句序号**，`jump 1 always` 跳第二条，`jump 2` 在三条程序里跳自己形成自旋；另外汇编器会为缺省比较操作数生成一个占位变量 **`x`**（`set z 1` + `jump 1 always` → vars `@counter, z, x`），读变量时别把它当程序变量。新增 `tools/mlog_needs.py`：扫 `.mlog`/`.msch`，把 `sensor` 属性、`ubind` 单位、`ucontrol` 子命令、`ulocate` 目标、`radar` 过滤、`printflush`/`control` 方块、跨处理器 `read/write` 链接、世界全局量汇总成 JSON/Markdown；`.msch` 会用蓝图自己的链接表把 `message1` 之类解析成真实方块类型（`message1(message)`），纯 `.mlog` 没有链接表，只能给候选名。全量 `out/` 跑出 1431 文件 / 5773 程序 / 2 个坏文件，最高频是 `sensor @x/@y/@name/@flag/@enabled/@dead`、`ubind @flare`、`ucontrol flag/itemDrop/approach`、`printflush sorter1`；demo 子集 34 文件 / 35 程序，需要 `@flare/@mono/@poly/@mega` 四种单位。`mlogsim.py --units flare:2` 可直接在处理器旁刷单位：`Vars.state.rules.logicUnitControl = true` 后 `UnitType.spawn`，但暂停世界不跑 `Teams.updateTeamStats()`，**必须手动调一次**，否则 `ubind` 的 `unitCache` 是 null、`@unit` 绑不上。限制：暂停世界不跑单位物理，`ucontrol move` 只写指令不改坐标；单位传感器（`@health/@x/@y/@dead` 等）可读。

- 第 60 次整理：**默认世界改成 64×64 空白图**。用户问「减小世界大小对运行效率会有提升吗」，实测分两段：启动（JVM+server 1.80s、host 随机图 0.46s）与执行（2000 条指令 0.35s 含 JIT 冷启动、同进程第二轮 0.04s；`loadGenerator(100,100)` 后同样 0.04s）。**地图大小对执行时间没有影响**——`tile` 查找 O(1)，暂停的世界不跑世界模拟；能省的只有启动。于是发现更省的一条：不 host，直接 `Vars.world.loadGenerator(64,64,...)`——server 启动后 `Vars.world` 已存在（宽 0），没有端口绑定、没有随机选图，CLI 从 3.93s 降到 2.95s（约省 1s / 25%）。64 是蓝图上限，默认正好装下任何 `.msch`；`--world N` 可改、`--world 0` 或 `--host` 回退随机图（给读真实地形/`@mapw` 的程序）。`run_msch` 加了越界检查：放不下就报 `schematic is 4x1, does not fit the 3x3 world (use --world 4 or --host)`，不再静默截断。三个小坑：①`tiles.fill()` 只是把每个格子换成新的 air 方块（`new Tile(x,y)` 的 floor 也是 air），要 stone 地面得自己 `setFloor`；②host 失败（6567 被占）会留下 java 进程，把后续所有运行挡在端口上，`Server.__init__` 失败必须 `close()` 再抛；③空白世界没有地形，`sensor @floor` 读到的是自己铺的 stone，需要真实地形就用 `--host`。方法论：**先量再改**——世界大小对执行的影响是 0，省的 1s 全在启动；改默认值前先证明它没碰语义（33 个 demo + p8 + `--units` 全过）。

- 第 61 次整理：**tick 模式下 `@time/@tick/@second` 现在会走了**。`GlobalVars.update()` 只在 `State.update()` 里被调用，暂停世界永远不跑，所以 `--ticks` 下这三个量一直是 0（`@time` 是 `state.tick/60*1000` 毫秒，不是墙钟）。修法：tick 循环里每 tick `Vars.state.tick++; Vars.logicVars.update();` 再 `updateTile()`（`.msch` 场景模式在外层 tick 循环做一次，别每个处理器加一次）。实测 120 ticks → `@time=1950`、`@tick=118`、`@second≈1.967`。方法论：**全局量不是常量，是「谁在 tick 它」的产物**——暂停世界把 update 链整条剪掉了，凡是依赖 `State.update()` 的传感器都要单独补。

- 第 62 次整理：**世界模拟开关：`--update all` / `--power`**。用户问「能不能自己控制同步 update 所有工厂，省性能又方便调试」，并定下：电力不纳入闭包、默认满电、电力管理留接口；正确性优先，「全量不会出错就走全量」。实测三件事：①空白世界的 `Vars.state` 是 `menu`，`isPlaying()==false`，`Building.update()` 会走 `updateConsumption()` 这条链并把 `efficiency` 算成 0，工厂完全不动——必须 `state.set(playing)` 才模拟；但**只能在 tick 循环期间置 playing，`finally` 里立刻恢复 paused**，否则 server 自己的帧循环会按真实时间推世界。②`efficiency` 是「所有消费者效率的最小值」，电力消费者的 `efficiency()` 返回 `build.power.status`；没有 `PowerGraph` 时 status 恒 0，所以先 `b.efficiency=1` 没用（`updateConsumption()` 每 tick 重算），要每 tick 把 `b.power.status = 1.0` 才是满电。实测硅冶炼厂（`hasPower=true, consumePower(0.5)`）输入 200 沙+200 煤，120 ticks → 2 硅、`efficiency=1`、`power.status=1`。③`Packages.mindustry.gen.Groups.build` 是 `EntityGroup`，只有 `.size()` / `.index(i)`，**没有 `.get(i)`**；update 可能 add/remove 方块，遍历前先快照，按 `block.name.indexOf("processor")` 跳过处理器（处理器由 step 循环单独驱动，不能双重 update）。默认值：`--ticks` 下 `--update all`，`--steps` 下 `none`；`--power full` 钉 1.0、`--power none` 钉 0.0（预留真实 `PowerGraph` 的钩子）。34 个 demo `--ticks 40` 全过，测试 24/24。代价：JS 逐块 `update()` 约 0.45µs/块（60 条 conveyor 26–29µs/tick），Java 侧 `Groups.build.update()` 一次只要 1.3–1.6µs；现在按正确性优先走逐块 + 跳过处理器，性能优化留到需要时。方法论：**「不更新」也是一种模拟选择，必须显式**——暂停世界不是「没发生」，而是把 update 链整条剪掉；凡是要模拟的世界行为，都得由驱动层逐条补回来，并且只补你声明要补的那部分。

- 第 63 次整理：**单位物理 B 档落地（真执行器 + 只驱动 LogicAI 单位）**。用户定「B 够了，真游戏交给玩家测试」，并把这句话写进 skill 的边界。三件事：①`ucontrol move` 只写 `LogicAI.moveX/moveY`（`LExecutor.java:350-371`），位移发生在 `Unit.update()` → `controller.updateUnit()` → `updateMovement()` → `VelComp.update()`（`move(vel * Time.delta)`）→ `move()` 做 tile 碰撞检查。所以模拟器每 tick 只需对「`controller() instanceof LogicAI`」的单位调一次 `u.update()`；野 AI、波次、战斗目标都不碰。②空白世界没有核心，`Units.getCap(team)` = 0，`Unit.add()` 里 `count() > cap()` 会立刻 `unitCapDeath`：spawn 出来就是 `valid=false/dead=true/hp=70`，`Groups.unit` 马上清空。所以 UNIT_JS 里先 `Vars.state.rules.unitCap = 1000`。③`Groups.unit` 是 `EntityGroup`，`size` 是方法不是字段（`UG.size()`），`index(i)` 取元素；遍历前快照，update 可能 kill/despawn 改变分组。实测：`_t_move.mlog`（ubind flare、ucontrol move 40 40）300 ticks → `@x≈39.95,@y≈39.81`；`within 40 40 2` 从 0 翻到 1；`--update none` 时单位停在 2,2；24/24 测试、36 个 demo `--ticks 40` 全过。已写进 `.dsh/skills/mlog-agentskill/SKILL.md` 的边界：模拟器只到逻辑层 + 单位运动层，真游戏行为必须由玩家验收。方法论：**引擎里「已经有一半」的行为，先找它的入口函数，再决定只调哪一段**——`u.update()` 是整条链，`controller.updateMovement()` + 物理是中间段，自己积分是最后手段；能用真链就别自己写。
- 第 64 次整理：**天气状态机接进模拟器（不是 stub）**。用户说「天气就一个状态机，不难吧」，源码证实：`Logic.updateWeather()`（`Logic.java:376-391`）每条 `WeatherEntry` 的 `cooldown -= Time.delta`，到期且未激活就按 entry 自己的 min/max duration/frequency 随机 `duration`，再 `Call.createWeather(entry.weather, entry.intensity, duration, 随机方向)`；激活中的天气由 `Groups.weather.update()` 扣 `life`，`life<0` 移除（`Weather.java:297-324`），`fadeTime=240`。模拟器实现：tick 循环里先 `weatherTick()`（复刻 updateWeather 的 cooldown 逻辑，随机数用固定种子的 LCG `WSEED*16807%2147483647`，保证同命令同结果）再 `Groups.weather.update()`。三个必须记住的坑：①`weathersense`/`weatherset` 是 privileged（`LStatements.java:1667,1721`），微处理器解析时整行换成 InvalidStatement **静默消失**——程序里出现这类语句必须放 `world-processor`（ipt=8，`Blocks.java:6949`），自动判定在 `--processor auto`；②`weatherset true` 在天气已激活时是把 `life` 重置为 `fadeTime`，所以循环里每 tick 都 set true 的天气**永远不会自然过期**（写测试程序时别把 `weatherset` 放在循环体里还指望验证 240 tick 过期）；③tick 模式第一 tick 不执行任何指令：`LogicBlock.updateTile()` 是先把 accumulator 加满再 while，`--ticks N` 实际是 N-1 个有效 tick、`@tick` 从 2 开始——这是引擎语义不是驱动 bug。另外 `maxTextBuffer=400`（`LExecutor.java:46`），print 超长会被游戏截断。实测：`_weather.mlog` 6 ticks → `rain1` 从 0 翻 1、world processor、ipt=8；`_weather_life.mlog` 300 ticks → 天气在 tick 2 创建、tick 243 感知为 0（240 tick fadeTime）；`--weather rain` 强制开局激活；44 个 demo `--ticks 40` 单 server 全过、24/24、p8 仍 a=7/b=null/c=null。方法论：**特权指令的失败方式是「静默删行」，不是报错**——任何带天气/规则/消息的程序，先确认它落在哪个处理器上，再看结果，否则你测的是一段被删过的程序。
- 第 65 次整理：**演示：mono 绕处理器转圈**（`out/_mono_orbit.mlog`，900 ticks 约 1.4 圈，稳态半径 1.7–2.2，目标 2）。三个语言事实，都是这次踩出来的：①`ucontrol move x y` 的坐标是**逻辑 tile 坐标**，不是 world 像素：`LExecutor.java:352` 用 `World.unconv`（tile→world，乘 8）存进 `LogicAI.moveX`，`AIController.moveTo` 再按 world 追；`sensor @x/@y` 返回的也是同一套 tile 坐标（`ucontrol move 5 5` → `@x≈4.95`）。第一版把 world 尺度的 `cx=4 r=12` 直接当 tile 传，目标被放大 8 倍（≈(128,38)），单位飞向远端后冻结。②`op sin/cos` 吃的是**角度**不是弧度：第一版 `d=0.02`（本想当弧度）每 pass 只转 0.02°，目标几乎不动，单位到位就停；改 `d=4`（度/pass）才转起来。③`ucontrol` 只写意图，单位每个 pass 重新追移动目标；不会因为「到过一次」就锁死，但半径会有 0.2–0.3 tile 的抖动（转向 + 加速度限制），要更圆就降角速度或加大半径。工具侧新增 `--unit-pos X,Y`（tile 坐标）：默认 `--units` 在处理器旁 2 tile 处生成单位，演示需要「正好从圆上出发」时用它（`--unit-pos 6,4`）。方法论：**坐标单位是模拟器里最容易「看起来对、其实差 8 倍」的东西**——先做一次 `ubind @mono / ucontrol move 5 5 / sensor @x` 的最小实证，再谈轨迹。
- 第 66 次整理：**战斗 tick 与 trace/assert 落地**。用户定「战斗先搁置？」后来改成 P0 两条：战斗 tick、trace/断言都做。战斗层按 `Logic.updateEntities()`（`Logic.java:486`）的顺序镜像：每 tick 先 `Groups.bullet.updatePhysics(); Groups.unit.updatePhysics();`，逻辑 step 后再 `Groups.bullet.update(); Groups.bullet.collide();`。三个必须记住的点：①不开战斗时 `ucontrol target` 仍然会 `shots` 增加、子弹对象也会进 `Groups.bullet`，但它们**不动、不碰、不结算伤害**——所以「开火」和「命中」必须分开验证，用 `--combat off` 做对照，看目标 hp 有没有差；②trace 只记 `controller() instanceof LogicAI` 的单位，即处理器真正接管的那个；没 `ucontrol` 过的野单位不在表里。列 `unit,tick,ux,uy,uhp,range,tx,ty,dist,cx,cy,chp,bullets,shots` 全是 tile 坐标，`range` 是 `@range`，`tx/ty/dist` 只在 `ucontrol target` 下非空，`cx/cy/chp` 是最近的敌方 `CoreBlock`（`Groups.build` 里按方块类型 + 敌我筛，不用 `ulocate`，所以不受特权/射程限制），`bullets` 是 `Groups.bullet.size()`，`shots` 是各 weapon mount 的 `totalShots` 之和；③TRACE 行是 JS 里 push 到数组的，**必须显式 `print` 出来**，否则 Python 端一行都收不到（第一版就栽在这，trace 0 行且没有任何报错）。断言：`--assert EXPR` 对每一行求值（不变量，如 `dist >= range - 1.5`），`--assert-last EXPR` 只对最后一行（结果，如 `chp < 1100`），列名直接当变量、`eval` 禁 builtins，任一失败退出码 3。实测（dagger 打 coreShard，200 ticks）：combat on → 核心 1100→974、shots=15、在飞子弹 1；combat off → 核心 1100、15 发子弹全部原地不动；`--assert-last "chp < 1100"` 过，`--assert "dist >= range"` 故意写错会 FAIL 并退 3。另外修了 `_scene_loop_js` 生成 JS 的括号错误（多一个 `}`，报 `EvaluatorException: 'try' without 'catch' or 'finally'`）——生成代码也要当代码测。回归：24/24、49 个 `out/*.mlog` `--ticks 40` 单 server 全过、p8 `a=7/b=null/c=null`、天气 `rain1=1` 不变。方法论：**「能开火」不等于「能打中」**——`shots` 只证明指令执行了，伤害必须从目标 hp 的变化读出来；有对照（combat on/off）才能把差值归因给子弹物理。
- 第 67 次整理：**场景载入（.msav）与「炮台为什么不开火」**。用户给的是三张 `.msav` 存档（不是蓝图）：`open`、`garded-line`、`maze`，自带地图/队伍/核心/建筑/单位，正合适当通用调试场景。实现：`Server(..., save=)` 把存档复制到 `<workdir>/config/saves/scene.msav`，控制台 `load scene`（slot 名**不带** `.msav` 后缀），等 `Save loaded.` 后 `pause on`，再用螺旋搜索从我方核心往外找第一块「air + 地板不实心」的格子放处理器；世界尺寸从存档读，不再用 `--world`。三个坑：①存档里的 `state.tick` 是存档时刻的值（实测 1500+），每次运行前归零（`Vars.state.tick = 0; Time.setInternalTime(0)`），否则 `@tick`/`@time` 不可复现；②`Timer`/`timer()` 类建筑逻辑吃的是 `Time.time`，只 `state.tick++` + `logicVars.update()` 不够——炮台 `findTarget()` 由 `timer(timerTarget, targetInterval)` 门控，`Time.time` 不前进就永远不选目标，射程、弹药、敌我全对也不开火；每 tick 必须 `Time.update()`（`Logic.update` 正是这么做的）。这是这次卡最久的点：trace 里 `bullets=0`、`uhp` 不变，但 `enabled=true/ammo=1`。③`--unit-ai all` 只是对非 `LogicAI` 单位也调 `u.update()`；`CommandAI` 单位没有命令时仍然不动（原版服务器没有指挥官），所以 garded-line 里 5 个 `crux:fortress` 保持静止，炮台才是真正会还手的部分。实测：`open` 载入后 `_sim_a.mlog --ticks 20` 仍 `result=43`；`garded-line` 里把 dagger 放到 (46,31)（salvo/duo 旁边）跑 120 tick → hp 150→22、trace 50 行、tick 从 2 开始。另修 `WORLD	64x64` 的解析（第一版 `int(out[0].split('x')[0])` 把 `WORLD	64` 丢给 int）。方法论：**「世界不更新」和「世界更新了但计时器没走」是两种病**——前者看 `state.isPlaying()`/`update()` 有没有被调，后者看 `Time.time` 有没有前进；炮台不动时先读它的 `target`/`reload`，再怀疑射程。
### 第 68 次整理：堡垒寻核（真执行器）

- ulocate building 是 8 参数：locate flag enemy ore outX outY outFound outBuild；enemy=true 走 indexer.getEnemy(unit.team, flag)，ore 占位也必須给（@copper）。
- 堡垒 @range=29.5 tile（artillery 240 world 减 margin）；speed 0.43 是 **world/tick**，折 0.054 tile/tick，跨 60 格约 1100 tick。
- 单位 spawn 在 solid 格（核心/处理器）上，第一次 u.update() 就 kill()（UnitComp 的 !canPassOn() 分支），900 HP 一帧归零；--units 现用 reeSpot 找 air+非液体地板并避开基站格；PICK_BASE_JS 也排除 loor().isLiquid（水不是 solid）。
- --unit-pos 改为格中心 x*8+4。
- 场景实测：open 从基地 1200 tick 到 28.3 格、核心 3500→1137；maze 直线撞墙停在 46.9 格（B 档无寻路）；garded-line 被 5 个敌方堡垒打到 12 HP，只开 1 炮。
### 第 69 次整理：跳转越界没人报错，只有检查器会报

- 粘贴版（聊天里少贴一个 end）只有 29 条语句（0..28），三处 jump 29 越界；游戏 LAssembler 照收，JumpStatement.destIndex 保留 29，LExecutor.runOnce 发现 counter 越界就归 0，于是每次执行都跳回第 0 条——表现是逻辑“断跳/卡在开头”，控制台无报错。
- mlog.py check 会报 [ERR] jump target 29 out of range (0..28)；游戏内粘贴不会。
- 定案：逻辑只留一个 end。堡垒寻核改为 29 条（0..28），三处 jump 28；装进游戏实测 N=29、destIndex 28/28/28，open 场景 1200 tick 仍是 dist 28.28、核心 3500→1137。
- 教训：给用户的代码块必须与仓库文件逐行一致，end 不能省。
### 第 70 次整理：tick 1 预检（编译、生成数量、单位存活）

- mlogsim 默认在 tick 1 做三件事：`b.executor.initialized()` 必须为真；`--units` 的请求数必须全部生成；生成出来的每个单位 `isValid()` 必须仍为真。失败抛 `PREFLIGHT: ...`，退出码 1；`--no-preflight` 只关第三条。
- 动机：单位落在实体格上时第一次 `u.update()` 就被 kill，之后的 1200 tick 只是“单位没动”，日志无任何报错。预检把这种静默错误变成 tick 1 的显式失败。
- 实测耗时：编译错误 3.1 s 退出；正常 10 tick 3.3 s；open 场景 1200 tick（含 trace）5.8 s——之前“每次跑 30-40 s”的估计偏高，真实成本主要在诊断而非运行。
- 实现点：`UNIT_JS` 保存 `SPAWNED` 数组并核对 `made < total`；`PREFLIGHT_JS` 的 `preflightTick()` 只在 `i==0`/`t==0` 调；`STEP_JS`/`SCENE_JS` 编译后直接查 `initialized()`。
- 验证：compile 失败 `jump nowhere`、未知单位 `nosuchunit:1` 均 3 s 内报 PREFLIGHT；24/24、p8（a=7/b=null/c=null）、天气、堡垒 open 1200 tick 全部不变。
### 第 71 次整理：现实场景（PVP / campaign）与 v160.7 默认

- 默认 jar 改为 v160.7（`out/_server160.jar`，19,453,000 B）。build 160 存档在 v159.3 报 `Error reading region "map"` / `Could not skip bytes. Expected length: 16842752; Actual length: 11699`，v160 可读；PVP 两版都能读。`_default_jar()` 顺序 MLOGSIM_JAR → v160 → v159 → v146。
- PVP：64×64，sharded/crux/blue，双方各 2 核心（nucleus 6000 + shard 1100）、钻头/传送带/工厂、5 mono/5 poly；蓝队 118 item-source/62 scorch。campaign：单队核心 3500、硅/塑钢/爆炸物/冷冻液/电力、8 mass-driver、1 个 5534 字节 micro 处理器（不会被当入口执行）。
- 堡垒在 PVP 上 `ulocate` 到 crux shard(49,14)；从 (35,20) 出发会后退到 25.6 格并开火（核心 1100→1056）。从基地出发会被基地建筑卡住（B 档不寻路）——实景测试用 `--unit-pos` 放空地，或换 open。
- `ulocate ... outBuild` 只在 `within(max(unit.range, buildingRange))` 时赋值：47 格时 `core` 为 null，`core.x/core.y` 仍有效。判存在用 found?，不要用 outBuild。
- `--save` 载入后世界时钟归零；campaign 自带的 5534 字节处理器不参与执行（`--update all` 跳过 processor）。

### 第 72 次整理：三个盲区合成台（memory / processor / sensor）

- memory-bench：未写过的记忆格槽读 **0**，不是 null；`read d writer1 "declared"` 跨处理器读到 42；`write 99` 后同一轮 `read` 立即读到 99。同队处理器按名读写不需要 `logicUnitControl`。
- processor-bench：micro/logic/hyper/world 的 `@ipt` 实测 2/8/25/8；hyper 可写 bank 槽 63=25；world 的 `setrule unitCap 77` 编译并生效（同一行在 micro 里被静默丢弃）。
- 链接范围是 10 格（`LogicBlock.range = 8 * 10`）。超范围链接不报错、装载时变成 null——台子第一版把 cell 放到 14 格外，read 全 null，就是它。
- sensor-bench：五个单位（dagger/flare/mono/mega/fortress）的 health/armor/shield/range/speed/flag 与引擎值逐一相等；`@type` 返回类型对象；无玩家/无命令时 `@controlled=0`。fortress `@range=29.5`、`@speed=3.225`（tile、tile/秒）。
- 两个工具坑：`mschgen.Blueprint.add_block()` 拒绝逻辑方块，要 `add_logic(block="logic-processor")`，默认 micro；mlog 的 `print` 只吃一个参数，多参数只打第一个。


### 第 73 次整理：核心库存取放、aigenerated、两条“静默”规则

- `--core-items silicon:400` 遍历我方（sharded）核心逐个 `items.add`；空白世界会在 base+(6,4) 自动放一个 `core-shard`。放完必须 `Vars.indexer.addIndex(tile)`——`Tile.setBlock` 不更新索引器，否则 `ulocate building core` 永远 `found?=0`。
- 取放料距离 = `logicItemTransferRange`（45 world）+ `block.size*8/2`；核心 3×3 约 6 格，间距 7.1 格取不到，要先 `ucontrol approach core.x core.y 2`。
- core-bench：`--core-items silicon:400`，取 15、放回 5，断言 385 / 15 / 10 / 390；四台合计 62 项全绿。
- `ucontrol itemTake` 还要求 `build.team==unit.team`、`build.items!=null`、第二参是 Item、`timeoutDone(unit, LogicAI.transferDelay)`；`itemDrop` 额外要 `allowDeposit()`。
- 特权内置变量 `@server`、`@client`、`@clientLocale/@clientUnit/@clientName/@clientTeam/@clientMobile/@clientMusicPlaying` 在普通处理器里被 `GlobalVars.get(name,false)` 换成 `"null"` 常量，不报错；只有 world processor 有真值。
- `wait`/`stop`/`printflush @wait` 的 yield 只让出本 tick 剩余 ipt，等待期间处理器静止；要边等边算就用 `op add cfg.timer @time 500` + `@time >= cfg.timer` 判定，别用 `wait` 空转。
- `tools/aigenerated.py`：`sign` 写文件头注释 + `end` 之后的不可达 `set`，哈希只覆盖正文；`verify` 检头部/正文哈希/尾部；`strip` 直接拒绝（退 2）。`.msch` 存源码，先签 `.mlog` 再生成，标记随源码进蓝图。
- 回归：`tests/run_tests.py` 24/24；四台 62 项全 PASS；场景 README 同步为“四个合成台”。


**第 74 次整理（2026-10-20）：检查器认识特权内置变量**

- `check` 新增 INFO：`@server` / `@client` / `@clientLocale` / `@clientUnit` / `@clientName` / `@clientTeam` / `@clientMobile` / `@clientMusicPlaying`。
- 语义：`GlobalVars.get(name, false)` 对 `privilegedNames` 直接返回 `"null"` 常量（GlobalVars.java:253-256），普通处理器里不报错、读到 null；只有 world processor（privileged=true）有真值（:81-90）。
- `check` 是静态的，`.mlog` 不说明方块类型，所以报 INFO 而不是 WARN；world processor 是合法例外。
- 语料 65 份 `out/*.mlog`：16 份 29 条命中，集中在 `无线超-v3`(4)、`无线超-v2`(3)、`_ai-wireless`(3)、`other-ai`(5)，其余多为 `_t`/`_emod`/`_ds_*` 测试文件；`print "@clientUnit"` 这类字符串不算（检测前先剥引号内容）。
- golden 25 条；`rules/privileged-var-needs-world-processor.json`（semantics/INFO）；反例用 `print "@clientUnit…"` 字符串。
### 第 75 次整理（2026-10-20）：链接自动接线 + 三条语义纠正

- `--links auto`：裸 `.mlog` 没有链接表，模拟器从 `uses - defs` 找 `cell1`/`bank1`/`message1`/`dome1` 这类名字，按别名表放同类方块并用 `new LogicBlock$LogicLink(x,y,name,true)` 接上，再 `updateCode`；`--links off` 才是 null。
- `LogicLink` 的 x/y 是格坐标（游戏自己的建链代码用 `tileX()/tileY()`），`updateCode` 用 `world.build` 还原；`validLink` 要求同队、`within(range + 半宽)`，`range = 80 world = 10 格`。
- 自动接线前必须 `b.executor.team = Team.sharded`，否则 `MemoryBuild.readable` 判队伍不符 → 读写都是 null（`MemoryBlock.java:59-81`）。
- `set cfg.count 0` 不是死代码：它是留给使用者改的配置面；规范 §2 已写明，交付时在文件头写含义与范围，`ir` 报“赋值未读”先确认是不是参数。
- `ubind` 给类型是按 `unitCache` 轮转（`exec.binds[id]` 取模自增），给单位是直接绑；要盯一个单位就别每轮 `ubind @type`。
- 顺带：`_link_test` 42/4242；`无线超-v3` 在 PVP 存档上自动接 `dome1`。
### 第 76 次整理（2026-10-20）：read/write 按名字访问处理器变量

- `read a @this "secret"` / `write 9 @this "secret"` 在**模拟器里本来就能跑**（真 `LExecutor`）：`LogicBlock.read` 先 `executor.optionalVar(name)`，没有变量再 `optionalLink(name)`；数字下标才是链接。
- `LogicBlock.write` 找不到变量名或目标是常量时直接 return，**静默空操作**；所以 `write 5 @this "nope"` 什么也不发生。
- 缺的是静态分析：`mlogir` 之前不把字符串地址当变量。现在 `Stmt.addr_reads/addr_writes` 记录 read/write 的 `@this "name"`，`check` 报两条 INFO：`self-read-undefined`（读未声明，得 null）、`self-write-noop`（写未声明，空操作）。带编号的名字（`cell1`）按链接算，不报。
- `ucontrol idle` 的绑定架构：`ubind` 只写 `@unit`，不认领控制；第一条 `ucontrol`/`ulocate` 走 `checkLogicAI`，把 `LogicAI` 挂到单位上（控制器=本处理器，清 `mineTile`/`buildPlan`），并把 `controlTimer` 续到 600 tick。`idle` 只设 `control=idle`，`LogicAI.updateMovement` 没有 idle 分支，所以它**不发运动指令**（速度靠 drag 衰减），也不清 `mineTile`——那是 `stop` 的事。
- 证据：`_this_test` → `a=7,b=9,c=null`、text `7/9/null`；`_idle_test` → `@controlled=1`、`@controller=micro-processor`。
- 坑：`tests/run_tests.py` 导入的是 `mindustry-blueprint/tools/` 副本，改根 `tools/mlogcheck.py` 后必须复制并 `sync_mlogagent.py`；`--write --case` 会把 golden 重写成一条，恢复用 `git checkout -- tests/expected.json` 后全量 `--write`。golden 26 条。
### 第 77 次整理：@counter 也是跳转，署名藏在参数尾巴（2026-10-20）

1. **`set`/`op` 写 @counter，检查器以前当普通语句**。现在 `_counter_target` 和 `mlogir.successors` 都算：取指先自增，所以 `op add @counter @counter K` 落到 `i+1+K`，`set @counter N` 是绝对 N；变量/解析不出的目标按全可达处理，越界按 `[]`（真执行器把 counter 归 0）。golden 新增 cost/counter-op（`[2,4]`）、counter-set（`[1,2]`）、counter-unknown（无不可达）。
2. **digest_cost 解析 UNREACHABLE 时差点把 `⏸ blocking` 的 L3/L5 当不可达**。必须只认 UNREACHABLE 段内的 `L\d+:`，遇到 `opcodes|loop heads|worst-case|⏸|reachability` 就退出该段；否则 wait1/wait2 的 golden 全被污染。
3. **AI 署名改成“命令的无效字符串参数”**：`end "aigenerated:猪猪鱼:<id>"`。`LParser` 按声明参数个数填字段，多出来的 token 解析后丢弃，所以指令行为、print 输出、语句数、最坏指令数都不变；注释会被游戏剥掉，`end` 后再加 `set` 会改 jump 相对位置，都不行。
4. **签名不能自毁**：`_body` 先剥掉签名和旧式 `# @aigenerated`/`set aigenerated.*` 行再算 sha256，id 取前 12 hex；改正文再 `sign` 会拒绝，必须 `--force`；`verify` 发现改正文/删 token 退 1；`strip` 退 2。测试 `tool/aigenerated` 跑 sign/verify/篡改/拒签/强签/strip 七步。
5. **测试导入的是分发副本**：`tests/run_tests.py` 的 `TOOLS` 指向 `mindustry-blueprint/tools`，改根 `tools/*.py` 后必须复制两份再跑，否则 digest 为空/旧。本次 30/30。
第 78 次整理：隐签名改到 jump 的 p4 槽
- 尾参数方案作废：`end "aigenerated:..."` 的多余 token 在 LParser 里就丢，游戏 `LAssembler.write` 往返后签名消失。
- 也验证了 `end` 后加 `set` 会被整段丢弃（write 输出到 `end` 就停），`op`/`control` 的多余 token 同样丢。
- 能活下来的位置是语句声明的参数槽：`jump 0 always 0 "aigenerated:作者:id"` 替换末尾 `end`。always 不读 p3/p4；end 与 jump 0 都把 @counter 置 0，语义等价；p4 是 JumpStatement 的字段，write 原样保留。
- `LAssembler.write` 的签名是 `write(Seq<LStatement>)`，没有 `write(LExecutor)`；`read` 要 `privileged=true` 才认特权语句。
- aigenerated.py 哈希改成 sha256(author + "\n" + body)[:12]，作者进哈希；旧式头注释/`set aigenerated.<id>`/尾参数在重签时清掉。
- 实测：sign→id 63fa438c6056，verify OK；check 0 issue；mlogsim 行为不变（血量序列同前）；tests 30/30。
第 79 次整理：gen 默认自动签名
- `tools/mlog.py gen` 现在默认先签再打包：`--source` 把源 .mlog 原地签好再读回；`--logic`/stdin 在内存里签；`--no-sign` 关闭，`--author` 换作者。
- 已有签名且正文未改：`sign` 返回 already signed，不会重写文件；正文改过则自动 `--force` 重签（生成流程不为签名停下）。
- 打包前的 VERIFY 比对的是**签名后的 code**，所以蓝图里存的源码带签名；`LAssembler.write` 往返保留 jump 的 p4。
- golden：`digest_aigenerated` 增加 `gen/gen_nosign` 四个字段（rc、蓝图里是否带签名、源文件是否带签名），30/30。
- 注意：`gen` 会写源文件；不想让工具改文件时用 `--no-sign` 或先复制。


### 80. 读核心库存与“写满停”

- **读核心没有内置变量**：`@core` 不存在。唯一正规路径是先用 `ubind` 绑一个己方单位（`ulocate` 的 `checkLogicAI` 要求 `@unit` 非空），再
  `ulocate building core false @copper cx cy cf core`，然后 `sensor n core @silicon` / `sensor cap core @itemCapacity`。
  `cf=0` 要先判掉；`core` 只是接收第 8 个输出的变量名，不是关键字。
- 写满停用 `op mul a n 1000`、`op mul b cap 999`、`greaterThanEq a b` 做千分比比较，避免浮点；满则对 9 台硅炉
  `control enabled <炉> 0`，未满/失败则 `1`（失败保运行）。`control enabled` 落在 `BuildingComp.control(LAccess,double,...)`：
  `if(type == LAccess.enabled) enabled = !Mathf.zero(p1)`，与 UI 的开关同一条路。
- 实测：核心 3996/4000（99.9%）→ `st.on=0`、`e=0`；1000/4000 → `st.on=1`、`e=1`。
- mlogsim 两个测试用修复：①`freeSpot` 只看原点格的 `block()==air`，多格方块的其余格仍是 air，3×3 炉会重叠；
  改为维护 `placed` 矩形并检查 `t.build != null`（`Tile.build` 是字段不是方法）。②自动核心改放到世界远角，
  否则自动接线在基地旁的炉子会压到核心的非原点格，把整个核心删掉、`ulocate` 返回 `cf=0`。

## 第 81 次整理：链接名只看最后一段（2026-10-21）

- `LogicBlock.getLinkName()`：方块名按 `-` 切，最后一段是 `large` 或数字就取前一段。`silicon-arc-furnace` → `furnace1`，写全名永远不绑定。
- 症状：`control enabled silicon-arc-furnace1 1` 不报错、静默无操作；`jump` 行号全对也白搭。
- `check` 新增 ERR `link-name-hyphen`：名字里带 `-` 且不是字面量/`@` 开头就报。fixture `link-hyphen.mlog`（2 条 ERR）。
- 修法：`Logic/写满停.mlog` 全部改 `furnace1..9`，重签 id `bac1e1ef283b`；`mlogsim` 的 `LINK_ALIASES` 改为 `furnace: silicon-arc-furnace`。
- 复测：3996/4000 → `st.on=0,e=0`；1000/4000 → `st.on=1,e=1`；31/31 golden。

## 第 82 次整理：批量/预热与统一入口

- `mlogsim.py` 支持一次启动跑多个文件：`--ticks 20` 跑 10 个文件 5.25 s（逐个冷启动约 37 s）；每个文件前 `reset_world()` 重载世界（约 0.12 s），`prepare()` 重放 init-js/核心/单位/天气。
- `--daemon` 预热 + `--remote` 投任务：单文件 0.61 s（含 Python 启动），冷启动约 3.7 s；预处理阶段就可以先起 daemon。
- 预检扩展：`LINKWARN`（未知方块/没地方放）与 `updateCode` 后 `link.valid == false`（目标缺失或超 10 格）都直接 `PREFLIGHT: link 'x' did not bind`，不再等跑完才发现 null。
- `mlog.py` 收编：`sim`（转发 mlogsim）、`ranges`/`jumps`（mlogrange）、`post`/`labelize`（aigenerated/mlog_labelize）；`mlog_labelize.main(argv)` 现在收 argv。

## 第 83 次整理（2026-10-21）：蓝图生成器坐标归一化 + BOM
- `Blueprint.build()` 没减包围盒原点：`--at 20,20` 出 24x21、内容偏 20 格；现在 `_origin()` + `_pack(x-ox,y-oy)`，`bounds()` 用 max-min+1，parse 得 4x1/(0,0)。
- 链接坐标本来就是相对处理器（`msch.parse_logic(relative_to=...)` 加回），别改成绝对——双重偏移会得 (43,40)。
- `--source` 必须 utf-8-sig：PowerShell 的 BOM 把首行编成 Noop，`write` 静默不执行。
- 回归 `gen/normalized`：BOM + `--at 20,20` + link/with-block，33/33。

## 第 84 次整理（2026-10-21）：变量声明 = 任意语句首次提及
- 汇编器 `readVar()` 是 `vars.get(name, true)`：任何语句第一次出现名字就创建变量（初值 null），不需要 `set`。
- `draw triangle a b c d e f` 是紧凑声明表（6 个，值 null→0），不是“画三角形”专用；它的参数仍被读，但效果是声明。
- `read/write @this "名字"`：只有**全文从未提及**才算未声明；只声明未赋值读到 null（不是 0），`op add` 仍然报“读 null”。
- `mlogir.Stmt.declares` + `Program.declared` 暴露声明集；check 的 `self-read-undefined`/`self-write-noop` 改用 `mentioned`（defs∪uses）。fixture `check/declared-by-mention`，34/34。
### 85. 序切着陆 v2.1：排序 bug 与 209→65
- 2.0 的 `set num.min itc` 只在进 10 轮循环前执行一次，第 2..10 轮不再产生新的 min，`aclist` 被同一个 `10^(15-id)` 连减，掩码借位。v2.1 每轮重置 `num.min`/`item.min`/`accut`。
- `lookup` 参数序是 `lookup <type> <result> <id>`，写成 `lookup uty unit uid` 会报 result 未赋值；`select` 有 build>=150 版本门，改成 `jump` 比较更稳。
- 所有空 pad 只吃 `abs.min.item`，K=10 名次没被消费；把 `cfg.top` 默认设 1，单轮 min，209 条降到 65 条（~62 指令/周期）。
- `pad.i` 原为 1 基，跳过了第 0 个 pad、`< @links` 又读到 null；改 0 基。
- 模拟器验证：mask 只留硅/钛，`--core-items silicon:10,titanium:4000` → `item.min=silicon`、`pad1 @config=silicon`；反向 `titanium:10` → `titanium`。空白世界 `state.getPlanet()` 为 null，着陆台 `config` 被 `accessible()` 拒绝，测试需 `--init-js` 设 `rules.planet=serpulo` 并去掉效率守卫。
- 提交：`Logic/序切着陆-v2.1.mlog` + `mlogsim` 的 `pad→landing-pad` 别名。

### 86. aigenerated.post 把注释挪到签名前
- `post` 先把 `jump Lx` 转回行号，再把所有 `#` 注释整行搬到末尾（签名行之前），最后签名；正文只剩语句，复制进游戏不会带着半截注释。
- `_canonical` 修复：文件末尾有注释时，原实现把 `end` 插在注释**之前**，`sign_text` 又把最后一行（注释）替换成签名，最后一个注释会丢；现在把尾随注释移到 `end` 之前。
- `Logic/序切着陆-v2.1.mlog`：post（14 label/19 jump→数字，id c42be3de8eb6）→ labelize 重新标注（12 label，id 28a3a1ce8ceb），verify OK、check 0 issue、34/34。

## 87. 注释进签名：token 里带原始行号

- 署名 token 现在可以带第 4 段 payload：`base64url(zlib(JSON [[line, stmt, text], ...]))`；`line` 是输入文件 1 基行号，`stmt` 是该注释之前的语句数（标签行不算语句，重新标注后锚点仍成立）。
- 哈希只覆盖**无注释正文**：`_clean` 直接丢掉 `#` 行，签名/旧标记先剥；所以把注释挪进挪出正文 id 不变，改真逻辑才失败。
- `restore` 不能走 `sign_text`（它会把注释再丢掉），必须直接重建“正文 + 注释 + 签名行”；`extract` 按 `L<line> (stmt N): text` 打印。
- `labelize` 在有签名时先 `extract_text` 拿 payload，重新标注后再 `sign_text(comments=...)`，否则一标注就丢注释。
- `Logic/序切着陆-v2.1.mlog` 重新签为 id `aa28ebad9bdf`，6 条注释（L1/L2/L7/L27/L53/L75），签名行 518 字符；正文 0 条 `#`。
- 教训：`sign --force` 对“注释已在 token、正文无注释”的文件会收集到 0 条注释，必须从带注释的原稿重签或先 `restore`。
