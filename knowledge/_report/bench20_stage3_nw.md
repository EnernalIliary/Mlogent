# bench 20 题检索冒烟

- 库: <scratch-dir>\kb-stage\_kb_build3\kb.sqlite3
- 题库: <repo>\knowledge\08-evidence\bench\questions.jsonl（每 15 行取 1，共 20 题；第 1,16,31,46,61,76,91,106,121,136,151,166,181,196,211,226,241,256,271,286 行）
- 预热 3.6s · 单题 p50=473ms p90=672ms max=708ms
- A 锚点命中 top1/top3/top6 = 9/12/14（45%/60%/70%）
- B 答案命中 top1/top3/top6 = 3/3/6
- top1 落在 knowledge/ 之外: 10/20

| # | 行 | 域 | 题干 | A@1 | A@3 | B@3 | ms | 首条 | 金标 |
|---:|---:|---|---|---|---|---|---:|---|---|
| 1 | 1 | 执行模型 | LExecutor 允许的单个处理器程序最多多少条指令（默认上限常量）？ | Y | Y | Y | 473 | knowledge/01-execution/E03-变量与内存边界.md | Mindustry-Source/core/src/mindustry/logic/LExecutor. |
| 2 | 16 | 执行模型 | 600 条指令的程序在默认 instructionsPerTick=1 下跑完一轮需要多 | N | Y | N | 624 | docs/断言表.md | Mindustry-Source/core/src/mindustry/world/blocks/log |
| 3 | 31 | 变量与作用域 | sensor 语句的第 0 个参数（文本第一个参数）是什么？
A) 被读取的方块
B)  | N | Y | N | 672 | mindustry-blueprint/SKILL.md | tools/instr_semantics.json#sensor |
| 4 | 46 | 变量与作用域 | set i 0 后连续执行 5 次 op add i i 1，i 最终是多少？ | N | N | N | 400 | tools/mlogcheck.py | tools/instr_semantics.json#op |
| 5 | 61 | 控制流 | 下面程序会打印几个数字？
```mlog
set i 0
jump greaterTha | N | N | N | 514 | tools/mlog.py | Mindustry-Source/core/src/mindustry/logic/LStatement |
| 6 | 76 | 读写感知 | memory-cell（记忆库）有多少个存储格？ | N | N | N | 311 | docs/游戏速查/方块.md | Mindustry-Source/core/src/mindustry/content/Blocks.j |
| 7 | 91 | 读写感知 | read 与 sensor 的核心区别是？
A) read 只能读数字，sensor 能 | Y | Y | N | 636 | knowledge/07-patterns/P03-comm-bus.md | Mindustry-Source/core/src/mindustry/logic/LExecutor. |
| 8 | 106 | 绘制文本 | printflush 的默认目标方块是？
A) display1
B) message1 | N | N | N | 458 | tools/logicd.py | Mindustry-Source/core/src/mindustry/logic/LStatement |
| 9 | 121 | 绘制文本 | 一个 tick 内 draw 次数超过 256 后会怎样？
A) 扩展到 1024
B) | Y | Y | N | 621 | knowledge/06-mlog/M05-绘制与文本.md | Mindustry-Source/core/src/mindustry/logic/LExecutor. |
| 10 | 136 | 世界交互 | status 语句的第一个参数（index0）是什么？
A) 单位
B) 布尔字面量：t | N | N | N | 708 | knowledge/06-mlog/M04-读写与感知.md | Mindustry-Source/core/src/mindustry/logic/LStatement |
| 11 | 151 | 单位控制 | LUnitControl 枚举一共有多少种 ucontrol 操作？ | Y | Y | Y | 626 | knowledge/06-mlog/M07-单位与逻辑控制.md | Mindustry-Source/core/src/mindustry/logic/LUnitContr |
| 12 | 166 | 单位控制 | 绑定最近的 flare 并让它向左移动，程序怎么写？
```mlog
ubind @fl | N | N | N | 455 | tools/mlogsim.py | Mindustry-Source/core/src/mindustry/logic/LStatement |
| 13 | 181 | 性能限制 | 单 tick 绘制命令缓冲上限 maxGraphicsBuffer 是多少？ | Y | Y | N | 289 | knowledge/01-execution/E04-时间与wait精度.md | Mindustry-Source/core/src/mindustry/logic/LExecutor. |
| 14 | 196 | 性能限制 | 为什么把循环内的常量运算提到循环外能提速？
A) 提高 ipt
B) 避免浮点误差
C) | Y | Y | N | 358 | knowledge/01-execution/E01-执行模型与预算.md | Mindustry-Source/core/src/mindustry/world/blocks/log |
| 15 | 211 | 方块与锚点 | logic-processor 的占地与建造成本是？
A) size=3，silicon | N | N | N | 455 | docs/游戏速查/方块.md | tools/block_attrs.json#logic-processor |
| 16 | 226 | 电力与热 | PowerGenerator 的默认发电量 powerProduction 是多少？ | N | Y | N | 442 | docs/游戏速查/方块.md | Mindustry-Source/core/src/mindustry/world/blocks/pow |
| 17 | 241 | 电力与热 | power-node 与 power-node-large 的占地分别是？
A) 2×2 | N | N | N | 562 | docs/游戏速查/方块.md | tools/block_attrs.json#power-node-large |
| 18 | 256 | 液体与物流 | Liquid.gas 为 true 表示什么？
A) 易燃
B) 该液体是气体（渲染与流 | Y | Y | N | 473 | knowledge/02-world/W05-heat.md | Mindustry-Source/core/src/mindustry/type/Liquid.java |
| 19 | 271 | 液体与物流 | liquids.json 的 color 字段用途是？
A) 该液体的渲染颜色（十六进制 | Y | Y | N | 459 | knowledge/02-world/W04-liquids.md | data/game/liquids.json |
| 20 | 286 | 战斗与单位 | StatusEffect 默认的 effectChance 是多少？
A) 0.05
B | Y | Y | Y | 565 | knowledge/03-combat/C04-status.md | Mindustry-Source/core/src/mindustry/type/StatusEffec |

## A 未命中明细（6）

- [46] set i 0 后连续执行 5 次 op add i i 1，i 最终是多少？
    gold=tools/instr_semantics.json#op
    top: tools/mlogcheck.py
    top: knowledge/06-mlog/M03-控制流.md
    top: tools/mlogprovider.py
- [61] 下面程序会打印几个数字？
```mlog
set i 0
jump greaterThanEq i 3 5
print i
op add i i 1
jump always 1
printflush message1
```
    gold=Mindustry-Source/core/src/mindustry/logic/LStatements.java:986-1069
    top: tools/mlog.py
    top: tools/mlogprovider.py
    top: tools/review.py
- [106] printflush 的默认目标方块是？
A) display1
B) message1
C) cell1
D) switch1
    gold=Mindustry-Source/core/src/mindustry/logic/LStatements.java:388
    top: tools/logicd.py
    top: mindustry-blueprint/REFERENCE.md
    top: tools/mlogprovider.py
- [136] status 语句的第一个参数（index0）是什么？
A) 单位
B) 布尔字面量：true 表示施加、false 表示移除
C) 时长
D) 状态效果名
    gold=Mindustry-Source/core/src/mindustry/logic/LStatements.java:1568-1625
    top: knowledge/06-mlog/M04-读写与感知.md
    top: tools/logicd.py
    top: tools/mlogsim.py
- [211] logic-processor 的占地与建造成本是？
A) size=3，silicon 200
B) size=2，copper 500
C) size=2，lead 320 + silicon 80 + graphite 60 + thorium 50
D) size=1，lead 100
    gold=tools/block_attrs.json#logic-processor
    top: docs/游戏速查/方块.md
    top: tools/logicd.py
    top: tools/mlog.py
- [241] power-node 与 power-node-large 的占地分别是？
A) 2×2 与 3×3
B) 都是 1×1
C) 都是 2×2
D) power-node 为 1×1，power-node-large 为 2×2
    gold=tools/block_attrs.json#power-node-large
    top: docs/游戏速查/方块.md
    top: tools/mschgen.py
    top: 00-data/src_anchors.json
