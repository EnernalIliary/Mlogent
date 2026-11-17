# rt_verify 重跑结果（机器生成）

- 时间：2026-11-08 05:40:08
- 环境：v160.7 真服务器（out/_server160.jar + out/jre21），起服 2.30s，反射 1.06s，总 3.43s
- 说明：①②③ 组的文章值由「实体名 + 字段名」在正文里现场定位（不按行号；括号注「类默认/旧值/源码」不当断言），④⑤⑥ 组直接解析 markdown 表；jar 值每次现场反射。
- 判定：PASS 数值一致；FAIL 文章值错；口径差 jar 无对应字段或浮点取整/单位口径不同。

## ① CHEAT.md 数值表（26 条：PASS 26 / FAIL 0 / 口径差 0）

| # | 检查 | 出处 | 文章定位 | 文章值 | jar 值 | 判定 |
|---|---|---|---|---|---|---|
| ①-1 | tile = 8 px（tilesize） | 08-evidence/CHEAT.md | L94 | 8.0 | 8 | PASS |
| ①-2 | print 文本上限 150 | 08-evidence/CHEAT.md | L100 | 150.0 | 150 | PASS |
| ①-3 | 单次执行上限 1000 行 | 08-evidence/CHEAT.md | L100 | 1000.0 | 1000 | PASS |
| ①-4 | print 缓冲 400 字符 | 08-evidence/CHEAT.md | L100 | 400.0 | 400 | PASS |
| ①-5 | turnDuration 7200 | 08-evidence/CHEAT.md | L105 | 7200.0 | 7200 | PASS |
| ①-6 | 入侵宽限 20 分钟 | 08-evidence/CHEAT.md | L106 | 20.0 | 20 | PASS |
| ①-7 | 入侵概率基数 1/100 | 08-evidence/CHEAT.md | L107 | 0.01 | 0.01 | PASS |
| ①-8 | 护甲保底 0.1D | 08-evidence/CHEAT.md | L114 | 0.1 | 0.1 | PASS |
| ①-9 | memory-cell 64 格（类默认 32 被覆盖） | 08-evidence/CHEAT.md | L101 | 64.0 | 64 | PASS |
| ①-10 | memory-bank 512 格 | 08-evidence/CHEAT.md | L101 | 512.0 | 512 | PASS |
| ①-11 | waveSpacing 7200 | 08-evidence/CHEAT.md | L103 | 7200.0 | 7200 | PASS |
| ①-12 | Serpulo 发射倍率 0.5 | 08-evidence/CHEAT.md | L108 | 0.5 | 0.5 | PASS |
| ①-13 | erekir 发射倍率 0.25 | 08-evidence/CHEAT.md | L108 | 0.25 | 0.25 | PASS |
| ①-14 | core-shard 容量 4000 | 08-evidence/CHEAT.md | L109 | 4000.0 | 4000 | PASS |
| ①-15 | core-foundation 容量 9000 | 08-evidence/CHEAT.md | L109 | 9000.0 | 9000 | PASS |
| ①-16 | core-nucleus 容量 13000 | 08-evidence/CHEAT.md | L109 | 13000.0 | 13000 | PASS |
| ①-17 | 核心单位上限 +8 | 08-evidence/CHEAT.md | L110 | 8.0 | 8 | PASS |
| ①-18 | 核心单位上限 +16 | 08-evidence/CHEAT.md | L110 | 16.0 | 16 | PASS |
| ①-19 | 核心单位上限 +24 | 08-evidence/CHEAT.md | L110 | 24.0 | 24 | PASS |
| ①-20 | micro ipt 2（点/tick） | 08-evidence/CHEAT.md | L97 | 2.0 | 2 | PASS |
| ①-21 | logic ipt 8（点/tick） | 08-evidence/CHEAT.md | L97 | 8.0 | 8 | PASS |
| ①-22 | hyper ipt 25（点/tick） | 08-evidence/CHEAT.md | L97 | 25.0 | 25 | PASS |
| ①-23 | 单 tick 上限 40（micro） | 08-evidence/CHEAT.md | L99 | 40.0 | 40 | PASS |
| ①-24 | 单 tick 上限 40（logic） | 08-evidence/CHEAT.md | L99 | 40.0 | 40 | PASS |
| ①-25 | 单 tick 上限 40（hyper） | 08-evidence/CHEAT.md | L99 | 40.0 | 40 | PASS |
| ①-26 | world 单次上限 1000 | 08-evidence/CHEAT.md | L98 | 1000.0 | 1000 | PASS |

## ② C10 DPS/TTK（14 条：PASS 14 / FAIL 0 / 口径差 0）

| # | 检查 | 出处 | 文章定位 | 文章值 | jar 值 | 判定 |
|---|---|---|---|---|---|---|
| ②-1 | dagger 2×26 → 41.5 | 03-combat/C10-numbers.md | L69 | 41.5 | 41.54 | PASS |
| ②-2 | mace 2×44 → 201.8 | 03-combat/C10-numbers.md | L59 | 201.8 | 201.82 | PASS |
| ②-3 | toxopid 主武器 2×60 → 440.0（含 shots 2） | 03-combat/C10-numbers.md | L71 | 440.0 | 440.0 | PASS |
| ②-4 | toxopid 含副炮 → 454.3 | 03-combat/C10-numbers.md | L76 | 454.3 | 454.29 | PASS |
| ②-5 | reign 2×18 → 533.3 | 03-combat/C10-numbers.md | L60 | 533.3 | 533.33 | PASS |
| ②-6 | omura 1×110 → 681.8 | 03-combat/C10-numbers.md | L73 | 681.8 | 681.82 | PASS |
| ②-7 | corvus 1×350 → 96.0 | 03-combat/C10-numbers.md | L74 | 96.0 | 96.0 | PASS |
| ②-8 | spectre vs toxopid TTK 91.67 | 03-combat/C10-numbers.md | L101 | 91.67 | 91.67 | PASS |
| ②-9 | duo vs toxopid TTK 8148.15 | 03-combat/C10-numbers.md | L102 | 8148.15 | 8148.15 | PASS |
| ②-10 | meltdown vs toxopid TTK 32.74 | 03-combat/C10-numbers.md | L98 | 32.74 | 32.74 | PASS |
| ②-11 | scorch vs toxopid TTK 1294.12 | 03-combat/C10-numbers.md | L87 | 1294.12 | 1294.12 | PASS |
| ②-12 | salvo vs toxopid TTK 7088.89 | 03-combat/C10-numbers.md | L88 | 7088.89 | 7088.89 | PASS |
| ②-13 | cyclone vs toxopid TTK 6111.11 | 03-combat/C10-numbers.md | L89 | 6111.11 | 6111.11 | PASS |
| ②-14 | hail 实战 DPS 20 | 03-combat/C10-numbers.md | L56 | 20.0 | 20.0 | PASS |

## ③ W06/W07 物流·钻头（41 条：PASS 41 / FAIL 0 / 口径差 0）

| # | 检查 | 出处 | 文章定位 | 文章值 | jar 值 | 判定 |
|---|---|---|---|---|---|---|
| ③-1 | conveyor speed 0.035 格/tick | 02-world/W06-logistics.md | L111 | 0.035 | 0.035 | PASS |
| ③-2 | titanium-conveyor speed 0.0801 | 02-world/W06-logistics.md | L112 | 0.0801 | 0.0801 | PASS |
| ③-3 | armored-conveyor speed 0.08 | 02-world/W06-logistics.md | L113 | 0.08 | 0.08 | PASS |
| ③-4 | plastanium speed 0.0667 | 02-world/W06-logistics.md | L114 | 0.0667 | 0.0667 | PASS |
| ③-5 | surge speed 0.0833 | 02-world/W06-logistics.md | L115 | 0.0833 | 0.0833 | PASS |
| ③-6 | duct speed 4（tick/件） | 02-world/W06-logistics.md | L116 | 4.0 | 4 | PASS |
| ③-7 | junction speed 26 | 02-world/W06-logistics.md | L40 | 26.0 | 26 | PASS |
| ③-8 | junction displayedSpeed 13 | 02-world/W06-logistics.md | L40 | 13.0 | 13 | PASS |
| ③-9 | router speed 8 | 02-world/W06-logistics.md | L41 | 8.0 | 8 | PASS |
| ③-10 | bridge range 4 | 02-world/W06-logistics.md | L83 | 4.0 | 4 | PASS |
| ③-11 | bridge buffer 14 | 02-world/W06-logistics.md | L83 | 14.0 | 14 | PASS |
| ③-12 | bridge speed 74 | 02-world/W06-logistics.md | L83 | 74.0 | 74 | PASS |
| ③-13 | bridge displayedSpeed 11 | 02-world/W06-logistics.md | L83 | 11.0 | 11 | PASS |
| ③-14 | phase-conveyor range 12 | 02-world/W06-logistics.md | L85 | 12.0 | 12 | PASS |
| ③-15 | phase-conveyor transportTime 2 | 02-world/W06-logistics.md | L85 | 2.0 | 2 | PASS |
| ③-16 | mass-driver range 440 | 02-world/W06-logistics.md | L89 | 440.0 | 440 | PASS |
| ③-17 | mass-driver reload 200 | 02-world/W06-logistics.md | L89 | 200.0 | 200 | PASS |
| ③-18 | mass-driver minDistribute 10 | 02-world/W06-logistics.md | L89 | 10.0 | 10 | PASS |
| ③-19 | unloader speed 5.4545 | 02-world/W06-logistics.md | L100 | 5.4545 | 5.4545 | PASS |
| ③-20 | duct-unloader speed 4 | 02-world/W06-logistics.md | L101 | 4.0 | 4 | PASS |
| ③-21 | mechanical drillTime 600 | 02-world/W07-drills-resources.md | L92 | 600.0 | 600 | PASS |
| ③-22 | pneumatic drillTime 400 | 02-world/W07-drills-resources.md | L92 | 400.0 | 400 | PASS |
| ③-23 | laser drillTime 280 | 02-world/W07-drills-resources.md | L159 | 280.0 | 280 | PASS |
| ③-24 | blast drillTime 280 | 02-world/W07-drills-resources.md | L160 | 280.0 | 280 | PASS |
| ③-25 | impact drillTime 720 | 02-world/W07-drills-resources.md | L130 | 720.0 | 720 | PASS |
| ③-26 | eruption drillTime 281.25 | 02-world/W07-drills-resources.md | L162 | 281.25 | 281.25 | PASS |
| ③-27 | plasma-bore 160 | 02-world/W07-drills-resources.md | L163 | 160.0 | 160 | PASS |
| ③-28 | large-plasma-bore 100 | 02-world/W07-drills-resources.md | L164 | 100.0 | 100 | PASS |
| ③-29 | cliff-crusher 110 | 02-world/W07-drills-resources.md | L165 | 110.0 | 110 | PASS |
| ③-30 | large-cliff-crusher 48 | 02-world/W07-drills-resources.md | L166 | 48.0 | 48 | PASS |
| ③-31 | hardnessDrillMultiplier 50（mechanical） | 02-world/W07-drills-resources.md | L58 | 50.0 | 50 | PASS |
| ③-32 | impact hardnessDrillMultiplier 0 | 02-world/W07-drills-resources.md | L21 | 0.0 | 0 | PASS |
| ③-33 | laser 耗电 1.1/tick | 02-world/W07-drills-resources.md | L159 | 1.1 | 1.1 | PASS |
| ③-34 | blast 耗电 3/tick | 02-world/W07-drills-resources.md | L160 | 3.0 | 3 | PASS |
| ③-35 | impact 耗电 2.6667/tick | 02-world/W07-drills-resources.md | L161 | 2.667 | 2.6667 | PASS |
| ③-36 | eruption 耗电 6/tick | 02-world/W07-drills-resources.md | L162 | 6.0 | 6 | PASS |
| ③-37 | plasma-bore 0.15/tick | 02-world/W07-drills-resources.md | L163 | 0.15 | 0.15 | PASS |
| ③-38 | large-plasma-bore 0.8/tick | 02-world/W07-drills-resources.md | L164 | 0.8 | 0.8 | PASS |
| ③-39 | cliff-crusher 0.1833/tick | 02-world/W07-drills-resources.md | L165 | 0.1833 | 0.1833 | PASS |
| ③-40 | large-cliff-crusher 1/tick | 02-world/W07-drills-resources.md | L166 | 1.0 | 1 | PASS |
| ③-41 | mechanical 液体加速 1.6 | 02-world/W07-drills-resources.md | L157 | 1.6 | 1.6 | PASS |

## ④ C02 炮塔表（解析文章原表）（28 条：PASS 25 / FAIL 0 / 口径差 3）

| # | 对象 | 判定 | 差异 |
|---|---|---|---|
| ④-1 | duo | PASS |  |
| ④-2 | scatter | PASS |  |
| ④-3 | scorch | PASS |  |
| ④-4 | hail | PASS |  |
| ④-5 | wave | PASS |  |
| ④-6 | lancer | PASS |  |
| ④-7 | arc | PASS |  |
| ④-8 | parallax | 口径差 | reload: 文章=0 / jar 无字段；inacc: 文章=0 / jar 无字段；maxAmmo: 文章=0 / jar 无字段；ammoPerShot: 文章=0 / jar 无字段 |
| ④-9 | swarmer | 口径差 | reload: 文章=34 / jar=34.2857 |
| ④-10 | salvo | PASS |  |
| ④-11 | segment | 口径差 | inacc: 文章=0 / jar 无字段；maxAmmo: 文章=0 / jar 无字段；ammoPerShot: 文章=0 / jar 无字段；targetAir: 文章=1 / jar 无字段；targetGround: 文章=1 / jar 无字段 |
| ④-12 | tsunami | PASS |  |
| ④-13 | fuse | PASS |  |
| ④-14 | ripple | PASS |  |
| ④-15 | cyclone | PASS |  |
| ④-16 | foreshadow | PASS |  |
| ④-17 | spectre | PASS |  |
| ④-18 | meltdown | PASS |  |
| ④-19 | breach | PASS |  |
| ④-20 | diffuse | PASS |  |
| ④-21 | sublimate | PASS |  |
| ④-22 | titan | PASS |  |
| ④-23 | disperse | PASS |  |
| ④-24 | afflict | PASS |  |
| ④-25 | lustre | PASS |  |
| ④-26 | scathe | PASS |  |
| ④-27 | smite | PASS |  |
| ④-28 | malign | PASS |  |

## ⑤ C05 单位 armor/health（解析文章原表）（41 条：PASS 41 / FAIL 0 / 口径差 0）

| # | 对象 | 判定 | 差异 |
|---|---|---|---|
| ⑤-1 | elude | PASS |  |
| ⑤-2 | nova | PASS |  |
| ⑤-3 | risso | PASS |  |
| ⑤-4 | renale | PASS |  |
| ⑤-5 | atrax | PASS |  |
| ⑤-6 | horizon | PASS |  |
| ⑤-7 | mega | PASS |  |
| ⑤-8 | mace | PASS |  |
| ⑤-9 | pulsar | PASS |  |
| ⑤-10 | minke | PASS |  |
| ⑤-11 | merui | PASS |  |
| ⑤-12 | quell | PASS |  |
| ⑤-13 | zenith | PASS |  |
| ⑤-14 | cleroi | PASS |  |
| ⑤-15 | tecta | PASS |  |
| ⑤-16 | stell | PASS |  |
| ⑤-17 | obviate | PASS |  |
| ⑤-18 | anthicus | PASS |  |
| ⑤-19 | locus | PASS |  |
| ⑤-20 | fortress | PASS |  |
| ⑤-21 | quasar | PASS |  |
| ⑤-22 | spiroct | PASS |  |
| ⑤-23 | collaris | PASS |  |
| ⑤-24 | disrupt | PASS |  |
| ⑤-25 | quad | PASS |  |
| ⑤-26 | precept | PASS |  |
| ⑤-27 | sei | PASS |  |
| ⑤-28 | aegires | PASS |  |
| ⑤-29 | latum | PASS |  |
| ⑤-30 | corvus | PASS |  |
| ⑤-31 | arkyid | PASS |  |
| ⑤-32 | vela | PASS |  |
| ⑤-33 | omura | PASS |  |
| ⑤-34 | antumbra | PASS |  |
| ⑤-35 | scepter | PASS |  |
| ⑤-36 | navanax | PASS |  |
| ⑤-37 | vanquish | PASS |  |
| ⑤-38 | toxopid | PASS |  |
| ⑤-39 | eclipse | PASS |  |
| ⑤-40 | conquer | PASS |  |
| ⑤-41 | reign | PASS |  |

## ⑥ C06 单位武器 DPS（解析文章原表，含 shots）（28 条：PASS 28 / FAIL 0 / 口径差 0）

| # | 对象 | 判定 | 差异 |
|---|---|---|---|
| ⑥-1 | dagger | PASS |  |
| ⑥-2 | mace | PASS |  |
| ⑥-3 | fortress | PASS |  |
| ⑥-4 | zenith | PASS |  |
| ⑥-5 | stell | PASS |  |
| ⑥-6 | locus | PASS |  |
| ⑥-7 | precept | PASS |  |
| ⑥-8 | vanquish | PASS |  |
| ⑥-9 | conquer | PASS |  |
| ⑥-10 | merui | PASS |  |
| ⑥-11 | cleroi | PASS |  |
| ⑥-12 | tecta | PASS |  |
| ⑥-13 | collaris | PASS |  |
| ⑥-14 | quell | PASS |  |
| ⑥-15 | corvus | PASS |  |
| ⑥-16 | scepter | PASS |  |
| ⑥-17 | reign | PASS |  |
| ⑥-18 | omura | PASS |  |
| ⑥-19 | atrax | PASS |  |
| ⑥-20 | spiroct | PASS |  |
| ⑥-21 | arkyid | PASS |  |
| ⑥-22 | toxopid | PASS |  |
| ⑥-23 | eclipse | PASS |  |
| ⑥-24 | nova | PASS |  |
| ⑥-25 | quasar | PASS |  |
| ⑥-26 | poly | PASS |  |
| ⑥-27 | risso | PASS |  |
| ⑥-28 | minke | PASS |  |

## 汇总

| 组 | 条数 | PASS | FAIL | 口径差 |
|---|---|---|---|---|
| ① | 26 | 26 | 0 | 0 |
| ② | 14 | 14 | 0 | 0 |
| ③ | 41 | 41 | 0 | 0 |
| ④ | 28 | 25 | 0 | 3 |
| ⑤ | 41 | 41 | 0 | 0 |
| ⑥ | 28 | 28 | 0 | 0 |
| **合计** | **178** | **175** | **0** | **3** |

## 与世界数据表的一致性

- blocks：jar=447，期望=447 → PASS
- items：jar=22，期望=22 → PASS
- liquids：jar=11，期望=11 → PASS
- units：jar=70，期望=70 → PASS
- statusEffects：jar=23（无固定期望数，供 00-data/status.json 对照）
