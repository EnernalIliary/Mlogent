---
id: COMBAT.TURRET.002
title: 原版炮塔评价——该造哪门、值不值
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "knowledge/03-combat/C10-numbers.md:84-122（DPS(0甲) 与拐点 A*，本文表 1/表 2 的输入）"
  - "knowledge/03-combat/C02-turrets.md:114-147（size / shots / reload / targetAir 原表）"
  - "jar:v160.7#blocks[].requirements → 00-data/blocks.json:1（造价 = 件数之和）"
  - "jar:v160.7#blocks[].raw → 00-data/turrets.json:1（power.usagePerSecond / range）"
data: [00-data/turrets.json, 00-data/blocks.json]
depends: [COMBAT.TURRET.001, COMBAT.NUMBERS.001, COMBAT.ARMOR.001, COMBAT.WAVE.001]
tags: [炮塔, 选型, 性价比, 梯队, 评价]
tokens: 944
---

## 一句话

炮塔不该按面板 DPS 排名，而该按**职责位**排名：每门炮只在特定位置值钱——近程绞肉（scorch/arc/wave）、直射主力（duo→salvo→cyclone→spectre）、远程压制（hail/ripple/titan/scathe）、穿甲专精（lancer/breach/diffuse）、防空位（swarmer/scatter/fuse/disperse/parallax/segment）、激光持续（meltdown/lustre/malign）；剩下的门不是劣化替代，就是只在某个护甲段内才能成立。

## 规则 / 公式

评价一门炮只问四件事，全部落在已有公式上（不重复推导）：

1. **能不能用**：`targetAir / targetGround` 决定打不打得到，`range` 决定覆盖到哪（8 单位 = 1 格）[src: 03-combat/C02-turrets.md:87-101]。目标在射程外时 DPS 等于 0，见 [[UNIT.MOVE.001]]。
2. **打不打穿**：单发实伤 `d = max(D − A, 0.1D)`，拐点 `A* = 0.9D` [src: 03-combat/C10-numbers.md:41-43,122]。目标护甲 ≥ A* 后 DPS 恒为 `射速 × 发数 × 0.1D`，此时加伤害不如加射速/换弹种。
3. **值不值**：`性价比 = DPS / 造价`、`面积效率 = DPS / size²`、`电力效率 = DPS / 耗电`。**造价只在同星球同资源内可比**（Serpulo：铜/铅/石墨/钛/钍/合金；Erekir：铍/钨/氧化物/碳化物），跨星球比件数是伪比较。
4. **能开火多久**：`有效 DPS = DPS(目标护甲) × 可开火占比 g`，g 由射程覆盖、弹药补给、电力稳定度决定。表 1 的 DPS 都是 g = 1 的理想值。

## 数值

### 表 1：13 门主力炮的性价比（DPS(0甲)、A* 取自 [[COMBAT.NUMBERS.001]] 表 3/表 4；造价与耗电见 DATA#blocks.json / DATA#turrets.json）

| 炮塔 | size | 造价(件) | 耗电/s | 射程(格) | DPS(0甲) | DPS/造价 | DPS/格² | 拐点 A* | 打空 |
|---|---|---|---|---|---|---|---|---|---|
| duo | 1 | 35 | 0 | 20.0 | 27.0 | **0.771** | 27.0 | 8.1 | ✔ |
| scorch | 1 | 47 | 0 | 7.5 | 170.0 | **3.617** | **170.0** | 15.3 | ✘ |
| salvo | 2 | 230 | 0 | 23.8 | 31.0 | 0.135 | 7.8 | 13.5 | ✔ |
| cyclone | 3 | 405 | 0 | 25.0 | 36.0 | **0.089** | 4.0 | 5.4 | ✔ |
| swarmer | 2 | 145 | 0 | 30.0 | 70.0 | 0.483 | 17.5 | — | ✔ |
| diffuse | 3 | 600 | 0 | 15.6 | 82.0 | 0.137 | 9.1 | 41.0 | ✔ |
| lancer | 2 | 220 | 360 | 20.6 | 105.0 | 0.477 | 26.2 | **126.0** | ✘ |
| breach | 3 | 425 | 0 | 23.8 | 127.5 | 0.300 | 14.2 | 76.5 | ✔ |
| titan | 4 | 950 | 0 | 48.8 | 152.2 | 0.160 | 9.5 | **315.0** | ✘ |
| spectre | 4 | 1875 | 0 | 32.5 | 428.6 | 0.229 | 26.8 | 45.0 | ✔ |
| smite | 5 | 2200 | 0 | 37.5 | 750.0 | 0.341 | 30.0 | 225.0 | ✔ |
| malign | 5 | 2400 | 2400 | 51.2 | 1200.0 | 0.500 | 48.0 | 63.0 | ✔ |
| meltdown | 4 | 2500 | 1020 | 24.4 | 936.0 | 0.374 | **58.5** | 70.2 | ✔ |

读法：`DPS/造价` 最高的是 **scorch 3.617**，最低的是 **cyclone 0.089**，差 40 倍——但这不代表 scorch 是主力，见反例 1。造价用"件数之和"是为了在**同一星球内**横向比；Erekir 的 breach/titan/smite/malign/diffuse 与 Serpulo 的 spectre/meltdown 不能直接相减。

### 表 2：按目标护甲选型（22 甲列取自 [[COMBAT.NUMBERS.001]] 表 4）

| 目标护甲 | 仍满伤的炮 | 已进保底的炮 | 结论 |
|---|---|---|---|
| 0–5 | 全部 13 门 | — | 谁射程覆盖好造谁 |
| 9 | spectre 351 / lancer 98.2 / breach 114 / titan 148.3 / smite 723 | duo 2.7、scorch 80、salvo 12.4、cyclone 3.6 | duo/salvo/cyclone **必须退役** |
| 13–16 | spectre 317 / lancer 95.2 / breach 108 / titan 146.5 / smite 711 / meltdown 780 | salvo 4.1、cyclone 3.6 | 换 lancer/breach 线 |
| 22 | malign 822.9 / smite 684 / meltdown 672 / spectre 240 / titan 142.6 | duo 2.7、salvo 3.1、cyclone 3.6、scorch 17 | 只留高 A* 的 5–6 门 |

口径：一格里有多门时按"该门在当前护甲下的 DPS"排序，数字都是 `射速 × 发数 × max(D−A, 0.1D)`，可照 [[COMBAT.NUMBERS.001]] 表 4 逐格复算。

### 表 3：防空缺口（不能打空中的 7 门，见 [[COMBAT.TURRET.001]]）

| 不能打空 | 后果 |
|---|---|
| scorch、lancer、arc、hail、ripple、titan、scathe | 只造这些的阵地遇到空军**全程不开火**；必须另配 swarmer/scatter/fuse/disperse/cyclone/salvo/spectre 之一 |

## 源码锚点

本文是新结论，不含新机制；数字链路的锚点全部在既有篇目：

- `world/blocks/defense/turrets/Turret.java:329-331`：`estimateDps() = shots/reload*60 * ammo.estimateDPS()`（表 1 的 DPS 口径来源，见 [[COMBAT.NUMBERS.001]]）。
- `entities/Damage.java:659-661` 与 `Vars.java:133`：`max(D−A, 0.1D)`，拐点 `A* = 0.9D`。
- `content/Blocks.java`：各炮塔的 `requirements`（造价）与 `power.usage`（耗电），由 `jar:v160.7` 反射进 `00-data/blocks.json` / `00-data/turrets.json`。
- `content/Blocks.java:4331,4323,4325`（meltdown）、`:4643`（titan）、`:3466`（hail）：单发 D 的原始赋值，见 [[COMBAT.BULLET.001]]。

## 实测与反例

**反例 1：只看 DPS/造价，会把 scorch 当主力。**
scorch 的 `DPS/造价 = 3.617`、`DPS/格² = 170` 都是全场第一，但它射程只有 7.5 格、`targetAir = 0`、弹药要 pyratite 链。归一化到"能开火占比"后，`g` 在开阔图通常不到 0.3 ⇒ 有效 DPS 掉到 50 以下，还不如两门 duo。**判据：性价比只在"能持续开火的位置"上成立。**

**反例 2：跨星球比造价。**
breach 造价 425、spectre 1875，看着便宜 4.4 倍；但 breach 吃铍/硅、spectre 吃铜/石墨/钍/合金，Erekir 与 Serpulo 的资源不可换算，而且目标护甲 22 时 breach 剩 94.5、spectre 剩 240——贵的反而更耐甲。**跨星球只能比"同职责位的相对强弱"，不能比件数。**

**反例 3：以为 titan 弹夹小就是弱。**
titan 的 `maxAmmo 12 / ammoPerShot 4` ⇒ 每 3 发就要补一次弹（见 [[COMBAT.TURRET.001]] 弹药容量一节），看着是坑；但它的 `A* = 315` 意味着对 22 甲仍打满 142.6 DPS，是全场护甲最不敏感的门之一。**弹夹小影响的是 g（补弹间隙），不是 DPS 上限。**

**正例核对**：对 22 甲，meltdown 每 5 tick 结算 `max(78−22, 7.8) = 56` ⇒ `DPS = 56/5×60 = 672`，与 [[COMBAT.NUMBERS.001]] 表 4 的 672 一致；同一护甲下 cyclone 只剩 3.6，低了 187 倍。

## 常见误解

- ❌ "后期炮塔一定比前期强"。→ duo 的 0.771 DPS/件是全场第二高，开局三台 duo（105 件）压制力胜过攒一台 spectre（1875 件）。
- ❌ "DPS 高就能守"。→ 射程外的 DPS 是 0：scorch 7.5 格 vs titan 48.8 格，同一个阵地里两者根本不在一个战场。
- ❌ "群伤炮打单体也强"。→ cyclone/salvo 的溅射不进单体 DPS（[[COMBAT.NUMBERS.001]] 表 1：hail 面板 44.8 / 单体 20）。
- ❌ "造了炮塔就有防空"。→ 7 门炮 `targetAir = 0`，空军波来了它们不开火，不是"打得慢"。
- ❌ "耗电高的炮一定强"。→ malign 耗 2400/s 换 1200 DPS（0.50 DPS/电），meltdown 耗 1020/s 换 936 DPS（0.92 DPS/电）；电力紧张时后者更划算。

## 相关

- [[COMBAT.TURRET.001]] 28 门炮塔的机制与完整参数表（本文表 1 的 size/shots/射程输入）
- [[COMBAT.NUMBERS.001]] DPS 三式、TTK、护甲曲线（本文表 1/表 2 的数值来源）
- [[COMBAT.ARMOR.001]] 护甲的减法与保底、拐点的推导
- [[COMBAT.WAVE.001]] 波次的兵种构成决定该配哪一类炮
- [[COMBAT.DEFENSE.001]] 墙体/护盾与炮塔的搭配（承伤位与输出位分开）
- [[UNIT.MOVE.001]] 单位速度与射程覆盖（g 的物理来源）
