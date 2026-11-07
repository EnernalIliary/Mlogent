# -*- coding: utf-8 -*-
"""域 1-6：执行模型 / 变量与作用域 / 控制流 / 读写感知 / 绘制文本 / 世界交互。"""
from _gen_core import *

def build_exec():
    D = "执行模型"
    short(D, "LExecutor 允许的单个处理器程序最多多少条指令（默认上限常量）？", "1000 条",
          "LExecutor.java:41 public static int maxInstructions = 1000;", F_EXEC + ":41", "v159.3_src", 1)
    short(D, "LogicBlock 的 instructionsPerTick 默认值是多少？", "1（每 tick 1 条）",
          "LogicBlock.java:46 public int instructionsPerTick = 1;", F_LOGICB + ":46", "v159.3_src", 1)
    short(D, "LogicBlock 的 maxInstructionScale 默认值是多少？", "5",
          "LogicBlock.java:45 public int maxInstructionScale = 5;", F_LOGICB + ":45", "v159.3_src", 1)
    short(D, "LogicBlock 的 maxInstructionsPerTick 默认值是多少（源码注释标 privileged only）？", "40",
          "LogicBlock.java:47-48 //privileged only + public int maxInstructionsPerTick = 40;", F_LOGICB + ":47-48", "v159.3_src", 1)
    calc(D, "处理器方块 LogicBlock 的连接范围写成 8 * 10，等于多少 tile？", "8 * 10", "80 tile",
         "LogicBlock.java:49 public float range = 8 * 10;", F_LOGICB + ":49", "v159.3_src", 1)
    short(D, "instr_semantics.json 收录的语句与运算符各多少个？", "语句 53 个、运算符 45 个",
          "tools/instr_semantics.json 顶层 instructions=53、ops=45。", F_INSTR + "#instructions", "v159.3_src", 1)
    mc(D, "游戏逻辑以 tick 为最小时间单位，1 tick 等于多少秒？", "1/60 秒",
       ["1/50 秒", "1/30 秒", "1 秒"], "VERSION.md：能量 1 单位/tick = 60/s，即 1 tick = 1/60 s。", F_VER, "both", 1)
    mc(D, "执行到 end 语句时 @counter 会被设成什么？", "@counter = 指令总数（下一 tick 从头重新执行）",
       ["@counter = 0（同一 tick 内立即从头）", "@counter 不变（继续下一条）", "@counter = -1（永久停机）"],
       "LStatements.java:968-977 -> EndI（LExecutor.java:897-903）sets @counter = instructions.length。", F_STMT + ":968-977", "v159.3_src", 2)
    mc(D, "stop 语句执行时对 @counter 做了什么？", "counter--（回退一条），并 yield=true、stop=true",
       ["counter++", "counter 置 0", "counter 置为指令总数"],
       "LStatements.java:856-865 -> StopI（LExecutor.java:1236-1245）：counter--, yield=true, stop=true。", F_STMT + ":856-865", "v159.3_src", 2)
    mc(D, "wait 语句的参数单位是什么？", "秒（等待 value 秒后才继续）",
       ["tick", "毫秒", "指令条数"], "LStatements.java:835-846 -> WaitI（LExecutor.java:1206-1234）: yields until value seconds elapsed。", F_STMT + ":835-846", "v159.3_src", 2)
    mc(D, "想修改 @ipt（每 tick 指令数），正确的语句是？", "setrate",
       ["set @ipt", "op add @ipt", "control @ipt"], "SetRateI 直接写 exec.build.ipt 与 exec.ipt，绕过 LVar 常量检查，是唯一能改 @ipt 的语句（LStatements.java:2045-2060）。", F_STMT + ":2045-2060", "v159.3_src", 2)
    mc(D, "mlog 文本里参数的出现顺序由什么决定？", "语句类在 LStatements.java 中 Java 字段的声明顺序",
       ["字母序", "指令文档表格顺序", "按参数类型自动排序"], "instr_semantics.json#_notes：PARAM ORDER RULE —— mlog 文本顺序 == Java 字段声明顺序，序列化由 LogicIO.write 生成。", F_INSTR + "#_notes", "v159.3_src", 2)
    mc(D, "处理器里的 yield 与下列哪种情况直接相关？", "wait / stop 这类语句让处理器提前结束本 tick",
       ["op 运算溢出", "变量未赋值", "drawflush 失败"], "WaitI 与 StopI 都设置 yield（LStatements.java:835-846、856-865）。", F_STMT + ":835-865", "v159.3_src", 2)
    mc(D, "op 语句的 4 个参数槽（op,result,a,b）中，被写入的是哪个下标？", "1（result）",
       ["0（op）", "2（a）", "3（b）"], "instr_semantics.json#op: arity 4, defs=[1], uses=[2,3]。", F_INSTR + "#op", "v159.3_src", 2)
    mc(D, "jump 语句本身不把结果写进普通变量，但它会写哪个特殊变量？", "@counter",
       ["@ipt", "@unit", "@links"], "instr_semantics.json#jump: writes_special=[@counter]；JumpI 条件成立时把 exec.counter 改成目标行号。", F_INSTR + "#jump", "v159.3_src", 2)
    short(D, "600 条指令的程序在默认 instructionsPerTick=1 下跑完一轮需要多少 tick、多少秒？", "600 tick ≈ 10 秒",
          "LogicBlock.java:46 ipt=1；1 tick=1/60 s（VERSION.md），600/60=10 s。", F_LOGICB + ":46", "v159.3_src", 3)
    calc(D, "程序 240 条指令、ipt=1，跑完一轮需要多少 tick？", "240 / 1", "240 tick",
         "每 tick 执行 ipt 条：240/1=240 tick（=4 秒）。", F_LOGICB + ":46", "v159.3_src", 3)
    calc(D, "程序 1000 条指令（刚好触上限）、ipt=1，跑完一轮要多少秒？", "1000 / 60", "16.67 秒",
         "1000 tick ÷ 60 tick/s ≈ 16.67 s；指令上限见 LExecutor.java:41。", F_EXEC + ":41", "v159.3_src", 3)
    calc(D, "程序 300 条指令、ipt=2 时跑完一轮需要多少 tick？", "300 / 2", "150 tick（=2.5 秒）",
         "每 tick 2 条：300/2=150 tick。", F_LOGICB + ":46", "v159.3_src", 2)
    code(D, "下面程序执行完毕后最终 print 的数字是多少？",
         ["set x 5", "op add x x 3", "print x", "printflush message1"],
         "8", "op add x x 3 把 x 从 5 加到 8；print 追加到文本缓冲，printflush 输出。", F_STMT + ":283-303", "v159.3_src", 3)
    code(D, "下面程序打印几次、每次打印什么？",
         ["set i 0", "print i", "op add i i 1", "jump lessThan i 3 1"],
         "打印 0、1、2 三个数字（共 3 次）",
         "jump 的 index0 是行号 1；LParser 把标签/行号解析为行索引，i<3 时回到 print。", F_STMT + ":986-1069", "v159.3_src", 3)
    mc(D, "处理器默认 ipt=1 带来的主要后果是什么？", "长程序需要多 tick 才完成一轮，实时性受程序长度限制",
       ["长程序会被拒绝编译", "每 tick 自动执行完全部程序", "op 结果会丢精度"],
       "LogicBlock.java:45-46：maxInstructionScale=5、instructionsPerTick=1。", F_LOGICB + ":45-46", "v159.3_src", 3)
    mc(D, "把 @counter 直接 set 成某个行号会发生什么？", "下一条执行的指令跳到该行号（@counter 是 3 个特殊可写变量之一）",
       ["语法错误，@counter 只读", "整个程序重编译", "只影响下个 tick 的 ipt"],
       "instr_semantics.json#builtin_special_writable = [@counter,@ipt,@unit]；LExecutor 用 counter.numval 决定下一条。", F_INSTR + "#builtin_special_writable", "v159.3_src", 3)
    calc(D, "某处理器程序 90 条、ipt=1；其中 6 条是 sensor。忽略其它开销，跑一轮多少 tick？", "90 / 1", "90 tick（=1.5 秒）",
         "每 tick 1 条，90 条需要 90 tick。", F_LOGICB + ":46", "v159.3_src", 1)
    mc(D, "下列哪个不是 mlog 的特殊可写内建变量？", "@links",
       ["@counter", "@ipt", "@unit"], "instr_semantics.json#builtin_special_writable 只有 [@counter,@ipt,@unit]。", F_INSTR + "#builtin_special_writable", "v159.3_src", 2)

def build_var():
    D = "变量与作用域"
    short(D, "instr_semantics.json 记录的内建只读变量共有多少个？", "34 个",
          "tools/instr_semantics.json#builtin_readonly_vars 长度 34（含 @this/@thisx/@thisy/@links/@ipt…）。", F_INSTR + "#builtin_readonly_vars", "v159.3_src", 1)
    mc(D, "下列哪个属于内建只读变量（不能被 set 修改）？", "@links",
       ["@counter", "@ipt", "@unit"], "只读列表含 @links；可写特殊变量只有 [@counter,@ipt,@unit]。", F_INSTR + "#builtin_readonly_vars", "v159.3_src", 1)
    short(D, "set 语句有两个参数槽，被写入的下标是哪个？", "0（result）",
          "instr_semantics.json#set: params=[result,value], defs=[0], uses=[1]。", F_INSTR + "#set", "v159.3_src", 1)
    short(D, "setrate 唯一能修改的特殊变量是哪一个？", "@ipt",
          "SetRateI 写 build.ipt 与 ipt.numval（LStatements.java:2045-2060），writes_special=[@ipt]。", F_STMT + ":2045-2060", "v159.3_src", 1)
    mc(D, "同一处理器内不同语句块之间定义的变量是什么关系？", "共享同一张变量表（没有块级作用域）",
       ["各自独立，块内可见", "按行号分段隔离", "只在 op 内可见"], "LExecutor 用 LVar 按名字存处理器级变量，@counter 只决定下一条语句，没有块作用域概念。", F_EXEC + ":41", "v159.3_src", 2)
    mc(D, "sensor 语句的第 0 个参数（文本第一个参数）是什么？", "结果目标变量（写入处）",
       ["被读取的方块", "属性名", "过滤类型"], "instr_semantics.json#sensor: params=[result,from,type], defs=[0], uses=[1,2]。", F_INSTR + "#sensor", "v159.3_src", 2)
    mc(D, "把 @copper 这类内容常量 set 给变量后，变量保存的是什么？", "内容对象（item 常量），不是数字",
       ["id 数字", "字符串", "null"], "lookup/lookupContent 走 setobj 对象分支；@copper 是内容常量（LExecutor.java:1247-1265）。", F_EXEC + ":1247-1265", "v159.3_src", 2)
    mc(D, "想读第 2 个链接方块的坐标，正确做法是？", "先 getlink b 1，再 sensor x b @x",
       ["sensor b 1 @x", "getlink @x 1", "lookup block b 1"], "getlink params=[output,index], defs=[0]；sensor 再从方块读属性（instr_semantics.json#getlink、#sensor）。", F_INSTR + "#getlink", "v159.3_src", 2)
    code(D, "程序结束时 x 和 y 各是多少？",
         ["set x 2", "set y 3", "op mul x x y", "print x", "printflush message1"],
         "x=6，y=3", "op mul x x y：x=2*3=6，y 未被写。", F_INSTR + "#op", "v159.3_src", 2)
    short(D, "变量名在 mlog 里允许带空格或中文吗？", "不允许；变量名是单个 token",
          "LParser 按空白切 token，语句参数是独立 token，名字必须是单 token。", F_STMT + ":283-303", "v159.3_src", 2)
    mc(D, "@this 表示什么？", "当前处理器方块自身",
       ["当前执行行号", "上一条指令结果", "最近绑定的单位"], "只读变量表把 @this 列在首位，@thisx/@thisy 是它的坐标。", F_INSTR + "#builtin_readonly_vars", "v159.3_src", 2)
    mc(D, "用 set 给变量赋字符串（如 set s abc）在 v159.3 会怎样？", "mlog 没有字符串字面量，abc 会被当作变量名/内容名解析",
       ["正常得到字符串", "编译报错并终止游戏", "自动转成 ASCII 数字"], "LParser 只识别数字、内容常量与变量名；print 也只接受单个 value 参数（LStatements.java:283-303）。", F_STMT + ":283-303", "v159.3_src", 3)
    calc(D, "set a 1、set b 2 后执行 op add c a b，c 是多少？", "1 + 2", "3",
         "op add 把两个操作数相加写入 result（defs=[1]）。", F_INSTR + "#op", "v159.3_src", 1)
    mc(D, "变量在两次 end→重新开始之间会怎样？", "保留上一轮的值（@counter 重置，变量表不清空）",
       ["全部清 0", "全部变 null", "随机重置"], "end 只把 @counter 设为指令总数（LStatements.java:968-977），没有清变量表的路径。", F_STMT + ":968-977", "v159.3_src", 3)
    mc(D, "sensor 的第 2 个参数（type 槽）通常放什么？", "属性名或内容常量（如 @copper）",
       ["方块对象", "结果变量", "行号"], "instr_semantics.json#sensor: index2 是 property/content var，uses=[1,2]。", F_INSTR + "#sensor", "v159.3_src", 2)
    code(D, "下面程序输出什么？",
         ["set x 1", "op equal x x 1", "print x", "printflush message1"],
         "1（真）", "op equal 返回 1/0；x 原本是 1，1==1 为真。", F_COP + ":6", "v159.3_src", 3)
    mc(D, "想让处理器保存上一次 tick 的状态，最可靠的方式是？", "用变量（跨 tick 保留）",
       ["写进 message1", "用 print 缓冲", "每次都重新 set"], "变量表在处理器实例上跨 tick 存活，@counter 只控制执行位置。", F_STMT + ":968-977", "v159.3_src", 3)
    mc(D, "@ipt 与 @counter 的区别是？", "@ipt 是每 tick 执行指令数，@counter 是下一条指令行号",
       ["两者同义", "@ipt 是行号，@counter 是速度", "@ipt 只读"], "@ipt 由 setrate 改（LStatements.java:2045-2060），@counter 由 jump/end 改（LStatements.java:986-1069、968-977）。", F_STMT + ":986-1069", "v159.3_src", 3)
    short(D, "set rate 2 与 setrate 2 的区别是什么？", "set rate 2 只给普通变量 rate 赋值；setrate 2 改的是 @ipt",
          "只有 setrate 走 SetRateI 分支写 ipt.numval（LStatements.java:2045-2060）。", F_STMT + ":2045-2060", "v159.3_src", 3)
    mc(D, "变量名区分大小写吗？", "区分（token 按原文匹配）",
       ["不区分", "只对关键字区分", "由 @ 前缀决定"], "LParser 以 token 原文构造 LVar 名字，未做大小写折叠。", F_STMT + ":2045-2060", "v159.3_src", 3)
    calc(D, "set i 0 后连续执行 5 次 op add i i 1，i 最终是多少？", "0 + 5×1", "5",
         "每次自增 1，共 5 次。", F_INSTR + "#op", "v159.3_src", 1)
    mc(D, "@unit 属于哪一类变量？", "特殊可写变量（ubind 会改写它）",
       ["只读常量", "普通数字变量", "内容常量"], "instr_semantics.json#builtin_special_writable=[@counter,@ipt,@unit]；ubind 绑定单位即写 @unit。", F_INSTR + "#builtin_special_writable", "v159.3_src", 2)
    mc(D, "下列哪种写法最可能不被接受？", "set 1 x（把数字当目标变量）",
       ["set x 1", "op add x 1 2", "sensor r b @x"], "set 的 defs=[0] 是目标变量槽，必须是可写变量名，数字不能作目标。", F_INSTR + "#set", "v159.3_src", 2)
    mc(D, "@thisx 与 @thisy 表示什么？", "处理器自身所在的 tile 坐标",
       ["屏幕坐标", "当前单位坐标", "鼠标坐标"], "只读变量表中 @thisx/@thisy 紧邻 @this，表示本方块坐标。", F_INSTR + "#builtin_readonly_vars", "v159.3_src", 2)
    mc(D, "@counter 属于哪一类变量？", "特殊可写变量",
       ["只读变量", "内容常量", "局部变量"], "instr_semantics.json#builtin_special_writable 含 @counter，jump 与 end 都会改它。", F_INSTR + "#builtin_special_writable", "v159.3_src", 1)

def build_flow():
    D = "控制流"
    short(D, "jump 语句有 4 个参数槽（dest,op,value,compare），dest 槽（index0）保存什么？", "目标行号（LParser 把标签解析成行索引）",
          "instr_semantics.json#jump：index0 是 LINE NUMBER，不是变量；LParser.java:130-133,194-199 负责标签→行号。", F_INSTR + "#jump", "v159.3_src", 1)
    short(D, "jump 的 index1 槽放什么？", "ConditionOp 条件名（equal/lessThan/always 等）",
          "instr_semantics.json#jump：index1 是 ConditionOp token。", F_INSTR + "#jump", "v159.3_src", 1)
    short(D, "ConditionOp 一共有几个取值？", "8 个",
          "ConditionOp.java:6-13：equal/notEqual/lessThan/lessThanEq/greaterThan/greaterThanEq/strictEqual/always。", F_COP + ":6-13", "v159.3_src", 1)
    mc(D, "jump equal 判定两个数相等时用什么精度？", "绝对差 < 1e-6",
       ["精确位相等", "四舍五入到整数", "差 < 0.1"], "ConditionOp.java:6：equal(\"==\", (a,b) -> Math.abs(a-b) < 0.000001, ...)。", F_COP + ":6", "v159.3_src", 2)
    mc(D, "jump ===（strictEqual）对两个数字的比较结果是？", "恒为 false",
       ["恒为 true", "同 == 一致", "抛异常"], "ConditionOp.java:12：strictEqual(\"===\", (a,b) -> false)，数字走 lambda 分支永远 false。", F_COP + ":12", "v159.3_src", 2)
    mc(D, "select 语句从哪个 build 起才存在？", "build 150",
       ["build 146", "build 159", "一直都有"], "instr_semantics.json#select: min_build=150。", F_INSTR + "#select", "v159.3_src", 2)
    mc(D, "select 语句的语义是？", "根据条件二选一：cond(comp0,comp1) 真取 a，否则取 b",
       ["比较三对数的大小", "把 a 赋给 b", "循环执行 a 直到 b"], "SelectI（LExecutor.java:875-895）：result.set(op.test(comp0,comp1) ? a : b)，只解引用被选中的一侧。", F_EXEC + ":875-895", "v159.3_src", 2)
    mc(D, "jump 目标写标签（如 loop:）时由谁换算成行号？", "LParser 在解析阶段把标签写成行索引",
       ["LExecutor 运行时查表", "处理器方块构建时", "游戏 tick 循环"], "LParser.java:130-133,194-199 解析标签为行索引；运行时 JumpI 直接改 @counter。", F_INSTR + "#jump", "v159.3_src", 2)
    mc(D, "end 与 stop 的核心区别是？", "end 把 @counter 设为指令末尾（下一 tick 从头执行）；stop 是 counter-- 并立即 yield/stop",
       ["两者完全等价", "end 停机、stop 重跑", "end 清变量、stop 不清"], "EndI（LExecutor.java:897-903）与 StopI（LExecutor.java:1236-1245）实现不同。", F_STMT + ":856-977", "v159.3_src", 3)
    code(D, "下面程序打印什么？",
         ["set x 0", "jump greaterThan x 0 4", "op add x x 1", "jump always 1", "print x", "printflush message1"],
         "1", "x=0 时 0>0 为假，跳到行 2 自增成 1；再 jump always 回行 1，此时 1>0 为真跳到行 4，打印 x=1。", F_STMT + ":986-1069", "v159.3_src", 3)
    code(D, "下面程序会打印几个数字？",
         ["set i 0", "jump greaterThanEq i 3 5", "print i", "op add i i 1", "jump always 1", "printflush message1"],
         "打印 0、1、2，共 3 个", "i 从 0 递增到 3 时跳出；每次先 print 再自增。", F_STMT + ":986-1069", "v159.3_src", 3)
    mc(D, "若 jump 的目标行号大于程序长度会发生什么？", "相当于执行到程序末尾，本轮结束",
       ["回到第 0 行", "编译报错", "立即崩溃"], "JumpI 直接把行号写进 @counter，执行循环以 instructions.length 为上界（LExecutor.java:1183-1204）。", F_EXEC + ":1183-1204", "v159.3_src", 2)
    calc(D, "程序第 0-9 行为有效指令，jump 到行号 10 等价于跳到第几条语句？", "10（0 基下标，即末尾）", "行号 10",
         "mlog 行号 0 基（instr_semantics.json#_notes 的 index_base 说明参数下标从 0 起）。", F_INSTR + "#_notes", "v159.3_src", 1)
    mc(D, "jump lessThan 与 jump lessThanEq 的差别是？", "< 与 <=（相等时分支不同）",
       ["符号相同", "一个比较数与数、一个比较对象", "一个可跳转、一个不可"], "ConditionOp.java:8-9：lessThan(\"<\") 与 lessThanEq(\"<=\")。", F_COP + ":8-9", "v159.3_src", 1)
    code(D, "这段代码的 bug 是什么？",
         ["set i 0", "print i", "op add i i 1"],
         "缺少回跳 jump，只打印一次就结束",
         "mlog 没有隐式循环，顺序执行到末尾即本轮结束。", F_STMT + ":986-1069", "v159.3_src", 3)
    mc(D, "notEqual 的文本符号串写作什么？", "not",
       ["!=", "notEqual", "<>"], "ConditionOp.java:7：notEqual(\"not\", ...)。", F_COP + ":7", "v159.3_src", 2)
    mc(D, "写 jump equal x 0 0 时最容易踩的坑是？", "index0 是行号，最后那个 0 才是被比较的常量",
       ["行号必须写标签", "equal 只比较对象", "0 不能作比较值"], "参数顺序是 dest,op,value,compare（instr_semantics.json#jump）。", F_INSTR + "#jump", "v159.3_src", 2)
    code(D, "下面的循环会执行多少次 op add？",
         ["set n 0", "op add n n 1", "jump lessThan n 4 1"],
         "4 次（n 依次 1,2,3,4，n<4 为假时停止）",
         "n 从 0 起每次 +1；n=4 时 4<4 为假跳出。", F_STMT + ":986-1069", "v159.3_src", 3)
    mc(D, "jump 里给 value/compare 传变量名（而非常量）可以吗？", "可以，这两个槽是普通读取槽（uses=[2,3]）",
       ["不可以，必须是常量", "只能传数字", "只能传 @ 常量"], "instr_semantics.json#jump: uses=[2,3]；只有 dest 与 op 是结构槽。", F_INSTR + "#jump", "v159.3_src", 2)
    mc(D, "把 jump 的 op 写成不存在的名字，v159.3 的行为是？", "LParser 把整条语句替换成 noop（无效语句）",
       ["抛异常终止游戏", "自动当成 always", "编译成 set"], "instr_semantics.json#noop 注：LParser 对未知语句用 InvalidStatement 替代（LParser.java:146,173）。", F_INSTR + "#noop", "v159.3_src", 3)
    mc(D, "下列哪种写法能实现先判断再执行的 while 语义？", "条件成立才进入循环体，循环体末尾无条件 jump 回条件处",
       ["循环体末尾用 end", "用 stop 代替 jump", "用 wait 代替 jump"], "需要 always 回跳 + 条件跳转两个 jump（LStatements.java:986-1069）。", F_STMT + ":986-1069", "v159.3_src", 2)
    calc(D, "循环 0..9 共 10 次迭代，每次 1 条 op + 1 条 jump，共执行多少条语句？", "10 × 2", "20 条",
         "10 次迭代 × 每次 2 条语句。", F_STMT + ":986-1069", "v159.3_src", 1)
    mc(D, "标签（label）在 mlog 文本中的形式是？", "行首的 名字: ，跳转时写该名字",
       ["@名字", "名字()", "#名字"], "LParser.java:130-133,194-199 识别 label: 并登记行号。", F_INSTR + "#jump", "v159.3_src", 2)
    mc(D, "想让处理器公平地每 tick 只前进 1 条，应避免哪种写法？", "无 wait 的 jump always 死循环",
       ["带 wait 的循环", "顺序执行", "用 end 收尾"], "死循环只受 ipt 限制，会占满每 tick 的指令预算（LogicBlock.java:45-46）。", F_LOGICB + ":45-46", "v159.3_src", 2)
    mc(D, "jump 的 op 写成 always 时，value/compare 两个槽还要填吗？", "要：语法上仍是 4 槽，else 分支已恒真故这两槽被忽略（填 0 即可）",
       ["不用填，可以只写 2 个槽", "必须填真实变量", "填 null 会编译失败"], "jump 固定 4 槽 dest/op/value/compare（LStatements.java:986-1069）；ConditionOp.java:13 always 恒为 true。", F_STMT + ":986-1069", "v159.3_src", 2)
