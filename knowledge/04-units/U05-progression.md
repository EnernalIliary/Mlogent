---
id: UNIT.PROGRESSION.001
title: 单位成长——没有经验与等级，只有档次、波次表与难度乘数
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:183,759-784"
  - "Mindustry-Source/core/src/mindustry/content/UnitTypes.java:4572,4613"
  - "Mindustry-Source/core/src/mindustry/type/unit/MissileUnitType.java:18"
  - "Mindustry-Source/core/src/mindustry/game/Waves.java:15-130,365-394"
  - "Mindustry-Source/core/src/mindustry/game/SpawnGroup.java:23-73"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:83-88,290-306"
  - "Mindustry-Source/core/src/mindustry/game/CampaignRules.java:39-41"
  - "Mindustry-Source/core/src/mindustry/ai/types/LogicAI.java:16-22,49-64"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:179-205,322-352"
  - "Mindustry-Source/core/src/mindustry/logic/LStatements.java:1070-1099"
data: [00-data/units.json]
depends: [UNIT.PRODUCE.001, UNIT.AI.001]
tags: [等级, 经验, 波次, 难度, ubind, ucontrol, 逻辑控制]
tokens: 896
---

## 一句话

**v159.3 与 v160.7 都没有单位经验/等级系统**（`UnitType` 无 `level/exp` 字段，全树 grep "experience" 0 命中，v160.7 jar 的 4842 个 class 字符串扫描同样 0 命中）；玩家感受到的"成长"来自四条真实机制：**重构链升阶、波次解锁表、难度乘数、逻辑 `ucontrol` 接管（10 秒超时）**。

## 规则 / 公式

### 1. 负面证据（为什么可以断言"没有等级"）

```
UnitType.java      → 无 level / exp / xp / rank / tier 字段（字段区 55-130 行）
Unit.java (gen)    → grep level|exp|lvl|tier|rank 只命中 mineTier / deathExplosionEffect / unitExplode1-3 / dynamicExplosion
v160.7 jar         → mindustry/type/UnitType.class、gen/Unit.class、type/Weapon.class 常量池无 experience 字符串
```

### 2. 真实的"升阶"：重构链

```
T1 dagger(150 hp, 0 armor) → T2 mace(550, 4) → T3 fortress(900, 9) → T4 scepter(9000, **20**) → T5 reign(24000, **30**)
```

升级靠 `Reconstructor.upgrades` 表（见 [[UNIT.PRODUCE.001]]），**不可逆、不吃经验、不需要击杀**，只吃物品、电和时间。

### 3. 波次表：敌人"变强"的真实来源

每个 `SpawnGroup` 有 `begin/end/spacing/unitAmount/unitScaling/max/shields/shieldScaling/effect`：

```
getSpawned(wave) = min(unitAmount + floor(((wave - begin)/spacing)/unitScaling), max)   // SpawnGroup.java:67-73
getShield(wave)  = max(shields + shieldScaling*(wave - begin), 0)                        // :75-77
```

波次变强不是"单位升级"，而是**更强的新 SpawnGroup 从某个 begin 波开始入场**。

### 4. 难度乘数（乘在 waveTeam 上）

```
CampaignRules.java:39-41
  waveTeam.unitHealthMultiplier = difficulty.enemyHealthMultiplier
  waveTeam.unitCostMultiplier   = 1 / difficulty.enemySpawnMultiplier
Rules.unitHealth(team) = max(unitHealthMultiplier * team.unitHealthMultiplier, 1e-6)   // :304
```

### 5. `ubind` / `ucontrol`（逻辑控制，单位视角）

```
ubind @type
  → 只能绑 logicControllable 单位（UnitType.java:183 默认 true）
  → 只能绑本队（exec.team）或 privileged 执行器（LExecutor.java:200）
  → 同类型按 id 轮询：binds[type.id]++（LExecutor.java:188-195）
ucontrol ...
  → 首次控制把 unit.controller 换成 LogicAI，并清 mineTile / clearBuilding()（:328-336）
  → 每次 ucontrol 刷新 controlTimer = logicControlTimeout = 60*10 = 600 tick（LogicAI.java:18）
  → 10 秒没有新的 ucontrol → resetController() 回默认 AI（LogicAI.java:59-64）
```

**21 种 `ucontrol` 的参数表见 [[MLOG.UNIT.001]]（M07），本文只写单位侧语义。**

## 数值

### 单位档次（health / armor / hitSize；hp 与 hitSize 两版一致，armor 取 v160.7 jar，见下注）

| 链 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| 地面机械 | dagger 150/0/8 | mace 550/4/10 | fortress 900/9/13 | scepter 9000/**20**/22 | reign 24000/**30**/30 |
| 飞行 | flare 70/0/9 | horizon 340/3/11 | zenith 700/5/20 | antumbra 7200/**17**/46 | eclipse 22000/**22**/58 |
| 蜘蛛 | crawler 150/0/8 | atrax 600/3/13 | spiroct 1000/**9**/15 | arkyid 8000/**14**/23 | toxopid 22000/**22**/26 |
| 海军 | risso 280/2/10 | minke 600/4/13 | bryde 910/7/20 | sei 11000/12/39 | omura 22000/16/58 |

**版本注**：护甲取 v160.7 jar（`00-data/units.json`）；v159.3 源码同名字段更低——spiroct 5（`UnitTypes.java:746`）、arkyid 6(:805)、toxopid 13(:909)、eclipse 13(:1264)、antumbra 9、scepter 10(:194)、reign 18(:295)。hp 与 hitSize 两版一致。

**T5 相对 T1 的 health 倍率**：reign/dagger = 24000/150 = **160×**；toxopid/crawler = 22000/150 ≈ **146.7×**；omura/risso = 22000/280 ≈ **78.6×**。

### 波次表节选（Waves.java:20-130）

| SpawnGroup | begin | end | spacing | unitAmount | unitScaling | max | shields / shieldScaling | effect |
|---|---|---|---|---|---|---|---|---|
| dagger | 0 | 10 | 1 | 1 | 2 | 30 | — | — |
| crawler | 4 | 13 | 1 | 2 | 1.5 | 40 | — | — |
| flare | 12 | 16 | 1 | 1 | 1 | 40 | — | — |
| mace | 7 | 30 | 3 | 1 | 2 | 40 | — | — |
| fortress | 40 | — | — | — | — | — | — | — |
| spiroct | 45 | — | 3 | 1 | 1 | 10 | shields 100 / +30 每波 | overdrive |
| quasar | 82 | — | 3 | 4 | 3 | 40 | +30 每波 | overdrive |
| pulsar | 120 | — | 2 | 5 | 3 | 40 | — | overdrive |

### 难度五档（Difficulty 枚举）

| 难度 | enemyHealthMultiplier | enemySpawnMultiplier | waveTimeMultiplier |
|---|---|---|---|
| casual | 0.5 | 0.5 | 2 |
| easy | 1 | 0.75 | 1.5 |
| normal | 1 | 1 | 1 |
| hard | 1.25 | 1.5 | 0.8 |
| eradication | 1.5 | 2 | 0.6 |

hard 相对 normal：敌人 **1.25× 血**、**1.5× 数量**、**0.8× 波间隔**。

### 逻辑控制关键常量

| 量 | 值 | 来源 |
|---|---|---|
| `logicControlTimeout` | **600 tick = 10 s** | LogicAI.java:18 |
| `transferDelay` | 90 tick = 1.5 s | LogicAI.java:16 |
| `rules.logicUnitControl` 默认 | **true** | Rules.java:99 |
| `UnitType.logicControllable` 默认 | **true** | UnitType.java:183 |
| 不可逻辑控制的单位 | `manifold`（UnitTypes.java:4572）、`assemblyDrone`（:4613）、所有 `MissileUnitType`（MissileUnitType.java:18） | — |
| `ubind` 每类型轮询 | `binds[type.id]++` | LExecutor.java:188-195 |
| boss 首次波 | `rand(50,70)` | Waves.java:365 |
| 终局 boss 波 | `120 + rand(30)` | Waves.java:394 |

## 源码锚点

- [src: UnitType.java:183] `logicControllable = true`（`UnlockableContent` 字段区的开关）。
- [src: UnitType.java:759-761] `public boolean isBanned(){ return state.rules.isBanned(this); }` —— 被禁用的单位 `canCreate` 直接失败。
- [src: UnitType.java:768] `for(UnitType[] recipe : r.upgrades)` —— 重构链是**唯一**的单位强度成长路径。
- [src: SpawnGroup.java:23,36] `unitScaling = UnitScaling.never`；`:42` `unitAmount = 1`。
- [src: Waves.java:365-368] `bossWave = rand(50,70) * lerp(1,0.5,diff)`；`bossTier = diff < 0.6 ? 3 : 4`。
- [src: LogicAI.java:18] `logicControlTimeout = 60f * 10f`。
- [src: LogicAI.java:59-64] `controlTimer <= 0` → `unit.resetController()`。
- [src: LExecutor.java:186-205] `ubind` 的三条分支（UnitType 轮询 / 具体 Unit / null）。
- [src: LExecutor.java:344] 非 privileged 执行器需 `state.rules.logicUnitControl`。

## 实测与反例

**反例 1：以为"杀敌升级"。**
全树没有 `experience` 字段；一个 dagger 打 1000 个 crawler 仍是 150 hp、9 伤害（`BulletType(2.5, 9)`）。想变强只能重构成 mace（550 hp）——这是**换单位**，不是升级。

**反例 2：以为高波次敌人是"等级更高"。**
波 45 出现 spiroct 时，它的 health 仍是 1000（源码固定），但 `getShield(45) = 100 + 30*(45-45) = 100` 且每过一波 +30 —— **护盾**在涨，本体不变。wave 60 时该组护盾 = `100 + 30*15 = 550`。

**反例 3：以为 `ucontrol` 可以永久接管。**
`logicControlTimeout = 600` tick。逻辑处理器只需每 10 秒至少发一条 `ucontrol`，否则单位 `resetController()`——这是"逻辑阵突然失灵"的最常见原因（处理器被摧毁/断电同样立即断控）。

**反例 4：以为 `ubind` 能绑敌人。**
`ubind` 只接受 `exec.team` 的单位或 privileged 执行器（LExecutor.java:200）；`@enemy` 之类的类型若属敌队则绑定为 null（:198/:204）。

**可复算**：hard 难度 wave 60 的 spiroct 组（begin 45, shields 100, shieldScaling 30）：
`getShield(60) = 100 + 30 × (60-45) = 550`；`getSpawned(60) = min(1 + floor(((60-45)/1)/1), 10) = 10`（max=10）。
→ 10 只 spiroct，每只 1000 hp + 550 护盾 = **15500 有效血量**，且全部带 `overdrive`（StatusEffects 加速 1.15 攻速/移速）。

## 常见误解

- ❌ "单位有等级/星级"。→ 没有；星级图标是 mod 或旧版本记忆。
- ❌ "难度只影响敌人血量"。→ 还影响数量（enemySpawnMultiplier）与波间隔（waveTimeMultiplier）。
- ❌ "`unitHealthMultiplier` 随波数增长"。→ 只在难度初始化时设一次（CampaignRules.java:40）。
- ❌ "`logicControllable` 的单位都能被 `ucontrol` 控制"。→ 还要 `exec.privileged || rules.logicUnitControl`（规则可关）。
- ❌ "`ubind` 一次绑全部同型单位"。→ 每次只推进一个，靠 `binds[type.id]++` 轮询。

## 相关

- [[UNIT.PRODUCE.001]] 重构链与工厂配方
- [[UNIT.AI.001]] LogicAI 与默认 AI 的切换
- [[UNIT.ABILITY.001]] 能力不随波次成长
- [[COMBAT.WAVE.001]] 波次生成与难度乘数
- [[MLOG.UNIT.001]] `ucontrol` 21 种参数的完整表（M07）
