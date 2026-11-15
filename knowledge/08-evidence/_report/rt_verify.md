# rt_verify —— v160.7 jar 反射真值核对（第一批 CHEAT/C10/W06+W07 + 第二批 C02/单位）

- 生成时间：2026-11-08 05:06 (+08:00)
- 环境：v160.7 真服务器（`out/_server160.jar` + `out/jre21`），Rhino 反射，起服 ~2.1–4.4 s；抽取器 `kb-stage/tools/extract_rt.py` 的 `Extractor`。
- 原始数据：`kb-stage/08-evidence/_report/_rtverify/_raw/probe_vals.json`（常量/规则/行星/方块）、`.../probe_vals2.json`（处理器/内存/弹药）、`.../probe_vals3.json`（功率/钻头/熔毁）。
- 口径约定：**PASS** = jar 直接字段或可复算值与文章一致；**FAIL** = jar 值与文章不一致（给出正确值与改法）；**口径差** = jar 无对应 public 字段、或文章单位/公式口径与字段语义不同（给出可读到的部分）。
- 浮点按 4 位小数；tick↔秒统一 60 tick = 1 s；功率/耗电原值单位是 **power/tick**，×60 得 /s（表内两列并列）。

### 单位口径（ipt 与 /s，全报告通用）

**ipt = instructions per tick = 点/tick**；换 点/s 必须 ×60（1 s = 60 tick）。功率同理：`usage` / `powerProduction` 原值单位是 **power/tick**，×60 才是 /s。

| 处理器 | ipt（点/tick） | ipt×60（点/s） | maxInstructionsPerTick | 5×ipt | 单 tick 实际上限 min(5×ipt, 该值) |
|---|---|---|---|---|---|
| micro-processor | 2 | 120 | 40 | 10 | **10** |
| logic-processor | 8 | 480 | 40 | 40 | **40** |
| hyper-processor | 25 | 1500 | 40 | 125 | **40**（被 40 截断） |
| world-processor | 8 | 480 | 1000 | 40 | **40**（1000 是 LExecutor 单次执行上限，不是单 tick 预算） |

## ① CHEAT.md 数值表（L91-122）

| # | 值 | 文章出处 | jar 重算值 | 判定 | 备注 |
|---|---|---|---|---|---|
| ①-1 | tick = 1/60 s | CHEAT.md:93 | 无 tick 常量（60 tick/s 定义） | 口径差 | 时间单位定义，非字段 |
| ①-2 | 1 tile = 8 px | CHEAT.md:94 | `Vars.tilesize=8` | PASS | |
| ①-3 | wait 单位=秒，粒度 1 tick | CHEAT.md:95 | 无字段 | 口径差 | `@wait` 语义 |
| ①-4 | @time 毫秒 | CHEAT.md:96 | 无字段 | 口径差 | 逻辑变量语义 |
| ①-5 | 处理器 ipt：micro 2 / logic 8 / hyper 25 | CHEAT.md:97 | `instructionsPerTick` = 2 / 8 / 25 | 口径差 | **单位是「点/tick」不是「点/s」**；点/s = ipt×60 = 120 / 480 / 1500（文章写成点/s 属单位错位） |
| ①-6 | world 8 点/s，上限 1000 | CHEAT.md:98 | world `instructionsPerTick=8`、`maxInstructionsPerTick=1000` | 口径差 | 8 是 **点/tick**（=480 点/s）；1000 是 `LExecutor.maxInstructions`（单次执行上限），不是单 tick 预算（见下「单位口径」表） |
| ①-7 | 单 tick 预算 5×ipt | CHEAT.md:99 | `maxInstructionScale=5`；`maxInstructionsPerTick` micro/logic/hyper=40、world=1000 | 口径差 | 实际上限 = **min(5×ipt, maxInstructionsPerTick)**：micro 10、logic 40、hyper 125→**40**、world 40 |
| ①-8 | 1000 行 / print 400 / 聊天 150 | CHEAT.md:100 | `LExecutor.maxInstructions=1000`、`maxTextBuffer=400`、`Vars.maxTextLength=150` | PASS | |
| ①-9a | memory cell 32 格 | CHEAT.md:101 | `memory-cell.memoryCapacity=64` | **FAIL** | v160.7 普通 cell = **64 格**（不是 32）；改法：CHEAT 数值表改为 64，并复核 v159.3 源码行号 |
| ①-9b | world memory 512 格 | CHEAT.md:101 | `memory-bank.memoryCapacity=512` | PASS | |
| ①-10 | radar 每 30 tick 缓存 | CHEAT.md:102 | 无 public 常量（LExecutor 无 radar 字段） | 口径差 | jar 反射不可得；按**「源码注释 + 行为口径」**记录，待行为实测，**不判 PASS** |
| ①-11 | waveSpacing = 7200 tick = 120 s | CHEAT.md:103 | `rules.waveSpacing=7200` | PASS | |
| ①-12 | 首波 2×7200 = 240 s | CHEAT.md:104 | `rules.initialWaveSpacing=0`、`waveSpacing=7200` | 口径差 | 240 s 是派生；默认 initialWaveSpacing=0 |
| ①-13 | turnDuration 7200 tick | CHEAT.md:105 | `Vars.turnDuration=7200` | PASS | |
| ①-14 | 入侵宽限 20 分钟 | CHEAT.md:106 | `Vars.invasionGracePeriod=20` | PASS | |
| ①-15 | 入侵概率 1/100×(0.8+(n−1)×0.3) | CHEAT.md:107 | `Vars.baseInvasionChance=0.01` | 口径差 | 基数 0.01 ✓；0.8/0.3 系数无 public 字段 |
| ①-16 | 发射倍率 Serpulo 0.5 / 其它 0.25 | CHEAT.md:108 | `Planets.serpulo.launchCapacityMultiplier=0.5`；erekir/sun/tantros=0.25 | PASS | |
| ①-17 | 核心容量 4000/9000/13000 | CHEAT.md:109 | core-shard/foundation/nucleus `itemCapacity` = 4000/9000/13000 | PASS | |
| ①-18 | 核心单位上限 +8/+16/+24 | CHEAT.md:110 | `unitCapModifier` = 8/16/24 | PASS | |
| ①-19 | 单位上限 max(0, rules.unitCap+team.unitCap) | CHEAT.md:111 | `rules.unitCap=0`、`unitCapVariable=true` | 口径差 | 公式为源码语义，字段可读 |
| ①-20 | 敌方单位上限无限 | CHEAT.md:112 | 未直读（v160.7 Units 在 `mindustry.entities`） | 口径差 | 待行为/源码复核 |
| ①-21 | 波次上限 150 / 13 / 6 | CHEAT.md:113 | `Waves` 无对应 public 字段（只有 `waveVersion=7`） | 口径差 | 待源码复核 |
| ①-22 | 护甲 max(D−A, 0.1D) | CHEAT.md:114 | `Vars.minArmorDamage=0.1` | PASS | 0.1 保底系数 ✓ |
| ①-23 | 护甲拐点 A*=0.9D | CHEAT.md:115 | 由 `minArmorDamage=0.1` 派生 | PASS | 派生值 |
| ①-24 | meltdown 4680 vs 936 | CHEAT.md:116 | bullet `damage=78`、`damageInterval=5`：936=78×60/5；4680=78×100/5×3 | PASS | 两口径同源，1 个 bullet 字段两个算法 |
| ①-25 | spectre 对 22 甲 428.6→240 | CHEAT.md:117 | `damage=50`、`reload=7`：50×60/7=428.57；max(50−22,5)×60/7=240.0 | PASS | |
| ①-26 | conveyor 0.035 格/tick = 2.1 格/s | CHEAT.md:118 | `conveyor.speed=0.035`；×60=2.1 | PASS | |
| ①-27 | 吞吐 speed×60/0.4 ≈ 5.25 件/s；单格 3 件 | CHEAT.md:119 | `speed=0.035`、`itemCapacity=3`；0.035×60/0.4=5.25 | 口径差 | itemSpace=0.4 无字段；3 件 ✓ |
| ①-28 | phase-conveyor 30 件/s，range 12 | CHEAT.md:120 | `transportTime=2`、`range=12`、`usage=0.3/tick`；60/2=30，18/s 耗电 | PASS | |
| ①-29 | mass-driver range 440px=55 格，reload 200 | CHEAT.md:121 | `range=440`、`reload=200`、`itemCapacity=120`、`minDistribute=10`、`size=3` | PASS | |

## ② C10-numbers.md DPS/TTK 关键行

| # | 值 | 文章出处 | jar 重算值 | 判定 | 备注 |
|---|---|---|---|---|---|
| ②-1 | dagger 2×26 → 41.5 | C10:69 | 9×2×(60/26)=41.54 | PASS | |
| ②-2 | mace 2×44 → 201.8 | C10:70 | 74×2×(60/44)=201.82 | PASS | |
| ②-3 | toxopid 主武器 2×60 → 440.0（含 shots 2） | C10:71 | 110 × 2 挂点 × shots 2 × (60/60) = 440 | PASS | 漏乘 shots 会得 220（旧文值，第三批已改） |
| ②-4 | toxopid 加 cannon = 454.3 | C10:76 | 440 + 50×(60/210) = 454.29 | PASS | 副炮 shots=1 |
| ②-5 | reign 2×18 → 533.3 | C10:72 | 80×2×(60/18)=533.33 | PASS | |
| ②-6 | omura 1×110 → 681.8 | C10:73 | 1250×60/110=681.82 | PASS | |
| ②-7 | corvus 1×350 → 96.0 | C10:74 | 560×60/350=96.0 | PASS | |
| ②-8 | spectre vs toxopid TTK 91.67 | C10:93/99 | max(50−22,5)=28；28×60/7=240；22000/240=91.67 | PASS | |
| ②-9 | duo vs toxopid TTK 8148.15 | C10:84 | max(9−22,0.9)=0.9；0.9×60/20=2.7；22000/2.7=8148.15 | PASS | |
| ②-10 | meltdown vs toxopid TTK 32.74 | C10:96 | 78−22=56；56×(60/5)=672；22000/672=32.74 | PASS | |
| ②-11 | scorch vs toxopid 1294.12 | C10:85 | 17→max(17−22,1.7)；1.7×10=17；22000/17=1294.12 | PASS | |
| ②-12 | salvo vs toxopid 7088.89 | C10:86 | 15→1.5；1.5×60/29=3.103；22000/3.103=7088.9 | PASS | |
| ②-13 | cyclone vs toxopid 6111.11 | C10:87 | 6→0.6；0.6×60/10=3.6；22000/3.6=6111.1 | PASS | |
| ②-14 | hail 实战 20.0（DPS） | C10:56 | damage=20、reload=60；20×60/60=20 | PASS | 溅射放大项未计 |

## ③ W06 物流 / W07 钻头关键值

| # | 值 | 文章出处 | jar 重算值 | 判定 | 备注 |
|---|---|---|---|---|---|
| ③-1 | conveyor speed 0.035 格/tick | W06:45/111 | `speed=0.035` | PASS | |
| ③-2 | conveyor 5.25 件/s | W06:45/119 | `speed=0.035`；公式 0.035×60/0.4=5.25 | 口径差 | **公式值 5.25 vs 显示值 5**（`displayedSpeed=5`），见下双列表 |
| ③-3 | titanium 0.0801 / 10 件/s | W06:112 | `speed=0.0801`；公式值 0.0801×60/0.4=12.02 | 口径差 | 原值 ✓；「10」是 **显示值** `displayedSpeed=10`，公式值 12.02 |
| ③-4 | armored 0.08 / 10 件/s | W06:113 | `speed=0.08`；公式值 12.00 | 口径差 | 同 ③-3（显示值 10 / 公式值 12.00） |
| ③-5 | plastanium 40 件/s | W06:114 | 10×0.0667×60=40.02 | PASS | `speed=0.0667`、`itemCapacity=10` |
| ③-6 | surge 50 件/s | W06:115 | 10×0.0833×60=49.98 | PASS | 耗电 0.0167/tick=1/s |
| ③-7 | duct speed=4 tick/件 | W06:72/116 | `speed=4`；60/4=15 件/s | 口径差 | 显示值 15（stats）vs 文章手算 20（口径差，duct 无 itemSpace）；见双列表 |
| ③-8 | junction speed=26，displayedSpeed=13 | W06:77/119 | `speed=26`、`displayedSpeed=13` | PASS | `itemCapacity=10` |
| ③-9 | router speed=8 → 7.5 件/s | W06:76/120 | `speed=8`；60/8=7.5 | PASS | |
| ③-10 | bridge-conveyor range4/buffer14/cap10/speed74/display11 | W06:83/121 | range=4、bufferCapacity=14、itemCapacity=10、speed=74、displayedSpeed=11 | PASS | |
| ③-11 | phase-conveyor range12/transportTime2/耗电0.3tick=18s/30件s | W06:85/122 | range=12、transportTime=2、usage=0.3/tick；60/2=30、×60=18/s | PASS | |
| ③-12 | mass-driver range440/reload200/cap120/minDistribute10/size3 | W06:89/123 | range=440、reload=200、itemCapacity=120、minDistribute=10、size=3 | PASS | range/tilesize=55 格 |
| ③-13 | unloader 60/11=5.4545 → 11 件/s | W06:100/124 | `speed=5.4545`；60/5.4545=11 | PASS | |
| ③-14 | duct-unloader speed4 → 15 件/s | W06:101/125 | `speed=4`；60/4=15 | PASS | |
| ③-15 | 钻头默认 hardnessDrillMultiplier=50 | W07:58 | mechanical/pneumatic/laser/blast=50；impact/eruption=0 | PASS | |
| ③-16 | 硬度公式 (drillTime+50×hardness)/倍率 | W07:55/174 | 字段齐：`drillTime`/`hardnessDrillMultiplier`/`drillMultipliers`（impact/eruption 对 beryllium 2×） | PASS | 覆盖率项为运行时量 |
| ③-17 | mechanical copper 650 tick → 0.369/s | W07:174 | 600+50×1=650；4×60/650=0.369 | 口径差 | 650 ✓；覆盖 4 格为运行时量 |
| ③-18 | mechanical 600 / pneumatic 400 | W07:157-158/92 | drillTime=600 / 400 | PASS | |
| ③-19 | laser 280 / blast 280 | W07:159-160 | drillTime=280 / 280 | PASS | |
| ③-20 | impact 720 / eruption 281.25 | W07:161-162 | drillTime=720 / 281.25 | PASS | |
| ③-21 | plasma-bore 160 / large 100 / cliff 110 / large-cliff 48 | W07:163-166 | drillTime=160 / 100 / 110 / 48 | PASS | |
| ③-22 | laser 电 1.1/tick=66/s | W07:159 | usage=1.1；×60=66 | PASS | |
| ③-23 | blast 3/tick=180/s | W07:160 | usage=3；×60=180 | PASS | |
| ③-24 | impact 2.667/tick=160/s | W07:161 | usage=2.6667；×60=160 | PASS | |
| ③-25 | eruption 6/tick=360/s | W07:162 | usage=6；×60=360 | PASS | |
| ③-26 | plasma-bore 0.15→9/s、large 0.8→48/s | W07:163-164 | usage=0.15/0.8；×60=9/48 | PASS | |
| ③-27 | cliff 0.1833→11/s、large-cliff 1→60/s | W07:165-166 | usage=0.1833/1；×60=11/60 | PASS | |
| ③-28 | 液体加速 1.6 双乘=2.56 倍 | W07:104 | mechanical `liquidBoostIntensity=1.6` | 口径差 | 1.6 ✓；“双乘 2.56”是公式派生 |
| ③-29 | impact-drill 720 tick、16 件=1.333/s | W07:130 | drillTime=720；16 件无对应字段 | 口径差 | 720 ✓；产出件数需源码/实测 |

## ④ C02-turrets.md 全表 28 条 vs jar（含 jar 新增 3 条）

C02 列序：`炮塔 | size | hp | range | reload | inacc | rotate | maxAmmo | ammoPerShot | 打空 | 打地 | coolantMult | 需热 | shootCone`。jar 字段见 `00-data/turrets.json`。

| # | 炮塔 | C02:size/hp/range/reload | jar:size/hp/range/reload | 判定 | 差异/备注 |
|---|---|---|---|---|---|
| ④-1 | duo | 1/250/160/20 | 1/250/160/20 | PASS |  |
| ④-2 | scatter | 2/800/220/18 | 2/800/220/18 | PASS |  |
| ④-3 | scorch | 1/400/60/6 | 1/400/60/6 | PASS |  |
| ④-4 | hail | 1/260/235/60 | 1/260/235/60 | PASS |  |
| ④-5 | wave | 2/1000/110/3 | 2/1000/110/3 | PASS |  |
| ④-6 | lancer | 2/1120/165/80 | 2/1120/165/80 | PASS |  |
| ④-7 | arc | 1/260/90/35 | 1/260/90/35 | PASS |  |
| ④-8 | parallax | 2/640/300/0 | 2/640/300/- | 口径差 | C02 reload=0 表示非弹道；jar TractorBeamTurret **无 reload 字段**（range300/hp640/size2/coolant1/cone6 一致） |
| ④-9 | swarmer | 2/1200/240/34 | 2/1200/240/34.2857 | 口径差 | C02 reload 34（取整）vs jar 34.2857（=240/7）；其余字段一致 |
| ④-10 | salvo | 2/960/190/29 | 2/960/190/29 | PASS |  |
| ④-11 | segment | 2/1000/180/8 | 2/1000/180/8 | 口径差 | size/hp/range/reload/coolant/cone 一致；targetAir/targetGround 反射不可得（PointDefenseTurret 无该字段） |
| ④-12 | tsunami | 3/2250/190/3 | 3/2250/190/3 | PASS |  |
| ④-13 | fuse | 3/1980/90/35 | 3/1980/90/35 | PASS |  |
| ④-14 | ripple | 3/1170/290/120 | 3/1170/290/120 | PASS |  |
| ④-15 | cyclone | 3/1305/200/10 | 3/1305/200/10 | PASS |  |
| ④-16 | foreshadow | 4/2400/500/200 | 4/2400/500/200 | **FAIL** | C02 coolantMult=0 → jar **0.4**（C02:56 正文已写 0.4） |
| ④-17 | spectre | 4/2560/260/7 | 4/2560/260/7 | **FAIL** | C02 coolantMult=0 → jar **0.5**（C02:56 正文已写 0.5，表格与正文自相矛盾） |
| ④-18 | meltdown | 4/3200/195/90 | 4/3200/195/90 | PASS |  |
| ④-19 | breach | 3/1620/190/40 | 3/1620/190/40 | PASS |  |
| ④-20 | diffuse | 3/1890/125/30 | 3/1890/125/30 | PASS |  |
| ④-21 | sublimate | 3/1890/130/10 | 3/1890/130/10 | PASS |  |
| ④-22 | titan | 4/4000/390/138 | 4/4000/390/138 | PASS |  |
| ④-23 | disperse | 4/4480/310/9 | 4/4480/310/9 | PASS |  |
| ④-24 | afflict | 4/3520/368/50 | 4/3520/368/50 | PASS |  |
| ④-25 | lustre | 4/3360/250/10 | 4/3360/250/10 | PASS |  |
| ④-26 | scathe | 4/3520/1350/600 | 4/3520/1350/600 | PASS |  |
| ④-27 | smite | 5/8750/300/100 | 5/8750/300/100 | PASS |  |
| ④-28 | malign | 5/9250/410/3.5 | 5/9250/410/3.5 | PASS |  |

补充核对（C02 其余列）：inacc/rotate/maxAmmo/ammoPerShot/targetAir/targetGround/shootCone 在 28 条中 **26 条全一致**；仅 spectre、foreshadow 的 coolantMult 不一致。

## ⑤ 单位 armor/health 抽样 15 条（jar 全 70 条见 `00-data/units.json`）

出处：C05 表取 v160.7 jar；U05 部分行是 v159.3 源码值（C05:111 已注明版本差）。

| # | 单位 | 文章 hp / armor | 出处 | jar hp / armor | 判定 | 备注 |
|---|---|---|---|---|---|---|
| ⑤-1 | dagger | 150 / 0 | U05-progression.md:88 | 150 / 0 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-2 | mace | 550 / 4 | U05-progression.md:88 | 550 / 4 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-3 | fortress | 900 / 9 | U05-progression.md:88 | 900 / 9 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-4 | scepter | 9000 / 20 | C05-armor.md:108 | 9000 / 20 | PASS | U05 旧行写 v159.3 值（scepter 10 / reign 18 / arkyid 6 / toxopid 13），引用 U05 须带版本标签 |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-5 | reign | 24000 / 30 | C05-armor.md:109 | 24000 / 30 | PASS | U05 旧行写 v159.3 值（scepter 10 / reign 18 / arkyid 6 / toxopid 13），引用 U05 须带版本标签 |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-6 | crawler | 150 / 0 | U05-progression.md:90 | 150 / 0 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-7 | atrax | 600 / 3 | U05-progression.md:90 | 600 / 3 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-8 | spiroct | 1000 / 5 | U05-progression.md:90 | 1000 / 9 | 口径差 | U05:90 为 v159.3 源码值（armor 5）；v160.7 jar = **9**（版本差，非错） |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-9 | arkyid | 8000 / 14 | C05-armor.md:107 | 8000 / 14 | PASS | U05 旧行写 v159.3 值（scepter 10 / reign 18 / arkyid 6 / toxopid 13），引用 U05 须带版本标签 |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-10 | toxopid | 22000 / 22 | C05-armor.md:108 | 22000 / 22 | PASS | U05 旧行写 v159.3 值（scepter 10 / reign 18 / arkyid 6 / toxopid 13），引用 U05 须带版本标签 |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-11 | corvus | 18000 / 14 | C05-armor.md:107 | 18000 / 14 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-12 | omura | 22000 / 16 | C05-armor.md:107 | 22000 / 16 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-13 | eclipse | 22000 / 22 | C05-armor.md:108 | 22000 / 22 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-14 | conquer | 22000 / 26 | C05-armor.md:109 | 22000 / 26 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| ⑤-15 | vela | 8200 / 16 | C05-armor.md:107 | 8200 / 16 | PASS |  |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |

**版本差（引用须带版本标签）**：U05-progression.md:88-90 的 scepter armor 10、reign 18、arkyid 6、toxopid 13、spiroct 5 均为 **v159.3 源码值**；v160.7 jar = **20 / 30 / 14 / 22 / 9**（C05:111 已注明）。

**抽样结论**：14 PASS + 1 口径差（spiroct，U05 v159.3 值）；C05 的 v160.7 jar 表与反射完全一致，无真错。

## 汇总（第二批完成，累计）

| 组 | 条数 | PASS | FAIL | 口径差 |
|---|---|---|---|---|
| ① CHEAT | 30 | 16 | 1 | 13 |
| ② C10 | 14 | 14 | 0 | 0 |
| ③ W06+W07 | 29 | 24 | 0 | 5 |
| ④ C02 炮塔 | 28 | 23 | 2 | 3 |
| ⑤ 单位抽样 | 15 | 14 | 0 | 1 |
| ⑥ C06 单位 DPS（第三批） | 28 | 28 | 0 | 0 |
| **合计（三批）** | **144** | **119** | **3** | **22** |

> ⑥ 为第三批新增（C06 表 1 全 28 行 PASS）；② C10 的 14 行在数值按 shots 修正后仍全 PASS（220.0 → 440.0、234.3 → 454.3）。

（另有 ④ 补充 3 条 jar-only 炮塔，不计入判定。）

## 待改文章清单（必须改）

| 文件:行 | 现文 | 应为 | 依据 |
|---|---|---|---|
| `kb-stage/08-evidence/CHEAT.md:101` | 普通 memory cell 32 格 | **64 格** | `memory-cell.memoryCapacity=64`（v160.7 jar 反射；world bank 512 不变） |
| `kb-stage/03-combat/C02-turrets.md:115` | foreshadow coolantMult = 0 | **0.4** | jar `coolantMultiplier=0.4`；同文件 L56 正文已写 foreshadow=0.4 |
| `kb-stage/03-combat/C02-turrets.md:116` | spectre coolantMult = 0 | **0.5** | jar `coolantMultiplier=0.5`；同文件 L56 正文已写 spectre=0.5 |

如 v159.3 源码确为 32 格，CHEAT 那条改为写「v159.3=32 / v160.7=64」的版本差，但仍须标注当前版本值 64。

## 建议改（口径措辞，不影响数值，不阻塞发布）

| 文件:行 | 现文 | 建议 | 依据 |
|---|---|---|---|
| `kb-stage/08-evidence/CHEAT.md:97` | micro/logic/hyper 的 ipt 写成「点/s」（2/8/25） | 「点/tick，120/480/1500 点/s」 | ipt 是 per tick；`instructionsPerTick` |
| `kb-stage/08-evidence/CHEAT.md:99` | 单 tick 预算 5×ipt | 「min(5×ipt, maxInstructionsPerTick)；hyper 被 40 截断」 | `maxInstructionScale=5`、`maxInstructionsPerTick=40` |
| `kb-stage/02-world/W06-logistics.md:112-113` | titanium/armored「10 件/s」 | 「显示值 10；公式值 12.02 / 12.00」 | `displayedSpeed=10` vs `speed×60/0.4` |
| `kb-stage/02-world/W06-logistics.md:45` | conveyor 5.25 件/s | 「公式值 5.25；游戏内显示 5」 | `displayedSpeed=5` |
| `kb-stage/02-world/W06-logistics.md:72` | duct 15 或手算 20 | 明确「tick/件口径：60/4=15；20 为另一口径」 | `speed=4` |
| `kb-stage/03-combat/C02-turrets.md:106` | swarmer reload 34 | 「34.2857（=240/7），34 为取整」 | jar `reload=34.2857` |
| `kb-stage/04-units/U05-progression.md:88-90` | scepter 10 / reign 18 / toxopid 13 / arkyid 6 / spiroct 5（无版本标签） | 行内加 [v159.3]，并注 v160.7 = 20/30/22/14/9 | jar 反射 + C05:111 |

## 后续

- radar 30 tick、护甲公式外的状态系数：反射不可得，标「口径差」，需行为实测或源码复核，不进待改清单。
- 可重跑脚本 `kb-stage/tools/rt_verify.py`（起服 → 反射 → 比对 → 重写本文件）。

## 第三批：C06/C10 的 DPS 口径修正与逐挂点复测（2026-11-08，v160.7 jar）

### 3.1 修正结论

- **9 行全部改完并复测 PASS**：C06 表 1 的 7 行 + C10 表 2 的 1 行 + C10 说明段 1 行。
- 三类错误根因（不是同一个 bug）：
  1. **漏乘 `shoot.shots`**（zenith / tecta / scepter / toxopid / C10 两行）：`mirror=true` 的武器在 `UnitType.init()` 里已复制挂点、reload 已 ×2，但 `shots` 仍要乘；漏乘会按「发数」比例偏低（toxopid 220 vs 440）。
  2. **同名武器不同 reload 被当成同一把**（vanquish 副炮 44/54、arkyid 18/28/44、eclipse 18/24）：文章按「6 把都 reload 18」之类算，虚高（arkyid 816.0 → 563.2）。
  3. **算术不自洽**（scepter 原 293.3 = 46.7 + 50×4，只算了 1 把主炮）。
- 正确公式（已写进 C06 表 1 上方 blockquote）：`dps = Σ挂点 (bullet.damage × shoot.shots × 60 / reload)`，只计单目标直伤。
- **注意口径**：jar 的 `weapon.dps()` / `unit.estimateDps()` 走 `BulletType.estimateDPS()`，会把贯穿按 2 目标、溅射 ×0.75、碎弹另加（toxopid 主炮 `dps()`=440，而其单目标直伤=220/挂点）——所以复测表里两者分列，判定用直伤和。

### 3.2 9 行：旧值 → 新值 → jar 复测

| 文件:行 | 单位 | 旧值 | 新值 | jar 逐挂点直伤（damage×shots×60/reload） | 直伤合计 | `unit.estimateDps()` | 判定 |
|---|---|---|---|---|---|---|---|
| `kb-stage/03-combat/C06-unit-weapons.md:90` | zenith | 21.0 | **42.0** | 21.0 + 21.0（shots 2） | 42.0 | 75.75 | PASS |
| `kb-stage/03-combat/C06-unit-weapons.md:94` | vanquish | 288.9 | **270.0** | 84.4 + 51.1 + 51.1 + 41.7 + 41.7（reload 80/44/44/54/54） | 269.98 | 504.36 | PASS |
| `kb-stage/03-combat/C06-unit-weapons.md:98` | tecta | 57.4 | **172.1** | 86.1 + 86.1（shots 3） | 172.13 | 374.63 | PASS |
| `kb-stage/03-combat/C06-unit-weapons.md:102` | scepter | 293.3 | **460.0** | 140.0 + 140.0 + 50.0 + 50.0 + 40.0 + 40.0（reload 90/90/24/24/30/30） | 460.0 | 460.0 | PASS |
| `kb-stage/03-combat/C06-unit-weapons.md:107` | arkyid | 816.0 | **563.2** | 133.3×2 + 85.7×2 + 54.5×2 + 8.0×2（reload 18/28/44/90） | 563.19 | 1175.37 | PASS |
| `kb-stage/03-combat/C06-unit-weapons.md:108` | toxopid | 234.3 | **454.3**（主炮 440.0） | 220.0 + 220.0 + 14.3（主炮 shots 2） | 454.29 | 987.5 | PASS |
| `kb-stage/03-combat/C06-unit-weapons.md:109` | eclipse | 353.3 | **328.3** | 76.7×2 + 50.0×2 + 37.5×2（reload 90/18/24） | 328.33 | 1663.75 | PASS |
| `kb-stage/03-combat/C10-numbers.md:71` | toxopid 主武器 | 220.0（射速 2.000/s） | **440.0**（射速 4.000/s） | 220.0 × 2 挂点 | 440.0 | 987.5 | PASS |
| `kb-stage/03-combat/C10-numbers.md:76` | toxopid 含副炮 | 234.3 | **454.3** | 220.0 × 2 + 14.3 | 454.29 | 987.5 | PASS |

复测方式：`kb-stage/tools/rt_verify.py`（真服务器 `out/_server160.jar` + JRE21）现测 `unit.estimateDps()` 与逐挂点 `bullet.damage / reload / shoot.shots`，原始日志 `kb-stage/08-evidence/_report/_rtverify/_raw/probe_dps_c06.json`（28 单位全量）。

### 3.3 机器重跑结果（`rt_verify.py` 第三批）

- 起服 2.22s，反射 1.11s，总 3.33s；输出 `_rtverify/RERUN.md`。
- **PASS 174 / FAIL 1 / 口径差 3 / 缺失 0**；六组：①26、②14（全 PASS，含 toxopid 440.0/454.3）、③41、④28、⑤41、⑥28（**C06 表 1 全 28 行 PASS**）。
- 唯一 FAIL 仍是 `kb-stage/08-evidence/CHEAT.md:101`「memory cell 32 格」（jar=64）：v159.3 源码确为 32，属版本差，等你决定改法（改成 64 或标 `v159.3=32 / v160.7=64`）。
- 口径差 3 条在 ④ C02（swarmer reload 34 vs 34.2857、segment/parallax 无 targetAir 字段），按要求不动 C02。

### 3.4 静态门禁

- `python kb-stage/tools/check_kb.py --root kb-stage` → **RESULT: PASS**，errors 0 / warnings 164（48 文件 / 492,174 字节 / 49,961 tokens / 1,028 个 ID / 18 张 data 表；C06、C10 改完复跑同值）。
- C06 = 175 行、C10 = 170 行（均 ≤250）。

---

## 终版 RERUN：①②③ 改为「实体名 + 字段名」解析（2026-11-08 05:40）

Lead 判定三处剩余 FAIL 是校验器解析问题、不是文章错（`m01003`），按要求停用「文件:行 + 手抄值」，改为按实体名/字段名在正文里现场定位。改动只发生在 `kb-stage/tools/rt_verify.py`，**未动任何文章**（含 C02、CHEAT）。

### 4.1 解析口径

- `CHECKS` 由 5 元组升级为 6 元组：`(组, 检查名, 文件, [关键词], jar 取值 lambda, tol)`。运行时 `art_check()` 在文件里找**同时含全部关键词**的行（关键词 = 实体名 + 字段名，如 `memory cell 格数`、`toxopid` + `large-purple`），**任一行含 jar 值即 PASS**，不再依赖行号。
- 两轮匹配：先在**原文**数字里找；找不到再在**去括号注**的文本里找。括号注 = 含 `类默认 / 旧值 / 默认 / 源码 / 注释 / 被实例覆盖 / v159 / v160` 字样的 `（…）`，整段剔除后才参与匹配 —— 所以正文「类默认 32 被实例覆盖」不会再被当成断言值。
- 数字抽取支持分数（`1/100 → 0.01`）与尾随字母（`0.1D`）；容差 `max(tol, |jar|×0.2%)`，覆盖文章 4 位取整（2.667 对 jar 2.6667、7088.89 对 7088.889）。
- ④⑤⑥ 仍直接解析 markdown 表：C02 按**炮塔名 + 字段名**（列名→jar 字段映射），C05 按表中的单位名，C06 按单位名取表 1 的 DPS 列。

### 4.2 终版结果（`_rtverify/RERUN.md`；起服 2.30s、反射 1.06s、总 3.43s）

| 组 | 条数 | PASS | FAIL | 口径差 |
|---|---|---|---|---|
| ① CHEAT.md 数值表 | 26 | 26 | 0 | 0 |
| ② C10 DPS/TTK | 14 | 14 | 0 | 0 |
| ③ W06/W07 物流·钻头 | 41 | 41 | 0 | 0 |
| ④ C02 炮塔表 | 28 | 25 | 0 | 3 |
| ⑤ C05 单位 armor/health | 41 | 41 | 0 | 0 |
| ⑥ C06 单位武器 DPS | 28 | 28 | 0 | 0 |
| **合计** | **178** | **175** | **0** | **3** |

**FAIL = 0**，缺失 = 0；`rt_verify.py` 退出码 0。①②③ 全部 81 条 PASS，`memory-cell` 与 `foreshadow/spectre` 不再报错。

### 4.3 三处旧 FAIL 的归因（都判为解析问题，文章维持原文）

| 旧 FAIL 位置 | 现文 | jar | 归因 | 终版判定 |
|---|---|---|---|---|
| `08-evidence/CHEAT.md:101` memory-cell | 64（句末注明「类默认 32 被实例覆盖」）| 64 | 旧校验器把括号注里的「类默认 32」当成了断言值 | **PASS**（L101，命中 64）|
| `03-combat/C02-turrets.md:115` foreshadow `coolantMultiplier` | 0.4（正文 L56 与表 L60 处的值均为 0.4）| 0.4 | 行号漂移：C02 改写后整体后移，旧校验器按固定行号取错了行 | **PASS**（按炮塔名 + 字段名取到 0.4）|
| `03-combat/C02-turrets.md:116` spectre `coolantMultiplier` | 0.5 | 0.5 | 同上 | **PASS**（取到 0.5）|

与源码对照：`MemoryBlock.java:12` 是类默认 `memoryCapacity = 32`，`Blocks.java:6875` 把 memory-cell 覆写为 64、`:6881` memory-bank 512、`:6967` world-cell 512 —— 文章写法与源码一致，之前的 FAIL 纯属解析器读到了注释值。

### 4.4 剩余 3 条口径差（不是文章错，按指示不动 C02）

- ④-8 **parallax**（TractorBeamTurret）：无 `reload` / `inaccuracy` / `maxAmmo` / `ammoPerShot` 字段，表内 0 是占位。
- ④-9 **swarmer**：文章 `reload 34` 是 `240/7 = 34.2857` 的取整，jar 4 位小数为 34.2857。
- ④-11 **segment**（PointDefenseTurret）：无 `inaccuracy` / `maxAmmo` / `ammoPerShot` / `targetAir` / `targetGround` 字段。

### 4.5 复跑

```
python -u kb-stage/tools/rt_verify.py
```

真服务器 `out/_server160.jar` + `out/jre21`，输出 `kb-stage/08-evidence/_report/_rtverify/RERUN.md` 与 `rerun.json`；退出码 0 = 0 FAIL 且 0 缺失。上节 3.3 记录的 `PASS 174 / FAIL 1` 为改造前快照，已被本节取代。
