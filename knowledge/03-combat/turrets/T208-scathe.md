---
tokens: 572
id: COMBAT.TURRET.208
title: scathe —— 1350 世界单位、十秒一发的导弹架
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5212"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/scathe"
  - "jar:v160.7#blocks/scathe"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, scathe, 跨屏导弹 / 战略打击]
---

## 一句话

scathe 不是炮，是发射架：塔的弹体 BulletType(0,0) 只负责 spawnUnit，真伤害在导弹武器的 1000 溅射上，所以按塔面板算 DPS 会得到 0。它解决「打到屏幕外」——1350 世界单位（168.75 格）覆盖，10 秒一发、一匣 3 发；代价是 1650 件、只打地面，以及 30 秒的空窗风险。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5218]

## 规则 / 公式

- **层位**：A ｜ **岗位**：跨屏导弹 / 战略打击
- **射击模式**：发射 MissileUnitType 导弹单位（每触发 1 发；reload 600 tick） [src: 00-data/turret_shots.json]
- **目标层**：地面、建筑
- 塔的 shootType 是 BulletType(0,0) + spawnUnit 导弹单位：塔 0 伤害，真伤害在导弹武器溅射 1000 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5218]
- reload 600 tick ⇒ 10 秒一发；maxAmmo 45 / ammoPerShot 15 ⇒ 一匣 3 发 [src: 00-data/turrets.json]
- 1350 世界单位（168.75 格）是全作最远，属于跨屏战略武器 [src: 00-data/turrets.json]
- 只打地面（air False）；三种弹药 phase-fabric / surge-alloy / carbide 的 rm 0.80 / 0.90 / 1.00 只改装填节奏，不改伤害 [src: 00-data/turrets.json]
- 溅射 1000 对 22 甲剩 978（98%），几乎不吃护甲 [src: 00-data/turrets.json]
- **优点**：
  - 168.75 格覆盖让它在敌人进射界前就打掉对方阵地，是 Erekir 唯一的先手战略 [src: 00-data/turrets.json]
  - 溅射 1000 对 22 甲保留 98%，重甲单位在它面前一样脆 [src: 00-data/turrets.json]
- **缺点**：
  - 1650 件 + 10 秒一发：单塔持续输出低到可忽略，它买的是「一发清一片」 [src: 00-data/turrets.json]
  - 只打地面，空中波次完全沉默 [src: 00-data/turrets.json]
  - 一匣 3 发、ammoPerShot 15，补给断了就是 30 秒空窗 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 4 | 00-data/blocks.json |
| 血量 | 3520 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 1650 件（graphite × 400、silicon × 450、tungsten × 500、oxide × 100、carbide × 200） | 00-data/blocks.json |
| 射程 | 1350 世界单位（168.75 格） | 00-data/turrets.json |
| reload | 600 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 15 / 1 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| phase-fabric | 0 | 0 | 0.80 | 0.12 | 0.0 | 0.0 | 0.38 | 0.0 | 00-data |
| surge-alloy | 0 | 0 | 0.90 | 0.11 | 0.0 | 0.0 | 1.67 | 0.0 | 00-data |
| carbide | 0 | 0 | 1.00 | 0.10 | 0.0 | 0.0 | 1.50 | 0.0 | 00-data |

- 这是导弹发射架而不是炮：伤害由导弹落地结算，所以 DPS 不能按塔的 shootType 算。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5212]
- 射程 1350 世界单位（约 169 格）是全作最远，属于跨屏战略武器。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5212]

- 千万别用塔的直伤 0 去算 DPS：那是 spawnUnit 的占位弹，真伤害在 scathe-missile-weapon1 的溅射 1000 [src: 00-data/bullets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5212 —— 定义行 new ItemTurret("scathe")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5224 —— 含 MissileUnitType
- 00-data/turret_shots.json#id=scathe —— 源码派生记录（含证据行）

## 实测与反例

- 反例：按塔面板算 scathe 的 DPS 会得到 0，从而把它评为最差塔；实际是 1000 溅射 × 3 发/匣 [src: 00-data/bullets.json]
- 反例：拿 scathe 打空中波次，air False 直接 0 输出 [src: 00-data/turrets.json]

## 常见误解

- 「0 伤害 = 废塔」错：塔只是发射架，伤害在弹体上 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5218]
- 「10 秒一发太慢」半错：它的价值是 168.75 格先手与 1000 溅射，不是 DPS [src: 00-data/turrets.json]
- 「换 carbide 伤害更高」错：三种弹药塔伤害都是 0，rm 只改装填速度 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.207]]
- [[COMBAT.TURRET.209]]
