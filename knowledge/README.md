# Mindustry mechanics knowledge base (knowledge/)

A Mindustry vanilla-mechanics knowledge base that an AI can use directly and a human can read: **92 articles + 12 canonical data tables (plus 6 rt_list spot-check files) + 85 re-testable assertions + 20 executable probes + 300 evaluation questions**, covering both v160.7 (numbers) and v159.3 (source semantics), and already built into a searchable production database (9,397 chunk).

**Measured metrics** (retrieval A+B+C all on, k=6, frozen 300-question set): hit@1 **59.0%**, hit@6 **85.0%**, mrr 0.685, out-of-library slots **0%**; the 20-question smoke run gives A@1 **16/20** (previous version 4/20).

## Where to start

| If you are | Start with |
|---|---|
| A human who wants a quick overview | [`KB.md`](KB.md) → [`08-evidence/CHEAT.md`](08-evidence/CHEAT.md) (40 pitfalls + 30 numbers + 20 retrieval routes) |
| An AI/agent that needs to plug in | [`AI-SETUP.md`](AI-SETUP.md) (three integration modes + system prompts you can paste as-is) |
| Looking up one number | the JSON in [`00-data/`](00-data/) (with id and src) |
| Wondering whether the old knowledge bases still count | [`INTEGRATION.md`](INTEGRATION.md) (item-by-item mapping: what supersedes what, and when you do have to go back to the old files) |
| Changing or extending this base | [`CONVENTIONS.md`](CONVENTIONS.md) (writing contract) + [`tools/REBUILD.md`](tools/REBUILD.md) (rebuild and publish flow) |
| An English reader / an English-only model | [`INDEX.en.md`](INDEX.en.md) (English title and one line per article) → [`GLOSSARY.md`](GLOSSARY.md) (Chinese / English / legacy / colloquial mapping, 504 entity names) |
| Seeing a Chinese name and not knowing its id | the three-layer name tables in [`GLOSSARY.md`](GLOSSARY.md), or `python tools/kb_grep.py search "<词>"` |

## Layout

```text
knowledge/
├── KB.md                 入口：30 秒上手 / AI 使用协议 / 12 能力域 / 陷阱 Top 14
├── AI-SETUP.md           把库交给 AI 的三种方式 + 系统提示词
├── INTEGRATION.md        旧知识库整合映射（停更/取代/仍独有）
├── CONVENTIONS.md        写作契约（frontmatter / 七节 / 数值来源 / 版本口径）
├── VERSION.md            双版本真源优先级 + 已知错误清单 + 交付验收 + 环境坑
├── 00-data/              12 张 canonical 表 + 6 张 rt_list 抽查件（blocks 447 / turrets 31 / bullets 137 / units 70 / turret_shots 28 /
│                         items 22 / liquids 11 / status 23 / rules 118 / formulas 19 …）
├── 01-execution/  E01-E06   执行模型、预算、语义陷阱 30 条、时间精度、链接与 @ 常量、跨版本
├── 02-world/      W01-W16   方块锚点、配方、电力、液体、热、物流、钻探、载荷、地形、存储、配置、沙盒、名对照×4
├── 03-combat/     C01-C11   伤害管线、炮塔、弹道、状态、护甲、单位武器、支援、波次、防御、跨层数值、炮塔评价
│       └── turrets/  T101-T210  28 篇逐台炮塔页（_turrets/ 为评价文案源数据）
├── 04-units/      U01-U06   移动、生产、AI、能力、进阶（两版均无经验/等级系统）、单位名对照
├── 05-campaign/   CAMP.*    波次、难度、生成、胜负、星区、Rules 全字段
├── 06-mlog/       M01-M08   + instructions.json（73 条指令）+ enums.json（13 组枚举）
├── 07-patterns/   P01-P09   + code/（六份成品 .mlog）+ idioms.json（30 惯用法）+ anti-patterns.md（AP-01..20）
├── 08-evidence/   claims.jsonl(85) / CHEAT.md / probes/(20) / bench/(300+24 题)
└── tools/         抽取（jar 反射/源码）、门禁、索引、检索、评测、发布
```

## Quality gates

```powershell
python knowledge\tools\check_kb.py --root knowledge --all     # 92 篇 0 error（warning 为提示级）
python knowledge\tools\build_index.py --root knowledge         # 生成 index.json
python knowledge\tools\build_index.py --root knowledge --check # 校验索引与内容一致
```

- Gate rules: ids are unique and match `^(EXEC|WORLD|COMBAT|UNIT|CAMP|MLOG|PATTERN|DATA|EV)\.[A-Z][A-Z0-9_]*\.\d{3}$`, all seven sections are present, `data` may only reference files that exist under `00-data/`, a number that conflicts with a data table is an error, and ≤250 lines.
- Directories and files with a leading underscore (`_report/`, `_probe*`) are not indexed, not gated and not synced to the repo — put work products in `_report/`.

## Rebuild and publish (production MCP database)

```powershell
$R="<仓库根>"; $W="<临时暂存目录>"   # $R 为本机仓库绝对路径；$W 为任意本地目录，脚本按参数/环境变量取
$env:KB_ROOT=$R; $env:KB_KNOWLEDGE="$R\knowledge"; $env:KB_DIR="$W\out\kb_build"
python "$R\knowledge\tools\kb.py" build                       # ≈9,460 chunk / 187 files
python "$R\knowledge\tools\publish_db.py" "$W\out\kb_build\kb.sqlite3" "$R\out\_kb\kb.sqlite3"
python "$R\knowledge\tools\postpublish.py" --db "$R\out\_kb\kb.sqlite3" --staging "$W\out\kb_build\kb.sqlite3"
```

Details (the 4 traps you are bound to hit, the three retrieval switches, and the fixed post-publish check order) are in [`tools/REBUILD.md`](tools/REBUILD.md).

## Where the data comes from

Every number comes from **jar reflection against the real v160.7 server** (`tools/extract_rt.py`, server startup 2–4 s); semantics come from the **v159.3 source tree** (`Mindustry-Source/core/src`). Where the two disagree, both are written into the article side by side: the source explains the mechanism, the jar supplies the number — for example toxopid armor 22 (jar) / 13 (source).

## What this does not cover

- No development docs for mods, plugins or tool products (the tool sources under `MlogAuxiliary/` and `tools/` are not knowledge entries themselves).
- No blueprint content itself (only blueprint logic and how mlog is written and how the mechanics behave); for finished blueprints see `BLUEPRINT-ANALYSIS.md` (see `INTEGRATION.md`).
- An unverified conclusion is always `conf: U` and says which verification step is missing; it is never used as fact.
