---
tokens: 670
id: COMBAT.TURRET.203
title: sublimate —— 每结算 130 的液体喷灯
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:4553"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/sublimate"
  - "jar:v160.7#blocks/sublimate"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, sublimate, 持续火焰 / 换弹换射程]
---

## 一句话

sublimate 解决「持续灼烧 + 一条火线烧穿几个目标」，不是「爆发点杀」：ozone 每结算 60 给 720 DPS，换 cyanogen 每结算 130 直接翻到 1560，还附赠 rangeChange +70 与 pierceCap 3。代价是 18/s 的液体双层供给，以及不换 cyanogen 时 130 世界单位（16.25 格）的短射界。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4570]

## 规则 / 公式

- **层位**：A ｜ **岗位**：持续火焰 / 换弹换射程
- **射击模式**：连续火焰（每触发 1 发；reload 10 tick） [src: 00-data/turret_shots.json]
- **目标层**：空中、地面、建筑
- 连续火焰型，damageInterval 5 tick ⇒ ×12 结算；ozone 每结算 60 → 720 DPS，cyanogen 130 → 1560 DPS [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4570]
- cyanogen 自带 rangeChange +70，把射程从 130 拉到 200 世界单位（25 格），是少数换弹药换射界的塔 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- pierceCap 2（ozone）/ 3（cyanogen）：一条火线能同时烧穿多个单位，密集队形下实际输出高于单体口径 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- 液体消耗 18/s，比物品塔更吃管道：断液即停火，不存在「打空弹匣」 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4553]
- 对 22 甲：ozone 每结算 60 剩 38（63%）、cyanogen 每结算 130 剩 108（83%）——单发越高，护甲惩罚越轻 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- **优点**：
  - 1560 DPS + 穿透 3，是 Erekir 持续输出最高的塔之一，清重甲群不靠弹幕密度靠灼烧 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
  - 换 cyanogen 自带 +70 射程，等于用弹药换了半门新塔 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
  - 连续型不吃弹道与命中判定，目标在射界内就一直结算，数字极稳 [src: 00-data/turrets.json]
- **缺点**：
  - 18/s 液体 + 电力/冷却，双层供给，一条管线断了整塔停摆 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4570]
  - ozone 曲线只有 720 DPS，换不起 cyanogen 时它只是中游塔 [src: 00-data/turrets.json]
  - 不换 cyanogen 时 130 世界单位（16.25 格）太短，够不到远程波次 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4553]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 3 | 00-data/blocks.json |
| 血量 | 1890 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 790 件（silicon × 200、beryllium × 400、tungsten × 150、oxide × 40） | 00-data/blocks.json |
| 射程 | 130 世界单位（16.25 格） | 00-data/turrets.json |
| reload | 10 tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 1 / 8 | 00-data/turrets.json |
| 耗电 | 0/s | 00-data/turrets.json |

| 弹药 | 每结算伤害 | 0甲 DPS | 特殊 | 来源 |
|---|---|---|---|---|
| ozone | 60 | 720 | ammoMultiplier 1.2、pierceCap 2 | Mindustry-Source/core/src/mindustry/content/Blocks.java:4570 |
| cyanogen | 130 | 1560 | rangeChange +70、pierceCap 3 | Mindustry-Source/core/src/mindustry/content/Blocks.java:4576 |

- 连续火焰型（damageInterval 5 tick，×12 结算）；液体消耗 18/s，是双层供给（弹药液体 + 电力/冷却）。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4553]
- cyanogen 的 rangeChange +70 会实打实延长射界，是少数「换弹药换射程」的塔。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4553]

- 本库不给「对 22 甲」列（连续型没有 ammo[] 反射表），63% / 83% 是按每结算伤害套 max(d−22, 0.1d) 算的，口径见 [[COMBAT.NUMBERS.001]] [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:4553 —— 定义行 new ContinuousLiquidTurret("sublimate")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- 00-data/turret_shots.json#id=sublimate —— 源码派生记录（含证据行）

## 实测与反例

- 反例：把 sublimate 摆在 130 世界单位射界内等敌人走进来，敌人停在 200 格外时它 0 输出；换 cyanogen 才够到 200 世界单位 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- 反例：按 18/s 液体配半条管线，1560 DPS 会按供给比例线性缩水，不是「少一点」 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4570]

## 常见误解

- 「火焰塔对护甲无效」错：它走普通直伤结算，cyanogen 对 22 甲仍保留 83% [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]
- 「720 DPS 是它的上限」错：ozone 只是零头，cyanogen 才是主曲线，两者差 2.17 倍 [src: 00-data/turrets.json]
- 「换弹只换伤害」错：cyanogen 同时换射程 +70、pierceCap 3，是三维升级 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:4576]

## 相关

- [[COMBAT.TURRET.118]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.202]]
- [[COMBAT.TURRET.204]]
