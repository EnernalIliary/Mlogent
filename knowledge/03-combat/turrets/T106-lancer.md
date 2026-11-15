---
tokens: 580
id: COMBAT.TURRET.106
title: lancer —— 140 直伤的重甲开罐器
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3561"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/lancer"
  - "jar:v160.7#blocks/lancer"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, lancer, 反重甲 / 单发穿透]
---

## 一句话

lancer 是「一发换一个目标」的塔：140 直伤、0.75 发/s，0 甲 105 DPS；但它真正的卖点是 armorMultiplier 4——打 22 甲时目标护甲按 88 扣，单发只剩 52、DPS 掉到 39，仍是全家对重甲最稳的塔之一。代价是 360/s 的持续耗电和极慢的节奏，漏一发就白等 80 tick。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：反重甲 / 单发穿透
- **射击模式**：ShootPattern + firstShotDelay（每触发 1 发；reload 80 tick） [src: 00-data/turret_shots.json]
- **目标层**：地面、建筑
- 每触发 1 发，reload 80 tick（0.75 发/s）；靠电工作，360/s 的耗电比同级炮塔高一个数量级 [src: 00-data/turrets.json]
- armorMultiplier 4：计算伤害时目标护甲 ×4 参与减法，所以它打高甲目标掉得比别的塔慢，但打 0 甲目标也不占便宜 [src: 00-data/turrets.json]
- pierceCap 4 意味着一条激光能串 4 个目标，排成线的敌人会吃满 [src: 00-data/turrets.json]
- buildingDamageMultiplier 0.25：拆建筑只有四分之一伤害，它不是拆迁塔 [src: 00-data/turrets.json]
- **优点**：
  - 对 22 甲仍有 39 DPS，是同阶段对重甲最可靠的单塔 [src: 00-data/turrets.json]
  - 穿 4 个目标，一条线站满时实际输出远超 105 [src: 00-data/turrets.json]
  - 射界 165 世界单位（20.62 格）比 duo 长，能架在二线 [src: 00-data/turrets.json]
- **缺点**：
  - 360/s 的耗电意味着必须有独立电网，前期根本供不起 [src: 00-data/turrets.json]
  - 0.75 发/s 的节奏对高机动目标是灾难，打空一发就是 80 tick 的损失 [src: 00-data/turrets.json]
  - 拆建筑只有 0.25 倍，攻坚时要另配拆迁手段 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 2 | 00-data/blocks.json |
| 血量 | 1120 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 220 件（copper × 60、lead × 70、titanium × 30、silicon × 60） | 00-data/blocks.json |
| 射程 | 165 世界单位（20.62 格） | 00-data/turrets.json |
| reload | 80 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 8 | 00-data/turrets.json |
| 耗电 | 360/s | 00-data/turrets.json |

| 项 | 值 | 说明 | 来源 |
|---|---|---|---|
| 直伤 | 140 | LaserBulletType | Mindustry-Source/core/src/mindustry/content/Blocks.java:3566 |
| armorMultiplier | 4 | 目标护甲 ×4 参与减法 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3567 |
| 发/s | 0.75 | reload 80 tick | Mindustry-Source/core/src/mindustry/content/Blocks.java:3568 |
| 0甲 DPS | 105 | 140 × 0.75 | 本文口径 |
| 耗电 | 360/s | consumePower(6) | Mindustry-Source/core/src/mindustry/content/Blocks.java:3573 |

- 对 22 甲的靶子：有效护甲 22 × 4 = 88，单发只剩 52，DPS 掉到 39。这是全作最吃护甲惩罚的塔。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3561]
- pierceCap 4；buildingDamageMultiplier 0.25（拆建筑只有 1/4）。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3561]

- 105 DPS 只在 0 甲成立；对 22 甲要按 (140 − 22×4) × 0.75 = 39 算，两个数字差 2.7 倍 [src: 00-data/turrets.json]
- pierceCap 4 的收益不进单体 DPS，排线命中时请自行按目标数乘

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3561 —— 定义行 new PowerTurret("lancer")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3565 —— 含 firstShotDelay / 40
- 00-data/turret_shots.json#id=lancer —— 源码派生记录（含证据行）

## 实测与反例

- 反例：拿 lancer 打 0 甲的 crawler 群，105 DPS 只相当于两门 duo 石墨（67.5×2），却要 360/s 电；复现：00-data/turrets.json 里 lancer 的单体 DPS 与 duo 对比 [src: 00-data/turrets.json]
- 反例：以为 lancer 能拆家——buildingDamageMultiplier 0.25 让 140 直伤对建筑只剩 35；复现：gen_turrets.py 的 MANUAL lancer 表 notes [src: 00-data/turrets.json]

## 常见误解

- 「armorMultiplier 4 = 伤害 ×4」错：它是让目标护甲 ×4 再相减，对 0 甲目标毫无加成
- 「lancer 是全能塔」错：慢射速+低拆建伤害，它只擅长打单个高甲目标

## 相关

- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.107]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.105]]
