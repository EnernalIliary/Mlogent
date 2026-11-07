---
id: COMBAT.ARMOR.001
title: 护甲与抗性——减法公式、10% 保底、穿甲与免疫
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
tags: [护甲, armor, 穿甲, 免疫, 保底伤害, 建筑护甲]
tokens: 839
---

## 一句话

护甲是**减法**不是百分比：`实际伤害 = max(伤害 − 护甲, 0.1 × 伤害)`；因此护甲对**小口径**几乎免疫、对**大口径**几乎无效——护甲 26 的单位被 9 伤子弹打只掉 0.9，被 350 伤子弹打掉 324。

## 规则 / 公式

### 1. 唯一公式（单位与建筑共用）

```
applyArmor(damage, armor) = max(damage - armor, minArmorDamage * damage)
minArmorDamage = 0.1                     // 常量，不可配置
```

**推导**：源码 `Damage.applyArmor` 只有这一行。它意味着：

- 当 `damage - armor >= 0.1*damage`，即 `armor <= 0.9*damage` 时，是纯减法；
- 当 `armor > 0.9*damage` 时进入保底区，伤害恒为 `0.1*damage`，**再多护甲也没用**；
- 拐点：`damage* = armor / 0.9`。护甲 26 → 拐点 28.9；单发 ≤28.9 全部只吃 10%。

### 2. 建筑走另一条入口，但同一公式

```
damage = other.type.buildingDamage(other)                        // 含 buildingDamageMultiplier
if(!t.pierceArmor)
    damage = Damage.applyArmor(damage, block.armor * t.armorMultiplier * t.blockArmorMultiplier)
```

| 系数 | 作用对象 | 默认 |
|---|---|---|
| `armorMultiplier` | 护甲值本身（穿甲弹可放大护甲） | 1 |
| `blockArmorMultiplier` | **只作用于建筑**的护甲 | 1 |
| `buildingDamageMultiplier` | 只作用于建筑的伤害 | 1 |
| `pierceArmor` | true 时**楼舍整个 applyArmor** | false |

### 3. 三种"绕过护甲"的方式

1. `pierceArmor = true`（BulletType 字段）：完全跳过护甲。
2. `splashDamagePierce = true`：溅射部分跳过护甲。
3. status `armorOverride`：只有 `dynamic` 类 status 能设，`>=0` 时**覆盖**目标护甲（值为 0 也覆盖，`-1` 表示不覆盖）。

### 4. 免疫不通过护甲实现

```
isImmune(effect) = type.immunities.contains(effect)     // StatusComp.java:98-100
```

免疫只挡 **status**，**不挡伤害**。原版没有任何"伤害免疫"的护甲式机制（除了 invincible status 与护盾）。

### 5. 护甲值从哪来

- 单位：`UnitType.armor`，静态，不随等级变化（无等级系统，见 [[UNIT.PROGRESSION.001]]）。
- 方块：`Block.armor`（默认 0），墙/核心专用。
- status：`armorOverride`（dynamic）。

## 数值

### 实际伤害矩阵（行=单发伤害 D，列=护甲 A）

| D \ A | 0 | 2 | 4 | 6 | 9 | 13 | 16 | 20 | 26 |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 9 | 7 | 5 | 3 | 0.9 | 0.9 | 0.9 | 0.9 | 0.9 |
| 18 | 18 | 16 | 14 | 12 | 9 | 5 | 2 | 1.8 | 1.8 |
| 50 | 50 | 48 | 46 | 44 | 41 | 37 | 34 | 30 | 24 |
| 80 | 80 | 78 | 76 | 74 | 71 | 67 | 64 | 60 | 54 |
| 140 | 140 | 138 | 136 | 134 | 131 | 127 | 124 | 120 | 114 |

### 需要的命中数（1000 血目标，按上式复算）

| D \ A | 0 | 9 | 16 | 26 |
|---|---|---|---|---|
| 9 | 111 | 1111 | 1111 | 1111 |
| 18 | 56 | 111 | 500 | 556 |
| 50 | 20 | 24.4 | 29.4 | 41.7 |
| 80 | 12.5 | 14.1 | 15.6 | 18.5 |

`9 伤子弹打 1000 血 26 甲目标需要 1111 发`（1000/0.9），而 80 伤子弹只需 18.5 发。**这就是"小炮打大甲完全无效"的量化来源。**

### 单位护甲梯度（v160.7 jar 反射，hp / armor）

| 护甲 | 代表单位（hp / armor） |
|---|---|
| 0 | dagger(150)、crawler(150)、flare(70)、mono(100)、poly(400)、alpha(150) |
| 1~2 | elude(600/1)、nova(200/1)、risso(280/2)、renale(500/2) |
| 3~5 | atrax(600/3)、horizon(340/3)、mega(460/3)、mace(550/4)、pulsar(320/4)、minke(600/4)、merui(680/4)、quell(6000/4)、zenith(700/5)、cleroi(1100/5)、tecta(6500/5) |
| 6~9 | stell(850/6)、obviate(2300/6)、anthicus(2700/7)、locus(2100/8)、fortress(900/9)、quasar(640/9)、spiroct(1000/9)、collaris(18000/9)、disrupt(12000/9) |
| 10~16 | quad(6000/10)、precept(5000/11)、sei(11000/12)、aegires(12000/12)、latum(20000/12)、corvus(18000/14)、arkyid(8000/14)、vela(8200/16)、omura(22000/16) |
| 17~22 | antumbra(7200/17)、scepter(9000/20)、navanax(20000/20)、vanquish(11000/20)、toxopid(22000/22)、eclipse(22000/22) |
| 26~30 | conquer(22000/26)、reign(24000/30) |

**版本注**：上表取 v160.7 jar（数值权威）。v159.3 源码同名字段普遍更低——toxopid 13（`UnitTypes.java:909`）、eclipse 13(:1264)、reign 18(:295)、scepter 10(:194)、arkyid 6(:805)、vela 9(:507)、corvus 9(:578)、spiroct 5(:746)、quad 8(:1460)。按 VERSION.md 冲突一律取 jar，本文所有护甲算式用 jar 值。

### 建筑护甲（v160.7 反射 raw）

| 方块 | hp | armor | 备注 |
|---|---|---|---|
| copper-wall | 320 | 0 | — |
| beryllium-wall | 520 | 2 | — |
| tungsten-wall | 720 | 14 | — |
| carbide-wall | 1080 | 16 | — |
| shielded-wall | 4160 | 15 | 另有 shieldHealth 900 |
| blast-door | 2800 | 14 | AutoDoor |
| core-bastion | 4500 | 5 | — |
| core-citadel | 16000 | 10 | — |
| core-acropolis | 30000 | 15 | — |

### 免疫表（v159.3 UnitTypes.java，共 7 处）

| 单位 | 免疫 |
|---|---|
| mace | burning |
| vela | burning |
| atrax | burning, melting |
| navanax | burning |
| precept | burning, melting |
| vanquish | burning, melting |
| conquer | burning, melting |

## 源码锚点

- `Damage.java:659-661`：`return Math.max(damage - armor, minArmorDamage * damage);`
- `Vars.java:133`：`public static final float minArmorDamage = 0.1f;`（v160.7 反射确认 const=0.1）
- `BuildingComp.java:1762-1778` `collision(Bullet)`：`if(!t.pierceArmor) damage = Damage.applyArmor(damage, block.armor * t.armorMultiplier * t.blockArmorMultiplier);`
- `BulletType.java:187-191`：`pierceArmor=false`、`armorMultiplier=1f`、`blockArmorMultiplier=1f`
- `Block.java:191-192`：`public float armor = 0f;`（注释："damage absorption, similar to unit armor"）
- `StatusComp.java:98-100`：`isImmune = type.immunities.contains(effect)`
- `UnitTypes.java:125/510/698/2439/2779/2853/2964`：7 处 immunities 赋值（mace / vela / atrax / navanax / precept / vanquish / conquer）

## 实测与反例

**反例 1：把护甲当"减伤百分比"。**
18 伤 vs 13 甲：百分比思路 = 18×(1−13%) = 15.7。实际 `max(18−13, 1.8) = 5`。**差 3 倍**，且不会因为"护甲 100"就减 100%。

**反例 2：以为溅射忽略护甲。**
溅射走同一条 `damage(amount)`，护甲照减。spectre 溅射 40 伤打 16 甲目标：`max(40−16, 4)= 24`，边缘再乘 0.4 → **9.6**。

**反例 3：以为穿甲弹（pierceArmor）减半护甲。**
源码是 `if(pierceArmor) damagePierce(...)`，**完全不调用 applyArmor**。对建筑同理（BuildingComp L1767）。

**反例 4：拿护甲当"免疫 status"。**
护甲只管伤害。想免疫 burning 必须写进 `unit.immunities`；toxopid 护甲 22（v160.7 jar；v159.3 源码为 13）但**照样被点燃**（它没有 burning 免疫——免疫表里没有它）。

**可复算**：dagger 单发 9，打 tungsten-wall（armor 14）：`max(9−14, 0.9) = 0.9/发`，720 血需要 **800 发**；换成 conquer（单发 360）：`max(360−14, 36) = 346`，只需 3 发。

## 常见误解

- ❌ "护甲可以叠到 100% 免伤"。→ 保底 10%，永不归零。
- ❌ "blockArmorMultiplier 对单位也生效"。→ 只作用于建筑护甲（BuildingComp 那一条）。
- ❌ "免疫 = 免伤"。→ 免疫只针对 status。
- ❌ "护甲会随难度/波次提升"。→ 原版不变；难度只缩放 hp 与伤害（rules.unitHealth / unitDamage）。
- ❌ "护甲 0 的单位护甲字段为空"。→ `armor = 0f` 是有效值，`applyArmor(D, 0) = D`。

## 相关

- [[COMBAT.DAMAGE.001]] 护甲在伤害管线中的位置
- [[COMBAT.STATUS.001]] healthMultiplier / armorOverride
- [[COMBAT.NUMBERS.001]] 护甲曲线与 TTK
- [[COMBAT.DEFENSE.001]] 墙体与护盾方块
