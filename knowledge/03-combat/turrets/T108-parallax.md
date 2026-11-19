---
tokens: 573
id: COMBAT.TURRET.108
title: parallax —— 16 牵引力的空中拉手
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3641"
  - "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"
  # ver: v160.7_rt  # jar 反射取值（运行值口径）
  - "jar:v160.7#turrets/parallax"
  - "jar:v160.7#blocks/parallax"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]
tags: [炮塔, parallax, 空中位移控制 / 拉近]
---

## 一句话

parallax 不是杀伤塔，是位移塔：只打空中，用 16 的基础牵引力把飞行单位**往自己这里拽**，附带的伤害只有 30/s。它解决的是「飞行单位贴脸拆核心」——把目标从核心区拖走、拖进别的塔的射界，代价是它自己几乎不产生击杀；把它当防空 DPS 用会非常失望。 [src: 00-data/turrets.json]

## 规则 / 公式

- **层位**：A ｜ **岗位**：空中位移控制 / 拉近（把目标拖向自己）
- **射击模式**：无射击循环（持续牵引）（每触发 1 发；无 reload（连续型/牵引型）） [src: 00-data/turret_shots.json]
- **目标层**：空中
- 只打空中（targetAir 为真、targetGround 为假），射界 300 世界单位（37.5 格）是防空塔里最远的 [src: 00-data/turrets.json]
- 牵引力 16、随距离缩放的分量 9，**越近越强**：冲量方向是 `炮塔位置 − 目标位置`，所以核心效果是把目标拖向自己，而不是打掉 [src: Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/TractorBeamTurret.java:133]
- 附带的伤害是 0.5/tick，换算 30/s——这个数字只是附赠，不足以击杀任何中后期单位 [src: 00-data/turrets.json]
- 耗电 198/s；它必须与真正的输出塔配对，单独成线等于没有输出 [src: 00-data/turrets.json]
- **优点**：
  - 37.5 格的射界让它能在很远的地方就开始施力：飞行单位一进 37.5 格就被拖向炮塔，等于把它们从核心区拽走 [src: 00-data/turrets.json]
  - 对飞行单位是「钩子」：拉近会把轰炸机/投弹单位从投弹位置上拽偏，压制效果远大于 30/s 的伤害 [src: 00-data/turrets.json]
  - 只占一个塔位就能显著改变空投波的落点
- **缺点**：
  - 30/s 的伤害意味着它几乎不能独立完成击杀，必须配输出塔 [src: 00-data/turrets.json]
  - 对地面单位完全无效，地面波次里它是纯白板
  - 198/s 的耗电换来的不是杀伤，规划时容易被误判为「防空塔」 [src: 00-data/turrets.json]
- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]

## 数值

| 项 | 值 | 来源 |
|---|---|---|
| 尺寸 | 2 | 00-data/blocks.json |
| 血量 | 640 | 00-data/blocks.json |
| 护甲 | 0 | 00-data/blocks.json |
| 造价 | 320 件（graphite × 50、titanium × 110、silicon × 160） | 00-data/blocks.json |
| 射程 | 300 世界单位（37.50 格） | 00-data/turrets.json |
| reload | — tick | 00-data/turrets.json |
| shots | 1 | 00-data/turret_shots.json |
| 冷却液倍率 / shootCone | 1 / 6 | 00-data/turrets.json |
| 耗电 | 198/s | 00-data/turrets.json |

| 项 | 值 | 说明 | 来源 |
|---|---|---|---|
| force | 16 | 牵引力 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3642 |
| scaledForce | 9 | 随距离缩放 | Mindustry-Source/core/src/mindustry/content/Blocks.java:3643 |
| damage | 0.5/tick | setStats 显示 ×60 = 30/s | Mindustry-Source/core/src/mindustry/content/Blocks.java:3644 |
| 耗电 | 198/s | | Mindustry-Source/core/src/mindustry/content/Blocks.java:3653 |

- 只打空中（targetAir=true, targetGround=false），冲量 `Tmp.v1.set(this).sub(target)` 指向炮塔，即把飞行单位往自己这里拽；越近附加项 `(1 − d/range) × scaledForce` 越大。是位移控制而非杀伤。 [src: Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/TractorBeamTurret.java:133]
- 30/s 的伤害只是附赠，指望它击落是误用。 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:3641]

- 本库不给 parallax 算 DPS 排名：30/s 是附带伤害，它的产出是位移量（牵引力 16），两者不可换算 [src: 00-data/turrets.json]

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java:3641 —— 定义行 new TractorBeamTurret("parallax")
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）
- Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/TractorBeamTurret.java:133 —— `target.impulseNet(Tmp.v1.set(this).sub(target).limit((force + (1f - target.dst(this) / range) * scaledForce) * edelta))`，冲量指向炮塔 = 拉近
- 00-data/turret_shots.json#id=parallax —— 源码派生记录（含证据行）

## 实测与反例

- 反例：用 parallax 单独守空投，30/s 打不掉任何中后期飞行单位，只能拖延；复现：gen_turrets.py 的 MANUAL parallax 表（force 16 / damage 0.5 per tick） [src: 00-data/turrets.json]
- 反例：把它摆在地面波次路线上，targetGround 为假，整波零输出；复现：00-data/turrets.json 里 parallax 的 targetGround 字段 [src: 00-data/turrets.json]

## 常见误解

- 「parallax 是防空炮」错：它是位移工具，击杀要靠别的塔
- 「牵引力越大伤害越高」错：force 16 与 0.5/tick 是两套独立参数 [src: 00-data/turrets.json]
- 「parallax 把单位推开」错：冲量方向是「炮塔 − 目标」，它是**拉近**，而且越近越强 [src: Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/TractorBeamTurret.java:133]

## 相关

- [[COMBAT.TURRET.109]]
- [[COMBAT.TURRET.115]]
- [[COMBAT.TURRET.001]]
- [[COMBAT.TURRET.002]]
- [[COMBAT.NUMBERS.001]]
- [[COMBAT.TURRET.107]]
