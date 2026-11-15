---
tokens: 663
id: COMBAT.TURRET.207
title: lustre —— 360° 射界、专挑最硬目标的激光
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5147"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/lustre"
  - "jar:v160.7#blocks/lustre"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, lustre, 全向点杀 / 最强目标优先]
---

## 一句话

lustre 解决「阵地中央的点杀与补刀」：shootCone 360 的全向射界 + unitSort strongest，自动挑最硬的目标，不用为它调朝向；590 件、4×4，每次结算 210，对 22 甲单次保留 90%。代价是 200 电/s 加氮的双层供给，以及一个诚实的缺口——本库不给 DPS 数字，因为 ContinuousTurret 的结算间隔不在反射表里。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]

## 规则 / 公式

- **层位**：A ｜ **岗位**：全向点杀 / 最强目标优先
- **射击模式**：连续光束（每触发 1 发；reload 10 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- PointLaserBulletType，每次结算 210；shootCone 360 ⇒ 全向射界，不需要转向 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- unitSort strongest ⇒ 自动挑最硬/最贵的目标，是「优先级」而不是「最近」 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5157]
- 消耗氮 + 电 200/s，双层供给；4×4、590 件、3360 血 [src: 00-data/turrets.json]
- 对 22 甲：每次结算 210 剩 188（90%），是护甲惩罚最轻的结算方式之一 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- 250 世界单位（31.25 格）的覆盖，全向意味着实际覆盖是按它画的一个圆 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5147]
- **优点**：
  - 360° + strongest，摆阵地正中能同时照顾四面，不需要为它改朝向 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5160]
  - 590 件是同档最便宜；单次结算 210 的瞬时命中不吃弹道 [src: 00-data/turrets.json]
- **缺点**：
  - 本库不给 DPS 数字：结算间隔不在反射表里，硬写 DPS 就是编 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
  - 200 电/s + 氮，双供给断一路就停火 [src: 00-data/turrets.json]
  - 31.25 格的覆盖在后期偏近，会被 titan 的 48.75 格覆盖压制 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 4 | 00-data/blocks.json |
| 血量 | 3360 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 590 件（graphite × 200、silicon × 250、oxide × 50、carbide × 90） | 00-data/blocks.json |
| 射程 | 250 世界单位（31.25 格） | 00-data/turrets.json |
| reload | 10 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 1 / 360 | 00-data/turrets.json |
| 耗电 | 200/s | 00-data/turrets.json |

| 项 | 值 | 说明 | 来源 |
|---|---|---|---|
| 每次结算伤害 | 210 | PointLaserBulletType | Mindustry-Source/core/src/mindustry/content/Blocks.java:5148 |
| shootCone | 360 | 全向射界 | Mindustry-Source/core/src/mindustry/content/Blocks.java:5160 |
| unitSort | strongest | 优先打最强目标 | Mindustry-Source/core/src/mindustry/content/Blocks.java:5157 |
| 消耗 | nitrogen 6/60 每 tick + 电 200/60 每 tick | 双层供给 | Mindustry-Source/core/src/mindustry/content/Blocks.java:5165 |

- 连续光束型；DPS 口径依赖 ContinuousTurret 的结算间隔，本表不给 DPS 数字（诚实缺口见文末）。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5147]
- shootCone 360 + strongest 排序 ⇒ 天然点杀最硬的目标，适合放阵地中央。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5147]

- 别拿「每次结算 210」乘任意系数当 DPS：结算间隔本库没有，210 只能当一次命中的量级 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- 对 22 甲的 90% 只是单次结算保留率，不是 DPS 保留率 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5147 —— 定义行 new ContinuousTurret("lustre")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=lustre —— 源码派生记录（含证据行）

## 实测与反例

- 反例：把 210 当「210 DPS」去和 afflict 的 216 比，会得出 lustre 略弱的错误结论；实际它每秒结算多次，但本库没有间隔数字，不能反推 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- 反例：把 lustre 摆到前线，它 31.25 格的有效距离先被 titan 的 48.75 格覆盖压制；它该放二线中央 [src: 00-data/turrets.json]

## 常见误解

- 「光束塔 DPS 低」错：210 是单次结算量，间隔未知，不能当每秒伤害 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5148]
- 「360° 只是好看」错：unitSort strongest 让它自动补刀最硬目标，省掉手动集火 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5157]
- 「氮可以省」错：氮是它的第二供给，与电同级 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.206]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.TURRET.208]]
