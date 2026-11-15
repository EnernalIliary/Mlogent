---
tokens: 520
id: COMBAT.TURRET.104
title: hail —— 235 世界单位的单发炮击
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3463"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/hail"
  - "jar:v160.7#blocks/hail"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, hail, 早期曲射 / 群体压制]
---

## 一句话

hail 用一门 57 件的炮把火力投到 235 世界单位（29.38 格）外，是开局唯一能越过前排打后排的手段。它每 60 tick 才响一发，单体 25、面板 58.8，数字不好看；真正的问题是这发炮弹飞得慢、落点固定，敌人一走位就全空。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：B ｜ **岗位**：早期曲射 / 群体压制
- **射击模式**：ShootPattern(默认)（每触发 1 发；reload 60 tick） [src: 00-data/turret_shots.json]
- **目标层**：地面、建筑
- 每触发 1 发，reload 60 tick（1 发/s）；只打地面，空中目标不入选 [src: 00-data/turrets.json]
- pyratite 25 直伤 + 45 溅射 → 面板 58.8；石墨 20 + 33 → 44.8；硅弹 reloadMultiplier 1.20 把射速压到 0.83 发/s，面板只有 37.3 [src: 00-data/turrets.json]
- 曲射弹道（ArtilleryBulletType）会越过墙体，所以它能打墙后的集结单位，这是它存在的核心理由
- 溅射半径是主要价值：单体 25 意味着它从来不是点杀塔，而是往人堆里丢石头
- **优点**：
  - 235 世界单位（29.38 格）的射界在前期无对手，能在敌人接近前就开始削血 [src: 00-data/turrets.json]
  - 越墙曲射，能打到被墙挡住的地面单位
  - 57 件造价 + 1 发/s，供给压力极小（0.25~0.5 件/s） [src: 00-data/turrets.json]
- **缺点**：
  - 1 发/s 的节奏太慢，漏一发就少一发；对高机动目标命中率惨淡
  - 不防空，空投波次里完全缺席
  - 面板 58.8 在 130 件的 scatter（222.5）面前毫无竞争力，只赢在射界 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 1 | 00-data/blocks.json |
| 血量 | 260 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 57 件（copper × 40、graphite × 17） | 00-data/blocks.json |
| 射程 | 235 世界单位（29.38 格） | 00-data/turrets.json |
| reload | 60 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 10 / 10 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| pyratite | 25 | 45 | 1.00 | 1.00 | 25.0 | 58.8 | 0.25 | 3.0 | 00-data |
| graphite | 20 | 33 | 1.00 | 1.00 | 20.0 | 44.8 | 0.50 | 2.0 | 00-data |
| silicon | 20 | 33 | 1.20 | 0.83 | 16.7 | 37.3 | 0.28 | 1.7 | 00-data |

- 面板 58.8 = 1 发/s × (25 + 0.75×45)，溅射占了大头；只报单体 25 会严重低估它，只报面板会高估单挑能力 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3463 —— 定义行 new ItemTurret("hail")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=hail —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 hail 打单体 boss，1 发/s × 25 直伤 ≈ 25 DPS，连 duo 铜弹（27）都不如；复现：00-data/turrets.json 里 hail 单体 DPS 列与 duo 对比 [src: 00-data/turrets.json]
- 反例：把 hail 当防空，targetAir 为 false，飞行单位从头顶过也不开火；复现：同表 air/ground 字段 [src: 00-data/turrets.json]

## 常见误解

- 「炮击塔伤害高」错：hail 单发只有 25，它的价值是射界与越墙，不是数字
- 「溅射能补足单发」部分对：面板 58.8 确实靠溅射撑起来，但前提是敌人聚团 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.114]]
- [[COMBAT.TURRET.101]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.103]]
- [[COMBAT.TURRET.105]]
