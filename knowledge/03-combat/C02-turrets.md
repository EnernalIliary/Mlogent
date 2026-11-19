---
id: COMBAT.TURRET.001
title: "Turret mechanics: range, reload, ammo, coolant, aiming and overheat"
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
tags: [turret, reload, coolant, ammo, shootCone, heat, fire-rate]
tokens: 1074
---

## In one line

A turret's whole rhythm is three counters: **reloadCounter (reload) → fires when full → cooldownTime cooldown**; coolant is not an "extra reload percentage" but **an extra `coolantNumber × liquid heatCapacity × coolantMultiplier` added to reloadCounter every tick**, so water gives a bonus of 0.1×0.4×10 = **40%** and cryofluid 0.1×0.9×10 = **90%**, independently of the turret.

## Rules and formulas

### 1. Rate of fire

```
基础射速 shots/s = 60 / reload                     // reload 单位是 tick
每秒发数 = shots/s × shoot.shots                    // 多管/多发
DPS ≈ 60 / reload × shoot.shots × 单发伤害(ammo)
```

duo: reload 20 → 3 shots/s. smite: reload 100, shots=5 → 3 shots/s × 5 = 15 shots/s.
**`reload` is not milliseconds**; writing it as 20ms is off by 60×.

### 2. Coolant (ReloadTurret.updateCooling)

```
每 tick:  reloadCounter += delta() * baseReloadSpeed()          // 基础 = efficiency ≈ 1
        + coolant.amount * efficiency * heatCapacity * coolantMultiplier   // 有冷却液时额外加
ready 条件: reloadCounter >= reload
```

Substituting duo (`coolant.amount = 0.1`, `coolantMultiplier = 10`):

| Coolant | heatCapacity | extra per tick | total reload speed | effective reload | relative rate |
|---|---|---|---|---|---|
| none | — | 0 | 1.0× | 20 tick | 100% |
| water | 0.4 | 0.10×0.4×10 = 0.4 | 1.4× | ≈14.3 tick | 140% |
| oil | 0.7 | 0.7 | 1.7× | ≈11.8 tick | 170% |
| cryofluid | 0.9 | 0.9 | 1.9× | ≈10.5 tick | 190% |

`coolantMultiplier` is the reload / fire-rate multiplier while coolant is connected, and it differs per turret (v160.7 jar / raw measurements, all 28 turrets checked): from foreshadow at **0.4** to arc at **30**, a span of roughly **75×** — the same barrel of water (heatCapacity 0.4, `coolant.amount` 0.1) adds only +1.6% to foreshadow but +120% to arc.

| Turret | coolantMultiplier | water bonus = 0.1×0.4×mult |
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

Accounting note: **no turret out of the 28 has coolantMultiplier = 0** (the minimum is foreshadow at 0.4), so "0 = unaffected by coolant" has no instance in this version; if the field is set to 0, `amount * … * coolantMultiplier` in `ReloadTurret.updateCooling` stays 0 and coolant adds nothing (`ReloadTurret.java:28-39`).

### 3. Ammo capacity

```
totalAmmo 上限 = maxAmmo                       // 单位是"弹药点"，不是物品数
每种弹药每 1 个物品给 ammoMultiplier 个弹药点     // BulletType.ammoMultiplier 默认 2f
单发消耗 = ammoPerShot
可开火次数 = maxAmmo / ammoPerShot
可接受物品数 = (maxAmmo - totalAmmo) / ammoMultiplier
```

duo: maxAmmo 30, ammoPerShot 1, ammoMultiplier 2 → **15 copper = 15 shots** (not 30 shots).
ripple: maxAmmo 30, ammoPerShot 2 → 15 shots; each shot burns 2 ammo points.

### 4. Aiming and hitting

| Field | Default | Meaning |
|---|---|---|
| `range` | varies per turret | firing distance (px, 8px = 1 tile) |
| `minRange` | 0 | minimum range (arc turrets such as ripple/titan take close targets even at 0) |
| `trackingRange` | 0 (base `range()`) | target lock distance = range + trackingRange - range |
| `shootCone` | 8 (field default) / overridden per turret | angle tolerance between barrel and target (degrees); values >90 (lustre 360, scorch 50) leave almost no blind spot |
| `inaccuracy` | 0 | random bullet spread (degrees) |
| `rotateSpeed` | 0.9~20 per turret | degrees/tick, duo=10 → 600°/s |
| `targetInterval` / `targetSwitchInterval` | 20 / 70 | target acquisition refresh interval (tick) |
| `ammoEjectBack` | 1 | shell-eject recoil visual factor, no effect on numbers |
| `elevation` | -1 | barrel elevation animation, no effect on damage |

`targetAir / targetGround` decide whether air or ground can be engaged: scorch, lancer, arc, hail, ripple, titan and scathe **cannot hit air** (targetAir=0); every other turret is 1. This is the trap beginners hit most — point a scorch at an air unit and the turret never fires at all.

### 5. Heat

```
heatReq = calculateHeat(sideHeat)                     // 从相邻热源取热
efficiency *= clamp(heatReq / heatRequirement, 0, maxHeatEfficiency)
```

`heatRequirement = -1` (the default) means **no heat is needed** and efficiency stays 1; only **afflict (144) and malign (144)** need a heat source, and without one efficiency = 0 and they do not work at all. Heat is a power input, not an overheat penalty.

## Numbers

| Turret | size | hp | range | reload(tick) | shots/s | inacc | rotate | maxAmmo | ammoPerShot | anti-air | anti-ground | coolantMult | heat req | shootCone | class |
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

Every `shots/s` is derived from `60/reload` and can be recomputed row by row (hail: 60/60 = 1.00; swarmer: reload 34.2857 → 60/34.2857 = 1.75; malign: reload 3.5 → 60/3.5 = 17.14; titan: 60/138 = 0.435).

Multi-barrel notes (explicit source assignments; everything else defaults to shots=1): swarmer `shots = 4`; tsunami `shoot.shots = 2`; ripple `shoot.shots = 4`; smite `shots = barrels = 5`.

## Source anchors

- `Turret.java:47-150` field block: `maxAmmo=30`(L47), `ammoPerShot=1`(L49), `heatRequirement=-1`(L53), `inaccuracy=0`(L58), `shootCone=8`(L64), `trackingRange=0`(L72), `minRange=0`(L74), `reloadWhileCharging=true`(L82), `targetAir=true`(L89), `targetGround=true`(L91), `ammoEjectBack=1`(L134), `cooldownTime=20`(L148), `elevation=-1`(L150).
- `Turret.java:342-351` `range()` and `trackingRange()`: ammo can change the range (`peekAmmo().rangeChange`).
- `Turret.java:720` reload main loop: `if(reloadCounter < reload) reloadCounter += delta() * ammoReloadMultiplier() * baseReloadSpeed();`
- `Turret.java:730-735` firing: a shot leaves only once `reloadCounter >= reload`; afterwards `reloadCounter %= reload`.
- `Turret.java:625-676` heat logic: `heatReq <= 0` means the turret does not work at all; `efficiency *= clamp(heatReq/heatRequirement, 0, maxHeatEfficiency)`.
- `ReloadTurret.java:28-39` coolant formula; `:45-51` `baseReloadSpeed()=efficiency`, `canReload()=reloadCounter<reload`.
- `ItemTurret.java:129-219` ammo: `totalAmmo += type.ammoMultiplier`(L168/176/183), capacity test `totalAmmo + ammoMultiplier <= maxAmmo`(L188).
- `Turret.java:194-200` heat UI text: `bar.heatpercent` shows `min(heatReq/heatRequirement, maxHeatEfficiency)`.

## Measurements and counterexamples

**Counterexample 1: reading coolantMultiplier as a fire-rate bonus percentage.**
duo's `coolantMultiplier = 10` reads at face value as "+10% fire rate". The real bonus is 0.1×0.4×10 = +40%. arc's 30 is not "+30%" either, it is +120% (0.1×0.4×30).

**Counterexample 2: assuming `maxAmmo=30` means 30 shots.**
duo takes 1 ammo point per shot and 2 points per item → 15 shots; ripple takes 2 points per shot → 15 shots; titan takes 4 points per shot with maxAmmo=12 → 3 shots. **titan has only 3 shells per magazine**, which is the main reason its DPS lands below the paper figure.

**Counterexample 3: using scorch against air units.**
scorch has `targetAir = 0`, so it **does not fire at all** even when an air unit comes inside its 60px range: this is not a low hit rate, there is simply no target.

**Counterexample 4: assuming a smaller reload always means linearly better rate of fire.**
reload has a floor: firing drops straight into `cooldownTime` (20 tick by default, but the value Turret keeps after `Mathf.clamp`), and shootWarmup needs `minWarmup` before a shot is allowed, so an extremely short reload cannot stack rate of fire without bound.

## Common misconceptions

- ❌ "`rotateSpeed` is rpm". → It is **degrees/tick**; 10 degrees/tick = 600°/s.
- ❌ "turrets pick the best ammo automatically". → They take the first entry of the `ammo` queue (feed order); the player must sort ammo by hand or swap it with an unloader.
- ❌ "`inaccuracy` is a pixel offset". → It is an **angle** (degrees); the lateral deviation is roughly range × tan(inaccuracy).
- ❌ "`targetInterval=20` = 20 seconds". → 20 tick = 0.33 s.
- ❌ "overheat lowers the fire rate". → Vanilla turrets have no overheat penalty; `heat` is only the **input requirement** of afflict/malign.

## See also

- [[COMBAT.BULLET.001]] the bullet fields each ammo feeds (speed/lifetime decide the real reach)
- [[COMBAT.NUMBERS.001]] turret DPS and TTK tables
- [[COMBAT.DAMAGE.001]] the damage pipeline after a hit lands
- [[WORLD.BLOCKS.001]] the 3×3/4×4/5×5 footprint of multi-tile turrets
- [[COMBAT.TURRET.002]] value for cost and selection verdicts for these turrets (DPS/cost, armor knee A*, anti-air gaps)
