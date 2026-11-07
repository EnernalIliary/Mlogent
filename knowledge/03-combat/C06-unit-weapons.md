---
id: COMBAT.UNITWEAPON.001
title: 单位武器——weapons[]、挂点坐标、镜像与单位 DPS
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
tags: [单位武器, Weapon, 挂点, mirror, alternate, 单位DPS]
tokens: 1342
---

## 一句话

单位武器是 `Seq<Weapon> weapons` 里的若干条目，`mirror = true`（默认）会把同一武器镜像到身体另一侧，所以 **v160.7 的 jar 反射里同一武器总是成对出现（`x` 与 `-x`，如 dagger 的 ±4）**；"单位 DPS"必须按**所有挂点求和**，每个挂点独立装填，不能拿"一个武器 = 一个炮管"去算。

## 规则 / 公式

### 1. 单挂点 DPS 与单位 DPS（jar 口径）

```
perMountDPS = (60 / mount.reload) * bullet.damage      // reload 单位 = tick
unitDPS     = Σ perMountDPS over all mounts           // jar 的 weapons[] 已逐条枚举镜像挂点
mountCount  = weapons[] 条目数（mirror 武器在 jar 里就是 2 条）
```

**不要**再对 jar 的挂点表乘一次 2：dagger 的 jar 数据是"2 个挂点 × reload 26"，直接求和 = 41.5（见表 1）；再乘 2 才是错的。

源码里 `Weapon.dps()` = `(bullet.estimateDPS()/reload) * shoot.shots * 60`，是**单挂点**面板值，且把溅射按 75% 计入（`BulletType.java:414-432`），对单体要打折。

### 2. 挂点坐标（最容易错的部分）

```
weapon.x  = 沿"武器朝向"的前后偏移（px），正 = 朝前
weapon.y  = 侧向偏移（px），mirror 时另一侧取 -y
weapon.shootX / shootY = 枪口相对挂点的再偏移；默认 shootX=0, shootY=3（朝前 3px 出膛）
weapon.baseRotation   = 固定基准角（avert baseRotation=-35）
weapon.rotate = false → 武器随身体朝向、不独立转向
```

**不是"屏幕坐标"**：x 会跟着 `mount.rotation` 旋转，同一份 `x=4, y=2` 在不同朝向下落点不同。jar 里 vanquish 的 4 个副炮挂点就是 `(±12, 8.5)` 与 `(±12, -9)` 两组。

### 3. 开火条件

| 字段 | 默认 | 作用 |
|---|---|---|
| `reload` | 1 tick | 装填时间 |
| `inaccuracy` | 0 | 角度散布（度） |
| `shootCone` | 5 | 允许开火的角度容差；360 = 无死角（lustre、elude） |
| `rotateSpeed` | 20 | 度/tick |
| `cooldownTime` | 20 | 连发间隔/冷却 |
| `alternate` | true | 多 mount 交替发射（只错相位，不改总射速） |
| `mirror` | true | 是否镜像到另一侧（jar 里体现为成对挂点） |
| `top` | true | 绘制在机体上层 |
| `controllable` | 见字段 | 玩家 ucontrol 时能否手动控制该武器 |
| `alwaysShooting` | false | 无视目标持续开火 |
| `autoTarget` | true | 自动索敌（false 需玩家/逻辑指定） |
| `shootWarmupSpeed` | 0.1 | 预热速度，`minWarmup` 前不能开火 |
| `shootStatusDuration` | 300 | 部分武器附带的 status 时长 |

### 4. 单位武器的三种"伤害放大器"

1. **挂点数量**：jar 里 vanquish 有 5 个挂点（主炮 1 + 副炮 4）、arkyid 有 8 个、scepter 有 6 个 —— 数量本身就是 DPS 乘数。
2. **多武器条目**：如 risso = 机炮 ×2 + 导弹 ×1，三组独立装填，DPS 相加 = 70.3。
3. **溅射/碎片**：artillery 类 `splashDamageRadius` 可到 80px（toxopid 炮 80px = 10 格），对群时实际 DPS 远超单发。

## 数值

### 表 1：单位武器 DPS（v160.7 jar，`00-data/units.json` + `bullets.json`，逐挂点求和）

> **DPS 口径（v160.7 jar，2026-11-08 反射复测）**
> - 公式：`dps = Σ挂点 (bullet.damage × shoot.shots × 60 / reload)`（`Weapon.java:189` 的 `dps()`；`UnitType.java:1129-1145` 的 `dpsEstimate = weapons.sumf(Weapon::dps)`）。
> - `mirror=true` 的武器在 `UnitType.init()` 里会复制一份挂点，且两把的 reload/recoil 都被 ×2（源码注释原文 since there are now two weapons, the reload and recoil time must be doubled）⇒ jar 里的 reload 已是 ×2 后的值，**shots 仍要乘**：漏乘 shots 会把 toxopid 主炮报成 220 而不是 440。
> - 表内「挂点」= jar 的 `unit.weapons.size`（已含镜像复制），「单位合计 DPS」= 全部挂点之和；含副炮的行在括号里注明 主炮/合计。shots>1 的挂点，「单挂点 DPS」已乘 shots。
> - 只计单目标直伤，不含溅射/贯穿/碎片放大（那属于读法里的面板放大项，对群时另算）。

| 单位 | 武器（jar 名称，×n = 挂点数） | 挂点 | 每挂点 reload | 单发 D | 单挂点 DPS | 单位合计 DPS | 备注 |
|---|---|---|---|---|---|---|---|
| dagger | large-weapon×2 | 2 | 26 | 9 | 20.8 | **41.5** | — |
| mace | flamethrower×2 | 2 | 44 | 74 | 100.9 | **201.8** | — |
| fortress | artillery×2 | 2 | 120 | 20 | 10.0 | **20.0** | 溅射 80@35 |
| zenith | zenith-missiles×2（shots 2） | 2 | 80 | 14 | 21.0 | **42.0** | 溅射 15@25 |
| stell | stell-weapon | 1 | 50 | 30 | 36.0 | **36.0** | — |
| locus | locus-weapon | 1 | 18 | 36 | 120.0 | **120.0** | — |
| precept | precept-weapon | 1 | 80 | 90 | 67.5 | **67.5** | 溅射 50@20，frag 4 |
| vanquish | vanquish-weapon + point-weapon×4 | 5 | 80 / 44 / 54 | 112.5 / 37.5 | 84.4 + 51.1 + 41.7 | **270.0** | 溅射 50@20，frag 5 |
| conquer | conquer-weapon | 1 | 100 | 270 | 162.0 | **162.0** | — |
| merui | merui-weapon | 1 | 63 | 30 | 28.6 | **28.6** | 溅射 30@19 |
| cleroi | cleroi-weapon×2 + point-defense×2 | 4 | 66 / 18 | 22.5 / 28.5 | 20.5 + 95.0 | **230.9** | 溅射 43@30 |
| tecta | tecta-weapon×2（shots 3） | 2 | 80 | 38.25 | 86.1 | **172.1** | 溅射 60@30 |
| collaris | collaris-weapon×2 | 2 | 260 | 195 | 45.0 | **90.0** | 溅射 120@36，frag 15 |
| quell | quell-weapon×2 | 2 | 110 | 52.5 | 28.6 | **57.3** | frag 1 |
| corvus | corvus-weapon | 1 | 350 | 560 | 96.0 | **96.0** | 激光 |
| scepter | scepter-weapon×2（shots 3）+ mount×4 | 6 | 90 / 24 / 30 | 70 / 20 | 140.0 + 50.0 + 40.0 | **460.0** | 链闪 2 |
| reign | reign-weapon×2 | 2 | 18 | 80 | 266.7 | **533.3** | 溅射 18@13，frag 3 |
| omura | omura-cannon | 1 | 110 | 1250 | 681.8 | **681.8** | 轨道炮 |
| atrax | atrax-weapon×2 | 2 | 18 | 13 | 43.3 | **86.7** | 液弹（slag） |
| spiroct | spiroct-weapon×2 + mount-purple×2 | 4 | 28 / 36 | 23 / 18 | 49.3 + 30.0 | **158.6** | — |
| arkyid | spiroct-weapon×6 + large-purple×2 | 8 | 18 / 28 / 44 / 90 | 40 / 12 | 133.3 + 85.7 + 54.5 + 8.0 | **563.2** | 溅射 65@70，链闪 3 |
| toxopid | large-purple×2（shots 2）+ toxopid-cannon | 3 | 60 / 210 | 110 / 50 | 220.0 + 14.3 | **454.3**（主炮 440.0） | 溅射 75@80，链闪 5 |
| eclipse | large-laser×2 + large-artillery×4 | 6 | 90 / 18 / 24 | 115 / 15 | 76.7 + 50.0 + 37.5 | **328.3** | 溅射 65@25 |
| nova | heal-weapon×2 | 2 | 60 | 13（治疗） | 13.0 | **26.0** | 非伤害 |
| quasar | beam-weapon×2 | 2 | 110 | 45 | 24.5 | **49.1** | 激光 |
| poly | poly-weapon×2 | 2 | 60 | 12 | 12.0 | **24.0** | inacc 15 |
| risso | mount-weapon×2 + missiles-mount | 3 | 26 / 25 | 9 / 12 | 20.8 + 28.8 | **70.3** | 溅射 10@25 |
| minke | mount-weapon×2 + artillery×2 | 4 | 20 / 60 | 3 / 20 | 9.0 + 20.0 | **58.0** | 溅射 40.5@15；40@22.5 |

可逐行复算三例：reign `2 × 60/18 × 80 = 533.3`；omura `60/110 × 1250 = 681.8`；corvus `60/350 × 560 = 96.0`。

### 表 2：版本差异注（数值取 jar，源码只作注）

| 单位 | 字段 | v160.7 jar | v159.3 源码 | 源码位置 |
|---|---|---|---|---|
| dagger | 主武器 reload | 26 ×2 挂点 | 13（单条 mirror 定义） | UnitTypes.java:107 附近 |
| mace | 主武器 reload | 44 ×2 | 22 | 同上 |
| reign | 主武器 reload | 18 ×2 | 9 | UnitTypes.java:290 块 |
| toxopid | 主武器 reload / armor | 60 ×2 / **22** | 30 / 13 | UnitTypes.java:909 |
| reign | armor | **30** | 18 | UnitTypes.java:295 |
| stell | 单发伤害 | 30 | 40 | UnitTypes.java:2669 |
| precept | 单发伤害 | 90 | 120 | UnitTypes.java:2798 |
| nova | 主武器 reload | 60 ×2 | 24 | UnitTypes.java:370 |

按 VERSION.md：**数值以 v160.7 为准，算法以源码为准**。因此 dagger 的"单位 DPS"主值是 41.5；若按源码单条定义 `60/13 × 9 × 2 挂点 = 83.1`，那是 v159.3 口径，本文不采用（只在此注明）。

## 源码锚点

- `type/Weapon.java:31-163` 全部字段：`name`(L31)、`bullet`(L33)、`mirror=true`(L39)、`alternate=true`(L43)、`rotate=false`(L45)、`baseRotation=0`(L49)、`top=true`(L51)、`controllable`(L59)、`alwaysShooting`(L63)、`autoTarget`(L65)、`predictTarget`(L67)、`targetInterval=40`(L71)、`rotateSpeed=20`(L73)、`reload=1`(L75)、`inaccuracy=0`(L77)、`recoil=1.5`(L81)、`cooldownTime=20`(L89)、`shootX=0 shootY=3`(L91)、`x=5f y=0f`(L93)、`shootCone=5`(L105)、`rotationLimit=361`(L107)、`shootWarmupSpeed=0.1`(L111)、`shootStatusDuration=300`(L155)。
- `Weapon.java:188-194` `dps() = (bullet.estimateDPS()/reload)*shoot.shots*60`、`shotsPerSec()`。
- `UnitType.java:286` `public Seq<Ability> abilities`；:363-367 命令与姿态按能力自动分配。
- `BulletType.java:414-432` `estimateDPS`（面板 DPS 与单位 DPS 同源，溅射按 75% 计）。
- `00-data/units.json` 每条单位的 `weapons[]` 已是**逐挂点**清单（含 `x/y`、`reload`、`bullet` id、`mirror`、`alternate`），可直接求和。

## 实测与反例

**反例 1：把 jar 的挂点表再乘一次 mirror。**
dagger 的 jar 数据是 2 个挂点、每点 reload 26 → 41.5 就是单位 DPS。再乘 2 得到 83.1，那是"v159.3 源码单条定义 × 2 挂点"的口径，与 jar 结构重复计数。

**反例 2：把 `alternate` 当成"减半射速"。**
alternate 只让左右交替开火（相位差），两挂点各自按 reload 装填，总射速不变。真正减半的是一个挂点被 `rotate=false` + `shootCone` 挡住时。

**反例 3：以为 `x/y` 是像素屏幕坐标。**
`x` 沿武器朝向、`y` 侧向；单位转 90° 后同一挂点落点完全不同。modder 常把 `x=4` 写成"往右 4px"导致炮口错位。

**反例 4：用面板 DPS 判断 collaris。**
面板把溅射 120 按 75% 计 → 数字虚高；jar 直伤只有 2 × 60/260 × 195 = **90.0**（对单目标），不是 240+。

**反例 5：拿"炮管数"估 arkyid。**
arkyid 有 8 个挂点（6 个 sap 小炮，reload 分别是 18/18/28/28/44/44，+ 2 个 purple 炮 reload 90），直伤合计 **563.2** DPS；只看那门"大炮"（12 × 60/90 = 8.0）会把它的输出低估两个数量级。若把 6 门小炮都当 reload 18 算，会虚高成 816.0。

**可复算**：conquer 单发 270、reload 100、1 个挂点 → `60/100 × 270 = 162.0 DPS`；对 13 甲目标 `max(270-13, 27) = 257` → `0.6 × 257 = 154.2 DPS`。护甲几乎无效，因为 270 ≫ 13。

## 常见误解

- ❌ "`weapons` 数组里每项就是一个炮管"。→ 源码里 mirror 默认 true 会生成两个挂点，jar 则把两个挂点**都列出来**。
- ❌ "`shootCone=360` 表示全向索敌"。→ 是**允许开火的角度范围**，索敌仍受 `targetAir/targetGround` 与武器 `bullet` 限制。
- ❌ "`reload` 越小越好，无下限"。→ 还要等 `cooldownTime` 与 `shootWarmup`，且 `reload < cooldownTime` 时以 cooldown 为准。
- ❌ "单位武器可以随便换弹"。→ 单位没有弹药系统，`bullet` 固定；"换弹"是炮塔（ItemTurret）专属。
- ❌ "治疗武器造成伤害"。→ nova/mega 的 heal-weapon 走 `healAmount/healPercent`，不扣血。

## 相关

- [[COMBAT.BULLET.001]] 武器发射的 bullet 字段
- [[COMBAT.NUMBERS.001]] 用这些 DPS 算 TTK
- [[COMBAT.ARMOR.001]] 单位护甲梯度（jar 值）
- [[UNIT.ABILITY.001]] 能力与武器是两套并行系统
- [[UNIT.MOVE.001]] 单位 speed 与武器射程的配合
