---
tokens: 540
id: COMBAT.TURRET.117
title: spectre —— 685 点秒伤的终局主炮
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4248"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/spectre"
  - "jar:v160.7#blocks/spectre"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, spectre, 后期主力 / 全能点杀]
---

## 一句话

spectre 是后期防线的答案：reload 7 tick、8.57 发/s，thorium 下单体 685.7 DPS，对 22 甲 497.1，空陆通吃，射界 260 世界单位（32.5 格）。它唯一的问题是弹耗——4.29 件/s 的 thorium 意味着一条专用产线只够喂两门，且 1875 件的造价让成型很晚。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：S ｜ **岗位**：后期主力 / 全能点杀
- **射击模式**：ShootAlternate(8f)（每触发 1 发；reload 7 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 每触发 1 发，reload 7 tick ⇒ 8.57 发/s；ShootAlternate 双管交替，空陆都打 [src: 00-data/turrets.json]
- thorium 80 直伤 → 685.7 单体/面板，对 22 甲 497.1；pyratite 70 + 20 溅射 → 600 / 728.6 面板 [src: 00-data/turrets.json]
- coolantMult 0.5：吃冷却液能把 reload 压到 3.5 tick，这是它真正的上限所在 [src: 00-data/turrets.json]
- 石墨模式 rm 1.70 把射速压到 5.04 发/s、DPS 252.1，说明它对弹药质量极度敏感 [src: 00-data/turrets.json]
- **优点**：
  - 685.7 单体 / 497.1 对 22 甲，是空陆通用的最强持续输出 [src: 00-data/turrets.json]
  - 8.57 发/s 的高射速让漏发损失极小，输出极其稳定 [src: 00-data/turrets.json]
  - 32.5 格射界 + 2560 血量，能架在二线并扛住零星反击 [src: 00-data/turrets.json]
- **缺点**：
  - 4.29 件/s 的 thorium 消耗，供给线一断 DPS 立刻归零 [src: 00-data/turrets.json]
  - 1875 件造价 + 4×4 占地，成型窗口很晚
  - 对 0 甲不如 fuse 的 540 来得便宜，它的优势在护甲与射界 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 4 | 00-data/blocks.json |
| 血量 | 2560 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 1875 件（copper × 900、graphite × 300、thorium × 250、plastanium × 175、surge-alloy × 250） | 00-data/blocks.json |
| 射程 | 260 世界单位（32.50 格） | 00-data/turrets.json |
| reload | 7 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 0.5 / 24 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| thorium | 80 | 0 | 1.00 | 8.57 | 685.7 | 685.7 | 4.29 | 497.1 | 00-data |
| pyratite | 70 | 20 | 1.00 | 8.57 | 600.0 | 728.6 | 2.86 | 411.4 | 00-data |
| graphite | 50 | 0 | 1.70 | 5.04 | 252.1 | 252.1 | 1.26 | 141.2 | 00-data |

- 497.1 = 8.57 × (80 − 22)，thorium 模式下与 685.7 差 27.5%，护甲仍是要算的 [src: 00-data/turrets.json]
- coolantMult 0.5 的收益不进本表 DPS：表值是不冷却口径，实际接冷却液会更高，别直接对比 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4248 —— 定义行 new ItemTurret("spectre")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4302 —— 含 ShootAlternate
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29
- 00-data/turret_shots.json#id=spectre —— 源码派生记录（含证据行）

## 实测与反例

- 反例：以为 spectre 面板最高所以通杀，它的 728.6 是 pyratite 溅射口径，单体只有 600，比 thorium 的 685.7 低；复现：00-data/turrets.json 里 spectre 各弹药行的单体/面板列 [src: 00-data/turrets.json]
- 反例：拿 spectre 打早期波次，4.29 件/s 的 thorium 在前期根本供不起，实际 DPS 远低于标称；复现：同表 ips 列与 550 件的 fuse 对比 [src: 00-data/turrets.json]

## 常见误解

- 「面板 DPS 就是实战 DPS」错：不冷却、零甲、满供弹三个前提缺一不可
- 「双管=双倍射速」错：8.57 发/s 已是 reload 7 的口径，炮管数只影响外观与弹道 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.113]]
- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.118]]
