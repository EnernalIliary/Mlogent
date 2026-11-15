---
tokens: 502
id: COMBAT.TURRET.209
title: smite —— 五管重击、对 22 甲保留最高的后期主炮
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5656"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootMulti.java:30"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/smite"
  - "jar:v160.7#blocks/smite"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, smite, 后期主炮 / 五管重击]
---

## 一句话

smite 解决「后期重甲波次的主输出」，不解决「清群」：shots 5 的 ShootMulti 在 reload 100 tick 下给 3 发/s，单发 187.5 → 562.5 单体 DPS，对 22 甲 496.5（88%）——Erekir 通用塔里最高的护甲保留。代价是 2200 件、6 件/s 料耗与 5×5 占地，属于「一个塔位换一条战线」的买卖。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：S ｜ **岗位**：后期主炮 / 五管重击
- **射击模式**：ShootMulti(ShootAlternate(5f) 派生) + shots=barrels=5（每触发 5 发；reload 100 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- shots 5 + ShootMulti(ShootAlternate(5f))，reload 100 tick ⇒ 3 发/s，单发 187.5 → 562.5 单体 DPS [src: Mindustry-Source/core/src/mindustry/entities/pattern/ShootMulti.java:30]
- 5 管是轮转不是同 tick 齐射；射速口径是 3 发/s，不是 15 发/s [src: 00-data/turret_shots.json]
- 对 22 甲 496.5（88%），是 Erekir 通用塔里最高的护甲保留 [src: 00-data/turrets.json]
- 耗料 6 件/s（surge-alloy），5×5、8750 血、2200 件、建造 2450 tick [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5656]
- 空陆通吃，300 世界单位（37.50 格）覆盖，是后期少有的能同时接两层的塔 [src: 00-data/turrets.json]
- **优点**：
  - 562.5 DPS + 88% 护甲保留 + 空陆通吃，是 Erekir 后期最稳的主力 [src: 00-data/turrets.json]
  - 8750 血 + 5×5，能顶前排，不是后排玻璃炮 [src: 00-data/turrets.json]
- **缺点**：
  - 2200 件 + 5×5 占地，一个塔位的机会成本极高 [src: 00-data/turrets.json]
  - 3 发/s 对高速目标容错差，靠单发厚而不是弹幕密 [src: 00-data/turrets.json]
  - surge-alloy 6 件/s 要专门产线，与 breach 的 carbide 抢料 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 5 | 00-data/blocks.json |
| 血量 | 8750 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 2200 件（silicon × 800、phase-fabric × 300、surge-alloy × 400、oxide × 200、carbide × 500） | 00-data/blocks.json |
| 射程 | 300 世界单位（37.50 格） | 00-data/turrets.json |
| reload | 100 tick | 00-data/turrets.json |
| shots | 5 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 15 / 30 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| surge-alloy | 187.5 | 0 | 1.00 | 3.00 | 562.5 | 562.5 | 6.00 | 496.5 | 00-data |

- 面板 = 单体（无溅射）；别把 shots 5 当 5 倍伤害，射速已经折算进 3 发/s [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5656 —— 定义行 new ItemTurret("smite")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5721 —— 含 ShootAlternate
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5723 —— 含 shots / barrels / 5
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootMulti.java:30
- 00-data/turret_shots.json#id=smite —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用五台 smite 清一群小单位，562.5 DPS 却按 3 发/s 逐发结算，清群效率不如一台 malign 的 1200 DPS 弹幕 [src: 00-data/turrets.json]
- 反例：三台 smite 就是 18 件/s surge-alloy 的料耗，产线先崩再谈输出 [src: 00-data/turrets.json]

## 常见误解

- 「5 管 = 5 倍 DPS」错：ShootAlternate 轮转，总射速 3 发/s [src: 00-data/turret_shots.json]
- 「2200 件太贵」半错：它买到 8750 血 + 空陆通吃 + 88% 保留，摊到战力上不贵 [src: 00-data/turrets.json]
- 「smite 对空弱」错：air True，187.5 单发打飞行单位一样不虚 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.210]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.208]]
