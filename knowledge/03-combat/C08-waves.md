---
id: COMBAT.WAVE.001
title: 敌方与攻击波——生成点、波次组成、难度缩放与 AI 目标
domain: combat
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/ai/WaveSpawner.java:62-160"
  - "Mindustry-Source/core/src/mindustry/game/SpawnGroup.java:26-78"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:151-152,302-306"
  - "Mindustry-Source/core/src/mindustry/game/Difficulty.java:5-21"
  - "Mindustry-Source/core/src/mindustry/game/Waves.java:356-400"
  - "Mindustry-Source/core/src/mindustry/entities/Units.java:114-125,307-310"
  - "Mindustry-Source/core/src/mindustry/core/Logic.java:272,322"
data: [00-data/rt_list_WaveSpawner.json, 00-data/rt_list_Difficulty.json]
depends: [COMBAT.ARMOR.001, UNIT.AI.001]
tags: [波次, 敌基, 生成, 难度, boss, 攻击模式]
tokens: 752
---

## 一句话

攻击波由 `rules.spawns` 里的一串 `SpawnGroup` 驱动，数量公式是 **`min(unitAmount + ⌊((wave−begin)/spacing)/unitScaling⌋, max)`**；强度提升有三条独立通道——**数量（unitScaling）、血量（难度 enemyHealthMultiplier → team.unitHealthMultiplier）、护盾（shieldScaling）**，三者相乘而不是相加。

## 规则 / 公式

### 1. 每波生成多少单位

```
getSpawned(wave):
    if(spacing == 0) spacing = 1
    if(wave < begin || wave > end || (wave - begin) % spacing != 0) return 0
    return min(unitAmount + (int)(((wave - begin) / spacing) / unitScaling), max)

默认: unitAmount = 1, max = 40, spacing = 1, unitScaling = never(Integer.MAX_VALUE)
```

- `spacing = 1` → 每波都生成；`spacing = 5` → 每 5 波一次。
- `unitScaling = never` → 数量**永远不涨**（原版默认）；`unitScaling = 10` → 每 10 个"spacing 周期"多 1 个。
- 上限 `max = 40`：单组最多 40 个。

### 2. 护盾

```
getShield(wave) = max(shields + shieldScaling * (wave - begin), 0)
```

boss 组用 `shieldScaling = shieldsPerWave`，所以后期 boss 出场自带护盾。

### 3. 战役难度缩放（三个乘数）

| 难度 | enemyHealthMultiplier | enemySpawnMultiplier | waveTimeMultiplier |
|---|---|---|---|
| casual | 0.5 | 0.5 | 2.0 |
| easy | 1.0 | 0.75 | 1.5 |
| normal | 1.0 | 1.0 | 1.0 |
| hard | 1.25 | 1.5 | 0.8 |
| eradication | 1.5 | 2.0 | 0.6 |

- **数量**：`spawned *= enemySpawnMultiplier`；boss 组用 `(int)` 向下取整（1.5×1 个 boss 不会变成 2 个），非 boss 用 `Mathf.round`。
- **血量**：`CampaignRules` 把 `difficulty.enemyHealthMultiplier` 写进 `rules.teams.get(waveTeam).unitHealthMultiplier`，最终 `unitHealth(team) = rules.unitHealthMultiplier × team.unitHealthMultiplier`，在伤害管线里作**除数** → 1.5 倍血量即"受到伤害 ÷1.5"。
- **时间**：`state.wavetime = waveSpacing × waveTimeMultiplier`。

### 4. 波次间隔

```
rules.waveSpacing = 2 * Time.toMinutes = 7200 tick = 120 s
首波: wavetime = (initialWaveSpacing <= 0 ? waveSpacing*2 : initialWaveSpacing)   // 默认 240 s
```

### 5. 生成点与冲击波

```
eachGroundSpawn: 遍历 state.rules.spawns 的落点（地图上的敌基 spawn 标记）
   → doShockwave: 范围内 waveTeam 单位受 99999999 伤害（清场，保证落点空出）
地面 spread = tilesize * 2 = 16 px；飞行 spread = margin / 1.5
attackMode / wavesSpawnAtCores: 从敌方核心 "指挥点" 生成，距玩家核心 coreMargin = 16 格
```

### 6. AI 目标选择

```
Units.bestTarget(team, x, y, range, ...):
    if(dst2 < range² && (result == null || dst2 < cdist || e.type.targetPriority > cpriority) && e.type.targetPriority >= cpriority)
```

单位按 `UnitType.targetPriority` 抢优先级（数值越大越优先），并同时受距离约束。原版大多数单位是默认 0；`targetPriority = -2` 的单位（UnitTypes.java:4348/4413/4493）是"建造/辅助型"，不会被优先盯。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| `rules.waveSpacing` | 7200 tick = **120 s** | Rules.java:151；v160.7 反射 default 7200 |
| 首波延迟 | 240 s（normal） | Logic.java:272 |
| `SpawnGroup.max` | 40 | SpawnGroup.java:34；反射 default 40 |
| `SpawnGroup.unitAmount` | 1 | SpawnGroup.java:42 |
| `SpawnGroup.unitScaling` | never = Integer.MAX_VALUE | SpawnGroup.java:23,36 |
| `WaveSpawner.coreMargin` | 16.0 格 | WaveSpawner.java:38；反射 const=16.0 |
| 地面生成散布 | 16 px | WaveSpawner.java:95 |
| 冲击波伤害 | 99999999 | WaveSpawner.java:118 |
| 首个 boss 波 | `random(50,70)×lerp(1,0.5,difficulty)` → normal 50~70 / eradication 25~35 | Waves.java:365 |
| boss 间隔 | `random(25,40)×lerp(1,0.5,difficulty)` → normal 25~40 波 | Waves.java:366 |
| boss 组上限 | max = 16 | Waves.java:376 |
| 最终 boss 起始 | `120 + random(30)` = 120~150 波 | Waves.java:394 |
| boss 强度 | `StatusEffects.boss`（damageMultiplier 1.3、healthMultiplier 1.5、permanent） | StatusEffects.java:178-183 |

## 源码锚点

- `WaveSpawner.java:62-109` `spawnEnemies`：冲击波 → 遍历 spawns → 难度乘数 → 飞行/地面分组生成 → `Time.run(121f, spawning=false)`。
- `WaveSpawner.java:111-113` `spawnUnit`：朝向地图中心，wave 传 `state.wave - 1`（Spawning 语义从 0 计）。
- `WaveSpawner.java:116-119` `doShockwave`：`Damage.damage(waveTeam, x, y, dropZoneRadius, 99999999f, true)`。
- `WaveSpawner.java:125-160` `eachGroundSpawn`：spawn 标记 + `wavesSpawnAtCores && attackMode` 时的核心落点（`coreMargin + size*tilesize/2*sqrt2`）。
- `SpawnGroup.java:67-78` `getSpawned` / `getShield`。
- `Rules.java:151` `waveSpacing = 2*Time.toMinutes`；`:302-306` `unitHealth(team)`。
- `CampaignRules.java:39-40` 把难度写进 `waveTeam` 的 `blockHealthMultiplier/unitHealthMultiplier`。
- `Difficulty.java:5-10` 五档难度数值。
- `Waves.java:356-400` 波次编排：5~5+rand(5) 起步，每 `rand(15,30)×lerp(1,0.5,difficulty)` 波升一档，`curTier` 上限 3（boss 除外用 4）。
- `Units.java:114-125` `canCreate/getCap`（波次队伍在非 pvp 战役里 cap = MAX_VALUE）。
- `Units.java:307-310` `bestTarget` 的 targetPriority 比较。

## 实测与反例

**反例 1：以为波数越高敌人数量一定越多。**
原版 `unitScaling = never`，普通组数量是**恒定**的。波数提升主要靠"解锁更高 tier 的单位类型"（Waves 的 curTier 递进），不是靠数量。

**反例 2：以为难度只影响血量。**
hard 是 `1.25 hp × 1.5 数量 × 0.8 间隔`，三项同时变——实际压力接近 `1.25×1.5/0.8 ≈ 2.34 倍`。

**反例 3：以为冲击波是特效。**
`doShockwave` 对 `dropZoneRadius`（默认 300px）内**waveTeam 单位**造成 99999999 伤害——它是"落点清场"，也会打死刚生成在那里的残血敌人。

**反例 4：以为 boss 是"波数到 50 就来"。**
boss 波是随机的 50~70，之后每 25~40 波一个，且**两条独立线程**（主 boss + 偏移 `rand(3,5)×bossSpacing` 的替补 boss），可出现连环 boss 波。

**可复算**：normal 难度、首波在 `t=240s`，之后每 120 s 一波；到第 10 波共耗时 `240 + 9×120 = 1320 s = 22 min`。若把 waveSpacing 用逻辑处理器改成 60（`LExecutor.java:1778` 的 `value.numf()*60`），则每 60 s 一波。

## 常见误解

- ❌ "`spacing` 是秒"。→ 是**波数**间隔。
- ❌ "`max=40` 是全场敌人上限"。→ 是**单组**上限。
- ❌ "敌人血量随波数线性涨"。→ 原版**不随波数涨**，只随难度（team.unitHealthMultiplier）与单位类型档次。
- ❌ "飞行单位也走地面生成点"。→ 飞行用 `eachFlyerSpawn`，散布 `margin/1.5`，与地面 16px 不同。
- ❌ "wave 传的是当前波号"。→ `spawnUnit` 传 `state.wave - 1`，差 1 会让首波缩放算错。

## 相关

- [[UNIT.AI.001]] 单位如何选目标、如何寻路
- [[UNIT.PRODUCE.001]] 单位上限与敌方无上限的差异
- [[COMBAT.DEFENSE.001]] 用什么挡波次
- [[COMBAT.STATUS.001]] boss 状态的 1.3 伤害 / 1.5 血量
