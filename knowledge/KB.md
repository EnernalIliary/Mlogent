# Mindustry 机制知识库 · 入口（KB.md）

> 版本：v1.1 · 覆盖 Mindustry v160.7（数值）/ v159.3（源码语义）· 只收原版机制，不含模组与工具产品开发
> 面向读者：**AI 与人类**。目标不是"能查到答案"，而是**能推导答案**。
> 规模：**63 篇文章 / 11 张 canonical 数据表 / 85 条断言 / 20 条可执行探针 / 300 题评测**；检索库 8,317 chunk，实测 hit@1 **59.7%**、hit@6 **86.3%**（k=6，300 题冻结集）。

## 0. 30 秒上手

1. 先读本文件（你在读）→ 再读 `08-evidence/CHEAT.md`（速查卡：40 陷阱 + 30 数字 + 20 路由）→ 接 AI 看 `AI-SETUP.md`。契约与版本见 `CONVENTIONS.md`、`VERSION.md`；**旧知识库是否还算数见 `INTEGRATION.md`**。
2. 想知道"某个机制怎么算"→ 去 `00-data/` 查表、`05-campaign/` 查公式。
3. 想知道"某个东西什么数值"→ `00-data/blocks.json`、`turrets.json`、`bullets.json`、`units.json`。
4. 想写/读 mlog → `01-execution/`（执行模型与陷阱）+ `06-mlog/`（指令语义）。
5. 想复用成熟写法 → `07-patterns/`（架构与 idiom）。
6. 怀疑某结论 → `08-evidence/claims.jsonl`（85 条可复测断言）+ `probes/`（可执行探针）+ `bench/`（300 题评测）。

## 1. 目录地图

| 目录 | 内容 | 何时用 |
|---|---|---|
| `00-data/` | 机器可读事实表：blocks/turrets/bullets/units/liquids/items/status/rules + formulas.json | 查任何数值、做计算、校验结论 |
| `01-execution/` | mlog 执行模型、指令预算、语义陷阱 30 条、变量边界、时间精度、跨版本差异 | 写逻辑前必读；调试诡异行为 |
| `02-world/` | 方块与锚点、配方、电力、液体、热、物流、钻探、载荷、地形、存储、配置、沙盒、中英名对照（W01-W16） | 机制"怎么运作" |
| `03-combat/` | 伤害管线、炮塔、弹道、状态、护甲、单位武器、治疗护盾、敌军、防御、DPS 实例、炮塔评价（C01-C11） | 战斗数值与判伤、选型 |
| `04-units/` | 单位类型/移动、生产、AI、能力、经验等级、单位名对照（U01-U06） | 单位行为与产能 |
| `05-campaign/` | 波次、难度、胜负、敌基、版本差异、Rules 全字段（CAMP.*） | 战役与规则定制 |
| `06-mlog/` | 指令表（73 条 instructions.json）+ 语言语义 8 篇（M01-M08） | 查指令参数、语义边界 |
| `07-patterns/` | 架构、状态机、总线、数据结构、索敌、性能、单位多控、@counter 架构（P01-P08）+ idioms.json | 设计蓝图 |
| `08-evidence/` | claims.jsonl（85 条可复测断言）、probes/（可执行探针）、idioms.json、anti-patterns.md、bench/（300 题 + 跨源推导题） | 验证与评测 |
| `tools/` | extract_rt.py（jar 反射）、extract_src.py（源码）、check_kb.py、build_index.py、eval_kb.py、kb.py | 复现与维护 |

## 2. AI 使用协议（重要）

### 2.1 检索顺序（不要跳步）
1. **精确查表**：`00-data/*.json` — 结构化、带 id，先命中就先赢。
2. **机制公式**：`00-data/formulas.json` — 拿到 formula 再代数。
3. **文章正文**：按域读对应 `.md`，注意"常见误解"小节——它专门用来纠正直觉。
4. **证据层**：`08-evidence/claims.jsonl` 找可复测断言；结论冲突时按 id 回溯。
5. **源码/真源**：仅在上述不够时读 `Mindustry-Source/`（v159.3 语义）或重跑 `tools/extract_rt.py`（v160.7 数值）。

### 2.2 置信度（每条知识的 conf 字段）
- `S` 源码可查（给文件:行）
- `E` 实测可复现（给脚本与输出）
- `I` 由 S/E 推导（必须写出推导链）
- `U` 未验证（**回答时必须声明不确定**，禁止当成事实）

### 2.3 五条硬规则
1. **没有来源的数字不许说**。要么来自 `00-data/`，要么 `文件:行`，要么实测记录。
2. **单位显式**。速率一律写清 `/tick` 还是 `/s`（1/tick = 60/s）；长度写 tile 还是 px（1 tile = 8 px）。
3. **双版本**。数值默认 v160.7；语义/源码引用标 v159.3；已知差异见 `VERSION.md` 与 `05-campaign/CAMP.VERSION.001`。
4. **反例优先**。学一个机制时先看它的"常见误解"与 anti-patterns，直觉错误比无知更危险。
5. **不写工具**。本库只描述游戏与 mlog 本身；工具/模组/产品相关内容不属于这里。

### 2.5 回答前自检（4 问）
1. 这个数字来自 `00-data/` 还是我背的？
2. 单位说清了吗（/tick 还是 /s、tile 还是 px）？
3. 相关文章的「常见误解」小节有没有在反驳这个结论？先读再答。
4. 冲突时我比对了两个版本吗（v160.7 数值 / v159.3 语义）？

### 2.4 回答风格（给 AI）
- 先给**结论 + 算式**，再给来源（`00-data/blocks.json#id=duo` 这类锚点）。
- 涉及取舍时给**两条以上路径**与各自代价（电/空间/预算/复杂度）。
- 不确定就标 `conf: U` 并说明缺哪一步验证，**不要用"一般来说"糊过去**。

## 3. 12 个能力域 → 文章索引

| # | 能力域 | 主入口 |
|---|---|---|
| 1 | 执行模型与 tick | `01-execution/E01`、`06-mlog/M01` |
| 2 | 变量与作用域 | `01-execution/E03`、`06-mlog/M02` |
| 3 | 控制流与时间 | `01-execution/E04`、`06-mlog/M03` |
| 4 | 读写与感知 | `06-mlog/M04` |
| 5 | 绘制与文本 | `06-mlog/M05` |
| 6 | 世界交互 | `06-mlog/M06`、`02-world/W11` |
| 7 | 单位控制 | `06-mlog/M07`、`04-units/U03`、`07-patterns/P07`、`07-patterns/P08` |
| 8 | 性能与预算 | `01-execution/E01`、`06-mlog/M08`、`07-patterns/P06`、`07-patterns/P08` |
| 9 | 方块/电力/热/物流 | `02-world/W01-W06` |
| 10 | 战斗与伤害 | `03-combat/C01-C05` |
| 11 | 单位与产能 | `04-units/U01-U05`、`03-combat/C06` |
| 12 | 战役与规则 | `05-campaign/CAMP.*` |

（完整文章清单由 `tools/build_index.py` 生成到 `index.json`。）

## 4. 数值真源优先级

1. `00-data/*.json`（由 v160.7 真服务器反射生成，`tools/extract_rt.py`）
2. `Mindustry-Source/core/src/**`（v159.3，语义权威）
3. `08-evidence/claims.jsonl` 中 pass 的实测
4. 本库文章正文
5. 仓库其它笔记（`MBO/`、`docs/`、`Logic-Docs`）——**只作线索，不作证据**

已知错误清单（务必先看）：`VERSION.md` §已知错误。典型：`data/game` 的 craftTime 全为 -1；`docs/速查卡` 耗电列实际是 /tick 却标成 /s（差 60 倍）。

## 5. 常见陷阱 Top 10（先记这些，能避开 80% 的错）

1. `wait` 的单位是 **秒**（`LExecutor.java:1218-1232`：`curTime += Time.delta/60f`），`wait 1` ≈ 60 tick；写成「等 N tick」是常见错。`@time` 单位是**毫秒**（`GlobalVars.java:195`），`@second`/`@minute` 才是秒。
2. `reload` 是"两次开火间隔 tick"，DPS 要用 `damage × 弹数 / reload × 60`，别忘了 `ammoMultiplier`。
3. `range` 是 **tile**（1 tile = 8 px）；子弹射程 = `lifetime × speed`（单位 px），换算 tile 要 /8。
4. `usage` 是"每 tick 电量"，`usagePerSecond = usage × 60`（v160.7 才有该字段）。
5. 护甲减免是**乘性还是减性**要按 `Damage.java` 的当前实现，不同版本改过——别背旧结论。
6. 传送带吞吐 `items/s = speed × 60 / 单件占位`，不是"速度"本身。
7. 状态效果同类**不叠加**（刷新时长），不同类乘算；顺序影响结果。
8. `getlink` 索引**从 0 开始**且随方块变动而变，蓝图重贴后编号会错位。
9. `@counter` 可写，跳转是**绝对索引**；在循环里改它会造成不可预测跳转。
10. 每 tick 指令预算有限（`instructionsPerTick` 类规则），大循环必须分帧。
11. `set @ipt ...` / `set @unit ...` 会被静默丢弃（`LAssembler.java:26-27` 的 `putConst`）：常量改不了，只有 `setrate`/`ubind` 能改运行值；`@counter` 反而可写。
12. `uradar` 的**第 5 个参数（order）是死槽**，写了不报错也不生效；radar 缓存是 **30 tick**（`LExecutor.java:761-763`），不是 40。
13. `ucontrol` 的坐标参数一律是 **tile**（内部 `World.unconv` = ×8 转 px）；喂像素坐标会偏 8 倍。
14. `strictEqual` 不是恒 false：`ConditionOp` 里那个 `(a,b)->false` 只是 `function` 字段，`LExecutor.test()` 会特判类型位相同 + 精确相等，所以 `jump strictEqual` 可以成立。
15. 记忆格容量不是 32：**memory-cell 64 / memory-bank 512 / world-cell 512**（32 是类默认值）；**越界读返回 null（NaN）不是 0**，越界写静默丢弃（`MemoryBlock.java:64-81`）。
16. `format` 一次只替换**一个**占位符，且只填**已在文本缓冲里、编号最小**的那个；占位符只认单数字 `{0}`-`{9}`，所以顺序是「先 `print` 再 `format`」。
17. `@ipt` 的单位是**点/tick**（hyper 25 ⇒ 1500 点/s），单 tick 实际预算 `min(5×ipt, maxInstructionsPerTick)`，hyper 会被截到 **40** —— 别按 125 算循环开销。

## 6. 维护

```powershell
# 重新生成 v160.7 数据表（需 out/_server160.jar + out/jre21）
python knowledge/tools/extract_rt.py
# 索引 / 门禁（--strict 让 warning 也阻断）
python knowledge/tools/build_index.py
python knowledge/tools/check_kb.py --all
# 重建检索库：KB_ROOT 必须是仓库根，KB_DIR 指定输出目录
$env:KB_ROOT='F:\OneDrive\桌面\AtomicStates'; $env:KB_DIR='<临时目录>'
python knowledge/tools/kb.py build
# MCP 在跑时不要直接覆盖 out/_kb/kb.sqlite3（WinError 5），用 backup 原地发布
python knowledge/tools/publish_db.py <临时目录>\kb.sqlite3 out\_kb\kb.sqlite3
# 发布后固定义务：三项校验（STRUCT/COUNT/RETRIEVAL）
python knowledge/tools/postpublish.py --db out/_kb/kb.sqlite3 --staging <临时目录>\kb.sqlite3
# 评测（300 题，A+B+C 检索开关默认已开）
python knowledge/tools/eval_kb.py --kb knowledge --engine kb -k 6
# 冒烟（20 题确定性样本，同一批行号）
python knowledge/tools/bench20.py --db out/_kb/kb.sqlite3
```

`check_kb.py` 的 warning 是**提示级、不阻塞**（exit 0 即合规）；`W_NUM_NO_SOURCE` 多为源码行号与举例数值，不必逐行补来源。

新增一篇文章：复制模板 → 填 frontmatter（id 唯一）→ 七段齐全 → `check_kb.py` 零 error → 重跑 index 与 kb 重建 → 在 `claims.jsonl` 里补可复测断言。
