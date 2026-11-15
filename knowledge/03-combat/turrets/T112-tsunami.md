---
tokens: 621
id: COMBAT.TURRET.112
title: tsunami —— 双管液体泼洒器
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3850"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/tsunami"
  - "jar:v160.7#blocks/tsunami"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, tsunami, 液体双管 / 减益与清杂]
---

## 一句话

tsunami 是 wave 的放大版：双管、每触发 2 发、reload 3 tick，20 触发/s 的液体弹幕，slag 模式下 95 DPS，是液体塔里唯一能算输出的。它的问题是成本——850 件 + 每发 2.5 单位液体的消耗，以及 190 世界单位（23.75 格）的射界，注定它是核心区防线而不是前线塔。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：B ｜ **岗位**：液体双管 / 减益与清杂
- **射击模式**：ShootAlternate(4f)（每触发 2 发；reload 3 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 每触发 2 发（shots 2，ShootAlternate 双管交替），reload 3 tick ⇒ 约 20 触发/s [src: 00-data/turrets.json]
- 弹药是液体：water 单发 0.2、slag 4.75、cryofluid 0.2、oil 0.2；每发消耗 2.5 单位液体，20 触发/s 即 50 液体/s [src: 00-data/turrets.json]
- 四种液体的分工与 wave 一致：water/cryofluid 灭火、cryofluid 冻结、oil 上油、slag 是唯一有实伤的选项 [src: 00-data/turrets.json]
- 空陆都打，是液体塔里少见的通用目标层
- **优点**：
  - slag 模式 95 DPS，是液体塔里唯一能当输出用的选项 [src: 00-data/turrets.json]
  - 20 触发/s 的密度让减益（冻结/上油/灭火）覆盖极快，比 wave 更快铺满
  - 2250 血量 + 3×3 占地，比 wave 耐打得多，能架在前排一点的位置
- **缺点**：
  - 850 件造价 + 50 液体/s 的消耗，供给链成本远超同 DPS 的固体弹药塔 [src: 00-data/turrets.json]
  - 95 DPS 在 405 件的 cyclone（415.5 面板）面前毫无竞争力，它只为减益存在 [src: 00-data/turrets.json]
  - 23.75 格的射界限制它只能护核心，护不到外圈 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 3 | 00-data/blocks.json |
| 血量 | 2250 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 850 件（lead × 400、metaglass × 100、titanium × 250、thorium × 100） | 00-data/blocks.json |
| 射程 | 190 世界单位（23.75 格） | 00-data/turrets.json |
| reload | 3 tick | 00-data/turrets.json |
| shots | 2 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 5 / 45 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 单发伤害 | 发/s | 0甲 DPS | ammoMultiplier | 来源 |
|---|---|---|---|---|---|
| water | 0.2 | 20 | 4 | 0.4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3857 |
| slag | 4.75 | 20 | 95 | 0.4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3858 |
| cryofluid | 0.2 | 20 | 4 | 0.4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3859 |
| oil | 0.2 | 20 | 4 | 0.4 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3860 |

- ammoMultiplier 0.4 ⇒ 每发消耗 2.5 单位液体，20 发/s 就是 50 液体/s，供液压力远大于 wave。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3850]
- shots=2（ShootAlternate 双管交替），所以 0甲 DPS 是 2 × 20 × 单发伤害。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3850]

- 事实卡 tsunami 表：slag 单发 4.75、0 甲 DPS 95；按 20 × 4.75 复算正好 95，与本表一致（若把双管各算一发会得到 190，本库不采用该口径） [src: 00-data/turrets.json]
- 每发 2.5 单位液体 × 20 触发/s = 50 液体/s，是规划管道时最该记住的数字 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3850 —— 定义行 new LiquidTurret("tsunami")
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3902 —— 含 ShootAlternate
- Mindustry-Source/core/src/mindustry/content/Blocks.java:3903 —— 含 shots / 2
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29
- 00-data/turret_shots.json#id=tsunami —— 源码派生记录（含证据行）

## 实测与反例

- 反例：拿 tsunami 当主力输出，95 DPS 不及一门 duo 石墨（67.5）的 1.5 倍，却贵 24 倍；复现：00-data/turrets.json 里 tsunami 的 MANUAL 表与 duo 对比 [src: 00-data/turrets.json]
- 反例：以为双管=双倍 DPS，表里 95 与 190 的差别正是「按触发算还是按管算」，本库统一按触发算；复现：gen_turrets.py 的 MANUAL tsunami 表 notes [src: 00-data/turrets.json]

## 常见误解

- 「液体塔伤害低所以没用」错：tsunami 的产出是冻结/上油/灭火这些减益，不是 DPS
- 「双管射速翻倍」错：shots 2 是每触发两发，触发频率本身由 reload 决定

## 相关

- [[COMBAT.TURRET.105]]
- [[COMBAT.TURRET.118]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.111]]
- [[COMBAT.TURRET.113]]
