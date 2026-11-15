# mlog-agentskill · Mindustry mlog 工具链

Mindustry mlog 逻辑的静态分析、规则审计、真执行器模拟，外加两个 DSH skill、一个 Agent 预设，以及一套可从零推导结论的机制知识库。

**本仓只含工具与知识库**：`tools/`、`rules/`、`tests/`、`docs/`（断言表 / 验证记录 / 速查卡 / 游戏速查）、
`knowledge/`（机制知识库：63 篇文章 + 11 张数据表 + 85 条可复测断言 + 300 题评测）、根级
`Logic-Docs-v1.1.0.md`（mlog 语言手册）、`mindustry-blueprint/`（技能文档，模式库 `PATTERNS.md` 与逐类精讲
`BLUEPRINT-ANALYSIS.md` 在这里）、
`.dsh/skills/`（技能安装副本）、`dsh-preset-mlog/`（Agent 预设）、`data/game/`（从 v160.7 导出的游戏事实）。
个人语料、工作笔记（`mlog工作笔记.md`）、场景截图、两个游戏内模组、本地 sidecar（`tools/logicd.py`）、门禁脚本（`gate.py`）
以及 `tools/dev/` 下的一次性拓荒脚本都不在本仓；文档里保留的、指向这些内容的命令与路径是作者本地的执行记录。

## 快速开始

下面的命令都在**仓库根**执行（`cd <repo>`）。如果拿到的是 `.dsh/skills/mlog-agentskill` 那份可独立拷走的技能副本，就照它的 `SKILL.md` §0 做：用绝对路径调用、不要 `cd`、第一步先 `info --verify`。

```bash
python tools/mlogagent.py info --verify        # 第一步：副本完整性（非零即停，别改文件绕过）
python tools/mlog.py doctor                    # 环境自检：入口、Java、server jar
python tools/mlog.py selftest                  # 工具自检（430 项蓝图往返）
python tools/mlog.py check logic.mlog          # 静态检查
python tools/mlog.py check logic.mlog --cost   # 死代码 / 最坏指令数
python tools/mlogagent.py report logic.mlog    # 五层分析一次跑完
python tests/run_tests.py                      # golden 用例（副本陈旧时直接拒绝运行）
python tests/docsig/run_docsig.py              # 文档里的语句签名与语义表逐项机检
python tests/ruleids/run_ruleids.py            # 每条规则必须在某个用例上真点火一次
python tests/shapes/run_shapes.py              # 检查器自身的语句形状不变量
python tests/probes/run_probes.py              # 运行期探针（真执行器，需要 JRE + server jar）
```

依赖：静态分析全部只用 Python 标准库（不用 `pip install`）；`pip install -r requirements.txt` 只为本地知识库 `tools/kb.py`（fastembed 向量 + 重排）；模拟器要 Java 21，环境变量样例见 `.env.example`。

四套测试各有分工：`tests/run_tests.py` 是 golden 断言；`tests/docsig/` 防文档教错语法（槽位数、槽位序、
示例参数数、枚举槽名字——`ucontrol`/`draw`/`ulocate` 子命令、`status` 布尔第一槽、`sensor` 属性必须是 LAccess/Content）；
`tests/ruleids/` 断言没有死规则（只写反例、从不点火的规则在这里红）；`tests/shapes/` 在语句尾部追加惰性 token，
要求规则仍然开火——防整行锚定正则 fail-open。`tests/probes/` 用真 v160.7 执行器跑程序并比对数字
（例如「裸状态名在 v160.7 施加 1200 tick、`@wet` 是静默 no-op」）：静态检查说什么都不算数，运行的数字才算；
没有 JRE 或 server jar 时该步骤报 SKIP 而不是失败。

模拟器（真 v160.7 执行器，需要 Java 21 + server jar）：

```bash
export MLOGSIM_JAR=/path/to/server-release.jar
export MLOGSIM_JAVA=/path/to/java
python tools/mlogsim.py logic.mlog --steps 200
python tools/mlogsim.py logic.mlog --ticks 300 --trace trace.tsv --assert-last "chp < 1000"
python tools/mlogsim.py logic.mlog --save scene.msav --units mono:1 --core-items silicon:400
```

## 目录

| 路径 | 内容 |
|---|---|
| `requirements.txt` / `.env.example` | 唯一需要 pip 的依赖（`kb.py` 的 fastembed，可选）与全部环境变量样例（`MLOGSIM_JAR`、`MLOG_CORPUS`、`KB_*` …） |
| `tools/` | 统一入口 `mlog.py`、模拟器 `mlogsim.py`、检查器/IR/值域、MCP 服务、签名、知识库构建（见 `tools/README.md`） |
| `mindustry-blueprint/` | 蓝图/逻辑技能文档（SKILL / REFERENCE / EMULATOR-CROSSCHECK）与参考数据 |
| `rules/` | 47 条规则（12 ERR / 12 WARN / 15 INFO / 8 SUPPRESSED），一条一个 JSON，供 `review.py` 逐条审计 |
| `tests/` | 75 个 golden 用例，`python tests/run_tests.py`；外加 `tests/docsig/`、`tests/ruleids/`、`tests/shapes/` 与运行期探针 `tests/probes/` |
| `docs/` | `断言表.md`（每条结论的出处与验证方式）、`验证记录.md`（逐条实测）、`速查卡.md`（速查）、`游戏速查/`（物品/方块/单位/配方） |
| `knowledge/` | 机制知识库（Mindustry v160.7 数值 / v159.3 语义）：`KB.md` 是入口与 AI 使用协议，`00-data/` 是机器可读事实表，`01-execution/`…`07-patterns/` 是 63 篇文章，`08-evidence/` 是 85 条可复测断言 + 可执行探针 + 300 题评测，`tools/` 是复现脚本 |
| `Logic-Docs-v1.1.0.md` | 根级 mlog 语言手册；模式库 / 逐类精讲已并入 `knowledge/07-patterns/`，现存副本在 `mindustry-blueprint/`。`tests/docsig/` 会逐条机检这些文档里的语句签名 |
| `data/game/` | 从 v160.7 真执行器导出的游戏事实（物品/液体/方块/单位/别名），供 `game.py` 与知识库使用 |
| `.dsh/skills/` | `mlog-agentskill`（可独立拷走）与 `mindustry-blueprint` 安装副本 |
| `dsh-preset-mlog/` | DeepSeek Harness 的 `mlog` Agent 预设（persona + 技能根 + 工具集） |

## 规则与边界

- 规则可以降级（自动提议），升级必须人点头；`rules/README.md` 说明字段与审计流程。
- 静态检查会误报：约 2 条/块，当提示器用，不当判决书。
- 模拟器覆盖逻辑层、单位运动（B 档）、世界方块更新、天气与子弹命中；战斗 AI/波次/电力图/地形碰撞不模拟，真游戏行为必须由玩家验收。
- 跨处理器按变量名 `read`/`write` 需要 `.msch` 里的链接表；裸 `.mlog` 用 `--links auto` 按名字推断。
- 知识库是快照：改完文档/工具后跑 `python tools/kb.py build`（`kb.py` 会先告诉你索引是不是已经旧了）；
  `knowledge/` 每条知识带置信度 S（源码可查）/ E（实测可复现）/ I（推导）/ U（未验证），引用时按这个标注。

## 许可

MIT。技能文档中的校准数字来自作者本地语料，仅作量级参考。
