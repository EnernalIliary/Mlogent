---
tokens: 623
id: COMBAT.TURRET.105
title: wave —— 20 发弹幕的灭火器
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3529"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/wave"
  - "jar:v160.7#blocks/wave"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, wave, 状态控制 / 灭火与击退]
---

## 一句话

wave 的 DPS 几乎是零（water 0 伤、slag 也只有 80），但它做的是 DPS 表达不了的事：20 发/s 的液体弹幕带 0.7 击退，能把近战单位按在原地；water 与 cryofluid 带灭火标记，是唯一能压住燃烧波的手段。它不打输出，它买的是「不让敌人靠近」。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：状态控制 / 灭火与击退
- **射击模式**：ShootPattern(默认)（每触发 1 发；reload 3 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- reload 3 tick ⇒ 20 发/s，是全作射速最高的塔之一；弹药不是物品而是液体，靠管道/容器供给，断液即停火 [src: 00-data/turrets.json]
- 四种液体分工明确：water 0 伤纯击退+灭火、slag 4 伤（80 DPS，唯一有伤害）、cryofluid 0 伤冻结+灭火、oil 0 伤只上油
- 击退 0.7 是它的核心：对近战/自爆单位，把推进速度压下去等于给后排争取时间 [src: 00-data/turrets.json]
- 射界 110 世界单位（13.75 格）偏短，注定是二线/贴核心的塔，不是前线塔 [src: 00-data/turrets.json]
- **优点**：
  - 20 发/s 的击退是全家最强的软控制，对 crawler 这类贴脸单位效果拔群 [src: 00-data/turrets.json]
  - 灭火标记能压住燃烧地面与燃烧单位，是防守图里的保险
  - slag 模式仍有 80 DPS，不至于完全没有输出
- **缺点**：
  - water/cryofluid/oil 三种弹药的直伤是 0，纯控制，遇到高血量推进单位只能拖延
  - 液体供给链一旦被拆或断流，塔立刻变哑巴
  - 13.75 格的射界意味着它护不住外圈，只能护核心 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 2 | 00-data/blocks.json |
| 血量 | 1000 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 145 件（copper × 25、lead × 75、metaglass × 45） | 00-data/blocks.json |
| 射程 | 110 世界单位（13.75 格） | 00-data/turrets.json |
| reload | 3 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 50 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 单发伤害 | 发/s | 0甲 DPS | 机制 | 来源 |
|---|---|---|---|---|---|
| water | 0 | 20 | 0 | 只有击退 0.7 与 extinguisher（灭火）标记 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3536 |
| slag | 4 | 20 | 80 | 唯一有伤害的弹药 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3541 |
| cryofluid | 0 | 20 | 0 | 冻结 + 灭火，无直伤 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3544 |
| oil | 0 | 20 | 0 | 只上油（可燃）状态 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3547 |

- reload 3 tick ⇒ 20 发/s，是本作射击频率最高的塔之一；优势全在状态与击退，不在伤害。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3529]
- 液体塔的弹药不是物品：要管道/容器供液，断液即停火（不是打空弹匣）。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3529]

- 本库对液体塔不给「DPS 排名」：water 的 0 伤是设计，不是缺数据；要比较请用 0.7 击退与灭火标记 [src: 00-data/turrets.json]
- slag 的 80 DPS 是 4 伤 × 20 发/s，别把它当成输出塔来规划火力

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3529 —— 定义行 new LiquidTurret("wave")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=wave —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 wave 顶第一排挡重甲，80 DPS 对 22 甲几乎打不动，反而先被打掉；复现：00-data/turrets.json 里 wave 无 ammo[] 表，数值见 gen_turrets.py 的 MANUAL 块 [src: 00-data/turrets.json]
- 反例：把 wave 接 oil 当输出塔，0 直伤意味着它一发不杀，只上油；复现：MANUAL 表 oil 行 0 直伤 [src: 00-data/turrets.json]

## 常见误解

- 「wave 是最强塔所以排第一」错：它强在控制与灭火，纯输出比不过任何同级炮塔
- 「液体塔不需要供给」错：断液立刻停火，比弹匣打空更致命

## 相关

- [[COMBAT.TURRET.112]]
- [[COMBAT.TURRET.118]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.104]]
- [[COMBAT.TURRET.106]]
