---
name: mindustry-blueprint
description: 生成/解析/校验 Mindustry 蓝图与 mlog 逻辑时使用：从蓝图提取逻辑源码、按逻辑生成可粘贴的蓝图码、静态检查 mlog、查方块 content ID 与指令格式。
whenToUse: 涉及 Mindustry 蓝图（.msch / 蓝图码）、mlog 逻辑编写或审查、需要方块尺寸或 content ID 时。
---

# Mindustry 蓝图与 mlog 工具链

## 这个技能能做什么

| 能力 | 命令 |
|---|---|
| **解析蓝图** —— 提取逻辑源码、方块、链接 | `mlog.py parse <file.msch> [--plain] [--no-text]` |
| **生成蓝图** —— 从 mlog 产出可粘贴蓝图码 | `mlog.py gen <logic.mlog> ...` |
| **静态检查 mlog** —— 抓 `@dead` 反用等真实 bug | `mlog.py check <logic.mlog>` |
| **成本分析** —— 死代码 + 最坏指令数 + 折合耗时 | `mlog.py check <logic.mlog> --cost` |
| **死存储 / 不可达代码** —— CFG + 活跃变量不动点 | `mlog.py ir <logic.mlog>` |
| **常量分支 / 可证 null** —— 抽象值不动点 | `mlog.py values <logic.mlog>` |
| **打包配置** —— 字段布局 + 低位能装几个 id | `mlog.py pack <logic.mlog>` |
| **查方块 ID / 尺寸** | `mlog.py id [名称]` |
| **查物品 ID / 解打包配置** | `mlog.py item [名称] [--unpack N]` |
| **查单位属性**（写逻辑第一步选单位） | `mlog.py unit [名称]` |
| **查方块配方 / 容量 / 功耗** | `mlog.py block [名称]` |
| **找参考实现** | `mlog.py find "几个词"` |
| **查指令格式** | `mlog.py cmd [关键字]` |
| **读信息板内容** —— 蓝图里 message 方块写的字 | mlog.py text <file.msch> [--plain] |
| **查一条指令的读写位** —— 哪个参数是输出 | `mlog.py explain <指令> [子命令]` |
| **查这条语句要哪个版本** `format` 147 / `select` 150 | `BUILDS.md`（GitHub 发布说明摘要），`mlog.py explain <指令>` 会直接打印 |
| **查这份逻辑要哪个 build** —— 蓝图不存版本号 | `mlog.py check` 的 `version gate` 行 / `mlogagent report` 的 `build >=N` |
| **跨处理器读写** —— 读到的到底是 null 还是常量 | `mlog.py cross <blueprint.msch>` |
| **回归自测** —— 429 个真实蓝图往返校验 | `mlog.py selftest` |

工具在 `tools/` 下,零第三方依赖(纯标准库)。`python tools/mlog.py --help`。

## 铁律(生成前逐条自查)

1. **`@dead` 死亡返回 1** —— "死了就重绑"必须写 `equal`,不是 `notEqual`。**这条抓出过真实 bug。**
2. **控制单位前必须 `ubind`** —— 否则 `@unit` 为 `null`,所有 `ucontrol`/`uradar`/`ulocate` 静默失效。
3. **`ulocate` 第 8 参必须接住** —— 写 `0` 就丢掉了建筑引用,后面无法 `itemTake`/`itemDrop`。
   (`core` 不是内置关键字,它只是接收这个输出的**变量名**。)
4. **取货点用 `move`,不要用 `approach`** —— `approach` 停在半径外可能够不到仓库,而 `itemTake` 够不到时**静默跳过**。
   `move` 不读第 3 个参数。(`move` 精确到 1 格;`approach` 停在 `radius - 7`)
5. **`ulocate` 要无条件执行,不能放进分支** —— 否则另一条路径上坐标从未赋值,单位会飞向 `(0,0)`。
6. **`end` 是"跳回开头"**,不能用来"结束一个分支后继续往下"。分支互斥请用 `jump`。
7. **`jump` 存的是绝对行号** —— 增删一行全盘偏移,生成前逐条数一遍。重点查:目标是否落在 `sensor`/`set` 这类有副作用的行上。
8. **单位只能带一种物品** —— `itemCapacity` 是**堆叠上限**,不是每种物品的上限。
9. **`op` 是固定元数** —— `abs`/`floor`/`sin`/`rand` 等一元运算只吃 2 个参数。
   (多写的 token 不参与执行,行为正常,但也不是你以为的运算。)
10. **不要自己发明阈值,不要做可行性推算** —— 游戏机制只要求某个下限,满足即满效率。
    实际战场有阻挡、有堵车;**"能跑"是实测出来的,不是算出来的**。
11. **不要为了讨好检查器去改正确的代码** —— 检查器是提示器,实测才是标准。
12. **`end` 之后不要再写语句** —— 它是"跳回程序开头",不是"结束"。写在它后面的都是死代码。
    用 `--cost` 一跑就能看到(会直接列出来)。

## 标准流程

```
写 mlog  →  mlog.py check --cost  →  mlog.py gen  →  游戏内实测  →  结论写回本文件
              ↑                                                        │
              └────────────────────────────────────────────────────────┘
```

**生成蓝图时必须遵守"确定性 + 自验证"**:

- 同一份源码 + 同一组参数 → **完全相同的字节**(不要引入时间戳/随机量)
- 生成前先跑 `check`
- 生成后**必须**重新解析验证(工具已内置,失败会拒绝输出)

## 成本分析(`--cost`)看什么

```
statements      : 159                     ← 语句数,>1000 会被静默截断
reachability    : all statements reachable ← 或列出永远跑不到的语句
opcodes         : op×62, jump×40, ...      ← 指令构成
loop heads      : L28(×80), L52(×80)       ← 循环起始行 + 推定圈数
worst-case path : ~2001 instructions       ← 一次完整决策最坏多少条
    ⚠ over LExecutor.maxInstructions (1000/tick): one cycle needs 2.0 ticks
    micro-processor  @ipt=2    1000 ticks (  16.7 s) per cycle
  ⏸ blocking      : 2 wait statement(s), ~240 ticks (4.0 s) blocked per cycle
      L3: wait -> ~120 ticks
```

**怎么用这三个数**:

| 看什么 | 说明什么 |
|---|---|
| **UNREACHABLE 非空** | 有死代码。多半是 `end` 之后写了东西,或跳转目标写错 |
| **worst-case > 1000** | 一个决策周期跑不完一 tick,单位响应会有对应延迟 |
| **@ipt 换算的秒数** | 直接回答"这套逻辑跟得上战况吗" |
| **⏸ blocking 那行** | `wait` 一条 ipt 都不烧,但周期时间几乎全在这里 |

**注意**:

- 循环圈数靠**守卫里的常量**推定(`jump 37 greaterThanEq index 80`)。看不到常量的循环按一圈算并给出警告
- 结果是**上界**(互斥分支不剪枝),意思是"最坏能到多少",不是"平时多少"
- 回到第 0 行的回边 = 主循环,只算**一圈**(mlog 本来就每 tick 重跑一遍)
- **`wait` 单独算**:参数是**秒**(60 tick = 1 秒),`wait 0` 不阻塞、只是"每 tick 跑一遍";
  `blocked` 已乘上包含它的循环圈数并加进三种处理器的 tick 数里。参数不是字面量时报 `UNBOUNDED`,不编数字
- 看到 `>=1001` 这种写法,意思是**循环体自己就把 1000 的预算填满了**,真实总量更大、算不出来;
  平静的 `~N` 才是量出来的

## 指令预算:别猜,这是确定的

**一条语句 = 一条指令,`jump` 也是 1 条,和 `op` / `print` 没有区别。**

`runOnce()` 里 **`counter` 先自增再执行,不看指令类型**(`LExecutor.java:111-121`):

```java
instructions[(int)(counter.numval++)].run(this);   // ← 无条件 +1
```

⇒ **钱花在"循环圈数 × 循环体语句数"上,不花在 `jump` 这个字上。**
⇒ 用 `jump` 跳过一段确实省下被跳过那些行,但**跳转自己仍然收 1 条**。

**每 tick 的额度**(`LogicBlock.java:564-578`,`ipt = instructionsPerTick`):

| 处理器 | ipt | 每秒 |
|---|---|---|
| 微型 micro-processor | **2** | 120 |
| 逻辑 logic-processor | **8** | 480 |
| 超级 hyper-processor | **25** | 1500 |
| 世界 world-processor | **8**(`maxInstructionsPerTick = 1000`) | 480 |

**两条容易漏的**:

- **只有 `wait` / `stop` / `printflush @wait` 会 `yield`**,提前结束这一 tick 的额度;**`jump 0 always` 没有这个机制**,会在一个 tick 内把额度烧光
- `setrate` 是唯一能改 ipt 的指令,上限是 `maxInstructionsPerTick`(逻辑卡 **40**,比默认 8 大 5 倍);`@ipt` 立即变新值,但**本 tick 的循环边界已经固定**,下个 tick 才生效

**所以改循环之前先跑 `check --cost`。** 算完的秒数就是单位从"看到"到"反应"的延迟。

## 常用调用

```bash
# 解析:看逻辑源码和结构
python tools/mlog.py parse "schematics/无线超.msch"

# 检查:生成前必做
python tools/mlog.py check logic.mlog
python tools/mlog.py check --msch out.msch

# 成本分析:死代码 + 最坏多少条指令 + 折合几秒
python tools/mlog.py check logic.mlog --cost
python tools/mlog.py check --msch out.msch --cost

# 死存储:赋值了但整个程序(含跨周期)从未读取
python tools/mlog.py ir logic.mlog
python tools/mlog.py ir --msch out.msch
python tools/mlog.py ir --all logic.mlog    # 连语法强制的输出槽一起列

# 值域分析:常量分支 + 可证 null
python tools/mlog.py values logic.mlog
python tools/mlog.py values --msch blueprints/*.msch
python tools/mlog.py values logic.mlog --trace r   # 逐次打印 r 的抽象值

# 打包配置:字段布局 + 低位字段能装几个 id(能直接指认容量 bug)
python tools/mlog.py pack logic.mlog
python tools/mlog.py pack --msch out.msch

# 生成:只放处理器(链接目标需自己摆)
python tools/mlog.py gen logic.mlog --name "我的逻辑" --link dome1@3,1

# 生成:连目标方块一起放(--with-block 坐标是【中心格】)
python tools/mlog.py gen logic.mlog --name "无线超" \
    --link dome1@3,1 --with-block overdrive-dome@4,2=248 \
    --out paste.txt --binary out.msch

# 查方块 ID 和尺寸
python tools/mlog.py id overdrive

# 查指令格式
python tools/mlog.py cmd ulocate

# 查一条指令到底哪个参数是输出(哪个是枚举、哪个会被读)
python tools/mlog.py explain ulocate
python tools/mlog.py explain ulocate ore     # 只看 ore 分支
python tools/mlog.py explain select
python tools/mlog.py explain op add
```

## ⚠️ 最容易搞错的一件事:方块坐标是「中心格」

schematic 里 Stile 存的是方块的**中心格**,不是左上角。**已双重验证**:

- 源码:`Tile.setBlock()` 用 `int offset = -(block.size - 1) / 2` 铺开多格方块 → `(x,y)` 是中间那格
- 实证:624 个真实蓝图里,按"角"解释会产生 **11 处方块重叠**,按"中心"解释 **0 处**

所以一个 3×3 方块,要让它的成品占据 `(3,1)–(5,3)`,**中心要写 `(4,2)`**。

链接的 `name@dx,dy` 也要对到**方块覆盖范围内的任意格**(工具会按 footprint 校验并提示)。

## `ir` 看什么、不看什么

四层分级,默认只打第一层:

| 层 | 含义 | 该不该管 |
|---|---|---|
| `reported` | 值被覆盖前没人读(`overwritten`)/ 从没人读但写了不止一次(`stale-write`) | **是 bug,去看** |
| `slot` | `ulocate`/`ucontrol`/`radar`/`sensor` 的多输出槽没读,且**只写一次** | 语法强制,不是错 |
| `declaration` | `set x 字面量` 且没人读 | 作者的"声明",忽略 |
| `annotation` | 变量名是纯标点(`//`) | mlog 没有行尾注释(只有 `#`),作者拿它当注释 |

`stale-write` 是为「强制输出槽写两次」加的一层:写**一次**且没人读,可能只是语法逼你起个名字(`slot`,降级隐藏);但同一个槽**写两次**且从没人读,第一次写可证被丢弃 —— 那是真 bug。实例:`17十七硫幽灵四熔毁四油海啸组.msch` 的 micro-processor @(16,8) 里 `found` 在 `L6` 与 `L61` 各被 `ulocate` 写一次、全程序无读,改动前它被 `slot` 层藏住(`dead-store 0(+3 hidden)`),改动后才报出来。

**校准(全语料 617 文件 / 2409 块,已排除模拟器蓝图)**:80.9% 的处理器**一条都不报**,p50=0、p90=1;均值 0.829/块是被约 20 个代码生成式蓝图拉高的。抽样 28 个站点人工核对,**全部为真**。

**它不能证明你的逻辑是对的**:
- 不跨处理器(说明:`read`/`write` 可以按**名字**访问另一个处理器的变量(必須提前聲明、寫給未聲明的槽是靜默空操作)。老蓝图库里看不到这种写法,所以对老库「这个变量从未赋值」的判断是可靠的;新库里它是一条合法的"别处赋值"路径 —— 报 A 层之前先确认两份逻辑是不是同一代产物。) —— 别的处理器用 `read x cell1 "名字"` 读它,这里看不见(实测全语料 0 例,但报了 `never-read` 仍要自己确认)
- 只判"值有没有人用",不判"值算得对不对"(`op add dx dy dx` 想算距离却写加法,`ir` 不报)

## 「未定义变量」要先分五层,再决定改不改

静态检查报「`X` is read here but is never assigned anywhere」时,**先别改**。mlog 圈有一整套只用变量列表承载的写法,靠规范测不出来。926 份蓝图包的实测分布(分层把 A 从 883 条降到 77 条):

| 层 | 含义 | 条数 | 改不改 |
|---|---|---:|---|
| **A 真错** | 名字被读的地方,值真的改变行为 | 77 | **要改** |
| B 恒真守卫 | `jump` 两侧都是常量 ⇒ 分支固定 | 55 | 一般不用 |
| C 无效参数 | 名字落在指令**读不到**的参数位上 | 944 | 不用 |
| D 死引用 | 形如链接名,但这块处理器没有这个链接 | 788 | **要改**(静默失效) |
| E 署名 | 只为出现在编辑器变量列表里 | 5540 | 不用 |

- **E 署名**:编辑器变量列表会显示程序用到的所有变量,写个自己的名字当变量就是署名 —— `print by:NOSB(hghg`、`set Madeby mineqwwe`、`jump 21 equal colour ender`、`control config Carrot 0914 0 0 0`。判 **INFO**。
- **C 无效参数**:语句长度 > 指令真正读的位数时,多出来的 token 是惰性的。`control` 只有三个有效位(类型/目标/p1,p2–p4 被各方块忽略);`ucontrol` 按 `semantic_uses` 算,`flag`/`payTake` 只有一个语义参数;一元 `op` 的第三位永远丢掉(`op rand g 255 b` 的 `b`)。
- **D 死引用**:`scatter1` 看着是有效链接,但处理器的链接表里没有它 —— `LExecutor` 的 `validLink(b)` 直接挡掉,`control shootp scatter1` 一发不发,**不报错也不崩溃**。只有 `.msch` 能查(`.mlog` 没有链接表)。
- **`true`/`false` 是常量,不是普通变量**:`GlobalVars.java:54-55` 用 `putEntry` 注册成 1 / 0,`LAssembler.var()` 先查 `logicVars` 才轮到 `putVar` ⇒ `jump T equal X true` 就是 `X == 1`。**我曾只看 `var()` 就断定它俩是未赋值变量,凭空造出 653 条假警告** —— 判内建要查"注册了什么",不是查"解析函数怎么处理"。

`set // 装载电池组`(变量名纯标点)也在这套习惯里:mlog 只有 `#` 起注释(`LParser.java:98-99`),想让注释在变量列表可见就这么写 —— 归 `annotation` 层或整行跳过。

`noop` 单列一条:**判 ERR**。它是 `LStatements.InvalidStatement`(`LStatements.java:48-59`),`build()` 返回空跑的 `NoopI` —— 游戏把**解析不了的语句**替换成它。所以看到 `noop` 等于「这里原本有一条语句,没了」:最常见的原因是**高版本写的逻辑在低版本打开**,旧解析器不认识的语句被丢掉。这种程序**基本就死了** —— 丢的正是干活的那条,后面的 `jump` 还会照旧指向错位置。(极少数只是空行占位,那是特例;按错误报,让人去看一眼。)

真正要改的 A 层:`op mod n n padNeedCount`(模数 0 ⇒ null)、`ubind u` 而 `u` 从未赋值、`control config unloader1 mmm 0 0 0`、`flase` 拼错落在 `ulocate` 的 enemy 位。

**注意惰性位与内部位的区别**:参数槽**之外**的 token 不读(`op rand g 255 b` 的 `b`、`jump T always x false` 的 `x`);但署名写进参数槽**内部**(`control enabled reactor enable 0 by bicker` 的 `by`/`bicker`)游戏确实会读它们 —— 只是因为 `control` 的 p2–p4 对方块无意义，所以仍然判 C。

## `values` 看什么、不看什么

`mlog.py values` 跑的是**抽象值不动点**:给每个变量在每个位置算一个区间/常量,然后回答两个 token 流回答不了的问题。

```
resolved branches: 1
  L3   always taken  jump 5 strictEqual r null    (cond = 1)
provably null: L3 r is null
```

| 输出 | 含义 | 该怎么用 |
|---|---|---|
| `always taken` / `never taken` | 条件两边都是常量,分支恒定 | 要么写错了,要么是刻意的死分支 —— 去看 |
| `... is null` | 这条语句执行时该变量必定是 null | `===` 能区分,`==` 不能(见下) |
| `?` | 不知道(外部输入、`rand`/`noise`) | 正常,别当 bug |

**必须先知道的两条语言事实**:

- **未赋值的变量是数字 `0`,不是 null**(`new LVar` 的 `numval = 0`)。所以 **`equal x null` ⇔ `x.num() == 0`**,对没赋过值的 `x` 恒真;**只有 `strictEqual`(`===`)区分 null 和 0**(`ConditionOp.java:31-40`:两边都是对象才比对象,否则比数字)。看到 `jump ... equal var null`,先怀疑它想写的是 `===`。
- **NaN / ±Infinity 会被静默转成 null**(`LVar.setnum` 的 `invalid()` 检查)。这正是按位剥离循环能退出的原因:`op logn x 2` 在 `x=0` 时得 `-Infinity` → null → `=== null` 成立。

**校准(全语料 2396 块,排除模拟器,39 ms/块)**:4.1% 的块有信号,平均 0.120 条分支 / 0.060 条可证 null;未收敛 0。抽样人工核对,结论都为真。

**它不能证明什么**:
- 外部输入一律 `⊤` —— `sensor`/`getlink`/`ulocate` 拿到的值都算"不知道",所以**只对纯计算链有效**
- 同一变量连改 3 轮就丢精度到 `⊤`(widen),深循环里会变回 `?`
- 不跨处理器,也不判"值算得对不对"(那是人的事)

## `pack` 看什么、不看什么

`mlog.py pack` 认的是**把多个字段塞进一个数字**的惯用法(`data = status*1e8 + outputID*1e6 + inputMask`),然后算**低位字段能装多少个 id**。

```
    `data`  (first seen L2)
      1e8  ->  status   (= data / 1e8)   at L2
      1e6  ->  outputID (= data / 1e6)   at L3
      1e6  ->  mask     (= data % 1e6)   at L4
      low field `1e6` holds 0..999999  =>  20 usable bit positions (ids 0..19)
      !! 22 items exist but only 20 fit: ids 20..21 overflow into the next field
         (raise the separator, e.g. 1e6 -> 1e7)
      note: `outputID` also contains 100x `status`; a correct decode must first
            assert `status == 0`
```

| 输出 | 含义 |
|---|---|
| `1e8 -> status` | 这一层剥出来的是 `status` |
| `N usable bit positions` | 低位字段能表示 `0..10^N-1`,`(10**N-1).bit_length()` 就是能装几个 id |
| `!! ... only 20 fit` | **真 bug**:原版有 22 个物品,`fissile-matter`(20)与 `dormant-cyst`(21)放不下 |
| `note: ... must first assert X == 0` | `op idiv` 不掩高位,`idiv` 出来的值里还含着更高位 ⇒ 必须先断言高位为 0 |
| `ok: ... subtract-mask` | 先 `op mul hi 1eN` 再 `op sub` 减掉高位 —— **解码正确,不报警** |

**它是全套工具里唯一能直接给出"这段代码有 bug"结论的地方**,代价是出现率极低:**全语料 2420 块里只有 3 块(0.1%)** 用这个惯用法。所以它**不是 linter**:拿它扫整个语料几乎什么都看不到,但一旦命中,给出的是具体容量数字,不是"这里可能有问题"。

**边界**:只认 `op idiv|mod <dst> <src> 10**exp`,且同一个 `src` 上要**至少两个不同指数**才算一个 pack site;不重建表达式;`10^3` 以下不算分隔;掩码检测是全程序文本匹配(不做数据流),别处同形的 `mul`+`sub` 可能让真漏判静默通过。

## 独立副本

同一套工具已经打包成独立的 mlogagent 技能（.dsh/skills/mlogagent/），目录自带全部模块与数据，可整体拷走。一审一整套分析用 mlogagent.py report <file>；改完模块后用 python tools/sync_mlogagent.py 刷新那份副本（--check 只比对）。

### `cross` 只看跨处理器,不看记忆格

`read`/`write` 有两种完全不同的用法,别混:

- `read x cell1 "slot"` —— **记忆格**,引号里是**地址变量名**。极常见(我的库 82 份里有它)。
- `read x processor1 "name"` —— **另一个处理器的变量**,引号里是那个处理器里的**变量名**。
  少见:我的库 625 份只有 **9 份**真的指向处理器,彩末包 926 份只有 13 份。

可读的那个槽就是**目标自己的变量**(所以 `set` 就够,`write` 不是必须的),这也是
「必须先在那边声明」的原因。`cross` 把 join(目标自己的所有赋值, 所有外部 `write`)
算出来,分四类报:`never assigned` / `always null` / `constant` / `written, never read`。

自链接(`processor1` 偏移 0,0)是合法写法,读的是自己的变量。

**版本**:按名字读写另一个处理器 / message 方块是 **v7(build 146)** 才有的;v6 的 `read`
只能拿数字下标访问记忆格 ⇒ 一份用它读写处理器的蓝图跑不到 v6 上(`cross` 会带一行
`note : ... v7 (build 146) feature` 提示)。

**报告基线是 build 146**（v7.0 首个正式版）：基线里就有的语句不报，只有更新的才报。判据是 `floor > 146`，不是 `>= 147`。

### 改完分析器先跑測試

```bash
python tests/run_tests.py          # 12 條 golden digest，任何結論變化都會失敗
python tests/run_tests.py -v       # 逐條列出
python tests/run_tests.py --write  # 改了就有意識地改期望值——然後讀 diff
```

digest 是**去措辭的結論**（`(severity, line)` 對、語句數、分支判定、容量位數…），
所以文案可以隨便改，結論一變就紅。`mlog.py selftest` 只證明解析器不丟東西
（429/429 round-trip），這五個分析器的正確性靠這套兜住。

### `values` 的跨处理器模式

只有 `--msch` 会给它跨处理器的知识：先跑一遍 `cross` 拿到每个槽的值，再带着这张表重跑（**只迭代一次**，不做不动点）。单个 `.mlog` 没有同伴，`read` 仍是 ⊤。蓝图不完整时（对方处理器没一起存）报 null 可能只是没存下来。

## 写逻辑之前：先查这三样

写逻辑缺的从来不是语法，是**目标**和**游戏事实**。这三条命令对应后者的三个大头：

```bash
python mlog.py find "wireless overdrive"     # 1. 别人怎么做的（先找参考，别自己发明）
python mlog.py unit flare                    # 2. 这个单位的速度/血量/能带多少货/会不会飞
python mlog.py block silicon-smelter         # 3. 这个方块吃什么、产什么、装多少、多少电
```

- `find` 扫描游戏存档目录里的全部蓝图（`MLOG_CORPUS` 可覆盖），按 `名字/描述/信息板/变量名/指令` 打分，打印 **分数拆解**——匹配得不对时能看出为什么不对。默认跳过 >5000 条语句的块与 >2MB 的文件（`BADAPPLE!!` 是 56 万条语句的动画，`Linux on mlogv32` 是 16MB），这些不是参考逻辑。首次 9 秒，之后读缓存 0.7 秒；`--rebuild` 强制重建。
- `unit` / `block` 的数据由 `tools/units_from_source.py` 与 `tools/blocks_from_source.py` 从源码抽出，`--check` 可校验是否与当前源码一致。**它们只列源码里写了的字段**，缺的字段是引擎默认值（`unit` 会标成 `(default X)`）——不要凭记忆补。

**“这个方块收不收 X”** 是最容易写错、错了还静默的一条——搬错了屏幕上什么都不会发生。规则来自源码
（`BuildingComp.acceptItem` = `block.consumesItem(item) && 容量`，而 `consumesItem` 是消费者填出来的布尔数组），所以：

| `accepts` | 含义 | 例子 |
|---|---|---|
| `any` | 只看容量，什么都收 | `core-shard`、`container` |
| `recipe` | **只收配方里的物品** | `silicon-smelter` 只收煤和沙 |
| `custom` | 收，但收不收/往哪走取决于配置 | `sorter`、`unloader`、`conveyor` |
| `none` | 一律不收 | `landing-pad`、`PayloadUnloader` |

反查：`mlog.py block --accepts coal` 列出所有收煤的方块（配方输入 + `any` + `custom`）。
注意 `custom` 只回答“可能收”，**“现在收不收”要看运行时状态**（sorter 的配置、router 是否空、焚化炉是否通电）。


## 自动打标签

蓝图标签(颜色=维度、私有区图标=值身份)是手打的,但**其中 24 个值可以从内容推出来**,
留出集精确率 ≥70%:

```bash
python tools/label_auto.py                      # 学习规则 + 留出集报表
python tools/label_auto.py --suggest F.msch      # 只输出可信建议(附依据与精确率)
python tools/label_auto.py --apply F.msch --out DIR   # 写回副本,不动原件
```

`数量` / `品质` / `系列` / `无线` / `火控` 这类量不出精确率的值不会出现在建议里 ——
它们要么是主观判断,要么同一份蓝图三种都沾。写回只重写 tags 段,其余字节原样搬运。

## 生成蓝图时的作者标签

本仓库用 `mschgen` 生成的蓝图,`labels` 一律写 `["[blue]DeepSeek"]`
(用户标签体系里的"作品来源"类),描述末尾带 `逻辑 by [#8abcd1]DeepSeek[]`。

## 参考数据

| 文件 | 内容 |
|---|---|
| `tools/wiki_block_ids.json` | 422 个原版方块 → content ID |
| `tools/block_sizes.json` | 446 个方块尺寸(从源码推导) |
| `tools/cmd_index.json` | 86 条 mlog 指令的格式/参数/注意事项 |
| [REFERENCE.md](REFERENCE.md) | 完整知识库:编号体系、机制、坑、被推翻的旧结论 |
| [PATTERNS.md](PATTERNS.md) | 逻辑模式库 + 蓝图工程分析 |

## 关键事实速查

- **蓝图里存的是 mlog 明文源码**,不需要反编译
- **content ID 是"构造顺序号"**,原版方块先构造、mod 后追加 ⇒ **mod 不会让原版方块 ID 偏移**
- **蓝图不存 content ID**,游戏加载时**按方块名解析** ⇒ 放原版方块只要名字对
- **`@dead` 对 `null` 目标也返回 1** ⇒ 兼作"单位不存在"判断
- **`sensor` 的 null 会传染** ⇒ 目标为 null 时所有属性都返回 null
- **链接名 = 内部名按 `-` 切分取最后一段 + 序号** ⇒ `overdrive-dome` → `dome1`
