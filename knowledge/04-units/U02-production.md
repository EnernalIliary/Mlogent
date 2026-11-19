---
id: UNIT.PRODUCE.001
title: The unit production chain — factories, reconstructors, assemblers and the unit cap
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/world/blocks/units/UnitFactory.java:39,101,207-219,392-443"
  - "Mindustry-Source/core/src/mindustry/world/blocks/units/Reconstructor.java:36-41,168,334"
  - "Mindustry-Source/core/src/mindustry/world/blocks/units/UnitAssembler.java:45-52,278-281"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:6269-6581"
  - "Mindustry-Source/core/src/mindustry/entities/Units.java:114-131"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:75,83,157,290-295"
  - "Mindustry-Source/core/src/mindustry/entities/comp/BlockUnitComp.java / BlockIndexer.java:216,614"
  - "Mindustry-Source/core/src/mindustry/Vars.java:137"
data: [00-data/blocks.json, 00-data/units.json]
depends: [UNIT.MOVE.001]
tags: [factory, reconstructor, assembler, unit cap, unitCap, buildSpeed, payload]
tokens: 1193
---

## In one line

Vanilla builds units through **three pipelines**: factories (items + power → low-tier units, where `UnitPlan.time` is in **ticks**), reconstructors (feed an existing unit in, get a higher tier out, `constructTime` also in ticks), and assemblers (units and blocks as **raw material** for tier 4/5 leviathans); the cap comes from **summing each core's `unitCapModifier`**, with `rules.unitCap = 0` and `unitCapVariable = true` by default.

## Rules / formulas

### 1. Factories (UnitFactory)

```
progress += edelta() * Vars.state.rules.unitBuildSpeed(team)      // UnitFactory.java:403
if(progress >= plan.time) → 生成单位、consume()、progress %= 1
```

- `UnitPlan.unit` / `.time` / `.requirements` (UnitFactory.java:207-216).
- A unit's cost and build time are **not affected by factory tier**, only scaled by `rules.unitBuildSpeed(team)`:
  `unitBuildSpeed(team) = unitBuildSpeedMultiplier × teams.get(team).unitBuildSpeedMultiplier` (Rules.java:290-291, both default 1).
- Factory `itemCapacity = 10`, and the comment spells it out: "unit factories can't control their own capacity externally" (UnitFactory.java:101).
- Factories with `configurable = false` (tank/ship/mech-fabricator) have one plan and cannot switch.

### 2. Reconstructors (Reconstructor)

```
把低阶单位作为 payload 送入 → progress += edelta() → progress >= constructTime 时替换为高阶单位
fraction() = progress / constructTime                       // Reconstructor.java:168
stats: Stat.productionTime = constructTime / 60f 秒          // Reconstructor.java:90
```

A reconstructor has an `upgrades` table (`Seq<UnitType[]>`), **accepts only the low-tier units declared in it**, and the input unit disappears (it is consumed) — this is not parallel production.

### 3. Assemblers (UnitAssembler)

- The raw material is **payload** (`PayloadStack`: a unit or a block), not items;
- `areaSize = 11` (the default; Blocks raises it to 13): the square footprint shared by the assembler and its modules;
- `dronesCreated = 4`, `droneConstructTime = 240` ticks: four build drones assemble the unit step by step;
- each module tier (`UnitAssemblerModule`) adds capacity and parallelism; `basic-assembler-module` is the tier 1 module.

### 4. Unit cap

```
canCreate(type, team) = !type.useUnitCap
                     || (team.data().countType(type) < getCap(team) && !type.isBanned())    // Units.java:115-117
getCap(team):
    if(waveTeam 且 非 pvp) / 战役 waveTeam / rules.disableUnitCap / team.ignoreUnitCap → Integer.MAX_VALUE
    else max(0, rules.unitCapVariable ? rules.unitCap + team.data().unitCap : rules.unitCap)  // :119-125
```

- `rules.unitCap = 0`, `rules.unitCapVariable = true` (Rules.java:75,157) → the cap = **the sum of every core's `unitCapModifier`** + `rules.unitCap`.
- Core bonuses: core-shard **8**, core-foundation **16**, core-nucleus **24**, core-bastion **15**, core-citadel **15**, core-acropolis **15** (Blocks.java:3138/3150/3163/3185/3202/3220).
- `BlockIndexer.java:216/614` maintains `team.data().unitCap` when cores are placed or removed.
- **In campaign the enemy waveTeam has cap = MAX_VALUE** (not capped at all) — that is the root cause of "the enemy keeps growing while you stay limited".

### 5. Payload capacity

```
Vars.tilePayload = tilesize * tilesize = 64     // Vars.java:137
UnitType.payloadCapacity 单位是 world units²；显示时 ÷ tilePayload 换算成"格²"
```

### 6. Cost scaling

`Rules.unitCostMultiplier = 1` (Rules.java:83), multiplied with the team version (:295). `CampaignRules.java:41` sets the enemy team to `1 / enemySpawnMultiplier` — on hard (1.5) enemy units cost **0.667×**.

## Numbers

### Factories (Blocks.java:6269-6447)

| Block | Size | Power | Plans (unit / time in ticks / item cost) |
|---|---|---|---|
| ground-factory | 3 | 1.2 | dagger 900t(15s) silicon10+lead10; crawler 600t(10s) silicon8+coal10; nova 2400t(40s) silicon30+lead20+titanium20 |
| air-factory | 3 | 1.2 | flare 900t silicon15; mono 2100t silicon30+lead15 |
| naval-factory | 3 | 1.2 | risso 2700t silicon20+metaglass35; retusa 2100t silicon15+titanium20（floating） |
| tank-fabricator | 3 | 1.5 | stell 2100t beryllium40+silicon50（configurable=false） |
| ship-fabricator | 3 | 1.5 | elude 2400t graphite50+silicon70 |
| mech-fabricator | 3 | 1.5 | merui 2400t beryllium50+silicon70 |

### Reconstructors (Blocks.java:6303-6385)

| Block | Size | Power | Items/s | Liquid | constructTime | Upgrade pairs |
|---|---|---|---|---|---|---|
| additive-reconstructor | 3 | 3 | silicon40+graphite40 | — | 600t = **10 s** | 7 |
| multiplicative-reconstructor | 5 | 6 | silicon130+titanium80+metaglass40 | — | 1800t = **30 s** | 7 |
| exponential-reconstructor | 7 | 13 | silicon850+titanium750+plastanium650 | cryofluid **1/s** | 5400t = **90 s** | 7 |
| tetrative-reconstructor | 9 | 25 | silicon1000+plastanium600+surgeAlloy500+phaseFabric350 | cryofluid **3/s** | 14400t = **240 s** | 7 |

Upgrade chains (7 pairs per block, excerpt): additive: dagger→mace, crawler→atrax, nova→pulsar, flare→horizon, mono→poly, risso→minke, retusa→oxynoe. tetrative: antumbra→eclipse, arkyid→toxopid, scepter→reign, sei→omura, quad→oct, vela→corvus, aegires→navanax.

### Assemblers (Blocks.java:6522-6564)

| Block | Size | Power | Liquid | Plans (unit / time / payload inputs) |
|---|---|---|---|---|
| tank-assembler | 5 | 2.5 | cyanogen 9/60 per second | vanquish 3000t + 4×stell + 10×tungsten-wall-large |
| tank-assembler | 5 | 2.5 | same as above | conquer 10800t + 6×locus + 20×carbide-wall-large |
| ship-assembler | 5 | 2.5 | cyanogen 12/60 per second | quell 3600t + 4×elude + 12×beryllium-wall-large; disrupt 10800t + 6×avert + 20×carbide-wall-large |
| mech-assembler | 5 | 3 | cyanogen 12/60 per second | tecta 4200t + 5×merui + 12×tungsten-wall-large; collaris 10800t + 6×cleroi + 20×carbide-wall-large |

### Payload capacity

| Unit | Field | Conversion |
|---|---|---|
| mega | `(2*2)*64 = 256` | 4 tiles² |
| quad | `(3*3)*64 = 576` | 9 tiles² |
| quell | `sqr(4)*64 = 1024` | 16 tiles² |
| disrupt | `sqr(6)*64 = 2304` | 36 tiles² |
| default | `payloadCapacity = 8` | 0.125 tiles² (cannot carry any block) |

### Tier ratios and the whole-chain bottleneck (deriving the build-out)

Unit production is a **serial pipeline**: T1 is built by factories, T2..T5 are built by reconstructors that consume the previous tier. Each machine's "units per second" is set only by that tier's `constructTime`:

    units/s per machine = outPer / (constructTime / 60)        // 60 ticks = 1 s

| Tier | Block | Time | Per machine (units/s) |
|---|---|---|---|
| T1 | ground-factory (dagger) | 900 t = 15 s | 0.0667 |
| T2 | additive-reconstructor (mace) | 600 t = 10 s | 0.1000 |
| T3 | multiplicative-reconstructor (fortress) | 1800 t = 30 s | 0.0333 |
| T4 | exponential-reconstructor (scepter) | 5400 t = 90 s | 0.0111 |
| T5 | tetrative-reconstructor (reign) | 14400 t = 240 s | 0.0042 |

The times come from the factory and reconstructor tables above [src: Blocks.java:6269-6447] [src: Blocks.java:6303-6385]; the per-second conversion follows [src: Reconstructor.java:90] (`Stat.productionTime = constructTime / 60f`). Factories have no `constructTime` field, only `plans[].time` (T1 = `UnitPlan.time`, [src: Blocks.java:6272]); `constructTime` belongs to reconstructors ([src: Blocks.java:6310]). The rate holds only while `efficiency > 0` (full power and full input) and `rules.unitBuildSpeed = 1` ([src: Reconstructor.java:328-334], [src: UnitFactory.java:401-420]).

**The tier ratio is not 1:1** — it is inversely proportional to each tier's per-machine rate:

    machines_upstream_k ≈ demand_downstream_k × rate_k⁻¹
    1 T4 machine feeds 0.0111 / 0.0042 ≈ 2.67 T5 machines
    1 T3 feeds 3 T4; 1 T2 feeds 3 T3; 1 T1 feeds only 0.67 T2

Actual whole-chain output is limited by **the slowest stage** (each tier upgrades one-to-one, so any starved stage drags the whole chain down to its rate):

    chain output = min_k( count_k × rate_k / Π_{j>k} inPer_j )      // inPer defaults to 1

Example: 5 fully fed T5 machines ⇒ T1..T5 counts = **1/1/1/2/5**, whole chain 0.0208 units/s; material must be derived from what the chain actually reaches, not from the 5 machines you want (otherwise silicon comes out about 2.4× too high).

**Counterexample (a common misreading)**: wiring T4/T5 at 1:1 — 5 T5 machines eat only 0.021/s while 5 T4 machines can produce 0.056/s, so T4 runs at 37.5% utilisation and 3 of them are wasted; conversely, 1 T4 feeding 5 T5 caps the chain at 0.011/s and T5 runs at 53%. The other trap is multiplying per-item cost by the output you want: surplus capacity upstream of the bottleneck consumes nothing extra, so budgeting that way overstates chain material by more than 2×.

## Source anchors

- [src: UnitFactory.java:392-443] `updateTile`: `progress += edelta() * Vars.state.rules.unitBuildSpeed(team)`, spawning at `plan.time`.
- [src: UnitFactory.java:207-219] `UnitPlan{UnitType unit; ItemStack[] requirements; float time;}`.
- [src: Reconstructor.java:36-41] `constructTime = 60*2` default, `upgrades`, `capacities`.
- [src: Reconstructor.java:90] `stats.add(Stat.productionTime, constructTime/60f, StatUnit.seconds)`.
- [src: UnitAssembler.java:45-52] `areaSize=11`, `dronesCreated=4`, `droneConstructTime=60*4`, `capacities`, `plans`.
- [src: Rules.java:290-295] the multiplications in `unitBuildSpeed(team)` / `unitCost(team)`.
- [src: Units.java:114-131] `canCreate` / `getCap` / `getStringCap`.
- [src: BlockIndexer.java:216,614] decrement/increment of `unitCap`.
- [src: Vars.java:137] `tilePayload = tilesize*tilesize`.

## Tests and counterexamples

**Counterexample 1: reading `UnitPlan.time` as seconds.**
dagger's 900 is **900 ticks = 15 s** (900/60). Read as seconds it looks like 15 minutes. Every `time`/`constructTime`/`reload` in this source tree is in ticks.

**Counterexample 2: assuming `unitCap` is a fixed number.**
`rules.unitCap` defaults to **0**; with `unitCapVariable` true the cap comes entirely from cores: 3 core-nucleus = `3×24 = 72`. Placing a `core-acropolis` (modifier 15) gives **9 fewer** than a nucleus — the big core's strength is 30000 hp and 6×6, not cap.

**Counterexample 3: assuming an assembler assembles in parallel without limit.**
`AssemblerUnitPlan` advances one plan at a time; `conquer` needs 10800 ticks (180 s) + 6 locus (each of which needs 2100t to build) + 20 carbide-wall-large, so it is an **exponential industry chain**, not "build it and a 22000 hp unit pops out".

**Counterexample 4: assuming the enemy obeys the 40/unit cap too.**
In campaign `waveTeam` hits the first branch of `getCap` → `Integer.MAX_VALUE`.

**Recomputable**: a ground-factory needs 900 ticks for 1 dagger; `unitBuildSpeed` defaults to 1 → 15 s. If a logic processor sets `rules.unitBuildSpeedMultiplier` to 3 (the `LExecutor` `unitbuildspeed`), that becomes 300 ticks = 5 s each; 10 daggers take 150 ticks × ... in practice `10 × 900 / 3 = 3000 ticks = 50 s`.

## Common misconceptions

- ❌ "A reconstructor can build new units." → it can only swap an **existing low-tier unit** for a high-tier unit in its table.
- ❌ "A factory stores its own input." → `itemCapacity = 10`, fed from outside; a full buffer stops the factory.
- ❌ "The unit cap applies to NPCs too." → it applies only to player/team units with `useUnitCap = true`.
- ❌ "payload is a number of tiles." → the field is in world units², divided by 64 only for display.
- ❌ "core-acropolis has the highest cap." → the six cores' modifiers are 8/16/24/15/15/15; nucleus is the highest.

## Related

- [[UNIT.MOVE.001]] how the units you build actually move
- [[UNIT.AI.001]] the default commands factory output gets
- [[UNIT.PROGRESSION.001]] why there are "tiers" but no "levels"
- [[COMBAT.WAVE.001]] the uncapped enemy waves
