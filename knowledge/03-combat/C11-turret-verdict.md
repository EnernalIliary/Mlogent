---
tokens: 821
id: COMBAT.TURRET.002
title: 原版炮塔评价总览与选型决策表（28 台逐台索引）
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: I
src:
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3258"
data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]
depends: [COMBAT.TURRET.001, COMBAT.NUMBERS.001]
tags: [炮塔, 评价, 选型, 索引]
---

## 一句话

28 门炮塔要按「层位（拿到手的时代）」和「岗位（你缺什么）」两个维度选，而不是按单体 DPS 排名：同层位里 DPS 最高的塔往往最吃供给、最吃位置，而低 DPS 的塔常常是唯一能解决某个具体问题的。

## 规则 / 公式

- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤，只算一个目标、零护甲、不冷却、不卡供给。它不是实战输出，是可比价。
- **层位字母**：S=长期一线主力 ｜ A=强但专用（特定敌人/局面才上）｜ B=过渡或补充 ｜ C=只在特定场合 ｜ D=有更好选择。这是按「长期战役里值不值得造」给的判断，不是数值排名。
- **护甲修正**：对 A 甲目标换成 60/(reload × rm) × shots × max(直伤 − A, 0.1 × 直伤)（minArmorDamage 0.1，见 [[COMBAT.TURRET.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]
- **供给约束**：物品/秒 列是满射速时的弹药消耗，超过产能就自动降频，所以「DPS/物品」这一列才决定持续输出。
- **层位不等于强度**：Serpulo 与 Erekir 是两套独立科技线，跨线比数字没有意义。

## 数值

| 塔 | 层位 | 岗位 | 最佳弹药 | 单体DPS(0甲) | 造价(件) | DPS/件 | 射程(格) | 目标 | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| COMBAT.TURRET.101 duo | B | 早期万金油 / 便宜的连发基线 | graphite | 67.5 | 35 | 1.93 | 20.0 | 空地 | 00-data |
| COMBAT.TURRET.102 scatter | B | 近程防空 / 清弹幕 | scrap | 40.0 | 130 | 0.31 | 27.5 | 空 | 00-data |
| COMBAT.TURRET.103 scorch | C | 贴脸火墙 / 熔断近战 | pyratite | 300.0 | 47 | 6.38 | 7.5 | 地 | 00-data |
| COMBAT.TURRET.104 hail | B | 早期曲射 / 群体压制 | pyratite | 25.0 | 57 | 0.44 | 29.4 | 地 | 00-data |
| COMBAT.TURRET.105 wave | A | 状态控制 / 灭火与击退 | 液体/特殊 | 见正文 | 145 | - | 13.8 | 空地 | 00-data |
| COMBAT.TURRET.106 lancer | A | 反重甲 / 单发穿透 | 液体/特殊 | 见正文 | 220 | - | 20.6 | 地 | 00-data |
| COMBAT.TURRET.107 arc | B | 链式电击 / 打断控制 | 液体/特殊 | 见正文 | 100 | - | 11.2 | 地 | 00-data |
| COMBAT.TURRET.108 parallax | A | 空中位移控制 / 拉近（把目标拽向自己） | 液体/特殊 | 见正文 | 320 | - | 37.5 | 空 | 00-data |
| COMBAT.TURRET.109 swarmer | A | 导弹群伤 / 中程防空 | surge-alloy | 126.0 | 145 | 0.87 | 30.0 | 空地 | 00-data |
| COMBAT.TURRET.110 salvo | A | 中期主力 / 连发点杀 | graphite | 320.7 | 230 | 1.39 | 23.8 | 空地 | 00-data |
| COMBAT.TURRET.111 segment | A | 弹体拦截 / 防空清弹 | 液体/特殊 | 见正文 | 290 | - | 22.5 | - | 00-data |
| COMBAT.TURRET.112 tsunami | B | 液体双管 / 减益与清杂 | 液体/特殊 | 见正文 | 850 | - | 23.8 | 空地 | 00-data |
| COMBAT.TURRET.113 fuse | S | 近程终局 / 反重甲爆发 | thorium | 540.0 | 550 | 0.98 | 11.2 | 空地 | 00-data |
| COMBAT.TURRET.114 ripple | A | 远程曲射压制 | pyratite | 96.0 | 345 | 0.28 | 36.2 | 地 | 00-data |
| COMBAT.TURRET.115 cyclone | A | 防空群伤 / 中程弹幕 | surge-alloy | 78.0 | 405 | 0.19 | 25.0 | 空地 | 00-data |
| COMBAT.TURRET.116 foreshadow | A | 超远程狙击 / 反重甲先手 | surge-alloy | 405.0 | 2700 | 0.15 | 62.5 | 空地 | 00-data |
| COMBAT.TURRET.117 spectre | S | 后期主力 / 全能点杀 | thorium | 685.7 | 1875 | 0.37 | 32.5 | 空地 | 00-data |
| COMBAT.TURRET.118 meltdown | S | 近程持续激光 / 高耗电清场 | 液体/特殊 | 见正文 | 2500 | - | 24.4 | 空地 | 00-data |
| COMBAT.TURRET.201 breach | B | 开局主力 / 高单发速射 | carbide | 2437.5 | 425 | 5.74 | 23.8 | 空地 | 00-data |
| COMBAT.TURRET.202 diffuse | B | 近程清群 / 15 发散射 | oxide | 2025.0 | 600 | 3.38 | 15.6 | 空地 | 00-data |
| COMBAT.TURRET.203 sublimate | A | 持续火焰 / 换弹换射程 | 液体/特殊 | 见正文 | 790 | - | 16.2 | 空地 | 00-data |
| COMBAT.TURRET.204 titan | A | 长程炮击 / 只打地面 | carbide | 285.3 | 950 | 0.30 | 48.8 | 地 | 00-data |
| COMBAT.TURRET.205 disperse | A | 专职防空 / 四管高射 | thorium | 2117.6 | 650 | 3.26 | 38.8 | 空 | 00-data |
| COMBAT.TURRET.206 afflict | B | 中口径电塔 / 穿刺射击 | 液体/特殊 | 见正文 | 590 | - | 46.0 | 空地 | 00-data |
| COMBAT.TURRET.207 lustre | A | 全向点杀 / 最强目标优先 | 液体/特殊 | 见正文 | 590 | - | 31.2 | 空地 | 00-data |
| COMBAT.TURRET.208 scathe | A | 跨屏导弹 / 战略打击 | phase-fabric | 0.0 | 1650 | 0.00 | 168.8 | 地 | 00-data |
| COMBAT.TURRET.209 smite | S | 后期主炮 / 五管重击 | surge-alloy | 562.5 | 2200 | 0.26 | 37.5 | 空地 | 00-data |
| COMBAT.TURRET.210 malign | S | 终局弹幕 / 覆盖式压制 | 液体/特殊 | 见正文 | 2400 | - | 51.2 | 空地 | 00-data |

## 源码锚点

- Mindustry-Source/core/src/mindustry/content/Blocks.java —— 28 台塔的定义、shootType 与弹药表
- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1
- Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414 —— estimateDPS（面板口径）
- 00-data/turret_shots.json —— 源码派生的 shots/pattern 表（jar 反射拿不到）

## 实测与反例

- 只看单体 DPS 会得出「breach 2437.5 最强」的结论，但 breach 用 carbide 时 7.5 发/s × 2 件 = 15 件/s，一条满速传送带（11 件/s）根本喂不满；掐掉供给后它与 300 件的塔没区别。 [src: 00-data/turrets.json + 00-data/blocks.json]
- 反向例子：wave 的 0 甲 DPS 是 0（water 无伤），但它是唯一能灭火、能击退的塔，在燃烧/近战波次里的价值无法用 DPS 表达。

## 常见误解

- 「造价越贵越强」：foreshadow 造价 2700 件、单体 405 DPS；spectre 1875 件就有 685.7 DPS。贵的部分买的是射程与穿甲，不是数字。 [src: 00-data/turrets.json]
- 「口径可以混用」：旧表格混过「单发伤害」与「每发伤害 × 发数」，同一张表里 duo 27 与 salvo 31 不可比。本库统一按上面的口径重算，旧数字作废。

## 相关

- [[COMBAT.TURRET.001]] 炮塔机制（reload / 冷却液 / 过热 / 目标层）
- [[COMBAT.NUMBERS.001]] DPS 三式与三层口径
- [[COMBAT.TURRET.101]] duo
- [[COMBAT.TURRET.102]] scatter
- [[COMBAT.TURRET.103]] scorch
- [[COMBAT.TURRET.104]] hail
- [[COMBAT.TURRET.105]] wave
- [[COMBAT.TURRET.106]] lancer
- [[COMBAT.TURRET.107]] arc
- [[COMBAT.TURRET.108]] parallax
- [[COMBAT.TURRET.109]] swarmer
- [[COMBAT.TURRET.110]] salvo
- [[COMBAT.TURRET.111]] segment
- [[COMBAT.TURRET.112]] tsunami
- [[COMBAT.TURRET.113]] fuse
- [[COMBAT.TURRET.114]] ripple
- [[COMBAT.TURRET.115]] cyclone
- [[COMBAT.TURRET.116]] foreshadow
- [[COMBAT.TURRET.117]] spectre
- [[COMBAT.TURRET.118]] meltdown
- [[COMBAT.TURRET.201]] breach
- [[COMBAT.TURRET.202]] diffuse
- [[COMBAT.TURRET.203]] sublimate
- [[COMBAT.TURRET.204]] titan
- [[COMBAT.TURRET.205]] disperse
- [[COMBAT.TURRET.206]] afflict
- [[COMBAT.TURRET.207]] lustre
- [[COMBAT.TURRET.208]] scathe
- [[COMBAT.TURRET.209]] smite
- [[COMBAT.TURRET.210]] malign
