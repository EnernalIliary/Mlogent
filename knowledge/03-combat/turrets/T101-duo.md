---
tokens: 661
id: COMBAT.TURRET.101
title: duo —— 35 件买到的连发基线
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3258"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/duo"
  - "jar:v160.7#blocks/duo"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, duo, 早期万金油 / 便宜的连发基线]
---

## 一句话

duo 解决的是「开局没有火力」，不是「后期打不动」：35 件、1×1 占地，铜弹就能把 3 发/s 铺到 160 世界单位（20 格）内，空陆都打。代价是单发只有 9~18，穿甲几乎为零——换石墨后对 22 甲只剩 6.8 DPS，过了中期它就只配守后方或打杂兵。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：B ｜ **岗位**：早期万金油 / 便宜的连发基线
- **射击模式**：ShootAlternate(3.5f)（每触发 1 发；reload 20 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 每触发 1 发，reload 20 tick；ShootAlternate(3.5f) 只是左右炮管交替，不增加发数，所以射速就是 60/20 = 3 发/s（铜弹） [src: 00-data/turrets.json]
- 三种弹药的曲线完全不同：石墨 67.5、铜 27、硅 24 单体 DPS；石墨靠 reloadMultiplier 0.80 把表里的发/s 抬到 3.75，单发 18 [src: 00-data/turrets.json]
- 硅弹买的是省弹与追踪：DPS/物品 60，铜只有 18；它的 24 DPS 比铜还低，但 0.4 件/s 的消耗几乎不吃供给 [src: 00-data/turrets.json]
- 冷却液倍率 10 是早期塔里最高档，接水能明显提高有效射速；但 1×1 的塔位往往比冷却更稀缺
- 空陆通吃（air True / ground True），是开局唯一能顺手照顾空投的低价塔
- **优点**：
  - 造价 35 件、建造 17.5 tick，开局几十秒就能架起两三门，回本极快 [src: 00-data/turrets.json]
  - 1×1 占地，能塞进任何缝隙；石墨弹 67.5 DPS 在同造价段里是顶格（约 1.9 DPS/件） [src: 00-data/turrets.json]
  - 铜、石墨、硅三种弹药全程可得，不会因为换矿线断供
- **缺点**：
  - 穿甲是全家短板：石墨对 22 甲只剩 6.8 DPS，同口径 salvo 石墨是 93.1 [src: 00-data/turrets.json]
  - 160 世界单位（20 格）的射界撑不到中期，敌人远程火力一到位就只能挨打 [src: 00-data/turrets.json]
  - 单发太轻，靠数量堆伤害；塔位一挤，几门 duo 的输出会被摊薄到不够看 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 1 | 00-data/blocks.json |
| 血量 | 250 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 35 件（copper × 35） | 00-data/blocks.json |
| 射程 | 160 世界单位（20.00 格） | 00-data/turrets.json |
| reload | 20 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 10 / 15 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| graphite | 18 | 0 | 0.80 | 3.75 | 67.5 | 67.5 | 0.94 | 6.8 | 00-data |
| copper | 9 | 0 | 1.00 | 3.00 | 27.0 | 27.0 | 1.50 | 2.7 | 00-data |
| silicon | 12 | 0 | 1.50 | 2.00 | 24.0 | 24.0 | 0.40 | 2.4 | 00-data |

- duo 的弹药没有溅射，面板 DPS 与单体 DPS 相同，0.75 折算对它不适用（对比 scatter 的 370 面板 vs 40 单体） [src: 00-data/turrets.json]
- DPS/物品 72 意味着石墨满射速只吃 0.94 件/s，供给从来不是 duo 的瓶颈，位置才是 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3258 —— 定义行 new ItemTurret("duo")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3300 —— 含 ShootAlternate
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29
- 00-data/turret_shots.json#id=duo —— 源码派生记录（含证据行）

## 实测与反例

- 反例：拿 4 门石墨 duo 打 22 甲重甲波，合计 27.2 DPS，不如一门 lancer 的单发穿透——对 22 甲时 duo 的 67.5 会掉到 6.8。复现：00-data/turrets.json 的 duo 石墨行「对22甲」列 × 4 [src: 00-data/turrets.json]
- 反例：把 duo 当远程塔摆在 160 世界单位外沿，敌人只要在射界外停下换目标，它的 27 DPS 就是 0。复现：对照 00-data/turrets.json 的 range 字段与实战敌人停火距离 [src: 00-data/turrets.json]

## 常见误解

- 「4 根炮管 = 4 发」错：ShootAlternate 只交替炮管，shots 仍是 1，射速只由 reload 20 tick 决定 [src: 00-data/turrets.json]
- 「便宜所以弱」错：石墨 duo 的 67.5 DPS 在同造价里是顶格，弱的是穿甲与射界，不是数字 [src: 00-data/turrets.json]
- 「硅弹最强」错：硅弹只有 24 DPS，它买的是省弹（0.4 件/s）与追踪，不是伤害 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.110]]
- [[COMBAT.TURRET.102]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
