---
id: COMBAT.NUMBERS.001
title: 战斗数值实例——DPS 定义式、跨层口径与 TTK
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
tags: [DPS, TTK, 护甲曲线, 算式, 跨层口径, 连续伤害]
tokens: 1211
---

## 一句话

一切战斗数值都由三式复算：`射速 = 60/reload`、`单发实际伤害 d = max(D − A, 0.1D)`、`DPS = 射速 × 发数 × d`；**同一门武器在"子弹层 / 载体层 / 实战层"三个口径下能差 5 倍**（meltdown 面板 4680 vs 实战 936），因为护甲只做减法，每门炮都有一个拐点 `A* = 0.9D`。

## 规则 / 公式

### 1. 三层口径定义（数字从哪来）

| 层 | 公式 | 源码 |
|---|---|---|
| 子弹层 estimateDPS | `(damage + splashDamage*0.75) * (pierce ? clamp(pierceCap,1,2) : 1) + fragDPS*fragBullets/2` | `BulletType.java:414-432` |
| 载体层（炮塔/单位武器） | `shots/reload*60 * ammo.estimateDPS()` | `Turret.java:329-331`、`Weapon.java:188-190` |
| 连续层（激光/火焰） | `damage / damageInterval * 60`，`damageInterval = 5` tick ⇒ **×12** | `ContinuousBulletType.java:11,33-35` |

连续层为什么是 ×12 而不是 ×60：伤害不是每 tick 结算，而是每 `damageInterval`（5 tick）结算一次完整 `damage`（`ContinuousBulletType.java:72` `if(b.timer(1, damageInterval)) applyDamage(b)`），所以每秒只结算 12 次。

### 2. 实战层三式（本文所有表都由它生成）

```
射速 shots/s = 60 / reload                       // reload 单位是 tick，不是秒
单发实伤 d   = max(D - A, 0.1 * D)               // 护甲只做减法 + 10% 保底
DPS          = 射速 * 发数(shots 或挂点数) * d
TTK(秒)      = 目标生命 / DPS
```

单位武器与炮塔共用同一式：炮塔的"发数"是 `shoot.shots`（多管/连发），单位武器的是挂点数 N（`mirror=true` 在 `units.json` 里展开成 N 条记录），`alternate` 时有效射速 = `N/reload`。炮塔的 shots、弹种与完整 28 门参数见 [[COMBAT.TURRET.001]]，本文只引用不重复。

## 数值

### 表 1：跨层口径对比（同一件武器，三种算法）

| 武器 | 层 | 单发 D | estimateDPS | 载体层 DPS | 实战单体 DPS | 面板/实战 |
|---|---|---|---|---|---|---|
| duo（copper） | 炮塔 | 9 | 9 | 27.0 | 27.0 | 1.00× |
| spectre（graphite） | 炮塔 | 50 | 50 | 428.6 | 428.6 | 1.00× |
| hail（graphite） | 炮塔 | 20 + 溅射 33 | 44.75 | 44.8 | 20.0 | **2.24×** |
| titan（thorium） | 炮塔 | 350 + 溅射 350 | 612.5 | 266.3 | 152.2 | **1.75×** |
| smite（surge） | 炮塔 | 250×5 | 250 | 750.0 | 750.0 | 1.00× |
| mace（flamethrower） | 单位 | 74（pierce 2） | 148 | 403.6 | 201.8 | **2.00×** |
| reign（reign-weapon） | 单位 | 80 + 溅射 18 | 187 | 1246.7 | 533.3 | **2.34×** |
| meltdown（激光） | 炮塔 | 78/5tick | 4680 | 3120 | **936** | **5.00×** |

读法：溅射、贯穿、碎片是"面板放大项"，只有打单体、不贯穿时才归 1.00×。meltdown 的 4680 来自 `estimateDPS = damage*100/damageInterval*3`（`ContinuousBulletType.java:39-44`，按"持续 100 tick、贯穿 3 个目标"假设），3120 是 `Turret.estimateDps()` 把"已是每秒值"的 estimateDPS 又按 `shots/reload*60` 除一次的产物 —— **两者都不是开火期真实值**。

### 表 3：白靶实测（真执行器，2026-11-19）

不看公式，把炮塔放进场景、给一个**打不死的靶子**，数每 tick 掉的血。协议：v160.7 执行器、1800 tick、靶子放在 `(range+minRange)/2` 的合法带上（air-only 炮塔换 flare 靶）、靶子与炮塔每 tick 都回满血、200 库存弹药。

| 炮塔（弹药） | 面板 DPS（`60/reload×shots×D`） | 白靶实测 DPS | 实测/面板 | 差异从哪来 |
|---|---|---|---|---|
| duo（copper） | 27.0 | 26.1 | 0.97× | 只差预热与飞行时间 |
| salvo（copper） | 124.1 | 119.5 | 0.96× | 同上 |
| spectre（graphite） | 428.6 | 483.3 | 1.13× | 面板把 reload 当纯射速，实战连发更密 |
| fuse（titanium） | 339.4 | 143.0 | 0.42× | 3 发里只有 1 发落到同一个点目标 |
| hail（graphite） | 20.0 | 30.2 | 1.51× | 溅射 33 也打在同一个靶上 |
| scatter（scrap） | 20.0 | 53.6 | 2.68× | 溅射 33 全额叠加（且只打空中） |
| cyclone（metaglass） | 36.0 | 244.6 | **6.79×** | 溅射 45 + 破片对单目标反复结算 |
| ripple（graphite） | 80.0 | 50.0 | 0.63× | 曲射散布，4 发里有落空 |
| foreshadow（surge-alloy） | 405.0 | **0** | 0.00× | 1800 tick 内一发未中：弹道太慢、落点散 |
| titan（thorium） | 114.1 | **0** | 0.00× | 同上，单点小目标几乎必空 |

四个结论：

1. **面板式只对直射单体成立**：duo/salvo 在 5% 内吻合，spectre 偏 13%（连发节奏比 `reload` 更密）。
2. **溅射与破片对单目标是放大器**，不是折扣：cyclone 实测是面板的 6.8 倍，因为一发炮弹的溅射 45 与破片都对同一个靶结算。
3. **曲射（ripple/foreshadow/titan）反过来**：面板假设"每发都命中"，实测单点小目标命中率极低，炮越大越明显 —— titan 一个弹夹只有 3 炮（见上文），1800 tick 打空是常态。
4. 所以"实战 DPS"必须写清**目标形态**（单体/群体、静止/移动、点目标/大目标），否则同一门炮能报出 0 到 6.8 倍面板的任意数字。

复现：`python tools/dps.py box <block>` 先查合法射界，再 `python tools/dps.py measure <block> <ammo>`；`tests/dps/` 里有纯数学层与一条只跑 duo 的实机回归。

### 表 2：单位武器层 DPS（v160.7 units.json，按挂点数折算）

| 单位 | 武器 | 挂点数 × reload(tick) | 有效射速/s | 单发 D | DPS |
|---|---|---|---|---|---|
| dagger | large-weapon | 2 × 26 | 4.615 | 9 | **41.5** |
| mace | flamethrower | 2 × 44 | 2.727 | 74 | **201.8** |
| toxopid | large-purple-mount（shots 2） | 2 × 60 | 4.000 | 110 | **440.0** |
| reign | reign-weapon | 2 × 18 | 6.667 | 80 | **533.3** |
| omura | omura-cannon | 1 × 110 | 0.545 | 1250 | **681.8** |
| corvus | corvus-weapon | 1 × 350 | 0.171 | 560 | **96.0** |

单位武器的参数（挂点 x/y、shootCone、alternate）见 [[COMBAT.UNITWEAPON.001]]；这一层没有"多管"概念，只有挂点数。toxopid 本表只计主武器 2×large-purple-mount（440.0）；加上 toxopid-cannon（1×210、单发 50）= 454.3，与 C06 表 1 一致。

口径（v160.7 jar 复测）：`dps = Σ挂点 (bullet.damage × shoot.shots × 60 / reload)`；`mirror=true` 的挂点已复制成两把、且 jar 里的 reload 已是 ×2 后的值（`UnitType.java:1129-1145`、`Weapon.java:189`），但 `shots` 仍要乘——toxopid 每挂点 `shots=2`，所以是 2 挂点 × 2 发 × 110 × 60/60 = 440.0，而不是 220.0。

### 表 3：TTK（秒；靶：dagger 150hp/0甲、fortress 900hp/9甲、toxopid 22000hp/**22 甲**）

toxopid 护甲取 v160.7 jar 的 22（`00-data/units.json`）；v159.3 源码 `UnitTypes.java:909` 是 13。用 13 算会把 TTK 低估约 1/3（见反例 3）。

| 炮塔 | DPS(0甲) | vs dagger | vs fortress(9) | vs toxopid(22) |
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

复算三例（都能在计算器里按一遍）：
- spectre vs toxopid：`d = max(50−22, 5) = 28`；`DPS = 60/7 × 28 = 240.0`；`TTK = 22000/240 = 91.67 s`。
- duo vs toxopid：`d = max(9−22, 0.9) = 0.9`（撞保底）；`DPS = 3 × 0.9 = 2.7`；`TTK = 22000/2.7 = 8148.15 s ≈ 2.26 小时`。
- meltdown vs fortress：`d = max(78−9, 7.8) = 69`；每 5 tick 结算一次 ⇒ `DPS = 69/5×60 = 828`；`TTK = 900/828 = 1.09 s`。

### 表 4：护甲曲线（DPS；A = 目标护甲）

| 炮塔 | 0 | 4 | 9 | 13 | 16 | 20 | 22 | 26 |
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

拐点 `A* = 0.9D`（超过就恒定吃 10%）：duo 8.1、scorch 15.3、salvo 13.5、cyclone 5.4、hail 18、spectre 45、lancer 126、breach 76.5、titan 315、smite 225、malign 63、meltdown 70.2。曲线在 `A*` 左侧斜率 = `−射速×发数`，右侧水平。

## 源码锚点

- `entities/Damage.java:659-661`：`applyArmor = max(damage - armor, minArmorDamage * damage)`。
- `Vars.java:133`：`minArmorDamage = 0.1f`（10% 保底）。
- `entities/bullet/BulletType.java:414-432`：`estimateDPS()`，含 `splashDamage*0.75` 与 `pierceCap` 放大。
- `entities/bullet/ContinuousBulletType.java:11` `damageInterval = 5f`；`:33-35` `continuousDamage = damage/damageInterval*60`；`:72` 每 5 tick 结算一次。
- `type/Weapon.java:188-190`：`dps() = (bullet.estimateDPS()/reload)*shoot.shots*60`；`:75` `reload` 默认 1（tick）。
- `world/blocks/defense/turrets/Turret.java:720-735`：`reloadCounter += delta()*ammoReloadMultiplier()*baseReloadSpeed()`，够 `reload` 就开火。
- `Turret.java:329-331`：`estimateDps() = shots/reload*60 * ammo.estimateDPS() * potentialEfficiency * timeScale`。
- `content/Blocks.java:4331` meltdown `ContinuousLaserBulletType(78)`；`:4323` `reload = 90f`；`:4325` `shootDuration = 230f`。
- `content/Blocks.java:4643` titan thorium `ArtilleryBulletType(2.5f, 350)` + `splashDamage = 350`；`:3466` hail `(3f,20)` + `splashDamage = 33`。
- `content/UnitTypes.java:107` dagger 源码 `reload = 13f`（v160.7 jar 为每条镜像挂点 26）。

## 实测与反例

**反例 1：把面板 DPS 当实战 DPS。**
meltdown 面板 4680（estimateDPS 口径），实战开火期只有 936，差 **5 倍**；hail 面板 44.8，打单体 20，差 2.24 倍；titan 面板 266.3，直击 152.2。面板只适合"同类型同弹种横向比"，跨类型比必然错。

**反例 2：以为多管 = 多倍伤害（把 ammoPerShot 当发数）。**
v160.7 `turrets.json` 里 titan `ammoPerShot = 4`、smite `ammoPerShot = 2`，但它们是**耗弹量**不是子弹数：titan 每发打 1 颗 350，smite 每发打 5 颗 250（`Blocks.java:5721-5727` `ShootAlternate{shots = barrels = 5}`）。反过来 smite 的 5 发是**顺序**喷出的（ShootAlternate），不是同一 tick 全中。

**反例 3：拿 v159.3 源码的护甲/装填算 v160.7。**
toxopid 护甲源码 13、jar 22：spectre 对它的 TTK 从 69.37 s 变 91.67 s（+32%）。dagger 主武器源码 `reload = 13`、jar 每条挂点 26（两挂点交替），若按 13 算会得 83 DPS，是 v160.7 的 41.5 的 2 倍。**规则：数值取 v160.7，算法取源码。**

**反例 4：以为 TTK 随 DPS 线性变化。**
duo 对 dagger 5.56 s、对 toxopid 8148 s：DPS 只降 10 倍，TTK 却涨 1466 倍 —— 因为护甲同时把单发压到 10% 保底，护甲是 TTK 的非线性放大器。

**正例核对**：scorch 对 fortress `d = max(17−9, 1.7) = 8`，`DPS = 10×8 = 80`，`TTK = 900/80 = 11.25 s`；对 toxopid（22 甲）`d = 1.7`（撞保底），`DPS = 17`，`TTK = 1294.12 s`。

## 常见误解

- ❌ "DPS 高就强"。→ 对重甲看**单发 D**，对轻甲看 DPS，对群看溅射半径与 falloff。
- ❌ "reload 是秒"。→ reload 单位是 tick，`reload/60` 才是秒；把 reload 当秒会算成 1/60 的射速。
- ❌ "连续激光 DPS = damage × 60"。→ 是 `damage/5 × 60`（`damageInterval = 5`），×60 会高估 5 倍。
- ❌ "溅射伤害按半径均摊"。→ 中心 100%、边缘 40%，线性衰减（`Damage.java:652-656`，falloff 0.4）。
- ❌ "多管炮塔 shots 翻倍则精度不变"。→ swarmer 4 连发有 spread、smite 5 发顺序喷出，移动靶会漏。
- ❌ "护甲能把伤害减到 0"。→ 保底 10%，`max(D−A, 0.1D) > 0`。

## 相关

- [[COMBAT.TURRET.001]] 28 门炮塔的 reload/range/shots/弹药全表（本文表 1、表 3 的输入）
- [[COMBAT.ARMOR.001]] 护甲公式、穿甲、免疫的完整推导
- [[COMBAT.BULLET.001]] 单发伤害、溅射半径、穿透与 frag
- [[COMBAT.UNITWEAPON.001]] 单位武器的挂点与 alternate 口径
- [[COMBAT.DEFENSE.001]] 防御方块的 hp/护甲（TTK 的反向应用）
- [[UNIT.MOVE.001]] 单位 speed 决定能否进入射程（射程外的 DPS 等于 0）
- [[COMBAT.TURRET.002]] 用这些数字做选型：该造哪门、拐点在哪（DPS/造价与 A* 表）
