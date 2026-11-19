---
id: COMBAT.ARMOR.001
title: "Armor and resistances: the subtraction formula, 10% floor, armor piercing and immunity"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/Damage.java:659-661"
  - "Mindustry-Source/core/src/mindustry/Vars.java:133"
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:1762-1778"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:187-191"
  - "Mindustry-Source/core/src/mindustry/world/Block.java:191-192,644-645"
  - "Mindustry-Source/core/src/mindustry/entities/comp/StatusComp.java:98-100"
  - "Mindustry-Source/core/src/mindustry/content/UnitTypes.java:125,510,698,2439,2779,2853,2964"
data: [00-data/units.json, 00-data/blocks.json]
depends: [COMBAT.DAMAGE.001]
tags: [armor, armor, piercing, immunity, floor-damage, block-armor]
tokens: 839
---

## In one line

Armor is **subtraction**, not a percentage: `actual damage = max(damage − armor, 0.1 × damage)`; so armor is nearly immunity against **small calibers** and nearly useless against **large calibers** — a unit with armor 26 loses only 0.9 to a 9-damage bullet and 324 to a 350-damage one.

## Rules and formulas

### 1. The single formula (units and blocks share it)

```
applyArmor(damage, armor) = max(damage - armor, minArmorDamage * damage)
minArmorDamage = 0.1                     // 常量，不可配置
```

**Derivation**: the source `Damage.applyArmor` is exactly this one line. It means:

- When `damage - armor >= 0.1*damage`, i.e. `armor <= 0.9*damage`, it is pure subtraction;
- When `armor > 0.9*damage` you are in the floor zone, damage is always `0.1*damage`, and **more armor buys nothing**;
- Knee: `damage* = armor / 0.9`. Armor 26 → knee 28.9; any single hit ≤28.9 only ever gets through 10%.

### 2. Blocks enter through a different door but use the same formula

```
damage = other.type.buildingDamage(other)                        // 含 buildingDamageMultiplier
if(!t.pierceArmor)
    damage = Damage.applyArmor(damage, block.armor * t.armorMultiplier * t.blockArmorMultiplier)
```

| coefficient | applies to | default |
|---|---|---|
| `armorMultiplier` | the armor value itself (AP rounds can amplify armor) | 1 |
| `blockArmorMultiplier` | armor of **blocks only** | 1 |
| `buildingDamageMultiplier` | damage to blocks only | 1 |
| `pierceArmor` | when true, **skips applyArmor entirely** | false |

### 3. Three ways to "bypass armor"

1. `pierceArmor = true` (BulletType field): skips armor completely.
2. `splashDamagePierce = true`: the splash portion skips armor.
3. status `armorOverride`: only `dynamic`-class statuses can set it; when `>=0` it **overrides** the target's armor (0 also overrides, `-1` means no override).

### 4. Immunity is not implemented through armor

```
isImmune(effect) = type.immunities.contains(effect)     // StatusComp.java:98-100
```

Immunity only blocks **status**, **not damage**. Vanilla has no armor-like "damage immunity" mechanism at all (apart from the invincible status and shields).

### 5. Where armor values come from

- Units: `UnitType.armor`, static, does not change with level (there is no level system, see [[UNIT.PROGRESSION.001]]).
- Blocks: `Block.armor` (default 0), used by walls/cores.
- Status: `armorOverride` (dynamic).

## Numbers

### Actual damage matrix (rows = per-shot damage D, columns = armor A)

| D \ A | 0 | 2 | 4 | 6 | 9 | 13 | 16 | 20 | 26 |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 7 | 5 | 3 | 0.9 | 0.9 | 0.9 | 0.9 | 0.9 |
| 18 | 18 | 16 | 14 | 12 | 9 | 5 | 2 | 1.8 | 1.8 |
| 50 | 50 | 48 | 46 | 44 | 41 | 37 | 34 | 30 | 24 |
| 80 | 80 | 78 | 76 | 74 | 71 | 67 | 64 | 60 | 54 |
| 140 | 140 | 138 | 136 | 134 | 131 | 127 | 124 | 120 | 114 |

### Hits required (1000 hp target, recomputed from the formula above)

| D \ A | 0 | 9 | 16 | 26 |
|---|---|---|---|---|
| 9 | 111 | 1111 | 1111 | 1111 |
| 18 | 56 | 111 | 500 | 556 |
| 50 | 20 | 24.4 | 29.4 | 41.7 |
| 80 | 12.5 | 14.1 | 15.6 | 18.5 |

`A 9-damage bullet needs 1111 shots against a 1000 hp, armor 26 target` (1000/0.9), while an 80-damage bullet needs only 18.5. **This is the quantified source of "small guns do nothing against heavy armor".**

### Unit armor ladder (v160.7 jar reflection, hp / armor)

| armor | representative units (hp / armor) |
|---|---|
| 0 | dagger(150), crawler(150), flare(70), mono(100), poly(400), alpha(150) |
| 1~2 | elude(600/1), nova(200/1), risso(280/2), renale(500/2) |
| 3~5 | atrax(600/3), horizon(340/3), mega(460/3), mace(550/4), pulsar(320/4), minke(600/4), merui(680/4), quell(6000/4), zenith(700/5), cleroi(1100/5), tecta(6500/5) |
| 6~9 | stell(850/6), obviate(2300/6), anthicus(2700/7), locus(2100/8), fortress(900/9), quasar(640/9), spiroct(1000/9), collaris(18000/9), disrupt(12000/9) |
| 10~16 | quad(6000/10), precept(5000/11), sei(11000/12), aegires(12000/12), latum(20000/12), corvus(18000/14), arkyid(8000/14), vela(8200/16), omura(22000/16) |
| 17~22 | antumbra(7200/17), scepter(9000/20), navanax(20000/20), vanquish(11000/20), toxopid(22000/22), eclipse(22000/22) |
| 26~30 | conquer(22000/26), reign(24000/30) |

**Version note**: the table takes the v160.7 jar (authoritative numbers). The same-named fields in the v159.3 source are generally lower — toxopid 13 (`UnitTypes.java:909`), eclipse 13(:1264), reign 18(:295), scepter 10(:194), arkyid 6(:805), vela 9(:507), corvus 9(:578), spiroct 5(:746), quad 8(:1460). Per VERSION.md, conflicts always resolve to the jar, so every armor expression in this article uses jar values.

### Block armor (v160.7 reflection raw)

| block | hp | armor | note |
|---|---|---|---|
| copper-wall | 320 | 0 | — |
| beryllium-wall | 520 | 2 | — |
| tungsten-wall | 720 | 14 | — |
| carbide-wall | 1080 | 16 | — |
| shielded-wall | 4160 | 15 | also has shieldHealth 900 |
| blast-door | 2800 | 14 | AutoDoor |
| core-bastion | 4500 | 5 | — |
| core-citadel | 16000 | 10 | — |
| core-acropolis | 30000 | 15 | — |

### Immunity table (v159.3 UnitTypes.java, 7 entries)

| unit | immunities |
|---|---|
| mace | burning |
| vela | burning |
| atrax | burning, melting |
| navanax | burning |
| precept | burning, melting |
| vanquish | burning, melting |
| conquer | burning, melting |

## Source anchors

- `Damage.java:659-661`: `return Math.max(damage - armor, minArmorDamage * damage);`
- `Vars.java:133`: `public static final float minArmorDamage = 0.1f;` (v160.7 reflection confirms const=0.1)
- `BuildingComp.java:1762-1778` `collision(Bullet)`: `if(!t.pierceArmor) damage = Damage.applyArmor(damage, block.armor * t.armorMultiplier * t.blockArmorMultiplier);`
- `BulletType.java:187-191`: `pierceArmor=false`, `armorMultiplier=1f`, `blockArmorMultiplier=1f`
- `Block.java:191-192`: `public float armor = 0f;` (comment: "damage absorption, similar to unit armor")
- `StatusComp.java:98-100`: `isImmune = type.immunities.contains(effect)`
- `UnitTypes.java:125/510/698/2439/2779/2853/2964`: the 7 immunities assignments (mace / vela / atrax / navanax / precept / vanquish / conquer)

## Measurements and counterexamples

**Counterexample 1: treating armor as a "damage reduction percentage".**
18 damage vs 13 armor: the percentage reading gives 18×(1−13%) = 15.7. The actual `max(18−13, 1.8) = 5`. **A 3× gap**, and "armor 100" never turns into 100% reduction.

**Counterexample 2: assuming splash ignores armor.**
Splash goes through the same `damage(amount)`, so armor is subtracted as usual. spectre's 40-damage splash against a 16-armor target: `max(40−16, 4)= 24`, then ×0.4 out at the edge → **9.6**.

**Counterexample 3: assuming AP rounds (pierceArmor) halve armor.**
The source is `if(pierceArmor) damagePierce(...)` — `applyArmor` is **not called at all**. Blocks are the same (BuildingComp L1767).

**Counterexample 4: taking armor as "status immunity".**
Armor only governs damage. Immunity to burning has to be written into `unit.immunities`; toxopid has armor 22 (v160.7 jar; v159.3 source says 13) yet **catches fire all the same** (it has no burning immunity — it is not in the immunity table).

**Recomputable**: dagger at 9 per shot against tungsten-wall (armor 14): `max(9−14, 0.9) = 0.9/shot`, so 720 hp needs **800 shots**; switch to conquer (360 per shot): `max(360−14, 36) = 346`, only 3 shots.

## Common misconceptions

- ❌ "armor can stack up to 100% immunity". → The floor is 10%; it never reaches zero.
- ❌ "blockArmorMultiplier also works on units". → It only affects block armor (that one line in BuildingComp).
- ❌ "immunity = damage immunity". → Immunity only covers statuses.
- ❌ "armor goes up with difficulty/waves". → Vanilla armor is fixed; difficulty only scales hp and damage (rules.unitHealth / unitDamage).
- ❌ "a unit with armor 0 has an empty armor field". → `armor = 0f` is a valid value, `applyArmor(D, 0) = D`.

## See also

- [[COMBAT.DAMAGE.001]] where armor sits in the damage pipeline
- [[COMBAT.STATUS.001]] healthMultiplier / armorOverride
- [[COMBAT.NUMBERS.001]] armor curves and TTK
- [[COMBAT.DEFENSE.001]] wall and shield blocks
