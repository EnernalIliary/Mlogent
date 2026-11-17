#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成「跨源推导题」v2 草案：24 题 = 12 域 × 2，id BENCH.0301-0324，全部 hard。

与冻结的 300 题分开存放（questions-derive.jsonl），每题必须组合 >=2 个真源。
字段在 300 题 schema 基础上扩展：
  srcs   : [>=2 个真源，与 src 同格式]
  derive : 一句话说明「为什么必须组合」（哪两个源各提供什么）
"""
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import json
import os
import re
from pathlib import Path

REPO = Path(os.environ.get("AS_REPO", str(Path(__file__).resolve().parents[4])))
OUT = Path(__file__).resolve().parent / "questions-derive.jsonl"
SRC = "Mindustry-Source/core/src/mindustry/"

Q = []


def q(domain, typ, text, answer, why, src, srcs, derive):
    Q.append({
        "id": None, "domain": domain, "difficulty": 3, "type": typ,
        "q": text, "answer": answer, "why": why,
        "src": src, "srcs": srcs, "derive": derive,
        "ver": "both",
    })


def code_block(lines):
    fence = chr(96) * 3
    return "\n" + fence + "mlog\n" + "\n".join(lines) + "\n" + fence


# ---------------------------------------------------------------- 执行模型
q("执行模型", "calc",
  "某处理器程序共 600 条指令，instructionsPerTick 设为 2。跑完一整轮需要多少 tick、多少秒？会不会碰到指令数上限？",
  "300 tick = 5 秒；不会碰到上限（600 < 1000）。",
  "600 / 2 = 300 tick；1 tick = 1/60 s → 300/60 = 5 s。上限是 1000 条，600 条安全。",
  SRC + "world/blocks/logic/LogicBlock.java:46",
  [SRC + "world/blocks/logic/LogicBlock.java:46", SRC + "logic/LExecutor.java:41", "knowledge/VERSION.md"],
  "ipt 给除数（源码默认值），时间换算给 tick→秒（实测口径），上限常量判断是否越界。")

q("执行模型", "short",
  "单人最多只能把 ipt 调到 5，官方服务器可到 40：这两个数字分别来自哪个常量？ipt=40 时，一个 1000 条指令的程序最短跑多少 tick？",
  "5 = maxInstructionScale（默认 5，乘 ipt 基准 1）；40 = maxInstructionsPerTick（//privileged only）。1000/40 = 25 tick ≈ 0.417 秒。",
  "LogicBlock.java:45 maxInstructionScale = 5、:46 instructionsPerTick = 1（1×5=5）；:47-48 //privileged only + maxInstructionsPerTick = 40；LExecutor.java:41 上限 1000 条 → 1000/40 = 25 tick。",
  SRC + "world/blocks/logic/LogicBlock.java:45",
  [SRC + "world/blocks/logic/LogicBlock.java:45", SRC + "world/blocks/logic/LogicBlock.java:47-48", SRC + "logic/LExecutor.java:41"],
  "scale/ipt 给「单人上限」，privileged 常量给「服务器上限」，程序上限常量给分母 —— 缺任一算不出 25 tick。")

# ---------------------------------------------------------------- 变量与作用域
q("变量与作用域", "short",
  "一个 999 条指令的程序，ipt=3。第 1 个 tick 结束时执行到第几条？第 2 个 tick 结束时呢？",
  "第 1 tick 结束执行到第 3 条，第 2 tick 结束执行到第 6 条。",
  "ipt=3 → 每 tick 走 3 条；999 < 1000 上限所以整程序合法。第 n tick 结束位于第 3n 条。",
  SRC + "world/blocks/logic/LogicBlock.java:46",
  [SRC + "world/blocks/logic/LogicBlock.java:46", SRC + "logic/LExecutor.java:41"],
  "ipt 决定步进速率，1000 上限决定程序是否合法（999 合法 → 不会在第 3 tick 被截断）。")

q("变量与作用域", "calc",
  "memory-bank 有 512 个存储单元。用 read 语句逐个读到 ipt=1 的处理器变量表里，读完需要多少 tick？ipt=5 时呢？",
  "512 tick ≈ 8.53 秒；ipt=5 时 102.4 tick ≈ 1.71 秒。",
  "512 条 read 指令 / 1 条每 tick = 512 tick；512/5 = 102.4 tick；换算 512/60 ≈ 8.53 s。",
  "Mindustry-Source/core/src/mindustry/world/blocks/logic/MemoryBlock.java:12",
  ["Mindustry-Source/core/src/mindustry/content/Blocks.java:6878-6881",
   "Mindustry-Source/core/src/mindustry/world/blocks/logic/MemoryBlock.java:12",
   SRC + "world/blocks/logic/LogicBlock.java:46"],
  "容量 512 来自方块定义，默认 32 来自 MemoryBlock 字段，ipt 给吞吐 —— 三者组合才能算出耗时。")

# ---------------------------------------------------------------- 控制流
q("控制流", "calc",
  "循环体 5 条指令 + 末尾一条 wait 0.5，处理器 ipt=1。跑一轮循环占多少 tick、多少秒？跑 10 轮共多少秒？",
  "35 tick ≈ 0.583 秒/轮；10 轮 ≈ 5.83 秒。",
  "wait 0.5 秒 = 30 tick（1 tick = 1/60 s）；5 条指令 = 5 tick；合计 35 tick = 35/60 ≈ 0.583 s；×10 ≈ 5.83 s。",
  SRC + "logic/LStatements.java:835-846",
  [SRC + "logic/LStatements.java:835-846", "knowledge/VERSION.md", SRC + "world/blocks/logic/LogicBlock.java:46"],
  "wait 的语义在源码（时间参数按秒换算成 tick），秒↔tick 的口径在实测文档，ipt 决定指令本身的 tick 成本。")

q("控制流", "mc",
  "有人用 jump === 判断两个数是否相等，结果永远走不到分支里。原因与正确写法是？\nA) === 是严格相等，浮点要用 ==\nB) strictEqual 的实现是 (a,b)->false，恒为 false；要用 jump equal（|a-b|<1e-6）\nC) === 需要先 packcolor\nD) === 只对整数有效",
  "B) strictEqual 的实现是 (a,b)->false，恒为 false；要用 jump equal（|a-b|<1e-6）",
  "ConditionOp.java:12 strictEqual(\"===\", (a,b)->false) 恒 false；:6 equal 用 |a-b| < 0.000001 浮点近似比较。",
  SRC + "logic/ConditionOp.java:12",
  [SRC + "logic/ConditionOp.java:12", SRC + "logic/ConditionOp.java:6"],
  "要知道 === 恒 false（:12）还得知道替代品 equal 的精度（:6），只读一个会写错修法。")

# ---------------------------------------------------------------- 读写感知
q("读写感知", "calc",
  "print 的文本缓冲上限是 400 字符，message 方块的 maxTextLength 也是 400。想在一次 printflush 里输出 900 字符的一段说明，实际会怎样？怎么改？",
  "缓冲只保留 400 字符（超出部分被丢弃/截断），消息方块最多显示 400 字符；需拆成 3 次 printflush，或改用 3 个消息方块。",
  "LExecutor 文本缓冲 maxTextBuffer=400（PrintI 里 >=400 直接 return）；MessageBlock.java:29 maxTextLength=400。两个 400 是两个独立限制，都要满足。",
  SRC + "logic/LExecutor.java:43-46",
  [SRC + "logic/LExecutor.java:43-46", SRC + "logic/LExecutor.java:1045-1087",
   "Mindustry-Source/core/src/mindustry/world/blocks/logic/MessageBlock.java:29"],
  "缓冲上限在执行器常量里，单次 print 截断在 PrintI 里，显示上限在方块字段里 —— 三处都可能截断。")

q("读写感知", "mc",
  "memory-cell 容量 64、memory-bank 容量 512。往 memory-cell 的地址 100 写 42，再读回来得到什么？\nA) 42\nB) 越界写被静默忽略，读回 NaN\nC) 报错停机\nD) 自动扩容到 101",
  "B) 越界写被静默忽略，读回 NaN",
  "Blocks.java:6872-6875 memory-cell = 64 单元；MemoryBlock.java:77-81 越界写直接 return（不报错），:65-69 越界读返回 NaN。",
  "Mindustry-Source/core/src/mindustry/content/Blocks.java:6872-6875",
  ["Mindustry-Source/core/src/mindustry/content/Blocks.java:6872-6875",
   "Mindustry-Source/core/src/mindustry/world/blocks/logic/MemoryBlock.java:77-81",
   "Mindustry-Source/core/src/mindustry/world/blocks/logic/MemoryBlock.java:65-69"],
  "容量 64 在方块定义里，越界行为在 MemoryBlock 读写实现里 —— 两个文件缺一个就会猜错（很多人以为会报错）。")

# ---------------------------------------------------------------- 绘制文本
q("绘制文本", "calc",
  "LogicDisplay 的 maxSides=25、displaySize=64、每帧图形命令上限 256。用 draw line 画一个 25 边形并 drawflush，ipt=1 时需要多少 tick？一帧最多能画几个这样的多边形？",
  "26 tick ≈ 0.433 秒（25 条 line + 1 条 drawflush）；一帧最多 10 个（250 条命令，第 11 个会超过 256）。",
  "每边 1 条 draw line，加 1 条 drawflush = 26 tick；256/25 = 10.24 → 10 个。",
  SRC + "world/blocks/logic/LogicDisplay.java:51",
  [SRC + "world/blocks/logic/LogicDisplay.java:51", SRC + "world/blocks/logic/LogicDisplay.java:53",
   SRC + "logic/LExecutor.java:43-46"],
  "maxSides 给每多边形边数，graphicsBuffer=256 给每帧条数上限，ipt 给 tick 成本。")

q("绘制文本", "mc",
  "print 3.0000004 会显示什么？format \"{0}-{1}\" 用两个参数调用一次会输出什么？\nA) 3.0000004 与 a-b\nB) 3 与 a-{1}（每次只替换数字最小的一个占位符，要再调一次才换 {1}）\nC) 3 与 a-b\nD) 4 与 a-{1}",
  "B) 3 与 a-{1}（每次只替换数字最小的一个占位符，要再调一次才换 {1}）",
  "PrintI：数字满足 |v-round(v)| < 1e-5 时按整数打印 → 3.0000004 打印 3；FormatI:1127-1139 只替换「数字最小的」一个占位符，所以第一参数替换 {0}，{1} 保留。",
  SRC + "logic/LExecutor.java:1045-1087",
  [SRC + "logic/LExecutor.java:1045-1087", SRC + "logic/LExecutor.java:1127-1139"],
  "整数化打印规则在 PrintI，占位符逐个替换规则在 FormatI —— 两个独立坑，必须都读。")

# ---------------------------------------------------------------- 世界交互
q("世界交互", "mc",
  "getblock 的 layer 是第一个参数，setblock 的 layer 也是第一个参数但只能写 floor/ore/block。想把一格地面的 building 层「改掉」会有什么结果？\nA) 可以，任何层都能写\nB) 不能：building 层不可 setblock（settable 只有 floor/ore/block），要拆/建方块得用建筑相关操作\nC) 要用 getblock 读出来再写回\nD) 只能改成 air",
  "B) 不能：building 层不可 setblock（settable 只有 floor/ore/block）",
  "LStatements:1359-1398 getblock（layer 在前）、:1400-1461 setblock（layer,block,x,y,team,rotation）；TileLayer 的 settable 集合只有 floor/ore/block。",
  SRC + "logic/LStatements.java:1400-1461",
  [SRC + "logic/LStatements.java:1400-1461", SRC + "logic/LStatements.java:1359-1398",
   SRC + "logic/TileLayer.java"],
  "参数序在两条语句的注册代码里，可写层集合在枚举里 —— 只读 setblock 源码会以为任何层都能写。")

q("世界交互", "short",
  "spawn 语句默认参数是 type=@dagger、team=@sharded、effect=true。而自然波次表里 dagger 的 end=10、max=30。用 spawn 手工刷 100 个 dagger，与自然波次的 30 个上限是什么关系？",
  "spawn 语句本身没有 end/max 参数，不受波次表 end/max 约束（只看队伍单位上限与处理器指令预算）；波次的 max=30 只限制波次生成。",
  "LStatements:1465 SpawnStatement 默认 type=@dagger,x=10,y=10,rotation=90,team=@sharded,effect=true —— 参数里没有 end/max；Waves.java:17-40 dagger 组 end=10、max=30。",
  SRC + "logic/LStatements.java:1465",
  [SRC + "logic/LStatements.java:1465", SRC + "game/Waves.java:17-40"],
  "spawn 的默认参数表在语句注册里，波次上限在 Waves 的 SpawnGroup 里 —— 两个机制名字都叫「生成」，但互不相干。")

# ---------------------------------------------------------------- 单位控制
q("单位控制", "mc",
  "写 ucontrol move core 8 0 0 0 想让单位带半径移动，结果单位只朝 (8,0) 走。原因与正确写法？\nA) move 需要 5 个参数，少写了\nB) move 只读 x y；半径只有 approach 才读（第 3 个参数 d1）；要带半径用 ucontrol approach x y radius\nC) 半径要写进 flag\nD) move 的第三个参数是队伍",
  "B) move 只读 x y；半径只有 approach 才读（第 3 个参数 d1）；要带半径用 ucontrol approach x y radius",
  "LExecutor.java:358 case move, stop, approach, pathfind → ai.moveX=x1, ai.moveY=y1，只有 type==approach 时才 ai.moveRad=d1；LUnitControl 里 approach 是 (x, y, radius) 三参。",
  SRC + "logic/LExecutor.java:304-552",
  [SRC + "logic/LExecutor.java:304-552", SRC + "logic/LUnitControl.java"],
  "参数表在 LUnitControl（枚举），实际读哪几个参数在 LExecutor 的 UnitControlI —— 只看枚举名会以为 move 也吃半径。")

q("单位控制", "short",
  "uradar enemy ... 搜到的目标里会不会包含中立残骸（derelict）队伍的单位？为什么？",
  "不会。RadarTarget.enemy 的实现明确排除 Team.derelict，derelict 不算敌人。",
  "RadarTarget 8 值 any/enemy/ally/player/attacker/flying/boss/ground，其中 enemy 的过滤条件排除 Team.derelict；uradar 的目标枚举与排序（RadarSort 5 值）在两条不同语句里复用。",
  SRC + "logic/RadarTarget.java",
  [SRC + "logic/RadarTarget.java", SRC + "logic/RadarSort.java"],
  "目标枚举决定「谁能被选中」，排序枚举决定「多个时选谁」—— 排错题只会看排序，不看过滤。")

# ---------------------------------------------------------------- 性能限制
q("性能限制", "calc",
  "ipt=5、程序恰好 1000 条指令（上限）。跑完一轮要多少 tick？如果程序是个 noop 死循环，会怎样？",
  "200 tick ≈ 3.33 秒；死循环不会「跑完」，每 tick 只推进 5 条，除 stop/end 外永不结束。",
  "1000/5 = 200 tick = 3.33 s；maxInstructions=1000 是「程序指令数上限」，不是「每 tick 执行数」，每 tick 只执行 ipt 条。",
  SRC + "logic/LExecutor.java:41",
  [SRC + "logic/LExecutor.java:41", SRC + "world/blocks/logic/LogicBlock.java:45-46"],
  "上限常量在 LExecutor，每 tick 步进在 LogicBlock —— 混淆二者就会以为死循环会自己停。")

q("性能限制", "mc",
  "三个缓冲上限：graphicsBuffer=256、displayBuffer=1024、textBuffer=400。哪个说法对？\nA) 三者都是每帧上限，超了报错\nB) draw 超过 256 条直接 return（不报错），print 超过 400 字符截断，format 结果超 400 也截断\nC) 三者都是每秒上限\nD) 只有 textBuffer 会截断，其余会排队",
  "B) draw 超过 256 条直接 return（不报错），print 超过 400 字符截断，format 结果超 400 也截断",
  "LExecutor.java:43-46 maxGraphicsBuffer=256 / maxDisplayBuffer=1024 / maxTextBuffer=400；:930 headless 或图形缓冲已满时 draw 直接 return；PrintI 缓冲≥400 直接 return；FormatI:1155-1156 超 400 截断。",
  SRC + "logic/LExecutor.java:43-46",
  [SRC + "logic/LExecutor.java:43-46", SRC + "logic/LExecutor.java:930",
   SRC + "logic/LExecutor.java:1127-1139"],
  "三个常量在一处声明，但三处超限行为分别在 draw/print/format 的实现里，必须逐个读。")

# ---------------------------------------------------------------- 方块与锚点
q("方块与锚点", "calc",
  "logic-processor 的 size=2，建造成本 lead:320、silicon:80、graphite:60、thorium:50。它占几格？总成本多少资源？在 3×3 的区域里最多放几个？",
  "占 2×2=4 格；总成本 510（320+80+60+50）；3×3 区域最多放 1 个（放不下第二个 2×2）。",
  "size=2 → 2×2；成本四元求和 = 510；3×3 里 2×2 只能放 1 个。",
  "tools/block_attrs.json#logic-processor",
  ["tools/block_attrs.json#logic-processor", "data/game/blocks.json#logic-processor",
   "tools/block_sizes.json"],
  "成本与 size 来自 attrs（源码抽取），方块条目与 447 总数来自 blocks.json，size 映射表来自 block_sizes —— 三口径要一致。")

q("方块与锚点", "mc",
  "blocks.json 有 447 条、block_attrs.json 有 253 条、block_sizes.json 有 446 项。三者差在哪里？\nA) 都相等，只是格式不同\nB) 447=注册方块总数；253=抽取了属性（accepts/power/inputs 等）的子集；446=name→size 映射，少 1 个无 size 的特殊项\nC) 447 是含隐藏方块，253 是可见方块，446 是物品\nD) 446 是 447 减去处理器",
  "B) 447=注册方块总数；253=抽取了属性的子集；446=name→size 映射，少 1 个无 size 的特殊项",
  "meta.json 记 blocks=447；block_attrs.json 只有 253 个能从 Blocks.java 抽到 accepts/build/inputs 等属性的方块；block_sizes.json 446 项，比 447 少一个无 size 的条目。",
  "data/game/blocks.json",
  ["data/game/blocks.json", "data/game/meta.json", "tools/block_attrs.json", "tools/block_sizes.json"],
  "四个数据文件各自的统计口径不同，只报一个数字就会自相矛盾（这是 docs 里最容易写错的点）。")

# ---------------------------------------------------------------- 电力与热
q("电力与热", "calc",
  "impact-reactor 的 power=25（每 tick）、liquids=cryofluid:15/s。1 秒能发多少电？每秒消耗多少 cryofluid？换算成「每次冷却液成本」是多少电力每液体单位？",
  "1500 电力/秒；消耗 15 cryofluid/秒；1500/15 = 100 电力每单位 cryofluid。",
  "power 字段单位是每 tick → 25×60 = 1500/s（1 tick = 1/60 s）；液体消耗已在 attrs 里标 /s = 15/s；1500/15 = 100。",
  "tools/block_attrs.json#impact-reactor",
  ["tools/block_attrs.json#impact-reactor", "knowledge/VERSION.md", "data/game/liquids.json#cryofluid"],
  "power 是 /tick、liquids 是 /s（两个口径混在同一张表里），必须靠 tick 换算才能对齐 —— 这就是「差 60 倍」的坑。")

q("电力与热", "mc",
  "PowerGenerator 的 explosionRadius=12、explosionDamage=0、explosionPuddleAmount=100、explosionPuddles=10。发电厂被摧毁时实际发生什么？\nA) 半径 12 内造成 12 点伤害\nB) 半径 12 内造成 0 伤害，但生成 10 处液体（每处 100），靠液体/爆炸效果威胁周边\nC) 只是视觉特效\nD) 半径 12 内所有建筑受到 100 伤害",
  "B) 半径 12 内造成 0 伤害，但生成 10 处液体（每处 100）",
  "PowerGenerator.java:23-40：explosionRadius=12、explosionDamage=0、explosionPuddles=10、explosionPuddleAmount=100、explosionPuddleRange=tilesize*2；伤害为 0 说明威胁来自液体（如 slag 烫伤）与方块自身 flammable/solid 属性。",
  SRC + "world/blocks/power/PowerGenerator.java:23-40",
  [SRC + "world/blocks/power/PowerGenerator.java:23-40", "tools/block_attrs.json#combustion-generator",
   "data/game/liquids.json#slag"],
  "爆炸参数在 PowerGenerator，实际威胁要结合生成液体的属性（Liquids.java 的 temperature/damage）才推得出来。")

# ---------------------------------------------------------------- 液体与物流
q("液体与物流", "calc",
  "water 的 heatCapacity=0.4、temperature=0.5；cryofluid 的 heatCapacity=0.9、temperature=0.25。同样 1 单位液体升高 1 度，两者吸热比是多少？为什么反应堆用 cryofluid 而不是水？",
  "吸热比 = 0.9 : 0.4 = 2.25 : 1；cryofluid 热容更高且初始温度更低（0.25 < 0.5），冷却能力更强。",
  "Liquids.java：water heatCapacity=0.4/temperature=0.5；cryofluid heatCapacity=0.9/temperature=0.25；Liquid.java:38-46 字段默认 temperature/heatCapacity/viscosity=0.5。",
  "Mindustry-Source/core/src/mindustry/content/Liquids.java",
  ["Mindustry-Source/core/src/mindustry/content/Liquids.java", SRC + "type/Liquid.java:38-46"],
  "逐项数值在 Liquids，字段语义与默认值在 Liquid —— 只读默认值会以为所有液体都 0.5。")

q("液体与物流", "mc",
  "oil 的 viscosity=0.75、flammability=1.2、explosiveness=1.2。这三个值同时说明什么？\nA) 只是颜色不同，没有机制影响\nB) 输送更慢（粘度高）、易被点燃（易燃 1.2）、会爆炸并串联（爆炸性 1.2）—— 油管要分段并远离热源\nC) 粘度高会让它流得更快\nD) 易燃与爆炸是同一个字段",
  "B) 输送更慢（粘度高）、易被点燃、会爆炸并串联 —— 油管要分段并远离热源",
  "Liquids.java：oil viscosity=0.75（默认 0.5）、flammability=1.2、explosiveness=1.2；Liquid.java:38-46 三个字段默认值都是 0.5，oil 三项都偏离默认。",
  "Mindustry-Source/core/src/mindustry/content/Liquids.java",
  ["Mindustry-Source/core/src/mindustry/content/Liquids.java", SRC + "type/Liquid.java:38-46",
   "tools/block_attrs.json#liquid-tank"],
  "要知道默认值 0.5 才能判断 0.75/1.2 是「高」还是「低」；产量/容量还要看方块属性。")

# ---------------------------------------------------------------- 战斗与单位
q("战斗与单位", "calc",
  "dagger 的武器 damage=9、reload=26 tick。它的理论 DPS 是多少？打一个 health=150 的单位需要几发、几秒？",
  "DPS = 9 / (26/60) ≈ 20.8/秒；150/9 ≈ 17 发（16.67 上取整）；17 × 26 tick = 442 tick ≈ 7.37 秒。",
  "reload 单位是 tick（1 tick = 1/60 s）：26/60 ≈ 0.433 s/发；9/0.433 ≈ 20.8 DPS；150/9 = 16.67 → 17 发；17×26 = 442 tick ≈ 7.37 s。",
  "data/game/units.json#dagger",
  ["data/game/units.json#dagger", "knowledge/VERSION.md", SRC + "entities/bullet/BulletType.java:33"],
  "伤害与 reload 在数据表，tick→秒 在实测口径，BulletType.lifetime=40 决定子弹存活上限（远程命中还要考虑）。")

q("战斗与单位", "calc",
  "护甲公式是 max(damage - armor, minArmorDamage × damage)，minArmorDamage=0.1。用 damage=9 打 armor=4 的 mace、以及打 armor=20 的假想单位，各造成多少伤害？",
  "armor=4：max(9-4, 0.9) = 5；armor=20：max(-11, 0.9) = 0.9（10% 保底）。",
  "Damage.java:659-660 applyArmor = Math.max(damage - armor, minArmorDamage * damage)；Vars.java:133 minArmorDamage = 0.1f；mace armor=4 见 units.json。",
  SRC + "entities/Damage.java:659-660",
  [SRC + "entities/Damage.java:659-660", SRC + "Vars.java:133", "data/game/units.json#mace"],
  "公式在 Damage、保底系数在 Vars、护甲值在数据表 —— 三者缺一算不出 0.9 这个保底。")

# ---------------------------------------------------------------- 校验并落盘
DOMAINS = ["执行模型", "变量与作用域", "控制流", "读写感知", "绘制文本", "世界交互",
           "单位控制", "性能限制", "方块与锚点", "电力与热", "液体与物流", "战斗与单位"]


def norm_src(src: str):
    frag = None
    if "#" in src:
        src, frag = src.split("#", 1)
    m = re.match(r"^(.*?)(?::(\d+)(?:-(\d+))?)?$", src)
    path, l1, l2 = m.group(1), m.group(2), m.group(3)
    return path, l1, l2


for i, item in enumerate(Q, 1):
    item["id"] = f"BENCH.{300 + i:04d}"

assert len(Q) == 24, len(Q)
cnt = {}
for item in Q:
    cnt[item["domain"]] = cnt.get(item["domain"], 0) + 1
assert set(cnt) == set(DOMAINS), (set(cnt) ^ set(DOMAINS))
assert all(v == 2 for v in cnt.values()), cnt
assert [f"BENCH.{300+i:04d}" for i in range(1, 25)] == [x["id"] for x in Q]
for item in Q:
    assert item["difficulty"] == 3
    assert len(item["srcs"]) >= 2, item["id"]
    assert item["derive"]
    for s in [item["src"], *item["srcs"]]:
        path, l1, l2 = norm_src(s)
        f = REPO / path
        assert f.exists(), f"{item['id']}: missing {path}"
        if l1:
            n = sum(1 for _ in f.open(encoding="utf-8", errors="ignore"))
            assert int(l1) <= n, f"{item['id']}: {s} 行号越界（{n} 行）"

with OUT.open("w", encoding="utf-8", newline="\n") as fh:
    for item in Q:
        fh.write(json.dumps(item, ensure_ascii=False) + "\n")
print(f"wrote {OUT}  ({len(Q)} 题, {OUT.stat().st_size} bytes)")
print("domains:", {k: v for k, v in cnt.items()})
print("types:", {t: sum(1 for x in Q if x["type"] == t) for t in ("mc", "short", "calc", "code")})
