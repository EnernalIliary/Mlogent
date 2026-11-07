# AtomicStates · Mindustry mlog 工具链

Mindustry mlog 逻辑的静态分析、规则审计、真执行器模拟，外加两个 DSH skill、一个 Agent 预设和一个本地知识库。

这是**完整工作区**：除工具/规则/测试/技能外，还包含个人语料、工作笔记、场景截图与 `Logic/` 下的示例程序。
公开的精简版在 https://github.com/EnernalIliary/mlog-agentskill （只含工具、规则、测试、技能文档）。

## 快速开始

```bash
python tools/mlog.py doctor                    # 环境自检：入口、Java、server jar
python tools/mlog.py selftest                  # 工具自检（430 项蓝图往返）
python tools/mlog.py check logic.mlog          # 静态检查
python tools/mlog.py check logic.mlog --cost   # 死代码 / 最坏指令数
python tools/mlogagent.py report logic.mlog    # 五层分析一次跑完
python gate.py                                 # 全部门禁一次跑完（见下）
python gate.py --full                          # 再加 430 项蓝图自检 + 运行期探针 + 语料两关 + 语句形状不变量（需 JRE；重步骤并发，约 25 s）
python tests/probes/run_probes.py              # 只跑运行期探针（真执行器，断言语义）
python tools/logicd.py                         # Mlog辅助的本地 sidecar（游戏内模组 MlogAuxiliary/ 的后端）
python tests/logicd/run_logicd_tests.py        # sidecar 契约：协议 + 把载荷灌进真处理器回读
python tests/mlogauxiliary/run_quickcheck_tests.py  # 游戏内快检：规则表没漂移 + 14 个用例 + 不误报交叉验证
python tests/mlogauxiliary/run_rhino_parity.py      # 同一批用例在真 v160.7 的 Rhino 里重跑，与 node 逐条比对
python tests/mlogauxiliary/run_ui_smoke.py         # 整个 main.js 在真引擎里初始化 + 设置表格布线（无 JRE 则 SKIP）
```

`python gate.py` 依次跑：`mirror`（`tools/` 与三处副本是否一致 —— 测试实际上导入的是
`mindustry-blueprint/tools` 副本，副本陈旧会让整套测试“绿着但测的是旧代码”）、`tests`、
`rule_capture.py lint`、`tests/shapes/run_shapes.py`（检查器自身的语句形状不变量：
语句尾部追加惰性 token 后规则仍须开火，防整行锚定正则 fail-open）、`tests/docsig/run_docsig.py`（文档里的语句签名与 `tools/instr_semantics.json` 机检：槽位数、槽位序、示例参数数、参数表、枚举槽名字（`ucontrol`/`draw`/`ulocate` 子命令、`status` 布尔第一槽、`sensor` 属性必须是 LAccess/Content）；
文档教错语法会在这里红）、`tests/ruleids/run_ruleids.py`（每条规则必须在某个 `tests/cases/*.mlog` 上真点火一次，
且 rid → 用例的映射与 `tests/rule-coverage.json` 一致——只写反例的规则在这里红）、`quickcheck`（游戏内快检 `MlogAuxiliary/scripts/quickcheck.js` 的规则表由 `tools/rules_export.py` 从 `instr_semantics.json` 生成：先验表没漂移，再跑 14 个用例，并用全量检查器做**单向**交叉验证——快检说断链的行，全量检查必须也这么说；少报允许，瞎报不允许）、`rhinoparity`（同一批用例在真 v160.7 的 Rhino 里重跑；node 永远看不见 split(正则) 按字符切的那个 bug）、`ui`（把 MlogAuxiliary/scripts/main.js 整段按 Mods.loadScripts 的方式加载进真引擎的脚本作用域，再让模组把设置表格造到一张假表上——抓 Table/Cell 漂移和初始化抛错，这些 node 侧一条也发现不了）、`global`（用户级技能副本）、`kb`（`out/_kb/kb.sqlite3` 是否比
`docs/断言表.md`、`tools/*.py` 旧）。默认档约 5 s，够日常改完就看；`--full` 追加 `mlog.py selftest` / `probes` / `logicd` / `corpus` / `coverage` 五步——它们互不依赖（各自起 JVM、各写各的 `out/_bench` 文件），所以**并发跑**；两条长杆内部再各自并行（`probes` 20 个 JVM、`selftest` 8 进程 + 验证重建用 deflate 1 级），合计 100 s → **约 25 s**，`--serial` 恢复串行。`--kb-build` 在 KB
陈旧时自动重建，`--only test` 只跑名字含某子串的步骤，`--strict` 把 WARN **和 SKIP** 都当失败
（`probes`/`corpus` 的跳过条件正好是干净 checkout 的默认状态，不 strict 的话它们可以永久静默）。
`--full` 里的 `probes` 用真执行器跑 `tests/probes/manifest.json` 里的程序并比对数字（例如
“裸状态名在 v160.7 施加 1200 tick、`@wet` 是静默 no-op”）——静态检查说什么都不算数，
运行的数字才算；没有 JRE 或 `out/` 下的分版本 jar 时该步骤报 SKIP 而不是失败。

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
| `tools/` | 统一入口 `mlog.py`、模拟器 `mlogsim.py`、检查器/IR/值域、MCP 服务、签名、知识库、写入服务 sidecar `logicd.py` |
| `mindustry-blueprint/` | 蓝图/逻辑技能文档（SKILL / REFERENCE / EMULATOR-CROSSCHECK）与参考数据 |
| `gate.py` | 一键门禁（mirror 一致性 / tests / lint / 语句形状 / 全局副本 / KB 新鲜度） |
| `rules/` | 41 条规则（33 条在报，8 条 SUPPRESSED），一条一个 JSON，供 `review.py` 逐条审计 |
| `tests/` | 43 个 golden 用例，`python tests/run_tests.py`（副本陈旧时直接拒绝运行）；`tests/probes/` 是真执行器的运行期断言，`tests/shapes/` 是检查器自身的语句形状不变量（7 形状 x 4 变体），`tests/ruleids/` 断言没有死规则 |
| `docs/` | 本地知识库说明、`断言表.md`、`验证记录.md`、`速查卡.md`、`Mlog辅助-设计.md`、`MBO与配比计算器.md`（MBO/ratio-calc 的结论、公式、数值表）、`游戏速查/`（物品/方块/单位/配方） |
| `data/game/` | 从 v160.7 真执行器导出的游戏事实（物品/液体/方块/单位/别名），供 `game.py` 与知识库使用 |
| `Logic/` | `逻辑代码规范.md` 与示例逻辑（个人程序） |
| `out/scenes/` | 5 张现实场景 `.msav`、3 个合成台（`benches/`：core / memory / processor）、快照 |
| `.dsh/skills/` | `mlog-agentskill`（可独立拷走）与 `mindustry-blueprint` 安装副本 |
| `MlogAuxiliary/` | 游戏内模组（Rhino JS）：F4 一句话 → 本地 sidecar 选模板生成 + 预检 → 走原版 config 通道写进处理器；原版逻辑编辑器底部自动挂审查栏 |
| `dsh-preset-mlog/` | DeepSeek Harness 的 `mlog` Agent 预设（persona + 技能根 + 工具集） |
| `MBO/` | 蓝图生成/搜索/优化/真机验证（`python -m mbo …`，`docs/00-23`，`runs/` 里是真机实测的蓝图与画廊） |
| `ratio-calc/` | 自动配比计算器单页网页（双击 `index.html`；`core.js` 内核与 MBO 规则一致） |

## 规则与边界

- 规则可以降级（自动提议），升级必须人点头；`rules/README.md` 说明字段与审计流程。
- 静态检查会误报：约 2 条/块，当提示器用，不当判决书。
- 模拟器覆盖逻辑层、单位运动（B 档）、世界方块更新、天气与子弹命中；战斗 AI/波次/电力图/地形碰撞不模拟，真游戏行为必须由玩家验收。
- 跨处理器按变量名 `read`/`write` 需要 `.msch` 里的链接表；裸 `.mlog` 用 `--links auto` 按名字推断。
- 知识库是快照：改完文档/工具后跑 `python tools/kb.py build`（或 `python gate.py --kb-build`，`gate.py` 会先告诉你它已经旧了）。

## 许可

MIT。技能文档中的校准数字来自作者本地语料，仅作量级参考。