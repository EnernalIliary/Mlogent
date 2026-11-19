---
id: CAMP.WINLOSE.001
title: Win, loss and game over — what actually counts as winning in each of the three modes
domain: camp
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src: Mindustry-Source/core/src/mindustry/core/Logic.java:327-374,509; game/Team.java:106-114; game/Teams.java:450-461; game/Rules.java:55; world/blocks/storage/CoreBlock.java:659-680; logic/LogicRule.java:16
data: [00-data/rules.json#records]
depends: [CAMP.RULES.001, CAMP.WAVES.001]
tags: [win/loss, gameOver, sectorCapture, attackMode, winWave, canGameOver]
tokens: 863
---

## In one line

Win/loss is decided by `Logic.checkGameState()` once per tick (`Logic.java:327-374`), and **campaign has no victory state**: a loss is every player core gone (`GameOverEvent(waveTeam)`), a win is `Call.sectorCapture()` capturing the sector; only non-campaign ever gets a real `GameOverEvent(winTeam)`. The whole check sits behind three gates — `rules.canGameOver`, `isEditor()` and `isInvalidMap()` (`Logic.java:509`).

## Rules / formulas

### 1. The entry point (gates first, then the verdict)

```
runStateCheck = !net.client() && !world.isInvalidMap() && !state.isEditor() && rules.canGameOver   [Logic.java:509]
```

- **`canGameOver = false` ⇒ win/loss is never evaluated** (even losing every core does not end the game). This is the switch sandbox and demo maps use most, and it is also what the logic `set rule canGameOver false` achieves (`LogicRule.java:16` has it on the whitelist).
- Clients (non-host in multiplayer) never run the check; they only receive the server's broadcast.

### 2. The campaign branch (`state.isCampaign()`, `Logic.java:329-354`)

```
输：playerCores().size == 0 && !gameOver  → gameOver = true; Event(GameOverEvent(waveTeam))   [:331-334]
自动停波：rules.waves && (spawner.countSpawns() + 敌军核心数 <= 0) → rules.waves = false      [:337-340]
赢：rules.waves && enemies == 0 && winWave > 0 && wave >= winWave && !spawner.isSpawning()
    或 rules.attackMode && !waveTeam.isAlive()                                            [:343-344]
  → 若 sector.preset.attackAfterWaves 且当前不是 attackMode：切成 attackMode、关 waves、重载规则
  → 否则 Call.sectorCapture()                                                             [:346-353]
```

- `playerCores()` counts only the cores of the player team (`defaultTeam`); losing an ally's core does not hurt you, but losing all of your own is a loss.
- `Team.isAlive()` = `TeamData.hasCore()` = `cores.size > 0` (`Teams.java:450-457`) — **cores only, never units or buildings**. So winning under attackMode means dismantling every enemy core; killing all their units does not count.
- Once `waves` is switched off automatically (line 337), the wave-victory branch on line 343 can never be entered again ⇒ a map you want to win by holding waves must keep either spawn points or enemy cores, or explicitly set `winWave` and turn waves off.
- Sectors with `attackAfterWaves = true` (most annihilation levels): after holding the waves the map **does not end**; it switches to `attackMode` so you can push back against the enemy cores and then take the `!waveTeam.isAlive()` victory branch.

### 3. The non-campaign branch (`Logic.java:356-372`)

| Condition | Result |
|---|---|
| `!attackMode && playerCores().size == 0` | Loss: `GameOverEvent(waveTeam)` |
| `attackMode` | living-team count `countAlive <= 1`, or (non-pvp and `defaultTeam.core() == null`) ⇒ win: `GameOverEvent(living team)`; with no living team it records `derelict` |
| `!gameOver && waves && enemies == 0 && winWave > 0 && wave >= winWave && !isSpawning()` | Win: `GameOverEvent(defaultTeam)` |
| anything else | keep playing (with `winWave = 0` there is no wave victory) |

`countAlive` counts teams for which `t.isAlive() && t.team != Team.derelict` (`Logic.java:361`) — derelict never counts as living, so ruins never stop you from winning.

### 4. Losing the core is what ends the game (not a building being destroyed)

Once a `CoreBlock` is destroyed there are two paths (`CoreBlock.java:659-680`):

- with `rules.coreCapture = true` the core block **is converted in place into a core of the attacker's team** (`tile.setBlock(block, lastDamage)`), and that tile still counts as a core;
- with it off, the core really disappears and `cores.size` drops by 1; when it hits 0, the next tick's `checkGameState` rules a loss.

That also explains the illusion of destroying the core with the last hit but not losing: `coreCapture` puts the enemy's core where yours stood, `playerCores()` no longer counts it as yours ⇒ yours is 0 ⇒ you still lose on the next tick.

## Numbers

| Quantity | Value/condition | Source |
|---|---|---|
| Check frequency | once per tick (when `runStateCheck` runs inside `update()`) | Logic.java:509 |
| Loss threshold | `playerCores().size == 0` | Logic.java:331,356 |
| campaign victory wave | `winWave > 0 && wave >= winWave` and `enemies == 0` and `!isSpawning()` | Logic.java:343 |
| attackMode victory | living teams (derelict excluded) ≤ 1 | Logic.java:361-363 |
| automatic wave stop | `spawner.countSpawns() + cores(waveTeam).size <= 0` | Logic.java:337 |
| `canGameOver` default | true | 00-data/rules.json (Rules.java:55) |
| `winWave` default | 0 (no wave victory) | 00-data/rules.json (Rules.java:155) |
| `coreCapture` default | false | 00-data/rules.json |
| `attackMode` default | false | 00-data/rules.json |

## Source anchors

- `Logic.java:327-374` the whole `checkGameState()` (campaign / non-campaign branches).
- `Logic.java:337-340` no spawn points and enemy cores cleared ⇒ `rules.waves = false` (which also kills wave victory).
- `Logic.java:346-353` the `attackAfterWaves` switch and `Call.sectorCapture()`.
- `Logic.java:509` the gates (`canGameOver` / editor / invalid map / client).
- `Teams.java:450-457` `TeamData.hasCore()/isAlive()`: it only looks at `cores.size`.
- `Team.java:106-114` how `isAlive()` differs from `active()` and `isAI()`.
- `CoreBlock.java:659-680` a destroyed core: `coreCapture` flips the team, otherwise it really disappears.
- `LogicRule.java:16` logic can write `canGameOver`.

## Tests and counterexamples

**Counterexample 1: assuming wiping out the enemy's units wins.** Under `attackMode` the victory condition is `!waveTeam.isAlive()`, and `isAlive()` looks only at cores (`Teams.java:455`). Enemy cores still standing with every unit dead means the game continues; conversely, one core destroyed with a crowd of enemies left on the field immediately counts as a win.

**Counterexample 2: assuming campaign completes the moment you hold `winWave` waves.** The campaign branch checks `attackAfterWaves` first: most annihilation sectors switch to `attackMode` and keep going instead of showing a victory; only maps without `attackAfterWaves` call `sectorCapture()`. And if a map has no spawn points and the enemy cores are cleared, `waves` is switched to false automatically (lines 337-340), which disables the wave-victory branch outright.

**Counterexample 3: assuming `canGameOver=false` merely hides the results screen.** It switches off the check itself (`Logic.java:509`): losing every core does not end the game, enemies keep spawning and the player can keep acting. Fine for a showcase map, but it turns defeat into a state that can never end.

**Counterexample 4: assuming a team dies the instant its core is destroyed.** The core only truly disappears when `coreCapture=false`; with `coreCapture` on, the core turns into the enemy's core on the spot and your `playerCores()` drops straight to zero — both paths lose on the next tick, but they look completely different on the map (one leaves a hole, the other changes colour).

## Common misconceptions

1. **campaign victory = killing every enemy**: campaign has no win event, only `sectorCapture()`; wiping out the enemy is merely one condition that triggers it.
2. **Reaching `winWave` is enough**: `waves == true`, `enemies == 0` and `!spawner.isSpawning()` must hold too; `winWave = 0` means you can never win that way.
3. **`teams.playerCores()` includes ally cores**: it counts `defaultTeam` (the player team) only; an ally losing its core does not lose you the game.
4. **derelict blocks victory**: `countAlive` explicitly excludes `Team.derelict` (`Logic.java:361`).
5. **Logic processors cannot affect win/loss**: `set rule canGameOver false` disables the check, and `setblock` can destroy a core to cause a loss — but no instruction can trigger `GameOverEvent` directly.

## Related

- [[CAMP.RULES.001]] the defaults and order of effect of `canGameOver` / `winWave` / `attackMode` / `coreCapture`
- [[CAMP.WAVES.001]] wave rhythm (the `wave` counter that `winWave` depends on)
- [[CAMP.SPAWN.001]] spawn points and `countSpawns()` (the source of the automatic wave stop on line 337)
- [[CAMP.SECTOR.001]] sector capture and the consequences of `sectorCapture()`
