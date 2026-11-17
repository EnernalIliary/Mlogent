# 检索冒烟

- 题库: <scratch-dir>\kb-stage\_report\smoke_self.jsonl（45 题，其中 45 题有 expect）
- 库: <scratch-dir>\kb-stage\_kb_build2\kb.sqlite3
- 模型预热: 1.3s  ·  单题 p50=138ms  p90=159ms  max=218ms
- top1 命中 0/45（0%）  top3 0/45（0%）  top6 0/45（0%）

| # | 题干 | top1 | 命中@3 | ms | 首条命中 |
|---:|---|---|---|---:|---|
| 1 | 链接与 @ 常量：@links / getlink、内置变量分类与单位 | N | N | 153 | knowledge/01-execution/E05-链接与@常量.md |
| 2 | 变量与内存边界：LVar 的四种状态、memory cell 与文本缓冲 | N | N | 101 | knowledge/01-execution/E03-变量与内存边界.md |
| 3 | 执行模型与指令预算：从 tick 到 accumulator 的完整链路 | N | N | 133 | knowledge/01-execution/E01-执行模型与预算.md |
| 4 | 时间与 wait 精度：tick、秒与帧差 | N | N | 134 | knowledge/01-execution/E04-时间与wait精度.md |
| 5 | 指令语义陷阱 30 条（向量 / 对象 / 数值 / 时序 / 内存 / 交互） | N | N | 115 | knowledge/01-execution/E02-指令语义陷阱.md |
| 6 | 跨版本差异：v159.3 源码 vs v160.7 实测，以及文档冲突清单 | N | N | 127 | knowledge/01-execution/E06-跨版本差异.md |
| 7 | 方块模型与多格锚点 | N | N | 100 | knowledge/02-world/W01-blocks-multiblock-anchor.md |
| 8 | 配方与制造 | N | N | 140 | knowledge/02-world/W02-crafting-recipes.md |
| 9 | 热量系统 | N | N | 107 | knowledge/02-world/W05-heat.md |
| 10 | 液体系统 | N | N | 130 | knowledge/02-world/W04-liquids.md |
| 11 | 物流与物品传输（传送带 / 路由 / 交叉 / 桥 / 质量驱动器） | N | N | 130 | knowledge/CONVENTIONS.md |
| 12 | 电力网络 | N | N | 129 | knowledge/02-world/W03-power.md |
| 13 | 护甲与抗性——减法公式、10% 保底、穿甲与免疫 | N | N | 118 | knowledge/03-combat/C05-armor.md |
| 14 | 子弹与弹道——lifetime/speed/drag、贯穿、溅射、闪电与碎片 | N | N | 151 | knowledge/03-combat/C03-bullets.md |
| 15 | 伤害管线总览——一次命中从 BulletType 到 health 的完整顺序 | N | N | 168 | knowledge/03-combat/C01-damage-pipeline.md |
| 16 | 防御工事——墙体、门、护盾与修理器的数值与判定顺序 | N | N | 122 | knowledge/03-combat/C09-defense.md |
| 17 | 战斗数值实例——DPS、TTK 与护甲曲线（可复算） | N | N | 143 | knowledge/03-combat/C10-numbers.md |
| 18 | 状态效果——倍率字段、时长、叠加与刷新、反应伤害 | N | N | 154 | knowledge/03-combat/C04-status.md |
| 19 | 治疗、护盾与修理——heal / shield / mend / repairSpeed | N | N | 130 | knowledge/03-combat/C07-support.md |
| 20 | 炮塔机制——射程、装填、弹药、冷却液、朝向与过热 | N | N | 133 | knowledge/03-combat/C02-turrets.md |
| 21 | 单位武器——weapons[]、挂点坐标、镜像与单位 DPS | N | N | 138 | knowledge/03-combat/C06-unit-weapons.md |
| 22 | 敌方与攻击波——生成点、波次组成、难度缩放与 AI 目标 | N | N | 108 | knowledge/03-combat/C08-waves.md |
| 23 | 单位能力——abilities 列表、16 类 Ability 的参数与触发 | N | N | 108 | knowledge/01-execution/E02-指令语义陷阱.md |
| 24 | 单位 AI——控制器、目标选择、命令与姿态、寻路代价 | N | N | 142 | mindustry-blueprint/REFERENCE.md |
| 25 | 单位类型与移动——speed 的真实单位、hitSize、地形与 boost | N | N | 148 | knowledge/04-units/U01-movement.md |
| 26 | 单位生产链——工厂、重构厂、组装厂与单位上限 | N | N | 141 | docs/MBO与配比计算器.md |
| 27 | 难度系数换算卡——三元组如何变成血量、数量、造价与波次间隔 | N | N | 150 | knowledge/02-world/W02-crafting-recipes.md |
| 28 | Rules 规则对象全字段（118 项） | N | N | 119 | knowledge/06-mlog/M06-世界交互.md |
| 29 | 刷怪组数据模型——SpawnGroup 的 8 个字段怎么变成每波的数量与护盾 | N | N | 150 | knowledge/03-combat/C08-waves.md |
| 30 | 波次节奏的数值模型——waveSpacing、首波宽限与倒计时推进 | N | N | 157 | knowledge/03-combat/C08-waves.md |
| 31 | 绘制与文本：draw 的 16 种命令、10 bit 打包与文本缓冲 | N | N | 147 | knowledge/06-mlog/M05-绘制与文本.md |
| 32 | 执行模型总览：tick、@counter 与每 tick 指令预算 | N | N | 148 | knowledge/06-mlog/M01-执行模型总览.md |
| 33 | 控制流：jump 的 8 个条件、循环写法与 @counter 改写后果 | N | N | 132 | knowledge/06-mlog/M03-控制流.md |
| 34 | 读写与感知：read / write / sensor / radar / ulocate / getlink / lookup | N | N | 148 | knowledge/06-mlog/M04-读写与感知.md |
| 35 | 性能与限制：预算、延迟、卡顿与各项硬上限 | N | N | 149 | knowledge/06-mlog/M08-性能与限制.md |
| 36 | 单位与逻辑控制：ubind、ucontrol 的 21 个子命令与 @unit 生命周期 | N | N | 164 | knowledge/06-mlog/M07-单位与逻辑控制.md |
| 37 | 变量与作用域：number / object / null 三态 | N | N | 159 | knowledge/06-mlog/M02-变量与作用域.md |
| 38 | 世界交互：control、setrule 与 world processor 的 26 条特权指令 | N | N | 153 | knowledge/06-mlog/M06-世界交互.md |
| 39 | 蓝图架构总览：预算、分层与拓扑 | N | N | 118 | knowledge/07-patterns/P01-architecture.md |
| 40 | 通信与总线：内存信箱、通道编码与读写竞态 | N | N | 218 | knowledge/07-patterns/P03-comm-bus.md |
| 41 | 数据结构：数组、队列、环形缓冲与画布的内存布局 | N | N | 133 | knowledge/07-patterns/P04-data-structures.md |
| 42 | 性能与鲁棒性：预算分配、降频与自恢复 | N | N | 152 | knowledge/07-patterns/P06-performance.md |
| 43 | 状态机：枚举、转移表与 @counter 分派 | N | N | 183 | knowledge/07-patterns/P02-state-machine.md |
| 44 | 雷达与索敌：filter/sort/order 的组合与射程判定 | N | N | 122 | knowledge/07-patterns/P05-radar-targeting.md |
| 45 | 反模式清单：20 条真实蓝图里的错误写法 | N | N | 121 | knowledge/08-evidence/anti-patterns.md |

## 未命中明细（45）

- 题干: 链接与 @ 常量：@links / getlink、内置变量分类与单位  ·  expect=['EXEC.LINK.001', 'knowledge/01-execution/E05-链接与@常量.md']
    - knowledge/01-execution/E05-链接与@常量.md
    - knowledge/06-mlog/M02-变量与作用域.md
    - knowledge/01-execution/E03-变量与内存边界.md
- 题干: 变量与内存边界：LVar 的四种状态、memory cell 与文本缓冲  ·  expect=['EXEC.MEM.001', 'knowledge/01-execution/E03-变量与内存边界.md']
    - knowledge/01-execution/E03-变量与内存边界.md
    - knowledge/06-mlog/M02-变量与作用域.md
    - knowledge/01-execution/E02-指令语义陷阱.md
- 题干: 执行模型与指令预算：从 tick 到 accumulator 的完整链路  ·  expect=['EXEC.MODEL.001', 'knowledge/01-execution/E01-执行模型与预算.md']
    - knowledge/01-execution/E01-执行模型与预算.md
    - knowledge/06-mlog/M01-执行模型总览.md
    - knowledge/07-patterns/P06-performance.md
- 题干: 时间与 wait 精度：tick、秒与帧差  ·  expect=['EXEC.TIME.001', 'knowledge/01-execution/E04-时间与wait精度.md']
    - knowledge/01-execution/E04-时间与wait精度.md
    - knowledge/01-execution/E02-指令语义陷阱.md
    - knowledge/06-mlog/M08-性能与限制.md
- 题干: 指令语义陷阱 30 条（向量 / 对象 / 数值 / 时序 / 内存 / 交互）  ·  expect=['EXEC.TRAP.001', 'knowledge/01-execution/E02-指令语义陷阱.md']
    - knowledge/01-execution/E02-指令语义陷阱.md
    - knowledge/01-execution/E03-变量与内存边界.md
    - knowledge/01-execution/E06-跨版本差异.md
- 题干: 跨版本差异：v159.3 源码 vs v160.7 实测，以及文档冲突清单  ·  expect=['EXEC.VER.001', 'knowledge/01-execution/E06-跨版本差异.md']
    - knowledge/01-execution/E06-跨版本差异.md
    - knowledge/VERSION.md
- 题干: 方块模型与多格锚点  ·  expect=['WORLD.BLOCKS.001', 'knowledge/02-world/W01-blocks-multiblock-anchor.md']
    - knowledge/02-world/W01-blocks-multiblock-anchor.md
    - mindustry-blueprint/REFERENCE.md
    - knowledge/06-mlog/M06-世界交互.md
- 题干: 配方与制造  ·  expect=['WORLD.CRAFTING.001', 'knowledge/02-world/W02-crafting-recipes.md']
    - knowledge/02-world/W02-crafting-recipes.md
    - docs/游戏速查/物品.md
    - docs/MBO与配比计算器.md
- 题干: 热量系统  ·  expect=['WORLD.HEAT.001', 'knowledge/02-world/W05-heat.md']
    - knowledge/02-world/W05-heat.md
    - knowledge/02-world/W03-power.md
- 题干: 液体系统  ·  expect=['WORLD.LIQUIDS.001', 'knowledge/02-world/W04-liquids.md']
    - knowledge/02-world/W04-liquids.md
- 题干: 物流与物品传输（传送带 / 路由 / 交叉 / 桥 / 质量驱动器）  ·  expect=['WORLD.LOGISTICS.001', 'knowledge/02-world/W06-logistics.md']
    - knowledge/CONVENTIONS.md
    - docs/MBO与配比计算器.md
    - knowledge/02-world/W04-liquids.md
- 题干: 电力网络  ·  expect=['WORLD.POWER.001', 'knowledge/02-world/W03-power.md']
    - knowledge/02-world/W03-power.md
    - docs/游戏速查/方块.md
- 题干: 护甲与抗性——减法公式、10% 保底、穿甲与免疫  ·  expect=['COMBAT.ARMOR.001', 'knowledge/03-combat/C05-armor.md']
    - knowledge/03-combat/C05-armor.md
    - knowledge/03-combat/C01-damage-pipeline.md
- 题干: 子弹与弹道——lifetime/speed/drag、贯穿、溅射、闪电与碎片  ·  expect=['COMBAT.BULLET.001', 'knowledge/03-combat/C03-bullets.md']
    - knowledge/03-combat/C03-bullets.md
    - knowledge/03-combat/C02-turrets.md
- 题干: 伤害管线总览——一次命中从 BulletType 到 health 的完整顺序  ·  expect=['COMBAT.DAMAGE.001', 'knowledge/03-combat/C01-damage-pipeline.md']
    - knowledge/03-combat/C01-damage-pipeline.md
    - knowledge/03-combat/C04-status.md
    - docs/断言表.md
- 题干: 防御工事——墙体、门、护盾与修理器的数值与判定顺序  ·  expect=['COMBAT.DEFENSE.001', 'knowledge/03-combat/C09-defense.md']
    - knowledge/03-combat/C09-defense.md
    - knowledge/03-combat/C05-armor.md
- 题干: 战斗数值实例——DPS、TTK 与护甲曲线（可复算）  ·  expect=['COMBAT.NUMBERS.001', 'knowledge/03-combat/C10-numbers.md']
    - knowledge/03-combat/C10-numbers.md
    - knowledge/03-combat/C01-damage-pipeline.md
    - knowledge/03-combat/C05-armor.md
- 题干: 状态效果——倍率字段、时长、叠加与刷新、反应伤害  ·  expect=['COMBAT.STATUS.001', 'knowledge/03-combat/C04-status.md']
    - knowledge/03-combat/C04-status.md
    - docs/断言表.md
- 题干: 治疗、护盾与修理——heal / shield / mend / repairSpeed  ·  expect=['COMBAT.SUPPORT.001', 'knowledge/03-combat/C07-support.md']
    - knowledge/03-combat/C07-support.md
    - knowledge/03-combat/C09-defense.md
- 题干: 炮塔机制——射程、装填、弹药、冷却液、朝向与过热  ·  expect=['COMBAT.TURRET.001', 'knowledge/03-combat/C02-turrets.md']
    - knowledge/03-combat/C02-turrets.md
    - knowledge/03-combat/C10-numbers.md
    - knowledge/03-combat/C09-defense.md
- 题干: 单位武器——weapons[]、挂点坐标、镜像与单位 DPS  ·  expect=['COMBAT.UNITWEAPON.001', 'knowledge/03-combat/C06-unit-weapons.md']
    - knowledge/03-combat/C06-unit-weapons.md
- 题干: 敌方与攻击波——生成点、波次组成、难度缩放与 AI 目标  ·  expect=['COMBAT.WAVE.001', 'knowledge/03-combat/C08-waves.md']
    - knowledge/03-combat/C08-waves.md
- 题干: 单位能力——abilities 列表、16 类 Ability 的参数与触发  ·  expect=['UNIT.ABILITY.001', 'knowledge/04-units/U04-abilities.md']
    - knowledge/01-execution/E02-指令语义陷阱.md
    - knowledge/04-units/U01-movement.md
    - knowledge/06-mlog/M05-绘制与文本.md
- 题干: 单位 AI——控制器、目标选择、命令与姿态、寻路代价  ·  expect=['UNIT.AI.001', 'knowledge/04-units/U03-ai.md']
    - mindustry-blueprint/REFERENCE.md
    - knowledge/06-mlog/M07-单位与逻辑控制.md
    - docs/验证记录.md
- 题干: 单位类型与移动——speed 的真实单位、hitSize、地形与 boost  ·  expect=['UNIT.MOVE.001', 'knowledge/04-units/U01-movement.md']
    - knowledge/04-units/U01-movement.md
- 题干: 单位生产链——工厂、重构厂、组装厂与单位上限  ·  expect=['UNIT.PRODUCE.001', 'knowledge/04-units/U02-production.md']
    - docs/MBO与配比计算器.md
    - docs/游戏速查/方块.md
- 题干: 难度系数换算卡——三元组如何变成血量、数量、造价与波次间隔  ·  expect=['CAMP.DIFFICULTY.001', 'knowledge/05-campaign/CAMP.DIFFICULTY.001.md']
    - knowledge/02-world/W02-crafting-recipes.md
    - knowledge/03-combat/C08-waves.md
    - knowledge/03-combat/C07-support.md
- 题干: Rules 规则对象全字段（118 项）  ·  expect=['CAMP.RULES.001', 'knowledge/05-campaign/CAMP-RULES.md']
    - knowledge/06-mlog/M06-世界交互.md
    - knowledge/01-execution/E03-变量与内存边界.md
    - knowledge/CONVENTIONS.md
- 题干: 刷怪组数据模型——SpawnGroup 的 8 个字段怎么变成每波的数量与护盾  ·  expect=['CAMP.SPAWN.001', 'knowledge/05-campaign/CAMP.SPAWN.001.md']
    - knowledge/03-combat/C08-waves.md
    - docs/验证记录.md
    - knowledge/08-evidence/bench/README.md
- 题干: 波次节奏的数值模型——waveSpacing、首波宽限与倒计时推进  ·  expect=['CAMP.WAVES.001', 'knowledge/05-campaign/CAMP.WAVES.001.md']
    - knowledge/03-combat/C08-waves.md
    - knowledge/06-mlog/M08-性能与限制.md
- 题干: 绘制与文本：draw 的 16 种命令、10 bit 打包与文本缓冲  ·  expect=['MLOG.DRAW.001', 'knowledge/06-mlog/M05-绘制与文本.md']
    - knowledge/06-mlog/M05-绘制与文本.md
    - tools/README.md
    - knowledge/08-evidence/anti-patterns.md
- 题干: 执行模型总览：tick、@counter 与每 tick 指令预算  ·  expect=['MLOG.EXEC.001', 'knowledge/06-mlog/M01-执行模型总览.md']
    - knowledge/06-mlog/M01-执行模型总览.md
    - knowledge/01-execution/E01-执行模型与预算.md
    - knowledge/07-patterns/P01-architecture.md
- 题干: 控制流：jump 的 8 个条件、循环写法与 @counter 改写后果  ·  expect=['MLOG.FLOW.001', 'knowledge/06-mlog/M03-控制流.md']
    - knowledge/06-mlog/M03-控制流.md
    - Logic/逻辑代码规范.md
    - mindustry-blueprint/REFERENCE.md
- 题干: 读写与感知：read / write / sensor / radar / ulocate / getlink / lookup  ·  expect=['MLOG.IO.001', 'knowledge/06-mlog/M04-读写与感知.md']
    - knowledge/06-mlog/M04-读写与感知.md
    - knowledge/01-execution/E02-指令语义陷阱.md
    - knowledge/01-execution/E05-链接与@常量.md
- 题干: 性能与限制：预算、延迟、卡顿与各项硬上限  ·  expect=['MLOG.PERF.001', 'knowledge/06-mlog/M08-性能与限制.md']
    - knowledge/06-mlog/M08-性能与限制.md
    - knowledge/06-mlog/M03-控制流.md
    - knowledge/01-execution/E04-时间与wait精度.md
- 题干: 单位与逻辑控制：ubind、ucontrol 的 21 个子命令与 @unit 生命周期  ·  expect=['MLOG.UNIT.001', 'knowledge/06-mlog/M07-单位与逻辑控制.md']
    - knowledge/06-mlog/M07-单位与逻辑控制.md
    - knowledge/01-execution/E05-链接与@常量.md
    - knowledge/06-mlog/M06-世界交互.md
- 题干: 变量与作用域：number / object / null 三态  ·  expect=['MLOG.VAR.001', 'knowledge/06-mlog/M02-变量与作用域.md']
    - knowledge/06-mlog/M02-变量与作用域.md
    - knowledge/01-execution/E03-变量与内存边界.md
    - knowledge/06-mlog/M04-读写与感知.md
- 题干: 世界交互：control、setrule 与 world processor 的 26 条特权指令  ·  expect=['MLOG.WORLD.001', 'knowledge/06-mlog/M06-世界交互.md']
    - knowledge/06-mlog/M06-世界交互.md
    - mindustry-blueprint/REFERENCE.md
    - Logic/逻辑代码规范.md
- 题干: 蓝图架构总览：预算、分层与拓扑  ·  expect=['PATTERN.ARCH.001', 'knowledge/07-patterns/P01-architecture.md']
    - knowledge/07-patterns/P01-architecture.md
    - knowledge/07-patterns/P03-comm-bus.md
    - knowledge/07-patterns/P04-data-structures.md
- 题干: 通信与总线：内存信箱、通道编码与读写竞态  ·  expect=['PATTERN.COMM.001', 'knowledge/07-patterns/P03-comm-bus.md']
    - knowledge/07-patterns/P03-comm-bus.md
    - knowledge/07-patterns/P04-data-structures.md
    - knowledge/07-patterns/P01-architecture.md
- 题干: 数据结构：数组、队列、环形缓冲与画布的内存布局  ·  expect=['PATTERN.DATA.001', 'knowledge/07-patterns/P04-data-structures.md']
    - knowledge/07-patterns/P04-data-structures.md
    - knowledge/07-patterns/P03-comm-bus.md
    - docs/游戏速查/方块.md
- 题干: 性能与鲁棒性：预算分配、降频与自恢复  ·  expect=['PATTERN.PERF.001', 'knowledge/07-patterns/P06-performance.md']
    - knowledge/07-patterns/P06-performance.md
    - knowledge/08-evidence/anti-patterns.md
    - knowledge/07-patterns/P02-state-machine.md
- 题干: 状态机：枚举、转移表与 @counter 分派  ·  expect=['PATTERN.STATE.001', 'knowledge/07-patterns/P02-state-machine.md']
    - knowledge/07-patterns/P02-state-machine.md
    - knowledge/07-patterns/P01-architecture.md
    - knowledge/06-mlog/M02-变量与作用域.md
- 题干: 雷达与索敌：filter/sort/order 的组合与射程判定  ·  expect=['PATTERN.TARGET.001', 'knowledge/07-patterns/P05-radar-targeting.md']
    - knowledge/07-patterns/P05-radar-targeting.md
    - knowledge/07-patterns/P06-performance.md
- 题干: 反模式清单：20 条真实蓝图里的错误写法  ·  expect=['PATTERN.ANTI.001', 'knowledge/08-evidence/anti-patterns.md']
    - knowledge/08-evidence/anti-patterns.md
    - docs/验证记录.md
    - knowledge/08-evidence/bench/README.md
