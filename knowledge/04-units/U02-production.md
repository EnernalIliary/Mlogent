---
id: UNIT.PRODUCE.001
title: 单位生产链——工厂、重构厂、组装厂与单位上限
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/units/UnitFactory.java:39,101,207-219,392-443"
  - "Mindustry-Source/core/src/mindustry/world/blocks/units/Reconstructor.java:36-41,168,334"
  - "Mindustry-Source/core/src/mindustry/world/blocks/units/UnitAssembler.java:45-52,278-281"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6269-6581"
  - "Mindustry-Source/core/src/mindustry/entities/Units.java:114-131"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:75,83,157,290-295"
  - "Mindustry-Source/core/src/mindustry/entities/comp/BlockUnitComp.java / BlockIndexer.java:216,614"
  - "Mindustry-Source/core/src/mindustry/Vars.java:137"
data: [00-data/blocks.json, 00-data/units.json]
depends: [UNIT.MOVE.001]
tags: [工厂, 重构厂, 组装厂, 单位上限, unitCap, buildSpeed, payload]
tokens: 1161
---

## 一句话

原版造兵有**三条管道**：工厂（物品+电 → 低阶单位，`UnitPlan.time` 单位是 **tick**）、重构厂（把已有单位当输入，升级成高阶，`constructTime` 同样按 tick）、组装厂（把**单位与方块当原料**造 tier 4/5 巨兽）；上限由**核心的 `unitCapModifier` 求和**决定，默认 `rules.unitCap = 0` 且 `unitCapVariable = true`。

## 规则 / 公式

### 1. 工厂（UnitFactory）

```
progress += edelta() * Vars.state.rules.unitBuildSpeed(team)      // UnitFactory.java:403
if(progress >= plan.time) → 生成单位、consume()、progress %= 1
```

- `UnitPlan.unit` / `.time` / `.requirements`（UnitFactory.java:207-216）。
- 单位造价与时间**不受工厂等级影响**，只受 `rules.unitBuildSpeed(team)` 缩放：
  `unitBuildSpeed(team) = unitBuildSpeedMultiplier × teams.get(team).unitBuildSpeedMultiplier`（Rules.java:290-291，两者默认 1）。
- 工厂 `itemCapacity = 10` 且注释写明"unit factories can't control their own capacity externally"（UnitFactory.java:101）。
- `configurable = false` 的工厂（tank/ship/mech-fabricator）只有一种计划，不能切换。

### 2. 重构厂（Reconstructor）

```
把低阶单位作为 payload 送入 → progress += edelta() → progress >= constructTime 时替换为高阶单位
fraction() = progress / constructTime                       // Reconstructor.java:168
stats: Stat.productionTime = constructTime / 60f 秒          // Reconstructor.java:90
```

重构厂有 `upgrades` 表（`Seq<UnitType[]>`），**只接受表里声明的低阶单位**；输入单位会消失（被重构），不是并行生产。

### 3. 组装厂（UnitAssembler）

- 原料是 **payload**（`PayloadStack`：单位或方块），不是物品；
- `areaSize = 11`（默认，Blocks 里改成 13）：组装厂+模块占用的方形区域；
- `dronesCreated = 4`、`droneConstructTime = 240` tick：4 个建造无人机逐步拼装；
- 每级模块（`UnitAssemblerModule`）增加容量与并行能力，`basic-assembler-module` 是 tier 1 模块。

### 4. 单位上限（unit cap）

```
canCreate(type, team) = !type.useUnitCap
                     || (team.data().countType(type) < getCap(team) && !type.isBanned())    // Units.java:115-117
getCap(team):
    if(waveTeam 且 非 pvp) / 战役 waveTeam / rules.disableUnitCap / team.ignoreUnitCap → Integer.MAX_VALUE
    else max(0, rules.unitCapVariable ? rules.unitCap + team.data().unitCap : rules.unitCap)  // :119-125
```

- `rules.unitCap = 0`、`rules.unitCapVariable = true`（Rules.java:75,157）→ 上限 = **所有核心 `unitCapModifier` 之和** + `rules.unitCap`。
- 核心加成：core-shard **8**、core-foundation **16**、core-nucleus **24**、core-bastion **15**、core-citadel **15**、core-acropolis **15**（Blocks.java:3138/3150/3163/3185/3202/3220）。
- 增删核心时由 `BlockIndexer.java:216/614` 维护 `team.data().unitCap`。
- **敌方 waveTeam 在战役里 cap = MAX_VALUE**（不受上限约束）——这是"敌人越打越多、你被限制"的根因。

### 5. 载荷容量（payload）

```
Vars.tilePayload = tilesize * tilesize = 64     // Vars.java:137
UnitType.payloadCapacity 单位是 world units²；显示时 ÷ tilePayload 换算成"格²"
```

### 6. 造价缩放

`Rules.unitCostMultiplier = 1`（Rules.java:83），与 team 的版本相乘（:295）。`CampaignRules.java:41` 把敌方队伍设为 `1 / enemySpawnMultiplier`——hard 难度（1.5）下敌方单位造价 **0.667 倍**。

## 数值

### 工厂（Blocks.java:6269-6447）

| 方块 | 尺寸 | 功率 | 计划（单位 / 时间 tick / 物品成本） |
|---|---|---|---|
| ground-factory | 3 | 1.2 | dagger 900t(15s) silicon10+lead10；crawler 600t(10s) silicon8+coal10；nova 2400t(40s) silicon30+lead20+titanium20 |
| air-factory | 3 | 1.2 | flare 900t silicon15；mono 2100t silicon30+lead15 |
| naval-factory | 3 | 1.2 | risso 2700t silicon20+metaglass35；retusa 2100t silicon15+titanium20（floating） |
| tank-fabricator | 3 | 1.5 | stell 2100t beryllium40+silicon50（configurable=false） |
| ship-fabricator | 3 | 1.5 | elude 2400t graphite50+silicon70 |
| mech-fabricator | 3 | 1.5 | merui 2400t beryllium50+silicon70 |

### 重构厂（Blocks.java:6303-6385）

| 方块 | 尺寸 | 功率 | 物品/秒 | 液体 | constructTime | 升级对数 |
|---|---|---|---|---|---|---|
| additive-reconstructor | 3 | 3 | silicon40+graphite40 | — | 600t = **10 s** | 7 |
| multiplicative-reconstructor | 5 | 6 | silicon130+titanium80+metaglass40 | — | 1800t = **30 s** | 7 |
| exponential-reconstructor | 7 | 13 | silicon850+titanium750+plastanium650 | cryofluid **1/s** | 5400t = **90 s** | 7 |
| tetrative-reconstructor | 9 | 25 | silicon1000+plastanium600+surgeAlloy500+phaseFabric350 | cryofluid **3/s** | 14400t = **240 s** | 7 |

升级链（每台 7 对，节选）：additive：dagger→mace、crawler→atrax、nova→pulsar、flare→horizon、mono→poly、risso→minke、retusa→oxynoe。tetrative：antumbra→eclipse、arkyid→toxopid、scepter→reign、sei→omura、quad→oct、vela→corvus、aegires→navanax。

### 组装厂（Blocks.java:6522-6564）

| 方块 | 尺寸 | 功率 | 液体 | 计划（单位 / 时间 / 载荷原料） |
|---|---|---|---|---|
| tank-assembler | 5 | 2.5 | cyanogen 9/60 每秒 | vanquish 3000t + 4×stell + 10×tungsten-wall-large |
| tank-assembler | 5 | 2.5 | 同上 | conquer 10800t + 6×locus + 20×carbide-wall-large |
| ship-assembler | 5 | 2.5 | cyanogen 12/60 每秒 | quell 3600t + 4×elude + 12×beryllium-wall-large；disrupt 10800t + 6×avert + 20×carbide-wall-large |
| mech-assembler | 5 | 3 | cyanogen 12/60 每秒 | tecta 4200t + 5×merui + 12×tungsten-wall-large；collaris 10800t + 6×cleroi + 20×carbide-wall-large |

### 载荷容量

| 单位 | 字段 | 换算 |
|---|---|---|
| mega | `(2*2)*64 = 256` | 4 格² |
| quad | `(3*3)*64 = 576` | 9 格² |
| quell | `sqr(4)*64 = 1024` | 16 格² |
| disrupt | `sqr(6)*64 = 2304` | 36 格² |
| 默认 | `payloadCapacity = 8` | 0.125 格²（不能载任何方块） |

### 台数比例与整链瓶颈（配比推导）

造兵是**串行流水线**：T1 由工厂造，T2..T5 由重构厂把上一级单位当原料升级。每级单台的"每秒产出单位数"只由该级方块的 `constructTime` 决定：

    每台每秒 = outPer / (constructTime / 60)        // 60 tick = 1 s

| 级 | 方块 | 时间 | 每台每秒（单位/s） |
|---|---|---|---|
| T1 | ground-factory（dagger） | 900 t = 15 s | 0.0667 |
| T2 | additive-reconstructor（mace） | 600 t = 10 s | 0.1000 |
| T3 | multiplicative-reconstructor（fortress） | 1800 t = 30 s | 0.0333 |
| T4 | exponential-reconstructor（scepter） | 5400 t = 90 s | 0.0111 |
| T5 | tetrative-reconstructor（reign） | 14400 t = 240 s | 0.0042 |

时间取自上文工厂表与重构厂表 [src: Blocks.java:6269-6447] [src: Blocks.java:6303-6385]；每秒折算依据 [src: Reconstructor.java:90]（`Stat.productionTime = constructTime / 60f`）。

**台数比例不是 1:1**，而是与各级单台速率成反比：

    上游台数_k ≈ 下游需求_k × 每台每秒_k⁻¹
    1 台 T4 能带 0.0111 / 0.0042 ≈ 2.67 台 T5
    1 台 T3 能带 3 台 T4；1 台 T2 能带 3 台 T3；1 台 T1 只能带 0.67 台 T2

整链实际产出受**最慢一段**限制（级间是一对一升级，任一环饿死则整链同步降到最低）：

    整链产出 = min_k( count_k × 每台每秒_k / Π_{j>k} inPer_j )      // inPer 默认为 1

例：目标 5 台 T5 满效 ⇒ T1..T5 台数 = **1/1/1/2/5**，整链 0.0208 单位/s；材料必须按"实际达成"折算，而不是按"想要的 5 台"折算（否则硅会虚高约 2.4 倍）。

**反例（常见误解）**：按 1:1 配 T4/T5 —— 5 台 T5 只吃 0.021/s，而 5 台 T4 能出 0.056/s，T4 利用率只有 37.5%，白造 3 台；反过来只配 1 台 T4 却堆 5 台 T5，整链被 T4 卡在 0.011/s，T5 利用率只有 53%。另一个坑是拿"想要的产出"乘材料单耗：没进瓶颈的多余产能不消耗原料，按想要量算会把整链材料高估 2 倍以上。

## 源码锚点

- [src: UnitFactory.java:392-443] `updateTile`：`progress += edelta() * Vars.state.rules.unitBuildSpeed(team)`，达到 `plan.time` 生成。
- [src: UnitFactory.java:207-219] `UnitPlan{UnitType unit; ItemStack[] requirements; float time;}`。
- [src: Reconstructor.java:36-41] `constructTime = 60*2` 默认、`upgrades`、`capacities`。
- [src: Reconstructor.java:90] `stats.add(Stat.productionTime, constructTime/60f, StatUnit.seconds)`。
- [src: UnitAssembler.java:45-52] `areaSize=11`、`dronesCreated=4`、`droneConstructTime=60*4`、`capacities`、`plans`。
- [src: Rules.java:290-295] `unitBuildSpeed(team)` / `unitCost(team)` 的乘算。
- [src: Units.java:114-131] `canCreate` / `getCap` / `getStringCap`。
- [src: BlockIndexer.java:216,614] `unitCap` 的减/加。
- [src: Vars.java:137] `tilePayload = tilesize*tilesize`。

## 实测与反例

**反例 1：把 `UnitPlan.time` 当秒。**
dagger 900 是 **900 tick = 15 s**（900/60）。若按秒算会以为是 15 分钟。所有 `time`/`constructTime`/`reload` 在这套源码里都是 tick。

**反例 2：以为 `unitCap` 是固定值。**
`rules.unitCap` 默认 **0**，true 时上限完全来自核心：3 个 core-nucleus = `3×24 = 72`。放 `core-acropolis`（modifier 15）反而**比 nucleus 少 9**——大核心强在 30000 hp 与 6×6，不是上限。

**反例 3：以为组装厂可以无限并行。**
`AssemblerUnitPlan` 一次只推进一个 plan；`conquer` 要 10800 tick（180 s）+ 6 个 locus（每个又要 2100t 造）+ 20 个 carbide-wall-large，实际是**指数级产业链**，不是"造出来就能出 22000 hp 单位"。

**反例 4：以为敌人也受 40/单位上限约束。**
战役里 `waveTeam` 命中 `getCap` 的第一条分支 → `Integer.MAX_VALUE`。

**可复算**：ground-factory 造 1 个 dagger 需要 900 tick；`unitBuildSpeed` 默认 1 → 15 s。若用逻辑处理器把 `rules.unitBuildSpeedMultiplier` 设为 3（`LExecutor` 的 `unitbuildspeed`），则 300 tick = 5 s 一个；10 个 dagger 共 150 tick × ... 实际为 `10 × 900 / 3 = 3000 tick = 50 s`。

## 常见误解

- ❌ "重构厂能造新单位"。→ 只能把**已有的低阶单位**换成表里的高阶单位。
- ❌ "工厂能自己存料"。→ `itemCapacity = 10`，靠外部输入；工厂缓存满即停机。
- ❌ "单位上限对 NPC 也生效"。→ 只对 `useUnitCap = true` 的玩家/队伍单位生效。
- ❌ "payload 是格子数"。→ 字段单位是 world units²，显示时才 ÷64。
- ❌ "core-acropolis 上限最高"。→ 6 个核心的 modifier 是 8/16/24/15/15/15，nucleus 最高。

## 相关

- [[UNIT.MOVE.001]] 造出来的单位怎么移动
- [[UNIT.AI.001]] 工厂产物的默认命令
- [[UNIT.PROGRESSION.001]] 为什么没有"等级"只有"升阶"
- [[COMBAT.WAVE.001]] 敌方无上限的波次
