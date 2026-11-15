---
id: CAMP.WAVES.001
title: 波次节奏的数值模型——waveSpacing、首波宽限与倒计时推进
domain: camp
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:31,47,151-157"
  - "Mindustry-Source/core/src/mindustry/core/Logic.java:269-297,315-325,327-345,585-591,617"
  - "Mindustry-Source/core/src/mindustry/core/GameState.java:19"
  - "Mindustry-Source/core/src/mindustry/game/Difficulty.java:5-10"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1772-1780"
data: [00-data/formulas.json, 00-data/constants_rules_difficulty_drill_heat.json]
depends: [COMBAT.WAVE.001]
tags: [波次, 计时, waveSpacing, 难度, 逻辑规则]
tokens: 570
---

## 一句话

波次只看两个状态：`state.wave`（当前波号）与 `state.wavetime`（距下一波剩余 tick）；`waveSpacing` 默认 `2 × Time.toMinutes = 7200 tick = 120 s` [src: Rules.java:151]，首波是它的 **2 倍**，战役难度只乘 `waveTimeMultiplier`，不改波号与每波的组成。

## 规则 / 公式

```
waveSpacing = 2 * Time.toMinutes        // 7200 tick = 120 s                  [Rules.java:151]
首波 wavetime = (initialWaveSpacing <= 0 ? waveSpacing*2 : initialWaveSpacing) * waveTimeMultiplier   [Logic.java:272]
之后 wavetime = waveSpacing * waveTimeMultiplier                                                   [Logic.java:322]
到达第 N 波时刻 T(N) = 首波间隔 + (N - 1) × 间隔                    （N ≥ 1，从开局计时）
```

倒计时推进（每 tick）：

```
if(rules.waves && rules.waveTimer && !gameOver) wavetime = max(wavetime - Time.delta, 0)   [Logic.java:585-587]
if(wavetime <= 0 && rules.waves) runWave()                                                  [Logic.java:591]
runWave(): spawner.spawnEnemies(); wave++; wavetime = 间隔                                  [Logic.java:319-325]
```

- `waveTimeMultiplier` 只在 `state.isCampaign()` 时读取（行星 campaignRules 的难度），非战役恒为 1。
- `initialWaveSpacing > 0` 时首波不再翻倍（地图作者可自定义宽限）。
- `skipWave()` 就是直接 `runWave()`，不改变 waveTimer 开关状态。
- `waitEnemies = true`，或 `wave >= winWave > 0` 时，倒计时**暂停**直到场上敌人清空：
  `(rules.waitEnemies || (wave >= winWave && winWave > 0)) && enemies > 0` [Logic.java:617]
- 逻辑处理器写规则时**单位是秒**：`set waveSpacing = 120` → `rules.waveSpacing = 120 × 60`；`set currentWaveTime` 同理 ×60 [LExecutor.java:1774,1778]。而 `enemyCoreBuildRadius`/`dropZoneRadius` 是 ×8（格→世界单位）[LExecutor.java:1779-1780]。

## 数值

| 难度 | waveTimeMultiplier | 首波 | 波间隔 | 第 10 波 | 第 30 波 | 第 50 波 | 来源 |
|---|---|---|---|---|---|---|---|
| casual | 2.0 | 480 s | 240 s | 2640 s | 7440 s | 12240 s | [v160.7] |
| easy | 1.5 | 360 s | 180 s | 1980 s | 5580 s | 9180 s | [v160.7] |
| normal | 1.0 | 240 s | 120 s | 1320 s（22 min） | 3720 s（62 min） | 6120 s | [v160.7] |
| hard | 0.8 | 192 s | 96 s | 1056 s | 2976 s | 4896 s | [v160.7] |
| eradication | 0.6 | 144 s | 72 s | 792 s（13 min） | 2232 s（37 min） | 3672 s | [v160.7] |

表中时刻全部由 T(N) 代入 `waveSpacing=7200`、`initialWaveSpacing=0`、`waveTimeMultiplier` 算出（waveSpacing/initialWaveSpacing/waveTimeMultiplier 均为 [verified v160.7] 反射值，见 DATA.FORMULA.011 与 00-data/constants_rules_difficulty_drill_heat.json）。

| 常数 | 值 | 来源 |
|---|---|---|
| rules.waveSpacing | 7200 tick = 120 s | Rules.java:151；[verified v160.7] |
| rules.initialWaveSpacing | 0 tick | Rules.java:153；[verified v160.7] |
| rules.waveTimer | true | Rules.java:31；[verified v160.7] |
| rules.winWave | 0（无限制） | Rules.java:155；[verified v160.7] |
| rules.waitEnemies | false | Rules.java:47；[verified v160.7] |
| state.wavetime | float，单位 tick | GameState.java:19 |

## 源码锚点

- Rules.java:151 `waveSpacing = 2 * Time.toMinutes`，反射默认值 7200 tick = 120 s [verified v160.7]。
- Logic.java:272 首波宽限 × waveTimeMultiplier；:322 每波重置。
- Logic.java:585-591 倒计时与触发；:617 等待清场判定；:315-325 skipWave/runWave。
- Logic.java:327-345 战役没有 wins 状态，只剩「核心全灭」判定（胜负见 CAMP.VICTORY.001）。
- LExecutor.java:1774,1778 逻辑规则的单位换算（秒→tick），:1779-1780 格→世界单位 [src: LExecutor.java:1774-1780]。

## 实测与反例

**反例 1：把 waveSpacing 当秒。** 直接写 `rules.waveSpacing = 120` 会变成 120 tick = 2 s 一波 [src: Rules.java:151]；要 120 s 必须写 7200。用逻辑规则 `set waveSpacing = 120` 才是 120 s（内部 ×60）。

**反例 2：以为 waveTimer=false 就没有波。** 关掉的只是自动倒计时；`skipWave()` 或逻辑 `set currentWaveTime = 0` 仍会立刻推波。

**反例 3：以为首波也是 120 s。** 首波固定 2×waveSpacing（normal 240 s、eradication 144 s）[src: Logic.java:272]——这是难度最直观的体感差异来源。

**反例 4：以为「等敌人清空」是默认行为。** 默认 `waitEnemies=false`，敌人没死光也照常来下一波。

**可复算**：normal、`waveTimer` 打开、不跳波 → 第 30 波落在 240 + 29×120 = 3720 s = 62 min；同图改 eradication 则是 144 + 29×72 = 2232 s = 37.2 min（代入 T(N) 即得，常数见上表 [v160.7]）。

## 常见误解

- 「波号是时间的函数」→ 只有在不跳波、不过早触发时成立；`state.wave` 与 wavetime 是两个独立可写状态。
- 「waveSpacing 单位是秒」→ 是 tick（60 tick = 1 s）[src: Logic.java:585-591]。
- 「难度只改波次间隔」→ 间隔只是三元组里的第三项，改血量/数量见 CAMP.DIFFICULTY.001。
- 「战役图靠 winWave 获胜」→ `winWave` 只在非战役地图生效；战役靠核心全灭/据点占领 [Logic.java:328-329,343]。

## 相关

- [[COMBAT.WAVE.001]] 波次的战斗侧视角（生成点、冲击波、AI 目标选择）
- [[CAMP.DIFFICULTY.001]] 难度三元组如何同时改血量/数量/间隔
- [[CAMP.SPAWN.001]] 每个刷怪组刷多少、带多少护盾
- DATA.FORMULA.011 波次计时公式（含代数与代入示例）
