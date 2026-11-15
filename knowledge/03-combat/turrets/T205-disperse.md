---
tokens: 549
id: COMBAT.TURRET.205
title: disperse —— 只打空、310 世界单位的高射炮
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4840"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/disperse"
  - "jar:v160.7#blocks/disperse"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, disperse, 专职防空 / 四管高射]
---

## 一句话

disperse 解决「空中波次怎么拦」，不解决「地面怎么打」：thorium 下 4 管交替 31.37 发/s × 67.5 = 2117.6 DPS、310 世界单位（38.75 格）覆盖大片空域。代价是 targetGround False——地面波次它整场 0 输出，而 31.37 件/s 的吞吐已经贴到单条满带极限。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：专职防空 / 四管高射
- **射击模式**：ShootAlternate(4f) + shots/barrels（每触发 4 发；reload 9 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、建筑
- shots 4 + ShootAlternate(4f)，reload 9 tick：thorium rm 0.85 ⇒ 31.37 发/s × 67.5 = 2117.6 DPS [src: 00-data/turrets.json]
- 只打空中（ground False），地面单位进射界也不开火 [src: 00-data/turrets.json]
- surge-alloy 用 11.85 件/s 换 1733.3 DPS，对 22 甲 951.1；tungsten 8.89 件/s 换 1300.0，是省料版 [src: 00-data/turrets.json]
- silicon 单发 27.75 对 22 甲只剩 153.3（21%）——AA 塔也会被护甲咬，只是平时打的是低甲飞机 [src: 00-data/turrets.json]
- 310 世界单位（38.75 格）的覆盖，4×4、650 件、4480 血 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4840]
- **优点**：
  - 2117.6 DPS + 310 覆盖，是 Erekir 唯一专职防空，空中波次没它就是漏 [src: 00-data/turrets.json]
  - 31.37 发/s 配合四管交替，命中容错高，打散开的飞行群不易漏 [src: 00-data/turrets.json]
  - thorium 对 22 甲保留 67%，比大多数 Erekir 塔的低阶弹药曲线体面 [src: 00-data/turrets.json]
- **缺点**：
  - ground False：地面波次时 650 件的塔 0 输出，必须另配地面火力 [src: 00-data/turrets.json]
  - 31.37 件/s 接近满带极限，断料立刻掉到 tungsten 的 26.67 发/s [src: 00-data/turrets.json]
  - silicon 曲线对 22 甲只剩 21%，别拿它打重甲飞行单位 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 4 | 00-data/blocks.json |
| 血量 | 4480 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 650 件（thorium × 50、silicon × 200、beryllium × 350、oxide × 50） | 00-data/blocks.json |
| 射程 | 310 世界单位（38.75 格） | 00-data/turrets.json |
| reload | 9 tick | 00-data/turrets.json |
| shots | 4 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 6.25 / 30 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| thorium | 67.5 | 0 | 0.85 | 31.37 | 2117.6 | 2117.6 | 31.37 | 1427.5 | 00-data |
| surge-alloy | 48.75 | 0 | 0.75 | 35.56 | 1733.3 | 1733.3 | 11.85 | 951.1 | 00-data |
| tungsten | 48.75 | 0 | 1.00 | 26.67 | 1300.0 | 1300.0 | 8.89 | 713.3 | 00-data |
| silicon | 27.75 | 0 | 1.00 | 26.67 | 740.0 | 740.0 | 6.67 | 153.3 | 00-data |

- 面板 = 单体（无溅射）；四管是轮转不是四连发，射速口径按 31.37 发/s 看 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4840 —— 定义行 new ItemTurret("disperse")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5001 —— 含 ShootAlternate
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5003 —— 含 shots / 4
- Mindustry-Source/core/src/mindustry/content/Blocks.java:5004 —— 含 barrels / 4
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29
- 00-data/turret_shots.json#id=disperse —— 源码派生记录（含证据行）

## 实测与反例

- 反例：拿 disperse 顶地面波次，targetGround False 让它整场 0 输出 [src: 00-data/turrets.json]
- 反例：只喂 silicon 打重甲飞行单位，对 22 甲 153.3 DPS 是 thorium 的 10.7%；复现看 对22甲 列 1427.5 与 153.3 [src: 00-data/turrets.json]

## 常见误解

- 「AA 塔打甲无所谓」错：thorium 对 22 甲保留 67%，silicon 只剩 21% [src: 00-data/turrets.json]
- 「shots 4 是四连发」错：ShootAlternate 是四管轮转，31.37 发/s 是总射速 [src: 00-data/turrets.json]
- 「surge 一定最强」错：surge DPS 比 thorium 低 18%，它买的是更低吞吐（11.85 件/s） [src: 00-data/turrets.json]

## 相关

- [[COMBAT.TURRET.102]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.204]]
- [[COMBAT.TURRET.206]]
