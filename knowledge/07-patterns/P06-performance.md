---
id: PATTERN.PERF.001
title: 性能与鲁棒性：预算分配、降频与自恢复
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:560-580,826"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:18"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41,763"
  - "mindustry-blueprint/PATTERNS.md:496-517,777-804,1126-1149,2134-2149"
data: []
depends: [PATTERN.ARCH.001, PATTERN.STATE.001]
tags: [性能, 预算, 降频, 轮转, 鲁棒性, 自恢复]
tokens: 636
---

## 一句话

性能问题在 mlog 里等价于「这一 tick 有多少条语句抢 2/8/25 条预算」：先降频（少跑几 tick）再轮转（每 tick 只碰一小片），最后才拆核；鲁棒性则要求每个外部引用（单位、建筑、目标）在每次使用前判活，并给重试设上限。

## 规则 / 公式

预算分配公式：

```text
单 tick 可用条数 K = ipt * edelta（正常速度下 edelta = 1）
每秒可用条数 = 60 * ipt
需要的轮转周期 T = 语句总数 / ipt   (tick)
```

四条降本手段（按收益排序）：

1. 降频：用 @second / @time 做闸门，把「每 tick 都查」改成「每 N tick 查一次」。
2. 轮转：每 tick 只处理 1 个链接/1 个炮塔，`op mod i i @links` 取索引，多出来的预算留给逻辑。
3. 提前退出：不满足条件时用 end 而不是 jump 绕圈；先判最便宜的条件。
4. 拆核：把索敌、搬运、显示拆到不同处理器，用内存格交换结论（见 PATTERN.COMM.001）。

失效检测三件套：

- 每次使用前判空与判死（null、@dead、@controller 三态）。
- 重试有上限（语料里的死单位重绑用 try <= 3）。
- 自恢复：检测到连续 N 轮无进展就重置状态机到初始态，而不是原地重试。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| micro / logic / hyper 预算 | 2 / 8 / 25 条每 tick（120 / 480 / 1500 条每秒） | Blocks.java:6849/6856/6867 |
| world 预算上限 | setrate 最大 1000 → 60000 条每秒 | [src: Blocks.java:6958] |
| 积压上限 | 5 x ipt | [src: LogicBlock.java:45] |
| 单处理器语句硬上限 | 1000 | [src: LExecutor.java:41] |
| 100 炮塔轮转一圈 | 100 tick 约 1.7 s | mindustry-blueprint/PATTERNS.md:512 |
| 死单位重绑重试上限 | 3 次 | mindustry-blueprint/PATTERNS.md:777-804 |
| 逻辑控单位超时 | 10 s（600 帧） | [src: LogicAI.java:18] |

## 源码锚点

- LogicBlock.java:560-580 —— accumulator 主循环；`wait` 走 yield 分支 break，本 tick 剩余预算作废。
- LogicBlock.java:826 —— `write.s(Mathf.clamp(ipt,1,maxInstructionsPerTick))`，显示值被 clamp 到 40（世界 1000）。
- LExecutor.java:763 —— 30 tick 刷新窗口，说明「不是所有 sensor 都是每 tick 真实读取」。

## 实测与反例

标准「轮转 + 判活」骨架：

```mlog
# 每 tick 只处理一个链接，@links 为链接总数
op mod i i @links
getlink b i
jump 跳过 equal b null
sensor alive b @enabled
jump 跳过 equal alive false
control shoot b target 1
跳过:
op add i i 1
end
```

**反例（每 tick 全量遍历 100 个炮塔）**：2 ipt 的 micro 一圈要 50 tick，实际射速被逻辑拖慢，且卡顿时积压到 5 x ipt 上限后集中爆发。语料里 95 个逻辑块采用轮转（PATTERNS.md:496-517）。

**反例（死循环烧预算）**：`jump 0 equal @unit null` 在没绑单位时是原地死循环，一 tick 打满预算并阻塞同一处理器上所有其它逻辑（PATTERNS.md:2134-2149 列为真实 bug）。规范：所有绑定循环都必须有「找不到就退出」的出口。

**反例（无上限重试）**：死单位重绑不设 try 上限时，一旦没有可绑单位就永远卡在重绑分支；语料用 try <= 3 后放弃并回到待机态。

蓝图重载（conf=U）：处理器方块被覆盖蓝本后，@counter、变量、内存建筑内容是否保留，本库尚未实测，需用「部署 -> 运行到状态 X -> 覆盖同一处理器 -> 读状态」三步实验确认。在验证前，工程写法应假设重载会重置并做一次显式初始化握手（PATTERN.STATE.001 的初始化分支）。

## 常见误解

1. 「wait 只是延时，预算会补回来」—— 错，wait 走 yield，本 tick 剩余预算直接作废，不累积。
2. 「处理器显示 40 ipt 就真跑 40」—— 错，那是 clamp 后的显示上限，实际是建筑配置的 ipt。
3. 「逻辑控住单位后不会再丢」—— 错，10 s 不刷新控制就回 AI（LogicAI.java:18）。
4. 「降频会漏事件」—— 会。降频前先确认状态是「可轮询」而不是「必须捕获」的（后者要用事件式写法或缩短周期）。

## 相关

- PATTERN.ARCH.001 架构总览（预算来源）
- PATTERN.STATE.001 状态机（初始化握手）
- PATTERN.TARGET.001 雷达与索敌（30 tick 缓存）
- 08-evidence/idioms.json: 本文 idiom 条目的原始出处（30 条，含 src/ver）
