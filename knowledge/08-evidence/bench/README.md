# Benchmark：300 题 mlog / Mindustry 机制评测集

> 2026-11-17：`docs/游戏速查/`（方块/单位/物品/配方）已删除，数值母本在 `knowledge/00-data/`。下文出现的这些路径是当年评测语料的快照，保留只为对照历史数字。

本目录是知识库的**可复现评测集**：300 道题覆盖 mlog 逻辑与 Mindustry 机制的 12 个域，
每题带唯一真源（源码文件 + 行号 或 数据文件锚点），配套检索型评测脚本 `tools/eval_kb.py`，
用来度量「知识库能不能答出这 300 题」。

> 结论先行：题目是**真源驱动**生成的（不凭记忆），难度按 24/52/24 归一；
> 检索侧用 `coverage / hit@1 / hit@k / mrr / strong@k` 五个指标衡量，
> 当前库（<临时暂存目录> 镜像，104 个文件 / 1051 chunk，2026-11-08）lexical 基线为
> **coverage 100% / hit@1 45.3% / hit@6 78.7% / mrr 0.582 / strong@6 92.2%**；
> 更早的 74 文件快照 coverage 只有 87%（39 条缺口），两次快照并列在 §4。

---

## 1. 文件清单

| 文件 | 作用 |
| --- | --- |
| `questions.jsonl` | 300 题，一行一题，UTF-8，字段见 §2 |
| `gen_questions.py` | 主装配：调用 4 个域模块 → 校验 → 写出 jsonl |
| `_gen_core.py` | 真源加载（data/game/*.json、tools/*.json）+ 题目构造助手 |
| `_gen_d1.py` | 执行模型 / 变量与作用域 / 控制流（75 题） |
| `_gen_d2a.py` | 读写感知 / 绘制文本 / 世界交互（75 题） |
| `_gen_d2b.py` | 单位控制 / 性能限制 / 方块与锚点（75 题） |
| `_gen_d2c.py` | 电力与热 / 液体与物流 / 战斗与单位（75 题） |
| `tools/eval_kb.py` | 评测脚本（两种检索引擎，可重跑） |
| `eval_report.json` | 评测的机器可读报告：lexical / hybrid 两段 + comparison（逐域、按 source_kind） |
| `classify_sources.py` / `source_kind.json` | 300 题的 source_kind 分类脚本与逐题标签（§9） |
| `merge_report.py` | 把 lexical 与 hybrid 两次评测合并成三段式 eval_report.json |
| `questions-derive.jsonl` | **v2 草案**：24 道跨源推导题（BENCH.0301-0324，12 域×2，全 hard，每题 ≥2 源），见 §11 |
| `subset_report.py` / `subset_report.json` | 分族群评测：公式题 22 + 跨源题 24 = 46 题的专属 hit@6（§9 末） |
| `hybrid_diag.py` / `hybrid_diag*.json` | H1 的分层诊断：as-is / 按文件去重 / 只留 knowledge 四种读法（§10.3） |
| `kb_scope_eval.py` | A/B/C 六变体对照 runner（基线、去重、硬过滤、A+B、ASCII、全开），输出 §10.5 的表 |
| `snap_ab.json` / `snap_ab_pq.json` | **现行**对照数据（冻结快照 63 md + 18 表；含逐题明细） |
| `scope_ab.json` / `scope_ab_pq.json` | 旧语料（writer 加文中途）对照数据，仅留档，勿引用 |
| `../../tools/kb_scope.py` | 仓库 `tools/kb.py` 的三开关副本（A/B/C 实验用；默认配置已回灌 kb.py，见 §10.6） |

重新生成题库（**必须**指向仓库根；脚本只读仓库、不写仓库）：

```powershell
$env:AS_REPO='<仓库根>'
$env:PYTHONIOENCODING='utf-8'
python gen_questions.py     # 断言 300 题 / 每域 25 / 难度 6-13-6，并校验 src 存在性与行号
```

---

## 2. JSONL 字段

```json
{"id":"BENCH.0001","domain":"执行模型","difficulty":1,"type":"mc",
 "q":"游戏逻辑以 tick 为最小时间单位，1 tick 等于多少秒？\nA) 1/50 秒\nB) 1/60 秒\nC) 1/30 秒\nD) 1 秒",
 "answer":"B) 1/60 秒","why":"VERSION.md：能量 1 单位/tick = 60/s，即 1 tick = 1/60 s。",
 "src":"knowledge/VERSION.md","ver":"both"}
```

| 字段 | 含义 |
| --- | --- |
| `id` | `BENCH.NNNN`，四位数、从 0001 连续编号（域按 §3 顺序拼装） |
| `domain` | 12 个中文域名之一（§3） |
| `difficulty` | 1=易 / 2=中 / 3=难；每域固定 6/13/6 |
| `type` | `mc`（四选一，选项在 q 里）/ `short`（一句话）/ `calc`（要算式与数值）/ `code`（给 mlog 片段，问输出或 bug） |
| `q` | 题面；mc 题在题面后附 A)~D) 四行；code 题用 mlog 围栏包代码（≤15 行） |
| `answer` | 参考答案；mc 答案写成 `B) 文本` 形式，字母与 q 里的选项一致 |
| `why` | 判定依据：引用源码原文要点，calc 题附算式 |
| `src` | 唯一真源：`<仓库相对路径>[:行号或行号区间][#锚点]` |
| `ver` | 数值/语义权威版本：`v160.7_rt`（jar 反射数值）、`v159.3_src`（源码语义）、`both`（两者一致，或数据文件+schema） |

校验由 `gen_questions.py` 强制：`src` 去掉 `#` 与行号后必须是真实存在的文件，
行号不得越界；code 题 ≤15 行；mc 恰 4 个选项；总题数 300。

---

## 3. 覆盖矩阵（12 域 × 25 题 = 300）

| # | 域 | E/M/H | 主要真源 | 考什么 |
| --- | --- | --- | --- | --- |
| 1 | 执行模型 | 6/13/6 | `logic/LExecutor.java`, `LogicBlock.java`, `tools/instr_semantics.json` | ipt/预算/53 条语句与 45 个 op、参数槽位与写回下标、@counter 语义 |
| 2 | 变量与作用域 | 6/13/6 | `LExecutor.java`, `GlobalVars.java` | 变量表私有性、@this/@links/@ipt、只读 vs 可写常量、null 语义 |
| 3 | 控制流 | 6/13/6 | `LStatements.java:986-1069`, `ConditionOp.java` | jump 四槽顺序、7 个条件 op、strictEqual 恒 false、标签展开、end/stop/wait |
| 4 | 读写感知 | 6/13/6 | `ReadI/WriteI`, `MemoryBlock.java`, `LAccess.java` | 可读/可写接口、越界行为（NaN/null）、记忆库权限与容量 |
| 5 | 绘制文本 | 6/13/6 | `LogicDisplay.java`, `LExecutor.java:910-1160`, `MessageBlock.java` | 16 条绘制命令、maxSides/displaySize、print 转换规则、format 占位符陷阱 |
| 6 | 世界交互 | 6/13/6 | `getblock/setblock/spawn/status/query/fetch` 段 | 层顺序（layer 在前）、query 形状、spawn 队伍、rule/weather/cutscene |
| 7 | 单位控制 | 6/13/6 | `LUnitControl.java`, `LLocate.java`, `RadarTarget/Sort` | 21 种 ucontrol、ulocate 4 类、uradar 6 参数、enemy 排除 derelict |
| 8 | 性能限制 | 6/13/6 | `LogicBlock.java:45-49`, `LExecutor.java:41-46` | maxInstructions=1000、ipt=1、scale=5、privileged 40、缓冲上限、死循环代价 |
| 9 | 方块与锚点 | 6/13/6 | `block_attrs.json`, `block_sizes.json`, `data/game/blocks.json` | 447/253/446 三个口径、size/itemCapacity/liquidCapacity、成本格式、隐藏方块 |
| 10 | 电力与热 | 6/13/6 | `PowerGenerator.java`, `ConsumePower.java`, `Rules.java` | usage/capacity/buffered、status 效率、爆炸参数、solar/lighting 规则、/s↔/tick |
| 11 | 液体与物流 | 6/13/6 | `Liquid.java`, `Liquids.java`, `liquids.json` | 11 种液体与逐项参数（热容/温度/粘度/可燃/爆）、导管容量、distribution 类别 |
| 12 | 战斗与单位 | 6/13/6 | `BulletType.java`, `Damage.java`, `StatusEffect.java`, `units.json` | 护甲公式 max(dmg-armor, 0.1*dmg)、子弹默认值、状态倍率、波次表 |

题型分布：mc 220 / short 51 / calc 15 / code 14。难度分布：72 / 156 / 72（24% / 52% / 24%）。

**难度归一规则**（`gen_questions.py::_normalize_difficulty`）：每域内按
`(手标难度, 是否 code/calc 题)` 升序稳定排序，前 6 名记 1、中 13 名记 2、后 6 名记 3。
手标只影响排序，最终分布由断言保证，因此同一题的难度在不同批次间稳定（排序确定性）。

---

## 4. 评测方法

```powershell
# 默认：自动选引擎，跑全部 300 题（零依赖版）
python tools/eval_kb.py --kb . --engine lexical -k 6

# 用产品检索器（tools/kb.py 混合检索，需要 out/_kb/kb.sqlite3 + out/_kblibs/_kbmodels）
python tools/eval_kb.py --engine kb --root <仓库根> -k 6
```

判定 gold 的方式：取 `src` 的 basename（如 `LExecutor.java`），
凡正文里出现该名字的文档都视为「可能答得出这题」。于是：

| 指标 | 定义 |
| --- | --- |
| coverage | 有 gold 文档的题 / 总题数。**没覆盖 = 知识库里根本没引用该源文件，属 KB 缺口** |
| hit@1 / hit@k | top-1 / top-k 命中任一 gold 文档的题占比（分母是 coverage） |
| mrr@k | 首个命中位次的倒数均值 |
| strong@k | top-k 命中的文档同时含 `文件:行号` 完整锚点（仅对带行号的 src 统计） |

评测语料排除：`_kb/ _raw/ _report/ __pycache__/ bench/` 与 `_` 开头的生成器脚本 ——
避免 `questions.jsonl` 与 `_gen_*.py` 把答案泄漏进索引。

### 基线（每行都标死「引擎 + 语料版本」，否则三个月后无法复现）

| # | 引擎 | 语料（文件数 / chunk 数） | 题数 | coverage | hit@1 | hit@6 | mrr | strong@6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | lexical BM25 | <临时暂存目录> 104 文件 / 1051 chunk（2026-11-08 04:18，§5 缺口已补齐） | 300 | 100% | 45.3% | 78.7% | 0.582 | 92.2% |
| L0 | lexical BM25 | <临时暂存目录> 74 文件 / 798 chunk（同日更早快照，39 条缺口未补） | 300 | 87.0% | 49.4% | 77.0% | 0.602 | 93.8% |
| H0 | kb.py 混合 | 仓库 knowledge 47 文件（旧快照，40 题抽样） | 40 | 100% | 20.0% | 52.5% | 0.327 | 55.6% |
| H1 | kb.py hybrid | 仓库 knowledge 48 篇（库总 8113 chunk / 140 files，DB READY 快照） | 300 | 100% | 28.3% | 54.7% | 0.372 | 62.2% |

- L1 是当前默认基线；L0 保留作「补缺口前」的对照：同样 300 题，coverage 从 87.0%→100%，
  hit@6 只从 77.0%→78.7% —— **补上文件引用能补齐 coverage，但不自动提升排序**，这就是 §8 前半句的含义。
- H0 不作为结论（仓库 knowledge 当时未同步本批文章，只证明两条引擎路径都能跑通）；H1 见 §10。
- 复现命令（引擎、语料、k 必须同时固定）：
  `python tools/eval_kb.py --questions 08-evidence/bench/questions.jsonl --kb <语料根> --engine lexical -k 6 --out <报告> --per-question <逐题明细>`

分词：中英混排按「ASCII 词 + 数字 + 中文二元组 + 单字」四路并行，纯标准库实现，
任何机器 `python tools/eval_kb.py` 即可复现，无需模型。

---

## 5. 已知 KB 缺口（39 题，按源文件聚合）

> **状态（2026-11-08 04:18）**：这批缺口在 <临时暂存目录> 镜像里已全部补上（L1 快照 coverage=100%），
> 本表保留为历史记录与派活依据（证据原文：L0 快照 coverage 87.0%）。补法见 §8。

这些源文件在原知识库里**一次都没被提到**，对应题必然 coverage 未命中 —— 补文档优先写它们：

| 题数 | 缺失源文件 | 说明 |
| --- | --- | --- |
| 10 | `logic/LUnitControl.java` | 21 种 ucontrol 操作的参数表（M07 只写了部分） |
| 10 | `content/Liquids.java` | 11 种液体的逐项数值（热容/温度/粘度/可燃/爆/气体） |
| 6 | `logic/ConditionOp.java` | 7 个条件 op 的符号与判定（含 strictEqual 恒 false 的坑） |
| 3 | `logic/TileLayer.java` | floor/ore/block/building 四层与可写性 |
| 2 | `logic/RadarTarget.java` | 8 种目标（enemy 排除 derelict） |
| 2 | `tools/block_sizes.json` | 446 项 name→size 映射（W01 只提了部分） |
| 1 | `MessageType/CutsceneAction/QueryType/QueryShape/LLocate/RadarSort` | 枚举取值散落在 M06/M07 |

注：`hit@k` 低但 `strong@k` 高的域（「方块与锚点」hit 35%、「电力与热」hit 36%、strong 0%）
说明检索确实落到了「提到该源文件的宽文档」（大 JSON 数据表），但正文里没有 `文件:行号` 锚点 ——
这类域需要把数字搬进文章，而不是只留在 `00-data/*.json`。

---

## 6. 如何加题 / 改题

1. 在对应域的 `_gen_d*.py` 的 `build_xxx()` 里加一行 `mc/short/calc/code(...)`，
   参数末尾是 `(src, ver, 手标难度)`；`src` 必须是真实文件（可带 `:行号` 或 `#锚点`）。
2. 跑 `python gen_questions.py`：该域不再是 25 题、难度不是 6/13/6、mc 不是 4 选项、
   code 超 15 行、或 src 文件/行号不存在，都会 assert 失败并指出位置。
3. 规则：一个数字只从真源读（`data/game/*.json` 或源码），不手抄；
   容易被文档写错的点（耗电 `/s` 与 `/tick` 差 60 倍、`getblock` 的 layer 在第一个参数）
   优先做 medium/hard 题。

---

## 7. 局限（读结论前先看这里）

- **gold 用 basename 判定**：`blocks.json` 这类名字会同时命中 `00-data/blocks.json`（数据表）与文章，
  宽文档抬高 hit@k、压低 strong@k。
- **coverage 不等于可答性**：文档提到 `LExecutor.java` 不代表它写对了 ipt 的影响，
  coverage 只回答「这个源文件有没有进库」。
- **难度是相对排序**，不是绝对标定；同域内 6/13/6 由排序保证，跨域不可比。
- **lexical 基线很弱**（中文二元组 + BM25），它的作用是把「库缺不缺内容」与「检索排得好不好」
  分开看：换更强检索器后 hit@1 应上升，coverage 不应变化。

---

## 8. 附录：给写作者的 5 条检索友好规则（补缺口前必读）

本节由 300 题实测反推，不是文风偏好；每条都附证据，数字来自同目录 `eval_report.json`。

1. **正文必须有「文件:行号」锚点，不能只提文件名。**
   证据：`电力与热` 域 coverage 100% / hit@6 36%，但 strong@6 = **0%** ——
   检索命中的是只写了 "ConsumePower.java" 字样的散文或数据表，正文没有 `PowerGenerator.java:23-40` 这种锚点。
   strong@6 是「答得出」的强信号，缺锚点的文章在强检索器下会掉分。

2. **每个数字写成「主体 + 字段 = 值 + 单位口径」的可检索短句，别只塞进 JSON / 表格。**
   反例：`00-data/liquids.json` 里有全部数值，但 `Liquids.java` 的 10 道题 coverage 全灭（该域 60%）。
   正例句式：`water 的 heatCapacity=0.4、temperature=0.5`；`impact-reactor 耗电 power=25/tick（=1500/s）`。
   单位换算必须明写 `/tick` 与 `/s`（差 60 倍，`docs/游戏速查/方块配方.md` 耗电列标错就是这个坑）。

3. **枚举必须逐项列全，含每个取值的参数槽位顺序。**
   `LUnitControl` 21 项、`ConditionOp` 7 项、`RadarTarget` 8 项分别带 10/6/2 道题，全灭原因是文章只写「支持多种操作」。
   正确形式：`ucontrol move x y`（2 参）、`ucontrol build x y block rotation config`（5 参）、
   `ucontrol within x y radius result`（最后一个是输出变量）。

4. **小枚举文件最容易被漏：一篇文章要把它域内的真源文件逐个点名。**
   39 条缺口里有 6 个是只带 1-3 题的「小文件」：`TileLayer`(3)、`RadarTarget`(2)、
   `MessageType` / `CutsceneAction` / `QueryType` / `QueryShape` / `LLocate` / `RadarSort` 各 1。
   写域综述时把这些名字连同取值一起进正文，例如
   `TileLayer: floor / ore / block / building，其中 building 不可 setblock`。

5. **标题与首段同时出现中文术语和英文标识符，且用题目会问的原词。**
   lexical 走「中文二元组 + ASCII 词」双通道：只写「单位控制」不写 `ucontrol`、或只写 `ucontrol` 不写「单位控制」，
   都会掉一个召回通道。数据表类文章（`00-data/*.json`）尤其要在正文补一行人话摘要 + 锚点。

> 验收口径（派活用）：补完后用同一套 300 题重跑
> `python tools/eval_kb.py --kb <repo> --engine kb -k 6`，该域 coverage 与 hit@6 必须上升，
> 且对应题目的 top-6 文档里出现该源文件名；只改数据表不改正文，coverage 会升但 hit@6/strong 不动 —— 不算补上。

---

## 9. 按「答案必须来自哪类真源」再切一刀（source_kind）

题库冻结后按**答案的最终依据**给 300 题打单一标签（脚本 `classify_sources.py`，逐题标签见 `source_kind.json`）。
规则有优先级，从上到下命中即停：

| 标签 | 判据（确定性） | 含义：AI 要答对必须会什么 |
| --- | --- | --- |
| 实测 | `ver` 含 rt，或 `src` 是 `knowledge/VERSION.md` | 数字只能靠 jar 反射/双版本对照确认（如 1 tick=1/60 s、能量 /s↔/tick） |
| 公式 | `type=calc`，或 `why` 里出现「= … * / ×」算式 | 把多个数值代进公式算（ipt→耗时、耗电 /s↔/tick、护甲 max(dmg-armor, 0.1·dmg)） |
| 数据表 | `src` 以 `.json` 结尾（`data/game/*`、`tools/*`） | 从表里取一个值/一条结构（447 方块、446 size、22 物品…） |
| 源码 | 其余（`*.java` 语义、枚举值、默认常量、行号） | 读代码即得：常量值、枚举项、参数槽位、默认值 |

### 总体分布（n=300）

| 类 | 题数 | 占比 | 典型题 |
| --- | --- | --- | --- |
| 源码 | 260 | 86.7% | BENCH.0001 `LExecutor.java:41 maxInstructions=1000`、BENCH.0153 `RadarTarget 8 种` |
| 公式 | 22 | 7.3% | BENCH.0018 `1000 指令 ÷ 60 tick/s ≈ 16.67 s`、BENCH.0243 能量换算 |
| 数据表 | 14 | 4.7% | BENCH.0202 `blocks.json 447 条`、BENCH.0203 `block_sizes.json 446 项` |
| 实测 | 4 | 1.3% | BENCH.0007/0187/0243/0268（tick 与能量口径） |

### 逐域（行=域，列=四类）

| 域 | 源码 | 数据表 | 公式 | 实测 | n |
| --- | --- | --- | --- | --- | --- |
| 执行模型 | 18 | 0 | 6 | 1 | 25 |
| 变量与作用域 | 22 | 0 | 3 | 0 | 25 |
| 控制流 | 23 | 0 | 2 | 0 | 25 |
| 读写感知 | 23 | 0 | 2 | 0 | 25 |
| 绘制文本 | 25 | 0 | 0 | 0 | 25 |
| 世界交互 | 25 | 0 | 0 | 0 | 25 |
| 单位控制 | 25 | 0 | 0 | 0 | 25 |
| 性能限制 | 20 | 1 | 3 | 1 | 25 |
| 方块与锚点 | 16 | 8 | 1 | 0 | 25 |
| 电力与热 | 22 | 0 | 2 | 1 | 25 |
| 液体与物流 | 20 | 2 | 2 | 1 | 25 |
| 战斗与单位 | 21 | 3 | 1 | 0 | 25 |

### 难度交叉 / 缺口交叉

| difficulty | 源码 | 数据表 | 公式 | 实测 | n |
| --- | --- | --- | --- | --- | --- |
| 1 易 | 63 | 5 | 3 | 1 | 72 |
| 2 中 | 131 | 7 | 15 | 3 | 156 |
| 3 难 | 66 | 2 | 4 | 0 | 72 |

39 条 KB 缺口按类：**源码 36 / 数据表 2 / 实测 1**（公式类 0 缺口 —— 公式题的源文件都在库里，缺的是算式）。

### 怎么读这张表（判断「AI 是否真能推导」）

- **86.7% 的题本质是「查源码」**：能答对说明知识库把行号 + 常量搬对了，**不证明会推导**。
  这就是 §8 规则 1 的由来：源码题全灭（36/39 缺口）说明文章在漏「文件:行号」，不在漏概念。
- **真正检验推导的只有 22 题（7.3%）**，且集中在执行模型（6）、变量（3）、性能限制（3）。
  「绘制文本 / 世界交互 / 单位控制」三个 25 题域**零公式题**，说明题库对这三域的推导强度覆盖偏弱 ——
  题库已冻结，这条记为下一版待补（每域加 2-3 道「多源组合」题，例如 ucontrol 参数序 × 单位 AI 行为）。
- **数据表只有 14 题（4.7%）但最容易被高估**：检索命中 `00-data/*.json` 就能拿到 gold，hit 虚高、strong 低（见 §5）。
- **实测只有 4 题**：所有 tick/能量口径题都靠这一条（1 tick = 1/60 s），它错一个就等于全库数值口径错，
  所以 `VERSION.md` 的 4 行必须有 v160.7_rt 与 v159.3_src 双版本标注。

### 推导专测：46 题（v2 是否有价值的唯一指标）

按 §9 口径把「真正考推导、不能靠查一行」的题拉出来单独统计（脚本 `subset_report.py`，
读 `eval_kb.py --per-question` 的逐题明细，不重跑检索）：

| 族群 | 题数 | coverage | hit@6 | mrr@6 | strong@6 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| 公式题（冻结 300 题内） | 22 | 100% | **81.8%** | 0.589 | 36.4% | 必须代公式/算数（ipt→耗时、/s↔/tick、护甲保底） |
| 跨源题（v2 草案，§11） | 24 | 100% | **91.7%** | — | — | 每题 ≥2 源，gold 取主源；**不进主指标** |
| 合计 | 46 | 100% | **87.0%**（加权） | — | — | 两段语料快照不同，只作量级参考 |

按 source_kind 的 hit@6（同一 L1 快照，n=300）：源码 **77.3%**、公式 **81.8%**、数据表 92.9%、实测 100%。

怎么读：

- **86.7% 的题只是「查源码」**（§9 表）：答对只证明知识库把行号 + 常量搬对了，**不证明会推导**。
- **真正考推导的是这 46 题**（22 公式 + 24 跨源）：它们才是判断 v2 是否有价值的唯一指标 ——
  主指标 hit@6 78.7% 里，推导题只占 15.3%，所以「总分涨了」不足以说明 AI 变强；
  推导题 hit@6 从 81.8% 涨到接近 100% 才有意义。
- 公式题 strong@6 只有 **36.4%**（远低于总体 92.2%）：说明算式散落在文章里但**公式所在行没有锚点**，
  这正是 §8 规则 2 的证据；跨源题 hit@6 高（91.7%）是因为出题时已按「每源都要有文章写到」反推过，
  它测的是「组合检索」，不是「AI 能否自己想到要组合」。

复现：`python 08-evidence/bench/subset_report.py --per-question <逐题明细> --derive-pq <跨源逐题明细> --out 08-evidence/bench/subset_report.json`
（需先用 `eval_kb.py --per-question` 生成两份逐题明细；分类口径：`python 08-evidence/bench/classify_sources.py --json 08-evidence/bench/source_kind.json`，只读题库，不改题）。

---

## 10. hybrid 基线（kb.py 混合引擎 × 仓库 knowledge）

**状态：已跑完**。H1 = 旧版 kb.py（无路径权重、chunk 不去重、库外 code chunk 抢槽），DB READY 快照 48 篇 / 8113 chunk / 140 files，2026-11-08 04:3x。
H2 = recon-d 的 1FB23F2A 基线（软路径权重 + depth 40）；H3 = 现行默认（A 硬过滤 + B 去重 + C ASCII 加权）。
后两行用**冻结快照**（63 篇 md + 18 张 00-data 表）重跑，细节与逐域表见 §10.5 / §10.6。

口径（与 §4 的 L1 严格可比）：gold 仍只认 `knowledge/` 内的文章（kb.py 额外收录的
`mindustry-blueprint/`、`docs/游戏速查/`、`tools/*.py` 不算 gold），否则两个引擎的分母不同。

### 10.1 三段式结果（同一套冻结 300 题，k=6）

| # | 引擎 | 语料 | coverage | hit@1 | hit@6 | mrr | strong@6 | knowledge 外命中 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | lexical BM25 | <临时暂存目录> 104 文件 / 1051 chunk | 100% | **45.3%** | **78.7%** | **0.582** | **92.2%** | —（语料即知识库本身） |
| H1 | kb.py hybrid（dense bge-small-zh + FTS5 + RRF） | 仓库 knowledge 48 篇 + tools/docs/blueprint（库总 8113 chunk / 140 files） | 100% | 28.3% | 54.7% | 0.372 | 62.2% | **top-6 槽 52.3% 落在 knowledge 外；top-1 有 45.3% 的题首选库外文档** |
| H2 | kb.py hybrid + 软路径权重（1FB23F2A） | 冻结快照 63 md + 18 表（索引 8164 chunk / 138 files，depth 40） | 99.3% | 45.0% | 67.5% | 0.528 | 82.9% | 18.5% |
| H3 | **+A 硬过滤 +B 去重 +C ASCII（现行默认）** | 同上（索引 8167 chunk / 138 files，仓库全库 build） | 99.3% | **58.1%** | **85.6%** | **0.682** | **97.1%** | **0%** |
| H4 | **A+B+C（同 H3 策略，最终交付库）** | recon-d 发布库：仓库 knowledge **66 篇 md + 18 张表**（库总 **8211 chunk / 141 files**，2026-11-08 05:12 发布） | 100% | **60.0%** | **86.7%** | **0.697** | **94.2%** | **0%**（data 槽 2.4%） |
| H5 | **A+B+C（同 H3 策略，FINAL2 交付库）** | 仓库 knowledge **67 篇 md + 18 张表**（新增 INTEGRATION.md，KB/README/AI-SETUP/VERSION 补写；库总 **8277 chunk / 142 files**，2026-11-08 05:23 发布） | 100% | **59.7%** | **86.3%** | **0.694** | **94.2%** | **0%**（data 槽 2.4%） |
| H6 | **A+B+C（同 H3 策略，FINAL3 交付终版）** | 仓库 knowledge 67 篇 md + 18 张表（C06/C10 的 9 行 DPS 修正、bench 中间件移入 `_scripts/`；库总 **8284 chunk / 142 files**，2026-11-08 05:36 发布） | 100% | **59.7%** | **86.3%** | **0.694** | **94.2%** | **0%**（data 槽 2.4%） |

**结论（lead 已批准、本节必带的一句）**：题库里 86.7%（260/300，与 hit@6 同值纯属巧合）的题本质是「查常量/查行号」，
hybrid 命中率高只证明**锚点搬对了**，不证明 AI 能推导；判断推导能力要看 §9 末的 46 题。
H1 那次 hybrid 不但没涨，反而比 lexical 低 24 pt —— 原因见 10.3，不是「文章变差了」。
修复检索策略后（§10.5）H3 已达 hit@6 **85.6%**、FINAL3 交付终版（§10.8）**86.3%**，高于 lexical 78.7%：**引擎本身没问题，是「库外 chunk 抢槽 + 不按文件去重 + dense 稀释标识符」三件事拖的**。

推导型题在 hybrid 下更差（逐题口径，§9 末的 46 题机会点）：公式题 22 道 hit@6 从 lexical 81.8% → **63.6%**，数据表 14 道 92.9% → 57.1%，源码 260 道 77.3% → 53.1%。也就是说「检索器换强」并没有让推导题更好，反而因为排序被库外文档打乱而更差 —— 修法见 10.4。

### 10.2 H1 逐域对比（hit@6，按 hybrid 从弱到强；H2/H3 的逐域表见 10.5）

| 域 | n | lexical | hybrid | Δ |
| --- | --- | --- | --- | --- |
| 方块与锚点 | 25 | 64% | 28% | -36 pt |
| 电力与热 | 25 | 44% | 36% | -8 pt |
| 世界交互 | 25 | 80% | 40% | -40 pt |
| 控制流 | 25 | 88% | 44% | -44 pt |
| 变量与作用域 | 25 | 88% | 48% | -40 pt |
| 读写感知 | 25 | 80% | 48% | -32 pt |
| 战斗与单位 | 25 | 84% | 60% | -24 pt |
| 单位控制 | 25 | 68% | 64% | -4 pt |
| 液体与物流 | 25 | 72% | 64% | -8 pt |
| 执行模型 | 25 | 100% | 68% | -32 pt |
| 绘制文本 | 25 | 88% | 68% | -20 pt |
| 性能限制 | 25 | 88% | 88% | +0 pt |

（H1 口径）hybrid 最弱 3 个域：**方块与锚点 28%**、**电力与热 36%**、**世界交互 40%**；H3 口径下已变为 读写感知 74% / 变量与作用域 76% / 方块与锚点 76%（§10.5）：
lexical 在这三域分别是 64%/44%/80% —— 「方块与锚点」「世界交互」在 hybrid 下掉得最狠（-36 / -40 pt）。

### 10.3 诊断：分数丢在哪（`hybrid_diag.py`，用 k=20 的逐题明细）

同一份结果按四种读法重算（明细见 `hybrid_diag.json`）：

| 读法 | hit@1 | hit@3 | hit@6 | hit@10 |
| --- | --- | --- | --- | --- |
| as-is（官方口径） | 28.3% | 42.7% | 54.7% | 61.0% |
| 按文件去重 | 28.3% | 45.7% | 57.0% | 65.0% |
| 只留 knowledge/ | 43.0% | 56.7% | 64.3% | 67.0% |
| 去重 + 只留 knowledge/ | 43.0% | 59.0% | 66.0% | 67.0% |

两个可量化的结构性原因：

1. **chunk 级结果没有按文件去重**：top-6 里有重复文件的题占 **242/300（80.7%）**，
   top-6 平均只覆盖 **4.47 个不同文件**（最少 1 个）。kb.py 的 `k` 数的是 chunk 不是文档，
   同一个 `.md` 的 2-3 个 chunk 会连号占槽 —— 只做去重就能把 hit@6 从 54.7% 拉到 57.0%。
2. **库外文档抢占排序**：top-6 槽位里有 **52.3%** 不是 knowledge 文章（k=20 时为 59.7%），
   最占位的是 `tools/mlogcheck.py`(397 次)、`docs/游戏速查/方块.md`(318)、`tools/mlog.py`(254)、
   `tools/chats.py`(249)、`mindustry-blueprint/REFERENCE.md`(187)。把库外文档剔掉后
   hit@1 从 28.3% → 43.0%、hit@6 从 54.7% → 64.3%；再去重 → **66.0%**。

即便如此（43.0% / 66.0%）仍低于 lexical 的 45.3% / 78.7%：**混合检索器本身对这 300 题的
「标识符密集型查询」不如纯 BM25**。题库题干大量是 `LExecutor.java`、`ConsumePower.java:10`、
`ucontrol build` 这类 ASCII 标识符，FTS5 能精确匹配，dense 向量反而稀释了这种信号；
RRF 融合后库外长文档（tools/*.py，6266 个 code chunk）更容易挤进前排。

### 10.4 建议的 3 个修法（按性价比排序；**均已在 §10.5 实施并实测**）

1. **kb.py 检索结果按文件去重 + 只对 knowledge 打分（或加路径权重）**：改动最小、收益最确定
   （诊断显示 hit@6 +11.3 pt、hit@1 +14.7 pt），且不影响「AI 实际检索」的口径 —— 它本来就是按文件读文章。
2. **给 FTS5 通道加标识符加权**（`LExecutor.java`、`ConsumePower.java:10` 这类 token 权重 ×2-3），
   dense 通道权重下调；或在 RRF 后对「路径在 knowledge/ 且正文含该题 src basename」的文档加 boost。
3. **把 tools/*.py 的 code chunk 排除出检索语料**（或压到单独索引）：6266 个 code chunk 对
   「读知识库文章」没有价值，只会抢槽；若确实要保留（供代码检索），至少默认检索不应混排。

> 复现：`python knowledge/tools/eval_kb.py --questions knowledge/08-evidence/bench/questions.jsonl --kb knowledge --root <repo> --engine kb -k 20 --out tmp_hybrid_k20.json --per-question tmp_hybrid_k20_pq.json`
> 然后 `python knowledge/08-evidence/bench/hybrid_diag.py --pq tmp_hybrid_k20_pq.json --kb knowledge --out hybrid_diag.json`。

### 10.5 检索策略对照实验：A 硬过滤 / B 按文件去重 / C ASCII 标识符加权（2026-11-08）

lead 采纳「A+B+C 一起做」后，在 `<临时暂存目录>/tools/kb_scope.py`（仓库 `tools/kb.py` 的副本，**未改仓库版**）
实现三个可独立开关的策略，用同一套冻结 300 题 + 24 题跨源草案跑对照。

**口径（重要）**：本表用**冻结语料快照** `<临时暂存目录>/out/_snap_knowledge`（63 篇 md + 18 张 00-data 摘要表，
2026-11-08 04:49 复制；基线索引 8164 chunk / 硬过滤索引 921 chunk）。此前的五组数字是在 writer 持续加文章时
跑的（同一 runner 三次跑出 144 / 182 / 63 篇 gold），已作废 —— 本表与 §10.1 的 H2/H3 同源，可并读。
k=6、candidates=40、coverage 99.3%（298/300：快照里缺 2 题的真源，不是检索失败）。

| 组 | hit@1 | hit@6 | mrr | strong@6 | 库外槽% | data 槽% | top6 不同文件 | 公式 22 hit@6 | 跨源 24 hit@6 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 基线（1FB23F2A：软权重 ×1.25/×0.8，depth 40） | 45.0% | 67.5% | 0.528 | 82.9% | 18.5% | 0.1% | 4.42 | 63.6% | 87.5% |
| +B 按文件去重 | 45.0% | 71.1% | 0.544 | 84.3% | 23.1% | 0.7% | 5.96 | 63.6% | 91.7% |
| +A 硬过滤 `knowledge/` | 46.0% | 73.5% | 0.552 | 84.3% | **0%** | 0.1% | 4.41 | 63.6% | 91.7% |
| +A+B | 46.0% | 78.2% | 0.573 | 85.7% | 0% | 0.3% | 6.00 | 63.6% | 95.8% |
| +C ASCII 加权（不硬过滤） | 55.7% | 77.2% | 0.639 | 97.1% | 17.6% | 1.6% | 4.14 | 68.2% | 91.7% |
| **A+B+C（已固化为默认）** | **58.1%** | **85.6%** | **0.682** | **97.1%** | **0%** | 2.7% | 6.00 | 68.2% | 95.8% |

**逐域 hit@6（同一快照，四列对照）**

| 域 | 1FB23F2A 基线 | +A 硬过滤 | +A+B | A+B+C |
| --- | --- | --- | --- | --- |
| 世界交互 | 60% | 80% | 88% | 88% |
| 单位控制 | 80% | 80% | 84% | 92% |
| 变量与作用域 | 68% | 68% | 76% | 76% |
| 性能限制 | 92% | 92% | 92% | 96% |
| 战斗与单位 | 76% | 76% | 76% | 96% |
| 执行模型 | 84% | 84% | 96% | 96% |
| 控制流 | 56% | 68% | 76% | 80% |
| 方块与锚点 | 48% | 64% | 68% | 76% |
| 液体与物流 | 64% | 72% | 72% | 80% |
| 电力与热 | 36% | 40% | 44% | 80% |
| 绘制文本 | 76% | 84% | 92% | 92% |
| 读写感知 | 70% | 74% | 74% | 74% |

全开组最弱 3 域：**读写感知 74%**、**变量与作用域 76%**、**方块与锚点 76%**（基线组是 电力与热 36% / 方块与锚点 48% / 控制流 56%）。
最大改善域是**电力与热 36% → 80%（+44 pt）**。

**五条结论**

1. **C（ASCII 加权）是单项收益最大的开关**：单开就能 hit@1 +10.7 pt、hit@6 +9.7 pt、mrr +0.111、strong +14.2 pt，
   公式题 63.6% → 68.2%。它修的是「题干是 `LExecutor.java`、`ConsumePower.java:10` 这类标识符，dense 向量把信号稀释掉」。
2. **B（去重）单独用不安全**：只 +3.6 pt，但库外槽位 18.5% → 23.1% —— 去重让更多**不同文件**进 top-6，
   其中一部分是 tools/*.py 与 docs/；必须配 A 才有净收益（A+B 78.2%）。
3. **A（硬过滤）与软路径权重不重叠、可叠加**：软权重已把库外 top-1 压到 ~18.5% 槽位，A 再挤出 +6.0 pt hit@6
   （67.5→73.5）并把库外污染清零；两者不是重复实现。
4. **硬过滤不会把 00-data 一起挡掉**（lead 的问题）：硬过滤索引 921 chunk 里 18 张 00-data 摘要表都在，
   data 槽占比 0.1%（A）/ 0.3%（A+B）/ 2.7%（全开）；真正被挡掉的是 tools/*.py 的 6266 个 code chunk、
   docs/游戏速查、mindustry-blueprint —— 这些本来就极少是答案（data 槽在全开组升到 2.7% 是因为候选更集中，不是丢表）。
5. **A+B+C = 85.6%，超过 lead 定的 80% 门槛**，比 1FB23F2A 基线 hit@6 +18.1 pt、hit@1 +13.1 pt、mrr 0.528→0.682、
   strong@6 82.9%→97.1%。跨源题 87.5%→95.8%；公式题仍低于 lexical 的 81.8%（68.2%）—— ASCII 加权只补标识符匹配，
   补不了「算式行缺锚点」，与 §8 规则 2、§9 的 strong@6 结论一致。

另一个顺带发现：**「世界交互」六组 strong@6 全为 0**（hit@6 最高 88%）—— 命中的文章里没有「文件:行号」锚点。
这是 §8 规则 2（数字要搬正文、要带锚点）的又一证据，与检索策略无关。

**产物 / 复现**

- `<临时暂存目录>/tools/kb_scope.py`（三开关副本，仓库 kb.py 未动）；`08-evidence/bench/kb_scope_eval.py`（6 变体 runner）
- `08-evidence/bench/snap_ab.json` + `snap_ab_pq.json`（本表原始数据）；`scope_ab.json`（旧语料，作废仅留档）
- 快照：`<临时暂存目录>/out/_snap_knowledge`；索引：`<临时暂存目录>/out/_kb_base_snap`（8164 chunk）、`_kb_scope_snap`（921 chunk）

### 10.6 固化：`tools/kb.py` 默认开启 A+B+C

lead 要求「固化进仓库要用的那一个文件，不要另起 kb_scope.py」，已直接改 `<临时暂存目录>/tools/kb.py`（同步到仓库 `tools/kb.py`）：

| 项 | 值 |
| --- | --- |
| 文件 | `tools/kb.py`（<临时暂存目录> 版，待 Lead 同步进仓库） |
| md5 / 大小 | **1289C89F**28B4238C988B8415FB8ED562 / 26,338 B |
| build（`KB_DIR=<临时暂存目录>/_kb_final`） | **8167 chunks / 138 files / 18 data_tables** |
| bench20（前 20 题，新库） | **hit@1 65.0%、hit@6 95.0%、mrr 0.745、库外槽 0%**（20 题冒烟，非全量） |

**三个开关（默认全开，置 0 回退到 1FB23F2A 行为；CLI 与 MCP 签名不变）**

| 开关 | 默认 | 关掉后 |
| --- | --- | --- |
| `KB_ONLY_KNOWLEDGE` | 1：只检索 `knowledge/`（含 00-data 摘要） | 0：全库混排（tools/、docs/、blueprint 都进来） |
| `KB_DEDUPE_FILE` | 1：k 数文档，同文件 top3 块合并、正文裁 1200 字 | 0：k 数 chunk（旧行为） |
| `KB_ASCII_BOOST` | 1：FTS 标识符 ×2、dense ×0.7 | 0：两路等权 |

其余保留不变：`_` 前缀目录排除、`KB_KNOWLEDGE_BOOST=1.25` / `KB_CODE_PENALTY=0.8` 路径权重、
`KB_CANDIDATES`（默认 40，原 30）、frontmatter 与输出字段（`path/start/end/kind/heading/text/score`，去重时多一个 `n_chunks`）。
**A 只在调用方没指定 `kind` 时生效**：MCP 的 `kb_search(kind="code")` 仍能搜 tools/*.py，避免把代码检索一起关死。

```bash
# 复现（仓库内）
python tools/kb.py build
python tools/kb.py search "ConsumePower capacity" -k 3
# 对照实验
python knowledge/08-evidence/bench/kb_scope_eval.py --out snap_ab.json --per-question snap_ab_pq.json
```

### 10.7 最终交付库评测（H4 初版 → FINAL2 终版，2026-11-08 05:12 / 05:23）

lead 冻结内容后，recon-d 在仓库重建了交付库；本节是在**该成品库**上跑冻结 300 题的结果（上一节 10.5/10.6 用的是评测期冻结快照 `_snap_knowledge`，两者语料内容一致、索引方式不同）。

| 项 | 值 |
| --- | --- |
| 库文件 | 仓库 `out/_kb/kb.sqlite3`（42,708,992 B，mtime 2026-11-08T05:12:10） |
| 索引规模 | **8211 chunk / 141 files**（kind：code 6267 / doc 1781 / data 163；FTS 8211 行，18 张 `00-data` 表在库） |
| gold（评测时实测） | **66 篇 md 文章 + 18 张 `00-data` 表**（02-world 12、03-combat 10、06-mlog 8、01-execution 6、05-campaign 6、07-patterns 6、04-units 5、08-evidence 5、tools 3、根目录 5）|
| 检索策略 | `tools/kb.py` 1289C89F，A+B+C 全开；k=6、candidates=40 |
| 结果 | coverage **100%**、hit@1 **60.0%**、hit@6 **86.7%**、mrr **0.6967**、strong@6 **94.2%**、库外槽 **0.0%**、data 槽 2.4%、top-6 平均不同文件 **6.00** |
| 推导专测 | 公式题 22 道 **72.7%（16/22）**；跨源题 24 道 **95.8%（23/24）** |
| **FINAL2 复测（详见 §10.8；其后还有 FINAL3 终版）** | 库 **8277 chunk / 142 files**、gold **67 篇 + 18 表** → hit@1 **59.7%**、hit@6 **86.3%**、mrr **0.6943**、strong@6 **94.2%**、库外槽 0%、公式 72.7%、跨源 95.8%；较 H4 全部跌幅 < 1 pt（BENCH.0182 抢槽、BENCH.0058 gold 口径误判） |

**逐域（按 hit@6 升序）**

| 域 | hit@1 | hit@6 | mrr | strong@6 |
| --- | --- | --- | --- | --- |
| 变量与作用域 | 40.0% | **76.0%** | 0.513 | 72.7% |
| 方块与锚点 | 52.0% | **76.0%** | 0.591 | 100% |
| 电力与热 | 56.0% | **76.0%** | 0.641 | 100% |
| 液体与物流 | 48.0% | 80.0% | 0.627 | 100% |
| 读写感知 | 44.0% | 80.0% | 0.593 | 88.9% |
| 控制流 | 60.0% | 84.0% | 0.686 | 100% |
| 世界交互 | 44.0% | 92.0% | 0.584 | 90.9% |
| 单位控制 | 60.0% | 92.0% | 0.725 | 88.9% |
| 性能限制 | 84.0% | 96.0% | 0.881 | 100% |
| 战斗与单位 | 88.0% | 96.0% | 0.901 | 100% |
| 执行模型 | 68.0% | 96.0% | 0.775 | 100% |
| 绘制文本 | 76.0% | 96.0% | 0.843 | 91.7% |

**最弱 3 域**：变量与作用域 76%、方块与锚点 76%、电力与热 76%（三域 hit@6 并列，按 hit@1 再排：变量 40% < 方块 52% < 电力 56%；变量域 strong@6 也只有 72.7%，是全库唯一「命中但缺行号锚点」的重灾区）。

**与快照版（10.5 的 A+B+C 行，58.1/85.6/0.682/97.1）对比**：hit@1 **+1.9 pt**、hit@6 **+1.1 pt**、mrr **+0.015**、strong@6 **−2.9 pt**（97.1→94.2）、公式题 68.2→**72.7**、跨源 95.8→**95.8**。差异来源：交付库比快照索引多 44 chunk / 3 文件（recon-d 的 build 索引全库、含更多 `04-units`/`08-evidence` 内容），分母变大后 strong@6 略降、逐域最低值从 74 抬到 76；**主结论不变**（库外槽 0、hit@6 86%+，仍显著高于 lexical 78.7%）。

```bash
# 复现（用成品库跑冻结 300 题）
cd knowledge/08-evidence/bench
KS_DB_BASE=<仓库>/out/_kb/kb.sqlite3 KS_DB_SCOPE=<仓库>/out/_kb/kb.sqlite3 \
  python kb_scope_eval.py --variants baseline --out final_ab.json --per-question final_ab_pq.json
```

未命中 40 题按域：变量 7、方块 6、电力 6、液体 5、读写 5、控制流 4、世界交互 3、单位控制 2、执行模型 1、绘制 1、性能 1、战斗 1；逐题明细在 `final_ab_pq.json` 的 `baseline` 数组（`hit=false` 的行）。


### 10.8 FINAL2 / FINAL3 复测（**交付口径 = FINAL3 终版**，2026-11-08 05:23 / 05:36）

lead 在最后一轮内容修正后重新发布了库；本节是在**成品库**上重跑冻结 300 题：先 FINAL2（相对 §10.7 H4 逐题对比），再 FINAL3（相对 FINAL2 逐题对比，结果完全一致）。

| 项 | H4（05:12） | **FINAL2（05:23）** | Δ |
| --- | --- | --- | --- |
| 库文件 | 42,708,992 B | **43,065,344 B**（mtime 05:22:57，8s 稳定性校验通过） | +356,352 B |
| 索引规模 | 8211 chunk / 141 files | **8277 chunk / 142 files**（code 6321 / doc 1793 / data 163） | +66 chunk / +1 file |
| gold | 66 篇 md + 18 表 | **67 篇 md + 18 表**（新增 `knowledge/INTEGRATION.md`；VERSION/KB/README/AI-SETUP 补写） | +1 篇 |
| coverage | 100% | **100%** | 0 |
| hit@1 | 60.0% | **59.7%** | −0.33（1 题） |
| hit@6 | 86.7% | **86.3%** | −0.34（1 题） |
| mrr | 0.6967 | **0.6943** | −0.0024 |
| strong@6 | 94.2% | **94.2%** | 0 |
| 库外槽 / data 槽 | 0.0% / 2.4% | **0.0% / 2.4%** | 0 |
| 公式 22 题 | 72.7% | **72.7%**（16/22） | 0 |
| 跨源 24 题 | 95.8% | **95.8%**（23/24） | 0 |

**跌幅全部 < 1 pt（最大 0.34），不触发回滚；但两处变化已逐题定位到具体题号**

| 题号 | 域 | 变化 | 原因（证据） |
| --- | --- | --- | --- |
| **BENCH.0182** | 性能限制 | top-1 → rank 2（仍 hit@6） | 新根文档 `knowledge/KB.md` 挤掉了原 top-1 `06-mlog/M01-执行模型总览.md`；典型「新根文档抢槽」，可接受 |
| **BENCH.0058** | 控制流 | hit@6 失分（原 rank 5） | 原来命中靠 `knowledge/VERSION.md` 正文里列了 `instr_semantics.json` 这个文件名；VERSION.md 补写后不再出现 → gold 定义（正文含 src basename）不再成立。**这是 gold 口径误判，不是检索退化**：新 top-6 里第 5 位换成了语义更对的 `01-execution/E02-指令语义陷阱.md` |

**新根文档占槽统计（FINAL2，k=6 × 300 题 = 1800 槽）**：`knowledge/KB.md` 33 槽、`AI-SETUP.md` 24、`08-evidence/probes/README.md` 24、`VERSION.md` 12、`INTEGRATION.md` 8、`README.md` 3，合计 104 槽（5.8%）；除 BENCH.0182 外未再造成 top-1 损失，BENCH.0058 属上面说的 gold 口径问题。

**逐域变化**：仅两处（其余 10 域与 H4 完全一致）——性能限制 hit@1 84.0→80.0（BENCH.0182，hit@6 仍 96.0）、控制流 hit@6 84.0→80.0（BENCH.0058）。最弱 3 域不变：变量与作用域 76.0%、方块与锚点 76.0%、电力与热 76.0%。

**复现**

```bash
cd knowledge/08-evidence/bench
KS_DB_BASE=<仓库>/out/_kb/kb.sqlite3 KS_DB_SCOPE=<仓库>/out/_kb/kb.sqlite3 \
  python kb_scope_eval.py --variants baseline --out final_ab2.json --per-question final_ab2_pq.json
```

产物：`final_ab2.json`（2,537 B，MD5 `079922AB`）、`final_ab2_pq.json`（128,980 B，MD5 `4E302505`，逐题 `hit` / `rank` / `top`）。**交付验收以本节 FINAL2 行为准**（H4 仅作前后对照保留）。


**FINAL3（交付终版，2026-11-08 05:36）**

| 项 | FINAL2（05:23） | **FINAL3（05:36）** | Δ |
| --- | --- | --- | --- |
| 库文件 | 43,065,344 B | **43,085,824 B**（mtime 05:35:43，8s 稳定性校验通过） | +20,480 B |
| 索引规模 | 8277 chunk / 142 files | **8284 chunk / 142 files**（code 6321 / doc **1800** / data 163） | +7 chunk（全是 doc） |
| gold | 67 篇 md + 18 表 | **67 篇 md + 18 表**（内容改动：`03-combat/C06` 与 `C10` 的 9 行 DPS 修正；bench 下 25 个中间件移入 `08-evidence/bench/_scripts/`，下划线目录不进索引；rt_verify 报告更新） | 0 |
| coverage | 100% | **100%** | 0 |
| hit@1 | 59.7% | **59.7%** | 0 |
| hit@6 | 86.3% | **86.3%** | 0 |
| mrr | 0.6943 | **0.6943** | 0 |
| strong@6 | 94.2% | **94.2%** | 0 |
| 库外槽 / data 槽 | 0.0% / 2.4% | **0.0% / 2.4%** | 0 |
| 公式 22 题 | 72.7% | **72.7%**（16/22） | 0 |
| 跨源 24 题 | 95.8% | **95.8%**（23/24） | 0 |

**题号级差异：0/300**。逐题比对 `hit` / `rank` / `top-6` 三个字段：lost hit **0**、gained hit **0**、rank 变化 **0** —— 新库多出的 7 个 doc chunk 来自 C06/C10 的 DPS 行修正，未触及任何一题的 gold 文档与 top-6 排序，因此指标与 FINAL2 逐位相同（59.67 / 86.33 / 0.6943 / 94.21）。最弱 3 域仍为变量与作用域 76.0%、方块与锚点 76.0%、电力与热 76.0%。

```bash
# 复现（FINAL3；脚本已移入 _scripts/，用 KS_STAGE 指回 <临时暂存目录>）
cd knowledge/08-evidence/bench
KS_STAGE=<临时暂存目录> KS_DB_BASE=<仓库>/out/_kb/kb.sqlite3 KS_DB_SCOPE=<仓库>/out/_kb/kb.sqlite3 \
  python _scripts/kb_scope_eval.py --questions questions.jsonl --source-kinds source_kind.json \
    --derive _scripts/questions-derive.jsonl --variants baseline \
    --out final_ab3.json --per-question final_ab3_pq.json
```

产物：`final_ab3.json`（2,448 B，MD5 `7102DF0B`）、`final_ab3_pq.json`（128,988 B，MD5 `D879B502`，逐题 `hit` / `rank` / `top`）。FINAL2 的 `final_ab2.json`（MD5 `079922AB`）留在 bench 根作对照，`final_ab2_pq.json` 已随中间件移入 `_scripts/`。**交付验收以 FINAL3 行为准：hit@1 59.7%、hit@6 86.3%、mrr 0.6943、strong@6 94.2%、库外槽 0%、公式 72.7%、跨源 95.8%**。

注：`kb_scope_eval.py` 因移入 `_scripts/` 后 `HERE.parents[1]` 会少上溯一级，已加 `KS_STAGE` / `KS_STAGE_TOOLS` 环境变量覆写（默认行为不变），本次运行即用它指回 `<临时暂存目录>`。

## 11. v2 草案：跨源推导题 24 道（`questions-derive.jsonl`，不进主指标）

**为什么单独一个文件**：300 题已冻结（`questions.jsonl` 一字不改，主指标只认它）。
v2 想解决的是 §9 暴露的结构性问题 —— 260/300（86.7%）的题只需查一行源码，考不出「组合两个真源做推导」。
这 24 道题是**样本草案**，用来先看清「推导型覆盖」长什么样，再决定是否扩成 v2 正式题库。

**规格**

| 项 | 值 |
| --- | --- |
| 题数 / id | 24 题，`BENCH.0301`–`BENCH.0324`（与冻结题库 id 段不冲突） |
| 分布 | 12 域 × 2 题；难度全为 3（hard）；类型 calc 11 / mc 9 / short 4 |
| 新增字段 | `srcs`（**≥2** 个真源，每题都校验存在性与行号）、`derive`（一句话说明「为什么必须组合才能答」） |
| 是否进主指标 | **否**。主评测只跑 `questions.jsonl`；本节数字仅作 v2 参考 |
| 生成器 | `_gen_derive.py`（可重跑，同样做「文件存在 + 行号不越界」断言） |

**三个样例（每题都能看出「少一个源就答不出」）**

- `BENCH.0301`（执行模型）：`instructionsPerTick=2`（`world/blocks/logic/LogicBlock.java:46`）×
  `maxInstructions=1000`（`logic/LExecutor.java:41`）→ 600 条指令要 300 tick = 5 s，且未突破 1000 上限；
  只查一个常量答不出耗时，只查上限也答不出。
- `BENCH.0319`（电力与热）：impact-reactor `power=25/tick`（`tools/block_attrs.json`）× 1 tick=1/60 s
  （`knowledge/VERSION.md`）÷ 冷却液 `cryofluid:15/s`（同一数据表）→ **100 电力/液体单位**。
- `BENCH.0324`（战斗与单位）：护甲公式 `max(damage-armor, 0.1·damage)`
  （`entities/Damage.java:659-660` + `Vars.java:133 minArmorDamage=0.1`）代入
  mace `armor=4`（`data/game/units.json`）→ 9 伤害打 5；armor=20 时被 0.9 保底 —— 三个源缺一不可。

**草案已测（lexical，<临时暂存目录> 104 文件 / 1051 chunk）**：coverage 100%、hit@6 **91.7%**（22/24）。
注意这个数字偏乐观：出题时已保证「每个源都有文章写过」，它测的是**组合检索**能不能一次捞到多个源，
不测 AI 会不会主动想到组合。真正的 v2 验收标准应是「多源问答的正确率」，不是 hit@6。

**如果扩成 v2 正式题库，建议规则**

1. 每域 ≥5 题、总量 ≥60，且**公式题占比 ≥40%**（当前 300 题只有 7.3%）；
2. 每题 `srcs` 至少跨两类真源（源码 / 数据表 / 实测 / 文档口径），并写明「缺哪个源就答错」；
3. 与冻结 300 题共用同一套 `eval_kb.py` 与 gold 口径，但在报告里**永远单列**，不合并总分；
4. 新增「答案必须给数值 + 单位」的判分项：推导题的失败大多不是检索失败，而是单位换算错（/tick 与 /s 差 60 倍）。

---

## 12. 英文化之后的重新测量（2026-11-19）

2026-11-19 知识库正文全部改成英文（见 `knowledge/STYLE-en.md`），题库仍是中文。
于是这 300 题从「同语言检索」变成了**跨语言检索**：问句是中文，答案是英文文章。
这一节记录重新测量的结果，以及两种候选改法各自的真实收益。

### 12.1 四种配置（同一语料、同一 chunker、300 题）

| 配置 | hit@1 | hit@6 | mrr@6 | ndcg@6 | ms/query |
| --- | --- | --- | --- | --- | --- |
| dense，`BAAI/bge-small-zh-v1.5`（默认） | 38.7% | 75.7% | 0.514 | 0.574 | 118 |
| dense，`paraphrase-multilingual-MiniLM-L12-v2` | 44.0% | 76.0% | 0.552 | 0.603 | 78 |
| hybrid，`bge-small-zh`（默认） | **50.3%** | **81.7%** | **0.616** | **0.666** | 117 |
| hybrid，`multilingual-MiniLM` | 50.0% | 80.7% | 0.613 | 0.661 | 78 |
| hybrid，`bge-small-zh`，关掉中文名桥 | 49.7% | 81.7% | 0.613 | 0.663 | 117 |

复现：

```bash
python tools/kb.py build
python knowledge/tools/eval_kb.py --root . --engine kb --mode hybrid --limit 300

# 多语言 embedding（模型走 HF 镜像下载，落在 out/_kbmodels/）
HF_ENDPOINT=https://hf-mirror.com KB_DIR=out/_kb_ml \
  KB_EMB_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
  python tools/kb.py build
KB_DIR=out/_kb_ml KB_EMB_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
  python knowledge/tools/eval_kb.py --root . --engine kb --mode hybrid --limit 300

# 关掉中文名桥做对照
MLOG_NO_EXPAND=1 python knowledge/tools/eval_kb.py --root . --engine kb --mode hybrid --limit 300
```

### 12.2 三条结论

1. **多语言 embedding 值得换，但只值得换一半。** 只开 dense 时它把 hit@1 从 38.7% 抬到
   44.0%（+5.3 点）且快 34%；一旦上了 hybrid（trigram BM25 + RRF），两条配置打平
   （50.3% vs 50.0%）。原因是混合检索的稀疏腿本来就在补语言错配，换 embedding 是在
   补同一块短板。**默认仍是 `bge-small-zh`**，多语言模型作为 `KB_EMB_MODEL` 的可选项留下。
2. **中文名桥（`tools/cjken.py`）整体 +0.6 点，但对含实体名的题是 0 与 1 的差别。**
   300 题里只有 12–28 题含名字表里的词，所以总分动得少；对「差扰是什么」这类问题，
   没有桥就是全库 0 命中。
3. **cross-encoder 重排没重测，默认继续关。** 它要 ~7 s/query（300 题 ≈ 35 分钟），
   而 11-17 在中文语料上测过：dense-rr hit@1 37.0% / hit@6 59.0%，比不重排还差。
   重排要重新变成候选，得先换更强的 reranker，而不是调参数。

### 12.3 仍然存在的边界

题库是中文、语料是英文，这**不是**评测缺陷而是真实用法：提问的人写中文，母本是英文。
剩下 266/300 题不含实体名（问的是机制，如「把 @counter set 成行号会怎样」），
名字桥帮不上，多语言 embedding 也只补到 44%。再往上要么给题库配英文版对照
（会掩盖真实场景），要么上一版跨语言翻译层（成本另计）——两条都不在本次范围内。
