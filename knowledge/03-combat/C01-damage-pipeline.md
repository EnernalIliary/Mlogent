---
id: COMBAT.DAMAGE.001
title: 伤害管线总览——一次命中从 BulletType 到 health 的完整顺序
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:480-521"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:549-576"
  - "Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:593-612"
  - "Mindustry-Source/core/src/mindustry/entities/comp/ShieldComp.java:26-81"
  - "Mindustry-Source/core/src/mindustry/entities/Damage.java:652-661"
  - "Mindustry-Source/core/src/mindustry/entities/comp/HealthComp.java:42-117"
  - "Mindustry-Source/core/src/mindustry/Vars.java:133"
  - "KB/00-data/rt_values_raw.json (mindustry.Vars.minArmorDamage)"
data: [00-data/rt_values_raw.json]
depends: [COMBAT.ARMOR.001]
tags: [伤害, 护甲, 护盾, 溅射, 管线, 最小伤害]
tokens: 783
---

## 一句话

一次命中固定走 6 个阶段：**命中判定 → 伤害数值修饰（穿甲/护甲倍率/护盾上限）→ 护甲减免 → 单位系数（healthMultiplier、rules.unitHealth）→ 护盾吸收 → 扣 health**；护甲减免永远用 `max(damage - armor, 0.1 * damage)`，所以**再高的护甲也只能把单发伤害压到 10%，永远压不到 0**。

## 规则 / 公式

### 1. 完整顺序（单位目标）

```
BulletType.hit(b, x, y)                      // 1. 触发效果与范围伤害
  → hitEntity(b, unit)                       // 2. 单体命中
      → 计算护盾（maxDamageFraction 时 cap = maxHealth*fraction + shield）
      → 选择伤害模式（三选一）
      → unit.damage / damagePierce / damageArmorMult
          → ShieldComp.damage(amount, withEffect)
              → rawDamage(applyArmor(amount, armor) / healthMultiplier / rules.unitHealth(team))
                  → shield -= min(shield, amount)   // 3. 护盾先吃
                  → health -= 剩余                   // 4. 再扣血
                      → health <= 0 → kill()         // 5. 死亡
```

**关键：护盾在护甲之后、血量之前。** 顺序写反（先算护盾再减护甲，或护甲只作用于血量）是最常见的手算错误。

### 2. 三种伤害模式（BulletType 的字段决定走哪条）

| 字段 | 取值 | 走的方法 | 护甲处理 |
|---|---|---|---|
| `pierceArmor = true` | 默认 false | `damagePierce(amount)` | **完全忽略护甲**，原值扣 |
| `armorMultiplier != 1` | 默认 1 | `damageArmorMult(amount, mult)` | `applyArmor(amount, armor * mult)` |
| 都不满足（绝大多数子弹） | — | `damage(amount)` | `applyArmor(amount, armor)` |

三者互斥，源码里是 `if(pierceArmor) … else if(armorMultiplier != 1) … else …` 的链式分支。

### 3. 护甲减免公式（全库唯一）

```
applyArmor(damage, armor) = max(damage - armor, minArmorDamage * damage)
minArmorDamage = 0.1                       // Vars.java:133，v160.7 反射确认 const=0.1
```

等价写法：**实际伤害 = max(D - A, 0.1·D)**。当 `A ≥ 0.9·D` 时进入"保底区"，伤害恒为 `0.1·D`。

### 4. 单位系数（在护甲之后乘）

```
最终扣血 = applyArmor(amount, armor) / healthMultiplier / rules.unitHealth(team)
```

- `healthMultiplier`：单位当前 status 乘出来的血量倍率（healthMultiplier 越**大**越硬，因为是除数）。冻结 freezing = 0.8 → 受到伤害 ×1.25。
- `rules.unitHealth(team)`：难度/波次缩放。默认 1。
- 溅射另有 `buildingDamageMultiplier`，**只作用于建筑**，不影响单位。

### 5. 溅射的衰减

```
calculateDamage(radius, dist) = lerp(1 - dist/radius, 1, 0.4)     // falloff = 0.4
→ 中心 100%，边缘 40%，与距离线性
```

半径 ≤ 1e-5 时视为单点，不衰减。当 `scaledSplashDamage = true` 时，溅射伤害还要再乘 `damage / 100` 之类的"按伤害缩放"系数（源码 `splashDamage * b.damageMultiplier()` 那一支）。

### 6. 连续伤害（激光/火焰/液流）

`damageContinuous(amount)` = `damage(amount * Time.delta)`。**字段里的 damage 是"每 tick 伤害"，不是每发**。60 tick/s，所以 `damage=78` 的 ContinuousLaser 每秒 78*60 = 4680。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| `Vars.minArmorDamage` | 0.1 | Vars.java:133；`00-data/rt_values_raw.json` 反射 const=0.1 |
| `BulletType.damage` 默认 | 1f | BulletType.java:41 |
| `BulletType.splashDamage` 默认 | 0f | BulletType.java:109 |
| `BulletType.statusDuration` 默认 | 480 tick = 8 s | BulletType.java:119（`60*8`） |
| `BulletType.buildingDamageMultiplier` 默认 | 1.0 | BulletType.java:99 + v160.7 反射 |
| 溅射衰减 falloff | 0.4 | Damage.java:652-656 |
| `Vars.tilesize` | 8 px | Vars.java:135；v160.7 反射 const=8 |
| `Vars.tilePayload` | 64 px² | Vars.java:137 |

## 源码锚点

- `entities/bullet/BulletType.java:480-521` `hitEntity`：护盾上限、三种伤害模式、命中后 `unit.apply(status, statusDuration)` 与击退。
- `entities/bullet/BulletType.java:549-576` `hit(b,x,y)` 的执行顺序：hitEffect/sound → frags → puddles → incend → createUnits → suppression → **createSplashDamage** → lightning。
- `entities/bullet/BulletType.java:593-612` `createSplashDamage`：调 `Damage.damage(..., splashDamage * b.damageMultiplier(), splashDamagePierce, ..., armorMultiplier)`，并对区域内单位补 status。
- `entities/comp/ShieldComp.java:26-31` `damage(amount, withEffect)`：`rawDamage(applyArmor(amount, armorOverride >= 0 ? armorOverride : armor) / healthMultiplier / state.rules.unitHealth(team))`。
- `ShieldComp.java:35-43` `damagePierce` 直接 rawDamage，不减护甲。
- `ShieldComp.java:47-55` `damageArmorMult(amount, armorMult)` → `applyArmor(amount, armor * armorMult)`。
- `ShieldComp.java:57-81` `rawDamage`：先扣 shield（`shieldDamage = min(max(shield,0), amount)`），剩余扣 health；死亡走 `kill()`；护盾碎裂播 `Fx.unitShieldBreak`。
- `entities/Damage.java:652-661`：`calculateDamage` 的 0.4 falloff 与 `applyArmor`。
- `entities/comp/HealthComp.java:71-79` `damage(amount)`：`health -= amount; hitTime = 1f; if(health <= 0 && !dead) kill();`
- `HealthComp.java:109-117` `heal(amount)` 与 `healFract(amount)`（按 maxHealth 的 0~1 比例）。

## 实测与反例

**反例 1：把护甲当"百分比减伤"算。**
错误手算：toxopid 护甲 22（v160.7 jar；v159.3 源码为 13），dagger 单发 9 → 以为 "9 × (1 - 22%) = 7.02"。
源码结果：`applyArmor(9, 22) = max(9-22, 0.9) = 0.9`。**一发 9 伤害只掉 0.9 血**，22 点护甲把 9 点伤害吃掉 90%（撞到 10% 保底）。这正是"小口径炮打重甲单位几乎无伤"的原因。

**反例 2：以为高护甲能完全免疫。**
护甲 50 vs 单发 5：`max(5-50, 0.5) = 0.5`，仍掉 0.5。只要 `damage > 0`，伤害恒 ≥ 10%。所以 crawler（自爆 0 速子弹）之外，没有任何"完全免疫"的原版机制；真正的免疫靠 `immunities`（见 COMBAT.ARMOR.001）。

**反例 3：把 statusDuration 当秒。**
`statusDuration = 480` 是 tick，**8 秒**，不是 480 秒；写成 `60*8` 的写法在源码里就是为了防止误读。

**正例（可核对）**：duo 打 dagger（armor 0）：9 伤害 → 9 血；打 fortress（armor 9）：`max(9-9, 0.9)=0.9`。同一发子弹对 900 血 fortress 需要 1000 发，对 150 血 dagger 只需 17 发。

## 常见误解

- ❌ "护盾在护甲之前计算"。→ 错，护甲先算，护盾吃的是**已经减过护甲**的数值。
- ❌ "穿甲（pierceArmor）是减一半护甲"。→ 是**完全跳过** `applyArmor`，一点护甲都不减。
- ❌ "溅射边缘是中心的一半"。→ 是 **40%**（falloff 0.4）。
- ❌ "`rules.unitHealth` 也影响玩家单位"。→ 它按 team 取值，玩家队默认 1，只有波次敌人吃难度缩放。
- ❌ "护甲对溅射无效"。→ 溅射走同一条 `damage()` 管线（`armorMultiplier` 也一并传下去），护甲同样生效且同样保底 10%。

## 相关

- [[COMBAT.ARMOR.001]] 护甲公式推导与穿甲
- [[COMBAT.BULLET.001]] 子弹字段与弹道
- [[COMBAT.STATUS.001]] 状态倍率（healthMultiplier 就在这条管线里）
- [[COMBAT.NUMBERS.001]] 用本管线手算 TTK
