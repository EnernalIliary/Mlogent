---
id: PATTERN.COUNTER.001
title: "@counter 高级架构与 name 打表：派发、收缩、建筑变量表"
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41,119,143-156,604-609,910-921,1247-1263"
  - "Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:228-236"
  - "Mindustry-Source/core/src/mindustry/logic/LAssembler.java:139-149"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:45,48,607-636,644-650"
  - "Mindustry-Source/core/src/mindustry/entities/comp/UnitComp.java:316-328"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6872-6881"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16"
data: []
depends: [PATTERN.MULTI.001, PATTERN.ARCH.001, PATTERN.PERF.001, EXEC.MEM.001]
tags: [@counter, 派发, 定长槽, 建筑变量, name 打表, 单位多控, 架构]
tokens: 1609
---

## 一句话

@counter 是 mlog 里唯一能「算出下一条地址」的原语：把每个处理对象的体做成**定长槽**、只算一次偏移就能从槽 N 落到槽 1，一圈 = `3 + N x stride + 1` 条；而建筑变量空间（`read`/`write @this <名字>`）是唯一能装**对象**的表，用运行时能算出的字符串（单位类型名）当行键，就能在不写死任何类型字面量的情况下遍历单位 —— 它换来的是可维护性，不是更高的上限。

## 规则 / 公式

### 一、定长槽派发

```text
一圈条数      = 3 + N x stride + 1        (3 = 热入口/守卫，1 = 循环尾)
单对象周期(s)  = stride / (60 x ipt)
一圈耗时(s)    = 一圈条数 / (60 x ipt)
```

@counter 在指令 `run()` **之前**自增，执行第 i 条时它恒为 i+1，所以在指令里写 @counter 就是精确设定下一条 [src: LExecutor.java:119]。槽必须**倒序排布**（槽 N 在最前、槽 1 在最后），让指针一路往后走、中途不跳。

推荐**相对派发**（每圈只花 1 条，位移在 init 算一次）：

```mlog
init:  op mul tmp.hp N -stride
       op sub tmp.hp tmp.hp 3        # 表尾 3 条：时间闸门 / 判空守卫 / 本加法
...
uN:    ...                          # 槽 N
...
u1:    ...                          # 槽 1
gate:  jump refill greaterThanEq @time cfg.next
hot:   jump gate strictEqual cfg.item null
       op add @counter @counter tmp.hp
```

**绝对派发**（表长会变时用，例如下面的 live 架构）：

```mlog
init:  set tmp.base @counter
       op add tmp.off tmp.base (4 + slots*stride)
       op mul tmp.p N -stride
hot:   op add @counter tmp.off tmp.p
```

### 二、stride 的账

`stride` 是每槽的固定条数，改任何一条槽内语句都要同步改它：

```text
stride = 12 (ubind / 判空 / 取货 / 投递 / 杂物 基本体)
       + 3  (顺路容器：ulocate storage + 判重 + itemTake)
       + 2  (短路径：拿到货才拐弯的 sensor + jump)
       + 1  (卸空标记 set tmp.needloc 1)
```

### 三、体检段也派发

补员前的「逐槽判活」如果写成每槽一条 `jump ... greaterThan K N` 守卫，N 越大越亏。改成把入口地址算出来 [src: LExecutor.java:119]：

```mlog
chk:   set tmp.cbk @counter
       op mul tmp.p N -2
       op add tmp.cbo tmp.cbk (3 + 2*n)
       op add @counter tmp.cbo tmp.p
```

chk 降序排列、每槽 2 条（`sensor tmp.c @controller` + 空则跳 fill），省掉 N 条守卫。

### 四、表长 = 存活数（live 架构）

固定槽表的浪费在空槽。让 L = 实际占用槽数，热入口改成 `op mul tmp.p L -stride`，死亡就收缩：

```text
收缩段（每槽 4 条，降序 shN..sh1）
shK:  jump sh(K-1) notEqual L K        # L != K，本级和我无关
      sensor tmp.c uK @controller      # 活着且归我？
      jump sh(K-1) equal tmp.c @this
      op sub L L 1                     # L 减 1 后正好匹配下一级，一趟连续收缩
```

收缩入口用 `op mul tmp.p L -4` 把 @counter 直接算到第 L 级，只走活着的级、不扫全表。补员要两条守卫：`jump hot greaterThan K N`（用户上限）与 `jump hot lessThan L K-1`（密度：只有 K <= L+1 才补），补上后 `op max L L K`。

### 五、双速环（已弃用，留判据）

快环每对象 2 条（缓存目标坐标、只管航向），慢环每圈只轮 1 个对象做完整判定。看似省，实际被「慢块条数」卡死：

```text
单对象周期(慢环) = (N x stride_slow + 快环条数) / (60 x ipt)
                = (8 x 22 + 23) / 120 ≈ 1.66 s   >   单环全判 1.06 s
```

慢块 22 条已经超过单环架构里一个对象的整块，所以轮判永远追不上全判；只有 N 极小时才可能占优。**结论：单环（一）优先。**

### 六、name 打表（建筑变量空间当表用）

表 = 处理器自己的变量空间，行键 = **运行时能算出的字符串**，行值 = 任意对象（单位、建筑都行）。

```mlog
hot:  set tmp.i 0
row:  lookup unit tmp.ty tmp.i        # i -> 单位类型（内容注册表，非实例）
      sensor tmp.nm tmp.ty @name      # 类型 -> 名字字符串，这就是行键
      read u @this tmp.nm             # 按行键取行值
      jump next strictEqual u null    # 空行：6 条 / 3 tick
      ubind u                         # 拿到对象入口，只绑这一只
      ...
next: op add tmp.i tmp.i 1
      jump row lessThan tmp.i 50
```

写入同理：`write @unit @this tmp.nm`。行键必须在程序里**存在**（被任何语句引用过）才会进变量表 [src: LAssembler.java:139-149]，所以要么 init 里 `set` 一次，要么在末尾用 `draw` 声明：

```mlog
jump hot always
draw triangle dagger mace fortress scepter reign nova   # 不可达，仅声明（一行 6 个键）
```

`read @this <名字>` 的回落顺序：先查程序变量，查不到再当**链接名**找建筑，且名字末位必须是数字，否则 null [src: LogicBlock.java:607-636]。`write @this <名字>` 只在程序变量命中时生效，否则静默丢弃 [src: LogicBlock.java:644-650]。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| micro / logic / hyper 预算 | 2 / 8 / 25 条每 tick | [src: Blocks.java:6849,6856,6867] |
| 语句硬上限 | 1000 条，超出静默截断 | [src: LExecutor.java:41] |
| 单位转移冷却 | 1.5 s（90 tick），take 与 drop 共用 | [src: LogicAI.java:16] |
| 定长槽 stride（搬运体） | 20 条（12 基本 + 3 顺路 + 2 短路径 + 2 卸空判定 + 1 标记） | [实测: mlogc 生成器断言] |
| N=8 一圈（相对派发程序） | 155 条 = 1.29 s | [实测: 静态计算 + itrace] |
| 体检段派发 | 每槽 2 条 + 入口 4 条 | [实测: mlogc --dispatch] |
| live 架构容量 | 29 槽 999 条；30 槽超 1000 | [实测: 生成器统计] |
| memory-cell / memory-bank 容量 | 64 / 512 格 | [src: Blocks.java:6875,6881] |
| 一格能存什么 | 任意对象（v160 有 objectMemory 数组）或数字；越界返回 null | [实测: write @unit cell1 0 读回 Unit] |
| 单位类型注册表 | @unitCount 56，非空名字 49 个 | [实测: probe_names 全表扫描] |
| 行表空行 / 满行 | 6 条（3 tick） / 17 条（8.5 tick） | [实测: 16 行 & 51 行两版 itrace] |
| 50 行 + 5 只满扫 | 静态 6x50+11x5+3 = 358 条 ≈ 179 tick；实测中位 173 tick = 2.88 s | [实测: out/r50.itrace 800 tick] |
| 16 行 + 5 只 | 静态 6x16+11x5+3 = 154 条 ≈ 77 tick；实测中位 71 tick = 1.18 s | [实测: out/r16.itrace 300 tick] |
| 行表的时间预算 | 6R + 11N <= 180（R 行数、N 单位数） | [src: 上式 + LogicAI.java:16] |
| 1000 条能开的空行 | 约 130 行 | [实测: 生成器统计] |

`6R + 11N <= 180` 的由来：空行 6 条、满行增量 11 条，一圈必须小于 1.5 s 的转移冷却（120 条每秒时 1.5 s = 180 条）[src: LogicAI.java:16]。

## 源码锚点

- LExecutor.java:119 —— `instructions[(int)(counter.numval++)].run(this)`：先自增后执行，全部派发公式的依据。
- LExecutor.java:41 —— `maxInstructions = 1000`，装载与编辑器都按它截断。
- LExecutor.java:143-156 —— `optionalVar`：按名字在 `vars` 里找，找不到返回 null；@this 的读写都以此判定「名字是不是程序变量」。
- LExecutor.java:604-609 —— getlink 第二参是 0 基下标，返回 `exec.links[address]`；这也是 `read @this <数字>` 的语义。
- LExecutor.java:910-921 —— DrawI 的 6 个参数都是 LVar：`draw` 的每个名字都被当作变量，所以它同时是声明语句。
- LExecutor.java:1247-1263 —— LookupI：`dest.setobj(logicVars.lookupContent(type, from.numi()))`。
- GlobalVars.java:228-236 —— `lookupContent`：按内容注册表下标取值，越界或空位返回 null；team 单独处理。
- LAssembler.java:139-149 —— `putVar`：任何被语句引用过的名字都会进变量表，默认是 null 对象。
- LogicBlock.java:607-636 —— 读 @this：先 `optionalVar`，null 才走 `optionalLink`（名字末位必须是数字）。
- LogicBlock.java:644-650 —— 写 @this：`optionalVar` 为 null 或常量就 return，静默丢弃。
- UnitComp.java:316-328 —— senseObject：`type` 有、`name` 只有玩家控制才返回名字、`controller` 三态；**没有 id 分支**，落到 `default -> noSensed`。
- Blocks.java:6875,6881 —— memory-cell 64 格、memory-bank 512 格 [src: Blocks.java:6875,6881]。

## 实测与反例

**实测 1（派发探针）**：每槽入口插 `set dbg.sK 1`，N=1 / 8 / 30 分别只置位 1 / 8 / 30 个；`set N 40` 被 `op min N N 31` 夹到 31 槽 [实测: mlogsim 900 tick]。

**实测 2（live 收缩）**：数字形式的 trace 显示 `96 jump 100 notEqual L 8` -> `97 sensor u8` -> `99 op sub`（L=7）-> `100 守卫` -> `101 sensor u7` -> `103 op sub`（L=6）…… 一趟连续收缩，8 只单位最终 L=8 [实测: out/probe_w.mlog 80 tick]。

**实测 3（行表）**：50 行表 + 6 只 poly，5 行被填（dagger/mace/fortress/scepter/reign = Unit#212..#216），sx=59、st=核心，整圈中位 173 tick（2.88 s）；同一份代码把行数降到 16，整圈中位 71 tick（1.18 s）[实测: mlogsim v160.7, 800/300 tick]。

**反例 1（相对派发放表头）**：两条 op 若紧贴槽表开头，执行到加法时 @counter = 表首 A，`+N*stride` 落到槽 `slots-N`，实际跑的是 `slots-N` 个槽（slots=N 时直接越出表外）。必须放表尾。

**反例 2（位移变量复用）**：体检段每轮把 `tmp.p` 写成 `-2N`，热派发若也读它，N=8 时入口歪到槽中间，30 个探针全空。热派发要用专用变量（如 `tmp.hp`）。

**反例 3（单位实例取 @name / @id）**：两个都是 null。`@name` 只在被玩家控制时返回玩家名 [src: UnitComp.java:317]，`@id` 根本没有分支；必须先 `sensor ty @unit @type` 再 `sensor nm ty @name`。

**反例 4（行键没声明）**：既不 `set` 也不 `draw` 的名字，`write` 静默丢弃、`read` 恒 null；更隐蔽的是 `read @this <名字>` 会退化成按链接名找建筑，名字末位不是数字才返回 null，是数字的话可能读到一个完全不相干的建筑。

**反例 5（末尾声明放在签名之后）**：aigenerated 的 id 哈希覆盖除签名语句外的全部语句，draw 追加在签名行之后会让 `verify` 报 body changed；正确顺序是 `strip`（原地去签名）-> `post`（重签），且 draw 必须在签名槽之前。

**反例 6（live 架构 L 从 0 起手）**：`op mul tmp.p L -stride` 在 L=0 时把 @counter 打到入口前的 gate 上空转，必须 `set L 1` 起手并 `op max L L 1` 兜底。

**反例 7（指望行表提高上限）**：行表不改变时间预算 `6R + 11N <= 180`，R=N 时只能挂 10 只；它换的是「换兵种不用重编译、行名可读、可稀疏裁剪」。

## 常见误解

1. 「lookup 能按实例 id 找建筑/单位」—— 不能。它按**内容注册表**下标取，实例唯一可寻址键是 `getlink` 的下标。
2. 「@counter 可以直接写表达式」—— 只能被赋值成一条算术结果，先算到变量再 `op add @counter <var> <var>`。
3. 「draw 只是绘制」—— 它同时是变量声明，参数就是变量；但语句可达时会被执行（画图形、耗指令），声明应放在不可达处。
4. 「@this 的名字必须是字面量」—— 运行时字符串变量也行（`read u @this tmp.nm`），只有程序里不存在的名字才退化成链接名。
5. 「越多槽越好」—— 槽数只受 1000 条限制，吞吐受转移冷却限制；超出后多出来的槽只是排队。

## 相关

- PATTERN.MULTI.001 单位多控（定长槽 + @controller 三态 + 搬运闭环，本文的落地形态）
- PATTERN.ARCH.001 架构总览（预算来源与拆核）
- PATTERN.PERF.001 性能与鲁棒性（降频、轮转、判活）
- EXEC.MEM.001 变量与内存边界（变量空间、内存格、对象存储）
- MLOG.FLOW.001 控制流（jump 语义与 @counter）
- MLOG.DRAW.001 绘制与文本（draw 的参数即变量）
