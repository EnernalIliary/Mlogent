---
id: PATTERN.COMM.001
title: 通信与总线：内存信箱、通道编码与读写竞态
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6875,6881,6967"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:300-322"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:761-763"
  - "mindustry-blueprint/PATTERNS.md:457-582,1057-1140,1673-1745"
data: []
depends: [PATTERN.ARCH.001]
tags: [通信, 内存格, 黑板, 竞态, 多核]
tokens: 569
---

## 一句话

跨处理器通信只有两条物理通道 —— 内存建筑（read/write + 数字索引）和处理器变量空间（read/write + 字符串变量名，可存对象引用）；两者都没有锁，协议必须靠「单写者 + 序号」手工实现，不能指望原子性。

## 规则 / 公式

read/write 的地址参数有两种形态，语义完全不同：

| 地址形式 | 目标 | 能存什么 | 容量 |
|---|---|---|---|
| 数字索引 0..N-1 | 内存建筑（cell / bank） | 数字（引用不可依赖） | cell 64 格 / bank 512 格 |
| 字符串名 | 处理器的变量空间（按变量名） | 数字或对象引用 | 受变量数限制 |

三种可用拓扑：

1. 黑板（共享内存）：多写多读，靠手工索引分段避免冲突。
2. 信箱（点对点）：固定索引 = 固定收件人，写者只写自己那格。
3. 变量空间直连：write 单位引用 processor \"slot1\"，分配核把实体引用直接塞进控制核的变量 —— 唯一能跨处理器传实体引用的方式。

无锁下的竞态规则（三条，缺一不可）：

- 一个格子只允许一个写者；多写者必然互相覆盖。
- 读写顺序用序号列判定：写者先写数据、再自增序号；读者比对序号与上次记录，变化才取数据。
- 同一 tick 内写入后立刻读取不保证读到新值（处理器按 @ipt 预算交错执行，且 sensor 有 30 tick 刷新窗口）。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| memory-cell 格数 | 64 | [src: Blocks.java:6875] |
| memory-bank 格数 | 512 | [src: Blocks.java:6881] |
| 大型内存（世界处理器侧） | 512 | [src: Blocks.java:6967] |
| sensor/radar 结果刷新窗口 | 30 tick（0.5 s） | [src: LExecutor.java:761-763] |
| 语料 read 指令用量 | 8052 条 | ../AtomicStates-logic-corpus/idioms.json#unigrams |

## 源码锚点

- Blocks.java:6875/6881 —— memoryCapacity = 64 / 512。
- LogicBlock.java:300-322 —— 蓝图里链接以 (name, dx, dy) 存储，读入时转绝对坐标。
- LExecutor.java:761-763 —— 注释原文 fixed 30 tick interval，timer.get(30f) 决定 sensor/radar 类读取何时重算。

## 实测与反例

语料里真实使用的黑板分段（mindustry-blueprint/PATTERNS.md:1693-1695）：中国象棋.msch 在 bank1 用索引 91 存 shooting、96 存 s.team、99 存 t.team；超车模拟器.msch 在 cell1 用 30 存 dead、9 存 stop-r、6/7 存 run-r/run-l、1/2 存 o1x/o1y。共同点是索引分段且留空档（1/2/6/7/9/20/30/39、91/96/99），不是连续紧排 —— 给后续扩展留位。

**反例（用内存格传引用）**：内存格只能可靠承载数值。把单位/建筑引用写进 cell 再读到另一个处理器，不能当作稳定协议；要传引用改用 write 引用 processor \"变量名\"。

**反例（多写者）**：两个处理器都往 cell1[0] 写自己的状态，读者无法判断这格属于谁，症状是数值随机跳变、偶发卡死。修法：一格一写者，或加写者 ID 列由读者过滤。

## 常见误解

1. 「read/write 地址只能是数字」—— 错，字符串地址访问处理器变量空间，可存对象引用，是分配核/控制核架构的关键。
2. 「内存格是原子的，写完立刻能读」—— 错，无锁无事务，跨核可见性依赖 tick 顺序，必须用序号/双缓冲判新旧。
3. 「链接名是所在位置」—— 错，链接名随建筑变化会重算（getLinkName()），改名后旧代码静默失配。
4. 「@controlled 能判断是哪个处理器在控」—— 错，所有逻辑控制一律返回 1；要判断归属只能比较 @controller 与 @this。

## 相关

- PATTERN.ARCH.001 架构总览（分配核 + 控制核）
- PATTERN.DATA.001 数据结构（索引布局）
- PATTERN.PERF.001 帧差与同步
