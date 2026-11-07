---
id: WORLD.HEAT.001
title: 热量系统
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:412-470"
  - "Mindustry-Source/core/src/mindustry/world/blocks/heat/HeatProducer.java:14-62"
  - "Mindustry-Source/core/src/mindustry/world/blocks/production/HeatCrafter.java:13-85"
  - "Mindustry-Source/core/src/mindustry/world/blocks/heat/HeatConductor.java:53-111"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/NuclearReactor.java:29-153"
  - "Mindustry-Source/core/src/mindustry/world/consumers/ConsumeCoolant.java:5-12"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/ReloadTurret.java:28-39"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/ThermalGenerator.java:22, 71, 78-80"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:318-381 (地板 heat 属性)"
data: [00-data/blocks.json]
depends: [WORLD.LIQUIDS.001, WORLD.CRAFTING.001]
tags: [热量, HeatCrafter, HeatProducer, 冷却液, 过热, 反应堆, heatCapacity]
tokens: 1519
---

## 一句话

热量是**没有流体介质的标量场**：热源方块存一个 `heat` 数值，相邻方块按"接触点数 ÷ 自身尺寸"把这份热量**抄一份相加**（不守恒、不衰减、不消耗），所以传热是纯几何计算；而 `heatCapacity` 从不是"方块储热能力"，它只出现在**冷却液增益公式**里。

## 规则 / 公式

### 1. 三种热方块

| 接口/类 | 作用 | v160.7 数量 |
|---|---|---|
| `HeatBlock` | 提供 `heat()` / `heatFrac()` | 含在下面三类里 |
| `HeatProducer` | 靠配方产热（本身也是 GenericCrafter） | 6 |
| `HeatCrafter` | 靠邻接热量开工的制造机 | 5 |
| `HeatConductor` | 导热中继（不自己产热） | 3 |

`HeatProducerBuild` 每 tick 让 heat 逼近 `heatOutput × efficiency` [src: HeatProducer.java:51]：

```
heat = approachDelta(heat, heatOutput * efficiency, warmupRate * delta)   // warmupRate 默认 0.15
```

注意 `heat ` 是**绝对值**，不是每秒产量；`heatOutput` 就是它稳定时能达到的数值。`HeatProducer` 的 `heatOutput` 与 `ConsumePower` 的 `usage` 完全无关。

### 2. 传热公式（唯一的核心）

`BuildingComp.calculateHeat(sideHeat)` [src: BuildingComp.java:416-460]：

```
for (每个相邻且同队且 instanceof HeatBlock 的 heater):
    heat += heater.heat() / heater.size * contactPoints
    // contactPoints = min(size/2 + heaterSize/2 - 中心距(格), min(heaterSize, size))
    // 导热中继 splitHeat = true 时再 / 3
```

三个关键性质：

1. **加法而非平均**：三个 heatOutput = 8 的 slag-heater 贴着一个 heatRequirement = 24 的制造机，得到 24，正好满足。这是"堆热源"有效的原因。
2. **按尺寸摊薄**：`heater.heat() / heater.size`。一个 3×3 的 slag-heater（8 热）贴 1 格边只给 `8/3 ≈ 2.67`；贴 3 格边给 `8/3 × 3 = 8`（3×3 制造机的一整条边）。
3. **不守恒、不衰减**：同一份热被两个相邻消费者同时读到，各自都拿到全额；热量不会因为传出去而减少，也没有距离衰减（只算贴脸相邻，隔一格 = 0）。

朝向规则也在这里 [src: BuildingComp.java:428]：普通热源必须**面朝**消费者（`(relativeTo + 2) % 4 == heater.rotation`），导热中继则必须**背朝**消费者（`relativeTo != rotation`），例外是 `splitHeat = true` 的 heat-router 三个面都能出热并各自 / 3。

### 3. 热消费者：HeatCrafter

`HeatCrafterBuild.updateTile()` 先 `heat = calculateHeat(sideHeat)` 再跑配方 [src: HeatCrafter.java:49-53]，效率系数 [src: HeatCrafter.java:82-85]：

```
over  = max(heat - heatRequirement, 0)
scale = min( clamp(heat / heatRequirement) + over / heatRequirement * overheatScale, maxEfficiency )
```

- `heat < heatRequirement` → 线性降效（heat 一半就一半速度）；
- `heat >= heatRequirement` → 只有 `overheatScale > 0 才有额外收益；
- **v160.7 五个 HeatCrafter 全部 `maxEfficiency = 1`**，即"给再多热也只到 100%"，超热收益在这五个方块上被关掉了。

另外 `shouldConsume()` 要求 `heat > 0` [src: HeatCrafter.java:56-58]：**完全没热就不吃原料**，这条让"先铺热源再喂料"成为唯一正确顺序。

### 4. 冷却液与 heatCapacity

`heatCapacity` 出现在冷却公式里，不是储热公式里：

**炮塔**（`ReloadTurret`，所有 ItemTurret / LaserTurret 的父类）[src: ReloadTurret.java:30-33]：

```
capacity = 冷却液.heatCapacity        // 无冷却液时按 0.4
reloadCounter += coolant.amount * efficiency * edelta * capacity * coolantMultiplier
```

water 0.4、cryofluid 0.9 → **同一门炮用 cryofluid 的射速增益是水的 2.25 倍**（每 tick 消耗量相同）。

**护盾**：`ForceProjector` 的 `liquidHeat = 1 + (heatCapacity - 0.4) × 0.9` [src: ForceProjector.java:134]。
**修理塔**：`multiplier = 1 + heatCapacity × coolantMultiplier × efficiency` [src: RepairTurret.java:190]。
**牵引塔**：消耗量被 `min(库存, maxUsed×delta, (1/coolantMultiplier)/heatCapacity)` 反比限制 [src: TractorBeamTurret.java:97]——热容越高，单 tick 能"吃"的冷却液越少，但每滴更值钱。

### 5. 什么液体能当冷却液

`ConsumeCoolant` 的过滤器 [src: ConsumeCoolant.java:5-12]：

```
liquid.coolant && liquid.temperature <= maxTemp(0.5) && liquid.flammability < maxFlammability(0.1)
        && (allowLiquid && !liquid.gas || allowGas && liquid.gas)
```

按这张表逐个筛 v160.7 的 11 种液体，**合格的只有 water（0.5/0）、cryofluid（0.25/0）、gallium（0.5/0）**：

- slag 温度 1.0 → 超标；
- oil 可燃 1.2、arkycite 0.4、ozone 1、hydrogen 1、cyanogen 2 → 可燃超标；
- neoplasm 温度 0.54 → 超标；
- nitrogen 温度 0.5、可燃 0，但是 `gas` 且炮塔 `allowGas = 0` → 被气体规则挡掉。

注意 `Liquid.coolant` 这个字段只是第一道粗筛：slag / oil / neoplasm 的 `coolant` 都是 true，但在原版炮塔里仍然当不了冷却液。

### 6. 过热与爆炸：只有反应堆会炸

跨界面的"热"有且只有一个会失控：**核反应堆（thorium-reactor）** [src: NuclearReactor.java:96-133]：

```
fullness = 燃料数 / itemCapacity(30)
heat += fullness * heating(0.005) * min(delta, 4)        // 有燃料且 enabled
heat = max(0, heat - delta / ambientCooldownTime(1200))  // 没燃料时自然冷却
maxUsed = min(当前冷却液量, heat / coolantPower(0.125))
heat -= maxUsed * coolantPower ; 扣掉 maxUsed 冷却液
heat = clamp(heat, 0, 1)
if (heat >= 0.999) { kill(); }                            // 爆炸
```

代入 v160.7 参数可以算出三个硬数字：

- **满燃料无冷却**：每 tick +0.005 → **199 tick ≈ 3.3 秒**烧到 0.999 爆炸；
- **刚好压住**：每 tick 需要抽走 0.005 热，即 `0.005 / 0.125 = 0.04` 单位冷却液/tick = **2.4 单位/秒**（水的量）；
- **烧到满热**：需要 `1 / 0.125 = 8` 单位冷却液/tick = 480/s 才能压住，远超单条管道常见供给。

爆炸参数：`explosionRadius = 19` 格、`explosionDamage = 5000` [src: NuclearReactor.java:67-68]。`shouldExplode()` 还要求 `燃料 >= 5 || heat >= 0.5` [src: NuclearReactor.java:152-153]，所以空反应堆被打掉不会核爆。

`heatProgress` 与爆炸无关：它只是 `approachDelta(heatProgress, heat × heatOutput, heatWarmupRate)` 的输出功率平滑值，用来供电与供热。

### 7. 热力发电（把地板 heat 属性换成电）

`ThermalGenerator` 的 `productionEfficiency = sum(覆盖格 floor.attributes[heat]) + Attribute.heat.env()` [src: ThermalGenerator.java:78-80]，再乘 `powerProduction`。

- 短板热力发电机 2×2 覆盖 4 格：全在 molten-slag 上 = `4 × 0.85 = 3.4` 效率，即 `1.8 × 3.4 = 6.12/tick = 367/s`；
- `canPlaceOn` 要求所覆盖地板 heat 之和 `> minEfficiency` [src: ThermalGenerator.java:69-72]，所以必须贴热地板；
- 地板 heat 值：**molten-slag 0.85、magmarock 0.75、hotrock 0.5** [src: Blocks.java:327, 364, 374]；星球的 `defaultAttributes` heat = 0.8（`Planets.java:72`）会加到 `env()` 上。

液体自身也会因为星球环境热而汽化：`Liquid.willBoil() = Attribute.heat.env() >= boilPoint` [src: Liquid.java:110-113]。

## 数值

**热源（heatOutput）**

| 方块 | heatOutput | 备注 |
|---|---|---|
| electric-heater | 3 | 2×2，吃电 |
| oxidation-chamber | 5 | 3×3 |
| slag-heater | 8 | 3×3，吃 slag |
| heat-reactor | 10 | 3×3 |
| phase-heater | 15 | 2×2，吃 phase fabric |
| neoplasia-reactor | 60 | 5×5，HeaterGenerator |
| heat-source（沙盒） | 1000 | 1×1，编辑器 |

**热消费者（heatRequirement，全部 maxEfficiency = 1）**

| 方块 | heatRequirement | 尺寸 |
|---|---|---|
| cyanogen-synthesizer | 20 | 3×3 |
| atmospheric-concentrator | 24 | 3×3 |
| phase-synthesizer | 32 | 3×3 |
| carbide-crucible | 40 | 3×3 |
| surge-crucible | 40 | 3×3 |

**冷却液倍率 `coolantMultiplier`（炮塔）**

| 倍率 | 方块 |
|---|---|
| 30 | arc |
| 15 | breach / diffuse / scathe / smite |
| 10 | duo / hail |
| 6.25 | disperse |
| 5 | lancer / wave / swarmer / salvo / fuse / ripple / cyclone / afflict / malign / build-tower / scatter |
| 3.75 | titan |
| 2 | segment |
| 1.6 | repair-turret |
| 1 | meltdown / parallax / sublimate / lustre / repair-point |
| 0.5 | spectre |
| 0.4 | foreshadow |

**冷却液消耗（ConsumeCoolant.amount，per tick → per second）**

| 方块 | amount/tick | /秒 |
|---|---|---|
| duo / hail / arc | 0.1 | 6 |
| fuse / cyclone / ripple | 0.3 | 18 |
| foreshadow | 1 | 60 |

## 源码锚点

- `BuildingComp.java:416-460` `calculateHeat`：接触点数公式、朝向校验、`splitHeat` 的 /3、循环检测 `cameFrom`。
- `BuildingComp.java:412-414` 无 `cameFrom` 的简化重载（HeatCrafter 用这个）。
- `HeatProducer.java:51` `heat = approachDelta(heat, heatOutput * efficiency, warmupRate * delta)`。
- `HeatCrafter.java:49-57` 先算热再跑配方；`shouldConsume` 要求 `heat > 0`。
- `HeatCrafter.java:71-73` `warmupTarget = clamp(heat / heatRequirement)`。
- `HeatCrafter.java:82-85` `efficiencyScale`：线性 + overheatScale，封顶 maxEfficiency。
- `HeatConductor.java:85-90, 109-111` `updateHeat` 与 `heatFrac = heat / visualMaxHeat / (splitHeat ? 3 : 1)`。
- `NuclearReactor.java:101-133` 升温 / 冷却 / clamp / `heat >= 0.999f → kill()`。
- `NuclearReactor.java:112-116` 冷却液消耗 `maxUsed = min(库存, heat / coolantPower)`。
- `ConsumeCoolant.java:5-12` `maxTemp = 0.5`、`maxFlammability = 0.1` 过滤器。
- `ReloadTurret.java:28-39` 炮塔冷却增益公式（含 `ammoReloadMultiplier`）。
- `ThermalGenerator.java:71` `canPlaceOn` 依赖地板 heat 属性之和；`:78-80` 效率 = sum + `attribute.env()`。
- `Blocks.java:327/364/374` 地板 heat 属性 0.85 / 0.5 / 0.75。

## 实测与反例

**反例 1（方块没有 `maxTemp` 这个属性）**：任务清单里常写"heat / maxTemp"，但 v159.3 源码树搜 `maxTemp` 只命中 `ConsumeCoolant.java:5`——它是**冷却液过滤器的温度上限（0.5）**，不是任何方块的"耐热上限"。原版方块没有"高温损坏"机制：HeatCrafter 无论接多少热都不会烧毁，反应堆爆炸只看自己的 `heat >= 0.999`。

**反例 2（传热不守恒，一份热可以同时喂两个消费者）**：`calculateHeat` 只是把相邻 heater 的 `heat()` **读出来相加**，heater 自身的 heat 不会因此减少。所以两个 HeatCrafter 贴同一个 slag-heater，两者都拿到全额（各自受接触点数限制），不是"分走一半"。

**反例 3（`coolant = true` 不代表能当冷却液）**：slag 的 `Liquid.coolant` 字段是 true、oil 也是 true，但炮塔的 `ConsumeCoolant` 要求 `temperature <= 0.5` 且 `flammability < 0.1`，两者都被拒绝。原版炮塔实际只有 water / cryofluid / gallium 三种合法冷却液。

**反例 4（超热不等于超产）**：`HeatCrafter` 的源码默认 `maxEfficiency = 4`、`overheatScale = 1`，看起来"4 倍超热收益"，但 v160.7 五个 HeatCrafter 全部把 `maxEfficiency` 设为 1。也就是说给 carbide-crucible 接 80 热（需求 40）**不会**变成 2 倍速度。

**反例 5（反应堆的 `heatOutput = 8` 不是发电量）**：thorium-reactor 的 `heatOutput` 是供热值（HeatBlock 接口），它的发电量来自 `powerProduction = 15/tick`（900/s）。两者是两个独立字段，只是名字都带 heat。

## 常见误解

1. **"热量会随着距离衰减 / 需要管道输热"** → 只计算**贴脸相邻**（`proximity`）的 HeatBlock，隔一格就是 0；没有"热管道损耗"，导热中继只是把热"中转"到更远处。
2. **"heatCapacity 是方块储热能力，热容大的方块升温慢"** → 方块层面的储热字段不存在。`heatCapacity` 只属于**液体**，且只在冷却液增益公式里作为乘数。
3. **"冷却液会降低炮塔伤害/有其他副作用"** → 原版冷却液只增加 `reloadCounter` 的推进速度（更快开火），没有任何负面效果；`ConsumeCoolant` 是 `optional = true, booster = true`，没有冷却液也能开火。
4. **"所有发电机都有冷却"** → 只有实现 `ConsumeCoolant` 的 16 个方块（16 个炮塔类 + force-projector）有冷却口；反应堆的"冷却"是它自己手写的 `coolantPower` 逻辑，与 `ConsumeCoolant` 无关。
5. **"热源贴着就一定能供热"** → 普通 HeatProducer/HeatCrafter 有朝向要求（必须面朝对方）；只有 `splitHeat = true` 的 heat-router 才能三面出热，而它自己出热还要 / 3。
6. **"反应堆没水就慢慢过热、有时间抢救"** → 满燃料 199 tick（约 3.3 秒）就炸；不喂燃料时按 `ambientCooldownTime = 1200` tick（20 秒）自然冷却到 0。

## 相关

- `WORLD.LIQUIDS.001`（冷却液的液体属性、管道供给）
- `WORLD.CRAFTING.001`（HeatCrafter 继承 GenericCrafter，配方与 craftTime 语义不变）
- `WORLD.POWER.001`（反应堆发电、thermal-generator 的电力输出）
- `WORLD.TERRAIN.001`（地板 heat 属性与 `molten-slag` / `hotrock` / `magarock` 地形）
- `WORLD.BLOCKS.001`（方块尺寸如何影响 `contactPoints`）
- 数据表：`00-data/blocks.json`（`heatOutput` / `heatRequirement` / `coolantMultiplier` / `maxEfficiency` 在 `raw` 子树）
- 源码：`world/blocks/heat/*.java`、`world/blocks/production/HeatCrafter.java`、`world/blocks/power/NuclearReactor.java`、`world/consumers/ConsumeCoolant.java`
