---
id: UNIT.AI.001
title: 单位 AI——控制器、目标选择、命令与姿态、寻路代价
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/units/AIController.java:23-40,114-210"
  - "Mindustry-Source/core/src/mindustry/entities/Units.java:284-337"
  - "Mindustry-Source/core/src/mindustry/ai/UnitCommand.java:19-40"
  - "Mindustry-Source/core/src/mindustry/ai/UnitStance.java:18-40"
  - "Mindustry-Source/core/src/mindustry/ai/types/CommandAI.java:25-111,191,514-549"
  - "Mindustry-Source/core/src/mindustry/ai/Pathfinder.java:45-50,615,703"
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:89-129"
data: [00-data/units.json]
depends: [UNIT.MOVE.001]
tags: [AI, 目标选择, targetPriority, 寻路, 命令, 姿态, ucontrol]
tokens: 813
---

## 一句话

每个单位挂一个 `AIController`（GroundAI / FlyingAI / CommandAI / BuilderAI / MinerAI…），每 tick 跑 **updateTargeting → updateMovement → updateWeapons** 三段；选目标走 `Units.closestEnemy/bestEnemy`，优先级由 `UnitType.targetPriority`（默认 0，辅助单位为负）覆盖距离，寻路代价由类决定（ground 0 / legs 1 / naval 2 / hover 5）。

## 规则 / 公式

### 1. 控制器基类（AIController）

```
updateUnit():
    updateVisuals()
    updateTargeting()     // 选目标
    updateMovement()      // 移动/寻路
    updateWeapons()       // 开火
```

- `timer` 是 4 槽 Interval（`timerTarget/timerTarget2/3/4`），启动时随机错开 `random(40f)` / `random(60f)`，避免全图单位同一 tick 重算目标。
- `retarget()` 返回 true 才重新找目标；`targetInvalidated()` 会把 `timerTarget` 重置为 -1 → **下一 tick 立刻重选**。
- `updateWeapons`：`target = findMainTarget(unit.x, unit.y, unit.range(), unit.type.targetAir, unit.type.targetGround)`，`targetAir/targetGround` 决定能不能打空/打地。

### 2. 目标选择（Units.closestEnemy / bestEnemy）

```
过滤：dead / !predicate / team == derelict / !targetable(team) / inFogTo(team) → 跳过
距离：dst2 = e.dst2(x,y) - e.hitSize²            // 大单位"中心更近"
判据：dst2 < range²
      && (result == null || dst2 < cdist || e.type.targetPriority > cpriority)
      && e.type.targetPriority >= cpriority
```

**注意两点**：优先级的比较是 `>` 而不是 `>=`（首次出现 `cpriority = -99999`），且 `>= cpriority` 保证"低优先级不会覆盖高优先级"。

### 3. 命令（UnitCommand，10 种）

`moveCommand, repairCommand, rebuildCommand, assistCommand, mineCommand, enterPayloadCommand, loadUnitsCommand, loadBlocksCommand, unloadPayloadCommand, loopPayload`

每个命令自带：`controller`（切换 AI）、`switchToMove`（点了位置就转回 move）、`drawTarget`、`resetTarget`、`snapToBuilding`、`exactArrival`、`keybind`。

### 4. 姿态（UnitStance，8 种）

`stop, holdFire, pursueTarget, patrol, ram, boost, holdPosition, mineAuto`

- 姿态之间用 `incompatibleStanceBits` 位图互斥（`Bits(32)`），`toggle = true` 可反复开关。
- 命令也可以附带 `extraStances`（忽略互斥）。

### 5. CommandAI（RTS 控制时的 AI）

- `targetPos / attackTarget / group / command` 五个状态字段；
- `retarget()`：**有显式攻击目标时重算更快**（缩短 targetInterval）；
- `isLogicControllable()` 决定 `ucontrol` 能否接管（逻辑控制单位走 `LogicAI`）。

### 6. 寻路（Pathfinder）

```
PathCost: costGround = 0, costLegs = 1, costNaval = 2, costHover = 5      // Pathfinder.java:45-50
```

- 每个 team 预计算一个 cost field（`getField(team, costType, fieldCore)`），单位只是**读场取下一步**；
- `costNaval` 的场把 "amount >= 6000" 视为不可通行（L703）——即海军路径场的实心块判定阈值；
- 遇到危险区（`dangerous()`）会绕行（L434）。

## 数值

### AI 类与用途（ai/types/ 下 16 个文件）

| AI | 用途 | 备注 |
|---|---|---|
| GroundAI | 地面默认 | `findTarget` 默认实现 |
| FlyingAI | 飞行默认 | 覆写 `findTarget/findMainTarget`（L34/L42） |
| CommandAI | 玩家 RTS 命令 | 支持 group/command/stance |
| BuilderAI | 建造/协助 | 受 `buildSpeed` 限制 |
| MinerAI | 采矿 | `mineRange = 70`（UnitType.java:94） |
| RepairAI | 修理 | 配合 repairSpeed |
| SuicideAI | 撞人（crawler 系） | `target()` 覆写（L101） |
| HugAI | 贴脸（toxopid 系） | — |
| BoostAI | 自动 boost | 需 `canBoost` |
| DefenderAI | 驻守 | `findTarget(..., true, true)`（L28） |
| FlyingFollowAI | 跟随 | 编队飞行 |
| CargoAI | 货运单位 | 配合 UnitCargoLoader |
| LogicAI | 逻辑控制（ucontrol） | `isLogicControllable` |
| MissileAI | 导弹 | 配合 MissileBulletType |
| PrebuildAI | 预建造 | 不占单位上限的"预告"单位 |
| AssemblerAI | 组装厂无人机 | `dronesCreated = 4` |

### 关键常量

| 量 | 值 | 来源 |
|---|---|---|
| `targetPriority` 默认 | **0** | UnitType.java:129 |
| 辅助/建造单位优先级 | **-2** | UnitTypes.java:4348/4413/4493 |
| `timerTarget` 初始延迟 | `random(40)` tick ≈ 0~0.67 s | AIController.java:40 |
| `timerTarget2` 初始延迟 | `random(60)` tick = 0~1 s | AIController.java:41 |
| `UnitType.range` 默认 | **-1**（由武器推导） | UnitType.java:90 |
| `mineRange` | **70** px | UnitType.java:94 |
| `buildRange` | `Vars.buildingRange` | UnitType.java:96 |
| `aimDst` | -1（自动） | UnitType.java:122-123 |
| costGround / costLegs / costNaval / costHover | 0 / 1 / 2 / 5 | Pathfinder.java:45-50 |
| UnitCommand 数量 | **10** | UnitCommand.java:20 |
| UnitStance 数量 | **8** | UnitStance.java:19 |

## 源码锚点

- [src: AIController.java:26] `protected Interval timer = new Interval(4)`。
- [src: AIController.java:114-119] `updateTargeting()` 入口。
- [src: AIController.java:167-170] `targetInvalidated()` → `timer.reset(timerTarget, -1f)`。
- [src: AIController.java:172-190] `updateWeapons()`：`retarget()` → `findMainTarget(... targetAir, targetGround)`。
- [src: Units.java:295-315] `closestEnemy` 的距离与优先级判据（含 `hitSize` 修正）。
- [src: Units.java:317-337] `bestEnemy` 用 `Sortf` 成本函数替代距离。
- [src: Units.java:304] 过滤 `e.team == Team.derelict`、`!e.targetable(team)`、`e.inFogTo(team)`。
- [src: CommandAI.java:25-33] `targetPos/attackTarget/group/groupIndex/readAttackTarget`。
- [src: CommandAI.java:544-549] `retarget()` 显式目标时更快。
- [src: Pathfinder.java:45-50] 四种 cost 常量；`:703` naval 场 `amount >= 6000` 不可通行。

## 实测与反例

**反例 1：以为"最近的目标"一定被打。**
`targetPriority` 更高的单位会**抢走**目标，哪怕更远。负优先级（建造单位）会被放到最后；但如果场上只有它，仍会被打（优先级只影响排序，不产生免疫）。

**反例 2：以为单位每 tick 都重算目标。**
`retarget()` 由 Interval 控制，默认几十 tick 一次（初始 `random(40)`）。所以"刚打你的炮塔"可能 1 秒后才被反击——`targetInvalidated` 是唯一的即时重选入口。

**反例 3：以为海军和地面用同一张路网。**
`costNaval = 2`、`costHover = 5` 是**不同的场**，海军在水上找不到陆地路径，反之亦然。给海军下 `move` 到陆地会原地打转。

**反例 4：以为 `UnitStance.holdFire` 能阻止炮塔开火。**
姿态只管**单位**；`holdFire` 是 AI 层不主动开火，不改 `Weapon` 数值。

**可复算**：一个 `targetPriority = -2` 的 mono 与 `targetPriority = 0` 的 dagger 同在 100 px 内，turret 的 `findMainTarget` 先取 dagger。若把 dagger 移出 `range`，mono 才会成为目标——因为 `dst2 < range²` 的过滤在前，优先级只在候选集内排序。

## 常见误解

- ❌ "`ucontrol` 会替换 AI"。→ 只是接管输入，单位仍有 `LogicAI` 包装层。
- ❌ "`ram` 姿态 = 撞击伤害"。→ `ram` 是接近行为，撞击伤害来自 `crashDamageMultiplier`。
- ❌ "飞行单位不受寻路限制"。→ 飞行有独立的 `costHover` 场，仍会绕危险区。
- ❌ "`targetPriority` 越大越先被打"。→ 数值大 = 更**优先**被选中，但仍需在射程内。
- ❌ "AI 状态机会存档"。→ AI 是运行时对象，读档后靠 `afterRead` 重建（AIController.java:77）。

## 相关

- [[UNIT.MOVE.001]] 移动速度与地形如何影响 AI 选路
- [[UNIT.PRODUCE.001]] 工厂给新单位的默认命令
- [[UNIT.PROGRESSION.001]] ubind/ucontrol 与逻辑控制
- [[COMBAT.WAVE.001]] 波次单位用的是哪套 AI
