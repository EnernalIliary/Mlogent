---
id: PATTERN.TARGET.001
title: 雷达与索敌：filter/sort/order 的组合与射程判定
domain: pattern
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:761-763"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:18"
  - "mindustry-blueprint/PATTERNS.md:1250-1323,936-960,2027-2043"
data: []
depends: [PATTERN.COMM.001]
tags: [雷达, 索敌, 集火, 射程, uradar, 目标]
tokens: 532
---

## 一句话

radar 一条指令就完成「筛选 + 排序 + 取第一个」，因此索敌的正确写法是「用 filter 把不可能的目标排除掉、用 sort 决定优先级、用 order 定方向」，而不是把所有单位拉进数组自己排序；代价是雷达结果有 30 tick 的缓存窗口，射程必须自己再判一次。

## 规则 / 公式

指令签名（7 个参数）：

```text
radar <target1> <target2> <target3> <sort> <order> <source> <output>
```

- target1/2/3：三个过滤条件，逻辑与（AND），可填 any 表示不过滤；常用 enemy、ally、player、attacker、flying、ground、boss、spawn。
- sort：distance、health、shield、armor、maxHealth。
- order：1 = 由近到远（取最近），0 = 由远到近。这是最容易记反的一个参数。
- source：雷达来源建筑（炮塔/单位/处理器链接的雷达），必须自身可被雷达扫描；输出 output 是单个目标引用，不是数组。

多条过滤组合的语义要按「排除法」用：先想清楚不想要什么（flying 不打、player 不打），再写 filter，比逐个枚举想要的目标可靠。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| 雷达结果刷新窗口 | 30 tick = 0.5 s | LExecutor.java:761-763（注释：fixed 30 tick interval） |
| 逻辑控单位超时 | 600 帧 = 10 s | LogicAI.java:18 logicControlTimeout = 60f*10f |
| radar 参数个数 | 7 | mindustry-blueprint/PATTERNS.md:1250-1284 |

注意：mindustry-blueprint/PATTERNS.md:1300 附近写的是「radar/uradar 结果缓存 40 tick」，与源码 LExecutor.java:761 的 30 tick 不一致 —— 以源码 30 tick 为准（见「常见误解」）。

## 源码锚点

- LExecutor.java:761 注释 `//timers update on a fixed 30 tick interval`；:763 `timer.get(30f)` —— sensor/radar 类结果的刷新判据。
- LogicAI.java:18 `logicControlTimeout = 60f * 10f`；:22 `controlTimer = logicControlTimeout` —— 只要不断刷控制，单位就归逻辑控。

## 实测与反例

标准索敌骨架（可直接粘贴，射程自判）：

```mlog
# 需要：处理器已链接炮塔 tower1（或直接用链接的雷达建筑）
radar enemy any any distance tower1 1 target
jump 无目标 equal target null
sensor tx target x
sensor ty target y
sensor px tower1 x
sensor py tower1 y
op sub dx tx px
op sub dy ty py
op len d dx dy
jump 无目标 greaterThan d 40     # 40 格射程，按实际方块改
control shoot tower1 target 1
end
无目标:
control shoot tower1 0 0
end
```

**反例（把缓存当实时）**：雷达结果 30 tick 才重算一次，目标在 0.5 s 内移动/死亡，读到的是旧引用。必须先判 null 再用，且对「目标已死」做兜底（ucontrol 对已死目标无效果，见 PATTERN.PERF.001）。

**反例（uradar 掉控）**：uradar 不刷新 controlTimer，连续使用超过 10 s（600 帧）单位会脱离逻辑控回到 AI。修法：每轮插入一条会刷新控制时长的指令（如 ucontrol 的任意动作），或周期性重绑。

**反例（假距离）**：用 dx + dy 当距离（PATTERNS.md:2027-2043 列为高频 bug）会把方形等距线当圆，导致斜角方向提前开火或漏打；必须 op len。

## 常见误解

1. 「order 1 是取最远」—— 错，1 = 最近。
2. 「target3 是可选参数」—— 形态上可填 any，但 7 个参数一个都不能少。
3. 「ground 表示地面单位」—— 是「已着陆」，飞行单位着陆时也会被选中。
4. 「radar 能返回多个目标」—— 只返回 1 个；要多目标必须多次调用并换 sort 或换 source。

## 相关

- PATTERN.COMM.001 通信与总线（多核分工索敌）
- PATTERN.PERF.001 失效检测与自恢复
- COMBAT.TURRET.001 炮塔控制
- 08-evidence/idioms.json: 本文 idiom 条目的原始出处（30 条，含 src/ver）
