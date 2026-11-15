---
id: COMBAT.BULLET.001
title: 子弹与弹道——lifetime/speed/drag、贯穿、溅射、闪电与碎片
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:33-63"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:109-220"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414-440"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:480-612"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:832"
  - "MBO/gamedata/v160.7/gamedata.json (28 turret raw)"
data: [00-data/bullets.json]
depends: [COMBAT.DAMAGE.001, COMBAT.TURRET.001]
tags: [子弹, 弹道, 射程, 贯穿, 溅射, 闪电, 碎片, drag]
tokens: 746
---

## 一句话

子弹的**真实射程 = speed × lifetime（px/tick × tick）**，和炮塔 `range` 是两个独立数字——炮塔只是"在 range 内找目标"，子弹飞不出 lifetime 就消失；且 `splashDamageRadius` 默认 **-1 表示不溅射**（不是 0 半径），`pierceCap = -1` 表示贯穿**无上限**。

## 规则 / 公式

### 1. 射程

```
无阻力:  bulletRange = speed * lifetime                      // 单位 px
有阻力:  bulletRange = speed * (1 - pow(1 - drag, lifetime)) / drag
实际:    最终射程 = max(bulletRange, maxRange)                 // 若 maxRange > 0
```

- `speed` 单位是 **px/tick**（1 tile = 8px，60 tick = 1s）。速度 3.5 → 210 px/s ≈ 26 格/s。
- `lifetime` 单位是 **tick**。dagger 的 basic 弹 speed 2.5、life 60 → 150px ≈ 18.75 格。
- **drag > 0 时射程会饱和到 `speed/drag`**，永远达不到 speed×lifetime：speed=2.5、drag=0.1、life=60 → `2.5*(1-0.9^60)/0.1 = 24.96px`（≈3.1 格），而同样参数的 drag=0 是 150px。射程差 6 倍，所以"射程 = lifetime×speed"只对 drag=0 的子弹成立。

### 2. 贯穿

```
pierce = false           → 命中首个目标后消失
pierce = true            → 继续飞
pierceCap = -1（默认）   → 贯穿数无上限；>0 则命中 N 个后停止
pierceDamageFactor > 0   → 每穿一个目标，伤害按 initialHealth * factor 递减
removeAfterPierce = true → damage 归零即移除
```

reign 的弹 `pierce cap 10`：一发最多打穿 10 个单位。

### 3. 溅射

```
splashDamageRadius = -1（默认）→ 无溅射（>0 才结算）
溅射伤害 = Damage.damage(..., splashDamage * b.damageMultiplier(), ...)
边缘衰减 = lerp(1 - dist/radius, 1, 0.4)   // 边缘 40%
splashDamagePierce = true → 溅射无视护甲
scaledSplashDamage = true → 溅射按子弹伤害缩放
```

**溅射半径是"像素"**（要除 8 才是格）：fortress 的 artillery `splash 80 r35` = 35px ≈ 4.4 格。

### 4. 闪电与碎片（命中后的二次伤害）

```
lightning > 0 → 命中时在落点生成 lightning 条闪电
lightningDamage < 0 → 用子弹自身 damage（默认 -1，即"等于弹伤"）
lightningLength = 5（默认），lightningLengthRand = 0
fragBullets = 9（默认）→ 命中/消失时炸出 9 个碎片
fragVelocityMin/Max = 0.2 / 1.0；fragLifeMin/Max = 1.0
```

**fragBullets 默认就是 9**，所以任何 `fragBullet` 非空、没写 fragBullets 的子弹都会炸 9 片——这是"顺手的 9 倍伤害"最容易翻车的地方。

### 5. 碰撞开关

`collidesTiles = true`、`collidesAir = true`、`collidesGround = true`、`collidesTeam = false`、`collides = true`、`collideTerrain/collideFloor = false`、`hittable = true`、`absorbable = true`（可被护盾/力场吸收）、`reflectable = true`。

## 数值

| 字段 | 默认值 | 备注 |
|---|---|---|
| `lifetime` | 40 tick | BulletType.java:33 |
| `speed` | 1f px/tick | :37 |
| `damage` | 1f | :41 |
| `hitSize` | 4f | :43（碰撞体积，不是伤害） |
| `drag` | 0f | :49 |
| `pierce` | false | :53 |
| `pierceCap` | -1 | :57（-1 = 无限） |
| `pierceDamageFactor` | 0f | :59 |
| `maxDamageFraction` | -1f | :61（单发上限 = 目标 maxHP×该值） |
| `removeAfterPierce` | true | :63 |
| `splashDamage` | 0f | :109 |
| `splashDamageRadius` | -1f | :301（≤0 = 不溅射） |
| `splashDamagePierce` | false | :303 |
| `scaledSplashDamage` | false | :111 |
| `statusDuration` | 480 tick = 8 s | :119 |
| `ammoMultiplier` | 2f | :95 |
| `lightning` | 0 | :333 |
| `lightningLength` | 5 | :335 |
| `lightningDamage` | -1 | :339（-1 = 用本弹 damage） |
| `fragBullets` | 9 | :212 |
| `pierceArmor` / `armorMultiplier` | false / 1f | :187 / :189 |

v160.7 典型炮塔弹（速度, 伤害, 射程）：
duo+铜 Basic(2.5, 9, life60=150px)；hail+石墨 Artillery(3, 20, life?  Artillery 默认 life 由 code 算)；spectre+钍 Basic(8, 80, life?)；foreshadow 用 rail；meltdown `ContinuousLaserBulletType(78)` 的 78 是**每 tick 伤害**。

## 源码锚点

- `BulletType.java:33-63` 核心字段默认值（lifetime=40、speed=1、damage=1、hitSize=4、drag=0、pierceCap=-1）。
- `BulletType.java:414-432` `estimateDPS()`：`(damage + splashDamage*0.75) * (pierce ? (pierceCap==-1?2:clamp(pierceCap,1,2)) : 1)`，再叠加 `fragBullet.estimateDPS()*fragBullets/2`。**这就是游戏内 DPS 显示的来源，也是它系统性偏高的原因**（它假设溅射全中、贯穿 2 个）。
- `BulletType.java:435-440` `calculateRange()`：无 drag 用 `speed*lifetime`，有 drag 用 `speed*(1-pow(1-drag,lifetime))/drag`，再与 `maxRange` 取大。
- `BulletType.java:480-521` `hitEntity`：护盾上限 → 三种伤害模式 → status/击退。
- `BulletType.java:523-532` `handlePierce`：`sub = max(initialHealth*pierceDamageFactor, 0)`，`b.damage -= min(b.damage, sub)`。
- `BulletType.java:549-576` `hit` 的执行顺序（frags → puddles → incend → createUnits → suppression → splash → lightning）。
- `BulletType.java:594-600` 溅射：`splashDamageRadius > 0` 才调 `Damage.damage`，随后 `Damage.status` 同区域施状态。
- `BulletType.java:574` 闪电：`lightningDamage < 0 ? damage : lightningDamage`。

## 实测与反例

**反例 1：用炮塔 range 当子弹射程。**
duo range=160，但铜弹 2.5×60 = 150px。站在 155~160px 边缘的目标，炮塔会开火而**子弹提前消散**，看起来像"打不中"。

**反例 2：以为 `splashDamageRadius = -1` 是"半径 1px"。**
源码条件是 `splashDamageRadius > 0`，-1 等于**关闭溅射**。反过来，`splashDamage > 0` 但没设半径的子弹也**不会**溅射。

**反例 3：以为 `pierceCap = -1` 是"不贯穿"。**
-1 是**无上限**；`pierce = false` 才是不贯穿。两者是独立字段：pierce=true + pierceCap=-1 = 无限穿透。

**反例 4：忽略 fragBullets 默认 9。**
metaglass 的 scatter 弹写了 `frag Basic(3,5)`，没写 fragBullets → 实际炸 9 个 5 伤碎片 = 45 点潜在伤害，是主弹的 15 倍。

**可复算**：meltdown `ContinuousLaserBulletType(78)`，连续伤害按 `damage * Time.delta` 结算 → 每秒 78×60 = **4680 DPS**（单目标、无护甲）。护甲 13 的目标：`max(78-13, 7.8)=65`/tick → 3900 DPS。

## 常见误解

- ❌ "speed 是格/秒"。→ 是 **px/tick**；换算：speed × 60 / 8 = 格/秒。
- ❌ "lifetime 是秒"。→ tick，60 tick = 1 s。
- ❌ "碎片伤害会乘 fragBullets 之外的系数"。→ 每片独立走完整伤害管线（各自吃护甲）。
- ❌ "drag 只影响外观"。→ drag 直接决定射程饱和值（`speed/drag` 量级）。
- ❌ "闪电伤害固定"。→ `lightningDamage = -1` 时等于本弹 damage，写死数值才会覆盖。

## 相关

- [[COMBAT.DAMAGE.001]] 命中后的护甲/护盾顺序
- [[COMBAT.TURRET.001]] 炮塔如何装填并发射这些子弹
- [[COMBAT.STATUS.001]] `status`/`statusDuration` 的结算
- [[COMBAT.NUMBERS.001]] 用本页公式复算 DPS
