---
tokens: 535
id: COMBAT.TURRET.115
title: cyclone —— 415 面板 DPS 的防空核心
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4085"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/cyclone"
  - "jar:v160.7#blocks/cyclone"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, cyclone, 防空群伤 / 中程弹幕]
---

## 一句话

cyclone 是后期防空的主力：reload 10 tick、6 发/s，surge-alloy 下单体 78、面板 415.5，是空投波的天敌；射界 200 世界单位（25 格）也够用。它的短板很明确——对 22 甲只有 7.8 DPS，所以它清群无敌、啃重甲无力，遇到重装飞行单位要靠 fuse 或 spectre 补刀。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：防空群伤 / 中程弹幕
- **射击模式**：ShootBarrel（每触发 1 发；reload 10 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 每触发 1 发，reload 10 tick ⇒ 6 发/s；空陆都打，ShootBarrel 决定炮口位置 [src: 00-data/turrets.json]
- surge-alloy 13 直伤 + 75 溅射 → 单体 78 / 面板 415.5；metaglass 6 + 45 但 rm 0.80 让射速升到 7.5 发/s，面板 298.1 [src: 00-data/turrets.json]
- 伤害结构是「少量直伤 + 大溅射」，所以它对群体的效率远高于对单体
- 405 件造价 + 1305 血量，中期就能成规模铺开
- **优点**：
  - 415.5 面板 DPS 是防空塔里的顶级数值，且只需 405 件 [src: 00-data/turrets.json]
  - 6 发/s 的高射速让溅射持续覆盖空域，漏一发不致命
  - 空陆通吃，地面波也不会浪费塔位
- **缺点**：
  - 对 22 甲 7.8 DPS：13 点直伤被护甲吃光，只剩溅射的固定折损 [src: 00-data/turrets.json]
  - surge-alloy 1.2 件/s 的消耗需要合金产线支撑 [src: 00-data/turrets.json]
  - 25 格射界对超远程轰炸单位仍偏短，需要 foreshadow 之类先手 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 3 | 00-data/blocks.json |
| 血量 | 1305 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 405 件（copper × 200、titanium × 125、plastanium × 80） | 00-data/blocks.json |
| 射程 | 200 世界单位（25.00 格） | 00-data/turrets.json |
| reload | 10 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 30 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| surge-alloy | 13 | 75 | 1.00 | 6.00 | 78.0 | 415.5 | 1.20 | 7.8 | 00-data |
| plastanium | 8 | 37.5 | 1.00 | 6.00 | 48.0 | 216.8 | 1.50 | 4.8 | 00-data |
| blast-compound | 8 | 45 | 1.00 | 6.00 | 48.0 | 250.5 | 1.20 | 4.8 | 00-data |
| metaglass | 6 | 45 | 0.80 | 7.50 | 45.0 | 298.1 | 3.75 | 4.5 | 00-data |

- 415.5 = 6 × (13 + 0.75×75)，溅射贡献占九成以上；把 415.5 当单体 DPS 会高估五倍 [src: 00-data/turrets.json]
- 对 22 甲 7.8 与面板 415.5 的悬殊差距，是评价 cyclone 时最该摆出来的两个数字 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4085 —— 定义行 new ItemTurret("cyclone")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4166 —— 含 ShootBarrel
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4167 —— 含 barrels
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1
- 00-data/turret_shots.json#id=cyclone —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 cyclone 打 22 甲的重装飞行单位，7.8 DPS 等于没打；复现：00-data/turrets.json 里 cyclone 的「对22甲」列与 spectre 的 497.1 对比 [src: 00-data/turrets.json]
- 反例：拿 metaglass 追求「更便宜」，面板掉到 298.1 且 ips 3.75，是更费弹的选择；复现：同表 cyclone 各弹药行的 ips 列 [src: 00-data/turrets.json]

## 常见误解

- 「面板 415 所以比 spectre 强」错：单体只有 78，spectre 是 685.7 [src: 00-data/turrets.json]
- 「防空塔只能打空」错：cyclone 空陆都打，地面波里它同样在输出

## 相关

- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.114]]
