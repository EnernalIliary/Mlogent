---
tokens: 528
id: COMBAT.TURRET.113
title: fuse —— 540 点秒伤的贴脸霰弹
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3915"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/fuse"
  - "jar:v160.7#blocks/fuse"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, fuse, 近程终局 / 反重甲爆发]
---

## 一句话

fuse 是后期最强近防：每触发 3 发 thorium 霰弹、5.14 发/s，单体 540 DPS，对 22 甲仍有 426.9——这个数字比 spectre 的 497.1 只低一点，代价却是射界只有 90 世界单位（11.25 格）。它是「把敌人放进来再打死」的塔，摆错位置就等于没有。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：S ｜ **岗位**：近程终局 / 反重甲爆发
- **射击模式**：ShootSpread(3, 20f)（每触发 3 发；reload 35 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 每触发 3 发（shots 3，ShootSpread 20 度扇形），reload 35 tick ⇒ 5.14 发/s；空陆都打 [src: 00-data/turrets.json]
- thorium 单发 105 直伤 → 540 单体/540 面板（无溅射），对 22 甲 426.9，ips 1.03 [src: 00-data/turrets.json]
- 扇形散射让三发在近距离叠在同一目标上，远距离则散开，所以它的有效 DPS 随距离衰减得比表值快
- 1980 血量 + 3×3 占地，是能扛住一波贴脸的近防体格
- **优点**：
  - 540 单体 DPS / 426.9 对 22 甲，是 550 件价位最强的单点爆发 [src: 00-data/turrets.json]
  - 1.03 件/s 的 thorium 消耗在后期产线里几乎无感 [src: 00-data/turrets.json]
  - 扇形 3 发对贴脸的重甲单位，实际命中率比单发狙击高
- **缺点**：
  - 90 世界单位（11.25 格）的射界是全家最短板之一，敌人远程压制时它全程不还手 [src: 00-data/turrets.json]
  - 靠 thorium 供弹，前期没有 thorium 产线就完全用不了
  - 扇形散射在远距离会散到空处，标称 DPS 只在贴脸成立 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 3 | 00-data/blocks.json |
| 血量 | 1980 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 550 件（copper × 225、graphite × 225、thorium × 100） | 00-data/blocks.json |
| 射程 | 90 世界单位（11.25 格） | 00-data/turrets.json |
| reload | 35 tick | 00-data/turrets.json |
| shots | 3 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 30 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| thorium | 105 | 0 | 1.00 | 5.14 | 540.0 | 540.0 | 1.03 | 426.9 | 00-data |
| titanium | 66 | 0 | 1.30 | 3.96 | 261.1 | 261.1 | 0.99 | 174.1 | 00-data |

- 426.9 = 5.14 × (105 − 22)，护甲按每发减一次算；540 与 426.9 的差就是 22 甲的全部代价 [src: 00-data/turrets.json]
- 面板 DPS 与单体相同：fuse 的弹药没有溅射字段

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3915 —— 定义行 new ItemTurret("fuse")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3923 —— 含 ShootSpread / 3
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9
- 00-data/turret_shots.json#id=fuse —— 源码派生记录（含证据行）

## 实测与反例

- 反例：把 fuse 摆在能打到 20 格的地方，11.25 格的射界会让它在敌人靠近前一直沉默；复现：00-data/turrets.json 里 fuse 的 range 90 与 spectre 的 260 对比 [src: 00-data/turrets.json]
- 反例：以为 fuse 靠溅射清群，它的 3 发是扇形直伤、面板=单体，群伤能力远不如 cyclone 的 415.5 面板；复现：同表 fuse 与 cyclone 的「面板DPS」列 [src: 00-data/turrets.json]

## 常见误解

- 「射界短所以弱」错：在同一波贴脸的单位面前，540 DPS 是全作最高档
- 「3 发=3 倍伤害」错：3 发是 shots 内已计入 540 的口径，别重复乘

## 相关

- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.106]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.112]]
- [[COMBAT.TURRET.114]]
