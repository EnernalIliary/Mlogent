---
tokens: 622
id: COMBAT.TURRET.111
title: segment —— 225 点每秒的弹体清道夫
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3836"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/segment"
  - "jar:v160.7#blocks/segment"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, segment, 弹体拦截 / 防空清弹]
---

## 一句话

segment 是唯一「不杀人只清弹」的塔：它瞄准的是敌方子弹而不是单位，单发 30 点对弹体伤害、7.5 发/s，合计 225/s 的拦截吞吐。它把空投波从威胁变成可算的数学题，代价是 480/s 的电和完全为零的杀伤——敌人不来弹幕，它就白拿一个塔位。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：弹体拦截 / 防空清弹
- **射击模式**：点防（每触发拦截 1 枚弹体）（每触发 1 发；reload 8 tick） [src: 00-data/turret_shots.json]
- **目标层**：（表未标注）
- PointDefenseTurret 类：目标过滤只保留敌方弹体（单位不入选），所以它永远不会替别的塔补输出 [src: 00-data/turrets.json]
- reload 8 tick ⇒ 7.5 发/s，单发 bulletDamage 30 只对弹体结算，合计 225/s 的拦截吞吐 [src: 00-data/turrets.json]
- 拦截是概率性的：弹速越快、同时来弹越多，漏网率越高；225/s 是上限而不是保证 [src: 00-data/turrets.json]
- 射界 180 世界单位（22.5 格），需要覆盖在受威胁方向的前方，而不是贴核心 [src: 00-data/turrets.json]
- **优点**：
  - 拦下 225/s 的弹体伤害，等于把敌人的远程投射直接抹掉，对炮击/导弹波极为有效 [src: 00-data/turrets.json]
  - 不消耗物品弹药，只吃 480/s 电，后期电网宽裕时供给压力为零 [src: 00-data/turrets.json]
  - 覆盖 22.5 格，一座就能罩住一整段防线 [src: 00-data/turrets.json]
- **缺点**：
  - 对单位零伤害：敌人走到弹幕之外、或用近战单位推进时，它整场没有贡献 [src: 00-data/turrets.json]
  - 480/s 的耗电在中期是实打实的电价，需要单独电网或电池缓冲 [src: 00-data/turrets.json]
  - 225/s 只是上限，面对高弹速的 surge 类弹体仍会漏 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 2 | 00-data/blocks.json |
| 血量 | 1000 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 290 件（titanium × 40、thorium × 80、silicon × 130、phase-fabric × 40） | 00-data/blocks.json |
| 射程 | 180 世界单位（22.50 格） | 00-data/turrets.json |
| reload | 8 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 2 / 5 | 00-data/turrets.json |
| 耗电 | 480/s | 00-data/turrets.json |

| 项 | 值 | 说明 | 来源 |
|---|---|---|---|
| bulletDamage | 30 | 对弹体的伤害 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3837 |
| 发/s | 7.5 | reload 8 tick | Mindustry-Source/core/src/mindustry/content/Blocks.java:3843 |
| 拦截吞吐 | 225/s | 只对弹体成立，不对单位 | 本文口径 |
| 耗电 | 480/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:3849 |

- 点防塔：击落飞来的子弹/炮弹，不伤害单位与建筑；它的「DPS」是拦截吞吐而不是杀伤。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3836]
- 对弹幕型敌人价值远超数字，对纯激光/近战敌人几乎为零。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3836]

- 本库不给 segment 算「DPS」排名：30 是对弹体伤害，不进入单位伤害统计，225/s 是拦截吞吐而不是杀伤 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3836 —— 定义行 new PointDefenseTurret("segment")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=segment —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 segment 应付纯近战波（crawler/risser），它不选单位，整波零输出；复现：00-data/turrets.json 里 segment 的 target 字段与 MANUAL 表 notes「只打弹体不打单位」 [src: 00-data/turrets.json]
- 反例：拿 30 单发去算「30 × 7.5 = 225 DPS 所以能打单位」，225/s 的量级在真实 DPS 里只是中游，而且它根本不落在单位上 [src: 00-data/turrets.json]

## 常见误解

- 「点防塔等于防空塔」错：它拦的是子弹，飞行单位本体不在它的目标集里
- 「拦截率 100%」错：225/s 是吞吐上限，来弹更密或更快就会漏 [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.108]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.110]]
- [[COMBAT.TURRET.112]]
