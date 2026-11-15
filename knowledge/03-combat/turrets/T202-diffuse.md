---
tokens: 587
id: COMBAT.TURRET.202
title: diffuse —— 15 发散射、料耗全库第一的贴脸武器
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4463"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/diffuse"
  - "jar:v160.7#blocks/diffuse"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, diffuse, 近程清群 / 15 发散射]
---

## 一句话

diffuse 解决「一群小单位贴脸」，不是「打硬目标」：600 件、空陆通吃，shots 15 的 ShootSpread 让它在 30 发/s 下把 oxide 的 67.5 单发泼成 2025 单体 DPS。代价写在两个数字上——只有 125 世界单位（15.62 格）的射界，以及 45 件/s 的料耗；换 graphite 或 silicon 后对 22 甲只剩 28% / 16%。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：B ｜ **岗位**：近程清群 / 15 发散射
- **射击模式**：ShootSpread(15, 4f)（每触发 15 发；reload 30 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- shots 15 + ShootSpread(15, 4f)，reload 30 tick ⇒ 30 发/s；oxide 单发 67.5 → 2025 单体 DPS [src: 00-data/turrets.json]
- ammoPerShot 3、物品/秒 45 是全场最高档——它把「清群」直接写成「烧料」 [src: 00-data/turrets.json]
- graphite 30.75 与 silicon 26.25 的单发太轻：对 22 甲分别只剩 262.5 / 127.5 DPS（28% / 16%） [src: 00-data/turrets.json]
- 4f 是 ShootSpread 的散布角，不是发数倍增；真正发数来自 shots 15 [src: Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9]
- 空陆通吃，但 125 世界单位（15.62 格）比 breach 还短 65，定位就是贴脸武器 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4463]
- **优点**：
  - 600 件 + 空陆通吃 + 30 发/s，是 Erekir 最便宜的高发数塔，清一波小单位回本极快 [src: 00-data/turrets.json]
  - 15 发散射配 shootCone 40，对散开的飞行群也有覆盖，不要求精确瞄准 [src: 00-data/turrets.json]
- **缺点**：
  - 125 世界单位（15.62 格）的射界太短，远程重甲波次可以站着打它 [src: 00-data/turrets.json]
  - oxide 45 件/s 的吞吐要两条满带，断供时 graphite 对 22 甲只剩 28% [src: 00-data/turrets.json]
  - 单发轻：对 22 甲以上全靠 oxide 硬撑，换弹药就是换一门更弱的塔 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 3 | 00-data/blocks.json |
| 血量 | 1890 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 600 件（graphite × 200、silicon × 200、beryllium × 150、tungsten × 50） | 00-data/blocks.json |
| 射程 | 125 世界单位（15.62 格） | 00-data/turrets.json |
| reload | 30 tick | 00-data/turrets.json |
| shots | 15 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 15 / 40 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| oxide | 67.5 | 0 | 1.00 | 30.00 | 2025.0 | 2025.0 | 45.00 | 1365.0 | 00-data |
| graphite | 30.75 | 0 | 1.00 | 30.00 | 922.5 | 922.5 | 90.00 | 262.5 | 00-data |
| silicon | 26.25 | 0 | 1.00 | 30.00 | 787.5 | 787.5 | 90.00 | 127.5 | 00-data |

- 面板 DPS 与单体相同（三种弹药 splash 都是 0），但 30 发/s 含 inaccuracy 0.2 的散布，实际命中低于纸面 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4463 —— 定义行 new ItemTurret("diffuse")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4515 —— 含 ShootSpread / 15
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9
- 00-data/turret_shots.json#id=diffuse —— 源码派生记录（含证据行）

## 实测与反例

- 反例：把 diffuse 当主力打 22 甲波，silicon 单发 26.25 被护甲吃掉后只剩 127.5 DPS，不如一台 425 件的 breach carbide（2272.5）；复现看 对22甲 列的 127.5 与 2272.5 [src: 00-data/turrets.json]
- 反例：只接一条 20 件/s 的带子喂 diffuse，oxide 45 件/s 的需求只能满足 44%，射速打折后 2025 DPS 掉到约 900 [src: 00-data/turrets.json]

## 常见误解

- 「shots 15 是一次 15 发齐射」错：ShootSpread 是散布，15 发在 30 tick 内打完，30 发/s 才是射速口径 [src: 00-data/turrets.json]
- 「它是溅射塔」错：三种弹药 splash 都是 0，面板 = 单体，靠数量不靠范围 [src: 00-data/turrets.json]
- 「silicon 便宜适合刷」错：silicon 的 DPS/物品 8.8 是三种最低，省下的料全变成更长的击杀时间 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.203]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.201]]
