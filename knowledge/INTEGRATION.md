---
id: INTEGRATION.001
title: 旧知识库整合映射（谁被谁取代）
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src: 本仓库调研报告《Mindustry机制知识库-构建计划.md》§1.1 资产地图
data: []
depends: []
tags: [integration, legacy, migration]
tokens: 0
---

# 旧知识库整合映射

> 这份文件回答一个问题：**AtomicStates 里原来那些零散知识库，现在还算不算数、该什么时候去翻。**
> 三句话版：**机制问题一律以本知识库（knowledge/）为准**；旧资产只当"原始出处"和"独有证据"用；旧资产之间的近重复副本一律不再维护。

## 1. 三类旧资产的处理原则

| 类别 | 处置 | 理由 |
|---|---|---|
| **已被原样吸收**（内容搬进文章，数值经 jar 复核） | 不再作为回答依据，只在需要追溯"这条结论最初从哪来"时引用 | 两份真源 = 迟早分叉；本库已带 `src:` 锚点可回溯 |
| **部分吸收**（吸收机制结论，未吸收全部实测/配比细节） | 先查本库；本库明确没写的数字再去旧库查，并标明"来自旧实测，未复核" | 实测值有环境依赖，不能与字段值混排 |
| **未吸收**（大体量语料、外部工具） | 仍按原方式使用，本库**不**复制 | 1222MB 语料做检索会淹没有效内容 |

## 2. 逐项映射

| 旧资产 | 位置 | 体量 | 状态 | 新库对应 | 备注 |
|---|---|---|---|---|---|
| 权威源码 v159.3 | `Mindustry-Source/core` | 807 .java / 5.9MB | **保留为语义真源** | 全库 `src:` 的 `core/...:行号` 均指它 | 只有 core 模块；数值一律以 v160.7 jar 覆盖 |
| 运行时 dump v160.7 | `MBO/gamedata/v160.7/gamedata.json` | 3.0MB | **已提炼** | `00-data/*.json`（blocks/turrets/units/items/liquids/bullets/status/rules，447/26/70/22/11/137/23/118 条） | 原始 raw 参数（consumers[]）仍是查"某方块耗电/耗液细节"的最后一站 |
| 薄投影 | `data/game/*.json` | 149KB+ | **作废**（9 字段、craftTime 全 -1、炮塔无射程/伤害） | `00-data/` | 别再引用，会答错 60 倍耗电 |
| 指令语义表 | `tools/instr_semantics.json` | 56.5KB | **已被取代**（口径是 LStatement 类=53 条） | `06-mlog/instructions.json`（73 条）+ `enums.json`（13 组） | 旧表只保留 arity/defs/uses 的考古价值；且已发现三处尺寸分叉（56.5/62.8/50.6KB） |
| 枚举表 | `tools/instr_enums.json` | — | **已取代** | `06-mlog/enums.json` | 新增 RadarTarget/LLocate/LAccess 全量 |
| 语言手册 | `Logic-Docs-v1.1.0.md` | 546KB / 1.22 万行 | **部分吸收** | `06-mlog/M01-M08` | 手册机制段仅 15-20%，其余是逐指令抄录；本库 73 条指令表已覆盖，但"某指令的冷门参数组合"仍可能只在那里 |
| 经验笔记 | `mlog工作笔记.md` | 227KB / 12 章 | **部分吸收**（铁律→陷阱/反模式） | `01-execution/E02`、`08-evidence/CHEAT.md`、`07-patterns/anti-patterns.md` | 笔记里"已推翻的旧结论"未逐条搬入，遇到自相矛盾以本库为准 |
| 断言库 | `docs/断言表.md` | 202 条 | **已分层**：真机制 102 条 → claims.jsonl(85) + probes(20)；工具开发 82 条 **丢弃** | `08-evidence/claims.jsonl`、`probes/` | 原表 41% 是 jobqueue/undo/面板宽度这类产品断言，不属机制知识 |
| 验证记录 | `docs/验证记录.md` | 91KB / 120 条 | **部分吸收**（59.4% 覆盖区） | `08-evidence/probes/` 20 条可执行探针 + `claims.jsonl` 的 verdict | 本库改成"可重跑脚本 + 快照输出"，比纯文字记录可复验 |
| 模式库 | `PATTERNS.md`（根级 `蓝图逻辑模式库.md` 已于 2026-11-15 删除） | 107KB / 2471 行 | **已重构** | `07-patterns/P01-P09`（含 `code/` 六份成品 .mlog）+ `idioms.json`(30) + `anti-patterns.md`(AP-01..20) | 旧文的"567 处 bug"是 1081 逻辑块口径，本库实测 `.mlog` 口径是 677 处（142 文件），两口径并列记录 |
| 蓝图精讲 | `BLUEPRINT-ANALYSIS.md`（根级 `蓝图层逐类精讲.md` 已于 2026-11-15 删除） | 79KB / 1875 行 | **未并入 07-patterns**（属"蓝图逐类拆解"，非机制） | — | 需要"某个成品蓝图的实现思路"时才查；删除只是去掉重复副本，正文随 skill 文档保留 |
| 实测层 | `MBO/docs` 00-23 + README | 22 篇 / 21KB | **部分吸收** | `02-world/W06/W07/W10` 引用了传动带 4.9/s、硅 2.973/s 等 | 实测值标注 `conf: E`；与字段值冲突时先信字段，再解释"实测为何不同" |
| 配比模型 | `ratio-calc`（gamedata.js 1.13MB） | 33 工厂/17 兵厂/14 发电/10 钻头 | **未吸收**（是计算器，不是知识） | `02-world/W02` 只讲配方机制 | 要算"某产线要几台"仍用它 |
| 配比文档（我建） | `docs/MBO与配比计算器.md` | 246 行 | **已退场（2026-11-08）** | 机制/数值并入 `02-world/W02/W03/W06/W07` + `04-units/U02`；工程部分由 `ratio-calc/README.md` 承接 | 用户要求"以后统一提交到 knowledge"，平行知识库会造成双真源 |
| 检索器说明（我建） | `docs/本地知识库.md` | — | **已退场（2026-11-08）** | `knowledge/tools/README.md` + `REBUILD.md` | 检索/重建用法归 knowledge 工具文档 |
| 技能包 | `mindustry-blueprint/SKILL.md`（及 6 份副本） | 61.5KB | **不替代**（操作说明超集） | — | 它是"怎么用工具"，本库是"机制是什么"，互补 |
| 大语料 | `logic-corpus`（12.8MB / 2273 文件） | 833 .msch + 5774 逻辑块 | **只用于统计证据** | `07-patterns` 的频次数字来自它 | 已被本库引用为"真实写法分布"，不再需要直接检索 |
| 更大语料 | `C:\Users\lliary\mlog-corpus` | 1222MB / 61822 文件 | **未吸收** | — | 做检索会淹没知识；只在"统计某写法多常见"时用 |
| 外部编译器 | `C:\Users\lliary\src\mindcode` | 27.9MB | **交叉验证用** | — | 语义有争议时三方对照（源码 / 本库 / mindcode） |
| 全局 skill | `~/.dsh/skills/mlog-agentskill`（含 mlog.py/mlogcheck.py/instr_semantics.json） | 35KB + tools | **工具链仍用**，数据表已被本库覆盖 | `knowledge/tools/` | 两者不要混：本库不复制它的 82KB 校验器，直接调用即可 |

## 3. 什么时候允许回查旧资产

只有这四种情况，且回答里必须注明"来自旧资产，未经本库复核"：

1. 本库文章明确写了「本库未覆盖 / 见旧文档」的地方；
2. 需要某个**成品蓝图**或**具体模组**的实现（蓝图精讲、MlogAuxiliary、DP-*）；
3. 需要**实测秒表类**数字，而本库只给了字段值（MBO/docs）；
4. 需要**配比/产线台数**（ratio-calc）。

除此之外，答案只能来自 `knowledge/`——因为旧资产里已知的错误至少 6 类（v159.3 源码当现值、craftTime 全 -1、耗电每 tick 当每秒、Logic-Docs 两份不一致、语义表三种尺寸、同结论多副本），本库已逐条修掉并有 `VERSION.md` 的已知错误清单兜底。

## 4. 整合时做过的三件"去重"动作（避免以后又分叉）

1. **单一真源**：数值 → `00-data/`（jar 反射）；语义 → `Mindustry-Source` + 文章锚点；不再保留第二份手抄数值表。
2. **口径写进文件头**：每篇文章 `ver:` 标双版本，正文出现两版差异时用「版本注」而不是并列两张表。
3. **旧副本"停更"**：`PATTERNS.md`、`Logic-Docs-v1.1.0.md` 等仍在原地（有外部引用），但**任何机制修正只改 `knowledge/`**；下次发现旧文与本库冲突，按 `CONVENTIONS.md` 的"冲突处理"提 claims 条目。（2026-11-15 例外：用户裁定根级 `蓝图逻辑模式库.md` / `蓝图层逐类精讲.md` 与其 skill 副本重复，两个根级文件已物理删除，正文仍在 `mindustry-blueprint/` 下。）

> **2026-11-08 收紧**：新知识**只提交到 `knowledge/`**（规则见 `CONVENTIONS.md` §9）；旧文档降为只读存档，不再接收新内容。物理删除前必须同步改 `tests/docsig/run_docsig.py` 与 `rules/*.json` 的 `src`（它们仍把这些文件当输入），再跑 `python gate.py --full`。同期已清理知识库自身的工作产物：`knowledge/_report/attic`（6 份旧 kb.sqlite3，198 MB）与 46 个一次性探针脚本（`p_*.py` 等），门禁仍 `RESULT: PASS`、索引与库一致。
