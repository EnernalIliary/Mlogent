---
tokens: 532
id: COMBAT.TURRET.114
title: ripple —— 290 世界单位外的四连炮击
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3955"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/ripple"
  - "jar:v160.7#blocks/ripple"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, ripple, 远程曲射压制]
---

## 一句话

ripple 是中期唯一能稳定打到 290 世界单位（36.25 格）外的地面火力：每触发 4 发、2 发/s，pyratite 下单体 96、面板 231，靠溅射覆盖整片集结区。它打不到空中，且 0.5 触发/s 的节奏意味着它对快速突进几乎无反应——它是「提前削血」的塔，不是「救火」的塔。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：远程曲射压制
- **射击模式**：ShootPattern（每触发 4 发；reload 120 tick） [src: 00-data/turret_shots.json]
- **目标层**：地面、建筑
- 每触发 4 发（shots 4），reload 120 tick ⇒ 0.5 触发/s、2 发/s；只打地面 [src: 00-data/turrets.json]
- ammoPerShot 2：每次装填吃 2 件弹药，这是它弹耗看起来翻倍的原因 [src: 00-data/turrets.json]
- pyratite 48 直伤 + 90 溅射 → 单体 96 / 面板 231；石墨 40 + 70 → 80 / 185 但 ips 2.0 更费弹 [src: 00-data/turrets.json]
- 曲射弹道越墙，能打被墙挡住的地面集结区
- **优点**：
  - 36.25 格射界 + 越墙曲射，中期没有任何地面塔能替代它的覆盖范围 [src: 00-data/turrets.json]
  - 面板 231 的溅射输出对成团的地面波非常高效
  - 对 22 甲 pyratite 仍有 52 DPS，比 hail 的 25 单体强得多
- **缺点**：
  - 不能防空，空投波次完全缺席 [src: 00-data/turrets.json]
  - 0.5 触发/s 太慢，对高速突进单位几乎打不中 [src: 00-data/turrets.json]
  - blast-compound 与 plastanium 的面板都停在 215，说明它的上限被 reload 卡死，换弹提升有限 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 3 | 00-data/blocks.json |
| 血量 | 1170 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 345 件（copper × 150、graphite × 135、titanium × 60） | 00-data/blocks.json |
| 射程 | 290 世界单位（36.25 格） | 00-data/turrets.json |
| reload | 120 tick | 00-data/turrets.json |
| shots | 4 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 8 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| pyratite | 48 | 90 | 1.00 | 2.00 | 96.0 | 231.0 | 1.00 | 52.0 | 00-data |
| graphite | 40 | 70 | 1.00 | 2.00 | 80.0 | 185.0 | 2.00 | 36.0 | 00-data |
| plastanium | 40 | 90 | 1.00 | 2.00 | 80.0 | 215.0 | 2.00 | 36.0 | 00-data |
| blast-compound | 40 | 90 | 1.00 | 2.00 | 80.0 | 215.0 | 1.00 | 36.0 | 00-data |
| silicon | 40 | 70 | 1.20 | 1.67 | 66.7 | 154.2 | 1.11 | 30.0 | 00-data |

- 231 = 2 发/s × (48 + 0.75×90)，溅射占六成；只报单体 96 会低估清群，只报面板会高估点杀 [src: 00-data/turrets.json]
- ammoPerShot 2 意味着实际弹耗是 2 发/s × 2 = 4 件/s（pyratite 口径下 ips 1.0 已是按发计） [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3955 —— 定义行 new ItemTurret("ripple")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:4065 —— 含 shots / 4
- 00-data/turret_shots.json#id=ripple —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 ripple 打单体 boss，96 单体 DPS 只有 fuse 的 1/5，而造价 345 对 550；复现：00-data/turrets.json 里 ripple 与 fuse 的「单体DPS」列 [src: 00-data/turrets.json]
- 反例：以为换 blast-compound 能提 DPS，表里面板仍是 215、ips 1.0，提升只在溅射结构上；复现：同表 ripple 各弹药行 [src: 00-data/turrets.json]

## 常见误解

- 「曲射塔射程远所以能替代前线塔」错：0.5 触发/s 的节奏挡不住突进 [src: 00-data/turrets.json]
- 「4 发就是 4 倍」错：2 发/s 已是 4 发摊平后的射速口径

## 相关

- [[COMBAT.TURRET.104]]
- [[COMBAT.TURRET.116]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.113]]
- [[COMBAT.TURRET.115]]
