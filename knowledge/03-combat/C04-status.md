---
id: COMBAT.STATUS.001
title: 状态效果——倍率字段、时长、叠加与刷新、反应伤害
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/type/StatusEffect.java:19-69"
  - "Mindustry-Source/core/src/mindustry/entities/comp/StatusComp.java:36-70"
  - "Mindustry-Source/core/src/mindustry/entities/comp/StatusComp.java:178-235"
  - "Mindustry-Source/core/src/mindustry/content/StatusEffects.java:18-220"
  - "KB/00-data/rt_list_StatusEffect.json (v160.7 反射字段表)"
data: [00-data/status.json]
depends: [COMBAT.DAMAGE.001]
tags: [状态效果, status, 倍率, 减速, 反应, disarm, 持续时间]
tokens: 747
---

## 一句话

状态效果**不叠加层数、只刷新时长**：再次施加同一 status 时取 `max(旧剩余时长, 新时长)`；不同 status 的倍率字段**逐帧相乘**汇总到单位的 `speedMultiplier/healthMultiplier/damageMultiplier/reloadMultiplier`，所以"冻结(−20% 血) + 腐蚀"是相乘不是相加。

## 规则 / 公式

### 1. 施加与刷新

```
apply(effect, duration):
  if(effect == none || isImmune(effect)) return          // 免疫表直接挡掉
  遍历现有 statuses:
     同 effect       → entry.time = max(entry.time, duration)   // 刷新，不叠层
     互为 opposite   → effect.applyTransition(...)              // 触发反应，返回
  否则新增一条 entry（reactive 类如 shocked/blasted 不直接入表）
```

- **时长单位是 tick**：`60*8 = 480` 就是 8 秒。
- **permanent = true** 的永不衰减：overdrive、boss、dynamic、以及波次单位由 SpawnGroup 施加的 `999999f`。
- `reactive = true` 的 status（shocked、blasted）**只能靠反应产生**，不能直接施加。

### 2. 每帧聚合（StatusComp.update）

```
armorOverride = -1; speed=damage=health=reload=buildSpeed=drag=1; disarmed=false
for each entry:
    entry.time -= Time.delta
    if(entry.time <= 0 && !permanent) 移除
    else:
        speedMultiplier   *= entry.effect.speedMultiplier
        healthMultiplier  *= entry.effect.healthMultiplier
        damageMultiplier  *= entry.effect.damageMultiplier
        reloadMultiplier  *= entry.effect.reloadMultiplier
        buildSpeedMultiplier *= entry.effect.buildSpeedMultiplier
        dragMultiplier    *= entry.effect.dragMultiplier
        disarmed |= entry.effect.disarm
```

**healthMultiplier 越"小"越脆**（因为它作为除数出现在伤害管线里：`applyArmor(...)/healthMultiplier`）。freezing 0.8 → 受击伤害 ×1.25。

### 3. 伤害类 status

| status | 机制 | 每秒伤害 |
|---|---|---|
| burning | `damage = 0.167`/tick | 10.0 |
| melting | `damage = 0.3`/tick | 18.0 |
| corroded | `intervalDamage = 20`，`intervalDamageTime = 15` tick | 20/15×60 = 80.0 |
| overdrive | `damage = -0.01`/tick（回血） | +0.6 治疗/s |

### 4. 反应（transitionDamage / affinity）

| 组合 | 结果 | 来源 |
|---|---|---|
| burning + wet/freezing | wet 是 burning 的 opposite → 立即熄灭并结算 `transitionDamage = 8` | StatusEffects.java:24-33 |
| burning + tarred | 穿透伤害 8，并 `min(time+result.time, 300)` 延长 | :28-32 |
| melting + tarred | 穿透伤害 8，上限 200 tick | :111-115 |
| freezing + blasted | 穿透伤害 18 | :46-51 |
| wet + shocked | 非穿透伤害 14 | :83-89 |
| tarred + burning / melting | `result.set(burning, result.time + time)` 额外延长 | :147-150 |

**反应优先于叠加**：目标身上有 wet 时打 burning 弹，burning 不会挂上，只会结算 8 点反应伤害。

### 5. 地形状态

单位**贴地且不悬停**时，每帧 `apply(floor.status, floor.statusDuration)`：站在 slag 上持续 melting、站在 oil 上持续 tarred、站在水/冰上 wet/freezing。飞行单位（`isGrounded()==false`）与 `hovering` 单位不受地形状态影响。

## 数值

| status | speedMult | healthMult | damageMult | reloadMult | 其它 | 源码行 |
|---|---|---|---|---|---|---|
| none | 1 | 1 | 1 | 1 | 空 | :18 |
| burning | 1 | 1 | 1 | 1 | damage 0.167/tick，transitionDamage 8 | :20-34 |
| freezing | 0.6 | 0.8 | 1 | 1 | transitionDamage 18 | :36-53 |
| unmoving | 0 | 1 | 1 | 1 | 完全定身 | :55-58 |
| slow | 0.4 | 1 | 1 | 1 | show=false | :60-66 |
| fast | 1.6 | 1 | 1 | 1 | — | :68-73 |
| wet | 0.94 | 1 | 1 | 1 | transitionDamage 14 | :75-92 |
| muddy | 0.94 | 1 | 1 | 1 | show=false | :94-100 |
| melting | 0.8 | 0.8 | 1 | 1 | damage 0.3/tick | :102-117 |
| sapped | 0.7 | 0.8 | 1 | 1 | — | :119-125 |
| electrified | 0.7 | 1 | 1 | **0.6** | — | :127-133 |
| spore-slowed | 0.8 | 1 | 1 | 1 | — | :135-140 |
| tarred | 0.6 | 1 | 1 | 1 | 与 burning/melting 互扩 | :142-151 |
| overdrive | 1.15 | 0.95 | **1.4** | 1 | damage −0.01/tick，permanent | :153-161 |
| overclock | 1.15 | 1 | 1.15 | **1.25** | — | :163-170 |
| shielded | 1 | **3.0** | 1 | 1 | show=false | :172-176 |
| boss | 1 | 1.5 | **1.3** | 1 | permanent | :178-183 |
| shocked | 1 | 1 | 1 | 1 | reactive（只能反应产生） | :185-188 |
| blasted | 1 | 1 | 1 | 1 | reactive | :190-193 |
| corroded | 1 | 1 | 1 | 1 | intervalDamage 20 / 15 tick | :195-202 |
| disarmed | 1 | 1 | 1 | 1 | **disarm = true**（不能开火） | :204-208 |
| invincible | 1 | **+∞** | 1 | 1 | 完全免伤 | :210-213 |
| dynamic | — | — | — | — | `dynamic=true`，逻辑魔改用 | :215-219 |

字段默认值（v160.7 反射，`00-data/rt_list_StatusEffect.json`）：damageMultiplier / healthMultiplier / speedMultiplier / reloadMultiplier / buildSpeedMultiplier / dragMultiplier 全为 **1.0**；transitionDamage **0.0**；disarm / intervalDamagePierce / dynamic / permanent / reactive **false**；effectChance **0.15**；show **true**。

## 源码锚点

- `type/StatusEffect.java:19-69` 字段：`damageMultiplier`(L19)、`healthMultiplier`(L21)、`speedMultiplier`(L23)、`reloadMultiplier`(L25)、`buildSpeedMultiplier`(L27)、`dragMultiplier`(L29)、`transitionDamage`(L31)、`disarm`(L33)、`intervalDamagePierce`(L41)、`effectChance = 0.15`(L43)、`dynamic`(L51)、`show`(L53)、`permanent`(L65？见类尾)、`reactive`。
- `StatusComp.java:36-70` `apply(effect, duration)`：免疫→刷新 `max(time,duration)`→反应→新增。
- `StatusComp.java:98-100` `isImmune = type.immunities.contains(effect)`。
- `StatusComp.java:178-235` `update()`：地形状态、`time -= Time.delta`、倍率相乘、`disarmed |= effect.disarm`。
- `StatusComp.java:24` 聚合用的 transient 字段：`speedMultiplier/damageMultiplier/healthMultiplier/reloadMultiplier/buildSpeedMultiplier/dragMultiplier/armorOverride(-1)`。
- `content/StatusEffects.java:18-220` 全部 status 定义与反应表。

## 实测与反例

**反例 1：以为同类 status 会叠层。**
连打 3 发 burning：不是 3 层 30 dps，而是刷新到 `max` 时长，伤害仍是 0.167/tick。想叠伤害只能靠**不同** status（burning + melting = 28 dps）。

**反例 2：以为 wet 能减伤。**
wet 只有 `speedMultiplier = 0.94`，**不减伤害**；它的价值是"熄灭 burning + 被 shocked 引爆 14 伤"。

**反例 3：把 healthMultiplier 当加成方向搞反。**
shielded `healthMultiplier = 3`：看着像"血量 ×3"，实际是伤害除以 3 → 受到伤害仅 1/3，等效 3 倍血。反过来 freezing 0.8 → 伤害 ×1.25。

**反例 4：用 burning 打湿身单位。**
目标站在水里（wet）时，burning 完全不生效，只结算 8 点 transitionDamage —— 火焰类炮塔打水图几乎废掉。

**可复算**：overdrive + boss 同时存在时 `damageMultiplier = 1.4 × 1.3 = 1.82`，`healthMultiplier = 0.95 × 1.5 = 1.425`（受伤 ÷1.425）。

## 常见误解

- ❌ "status 有叠加上限/层数"。→ 原版**没有层数概念**，只有时长刷新。
- ❌ "`disarmed` 是减速"。→ 是**禁火**，速度不变。
- ❌ "corroded 是每帧 20 伤"。→ 每 15 tick 一次 20 伤 = 80 dps。
- ❌ "地形状态只影响移动"。→ slag 会挂 melting（每秒 18 伤 + 0.8 速、0.8 血）。
- ❌ "免疫表是全局的"。→ 每个 UnitType 自己维护 `immunities`（如 atrax 免疫 burning/melting）。

## 相关

- [[COMBAT.DAMAGE.001]] healthMultiplier 在伤害管线中的位置
- [[COMBAT.ARMOR.001]] immunities 与 armorOverride
- [[UNIT.ABILITY.001]] 能力如何周期性施加 status
- [[UNIT.MOVE.001]] 地形状态与移动倍率
