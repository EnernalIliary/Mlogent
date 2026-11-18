---
id: PATTERN.MULTI.001
title: 单位多控：@counter 派发、@controller 判活与搬运闭环
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41,119,186-205,252-279,322-340,352,523,539,604-609"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16,18,59-63,70-72"
  - "Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:190"
  - "Mindustry-Source/core/src/mindustry/Vars.java:125"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6849,6856,6867"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:45,48"
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:964-965"
  - "Mindustry-Source/core/src/mindustry/content/UnitTypes.java:1046-1047"
  - "Mindustry-Source/core/src/mindustry/entities/units/AIController.java:383-408"
data: []
depends: [PATTERN.ARCH.001, PATTERN.STATE.001, PATTERN.PERF.001]
tags: [单位多控, 单处理器, @counter, 派发, 补员, 搬运, 判活, 极限响应]
tokens: 1400
---

## 一句话

单台处理器控 N 个单位时，决定响应速度的不是语句总数而是**每单位每圈几条**：用 @counter 一次算出下一条地址（跳过全部空槽）、用 @controller 三态做判活与原子占位、把补员和建筑定位赶出热循环，一圈就能压到 `3 + N x stride + 1` 条。

## 规则 / 公式

一圈条数与耗时（ipt = 每 tick 指令数）：

```text
一圈条数   = 3 + N x stride + 1        (3 = 热入口，1 = 循环尾门控)
一圈耗时(s) = 一圈条数 / (60 x ipt)
单单位周期(s) = stride / (60 x ipt)
N 的吞吐上限 = 60 x ipt x transferDelay / stride
```

**派发（dispatch）**：@counter 在指令 `run()` **之前**自增，执行第 i 条时 @counter 恒为 i+1，所以指令内写 @counter 就是精确设定下一条 [src: LExecutor.java:119]。

两种写法，推荐**相对派发**（v27 起默认）：

```mlog
# ① 相对：槽表末尾只剩一条加法，tmp.hp 在 init 算一次
init:     op mul tmp.hp N -stride
          op sub tmp.hp tmp.hp 3      # 表尾 3 条：时间闸门 / 物品空守卫 / 本加法
...
gate:     jump refill greaterThanEq @time cfg.next
hot:      jump gate strictEqual cfg.item null
          op add @counter @counter tmp.hp
```

```mlog
# ② 绝对：每圈 2 条 + init 2 条（live 架构用，L 会变）
set tmp.base @counter
op add tmp.off tmp.base (4 + slots*stride)
op mul tmp.p N -stride
op add @counter tmp.off tmp.p
```

槽必须**倒序排布**（槽 N 在最前、槽 1 在最后），让 @counter 从槽 N 一路落到槽 1，中途不跳。N 由 `set N` 决定，配合 `op min N N slots` / `op max N N 1` 夹紧，越界不会落到程序外。

> ⚠ 相对派发的两个坑（实测踩过）：
> ① 那两条 op 必须放在**槽表末尾**。放表头时执行到加法那刻 @counter = 表首 A，`+`N*stride 落到槽 slots-N，跑的是 slots-N 个槽（slots=N 时直接越出表外）——写成 `op mul tmp.p N stride` 加上去看着对，实际是「跳过 N 槽」。
> ② 位移变量不能和别人共用：体检段（chk 派发）每轮把 `tmp.p` 写成 -2N，热派发跟着读到 -16，N=8 时入口歪到槽中间（trace 显示落到 604 而不是 u8 的 457），30 个 dbg 探针一个都没置位。热派发用专用 `tmp.hp`。

**判活三态**（@controller 的返回值即身份）：

| @controller | 含义 | 处置 |
|---|---|---|
| `@this` | 活着且归本处理器 | 直接用 |
| `null` | 单位已死 / 从未占用 | 进补员 |
| 其它对象 | 活着但被别的逻辑抢走 | 下一条 ucontrol 会重写 controller 夺回 [src: LExecutor.java:322-340] |

**补员（refill）**：`ubind <类型>` -> `sensor tmp.c @unit @controller` -> 仅当 `tmp.c == @unit`（自由单位）才收，`set uK @unit` 后紧跟一条任意 ucontrol 打戳。每次 ucontrol 都执行 `la.controller = exec.thisv.building()` [src: LExecutor.java:325]，所以「认领 + 打标」在同一段指令里完成，同 tick 撞车天然原子。补员用 `@time` 门控（`jump hot lessThan @time cfg.next`，稳态 0 额外开销），周期取 2 s，远小于 10 s 掉控超时。

**搬运闭环（单槽 20 条，状态外化型）** 不记账，状态从货舱推导：

```mlog
u8:  ubind u8
     sensor tmp.f @unit @firstItem          # 手里有什么就是什么状态
     jump u8d notEqual tmp.f null           # 有货 -> 投递腿
     ucontrol approach sx sy 6.5            # 空手 -> 去货源
     ulocate building storage 0 0 vx vy tmp.g2 vault   # 顺路容器，此刻离本单位最近
     jump u8k equal vault tmp.lnk           # 容器==投递目标就跳过，防原地倒腾
     ucontrol itemTake vault cfg.item 999
u8k: ucontrol itemTake st cfg.item 999      # 6 格内才生效，远了是 no-op
     sensor tmp.f @unit @firstItem
     jump u8e strictEqual tmp.f null        # 没拿到就别拐弯
u8d: jump u8j notEqual tmp.f cfg.item       # 手里不是该拿的货 -> 杂物腿
     ucontrol approach lx ly 6.5
     ucontrol itemDrop tmp.lnk 999
     sensor tmp.f @unit @firstItem
     jump u8e notEqual tmp.f null           # 没卸掉就留在投递点，别发返回指令
     set tmp.needloc 1                      # 卸空 = 下一个定位时机
     ucontrol approach sx sy 6.5
     jump u8e always
u8j: ucontrol approach cbx cby 6.5
     ucontrol itemDrop cbc 999              # 杂物倒回核心
u8e:
```

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| micro / logic / hyper 预算 | 2 / 8 / 25 条每 tick（120 / 480 / 1500 条每秒） | [src: Blocks.java:6849,6856,6867] |
| 积压上限 | 5 x ipt（maxInstructionScale） | [src: LogicBlock.java:45] |
| 单处理器语句硬上限 | 1000 条，超出被静默截断 | [src: LExecutor.java:41] |
| 显示用 ipt 上限 | 40，特权（世界处理器）专用 | [src: LogicBlock.java:48] |
| 单位转移冷却 | 1.5 s（90 tick），itemTake 与 itemDrop 共用同一计时器 | [src: LogicAI.java:16] |
| 逻辑控掉控超时 | 10 s（600 tick） | [src: LogicAI.java:18] |
| 物品交互距离 | 45 + size x 4 世界单位（1x1 = 49 = 6.1 格，3x3 核心 = 57 = 7.1 格） | [src: LExecutor.java:523,539; Vars.java:125] |
| approach 停机距离 | moveRad - 7 世界单位；6.5 格 -> 52 - 7 = 45（5.6 格） | [src: LogicAI.java:70-72; LExecutor.java:352] |
| @time 单位 | 毫秒（state.tick / 60 x 1000） | [src: GlobalVars.java:190] |
| flare 货舱 / poly 货舱 | 10 / 36（自动公式 max(round(hitSize x 4), 10)） | [src: UnitTypes.java:1047; UnitType.java:964-965] |
| N=8、stride=20 一圈 | 164 条 = 82 tick = 1.37 s（micro） | [实测: 静态计算 + mlogsim itrace] |
| 同一程序 30 槽满载 | 987 条（1000 条上限内） | [实测: check_kb 前的线数统计] |
| micro 上的 N 吞吐上限 | 60 x 2 x 1.5 / 20 = 9 个 | [src: 上式 + LogicAI.java:16] |

## 源码锚点

- LExecutor.java:119 —— `instructions[(int)(counter.numval++)].run(this)`，@counter 先自增后执行，派发公式的全部依据。
- LExecutor.java:186-205 —— ubind：类型分支走每处理器独立的 `exec.binds[type.id]` 环形推进；对象分支只校验同队 + logicControllable；两者都不满足则 `exec.unit.setconst(null)`。空槽绑定不会继承上一个单位。
- LExecutor.java:322-340 —— checkLogicAI：每条 ucontrol 都要求 `unit.isValid() && exec.unit.obj() == unit`，通过就 `la.controller = exec.thisv.building()`。这就是「任何 ucontrol 都能重新盖戳」与「夺回被抢单位」的机制。
- LExecutor.java:252-279 —— ulocate building：只按 flag 取 `Geometry.findClosest`，ore 参数不参与；失败分支只写 outFound=0，**outX/outY 一个字节都不写**。
- LExecutor.java:523 / :539 —— itemDrop / itemTake 都先校验 `unit.within(build, 45 + size*4)`；itemTake 还要求第二参 `instanceof Item`，null 直接 no-op。
- LExecutor.java:604-609 —— getlink 的第二参是**0 基下标**，不是链接名字。
- LogicAI.java:59-63 —— `controlTimer > 0 && controller != null && controller.isValid()` 否则 resetController；刷新靠每条 ucontrol。
- LogicAI.java:70-72 —— approach = `moveTo(moveRad - 7, 7, keepDistance=true)`。
- AIController.java:383-408 —— `length = clamp((dst - circleLength)/smooth, -1, 1)`，`length < -0.5` 时 `vec.rotate(180)`：进到环带内侧会掉头往外飞 [src: AIController.java:390,405-408]。

## 实测与反例

实测（Mindustry v160.7 真实执行器，mlogsim）[实测: 8 只 flare、8 槽程序、200 tick]：u1..u8 全占，sx/sy = 59,59，st = cbc = 核心，@counter 与派发预期一致；itrace 里 `ubind u8` 相邻出现间隔 34~62 tick [实测: itrace 500 tick]，即 164 条只是**满槽上界**，短路径会让它更短。

**反例 1（ulocate 是单位指令，@unit 为空时静默跳过）**：把 `ulocate` 放在 `ubind` 之前，或末尾槽位把 @unit 绑成 null 之后再调 ulocate，前者会让 sx/sy 停在 init 值（常写成 @thisx/@thisy），**全队飞向处理器自己的格子**。N 恰好等于单位数时看不出，N 大于单位数时必现。修法：定位段先 `ubind <类型>` 再判 `@unit != null`，或直接绑一个已知归己的槽位变量。

**反例 2（itemDrop 失败后无条件发返回指令）**：`itemDrop` 只是「尝试」，距离不够或 1.5 s 冷却未到都会静默失败 [src: LogicAI.java:16]，同段里后发的 `approach sx sy` 会立刻覆盖前一条 `approach lx ly`，单位永远到不了投递点。修法：drop 之后立刻读 `@firstItem`，非空就 `jump` 留在投递点。

**反例 3（把 core 当关键字）**：`ucontrol itemDrop core 999` 里的 `core` 不是关键字而是变量名，未定义就是 null -> 永久 no-op。必须先用 `ulocate building core ...` 把建筑对象取到变量里再 drop。

**反例 4（getlink 传名字）**：`getlink tmp.lnk sorter1` 会被 `numi()` 解析成非法下标，返回 null。正确写法是 `getlink tmp.lnk 1`。

**反例 5（补员段每槽补完就 jump hot）**：每次补员突发只补 1 个槽，表永远填不满。补完要落到下一个 fill 标签继续。

**反例 6（末尾没有回到热循环的 jump）**：程序跑完 @counter 归 0，从头重跑 init，把 N、sx/sy、cfg.nloc 全部刷回初始值，表现为单位周期性失去目标。

**反例 7（单位刚 spawn 就 itemTake，第一次必失败）**：`ItemTakeI` 一进来就 `timeoutDone(unit, transferDelay)`，而 `transferDelay = 90 tick` 是以 `Time.time` 为准的；单位刚出生时这个时间戳还没走够，单条 `itemTake` **静默失败**，大约 30–40 tick 之后重试才成功 [实测: 2 只 flare 连核心、逐 tick 记录 @firstItem]。所以搬运段不能「绑上就取」，要么循环重试直到 `@firstItem` 非空，要么把取货段放在热循环里（每圈都会再试一次，天然自愈）。

## 常见误解

1. 「micro 可以用 setrate 提速」—— 不能，setrate 是特权指令，只对世界处理器生效 [src: LogicBlock.java:48]。
2. 「ucontrol 一停就掉控」—— 不是，10 s 内任何 ucontrol（哪怕 payDrop 这种 no-op）都会刷新计时器 [src: LogicAI.java:18,59-63]。
3. 「@controller == @this 说明单位活着」—— 它说明「活着且归我」；死单位和被抢的单位分别是 null 和别的对象，三种情况必须分开处理。
4. 「move 和 approach 等价」—— approach 带 keepDistance，进到 `moveRad - 7 - 3.5` 以内会掉头往外飞 [src: LogicAI.java:70-72; AIController.java:405-408]；需要贴脸就用 move。
5. 「语句越少响应越快」—— 只要一圈 < 1.5 s 转移冷却 [src: LogicAI.java:16]，再少也没有吞吐收益；此时该削减的是「每单位每圈条数」而不是「总条数」。
6. 「ulocate 会按 ore 参数找矿」—— ore 参数在 building 分支里完全不参与，只按 flag 找最近的同队/敌对建筑 [src: LExecutor.java:252-256]。

## 相关

- PATTERN.ARCH.001 架构总览（预算来源与拆核）
- PATTERN.STATE.001 状态机（初始化握手、掉电恢复）
- PATTERN.PERF.001 性能与鲁棒性（降频、轮转、判活的通用做法）
- 04-units/U03 单位 AI 与控制器（@controller 三态的来龙去脉）
- 01-execution/E01 执行模型与预算（ipt、积压、@counter 语义）
