---
id: CAMP.SPAWN.001
title: 刷怪组数据模型——SpawnGroup 的 8 个字段怎么变成每波的数量与护盾
domain: camp
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/game/SpawnGroup.java:26-42,67-77,92"
  - "Mindustry-Source/core/src/mindustry/game/Waves.java:13,17-256,271-444"
  - "Mindustry-Source/core/src/mindustry/ai/WaveSpawner.java:62-109"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:177"
data: [00-data/formulas.json, 00-data/constants_rules_difficulty_drill_heat.json]
depends: [CAMP.WAVES.001, CAMP.DIFFICULTY.001]
tags: [SpawnGroup, 刷怪, 护盾, 波次, 关卡数据]
tokens: 733
---

## 一句话

每个刷怪组（SpawnGroup）只是 8 个数值字段；「这一波刷不刷」「刷几只」「带多少盾」是三件**互相独立**的计算，固定关卡里这些字段写死在 `Waves.get()`，随机地图由 `Waves.generate()` 现场造。

## 规则 / 公式

```
w = state.wave - 1                                     // WaveSpawner.java:74

刷不刷: begin <= w <= end 且 (w - begin) % spacing == 0   // 不满足则本波 0 只
数量:   getSpawned = min(unitAmount + (int)(((w - begin) / spacing) / unitScaling), max)   // SpawnGroup.java:72
        （(w-begin)/spacing 是整数除法；外层再除 unitScaling 后截断，故 spacing>1 时增长被稀释）
护盾:   getShield  = max(shields + shieldScaling × (w - begin), 0)                        // SpawnGroup.java:77
战役实际数量 = max(1, round(getSpawned × enemySpawnMultiplier))    // 非 boss 组        WaveSpawner.java:79-81
             = max(1, (int)(getSpawned × enemySpawnMultiplier))   // boss 组，向下取整
```

字段默认值 [src: SpawnGroup.java:26-42]：`begin=0`、`end=never(Integer.MAX_VALUE)`、`spacing=1`、`max=40`、`unitScaling=never`、`shields=0`、`shieldScaling=0`、`unitAmount=1`。因为 `unitScaling` 默认是 `never`，默认组永远只刷 `unitAmount` 只。

## 数值

固定关卡代表组（`Waves.get()` 内联 28 个组，下表为源码原值，未列字段即默认值）：

| 组 | begin | end | spacing | unitAmount | unitScaling | max | shields | shieldScaling | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| dagger | 0 | 10 | 1 | 1 | 2 | 30 | 0 | 0 | [v159.3] |
| crawler | 4 | 13 | 1 | 2 | 1.5 | 40 | 0 | 0 | [v159.3] |
| mace | 7 | 30 | 3 | 1 | 2 | 40 | 0 | 0 | [v159.3] |
| spiroct | 45 | never | 3 | 1 | 1 | 10 | 100 | 30 | [v159.3] |
| fortress | 40 | never | 5 | 2 | 2 | 20 | 0 | 30 | [v159.3] |
| scepter | 41 | never | 30 | 1 | 1 | 40 | 0 | 30 | [v159.3] |
| corvus | 145 | never | 35 | 1 | 1 | 40 | 100 | 30 | [v159.3] |
| toxopid | 210 | never | 35 | 1 | 1 | 40 | 1000 | 35 | [v159.3] |

代入公式得到的关键波（w 为组内 0 基波号，`state.wave = w + 1`）：

| 组 | w | 只数 | 护盾 | 计算过程 | 来源 |
|---|---|---|---|---|---|
| dagger | 0 / 2 / 10 | 1 / 2 / 6 | 0 | 1 + w/2，末波 w=10 撞上 end | 公式代入 |
| spiroct | 45 / 46 / 48 / 54 | 1 / 0 / 2 / 4 | 100 / 130 / 190 / 370 | 46 不满足 spacing，但护盾照涨 | 公式代入 |
| fortress | 40 / 45 / 50 | 2 / 2 / 3 | 0 / 150 / 300 | 量 2+w/10 向下取整，盾 30×(w-40) | 公式代入 |
| scepter | 41 / 71 / 101 | 1 / 2 / 3 | 0 / 900 / 1800 | spacing=30，每 30 波 +1 只 | 公式代入 |
| corvus | 145 / 180 / 215 | 1 / 2 / 3 | 100 / 1150 / 2200 | 100+30×(w-145) | 公式代入 |
| toxopid | 210 / 245 / 280 | 1 / 2 / 3 | 1000 / 2225 / 3450 | 1000+35×(w-210) | 公式代入 |

数值来源：组字段为源码实参（[src: Waves.java:20-252]）；数量/护盾列由上面的两条公式代入算出，无外部数据。

随机（生成）地图用 `Waves.generate()` 现场造组：

| 参数 | 值 | 源码 [v159.3] |
|---|---|---|
| 总波数上限 | 150 | Waves.java:299 |
| 护盾起算波 | 30 | Waves.java:301 |
| 每波护盾增量 | 20 + difficulty×30 | Waves.java:301 |
| 主组初始数量 | `6 / (int)scaling[tier]` → 6/3/2/1/1 | Waves.java:319 |
| 副组初始数量 | `3 / (int)scaling[tier]` → 3/1/1/0/0（tier≥4 整组不出现） | Waves.java:331 |
| 单组上限 | 主组 max=13，副组 max=6 | Waves.java:323-339 |
| 组长度 | `rand(8,16) + (int)lerp(5,0,difficulty) + tier×4` 波 | Waves.java:311 |
| 增长速率 | `(d<0.4 ? rand(2.5,5) : rand(1,4)) × scaling[tier]` | Waves.java:323 |
| boss 首波 | `(int)(rand(50,70) × lerp(1,0.5,difficulty))` | Waves.java:365 |

## 源码锚点

- SpawnGroup.java:72 `getSpawned`（整数除法 + 截断）、:77 `getShield`（与刷怪独立）、:92 `unit.shield = getShield(wave)`。
- Waves.java:13 `waveVersion = 7`（存档波次格式版本）；:17-256 `get()` 的 28 个固定组；:271-444 `generate()`。
- WaveSpawner.java:74 `getSpawned(state.wave - 1)`；:79-81 战役难度乘数量（boss 截断）；:86-105 飞行 spread=margin/1.5、地面 spread=8px×2=16px [src: WaveSpawner.java:74-105]。
- Rules.java:177 `spawns` 是 `Seq<SpawnGroup>`，即关卡数据就是这串对象（并非写死在代码里）[v160.7]。

## 实测与反例

**反例 1：以为 begin 之后的每一波都刷。** spiroct `begin=45, spacing=3` → 只在 w=45,48,51… 刷；w=46、47 是 0 只 [src: SpawnGroup.java:69] 。

**反例 2：以为「不刷怪」= 这一波没变化。** 护盾按 `w - begin` 线性涨，与刷不刷无关：spiroct w=46 刷 0 只，但 w=48 刷出的 2 只直接带 190 盾（而不是 160）[见公式 getShield]。

**反例 3：以为 max 是累计上限。** 它是**每波**上限：spiroct 达到 10 只后（w≥72）每 3 波仍然刷 10 只，不会停 [src: SpawnGroup.java:72]。

**反例 4：以为 unitScaling 的单位是波。** 它除的是「已走过的 spacing 周期数」：spiroct 每 3 波才 +1 只，从 1 到 10 需要 27 波（w=45→72）[src: SpawnGroup.java:72]。

**反例 5：以为低难度会少到 0 只。** 战役分支有 `Math.max(1, ...)`，`round(1×0.5)=0` 会被抬成 1 [src: WaveSpawner.java:79-81]；所以 casual 下「1 只」的组仍是 1 只，减半效果体现在多只组（如 6 → 3）。

**可复算**：toxopid（begin=210, spacing=35, shields=1000, shieldScaling=35）在 w=245：数量 = 1 + (int)((35/35)/1) = 2，护盾 = 1000 + 35×35 = 2225 → 该波实际是 2 只各 2225 盾的 T4 单位 [见公式]。

## 常见误解

- 「刷怪表是 JSON 数据文件」→ 逻辑上就是 SpawnGroup 对象序列，但固定关卡写在 Waves.java 里（28 组），不是外部数据表 [src: Waves.java:17-256]。
- 「护盾是护甲」→ 护盾是 `unit.shield` 池，先扣盾再扣血，与 `armor` 减伤是两套机制 [src: SpawnGroup.java:92]。
- 「spacing 越大越弱」→ spacing 同时控制出现频率和增长速度（见公式），40 波间隔的 corvus 一旦出现就整场压制 [见公式]。
- 「数量倍率对 boss 也生效」→ 生效但向下取整，1.5×1 仍是 1 只 [src: WaveSpawner.java:78-81]。

## 相关

- [[CAMP.WAVES.001]] 波次节奏、waveSpacing 与 T(N)
- [[CAMP.DIFFICULTY.001]] enemySpawnMultiplier 如何乘到这里
- [[COMBAT.WAVE.001]] 战斗侧视角：生成点、冲击波、boss 专属效果
- DATA.FORMULA.009 / DATA.FORMULA.010 每波数量与护盾公式
