---
id: CAMP.WINLOSE.001
title: 胜负与游戏结束——三种模式下到底什么才算赢
domain: camp
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src: Mindustry-Source/core/src/mindustry/core/Logic.java:327-374,509; game/Team.java:106-114; game/Teams.java:450-461; game/Rules.java:55; world/blocks/storage/CoreBlock.java:659-680; logic/LogicRule.java:16
data: [00-data/rules.json#records]
depends: [CAMP.RULES.001, CAMP.WAVES.001]
tags: [胜负, gameOver, sectorCapture, attackMode, winWave, canGameOver]
tokens: 863
---

## 一句话

胜负只由 `Logic.checkGameState()` 每 tick 判定一次（`Logic.java:327-374`），**campaign 没有胜利状态**：输 = 玩家核心全灭（`GameOverEvent(waveTeam)`），赢 = `Call.sectorCapture()` 占领星区；非 campaign 才有真正的 `GameOverEvent(winTeam)`。整个判定还受 `rules.canGameOver` 与 `isEditor()/isInvalidMap()` 三个闸门控制（`Logic.java:509`）。

## 规则/公式

### 1. 判定入口（先过闸门再判）

```
runStateCheck = !net.client() && !world.isInvalidMap() && !state.isEditor() && rules.canGameOver   [Logic.java:509]
```

- **`canGameOver = false` ⇒ 永远不判输赢**（核心全灭也不结束）。这是沙盒/演示图最常用的开关，也是逻辑 `set rule canGameOver false` 能达到的效果（`LogicRule.java:16` 白名单里有它）。
- 客户端（联机非主机）不跑判定，只接收服务端广播。

### 2. campaign 分支（`state.isCampaign()`，`Logic.java:329-354`）

```
输：playerCores().size == 0 && !gameOver  → gameOver = true; Event(GameOverEvent(waveTeam))   [:331-334]
自动停波：rules.waves && (spawner.countSpawns() + 敌军核心数 <= 0) → rules.waves = false      [:337-340]
赢：rules.waves && enemies == 0 && winWave > 0 && wave >= winWave && !spawner.isSpawning()
    或 rules.attackMode && !waveTeam.isAlive()                                            [:343-344]
  → 若 sector.preset.attackAfterWaves 且当前不是 attackMode：切成 attackMode、关 waves、重载规则
  → 否则 Call.sectorCapture()                                                             [:346-353]
```

- `playerCores()` 只统计玩家队（`defaultTeam`）的核心；盟友核心丢失不影响你，但你自己核心全丢即判负。
- `Team.isAlive()` = `TeamData.hasCore()` = `cores.size > 0`（`Teams.java:450-457`）——**只看核心，不看单位/建筑**。所以 attackMode 下打赢就是把对方核心全拆掉，拆光单位不算。
- `waves` 被自动关掉（第 337 行）后，第 343 行的波次胜利分支就永远进不去 ⇒ 想靠守波获胜的图必须保留刷新点或敌军核心，或显式设 `winWave` 并关波。
- `attackAfterWaves = true` 的星区（多数歼灭型关卡）：守满波次后地图**不结束**，而是切 `attackMode` 让你反推敌方核心，再走 `!waveTeam.isAlive()` 的胜利分支。

### 3. 非 campaign 分支（`Logic.java:356-372`）

| 条件 | 结果 |
|---|---|
| `!attackMode && playerCores().size == 0` | 输：`GameOverEvent(waveTeam)` |
| `attackMode` | 存活队数 `countAlive <= 1`，或（非 pvp 且 `defaultTeam.core() == null`）⇒ 赢：`GameOverEvent(存活队)`，无存活队则记 `derelict` |
| `!gameOver && waves && enemies == 0 && winWave > 0 && wave >= winWave && !isSpawning()` | 赢：`GameOverEvent(defaultTeam)` |
| 其余 | 继续游戏（`winWave = 0` 时没有波次胜利） |

`countAlive` 统计 `t.isAlive() && t.team != Team.derelict` 的队伍数（`Logic.java:361`）——derelict 永远不算活队，所以废墟不阻止你获胜。

### 4. 核心消失即判负（不是建筑被拆）

`CoreBlock` 被摧毁后有两种走向（`CoreBlock.java:659-680`）：

- `rules.coreCapture = true` 时，核心方块**原地转换成攻击方阵营的核心**（`tile.setBlock(block, lastDamage)`），该方块仍算核心；
- 关闭时核心真正消失，`cores.size` 减 1；减到 0 的下一个 tick 由 `checkGameState` 判负。

这也解释了最后一击拆掉核心却没判负的错觉：`coreCapture` 让敌方在你的核心位置放了它的核心，我方 `playerCores()` 视其为敌方核心 ⇒ 我方为 0 ⇒ 下一 tick 仍然判负。

## 数值

| 量 | 值/条件 | 来源 |
|---|---|---|
| 判定频率 | 每 tick 一次（`update()` 内 `runStateCheck` 时） | Logic.java:509 |
| 输的阈值 | `playerCores().size == 0` | Logic.java:331,356 |
| campaign 胜利波 | `winWave > 0 && wave >= winWave` 且 `enemies == 0` 且 `!isSpawning()` | Logic.java:343 |
| attackMode 胜利 | 存活队（排除 derelict）≤ 1 | Logic.java:361-363 |
| 自动停波条件 | `spawner.countSpawns() + cores(waveTeam).size <= 0` | Logic.java:337 |
| `canGameOver` 默认 | true | 00-data/rules.json（Rules.java:55） |
| `winWave` 默认 | 0（无波次胜利） | 00-data/rules.json（Rules.java:155） |
| `coreCapture` 默认 | false | 00-data/rules.json |
| `attackMode` 默认 | false | 00-data/rules.json |

## 源码锚点

- `Logic.java:327-374` `checkGameState()` 全部分支（campaign / 非 campaign）。
- `Logic.java:337-340` 没有刷新点且敌军核心清零 ⇒ `rules.waves = false`（连带关掉波次胜利）。
- `Logic.java:346-353` `attackAfterWaves` 的切换与 `Call.sectorCapture()`。
- `Logic.java:509` 判定闸门（`canGameOver` / 编辑器 / 无效地图 / 客户端）。
- `Teams.java:450-457` `TeamData.hasCore()/isAlive()`：只看 `cores.size`。
- `Team.java:106-114` `isAlive()` 与 `active()`、`isAI()` 的区别。
- `CoreBlock.java:659-680` 核心被摧毁：`coreCapture` 转阵营或真正消失。
- `LogicRule.java:16` 逻辑可写 `canGameOver`。

## 实测与反例

**反例 1：以为拆光敌方单位就赢。** `attackMode` 下胜利条件是 `!waveTeam.isAlive()`，而 `isAlive()` 只查核心（`Teams.java:455`）。敌方核心还在、单位全死，游戏继续；反之核心一拆，场上还有一堆敌人也会立刻判定胜利。

**反例 2：以为 campaign 守满 `winWave` 就通关。** 战役分支先看 `attackAfterWaves`：多数歼灭星区会切成 `attackMode` 继续打，不弹胜利；不设 `attackAfterWaves` 的图才 `sectorCapture()`。另外若地图没有刷新点、敌军核心被清空，`waves` 会被自动置 false（第 337-340 行），波次胜利分支直接失效。

**反例 3：以为 `canGameOver=false` 只是关掉结算界面。** 它把判定本身关掉（`Logic.java:509`）：核心全灭也不结束，敌人继续刷，玩家还能继续操作。适合做展示图，但会让失败变成永远无法结束的局面。

**反例 4：以为核心被拆后队伍立刻死。** 只有 `coreCapture=false` 时核心才真正消失；开着 `coreCapture` 时核心原地变成对方核心，你的 `playerCores()` 直接清零 —— 两种路径都在下一 tick 判负，但地图上看起来完全不同（一个留坑，一个换色）。

## 常见误解

1. **campaign 胜利 = 打光敌人**：campaign 没有 win 事件，只有 `sectorCapture()`；打光敌人只是触发它的一种条件。
2. **`winWave` 到了就赢**：还要 `waves == true`、`enemies == 0`、`!spawner.isSpawning()` 同时成立；`winWave = 0` 表示永不胜。
3. **`teams.playerCores()` 包括盟友核心**：只统计 `defaultTeam`（玩家队）；盟友丢核心不影响你的判负。
4. **derelict 会阻止胜利**：`countAlive` 明确排除 `Team.derelict`（`Logic.java:361`）。
5. **逻辑处理器不能影响胜负**：可以用 `set rule canGameOver false` 关判定，也可以 `setblock` 摧毁核心制造失败 —— 但没有任何指令能直接触发 `GameOverEvent`。

## 相关

- [[CAMP.RULES.001]] `canGameOver` / `winWave` / `attackMode` / `coreCapture` 的默认值与生效顺序
- [[CAMP.WAVES.001]] 波次节奏（`winWave` 依赖的 `wave` 计数）
- [[CAMP.SPAWN.001]] 刷新点与 `countSpawns()`（第 337 行自动停波的判定源）
- [[CAMP.SECTOR.001]] 星区占领与 `sectorCapture()` 的后果