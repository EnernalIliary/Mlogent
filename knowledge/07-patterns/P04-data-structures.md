---
id: PATTERN.DATA.001
title: 数据结构：数组、队列、环形缓冲与画布的内存布局
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6875,6881"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicDisplay.java:53,118,137"
  - "Mindustry-Source/core/src/mindustry/world/blocks/logic/TileableLogicDisplay.java:35"
  - "mindustry-blueprint/PATTERNS.md:1673-1800"
data: []
depends: [PATTERN.COMM.001]
tags: [数据结构, 数组, 队列, 环形缓冲, 内存布局, 画布]
tokens: 538
---

## 一句话

mlog 没有指针也没有长度，所有数据结构都是「内存建筑的索引 + 手算地址」；因此结构选择的第一标准不是渐近复杂度，而是每次操作要花几条指令（每条指令占 1 ipt 预算），数组 1 条、队列 3 条、环形缓冲 4 条、全画布 4096 条。

## 规则 / 公式

通用代价公式：一次数据结构操作 = 寻址指令 + 传输指令。寻址用 op，传输用 read/write，各 1 条。

| 结构 | 表示 | 单次操作指令数 | 容量上限 | 典型用途 |
|---|---|---:|---|---|
| 数组 | base + i | read/write 1 条（i 已知时） | cell 64 / bank 512 | 查表、坐标缓存 |
| 队列 | head、tail 两个索引 | 3 条（读 head、加、写回） | 受容量限制 | 任务分配、缓冲输入 |
| 栈 | top 一个索引 | 3 条 | 同上 | 递归/回溯模拟 |
| 环形缓冲 | i = (i+1) mod N | 4 条（op mod + 读写） | N 由 mod 常量决定 | 轮转、去重、滑窗 |
| 位图 | 一个数当 32 位组 | 3 条（op and/or + 位移） | 32 位/格 | 布尔集合、开关表 |

内存布局规则：

1. 分段：按语义分块并从高位往低位放（91/96/99），中间留空档。
2. 段基址与段长写成两条 set，所有访问走 base+i，禁止散写魔法索引。
3. 一个内存建筑只服务一件事；跨用途共享先切分再分配。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| memory-cell / memory-bank 容量 | 64 / 512 格 | Blocks.java:6875 / 6881 |
| 显示屏画布尺寸 | 64 x 64（tileable 为 32 x 32） | LogicDisplay.java:53 / TileableLogicDisplay.java:35 |
| 2025 语料中 read 用量 | 8052 条 | ../AtomicStates-logic-corpus/idioms.json#unigrams |
| 像素画蓝图数 / 语句量 | 18 个 / 约 140 万条 | mindustry-blueprint/PATTERNS.md:1774 |
| 单蓝图 draw 峰值 | 126,759 条（intel corei3.msch） | mindustry-blueprint/PATTERNS.md:1786 |

画布成本可算：64x64 = 4096 像素，每像素一条 draw 指令 → 画满一帧 4096 条；hyper-processor 25 ipt 需要 4096/25 = 163.8 tick，即 163.8/60 = 2.73 s 画一帧。

## 源码锚点

- Blocks.java:6875/6881 —— 两种内存建筑容量。
- LogicDisplay.java:53 `displaySize = 64`；:137 `new FrameBuffer(displaySize, displaySize)`；:118 displayWidth/displayHeight 只是别名。
- TileableLogicDisplay.java:35 `displaySize = 32`。

## 实测与反例

**反例（数组越界不报错）**：cell 只有 64 格，索引 64 以上读写静默无效（读到 0、写入丢弃）。表现是「表尾几项永远是 0」，排查时先打印索引范围而不是怀疑逻辑。

**反例（环形缓冲用 if 归零）**：用 jump lessThan i N 分支归零需要 3 条指令且分支长度不等，而 op mod i i N 只要 1 条 —— 语料里 913 条的多单位搬运就是用 mod 做槽位轮转（BLUEPRINT-ANALYSIS.md 多单位搬运拆解）。

**画布特例**：像素画蓝图占全部语料的绝大部分语句（18 个蓝图约 140 万条，PATTERNS.md:1774），它们是数据不是逻辑 —— 统计「逻辑技巧」时必须按 is_art 剔除，否则 draw 会以 1,305,167 次碾压所有真实指令（idioms.json#unigrams）。

## 常见误解

1. 「内存格可以当动态数组用」—— 错，没有长度字段，长度必须自己存一格。
2. 「read 一次就能读到最新值」—— 错，跨处理器存在 tick 交错，必须配序号列。
3. 「显示屏坐标是 0..64」—— 错，draw 的坐标范围是 0..displaySize（64），越界裁剪；tileable 版是 32。
4. 「队列比环形缓冲灵活」—— 在 mlog 里队列要多维护一个 head 索引，环形缓冲的 mod 更便宜。

## 相关

- PATTERN.COMM.001 通信与总线（索引分段与竞态）
- PATTERN.PERF.001 性能与鲁棒性（预算分配）
- MLOG.DRAW.001 绘制指令
