---
tokens: 563
id: COMBAT.TURRET.109
title: swarmer —— 4 发齐射的导弹雨
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3656"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/swarmer"
  - "jar:v160.7#blocks/swarmer"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, swarmer, 导弹群伤 / 中程防空]
---

## 一句话

swarmer 是中期最舒服的「一发多弹」塔：每次触发 4 发导弹、8 根发射管轮转，surge-alloy 下单体 126、面板 309.8。它的问题是弹药质量决定一切——换成 pyratite 单体掉到 84，而 22 甲面前 surge 也只有 12.6，它清群很强、啃硬目标很弱。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：导弹群伤 / 中程防空
- **射击模式**：ShootBarrel(barrels=8)（每触发 4 发；reload 34.29 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 每触发 4 发（shots 4，ShootBarrel 8 管轮转），reload 34.29 tick，空陆都打 [src: 00-data/turrets.json]
- surge-alloy 18 直伤 + 35 溅射 → 单体 126 / 面板 309.8；pyratite 12 + 45 → 84 / 320.3；blast-compound 10 + 45 → 70 / 306.3 [src: 00-data/turrets.json]
- 导弹是追踪类弹体，对移动目标命中率比曲射高，但飞行时间仍会让远距离目标少吃几发 [src: 00-data/turrets.json]
- 对 22 甲 surge 只剩 12.6，说明它是清群塔：护甲一高，导弹的 18 直伤就被吃光 [src: 00-data/turrets.json]
- **优点**：
  - 145 件造价拿到 309.8 面板 DPS，中期性价比很高 [src: 00-data/turrets.json]
  - 4 发齐射 + 溅射，对聚团的飞行/地面单位都是成片掉血
  - 30 格的射界在中期的空投波次里覆盖足够 [src: 00-data/turrets.json]
- **缺点**：
  - 对 22 甲 12.6 DPS，遇到重甲推进单位几乎无解 [src: 00-data/turrets.json]
  - 弹药消耗 1.75 件/s（surge），中期产能跟不上就降频 [src: 00-data/turrets.json]
  - 导弹飞行时间 + inaccuracy 10，对高速目标的有效命中率低于表值 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 2 | 00-data/blocks.json |
| 血量 | 1200 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 145 件（graphite × 35、titanium × 35、silicon × 30、plastanium × 45） | 00-data/blocks.json |
| 射程 | 240 世界单位（30.00 格） | 00-data/turrets.json |
| reload | 34.29 tick | 00-data/turrets.json |
| shots | 4 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 8 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| surge-alloy | 18 | 35 | 1.00 | 7.00 | 126.0 | 309.8 | 1.75 | 12.6 | 00-data |
| pyratite | 12 | 45 | 1.00 | 7.00 | 84.0 | 320.3 | 1.40 | 8.4 | 00-data |
| blast-compound | 10 | 45 | 1.00 | 7.00 | 70.0 | 306.3 | 1.40 | 7.0 | 00-data |

- 面板 309.8 与单体 126 的差来自溅射 0.75 折算，评估清群能力用面板、点杀用单体 [src: 00-data/turrets.json]
- DPS/物品 72（surge）意味着它比 spectre 省弹，但单发质量差得多

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3656 —— 定义行 new ItemTurret("swarmer")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3706 —— 含 ShootBarrel
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3712 —— 含 shots / 4
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3713 —— 含 shotDelay
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1
- 00-data/turret_shots.json#id=swarmer —— 源码派生记录（含证据行）

## 实测与反例

- 反例：拿 swarmer 打 22 甲 boss，12.6 DPS 不如一门 lancer 的 39，还要 1.75 件/s 的 surge；复现：00-data/turrets.json 里 swarmer 与 lancer 的「对22甲」列 [src: 00-data/turrets.json]
- 反例：以为齐射=4 倍伤害，实际 4 发都会各自被护甲削减，对高甲目标 4 发不如 1 发重弹；复现：对比 swarmer 与 fuse 的对22甲 12.6 vs 426.9 [src: 00-data/turrets.json]

## 常见误解

- 「导弹塔专打空中」不完全对：本库数据里 swarmer 空陆都选目标，它是通用群伤塔
- 「4 发就是 4 倍」错：4 发是 4 次独立的护甲减法，对高甲目标收益急剧下降

## 相关

- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.117]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.108]]
- [[COMBAT.TURRET.110]]
