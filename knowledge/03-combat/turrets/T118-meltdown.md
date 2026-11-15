---
tokens: 598
id: COMBAT.TURRET.118
title: meltdown —— 936 点秒伤的熔断激光
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4315"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/meltdown"
  - "jar:v160.7#blocks/meltdown"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, meltdown, 近程持续激光 / 高耗电清场]
---

## 一句话

meltdown 是后期近防的另一种答案：连续激光每 5 tick 结算 78 点，瞬时 936 DPS，持续 230 tick 后进入 90 tick 的冷却，平均下来 672.75。它把 1020/s 的电换成一整条被烧穿的地面/空中走廊，代价是它几乎必须贴着敌人放，且断电即失效。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：S ｜ **岗位**：近程持续激光 / 高耗电清场
- **射击模式**：连续激光（shootDuration 230）（每触发 1 发；reload 90 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- ContinuousTurret + ContinuousLaserBulletType：每 damageInterval 5 tick 结算 78 点 ⇒ 瞬时 936 DPS [src: 00-data/turrets.json]
- shootDuration 230 tick 后停火，reload 90 tick：按 936 × 230/(230+90) 算平均 672.75 DPS [src: 00-data/turrets.json]
- 1020/s 的耗电是全作最高，必须有独立电网 + 电池组 [src: 00-data/turrets.json]
- 射界 195 世界单位（24.375 格），空陆都打，是少数能同时清地空的近程塔 [src: 00-data/turrets.json]
- **优点**：
  - 瞬时 936 DPS，是全作纸面最高的持续输出，且空陆通吃 [src: 00-data/turrets.json]
  - 平均 672.75 DPS 仍高于 spectre 的 685.7 之下一点点，却只需要 2500 件 [src: 00-data/turrets.json]
  - 光束无弹道飞行时间，命中即结算，对高机动目标没有提前量问题
- **缺点**：
  - 1020/s 的耗电：电网一崩它立刻变砖，是全作对电最敏感的塔 [src: 00-data/turrets.json]
  - 必须贴到 24.375 格内，敌人远程压制时它无法还手 [src: 00-data/turrets.json]
  - 936 是瞬时值，30% 时间是冷却期，规划火力时要用 672.75 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 4 | 00-data/blocks.json |
| 血量 | 3200 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 2500 件（copper × 1200、lead × 350、graphite × 300、silicon × 325、surge-alloy × 325） | 00-data/blocks.json |
| 射程 | 195 世界单位（24.38 格） | 00-data/turrets.json |
| reload | 90 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 1 / 40 | 00-data/turrets.json |
| 耗电 | 1020/s | 00-data/turrets.json |

| 项 | 值 | 说明 | 来源 |
|---|---|---|---|
| 每结算伤害 | 78 | ContinuousLaserBulletType(78) | Mindustry-Source/core/src/mindustry/content/Blocks.java:4316 |
| damageInterval | 5 tick | 每 5 tick 结算一次 ⇒ ×12 | Mindustry-Source/core/src/mindustry/content/Blocks.java:4317 |
| 0甲 DPS | 936 | 78 × 12 | 本文口径 |
| shootDuration | 230 tick | 单次开火持续 | Mindustry-Source/core/src/mindustry/content/Blocks.java:4325 |
| 耗电 | 1020/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:4321 |

- 连续型：目标在射界内就一直结算，不需要命中判定，所以数字极稳。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4315]
- 附 melting 状态与 incendChance 0.4；冷却液消耗 0.5/s 属同级偏高。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4315]

- 本库同时给两个数字：瞬时 936（936 = 78 × 12，12 = 60/5）与平均 672.75（含 90 tick 冷却），比较时必须说清用哪个 [src: 00-data/turrets.json]
- 672.75 的推导可在源码核对：Blocks.java:4323 reload=90f、:4325 shootDuration=230f、:4331 ContinuousLaserBulletType(78) [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4315 —— 定义行 new LaserTurret("meltdown")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=meltdown —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 936 去和 spectre 的 685.7 比较，忽略 90 tick 冷却会高估 39%；复现：按 936 × 230/320 = 672.75 复算 [src: 00-data/turrets.json]
- 反例：以为 meltdown 是远程塔，195 世界单位（24.375 格）比 spectre 的 260 还短；复现：00-data/turrets.json 里两者 range 字段 [src: 00-data/turrets.json]

## 常见误解

- 「936 就是它每秒钟的伤害」只对前 230 tick 成立，长期平均要按 672.75 算 [src: 00-data/turrets.json]
- 「激光塔不耗电」错：1020/s 是全作最高档，它是最依赖电网的塔 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.105]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
