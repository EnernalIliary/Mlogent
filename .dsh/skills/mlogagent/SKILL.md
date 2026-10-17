---
name: mlogagent
description: 审查 Mindustry mlog 逻辑时使用：一次跑完静态检查/成本/不可达代码/死存储/常量分支/可证 null/打包配置，按证据强弱给出先看哪里，并附每层的校准数字与"不能证明什么"。
whenToUse: 需要审查或解释一段 mlog（.mlog 源码或 .msch 蓝图里的逻辑块）、判断某条语句是否白算、某个分支是否恒真、某个变量是否可能为 null、或某个数字打包了几层字段时。
---

# MLOGAGENT — mlog 逻辑分析

一个入口把六种分析全部跑一遍，并告诉你**先看哪里**。自带完整副本（`tools/` 里 8 个模块 + 5 个数据文件 + `MANIFEST.sha256`），整个目录拷走就能用，不依赖仓库其他部分。

```bash
python tools/mlogagent.py report logic.mlog            # 全部
python tools/mlogagent.py report logic.mlog --brief    # 只要 VERDICT 两行
python tools/mlogagent.py report out.msch              # 蓝图里每个逻辑块各跑一遍
python tools/mlogagent.py info                         # 数据版本 / 模块清单
python tools/mlogagent.py info --verify                # 校验 MANIFEST.sha256
```

位置参数按**后缀**分派：`.msch` 走蓝图解析（一个逻辑块一节），其余按 UTF-8 文本读。

## 先读这一节：五层各自能证明什么

| 层 | 回答的问题 | 证据强度 | 全语料命中 |
|---|---|---|---|
| `check` | 语法/参数位/`@dead` 反用这类**确定**错误，以及未定义变量的五层分级 | 最强，可直接改 | A 层误报 ~0 |
| `ir` → 死存储 | 某个变量**写了没人读** | 强，但分四层（见下） | 抽检 28 站全真 |
| `ir` → 不可达 | 某些语句**永远执行不到** | 最强 | 0 |
| `cost` | 一圈**最坏**要多少指令、`wait` 占多少秒 | 近似，可对拍 | — |
| `values` | 某个条件**恒真/恒假**、某个变量**必为 null** | 中，只报能证明的 | 4.1% 的块有信号 |
| `pack` | 一个数字**打包了几层字段**、低位够装几个 id | 强（低频） | 抽检 3 站全真 |

`VERDICT` 那行是结论摘要；末尾的「先看这里」按上表强弱排序，只指一个地方。

## 死存储必须分层读

`ir` 默认只报 `reported` 层，其余三层计数后隐藏（`--all` 才列出）：

| 层 | 含义 | 该不该改 |
|---|---|---|
| `reported` | 值被覆盖前没人读(`overwritten`),或从没人读却写了不止一次(`stale-write`) | **是 bug**，逐条看 |
| `slot` | 语法强制的输出槽（`ulocate` 的 `found`、`ucontrol` 的返回等）**且只写一次** | 多数不改，作者不需要那个值 |
| `declaration` | `set x <字面量>` 之后没读 | 作者的声明式初始化，无价值 |
| `annotation` | 变量名是纯标点（`//`、`--`） | 作者拿变量名当注释，不是 bug |

`stale-write` 专治「强制输出槽写两次」：写**一次**且没人读，可能只是语法逼你起个名字（`slot`，隐藏）；同一个槽**写两次**且从没人读，第一次写就可证被丢弃 —— 那是真 bug。实例：`17十七硫幽灵四熔毁四油海啸组.msch` 的 micro-processor @(16,8)，`found` 在 `L6` 与 `L61` 各被 `ulocate` 写一次、全程序无读；改动前它被归进 `slot`、只算进 `(+3 hidden)`，改动后才作为 `reported` 报出来。

mlog **只有 `#` 起注释**（`LParser.java:98-99`），没有行尾注释 —— 所以 `set // 上个位置` 是**真语句**，游戏照执行。这类占语料 `reported` 的 222 条，已归入 `annotation`。

## 「未定义变量」要先分五层，再决定改不改

`check` 报 `` `X` is read here but is never assigned `` 时**先别改**：mlog 圈有一整套只用变量列表承载的写作习惯，靠语言规范测不出来，只能从用户嘴里知道。全包 926 份蓝图的实测分布（A 从 883 条降到 77 条，就是这五层分出来的）：

| 层 | 含义 | 条数 | 改不改 |
|---|---|---:|---|
| **A 真错** | 名字被读的地方，值真的改变行为 | 77 | **要改** |
| B 恒真守卫 | `jump` 两侧都是常量 ⇒ 分支固定 | 55 | 一般不用 |
| C 无效参数 | 名字落在指令**读不到**的参数位上 | 944 | 不用 |
| D 死引用 | 形如链接名，但这块处理器没有这个链接 | 788 | **要改**（静默失效） |
| E 署名 | 只为出现在编辑器变量列表里 | 5540 | 不用 |

各层的判据与实例：

- **E 署名**。编辑器变量列表会显示程序用到的所有变量，所以写个自己的名字当变量就是署名：`print by:NOSB(hghg`、`set Madeby mineqwwe`、`jump 21 equal colour ender`（整合者彩色末影的名字，两个都未赋值 ⇒ 0==0 恒真，既是署名又当 `always` 用）、`control config Carrot 0914 0 0 0`。检查器判 **INFO**：目标变量全程序无人读、名字只出现在 `print` 里、或纯标点名。
- **C 无效参数**。语句长度 > 指令真正读的位数时，多出来的 token 是**惰性**的（`LParser` 按 `arity` 填字段，多的丢掉）。`control` 只有三个有效位（类型 / 目标 / p1，p2–p4 被各方块类型忽略）；`ucontrol` 各子命令按 `semantic_uses` 算，`flag`/`payTake` 只有一个语义参数；一元 `op` 的第三位永远丢掉（`op rand g 255 b` 的 `b`）。署名和"占位开关"都塞在这里。
- **B 恒真守卫**。`jump T equal X Y` 两边都不是变量赋值时，分支是常量。要么是署名，要么作者想要 `always`。
- **D 死引用**。`scatter1` 这种名字**看着**是有效链接，但处理器的链接表里没有它 —— `LExecutor` 的 `validLink(b)` 直接挡掉，`control shootp scatter1` 一发不发，不报错、不崩溃。`.mlog` 单独文件没有链接表，只有 `.msch` 能查。

真正要改的 A 层长这样：`op mod n n padNeedCount`（模数 0 ⇒ null）、`ubind u` 而 `u` 从未赋过、`control config unloader1 mmm 0 0 0`（`mmm` 当 0 用，但写成了名字）、`flase` 拼错落在 `ulocate` 的 enemy 位。

## 语言事实速查（每条都曾经让我误判）

| 事实 | 源码 | 后果 |
|---|---|---|
| `true`/`false` 是**注册常量**（1 / 0） | `GlobalVars.java:54-55` `putEntry("false", 0)`、`putEntry("true", 1)`，`LAssembler.var()` 先查 `logicVars` 才轮到 `putVar` | `jump T equal X true` 就是 `X == 1`，**不是**未赋值变量 |
| `lookup` 的结果在**第 2 参** | `LStatements.java:875-909`，第 0 位是 `ContentType` 关键字 | 把 `unit` 当目标 ⇒ 每个 `ubind u` 都变假错 |
| `ucontrol getBlock x y a b c` 有**三个输出** | `LExecutor.java:491-509`（p3/p4/p5） | 只认一个输出会把 `b` 当未赋值 |
| `ucontrol within x y r result` | `LExecutor.java:377` `p4.setnum(unit.within(...))` | `r` 是半径，`result` 是 1/0 |
| `equal X null` ⇔ `X.num() == 0` | `ConditionOp.java:31-40` | 对未赋值变量**恒真**；只有 `===` 区分 null 与 0 |
| NaN / ±Infinity 被静默转成 null | `LVar.setnum()` | 这是按位剥离循环的退出机制，也是"不能把 `rand` 建模成 NaN"的原因 |
| `noop` 是 `InvalidStatement` | `LStatements.java:48-59` 的类名就叫 `InvalidStatement`，`build()` 返回空跑的 `NoopI` | 游戏把**解析不了的语句**写成 `noop`。它是**丢失语句的墓碑**：高版本逻辑在低版本打开时丢一条语句，程序往往就此跑不动（丢的正是干活的那条）⇒ 判 **ERR** |
| `//` **不是**注释 | `LParser.java:98-99` 只认 `#` | `set // 上个位置` 是真语句 |
| `jump -1 always` 是 **nop** | `JumpI.run()` 有 `if(address != -1)` | 不是终止，继续往下走；当成终止会误报整片不可达 |
| `jump T always x false` 的 `x`/`false` 是补位 | `LParser` 多 token 惰性丢弃 | 派发表生成器的常见产物，不读 |
| `op add @counter @counter id` 是**派发表** | 下一句就是第 `id` 行 | 静态可达性从此失效，`ir` 会主动抑制不可达报告 |
| `0x`/`0b`/`%rrggbb` 是字面量 | `LAssembler.java:87-99` | 当成变量会误报硬错 |
| `control` 的 p2–p4 各方块忽略 | `LExecutor.ControlI.run()` | 实用有效位只有三个 |
| `ucontrol payTake`/`boost` 只吃布尔 | `LUnitControl.java:17,20` | 未赋值 ⇒ 恒 false，"只捡建筑" |

## 「我以为是作者写错」清单（其实都是检查器的 bug）

这一轮全包审查里，每一条误报都变成了规则，记下来免得下次重犯：

- 十六进制/二进制造型（`%ff0000`、`0b1010`）被当变量 → 硬错 1100 → 883。
- 一元 `op` 的第三位被当读取 → 182 条假警告清零。
- `jump T always x false` 的补位被当变量 → 276 个块凭空多出未定义 `x`。
- 派发表（写 `@counter`）⇒ 不可达 9384 → 495。
- `jump -1 always` 当终止 ⇒ `坦克大战.msch` 190 条里报 182 条不可达，实际全部可达。
- `lookup` 目标位算错 ⇒ `u` 族 23 条假错。
- **只看 `LAssembler.var()` 就断定 `true`/`false` 不是关键字** ⇒ 653 条假 WARN。真相在 `GlobalVars.init()`:它们是 `putEntry` 注册的常量 1 / 0。教训:**判一个名字是不是内建，要查"注册了什么"，不是查"解析函数怎么处理"** —— `var()` 第一步 `logicVars.get()` 就把它们接走了。
- `ucontrol getBlock` 只认一个输出 ⇒ `f` 假错。
- `struct` 层面的教训：**一个分析工具的第一次全量运行，主要产出是它自己的 bug 列表。**先抽样人工核对 20–30 站，再谈精度。

## 校准数字

**910 份真实蓝图 / 617 个文件（2409 个逻辑块）**

- `ir`：**80.9% 的处理器一条都不报**，p50 = 0、p90 = 1；均值 0.829/块是被约 20 个代码生成式蓝图（每个 60–78 条）拉高的。看**干净块占比**，别看均值。
- `values`：2396 块里 4.1% 有信号（常量分支 0.120/块、可证 null 0.060/块），39 ms/块，未收敛 0。
- `pack`：2420 块里只有 **3 块**（0.1%）用了打包，bit peel（`x & -x` + `log2`）**0 块**。

**蓝图包 926 份（481 份有逻辑、1698 块、359,131 条语句）**

- 五层分布见上面那张表：A 77 / B 55 / C 944 / D 788 / E 5540。
- 死存储 `reported` 2156 条 / 232 隐藏；常量分支 `values` 命中 98 块（4.1%）。
- 每块语句数：中位 **41**、p90 **902**、上限 **1000**（正好是 `maxInstructionsPerTick`，说明有人把预算写满）。
- 两批语料要分开算：`⭐不正经的东西⭐` + `🎯逻辑小游戏🎯` 只有 109 份文件却占 **87% 的语句量**（热舞 / 坏苹果 / 香蕉君这类动画演示，自旋是设计意图）。严肃子集 817 文件 / 902 块 / 45,722 语句里，硬错 16.6 条/千语句。

出现率差三个数量级 ⇒ **`ir` 是 linter，`pack` 是"点开就说话"的专用检查**，不能拿同一把尺子量。`pack` 也不是 linter：0.1% 的命中率意味着"报了就是有话说"，但"没报"不代表没打包。

## values 的语言事实（不记住会误判）

- `equal x null` ⇔ `x.num() == 0` —— **对从未赋值的变量恒真**（`LVar` 默认 `numval=0`、`isobj=false`）。只有 `===` 区分 null 与 0。（`ConditionOp.java:31-40`）
- NaN / ±Infinity 在 `LVar.setnum()` 里被**静默转成 null**。这就是 `op logn x 2` 在 `x=0` 时得 `-Infinity` → null、从而成为按位剥离循环退出条件的原因 —— **令牌流里没有任何字面信息说"退出"，只有值域说得清**。
- 所以 `op rand` / `op noise` 的值**不能建模成 NaN**（那会变成"必定是 null"）；本项目里它们一律是 ⊤。

## 边界：这些工具证明不了的事

- **不跨处理器(说明:`read`/`write` 可以按**名字**访问另一个处理器的变量(必須提前聲明、寫給未聲明的槽是靜默空操作)。老蓝图库里看不到这种写法,所以对老库「这个变量从未赋值」的判断是可靠的;新库里它是一条合法的"别处赋值"路径 —— 报 A 层之前先确认两份逻辑是不是同一代产物。)**。别的处理器 `read x cell1 "名字"` 看不见；实测 0 例，但 `ir` 报了死存储仍要自查有没有跨块约定。
- **只判"值有没有人用"，不判"值算得对不对"**。`op add dx dy dx` 想算距离却写成加法，`ir` 不报。
- **外部输入一律 ⊤**。`sensor` / `getlink` / `ulocate` 拿到的都是运行期状态 ⇒ 一半变量退化成未知，`values` 只能对纯计算链说话。
- `values` 3 轮后按变量放宽；`cost` 在 1000 条处截断并显式打 `>=`（那是下界，不是总量）。
- `pack` 只认**同一 `src` 上 ≥2 个不同指数**的 `op idiv`，不重建表达式；`MIN_EXP = 3`。

## 典型流程

1. `report --brief` 看 `VERDICT`，先确定有没有 `check` 报错。
2. 看「先看这里」指向哪层，只展开那一节（`--only ir` 之类）。
3. 展开前对照上面的**校准数字**，判断这一层的命中率是"正常噪声"还是"确实该看"。`ir` 报 1 条是常态，报 60 条要看生成方式。
4. 需要逐条证据时用 `--all` / `--trace VAR`，或退回单项工具拿更细的输出。

单项工具仍然可用（同一份 `tools/` 里）：`mlog.py check|ir|values|pack|explain|cmd|id|item|parse|gen`。`explain` 是查**某条指令哪个参数是输出**的唯一权威来源 —— 官方文档有 8 条指令的参数顺序是错的，`explain` 会直接打 `!! DOCS WRONG`。

## 维护

这个技能的 `tools/` 是从 `mindustry-blueprint/tools/` **整份拷过来的副本**，不是链接 —— 目的就是让目录能被单独拷走。改了任何模块之后在仓库里跑：

```
python mindustry-blueprint/tools/sync_mlogagent.py          # 重新拷贝 + 重写 MANIFEST.sha256
python mindustry-blueprint/tools/sync_mlogagent.py --check  # 只比对，过期时 exit 1
```

本目录的 `SKILL.md` **不参与同步**（它只属于这个技能；蓝图技能有自己的一份）。两份工具不一致时 `mlogagent.py info --verify` 会报 `MISMATCH` 并指出是哪几个文件。
