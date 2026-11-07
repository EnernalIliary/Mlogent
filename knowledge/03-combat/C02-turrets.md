---
id: COMBAT.TURRET.001
title: 炮塔机制——射程、装填、弹药、冷却液、朝向与过热
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/Turret.java:47-150"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/Turret.java:342-351"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/Turret.java:538-550,625-735"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/ReloadTurret.java:25-51"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/ItemTurret.java:129-219"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/Turret.java:194-200"
  - "MBO/gamedata/v160.7/gamedata.json (jar 反射 raw 字段，28 个 turret)"
data: [00-data/turrets.json]
depends: [COMBAT.BULLET.001, COMBAT.DAMAGE.001]
tags: [炮塔, reload, 冷却液, 弹药, shootCone, 过热, 射速]
tokens: 1058
---

## 一句话

炮塔的全部节奏由三个计数器构成：**reloadCounter（装填）→ 满则开火 → 冷却期 cooldownTime**；冷却液不是"加速装填百分比"，而是**每 tick 额外往 reloadCounter 里加 `coolantNumber × 液体heatCapacity × coolantMultiplier`**，所以水的加成 = 0.1×0.4×10 = **40%**，冷冻液 = 0.1×0.9×10 = **90%**，与炮塔无关。

## 规则 / 公式

### 1. 射速

```
基础射速 shots/s = 60 / reload                     // reload 单位是 tick
每秒发数 = shots/s × shoot.shots                    // 多管/多发
DPS ≈ 60 / reload × shoot.shots × 单发伤害(ammo)
```

duo：reload 20 → 3 发/s。smite：reload 100、shots=5 → 3 发/s × 5 = 15 发/s。
**`reload` 不是毫秒**，写成 20ms 会错 60 倍。

### 2. 冷却液（ReloadTurret.updateCooling）

```
每 tick:  reloadCounter += delta() * baseReloadSpeed()          // 基础 = efficiency ≈ 1
        + coolant.amount * efficiency * heatCapacity * coolantMultiplier   // 有冷却液时额外加
ready 条件: reloadCounter >= reload
```

代入 duo（`coolant.amount = 0.1`，`coolantMultiplier = 10`）：

| 冷却液 | heatCapacity | 每 tick 额外 | 总装填速度 | 实际 reload | 相对射速 |
|---|---|---|---|---|---|
| 无 | — | 0 | 1.0× | 20 tick | 100% |
| water | 0.4 | 0.10×0.4×10 = 0.4 | 1.4× | ≈14.3 tick | 140% |
| oil | 0.7 | 0.7 | 1.7× | ≈11.8 tick | 170% |
| cryofluid | 0.9 | 0.9 | 1.9× | ≈10.5 tick | 190% |

`coolantMultiplier` 是"接冷却液时的装填/射速倍率"，逐炮塔不同（v160.7 jar / raw 实测，28 个炮塔全查）：从 foreshadow **0.4** 到 arc **30**，跨度约 **75 倍**——同一桶 water（heatCapacity 0.4、`coolant.amount` 0.1）给 foreshadow 只加 +1.6%，给 arc 加 +120%。

| 炮塔 | coolantMultiplier | water 加成 = 0.1×0.4×mult |
|---|---|---|
| foreshadow | 0.4 | +1.6% |
| spectre | 0.5 | +2.0% |
| parallax / meltdown / sublimate / lustre | 1 | +4.0% |
| scorch | 1.5 | +6.0% |
| segment | 2 | +8.0% |
| titan | 3.75 | +15.0% |
| duo / hail | 10 | +40.0% |
| disperse | 6.25 | +25.0% |
| scatter / wave / lancer / swarmer / salvo / tsunami / fuse / ripple / cyclone / afflict / malign | 5 | +20.0% |
| breach / diffuse / scathe / smite | 15 | +60.0% |
| arc | 30 | +120.0% |

口径：28 个炮塔里**没有 coolantMultiplier = 0** 的（最小即 foreshadow 0.4），所以"0 = 不受冷却液影响"在本版本无实例；若字段设为 0，`ReloadTurret.updateCooling` 里 `amount * … * coolantMultiplier` 恒为 0，接冷却液也不加速（`ReloadTurret.java:28-39`）。

### 3. 弹药容量

```
totalAmmo 上限 = maxAmmo                       // 单位是"弹药点"，不是物品数
每种弹药每 1 个物品给 ammoMultiplier 个弹药点     // BulletType.ammoMultiplier 默认 2f
单发消耗 = ammoPerShot
可开火次数 = maxAmmo / ammoPerShot
可接受物品数 = (maxAmmo - totalAmmo) / ammoMultiplier
```

duo：maxAmmo 30、ammoPerShot 1、ammoMultiplier 2 → **15 个铜 = 15 发**（不是 30 发）。
ripple：maxAmmo 30、ammoPerShot 2 → 15 发；每发消耗 2 弹药点。

### 4. 朝向与命中

| 字段 | 默认 | 含义 |
|---|---|---|
| `range` | 各炮塔不同 | 开火距离（px，8px = 1 格） |
| `minRange` | 0 | 最小射程（ripple/titan 类曲射为 0 也能打近） |
| `trackingRange` | 0（基类 `range()`） | 目标锁定距离 = range + trackingRange - range |
| `shootCone` | 8（字段默认）/ 各炮塔覆盖 | 炮口与目标夹角容差（度），>90 的（lustre 360、scorch 50）几乎无死角 |
| `inaccuracy` | 0 | 弹道随机散布（度） |
| `rotateSpeed` | 各炮塔 0.9~20 | 度/tick，duo=10 → 600°/s |
| `targetInterval` / `targetSwitchInterval` | 20 / 70 | 索敌刷新间隔（tick） |
| `ammoEjectBack` | 1 | 抛壳后坐视觉系数，不影响数值 |
| `elevation` | -1 | 炮管抬升动画，不影响伤害 |

`targetAir / targetGround` 决定能否打空中/地面：scorch、lancer、arc、hail、ripple、titan、scathe **不能打空中**（targetAir=0）；其余为 1。这是新手最常踩的坑——用 scorch 打飞行单位，炮塔根本不开火。

### 5. 过热（heat）

```
heatReq = calculateHeat(sideHeat)                     // 从相邻热源取热
efficiency *= clamp(heatReq / heatRequirement, 0, maxHeatEfficiency)
```

`heatRequirement = -1`（默认）表示**不需要热**，效率恒为 1；只有 **afflict（144）与 malign（144）** 需要热源，否则 efficiency = 0 完全不工作。热不是"过热惩罚"，而是"功率输入"。

## 数值

| 炮塔 | size | hp | range | reload(tick) | shots/s | inacc | rotate | maxAmmo | ammoPerShot | 打空 | 打地 | coolantMult | 需热 | shootCone | 类别 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| duo | 1 | 250 | 160 | 20 | 3.00 | 2 | 10 | 30 | 1 | 1 | 1 | 10 | -1 | 15 | ItemTurret |
| scatter | 2 | 800 | 220 | 18 | 3.33 | 17 | 15 | 30 | 1 | 1 | 0 | 5 | -1 | 35 | ItemTurret |
| scorch | 1 | 400 | 60 | 6 | 10.00 | 0 | 5 | 30 | 1 | 0 | 1 | 1.5 | -1 | 50 | ItemTurret |
| hail | 1 | 260 | 235 | 60 | 1.00 | 1 | 5 | 30 | 1 | 0 | 1 | 10 | -1 | 10 | ItemTurret |
| wave | 2 | 1000 | 110 | 3 | 20.00 | 5 | 5 | 30 | 1 | 1 | 1 | 5 | -1 | 50 | LiquidTurret |
| lancer | 2 | 1120 | 165 | 80 | 0.75 | 0 | 5 | 30 | 1 | 0 | 1 | 5 | -1 | 8 | PowerTurret(6) |
| arc | 1 | 260 | 90 | 35 | 1.71 | 0 | 8 | 30 | 1 | 0 | 1 | 30 | -1 | 40 | PowerTurret(3.3) |
| parallax | 2 | 640 | 300 | 0 | — | 0 | 12 | 0 | 0 | 1 | 0 | 1 | -1 | 6 | TractorBeam |
| swarmer | 2 | 1200 | 240 | 34 | 1.75 | 10 | 4 | 30 | 1 | 1 | 1 | 5 | -1 | 8 | ItemTurret |
| salvo | 2 | 960 | 190 | 29 | 2.07 | 0 | 5 | 30 | 1 | 1 | 1 | 5 | -1 | 8 | ItemTurret |
| segment | 2 | 1000 | 180 | 8 | 7.50 | 0 | 20 | 0 | 0 | 1 | 1 | 2 | 0 | 5 | PointDefense(8) |
| tsunami | 3 | 2250 | 190 | 3 | 20.00 | 3 | 5 | 30 | 1 | 1 | 1 | 5 | -1 | 45 | LiquidTurret |
| fuse | 3 | 1980 | 90 | 35 | 1.71 | 0 | 5 | 30 | 1 | 1 | 1 | 5 | -1 | 30 | ItemTurret |
| ripple | 3 | 1170 | 290 | 120 | 0.50 | 11 | 5 | 30 | 2 | 0 | 1 | 5 | -1 | 8 | ItemTurret |
| cyclone | 3 | 1305 | 200 | 10 | 6.00 | 10 | 7 | 30 | 1 | 1 | 1 | 5 | -1 | 30 | ItemTurret |
| foreshadow | 4 | 2400 | 500 | 200 | 0.30 | 0 | 1.5 | 40 | 5 | 1 | 1 | 0.4 | -1 | 2 | ItemTurret(10) |
| spectre | 4 | 2560 | 260 | 7 | 8.57 | 3 | 4 | 30 | 1 | 1 | 1 | 0.5 | -1 | 24 | ItemTurret |
| meltdown | 4 | 3200 | 195 | 90 | 0.67 | 0 | 1.5 | 30 | 1 | 1 | 1 | 1 | -1 | 40 | LaserTurret(17) |
| breach | 3 | 1620 | 190 | 40 | 1.50 | 0 | 1.5 | 30 | 2 | 1 | 1 | 15 | -1 | 3 | ItemTurret |
| diffuse | 3 | 1890 | 125 | 30 | 2.00 | 0.2 | 3 | 30 | 3 | 1 | 1 | 15 | -1 | 40 | ItemTurret |
| sublimate | 3 | 1890 | 130 | 10 | 6.00 | 0 | 5 | 30 | 1 | 1 | 1 | 1 | -1 | 8 | ContinuousLiquid |
| titan | 4 | 4000 | 390 | 138 | 0.43 | 0 | 1.4 | 12 | 4 | 0 | 1 | 3.75 | -1 | 8 | ItemTurret |
| disperse | 4 | 4480 | 310 | 9 | 6.67 | 8 | 5 | 30 | 1 | 1 | 0 | 6.25 | -1 | 30 | ItemTurret |
| afflict | 4 | 3520 | 368 | 50 | 1.20 | 1 | 1.5 | 30 | 1 | 1 | 1 | 5 | 20 | 20 | PowerTurret(5) |
| lustre | 4 | 3360 | 250 | 10 | 6.00 | 0 | 0.9 | 30 | 1 | 1 | 1 | 1 | -1 | 360 | ContinuousTurret(3.33) |
| scathe | 4 | 3520 | 1350 | 600 | 0.10 | 0 | 0.9 | 45 | 15 | 0 | 1 | 15 | -1 | 1 | ItemTurret |
| smite | 5 | 8750 | 300 | 100 | 0.60 | 0 | 1.5 | 30 | 2 | 1 | 1 | 15 | -1 | 30 | ItemTurret |
| malign | 5 | 9250 | 410 | 3.5 | 17.14 | 0 | 2.6 | 30 | 1 | 1 | 1 | 5 | 144 | 100 | PowerTurret(40) |

`shots/s` 全部由 `60/reload` 算出，可逐行复算（hail：60/60 = 1.00；swarmer：reload 34.2857 → 60/34.2857 = 1.75；malign：reload 3.5 → 60/3.5 = 17.14；titan：60/138 = 0.435）。

多管补充（源码显式赋值，其余默认 shots=1）：swarmer `shots = 4`；tsunami `shoot.shots = 2`；ripple `shoot.shots = 4`；smite `shots = barrels = 5`。

## 源码锚点

- `Turret.java:47-150` 字段块：`maxAmmo=30`(L47)、`ammoPerShot=1`(L49)、`heatRequirement=-1`(L53)、`inaccuracy=0`(L58)、`shootCone=8`(L64)、`trackingRange=0`(L72)、`minRange=0`(L74)、`reloadWhileCharging=true`(L82)、`targetAir=true`(L89)、`targetGround=true`(L91)、`ammoEjectBack=1`(L134)、`cooldownTime=20`(L148)、`elevation=-1`(L150)。
- `Turret.java:342-351` `range()` 与 `trackingRange()`：弹药可改射程（`peekAmmo().rangeChange`）。
- `Turret.java:720` 装填主循环：`if(reloadCounter < reload) reloadCounter += delta() * ammoReloadMultiplier() * baseReloadSpeed();`
- `Turret.java:730-735` 开火：`reloadCounter >= reload` 才发；开火后 `reloadCounter %= reload`。
- `Turret.java:625-676` 热逻辑：`heatReq <= 0` 直接不工作；`efficiency *= clamp(heatReq/heatRequirement, 0, maxHeatEfficiency)`。
- `ReloadTurret.java:28-39` 冷却液公式；`:45-51` `baseReloadSpeed()=efficiency`、`canReload()=reloadCounter<reload`。
- `ItemTurret.java:129-219` 弹药：`totalAmmo += type.ammoMultiplier`(L168/176/183)、上限判断 `totalAmmo + ammoMultiplier <= maxAmmo`(L188)。
- `Turret.java:194-200` 热的 UI 文本：`bar.heatpercent` 显示 `min(heatReq/heatRequirement, maxHeatEfficiency)`。

## 实测与反例

**反例 1：把 coolantMultiplier 当成"射速加成百分比"。**
duo 的 `coolantMultiplier = 10`，直观读成"+10% 射速"。实际加成 = 0.1×0.4×10 = +40%。而 arc 的 30 也不是"+30%"，是 +120%（0.1×0.4×30）。

**反例 2：以为 `maxAmmo=30` 等于 30 发。**
duo 每发 1 弹药点、每物品 2 点 → 15 发；ripple 每发 2 点 → 15 发；titan 每发 4 点且 maxAmmo=12 → 3 发。**titan 一个弹夹只有 3 炮**，这是它 DPS 表现得比纸面低的主因。

**反例 3：用 scorch 打飞行单位。**
scorch `targetAir = 0`，飞行单位进入 60px 射程内它也**完全不开火**，不是命中率低而是没有目标。

**反例 4：认为 reload 越小射速线性越好。**
reload 有下限：开火后立刻进入 `cooldownTime`（默认 20 tick，但 Turret 内是 `Mathf.clamp` 后的值），且 shootWarmup 需要 `minWarmup` 才允许开火，超短 reload 并不能无限叠射速。

## 常见误解

- ❌ "`rotateSpeed` 是 rpm"。→ 是**度/tick**；10 度/tick = 600°/s。
- ❌ "炮塔会自动选择最优弹药"。→ 只按 `ammo` 队列（进料顺序）取第一种，玩家要手动排料或靠卸载器换弹。
- ❌ "`inaccuracy` 是像素偏移"。→ 是**角度**（度），实际横向偏差 ≈ range × tan(inaccuracy)。
- ❌ "`targetInterval=20` = 20 秒"。→ 20 tick = 0.33 s。
- ❌ "过热会降射速"。→ 原版炮塔没有过热惩罚；`heat` 只是 afflict/malign 的**输入需求**。

## 相关

- [[COMBAT.BULLET.001]] 弹药对应的子弹字段（speed/lifetime 决定真实射程）
- [[COMBAT.NUMBERS.001]] 炮塔 DPS 表与 TTK 表
- [[COMBAT.DAMAGE.001]] 命中后的伤害管线
- [[WORLD.BLOCKS.001]] 多格炮塔的 3×3/4×4/5×5 占位
