# -*- coding: utf-8 -*-
"""域 10-12：单位控制 / 性能限制 / 方块与锚点。"""
from _gen_core import *

def build_unit():
    D = "单位控制"
    short(D, "LUnitControl 枚举一共有多少种 ucontrol 操作？", "21 种",
          "logic/LUnitControl.java: idle…unbind 共 21 项。", F_UCTL, "v159.3_src", 1)
    short(D, "ulocate 支持哪四种查找目标？", "ore、building、spawn、damaged",
          "logic/LLocate.java: ore, building, spawn, damaged。", F_LOC, "v159.3_src", 1)
    short(D, "radar/uradar 的 RadarTarget 枚举有多少种目标类型？", "8 种",
          "logic/RadarTarget.java: any/enemy/ally/player/attacker/flying/boss/ground。", F_RTGT, "v159.3_src", 1)
    mc(D, "ubind 语句的作用是？", "把指定类型的单位绑定到 @unit",
       ["生成一个新单位", "删除单位", "给单位下命令"], "LStatements.java:1070 ubind；UnitBindI 在 LExecutor.java:167-210。", F_STMT + ":1070", "v159.3_src", 1)
    mc(D, "ucontrol 语句的前置条件是？", "先用 ubind 绑定一个单位（@unit 非 null）",
       ["先 setrule", "先 spawn", "不需要前置"], "UnitControlI 从 exec.unit 取单位；@unit 未绑定则命令无效（LExecutor.java:304-552）。", F_EXEC + ":304", "v159.3_src", 2)
    mc(D, "ubind 的默认单位类型是？", "@poly",
       ["@dagger", "@flare", "@mega"], "LStatements.java:1072 UnitBindStatement: type = \"@poly\"。", F_STMT + ":1072", "v159.3_src", 2)
    mc(D, "ucontrol move 需要几个参数？", "2 个：x, y",
       ["1 个", "3 个", "4 个"], "LUnitControl.java: move(\"x\",\"y\")。", F_UCTL, "v159.3_src", 2)
    mc(D, "ucontrol build 需要的参数是？", "x, y, block, rotation, config",
       ["x, y, block", "block, rotation", "x, y, rotation"], "LUnitControl.java: build(\"x\",\"y\",\"block\",\"rotation\",\"config\")。", F_UCTL, "v159.3_src", 2)
    mc(D, "ucontrol within 的最后一个参数是什么？", "结果变量（是否在范围内）",
       ["半径", "单位类型", "过滤条件"], "LUnitControl.java: within(\"x\",\"y\",\"radius\",\"result\")。", F_UCTL, "v159.3_src", 2)
    mc(D, "ucontrol getBlock 的参数是？", "x, y, type, building, floor",
       ["x, y, building", "x, y, type", "x, y, floor, building"], "LUnitControl.java: getBlock(\"x\",\"y\",\"type\",\"building\",\"floor\")。", F_UCTL, "v159.3_src", 2)
    mc(D, "ulocate ore 的参数顺序是？", "ore 类型、outX、outY、found、ore",
       ["outX、outY、found、ore 类型", "found、outX、outY、ore 类型", "x、y、ore、found"], "LStatements.java:1194-1302 ULocateStatement 参数顺序与 LExecutor.java:210-301 UnitLocateI 一致。", F_STMT + ":1194-1302", "v159.3_src", 3)
    mc(D, "ulocate building 的 group 参数不能取哪个值？", "derelict",
       ["enemy", "ally", "core"], "ulocate building 的 group 取 enemy/ally/player/core/builder 等，derelict 不是有效分组（LStatements.java:1194-1302）。", F_STMT + ":1194-1302", "v159.3_src", 2)
    mc(D, "uradar 语句一共有几个参数？", "6 个：target1、target2、target3、sort、order、result",
       ["4 个", "5 个", "7 个"], "LStatements.java:1170-1193 uradar；RadarI 在 LExecutor.java:735 构造参数为 3 个 target + sort + order + output。", F_STMT + ":1170-1193", "v159.3_src", 2)
    mc(D, "RadarSort 支持哪几种排序依据？", "distance、health、shield、armor、maxHealth",
       ["只有 distance", "distance、health、angle", "distance、hp、armor、team"], "logic/RadarSort.java: distance, health, shield, armor, maxHealth。", F_RSORT, "v159.3_src", 2)
    mc(D, "radar 与 uradar 的区别是？", "radar 以处理器自身为圆心，uradar 以 @unit 为圆心",
       ["两者完全等价", "uradar 只找建筑", "radar 需要链接炮塔"], "LStatements.java:484 radar、1170 uradar；对应 RadarI 在 LExecutor.java:721-825。", F_STMT + ":484", "v159.3_src", 2)
    code(D, "绑定最近的 flare 并让它向左移动，程序怎么写？",
         ["ubind @flare", "ucontrol move 40 80"],
         "ubind @flare / ucontrol move 40 80",
         "ubind 默认类型就是 @poly，这里显式写 @flare（LStatements.java:1072）；ucontrol move 接 tile 坐标。", F_STMT + ":1070-1113", "v159.3_src", 2)
    mc(D, "ucontrol itemTake 的参数是？", "from、item、amount",
       ["to、item、amount", "item、amount", "from、amount"], "LUnitControl.java: itemTake(\"from\",\"item\",\"amount\")。", F_UCTL, "v159.3_src", 2)
    mc(D, "ucontrol flag 的参数是什么？", "value（内部 flag 值）",
       ["x、y", "单位类型", "无参数"], "LUnitControl.java: flag(\"value\")。", F_UCTL, "v159.3_src", 2)
    mc(D, "没有可用单位时 @unit 的值是？", "null（未绑定）",
       ["0", "最近的敌方单位", "处理器自身"], "@unit 由 ubind 写入；无匹配时保持 null，ucontrol 命令随之失效。", F_EXEC + ":304", "v159.3_src", 2)
    mc(D, "RadarTarget.enemy 会匹配 derelict（中立残骸）队伍吗？", "不会，显式排除 Team.derelict",
       ["会", "只匹配 derelict", "取决于地图设置"], "logic/RadarTarget.java: enemy((team, other) -> team != other.team && other.team != Team.derelict)。", F_RTGT, "v159.3_src", 3)
    mc(D, "radar 语句的参数顺序是？", "target1、target2、target3、sort、order、result",
       ["sort、order、target1-3、result", "target1-3、result、sort、order", "result、target1-3、sort"], "LStatements.java:484-553 radar 与 1170-1193 uradar 参数结构相同。", F_STMT + ":484-553", "v159.3_src", 3)
    mc(D, "ucontrol payTake 的 takeUnits 参数是什么作用？", "为 true 时同时拿走载荷里的单位",
       ["拿走的数量", "目标队伍", "是否允许空取"], "LUnitControl.java: payTake(\"takeUnits\")。", F_UCTL, "v159.3_src", 3)
    mc(D, "ucontrol approach 与 pathfind 的区别是？", "approach 带 radius 参数（接近到半径内），pathfind 只给目标点",
       ["两者完全一样", "pathfind 带半径", "approach 只用于飞行单位"], "LUnitControl.java: approach(\"x\",\"y\",\"radius\") 与 pathfind(\"x\",\"y\")。", F_UCTL, "v159.3_src", 3)
    mc(D, "ucontrol target 与 targetp 的区别是？", "target 给坐标与开火标志，targetp 直接给单位对象",
       ["target 只能打建筑", "targetp 只给坐标", "两者等价"], "LUnitControl.java: target(\"x\",\"y\",\"shoot\") 与 targetp(\"unit\",\"shoot\")。", F_UCTL, "v159.3_src", 3)
    mc(D, "@unit 属于哪一类变量？", "特殊可写变量（由 ubind/unbind 改写）",
       ["只读常量", "内容常量", "普通数字变量"], "instr_semantics.json#builtin_special_writable = [@counter,@ipt,@unit]。", F_INSTR + "#builtin_special_writable", "v159.3_src", 3)

def build_perf():
    D = "性能限制"
    short(D, "LExecutor.maxInstructions 的默认值是多少？", "1000 条",
          "LExecutor.java:41 public static int maxInstructions = 1000;", F_EXEC + ":41", "v159.3_src", 1)
    short(D, "处理器默认每 tick 执行多少条指令？", "1 条（instructionsPerTick=1）",
          "world/blocks/logic/LogicBlock.java:46。", F_LOGICB + ":46", "v159.3_src", 1)
    short(D, "LogicBlock.maxInstructionScale 默认值是多少？", "5",
          "LogicBlock.java:45。", F_LOGICB + ":45", "v159.3_src", 1)
    short(D, "LogicBlock.maxInstructionsPerTick 默认值是多少（仅 privileged）？", "40",
          "LogicBlock.java:47-48：注释 //privileged only，值 40。", F_LOGICB + ":47-48", "v159.3_src", 1)
    short(D, "文本缓冲上限 maxTextBuffer 是多少？", "400 字符",
          "LExecutor.java:46 maxTextBuffer = 400。", F_EXEC + ":46", "v159.3_src", 1)
    short(D, "单 tick 绘制命令缓冲上限 maxGraphicsBuffer 是多少？", "256",
          "LExecutor.java:44。", F_EXEC + ":44", "v159.3_src", 1)
    mc(D, "instructionsPerTick 决定什么？", "每 tick 最多执行多少条指令",
       ["程序总长度上限", "每 tick 发电量", "链接方块数量"], "LogicBlock.java:46；LExecutor 每 tick 按 ipt 消耗预算。", F_LOGICB + ":46", "v159.3_src", 2)
    mc(D, "maxInstructionScale 限制的是？", "ipt 滑条能达到的上限倍率（5 倍）",
       ["程序条数", "单条指令耗时", "处理器范围"], "LogicBlock.java:45；实际 ipt 受 ipt 值与 scale 共同约束。", F_LOGICB + ":45", "v159.3_src", 2)
    mc(D, "想设置 ipt 超过 40，需要什么条件？", "处理器具有 privileged 权限（世界处理器）",
       ["把 maxInstructionScale 设 8", "链接更多处理器", "使用 setrate 40 以上即可"],
       "LogicBlock.java:47-48 注释 //privileged only + maxInstructionsPerTick = 40。", F_LOGICB + ":47-48", "v159.3_src", 2)
    mc(D, "maxInstructions 是 static 字段，这意味着？", "可被 mod 或运行环境整体修改（不是每方块实例字段）",
       ["每个处理器可单独改", "不能被修改", "只影响单机"], "LExecutor.java:41 public static int maxInstructions = 1000;", F_EXEC + ":41", "v159.3_src", 3)
    mc(D, "处理器方块的最大连接范围是多少？", "80 tile（源码写作 8 * 10）",
       ["8 tile", "10 tile", "40 tile"], "LogicBlock.java:49 public float range = 8 * 10;", F_LOGICB + ":49", "v159.3_src", 2)
    mc(D, "游戏 1 秒等于多少 tick？", "60 tick",
       ["50 tick", "30 tick", "100 tick"], "knowledge/VERSION.md：1 tick = 1/60 s（能量 1 单位/tick = 60/s）。", F_VER, "both", 2)
    calc(D, "程序 400 条指令、ipt=5，跑完一轮需要多少 tick？", "400 / 5", "80 tick",
         "400/5 = 80 tick（≈1.33 秒）。", F_LOGICB + ":46", "v159.3_src", 2)
    calc(D, "程序 1000 条指令（上限）、ipt=40，跑完一轮需要多少 tick？", "1000 / 40", "25 tick",
         "1000/40 = 25 tick（≈0.42 秒）。", F_EXEC + ":41", "v159.3_src", 2)
    mc(D, "logic-processor 的建造成本是？", "lead 320 + silicon 80 + graphite 60 + thorium 50",
       ["lead 100 + silicon 50", "copper 500", "titanium 200 + silicon 100"],
       "tools/block_attrs.json#logic-processor 的 build.cost（源自 content/Blocks.java 的定义）。", F_ATTR, "v159.3_src", 2)
    mc(D, "两个处理器能共享同一个变量吗？", "不能，变量表是每个处理器实例私有的",
       ["能，全局共享", "只有数字变量能共享", "通过 @links 自动共享"], "变量存于 LExecutor 实例（LExecutor.java:48-58），每个处理器各自一份。", F_EXEC + ":48-58", "v159.3_src", 2)
    mc(D, "显示器能缓存的绘制指令上限是？", "1024",
       ["256", "400", "2048"], "LExecutor.java:45 maxDisplayBuffer = 1024。", F_EXEC + ":45", "v159.3_src", 3)
    mc(D, "wait 语句对性能的直接好处是？", "立即让出本 tick 剩余指令预算，避免空转",
       ["减少程序条数", "提高 ipt", "减少电力消耗"], "WaitI（LExecutor.java:1206-1234）设置 yield 并结束本 tick 执行。", F_EXEC + ":1206-1234", "v159.3_src", 2)
    mc(D, "写一个 jump always 0 的死循环，会发生什么？", "每 tick 把 ipt 条预算耗尽在死循环里，程序永不前进",
       ["游戏崩溃", "被自动终止", "自动降为 1 条/tick"], "JumpI 只改 @counter，LExecutor 按 ipt 循环执行到预算用尽（LExecutor.java:1183-1204）。", F_EXEC + ":1183-1204", "v159.3_src", 3)
    mc(D, "wait 与 ipt 的关系是？", "wait 不等满 ipt，而是立刻结束本 tick 的执行",
       ["wait 会补满 ipt", "wait 只影响下个 tick", "wait 会提高 ipt"], "WaitI 设置 exec.yield = true，主循环随即停止本 tick（LExecutor.java:1206-1234）。", F_EXEC + ":1206-1234", "v159.3_src", 3)
    mc(D, "为什么把循环内的常量运算提到循环外能提速？", "每条指令都占 ipt 预算，减少总条数直接缩短一轮所需 tick",
       ["减少内存占用", "避免浮点误差", "提高 ipt"], "预算模型：每 tick 只执行 ipt 条（LogicBlock.java:46），条数越少轮次越快。", F_LOGICB + ":46", "v159.3_src", 3)
    mc(D, "一个 tick 内第 257 条 draw 会怎样？", "被直接丢弃（缓冲满即 return）",
       ["覆盖第一条", "自动 drawflush", "写入 message"], "LExecutor.java:930 graphicsBuffer.size >= maxGraphicsBuffer(=256) 时 return。", F_EXEC + ":930", "v159.3_src", 3)
    mc(D, "maxInstructions 与 maxInstructionsPerTick 的区别是？", "前者是程序总长度上限，后者是单 tick 执行上限",
       ["两者相同", "前者每 tick、后者总长", "前者只对世界处理器生效"], "LExecutor.java:41 与 LogicBlock.java:47-48。", F_EXEC + ":41", "v159.3_src", 2)
    mc(D, "多个处理器同时向同一个显示器 drawflush，会怎样？", "互相覆盖，最终显示取决于执行顺序",
       ["自动合并", "报错", "轮流显示"], "显示器持有单一显示缓冲；每次 drawflush 用新的命令覆盖（DrawFlushI，LExecutor.java:1026-1045）。", F_EXEC + ":1026", "v159.3_src", 3)
    mc(D, "降低 ipt 的直接后果是？", "同样程序需要更多 tick 才能跑完一轮",
       ["程序条数上限降低", "变量丢失", "链接断开"], "每 tick 执行 ipt 条（LogicBlock.java:46）。", F_LOGICB + ":46", "v159.3_src", 2)

def build_block():
    D = "方块与锚点"
    short(D, "tools/block_attrs.json 收录了多少个方块的属性？", "253 个",
          "tools/block_attrs.json 的 blocks 字典长度 253（只收有可抽取属性的方块）。", F_ATTR + "#blocks", "v159.3_src", 1)
    short(D, "data/game/blocks.json 一共有多少个方块？", "447 个",
          "data/game/blocks.json 为 447 条数组；meta.json 亦记录 blocks=447。", F_BJSON, "both", 1)
    short(D, "tools/block_sizes.json 有多少项？", "446 项",
          "tools/block_sizes.json 为 446 个 name→size 映射。", F_SIZES, "v159.3_src", 1)
    mc(D, "方块的 size 字段表示什么？", "方块占地的边长（tile 数）",
       ["方块血量", "建造耗时", "物品容量"], "block_sizes.json 与 blocks.json 的 size 字段；如 core-shard size=3。", F_SIZES, "both", 1)
    mc(D, "block_attrs.json 的 accepts 字段有哪几种取值？", "none、any、custom、recipe",
       ["yes/no", "solid/liquid", "true/false"], "tools/block_attrs.json：accepts 取值 none/any/custom/recipe（对应 Block.acceptsItems 等）。", F_ATTR + "#accepts", "v159.3_src", 2)
    mc(D, "下列哪个不是方块 category 的常见取值？", "weapon",
       ["power", "liquid", "distribution"], "block_attrs.json 的 build.category 常见值：power/liquid/distribution/logic/effect/production 等。", F_ATTR + "#build", "v159.3_src", 1)
    mc(D, "core-shard 的物品容量与占地是？", "itemCapacity=4000，size=3",
       ["1000 / 2", "4000 / 4", "5000 / 3"], "tools/block_attrs.json#core-shard: itemCapacity=4000, size=3。", F_ATTR + "#core-shard", "v159.3_src", 2)
    mc(D, "container（容器）的物品容量与占地是？", "itemCapacity=300，size=2",
       ["300 / 3", "1000 / 2", "150 / 2"], "tools/block_attrs.json#container: itemCapacity=300, size=2。", F_ATTR + "#container", "v159.3_src", 2)
    mc(D, "liquid-tank 的液体容量与占地是？", "liquidCapacity=1800，size=3",
       ["700 / 2", "1800 / 2", "1000 / 3"], "tools/block_attrs.json#liquid-tank: liquidCapacity=1800, size=3。", F_ATTR + "#liquid-tank", "v159.3_src", 2)
    mc(D, "conduit（导管）的液体容量是多少？", "20",
       ["10", "50", "100"], "tools/block_attrs.json#conduit: liquidCapacity=20。", F_ATTR + "#conduit", "v159.3_src", 2)
    mc(D, "logic-processor 的占地与建造成本是？", "size=2，lead 320 + silicon 80 + graphite 60 + thorium 50",
       ["size=1，lead 100", "size=3，silicon 200", "size=2，copper 500"],
       "tools/block_attrs.json#logic-processor: size=2、build.cost 四项。", F_ATTR + "#logic-processor", "v159.3_src", 2)
    mc(D, "blocks.json 里每个方块都有 health 字段吗？", "是，health 是基础字段之一",
       ["只有可破坏方块有", "只有建筑有", "没有 health 字段"], "data/game/blocks.json 的字段：id,name,size,health,category,hasPower,requirements,consumers,outputs,craftTime。", F_BJSON, "both", 2)
    mc(D, "为什么 blocks.json 有 447 条而 block_attrs.json 只有 253 条？", "attrs 只收录能从 Blocks.java 抽取到属性（成本/容量/类别等）的方块",
       ["attrs 是随机抽样", "blocks.json 有重复", "attrs 只收电力方块"], "block_attrs.json 的 _note 说明它按属性抽取；无相关属性的方块不出现。", F_ATTR + "#_note", "v159.3_src", 3)
    mc(D, "方块的 id 与 name 有什么区别？", "id 是数字序号（内容注册顺序），name 是唯一字符串标识",
       ["完全一样", "id 是中文名", "name 是数字"], "data/game/blocks.json 每条都有 id 与 name 两个字段。", F_BJSON, "both", 2)
    mc(D, "block_attrs.json 里 build.cost 的格式是？", "字符串数组，形如 copper:5、lead:20",
       ["数字总价", "对象 {copper:5}", "中文物品名"], "tools/block_attrs.json#battery: build.cost = [copper:5, lead:20]。", F_ATTR + "#build", "v159.3_src", 2)
    mc(D, "下列哪组方块属于 distribution（物流）类别？", "conveyor、router、sorter",
       ["battery、solar-panel", "conduit、liquid-tank", "core-shard、container"], "block_attrs.json：conveyor/router/sorter 的 build.category 均为 distribution。", F_ATTR + "#conveyor", "v159.3_src", 2)
    mc(D, "liquid-container 的液体容量与占地是？", "liquidCapacity=700，size=2",
       ["1800 / 3", "700 / 3", "300 / 2"], "tools/block_attrs.json#liquid-container: liquidCapacity=700, size=2。", F_ATTR + "#liquid-container", "v159.3_src", 2)
    mc(D, "world/consumers 目录下共有多少个 Consume 相关 java 文件？", "24 个（含基类 Consume.java）",
       ["12 个", "21 个", "30 个"], "core/src/mindustry/world/consumers 目录 24 个 .java 文件。", SRC + "world/consumers/", "v159.3_src", 3)
    mc(D, "处理器能链接的方块数量上限主要由什么决定？", "链接范围（80 tile）内的可链接方块数量，以及 maxSides 等界面限制",
       ["固定 10 个", "由地图大小决定", "由电力网络决定"], "LogicBlock.java:49 range = 8 * 10；链接集合按范围扫描。", F_LOGICB + ":49", "v159.3_src", 3)
    mc(D, "447 个方块里是否包含玩家无法建造的隐藏方块？", "是，包含如 world-cell 这类隐藏/特权方块",
       ["不包含", "只包含可建造方块", "只包含逻辑方块"], "Blocks.java:6962 worldCell = new MemoryBlock(\"world-cell\")（BuildVisibility.worldProcessorOnly），仍计入 blocks.json。", F_BLOCK + ":6962", "v159.3_src", 3)
    mc(D, "炮塔的射程/伤害/装填时间能在 data/game/blocks.json 里查到吗？", "不能，blocks.json 的 turret 条目没有这些字段",
       ["能，都在 requirements 里", "能，在 consumers 里", "能，在 craftTime 里"], "blocks.json 字段仅 id,name,size,health,category,hasPower,requirements,consumers,outputs,craftTime；弹道/弹药数据需查源码。", F_BJSON, "both", 3)
    mc(D, "为什么 3×3 的核心（core-shard）物品容量远大于 2×2 容器？", "不同方块类的 itemCapacity 各自定义，与 size 无固定换算",
       ["容量 = size²×100", "因为核心不可破坏", "因为核心有电力"], "core-shard 4000/3×3、container 300/2×2，说明容量不随面积线性推导。", F_ATTR + "#core-shard", "v159.3_src", 3)
    mc(D, "block_attrs.json 的 build.cost 与 blocks.json 的 requirements 应当一致吗？", "应当一致（同一份 Blocks.java 定义的两个投影）",
       ["必然不同", "requirements 更权威", "cost 是随机生成"], "两处都来自 content/Blocks.java 的 requirements(...) 调用。", F_BLOCK, "v159.3_src", 2)
    mc(D, "blocks.json 的 consumers 与 outputs 字段描述什么？", "输入/输出的物品或液体列表（配方）",
       ["电力网络", "伤害类型", "建造时间"], "data/game/blocks.json 字段定义；如 impact-reactor consumers 含 blast-compound。", F_BJSON, "both", 2)
    mc(D, "hasPower 字段为 true 表示？", "该方块接入了电力网络（耗电或发电）",
       ["只能发电", "只能耗电", "有独立电网"], "blocks.json 的 hasPower 字段源自 Block.hasPower（ConsumePower.apply 会置 true）。", F_BJSON, "both", 2)
