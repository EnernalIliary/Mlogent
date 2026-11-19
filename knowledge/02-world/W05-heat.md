---
id: WORLD.HEAT.001
title: The heat system
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/entities/comp/BuildingComp.java:412-470"
  - "Mindustry-Source/core/src/mindustry/world/blocks/heat/HeatProducer.java:14-62"
  - "Mindustry-Source/core/src/mindustry/world/blocks/production/HeatCrafter.java:13-85"
  - "Mindustry-Source/core/src/mindustry/world/blocks/heat/HeatConductor.java:53-111"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/NuclearReactor.java:29-153"
  - "Mindustry-Source/core/src/mindustry/world/consumers/ConsumeCoolant.java:5-12"
  - "Mindustry-Source/core/src/mindustry/world/blocks/defense/turrets/ReloadTurret.java:28-39"
  - "Mindustry-Source/core/src/mindustry/world/blocks/power/ThermalGenerator.java:22, 71, 78-80"
  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:318-381 (地板 heat 属性)"
data: [00-data/blocks.json]
depends: [WORLD.LIQUIDS.001, WORLD.CRAFTING.001]
tags: [heat, HeatCrafter, HeatProducer, coolant, overheating, reactors, heatCapacity]
tokens: 1519
---

## In one sentence

Heat is a **scalar field with no fluid medium**: a heat source block stores a `heat` value, neighbouring blocks **copy that heat and add it up** by "contact points ÷ own size" (non-conserving, no decay, nothing consumed), so heat transfer is pure geometry; and `heatCapacity` is never "a block's heat storage", it appears only in the **coolant bonus formula**.

## Rules / formulas

### 1. The three kinds of heat block

| Interface/class | Role | Count in v160.7 |
|---|---|---|
| `HeatBlock` | provides `heat()` / `heatFrac()` | counted inside the three below |
| `HeatProducer` | produces heat from a recipe (itself a GenericCrafter) | 6 |
| `HeatCrafter` | a crafter that works off adjacent heat | 5 |
| `HeatConductor` | heat-conduction relay (produces no heat itself) | 3 |

`HeatProducerBuild` drives heat towards `heatOutput × efficiency` every tick [src: HeatProducer.java:51]:

```
heat = approachDelta(heat, heatOutput * efficiency, warmupRate * delta)   // warmupRate 默认 0.15
```

Note that `heat ` is an **absolute value**, not an output per second; `heatOutput` is simply the value it settles at. A `HeatProducer`'s `heatOutput` is entirely unrelated to a `ConsumePower`'s `usage`.

### 2. The heat-transfer formula (the one core)

`BuildingComp.calculateHeat(sideHeat)` [src: BuildingComp.java:416-460]:

```
for (每个相邻且同队且 instanceof HeatBlock 的 heater):
    heat += heater.heat() / heater.size * contactPoints
    // contactPoints = min(size/2 + heaterSize/2 - 中心距(格), min(heaterSize, size))
    // 导热中继 splitHeat = true 时再 / 3
```

Three key properties:

1. **Addition, not averaging**: three slag-heater units with heatOutput = 8 against a crafter with heatRequirement = 24 give 24 — exactly enough. This is why "stack heat sources" works.
2. **Thinned by size**: `heater.heat() / heater.size`. A 3×3 slag-heater (8 heat) touching one tile of edge gives only `8/3 ≈ 2.67`; touching three tiles of edge gives `8/3 × 3 = 8` (one full edge of a 3×3 crafter).
3. **Non-conserving, non-decaying**: the same heat is read by two adjacent consumers at the same time and each gets the full amount; heat does not shrink by being transferred, and there is no distance falloff (only face-adjacent counts; one tile of separation = 0).

The facing rules live here too [src: BuildingComp.java:428]: an ordinary heat source must **face** the consumer (`(relativeTo + 2) % 4 == heater.rotation`), while a heat conductor must **face away** from it (`relativeTo != rotation`); the exception is a heat-router with `splitHeat = true`, which can output heat from three faces, each divided by 3.

### 3. Heat consumers: HeatCrafter

`HeatCrafterBuild.updateTile()` sets `heat = calculateHeat(sideHeat)` first and then runs the recipe [src: HeatCrafter.java:49-53]; the efficiency factor [src: HeatCrafter.java:82-85]:

```
over  = max(heat - heatRequirement, 0)
scale = min( clamp(heat / heatRequirement) + over / heatRequirement * overheatScale, maxEfficiency )
```

- `heat < heatRequirement` → efficiency falls linearly (half the heat, half the speed);
- `heat >= heatRequirement` → only `overheatScale > 0 yields extra benefit;
- **all five HeatCrafters in v160.7 have `maxEfficiency = 1`**, i.e. "no matter how much heat you give, it stops at 100%"; overheat benefit is switched off on these five blocks.

In addition `shouldConsume()` requires `heat > 0` [src: HeatCrafter.java:56-58]: **with no heat at all it does not eat inputs**, which makes "lay the heat sources first, then feed" the only correct order.

### 4. Coolant and heatCapacity

`heatCapacity` appears in the cooling formula, not in any heat-storage formula:

**Turrets** (`ReloadTurret`, the parent of every ItemTurret / LaserTurret) [src: ReloadTurret.java:30-33]:

```
capacity = 冷却液.heatCapacity        // 无冷却液时按 0.4
reloadCounter += coolant.amount * efficiency * edelta * capacity * coolantMultiplier
```

water 0.4, cryofluid 0.9 → **the same turret gains 2.25× the fire-rate bonus from cryofluid as from water** (per-tick consumption being equal).

**Shields**: `ForceProjector`'s `liquidHeat = 1 + (heatCapacity - 0.4) × 0.9` [src: ForceProjector.java:134].
**Repair towers**: `multiplier = 1 + heatCapacity × coolantMultiplier × efficiency` [src: RepairTurret.java:190].
**Parallax traction**: consumption is inversely capped by `min(stock, maxUsed×delta, (1/coolantMultiplier)/heatCapacity)` [src: TractorBeamTurret.java:97] — the higher the heat capacity, the less coolant a single tick can "eat", but the more each drop is worth.

### 5. Which liquids can serve as coolant

`ConsumeCoolant`'s filter [src: ConsumeCoolant.java:5-12]:

```
liquid.coolant && liquid.temperature <= maxTemp(0.5) && liquid.flammability < maxFlammability(0.1)
        && (allowLiquid && !liquid.gas || allowGas && liquid.gas)
```

Filtering the 11 liquids of v160.7 through that table one by one, **only water (0.5/0), cryofluid (0.25/0) and gallium (0.5/0) qualify**:

- slag, temperature 1.0 → over the limit;
- oil flammability 1.2, arkycite 0.4, ozone 1, hydrogen 1, cyanogen 2 → over the flammability limit;
- neoplasm, temperature 0.54 → over the limit;
- nitrogen, temperature 0.5 and flammability 0, but it is a `gas` and turrets have `allowGas = 0` → blocked by the gas rule.

Note that the `Liquid.coolant` field is only the first coarse sieve: slag / oil / neoplasm all have `coolant` true, yet still cannot act as coolant in a vanilla turret.

### 6. Overheat and explosion: only reactors explode

Exactly one thing called "heat" in the whole game can run out of control: the **nuclear reactor (thorium-reactor)** [src: NuclearReactor.java:96-133]:

```
fullness = 燃料数 / itemCapacity(30)
heat += fullness * heating(0.005) * min(delta, 4)        // 有燃料且 enabled
heat = max(0, heat - delta / ambientCooldownTime(1200))  // 没燃料时自然冷却
maxUsed = min(当前冷却液量, heat / coolantPower(0.125))
heat -= maxUsed * coolantPower ; 扣掉 maxUsed 冷却液
heat = clamp(heat, 0, 1)
if (heat >= 0.999) { kill(); }                            // 爆炸
```

Plugging in the v160.7 parameters yields three hard numbers:

- **Full fuel, no cooling**: +0.005 per tick → **199 tick ≈ 3.3 seconds** to explode at 0.999;
- **Just holding it**: you must draw off 0.005 heat per tick, i.e. `0.005 / 0.125 = 0.04` units of coolant/tick = **2.4 units per second** (of water);
- **Cooling a fully heated reactor**: holding it needs `1 / 0.125 = 8` units of coolant/tick = 480/s, far beyond what a single conduit typically supplies.

Explosion parameters: `explosionRadius = 19` tiles, `explosionDamage = 5000` [src: NuclearReactor.java:67-68]. `shouldExplode()` additionally requires `fuel >= 5 || heat >= 0.5` [src: NuclearReactor.java:152-153], so an empty reactor that gets destroyed does not go nuclear.

`heatProgress` is unrelated to the explosion: it is only the smoothed output-power value `approachDelta(heatProgress, heat × heatOutput, heatWarmupRate)`, used for supplying power and heat.

### 7. Thermal generation (turning floor heat attributes into power)

`ThermalGenerator`'s `productionEfficiency = sum(covered tiles' floor.attributes[heat]) + Attribute.heat.env()` [src: ThermalGenerator.java:78-80], multiplied by `powerProduction`.

- A short thermal generator (2×2 covering 4 tiles) entirely on molten-slag = `4 × 0.85 = 3.4` efficiency, i.e. `1.8 × 3.4 = 6.12/tick = 367/s`;
- `canPlaceOn` requires the summed heat of the covered floors to be `> minEfficiency` [src: ThermalGenerator.java:69-72], so it must sit on hot floor;
- Floor heat values: **molten-slag 0.85, magmarock 0.75, hotrock 0.5** [src: Blocks.java:327, 364, 374]; a planet's `defaultAttributes` heat = 0.8 (`Planets.java:72`) is added to `env()`.

Liquids themselves vaporise because of planetary ambient heat too: `Liquid.willBoil() = Attribute.heat.env() >= boilPoint` [src: Liquid.java:110-113].

## Numbers

**Heat sources (heatOutput)**

| Block | heatOutput | Note |
|---|---|---|
| electric-heater | 3 | 2×2, power-fed |
| oxidation-chamber | 5 | 3×3 |
| slag-heater | 8 | 3×3, slag-fed |
| heat-reactor | 10 | 3×3 |
| phase-heater | 15 | 2×2, phase-fabric-fed |
| neoplasia-reactor | 60 | 5×5, HeaterGenerator |
| heat-source (sandbox) | 1000 | 1×1, editor |

**Heat consumers (heatRequirement, all maxEfficiency = 1)**

| Block | heatRequirement | Size |
|---|---|---|
| cyanogen-synthesizer | 20 | 3×3 |
| atmospheric-concentrator | 24 | 3×3 |
| phase-synthesizer | 32 | 3×3 |
| carbide-crucible | 40 | 3×3 |
| surge-crucible | 40 | 3×3 |

**Coolant multiplier `coolantMultiplier` (turrets)**

| Multiplier | Blocks |
|---|---|
| 30 | arc |
| 15 | breach / diffuse / scathe / smite |
| 10 | duo / hail |
| 6.25 | disperse |
| 5 | lancer / wave / swarmer / salvo / fuse / ripple / cyclone / afflict / malign / build-tower / scatter |
| 3.75 | titan |
| 2 | segment |
| 1.6 | repair-turret |
| 1 | meltdown / parallax / sublimate / lustre / repair-point |
| 0.5 | spectre |
| 0.4 | foreshadow |

**Coolant consumption (ConsumeCoolant.amount, per tick → per second)**

| Block | amount/tick | /second |
|---|---|---|
| duo / hail / arc | 0.1 | 6 |
| fuse / cyclone / ripple | 0.3 | 18 |
| foreshadow | 1 | 60 |

## Source anchors

- `BuildingComp.java:416-460` `calculateHeat`: the contact-point formula, facing validation, `splitHeat`'s /3, and the `cameFrom` loop check.
- `BuildingComp.java:412-414` the simplified overload without `cameFrom` (HeatCrafter uses this one).
- `HeatProducer.java:51` `heat = approachDelta(heat, heatOutput * efficiency, warmupRate * delta)`.
- `HeatCrafter.java:49-57` compute heat first, then run the recipe; `shouldConsume` requires `heat > 0`.
- `HeatCrafter.java:71-73` `warmupTarget = clamp(heat / heatRequirement)`.
- `HeatCrafter.java:82-85` `efficiencyScale`: linear + overheatScale, capped at maxEfficiency.
- `HeatConductor.java:85-90, 109-111` `updateHeat` and `heatFrac = heat / visualMaxHeat / (splitHeat ? 3 : 1)`.
- `NuclearReactor.java:101-133` heating / cooling / clamp / `heat >= 0.999f → kill()`.
- `NuclearReactor.java:112-116` coolant consumption `maxUsed = min(stock, heat / coolantPower)`.
- `ConsumeCoolant.java:5-12` the `maxTemp = 0.5`, `maxFlammability = 0.1` filter.
- `ReloadTurret.java:28-39` the turret cooling bonus formula (including `ammoReloadMultiplier`).
- `ThermalGenerator.java:71` `canPlaceOn` relies on the sum of the floor heat attributes; `:78-80` efficiency = sum + `attribute.env()`.
- `Blocks.java:327/364/374` floor heat attributes 0.85 / 0.5 / 0.75.

## Measurements and counter-examples

**Counter-example 1 (blocks have no `maxTemp` property)**: checklists often say "heat / maxTemp", but searching the v159.3 source tree for `maxTemp` hits only `ConsumeCoolant.java:5` — it is the **coolant filter's temperature ceiling (0.5)**, not any block's "heat tolerance". Vanilla blocks have no high-temperature damage mechanism: a HeatCrafter never burns out no matter how much heat it receives, and a reactor explodes only on its own `heat >= 0.999`.

**Counter-example 2 (heat transfer is non-conserving: one unit of heat can feed two consumers at once)**: `calculateHeat` merely **reads and sums** the adjacent heaters' `heat()`, and the heater's own heat does not decrease. So two HeatCrafters against the same slag-heater both get the full amount (each limited by its own contact points), rather than "splitting it in half".

**Counter-example 3 (`coolant = true` does not mean it can be a coolant)**: slag's `Liquid.coolant` field is true and so is oil's, but a turret's `ConsumeCoolant` requires `temperature <= 0.5` and `flammability < 0.1`, so both are rejected. Vanilla turrets actually have only three legal coolants: water / cryofluid / gallium.

**Counter-example 4 (overheat is not overproduction)**: the `HeatCrafter` source defaults to `maxEfficiency = 4` and `overheatScale = 1`, which looks like "4× overheat benefit", but all five HeatCrafters in v160.7 set `maxEfficiency` to 1. That is to say, feeding carbide-crucible 80 heat (requirement 40) does **not** make it twice as fast.

**Counter-example 5 (the reactor's `heatOutput = 8` is not its generation)**: thorium-reactor's `heatOutput` is its heat-supply value (the HeatBlock interface); its generation comes from `powerProduction = 15/tick` (900/s). The two are independent fields that merely both have "heat" in the name.

## Common misconceptions

1. **"heat decays with distance / heat needs pipes"** → only face-adjacent (`proximity`) HeatBlocks are counted, and one tile of separation is 0; there is no "heat pipeline loss", and a heat conductor only "relays" heat further away.
2. **"heatCapacity is a block's heat storage, so a high-capacity block heats up slowly"** → no block-level heat-storage field exists. `heatCapacity` belongs only to **liquids**, and appears only as a multiplier in the coolant bonus formula.
3. **"coolant reduces turret damage / has other side effects"** → vanilla coolant only speeds up `reloadCounter` (faster fire) with no negative effect at all; `ConsumeCoolant` is `optional = true, booster = true`, so a turret fires without coolant too.
4. **"every generator has cooling"** → only the 16 blocks implementing `ConsumeCoolant` (16 turret classes + force-projector) have a coolant port; a reactor's "cooling" is its own hand-written `coolantPower` logic, unrelated to `ConsumeCoolant`.
5. **"a heat source adjacent to a block always supplies heat"** → ordinary HeatProducer/HeatCrafter have facing requirements (they must face each other); only a heat-router with `splitHeat = true` outputs heat from three faces, and its own output is then divided by 3.
6. **"a reactor without water overheats slowly, there is time to save it"** → with full fuel it explodes in 199 tick (about 3.3 seconds); with no fuel it cools naturally to 0 over `ambientCooldownTime = 1200` tick (20 seconds).

## Related

- `WORLD.LIQUIDS.001` (coolant liquid properties and conduit supply)
- `WORLD.CRAFTING.001` (HeatCrafter extends GenericCrafter, so recipe and craftTime semantics are unchanged)
- `WORLD.POWER.001` (reactor generation and thermal-generator output)
- `WORLD.TERRAIN.001` (floor heat attributes and `molten-slag` / `hotrock` / `magarock` terrain)
- `WORLD.BLOCKS.001` (how block size affects `contactPoints`)
- Data tables: `00-data/blocks.json` (`heatOutput` / `heatRequirement` / `coolantMultiplier` / `maxEfficiency` in the `raw` subtree)
- Source: `world/blocks/heat/*.java`, `world/blocks/production/HeatCrafter.java`, `world/blocks/power/NuclearReactor.java`, `world/consumers/ConsumeCoolant.java`
