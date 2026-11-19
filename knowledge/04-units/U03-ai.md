---
id: UNIT.AI.001
title: Unit AI — controllers, target selection, commands and stances, pathing cost
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
tags: [AI, targeting, targetPriority, pathfinding, command, stance, ucontrol]
tokens: 813
---

## In one line

Every unit carries one `AIController` (GroundAI / FlyingAI / CommandAI / BuilderAI / MinerAI…), and each tick it runs **updateTargeting → updateMovement → updateWeapons**; targets come from `Units.closestEnemy/bestEnemy`, where `UnitType.targetPriority` (0 by default, negative for support units) outranks distance, and pathing cost is decided by the class (ground 0 / legs 1 / naval 2 / hover 5).

## Rules / formulas

### 1. The controller base class (AIController)

```
updateUnit():
    updateVisuals()
    updateTargeting()     // 选目标
    updateMovement()      // 移动/寻路
    updateWeapons()       // 开火
```

- `timer` is a 4-slot Interval (`timerTarget/timerTarget2/3/4`), staggered at startup with `random(40f)` / `random(60f)` so that units map-wide do not all retarget on the same tick.
- Only a true `retarget()` re-searches; `targetInvalidated()` resets `timerTarget` to -1 → **a new target is picked on the very next tick**.
- `updateWeapons`: `target = findMainTarget(unit.x, unit.y, unit.range(), unit.type.targetAir, unit.type.targetGround)`; `targetAir/targetGround` decide whether it can hit air/ground.

### 2. Target selection (Units.closestEnemy / bestEnemy)

```
过滤：dead / !predicate / team == derelict / !targetable(team) / inFogTo(team) → 跳过
距离：dst2 = e.dst2(x,y) - e.hitSize²            // 大单位"中心更近"
判据：dst2 < range²
      && (result == null || dst2 < cdist || e.type.targetPriority > cpriority)
      && e.type.targetPriority >= cpriority
```

**Two things to note**: the priority comparison is `>` rather than `>=` (the first candidate starts with `cpriority = -99999`), and `>= cpriority` guarantees that a lower priority never overrides a higher one.

### 3. Commands (UnitCommand, 10 of them)

`moveCommand, repairCommand, rebuildCommand, assistCommand, mineCommand, enterPayloadCommand, loadUnitsCommand, loadBlocksCommand, unloadPayloadCommand, loopPayload`

Each command carries: `controller` (which AI to switch to), `switchToMove` (click a position and it reverts to move), `drawTarget`, `resetTarget`, `snapToBuilding`, `exactArrival`, `keybind`.

### 4. Stances (UnitStance, 8 of them)

`stop, holdFire, pursueTarget, patrol, ram, boost, holdPosition, mineAuto`

- Stances are mutually exclusive through the `incompatibleStanceBits` bitmap (`Bits(32)`); `toggle = true` makes one repeatable.
- A command may also ship `extraStances` (which ignore the exclusion bits).

### 5. CommandAI (the AI used under RTS control)

- Five state fields: `targetPos / attackTarget / group / command`;
- `retarget()`: **recalculates sooner when there is an explicit attack target** (shorter targetInterval);
- `isLogicControllable()` decides whether `ucontrol` can take over (logic-controlled units run `LogicAI`).

### 6. Pathfinding (Pathfinder)

```
PathCost: costGround = 0, costLegs = 1, costNaval = 2, costHover = 5      // Pathfinder.java:45-50
```

- Each team precomputes a cost field (`getField(team, costType, fieldCore)`); units merely **read the field for their next step**;
- in the `costNaval` field, "amount >= 6000" counts as impassable (L703) — that is the solid-block threshold for the naval path field;
- dangerous areas (`dangerous()`) are routed around (L434).

## Numbers

### AI classes and their uses (16 files under ai/types/)

| AI | Use | Notes |
|---|---|---|
| GroundAI | ground default | `findTarget` default implementation |
| FlyingAI | flying default | overrides `findTarget/findMainTarget` (L34/L42) |
| CommandAI | player RTS commands | supports group/command/stance |
| BuilderAI | build/assist | bounded by `buildSpeed` |
| MinerAI | mining | `mineRange = 70` (UnitType.java:94) |
| RepairAI | repair | paired with repairSpeed |
| SuicideAI | ramming (crawler line) | overrides `target()` (L101) |
| HugAI | close hugging (toxopid line) | — |
| BoostAI | automatic boost | needs `canBoost` |
| DefenderAI | garrison | `findTarget(..., true, true)` (L28) |
| FlyingFollowAI | follow | formation flight |
| CargoAI | cargo units | pairs with UnitCargoLoader |
| LogicAI | logic control (ucontrol) | `isLogicControllable` |
| MissileAI | missiles | pairs with MissileBulletType |
| PrebuildAI | pre-building | a "preview" unit that does not count against the cap |
| AssemblerAI | assembler drones | `dronesCreated = 4` |

### Key constants

| Quantity | Value | Source |
|---|---|---|
| `targetPriority` default | **0** | UnitType.java:129 |
| support/build unit priority | **-2** | UnitTypes.java:4348/4413/4493 |
| `timerTarget` initial delay | `random(40)` ticks ≈ 0~0.67 s | AIController.java:40 |
| `timerTarget2` initial delay | `random(60)` ticks = 0~1 s | AIController.java:41 |
| `UnitType.range` default | **-1** (derived from weapons) | UnitType.java:90 |
| `mineRange` | **70** px | UnitType.java:94 |
| `buildRange` | `Vars.buildingRange` | UnitType.java:96 |
| `aimDst` | -1 (automatic) | UnitType.java:122-123 |
| costGround / costLegs / costNaval / costHover | 0 / 1 / 2 / 5 | Pathfinder.java:45-50 |
| UnitCommand count | **10** | UnitCommand.java:20 |
| UnitStance count | **8** | UnitStance.java:19 |

## Source anchors

- [src: AIController.java:26] `protected Interval timer = new Interval(4)`.
- [src: AIController.java:114-119] the `updateTargeting()` entry point.
- [src: AIController.java:167-170] `targetInvalidated()` → `timer.reset(timerTarget, -1f)`.
- [src: AIController.java:172-190] `updateWeapons()`: `retarget()` → `findMainTarget(... targetAir, targetGround)`.
- [src: Units.java:295-315] `closestEnemy`'s distance and priority test (including the `hitSize` correction).
- [src: Units.java:317-337] `bestEnemy` replaces distance with a `Sortf` cost function.
- [src: Units.java:304] filters `e.team == Team.derelict`, `!e.targetable(team)`, `e.inFogTo(team)`.
- [src: CommandAI.java:25-33] `targetPos/attackTarget/group/groupIndex/readAttackTarget`.
- [src: CommandAI.java:544-549] `retarget()` is faster with an explicit target.
- [src: Pathfinder.java:45-50] the four cost constants; `:703` in the naval field `amount >= 6000` is impassable.

## Tests and counterexamples

**Counterexample 1: assuming "the nearest target" always gets shot.**
A unit with a higher `targetPriority` **steals** the target even from farther away. Negative-priority units (builders) sort last, but if they are the only thing on the field they still get shot (priority only reorders candidates, it grants no immunity).

**Counterexample 2: assuming units recalculate their target every tick.**
`retarget()` is driven by an Interval, by default once every few dozen ticks (starting at `random(40)`). So the turret that just shot you may not be answered for a second — `targetInvalidated` is the only immediate re-selection entry point.

**Counterexample 3: assuming naval and ground units share one path network.**
`costNaval = 2` and `costHover = 5` are **different fields**; a naval unit will not find a land route over water, and vice versa. Ordering a naval unit to `move` onto land leaves it circling in place.

**Counterexample 4: assuming `UnitStance.holdFire` stops turrets from firing.**
Stances only govern **units**; `holdFire` means the AI does not open fire on its own, it does not touch `Weapon` numbers.

**Recomputable**: a mono with `targetPriority = -2` and a dagger with `targetPriority = 0` both inside 100 px — the turret's `findMainTarget` picks the dagger first. Move the dagger out of `range` and the mono becomes the target — because the `dst2 < range²` filter runs first and priority only sorts inside the candidate set.

## Common misconceptions

- ❌ "`ucontrol` replaces the AI." → it only takes over input; the unit still has a `LogicAI` wrapper.
- ❌ "`ram` stance = collision damage." → `ram` is an approach behaviour; collision damage comes from `crashDamageMultiplier`.
- ❌ "flying units ignore pathfinding." → flying has its own `costHover` field and still routes around danger.
- ❌ "a bigger `targetPriority` is shot sooner." → a bigger number = more **preferred** as a target, but it still has to be in range.
- ❌ "the AI state machine is saved." → the AI is a runtime object, rebuilt after a load through `afterRead` (AIController.java:77).

## Related

- [[UNIT.MOVE.001]] how speed and terrain shape AI route choice
- [[UNIT.PRODUCE.001]] the default commands factories give new units
- [[UNIT.PROGRESSION.001]] ubind/ucontrol and logic control
- [[COMBAT.WAVE.001]] which AI the wave units run
