---
id: UNIT.ABILITY.001
title: 单位能力——abilities 列表、16 类 Ability 的参数与触发
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/abilities/Ability.java:12-16"
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:286"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/RegenAbility.java:9-30"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/ShieldRegenFieldAbility.java:15-55"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/RepairFieldAbility.java:15-46"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/ForceFieldAbility.java:22-66"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/EnergyFieldAbility.java:24-39"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/ShieldArcAbility.java"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/SuppressionFieldAbility.java:19-64"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/SpawnDeathAbility.java:13-37"
  - "Mindustry-Source/core/src/mindustry/entities/abilities/StatusFieldAbility.java:18-51"
  - "Mindustry-Source/core/src/mindustry/entities/Damage.java:46-71"
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:485-495,1343"
  - "Mindustry-Source/core/src/mindustry/type/unit/NeoplasmUnitType.java:20-32"
  - "Mindustry-Source/core/src/mindustry/content/UnitTypes.java:205,365,400,463,1373,1555,1705,2056,2286,2467,3512,3798,4054,4159,4332"
data: [00-data/units.json]
depends: [UNIT.MOVE.001]
tags: [abilities, 护盾, 治疗, 力场, 抑制, 孢子, 能力]
tokens: 843
---

## 一句话

`UnitType.abilities`（`Seq<Ability>`，UnitType.java:286）是**被动能力列表**，每个 `Ability` 每 tick 收到 `update(unit)` 回调，自己维护 `timer`；原版 62 个单位里只有 **15 个单位挂了 16 个能力实例**（scepter/nova/pulsar/quasar/poly/oct/bryde/oxynoe/aegires/navanax/tecta/elude/quell/disrupt/latum + 所有孢子单位），其余单位的能力列表为空。

## 规则 / 公式

### 1. 基类

```
public class Ability{
    public boolean display = true;   // 是否在单位信息面板显示
    public float data;               // 通用数据槽
    public void update(Unit unit){}  // 每 tick 调用
}
```

能力**不是** weapons：不占 `weapons[]`、不消耗 `reload`、不参与 DPS 统计；它们通过 `timer += Time.delta` 自己控制触发节奏。

### 2. 六种核心能力的数值语义

| 能力 | 触发 | 公式 |
|---|---|---|
| RegenAbility | 每 tick | `heal((maxHealth * percentAmount/100 + amount) * Time.delta)`（RegenAbility.java:30）→ 每秒回 `maxHealth*percentAmount/100*60 + amount*60` |
| ShieldRegenFieldAbility | `timer >= reload` | 半径 `range` 内**友军**加 `amount` 护盾，上限 `max`（:55）→ 每秒 `amount*60/reload` |
| RepairFieldAbility | `timer >= reload` | 半径 `range` 内友军回 `amount`（+ `healPercent%`），同型单位再乘 `sameTypeHealMult` |
| ForceFieldAbility | 持续 | 半径 `radius` 的 n 边形力场，护盾 `max`，每秒回 `regen`，破碎后冷却 `cooldown` tick |
| EnergyFieldAbility | `timer >= reload` | 半径 `range` 内最多 `maxTargets` 个敌人各受 `damage`，友军回 `healPercent%` |
| ShieldArcAbility | 持续 | 一段 `angle` 度的弧形护盾，`max` 上限，`regen`/s，破碎冷却 `cooldown`，`chanceDeflect` 概率完全弹开 |

### 3. 抑制场（SuppressionFieldAbility）——不是减速

```
Damage.applySuppression(team, x, y, range, reload, maxDelay, ...)
  → 对半径 range 内敌方建筑调用 applyHealSuppression(reload + 1f)   // Damage.java:50
  → BuildingComp.healSuppressionTime = max(prev, Time.time + amount)  // :489
  → isHealSuppressed() 期间 heal() 直接 return、修理投影器跳过该建筑    // BuildingComp.java:1343 / MendProjector.java:112
```

## 数值

### 原版全部能力实例（v159.3 源码）

| 单位 | 行号 | 能力与参数 | 换算 |
|---|---|---|---|
| scepter | UnitTypes.java:205 | ShieldRegenField(25, 250, 60t, 60px) | 25 盾/秒，上限 250，半径 7.5 格 |
| nova | :365 | RepairField(10, 240t, 60px) | 10 hp/4s = **2.5 hp/s** |
| pulsar | :400 | ShieldRegenField(20, 40, 300t, 60px) | 4 盾/秒，上限 40 |
| quasar | :463 | ForceField(60px, 0.4/s, 500, 360t) | 上限 500，碎后 6 s 冷却 |
| poly | :1373 | RepairField(5, 480t, 50px) | 0.625 hp/s |
| oct | :1555 | ForceField(140px, 4/s, 7000, 480t, 8 边) | 上限 7000，碎后 8 s |
| bryde | :1705 | ShieldRegenField(20, 40, 240t, 60px) | 5 盾/秒 |
| oxynoe | :2056 | StatusField(overclock, 360t, 360t, 60px) | 每 6 s 给友军 6 s overclock |
| aegires | :2286 | EnergyField(40 伤害, 65t, 180px) | 0.615 s 一次、**65 DPS 范围伤害**，maxTargets 25，healPercent 1.5、sameTypeHealMult 0.5 |
| navanax | :2467 | SuppressionField(默认 reload 90t, maxDelay 90t, range 200px) | 每 1.5 s 抑制 200px 内敌建筑治疗 1.5 s |
| tecta | :3512 | ShieldArc(radius 45, angle 82°, regen 45/60, cooldown 480t, max 2500, chanceDeflect 1) | 0.75 盾/秒，碎后 8 s |
| elude | :3798 | MoveEffect(missileTrailShort) | 纯视觉尾迹 |
| quell | :4054 | SuppressionField(reload 480t, default range 200) | 8 s 一次 |
| disrupt | :4159, :4169 | SuppressionField(reload 900t, range 320px) ×3（两个 active=false 纯视觉） | 15 s 一次 |
| latum | :4332 | SpawnDeath(renale, 5, spread 11px) | 死亡时生成 5 个 renale |
| 孢子系（NeoplasmUnitType） | NeoplasmUnitType.java:20-32 | Regen(percentAmount=1/(70*60)*100) + LiquidExplode(neoplasm) + LiquidRegen(neoplasm) | **70 秒回满血** ≈ 1.4286 %/s |

### 只有定义、原版没有单位使用的 Ability

`ArmorPlateAbility`、`MoveLightningAbility`、`UnitSpawnAbility` —— 在 `entities/abilities/` 下有类，但 `content/` 里没有 `new` 实例（全树 grep "new ArmorPlateAbility" 等 0 命中）。

## 源码锚点

- [src: Ability.java:12-16] `display / data / update(Unit)`。
- [src: UnitType.java:286] `public Seq<Ability> abilities = new Seq<>();`。
- [src: RegenAbility.java:9-11] `percentAmount = 0f`、`amount = 0f`（每 tick 的**固定值**）。
- [src: RegenAbility.java:17] `flat = amount >= 0.001f` 决定面板显示方式。
- [src: ShieldRegenFieldAbility.java:15] `amount=1, max=100, reload=100, range=60`。
- [src: RepairFieldAbility.java:15,22] `amount=1, reload=100, range=60, healPercent=0`，`sameTypeHealMult=1`。
- [src: ForceFieldAbility.java:22-32] `radius=60, regen=0.1, max=200, cooldown=300, sides=6, rotation=0`。
- [src: EnergyFieldAbility.java:24-39] `damage=1, reload=100, range=60, maxTargets=25, healPercent=3`。
- [src: SuppressionFieldAbility.java:19-21] `reload=90, maxDelay=90, range=200`。
- [src: Damage.java:46-60] 抑制只作用于 `build.team != team` 的建筑。
- [src: SpawnDeathAbility.java:37] `spawned = amount + random(randAmount)`。
- [src: NeoplasmUnitType.java:16] 孢子单位 `immunities.addAll(burning, melting)`。

## 实测与反例

**反例 1：以为抑制场降低炮塔攻速。**
`SuppressionFieldAbility` 走 `Damage.applySuppression` → `applyHealSuppression`（Damage.java:50 / BuildingComp.java:489），只**阻止治疗与修理**，对 `reload` 没有任何写入。navanax（SuppressionField range 200）因此克制 mender 阵，而不是克制炮塔。

**反例 2：以为力场是永久无敌。**
quasar 的 `ForceFieldAbility(60, 0.4, 500, 360)`：500 点盾被打穿后进入 `cooldown = 6 s`，这 6 秒内**完全无盾**；每秒只回 0.4。若 DPS 超过 0.4/s，力场只能吸收 500 点就被破。

**反例 3：以为护盾场能叠到无穷。**
`ShieldRegenFieldAbility` 的 `max` 是硬上限（:55 `Math.min(other.shield + amount, max)`），scepter 的 250 点盾打完就停在 250；多台 scepter 只是更快回满，不提高上限。

**反例 4：以为"孢子单位回血"是状态效果。**
`NeoplasmUnitType` 用 `RegenAbility.percentAmount`：70 秒回满（1.4286 %/s），任何禁疗（`healSuppression`）**都不能**阻止——RegenAbility 直接调 `unit.heal()`，而 heal suppression 只作用于建筑（BuildingComp.java:1343）。

**可复算**：aegires 的 EnergyField 每 65 tick 打 40 伤害 → `40 × (60/65) = 36.92` 单目标 DPS；26 个目标同时被扫到 → `36.92 × 26 = 960` 总面积 DPS（`maxTargets = 25`，第 26 个不会被选中）。scepter 护盾场 25 盾/秒 × 3 台 = 75 盾/秒，但 3 台共享 250 上限。

## 常见误解

- ❌ "能力要手动激活"。→ 原版 UnitType 的 abilities 全是被动，`update` 自动跑；主动技能不存在。
- ❌ "`display = false` 的能力不生效"。→ 只是不在面板显示，逻辑照跑（disrupt 的两个视觉抑制场就是 `active = false`）。
- ❌ "能力越多越强"。→ 原版最多 3 个（孢子系），普通单位 0~2 个。
- ❌ "`EnergyFieldAbility` 只打敌人"。→ 同时给友军回血（`healPercent`）。
- ❌ "`ability.data` 是通用冷却"。→ 它只是留给自定义能力存放数据的 float 槽。

## 相关

- [[UNIT.MOVE.001]] 单位移动与 boost
- [[UNIT.AI.001]] 能力与 AI 的关系（被动、不占目标选择）
- [[UNIT.PROGRESSION.001]] 无等级系统，能力不随等级成长
- [[COMBAT.SUPPORT.001]] 护盾层在伤害管线中的位置（治疗/护盾/修理）
