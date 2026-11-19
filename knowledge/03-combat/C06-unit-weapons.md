---
id: COMBAT.UNITWEAPON.001
title: "Unit weapons: weapons[], mount coordinates, mirroring and unit DPS"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "jar:v160.7#mindustry.content.UnitTypes$N → kb-stage/00-data/units.json:1（weapons[] 逐挂点枚举）"
  - "jar:v160.7#bullets → kb-stage/00-data/bullets.json:1（单位弹药 damage）"
  - "Mindustry-Source/core/src/mindustry/type/Weapon.java:31-163"
  - "Mindustry-Source/core/src/mindustry/type/Weapon.java:188-194"
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:286-367"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414-432"
data: [00-data/units.json, 00-data/bullets.json]
depends: [COMBAT.BULLET.001, COMBAT.TURRET.001]
tags: [unit-weapon, weapon, mount, mirror, alternate, unit-dps]
tokens: 1342
---

## In one line

Unit weapons are a handful of entries in `Seq<Weapon> weapons`; `mirror = true` (the default) mirrors the same weapon to the other side of the body, so **in the v160.7 jar reflection a weapon always appears in pairs (`x` and `-x`, e.g. dagger's ±4)**; "unit DPS" must be summed **across every mount**, each mount reloading independently — you cannot compute it as "one weapon = one barrel".

## Rules and formulas

### 1. Per-mount DPS and unit DPS (jar convention)

```
perMountDPS = (60 / mount.reload) * bullet.damage      // reload 单位 = tick
unitDPS     = Σ perMountDPS over all mounts           // jar 的 weapons[] 已逐条枚举镜像挂点
mountCount  = weapons[] 条目数（mirror 武器在 jar 里就是 2 条）
```

**Do not** multiply the jar's mount table by 2 again: dagger's jar data is "2 mounts × reload 26", and summing directly gives 41.5 (see table 1); multiplying by 2 gives the wrong answer.

In the source, `Weapon.dps()` = `(bullet.estimateDPS()/reload) * shoot.shots * 60`, which is a **per-mount** panel value that also counts splash at 75% (`BulletType.java:414-432`), so against a single target it must be discounted.

### 2. Mount coordinates (the easiest part to get wrong)

```
weapon.x  = 沿"武器朝向"的前后偏移（px），正 = 朝前
weapon.y  = 侧向偏移（px），mirror 时另一侧取 -y
weapon.shootX / shootY = 枪口相对挂点的再偏移；默认 shootX=0, shootY=3（朝前 3px 出膛）
weapon.baseRotation   = 固定基准角（avert baseRotation=-35）
weapon.rotate = false → 武器随身体朝向、不独立转向
```

**These are not screen coordinates**: `x` rotates with `mount.rotation`, so the same `x=4, y=2` lands in different places at different facings. In the jar, vanquish's 4 secondary-gun mounts are the two groups `(±12, 8.5)` and `(±12, -9)`.

### 3. Firing conditions

| Field | Default | Effect |
|---|---|---|
| `reload` | 1 tick | reload time |
| `inaccuracy` | 0 | angular spread (degrees) |
| `shootCone` | 5 | firing angle tolerance; 360 = no blind spot (lustre, elude) |
| `rotateSpeed` | 20 | degrees/tick |
| `cooldownTime` | 20 | burst interval / cooldown |
| `alternate` | true | multiple mounts fire in turn (phase offset only, total rate unchanged) |
| `mirror` | true | whether to mirror to the other side (pairs of mounts in the jar) |
| `top` | true | drawn above the body |
| `controllable` | see field | whether the player can control this weapon via ucontrol |
| `alwaysShooting` | false | keep firing regardless of target |
| `autoTarget` | true | acquire targets automatically (false needs a player/logic assignment) |
| `shootWarmupSpeed` | 0.1 | warmup rate; cannot fire before `minWarmup` |
| `shootStatusDuration` | 300 | status duration carried by some weapons |

### 4. Three "damage amplifiers" of unit weapons

1. **Mount count**: in the jar, vanquish has 5 mounts (1 main + 4 secondary), arkyid has 8, scepter has 6 — the count itself is a DPS multiplier.
2. **Multiple weapon entries**: e.g. risso = autocannon ×2 + missile ×1, three independent reloads, DPS summed = 70.3.
3. **Splash/fragments**: artillery-class `splashDamageRadius` reaches 80px (toxopid's gun 80px = 10 tiles), so the effective DPS against groups far exceeds the per-shot number.

## Numbers

### Table 1: unit weapon DPS (v160.7 jar, `00-data/units.json` + `bullets.json`, summed per mount)

> **DPS convention (v160.7 jar, reflection re-measured 2026-11-08)**
> - Formula: `dps = Σmount (bullet.damage × shoot.shots × 60 / reload)` (`dps()` at `Weapon.java:189`; `dpsEstimate = weapons.sumf(Weapon::dps)` at `UnitType.java:1129-1145`).
> - A weapon with `mirror=true` gets a duplicated mount in `UnitType.init()`, and both copies have reload/recoil ×2 (source comment text: since there are now two weapons, the reload and recoil time must be doubled) ⇒ the reload in the jar is already the doubled value, but **shots still has to be multiplied in**: dropping shots reports toxopid's main gun as 220 instead of 440.
> - "Mounts" in the table = the jar's `unit.weapons.size` (mirror duplication included), "unit total DPS" = the sum over all mounts; rows with secondary guns note main gun/total in parentheses. For mounts with shots>1, "per-mount DPS" already includes shots.
> - Counts single-target direct damage only, without splash/pierce/fragment amplification (those are the panel-inflation terms in the reading and are accounted separately against groups).

| unit | weapon (jar name, ×n = mount count) | mounts | reload per mount | per-shot D | per-mount DPS | unit total DPS | note |
|---|---|---|---|---|---|---|---|
| dagger | large-weapon×2 | 2 | 26 | 9 | 20.8 | **41.5** | — |
| mace | flamethrower×2 | 2 | 44 | 74 | 100.9 | **201.8** | — |
| fortress | artillery×2 | 2 | 120 | 20 | 10.0 | **20.0** | splash 80@35 |
| zenith | zenith-missiles×2 (shots 2) | 2 | 80 | 14 | 21.0 | **42.0** | splash 15@25 |
| stell | stell-weapon | 1 | 50 | 30 | 36.0 | **36.0** | — |
| locus | locus-weapon | 1 | 18 | 36 | 120.0 | **120.0** | — |
| precept | precept-weapon | 1 | 80 | 90 | 67.5 | **67.5** | splash 50@20, frag 4 |
| vanquish | vanquish-weapon + point-weapon×4 | 5 | 80 / 44 / 54 | 112.5 / 37.5 | 84.4 + 51.1 + 41.7 | **270.0** | splash 50@20, frag 5 |
| conquer | conquer-weapon | 1 | 100 | 270 | 162.0 | **162.0** | — |
| merui | merui-weapon | 1 | 63 | 30 | 28.6 | **28.6** | splash 30@19 |
| cleroi | cleroi-weapon×2 + point-defense×2 | 4 | 66 / 18 | 22.5 / 28.5 | 20.5 + 95.0 | **230.9** | splash 43@30 |
| tecta | tecta-weapon×2 (shots 3) | 2 | 80 | 38.25 | 86.1 | **172.1** | splash 60@30 |
| collaris | collaris-weapon×2 | 2 | 260 | 195 | 45.0 | **90.0** | splash 120@36, frag 15 |
| quell | quell-weapon×2 | 2 | 110 | 52.5 | 28.6 | **57.3** | frag 1 |
| corvus | corvus-weapon | 1 | 350 | 560 | 96.0 | **96.0** | laser |
| scepter | scepter-weapon×2 (shots 3) + mount×4 | 6 | 90 / 24 / 30 | 70 / 20 | 140.0 + 50.0 + 40.0 | **460.0** | chain lightning 2 |
| reign | reign-weapon×2 | 2 | 18 | 80 | 266.7 | **533.3** | splash 18@13, frag 3 |
| omura | omura-cannon | 1 | 110 | 1250 | 681.8 | **681.8** | railgun |
| atrax | atrax-weapon×2 | 2 | 18 | 13 | 43.3 | **86.7** | liquid bullet (slag) |
| spiroct | spiroct-weapon×2 + mount-purple×2 | 4 | 28 / 36 | 23 / 18 | 49.3 + 30.0 | **158.6** | — |
| arkyid | spiroct-weapon×6 + large-purple×2 | 8 | 18 / 28 / 44 / 90 | 40 / 12 | 133.3 + 85.7 + 54.5 + 8.0 | **563.2** | splash 65@70, chain lightning 3 |
| toxopid | large-purple×2 (shots 2) + toxopid-cannon | 3 | 60 / 210 | 110 / 50 | 220.0 + 14.3 | **454.3** (main gun 440.0) | splash 75@80, chain lightning 5 |
| eclipse | large-laser×2 + large-artillery×4 | 6 | 90 / 18 / 24 | 115 / 15 | 76.7 + 50.0 + 37.5 | **328.3** | splash 65@25 |
| nova | heal-weapon×2 | 2 | 60 | 13 (heal) | 13.0 | **26.0** | non-damage |
| quasar | beam-weapon×2 | 2 | 110 | 45 | 24.5 | **49.1** | laser |
| poly | poly-weapon×2 | 2 | 60 | 12 | 12.0 | **24.0** | inacc 15 |
| risso | mount-weapon×2 + missiles-mount | 3 | 26 / 25 | 9 / 12 | 20.8 + 28.8 | **70.3** | splash 10@25 |
| minke | mount-weapon×2 + artillery×2 | 4 | 20 / 60 | 3 / 20 | 9.0 + 20.0 | **58.0** | splash 40.5@15; 40@22.5 |

Three rows can be recomputed by hand: reign `2 × 60/18 × 80 = 533.3`; omura `60/110 × 1250 = 681.8`; corvus `60/350 × 560 = 96.0`.

### Table 2: version-difference notes (values from the jar, source only as a note)

| unit | field | v160.7 jar | v159.3 source | source location |
|---|---|---|---|---|
| dagger | main weapon reload | 26 ×2 mounts | 13 (single mirror definition) | near UnitTypes.java:107 |
| mace | main weapon reload | 44 ×2 | 22 | same as above |
| reign | main weapon reload | 18 ×2 | 9 | UnitTypes.java:290 block |
| toxopid | main weapon reload / armor | 60 ×2 / **22** | 30 / 13 | UnitTypes.java:909 |
| reign | armor | **30** | 18 | UnitTypes.java:295 |
| stell | per-shot damage | 30 | 40 | UnitTypes.java:2669 |
| precept | per-shot damage | 90 | 120 | UnitTypes.java:2798 |
| nova | main weapon reload | 60 ×2 | 24 | UnitTypes.java:370 |

Per VERSION.md: **numbers follow v160.7, algorithms follow the source**. So dagger's primary "unit DPS" is 41.5; the source's single-definition reading `60/13 × 9 × 2 mounts = 83.1` is the v159.3 convention and is not used here (noted only).

## Source anchors

- `type/Weapon.java:31-163` every field: `name`(L31), `bullet`(L33), `mirror=true`(L39), `alternate=true`(L43), `rotate=false`(L45), `baseRotation=0`(L49), `top=true`(L51), `controllable`(L59), `alwaysShooting`(L63), `autoTarget`(L65), `predictTarget`(L67), `targetInterval=40`(L71), `rotateSpeed=20`(L73), `reload=1`(L75), `inaccuracy=0`(L77), `recoil=1.5`(L81), `cooldownTime=20`(L89), `shootX=0 shootY=3`(L91), `x=5f y=0f`(L93), `shootCone=5`(L105), `rotationLimit=361`(L107), `shootWarmupSpeed=0.1`(L111), `shootStatusDuration=300`(L155).
- `Weapon.java:188-194` `dps() = (bullet.estimateDPS()/reload)*shoot.shots*60`, `shotsPerSec()`.
- `UnitType.java:286` `public Seq<Ability> abilities`; :363-367 commands and stances are auto-assigned from abilities.
- `BulletType.java:414-432` `estimateDPS` (panel DPS and unit DPS share this source; splash counted at 75%).
- `00-data/units.json` each unit's `weapons[]` is already a **per-mount** list (with `x/y`, `reload`, `bullet` id, `mirror`, `alternate`) and can be summed directly.

## Measurements and counterexamples

**Counterexample 1: multiplying the jar's mount table by mirror once more.**
dagger's jar data is 2 mounts at reload 26 each → 41.5 is the unit DPS. Doubling to 83.1 is the "v159.3 source single definition × 2 mounts" convention, which double-counts against the jar's structure.

**Counterexample 2: taking `alternate` as "halved fire rate".**
alternate only makes the left and right fire in turn (a phase offset); both mounts still reload on their own reload, so total rate is unchanged. What really halves the output is one mount getting blocked by `rotate=false` + `shootCone`.

**Counterexample 3: assuming `x/y` are pixel screen coordinates.**
`x` runs along the weapon's facing, `y` sideways; once the unit turns 90° the same mount lands somewhere completely different. Modders often write `x=4` as "4px to the right" and end up with a misaligned muzzle.

**Counterexample 4: judging collaris by its panel DPS.**
The panel counts the 120 splash at 75% → the figure is inflated; the jar direct damage is only 2 × 60/260 × 195 = **90.0** (single target), not 240+.

**Counterexample 5: estimating arkyid from its "barrel count".**
arkyid has 8 mounts (6 small sap guns at reload 18/18/28/28/44/44, plus 2 purple guns at reload 90); direct damage totals **563.2** DPS; looking only at that one "big gun" (12 × 60/90 = 8.0) underestimates its output by two orders of magnitude. Treating all 6 small guns as reload 18 inflates it to 816.0.

**Recomputable**: conquer 270 per shot, reload 100, 1 mount → `60/100 × 270 = 162.0 DPS`; against a 13-armor target `max(270-13, 27) = 257` → `0.6 × 257 = 154.2 DPS`. Armor barely matters because 270 ≫ 13.

## Common misconceptions

- ❌ "each entry of the `weapons` array is one barrel". → In the source mirror defaults to true and generates two mounts; the jar **lists both mounts**.
- ❌ "`shootCone=360` means omnidirectional target acquisition". → It is the **angle range in which firing is allowed**; acquisition is still limited by `targetAir/targetGround` and the weapon's `bullet`.
- ❌ "smaller `reload` is always better, with no floor". → You still wait on `cooldownTime` and `shootWarmup`, and when `reload < cooldownTime` the cooldown governs.
- ❌ "unit weapons can swap ammo freely". → Units have no ammo system, `bullet` is fixed; "swapping ammo" is exclusive to turrets (ItemTurret).
- ❌ "healing weapons deal damage". → nova/mega's heal-weapon runs on `healAmount/healPercent` and takes no health off.

## See also

- [[COMBAT.BULLET.001]] the bullet fields a weapon fires
- [[COMBAT.NUMBERS.001]] using these DPS numbers to get TTK
- [[COMBAT.ARMOR.001]] the unit armor ladder (jar values)
- [[UNIT.ABILITY.001]] abilities and weapons are two parallel systems
- [[UNIT.MOVE.001]] pairing unit speed with weapon range
