---
tokens: 610
id: COMBAT.TURRET.201
title: breach —— 325 单发、全场最密的开局炮
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4351"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/breach"
  - "jar:v160.7#blocks/breach"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, breach, 开局主力 / 高单发速射]
---

## 一句话

breach 解决的是「Erekir 第一波怎么活」，不是「后期怎么打」：425 件、3×3 占地，carbide 把 reload 40 tick 乘 0.20 压到 8 tick，7.5 发/s × 325 直伤就是 2437.5 单体 DPS，对 22 甲还剩 2272.5（93%）。代价有两处：190 世界单位（23.75 格）的短射界，以及 carbide 7.5 件/s 的吞吐——单条带子供不起，断料就掉回 1.5 发/s 的 tungsten 曲线。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：B ｜ **岗位**：开局主力 / 高单发速射
- **射击模式**：ShootPattern(默认)（每触发 1 发；reload 40 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- carbide 的 reload 40 tick 被 rm 0.20 压到 8 tick：7.5 发/s × 325 直伤 = 2437.5 单体 DPS，对 22 甲 2272.5 [src: 00-data/turrets.json]
- 三种弹药是两条曲线：carbide 走高频（7.5 发/s、7.5 件/s），tungsten 与 beryllium 都是 1.5 发/s 的慢速线 [src: 00-data/turrets.json]
- 无溅射，面板 DPS 与单体 DPS 同值，0.75 折算对它不成立 [src: 00-data/turrets.json]
- 空陆通吃（air True / ground True），425 件、3×3、建造 540 tick，是 Erekir 最早补上的火力点 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4351]
- coolantMult 15 是 Erekir 高档冷却，但 3×3 塔位通常先缺料缺电，冷却不是第一瓶颈 [src: 00-data/turrets.json]
- **优点**：
  - 425 件买到 2437.5 DPS，是同价位没有第二台的数值密度：950 件的 titan 单体只有 285.3 [src: 00-data/turrets.json]
  - 对 22 甲保留 93%，是 Erekir 少数「换不换弹药都能打重甲」的塔 [src: 00-data/turrets.json]
  - 空陆通吃且 3×3，任何阵型缝隙都能塞，开局不用为它改布局 [src: 00-data/turrets.json]
- **缺点**：
  - 190 世界单位（23.75 格）太短，中期以后敌人远程火力站在射界外就能磨它 [src: 00-data/turrets.json]
  - carbide 7.5 件/s 是全场最高吞吐之一，供给一断就退回 tungsten 的 106.9 DPS [src: 00-data/turrets.json]
  - beryllium 最省料但最弱：95.6 DPS、DPS/物品 31.9 是三种弹药最低 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 3 | 00-data/blocks.json |
| 血量 | 1620 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 425 件（graphite × 125、silicon × 150、beryllium × 150） | 00-data/blocks.json |
| 射程 | 190 世界单位（23.75 格） | 00-data/turrets.json |
| reload | 40 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 15 / 3 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| carbide | 325 | 0 | 0.20 | 7.50 | 2437.5 | 2437.5 | 7.50 | 2272.5 | 00-data |
| tungsten | 71.25 | 0 | 1.00 | 1.50 | 106.9 | 106.9 | 1.50 | 73.9 | 00-data |
| beryllium | 63.75 | 0 | 1.00 | 1.50 | 95.6 | 95.6 | 3.00 | 62.6 | 00-data |

- 别把 reload 40 tick 当射速：carbide 曲线实际 8 tick 一发，40 tick 是表里的基座值 [src: 00-data/turrets.json]
- maxAmmo 30 ÷ 7.5 件/s ≈ 4 秒，弹匣是缓冲不是续航 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4351 —— 定义行 new ItemTurret("breach")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=breach —— 源码派生记录（含证据行）

## 实测与反例

- 反例：只接一条刚好 7.5 件/s 的 carbide 带，breach 在 4 秒内打空 maxAmmo 30 后进入「打一发等一发」；要连续 2437.5 DPS 得双线或仓储 [src: 00-data/turrets.json]
- 反例：拿 breach 打 22 甲还用 tungsten，单发 71.25 对 22 甲只剩 73.9 DPS，是同塔 carbide 的 1/30；复现看 对22甲 列的 2272.5 与 73.9 两行 [src: 00-data/turrets.json]

## 常见误解

- 「breach 是前期塔，后期没用」错：carbide 2437.5 DPS 到终局仍是单塔最高档，它输在射程不在数字 [src: 00-data/turrets.json]
- 「单发 325 一定打得慢」错：rm 0.20 让它 7.5 发/s，比很多「速射塔」还密 [src: 00-data/turrets.json]
- 「beryllium 最划算」错：3.0 件/s 换 95.6 DPS，DPS/物品 31.9 是三种里最低 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.209]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.202]]
