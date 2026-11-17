---
id: PATTERN.CODE.001
title: "成品逻辑代码库：多控搬运、多控挖矿、行表与着陆台调度"
domain: pattern
status: active
ver: [v160.7_rt, v159.3_src]
conf: E
src:
  - "knowledge/07-patterns/code/p09-haul-31slot-v27.mlog:1-988"
  - "knowledge/07-patterns/code/p09-mine-30slot-v3.mlog:1-966"
  - "knowledge/07-patterns/code/p09-haul-8slot-research.mlog:1-313"
  - "knowledge/07-patterns/code/p09-rows-v2.mlog:1-71"
  - "knowledge/07-patterns/code/p09-luozi-v6-micro8.mlog:1-463"
  - "knowledge/07-patterns/code/p09-luozi-v52-micro8.mlog:1-149"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41,119"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16,18"
  - "Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:190"
data: []
depends: [PATTERN.MULTI.001, PATTERN.COUNTER.001, PATTERN.PERF.001, MLOG.UNIT.001]
tags: [成品, 代码示例, 单位多控, 搬运, 挖矿, 着陆台, 定长槽]
tokens: 793
---

## 一句话

六份可直接粘贴进处理器的成品逻辑（多控搬运两版、多控挖矿、name 行表、着陆台调度两版）共用同一套骨架：**定长槽 + 相对派发 + `@controller` 判活 + 2 s 补员突发**；换产品只换槽里的 18~20 条，派发与补员一行不动。

## 规则 / 公式

骨架公式（micro，`ipt` 点/tick）：

```text
一圈条数 = 3 + N x stride          # 3 = 表尾时间闸门 + 位移加法
一圈时间 = 一圈条数 / (60 x ipt)    # micro ipt=2 => 120 条/s
tmp.hp   = -(N x stride + 3)       # init 一次，表尾 op add @counter @counter tmp.hp
```

- 派发位移放**表尾**：`@counter` 在执行第 i 条时已自增到 i+1 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:119]，放表头会落到「槽 slots−N」而不是第 N 槽。
- 槽数 x stride 不得超过 1000 条语句上限 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41]。
- 两条硬闸门夹住 N：单位交互冷却 90 tick（1.5 s）[src: Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16]、逻辑控掉控 600 tick（10 s）[src: Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:18]。搬运受前者约束（N ≤ 9），挖矿只受后者（N 可到槽位上限）。
- 补员周期 2 s，用 `@time`（毫秒）累加，不用 `wait`（`wait` 的单位是**秒**）[src: Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:190]。

热入口（六份成品同形，v27 原文）：

```mlog
jump gate strictEqual cfg.item null
op mul tmp.hp N -19
op add @counter @counter tmp.hp
```

单槽（搬运版，19 条）按「判空手 → 顺路取货 → 取货 → 判到手 → 投递 → 判卸空 → 掉头」排列，`ucontrol` 一律在 `ubind` 之后；挖矿版把投递腿换成 `ucontrol mine ox oy`，并在补员时补一条 `ucontrol boost 1`。

## 数值

| 文件 | 行数 | 槽位 | stride | N=8 一圈 | 产品 | 来源 |
|---|---|---|---|---|---|---|
| `code/p09-haul-31slot-v27.mlog` | 988 | 31 | 19 | 155 条 ≈1.29 s | 单位多控搬运（旗舰） | 本库 code/ |
| `code/p09-mine-30slot-v3.mlog` | 966 | 30 | 18 | 147 条 ≈1.23 s | 多控挖矿 + boost | 本库 code/ |
| `code/p09-haul-8slot-research.mlog` | 313 | 8 | 20 | 164 条上界 | 8 槽研究版 | 本库 code/ |
| `code/p09-rows-v2.mlog` | 71 | 50 行表 | 6/空行 | 见反例 4 | name 打表遍历 | 本库 code/ |
| `code/p09-luozi-v6-micro8.mlog` | 463 | 8 台 | — | 408 条 ≈3.40 s | 着陆台调度（硬编码） | 本库 code/ |
| `code/p09-luozi-v52-micro8.mlog` | 149 | 动态台数 | — | 随台数线性 | 着陆台调度（循环） | 本库 code/ |

行数含头部 `print` 与签名槽；「N=8 一圈」是满槽上界，短路径命中时更短 [实测: knowledge/07-patterns/code/p09-haul-31slot-v27.mlog:1-988]。

## 源码锚点

- `LExecutor.java:41` `maxInstructions = 1000`：超过的语句在载入时被丢弃，不是运行时截断。
- `LExecutor.java:119` `instructions[(int)(counter.numval++)].run(this)`：先自增再执行，所以指令内写 `@counter` 是「设下一条」。
- `LogicAI.java:16` `transferDelay = 60f*1.5f`：`itemTake`/`itemDrop` 共用这个 per-unit 计时器 [src: Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16]。
- `LogicAI.java:18` `logicControlTimeout = 600`：超时 `resetController()`，单位回归游戏 AI。
- `GlobalVars.java:190` `varTime.numval = state.tick / 60.0 * 1000.0`：`@time` 是毫秒 [src: Mindustry-Source/core/src/mindustry/logic/GlobalVars.java:190]。

## 实测与反例

1. **派发放表头 ⇒ 实跑 slots−N 个槽**。两个 `op` 紧贴槽表开头时，`@counter` 已自增，加完落到倒序表第 (slots−N) 槽；只有 slots=2N 才碰巧正确 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:119]。
2. **`itemDrop` 失败后立刻发返回腿 ⇒ 覆盖去程**。`itemDrop` 只是尝试（距离不够或 90 tick 冷却未到就静默失败）[src: Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16]，紧跟一条 `approach sx sy` 会让单位永远飞不到投递点；修法是投递后先 `sensor @firstItem` 判是否卸空，再决定掉头。
3. **挖矿版 `loc` 段用 `ubind u1`**：u1 是补员链末槽，单位数 < N 时恒空 ⇒ `ulocate ore` 整段跳过 ⇒ 矿区坐标永远 null ⇒ 全队不挖矿。
4. **着陆台配额用「累计够了发一台」⇒ 台子发不满**：`npad` 除不尽时 floor 配额之和小于台数，实测 9 台只下发 8 台、第 9 台空置；改成累计取整 `tk = floor(npad x cu / sum)` 后 9 台全部下发 [实测: knowledge/07-patterns/code/p09-luozi-v52-micro8.mlog:1-149]。
5. **搬运旗舰的实测闭环**：8 只 poly、N=8 时 itemTake 55 次 / itemDrop 48 次，槽位全占、核心与投递点都是同一个 `core-shard` 变量 `st`/`cbc` [实测: knowledge/07-patterns/code/p09-haul-31slot-v27.mlog:1-988]。

## 常见误解

- **「槽位多就控得多」**：micro 上搬运一圈 155 条 ≈1.29 s 已贴住 1.5 s 冷却，31 槽只是给 N 留余量；实际一次只能有 ≈9 只单位在有效节拍上 [实测: knowledge/07-patterns/code/p09-haul-31slot-v27.mlog:1-988]。
- **「`core` 是关键字」**：它是变量名，必须先 `ulocate building core ... core` 赋值，否则 `ucontrol itemDrop core 999` 永远空操作。
- **「`sensor x @unit @type` 存的是类型对象」**：存的是**类型内容**（`flare`），对单位实例取 `@name`/`@id` 恒 null，必须经 `@type` 中转。
- **「签名槽可以省」**：末行 `jump N always 0 "aigenerated:…"` 是完整性标记，删掉不影响运行但会让文件无法校验来源；改任何语句都要重新签名。

## 相关

- 架构与判活：[PATTERN.MULTI.001](P07-unit-multicontrol.md)
- 派发与打表：[PATTERN.COUNTER.001](P08-counter-architectures.md)
- 预算与分帧：[PATTERN.PERF.001](P06-performance.md)、[MLOG.PERF.001](../06-mlog/M08-性能与限制.md)
- 单位控制语义：[MLOG.UNIT.001](../06-mlog/M07-单位与逻辑控制.md)
- 代码目录：[code/](code/)
