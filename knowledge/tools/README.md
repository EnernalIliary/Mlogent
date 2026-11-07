# knowledge/tools — 生成器 / 门禁 / 检索重建

三条命令覆盖日常维护。所有脚本只依赖标准库（kb.py 额外需要 out/_kblibs* + out/_kbmodels），无网络需求。

## 1. 生成总目录 knowledge/index.json

    python knowledge/tools/build_index.py
    python knowledge/tools/build_index.py --root <知识库根> --out <目标路径>    # 试跑/镜像
    python knowledge/tools/build_index.py --check                                 # 只比对（CI）

产物结构（AI 首读文件，字段只增不改）:

    version / generated / root / read_order
    domains[]  {id, code, title, desc, articles[{id,path,title,tokens,conf,ver,status,lines}]}
    data[]     {path, kind(canonical|raw), records, bytes, keys[]}   # 00-data/*.json
    evidence[] {path, kind, bytes, lines|entries}       # 08-evidence/{claims,probes,bench}
    evidence_dirs[] {path, kind, files, bytes}          # 子目录汇总（probes 空目录也出现）
    docs[]     {path, bytes, tokens}                    # KB.md / CONVENTIONS.md / VERSION.md
    counts     {articles, by_domain, data_tables, data_records, data_raw_tables,
                evidence_files, evidence_by_kind, evidence_dirs, tokens_total, empty}
    字段语义见 INDEX_CONTRACT.md（改字段必须先改该文件）。

`--check` 剔除 `generated` 时间戳后比对，不一致退出码 1。空库也能生成（counts.empty=true，退出 0）。

## 2. 静态门禁 check_kb.py

    python knowledge/tools/check_kb.py                   # 人读报告
    python knowledge/tools/check_kb.py --json            # 机器可读（CI 落盘）
    python knowledge/tools/check_kb.py --write-tokens     # 回填 frontmatter tokens
    python knowledge/tools/check_kb.py --root <知识库根> --all
    python knowledge/tools/check_kb.py --strict          # 强制把缺表升级为 error（CI 全量阶段用）

退出码: 0 = 无 error（warning 不阻塞）；1 = 有 error；2 = 根目录不存在。

检查项与错误码

| # | 规则 | error 码 | warning 码 |
|---|---|---|---|
| 1 | 8 个必填字段 id/title/domain/status/ver/conf/src/data | E_MISSING_FIELD | — |
| 1 | id 形如 域.子域.三位数，域码固定 8 个 | E_ID_FORMAT | — |
| 1 | id 全库唯一 | E_ID_DUP | — |
| 1 | status ∈ active/draft/deprecated，conf ∈ S/E/I/U | E_STATUS / E_CONF | — |
| 1 | domain 用短名 {exec,world,combat,unit,camp,mlog,pattern,evidence,data}，并与所在目录一一对应 | E_DOMAIN / E_DOMAIN_DIR | — |
| 2 | 七段模板小节齐全 | E_SECTION_MISSING | — |
| 3 | frontmatter data: 引用的 00-data 文件存在（支持 表.json#键 与 表.json#id=xxx）。**升级规则**：00-data 下出现 canonical 表（blocks/turrets/units/items/liquids/bullets/status/rules.json 且 records 非空）→ 缺表即 E_DATA_FILE（视为路径写错）；数据层未落地或 --strict 时分别按 W / E 处理。rt_* 抽查文件不触发落地判定 | E_DATA_FILE（数据层已落地 或 --strict） | W_DATA_FILE_MISSING / W_DATA_FRAGMENT / W_DATA_JSON |
| 4 | 数字声明行带来源标记（[src: / [实测 / [ver / 见 DATA 等）；紧邻上文有标记的表格/多行块整块豁免；表头含「来源/源/src」列的表整表豁免 | — | W_NUM_NO_SOURCE（每篇前 5 条逐行，余下汇总） |
| 4 | 文章里「实体名 + 血量/尺寸/射程」的数字与 00-data/blocks.json、turrets.json 冲突 | E_NUM_CONFLICT | — |
| 5 | ver 为列表且取值合法 | E_VER_VALUE | W_VER_SINGLE / W_VER_MANY |
| 6 | 相对链接可达 | E_LINK_DEAD | — |
| 6 | 相关 小节引用的 ID 存在 | — | W_REF_UNKNOWN |
| — | 文章 ≤ 250 行 | E_TOO_LONG | — |
| — | 每篇至少一个反例（实测与反例 / 常见误解 有实质内容） | — | W_NO_COUNTEREXAMPLE |
| — | tokens 与当前正文偏差 >20% | — | W_TOKENS_STALE / W_TOKENS_MISSING |
| — | 00-data 表条目含 id/src/ver、README 存在 | — | W_DATA_RECORD / W_DATA_README |
| — | src 条目形如 路径:行号 或 jar: | — | W_SRC_FORMAT |
| — | 标题重复 | — | W_TITLE_DUP |
| — | 域目录存在且有文章 | — | W_DOMAIN_DIR_MISSING / W_DOMAIN_EMPTY |

门禁只扫 01..08 域目录下的 *.md；根目录契约文档（KB.md / CONVENTIONS.md / VERSION.md / README.md）不参与。
数字检查会跳过围栏代码块内的行（mlog 示例里的数字不算声明）。

## 3. 重建检索库 kb.sqlite3

    python tools/kb.py build       # 需要 out/_kblibs311(py<3.12) 或 out/_kblibs，加 out/_kbmodels
    python tools/kb.py stats
    python tools/kb.py search "传送带 items/s" -k 6
    python tools/kb.py serve       # MCP(stdio)，暴露 kb_search

语料 = 原固定文档清单（README、Logic/、mindustry-blueprint/、断言表/验证记录 等）
+ docs/游戏速查/*.md + tools/*.py + tests/run_tests.py
**+ knowledge/ 全库**：knowledge/**/*.md 文章、knowledge/00-data/*.json 的条目摘要、KB.md/CONVENTIONS.md/VERSION.md。

### 接线（重要）

仓库里的 tools/kb.py 必须换成 knowledge 感知版（本目录 kb.py 即该版本，kb.diff 是与旧版的完整 diff）:

    copy knowledge\tools\kb.py   tools\kb.py
    copy knowledge\tools\kb.diff （留档，可选）

再重建 DB（build 会先删旧库，**重建前必须备份** out/_kb/kb.sqlite3 → kb.sqlite3.bak）:

    copy out\_kb\kb.sqlite3 out\_kb\kb.sqlite3.bak
    python tools\kb.py build
    python tools\kb.py stats          # chunks / files / data_tables

MCP 侧（mcp__kb__kb_search）由 profile 的 mcp 配置启动 python tools/kb.py serve；每次检索现开 sqlite 连接，
**重建 DB 后不用重启服务**，只要进程用的是同一个 out/_kb/kb.sqlite3。

### 环境变量

| 变量 | 默认 | 用途 |
|---|---|---|
| KB_ROOT | 脚本上级目录 | 仓库根（决定 DOC_FILES/CODE_GLOBS/路径前缀），用于在仓库外试跑 |
| KB_KNOWLEDGE | <KB_ROOT>/knowledge | knowledge 根（文章 + 00-data） |
| KB_DIR | <KB_ROOT>/out/_kb | sqlite 输出目录 |
| KB_LIBS | out/_kblibs311（py<3.12 时）否则 out/_kblibs | fastembed/numpy 目录 |
| KB_MODELS | out/_kbmodels | bge-small-zh-v1.5 / bge-reranker-base 权重缓存 |

相对旧版的改动: DOC_FILES 追加 3 个契约文档；新增 _knowledge_files()（递归 knowledge/**/*.md，排除 tools/ 与 00-data/）、
_data_summaries()（00-data 每条记录压成一行，kind=data 入库）、_rel()（路径统一为仓库相对路径）；
--kind 增加 data；stats 增加 data_tables；新增 KB_ROOT/KB_KNOWLEDGE 环境变量（默认行为与旧版一致）。
embedding、RRF 融合、MCP 协议逻辑未改。

## 4. 数字审计（文章 vs 00-data）

    python knowledge/tools/num_audit.py --root <知识库根> [--out 报告.md] [--json]
    python knowledge/tools/check_kb.py --audit --audit-out <报告.md>   # 门禁后附带跑一次

只读、不改文章，输出逐条「文件:行｜字段｜文章值｜表值｜偏差｜判定｜建议」。
判定：A_MATCH（±0.51 或 ±2% 内）/ A_MISMATCH / A_SUSPECT（reload 类 60 倍差）。
覆盖 blocks+turrets+units 的 health/size/armor/range/reload/speed/itemCapacity；字段缺就跳过。
按 (blocks+turrets) 联合查：turret 的 range/reload 只在 turrets.json。
五类假阳性已过滤：实体名词边界（避免 production→duct）、数字必须紧跟标签且在实体后、组件字段前缀（`SuppressionField range 200`）、子弹速度（「弹 speed」）、**声明值 vs 结果值**（`container 声明 scaledHealth 55 ⇒ 220`）与**源码锚点引用**（`world/Block.java:75 public int itemCapacity = 10;`）。当前 51 篇：24 行命中，A_MATCH=24 / A_MISMATCH=0。

## 5. 发布正式库（MCP 正在用，不能原地 build）

见 REBUILD.md：staging build → publish_db.py（sqlite backup，不 unlink）→ dbstat/check_kb/index --check 校验。

## 6. 检索冒烟

    python knowledge/tools/bench20.py --db <kb.sqlite3> --out _report/bench20.md   # 固定 20 题，见下
    python knowledge/tools/postpublish.py --db <正式库> --staging <staging库>         # 发布后一条命令校验
    python knowledge/tools/smoke_kb.py --questions q.jsonl --out _report/smoke.md [--k 6] [--db <kb.sqlite3>]
    # 题干行格式: {"q":"护甲减伤公式","expect":["C05"]}  或纯文本一行一题
输出 top1/top3/topk 命中率、单题 p50/p90 延迟（模型只预热一次）、未命中明细；命中按**不同文件**去重后算。

## 3b. 数字来源 warning 的处置口径（2026-11-08 定稿）

- **W_NUM_NO_SOURCE 是提示级，不阻塞发布**：按 CONVENTIONS 规则 1 由作者自证，门禁 exit 0 即通过，收尾/发版报告里注明"存在提示级 warning"即可。
- 真实规模比报告大：报告 120 条是"每篇前 5 条 + 另有 N 行"折叠后的数字，展开≈**382 行**，逐行全量口径（跳表格/代码块）**1024 行**；大头是源码行号与举例数值，**不要按行补 [src:]**。
- 要降噪就补「## 数值」「## 规则 / 公式」两节（≈46 行）+ 给表格表头加「来源」列（check_kb 对含来源列的表整表豁免）。

**加权证据（20 题确定性样本，题库冻结）**：knowledge/ 文章 ×1.25、tools//tests/ ×0.8（kb.py 查询期生效，环境变量 KB_KNOWLEDGE_BOOST / KB_CODE_PENALTY 可关）后，A 锚点 top1 **9/20 → 14/20（45% → 70%）**、top3 12→15、**top1 落在 knowledge/ 之外 10/20 → 1/20**，p50 不变（~230ms）。这是"文章翻倍 + 路径加权"两组变量的合计收益，已作为发布基线固化在 kb.py 里。

## 常见坑

- build_index.py --check 若报"已过期"先看差异：通常是真的有新文章；时间戳已剔除，不会因重跑误报。
- 空库（还没文章）时门禁退出码 0，只有 W_DOMAIN_EMPTY / W_DATA_README 之类 warning——这是设计行为，不是漏检。
- 文章 domain: 用短名（world），且必须与所在目录对应（02-world → world），否则 E_DOMAIN / E_DOMAIN_DIR。
- 半成品库阶段不要开 --strict：00-data 未生成时 data 引用会缺文件，默认只降级为 W_DATA_FILE_MISSING；canonical 表一旦落地，缺表自动变 E_DATA_FILE。
- 所有 JSON / md 读取用 encoding="utf-8-sig"：PowerShell 5.1 的 Set-Content -Encoding UTF8 会写 BOM，直接 utf-8 解析会报 "Unexpected UTF-8 BOM"。
- E_NUM_CONFLICT 是粗查：只覆盖 blocks/turrets 的 health/size/range，且要求实体名与标签同在一行、相距 <40 字符；散文里的数字不判。
- 写完文章跑一次 --write-tokens，否则 W_TOKENS_MISSING；tokens 是估算值（汉字 0.62 + 英文词 0.75），不是 tokenizer 真值。
- 路径含中文时不要用命令行参数传中文目录给 python（控制台 GBK 会 can't open file），改用 --root 的 ASCII 路径或直接 cd。
- W_NUM_NO_SOURCE 每篇只报 5 条 + 1 条汇总，**真实条数远大于报告条数**：实测 37 篇报 120 条，展开「另有 N 行」后为 382 行；逐行全量口径（跳过表格/代码块）为 1024 行。判断"要不要统一补来源"请看 _report/warn_policy_advice.md，不要按 120 估工时。
- 文章里引用组件参数（`navanax（SuppressionField range 200）`）不是单位属性，num_audit 已过滤；门禁的 E_NUM_CONFLICT 不做这层过滤，误报时看是否命中该类写法。
