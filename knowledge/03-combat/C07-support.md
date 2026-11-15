---
id: COMBAT.SUPPORT.001
title: 治疗、护盾与修理——heal / shield / mend / repairSpeed
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/comp/HealthComp.java:42-117"
  - "Mindustry-Source/core/src/mindustry/entities/comp/ShieldComp.java:57-81"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/MendProjector.java:26-115"
  - "Mindustry-Source/core/src/mindustry/world/blocks/units/RepairTurret.java:33,74,207"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ForceProjector.java:32-115"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/ShieldWall.java:14-80"
  - "MBO/gamedata/v160.7/gamedata.json (mender/mend-projector/force-projector/shielded-wall/repair-* raw)"
data: [00-data/blocks.json]
depends: [COMBAT.DAMAGE.001, COMBAT.ARMOR.001]
tags: [治疗, 护盾, 修理, mend, repairSpeed, 力场, 护盾墙]
tokens: 705
---

## 一句话

治疗有**三种完全不同的量纲**：单位 `heal(amount)` 是**平量 HP**、修理方块 `healPercent` 是**每次事件按目标最大生命百分比**、修理炮塔 `repairSpeed` 是**每秒 HP**；护盾则一律是"先于血量被扣的独立血条"，且**破碎不溢出**（溢出部分才进血量）。

## 规则 / 公式

### 1. 单位治疗（HealthComp）

```
heal(amount)      → health += amount; clampHealth()        // 平量，上限 maxHealth
healFract(f)      → heal(f * maxHealth)                    // 比例
heal()            → health = maxHealth（同时清 dead 标记，复活用）
damageContinuous  → amount * Time.delta（每 tick 结算的伤害/治疗）
```

治疗**不会**超过 `maxHealth`（`clampHealth`），且**不区分伤害来源**——无视护甲直接加血。

### 2. 修理投影器（MendProjector）

```
每 reload tick 一次：
    range_real = range + phaseHeat * phaseRangeBoost
    对范围内所有友方建筑：
        other.heal(other.maxHealth() * (healPercent + phaseHeat * phaseBoost) / 100 * efficiency)
```

**关键：治疗量是"目标最大生命的百分比"**，不是固定值。所以同一台 mend-projector 修 3×3 大核心比修 1×1 墙"数值上多得多"，但**修复时间占比一样**。

- `reload = 250` tick（≈4.17 s）
- `healPercent = 12`（每次 12% 最大生命）
- 等效 `= 12% / 4.17s ≈ 2.88% maxHP/s`
- `phaseBoost = 12`、`phaseRangeBoost = 50`：相位（相织布）满时再加 12% 并扩 50px 射程

### 3. 修理炮塔/修理点（RepairTurret）

```
target.heal(repairSpeed * strength * edelta() * multiplier)     // RepairTurret.java:207
每秒修复量 = repairSpeed * 60 * strength * multiplier
```

`repairSpeed` 本身是"每 tick HP"，UI 里乘 60 显示为 /s：`stats.add(Stat.repairSpeed, repairSpeed * 60f, StatUnit.perSecond)`。

### 4. 护盾

```
单位护盾（ShieldComp）: rawDamage 时先扣 shield，剩余才扣 health
                        shield -= min(shield, amount)          // 不溢出、不浪费
方块护盾:
    ForceProjector: shieldHealth，环形拦截子弹（每发按 shieldDamage 累积 buildup）
    ShieldWall:      shieldHealth 900，regenSpeed 恢复
力场被打破 → broken 状态 + breakCooldown 期间不恢复
```

## 数值

| 方块 / 单位 | 字段 | 值 | 每秒等效 |
|---|---|---|---|
| mender | range / reload | 40px / 200 tick | 每次事件 12%（默认 healPercent）→ 3.6%/s |
| mend-projector | range / reload | 85px / 250 tick | 12% / 4.17s = **2.88% maxHP/s** |
| repair-point | repairSpeed | 0.45 /tick | **27 HP/s** |
| repair-turret | repairSpeed | 3.0 /tick | **180 HP/s** |
| force-projector | shieldHealth | 750（v160.7） | 半径 radius=101.7px ≈ 12.7 格；phaseUseTime 350 |
| shielded-wall | shieldHealth | 900 | 2×2，armor 15，主血量 4160 |
| core-shard / foundation / nucleus | hp | 1100 / 3500 / 6000 | 治疗基数差异 5.5 倍 |

相位加成：`phaseRangeBoost` mender 20、mend-projector 50；满相位时治疗从 12% 涨到 24%（+phaseBoost 12）。

单位"自带护盾"来自波次：`SpawnGroup.getShield(wave) = max(shields + shieldScaling*(wave-begin), 0)`，与单位类型无关，是**波次配置**给的。

## 源码锚点

- `HealthComp.java:42-45` `heal()` 满血复活；`:103-106` `clampHealth`；`:109-117` `heal(amount)` / `healFract`。
- `HealthComp.java:71-79` `damage(amount)` 直接 `health -= amount`（护甲已在上游结算）。
- `ShieldComp.java:57-81` `rawDamage`：`shieldDamage = min(max(shield,0), amount)`，剩余进 health。
- `MendProjector.java:26-30` `reload=250`、`range=60`、`healPercent=12`、`phaseBoost=12`、`phaseRangeBoost=50`；`:113` 的 heal 调用；`:62` UI 的 `repairTime = 100/healPercent*reload/60` 秒。
- `RepairTurret.java:33` `repairSpeed = 0.3f` 类默认（Blocks 覆盖为 0.45 / 3.0，见 `Blocks.java:6389,6401`）；`:207` 实际 heal 调用；`:74` 每秒显示。
- `ForceProjector.java:32-39` `phaseUseTime=350`、`radius=101.7`、`shieldHealth=700`（v160.7 raw 为 750）；`:59-67` 子弹累积 `buildup += bullet.type.shieldDamage(bullet)`。
- `ShieldWall.java:15,44,80` `shieldHealth=900`、`shield = shieldHealth`、`shield += regenSpeed*edelta()`。
- `game/SpawnGroup.java:76-78` `getShield(wave)`。

## 实测与反例

**反例 1：把 mend-projector 的 12 当成"12 HP"。**
`healPercent = 12` 是 **12% 目标最大生命**。修 6000 血 nucleus 每次事件回 **720 HP**，修 320 血铜墙只回 38.4 HP。给"小方块"配大投影器是巨大浪费。

**反例 2：以为 repairSpeed 是每秒。**
`repairSpeed = 3` 是**每 tick 3 HP** → 180 HP/s。写成 3 HP/s 会低估 60 倍（这是全库最常见的 /tick 与 /s 混写错误）。

**反例 3：以为护盾破碎会溢出伤害。**
`shieldDamage = min(shield, amount)`，`amount -= shieldDamage` —— 溢出**会**进血量（这部分是对的），但护盾本身**不会为负**，不存在"破盾额外反伤"。

**反例 4：用治疗抵消高护甲单位的伤害。**
治疗无视护甲，但量级极小：repair-turret 180 HP/s vs spectre 对 0 甲 428.6 DPS，**修不回来**；要抗住必须靠护盾型方块（force-projector 的 750 点独立血条）。

**可复算**：mend-projector 修 3×3 核心（3500 HP，core-foundation）：每次 `3500 × 12% = 420`，4.17 s 一次 → 100.7 HP/s。修满血需要 `3500/100.7 ≈ 34.8 s`。

## 常见误解

- ❌ "治疗能超过最大生命"。→ `clampHealth` 硬上限。
- ❌ "护盾按护甲减免后再扣"。→ 护盾吃的是**已经过护甲**的数值，护盾自身无护甲。
- ❌ "修理器能修单位"。→ MendProjector 只修**建筑**（indexer.eachBlock + player.team）；单位靠 repair-turret/能力。
- ❌ "力场护盾有血量条就一定能扛"。→ `buildup` 满后进入 broken 冷却，期间完全失效。
- ❌ "shielded 状态是加护盾"。→ 它是 `healthMultiplier = 3`（减伤 2/3），不是护盾值。

## 相关

- [[COMBAT.DAMAGE.001]] 护盾吸收发生在护甲之后
- [[COMBAT.DEFENSE.001]] 防御方块的 hp/护盾全表
- [[UNIT.ABILITY.001]] RepairField/ShieldRegen 能力
- [[COMBAT.NUMBERS.001]] 用 DPS 对比治疗量
