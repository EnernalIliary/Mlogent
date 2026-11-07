# 00-data — v160.7 机器可读事实表

由 `tools/extract_rt.py` 从 **v160.7 真服务器 jar 反射**生成（`out/_server160.jar` + jre21 headless），**禁止手改**。

重跑：`python -u kb-stage/tools/extract_rt.py`（起服务器 2–8s，全量 5–40s，本机本次 5.9s）。

| 文件 | 条数 | 体积 | 抽取源 |
|---|---|---|---|
| `blocks.json` | 447 | 346KB | Vars.content.blocks() 全量（447） |
| `turrets.json` | 31 | 37KB | 类继承链含 *Turret 的方块（31 条；与 blocks.json 中 types 含 turret 的条数一致） |
| `bullets.json` | 137 | 148KB | 炮塔 ammoTypes + 单位 weapons 的 BulletType（IdentityHashMap 去重） |
| `units.json` | 70 | 133KB | Vars.content.units() 全量（70） |
| `items.json` | 22 | 7KB | Vars.content.items() 全量（22） |
| `liquids.json` | 11 | 4KB | Vars.content.liquids() 全量（11） |
| `status.json` | 23 | 13KB | Vars.content.statusEffects() 全量（23） |
| `rules.json` | 118 | 16KB | Vars.state.rules 全部 public 实例字段 + new Rules() 默认值 |

## 通用约定（所有表）

- 每条记录必带：`id`（游戏内 id，kebab-case，等于 name 字段）、`name`（英文名；单位/物品/液体/状态取 localizedName en）、`src`（`jar:v160.7#<Java 类全名>`，类名里的 `$<n>` 是匿名内部类）、`ver`（固定 `v160.7`）。
- **浮点统一 4 位小数**（jar 里 float 2.700000047683716 记为 2.7）。

### 单位口径（jar 原值 → 游戏单位；换算规则引自 v159.3 源码树 = 语义权威）

| 量 | 表内字段 | jar 单位 | 换算 | 源码依据 |
|---|---|---|---|---|
| 世界单位 | — | 1 tile = **8** world units | tiles = v / 8 | `core/src/mindustry/Vars.java:135`（tilesize = 8） |
| 时间/进度 | reload, lifetime, craftTime, drillTime, statusDuration | **ticks** | 秒 = v / 60 | `core/src/mindustry/world/blocks/defense/turrets/Turret.java:183` |
| 功率 | usage, production, capacity | **power/tick** | /s = v × 60 | `ConsumePower.usage` 由电网每 tick 结算 |
| 炮塔射程 | blocks/turrets 的 range | world units | tiles = range / 8 | `core/src/mindustry/world/blocks/defense/turrets/Turret.java:421`（range() = (range+…) / tilesize） |
| 弹体速度 | bullet speed | **world units/tick** | tiles/s = v × 60 / 8 | `core/src/mindustry/entities/bullet/BulletType.java:439`（range() = speed × lifetime） |
| 弹体射程 | bullet range | world units | tiles = range / 8 | 同上 |
| 单位速度 | unit speed | **world units/tick** | tiles/s = v × 60 / 8 | `core/src/mindustry/type/UnitType.java:791,1441`（speed*60f/tilesize） |
| 单位射程 | unit range / maxRange | world units | tiles = v / 8 | `core/src/mindustry/type/UnitType.java:794` |
| 单位体积 | hitSize | world units | blocks = v / 8 | `core/src/mindustry/type/UnitType.java:792` |

校验样例：duo range=160 → 20 tiles；duo-copper bullet speed=2.5 × lifetime=70 → 175 units → 21.9 tiles；dagger speed=0.5 → 3.75 tiles/s、maxRange=146 → 18.25 tiles、hitSize=8 → 1 tile。

- `itemCapacity` 是件数；`liquidCapacity` 是液体单位原值（不换算）。
- 除按类型白名单强制补齐的字段外，值为 `null` 的键**省略**；白名单内的键**一定存在**，取不到就是 `null`（下游可直接 `rec["craftTime"]` 不判键存在）。

## blocks.json

### 稳定契约字段（447 条全部有）

`category`、size（格）、health、armor、`requirements[].{item,amount}`、`consumers[]`、hasPower/hasItems/hasLiquids、rotate/solid/underBullets、itemCapacity/liquidCapacity、buildVisibility/group/privileged/inEditor/placeablePlayer/alwaysReplace/rebuildable/unitCapModifier、buildTime（ticks）、buildCostMultiplier、`types[]`（本表类型标签，255/447 条有；墙/植被/岩石/装饰等 192 条无可分类类型，因而没有类型字段）、`ammo[]`（仅炮塔：`{item,bullet}`，bullet 指向 bullets.json 的 id）。

`consumers[]`：`{cls,...}`。**ConsumePower 必带 `usage`（power/tick）与 `usagePerSecond`（/s）**；ConsumeItems/ConsumeLiquid 带 `items[]/liquids[]` 栈。

### power 对象（hasPower 或发电机/电池才出现）

`power = {usage, usagePerSecond, capacity, buffered, production}`，全部 5 个键**必定存在**（无值 `null`）。`usage` 单位 power/tick，capacity 是电池储能（battery=`capacity:4000, buffered:true`），production 单位 power/tick。

### 类型特有字段白名单（按 `types[]` 强制补齐，无值为 null）

| type | 字段（v160.7 真实字段名） |
|---|---|
| turret | range, minRange, reload, maxAmmo, ammoPerShot, clipSize, shootCone, inaccuracy, rotateSpeed, targetAir, targetGround, targetBlocks, coolantMultiplier, ammoEjectBack, recoil, recoilTime, shootWarmupSpeed, minWarmup, velocityRnd, reloadWhileCharging, ammoItems |
| drill | drillTime, tier, hardnessDrillMultiplier, liquidBoostIntensity, blockedItem, warmupSpeed |
| crafter | craftTime, dumpTime, warmupSpeed, ignoreLiquidFullness, dumpExtraLiquid, outputs, outputLiquids |
| separator | craftTime, dumpTime, results |
| conveyor | speed, displayedSpeed, pushUnits, isDuct |
| generator | powerProduction, explosionRadius, explosionDamage |
| battery | powerCapacity |
| heat | heatOutput, warmupSpeed, craftTime |
| liquid | liquidPadding, liquidPressure, outputsLiquid |
| storage | coreMerge |
| wall | chanceDeflect, flashHit |
| floor | isLiquid, shallow, speedMultiplier, dragMultiplier, damageTaken, drownTime, status, liquidDrop |
| ore | itemDrop |

取值来自 jar 同名字段；`outputs`=`outputItems[]`、`outputLiquids`=`outputLiquids[]`、`results`（Separator 的产出池）、`ammoItems`（炮塔接受的弹药物品名）。反射恒为 `null` 的字段：`ignoreLiquidFullness`（v160 已并入其它机制）、`powerCapacity`（v160 电池没有该字段，储能看 `power.capacity`）；`displayedSpeed` 只在传送带上可读（conveyor=8、titanium-conveyor=10），其他类型为 null。
**白名单是并集**：记录里没有该字段就是 `null`（如 parallax 无 reload）；v160.7 炮塔基类是 `BaseTurret`，parallax / segment / repair-point / repair-turret / build-tower 不在 `Turret` 分支下但仍归 `turret` 类型。

**best-effort 字段**（反射不保证）：`status/liquidDrop/blockedItem/itemDrop`（枚举/内容引用，取不到即省略）、floor/wall 类附加字段。

## turrets.json

**31 条**（= blocks.json 中 `types` 含 `turret` 的条数）。`kind` 取值：`item`（弹药炮塔，ammo[] 非空）、`liquid`（液体炮塔）、`power/laser/continuous/continuousliquid`（能量类，耗能看 power.usage）、`tractorbeam`（parallax）、`pointdefense`（segment）、`build`（build-tower）、`repair`（repair-point、repair-turret，无射程无 reload 循环）。`turretClass` 是命中的继承链类简名（如 `defense.turrets.ItemTurret`）。

字段：range（world units，÷8=tiles）、minRange、reload（ticks）、maxAmmo、ammoPerShot、clipSize、`shootCone`（度）、inaccuracy（度）、rotateSpeed（度/tick）、targetAir/targetGround/targetBlocks、coolantMultiplier、ammoEjectBack、recoil、recoilTime、shootWarmupSpeed、minWarmup、velocityRnd、reloadWhileCharging、consumeAmmoOnce、displayAmmoMultiplier、buildTime、power{...}（同上）。

`ammo[]` 每个接受的弹药物品一条：`{item, bullet, name, damage, speed, lifetime, range, ammoMultiplier, reloadMultiplier, status, statusDuration}`；`bullet` 是 bullets.json 的主键，`name` 是人读别名（如 `duo-copper`）。`range` 由 speed*lifetime 派生时带 `rangeDerived:true`。

## bullets.json

137 条（identity 去重）。`id = b<identityHashCode>` 是**同一次 run 内**的稳定主键（跨 run 不稳定，不要跨 run 比对）；`alias` = `<owner>-<弹药物品|weaponN>`，`owner/ownerType/owners[]` 记录所有引用者（炮塔弹药或单位武器），`name` 有 owner 时等于 alias，否则为 Java 匿名类简名。

字段：damage/speed（world units/tick，×60÷8 = tiles/s）/lifetime（ticks）/drag/pierce/pierceCap/splashDamage/splashDamageRadius/splashDamagePierce/lightning/lightningDamage/lightningLength/fragBullets/fragAngle/fragVelocityMin/fragVelocityMax/width/height/hitSize/ammoMultiplier/reloadMultiplier/status/statusDuration/collides/collidesAir/collidesGround/absorbable/hittable/keepVelocity/range/hitShake/hitUnder/knockback/reflectable/laserAbsorb/pierceArmor/buildingDamageMultiplier/intervalBullets/intervalBulletInterval。

## units.json

70 条。health/armor/speed（world units/tick，×60÷8 = tiles/s）/flying/naval/legCount/hitSize（÷8 = blocks）/range、maxRange（÷8 = tiles）/itemCapacity/buildSpeed/mineSpeed/mineTier/mineRange/buildRange/canBoost/boostMultiplier/useUnitCap/targetPriority/targetAir/targetGround/targetBlocks/drag/accel/rotateSpeed/payloadCapacity/engineSize/engineOffset/researchCostMultiplier/ammoCapacity/clipSize 等。

- `weapons[]` = `{name, bullet, bulletName, reload, x, y, inaccuracy, shootCone, alternate, mirror, ...}`，bullet 指向 bullets.json id，bulletName 是可读别名。
- `abilities[]` = `{cls, <该 Ability 子类 public 标量字段>}`。
- `immunities[]` = 状态名数组（`java.util.Set<StatusEffect>` 反射）。
- `legs` 是**派生**字段（`legCount > 0`），带 `legsDerived:true`：v160.7 的 UnitType 没有 `legs` 布尔字段，别当原始值用；爬行类用 `legCount>0 && !flying && !naval` 判断更准。
- v160.7 没有 `isCounted` 字段，单位上限吃掉与否用 `useUnitCap`。

## liquids.json / items.json / status.json

liquids（11）：viscosity/heatCapacity/temperature/flammability/explosiveness/coolant/gas/boilPoint/incinerable/blockReactive/canStayOn/particleSpacing/effectCls/colorHex；`effect` 与 `effectCls` 同值（Effect 类全名，不是实例摘要）。

items（22）：hardness/cost/flammability/explosiveness/radioactivity/charge/lowPriority/color（ARGB int）/colorHex/healthScaling/hidden/alwaysUnlocked/buildable。

status（23）：damageMultiplier/healthMultiplier/speedMultiplier/reloadMultiplier/buildSpeedMultiplier/dragMultiplier/disarm/transitionDamage/`intervalDamage/intervalDamageTime/intervalDamagePierce`/reactive/effect/effectChance/permanent/show/hidden/opposites[]/affinities[]/color。

**注意**：v160.7 的 StatusEffect 没有 `category/duration/interval` 字段（本文档旧版按 v159 写的），持续伤害改由 `intervalDamage*` 描述。`opposites/affinities` 是 `arc.struct.ObjectSet`（只有 `size` 和 `each(Cons)` 可用，Rhino 里用 `JavaAdapter` 实现 `Cons` 回调收集），元素都是 StatusEffect：opposites 只记名字，affinities 记 `状态名+damage`（权重读 StatusEffect 的 `damage` 字段），均已排序便于 diff；实测 `burning` opposites=[freezing,wet]、affinities=[tarred+0]，`tarred` affinities=[burning+0.167, melting+0.3]。

## rules.json

118 条 = `mindustry.game.Rules` 全部 public 实例字段（一个字段一条，不是一份 rules 对象）。`name/type/value/default`：`value` 是 headless 服务器 `Vars.state.rules` 的运行值，`default` 是 `new Rules()` 的默认值。**只记字段与值，语义解释交给 05-campaign / 07-rules 各篇。**

标量覆盖 `value 92/118`、`default 93/118`；其余 26 个是对象/集合/默认 null 字段（`teams`、`attributes`、`spawns/loadout/weather/ambientMusic/darkMusic`（Seq）、`bannedBlocks/bannedUnits/revealedBlocks/researched/objectiveFlags`（ObjectSet）、`blockLimits`、`objectives`、`tags`、staticColor/dynamicColor/ambientLight/cloudColor`、4 个字符串（modeName/mission/customBackgroundCallback/backgroundTexture）、`planet/planetBackground/sector`），本表只留 `type` 不展开；要具体值查存档或 05-campaign。

## 怎么联合查（示例）

查一个炮塔的完整画像（blocks.json 白名单字段 + turrets.json 弹药映射 + bullets.json 弹体）：

```python
import json
D = 'kb-stage/00-data/'
blocks = {b['id']: b for b in json.load(open(D + 'blocks.json', encoding='utf-8'))}
turrets = {t['id']: t for t in json.load(open(D + 'turrets.json', encoding='utf-8'))}
bullets = {b['id']: b for b in json.load(open(D + 'bullets.json', encoding='utf-8'))}
b, t = blocks['duo'], turrets['duo']
print(b['category'], b['size'], b['health'], b['range'] / 8, 'tiles', b['reload'], 'ticks', b['power'])   # blocks.json 已有炮塔字段
for a in t['ammo']:
    print(a['item'], bullets[a['bullet']]['damage'], bullets[a['bullet']]['speed'] * 60 / 8, 'tiles/s')
```

按类型筛 blocks：`[b for b in blocks if 'crafter' in b['types']]`；查制造时间：`blocks['graphite-press']['craftTime']`（ticks，÷60 秒）。

## 条数与覆盖率

精确条数：blocks=447, turrets=31, bullets=137, units=70, items=22, liquids=11, status=23, rules=118。

| 表 | 字段 | 有值/总数 |
|---|---|---|
| blocks | category | 447/447 |
| blocks | size | 447/447 |
| blocks | health | 447/447 |
| blocks | armor | 447/447 |
| blocks | requirements | 245/447 |
| blocks | consumers | 145/447 |
| blocks | hasPower | 447/447 |
| blocks | hasItems | 447/447 |
| blocks | hasLiquids | 447/447 |
| blocks | rotate | 447/447 |
| blocks | solid | 447/447 |
| blocks | underBullets | 447/447 |
| blocks | itemCapacity | 447/447 |
| blocks | liquidCapacity | 447/447 |
| blocks | buildVisibility | 447/447 |
| blocks | group | 447/447 |
| blocks | privileged | 447/447 |
| blocks | inEditor | 447/447 |
| blocks | placeablePlayer | 447/447 |
| blocks | alwaysReplace | 447/447 |
| blocks | rebuildable | 447/447 |
| blocks | unitCapModifier | 447/447 |
| blocks | buildTime | 447/447 |
| blocks | power | 121/447 |
| turrets | range | 29/31 |
| turrets | reload | 27/31 |
| turrets | maxAmmo | 26/31 |
| turrets | ammo | 17/31 |
| turrets | targetAir | 27/31 |
| turrets | targetGround | 27/31 |
| turrets | shootCone | 28/31 |
| turrets | inaccuracy | 26/31 |
| turrets | rotateSpeed | 29/31 |
| turrets | coolantMultiplier | 31/31 |
| turrets | ammoEjectBack | 26/31 |
| turrets | minRange | 26/31 |
| turrets | ammoPerShot | 26/31 |
| turrets | clipSize | 31/31 |
| turrets | recoil | 26/31 |
| turrets | shootWarmupSpeed | 26/31 |
| turrets | power | 12/31 |
| bullets | damage | 137/137 |
| bullets | speed | 137/137 |
| bullets | lifetime | 134/137 |
| bullets | drag | 137/137 |
| bullets | pierce | 137/137 |
| bullets | pierceCap | 137/137 |
| bullets | splashDamage | 137/137 |
| bullets | splashDamageRadius | 137/137 |
| bullets | lightning | 137/137 |
| bullets | lightningDamage | 137/137 |
| bullets | fragBullets | 137/137 |
| bullets | width | 104/137 |
| bullets | height | 90/137 |
| bullets | hitSize | 137/137 |
| bullets | ammoMultiplier | 137/137 |
| bullets | reloadMultiplier | 137/137 |
| bullets | status | 137/137 |
| bullets | statusDuration | 137/137 |
| bullets | collidesAir | 137/137 |
| bullets | collidesGround | 137/137 |
| bullets | absorbable | 137/137 |
| bullets | hittable | 137/137 |
| bullets | keepVelocity | 137/137 |
| bullets | range | 137/137 |
| bullets | owner | 137/137 |
| bullets | alias | 137/137 |
| units | health | 70/70 |
| units | armor | 70/70 |
| units | speed | 70/70 |
| units | flying | 70/70 |
| units | naval | 70/70 |
| units | legCount | 70/70 |
| units | legs | 70/70 |
| units | hitSize | 70/70 |
| units | range | 70/70 |
| units | maxRange | 70/70 |
| units | itemCapacity | 70/70 |
| units | buildSpeed | 70/70 |
| units | mineSpeed | 70/70 |
| units | mineTier | 70/70 |
| units | buildRange | 70/70 |
| units | canBoost | 70/70 |
| units | boostMultiplier | 70/70 |
| units | useUnitCap | 70/70 |
| units | targetPriority | 70/70 |
| units | abilities | 70/70 |
| units | immunities | 70/70 |
| units | weapons | 70/70 |
| liquids | viscosity | 11/11 |
| liquids | heatCapacity | 11/11 |
| liquids | temperature | 11/11 |
| liquids | flammability | 11/11 |
| liquids | explosiveness | 11/11 |
| liquids | coolant | 11/11 |
| liquids | effect | 11/11 |
| liquids | gas | 11/11 |
| liquids | boilPoint | 11/11 |
| liquids | incinerable | 11/11 |
| liquids | blockReactive | 11/11 |
| items | hardness | 22/22 |
| items | cost | 22/22 |
| items | flammability | 22/22 |
| items | explosiveness | 22/22 |
| items | radioactivity | 22/22 |
| items | charge | 22/22 |
| items | lowPriority | 22/22 |
| items | color | 22/22 |
| status | damageMultiplier | 23/23 |
| status | healthMultiplier | 22/23 |
| status | speedMultiplier | 23/23 |
| status | reloadMultiplier | 23/23 |
| status | buildSpeedMultiplier | 23/23 |
| status | dragMultiplier | 23/23 |
| status | disarm | 23/23 |
| status | transitionDamage | 23/23 |
| status | intervalDamage | 23/23 |
| status | intervalDamageTime | 23/23 |
| status | reactive | 23/23 |
| status | effect | 23/23 |
| status | opposites | 6/23 |
| status | affinities | 7/23 |
| rules | value | 92/118 |
| rules | default | 93/118 |

rules 的 value/default 不到 118/118 的原因：26 个对象/集合型字段默认 null，只记 type，见 rules.json 一节。

blocks 的 `types` 覆盖 255/447；其余 192 条是静态墙（stone-wall 等）、植被、岩石、装饰方块，v160.7 里没有对应的可分类字段，它们仍有“稳定契约字段”那一段的全部字段。`ammo` 只出现在炮塔（`types` 含 `turret`）。

### blocks.json 各类型白名单覆盖率（该类型条数内）

| type | 条数 | 字段: 有值/条数 |
|---|---|---|
| turret | 31 | range 29/31; minRange 26/31; reload 27/31; maxAmmo 26/31; ammoPerShot 26/31; clipSize 31/31; shootCone 28/31; inaccuracy 26/31; rotateSpeed 29/31; targetAir 27/31; targetGround 27/31; targetBlocks 26/31; coolantMultiplier 31/31; ammoEjectBack 26/31; recoil 26/31; recoilTime 26/31; shootWarmupSpeed 26/31; minWarmup 26/31; velocityRnd 26/31; reloadWhileCharging 26/31; ammoItems 17/31 |
| drill | 6 | drillTime 6/6; tier 6/6; hardnessDrillMultiplier 6/6; liquidBoostIntensity 6/6; blockedItem 1/6; warmupSpeed 6/6 |
| crafter | 31 | craftTime 31/31; dumpTime 31/31; warmupSpeed 31/31; ignoreLiquidFullness 31/31; dumpExtraLiquid 31/31; outputs 19/31; outputLiquids 8/31 |
| separator | 2 | craftTime 2/2; dumpTime 2/2; results 2/2 |
| conveyor | 5 | speed 5/5; displayedSpeed 3/5; pushUnits 3/5; isDuct 5/5 |
| generator | 14 | powerProduction 14/14; explosionRadius 14/14; explosionDamage 14/14 |
| battery | 2 | powerCapacity 0/2 |
| heat | 8 | heatOutput 8/8; warmupSpeed 7/8; craftTime 6/8 |
| liquid | 18 | liquidPadding 6/18; liquidPressure 18/18; outputsLiquid 18/18 |
| storage | 10 | coreMerge 10/10 |
| wall | 29 | chanceDeflect 29/29; flashHit 29/29 |
| floor | 107 | isLiquid 107/107; shallow 107/107; speedMultiplier 107/107; dragMultiplier 107/107; damageTaken 107/107; drownTime 107/107; status 107/107; liquidDrop 11/107 |
| ore | 13 | itemDrop 13/13 |

## 已知边界

- jar 反射给的是**代码里的基础值**，不等于运行时生效值（range 会被超速/冷却液/加成改变，craftTime 会被超速改变）。
- bullets.json 的 id 是 identity hash，**只在本 run 内有效**；不要写进文章，文章引用 `alias`（如 `duo-copper`）。
- rules.json 的 value 来自 headless 服务端默认 state，不是某个存档的规则。
- v160.x 新增内容在 v159.3 源码树里没有：本表不回填源码行号；类层次差异（如 `BaseTurret` 层）以 jar 反射为准，语义/S 级证据见 01–08 各篇。
- 反射只覆盖 public 字段 + public 无参 getter 不在此列：private/protected 字段（如部分内部计时器）不在表内。

## 生成命令

```
python -u kb-stage/tools/extract_rt.py            # 生成全部表 + 本 README
python -u kb-stage/tools/extract_rt.py --out DIR  # 指定输出目录
```

生成时间：2026-11-08 04:40:06　用时：5.9s
