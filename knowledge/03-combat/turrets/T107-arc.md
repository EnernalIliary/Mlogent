---
tokens: 539
id: COMBAT.TURRET.107
title: arc —— 链式电弧的 34 点秒伤
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3602"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/arc"
  - "jar:v160.7#blocks/arc"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, arc, 链式电击 / 打断控制]
---

## 一句话

arc 的单体数字很难看：20 直伤、1.71 发/s，0 甲 34.3 DPS；它买的是链状闪电——一次放电会跳到相邻目标，并附上 shocked 状态打断敌人。所以它是「人多时强、单挑时废」的塔，还得接受它完全不防空。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：B ｜ **岗位**：链式电击 / 打断控制
- **射击模式**：ShootPattern(默认)（每触发 1 发；reload 35 tick） [src: 00-data/turret_shots.json]
- **目标层**：地面、建筑
- 每触发 1 发，reload 35 tick（1.71 发/s），20 直伤，链长 25 世界单位 [src: 00-data/turrets.json]
- collidesAir=false：完全不防空，飞行单位从头顶过它一枪不发 [src: 00-data/turrets.json]
- 链式伤害是对群补偿：单体 34.3 DPS 只是下限，敌人越密总输出越高 [src: 00-data/turrets.json]
- 附 shocked 状态（打断/削弱），价值不在数字里；耗电 198/s 是它唯一的重成本 [src: 00-data/turrets.json]
- **优点**：
  - 100 件造价 + 链式伤害，在密集地面波里是性价比很高的清杂手段 [src: 00-data/turrets.json]
  - shocked 状态能打断敌人动作，对近战冲锋有额外价值
  - 1×1 占地，容易塞进任何防线缝隙
- **缺点**：
  - 34.3 单体 DPS 是全作垫底档，单挑任何硬目标都打不动 [src: 00-data/turrets.json]
  - 不防空，空投波次完全缺席
  - 90 世界单位（11.25 格）的射界很短，必须贴前线 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 1 | 00-data/blocks.json |
| 血量 | 260 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 100 件（copper × 50、lead × 50） | 00-data/blocks.json |
| 射程 | 90 世界单位（11.25 格） | 00-data/turrets.json |
| reload | 35 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 30 / 40 | 00-data/turrets.json |
| 耗电 | 198/s | 00-data/turrets.json |

| 项 | 值 | 说明 | 来源 |
|---|---|---|---|
| 直伤 | 20 | LightningBulletType | Mindustry-Source/core/src/mindustry/content/Blocks.java:3603 |
| lightningLength | 25 | 链长（世界单位） | Mindustry-Source/core/src/mindustry/content/Blocks.java:3604 |
| 发/s | 1.71 | reload 35 tick | Mindustry-Source/core/src/mindustry/content/Blocks.java:3626 |
| 0甲 DPS | 34.3 | 20 × 1.71 | 本文口径 |
| 耗电 | 198/s | consumePower(3.3) | Mindustry-Source/core/src/mindustry/content/Blocks.java:3631 |

- collidesAir=false ⇒ 完全不防空；链状闪电会跳到相邻目标，实际总输出高于单体 DPS。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3602]
- 附 shocked 状态（打断/削弱），价值高于数字。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3602]

- 34.3 = 20 × 1.71，只算一个目标；链式命中 N 个目标时实际输出近似乘 N（未在库里建模，属估算） [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3602 —— 定义行 new PowerTurret("arc")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=arc —— 源码派生记录（含证据行）

## 实测与反例

- 反例：拿 arc 打 boss，34.3 DPS 不到一门 duo 石墨（67.5）的一半；复现：00-data/turrets.json 里 arc 无 ammo[] 表，数值见 MANUAL 块 [src: 00-data/turrets.json]
- 反例：以为 arc 能防空的常见排布，飞行单位会直接穿过它的射界；复现：MANUAL arc 表 notes 的 collidesAir=false [src: 00-data/turrets.json]

## 常见误解

- 「电塔伤害都高」错：arc 的 20 直伤是全作最低档之一，它靠链与状态赚钱
- 「链状闪电能打空中」错：collidesAir 为 false，空中目标直接被过滤

## 相关

- [[COMBAT.TURRET.106]]
- [[COMBAT.TURRET.108]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
