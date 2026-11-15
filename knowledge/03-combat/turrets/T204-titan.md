---
tokens: 566
id: COMBAT.TURRET.204
title: titan —— 390 世界单位、几乎不吃护甲的攻城炮
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4639"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/titan"
  - "jar:v160.7#blocks/titan"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, titan, 长程炮击 / 只打地面]
---

## 一句话

titan 解决「在敌人射界外先手拆阵地」，不是「打单体」：390 世界单位（48.75 格）射程、carbide 单发 525 + 750 溅射，单体 285.3、面板 591.0，对 22 甲还有 273.4（96%）。代价是只打地面（air False）与 0.54 发/s 的慢节奏——空中波次时它是 950 件的摆设。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：长程炮击 / 只打地面
- **射击模式**：ShootPattern(默认)（每触发 1 发；reload 138 tick） [src: 00-data/turret_shots.json]
- **目标层**：地面、建筑
- reload 138 tick、carbide rm 0.80 ⇒ 0.54 发/s，单发 525 + 750 溅射：单体 285.3、面板 591.0 [src: 00-data/turrets.json]
- 只打地面（targetAir False），空中单位进射界也不开火 [src: 00-data/turrets.json]
- 390 世界单位（48.75 格）是 Erekir 常规塔最远档；4×4、950 件、4000 血 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4639]
- ammoPerShot 4、maxAmmo 12 ⇒ 一匣 3 发；carbide 2.17 件/s 的吞吐在 950 件塔上不算贵 [src: 00-data/turrets.json]
- 对 22 甲：carbide 273.4（96%）、oxide 126.1（90%）、thorium 104.6（92%）——高单发溅射塔几乎不被护甲咬 [src: 00-data/turrets.json]
- **优点**：
  - 面板 591.0 DPS + 750 溅射，隔着 48.75 格就能清一片，是 Erekir 唯一能先手开火的常规塔 [src: 00-data/turrets.json]
  - 对 22 甲保留 96%，是全场最不吃护甲的塔（carbide 曲线） [src: 00-data/turrets.json]
  - 4000 血 + 4×4，能顶在前排当半肉炮台 [src: 00-data/turrets.json]
- **缺点**：
  - 完全不打空：对面空中波次时它 0 输出，防空得另配 disperse [src: 00-data/turrets.json]
  - 0.54 发/s 的节奏，单点目标要两秒以上才结算一次，打高机动单位容易空放 [src: 00-data/turrets.json]
  - 4×4 占地要求前排有视野与肉盾，摆位比数值更决定它好不好用 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 4 | 00-data/blocks.json |
| 血量 | 4000 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 950 件（thorium × 400、silicon × 300、tungsten × 250） | 00-data/blocks.json |
| 射程 | 390 世界单位（48.75 格） | 00-data/turrets.json |
| reload | 138 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 3.75 / 8 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| carbide | 525 | 750 | 0.80 | 0.54 | 285.3 | 591.0 | 2.17 | 273.4 | 00-data |
| oxide | 225 | 180 | 0.70 | 0.62 | 139.8 | 223.6 | 2.48 | 126.1 | 00-data |
| thorium | 262.5 | 350 | 1.00 | 0.43 | 114.1 | 228.3 | 1.74 | 104.6 | 00-data |

- 面板 591.0 与单体 285.3 差 2.07 倍：评价它时别拿面板比单体，溅射按 0.75 折是 BulletType.estimateDPS 的口径 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4639 —— 定义行 new ItemTurret("titan")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=titan —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 titan 打空中波次，targetAir False 意味着那一波输出是 0；同价 950 件可以摆一门 disperse（650 件）加一门 breach [src: 00-data/turrets.json]
- 反例：算「titan 591.0 高于 smite 562.5」就把它当单体塔，打单个目标只有 285.3；复现看 单体DPS 列 285.3 与 面板DPS 列 591.0 [src: 00-data/turrets.json]

## 常见误解

- 「溅射塔不需要预判」错：inaccuracy 0 但 0.54 发/s，落点固定仍要算走位 [src: 00-data/turrets.json]
- 「打得远就能当主力」错：只打地面 + 5.4 秒一发，主力位要的是持续覆盖，不是单点重击 [src: 00-data/turrets.json]
- 「4×4 是缺点」半错：4×4 换来 4000 血与 390 的覆盖，摆位对了是优点 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.205]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.203]]
