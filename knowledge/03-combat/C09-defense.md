---
id: COMBAT.DEFENSE.001
title: 防御工事——墙体、门、护盾与修理器的数值与判定顺序
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "MBO/gamedata/v160.7/gamedata.json blocks[].raw（wall/door/shield/mend 各字段）"
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:1762-1778,467-483,1929"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ShieldWall.java:15-17,44,80,102"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ForceProjector.java:32-45,206-250"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/MendProjector.java:26-31,113"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/OverdriveProjector.java:23-29,110"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ShockwaveTower.java:25-29,87"
data: [00-data/blocks.json]
depends: [COMBAT.ARMOR.001, COMBAT.SUPPORT.001]
tags: [墙, 门, 护盾, 力场, 修理, 超速, 防御方块]
tokens: 892
---

## 一句话

原版防御是**四层**：墙体（纯 hp+armor）→ 护盾墙/力场（先吃伤害、破损进冷却）→ 修理/超速（把 hp 与射速抬回来）→ 炮塔（真正输出）；判定顺序是 **bullet.damage → 护甲 applyArmor → 护盾吸收 → 建筑 hp**，护盾吃的是**已经过护甲**的伤害。

## 规则 / 公式

### 1. 子弹打建筑的完整顺序

```
1. damage = bullet.type.buildingDamage(bullet)                        // 含 buildingDamageMultiplier
2. if(!pierceArmor) damage = applyArmor(damage, block.armor * t.armorMultiplier * t.blockArmorMultiplier)
3. building.damage(bullet, source, damage)                            // ShieldWall 等在此切走护盾
4. ShieldWall: shieldTaken = broken ? 0 : min(shield, damage); shield -= shieldTaken; 剩余进 hp
5. hp <= 0 → 方块被摧毁（掉落残骸/爆炸）
```

### 2. 墙体

墙体只提供 **hp + armor**，不阻挡子弹穿透（`pierceBuilding = true` 的子弹会穿）。`Block.armor` 走与单位完全相同的 `applyArmor`（见 [[COMBAT.ARMOR.001]]），所以 **armor 14 的 tungsten-wall 能免疫一切 ≤15.5 伤的单发**（`0.9×damage <= armor` 的拐点）。

### 3. 门

`door`/`door-large`/`blast-door` 是 `AutoDoor`：单位靠近自动开、离开关。开着的门**不挡子弹也不挡路**，是"限时墙"。blast-door 2×2 有 armor 14，是全游戏最硬的通行口。

### 4. 护盾墙 ShieldWall

```
shield = clamp(shield + regenSpeed * edelta(), 0, shieldHealth)       // regenSpeed = 2/s
breakCooldown = 600 tick = 10 s                                       // 破盾后 10 秒不回复
```

护盾吃满 `min(shield, damage)` 的**全额**（不衰减），所以 shielded-wall 的等效血量是 `4160 + 900 = 5060`（对单发不穿透的子弹）。

### 5. 力场投影仪 ForceProjector（3×3）

不是血量，而是**累积池 buildup**：

```
吸收: buildup += bullet.damage（仅当 !broken 且子弹落在六边形半径内）
破碎: buildup >= shieldHealth + phaseShieldBoost*phaseHeat → broken = true, buildup = shieldHealth
回复: buildup -= delta() * scale
      scale = cooldownNormal(1.75)                      // 正常
            × cooldownLiquid(1.5) × (1 + (heatCapacity-0.4)*0.9)  // 有冷却液
      broken 时 scale = cooldownBrokenBase(0.35)
```

- 750 盾、无冷却液：回满需要 `750 / (1.75×60) ≈ 7.1 s`；
- 被打碎后要先回 750 点才解除 broken：`750 / (0.35×60) ≈ 35.7 s`（这段时间完全不吸收）；
- 有冷却液（水 heatCapacity 0.4）：scale ×1.5 → 4.8 s 回满。

### 6. 超速投影仪 OverdriveProjector

```
applyBoost(realBoost(), reload + 1)     // speedBoost = 1.5, speedBoostPhase = 0.75 → 最高 2.25
BuildingComp.delta() = Time.delta * timeScale      // L1929
```

它加速的是**建筑的 delta**，因此：炮塔 reload 走得更快（射速 ×1.5）、工厂建造更快、修理器 heal 更快。`canOverdrive = false` 的方块（墙、核心）无效。

### 7. 修理器与修理炮塔

```
MendProjector: heal = maxHealth * (12 + phaseHeat*12)/100 * efficiency   // 每次 reload 250 tick
RepairTurret:  heal = repairSpeed * strength * edelta() * multiplier       // 持续
```

## 数值

### 墙体与门（v160.7 反射 raw）

| 方块 | 尺寸 | hp | armor | 特殊 |
|---|---|---|---|---|
| copper-wall | 1×1 | 320 | 0 | — |
| titanium-wall | 1×1 | 440 | 0 | — |
| plastanium-wall | 1×1 | 500 | 0 | `absorbLasers = true`（挡激光） |
| thorium-wall | 1×1 | 800 | 0 | — |
| phase-wall | 1×1 | 600 | 0 | 受击相位化（免伤窗口） |
| surge-wall | 1×1 | 920 | 0 | `lightningChance = 0.05` 反击 |
| beryllium-wall | 1×1 | 520 | 2 | — |
| tungsten-wall | 1×1 | 720 | 14 | — |
| carbide-wall | 1×1 | 1080 | 16 | 原版最硬 1×1 |
| shielded-wall | 2×2 | 4160 | 15 | shieldHealth 900 |
| door | 1×1 | 400 | 0 | AutoDoor |
| door-large | 2×2 | 1600 | 0 | AutoDoor |
| blast-door | 2×2 | 2800 | 14 | AutoDoor |

### 护盾/支援方块

| 方块 | 尺寸 | hp | 关键参数 |
|---|---|---|---|
| force-projector | 3×3 | 360 | shieldHealth 750、radius 101.7 px、sides 6、phaseUseTime 350、phaseShieldBoost 400、phaseRadiusBoost 80 |
| shield-projector | 3×3 | 360 | BaseShield（护盾投射器，可移动护盾） |
| mender | 1×1 | 80 | range 40、reload 200、heal 12%/次、phaseRangeBoost 20 |
| mend-projector | 2×2 | 320 | range 85、reload 250、heal 12%/次、phaseRangeBoost 50 |
| overdrive-projector | 2×2 | 175 | range 80、reload 60、speedBoost 1.5、speedBoostPhase 0.75、useTime 400 |
| shockwave-tower | 3×3 | 915 | range 170（v160.7 raw）/ 110（源码默认）、reload 80/90、bulletDamage 160、falloffCount 20 |
| repair-point | 1×1 | 40 | repairSpeed 0.45/s |
| repair-turret | 2×2 | 205 | repairSpeed 3/s |
| radar | 1×1 | 60 | 提供视野 |

### 核心（被摧毁即失败）

| 方块 | 尺寸 | hp | armor | unitCapModifier |
|---|---|---|---|---|
| core-shard | 3×3 | 1100 | 0 | 8 |
| core-foundation | 4×4 | 3500 | 0 | 16 |
| core-nucleus | 5×5 | 6000 | 0 | 24 |
| core-bastion | 4×4 | 4500 | 5 | 15 |
| core-citadel | 5×5 | 16000 | 10 | 15 |
| core-acropolis | 6×6 | 30000 | 15 | 15 |

## 源码锚点

- `BuildingComp.java:1762-1778` `collision(Bullet)`：护甲在此结算，再交给子类 `damage(...)`。
- `BuildingComp.java:467-483` `applyBoost(intensity, duration)`：timeScale 取最大强度。
- `BuildingComp.java:1929` `delta() = Time.delta * timeScale`。
- `ShieldWall.java:15-17` shieldHealth 900 / breakCooldown 600 / regenSpeed 2。
- `ShieldWall.java:102` `shieldTaken = broken() ? 0f : Math.min(shield, damage)`。
- `ForceProjector.java:32-45` phaseUseTime 350、phaseRadiusBoost 80、phaseShieldBoost 400、radius 101.7、sides 6、shieldHealth 700、cooldownNormal 1.75、cooldownLiquid 1.5、cooldownBrokenBase 0.35、crashDamageMultiplier 2。
- `ForceProjector.java:217-245` buildup 累加、破碎判定、`broken` 解除条件 `buildup <= 0`。
- `ForceProjector.java:270` `absorb = !broken && Intersector.isInRegularPolygon(sides, x, y, realRadius(), ...)`。
- `MendProjector.java:26-31` reload 250、range 60、healPercent 12、phaseBoost 12、phaseRangeBoost 50。
- `OverdriveProjector.java:110` `other.applyBoost(realBoost(), reload + 1f)`。
- `ShockwaveTower.java:87` `waveDamage = min(bulletDamage, bulletDamage*falloffCount/targets.size)`。

## 实测与反例

**反例 1：以为护盾先吃伤害、再由护甲减免。**
顺序相反：`BuildingComp.collision` 先 applyArmor，再调 `ShieldWall.damage`。所以对 shielded-wall（armor 15）打 20 伤子弹：护甲后 5 点，护盾只掉 5，而不是 20。

**反例 2：以为力场被打碎后立刻恢复。**
broken 后 scale 掉到 0.35，且必须先回满 750 才解除 broken——**35.7 秒真空期**。此时用 spectre（428 DPS）可以直接把 3×3 的 360 hp 打穿。

**反例 3：以为门能挡子弹。**
AutoDoor 打开时不参与碰撞。想"挡路又挡弹"只能用 blast-door 并保持关闭（会挡自己人）。

**反例 4：以为超速只影响炮塔。**
影响所有 `canOverdrive` 建筑的 delta——工厂、修理器、钻头全加速；但**墙与核心不加速**。

**可复算**：thorium-wall 800 hp、armor 0 对 dagger（单发 9、3 发/s）：`800/9 = 89 发`，即 `89/3 ≈ 29.6 s`。同墙对 spectre（单发 50、8.57 发/s）：`16 发`，`1.87 s`。换成 carbide-wall（1080 hp、armor 16）对 undefended dagger：单发 `max(9-16,0.9)=0.9` → **1200 发 ≈ 400 s**；但对 titan（单发 350）：`334` → 4 发。

## 常见误解

- ❌ "墙越贵越好"。→ 对高伤单体（titan/malign）armor 16 的 carbide-wall 只值 1080 hp；对密集小口径，armor 才是王道。
- ❌ "shieldHealth 是护盾墙的血"。→ ShieldWall 是额外 900 点缓冲，且 10 s 破盾冷却；ForceProjector 是**累积池**模型，不是血量。
- ❌ "修理器能修墙"。→ MendProjector 只治 `hasHealth` 的友方建筑与单位（`canHeal = !checkSuppression()`），且会受 `suppression` 状态压制。
- ❌ "shockwave-tower 数值两版一样"。→ v160.7 raw：range 170、reload 80；v159.3 源码默认：range 110、reload 90。以 v160.7 为准。
- ❌ "核心护甲高就安全"。→ 核心 armor 最高 15，对 malign（单发 70）仍有 55 点/发。

## 相关

- [[COMBAT.ARMOR.001]] 建筑护甲与 applyArmor
- [[COMBAT.SUPPORT.001]] 修理与护盾的单位侧
- [[COMBAT.TURRET.001]] 炮塔数值（防御的输出层）
- [[COMBAT.WAVE.001]] 什么波次会压垮这四层
