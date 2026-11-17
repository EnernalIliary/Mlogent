---
id: EV.CHEAT.001
title: AI 速查卡——40 条反直觉陷阱、30 个高频数字、20 条路由
domain: evidence
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src: Mindustry-Source/core/src/mindustry/logic/LVar.java:56-58; Mindustry-Source/core/src/mindustry/logic/LExecutor.java:46,352,377,491-510,763,111-121,1218-1232,1508-1537; Mindustry-Source/core/src/mindustry/logic/LAssembler.java:25-30; Mindustry-Source/core/src/mindustry/logic/LParser.java:185; Mindustry-Source/core/src/mindustry/logic/ConditionOp.java:6-13,31-40; Mindustry-Source/core/src/mindustry/logic/TileLayer.java:3-9; Mindustry-Source/core/src/mindustry/logic/LogicBlock.java:379,424-425,564-579; Mindustry-Source/core/src/mindustry/world/blocks/logic/MemoryBlock.java:64-81; Mindustry-Source/core/src/mindustry/core/GlobalVars.java:190-199; Mindustry-Source/core/src/mindustry/core/World.java:165-176; Mindustry-Source/core/src/mindustry/core/Logic.java:272; Mindustry-Source/core/src/mindustry/content/Blocks.java:3138,3150,3163,6846-6869,6949-6969; Mindustry-Source/core/src/mindustry/content/Planets.java:133; Mindustry-Source/core/src/mindustry/type/Planet.java:98-99; Mindustry-Source/core/src/mindustry/game/Units.java:119-125; Mindustry-Source/core/src/mindustry/game/Waves.java:299,323-339; Mindustry-Source/core/src/mindustry/entities/Damage.java:659-661; Mindustry-Source/core/src/mindustry/world/blocks/LogicDisplay.java:286-288; Vars.java:109,127,129,131,133
data: [00-data/blocks.json, 00-data/units.json, 00-data/rules.json, 06-mlog/instructions.json#instructions, 08-evidence/claims.jsonl]
depends: [EXEC.TRAP.001, COMBAT.NUMBERS.001, CAMP.RULES.001]
tags: [速查卡, 陷阱, 数字表, 路由, 口径, 第一锚点]
tokens: 1893
---

## 一句话

一张卡解决三件事：**四十条反直觉陷阱（错误直觉 → 正确结论）**、**三十个高频数字（每条带锚点）**、**二十条「问 X 查哪」路由**；口径固定为数值取 v160.7 jar、语义取 v159.3 源码、冲突并列 [ver v160.7_rt / v159.3_src]。

## 规则/公式

### A. 40 条最容易答错的陷阱（错误直觉 → 正确结论）

1. 「sensor 读到的 x/y 就是格子坐标」→ 是世界像素，÷8 才是 tile；getblock/setblock/ulocate 吃 tile [src: Mindustry-Source/core/src/mindustry/core/World.java:165-176]
2. 「equal x 0 能判空」→ 只有 equal x null 判空；num() 把 null 读成 0 [src: Mindustry-Source/core/src/mindustry/logic/LVar.java:56-58]
3. 「radar 第 6 槽放数量」→ 第 6 槽是排序方向（±1/0），radar 只输出 1 个结果 [src: Mindustry-Source/core/src/mindustry/logic/LStatements.java:1171-1186]
4. 「uradar 第 5 槽能按建筑过滤」→ 死槽，源码传 null、buildFrom()=false [src: Mindustry-Source/core/src/mindustry/logic/LStatements.java:1171-1186]
5. 「getblock 先写坐标」→ 文本序是 getblock (layer) (result) (x) (y)，layer 在 0 号槽 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1508-1537]
6. 「op select 能二选一」→ v160.7 静默换成 noop，不写结果、指令下标不变 [实测: docs/断言表.md L1-25]
7. 「读 @velX / @velY」→ 是 @velocityX / @velocityY，前者得 null [实测: docs/断言表.md L2-24]
8. 「set @ipt 10 能提速」→ 静默丢弃（putConst），提速只能用 setrate [src: Mindustry-Source/core/src/mindustry/logic/LAssembler.java:25-30]
9. 「set @unit u 能换单位」→ 静默丢弃，只能用 ubind [src: Mindustry-Source/core/src/mindustry/logic/LAssembler.java:25-30]
10. 「wait 1 就是 1 tick」→ 参数单位是秒，wait 1 = 60 tick [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1218-1232]
11. 「wait 0 能延迟一帧」→ 只让出本 tick 且不扣预算，最小延迟写 wait 0.0166 [实测: docs/断言表.md L1-30]
12. 「@time 是 tick 数」→ 是毫秒；@second=tick/60、@minute=tick/3600 [src: Mindustry-Source/core/src/mindustry/core/GlobalVars.java:190-199]
13. 「改 @counter 立刻生效」→ 当前指令必执行完，跳转在下一条（先取后加）[src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:111-121]
14. 「每条指令都吃预算」→ yield 分支在 accumulator-- 之前 break，wait/stop 不扣点 [src: Mindustry-Source/core/src/mindustry/logic/LogicBlock.java:564-579]
15. 「预算每 tick 清零」→ 跨 tick 累积池，上限 5×ipt，超出削顶丢弃 [src: Mindustry-Source/core/src/mindustry/logic/LogicBlock.java:564-579]
16. 「ipt 是每 tick 指令条数」→ ipt 是每秒点数率：micro 2 / logic 8 / hyper 25 [src: Mindustry-Source/core/src/mindustry/content/Blocks.java:6846-6869]
17. 「print 会自动扩容」→ 缓冲 400 字符，满了直接丢弃且不报错 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:46]
18. 「maxTextLength=150 限制 print」→ 那是聊天/长文本上限，与 print 无关 [src: Vars.java:109]
19. 「memory cell 是 32 格 / 越界读出 0」→ memory-cell 64 格（v160.7 jar 实测，与 v159.3 源码同）、memory-bank 512 格；越界读是 null(NaN)、越界写静默丢弃 [src: Mindustry-Source/core/src/mindustry/world/blocks/logic/MemoryBlock.java:64-81；content/Blocks.java:6872-6883]
20. 「程序可以写几千行」→ 解析上限 1000 行，超出静默消失 [src: Mindustry-Source/core/src/mindustry/logic/LParser.java:185]
21. 「draw color 可以填任意大数」→ 每通道 10 bit 有符号，范围 −511..511 [src: Mindustry-Source/core/src/mindustry/world/blocks/LogicDisplay.java:286-288]
22. 「ulocate 失败会清空全部输出」→ 只写 outFound=false，其余槽保持旧值 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:273-276]
23. 「ucontrol within 有 4 个输入」→ within (x) (y) (radius) 0 (result)，第 4 槽留 0、第 5 槽是输出 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:377]
24. 「getBlock 输出在最后两槽」→ 第 4/5/6 槽依次 type/building/floor [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:491-510]
25. 「ucontrol move 填像素」→ 填 tile，内部 World.unconv ×8 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:352]
26. 「ubind 之后永久持有单位」→ 单位死亡 @unit 变 null，所有 ucontrol 变空操作 [src: Mindustry-Source/core/src/mindustry/logic/LExecutor.java:304-552]
27. 「多处理器同 tick 的执行顺序固定」→ 未定（断言表 L3-05），要用 sync/flag 显式握手 [实测: docs/断言表.md L3-05]
28. 「未绑定的链接名可以当 sensor 目标」→ 结果为 null（S-17）[实测: docs/断言表.md S-17]
29. 「set 一个未知变量没有副作用」→ 会把该变量写成 null 覆盖旧值（S-16）[实测: docs/断言表.md S-16]
30. 「空容器读出来是 0」→ 无 payload 容器时是 null（内部 Float.NaN），equal 0 成立、大小比较给 0（S-14）[实测: docs/断言表.md S-14]
31. 「@links 是链接上限」→ 是当前有效链接数 [src: Mindustry-Source/core/src/mindustry/logic/LogicBlock.java:379]
32. 「@thisx/@thisy 是像素」→ 是 tile（World.conv 换算）[src: Mindustry-Source/core/src/mindustry/logic/LogicBlock.java:424-425]
33. 「@status-wet 写法到处通用」→ [v159.3] 只认裸名 wet；[v160.7] 裸名与 @status-wet 等效 [实测: docs/断言表.md L1-23]
34. 「strictEqual 恒为 false」→ 不成立，test() 特判类型位一致 + 数字精确相等 [src: Mindustry-Source/core/src/mindustry/logic/ConditionOp.java:31-40]
35. 「jump 的条件文本写 ==」→ 文本 token 是 equal/notEqual，== 只是 UI 符号 [src: Mindustry-Source/core/src/mindustry/logic/LStatements.java:1033-1041]
36. 「ConditionOp 只有 7 个值」→ 8 个（含 always）；7 只是「比较运算符」个数 [src: Mindustry-Source/core/src/mindustry/logic/ConditionOp.java:6-13]
37. 「setblock 能写 building 层」→ 只有 floor/ore/block 可写，building 层只读 [src: Mindustry-Source/core/src/mindustry/logic/TileLayer.java:3-9]
38. 「存档跨次版本通用」→ build 160 存档只能用 v160 载入（L3-04）[实测: docs/断言表.md L3-04]
39. 「unitCap=0 表示无限」→ unitCapVariable=true 时上限=核心加成之和（shard +8 / foundation +16 / nucleus +24）[src: Mindustry-Source/core/src/mindustry/game/Units.java:119-125]
40. 「护甲能把伤害减到 0」→ 10% 保底 max(D−A, 0.1D) [src: Mindustry-Source/core/src/mindustry/entities/Damage.java:659-661]

### B. 问 X 该查哪（20 条路由）

| 问题类型 | 查这里 | 关键字段 / 锚点 |
|---|---|---|
| 方块血量、尺寸、容量 | 02-world/W01-blocks-multiblock-anchor.md | 00-data/blocks.json: health/size/itemCapacity |
| 配方与制造速度 | 02-world/W02-crafting-recipes.md | craftTime/consumeItems/outputItems |
| 电力产能、耗电、范围 | 02-world/W03-power.md | powerProduction/powerConsumption/laserRange |
| 液体流量与容量 | 02-world/W04-liquids.md | liquidCapacity/flowRate |
| 热量、超频、冷却 | 02-world/W05-heat.md | heatOutput/heatCapacity/coolant |
| 传送带与路由吞吐 | 02-world/W06-logistics.md | speed/itemSpace/itemCapacity |
| 钻头等级与硬度惩罚 | 02-world/W07-drills-resources.md | tier/hardness/boost |
| 核心与容器容量 | 02-world/W10-storage.md | itemCapacity/unitCapModifier/storageCapacity |
| 一次命中怎么结算 | 03-combat/C01-damage-pipeline.md | BulletType → applyArmor → shield → hp |
| 炮塔射速、弹药、射程 | 03-combat/C02-turrets.md | reload/ammoTypes/range |
| 子弹寿命、速度、贯穿 | 03-combat/C03-bullets.md | lifetime/speed/drag/pierce |
| 护甲与状态倍率 | 03-combat/C05-armor.md、C04-status.md | armorMultiplier/speedMultiplier |
| 单位武器与挂点 | 03-combat/C06-unit-weapons.md | weapons[].reload/x/y |
| DPS 与 TTK 复算 | 03-combat/C10-numbers.md | 三式 + 护甲曲线 A*=0.9D |
| 单位速度与体型 | 04-units/U01-movement.md | speed/hitSize/boost |
| 单位生产与上限 | 04-units/U02-production.md | unitCapModifier/plans |
| 战役规则与难度 | 05-campaign/CAMP-RULES.md、CAMP.DIFFICULTY.001.md | 00-data/rules.json 的 118 个字段名 |
| 星区、科技解锁、跨局资源 | 05-campaign/CAMP-SECTOR.md | Sector/SectorPreset/TechTree |
| mlog 指令参数、槽位、预算 | 06-mlog/instructions.json#instructions、06-mlog/M04-读写与感知.md、01-execution/E01-执行模型与预算.md | params/defs/ipt |
| 某结论是否已验证 | 08-evidence/claims.jsonl | id/verdict/evidence/conf |

- **备注（不在上表 20 条内）**：查某方块 / 单位 / 物品 / 液体的**中文名或英文名** → `02-world/W13-name-blocks-terrain.md`、`W14-name-blocks-industry.md`、`W15-name-blocks-combat.md`（合起来 447 个方块全覆盖）、`W16-name-items.md`（22 物品 + 11 液体 + 23 状态）、`04-units/U06-name-units.md`（70 单位）；id 为 `WORLD.NAMES.001-004` / `UNIT.NAMES.001`，界面只显示名字、蓝图与波次只认 id。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| tick 长度 | 1/60 s，即 60 tick/s（Time.delta=1/tick）| LExecutor.java:1218-1232 |
| tile 与像素 | 1 tile = 8 px（tilesize=8）| core/World.java:165-176 |
| wait 参数单位 | 秒，粒度 1 tick（wait 1 = 60 tick）| LExecutor.java:1218-1232 |
| @time / @second | @time 是毫秒；@second=tick/60 | core/GlobalVars.java:190-199 |
| 处理器 ipt | micro 2 / logic 8 / hyper 25，单位是**点/tick**（点/s = 120 / 480 / 1500）| content/Blocks.java:6846-6869；v160.7 jar `instructionsPerTick` |
| world 处理器 ipt | 8 点/tick（= 480 点/s），上限 1000 | content/Blocks.java:6949-6960 |
| 单 tick 预算上限 | 累积池 = **5 × ipt**：micro **10** / logic **40** / hyper **125**；`maxInstructionsPerTick` 只是 `setrate` 能设到的 ipt 上限（非特权 40、世处 1000），**不参与削顶**（世处 `setrate 1000` ⇒ ipt 1000、池 5000）| logic/LogicBlock.java:565（`maxInstructionScale * ipt`）、`:558-559`（每帧复位 ipt）、LExecutor.java:2031（setrate clamp）|
| 程序 / 文本上限 | 1000 行 / print 400 字符 / 聊天 150 | LParser.java:185；LExecutor.java:46；Vars.java:109 |
| memory cell 格数 | memory-cell 64 / memory-bank 512 / world-cell 512（v159.3 源码与 v160.7 jar 实测一致；类默认 32 被实例覆盖）| content/Blocks.java:6875,6881,6967 |
| radar 缓存 | 每 30 tick 重算 | logic/LExecutor.java:763 |
| waveSpacing | 7200 tick = 120 s | 00-data/rules.json#waveSpacing |
| 首波倒计时 | initialWaveSpacing=0 ⇒ 2×7200 = 240 s | 00-data/rules.json + core/Logic.java:272 |
| turnDuration（战役时间片）| 7200 tick = 120 s | Vars.java:127 |
| 入侵宽限期 | 20 分钟 | Vars.java:131 |
| 入侵概率 | 1/100 × (0.8+(邻居数−1)×0.3) 每 turn | Vars.java:129 + game/Universe.java:232-237 |
| 发射容量倍率 | Serpulo 0.5 / 其它默认 0.25 | content/Planets.java:133；type/Planet.java:98-99 |
| 核心容量 | shard 4000 / foundation 9000 / nucleus 13000 | 00-data/blocks.json#itemCapacity |
| 核心单位上限加成 | shard +8 / foundation +16 / nucleus +24 | content/Blocks.java:3138/3150/3163 |
| 单位上限公式 | max(0, rules.unitCap + team.unitCap) | game/Units.java:119-125 |
| 敌方单位上限 | Integer.MAX_VALUE（无上限）| game/Units.java:119-125 |
| 波次总上限 / 单组上限 | 150 波；主组 13、副组 6 | game/Waves.java:299,323-339 |
| 护甲公式 | max(D − A, 0.1D)（护甲只做减法 + 10% 保底）| entities/Damage.java:659-661；Vars.java:133 |
| 护甲拐点 | A* = 0.9D，超过后恒吃 10% | 03-combat/C10-numbers.md |
| meltdown 双口径 | 子弹层 4680 DPS vs 实战 936 DPS（差 5 倍）| ContinuousBulletType.java:39-44；C10-numbers.md |
| spectre 对 22 甲 | 428.6 → 240 DPS | 03-combat/C10-numbers.md（00-data/units.json 护甲 22）|
| 传送带速度 | 0.035 格/tick = 2.1 格/s（v160.7）| 00-data/blocks.json#conveyor.speed |
| 传送带吞吐 | speed×60/0.4 ≈ 5.25 件/s；单格最多 3 件 | Conveyor.java:27-32 |
| phase-conveyor | 30 件/s，range 12 | content/Blocks.java:2115-2125 |
| mass-driver | range 440 px = 55 格，reload 200 tick | world/blocks/MassDriver.java:31,66 |
| 存档跨版本 | build 160 存档只能用 v160 载入（L3-04）| docs/断言表.md L3-04 |

- **数值以 v160.7 jar 为主**：00-data/*.json 每条带 src 字段（形如 jar:v160.7#类名），面板 DPS、护甲、容量一律取它。
- **语义与算法以 v159.3 源码为准**：仓库 Mindustry-Source 是 v159.3（落后一个次版本），公式、判定顺序、槽位从它推导。
- **两边冲突就并列写**：[v159.3] … [v160.7] …，不得只留一边；已收录的冲突见 01-execution/E06-跨版本差异.md。

## 源码锚点

- 三态与 null：logic/LVar.java:56-58（num 对 null 给 0、numOrNan 给 NaN）、:87-97（NaN/Inf 赋值变 null） 执行与预算：logic/LExecutor.java:111-121、logic/LogicBlock.java:564-579（yield 不扣点、5×ipt 削顶）、content/Blocks.java:6846-6869（ipt 三档）。
- 时间：logic/LExecutor.java:1218-1232（curTime += Time.delta/60f）、core/GlobalVars.java:190-199（@time 毫秒） 坐标：core/World.java:165-176（tilesize=8，conv/unconv）、logic/LVar.java:69-72（numfWorld 自动 ×8）。
- 屏幕与文本：world/blocks/LogicDisplay.java:286-288（10 bit 有符号）、logic/LExecutor.java:46（400 字符缓冲） 战斗：applyArmor 与 10% 保底 [src: entities/Damage.java:659-661]、Vars.java:133。

## 实测与反例

- ✅ 本卡 40 条陷阱里 33 条为源码可复算（S），7 条依赖真机/断言表实测（E），逐条已标锚点 [src: docs/断言表.md:3]。
- 反例（不成立边界）：第 15 条的「5×ipt 削顶」只约束**单 tick 能攒多少点**，不是每秒总量上限；持续超载时程序仍按 ipt 速率跑，只是攒不出突发 [src: logic/LogicBlock.java:564-579]。
- 【U】第 27 条「处理器执行顺序」仍是待定项 L3-05，需要双处理器同 tick 互写同一变量的对照实验才能定论 [实测: docs/断言表.md L3-05]。

## 常见误解

1. 「速查卡里的数字可以直接当官方数值」——不是：jar 反射值与源码默认值经常差一档（toxopid 护甲 22 vs 13），以本卡「三条口径」为准。
2. 「面板 DPS 就是实战 DPS」——差在护甲减法与保底：同一门炮能差 5 倍（meltdown 4680 vs 936）。
3. 「单位上限 0 表示无限」——0 + unitCapVariable=true = 核心加成之和；只有 disableUnitCap 或敌方队才无限 同理，所谓「坑」多是槽位顺序与 null 语义，不是版本 bug。

## 相关

- [[EXEC.TRAP.001]] 30 条指令语义陷阱的完整推导；[[EXEC.MODEL.001]] 预算链路；[[EXEC.TIME.001]] 时间口径。
- [[COMBAT.NUMBERS.001]] DPS/TTK 复算与护甲曲线；[[COMBAT.ARMOR.001]] 护甲公式全文 [[CAMP.RULES.001]] Rules 118 字段；[[CAMP.SECTOR.001]] 星区与跨局资源；[[MLOG.IO.001]] 读写槽位表。
- [[MLOG.PERF.001]] 各项硬上限。
