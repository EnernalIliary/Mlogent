---
id: UNIT.MOVE.001
title: 单位类型与移动——speed 的真实单位、hitSize、地形与 boost
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/type/UnitType.java:55-110,116-129,177,203-245,540-541,892-903,924-927"
  - "Mindustry-Source/core/src/mindustry/content/UnitTypes.java:357-916,1042-1550"
  - "MBO/gamedata/v160.7/units_production.json（70 单位 health/flying/hitSize）"
data: [00-data/units.json]
depends: [COMBAT.ARMOR.001]
tags: [单位, 移动, speed, hitSize, boost, 地形, 飞行, 海军]
tokens: 797
---

## 一句话

`UnitType.speed` 的单位是 **world units/tick（px/刻）**，不是 tiles/s——`speed × 60 ÷ 8 = tiles/s`；所以 dagger 的 `0.5` 等于 **3.75 格/秒**，flare 的 `2.7` 等于 **20.25 格/秒**，全表最快的是 alpha（22.5 格/秒）、最慢的是 corvus（2.25 格/秒）。

## 规则 / 公式

### 1. speed 的单位（最容易错的一条）

```
UnitType.speed  单位: world units per tick（1 格 = tilesize = 8 px）
tiles/s = speed × 60 / 8 = speed × 7.5
px/s    = speed × 60
```

源码注释写得很明确：`/** movement speed (world units/t) */`（UnitType.java:55）。

移动还有三层修正：

```
实际速度 = speed × boostMultiplier(若 boost) × floorMultiplier(地形) × 转向/加速度影响
```

- `drag = 0.3`：每 tick 速度按比例衰减，形成"松手滑行"；
- `accel = 0.5`：加速度占 speed 的比例；
- `rotateSpeed = 5`（度/tick）：机体转向速度，影响贴脸绕圈；
- `strafePenalty = 0.5`：朝反方向移动时的速度惩罚。

### 2. 运动类型（由 class 决定，不是手写字段）

| 类型 | 实现 | 代表单位 | 关键字段 |
|---|---|---|---|
| 飞行 | `flying = true` | flare / horizon / zenith / eclipse | `lowAltitude`、`riseSpeed 0.08`、`descentSpeed 0.08` |
| 履带 | 默认地面 | dagger / fortress / reign | `drag`、`accel` |
| 机甲腿 | `legCount`（MechComp/LegsComp） | atrax 4 / spiroct 6 / toxopid 8 | `legCount`、`stepShake`、`rippleScale` |
| 海军 | `naval`（init 里 `naval = true; canDrown = false; omniMovement = false`） | risso / minke / omura | 只能在水上，寻路用 `Pathfinder.costNaval` |
| 悬浮 | `hovering = true` | 蜘蛛类可越地形 | 不受地形减速，但会被 `muddy` 类状态影响 |

注意 `naval` 字段注释：`/** if true, this unit is detected as naval - do NOT assign this manually! Initialized in init() */`（UnitType.java:244-245）——它由 class（`UnitWaterMove`）反推，不是手配。

### 3. hitSize

```
/** size of one side of the hitbox square */   // UnitType.java:69-70
该值同时决定：碰撞体尺寸、寻路可通行宽度、被子弹命中的难易
```

- 小：dagger 8、nova 8、flare 9；
- 中：risso 10、minke 13、toxopid 26；
- 大：reign 30、conquer 46、eclipse 58。

### 4. 地形与出界

- `floorMultiplier = 1`：该单位受地形速度影响的程度（1 = 完全受影响）。
- `canDrown = true`：进入深水会淹死，`drownTimeMultiplier` 越大淹得越慢。
- `envDisabled = Env.scorching`：在"烧灼"环境里会爆炸/失效；`envRequired`/`envEnabled` 决定能否工作。
- 水体减速：水面 `floor.speedMultiplier` 更低，海军用 `UnderwaterMoveComp/WaterMoveComp` 替代。

### 5. boost

```
canBoost = true → 飞行/机甲可按下"加速"，速度 × boostMultiplier
```

原版 `canBoost` 单位与倍率：nova 1.5、pulsar 1.6、quasar 2.0、vela 2.4（另有多处 `canBoost = true` 的 boost 单位）。boost 通常伴随更高的耗电/耗液或需要 `boost` 键。

## 数值

### 移动速度总表（speed 原值 → 格/秒）

| 单位 | speed(px/t) | 格/秒 | hitSize | 类型 | hp / armor |
|---|---|---|---|---|---|
| alpha | 3.0 | **22.5** | 8 | 飞行 | 150 / 0 |
| gamma | 3.55 | **26.6** | 11 | 飞行 | 220 / 0 |
| flare | 2.7 | 20.25 | 9 | 飞行 | 70 / 0 |
| poly | 2.6 | 19.5 | 9 | 飞行 | 400 / 0 |
| mega | 2.5 | 18.75 | 16.05 | 飞行 | 460 / 3 |
| zenith | 1.7 | 12.75 | 20 | 飞行 | 700 / 5 |
| horizon | 1.65 | 12.4 | 11 | 飞行 | 340 / 3 |
| mono | 1.5 | 11.25 | 0 | 飞行 | 100 / 0 |
| quad | 1.2 | 9.0 | 36 | 飞行 | 6000 / 10 |
| risso | 1.1 | 8.25 | 10 | 海军 | 280 / 2 |
| crawler | 1.0 | 7.5 | 8 | 地面 | 150 / 0 |
| dagger | 0.5 | 3.75 | 8 | 地面 | 150 / 0 |
| toxopid | 0.5 | 3.75 | 26 | 蜘蛛(8 腿) | 22000 / **22** |
| omura | 0.62 | 4.65 | 58 | 海军 | 22000 / 16 |
| eclipse | 0.54 | 4.05 | 58 | 飞行 | 22000 / **22** |
| reign | 0.4 | 3.0 | 30 | 地面 | 24000 / **30** |
| corvus | 0.3 | **2.25** | 29 | 蜘蛛(4 腿) | 18000 / **14** |

极值差：alpha 22.5 vs corvus 2.25 = **10 倍**。同样横穿 100 格地图，alpha 约 4.4 s，corvus 约 44 s。

### 腿数分布（v159.3 UnitTypes.java）

| legCount | 单位 |
|---|---|
| 4 | atrax、merui、cleroi、corvus |
| 6 | spiroct、arkyid、merui(部分)、tecta、anthicus |
| 8 | toxopid、collaris |

## 源码锚点

- `UnitType.java:55-56`：`/** movement speed (world units/t) */ public float speed = 1.1f`
- `UnitType.java:57-110`：`boostMultiplier=1f`、`floorMultiplier=1f`、`rotateSpeed=5f`、`drag=0.3f`、`accel=0.5f`、`hitSize=6f`、`riseSpeed=0.08f`、`descentSpeed=0.08f`、`fallSpeed=0.018f`、`wreckHealthMultiplier=0.25f`、`drownTimeMultiplier=1f`、`strafePenalty=0.5f`。
- `UnitType.java:177` `canBoost = false`；`:203` `canDrown = true`；`:205` `useUnitCap = true`；`:213` `lowAltitude = false`；`:221` `hovering = false`；`:223` `omniMovement = true`。
- `UnitType.java:244-245` naval 由 init 反推；`:924-927` `naval = true; canDrown = false; omniMovement = false;`。
- `UnitType.java:892-903`：按类型选 `Pathfinder.costNaval / costHover / costGround`。
- `UnitTypes.java:357/388/447`、`:503-508` 等：`canBoost = true` / `lowAltitude = true` 的赋值点。
- `UnitType.java:540-541`：`naval` → databaseTag `"unit-naval"`。

## 实测与反例

**反例 1：把 speed 当"格/秒"。**
dagger `0.5` 若当格/秒，穿越 100 格要 200 s；实际是 3.75 格/秒 → **26.7 s**。差 7.5 倍（正好是 60/8）。这是本知识库最容易犯的换算错误。

**反例 2：以为 hitSize 只是"体型画多大"。**
它同时是碰撞方块边长：hitSize 58 的 eclipse 比 hitSize 8 的 dagger 大 7.25 倍，被命中面积大 52 倍，且无法穿过 1 格缝隙。

**反例 3：以为飞行单位不受地形影响。**
`floorMultiplier` 默认 1，飞过 `muddy`/`tarred` 地面同样吃 `speedMultiplier` 惩罚（status 也照上，见 [[COMBAT.STATUS.001]]）。

**反例 4：以为海军可以上岸。**
`naval` 由 class 决定且 `canDrown = false`——水陆两栖在原版不存在（`UnitWaterMove` 只认水面）。

**可复算**：flare speed 2.7 → `2.7 × 60 = 162 px/s`，地图 264×264 格 = 2112 px，横穿 `2112/162 ≈ 13.0 s`。boost 后（如 vela ×2.4）：`0.44×2.4 = 1.056 px/t = 63.4 px/s`。

## 常见误解

- ❌ "speed 越大机动性越好"。→ drag/accel/rotateSpeed 决定手感；corvus drag 高、转向慢，实际比 speed 数字更笨重。
- ❌ "hovering 等于飞行"。→ hovering 仍需贴地（`isGrounded()` 为真，会吃地形 status），飞行则不贴地且不受地面 status。
- ❌ "unit 的 speed 会随等级涨"。→ 无等级系统（见 [[UNIT.PROGRESSION.001]]）。
- ❌ "hitSize 可以直接当半径用"。→ 它是**方形边长**。
- ❌ "v160.7 单位数值全变了"。→ 70 个单位 health 仅 nova 120→200 变化，其余一致。

## 相关

- [[UNIT.PRODUCE.001]] 怎么把这些单位造出来
- [[UNIT.AI.001]] 移动由哪些 AI 接管
- [[UNIT.ABILITY.001]] boost 与护盾类能力
- [[COMBAT.UNITWEAPON.001]] 同一批单位的武器
