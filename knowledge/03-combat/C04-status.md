---
id: COMBAT.STATUS.001
title: "Status effects: multiplier fields, duration, stacking and refresh, reaction damage"
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
tags: [status-effect, status, multiplier, slow, reaction, disarm, duration]
tokens: 747
---

## In one line

Status effects **do not stack layers, they only refresh the duration**: re-applying the same status takes `max(old remaining time, new duration)`; the multiplier fields of different statuses are **multiplied frame by frame** into the unit's `speedMultiplier/healthMultiplier/damageMultiplier/reloadMultiplier`, so "freezing (−20% health) + corroded" multiplies rather than adds.

## Rules and formulas

### 1. Applying and refreshing

```
apply(effect, duration):
  if(effect == none || isImmune(effect)) return          // 免疫表直接挡掉
  遍历现有 statuses:
     同 effect       → entry.time = max(entry.time, duration)   // 刷新，不叠层
     互为 opposite   → effect.applyTransition(...)              // 触发反应，返回
  否则新增一条 entry（reactive 类如 shocked/blasted 不直接入表）
```

- **Duration is in tick**: `60*8 = 480` is 8 seconds.
- **permanent = true** never decays: overdrive, boss, dynamic, and the `999999f` that SpawnGroup applies to wave units.
- Statuses with `reactive = true` (shocked, blasted) **can only be produced by a reaction**, never applied directly.

### 2. Per-frame aggregation (StatusComp.update)

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

**The smaller healthMultiplier, the more fragile** (it appears as a divisor in the damage pipeline: `applyArmor(...)/healthMultiplier`). freezing at 0.8 → incoming damage ×1.25.

### 3. Damage statuses

| status | mechanism | damage per second |
|---|---|---|
| burning | `damage = 0.167`/tick | 10.0 |
| melting | `damage = 0.3`/tick | 18.0 |
| corroded | `intervalDamage = 20`, `intervalDamageTime = 15` tick | 20/15×60 = 80.0 |
| overdrive | `damage = -0.01`/tick (healing) | +0.6 healing/s |

### 4. Reactions (transitionDamage / affinity)

| combination | result | source |
|---|---|---|
| burning + wet/freezing | wet is burning's opposite → extinguished at once, `transitionDamage = 8` applied | StatusEffects.java:24-33 |
| burning + tarred | piercing damage 8, plus a `min(time+result.time, 300)` extension | :28-32 |
| melting + tarred | piercing damage 8, capped at 200 tick | :111-115 |
| freezing + blasted | piercing damage 18 | :46-51 |
| wet + shocked | non-piercing damage 14 | :83-89 |
| tarred + burning / melting | `result.set(burning, result.time + time)` extra extension | :147-150 |

**Reactions outrank stacking**: when the target is wet and a burning bullet lands, burning never attaches — only 8 points of reaction damage apply.

### 5. Terrain statuses

While a unit is **on the ground and not hovering**, every frame runs `apply(floor.status, floor.statusDuration)`: standing on slag keeps melting up, on oil keeps tarred, on water/ice wet/freezing. Air units (`isGrounded()==false`) and `hovering` units are unaffected by terrain statuses.

## Numbers

| status | speedMult | healthMult | damageMult | reloadMult | other | source line |
|---|---|---|---|---|---|---|
| none | 1 | 1 | 1 | 1 | empty | :18 |
| burning | 1 | 1 | 1 | 1 | damage 0.167/tick, transitionDamage 8 | :20-34 |
| freezing | 0.6 | 0.8 | 1 | 1 | transitionDamage 18 | :36-53 |
| unmoving | 0 | 1 | 1 | 1 | fully immobilized | :55-58 |
| slow | 0.4 | 1 | 1 | 1 | show=false | :60-66 |
| fast | 1.6 | 1 | 1 | 1 | — | :68-73 |
| wet | 0.94 | 1 | 1 | 1 | transitionDamage 14 | :75-92 |
| muddy | 0.94 | 1 | 1 | 1 | show=false | :94-100 |
| melting | 0.8 | 0.8 | 1 | 1 | damage 0.3/tick | :102-117 |
| sapped | 0.7 | 0.8 | 1 | 1 | — | :119-125 |
| electrified | 0.7 | 1 | 1 | **0.6** | — | :127-133 |
| spore-slowed | 0.8 | 1 | 1 | 1 | — | :135-140 |
| tarred | 0.6 | 1 | 1 | 1 | spreads with burning/melting | :142-151 |
| overdrive | 1.15 | 0.95 | **1.4** | 1 | damage −0.01/tick, permanent | :153-161 |
| overclock | 1.15 | 1 | 1.15 | **1.25** | — | :163-170 |
| shielded | 1 | **3.0** | 1 | 1 | show=false | :172-176 |
| boss | 1 | 1.5 | **1.3** | 1 | permanent | :178-183 |
| shocked | 1 | 1 | 1 | 1 | reactive (reaction only) | :185-188 |
| blasted | 1 | 1 | 1 | 1 | reactive | :190-193 |
| corroded | 1 | 1 | 1 | 1 | intervalDamage 20 / 15 tick | :195-202 |
| disarmed | 1 | 1 | 1 | 1 | **disarm = true** (cannot fire) | :204-208 |
| invincible | 1 | **+∞** | 1 | 1 | fully immune to damage | :210-213 |
| dynamic | — | — | — | — | `dynamic=true`, for logic modding | :215-219 |

Field defaults (v160.7 reflection, `00-data/rt_list_StatusEffect.json`): damageMultiplier / healthMultiplier / speedMultiplier / reloadMultiplier / buildSpeedMultiplier / dragMultiplier all **1.0**; transitionDamage **0.0**; disarm / intervalDamagePierce / dynamic / permanent / reactive **false**; effectChance **0.15**; show **true**.

## Source anchors

- `type/StatusEffect.java:19-69` fields: `damageMultiplier`(L19), `healthMultiplier`(L21), `speedMultiplier`(L23), `reloadMultiplier`(L25), `buildSpeedMultiplier`(L27), `dragMultiplier`(L29), `transitionDamage`(L31), `disarm`(L33), `intervalDamagePierce`(L41), `effectChance = 0.15`(L43), `dynamic`(L51), `show`(L53), `permanent`(L65? see end of class), `reactive`.
- `StatusComp.java:36-70` `apply(effect, duration)`: immunity → refresh `max(time,duration)` → reaction → add new.
- `StatusComp.java:98-100` `isImmune = type.immunities.contains(effect)`.
- `StatusComp.java:178-235` `update()`: terrain status, `time -= Time.delta`, multiplier product, `disarmed |= effect.disarm`.
- `StatusComp.java:24` transient fields used for aggregation: `speedMultiplier/damageMultiplier/healthMultiplier/reloadMultiplier/buildSpeedMultiplier/dragMultiplier/armorOverride(-1)`.
- `content/StatusEffects.java:18-220` every status definition and the reaction table.

## Measurements and counterexamples

**Counterexample 1: assuming the same status stacks in layers.**
Three burning shots in a row are not 3 layers at 30 dps — the duration refreshes to `max` and the damage stays 0.167/tick. Stacking damage requires **different** statuses (burning + melting = 28 dps).

**Counterexample 2: assuming wet reduces damage.**
wet only has `speedMultiplier = 0.94` and **reduces no damage**; its value is "extinguishes burning + gets detonated by shocked for 14 damage".

**Counterexample 3: getting the direction of healthMultiplier backwards.**
shielded `healthMultiplier = 3` reads like "health ×3", but it actually divides damage by 3 → incoming damage is only 1/3, an effective 3× health. Conversely freezing at 0.8 → damage ×1.25.

**Counterexample 4: hitting a wet unit with burning.**
While the target stands in water (wet), burning does not take effect at all — only 8 points of transitionDamage settle — so flame turrets are nearly dead weight on water maps.

**Recomputable**: with overdrive + boss both present, `damageMultiplier = 1.4 × 1.3 = 1.82`, `healthMultiplier = 0.95 × 1.5 = 1.425` (incoming damage ÷1.425).

## Common misconceptions

- ❌ "statuses have a stack limit / layer count". → Vanilla has **no notion of layers**, only duration refresh.
- ❌ "`disarmed` is a slow". → It is a **fire lock**; speed is unchanged.
- ❌ "corroded is 20 damage per frame". → 20 damage every 15 tick = 80 dps.
- ❌ "terrain statuses only affect movement". → slag applies melting (18 damage/s plus 0.8 speed, 0.8 health).
- ❌ "the immunity table is global". → Each UnitType keeps its own `immunities` (e.g. atrax is immune to burning/melting).

## See also

- [[COMBAT.DAMAGE.001]] where healthMultiplier sits in the damage pipeline
- [[COMBAT.ARMOR.001]] immunities and armorOverride
- [[UNIT.ABILITY.001]] how abilities apply statuses periodically
- [[UNIT.MOVE.001]] terrain statuses and movement multipliers
