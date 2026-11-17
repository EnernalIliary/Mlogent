# 知识库写作规范（CONVENTIONS）v1

本文件是**唯一写作契约**。所有 knowledge/ 下的产出必须遵守，否则 check_kb.py 不通过。

## 1. 目录与归属

    00-data/       机器可读事实表（脚本生成，禁止手改）
    01-execution/  执行模型（处理器/预算/帧差/同步）
    02-world/      方块/物流/电力/液体/热/钻探
    03-combat/     弹道/伤害/护甲/状态/炮塔
    04-units/      单位/AI/能力/生产
    05-campaign/   波次/规则/胜负
    06-mlog/       语言层（语法/指令/陷阱）
    07-patterns/   蓝图架构/idiom/反模式
    08-evidence/   证据（claims/probes/bench）
    tools/         生成与校验脚本
    .index/        检索产物

## 2. 知识原子 ID

格式：域.子域.三位序号，全大写。

    WORLD.LOGISTICS.002
    COMBAT.DAMAGE.003
    MLOG.BUDGET.001
    EXEC.PROCESSOR.001
    UNIT.AI.001
    CAMP.WAVES.001
    PATTERN.SWARM.001

- 域代码固定：EXEC / WORLD / COMBAT / UNIT / CAMP / MLOG / PATTERN / DATA
- 一篇 md = 一个 ID；一篇可以很长，但超过 250 行必须拆成同一子域的多个 ID。
- ID 一旦发布永不复用、永不改号；废弃用 status: deprecated。

## 3. frontmatter（每篇必带，YAML）

    ---
    id: WORLD.LOGISTICS.002
    title: 传送带吞吐与容量
    domain: world
    status: active          # active | draft | deprecated
    ver: [v160.7_rt, v159.3_src]
    conf: E                 # S 源码 / E 实测 / I 推断 / U 未验证
    src:
      - "MBO/docs/14-传送带与布线器实测.md:1-60"
      - "mindustry.world.blocks.distribution.Conveyor (v159.3)"
    data: [00-data/logistics.json#conveyor]   # 本文引用的数据表路径
    depends: [WORLD.LOGISTICS.001]
    tags: [物流, 吞吐, 传动带]
    tokens: 1600
    ---

tokens 由 check 脚本回填，不用手写精确值。

## 4. 置信度（conf）

- **S**：有源码行号或 jar 反射字段直接支撑。
- **E**：真机实测（MBO/ratio-calc/mlog_sim 探针），附实验条件。
- **I**：由 S/E 推导，文中必须写出推导链。
- **U**：未验证，必须写明"需要什么实验才能验证"，且**不得出现在 KB.md 的答案路径里**。

> **出处路径按旧名写、按同级目录找**：`MBO/`、`ratio-calc/`、`assetsraw/` 是拆出本仓库的
> **同级独立项目**（`../MBO/`、`../ratio-calc/`、`../TextureMDT/`）。`src:` 与 `[实测: …]`
> 里保留旧名是为了历史可对；真去找文件时去同级目录，本仓库内没有。

## 5. 硬规则（违反即失败）

1. **无源数字禁止**。任何数值必须满足其一：
   - 来自 00-data/*.json（写 `见 DATA#xxx` 或直接引用字段名）；
   - 紧跟 `[src: 文件:行]`；
   - 来自实测并写 `[实测: MBO/docs/xx]`。
   宁可写"见数据表"，也不要凭记忆写数字。
2. **单位必须显式**。/tick 与 /s 不可混写；能量 1 单位/tick = 60/s。写作 `1.5/tick（90/s）`。
3. **双版本**：凡 v159.3 与 v160.7 可能不同的，写 `[v159.3]… [v160.7]…`，不要只写一个。
4. **反例必写**。每篇至少一个"什么时候不成立/常见误解"，这是防幻觉的关键。
5. **不写产品/工具开发内容**（面板宽度、jobqueue、undo 快照等），它们属于工程库。
6. **不写模组内容**（DP-*、MindustryX），v1 只收录原版。

## 6. 七段式模板

    ## 一句话
    <一句话结论，可直接当答案首句>

    ## 规则 / 公式
    <可计算的规则，公式用 ``` 代码块；变量含义写清>

    ## 数值
    <表格，尽量由 00-data 生成；列出典型值与边界值>

    ## 源码锚点
    <类名:行号，说明这段代码在干什么>

    ## 实测与反例
    <真实数字 + 实验条件；至少一个反例/边界>

    ## 常见误解
    <AI 最容易答错的 2-4 条，每条给正确说法>

    ## 相关
    <ID 列表 + 数据表路径>

## 7. 表格与代码

- 表格用 markdown 表格，第一列是 id 或名称，数值列带单位。
- 代码块语言标记：mlog / json / java / text。
- 路径一律写相对仓库根的路径，便于 grep。

## 8. 数据表契约

00-data/*.json 每条记录必须含：

    id        游戏内 id（kebab-case）
    name      name 字段
    src       来源（"jar:v160.7#..." 或 "src:path:line"）
    ver       "v160.7" | "v159.3" | "both"
    数值字段   统一 { v: 数值, unit: 单位 } 或纯数值且在该表 README 中声明单位

表级 README 说明单位、口径、生成脚本、生成时间、条数。

## 9. 知识归属与提交点（2026-11-08 起）

**新增的机制 / 数值 / 公式 / 逻辑语义知识，只提交到 `knowledge/`**，按 §1 的域归位；数据进 `00-data/`，证据进 `08-evidence/`。不再往下列旧文档追加内容——它们只作存档与回归测试的输入：

| 旧文档 | 现状 | 还在被谁读 |
|---|---|---|
| `Logic-Docs-v1.1.0.md` | 存档（部分吸收） | `tests/docsig/run_docsig.py`、`rules/slot-not-in-enum.json`、`rules/under-arity.json` 的 src |
| `mlog工作笔记.md` | 存档（部分吸收） | `tests/docsig/run_docsig.py` |
| `蓝图逻辑模式库.md` / `蓝图层逐类精讲.md` | **根级副本已物理删除（2026-11-15）**；模式库内容在 07-patterns | 现存副本 `mindustry-blueprint/PATTERNS.md` / `BLUEPRINT-ANALYSIS.md` 现在是 docsig 的输入源，不再由根级派生 |
| `docs/游戏速查/` | 存档（薄投影，数值已作废） | `tools/kb.py` 的 DOC_GLOBS（检索语料） |
| `docs/断言表.md` / `docs/验证记录.md` | 存档（真机制部分已分层进 claims/probes） | 产品侧流程引用 |

- 工具用法（怎么跑命令、怎么自检）仍归 `mindustry-blueprint/SKILL.md`；模组/产品文档仍归 `docs/Mlog辅助-*`。两者都不是知识条目，不要写进 `knowledge/`（见 §5 第 5、6 条）。
- 若要物理删除某个旧文档，必须同步改 `tests/docsig/run_docsig.py`（它把这些文件当输入校验签名）和 `rules/*.json` 里引用它的 `src` 字符串，然后跑 `python gate.py --full`。
- 检索库的语料只从 `knowledge/` 构建（`build_index.py --root knowledge` → `kb.py build` → `publish_db.py` → `postpublish.py`）；工作产物放 `knowledge/_report/`，不进索引。
