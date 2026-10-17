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
| **查指令格式** | `mlog.py cmd [关键字]` |
| **读信息板内容** —— 蓝图里 message 方块写的字 | mlog.py text <file.msch> [--plain] |
| **查一条指令的读写位** —— 哪个参数是输出 | `mlog.py explain <指令> [子命令]` |
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
- 不跨处理器 —— 别的处理器用 `read x cell1 "名字"` 读它,这里看不见(实测全语料 0 例,但报了 `never-read` 仍要自己确认)
- 只判"值有没有人用",不判"值算得对不对"(`op add dx dy dx` 想算距离却写加法,`ir` 不报)

## 「未定义变量」不等于错误:两种社区写法

静态检查报「`X` is read here but is never assigned anywhere」时,**先别改**。mlog 圈有两个约定俗成的写法,靠规范测不出来:

| 写法 | 为什么不是错 | 检查器怎么判 |
|---|---|---|
| `print 我的名字`(名字从不赋值) | 编辑器**变量列表会显示程序里用到的所有变量** ⇒ 写个自己的名字当变量就是**署名**;打印出 `null` 无所谓 | **INFO**,文案 `signature only` |
| `set // 装载电池组`(变量名是纯标点) | mlog 只有 `#` 起注释(`LParser.java:98-99`),想让注释在变量列表里可见就这么写 | 整个变量名归 `annotation` 层 / 整行跳过 |
| 写了不读的变量 | 同上,为了出现在变量列表里 | `declaration` / `stale-write` 分开看 |

真正要改的是**参与运算或控制流**的未赋值变量:`op add a b c` 里 `c` 未定义 ⇒ 静默当 0;`jump T lessThan i max` 里 `max` 未定义 ⇒ 循环一次都不进;`jump T equal X null` 未定义 ⇒ **恒真**(未赋值=0,`null` 读成 0,只有 `===` 才会假)。

参数槽之外的 token 是**惰性的**(`LParser` 按 `arity` 填字段,多的丢掉),所以 `op rand g 255 b` 不读 `b`、`jump T always x false` 的 `x`/`false` 也不读 —— 署名常写在这些位置。但若署名写进了参数槽**内部**(`control enabled reactor enable 0 by bicker` 的 `by`/`bicker` 正好占 p3/p4),游戏确实会读它们。

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
