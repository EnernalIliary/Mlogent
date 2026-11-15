---
tokens: 558
id: COMBAT.TURRET.103
title: scorch —— 60 世界单位的贴脸火盆
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3419"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/scorch"
  - "jar:v160.7#blocks/scorch"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, scorch, 贴脸火墙 / 熔断近战]
---

## 一句话

scorch 是「把火泼在门口」的塔：射界只有 60 世界单位（7.5 格），却能在 6 tick 的 reload 下每秒泼出 10 发 pyratite，300 单体 DPS 在贴脸距离上非常凶。问题是它只打地面、射界短到必须建在最前线，敌人一旦绕路或远程压制，它就只是个烧钱的装饰。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：C ｜ **岗位**：贴脸火墙 / 熔断近战
- **射击模式**：ShootPattern(默认)（每触发 1 发；reload 6 tick） [src: 00-data/turret_shots.json]
- **目标层**：地面、建筑
- 每触发 1 发，reload 6 tick，射速 10 发/s；只打地面，空中目标不入选 [src: 00-data/turrets.json]
- pyratite 单发 30 → 300 DPS、1.0 件/s；coal 单发 17 → 170 DPS 但要 3.33 件/s，是「便宜但费弹」的反向选择 [src: 00-data/turrets.json]
- 弹体只活 18 tick 左右（火焰类），等于有效射界比面板的 60 世界单位还短，必须贴脸放 [src: 00-data/turrets.json]
- 对 22 甲 pyratite 仍有 80 DPS，是早期少见的「不太怕护甲」的塔——因为它的单发够重
- **优点**：
  - 300 单体 DPS 只需要 47 件造价，是前期性价比最极端的塔之一 [src: 00-data/turrets.json]
  - 对 22 甲 80 DPS，比同期的 duo 石墨（6.8）高一个数量级 [src: 00-data/turrets.json]
  - 1×1 占地 + 短射界，天然适合塞在墙后、门口、传送带汇合处
- **缺点**：
  - 60 世界单位（7.5 格）的射界意味着敌人站在射界外就能无损拆它 [src: 00-data/turrets.json]
  - 只打地面，对空投完全无解
  - 烧 pyratite 时 1.0 件/s，看似省，其实 pyratite 本身是二级产物，前期产能往往不够 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 1 | 00-data/blocks.json |
| 血量 | 400 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 47 件（copper × 25、graphite × 22） | 00-data/blocks.json |
| 射程 | 60 世界单位（7.50 格） | 00-data/turrets.json |
| reload | 6 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 1.5 / 50 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| pyratite | 30 | 0 | 1.00 | 10.00 | 300.0 | 300.0 | 1.00 | 80.0 | 00-data |
| coal | 17 | 0 | 1.00 | 10.00 | 170.0 | 170.0 | 3.33 | 17.0 | 00-data |

- 「10 发/s × 30」= 300，是本库口径下 scorch 的满射速上限；实际战斗中火焰弹的飞行时间会吃掉近身前的部分输出 [src: 00-data/turrets.json]
- 面板 DPS = 单体 DPS，火焰弹没有溅射字段，0.75 折算不适用 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3419 —— 定义行 new ItemTurret("scorch")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=scorch —— 源码派生记录（含证据行）

## 实测与反例

- 反例：把 scorch 排在二线当常规火力，7.5 格的射界会让它整场不输出；复现：00-data/turrets.json 里 scorch 的 range 为 60 世界单位，对比 duo 的 160 [src: 00-data/turrets.json]
- 反例：用 coal 追求「更省」，170 DPS 却要吃 3.33 件/s，实际是每点 DPS 消耗两倍煤；复现：对比表内 pyratite 与 coal 的「物品/秒」与「DPS/物品」两列 [src: 00-data/turrets.json]

## 常见误解

- 「火焰塔射程长」错：scorch 只有 60 世界单位，是全家最短的几门之一
- 「scorch 打不了重甲」错：它单发 30，对 22 甲还有 80 DPS，真正的短板是射界与目标层

## 相关

- [[COMBAT.TURRET.101]]
- [[COMBAT.TURRET.113]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.102]]
- [[COMBAT.TURRET.104]]
