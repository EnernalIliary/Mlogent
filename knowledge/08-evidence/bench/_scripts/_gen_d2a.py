# -*- coding: utf-8 -*-
"""域 7-9：读写感知 / 绘制文本 / 世界交互。"""
from _gen_core import *

def build_io():
    D = "读写感知"
    short(D, "memory-cell（记忆库）有多少个存储格？", "64 个",
          "Blocks.java:6872-6875 memoryCell = new MemoryBlock(\"memory-cell\"){{ memoryCapacity = 64; }}", F_BLOCK + ":6875", "v159.3_src", 1)
    short(D, "memory-bank（记忆库组）有多少个存储格？", "512 个",
          "Blocks.java:6878-6881 memoryBank：memoryCapacity = 512, size = 2。", F_BLOCK + ":6881", "v159.3_src", 1)
    short(D, "MemoryBlock 类里 memoryCapacity 的默认值是多少？", "32",
          "world/blocks/logic/MemoryBlock.java:12 public int memoryCapacity = 32;", F_MEM + ":12", "v159.3_src", 1)
    mc(D, "read 语句默认读哪个方块？", "cell1",
       ["bank1", "display1", "message1"], "LStatements.java:63 ReadStatement: output=\"result\", target=\"cell1\", address=\"0\"。", F_STMT + ":63", "v159.3_src", 1)
    mc(D, "read 语句的第一个参数（文本里第一段）是什么？", "结果输出变量",
       ["目标方块", "地址", "读到的值"], "LStatements.java:63 字段序 output/target/address，界面上先填 output。", F_STMT + ":63", "v159.3_src", 1)
    short(D, "getlink 的索引是从 0 开始还是从 1 开始？", "从 0 开始",
          "instr_semantics.json#getlink: params=[output,index], defs=[0]，index 0 对应第一个链接方块。", F_INSTR + "#getlink", "v159.3_src", 1)
    mc(D, "read 读越界地址（address >= 容量）会得到什么？", "NaN（而不是 0）",
       ["0", "null", "报错并停产"], "MemoryBlock.java:65-69：output.setnum(address < 0 || address >= memory.length ? Double.NaN : memory[address])。", F_MEM + ":68", "v159.3_src", 2)
    mc(D, "write 写越界地址会怎样？", "静默忽略，不报错",
       ["写入 0 号格", "整个记忆库清零", "抛出异常"], "MemoryBlock.java:77-81：if(address < 0 || address >= memory.length) return;", F_MEM + ":79", "v159.3_src", 2)
    mc(D, "读别的队伍的记忆库会怎样？", "读写都被拒绝（返回 null / 无操作），除非处理器具 privileged 权限",
       ["照常可读", "读到 0", "自动反编译"], "MemoryBlock.java:60-62 readable(): isValid() && (exec.privileged || (this.team == exec.team && !this.block.privileged))。", F_MEM + ":60", "v159.3_src", 3)
    mc(D, "sensor 语句的第三个参数（type 槽）放什么？", "属性名（LAccess）或内容常量，如 @totalItems、@copper",
       ["结果变量", "目标方块", "行号"], "instr_semantics.json#sensor: params=[result,from,type], defs=[0], uses=[1,2]。", F_INSTR + "#sensor", "v159.3_src", 2)
    mc(D, "control 语句的 type 默认值是什么？", "enabled",
       ["shoot", "config", "color"], "LExecutor.java:557 ControlI: public LAccess type = LAccess.enabled;", F_EXEC + ":557", "v159.3_src", 2)
    mc(D, "control 语句能操作哪些属性？", "LAccess 中带参数的那几个：enabled / shoot / shootp / config / color",
       ["任意 LAccess 属性", "只有 enabled", "任意方块字段"], "LAccess.java:controls = Seq.select(all, t -> t.params.length > 0)，对应 enabled(\"to\")、shoot、shootp、config、color。", F_LACC + "#controls", "v159.3_src", 2)
    mc(D, "control 的目标方块必须是？", "处理器已链接/可访问的方块（或 privileged 模式下任意方块）",
       ["任意方块", "只有炮塔", "只有工厂"], "LExecutor.java:574：exec.privileged || (exec.build != null && exec.build.validLink(b))。", F_EXEC + ":574", "v159.3_src", 3)
    code(D, "用 read 读 cell1 的第 0 格并打印，写法正确的是哪段？",
         ["read result cell1 0", "print result", "printflush message1"],
         "先 read 到变量再 print，最后 printflush 输出",
         "ReadStatement 默认 output=result/target=cell1/address=0（LStatements.java:63）；print 只进文本缓冲，需 printflush。", F_STMT + ":283-303", "v159.3_src", 2)
    mc(D, "@links 表示什么？", "处理器当前已链接的方块数量（只读变量）",
       ["链接方块的坐标数组", "可变寄存器", "内存容量"], "GlobalVars.java 的 putEntryOnly(\"@links\")；只读变量表把 @links 列为链接计数。", F_GV + ":45", "v159.3_src", 2)
    mc(D, "read 与 sensor 的核心区别是？", "read 按地址读存储格；sensor 按属性名读方块字段",
       ["read 只能读数字，sensor 能读对象", "两者等价", "sensor 只能读单位"], "ReadI 走 LReadable.read(position, output)（LExecutor.java:627-632）；SenseI 走 sense/senseObject（LExecutor.java:668-719）。", F_EXEC + ":612-719", "v159.3_src", 2)
    mc(D, "LAccess.settable 直接允许写的属性集合是？", "x,y,velocityX,velocityY,rotation,speed,armor,health,shield,team,flag,totalPower,payloadType,bulletTime,bulletLifetime",
       ["全部 105 行 LAccess 枚举值", "只有 x,y", "只有 health"], "LAccess.java 末尾：settable = {x, y, velocityX, velocityY, rotation, speed, armor, health, shield, team, flag, totalPower, payloadType, bulletTime, bulletLifetime}。", F_LACC + "#settable", "v159.3_src", 3)
    mc(D, "要让 read 语句能访问 cell1，前置条件是？", "把该记忆库链接到处理器（成为 links 之一）",
       ["把 cell1 放进核心", "给处理器开 privileged", "把地址设为 -1"], "read 的 target 是 LVar，其值必须是 LReadable 对象；链接由逻辑处理器范围 80 tile 内的链接方块提供。", F_EXEC + ":626-632", "v159.3_src", 2)
    calc(D, "把 memory-cell 的 64 个格子逐个写一遍，至少需要多少条 write 语句（不含循环开销）？", "64 条", "64 条",
         "每格一条 write；容量 64 见 Blocks.java:6875。", F_BLOCK + ":6875", "v159.3_src", 2)
    mc(D, "write 的目标不是可写方块（LWritable）时会发生什么？", "静默无操作",
       ["写入最近的内存块", "抛异常", "清空变量"], "LExecutor.java:659-665 WriteI：if(targetObj instanceof LWritable){...}，否则什么都不做。", F_EXEC + ":659-665", "v159.3_src", 3)
    mc(D, "read 的目标是一个字符串（CharSequence）时会读到什么？", "该地址上字符的 char 码（越界为 NaN）",
       ["null", "字符串长度", "直接报错"], "LExecutor.java:635-636：output.setnum(address < 0 || address >= str.length() ? Double.NaN : (int)str.charAt(address))。", F_EXEC + ":635-636", "v159.3_src", 3)
    mc(D, "read 的目标是一个序列（Seq，如 query 的结果）时会读到什么？", "该索引处的元素对象（越界为 null）",
       ["元素数量", "NaN", "首个元素"], "LExecutor.java:637-638：output.setobj(address < 0 || address >= seq.size ? null : seq.get(address))。", F_EXEC + ":637-638", "v159.3_src", 3)
    mc(D, "write 的 value 槽实际写入记忆库的是什么？", "value.num()，即数值（内容对象也被取数值）",
       ["任意对象", "字符串", "对象引用"], "MemoryBlock.java:80 memory[address] = value.num();", F_MEM + ":80", "v159.3_src", 3)
    mc(D, "read/write 的 address 槽只能用常量吗？", "可以放任意变量或运算结果",
       ["必须常量", "必须是 @ 常量", "只能 0"], "ReadI.java:634 int address = position.numi()，position 是 LVar。", F_EXEC + ":634", "v159.3_src", 3)
    mc(D, "想在多人游戏中同步一个变量给其他玩家，用哪条语句？", "sync",
       ["write", "print", "setprop"], "LStatements.java:2137 @RegisterStatement(\"sync\")；SyncI 在 LExecutor.java:2054-2074 把变量加入网络同步列表。", F_STMT + ":2137", "v159.3_src", 3)

def build_draw():
    D = "绘制文本"
    short(D, "LogicDisplay 的 displaySize 默认值是多少？", "64（绘制平面 64×64）",
          "world/blocks/logic/LogicDisplay.java:53 public int displaySize = 64;", F_DISP + ":53", "v159.3_src", 1)
    short(D, "LogicDisplay 的 maxSides 默认值是多少？", "25",
          "LogicDisplay.java:51 public int maxSides = 25;", F_DISP + ":51", "v159.3_src", 1)
    short(D, "处理器文本缓冲的最大长度（maxTextBuffer）是多少？", "400 字符",
          "LExecutor.java:46 maxTextBuffer = 400。", F_EXEC + ":46", "v159.3_src", 1)
    short(D, "处理器绘制命令缓冲的最大条数（maxGraphicsBuffer）是多少？", "256",
          "LExecutor.java:44 maxGraphicsBuffer = 256。", F_EXEC + ":44", "v159.3_src", 1)
    short(D, "显示器能缓存的最大绘制指令数（maxDisplayBuffer）是多少？", "1024",
          "LExecutor.java:45 maxDisplayBuffer = 1024。", F_EXEC + ":45", "v159.3_src", 1)
    mc(D, "printflush 的默认目标方块是？", "message1",
       ["display1", "cell1", "switch1"], "LStatements.java:388 PrintFlushStatement: target = \"message1\"。", F_STMT + ":388", "v159.3_src", 1)
    mc(D, "drawflush 的默认目标方块是？", "display1",
       ["message1", "cell1", "bank1"], "LStatements.java:367 DrawFlushStatement: target = \"display1\"。", F_STMT + ":367", "v159.3_src", 1)
    short(D, "LogicDisplay 定义了从 0 到 15 共多少种绘制命令？", "16 种",
          "LogicDisplay.java:23-43 commandClear=0 … commandResetTransform=15。", F_DISP + ":23-43", "v159.3_src", 1)
    mc(D, "print 输出一个接近整数的浮点（如 3.0000001）时会打印成？", "取整后的 3",
       ["3.0000001", "NaN", "3.0"], "LExecutor.java:1066-1067：|v-round(v)| < 0.00001 时 append(Math.round(v))。", F_EXEC + ":1066", "v159.3_src", 2)
    mc(D, "format 语句的占位符长什么样？", "{0}、{1} … {9}（单个数字）",
       ["%s", "0", "{{0}}"], "LExecutor.java:1127-1133：识别 { 数字 } 且只有一位数字。", F_EXEC + ":1127-1133", "v159.3_src", 2)
    mc(D, "一次 format 语句能替换几个占位符？", "一个（数字最小的那个）",
       ["全部", "最多 3 个", "按出现顺序全部"], "LExecutor.java:1124-1139：placeholderNumber 从 10 开始取最小 numChar，只 replace 一处。", F_EXEC + ":1124-1139", "v159.3_src", 3)
    mc(D, "print 一个内容常量（如 @copper）会打印出什么？", "内容的名字（copper）",
       ["[content]", "物品 id 数字", "null"], "LExecutor.java:1074-1084 PrintI.toString：MappableContent → content.name。", F_EXEC + ":1078", "v159.3_src", 2)
    mc(D, "print 一个 null 会打印出什么？", "null 四个字符",
       ["空", "0", "报错"], "LExecutor.java:1076：obj == null ? \"null\"。", F_EXEC + ":1076", "v159.3_src", 2)
    mc(D, "printchar 语句的作用是？", "把单个字符（char 码）追加到文本缓冲",
       ["打印整个字符串", "清空文本缓冲", "换行"], "LStatements.java:304 @RegisterStatement(\"printchar\")；PrintCharI 在 LExecutor.java:1088。", F_STMT + ":304", "v159.3_src", 2)
    mc(D, "print 的数字与文本缓冲满了之后会怎样？", "超出部分被丢弃（打印被跳过）",
       ["自动 printflush", "覆盖开头内容", "缓冲自动扩容"], "LExecutor.java:1057 if(exec.textBuffer.length() >= maxTextBuffer) return;，maxTextBuffer=400。", F_EXEC + ":1057", "v159.3_src", 2)
    code(D, "打印 1 和 2（连在一起）到 message1，程序怎么写？",
         ["print 1", "print 2", "printflush message1"],
         "print 1 / print 2 / printflush message1 —— 输出 12",
         "print 只追加到文本缓冲，printflush 才输出到 message 方块（LStatements.java:388）。", F_STMT + ":283-303", "v159.3_src", 2)
    mc(D, "draw 语句的颜色是用哪种数值表示的？", "打包成一个浮点数的 RGBA（packcolor 生成的位模式）",
       ["0-255 整数", "3 个独立参数", "十六进制字符串"], "LExecutor.java:932-942 DrawI：commandColorPack 时从 double 位里解出 r,g,b,a。", F_EXEC + ":932-942", "v159.3_src", 2)
    code(D, "在显示器上画一个矩形，程序应该包含哪些语句？",
         ["draw color 1 0 0 1", "draw rect 10 10 20 20", "drawflush display1"],
         "先 draw color 设置颜色，再 draw rect 画矩形，最后 drawflush display1",
         "draw 命令写入 graphicsBuffer，drawflush 才送到显示器（DrawI:910-1024、DrawFlushI:1026）。", F_EXEC + ":910-1024", "v159.3_src", 2)
    mc(D, "drawflush 之前不调用任何 draw 语句会怎样？", "显示器保持上一帧内容（没有新命令可刷）",
       ["显示器清空", "程序报错", "自动 clear"], "DrawFlushI 只是把 graphicsBuffer 里的命令推给显示器，空缓冲就什么也推不过去。", F_EXEC + ":1026", "v159.3_src", 2)
    mc(D, "在无头服务器（headless）上执行 draw 会怎样？", "直接返回，不产生任何绘制命令",
       ["正常绘制", "崩溃", "写入 message"], "LExecutor.java:930 if(Vars.headless || exec.graphicsBuffer.size >= maxGraphicsBuffer) return;", F_EXEC + ":930", "v159.3_src", 3)
    mc(D, "一个 tick 内 draw 次数超过 256 后会怎样？", "超出部分被丢弃（缓冲满即 return）",
       ["自动分行", "覆盖前 256 条", "扩展到 1024"], "LExecutor.java:930 graphicsBuffer.size >= maxGraphicsBuffer(=256) 时 return。", F_EXEC + ":930", "v159.3_src", 3)
    mc(D, "把文本缓冲里的内容画到显示器上，用的是哪个 draw 命令？", "draw print（commandPrint=11）",
       ["draw text", "draw image", "printflush"], "LogicDisplay.java:37 commandPrint = 11，DrawI:943-960 把 textBuffer 逐字符画到显示器。", F_DISP + ":37", "v159.3_src", 3)
    mc(D, "format 替换后文本缓冲超过 400 字符会怎样？", "截断到 400",
       ["整段丢弃", "自动换行", "保留最后 400"], "LExecutor.java:1155-1156 if(textBuffer.length() > maxTextBuffer) setLength(maxTextBuffer)。", F_EXEC + ":1155", "v159.3_src", 3)
    code(D, "画 4 条平行线到显示器，最少需要几条 draw 语句（不含 drawflush）？",
         ["draw color 1 1 1 1", "draw line 0 0 64 0", "draw line 0 16 64 16", "draw line 0 32 64 32", "draw line 0 48 64 48", "drawflush display1"],
         "4 条 draw line（颜色另算 1 条）", "每条线一条 draw line 命令；颜色状态只需设置一次。", F_EXEC + ":910-1024", "v159.3_src", 3)
    mc(D, "print 与 message 语句的区别是？", "print 写入处理器文本缓冲、需 printflush 才显示；message 直接弹出各类提示",
       ["两者完全等价", "message 只能写数字", "print 直接显示在屏幕上"], "PrintI 见 LExecutor.java:1045-1087；message 走 FlushMessageI（LExecutor.java:1889-1945）。", F_EXEC + ":1045", "v159.3_src", 3)

def build_world():
    D = "世界交互"
    short(D, "TileLayer 枚举有哪四个值？", "floor、ore、block、building",
          "logic/TileLayer.java: floor, ore, block, building；可写集合 settable={floor,ore,block}。", F_TLAYER, "v159.3_src", 1)
    short(D, "LogicRule 枚举一共有多少条规则？", "29 条",
          "logic/LogicRule.java：currentWaveTime…rtsMinSquad，共 29 项。", F_LRULE, "v159.3_src", 1)
    mc(D, "setblock 不能改写哪一种 tile 层？", "building（建筑层不可用 setblock 写）",
       ["floor", "ore", "block"], "TileLayer.java: settable = {floor, ore, block}，building 不在其中。", F_TLAYER, "v159.3_src", 2)
    mc(D, "message 语句支持哪一种类型不是有效的？", "chat",
       ["notify", "announce", "toast"], "logic/MessageType.java: notify, announce, toast, mission 四种。", F_MSGT, "v159.3_src", 1)
    mc(D, "cutscene 语句支持哪些动作？", "pan、zoom、stop",
       ["pan、zoom、rotate", "play、stop", "lock、unlock"], "logic/CutsceneAction.java: pan, zoom, stop。", F_CUT, "v159.3_src", 1)
    mc(D, "weathersense 语句的作用是？", "读取当前地图的天气强度或状态到变量",
       ["设置天气", "播放天气音效", "清除天气"], "LStatements.java:1627 weathersense；SenseWeatherI 在 LExecutor.java:1683。", F_STMT + ":1627", "v159.3_src", 2)
    mc(D, "spawn 语句默认生成什么单位？", "@dagger",
       ["@crawler", "@flare", "@alpha"], "LStatements.java:1465 SpawnStatement: type=\"@dagger\", x=\"10\", y=\"10\", rotation=\"90\", team=\"@sharded\"。", F_STMT + ":1465", "v159.3_src", 1)
    mc(D, "spawn 语句默认生成到哪个队伍？", "@sharded",
       ["@crux", "@derelict", "@green"], "LStatements.java:1465 team = \"@sharded\"。", F_STMT + ":1465", "v159.3_src", 1)
    mc(D, "getblock 语句的参数顺序是？", "layer 在最前：layer, block, x, y",
       ["x, y, layer, block", "block, layer, x, y", "x, y, block, layer"], "LStatements.java:1359-1398 GetBlockStatement 字段序 layer 在前（与很多玩家直觉相反）。", F_STMT + ":1359-1398", "v159.3_src", 3)
    mc(D, "setblock 语句一共有几个参数？", "6 个：layer, block, x, y, team, rotation",
       ["4 个", "5 个", "7 个"], "LStatements.java:1400-1461 SetBlockStatement 字段 layer,block,x,y,team,rotation。", F_STMT + ":1400-1461", "v159.3_src", 2)
    mc(D, "status 语句的第一个参数（index0）是什么？", "布尔字面量：true 表示施加、false 表示移除",
       ["单位", "状态效果名", "时长"], "LStatements.java:1568-1625：status 的 index0 是 clear/apply 的布尔值（文档常写错成单位）。", F_STMT + ":1568-1625", "v159.3_src", 3)
    mc(D, "effect 语句的作用是？", "在指定坐标播放一个特效（纯视觉）",
       ["造成范围伤害", "生成单位", "修改方块"], "LStatements.java:1946 effect；EffectI 在 LExecutor.java:1947-1976。", F_STMT + ":1946", "v159.3_src", 2)
    mc(D, "explosion 语句与 effect 语句的关键区别是？", "explosion 会造成真实范围伤害（effect 只是视觉）",
       ["explosion 只是视觉", "两者等价", "effect 会伤害方块"], "LStatements.java:2008 explosion；ExplosionI 在 LExecutor.java:1976-2017 调用真实爆炸伤害。", F_STMT + ":2008", "v159.3_src", 2)
    mc(D, "setrule 能修改下列哪一组东西？", "waveTimer、waves、unitCap、buildSpeed 等游戏规则",
       ["方块血量", "单位类型属性", "玩家背包"], "logic/LogicRule.java 29 条规则（waveTimer/waves/unitCap/buildSpeed…）；SetRuleI 在 LExecutor.java:1753。", F_LRULE, "v159.3_src", 2)
    mc(D, "weatherset 与 weathersense 的关系是？", "weatherset 设置天气，weathersense 读取天气",
       ["两者都是读", "两者都是写", "weatherset 已废弃"], "LStatements.java:1627 weathersense、1682 weatherset；对应 LExecutor.java:1683、1697。", F_STMT + ":1627-1736", "v159.3_src", 2)
    mc(D, "getflag 与 setflag 操作的是什么？", "全局 flag 位（与 @flag 属性不同，是全局标记）",
       ["单个方块的 flag 属性", "玩家名字", "地图标记"], "LStatements.java:2198 getflag、2229 setflag；LExecutor.java:2101、2131。", F_STMT + ":2198-2260", "v159.3_src", 2)
    mc(D, "sync 语句在单人游戏里的行为是？", "仍然可用，只是网络同步无意义",
       ["直接报错", "禁用处理器", "自动跳过整条程序"], "SyncI（LExecutor.java:2054-2074）把变量加入同步表，单人无对端但语句照常执行。", F_EXEC + ":2054-2074", "v159.3_src", 3)
    code(D, "把当前波次设为 10 并立刻发一波，最少需要哪些语句？",
         ["setrule wave 10", "spawnwave 1 0 0"],
         "setrule wave 10 + spawnwave（参数以实际地图为准）",
         "setrule 走 LogicRule.wave；spawnwave 走 SpawnWaveI（LExecutor.java:2151）。", F_STMT + ":1736", "v159.3_src", 3)
    mc(D, "query 语句能查询哪些类型？", "unit 与 building（bullet 因为对象池引用过期而不可查）",
       ["unit、building、bullet", "只有 unit", "只有 bullet"], "logic/QueryType.java: queryable = {unit, building}，注释写明 bullets are bugged due to stale references。", F_QTYPE, "v159.3_src", 3)
    mc(D, "query 语句支持哪些形状？", "circle 与 rect 两种",
       ["circle 一种", "rect 一种", "circle、rect、triangle"], "logic/QueryShape.java: circle, rect。", F_QSHAPE, "v159.3_src", 2)
    mc(D, "fetch 语句能取哪些计数/对象？", "unit/unitCount/player/playerCount/core/coreCount/build/buildCount 共 8 种",
       ["只有 unit 与 building", "6 种", "10 种"], "logic/FetchType.java: unit, unitCount, player, playerCount, core, coreCount, build, buildCount。", F_FETCH, "v159.3_src", 2)
    mc(D, "spawnwave 语句的第一个参数表示什么？", "要生成的波次编号（1 起）",
       ["生成单位数量", "地图编号", "难度"], "LStatements.java:1736 spawnwave；SpawnWaveI 在 LExecutor.java:2151 按波次索引生成。", F_STMT + ":1736", "v159.3_src", 2)
    mc(D, "把 getblock 的 layer 写成 building 会得到什么？", "读取该坐标的建筑对象（building 层可读）",
       ["语法错误", "永远是 null", "读取地板"], "TileLayer.building 不可 setblock，但 getblock 读取 building 层是有效用法（settable 只限制写）。", F_TLAYER, "v159.3_src", 3)
    mc(D, "spawn 语句的 team 参数能用于生成敌方单位吗？", "能，把 team 赋成 @crux 等敌方队伍常量即可",
       ["不能，只能生成己方", "只能生成 derelict", "team 参数被忽略"],
       "LStatements.java:1465 spawn 的 team 默认 @sharded，但作为普通参数可传任意队伍常量。", F_STMT + ":1465", "v159.3_src", 2)
    mc(D, "query 查到的结果要怎么取出具体元素？", "用 read 按索引读（结果是 Seq，read 会取该索引元素）",
       ["用 sensor 读", "结果自动写入 @unit", "无法取出"],
       "LExecutor.java:637-638 ReadI 对 Seq 目标按索引取元素，query 结果变量正是 Seq。", F_EXEC + ":637-638", "v159.3_src", 2)
