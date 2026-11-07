# Mindustry 机制知识库（knowledge/）

一份可被 AI 直接使用、也可被人阅读的 Mindustry 原版机制知识库：**55 篇文章 + 11 张 canonical 数据表（另 6 张 rt_list 抽查件）+ 85 条可复测断言 + 20 条可执行探针 + 300 题评测**，覆盖 v160.7（数值）与 v159.3（源码语义）双版本，已建成可检索的正式库（8,285 chunk）。

**实测指标**（A+B+C 检索全开，k=6，300 题冻结集）：hit@1 **59.7%**、hit@6 **86.3%**、mrr 0.694、库外槽 **0%**；20 题冒烟 A@1 **16/20**（旧版 4/20）。

## 从哪开始

| 你是 | 先看 |
|---|---|
| 人，想快速了解 | [`KB.md`](KB.md) → [`08-evidence/CHEAT.md`](08-evidence/CHEAT.md)（40 陷阱 + 30 数字 + 20 条检索路由） |
| AI/Agent，要接入 | [`AI-SETUP.md`](AI-SETUP.md)（三种接入方式 + 可直接粘贴的系统提示词） |
| 要查某个数值 | [`00-data/`](00-data/) 的 JSON（带 id 与 src） |
| 想知道旧知识库还算不算数 | [`INTEGRATION.md`](INTEGRATION.md)（逐项映射：谁被谁取代、什么情况才回查旧文件） |
| 要改/扩这个库 | [`CONVENTIONS.md`](CONVENTIONS.md)（写作契约）+ [`tools/REBUILD.md`](tools/REBUILD.md)（重建发布流程） |

## 结构

```text
knowledge/
├── KB.md                 入口：30 秒上手 / AI 使用协议 / 12 能力域 / 陷阱 Top 14
├── AI-SETUP.md           把库交给 AI 的三种方式 + 系统提示词
├── INTEGRATION.md        旧知识库整合映射（停更/取代/仍独有）
├── CONVENTIONS.md        写作契约（frontmatter / 七节 / 数值来源 / 版本口径）
├── VERSION.md            双版本真源优先级 + 已知错误清单 + 交付验收 + 环境坑
├── 00-data/              11 张 canonical 表 + 6 张 rt_list 抽查件（blocks 447 / turrets 26 / bullets 137 / units 70 /
│                         items 22 / liquids 11 / status 23 / rules 118 / formulas 19 …）
├── 01-execution/  E01-E06   执行模型、预算、语义陷阱 30 条、时间精度、链接与 @ 常量、跨版本
├── 02-world/      W01-W12   方块锚点、配方、电力、液体、热、物流、钻探、载荷、地形、存储、配置、沙盒
├── 03-combat/     C01-C10   伤害管线、炮塔、弹道、状态、护甲、单位武器、支援、波次、防御、跨层数值
├── 04-units/      U01-U05   移动、生产、AI、能力、进阶（两版均无经验/等级系统）
├── 05-campaign/   CAMP.*    波次、难度、生成、胜负、星区、Rules 全字段
├── 06-mlog/       M01-M08   + instructions.json（73 条指令）+ enums.json（13 组枚举）
├── 07-patterns/   P01-P06   + idioms.json（30 惯用法）+ anti-patterns.md（AP-01..20）
├── 08-evidence/   claims.jsonl(85) / CHEAT.md / probes/(20) / bench/(300+24 题)
└── tools/         抽取（jar 反射/源码）、门禁、索引、检索、评测、发布
```

## 质量门禁

```powershell
python knowledge\tools\check_kb.py --root knowledge --all     # 55 篇 0 error（warning 为提示级）
python knowledge\tools\build_index.py --root knowledge         # 生成 index.json
python knowledge\tools\build_index.py --root knowledge --check # 校验索引与内容一致
```

- 门禁规则：id 唯一且符合 `^(EXEC|WORLD|COMBAT|UNIT|CAMP|MLOG|PATTERN|DATA|EV)\.[A-Z][A-Z0-9_]*\.\d{3}$`、七节齐全、`data` 只能引 `00-data/` 存在的文件、数字与数据表冲突即 error、≤250 行。
- 下划线目录/文件（`_report/`、`_probe*`）不进索引、不进门禁、不同步仓库 —— 工作产物请放 `_report/`。

## 重建与发布（MCP 正式库）

```powershell
$R="F:\OneDrive\桌面\AtomicStates"; $W="F:\OneDrive\文档\deepseek-harness\default-workspace"
$env:KB_ROOT=$R; $env:KB_KNOWLEDGE="$R\knowledge"; $env:KB_DIR="$W\out\kb_build"
python "$R\knowledge\tools\kb.py" build                       # 8285 chunk / 142 files
python "$R\knowledge\tools\publish_db.py" "$W\out\kb_build\kb.sqlite3" "$R\out\_kb\kb.sqlite3"
python "$R\knowledge\tools\postpublish.py" --db "$R\out\_kb\kb.sqlite3" --staging "$W\out\kb_build\kb.sqlite3"
```

细节（含 4 个必踩的坑、检索三开关、发布后固定校验顺序）见 [`tools/REBUILD.md`](tools/REBUILD.md)。

## 数据出处

数值全部来自 **v160.7 真服务器 jar 反射**（`tools/extract_rt.py`，起服 2–4 s），语义来自 **v159.3 源码树**（`Mindustry-Source/core/src`），两者冲突一律并列写进文章并以后者解释机制、前者给数值，例如 toxopid 护甲 22（jar）/ 13（源码）。

## 不包含什么

- 不含模组、插件、工具产品的开发文档（`MlogAuxiliary/`、`tools/` 下的工具源码本身不是知识条目）。
- 不含蓝图内容本身（只讲蓝图逻辑与 mlog 的写法与机制）；要成品蓝图看 `BLUEPRINT-ANALYSIS.md`（见 `INTEGRATION.md`）。
- 未验证结论一律 `conf: U` 并标注缺哪一步验证，不当事实用。
