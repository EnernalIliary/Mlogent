---
tokens: 580
id: COMBAT.TURRET.206
title: afflict —— 368 世界单位、216 DPS 的穿甲电炮
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5024"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/afflict"
  - "jar:v160.7#blocks/afflict"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, afflict, 中口径电塔 / 穿刺射击]
---

## 一句话

afflict 解决「中期远程点掉两三个目标」，不是「终局主力」：reload 50 tick 的 180 直伤 = 216 DPS，pierceCap 2 让它在密集队形里打双份，368 世界单位（46.00 格）覆盖配 300 电/s。它不吃护甲惩罚（无 armorMultiplier，对 22 甲剩 158、88%），代价是慢弹道与对电网的绝对依赖。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5025]

## 规则 / 公式

- **层位**：B ｜ **岗位**：中口径电塔 / 穿刺射击
- **射击模式**：ShootPattern(默认)（每触发 1 发；reload 50 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- reload 50 tick ⇒ 1.2 发/s，直伤 180 → 216 DPS [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5025]
- pierceCap 2 可穿 2 个目标；speed 5、lifetime 80 ⇒ 弹道慢，打机动目标要预判 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- 无 armorMultiplier，对 22 甲单发剩 158（88%），是 Erekir 中不吃护甲惩罚的中口径 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5036]
- 耗电 300/s，4×4、590 件、3520 血 [src: 00-data/turrets.json]
- 368 世界单位（46.00 格）比 titan 短但比大多数 Erekir 塔远 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5024]
- **优点**：
  - 590 件 + 368 覆盖，是 Erekir 中期最便宜的远程点名塔 [src: 00-data/turrets.json]
  - pierceCap 2 在密集队形里等效双倍输出，且不吃护甲惩罚 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- **缺点**：
  - 216 DPS 在 590 件档不算高：smite 562.5 只贵 3.7 倍 [src: 00-data/turrets.json]
  - 300 电/s 需要独立电网，断电直接变摆设 [src: 00-data/turrets.json]
  - 弹道 speed 5，对高速飞行/走位单位命中率打折 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 4 | 00-data/blocks.json |
| 血量 | 3520 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 590 件（graphite × 250、silicon × 200、surge-alloy × 100、oxide × 40） | 00-data/blocks.json |
| 射程 | 368 世界单位（46.00 格） | 00-data/turrets.json |
| reload | 50 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 20 | 00-data/turrets.json |
| 耗电 | 300/s | 00-data/turrets.json |

| 项 | 值 | 说明 | 来源 |
|---|---|---|---|
| 直伤 | 180 | BasicBulletType | Mindustry-Source/core/src/mindustry/content/Blocks.java:5025 |
| 发/s | 1.2 | reload 50 tick | Mindustry-Source/core/src/mindustry/content/Blocks.java:5030 |
| 0甲 DPS | 216 | 180 × 1.2 | 本文口径 |
| 耗电 | 300/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:5036 |

- pierceCap 2（可穿 2 个目标），speed 5、lifetime 80 ⇒ 弹道偏慢、需要预判。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5024]
- Erekir 中口径电塔，定位类似 lancer 但不吃护甲惩罚（无 armorMultiplier）。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5024]

- 本库没有 afflict 的 ammo[]（shootType 不在 bullets.json），180 与 1.2 发/s 来自源码手工表；158 是按 max(180−22, 18) 算的对 22 甲单发 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5025]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5024 —— 定义行 new PowerTurret("afflict")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=afflict —— 源码派生记录（含证据行）

## 实测与反例

- 反例：把 afflict 当防空用，弹道 speed 5 追不上高速飞行单位；同价 590 件的 lustre 是瞬时命中 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- 反例：断电时 216 DPS 归零，一台 590 件的塔被电网单点故障整死 [src: 00-data/turrets.json]

## 常见误解

- 「pierceCap 2 = 双倍 DPS」错：只有两个目标重叠站位时才成立 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5030]
- 「电塔不吃弹药所以便宜」错：300 电/s 要占发电与储能，成本只是从料转到电 [src: 00-data/turrets.json]
- 「180 单发对 22 甲掉一半」错：剩 158，保留 88% [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5036]

## 相关

- [[COMBAT.TURRET.106]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.TURRET.205]]
- [[COMBAT.TURRET.207]]
