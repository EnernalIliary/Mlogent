---
id: PATTERN.ANTI.001
title: 反模式清单：20 条真实蓝图里的错误写法
domain: evidence
status: active
ver: [v159.3_src, v160.7_rt]
conf: E
src:
  - "mindustry-blueprint/PATTERNS.md:1900-2170"
  - "logic-corpus/_procs/*.mlog（1078 文件实测扫描）"
  - "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:761-763"
  - "Mindustry-Source/core/src/mindustry/unit/UnitComp.java:296,307,319"
data: []
depends: [PATTERN.PERF.001, PATTERN.STATE.001]
tags: [反模式, bug, 语料统计, 检测方法]
tokens: 1431
---

## 一句话

语料里 83.6% 的语句是绘制、67.7% 的一元运算多写了参数、17.8% 的文件里有自跳死循环 —— 这三条占了真实蓝图 bug 的绝大多数，而且全部可以用一行正则批量检出。

## 规则 / 公式

次数口径（两种，不可混用）：

- **[实测] 本库扫描**：`logic-corpus/_procs/*.mlog`，1078 个文件、389,341 行、9,195,463 字符，2026-11-08 用正则统计。
- **[文档] PATTERNS 扫描**：mindustry-blueprint/PATTERNS.md 第 11 章，用 tools/corpus/check_ops.py 扫 1081 个真实逻辑块（剔除像素画）。

两者对同一现象给出不同数字（见 AP-01），说明语料集合不同（.mlog 反编译文本 vs blocks.json 语句数组），引用时必须注明口径。

## 数值

| 指标 | 数量 | 占扫描面 |
|---|---:|---|
| draw 语句 | 325,586 | 占 389,341 行的 83.6% |
| @counter 引用 | 3,207 | 分布在 160/1078 文件（14.8%） |
| 一元运算多写参数 | 677 | 分布在 142/1078 文件 |
| 自跳死循环 jump 0 | 192 | 分布在 113/1078 文件 |
| control 语句 | 9,901 | — |
| sensor 语句 | 5,685 | 分布在 597 文件 |
| ucontrol 语句 | 4,007 | 分布在 357 文件 |
| ubind 语句 | 1,561 | 分布在 376 文件 |
| read / write | 1,340 / 1,086 | 172 / 115 文件 |
| radar / uradar | 96 / 65 | 62 / 40 文件 |
| op len（正确算距） | 20 | 仅 14 文件 |
| wait | 22 | 仅 13 文件 |

## 源码锚点

- LExecutor.java:761-763 —— sensor/radar 结果 30 tick 刷新，是「读到旧值」的定量根因。
- UnitComp.java:296 —— @controlled 恒返回 1（逻辑控制），不能区分处理器。
- UnitComp.java:307 —— @pingX 相关字段可产生 NaN。

## 实测与反例

### AP-01 一元运算多写参数（677 处 / 142 文件）

- 症状：`op rand 1 5 0`、`op floor x 0 0` —— rand/floor/ceil/cos/sin/abs/log10/round/not/atan/sqrt/log/tan 只需要 1 个输入，却按 2 输入格式写，指令仍执行但语义易误解，跨版本兼容性差。
- 根因：按「所有 op 都是 3 操作数」的模板复制粘贴。
- 正确做法：一元运算写 `op rand 5 result`（1 输入 + 1 输出）。
- 检测：`^op\s+(rand|floor|ceil|cos|sin|abs|log10|round|not|atan|sqrt|log|tan)\s+\S+\s+\S+\s+\S+\s*$`。
- 冲突记录：PATTERNS.md:1931-1945 记的是 567 处（1081 个逻辑块口径，rand 199/floor 88/ceil 65/cos 50/sin 50/abs 35/log10 24/round 24/not 13/atan 7/sqrt 6/log 5/tan 1）；本库实测 .mlog 文本口径是 677 处。两者不矛盾，是语料不同。

### AP-02 自跳死循环 `jump 0 ...`（192 处 / 113 文件）

- 症状：绑定失败时 `jump 0 equal @unit null` 原地打转，一 tick 打满预算并阻塞同处理器其它逻辑。
- 根因：把「等待」写成自旋，而 mlog 没有让出语义（wait 才是让出）。
- 正确做法：加计数上限，超限回待机态；或改用 wait 让出。
- 检测：`^jump\s+0\s`（自跳）+ 检查是否有 try 计数。

### AP-03 `@counter` 魔法分派（3,207 处 / 160 文件）

- 症状：`op add @counter @counter state` 后跟等长分支，插入一条指令全表错位且无注释。
- 根因：追求 O(1) 分派，牺牲可维护性。
- 正确做法：状态数 <= 20 时用 jump 链（PATTERN.STATE.001 写法 A）；必须用时把步长写成常量并加注释。
- 检测：`@counter` + 随后的 `jump <常数>` 序列；统计分支体长度是否相等。

### AP-04 每 tick 全量遍历（次数未统计）

- 症状：2 ipt 的 micro 每 tick 遍历 100 个炮塔，一圈 50 tick，射速被逻辑拖慢。
- 根因：把「每帧刷新」当成正确性要求。
- 正确做法：mod 轮转（每 tick 1 个），对照组是语料里 95 个已采用轮转的逻辑块（PATTERNS.md:496-517）。
- 检测：数 `getlink`/`control` 循环体里是否有 `@links` 取模。

### AP-05 dx+dy 假距离（次数未统计）

- 症状：`op add d dx dy` 当距离，斜角提前开火或漏打。
- 根因：不知道 `op len`。
- 正确做法：`op len d dx dy`；证据是本库实测 op len 只有 20 处（14 文件），而 sensor 有 5,685 处 —— 距离计算被严重低估。
- 检测：`op add` 的两个源变量名含 dx/dy 且结果变量名含 dist/range。

### AP-06 `@controlled` 误用（次数未统计）

- 症状：用 `@controlled` 判断控制者身份，结果在逻辑控下恒为 1。
- 根因：不知道源码 UnitComp.java:296 只有 0/1/2/3 四态。
- 正确做法：比较 `@controller` 与 `@this`。
- 检测：`sensor .* @controlled` 后紧跟 `jump equal ... 1`。

### AP-07 null 与 0 混比（次数未统计）

- 症状：`jump equal target 0` 当判空，永远不成立。
- 根因：equal 对 null 与 0 不相等（PATTERNS.md:2082-2098）。
- 正确做法：显式 `equal target null`。
- 检测：判空处出现数字 0。

### AP-08 画布全量重绘（325,586 条 draw）

- 症状：每帧逐像素 draw，64x64 画满需 4,096 条 ≈ hyper 处理器 2.73 s 一帧。
- 根因：把显示屏当帧缓冲而非色块输出。
- 正确做法：色块批画（PATTERN.DATA.001）；数据层证据是 18 个像素画蓝图占约 140 万语句（PATTERNS.md:1774），intel corei3.msch 单文件 126,759 条 draw（PATTERNS.md:1786）。
- 检测：`draw rect .* 1 1` 连续出现。

### AP-09 把 radar 缓存当实时（radar 96 + uradar 65）

- 症状：目标已死仍持续开火，或 0.5 s 内换了目标发现延迟。
- 根因：radar 结果 30 tick 才重算（LExecutor.java:761-763），不是每 tick 真实扫描。
- 正确做法：每次使用前判 null/判死。
- 检测：`radar` 后没有 `jump .* null` 的代码块。

### AP-10 uradar 不刷控制导致掉控（uradar 65 处）

- 症状：逻辑控 10 s 后单位脱控回 AI。
- 根因：uradar 不刷新 controlTimer（LogicAI.java:18 = 600 帧）。
- 正确做法：循环里插入会刷控制的 ucontrol 动作，或周期性重绑。
- 检测：`uradar` 所在分支之外没有任何 `ucontrol`。

### AP-11 内存格传对象引用（read 1,340 / write 1,086）

- 症状：A 处理器 write 单位引用到 cell，B 处理器 read 出来是错的。
- 根因：内存格只可靠承载数值；引用语义跨核不保证。
- 正确做法：`write 引用 proc \"变量名\"`（变量空间）。
- 检测：write 的源变量来自 `ubind`/`sensor @unit` 类结果且目标地址是数字。

### AP-12 多写者覆盖（次数未统计）

- 症状：黑板某格数值随机跳变、偶发卡死。
- 根因：两个处理器写同一格，读者无法判断归属。
- 正确做法：一格一写者 + 写者 ID 列。
- 检测：统计所有 write 的数字地址，找重复。

### AP-13 order 参数记反（radar 96 处）

- 症状：索敌总打最远的。
- 根因：order 1 = 最近，0 = 最远。
- 正确做法：需要最近写 1。
- 检测：`radar ... distance <source> 0 <out>` 后紧跟 `op len` 判射程失败率高。

### AP-14 标签踩空（次数未统计）

- 症状：跳转后行为随机，实际跳回开头。
- 根因：标签在文件末尾、行号 = 语句总数，@counter 越界重置为 0。
- 正确做法：标签下至少一条指令，分支末尾 end。
- 检测：文件最后一个非空行是 `名字:`。

### AP-15 相对跳转（次数未统计）

- 症状：插入一行后整个跳转表错位。
- 根因：用 jump 相对偏移而非标签。
- 正确做法：重新导出时保留标签（LParser 两趟解析），改代码走源码而非改数字。
- 检测：`jump <小数字>` 密集出现且无注释。

### AP-16 无上限重试（次数未统计）

- 症状：没有可绑单位时永远卡在重绑分支。
- 根因：重试没有退出条件。
- 正确做法：try <= 3 后回待机（PATTERNS.md:777-804 的正确写法）。
- 检测：`ubind` 前的 try 自增没有 greaterThan 上限。

### AP-17 `wait` 当延时以为预算会补（wait 仅 22 处）

- 症状：以为 wait 只是延后，实际本 tick 剩余预算作废。
- 根因：wait 走 yield，accumulator 不补偿（LogicBlock.java:560-580）。
- 正确做法：节流用 @second/@time 闸门（PATTERN.PERF.001）。
- 检测：`wait` 密集出现说明作者在用延时凑时序。

### AP-18 显示屏坐标越界（次数未统计）

- 症状：右侧/下方像素不显示。
- 根因：displaySize = 64（tileable 32），坐标按 65 或 128 算。
- 正确做法：按 `sensor w display1 @displayWidth` 取实际尺寸。
- 检测：draw 坐标常量 >= 64。

### AP-19 @pingX 得到 NaN（次数未统计）

- 症状：网络延迟显示/计算全变 NaN，后续比较全部为假。
- 根因：UnitComp.java:307 相关字段在非网络环境可为 NaN，NaN 参与比较恒假。
- 正确做法：先 `op not`/`equal v v` 自比判 NaN（NaN != NaN）。
- 检测：使用 `@ping` 系列属性但无自比检查。

### AP-20 冗余参数与死代码（次数未统计）

- 症状：`draw clear r g b 0 0 0` 后跟永远不执行的分支。
- 根因：从别的蓝图复制后只改一处。
- 正确做法：统一参数表 + 单入口；用 `end` 显式关断。
- 检测：统计某条指令的参数向量在语料里出现的不同形态数（PATTERNS.md:2151-2157 列为高频噪声）。

## 常见误解

1. 「bug 都是偶发的」—— 不。AP-01/02/03 都是静态可检的确定性错误，占语料大多数。
2. 「语料统计能直接当 bug 总数」—— 不能。两种口径（.mlog 文本 677 vs blocks.json 567）差 110 处，说明计数依赖扫描面，引用必须带口径。
3. 「draw 多是蓝图复杂」—— 不是，draw 占 83.6% 是像素画蓝图的特性，剔除 is_art 后才是逻辑。

## 相关

- PATTERN.PERF.001 性能与鲁棒性
- PATTERN.STATE.001 状态机
- idioms.json（30 条正确写法对照）
