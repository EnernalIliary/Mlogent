# Knowledge base - English index

Every article here is written in English; the Chinese names that are worth
keeping live in the name tables and in [GLOSSARY.md](GLOSSARY.md), which maps
each official Chinese name to its English id. `knowledge/README.md` explains how
the library is organised, `knowledge/CONVENTIONS.md` what a claim must look
like, and `knowledge/STYLE-en.md` the writing rules.

Two conventions that survive translation:

- **`null` is not `pass`.** Any field that says "not measured" must not be read
  as "fine" - that convention runs through every article here.
- **Names come from the game bundle.** `parallax` is the air puller (差扰), not
  a gravity tower; the three-layer name table (official / legacy / colloquial)
  is in [GLOSSARY.md](GLOSSARY.md).

## Where to start

| You want | Read |
|---|---|
| the execution model: tick, instruction budget, accumulator | `01-execution/E01` |
| why a statement silently does nothing | `01-execution/E02` |
| variable, object and memory-cell limits | `01-execution/E03` |
| link names and `@`-variables, and why a rename breaks them | `01-execution/E05` |
| a pattern that already works (bus, counters, multicontrol) | `07-patterns/P03`, `P07`, `P08` |
| Mindcode: compiling `.mnd`, syntax, source maps | `06-mlog/M09`, `M10` |
| what a verification result looks like | `04` in `docs/实施记录.md` |
| a number with a source anchor | `02-world/W1x`, or `00-data/*.json` |

## Articles

### `01-execution/` — 6 articles

| Article | Title | What it says |
|---|---|---|
| [`E01-执行模型与预算`](01-execution/E01-执行模型与预算.md) | Execution model and instruction budget: the full chain from tick to accumulator | How the per-tick accumulator refills at edelta x ipt, clips its pool to 5 x ipt under lag, and executes one instruction per point. |
| [`E02-指令语义陷阱`](01-execution/E02-指令语义陷阱.md) | 30 instruction semantics traps (vectors / objects / numbers / timing / memory / interaction) | Catalog of 30 mlog semantic traps across vectors, objects, numbers, timing, memory and interaction, each with the wrong form, the fix and the reason. |
| [`E03-变量与内存边界`](01-execution/E03-变量与内存边界.md) | Variable and memory boundaries: LVar's four states, memory cells and the text buffer | Why each LVar holds only number, object, null or const, and how memory cells and the text buffer carry every non-scalar value. |
| [`E04-时间与wait精度`](01-execution/E04-时间与wait精度.md) | Time and wait precision: ticks, seconds and frame delta | Why the game clock is 60 ticks/s, why wait takes seconds but resolves to whole ticks, and why wait 0.05 stalls three ticks. |
| [`E05-链接与@常量`](01-execution/E05-链接与@常量.md) | Links and @ constants: @links / getlink, built-in variable classes and units | How compile-time @link constants differ from const @ values that set silently discards and from engine-refreshed globals. |
| [`E06-跨版本差异`](01-execution/E06-跨版本差异.md) | Cross-version differences: v159.3 source vs v160.7 measurements, and the documentation conflict list | Why semantics follow the v159.3 source tree while numbers come from v160.7 jar reflection and live tests, plus known doc conflicts. |

### `02-world/` — 16 articles

| Article | Title | What it says |
|---|---|---|
| [`W01-blocks-multiblock-anchor`](02-world/W01-blocks-multiblock-anchor.md) | Block model and multiblock anchors | How block size maps to n x n tiles, why odd sizes center on the cursor while even sizes shift up-left, and how one Building is shared. |
| [`W02-crafting-recipes`](02-world/W02-crafting-recipes.md) | Recipes and manufacturing | How ConsumeItems/Liquid/Power, craftTime and outputs combine, and why items are charged per craft while liquids and power drain per tick. |
| [`W03-power`](02-world/W03-power.md) | Power network | Why power has no wires: each PowerGraph settles total demand against supply every tick and applies one coverage ratio, batteries taking the surplus. |
| [`W04-liquids`](02-world/W04-liquids.md) | Liquid system | Why liquid flow has no speed field, how each block moves liquid by fill-fraction difference times capacity, and why full or mixed pipes stall. |
| [`W05-heat`](02-world/W05-heat.md) | Heat system | Why heat is a scalar copied to neighbors by contact-count over size with no conservation or decay, and why heatCapacity only feeds coolant bonus. |
| [`W06-logistics`](02-world/W06-logistics.md) | Logistics and item transport (conveyors / routers / junctions / bridges / mass drivers) | How conveyors, ducts, routers, junctions, bridges and mass drivers move items, and why their speed fields use three incompatible units. |
| [`W07-drills-resources`](02-world/W07-drills-resources.md) | Drilling and resources: drill tiers, hardness penalty and ore coverage | How Drill, BeamDrill, BurstDrill and WallCrafter gate output by tier and hardness, making the UI's items/s an optimistic figure. |
| [`W08-payloads`](02-world/W08-payloads.md) | Payloads: the whole-block transport chain for block and unit payloads (conveyors / routers / constructors / deconstructors / mass drivers) | How payloads travel a separate chain of payload conveyors, routers, constructors, deconstructors and mass drivers, all measured in tiles. |
| [`W09-terrain`](02-world/W09-terrain.md) | Terrain and environment: the floor / overlay / wall three-layer structure, movement multipliers and land/water checks | How floor, ore overlay and wall layers each carry their own stats and jointly decide movement speed, liquid presence and buildability. |
| [`W10-storage`](02-world/W10-storage.md) | Storage: core capacity accounting, containers/vaults and unloader transfer priority | Why cores cap each item at storageCapacity, why adjacent containers merge into the core, and how unloaders choose source and destination. |
| [`W11-block-state`](02-world/W11-block-state.md) | Block state and configuration (config / rotation / enabled / @sensor) | How rotation, config and enabled are stored per building, how configured() dispatches config types, and how sense(LAccess) and sense(Content) read them. |
| [`W12-sandbox-editor`](02-world/W12-sandbox-editor.md) | Sandbox and editor (buildVisibility / inEditor / instantBuild / rules) | How buildVisibility, inEditor, placeablePlayer, instantBuild and map rules decide what can be built, leaving sandbox blocks with nothing special. |
| [`W13-name-blocks-terrain`](02-world/W13-name-blocks-terrain.md) | Block name reference 1: terrain / ores / walls (136 entries) | Lookup table mapping 136 terrain, ore and wall blocks between their in-game Chinese names, English names and ids. |
| [`W14-name-blocks-industry`](02-world/W14-name-blocks-industry.md) | Block name reference 2: logistics / power / liquids / production (168 entries) | Lookup table of 168 logistics, power, liquid and production blocks grouped by category, mapping Chinese names to English names and ids. |
| [`W15-name-blocks-combat`](02-world/W15-name-blocks-combat.md) | Block name reference 3: crafting / turrets / effects / unit blocks / logic (143 entries) | Lookup table of 143 crafting, turret, effect, unit-factory and logic blocks, where turret names are often imagery rather than description. |
| [`W16-name-items`](02-world/W16-name-items.md) | Item / liquid / status effect name reference (56 entries) | Lookup table of 56 items, liquids and status effects, the only way to turn a displayed name back into an id since these show no block id. |

### `03-combat/` — 39 articles

| Article | Title | What it says |
|---|---|---|
| [`C01-damage-pipeline`](03-combat/C01-damage-pipeline.md) | Damage pipeline overview: the full order of a hit from BulletType to health | The six fixed stages of a hit from BulletType to health, and why armor's max(damage - armor, 0.1 x damage) floor never reaches zero. |
| [`C02-turrets`](03-combat/C02-turrets.md) | Turret mechanics: range, reload, ammo, coolant, aiming and overheat | How reloadCounter, cooldownTime and coolant top-ups set turret rhythm, with water adding 40% and cryofluid 90% reload speed regardless of turret. |
| [`C03-bullets`](03-combat/C03-bullets.md) | Bullets and ballistics: lifetime/speed/drag, piercing, splash, lightning and fragments | Why real bullet range is speed x lifetime rather than turret range, and why splashDamageRadius -1 means no splash while pierceCap -1 means unlimited. |
| [`C04-status`](03-combat/C04-status.md) | Status effects: multiplier fields, duration, stacking and refresh, reaction damage | Why status effects refresh duration instead of stacking, taking max(remaining, new), while different statuses multiply into the four unit multipliers. |
| [`C05-armor`](03-combat/C05-armor.md) | Armor and resistances: the subtraction formula, 10% floor, armor piercing and immunity | Why armor subtracts rather than scales, so a 26-armor unit takes 0.9 from a 9-damage bullet but 324 from a 350-damage one. |
| [`C06-unit-weapons`](03-combat/C06-unit-weapons.md) | Unit weapons: weapons[], mount coordinates, mirroring and unit DPS | Why mirror = true duplicates each weapon mount at +x and -x, and why unit DPS must sum every mount's independent reload. |
| [`C07-support`](03-combat/C07-support.md) | Healing, shields and repair: heal / shield / mend / repairSpeed | Why unit heal is flat HP, block healPercent is per-event max HP, repair turrets use HP per second, and shields break without overflowing. |
| [`C08-waves`](03-combat/C08-waves.md) | Enemies and attack waves: spawn points, wave composition, difficulty scaling and AI targets | How SpawnGroup drives wave counts via min(unitAmount + floor(((wave-begin)/spacing)/unitScaling), max), multiplying count, health and shields. |
| [`C09-defense`](03-combat/C09-defense.md) | Defenses: stats and resolution order of walls, doors, shields and repair turrets | How walls, shield walls, repair/overdrive and turrets layer defense, and why shields absorb damage only after armor is applied. |
| [`C10-numbers`](03-combat/C10-numbers.md) | Combat number worked examples: the DPS definition, cross-layer accounting and TTK | How rate = 60/reload, d = max(D - A, 0.1D) and DPS = rate x shots x d reproduce combat numbers that differ up to 5x across layers. |
| [`C11-turret-verdict`](03-combat/C11-turret-verdict.md) | Vanilla turret evaluation overview and selection decision table (per-turret index of 28) | Why the 28 vanilla turrets should be chosen by era and role rather than raw DPS, since the top-DPS towers are the hungriest. |
| [`T101-duo`](03-combat/turrets/T101-duo.md) | duo - the burst-fire baseline for 35 items | Why the 35-item duo carries the opening with 3 copper shots/s over 20 tiles, yet drops to 6.8 DPS against 22 armor once graphite replaces copper. |
| [`T102-scatter`](03-combat/turrets/T102-scatter.md) | scatter - the 222 listed-DPS air sweeper | Why the 222 listed-DPS scatter is an anti-air patch only: two pellets per trigger, air-only targeting, and 3 direct damage that cannot dent 22 armor. |
| [`T103-scorch`](03-combat/turrets/T103-scorch.md) | scorch - the point-blank brazier at 60 world units | Why scorch trades its 7.5-tile reach for 10 pyratite rounds/s and 300 point-blank DPS, leaving it useless once enemies flank or outrange it. |
| [`T104-hail`](03-combat/turrets/T104-hail.md) | hail - single-shot shelling at 235 world units | Why hail is the only early way to hit back lines at 29 tiles, and why its one shot/s and slow fixed-impact shell miss once enemies move. |
| [`T105-wave`](03-combat/turrets/T105-wave.md) | wave - the 20-round-per-second fire extinguisher | Why wave deals almost no damage but earns its slot: 20 liquid rounds/s with 0.7 knockback, and water or cryofluid extinguishing burning waves. |
| [`T106-lancer`](03-combat/turrets/T106-lancer.md) | lancer - the heavy-armor can opener with 140 direct damage | Why lancer's 140 direct damage and 4x armorMultiplier keep 52 per shot against 22 armor, at the cost of 360 power/s and an 80-tick reload. |
| [`T107-arc`](03-combat/turrets/T107-arc.md) | arc - 34 DPS from chained lightning | Why arc is strong against crowds and useless alone: 34 single-target DPS, chained lightning that jumps and applies shocked, and no anti-air at all. |
| [`T108-parallax`](03-combat/turrets/T108-parallax.md) | parallax - the air puller with 16 traction | Why parallax displaces instead of kills: a 16 traction beam drags air units toward the turret (harder the closer they are), plus 30 damage/s. |
| [`T109-swarmer`](03-combat/turrets/T109-swarmer.md) | swarmer - the four-missile salvo rain | Why swarmer's four missiles from eight rotating barrels reach 309.8 listed DPS on surge-alloy but collapse to 12.6 against 22 armor. |
| [`T110-salvo`](03-combat/turrets/T110-salvo.md) | salvo - the four-round mainstay at 320 DPS | Why salvo is the mid-game standard: four graphite rounds per 29-tick cycle give 320.7 DPS and still 93.1 through 22 armor, at 2.59 items/s. |
| [`T111-segment`](03-combat/turrets/T111-segment.md) | segment - the 225-per-second projectile sweeper | Why segment never kills units: it intercepts enemy bullets at 30 damage and 7.5 shots/s, 225/s of throughput that costs 480 power/s. |
| [`T112-tsunami`](03-combat/turrets/T112-tsunami.md) | tsunami - the twin-barrel liquid sprinkler | Why tsunami is wave scaled up: twin barrels, two rounds per 3-tick trigger, about 20 triggers/s and 95 DPS on slag, for 850 items. |
| [`T113-fuse`](03-combat/turrets/T113-fuse.md) | fuse - the 540 DPS point-blank shotgun | Why fuse is the strongest late close defense: three thorium pellets per 35 ticks give 540 DPS and 426.9 through 22 armor within 11 tiles. |
| [`T114-ripple`](03-combat/turrets/T114-ripple.md) | ripple - four-round shelling beyond 290 world units | Why ripple is mid-game ground artillery: four shells per 120 ticks reach 36 tiles for 231 listed DPS, but cannot answer fast pushes or air. |
| [`T115-cyclone`](03-combat/turrets/T115-cyclone.md) | cyclone - the 415 listed-DPS anti-air core | Why cyclone anchors late anti-air at 415.5 listed DPS over 25 tiles, yet manages only 7.8 DPS against 22 armor, needing fuse or spectre backup. |
| [`T116-foreshadow`](03-combat/turrets/T116-foreshadow.md) | foreshadow - the 405-point hammer beyond 500 world units | Why foreshadow's 62.5-tile reach and 1350 direct damage keep 398.4 of 405 DPS through 22 armor, for 600 power/s and 5 items per shot. |
| [`T117-spectre`](03-combat/turrets/T117-spectre.md) | spectre - the 685 DPS endgame main gun | Why spectre is the endgame answer: 8.57 thorium rounds/s give 685.7 DPS and 497.1 through 22 armor over 32.5 tiles, at 4.29 items/s. |
| [`T118-meltdown`](03-combat/turrets/T118-meltdown.md) | meltdown - the 936 DPS burn-through laser | Why meltdown's continuous laser deals 78 every 5 ticks for 936 DPS, then averages 672.75 across its 90-tick cooldown and 1020 power/s. |
| [`T201-breach`](03-combat/turrets/T201-breach.md) | breach - 325 per shot, the densest opening gun in the game | Why breach, with carbide cutting reload to 8 ticks, reaches 2437.5 single-target DPS at 325 damage but needs 7.5 carbide/s and a 23.75-tile reach. |
| [`T202-diffuse`](03-combat/turrets/T202-diffuse.md) | diffuse - 15-projectile spread, the highest ammo draw in the library | Why diffuse sprays 15 oxide pellets for 2025 single-target DPS at 30 shots/s, but only within 15.6 tiles and at 45 items/s of ammo. |
| [`T203-sublimate`](03-combat/turrets/T203-sublimate.md) | sublimate - the liquid torch dealing 130 per damage tick | Why sublimate's continuous flame deals 60 per tick on ozone and 130 on cyanogen, which also adds 70 range and pierceCap 3 for 18 liquid/s. |
| [`T204-titan`](03-combat/turrets/T204-titan.md) | titan - a 390-world-unit siege gun that barely feels armor | Why titan's 48.75-tile carbide shells keep 96% of their damage through 22 armor, while hitting ground only at 0.54 shots/s. |
| [`T205-disperse`](03-combat/turrets/T205-disperse.md) | disperse - anti-air only, 310 world units | Why disperse is pure anti-air: four alternating barrels at 31.37 shots/s give 2117.6 DPS over 38.75 tiles, and zero output against ground. |
| [`T206-afflict`](03-combat/turrets/T206-afflict.md) | afflict - the 368-world-unit, 216 DPS armor-piercing electric gun | Why afflict's 180 piercing damage every 50 ticks gives 216 DPS over 46 tiles and ignores armor penalties, at 300 power/s and slow projectiles. |
| [`T207-lustre`](03-combat/turrets/T207-lustre.md) | lustre - the 360-degree laser that picks the toughest target | Why lustre's 360-degree cone and strongest-unit sort make it a fire-and-forget finisher, dealing 210 per tick for 200 power/s plus nitrogen. |
| [`T208-scathe`](03-combat/turrets/T208-scathe.md) | scathe - the 1350-world-unit missile rack, one shot per ten seconds | Why scathe shows zero turret DPS: its bullet only spawns a missile unit whose 1000 splash does the damage, 168.75 tiles away every 10 s. |
| [`T209-smite`](03-combat/turrets/T209-smite.md) | smite - five-barrel heavy hitter with the best 22-armor retention | Why smite's five barrels at 3 shots/s give 562.5 DPS and retain 496.5 through 22 armor, the best of Erekir's general towers, for 2200 items. |
| [`T210-malign`](03-combat/turrets/T210-malign.md) | malign - 2400 power and seventeen rounds per second at random impact points | Why malign fires 17.14 rounds/s at 70 damage plus lightning and laser fragments, covering rather than aiming, for 2400 power/s. |

### `04-units/` — 6 articles

| Article | Title | What it says |
|---|---|---|
| [`U01-movement`](04-units/U01-movement.md) | Unit types and movement: the real unit of speed, hitSize, terrain and boost | Why UnitType.speed is in world units per tick, so speed x 60 / 8 gives tiles/s, from alpha at 22.5 to corvus at 2.25 tiles/s. |
| [`U02-production`](04-units/U02-production.md) | Unit production chain: factories, reconstructors, assemblers and the unit cap | How factories, reconstructors and assemblers form three production paths, and how core unitCapModifier values sum into the unit cap. |
| [`U03-ai`](04-units/U03-ai.md) | Unit AI: controllers, target selection, commands and stances, pathfinding cost | How each AIController runs targeting, movement and weapons every tick, and how targetPriority overrides distance while class sets path cost. |
| [`U04-abilities`](04-units/U04-abilities.md) | Unit abilities: the abilities list, parameters and triggers of 16 Ability types | Why only 15 of 62 vanilla units carry the 16 Ability instances, and how each ability's timer and update(unit) callback drive it. |
| [`U05-progression`](04-units/U05-progression.md) | Unit progression: no experience or levels, only tiers, wave tables and difficulty multipliers | Why neither v159.3 nor v160.7 has unit experience or levels, and which four real mechanics produce the felt progression. |
| [`U06-name-units`](04-units/U06-name-units.md) | Unit name reference: English and Chinese names of 70 units (60 with official Simplified Chinese) | Lookup table of 70 unit English and Chinese names, 60 with official Simplified Chinese, bridging displayed names to blueprint and wave ids. |

### `06-mlog/` — 11 articles

| Article | Title | What it says |
|---|---|---|
| [`M01-执行模型总览`](06-mlog/M01-执行模型总览.md) | Execution model overview: ticks, @counter and the per-tick instruction budget | How a processor accumulates ipt x dt budget per tick, executes one instruction per point, and lets @counter select the next line. |
| [`M02-变量与作用域`](06-mlog/M02-变量与作用域.md) | Variables and scope: the number / object / null three-state model | Why every variable is a number or an object, why null is an empty object slot, and why num(null) yields 0 rather than NaN. |
| [`M03-控制流`](06-mlog/M03-控制流.md) | Control flow: jump's 8 conditions, loop idioms and the consequences of rewriting @counter | Why mlog has only jump and a writable @counter, how loops jump backward and branches forward, and what rewriting @counter breaks. |
| [`M04-读写与感知`](06-mlog/M04-读写与感知.md) | Reading, writing and sensing: read / write / sensor / radar / ulocate / getlink / lookup | The five ways mlog reads the world - sensor, radar, ulocate, getlink and lookup - plus read for memory blocks. |
| [`M05-绘制与文本`](06-mlog/M05-绘制与文本.md) | Drawing and text: draw's 16 commands, 10-bit packing and the text buffer | How draw packs arguments into 10-bit signed slots of -511..511, how print fills a 400-character buffer, and why flushes are required. |
| [`M06-世界交互`](06-mlog/M06-世界交互.md) | World interaction: control, setrule and the 26 privileged world processor instructions | Why only world processors can write rules, spawn units, place bombs and toggle buildings, listing their 26 privileged instructions. |
| [`M07-单位与逻辑控制`](06-mlog/M07-单位与逻辑控制.md) | Unit and logic control: ubind, ucontrol's 21 subcommands and the @unit lifecycle | How ubind binds a unit to @unit, why set @unit is silently dropped, and what the 21 ucontrol subcommands act on. |
| [`M08-性能与限制`](06-mlog/M08-性能与限制.md) | Performance and limits: budget, latency, lag and hard caps | Why every slowdown, lag spike and logic delay reduces to the per-tick instruction budget, tick rate or wait granularity. |
| [`M09-Mindcode`](06-mlog/M09-Mindcode.md) | Mindcode compile front end: .mnd -> mlog entry points, version arbitration and failure classification | How tools/mindcode.py finds the jar and JRE, runs cm and parses stderr into file:line:col for the CLI, Python API and MCP entries. |
| [`M10-Mindcode-Syntax`](06-mlog/M10-Mindcode-Syntax.md) | Mindcode syntax cheatsheet (measured): every rule with its compiled mlog | Measured Mindcode 3.19.3 syntax rules for target 7.0 with optimization off, each paired with the mlog it compiles to. |
| [`M11-世界指令实战样例`](06-mlog/M11-世界指令实战样例.md) | World processor examples: observed commands, arguments and caveats | Observed world-processor instructions and argument patterns from real blueprints, with version and runtime caveats. |

### `07-patterns/` — 9 articles

| Article | Title | What it says |
|---|---|---|
| [`P01-architecture`](07-patterns/P01-architecture.md) | Blueprint architecture overview: budget, layering and topology | Why architecture means fitting state size times loop frequency into the ipt x edelta budget before splitting processors, which adds communication cost. |
| [`P02-state-machine`](07-patterns/P02-state-machine.md) | State machines: enumerations, transition tables and @counter dispatch | Why prefer enumerated states with jump equal chains over @counter offset dispatch, which is O(1) but breaks on any inserted instruction. |
| [`P03-comm-bus`](07-patterns/P03-comm-bus.md) | Communication and buses: memory mailboxes, channel encoding and read/write races | Why cross-processor links are only memory cells and the shared variable space, both lock-free, so protocols need one writer plus sequence numbers. |
| [`P04-data-structures`](07-patterns/P04-data-structures.md) | Data structures: memory layout of arrays, queues, ring buffers and the canvas | Why mlog data structures are hand-addressed memory indexes chosen by instruction cost: array 1, queue 3, ring buffer 4, full canvas 4096. |
| [`P05-radar-targeting`](07-patterns/P05-radar-targeting.md) | Radar and targeting: combining filter/sort/order and range checks | Why one radar instruction filters, sorts and picks a target, and why its 30-tick cache means range must be rechecked manually. |
| [`P06-performance`](07-patterns/P06-performance.md) | Performance and robustness: budget allocation, throttling and self-recovery | Why performance work means throttling first, then rotating slices, then splitting processors, with liveness checks and bounded retries. |
| [`P07-unit-multicontrol`](07-patterns/P07-unit-multicontrol.md) | Unit multicontrol: @counter dispatch, @controller liveness checks and the hauling loop | How @counter dispatch, @controller tri-state liveness and keeping reinforcement out of the hot loop hold a loop to 3 + N x stride + 1 instructions. |
| [`P08-counter-architectures`](07-patterns/P08-counter-architectures.md) | @counter advanced architectures and name tables: dispatch, shrinking and building variable tables | How fixed-length per-object slots and computed @counter offsets shrink a loop, and how building variable tables keyed by runtime type names store objects. |
| [`P09-code-examples`](07-patterns/P09-code-examples.md) | Finished logic code library: multicontrol hauling, multicontrol mining, row tables and landing pad scheduling | Six paste-ready programs (two hauling, mining, name row table, two landing-pad dispatchers) on fixed slots, relative dispatch and 2 s reinforcement bursts. |
