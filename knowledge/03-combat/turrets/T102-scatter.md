---
tokens: 635
id: COMBAT.TURRET.102
title: scatter —— 222 面板 DPS 的空中清道夫
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3333"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/scatter"
  - "jar:v160.7#blocks/scatter"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, scatter, 近程防空 / 清弹幕]
---

## 一句话

scatter 是全作第一个真正能应付空投的塔：只打空，一次两发，铅弹 222.5 面板 DPS，散射范围能把一整群飞行单位同时削掉。它的代价写在目标层上——不打地面，所以它从来不是「主力」，而是防空缺口处的补丁；且单发只有 3，对 22 甲连破甲都破不动。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：B ｜ **岗位**：近程防空 / 清弹幕
- **射击模式**：ShootPattern + shotDelay（每触发 2 发；reload 18 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、建筑
- 每触发 2 发（shots 2，shoot.shotDelay 拉开间隔），reload 18 tick；只打空中，地面目标一律不选 [src: 00-data/turrets.json]
- 伤害几乎全在溅射里：scrap 单发 3 直伤 + 33 溅射，所以单体 DPS 只有 40、面板 370；铅弹 3 + 40.5 是 222.5 面板、20 单体 [src: 00-data/turrets.json]
- 弹药是弹幕量而不是质量：scrap 的 reloadMultiplier 0.50 把发/s 推到 13.33，消耗 2.67 件/s，射速高到近乎泼水 [src: 00-data/turrets.json]
- 对 22 甲的有效输出只有 4.0（scrap），意味着它对重装飞行单位基本只能靠溅射叠加，而不可能靠单发 [src: 00-data/turrets.json]
- **优点**：
  - 只花 130 件就能拿到 222.5 面板 DPS，是早期防空里最便宜的高数值 [src: 00-data/turrets.json]
  - 溅射半径覆盖整群，对付一团 flare 比单发狙击高效得多
  - 射程 220 世界单位（27.5 格）比同期的 hail 略短，但足以覆盖核心区上空 [src: 00-data/turrets.json]
- **缺点**：
  - 完全不落地：地面波次从它头顶过，它一枪不发，等于白占一个塔位
  - 单发直伤只有 3，任何护甲单位都免疫它的直伤，只能靠溅射的固定值磨
  - 对 22 甲 4.0 的 DPS 说明它是清杂兵的塔，不是打硬目标的塔 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 2 | 00-data/blocks.json |
| 血量 | 800 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 130 件（copper × 85、lead × 45） | 00-data/blocks.json |
| 射程 | 220 世界单位（27.50 格） | 00-data/turrets.json |
| reload | 18 tick | 00-data/turrets.json |
| shots | 2 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 35 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| scrap | 3 | 33 | 0.50 | 13.33 | 40.0 | 370.0 | 2.67 | 4.0 | 00-data |
| metaglass | 3 | 45 | 0.80 | 8.33 | 25.0 | 306.2 | 1.67 | 2.5 | 00-data |
| lead | 3 | 40.5 | 1.00 | 6.67 | 20.0 | 222.5 | 1.67 | 2.0 | 00-data |

- 面板 DPS 里的 0.75 折算只对溅射成立：scrap 40 单体 / 370 面板，两者相差 9 倍，评价它时必须说清用哪个口径 [src: 00-data/turrets.json]
- 13.33 发/s × 2 件/发左右，意味着 2.67 件/s 的消耗——单条传送带供 4 门就到极限 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3333 —— 定义行 new ItemTurret("scatter")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3402 —— 含 shotDelay
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3403 —— 含 shots / 2
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9
- 00-data/turret_shots.json#id=scatter —— 源码派生记录（含证据行）

## 实测与反例

- 反例：拿 scatter 去挡地面重甲波，它的 0 直伤落地输出意味着波次里每一只 crawler 都要靠别的塔处理。复现：00-data/turrets.json 里 scatter 的 targetGround 为 false [src: 00-data/turrets.json]
- 反例：算「scatter 370 DPS 比 salvo 320.7 强」，是拿面板口径比单体口径；同一波里若只有一个目标，scatter 只有 40，salvo 有 320.7。复现：两张表分别看「单体DPS」与「面板DPS」列 [src: 00-data/turrets.json]

## 常见误解

- 「溅射 DPS 高所以是主力」错：它只打空，地面波次里它的输出是 0，位置错了就完全没用
- 「3 点直伤太低是 bug」错：scatter 的伤害设计在溅射里，直伤只是触发器
- 「散射=命中率差」不完全对：inaccuracy 17 让弹着点散开，对群体是优点，对单点是缺点

## 相关

- [[COMBAT.TURRET.104]]
- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.101]]
- [[COMBAT.TURRET.103]]
