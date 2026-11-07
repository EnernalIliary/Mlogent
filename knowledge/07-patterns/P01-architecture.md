---
id: PATTERN.ARCH.001
title: 蓝图架构总览：预算、分层与拓扑
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:45,48,560-580"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6849,6856,6867,6954,6958"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41"
  - "mindustry-blueprint/PATTERNS.md:114-311"
data: []
depends: []
tags: [架构, 处理器, ipt, 预算, 分层]
tokens: 587
---

## 一句话

单处理器的能力上界是「ipt x edelta」的指令预算（积压不超过 5 x ipt），所以架构问题只有一条主线：先把「状态规模 x 每轮执行次数」压进预算；压不下去才拆处理器 —— 而拆完之后通信开销必然大于计算开销。

## 规则 / 公式

每 tick 实际执行的语句数不是固定值，而是按时间增量累积的预算（LogicBlock.java:560-580）：

```text
accumulator += edelta() * ipt
if (accumulator > 5 * ipt) accumulator = 5 * ipt   // 积压上限
while (accumulator >= 1) { runOnce(); accumulator--; }
```

三条可计算规则：

1. 吞吐：额定条数/秒 = 60 x ipt（1 tick = 1/60 s）。
2. 加速：游戏加速时 edelta() 变大，同一 tick 内跑更多条 —— 逻辑行为随速度改变。
3. 拆核判据：若「语句总数 x 每秒所需轮次」> 60 x ipt，必须拆多处理器。

分层（四层，每层只做一件事）：

| 层 | 载体 | 职责 | 不变量 |
|---|---|---|---|
| 计算层 | 处理器（micro/logic/hyper/world） | 只跑逻辑 | 语句数 <= 1000 |
| 共享层 | memory-cell / memory-bank，或处理器变量空间 | 跨处理器交换状态 | 索引手工分配、不重叠 |
| 人机层 | switch1 + @enabled | 人工启停 | 关断用一条 end，最省 ipt |
| 输出层 | 显示屏 / 消息块 | 只写不读 | drawflush / printflush 提交 |

拓扑只有三种可维护形态：单核单体、分配核 + N 个控制核、世界处理器驱动。点对点互写 @counter、环形多主属于不可维护区间。

## 数值

| 处理器 | 默认 @ipt | 额定条数/秒 | 链接半径 | 尺寸 | 备注 |
|---|---:|---:|---|---|---|
| micro-processor | 2 | 120 | 10 格 | 1x1 | 最省，适合小状态机 |
| logic-processor | 8 | 480 | 22 格 | 2x2 | 中量搬运/兵控 |
| hyper-processor | 25 | 1500 | 42 格 | 3x3 | 需冷却液，扛计算量 |
| world-processor | 8 | 480（setrate 到 1000 则 60000） | 全图 | 1x1 | 特权：建造/规则/跨队 |

@ipt 已对源码复核（Blocks.java:6849/6856/6867/6954）；链接半径与尺寸取自 mindustry-blueprint/PATTERNS.md:139-142，该表未标源码行，属二手数据 —— 故 @ipt 记 conf=S，半径记 conf=I。

## 源码锚点

- LogicBlock.java:45 `maxInstructionScale = 5` —— 积压上限倍数。
- LogicBlock.java:48 `maxInstructionsPerTick = 40` —— 默认上限，只有世界处理器被抬高。
- LogicBlock.java:560-580 —— 预算累积/裁剪/消费主循环；wait 在此 break。
- Blocks.java:6958 `worldProcessor.maxInstructionsPerTick = 1000`。
- LExecutor.java:41 `maxInstructions = 1000` —— 单处理器语句硬上限。

## 实测与反例

真实语料（../AtomicStates-logic-corpus/index.json：430 个蓝图、5774 个逻辑块、3,719,102 条语句）的处理器分布：

| 处理器 | 逻辑块数 | 占比 |
|---|---:|---:|
| micro-processor | 4823 | 83.5% |
| world-processor | 545 | 9.4% |
| logic-processor | 352 | 6.1% |
| hyper-processor | 54 | 0.9% |

剔除纯像素画后剩 1081 个真实逻辑块（mindustry-blueprint/PATTERNS.md:1933 记载的同一轮扫描口径）。也就是说：83.5% 的逻辑块跑在只有 2 ipt 的 micro 上 —— 架构第一目标不是算得快，而是每 tick 只算一点。

**反例（预算算错）**：micro-processor（2 ipt）链接 100 个炮塔、每 tick 全量遍历，需要 100 条/tick 而预算只有 2 条/tick，一圈要 50 tick。修法是轮转链接（每 tick 只碰 1 个，100 tick 一圈约 1.7 s），见 PATTERN.PERF.001。

## 常见误解

1. 「@ipt 是每帧固定条数」—— 错，它是每 tick 预算，按 edelta() 缩放；卡顿后一次最多补 5 个 tick 的量。
2. 「setrate 什么处理器都能用」—— 错，setrate 是特权指令，只有世界处理器生效且被 clamp(v,1,1000)。
3. 「1000 条只是建议」—— 错，解析到 1000 就停，超出部分静默丢弃、不报错。
4. 「拆处理器一定更快」—— 错，跨核只能靠 read/write（每值一条指令 + 同步延迟），且 @controlled 无法区分是哪个处理器在控（见 PATTERN.COMM.001）。

## 相关

- PATTERN.STATE.001 状态机（@counter 分派）
- PATTERN.COMM.001 通信与总线
- PATTERN.PERF.001 性能与鲁棒性
- EXEC.MODEL.001 执行模型
- 08-evidence/idioms.json: 本文 idiom 条目的原始出处（30 条，含 src/ver）
