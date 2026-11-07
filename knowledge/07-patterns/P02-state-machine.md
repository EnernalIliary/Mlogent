---
id: PATTERN.STATE.001
title: 状态机：枚举、转移表与 @counter 分派
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/logic/LParser.java:112-176"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:41"
  - "mindustry-blueprint/PATTERNS.md:313-455"
data: []
depends: [PATTERN.ARCH.001]
tags: [状态机, jump, 标签, counter, 跳转表]
tokens: 591
---

## 一句话

mlog 的状态机只有两种可维护写法：枚举状态 + 一串 jump equal（语句数随状态数线性增长，但可读可改），或 @counter 固定偏移分派（O(1)，但插入一条指令就全错位）。默认选前者，只有 ipt 预算卡死时才用后者。

## 规则 / 公式

标签在导入时被编译成行号（两趟解析）：第一趟扫描「名字:」记录行号且不产生语句，第二趟把 jump 的目标替换成数字。三条推论：

1. 标签不占语句位、不消耗 @ipt —— 它根本不是指令。
2. 从蓝图里解析出来的代码，jump 目标全是数字，标签名已丢失。
3. @counter 可写，因此可以在运行时算下一跳地址。

jump 语义：条件成立 → @counter = 目标；不成立 → @counter += 1。可用条件：equal（1e-6 浮点容差）、notEqual、lessThan(Eq)、greaterThan(Eq)、strictEqual（类型+值严格比较）、always（忽略后两参数）。

### 写法 A：枚举 + 转移表（默认，约 3N 条）

```mlog
# state: 0=待机 1=取货 2=返航
jump 待机 equal state 0
jump 取货 equal state 1
jump 返航 equal state 2
set state 0
end
待机:
set state 1
end
取货:
set state 2
end
返航:
set state 0
end
```

N=10 时约 30 条，micro 处理器 2 ipt 也能在一个 tick 内走完一圈。

### 写法 B：@counter 固定偏移分派（O(1)）

```mlog
# state 属于 [0,N)，每个分支恰好占 1 条语句
op add @counter @counter state      # 执行后 @counter 还会自动 +1
jump 20 always 0 false              # state=0 的落点
jump 24 always 0 false              # state=1 的落点
jump 28 always 0 false              # state=2 的落点
```

两条硬约束：各分支体长度必须严格相等（否则用 op mul 缩放，ILI反病毒.msch 用的是每档占 2 条的写法）；插入/删除任何一条指令都会让全部偏移失效。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| 单处理器语句上限 | 1000 条，超出静默截断 | LExecutor.java:41；PATTERNS.md:295 |
| 标签数量上限 | 500 个（maxJumps） | mindustry-blueprint/PATTERNS.md:307 |
| 未解析标签 | 目标 = -1，jump 不跳，等价 noop | 同上 |
| 语料中 @counter 技巧用量 | 39 处 | mindustry-blueprint/PATTERNS.md:405 |

equal 的容差是 1e-6；对象比较走 Structs.eq，null 与 0 不相等。

## 源码锚点

- LParser.java:112-176 —— 两趟解析：先 jumpLocations.put(label, line)，再回填。
- LExecutor.java:41 `maxInstructions = 1000`。
- LStatements.java —— JumpI 修改 @counter；未知指令落 InvalidStatement，等价 noop。

## 实测与反例

语料里 39 处 @counter 运算集中在三个蓝图（ILIOS.msch、ILI反病毒.msch、ILI集火逻辑.msch），并且没有一个注释（mindustry-blueprint/PATTERNS.md:453）。这不是风格偏好，是「作者自己也读不懂了」的信号。

**反例一（标签踩空）**：标签写在文件最末尾、下面没有任何指令时，行号 = 语句总数，跳过去后 @counter 越界被重置为 0 —— 实际跳回开头，行为不可预测。规范：标签下面至少跟一条指令，分支末尾用 end。

**反例二（把 end 当可有可无）**：直接跑到底与 end 行为相同（越界自动回 0），但 end 是最省 ipt 的关断手段 —— 开关没开时一条 end 直接结束本 tick，比用 jump 绕一圈便宜得多。

## 常见误解

1. 「jump 不成立时 @counter 不变」—— 错，会 +1 落到下一条。
2. 「标签占一条指令位」—— 错，第一趟就被吃掉，不占语句数、不计入 1000 上限。
3. 「equal 和 strictEqual 等价」—— 错。判断「是不是同一个对象」必须用 strictEqual（如 strictEqual c @unit），equal 走数值容差。
4. 「状态机必须用 @counter 才快」—— 错。按 2 ipt 预算，30 条的枚举状态机两 tick 内走完；O(1) 分派只在语句数上千时才有净收益。

## 相关

- PATTERN.ARCH.001 架构总览（预算从哪来）
- PATTERN.PERF.001 性能与鲁棒性（降频、防抖）
- MLOG.FLOW.001 跳转与标签语义
- 08-evidence/idioms.json: 本文 idiom 条目的原始出处（30 条，含 src/ver）
