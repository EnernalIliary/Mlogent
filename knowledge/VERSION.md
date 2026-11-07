# 版本与真源（VERSION）

## 双版本并列

| 代号 | 含义 | 位置 | 权威性 |
|---|---|---|---|
| v160.7_rt | 当前线上版本（jar 反射 + 真机） | out/_server160.jar、MBO/gamedata/v160.7/ | **数值权威** |
| v159.3_src | 源码树（HEAD 5811844…，tag v159.3） | Mindustry-Source/core/src/mindustry | **语义权威** |

源码落后一个次版本：源码里没有 v160.x 新增内容。凡涉及"当前版本是否仍如此"，以 v160.7 为准；凡涉及"算法怎么写的"，以源码为准；两者冲突必须在文中显式说明。

## 数值真源优先级（冲突时按此裁决）

1. v160.7 jar 反射（运行时真实值）
2. v159.3 源码（公式/字段语义/边界）
3. 真机实测（MBO/ratio-calc，带实验条件）
4. 自写手册/笔记（只作线索，必须回源）
5. 其它副本（不入库）

## 已知错误（不得继承）

- 旧 data/game/*.json 的 craftTime **447 条全为 -1** → 弃用该字段。
- docs/游戏速查/方块配方.md 的"耗电"列是**每 tick**，标签却写 /s → 差 60 倍。
- 蓝图逻辑模式库.md / 蓝图层逐类精讲.md 与 mindustry-blueprint 下两份是近重复副本，以 skill 目录版为准。
- instr_semantics.json 存在 3 个尺寸版本，以仓库 tools/ 版（56.5KB）为准；instr_enums.json（v160.7）作枚举补充。
- **单位数值以 jar 为准**：toxopid 护甲 jar=22 / v159.3 源码=13；reign armor jar=30 / 源码=18；dagger 主武器 jar=2 挂点×reload 26（DPS 41.5）/ 源码单挂点 reload 13（DPS 83.1）。文章主值一律 jar，源码差异写在版本注里。
- **连续伤害不是 estimateDPS**：meltdown 实战 DPS = damage/5×60 = **936**；旧稿 4680 是 BulletType.estimateDPS 的假设值，Turret 面板 3120 是重复除 reload 的产物。
- **MBO/gamedata 的 BeamDrill baseRate 与真实值差 2 倍**；drillTime 也不等于 getDrillTime（后者加 50×hardness）。
- **radar 缓存是 30 tick**（旧笔记写 40）；`uradar` 第 5 参数（order）是死槽。
- **ConditionOp 是 8 个**（旧题库写 7 只在排除 always 的口径成立）；`strictEqual` 不是恒 false。
- **memory 容量不是 32**：memory-cell **64**、memory-bank/world-cell **512**（32 只是 `MemoryBlock.java:12` 的类默认值，三个实例全部覆盖；v159.3 与 v160.7 一致）。
- **记忆格越界读是 null（NaN），不是 0**；越界写静默丢弃（`MemoryBlock.java:64-81` 注释原文 `Return null when out of bounds. (instead of 0)`）。
- **`format` 一次只吃 1 个值**，填「已在文本缓冲里」的**最低编号**占位符，必须先 `print` 再 `format`；占位符只认单数字 0-9（`{10}` 不替换）。
- **ipt 的单位是「点/tick」不是点/s**：micro 2 / logic 8 / hyper 25 ⇒ 120/480/1500 点/s；单 tick 上限是 `min(5×ipt, maxInstructionsPerTick)`，hyper 的 125 被截到 **40**。
- **单位护甲表不能混口径**：spiroct jar=9 / 源码=5、arkyid 14/6、toxopid 22/13、eclipse 22/13、antumbra 17/9、scepter 20/10、reign 30/18 —— U05/C05 已统一取 jar 并加版本注。
- **炮塔 coolantMultiplier 没有 0**：最小 foreshadow **0.4**、spectre **0.5**、arc **30**（跨度 75 倍），旧表写 0 是错的。

## 环境坑（重建/复现前必读）

1. `out/_kb/kb.sqlite3` 在 OneDrive 下是 Pinned 只读：MCP 持句柄时 `unlink` 会 WinError 5 并把库清成 24KB 空库 → 必须用 `tools/publish_db.py`（sqlite3 backup 原地重写）。
2. 重建时 `KB_ROOT` 必须是**仓库根**（`F:/OneDrive/桌面/AtomicStates`），`KB_DIR` 指向临时目录；`KB_ROOT` 若设成 `knowledge` 会去找 `knowledge/out/_kblibs` → `ModuleNotFoundError: fastembed`。
3. `tools/mlogsim.py` 的 `tempfile.mkdtemp(dir=<repo>/out/_sim)` 在 OneDrive 同步目录下可能卡死数分钟（爬到 `tempfile.py:375` 不动）；设环境变量 `MLOG_SIM_BASEDIR` 指向本地非同步目录即可绕过（已支持）。
4. 门禁 `check_kb.py` 的 warning 是提示级（exit 0 即合规）；`W_NUM_NO_SOURCE` 多为源码行号与举例数值，不必逐行补来源。

## 2026-11-08 整合重建（两处外部会话并入）

同一工作区的两个会话把各自的平行知识库并进来，本库据此做了一轮整理（内容源头已随仓库提交 8494ea4 / 5c2f933 / a5cf501 / 805fb4d）：

- **退场两份平行库**：`docs/本地知识库.md`（检索器说明）与 `docs/MBO与配比计算器.md`（配比文档）。机制/数值并入 `02-world/W02/W03/W06/W07` + `04-units/U02`，检索用法归 `tools/README.md`/`tools/REBUILD.md`，工程细节归 `ratio-calc/README.md`；映射见 `INTEGRATION.md` 第 45-46 行。
- **新增配比推导**：`04-units/U02-production.md` 第 128-156 行「台数比例与整链瓶颈」——每台每秒 = 60/constructTime、台数按速率反比、整链产出取最慢段；含 1/1/1/2/5 实例与「按 1:1 配 T4/T5」反例。
- **传送带吞吐统一口径**：v160.7 jar `speed=0.035`、`itemSpace=0.4` ⇒ **5.25 件/s**（UI 的 `displayedSpeed=5` 是手填近似）；v159.3 源码 `0.046` ⇒ 6.9 件/s 作为版本注保留。此前 6.9 被误当当前值，`00-data/formulas.json`、`CHEAT.md`、`W06` 表格已一致。
- **整理动作**：修 `P01-architecture.md` 里指向不存在的 `EXEC.PROCESSOR.001` → `EXEC.MODEL.001`；`W06` 吞吐表 conveyor 行补全口径；删掉过期的 `knowledge/index.repo.json`（04:18 的旧目录副本，移到 `_report/attic/`）。
- **重建结果**：index.json 57 篇 / 18 张表；正式库 **8,243 chunk / 140 files**（42.8MB，code 6322 / doc 1758 / data 163）；postpublish 三项 PASS（A@1 16/20、库外 top1 0）；300 题 **hit@1 59.7% / hit@6 86.3% / mrr 0.694 / strong@6 94.2%**（逐域与上一版一致，41 题未命中）。

## 2026-11-08 第二轮：炮塔评价 + 中英名对照（外部提交 49fac39 / 42aa158）

- **新增 `03-combat/C11-turret-verdict.md`**（`COMBAT.TURRET.002`，conf I）：13 门主力的 DPS/造价、按目标护甲选型、7 门不能打空的防空缺口。表 1/表 2 的 DPS(0甲) 与 A* 逐格等于 C10 表 3/表 4；造价=件数之和、耗电=`usagePerSecond`、射程=`range/8` 已逐条复算通过；`targetAir=false` 恰为 arc / hail / lancer / ripple / scathe / scorch / titan（31 条 turrets 记录里非战斗 3 条：build-tower / repair-point / repair-turret）。
- **新增中英名对照 5 篇**：`02-world/W13-W15-name-blocks-*.md` 合计 **447 条 = `00-data/blocks.json` 全量**（136 + 168 + 143，无重无漏）；`W16-name-items.md`（22 物品 + 11 液体 + 23 状态 = 56）；`04-units/U06-name-units.md`（70 单位，60 有官方简中）。
- **名称真源**：`assetsraw/assets/bundles/bundle.properties` + `bundle_zh_CN.properties`（2867 个 key）——`out/_server160.jar` 里没有任何 bundle 条目（服务端 jar 剥掉资源），所以名称只能取 assetsraw；生成器 `tools/gen_name_docs.py`（key 规则 `<kind>.<id>.name`）。缺名的 36 方块 / 10 单位 / 3 状态全是内部占位（air、build1-7、`*-missile`、dummy、turret-unit-build-tower…）。
- **交叉链接**：C02/C10 → `[[COMBAT.TURRET.002]]`；W01 → `[[WORLD.NAMES.001]]`-003；U01 → `[[UNIT.NAMES.001]]`；`08-evidence/CHEAT.md` 路由表下补一行「查中文名走哪」。
- **重建结果**：门禁 **61 篇 / 0 error / 193 warning**；正式库 **8,317 chunk / 146 files**（43.6MB，doc 1831 / code 6322 / data 163）；postpublish 三项 PASS（A@1 16/20、库外 top1 0、p50 68.3ms）；300 题 **hit@1 59.7% / hit@6 86.3% / mrr 0.693 / strong@6 94.2%**（新增内容未抢金标，分数与上一版持平）。

## 交付验收（v1.1，2026-11-08）

| 项 | 结果 | 复现命令 |
|---|---|---|
| 门禁 | **61 篇 / 0 error**（193 warning，全部提示级） | `check_kb.py --root knowledge --all` |
| 正式库 | **8,317 chunk / 146 files / 18 张数据表**（43.6MB，doc 1831 / code 6322 / data 163） | `dbstat.py out/_kb/kb.sqlite3` |
| 发布后校验 | STRUCT / COUNT / RETRIEVAL **三项 PASS**（chunks 8317 = staging 8317、files 146，journal 已落盘） | `postpublish.py --db ... --staging ...` |
| 300 题冻结评测 | coverage 100% / **hit@1 59.7% / hit@6 86.3%** / mrr 0.6932 / strong@6 94.2% / 库外槽 0%（v1.1 复跑，与 FINAL3 持平） | `08-evidence/bench/`（A+B+C 全开，k=6） |
| 推导题 | 公式 22 题 **72.7%**（16/22）、跨源 24 题 **95.8%**（23/24） | 同上 |
| 20 题冒烟（bench20） | A@1 **16/20（80%）**、A@3 16、库外 top1 **0/20**、p50 68.3ms（旧版 4/20、库外 12/20） | `bench20.py --db out/_kb/kb.sqlite3` |
| 可执行探针 | **17 PASS / 1 FAIL（已修claims）/ 2 INCONCLUSIVE** | `08-evidence/probes/_run_all.py` |
| jar 真值核对 | **终版 RERUN：178 条 / PASS 175 / FAIL 0 / 口径差 3**（①CHEAT 26 · ②C10 14 · ③W06/W07 41 · ④C02 28(3 口径差) · ⑤C05 41 · ⑥C06 28），退出码 0 | `python knowledge/tools/rt_verify.py`；明细 `08-evidence/_report/_rtverify/RERUN.md` |

检索三开关（默认全开，可用环境变量关）见 `tools/REBUILD.md` §4：`KB_ONLY_KNOWLEDGE`（只检索 knowledge/）、`KB_DEDUPE_FILE`（按文件去重）、`KB_ASCII_BOOST`（ASCII 标识符加权）。

## 当前内容规模（v1.1）

| 域 | 篇数 | 目录 |
|---|---|---|
| 执行模型 | 6 | `01-execution/`（E01-E06） |
| 世界/方块 | 16 | `02-world/`（W01-W16，含 W13-W16 中英名对照） |
| 战斗 | 11 | `03-combat/`（C01-C11，含 C11 炮塔评价） |
| 单位 | 6 | `04-units/`（U01-U06，含 U06 单位名对照） |
| 战役 | 6 | `05-campaign/`（CAMP.*） |
| mlog 语言 | 8 + 2 JSON | `06-mlog/`（M01-M08、instructions.json、enums.json） |
| 蓝图模式 | 6 + JSON | `07-patterns/`（P01-P06、idioms.json） |
| 证据/评测 | 2 + 300 题 + 探针 | `08-evidence/`（claims.jsonl、CHEAT.md、bench/、probes/） |
| 数据表 | 11 张 canonical（+6 张 rt_list 抽查件） | `00-data/`（blocks/turrets/units/bullets/items/liquids/status/rules/formulas/constants/src_anchors） |
