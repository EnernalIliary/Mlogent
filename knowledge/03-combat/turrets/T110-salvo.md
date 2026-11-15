---
tokens: 554
id: COMBAT.TURRET.110
title: salvo —— 4 连发 320 点秒伤的主力
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3731"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/salvo"
  - "jar:v160.7#blocks/salvo"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, salvo, 中期主力 / 连发点杀]
---

## 一句话

salvo 是中期防线的标准答案：每次 4 连发、reload 29 tick，石墨弹单体 320.7 DPS，对 22 甲还有 93.1——同造价段没有第二门塔能同时给出这个数字与这个穿甲。它的代价是 2.59 件/s 的石墨消耗，以及 1×1 塔位挤不下几门。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：中期主力 / 连发点杀
- **射击模式**：ShootPattern + shotDelay（每触发 4 发；reload 29 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 每触发 4 发（shots 4，shotDelay 拉开成连发），reload 29 tick，空陆都打 [src: 00-data/turrets.json]
- 石墨是主力弹：31 直伤、10.34 发/s → 320.7 DPS，且对 22 甲仍有 93.1，是全家最好的「便宜穿甲」 [src: 00-data/turrets.json]
- thorium 28 直伤但 reloadMultiplier 1.00 → 231.7；硅弹 rm 1.50 把射速压到 5.52 发/s，只剩 126.9 [src: 00-data/turrets.json]
- 射界 190 世界单位（23.75 格），比 duo 长一截，能架在二线覆盖前排 [src: 00-data/turrets.json]
- **优点**：
  - 320.7 单体 DPS + 93.1 对 22 甲，是 230 件价位的最优解 [src: 00-data/turrets.json]
  - DPS/物品 124（石墨），供给效率比 spectre 的 160 更好，比 swarmer 的 72 高
  - 4 连发的节奏让它在漏一发时损失可控，不像 lancer 那样一失手就白等
- **缺点**：
  - 2.59 件/s 的石墨消耗，一条满速传送带只够喂 4 门左右 [src: 00-data/turrets.json]
  - 1×1 占地（尺寸 1）挤不下几门，阵地规划会很快见顶
  - 对 22 甲 93.1 虽然好，但仍低于 spectre/fuse 的量级，后期会被替换 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 2 | 00-data/blocks.json |
| 血量 | 960 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 230 件（copper × 100、graphite × 80、titanium × 50） | 00-data/blocks.json |
| 射程 | 190 世界单位（23.75 格） | 00-data/turrets.json |
| reload | 29 tick | 00-data/turrets.json |
| shots | 4 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 8 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| graphite | 31 | 0 | 0.80 | 10.34 | 320.7 | 320.7 | 2.59 | 93.1 | 00-data |
| thorium | 28 | 0 | 1.00 | 8.28 | 231.7 | 231.7 | 2.07 | 49.7 | 00-data |
| pyratite | 25 | 15 | 1.00 | 8.28 | 206.9 | 300.0 | 1.66 | 24.8 | 00-data |
| silicon | 23 | 0 | 1.50 | 5.52 | 126.9 | 126.9 | 1.10 | 12.7 | 00-data |
| copper | 15 | 0 | 1.00 | 8.28 | 124.1 | 124.1 | 1.66 | 12.4 | 00-data |

- 93.1 = 10.34 发/s × (31 − 22)，护甲减法是逐发算的，所以连发塔的高射速在低甲时优势更大 [src: 00-data/turrets.json]
- 面板 DPS 与单体相同：salvo 的弹药没有溅射，0.75 折算不适用 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3731 —— 定义行 new ItemTurret("salvo")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3824 —— 含 shots / 4
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3825 —— 含 shotDelay / 3
- 00-data/turret_shots.json#id=salvo —— 源码派生记录（含证据行）

## 实测与反例

- 反例：拿 salvo 打 0 甲杂兵，320.7 DPS 是过剩的，同价位两门 duo 石墨（67.5×2）更便宜也更省弹；复现：00-data/turrets.json 里 salvo 与 duo 的造价/DPS 列 [src: 00-data/turrets.json]
- 反例：把 salvo 的 4 连发当 4 倍伤害算成 1282.8，实际表里 320.7 已经是 4 发合计；复现：同表 shots 4 与「单体DPS」列 [src: 00-data/turrets.json]

## 常见误解

- 「连发塔=高 DPS」对，但代价是 2.59 件/s 的供给，断弹后它什么都不是 [src: 00-data/turrets.json]
- 「石墨只是过渡弹」错：石墨在 salvo 上给出 320.7，比 thorium 的 231.7 还高 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.113]]
- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.109]]
- [[COMBAT.TURRET.111]]
