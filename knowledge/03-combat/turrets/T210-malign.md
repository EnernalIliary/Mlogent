---
tokens: 600
id: COMBAT.TURRET.210
title: malign —— 2400 电、每秒十七发的随机落点弹幕
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:5926"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootSummon.java:20"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/malign"
  - "jar:v160.7#blocks/malign"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, malign, 终局弹幕 / 覆盖式压制]
---

## 一句话

malign 解决「终局的清场与压制」，不解决「精准点杀」：reload 3.5 tick 的 70 直伤给 17.14 发/s、1200 单体 DPS，每发还带 intervalBullet 雷电 18 与 fragBullet 激光 65，实际总输出高于 1200。代价是 2400 电/s（全作最高）与 ShootSummon 的随机落点——它按覆盖结算，不按瞄准结算。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5941]

## 规则 / 公式

- **层位**：S ｜ **岗位**：终局弹幕 / 覆盖式压制
- **射击模式**：ShootSummon（每触发 1 发；reload 3.5 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- reload 3.5 tick ⇒ 17.14 发/s，直伤 70 → 1200 单体 DPS [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5941]
- 每发还带 intervalBullet 雷电 18 与 fragBullet 激光 65，实际总输出高于 1200 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5930]
- ShootSummon 在半径内随机落点，是覆盖式弹幕不是精确瞄准 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5926]
- 耗电 2400/s 是全作最高档，必须有独立电网 + 储能 [src: 00-data/turrets.json]
- 对 22 甲：单发 70 剩 48（69%），比 smite 的 88% 差一档——弹幕塔靠密度不靠单发 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5941]
- **优点**：
  - 1200 DPS + 两种附弹，是 Erekir 清场效率最高的塔 [src: 00-data/turrets.json]
  - 410 世界单位（51.25 格）覆盖 + 随机落点，压制面积极大 [src: 00-data/turrets.json]
- **缺点**：
  - 2400 电/s 让它在电网波动时最先熄火，供电成本要算进总账 [src: 00-data/turrets.json]
  - 随机落点打单体不如 smite 稳定，杀 boss 要配点杀塔 [src: 00-data/turrets.json]
  - 5×5 + 2400 件，终局才有资格摆 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 5 | 00-data/blocks.json |
| 血量 | 9250 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 2400 件（graphite × 500、silicon × 500、phase-fabric × 200、beryllium × 1000、carbide × 200） | 00-data/blocks.json |
| 射程 | 410 世界单位（51.25 格） | 00-data/turrets.json |
| reload | 3.5 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 100 | 00-data/turrets.json |
| 耗电 | 2400/s | 00-data/turrets.json |

| 项 | 值 | 说明 | 来源 |
|---|---|---|---|
| 直伤 | 70 | FlakBulletType(8, 70) | Mindustry-Source/core/src/mindustry/content/Blocks.java:5927 |
| 发/s | 17.14 | reload 3.5 tick | Mindustry-Source/core/src/mindustry/content/Blocks.java:5941 |
| 0甲 DPS | 1200 | 70 × 17.14 | 本文口径 |
| 附弹 | intervalBullet 雷电 18 + fragBullet 激光 65 | 每发还带两种子弹 | Mindustry-Source/core/src/mindustry/content/Blocks.java:5930 |
| 耗电 | 2400/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:5949 |

- 射界由 ShootSummon 在半径内随机落点（Blocks.java:6246），所以它不是精确瞄准，是覆盖式弹幕。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5926]
- 2400/s 的耗电是全作最高档，必须有独立电网与储能。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5926]

- 面板 DPS 的 0.75 折算只对溅射成立，malign 的 70 是直伤；附弹（雷电 18 / 激光 65）不计入 1200 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:5926 —— 定义行 new PowerTurret("malign")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:6246 —— 含 ShootSummon
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootSummon.java:20
- 00-data/turret_shots.json#id=malign —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 malign 单挑 22 甲 boss，单发 70 只剩 48，69% 保留 + 随机落点让它不如一台 smite 稳定 [src: 00-data/turrets.json]
- 反例：只配 1200 电/s 的电网，malign 会在其他塔用电时降到半速 [src: 00-data/turrets.json]

## 常见误解

- 「1200 DPS 是精确单体」错：ShootSummon 随机落点，命中期望低于纸面 [src: Mindustry-Source/core/src/mindustry/entities/pattern/ShootSummon.java:20]
- 「耗电高所以弱」错：它买到的是覆盖面积，不是效率 [src: 00-data/turrets.json]
- 「附弹只是特效」错：雷电 18 + 激光 65 每发都带，实际输出高于 1200 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:5930]

## 相关

- [[COMBAT.TURRET.209]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
