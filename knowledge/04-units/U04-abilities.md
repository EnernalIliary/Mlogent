---
id: UNIT.ABILITY.001
title: Unit abilities — the abilities list, and the parameters and triggers of the 16 Ability classes
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
tags: [abilities, shield, healing, force field, suppression, spores, ability]
tokens: 843
---

## In one line

`UnitType.abilities` (`Seq<Ability>`, UnitType.java:286) is a **list of passive abilities**: each `Ability` gets an `update(unit)` callback every tick and keeps its own `timer`. Of the 62 vanilla units only **15 carry the 16 ability instances** (scepter/nova/pulsar/quasar/poly/oct/bryde/oxynoe/aegires/navanax/tecta/elude/quell/disrupt/latum plus every spore unit); all other units have an empty ability list.

## Rules / formulas

### 1. Base class

```
public class Ability{
    public boolean display = true;   // 是否在单位信息面板显示
    public float data;               // 通用数据槽
    public void update(Unit unit){}  // 每 tick 调用
}
```

Abilities are **not** weapons: they do not occupy `weapons[]`, do not consume `reload`, and do not enter DPS accounting; they pace themselves with `timer += Time.delta`.

### 2. What the numbers of the six core abilities mean

| Ability | Trigger | Formula |
|---|---|---|
| RegenAbility | every tick | `heal((maxHealth * percentAmount/100 + amount) * Time.delta)` (RegenAbility.java:30) → per second `maxHealth*percentAmount/100*60 + amount*60` |
| ShieldRegenFieldAbility | `timer >= reload` | **friendly** units within `range` gain `amount` shield, capped at `max` (:55) → per second `amount*60/reload` |
| RepairFieldAbility | `timer >= reload` | friendly units within `range` heal `amount` (+ `healPercent%`), same-type units multiplied again by `sameTypeHealMult` |
| ForceFieldAbility | continuous | n-gon force field of `radius`, shield `max`, `regen` per second, `cooldown` ticks after breaking |
| EnergyFieldAbility | `timer >= reload` | up to `maxTargets` enemies within `range` each take `damage`; friendly units heal `healPercent%` |
| ShieldArcAbility | continuous | an arc shield over `angle` degrees, `max` cap, `regen`/s, `cooldown` after breaking, `chanceDeflect` fully deflects |

### 3. Suppression field (SuppressionFieldAbility) — not a slow

```
Damage.applySuppression(team, x, y, range, reload, maxDelay, ...)
  → 对半径 range 内敌方建筑调用 applyHealSuppression(reload + 1f)   // Damage.java:50
  → BuildingComp.healSuppressionTime = max(prev, Time.time + amount)  // :489
  → isHealSuppressed() 期间 heal() 直接 return、修理投影器跳过该建筑    // BuildingComp.java:1343 / MendProjector.java:112
```

## Numbers

### Every vanilla ability instance (v159.3 source)

| Unit | Line | Ability and parameters | Conversion |
|---|---|---|---|
| scepter | UnitTypes.java:205 | ShieldRegenField(25, 250, 60t, 60px) | 25 shield/s, cap 250, radius 7.5 tiles |
| nova | :365 | RepairField(10, 240t, 60px) | 10 hp/4s = **2.5 hp/s** |
| pulsar | :400 | ShieldRegenField(20, 40, 300t, 60px) | 4 shield/s, cap 40 |
| quasar | :463 | ForceField(60px, 0.4/s, 500, 360t) | cap 500, 6 s cooldown after breaking |
| poly | :1373 | RepairField(5, 480t, 50px) | 0.625 hp/s |
| oct | :1555 | ForceField(140px, 4/s, 7000, 480t, 8-gon) | cap 7000, 8 s after breaking |
| bryde | :1705 | ShieldRegenField(20, 40, 240t, 60px) | 5 shield/s |
| oxynoe | :2056 | StatusField(overclock, 360t, 360t, 60px) | 6 s of overclock to friendlies every 6 s |
| aegires | :2286 | EnergyField(40 damage, 65t, 180px) | once per 0.615 s, **65 DPS area damage**, maxTargets 25, healPercent 1.5, sameTypeHealMult 0.5 |
| navanax | :2467 | SuppressionField(default reload 90t, maxDelay 90t, range 200px) | suppresses enemy building healing within 200px for 1.5 s, every 1.5 s |
| tecta | :3512 | ShieldArc(radius 45, angle 82°, regen 45/60, cooldown 480t, max 2500, chanceDeflect 1) | 0.75 shield/s, 8 s after breaking |
| elude | :3798 | MoveEffect(missileTrailShort) | purely visual trail |
| quell | :4054 | SuppressionField(reload 480t, default range 200) | once every 8 s |
| disrupt | :4159, :4169 | SuppressionField(reload 900t, range 320px) ×3 (two with active=false, visual only) | once every 15 s |
| latum | :4332 | SpawnDeath(renale, 5, spread 11px) | spawns 5 renale on death |
| spore line (NeoplasmUnitType) | NeoplasmUnitType.java:20-32 | Regen(percentAmount=1/(70*60)*100) + LiquidExplode(neoplasm) + LiquidRegen(neoplasm) | **full heal in 70 s** ≈ 1.4286 %/s |

### Abilities that exist only as definitions, with no vanilla unit using them

`ArmorPlateAbility`, `MoveLightningAbility`, `UnitSpawnAbility` — the classes exist under `entities/abilities/`, but `content/` never constructs one (a whole-tree grep for "new ArmorPlateAbility" and the rest returns 0 hits).

## Source anchors

- [src: Ability.java:12-16] `display / data / update(Unit)`.
- [src: UnitType.java:286] `public Seq<Ability> abilities = new Seq<>();`.
- [src: RegenAbility.java:9-11] `percentAmount = 0f`, `amount = 0f` (the **fixed per-tick** value).
- [src: RegenAbility.java:17] `flat = amount >= 0.001f` decides how the panel displays it.
- [src: ShieldRegenFieldAbility.java:15] `amount=1, max=100, reload=100, range=60`.
- [src: RepairFieldAbility.java:15,22] `amount=1, reload=100, range=60, healPercent=0`, `sameTypeHealMult=1`.
- [src: ForceFieldAbility.java:22-32] `radius=60, regen=0.1, max=200, cooldown=300, sides=6, rotation=0`.
- [src: EnergyFieldAbility.java:24-39] `damage=1, reload=100, range=60, maxTargets=25, healPercent=3`.
- [src: SuppressionFieldAbility.java:19-21] `reload=90, maxDelay=90, range=200`.
- [src: Damage.java:46-60] suppression only touches buildings with `build.team != team`.
- [src: SpawnDeathAbility.java:37] `spawned = amount + random(randAmount)`.
- [src: NeoplasmUnitType.java:16] spore units `immunities.addAll(burning, melting)`.

## Tests and counterexamples

**Counterexample 1: assuming the suppression field cuts turret fire rate.**
`SuppressionFieldAbility` goes through `Damage.applySuppression` → `applyHealSuppression` (Damage.java:50 / BuildingComp.java:489): it only **blocks healing and repair** and writes nothing to `reload`. navanax (SuppressionField range 200) therefore counters mender clusters, not turrets.

**Counterexample 2: assuming a force field is permanent invulnerability.**
quasar's `ForceFieldAbility(60, 0.4, 500, 360)`: once the 500-point shield is punched through it enters `cooldown = 6 s`, and for those 6 s there is **no shield at all**; regen is only 0.4/s. If incoming DPS exceeds 0.4/s the field absorbs 500 points and breaks.

**Counterexample 3: assuming shield fields stack without bound.**
`ShieldRegenFieldAbility`'s `max` is a hard cap (:55 `Math.min(other.shield + amount, max)`), so scepter's 250-point shield stops at 250; more scepters only refill it faster, they never raise the cap.

**Counterexample 4: assuming "spore units regenerate" is a status effect.**
`NeoplasmUnitType` uses `RegenAbility.percentAmount`: full heal in 70 s (1.4286 %/s), and no heal suppression (`healSuppression`) **can** stop it — RegenAbility calls `unit.heal()` directly, while heal suppression only applies to buildings (BuildingComp.java:1343).

**Recomputable**: aegires' EnergyField deals 40 damage every 65 ticks → `40 × (60/65) = 36.92` single-target DPS; with 26 targets swept at once → `36.92 × 26 = 960` total area DPS (`maxTargets = 25`, so the 26th is never selected). scepter's shield field is 25 shield/s × 3 = 75 shield/s, but the 3 share one 250 cap.

## Common misconceptions

- ❌ "abilities must be activated manually." → every vanilla UnitType ability is passive and `update` runs automatically; active skills do not exist.
- ❌ "an ability with `display = false` does not take effect." → it is only hidden from the panel, the logic still runs (disrupt's two visual suppression fields are exactly `active = false`).
- ❌ "more abilities means stronger." → vanilla caps at 3 (the spore line); ordinary units have 0~2.
- ❌ "`EnergyFieldAbility` only hits enemies." → it also heals friendlies (`healPercent`).
- ❌ "`ability.data` is a shared cooldown." → it is just a float slot reserved for custom abilities to store data in.

## Related

- [[UNIT.MOVE.001]] unit movement and boost
- [[UNIT.AI.001]] how abilities relate to AI (passive, no target selection)
- [[UNIT.PROGRESSION.001]] no level system, so abilities never grow with level
- [[COMBAT.SUPPORT.001]] where the shield layer sits in the damage pipeline (healing/shield/repair)
