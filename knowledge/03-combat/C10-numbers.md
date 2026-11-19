---
id: COMBAT.NUMBERS.001
title: "Combat number worked examples: the DPS definition, cross-layer accounting and TTK"
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "jar:v160.7#blocks[].raw → kb-stage/00-data/turrets.json:1（reload/health/ammoPerShot）"
  - "jar:v160.7#units → kb-stage/00-data/units.json:1（health/armor/weapons[].reload）"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/ContinuousBulletType.java:11,33-35,72"
  - "Mindustry-Source/core/src/mindustry/type/Weapon.java:188-190（dps 公式）"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/Turret.java:720-735,329-331"
  - "Mindustry-Source/core/src/mindustry/entities/Damage.java:659-661（applyArmor）"
data: [00-data/turrets.json, 00-data/units.json, 00-data/bullets.json]
depends: [COMBAT.TURRET.001, COMBAT.ARMOR.001, COMBAT.BULLET.001, COMBAT.UNITWEAPON.001]
tags: [DPS, TTK, armor-curve, formula, cross-layer, continuous-damage]
tokens: 1211
---

## In one line

Every combat number can be recomputed from three formulas: `fire rate = 60/reload`, `per-shot actual damage d = max(D − A, 0.1D)`, `DPS = fire rate × shots × d`; **the same weapon can differ by 5× between the "bullet layer / carrier layer / field layer" conventions** (meltdown panel 4680 vs field 936), because armor is pure subtraction and every gun has a knee at `A* = 0.9D`.

## Rules and formulas

### 1. The three-layer conventions (where the numbers come from)

| layer | formula | source |
|---|---|---|
| bullet layer estimateDPS | `(damage + splashDamage*0.75) * (pierce ? clamp(pierceCap,1,2) : 1) + fragDPS*fragBullets/2` | `BulletType.java:414-432` |
| carrier layer (turret/unit weapon) | `shots/reload*60 * ammo.estimateDPS()` | `Turret.java:329-331`, `Weapon.java:188-190` |
| continuous layer (laser/flame) | `damage / damageInterval * 60`, `damageInterval = 5` tick ⇒ **×12** | `ContinuousBulletType.java:11,33-35` |

Why the continuous layer is ×12 and not ×60: damage is not settled per tick but once every `damageInterval` (5 tick), applying the full `damage` (`if(b.timer(1, damageInterval)) applyDamage(b)` at `ContinuousBulletType.java:72`), so only 12 settlements per second.

### 2. The three field-layer formulas (every table below is generated from them)

```
射速 shots/s = 60 / reload                       // reload 单位是 tick，不是秒
单发实伤 d   = max(D - A, 0.1 * D)               // 护甲只做减法 + 10% 保底
DPS          = 射速 * 发数(shots 或挂点数) * d
TTK(秒)      = 目标生命 / DPS
```

Unit weapons and turrets share the same formula: a turret's "shots" is `shoot.shots` (multi-barrel / burst), a unit weapon's is the mount count N (`mirror=true` expands into N records in `units.json`), and under `alternate` the effective rate = `N/reload`. For turret shots, ammo types and the full 28-gun parameters see [[COMBAT.TURRET.001]]; this article only cites them and does not repeat them.

## Numbers

### Table 1: cross-layer comparison (same weapon, three accounting methods)

| weapon | layer | per-shot D | estimateDPS | carrier-layer DPS | field single-target DPS | panel/field |
|---|---|---|---|---|---|---|
| duo (copper) | turret | 9 | 9 | 27.0 | 27.0 | 1.00× |
| spectre (graphite) | turret | 50 | 50 | 428.6 | 428.6 | 1.00× |
| hail (graphite) | turret | 20 + splash 33 | 44.75 | 44.8 | 20.0 | **2.24×** |
| titan (thorium) | turret | 350 + splash 350 | 612.5 | 266.3 | 152.2 | **1.75×** |
| smite (surge) | turret | 250×5 | 250 | 750.0 | 750.0 | 1.00× |
| mace (flamethrower) | unit | 74 (pierce 2) | 148 | 403.6 | 201.8 | **2.00×** |
| reign (reign-weapon) | unit | 80 + splash 18 | 187 | 1246.7 | 533.3 | **2.34×** |
| meltdown (laser) | turret | 78/5tick | 4680 | 3120 | **936** | **5.00×** |

Reading: splash, piercing and fragments are "panel amplifiers"; they only return 1.00× when firing at a single target without piercing. meltdown's 4680 comes from `estimateDPS = damage*100/damageInterval*3` (`ContinuousBulletType.java:39-44`, assuming "100 tick of uptime and 3 pierced targets"), while 3120 is what `Turret.estimateDps()` produces by dividing that already-per-second estimateDPS by `shots/reload*60` once more — **neither is the real value during firing**.

### Table 3: white-target measurements (real executor, 2026-11-19)

Ignore the formulas: put the turret into a scene with an **unkillable target** and count the health lost each tick. Protocol: v160.7 executor, 1800 tick, target placed on the legal band at `(range+minRange)/2` (air-only turrets get a flare target), target and turret refilled every tick, 200 ammo in stock.

| turret (ammo) | panel DPS (`60/reload×shots×D`) | white-target measured DPS | measured/panel | where the difference comes from |
|---|---|---|---|---|
| duo (copper) | 27.0 | 26.1 | 0.97× | only warmup and flight time |
| salvo (copper) | 124.1 | 119.5 | 0.96× | same as above |
| spectre (graphite) | 428.6 | 483.3 | 1.13× | the panel treats reload as pure fire rate; real bursts are denser |
| fuse (titanium) | 339.4 | 143.0 | 0.42× | only 1 of the 3 shots lands on the same point target |
| hail (graphite) | 20.0 | 30.2 | 1.51× | the 33 splash also lands on the same target |
| scatter (scrap) | 20.0 | 53.6 | 2.68× | the 33 splash stacks in full (and it only hits air) |
| cyclone (metaglass) | 36.0 | 244.6 | **6.79×** | 45 splash plus fragments settle repeatedly on one target |
| ripple (graphite) | 80.0 | 50.0 | 0.63× | arcing spread; some of the 4 shots miss |
| foreshadow (surge-alloy) | 405.0 | **0** | 0.00× | not one hit in 1800 tick: the shell is too slow and the spread too wide |
| titan (thorium) | 114.1 | **0** | 0.00× | same; a small point target is almost always missed |

Four conclusions:

1. **The panel formula only holds for direct-fire single targets**: duo/salvo agree within 5%, spectre is off by 13% (its burst rhythm is denser than `reload`).
2. **Splash and fragments are amplifiers** against a single target, not a discount: cyclone measures 6.8× its panel because one shell's 45 splash and its fragments all settle on that same target.
3. **Arcing shells (ripple/foreshadow/titan) go the other way**: the panel assumes "every shot hits", but the real hit rate on a small point target is very low, and the bigger the gun the more obvious it is — titan carries only 3 shells per magazine (see above), so 1800 tick of misses is normal.
4. So "field DPS" must state the **target shape** (single/group, static/moving, point/large), otherwise one gun can report anything from 0 to 6.8× its panel.

Reproduce: `python tools/dps.py box <block>` first to check the legal firing band, then `python tools/dps.py measure <block> <ammo>`; `tests/dps/` holds the pure-math layer plus a single live regression that only runs duo.

### Table 2: unit weapon layer DPS (v160.7 units.json, converted by mount count)

| unit | weapon | mounts × reload(tick) | effective rate/s | per-shot D | DPS |
|---|---|---|---|---|---|
| dagger | large-weapon | 2 × 26 | 4.615 | 9 | **41.5** |
| mace | flamethrower | 2 × 44 | 2.727 | 74 | **201.8** |
| toxopid | large-purple-mount (shots 2) | 2 × 60 | 4.000 | 110 | **440.0** |
| reign | reign-weapon | 2 × 18 | 6.667 | 80 | **533.3** |
| omura | omura-cannon | 1 × 110 | 0.545 | 1250 | **681.8** |
| corvus | corvus-weapon | 1 × 350 | 0.171 | 560 | **96.0** |

Unit weapon parameters (mount x/y, shootCone, alternate) are in [[COMBAT.UNITWEAPON.001]]; this layer has no notion of "multi-barrel", only mount count. toxopid here counts only the main weapon 2×large-purple-mount (440.0); adding toxopid-cannon (1×210, 50 per shot) = 454.3, consistent with table 1 in C06.

Convention (v160.7 jar re-measured): `dps = Σmount (bullet.damage × shoot.shots × 60 / reload)`; a `mirror=true` mount has been duplicated into two guns and the jar's reload is already the ×2 value (`UnitType.java:1129-1145`, `Weapon.java:189`), but `shots` must still be multiplied — toxopid has `shots=2` per mount, so it is 2 mounts × 2 shots × 110 × 60/60 = 440.0, not 220.0.

### Table 3: TTK (seconds; targets: dagger 150hp/0 armor, fortress 900hp/9 armor, toxopid 22000hp/**22 armor**)

toxopid's armor uses the v160.7 jar value 22 (`00-data/units.json`); the v159.3 source `UnitTypes.java:909` says 13. Using 13 underestimates TTK by about 1/3 (see counterexample 3).

| turret | DPS(0 armor) | vs dagger | vs fortress(9) | vs toxopid(22) |
|---|---|---|---|---|
| duo | 27.0 | 5.56 | 333.33 | 8148.15 |
| scorch | 170.0 | 0.88 | 11.25 | 1294.12 |
| salvo | 31.0 | 4.83 | 72.50 | 7088.89 |
| cyclone | 36.0 | 4.17 | 250.00 | 6111.11 |
| swarmer | 70.0 | 2.14 | 128.57 | 3142.86 |
| diffuse | 82.0 | 1.83 | 14.06 | 578.95 |
| lancer | 105.0 | 1.43 | 9.16 | 248.59 |
| breach | 127.5 | 1.18 | 7.89 | 232.80 |
| titan | 152.2 | 0.99 | 6.07 | 154.27 |
| spectre | 428.6 | 0.35 | 2.56 | 91.67 |
| smite | 750.0 | 0.20 | 1.24 | 32.16 |
| malign | 1200.0 | 0.12 | 0.86 | 26.74 |
| meltdown | 936.0 | 0.16 | 1.09 | 32.74 |

Three recomputations (each doable on a calculator):
- spectre vs toxopid: `d = max(50−22, 5) = 28`; `DPS = 60/7 × 28 = 240.0`; `TTK = 22000/240 = 91.67 s`.
- duo vs toxopid: `d = max(9−22, 0.9) = 0.9` (hits the floor); `DPS = 3 × 0.9 = 2.7`; `TTK = 22000/2.7 = 8148.15 s ≈ 2.26 hours`.
- meltdown vs fortress: `d = max(78−9, 7.8) = 69`; settled once every 5 tick ⇒ `DPS = 69/5×60 = 828`; `TTK = 900/828 = 1.09 s`.

### Table 4: armor curve (DPS; A = target armor)

| turret | 0 | 4 | 9 | 13 | 16 | 20 | 22 | 26 |
|---|---|---|---|---|---|---|---|---|
| duo (9) | 27.0 | 15.0 | 2.7 | 2.7 | 2.7 | 2.7 | 2.7 | 2.7 |
| scorch (17) | 170.0 | 130.0 | 80.0 | 40.0 | 17.0 | 17.0 | 17.0 | 17.0 |
| salvo (15) | 31.0 | 22.8 | 12.4 | 4.1 | 3.1 | 3.1 | 3.1 | 3.1 |
| cyclone (6) | 36.0 | 12.0 | 3.6 | 3.6 | 3.6 | 3.6 | 3.6 | 3.6 |
| diffuse (41) | 82.0 | 74.0 | 64.0 | 56.0 | 50.0 | 42.0 | 38.0 | 30.0 |
| lancer (140) | 105.0 | 102.0 | 98.2 | 95.2 | 93.0 | 90.0 | 88.5 | 85.5 |
| breach (85) | 127.5 | 121.5 | 114.0 | 108.0 | 103.5 | 97.5 | 94.5 | 88.5 |
| titan (350) | 152.2 | 150.4 | 148.3 | 146.5 | 145.2 | 143.5 | 142.6 | 140.9 |
| spectre (50) | 428.6 | 394.3 | 351.4 | 317.1 | 291.4 | 257.1 | 240.0 | 205.7 |
| smite (250×5) | 750.0 | 738.0 | 723.0 | 711.0 | 702.0 | 690.0 | 684.0 | 672.0 |
| malign (70) | 1200.0 | 1131.4 | 1045.7 | 977.1 | 925.7 | 857.1 | 822.9 | 754.3 |
| meltdown (78/5t) | 936.0 | 888.0 | 828.0 | 780.0 | 744.0 | 696.0 | 672.0 | 624.0 |

Knee `A* = 0.9D` (past it you always take 10%): duo 8.1, scorch 15.3, salvo 13.5, cyclone 5.4, hail 18, spectre 45, lancer 126, breach 76.5, titan 315, smite 225, malign 63, meltdown 70.2. Left of `A*` the slope is `−rate×shots`; to the right it is flat.

## Source anchors

- `entities/Damage.java:659-661`: `applyArmor = max(damage - armor, minArmorDamage * damage)`.
- `Vars.java:133`: `minArmorDamage = 0.1f` (the 10% floor).
- `entities/bullet/BulletType.java:414-432`: `estimateDPS()`, including the `splashDamage*0.75` and `pierceCap` amplification.
- `entities/bullet/ContinuousBulletType.java:11` `damageInterval = 5f`; `:33-35` `continuousDamage = damage/damageInterval*60`; `:72` settles once every 5 tick.
- `type/Weapon.java:188-190`: `dps() = (bullet.estimateDPS()/reload)*shoot.shots*60`; `:75` `reload` defaults to 1 (tick).
- `world/blocks/defense/turrets/Turret.java:720-735`: `reloadCounter += delta()*ammoReloadMultiplier()*baseReloadSpeed()`, fires once it reaches `reload`.
- `Turret.java:329-331`: `estimateDps() = shots/reload*60 * ammo.estimateDPS() * potentialEfficiency * timeScale`.
- `content/Blocks.java:4331` meltdown `ContinuousLaserBulletType(78)`; `:4323` `reload = 90f`; `:4325` `shootDuration = 230f`.
- `content/Blocks.java:4643` titan thorium `ArtilleryBulletType(2.5f, 350)` + `splashDamage = 350`; `:3466` hail `(3f,20)` + `splashDamage = 33`.
- `content/UnitTypes.java:107` dagger source `reload = 13f` (v160.7 jar has 26 per mirrored mount).

## Measurements and counterexamples

**Counterexample 1: taking panel DPS as field DPS.**
meltdown's panel is 4680 (estimateDPS convention) but only 936 during actual firing, a **5× gap**; hail's panel 44.8 against 20 on a single target, 2.24×; titan's panel 266.3 against 152.2 on a direct hit. The panel only fits "same type, same ammo, side by side"; comparing across types always goes wrong.

**Counterexample 2: assuming multi-barrel = multiple damage (treating ammoPerShot as shot count).**
In v160.7 `turrets.json`, titan has `ammoPerShot = 4` and smite `ammoPerShot = 2`, but those are **ammo consumption**, not bullet count: titan fires 1 shell of 350 per shot, smite fires 5 shells of 250 (`ShootAlternate{shots = barrels = 5}` at `Blocks.java:5721-5727`). Conversely smite's 5 shells come out **in sequence** (ShootAlternate), not all landing on the same tick.

**Counterexample 3: computing v160.7 with v159.3 source armor/reload.**
toxopid's armor is 13 in the source and 22 in the jar: spectre's TTK against it moves from 69.37 s to 91.67 s (+32%). dagger's main weapon source `reload = 13` versus 26 per mount in the jar (two mounts alternating); computing with 13 gives 83 DPS, twice v160.7's 41.5. **Rule: numbers from v160.7, algorithms from the source.**

**Counterexample 4: assuming TTK changes linearly with DPS.**
duo takes 5.56 s against dagger and 8148 s against toxopid: DPS drops only 10× while TTK rises 1466× — because armor also presses per-shot damage down to the 10% floor; armor is a non-linear amplifier of TTK.

**Positive check**: scorch vs fortress `d = max(17−9, 1.7) = 8`, `DPS = 10×8 = 80`, `TTK = 900/80 = 11.25 s`; against toxopid (armor 22) `d = 1.7` (hits the floor), `DPS = 17`, `TTK = 1294.12 s`.

## Common misconceptions

- ❌ "high DPS means strong". → Against heavy armor look at **per-shot D**, against light armor at DPS, against groups at splash radius and falloff.
- ❌ "reload is seconds". → reload is in tick, `reload/60` is seconds; treating reload as seconds gives a rate 1/60 of the real one.
- ❌ "continuous laser DPS = damage × 60". → It is `damage/5 × 60` (`damageInterval = 5`); ×60 overestimates 5×.
- ❌ "splash damage is split evenly over the radius". → 100% at the center, 40% at the edge, linear falloff (`Damage.java:652-656`, falloff 0.4).
- ❌ "doubling a multi-barrel turret's shots leaves accuracy unchanged". → swarmer's 4-round burst has spread and smite's 5 shells come out in sequence, so moving targets get missed.
- ❌ "armor can reduce damage to 0". → The floor is 10%, `max(D−A, 0.1D) > 0`.

## See also

- [[COMBAT.TURRET.001]] the full reload/range/shots/ammo table for 28 turrets (the input to tables 1 and 3 here)
- [[COMBAT.ARMOR.001]] the complete derivation of the armor formula, AP and immunity
- [[COMBAT.BULLET.001]] per-shot damage, splash radius, piercing and frag
- [[COMBAT.UNITWEAPON.001]] unit weapon mounts and the alternate convention
- [[COMBAT.DEFENSE.001]] defense block hp/armor (TTK applied backwards)
- [[UNIT.MOVE.001]] unit speed decides whether it can get into range (DPS outside range is 0)
- [[COMBAT.TURRET.002]] using these numbers to choose: which gun to build, where the knee is (DPS/cost and the A* table)
