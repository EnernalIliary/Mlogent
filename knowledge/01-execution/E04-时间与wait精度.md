---
id: EXEC.TIME.001
title: 时间与 wait 精度：tick、秒与帧差
domain: exec
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1206-1234
  - Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1236-1245
  - Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:564-579
data:
  - 06-mlog/instructions.json#instructions
  - 08-evidence/claims.jsonl#L1-29
  - 08-evidence/claims.jsonl#L1-30
depends: [EXEC.MODEL.001]
tags: [wait, tick, 帧差, 时间, 精度]
tokens: 610
---

# E04 时间与 wait 精度

## 一句话

游戏时钟只有 **tick**（60 tick/s）；`wait` 的参数单位是**秒**，但实际分辨率是 **1 tick** —— 所以 `wait 0.05` 不是 0.05 s 的精确等待，而是「停 3 tick」。 [src: knowledge/VERSION.md:1]

## 规则 / 公式

### 1. WaitI 的三个分支（原文）

```java
// LExecutor.java:1218-1232
if(value.num() <= 0){          // wait 0 / 负数
    exec.yield = true;         //   让出本 tick
    curTime = 0f;              //   不 counter--，下 tick 重试同一条
}else if(curTime >= value.num()){
    curTime = 0f;              //   等待结束，继续下一条
}else{
    exec.counter.numval--;     //   回到自己
    exec.yield = true;
    curTime += Time.delta / 60f;  // 每 tick 累加 1/60 秒 [src: knowledge/VERSION.md:1]
}
```

| 分支 | 条件 | 预算 | 下 tick |
|---|---|---|---|
| 空转让出 | v <= 0 | **不消耗**（yield 在 `accumulator--` 之前 break） | 重试同一条 |
| 等待完成 | curTime >= v | 正常 | 执行下一条 |
| 继续等待 | 其它 | 不消耗 | 重试同一条 |

### 2. 秒 → tick 的换算

每 tick 累加 1/60 ⇒ **停 N tick ⇔ 参数 v ∈ ((N−1)/60, N/60]**，即 `tick 数 = ceil(v × 60)`。

| 写法 | 实际停 | 来源（L1-29 实测） |
|---|---|---|
| `wait 0` | 1 tick（让出） | 见 L1-30 |
| `wait 0.001` / `wait 0.01` / `wait 0.0166` | **1 tick** | 三者行为逐字节相同 |
| `wait 0.02` | 2 tick | 实测 done 首置位 tick = t4 |
| `wait 0.05` | 3 tick | t5 |
| `wait 0.1` | 6 tick | t8 |
| `wait 1` | **60 tick ≈ 1 s** | 源码换算 |

实测口径：探针是 `wait X` 后接 `set done 1`，记录 done 首次置位的 tick（`<scratch>/_wq_*.mlog`，起始 tick 有 2 tick 引导开销）。 [src: knowledge/VERSION.md:1]

### 3. 帧差（Time.delta）

- `Time.delta` 是**本帧游戏时间步长**（tick 单位），正常 60 fps 下 = 1。
- 服务器暂停 / 主循环不调用 `Time.update` 时 delta = 0 ⇒ `curTime` 不增长 ⇒ **wait 永远等不完**（与 L3-06「暂停世界需手动 Time.update 否则炮塔不开火」同源）。
- 低帧率下同一 `wait` 跨的 tick 数变少（因为每 tick 累加 1/60 是常量，而墙钟时间更长）⇒ 逻辑节拍在卡顿时**变慢**。

### 4. stop / end

| 指令 | 行为 | 差异 |
|---|---|---|
| `stop` | `counter--; yield; stop=true` | 停在**本条**，直到外部恢复 |
| `end` | 计数器归 0 | 从第 0 条重来 |
| `wait 0` | yield | 下一条继续（不是停在原地语义） |

### 5. 延迟下限

- 任意两条指令之间最小间隔 = 1 tick（16.7 ms），除非同一 tick 内池子有剩余点。 [src: knowledge/VERSION.md:1]
- 跨处理器同步：同 tick 的执行顺序**未定**（L3-05 待定）⇒ 别用「A 写完 B 立刻读」的无握手假设。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| tick 率 | 60 /s（客户端） | 换算约定 |
| 1 tick | 1/60 s ≈ 16.7 ms | VERSION.md 单位口径 |
| wait 单位 | 秒 | LExecutor.java:1231 |
| wait 分辨率 | 1 tick | L1-29 实测 |
| 累加步长 | Time.delta/60 | LExecutor.java:1231 |

## 源码锚点

| 位置 | 内容 |
|---|---|
| LExecutor.java:1218-1232 | WaitI.run 三分支（上表原样） |
| LExecutor.java:1236-1245 | StopI：counter-- + yield + stop |
| LExecutor.java:1224 | 空转分支重置 curTime（注释：value 可能被别的处理器改） |
| LogicBlock.java:564-579 | yield 在 accumulator-- 之前 break |
| Time.java（引擎） | delta 为单位时间步长，暂停时不 update |

## 实测与反例

- ✅【E】`wait 0.001/0.01/0.0166` 三者行为完全一致（1 tick），`0.02→2`、`0.05→3`、`0.1→6`（L1-29）。 [实测: docs/断言表.md]
- ✅【E】`wait 0` 只 yield、不 `counter--`（L1-30），下次执行仍是本条，且不扣预算。
- 反例（不成立边界）：**「wait 0 能无限循环不卡」不成立**——它每 tick 仍占一条指令的调度机会，且让出后本 tick 剩余池子不会被执行（yield 直接 break）。
- 反例：**「wait 是精确睡眠」不成立**——暂停/低帧率下 curTime 不走，wait 会「睡过头」。
- 【U】多人服务器 tick 率低于 60 时的实际 wait 墙钟时长未实测，需要专用服务器计时实验。

## 常见误解

1. 「wait 1 是 1 tick」——是 **1 秒 = 60 tick**；要 1 tick 写 `wait 0.0166`。
2. 「wait 单位是 tick」（旧手册/部分文档的说法）——源码 `curTime += Time.delta/60f` 与比较值都是秒口径，L1-29 已实测确认。
3. 「wait 0 等于空指令」——它有让出语义，影响同 tick 剩余预算。
4. 「暂停游戏逻辑还在跑」——delta=0 时 wait 与依赖时间的指令全部停滞。

## 相关

- M03 控制流（wait 在循环里的用法）
- M08 性能与限制（延迟与吞吐）
- E01 执行模型与预算
