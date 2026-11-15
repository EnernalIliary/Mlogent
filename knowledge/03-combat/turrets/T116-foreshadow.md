---
tokens: 527
id: COMBAT.TURRET.116
title: foreshadow —— 500 世界单位外的 405 点重锤
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4203"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/foreshadow"
  - "jar:v160.7#blocks/foreshadow"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, foreshadow, 超远程狙击 / 反重甲先手]
---

## 一句话

foreshadow 用 2700 件买一门能打到 500 世界单位（62.5 格）的炮：0.3 发/s、单发 1350 直伤、405 DPS，对 22 甲还有 398.4——护甲几乎不影响它。它是「在敌人进入任何其他塔射界之前就先削掉它」的塔，代价是 600/s 的电、5 件/发的弹药和极慢的节奏。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：超远程狙击 / 反重甲先手
- **射击模式**：ShootPattern(默认)（每触发 1 发；reload 200 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 每触发 1 发，reload 200 tick ⇒ 0.3 发/s；射界 500 世界单位（62.5 格）是全作最远 [src: 00-data/turrets.json]
- surge-alloy 单发 1350 直伤 → 405 DPS，对 22 甲 398.4：一发就够破甲，护甲在它面前几乎不存在 [src: 00-data/turrets.json]
- ammoPerShot 5 + maxAmmo 40：每次开火吃 5 件弹药，弹匣只够 8 发，供弹必须跟上
- 600/s 的耗电是全作最高档之一，没有独立电网根本带不动 [src: 00-data/turrets.json]
- **优点**：
  - 62.5 格射界 + 405 单体 DPS，让它能在其他塔全部沉默的距离上开火 [src: 00-data/turrets.json]
  - 对 22 甲 398.4，是全作对重甲最有效的单塔（lancer 39、fuse 426.9 但射界 11.25 格） [src: 00-data/turrets.json]
  - 一发 1350，对高血量单体目标是效率最高的爆发
- **缺点**：
  - 0.3 发/s：一发打空就损失 3 秒以上，对高机动目标命中率是硬伤 [src: 00-data/turrets.json]
  - 2700 件 + 600/s 电 + 5 件/发，是全家最贵的维持成本 [src: 00-data/turrets.json]
  - 4×4 占地 + 极慢射速，前期完全不可用 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 4 | 00-data/blocks.json |
| 血量 | 2400 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 2700 件（copper × 1000、metaglass × 600、silicon × 600、plastanium × 200、surge-alloy × 300） | 00-data/blocks.json |
| 射程 | 500 世界单位（62.50 格） | 00-data/turrets.json |
| reload | 200 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 0.4 / 2 | 00-data/turrets.json |
| 耗电 | 600/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| surge-alloy | 1350 | 0 | 1.00 | 0.30 | 405.0 | 405.0 | 1.50 | 398.4 | 00-data |

- 398.4 = 0.3 × (1350 − 22)，与 405 只差 1.6%，这是「单发够重时护甲可忽略」的最好例证 [src: 00-data/turrets.json]
- 1.5 件/s = 0.3 发/s × 5 件/发，规划供弹时按这个数字算 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4203 —— 定义行 new ItemTurret("foreshadow")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=foreshadow —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 foreshadow 打 crawler 群，0.3 发/s 一轮只杀一个，性价比远不如 cyclone 的 415.5 面板；复现：00-data/turrets.json 里 foreshadow 与 cyclone 的「面板DPS」列 [src: 00-data/turrets.json]
- 反例：以为它靠溅射清群，1350 是纯直伤、面板=单体，群伤能力为零；复现：同表 foreshadow 行 [src: 00-data/turrets.json]

## 常见误解

- 「射程最远所以最强」错：0.3 发/s 的节奏让它在近身混战里几乎没有输出 [src: 00-data/turrets.json]
- 「高护甲目标打不动」错：对 22 甲仍有 398.4，是全作抗甲最好的塔之一 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.106]]
- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.115]]
