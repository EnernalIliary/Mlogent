# 00 接手交接：项目地图 · 团队分工 · 下一轮路线

日期：2026-10-24（本轮只读勘察，未改动任何原始文件）　牵头：lead（Agent Teams）
本轮用户要求：① 了解项目具体结构 ② 创建智能体团队并分工 ③ 不改动原始文件。

## 0. 30 秒版

- 这是一个 **Mindustry mlog 逻辑的工程化工具仓**：静态检查 + IR/值域 + 蓝图(.msch) 生成/解析 + 真执行器模拟（JVM + 游戏 jar）+ 签名后处理 + 规则库 + 断言/验证体系 + 本地知识库检索(MCP)，外加两个 DSH skill 和一个 Agent 预设。
- 主开发仓 `F:\OneDrive\桌面\AtomicStates`（HEAD `f055b92`），公开精简仓 https://github.com/EnernalIliary/mlog-agentskill（HEAD `7fae685`，release v1.0.3）。**两侧无共同祖先，不能互推。**
- 工具链本身是健康的：五条链路都通，36 条 golden、28 条规则、75 条断言、5 张模拟场景、4 张 .msch 合成台都在。
- 真正的风险不在功能，在**一致性**：① 测试跑的是 `mindustry-blueprint/tools` 副本而不是顶层代码；② 文档数字与状态已经漂移（断言表还写着「未执行」、golden 写着 24/12 实际 36）；③ 至少 5 条 PASS 的证据撑不住结论；④ 发布链路是手工的，本地无 tag、zip 手工打。
- 本轮产出 5 份报告（各 15–25 KB，共约 100 KB），全部在 `out/takeover-20261024/`，索引见 §3。

## 1. 项目结构与目录职责

| 路径 | 角色 | 关键事实 |
|---|---|---|
| `tools/` | **母本**：全部工具 | 42 个顶层 `.py` + 9 张数据表 JSON + `dev/`(178 一次性) + `corpus/`(46 批量流水线) |
| `rules/` | 规则库 | 28 个规则 JSON（22 semantics / 5 heuristic / 1 negative）+ README |
| `tests/` | golden 回归 | 36 条用例 + `expected.json` + `run_tests.py` |
| `docs/` | 断言表 / 验证记录 / 知识库说明 / 游戏速查 | 7 个 md；游戏速查 4 份共 76 KB（单位/方块/方块配方/物品） |
| `data/game/` | 游戏版本事实层 | v1.0.3 新纳入公开仓 |
| `mindustry-blueprint/` | skill 文档 + **tools 副本（超集 ~37 文件）** | `SKILL.md` 63KB、REFERENCE 73KB、PATTERNS 101KB、BLUEPRINT-ANALYSIS 78KB |
| `.dsh/skills/` | 仓库内 skill 安装副本 | `mlog-agentskill/tools/` 仅 20 项（9 py + 9 json + MANIFEST） |
| `dsh-preset-mlog/` | Agent 预设 | id=mlog，整份 config 替换（不深合并），customSkillDirs 指向 `<repo>/.dsh/skills` |
| `Logic/` | 用户自己的成品逻辑 | 7 个文件（序切着陆 v2.1、堡垒寻核、写满停、ILI资源保护、逻辑代码规范 20.9KB） |
| `out/` | 草稿与产物（2GB，17k 文件） | 场景、存档、JRE21、server jar、发布脚本、旧会话转储；大部分被 .gitignore 覆盖 |
| `saves/` | 游戏存档镜像（58 文件） | 不是场景池，尺寸可达 1000×1000 |
| `Mindustry-Source/`、`Arc-Source/`、`assetsraw/` | 上游源码与素材 | 全部 gitignore，仅本机存在 |

三份 tools 副本的关系：**母本 = `tools/`**；`mindustry-blueprint/tools/` 是超集（无 MANIFEST）；`.dsh/skills/mlog-agentskill/tools/` 是分发子集 —— **mlogsim / mlogrange / mlog_labelize / mlog_mcp / kb / review 根本没分发**，所以拷出去的技能包里模拟器和知识库不可用，`SKILL.md:707` 的「自带全部模块」只对 mlogagent 的 9 个模块成立。

## 2. 五条主链路（命令 → 入口 → 产物）

| # | 链路 | 命令 | 入口 | 产物 |
|---|---|---|---|---|
| 1 | 静态检查 | `python tools/mlog.py check x.mlog [--cost]` | `mlogcheck.py:642 analyse()` | Findings（ERR/WARN/INFO）+ cost |
| 2 | IR / 值域 / 跳转表 / 位域 | `mlog.py ir|values|ranges|pack` | `mlogir.py:437 Program` + `mlogval.py` | 指令表、可达行、值域、打包位域 |
| 3 | 蓝图 gen / parse | `mlog.py gen|parse` | `mschgen.py:287 Blueprint.build`（290-295 回读校验，失败不产出） | `.msch` 二进制 / 蓝图文本 |
| 4 | 真执行器模拟 | `python tools/mlogsim.py x.mlog --ticks/--steps/--save/--units/--assert` | `mlogsim.py:1256 main()`（jar `out/_server160.jar`，JRE `out/jre21`） | 变量终态、`@counter`、text buffer、trace TSV |
| 5 | 签名 + 标签化 | `mlog.py post` / `mlog_labelize` | `aigenerated.py:333 post()` | 带隐藏署名与注释包的 mlog |

另两条服务层：
- **MCP**：`tools/mlog_mcp.py` 暴露 check/ir/values/gen/sim；配置片段在 `tools/README.md:42-51`。
- **本地知识库**：`tools/kb.py` — build(`:170`) → SQLite+FTS5 trigram(`out/_kb/kb.sqlite3`) → search(`:235`，向量+FTS 双召回 RRF 融合，`--rerank` 可选) → serve(`:302`)；模型缓存在 `out/_kblibs*`、`out/_kbmodels`（均 gitignore，新克隆必须重建）。

数据表是「库的第二个输入」：`mlog.py:106-113` 在 import 时加载 8 张表，`_load_json` **吞异常返回 {}** → 少张表只会让检查变松，不会报错。

## 3. 团队分工与本轮产出

4 名 teammate（均 fresh 上下文）+ 共享任务板（task-1..4，写作用域互斥），lead 并行做发布链路审计。

| 成员 | 任务 | 报告 | 一句话结论 |
|---|---|---|---|
| repo-map | 工具链架构 | `01-repo-map.md`（220 行） | 五链路已定位到行；但测试/审核/模拟器都 import **副本**，改顶层不同步则 golden 全绿而线上错 |
| verify-assets | 断言/规则/golden 覆盖 | `02-verification-assets.md`（232 行） | 75 条断言 72 PASS / 2 推翻 / 4 未跑；断言表已不是单一真源；至少 5 条 PASS 证据不足 |
| sim-scenes | 模拟器边界与场景 | `03-sim-scenes.md`（171 行） | 能力边界清晰；上一会话点名的四大缺口**全部已修**；不模拟波次/电力图/寻路/毁建筑连锁 |
| session-digest | 上一会话交接 | `04-session-digest.md`（171 行） | 27 条用户规则、10 条决策、12 条教训、8 项待办，全部带 seq |
| lead | 发布链路 | `05-publish-chain.md` | 本地/公开无共同祖先；tag 只在远端；zip 手工；`out/_public` 落后 origin/main 2 条 |

配套件：`out/takeover-20261024/tools/session_dump.mjs`（多帧 zstd 解压 + 摘要导出；`--seq N` 取单条、`--grep` 全库搜），素材在 `_session/_digest_{user,assistant,tools}.md`。

## 4. 交叉核对：五份报告共同指出的 5 个系统性问题

### 问题 1（最高优先级）测试测的不是你改的代码
`tests/run_tests.py:43-50` 把 `sys.path` 指向 `mindustry-blueprint/tools` 再 import 分析器；`review.py:47`、`rule_audit.py:40`、`mlogsim.py:146` 同样指向副本。当前 7 个关键模块 SHA256 相同（verify-assets 实测），所以现在没炸；但一旦分叉，**测试全绿而线上是旧的**。工作笔记 `:3130` 记过这坑。修法二选一：让这些入口指回顶层 `tools/`，或把 `sync_mlogagent.py --check` 做成门禁。

### 问题 2 文档已经不是真源，而且互相矛盾
- `docs/断言表.md:3` 仍写「状态：未执行」，而表内判定列已填 ✅(E)。
- 被推翻的 `L2-11` 在 `docs/断言表.md:48` 仍是 ✅，与 `docs/验证记录.md:44` 的 FAIL 冲突。
- `docs/验证记录.md:110-112` 的「未实跑 9 条」是旧数据（其中 5 条实为 PASS）。
- golden 数量：README `:35` 写 36（对），`mindustry-blueprint/SKILL.md:703` 写 24、`:712` 写 12（都错）。
- `out/scenes/README.md` 提到的 `scenes.json` 实际不存在。
→ 口径：**验证记录 > 断言表 > SKILL/README**；引用任何数字前先自己跑一遍。

### 问题 3 PASS ≠ 已证明
证据分级 S(源码)/E(实测)/I(推断) 已建立，但有 5 条 PASS 的证据撑不住断言：`L1-17`（证据是 `a=null`，空场景区分不了链接下标）、`L1-19`（`no unit r=null`，没量到 range）、`L2-08`（用 5/9 格替代 6/8 格）、`L2-14`（证据指向外部未核对文件）、`L4-03`（「原件已失 → 改用别的断言覆盖」，实际没跑 mindcode 对拍，而 `out/probes/p1-p9` 都还在）。另有 9 处 I 级推论被当事实用（`02` §5 点名）。

### 问题 4 模拟器的能力边界没写进交付纪律
能证：逻辑指令层、天气、工厂方块更新、核心资源、ubind、v160 跨处理器链接、多处理器同 tick 顺序。部分：单位物理（B 级，stop 后 120 tick 仍余 0.096 tile）、战斗 AI（无寻敌/编队）、子弹命中（镜像 updateEntities，实测核心 hp 1100→974）。**不模拟**：波次（`WaveSpawner` 零命中）、电力图（`PowerGraph` 零命中）、引擎寻路、毁建筑连锁、payload 建造，以及一切画面。上一会话的误判几乎都出在这条边界上（`04` §4）。

### 问题 5 发布链路全靠人肉
`out/_sync_public.py`（脱敏替换表：猪猪鱼→mlog、艾铭→作者、iliary→you、D:/bots→`<bot-workspace>`、本机路径→`<repo>`）+ 手工 commit/push + `out/_release_v103.py`（硬编码 TAG/ZIP/正文，走代理 10808，token 来自 `git credential fill`）。缺口：zip 手工、无「公开仓 HEAD 应等于哪个 sha」的记录、**本地与公开仓都没有 tag**（tag 只在远端）、`out/_public` 落后 `origin/main` 2 条（`204c398`、`9d90546`，都是 README 过滤修正）。

## 5. 先信的 10 条硬事实（都有出处）

1. 环境：从仓库根跑 `python tools/mlog.py doctor` → python 3.11.4、server jar `out/_server160.jar`、JRE21 `out/jre21`；**PATH 里的 java 是 Java 8 stub**，模拟器必须用 JRE21。
2. 断言：75 条（L1 22 / L2 16 / L3 6 / L4 4 / R 14 / S 13），72 PASS、2 推翻（`L2-11`、`S-04`）、4 未跑（`L2-07`、`R-12`、`S-01`、`S-12`，后两条在本机无法验证）。
3. 规则：28 条，22 semantics（永不允许自动降级）、5 heuristic、1 negative；28/28 有 `counter_example`，`auto_downgrade` 全 false；但**反例守卫零自动化**（`rule_capture.py lint` 不在 tests 里），且 `unary-op-extra-operand` 的反例拿「该命中」的样例当反例。
4. golden：36 条，覆盖 check 16 / cost 5 / gate 3 / values 4 / ir 3 / pack·gen·aigenerated·mcp·cross 各 1；**mlogsim 一条测试都没有**，`review/rule_*` 为零，3 个 fixture 无人引用。
5. 模拟器 CLI：30 个参数（`mlogsim.py:1258-1324`）；`--ticks N` 只有 N−1 个活动 tick 且 `@tick` 从 2 起（`:79-83`）；`--steps` 数指令；`--update all` 会跳过处理器防双跑（`:675`）；`--power` 只是把 `power.status` 钉 1.0/0.0（`:676`），不建电力图。
6. 性能：冷启动 2.2–2.7 s、2000 步 0.14 s、reload 0.12 s、`--daemon --remote` 单文件 0.6 s；**64×64 是 `--world` 默认值不是引擎上限**（`out/maps` 300×220、存档镜像 1000×1000 都能跑）。
7. 四大历史缺口已修：`--core-items`（`mlogsim.py:295-328/420-453`，commit `40239f0`）、`read/write @this`（`mlogcheck.py:815/825`）、`ucontrol idle`（`instr_semantics.json:486-495`）、`ubind`（`mlogsim.py:661 updateTeamStats` 是 headless 侧唯一补丁）。遗留只是文档没同步（transferDelay 30–40 tick 重试、idle 认领不驱动、`@this` no-op）。
8. 数据表静默降级：`mlog.py:97-113` 的 `_load_json` 吞异常返回 `{}`，丢表不报错。
9. 作者署名硬编码在 `aigenerated.py:52 DEFAULT_AUTHOR`，公开分发全靠 `_sync_public.py` 洗。
10. 磁盘卫生：`out/_sim/` 有 **3711 个历史 run 目录**（`Server.close()` 只关进程不删，`mlogsim.py:368-373`）；`out/` 总 2 GB。

## 6. 上一会话留下的硬约束（精选 10 条，完整 27 条见 `04` §2）

1. **不要用 `wait` 空转控延迟**，用 `timer = @time + 延迟`，窗口里干别的（seq 11499）。
2. `@client` 一类是 world processor 专属特权变量，普通逻辑不得调用（seq 11499、12348）。
3. `ubind` 参数是 **unit type** → 按内部顺序轮转绑定；是 **unit 实例** → 绑那个单位（seq 12789）。
4. `set 控制数量 0` 是合法配置入口，不是 bug（seq 12789）。
5. `print` 里的反斜杠 n **是换行**；旧笔记「不换行」讲的是 `set Instruction` 的字符串处理，被错推广（seq 23271）。
6. `@counter` 的算术运算也要计入「类 jump」（seq 14417）。
7. link 变量名**只取最后一段**：`silicon-arc-furnace1` 只代表 `furnace1`（seq 17116）。场景测试必须给所有 link 有效化（seq 12789）。
8. 签名三支规则（以此为准）：① 末行有可解析的**无效参数** → 签进去；② 末行是 `end` → 换成 `jump 0 0 always` 再签；③ 其它且无 `end` → 追加 `jump 0` 再签。**token 不能被丢弃**（seq 15788/16171/23863）。
9. 注释要打包进签名字符串并保留原始行号（seq 21685/21841/22219）。
10. 交付口径：战斗/波次/真实战果**不在模拟器范围**，明确交玩家验收（seq 4941/6199）。

## 7. 下一轮路线（P0 先做，都有验收标准）

### P0 · 半天，先把「可信度」修回来 —— ✅ 2026-10-24 第二轮已全部完成（结果见 §11；下面保留原始验收标准以便复核）

1. **只读基线复验**：`check` 全量 + labelize 往返字节一致 + 签名 verify + 72 条 PASS 复跑。验收：一份 `out/takeover-20261024/06-baseline.md`，把红项逐条列出。理由：本轮所有「上一会话说 PASS」都还没被独立复验，而 selftest 曾因坐标平移误判出 100+ 假阳性。
2. **副本一致性门禁**：`sync_mlogagent.py --check` 进 `tests/run_tests.py`（或 pre-push）。验收：故意改顶层不同步，测试必须变红。
3. **文档对齐**：`docs/断言表.md:3` 去掉「未执行」、`:48` 的 `L2-11` 改 FAIL、`docs/验证记录.md:110-112` 删旧「9 条」段、golden 数字统一 36（README/SKILL 两处）。验收：全文 grep 「写 24 / 写 12 / 状态：未执行」无残留。
4. **补可做的未跑断言**：`L2-07`、`R-12` 实跑并回写；`S-01`、`S-12` 标注「本机不可验证 + 依赖 QQ 插件侧」。

### P1 · 1–2 天，能力与自动化

5. **`--assert` 直接断言 trace TSV**（约 30 行）：单场景回归一条命令跑完。
6. **规则反例守卫进 tests**：`rule_capture.py lint` 纳入，修 `unary-op-extra-operand` 反例，处理 3 个未引用 fixture。
7. **发布固化为 `tools/publish.py`**：sync → 反向脱敏扫描 → 公开仓 commit → tag → release → 下载校验 → 记录 `public_sha/tag_sha/zip_sha256`；并给 `out/_public` 加前置断言（HEAD == origin/main、工作区干净）。zip 改用 `git archive` 生成。
8. **check Finding ↔ rules 对齐表**（34 处 Finding ↔ 28 条规则）：目前两者无强制绑定，rules 里有规则 ≠ check 会报。
9. **清理与文档**：`out/scenes/README` 补 `scenes.json` 或删引用；`out/_sim` 只保留最近 N 次；`tools/dev/` 178 个脚本补 .gitignore 或迁移。

### P2 · 需要用户点头（上一会话已明确搁置）

10. 战斗/波次模拟 + `spawnWave` 场景（用户 seq 6199 明确交玩家验收，要先点头）。
11. B 方案「引擎事实表自动化」（用户 seq 19706「我准备审批」）。
12. VM 自研（用户 seq 23464「先不管这个 VM」，对比结论保留在助手 23156）。

## 8. 风险清单（按杀伤力）

1. **假安全感**：改顶层不同步副本 → 测试全绿、线上旧代码。
2. **发布即泄漏**：手工复制绕过 `_sync_public.py` 会把 `猪猪鱼/艾铭/iliary/OneDrive 路径/D:\bots` 带出去，也会把 `find_signature.py`、`classify_signature.py`、`PATTERNS.md`、`BLUEPRINT-ANALYSIS.md` 发出去（这些在 `EXCLUDE_PREFIX` 里）。
3. **误推公开库**：本地 `origin` 指向公开仓 main，直接 push 会 force 覆盖过滤树；两侧无 merge base，pull/merge 同样危险。
4. **知识库过期**：改 `tools/*.py` 或 9 个文档后不跑 `kb.py build`，检索会返回旧源码片段**附带 path:start-end 出处**（看起来更可信，实际更危险）。
5. **模拟器不可移植**：`mlogsim.py:154` 硬编码 Steam Java 路径、jar/JRE 都在 gitignore 的 `out/`；新克隆静态检查全绿但模拟器直接不可用。
6. **特权语句静默消失**：`mlogsim.py:151 PRIVILEGED_RE`（fetch/status/setblock/spawn/message…）在微处理器里会被 LParser 丢掉且行号错位，静态检查查不出。
7. **环境摩擦**：PowerShell 控制台 GBK（中文必须用 read/grep 或 `PYTHONIOENCODING=utf-8`）、CRLF/BOM、`git push` 需代理 10808、审批策略 ask + 超长上下文会导致工具全挂（上一会话就是这么结束的）。

## 9. 本轮约束遵守证据

- `git status --porcelain`：**13 个 M 文件与本轮开始前完全一致**（DP-CameraUnbind 全套 + 根目录两个大 md，都是接手前就存在的改动），未新增/修改/删除任何已跟踪文件。
- 新增文件仅 9 个，全部在 `out/takeover-20261024/` 下（5 份报告 + 3 份会话摘要 + `session_dump.mjs`）。
- 未执行 `git add/commit/push`，未跑 `mlogsim`（会起 JVM 并写 `out/_sim`），未联网。
- 唯一副作用是读：`out/` 与 `_session/` 大文件；`out/takeover-20261024/_session/` 合计约 9.4 MB 会话摘要（可随时删）。

## 10. 每份报告怎么用

| 想知道 | 看 |
|---|---|
| 某个工具文件是干什么的、改完要同步什么 | `01-repo-map.md` §1、§6 |
| 哪条结论可以信、哪条只是推断 | `02-verification-assets.md` §5、§6 |
| 这条断言 / 这版模拟器到底证明了什么 | `02` §4、`03` §2、§7 |
| 模拟器怎么开、某场景该怎么测 | `03` §1、§3、§9（可复现命令） |
| 用户以前明确要求过什么 | `04` §2（27 条带 seq） |
| 发布怎么走、哪里会炸 | `05-publish-chain.md` §3、§5 |

---

## 11. 第二轮（P0）执行结果 · 2026-10-24

用户 m00181 授权 P0 路线后执行，全部落地，已由 lead 亲自复跑验收。

### 11.1 交付

| 任务 | 负责人 | 产物 | 结论 |
|---|---|---|---|
| P0-1 只读基线复验 | verify-assets | 06-baseline.md + out/_baseline/raw/ | 6 项绿（doctor / tests 36 / selftest 430 / check 40 文件 / labelize 13 文件幂等 / 签名四态），3 项红全在**取证层** |
| P0-2 副本一致性门禁 | repo-map | tests/run_tests.py + 08-gate.md | 三镜像 + skill-doc 四类检查，能红能绿（self-check 3/3） |
| P0-3 文档对齐 | session-digest | 09-docs-align.md | 21 处改动，只碰 4 个文档文件 |
| P0-4 补跑断言 | sim-scenes | 07-assert-runs.md + out/_assert_runs/probe_l207.py | L2-07/R-12 **FAIL**；S-01/S-12 结构性不可验证 |
| P0-2b / P0-2c（复核中发现） | repo-map | 08-gate.md §9/§10 | 修 aigenerated 漂移 + 测试改测母本 + 第三镜像 + 安装副本同步 |

### 11.2 这一轮改变了什么事实（最重要）

1. **L2-07「出生在 solid 格当 tick 死」被推翻**（E，v160.7）：直接 UT.spawn 到 stone-wall / micro-processor 格，5 个活动 tick 后仍 valid=true hp=150，空地对照臂同样存活。R-12 是它的别名，同判。CLI 侧复现不了的原因不是没现象，而是 freeSpot（tools/mlogsim.py:622-637,651-652）硬绕开 solid。
2. **sensor dead @unit @dead 在 @unit == null 时返回 1** ⇒ 用 dead=1 判「单位死了」是假阳性，断言表 L2-07 行已加警告（须先判 @unit 非 null）。
3. **git 里有三份代码副本，不是两份**：mindustry-blueprint/tools、.dsh/skills/mlog-agentskill/tools、.dsh/skills/mindustry-blueprint/tools；最后一份是 DSH 实际加载的安装副本，本轮之前就已陈旧（mlogagent.py 14515B vs 母本 14698B），且 SKILL.md 与开发副本逐字节相同 ⇒ 只改开发副本对 bot 不可见。
4. **aigenerated.py 是孤儿运行时依赖**：tools/mlog.py:87 直接 import 它，但它既不在 mlogagent._MODULES 也不在 MANIFEST.sha256 里，所以同步永远漏掉它。已纳入 payload（tools/mlogagent.py:251-256）。
5. **测试原本测的是副本**：tests/run_tests.py:44 的 TOOLS 曾指向 mindustry-blueprint/tools，改母本不同步副本仍全绿。现改为 HERE.parent/"tools"，副本由门禁守。
6. **L1-17 / L1-18 记录错**：L1-17 实测 a=Building#211[0,2]:message（0 是链接下标，旧记录 a=null 是没开 --links）；L1-18 越界读**是 0 不是 null**（numval=0，只有 jump … equal r null 为真）。

### 11.3 验证口径（当前有效）

- 断言表 75 条 → 验证记录 78 行（L2-10 / L4-02 / S-13 各拆 a/b）；**PASS 68 · 已推翻 4 · UNRUN 6**。
- 已推翻 4：S-04、L2-11、L2-07、R-12。待复跑 4：L1-19 / L2-08 / L2-14 / L4-03。本机不可验证 2：S-01 / S-12（需 QQ 渠道 owner）。
- golden = **36** 条（tests/expected.json 36 个顶层键，tests/cases/ 35 文件），SKILL 里的 24/12 已改。

### 11.4 收尾复跑（lead 亲自跑）

- python tests/run_tests.py → **36/36 passed**，四条门禁全 PASS：mindustry-blueprint/tools、.dsh/skills/mlog-agentskill/tools（19 shared 0 differ）、mindustry-blueprint skill (install)、skill-doc/consistency（identical），EXIT=0。
- python tests/run_tests.py --self-check → 3/3，EXIT=0。
- .dsh/skills/mlog-agentskill/tools/mlogagent.py info --verify → manifest : all files match，EXIT=0。
- pre-manifest 比对：只有 6 个预期源文件 + 7 个副本文件变化（tests/run_tests.py 21113→29478、docs/断言表.md、docs/验证记录.md、README.md、mindustry-blueprint/SKILL.md、out/scenes/README.md、三个 mlogagent.py、aigenerated.py、MANIFEST.sha256），**没有其他已跟踪文件被动过**；git status 482 → 498 行，全部可解释。
- 未 git add/commit/push，未联网。

### 11.5 下轮建议（P1 之内，仍未授权）

1. tools/sync_mlogagent.py 加 --mirror bp|install|all，并给安装副本也写 MANIFEST.sha256：第三份副本现在靠手工 Copy-Item，门禁能发现但修起来还是手工。
2. mlogsim.Server(java, jar) 里 os.path.abspath：相对路径在库方式下必挂（Java 子进程 cwd 是 out/_sim/run-*）。
3. 改写 tools/mlogsim.py:618-621 注释（把「unitCap=0 在 add() 杀单位」与「solid 致死未复现」分开）。
4. JS 控制台读取式写进文档（Groups.unit.size() 是方法，Unit.dead/health 是属性）。
5. Logic/ILI资源保护-v1.1.mlog 独占 19 条 sensor-not-a-property WARN，是唯一「规则在真实程序上大量命中」的样本，建议人工抽 3 条判断是误报还是真问题。
6. KB 快照需重建（本轮改了工具与文档）：python tools/kb.py build。
7. dist/ 里两份旧 SKILL.md 仍写「12 條 golden」，属构建产物，未动。

---

## 12. 第三轮（P1 收尾五件 + 三个顺手修）· 2026-10-24

用户「都做吧」授权执行 §11.5 的建议。**全部完成**，收尾复跑全绿。

### 12.1 交付

| 项 | 谁 | 结果 | 报告 |
|---|---|---|---|
| ① sync --mirror 收敛四份副本 | repo-map | --mirror skill/bp/install/all，all 不含 global；三处各带 MANIFEST，写完自动 info --verify | 10-sync-mirror.md |
| ② Server jar/java abspath | sim-scenes | tools/mlogsim.py:179-194 新增 _abs_path（裸命令名不动，保持 PATH 语义）；:200-203 入口统一解析 | 11-sim-fixes.md |
| ③ spawn 注释改写 | sim-scenes | 现 tools/mlogsim.py:631-646 把「unitCap=0 在 add() 移除单位」与「solid 出生致死 v160.7 未复现（L2-07 推翻）」分开写 | 11-sim-fixes.md |
| ④ JS 控制台 API 文档 | sim-scenes | tools/README.md:30-74：三件套 + 读取式表 + 可跑示例 + 3 条坑 | 11-sim-fixes.md |
| ⑤ ILI 19 条 WARN 抽 3 条 | verify-assets | 结论：**规则太粗，不是数据表不全**；且这 19 行真正的问题是 `core` 链接名从未绑定（check 0 报错） → 19 条误报 + 1 条漏报 | 12-ili-warns.md |
| ⑥ KB 快照重建 | session-digest | 零联网（HF_HUB_OFFLINE=1 + TRANSFORMERS_OFFLINE=1），5352 块 / 56 文件 / 29.7 s | 13-kb-rebuild.md |
| ⑦a 我补：KB 语料补真源文档 | lead | tools/kb.py:47-62 DOC_FILES 增加 docs/断言表.md、docs/验证记录.md → 重建 5374 块 / 58 文件；「L2-07 已推翻」现在能检索到 | 本文件 §12.3 |
| ⑦b 我补：tools/README.md:3 版本号 | lead | 「真 v159.3 执行器」→ 默认官方 **v160.7** jar，并说明数据表 `source:` 的 v159.3 是数据表版本、不是模拟器版本 | 本文件 §12.3 |
| ⑦c 我补：第四份副本 global | lead | `sync_mlogagent.py --global` 已装到 C:/Users/lliary/.dsh/skills/mlog-agentskill（21 文件），`--check` 转 in sync | 本文件 §12.3 |

### 12.2 变更清单（本轮新增的已跟踪改动）

- 代码：tools/mlogsim.py、tools/kb.py、tools/sync_mlogagent.py（178→300 行）；两个镜像副本里的 sync_mlogagent.py 同步。
- 文档：tools/README.md（:3 版本号 + :30-74 JS API + :141-157 四处副本与 --mirror 命令）。
- 副本：mindustry-blueprint/tools/MANIFEST.sha256、.dsh/skills/mindustry-blueprint/tools/MANIFEST.sha256（各 1543 B，**新文件，建议纳入跟踪**：内容确定、让两处副本能自校验；不要就删，sync 会重建）。
- 未动：Logic/、dist/、docs/ 正文（除上一轮已改的两份）、tests/run_tests.py（门禁一行未改，MIRROR_IGNORE 已含 MANIFEST）。

### 12.3 收尾复跑（lead 亲自）

- python tests/run_tests.py → **36/36 passed** + 四条门禁 PASS，EXIT=0
- --self-check → 3/3，EXIT=0
- sync --mirror all --check → 三处 in sync，EXIT=0；sync --global --check → in sync，EXIT=0
- KB 重建后检索验证：「L2-07 已推翻 断言」前 4 条全落在 docs/验证记录.md 与 docs/断言表.md（补语料前 0 命中）
- git status 482 → 507 行，全部可解释；未 git add/commit/push，未联网（KB 全程带离线变量）

### 12.4 下轮候选（都还没做，按价值排序）

1. **`sensor-not-a-property` 规则文案与判据错了**（tools/mlogcheck.py:794-800）：只问「名字在不在 LAccess 白名单」，但 sensor 第三操作数也可以是 Content（源码 LExecutor.java:691-693 走 se.sense(co)，Senseable 默认返回 0 不是 null）。文案 "the game returns null here" 对 item 名是假的。
2. **「链接名从未绑定」没有任何规则覆盖**：ILI 那个文件 19 行全读 `core`（真实名是 shard1）→ 19 条误报 + 1 条漏报。建议加一条 check（link 名不在 getlink 集合里 → ERR）。
3. **`sensor-not-a-property` 不在 rules/ 体系**（内联规则，无 JSON、不走 auto_downgrade 单向棘轮）→ 治理缺口。
4. **`kb.py search` 排序区分度低**（RRF 0.0159–0.0167 挤在一起），专有标识符查询别信排序；噪声来自 _split_long 按行硬切（tools/kb.py:136）。
5. dist/ 两份旧 SKILL.md 仍写「12 條 golden」（构建产物，改了会被下次构建覆盖）。
6. P2 三条（战斗/波次模拟、引擎事实表自动化、VM 自研）仍等用户点头。


---

## 13. 第四轮（P0：sensor 判据 + 链接名 check + LAccess 数据表）· 2026-10-25

用户「修」授权做 §12.4 的第 1、2 条；执行中发现 253 条红线根因是**数据表缺项**，一并修掉。四个任务全部 completed，收尾复跑全绿。

### 13.1 交付

| 项 | 谁 | 结果 | 报告 |
|---|---|---|---|
| ① sensor 判据与文案 | repo-map | tools/mlogcheck.py:893-927 四分支：LAccess 静默 / item·liquid 静默 / block·unit·status → INFO `sensor-content-not-a-property` / 未知名 → WARN `sensor-not-a-property`（文案改成 v160.7 实测口径：目标变量被写成 null、比较恒假） | 14-sensor-link-fix.md |
| ② 新增「链接名永不可绑」 | repo-map | tools/mlogcheck.py:839-875 `link-name-unbindable`（WARN）；独立 token pass（`uses_of` 会过滤掉 KEYWORDS，实测 `uses_of('sensor n core @hyper-processor')==[]`）；LINK_PARAMS :384-388 覆盖 9 个助记符 | 14-sensor-link-fix.md |
| ③ 数据表 | repo-map | tools/content_names.json（12146 B）+ 生成器 tools/content_names_from_source.py | 14-sensor-link-fix.md |
| ④ 规则进 rules/ 体系 | repo-map | rules/ 四条：sensor-not-a-property / sensor-content-not-a-property / sensor-item-read-is-fine（negative）/ link-name-unbindable；lint 32 rules / 30 checked / 0 unguarded / 3 problem（既有） | 14-sensor-link-fix.md |
| ⑤ 真 v160.7 取证 | sim-scenes | out/takeover-20261024/scenes/sensor_oracle3.py / oracle4.py：有容器→数量、无容器→null、Block 名→null、**未知名字把目标写成 null（推翻「不赋值」的源码推断）**、未绑定链接→null | 15-sensor-link-oracle.md |
| ⑥ 验证固化 | verify-assets | tests/expected.json:227-240 digest 追加 [WARN,3]+[INFO,1]；docs/断言表.md 加 S-14..S-18 五条（全 ✅(E)）；docs/验证记录.md 追加 7 小节；ILI 19 条 → 0 | 16-verify-sensor-link.md |
| ⑦ LAccess 表重建 | repo-map | tools/sensor_attrs.json 75 → **77 项**（jar 枚举序），生成器 tools/sensor_attrs_from_jar.py（--check 幂等）；回归 100/1421 存档 sensor-not-a-property **981 → 0** | 17-laccess-table.md |
| ⑧ 我补：旧生成器退役 | lead | tools/sensor_from_source.py 只剩 DESC（被 sensor_attrs_from_jar 导入），`main()` 改成直接拒绝写；tools/mlog.py:666 的提示改指 jar 生成器 | 本节 |
| ⑨ 我补：docs 数字对齐 | lead | docs/验证记录.md 表头 75→80 条 / 78→83 行、合计 PASS 68→73，结果表补 S-14..S-18 五行；docs/断言表.md S-18 注明表已重建为 77 项 | 本节 |
| ⑩ 我补：global 副本 | lead | `sync_mlogagent.py --global` 22 文件写入 C:/Users/lliary/.dsh/skills/mlog-agentskill，`--global --check` in sync（teammate 会话写不了那里） | 本节 |

### 13.2 关键结论（都带源码或实测依据）

- `sensor` 第三操作数的语义分三层：LAccess 名（77 个）→ 读属性；Item/Liquid 名 → 容器里有就返回数量、没容器返回 null（内部 Float.NaN，`equal r 0` 会命中）；Block/UnitType/Status 名 → null。**未知名字不是「不赋值」，而是把目标变量写成 null**（v160.7 实测，`set d 77` 后被覆盖）。
- 链接名由 Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:331-360 `findLinkName` 生成：`bname + outnum`，outnum 从 1 起 ⇒ **真链接名一律以数字 ≥1 结尾**；`:123-135` `getLinkName` 把 `core-shard` 缩成 `shard`。所以 `core`、`you`、`Notification` 这类名字永远绑不上，写出来就是恒 null 的静默语句。
- 旧 tools/sensor_attrs.json 的 75 项是 **v159.3 Java 快照**；真机 out/_server160.jar 的 `mindustry/logic/LAccess.class` 有 87 字段、其中 ACC_ENUM(flags & 0x4000) **77** 个，与 Mindustry-Source 的 LAccess.java 完全一致，差集只有 `enabled`/`color`。jar 比源码多 3 个非枚举字段（privileged / privilegedAccess / senseablePrivileged）⇒ 下次升级必须以 jar 为准重跑生成器。
- `@color` 读到的是对象引用位模式（2.120554921e-314），`print` 显示 0 —— 别当数值用。

### 13.3 收尾复跑（lead 亲自）

- python tests/run_tests.py → **36/36 passed**，EXIT=0
- python tools/rule_capture.py lint --verbose → 32 rules / 30 checked / 0 unguarded / 3 problem（三条既有，EXIT=1 是基线）
- python tools/sensor_attrs_from_jar.py --check → `77 LAccess names from the jar; ok`，EXIT=0
- python tools/content_names_from_source.py --check → ok，EXIT=0
- sync --mirror all（三处各 2 changed）→ --check 三处 in sync；--global → --check in sync
- 回归（100/1421 存档、5944 处理器）：sensor-not-a-property 981→0、link-name-unbindable 0→15、sensor-content 0→4，其余规则 delta 全 0，总命中 1542→580
- 未 git add/commit/push；未联网

### 13.4 仍未做（下轮候选，按价值排序）

1. **同步脚本不给数据文件建新副本**：tools/sync_mlogagent.py 的 MIRRORS 三处 may_create=False，本轮新增的 content_names.json 是手工 bootstrap 到三处副本的；建议加「数据文件可创建」白名单。
2. ~~kb 快照又旧了~~ —— **本轮已重建**（离线变量同上）：chunks 5374→**5481**、files 58→**60**；检索「link-name-unbindable 链接名」前三条命中 tools/mlogcheck.py:837-845 与 mindustry-blueprint/REFERENCE.md:153-167。下次改工具/文档后记得再跑。
3. **link pass 只覆盖 9 个助记符**：新指令若带链接位置参数要手加 tools/mlogcheck.py:384-388；ulocate / ucontrol / getlink 故意排除。
4. **content_names.json 的 unverified 兜底**（block 25 / unit 6：build1..16、ore-* 等）让它们算已知 Content → INFO 而非 WARN，偏保守会漏报。
5. **E 级覆盖缺口**：unit 目标那批属性（health/x/team/type/controller…）因 mono 复制体死在实体格上没测到，需要活单位场景补。
6. **git 未提交**：本轮 + 上轮全部改动仍只在工作区（tools/ rules/ tests/ docs/ 三处副本 + out/takeover-20261024/）；建议一次 commit 分两块（规则与数据；副本 MANIFEST 与 content_names.json）。
7. P2 三条（战斗/波次模拟、引擎事实表自动化、VM 自研）仍等用户点头。
---

## 14. 公开仓发布（2026-10-25 凌晨，lead 亲自）

用户 m00948「gitcommit一下吧，可以push」→ 本地仓提交 + 公开仓三轮提交推送。

### 14.1 本地仓

- 提交 **e20e71a**「rules: sensor 判据改四分支、新增 link-name-unbindable、sensor_attrs 按 v160.7 jar 重建为 77 项」：42 files changed +7077/−2832，**只按显式路径 stage**，0 个 `out/` 文件入栈；脱敏扫描仅命中 token/Token 一词（注释），无路径无凭据。
- 本地 main 与 origin/main **无共同祖先**（公开仓是过滤重写后的另一条历史），**不可 push/pull 本地仓**；只 commit，push 走 `out/_public`。

### 14.2 公开仓（EnernalIliary/mlog-agentskill）

| 提交 | 内容 |
| --- | --- |
| **3844500** | rules: sensor 四分支 + link-name-unbindable + content_names/sensor_attrs_from_jar + rules/ 四条 JSON + tests digest + docs 断言表/验证记录；公开版补 `.dsh` 三处镜像与 `mindustry-blueprint/tools/content_names.json` |
| **318bc88** | dsh: 技能副本补 `aigenerated.py`（此前 `mlog.py` 顶层 import 直接 ModuleNotFoundError，这份「可独立拷走」的副本是坏的）+ 新增 `.gitattributes`（`* text=auto eol=lf`）+ MANIFEST 重算 20 条 |
| **609d6f5** | chore: 全仓换行统一 LF，修好 MANIFEST 在全新克隆上 9 个文件 MISMATCH |

推送远端 = `609d6f5`（`318bc88..609d6f5 main -> main`）。**直连 github.com:443 时通时不通，稳定走代理** `git -c http.proxy=http://127.0.0.1:10808 -c https.proxy=http://127.0.0.1:10808 push origin main`（`ls-remote` 同样要代理）。

### 14.3 发布链路的三处修补（`out/_sync_public.py`）

1. **新文件不会自动进公开仓**：脚本以 `git -C out/_public ls-files` 为文件集真源，新增的 `tools/content_names*.{json,py}`、`tools/sensor_attrs_from_jar.py`、`rules/*.json`（glob）、两处 `content_names.json`、`.dsh` 的 `aigenerated.py` 已并入 `NEW_FILES` / `NEW_GLOBS`。
2. **作者名脱敏会让 golden 签名 id 变化**：新增 `fix_golden_author_ids()` —— 跑公开仓 tests，只把「双方都含 `aigenerated:`」的失配 got 值回写 `tests/expected.json`（别的一概不碰，免得洗掉真实回归）。
3. **换行与哈希**：改为**按字节比对写 bytes**（母本 Windows CRLF 不再被误判成「内容相同」），并新增 `.gitattributes`（`* text=auto eol=lf`）；`rebuild_manifest()` 用 LF 字节重算 `.dsh` 的 MANIFEST。

### 14.4 全新克隆验收（从 GitHub 真克隆，非本地拷贝）

```
git -c http.proxy=http://127.0.0.1:10808 clone https://github.com/EnernalIliary/mlog-agentskill out/_clonecheck
CRLF 文件数            : 0        （全 LF）
python tests/run_tests.py  : 36/36 passed, EXIT=0
mlogagent.py info --verify : manifest: all files match, EXIT=0
mlog.py check tests/cases/sensor-not-prop.mlog : 3 WARN link-name-unbindable + 1 INFO sensor-content-not-a-property → 0 error/suspect, 3 warn
```

临时克隆验证完即删（`out/_clonecheck`）。

### 14.5 仍未做（顺延）

1. `out/_sync_public.py` 仍不是一条命令的发布固化（P1-7 `tools/publish.py` 仍缺）；每次同步都会重写那 2 条 author-signed id（幂等，无净 diff）。
2. 本地仓 491 条未提交改动里仍是接手前的历史改动（DP-CameraUnbind、两个大 md、saves/ 等），与规则无关，未处理。
3. §13.4 的 7 条除第 6 条（git 未提交）外全部顺延：数据文件自动建副本、link pass 助记符覆盖、unverified 兜底、unit 属性 E 级缺口、P2 三条。

---

## 15. 第五轮（C 阶段：全量 sweep 驱动 → `status` 规则整条推翻 + 度量基座）· 2026-10-25

用户 m01231「继续」。这一轮的顺序是「先量，再判，再改」：把 1421 个真存档全量跑一遍，
用数据找出最贵的单条规则，然后拿源码验它，验穿后推翻并改写。
详细报告：**`18-status-effect-slot.md`**；度量工具说明：**`out/_bench/bench-README.md`**。

### 15.1 交付

| 项 | 结果 | 位置 |
|---|---|---|
| 全量语料 sweep | 1421 save / 103787 处理器 / 8603 份不同程序，10 worker，185–199 s，unreadable=0 | `out/_bench/_corpus_sweep.py` → `sweep-full.json/.md` |
| findings 重聚类（绕开「Finding 无 rule id」） | 386 → 修复后 376 簇；按 msg 模板归并 | `out/_bench/_reagg.py`、`reagg-prefix.json`、`reagg.json` |
| 指标快照工具 | `tools/dev/bench.py`（392 行）：tests/lint/checks/sweep 四层 → 一个可 diff 的 JSON | `out/_bench/bench-20261025-160643.json` |
| 工具说明 | 三种计数口径 + 已知 rid 缺口写清 | `out/_bench/bench-README.md` |
| **规则推翻** | `status-name-needs-at`：effect 槽是**字面量裸名**，`@` 形式反而不生效 → 整条改为判决记录（`SUPPRESSED`） | `rules/status-name-needs-at.json` |
| 判据重写 | 删旧反向分支，新增槽位检查（`@` 在 effect 槽 → INFO；未知状态名 → INFO） | `tools/mlogcheck.py` |
| 语义表 | `status` 行 `uses [1,2]→[2,3]`、`maybe_uses [3]→[]` | `tools/instr_semantics.json` |
| fixture + golden | `status-bare-ok.mlog`（零 finding）、`status-effect-slot.mlog`（恰 2 条 INFO）；SUITE 两行 | `tests/cases/`、`tests/run_tests.py`、`tests/expected.json`（+19 行） |
| 文档固化 | 断言表 L1-23/L1-24（S 级）；验证记录两行 + 一节；表头口径 82 条/85 行 | `docs/断言表.md`、`docs/验证记录.md` |

### 15.2 量化（同口径前后对比才有意义）

| 口径 | 修复前 | 修复后 | Δ |
|---|---|---|---|
| 程序级（sweep-full.md TOTAL，跨 worker 去重） | 7490（388/1372/5730） | **6931（388/1372/5171）** | −559 |
| 分片级重聚类 `reagg.json total` | 16844（INFO 11407） | **13452（INFO 8015）** | −3392 |
| 处理器出现级（bench 快照） | 未取 | 49805（ERR 14662/WARN 17891/INFO 17252） | — |

消失的**只有** status 家族（10 个 msg 变体、3392 条、覆盖最多 412 存档），WARN/ERR 一条没动；
新槽位检查在 1421 存档里**命中 0**（语料里既没有 `@状态名` 也没有拼错的状态名）。
三种口径的关系写在 `out/_bench/bench-README.md` §3，**不可互相加减**。

### 15.3 收尾复跑（lead 亲自，全绿）

- `python tests/run_tests.py` → **38/38 passed**，EXIT=0
- `python tools/rule_capture.py lint` → **32 rule(s) / 32 checked / 0 unguarded / 0 problem**，EXIT=0（历史基线 3 problem）
- `python tools/sync_mlogagent.py --mirror all --check` → skill/bp/install 三处各 20 文件 in sync，EXIT=0
- `python tools/sync_mlogagent.py --global`（22 文件）→ `--global --check` in sync，EXIT=0
- `python tools/dev/bench.py --workers 10` → 全量 163.4 s，快照落盘，EXIT=0
- 未联网；`Logic/`、`saves/` 等原始文件只读未动；git 三个提交见 §15.5

### 15.4 仍未做（下轮候选，按价值排序）

1. **E 级缺口：状态是否真的施加**。`mlogsim.Server` 只有 `send/wait_for/js/fill_cores/reset_world/prepare/close`，
   没有「跑完程序查 `unit.hasEffect`」的钩子；要补得在 `srv.js()` 里遍历 `Groups.unit`。本轮的 L1-23/24 只有 S + 静默性 E。
2. **`_corpus_sweep.py` 的 rid 归类 bug 未修**：worker 里应拿 `rules/*.json` 的 `msg_any` 把 finding 归到 rule id，
   否则 `sweep-full.md` §1 的「规则」列永远混着语句文本（现在靠 `_reagg.py` 绕）。
3. ~~知识库又旧了~~ → **已重建**：`python tools/kb.py build` → `chunks 5492 / files 60`（上一版 5374/58；离线变量见 §12.3）。
4. **`@enabled` 那类「数据表口径」问题值得再扫一遍**：这次是 `status` 字面量槽，同类「x 槽其实是字面量/Content 名」
   的指令（`setrule` 的规则名、`control` 的配置项、`ulocate` 的组名）还没系统核过。
5. ~~git 未提交~~ → **已提交**（§15.5）：474ea02（status 判据反转，18 文件）、bf3a897（rules lint 归零，4 文件）、b1688ab（接手前的树内遗留 17 文件）。`tools/dev/bench.py` 仍不入库（`tools/dev/.gitignore:1:*`）。
6. P2 三条（战斗/波次模拟、引擎事实表自动化、VM 自研）仍等用户点头。

### 15.5 收尾提交与知识库（2026-10-25 16:40，依据用户 m01590「你可以动文件，自由gitcommit」）

| commit | 内容 | 规模 |
| --- | --- | --- |
| `474ea02` | check: status 的 effect 槽是字面量裸名（@ 形式静默无效）；推翻 status-name-needs-at | 18 files, +261/−113 |
| `bf3a897` | rules: lint 归零（32/32, 0 problem）——dead-polarity 转 SUPPRESSED、两条规则反例换 fixture | 4 files, +46/−40 |
| `b1688ab` | chore: 接手前就留在工作树里的改动（DP-CameraUnbind 脚本与打包、out 索引、两份大 md），与本轮规则无关 | 17 files, +2919/−2453 |

- 提交后 `git status --porcelain` 已无 tracked 修改，剩 481 个 `??`（`out/` 产物、`Logic/`、`saves/`、`Mindustry-Source/` 等原始文件，均为接手前状态）
- `tools/dev/bench.py` 仍不入库：`tools/dev/.gitignore:1` 是 `*`
- `python tools/kb.py build`（`HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`）→ `chunks 5492 / files 60`（上一版 5374/58）
- 提交后复跑：`tests/run_tests.py` **38/38** EXIT=0；`rule_capture.py lint` **32 checked / 0 unguarded / 0 problem** EXIT=0
- **未 push**：`git status -sb` = `## main...origin/main [ahead 167, behind 18]` —— 本地与 origin 已双向分叉，push 前需人决定策略，本轮只做本地提交

---

## 16. 第六轮（D 阶段：语料驱动的事实修正 + 发布 v1.0.4，2026-10-25 傍晚）

依据用户 m01726 的五项裁决：①核同类字面量槽 ②做 E 级「状态真的施加」实测 ③修 `_corpus_sweep.py` 的 rid 归类 bug
④P2 三条「都不起」 ⑤本轮结束发 release。原始文件（`Logic/`、`saves/`、`Mindustry-Source/`、`assetsraw/`）仍只读。

### 16.1 交付表

| 交付 | 位置 | 结论 |
| --- | --- | --- |
| 字面量槽核实报告（并入 §16.2） | `out/_bench/probe/literal_slots.mlog` | 枚举/布尔/Content 字面量槽**不会**被当成未赋值变量，同类误报不存在，不改判据 |
| E 级 status 实测 | `out/_bench/_e_status6.py` + `out/_bench/probe/status-effect-elevel.log` | 裸名有效（`getDuration` 1200 / 300），`@` 前缀 0，清除 0 |
| rid 归类修复 | `out/_bench/_corpus_sweep.py`（809 → 852 行） | findings 变 5 元组带真 rule id；计数逐位不变 |
| 本轮报告 | `out/takeover-20261024/19-status-elevel-and-rid-fix.md`（6787 字符） | 三节：结论 / 源码行号 / 量化 + 未做清单 |
| 断言升级 | `docs/断言表.md`、`docs/验证记录.md` | L1-23 / L1-24 由 S 级升 **E 级**；顺手删掉断言表里重复的两行 |
| 发布 | GitHub Release `v1.0.4` | 见 §16.4 |

### 16.2 三项核实的事实（可复现）

**① 字面量槽（结论：不需要改判据）**。`tools/instr_semantics.json` 已用 `tokens` 声明枚举槽：
`control` → `tokens={"0":"LAccess"}`、`ulocate` → `{"0":"LLocate","1":"BlockFlag"}`、`setrule` → `{"0":"LogicRule"}`、
`radar` → `{"0..2":"RadarTarget","3":"RadarSort"}`、`ucontrol` → `{"0":"LUnitControl"}`。
源码依据：`LStatements.java:432-482`（`:433 public LAccess type`，`:474-476 new ControlI(type, builder.var(target), builder.var(p1)…builder.var(p4))`）、
`:1194-1255`（`:1196 LLocate`、`:1197 BlockFlag`、`:1198 String enemy/ore`）、`:1768-1835`（`:1770 LogicRule`）、`:484-553`（`RadarStatement`）。
探针 `literal_slots.mlog` 11 行只报 3 条：`ERR L0 ulocate used but there is no ubind -> @unit is null` + `WARN L8 ax/ay sits in a parameter slot this instruction never reads`（`ucontrol idle ax ay 0 0 0` 的隐藏签名告警，属另一类）。

**② E 级 status（结论：裸名有效，`@` 前缀静默无效）**。钩子就是 `Server.js()`（`tools/mlogsim.py:300-311`），没改模拟器。
前提坑：空白世界没有 core 时 `unitCap=0`，spawn 的单位在 `add()` 里直接删掉 → 必须先 `srv._core_spec="copper:100"` 再 `srv._unit_spec=[["flare",1]]`。

| 用例 | 写法 | `getDuration` |
| --- | --- | --- |
| A 基线 | 无 | 0 |
| B 裸名施加 | `status false wet @unit 20` / `status false unmoving @unit 20` | **1200 / 1200**（20 s × 60） |
| C 清除 | `status true wet @unit` / `status true unmoving @unit` | 0 / 0 |
| D @ 前缀 | `status false @burning @unit 5` / `status false @unmoving @unit 5` | 0 / 0（no-op） |
| E 裸名别的效果 | `status false burning @unit 5` | **300** |

顺带记一个引擎坑：`unapply` 后 `hasEffect` 仍为 true（`StatusComp.java:83-92` 只删 entry 不清 `applied` 位、`:247-248` 读 `applied.get(id)`、`:186` 只在 `update()` 里重组；sim 默认 `--update none` 不自愈）→ **判读效果存在性用 `getDuration`**。

**③ rid 归类修复**。新增 `_matchers()`（读 `rules/*.json` 的 `match.sevs` + `msg_any`，两者都非空才收录）、`_rid_for(sev, msg)`（**最长 msg_any 命中优先**，窄规则压宽规则）、`_rid(f)`（取 `f[4]`，缺失回落语句文本再回落 `(no-id)`）；findings 由 4 元组变 **5 元组**，10 处解包点改成按索引。

| 指标 | 修复前 | 修复后 |
| --- | --- | --- |
| `sweep-full.md` §1「规则」列 | 大多是源码语句文本 | 全是真 rule id（virus-logic 3891 / link-name-not-bound 1126 / undefined-var 907 / jump-to-jump-chain 337 / version-gate 242 …） |
| 总命中（程序级去重） | 6931 | **6931（逐位相同 → 只改归类不改计数）** |
| rule_counts 键 | 41 | 41：32 键命中 `rules/*.json`（6868 条 / **99.1%**）；9 键回落语句文本（63 条） |

回落残留（治理缺口）：`link-name-hyphen` **52 条**（`mlogcheck` 里确实有这条规则，但 `rules/` 没有对应 JSON）、`ulocate building <flag> true @copper …` 7 条、`self-write-noop` 1 条。

### 16.3 收尾复跑（全绿，lead 亲跑）

- `python tests/run_tests.py` → **38/38 passed**，EXIT=0
- `python tools/rule_capture.py lint` → **32 rule(s) / 32 checked / 0 unguarded / 0 problem(s)**，EXIT=0
- `python tools/sync_mlogagent.py --mirror all --check` → skill/bp/install 各 20 文件 in sync，EXIT=0
- `python tools/sync_mlogagent.py --global --check` → in sync with `C:\Users\lliary\.dsh\skills\mlog-agentskill`，EXIT=0
- `python tools/mlog.py selftest` → `logic fidelity 430/430 exact round-trip`（full build 204 ok / 226 skipped）
- `python tools/kb.py build`（离线）→ **chunks 5493 / files 60**
- 全量 sweep 复跑（rid 修好后）→ 1421 save / 10 worker / `procs=103787 unique=8603 unreadable=0 secs=132.8`

### 16.4 发布 v1.0.4（用户裁决⑤）

| 项 | 值 |
| --- | --- |
| Release | https://github.com/EnernalIliary/mlog-agentskill/releases/tag/v1.0.4 |
| 公开仓提交 | `05d8744` docs: L1-23/L1-24 证据升 E 级；断言表去掉重复两行（2 files, +6/−8），`36b1f1e..05d8744` |
| tag sha | `05d8744e9b1b6aa5c2c04ef1794b00d3c82edb2e`（= 推上去的提交，未另打 tag 对象） |
| asset | `_release_v104.zip`，**843,630 B**，221 个 entry，顶层目录 `mlog-agentskill-1.0.4/`（= `out/_public` 整树） |
| 下载校验 | `HEAD browser_download_url` → **200**，Content-Length 843630 与本地一致 |
| 正文 | `out/_release_v104_body.md`（1520 字符，中文）；发布脚本 `out/_release_v104.py` |
| 本地提交 | `fb1bc02`（同内容，2 files, +6/−8；edit 工具写 LF 后会整文件翻行尾，已按原 CRLF/mixed 重写再提交，所以历史里只有真改动） |

发布链路（沿用 v1.0.3 形态）：`out/_sync_public.py` 同步 → `out/_scanpub2.py` 脱敏扫描（`scanned 2 file(s); personal-string hits: 0`）→ `out/_public` 内 `tests/run_tests.py` **38/38** → commit + push → `out/_release_v104.py`（`git credential fill` 取 token、POST/PATCH release、上传 asset、取 tag sha、HEAD 校验）。

### 16.5 未做 / 下轮候选（按价值排序）

1. **`link-name-hyphen` 缺 `rules/*.json`**：`mlogcheck` 里 52 条命中没有治理记录（既不在 rules 体系、也不走 `auto_downgrade` 棘轮）→ 补一条 kind=semantics 的规则 JSON。
2. **E 级 status 钩子没沉淀成正式 API**：现在靠 `out/_bench/_e_status6.py` 直接调 `srv.js()`；建议在 `tools/mlogsim.py` 加 `server.unit_effects()` 之类的只读查询，让「状态/装备/指令效果」都能一句测。
3. **`out/_bench/_corpus_sweep.py` 与 `_reagg.py` 仍在 out/**：不进 `tools/`（门槛：被 tests 或文档引用）就一直是草稿；若要长期用，考虑提到 `tools/corpus/`。
4. **公开仓本地知识库不同步**：公开仓只有语料/工具，本地 KB 已重建（5493/60），但公开版没有 KB 产物（设计如此）。
5. **P2 三条**（战斗/波次模拟、引擎事实表自动化、VM 自研）：用户 m01726 明确「都不起」，不再列候选。

## §17 第五轮修订：status effect 槽按版本改写（用户反馈驱动，2026-10-25）

### 17.1 起因

用户两次指出「裸名不是应该用 status-effect 才对吗，当前版本就只能这样施加状态。这是当前版本生效的完整命令：
`status false @status-wet unit 10`」。第 19 号报告与 docs 里「`@` 形式静默无效」的说法被否证，本轮重测并改正。

### 17.2 结论（双版本）

| 写法 | v159.3 | v160.7 |
| --- | --- | --- |
| `status false wet @unit 10`（裸已知名） | ✅ 600 | ✅ 600 |
| `status false @status-wet @unit 10` | ❌ none | ✅ 600 |
| `set s @status-wet` + `status false s @unit 10` | ❌ none | ✅ 600 |
| `@wet` / `status-wet` / 未知名 | ❌ none | ❌ none |

机制：v159.3 的 `ApplyEffectI.effect` 是 `String`（执行期 `content.statusEffect()` 精确查表）；v160.x 的同一字段变成 `LVar`，
LParser 把裸的已知状态名归一化成 `@status-<name>` 常量（`LStatements.java:1568-1625`、`ContentLoader.java:228-240`），
所以裸名、`@status-<name>`、以及「变量里存 `@status-<name>`」三种写法都生效；`@<name>` 与 `status-<name>` 都不是常量，静默 no-op。
证据：`out/_bench/_e_status12.py`（v160.7）、`out/_bench/_e_status13.py`（v159.3）、报告 `20-status-effect-slot-forms.md`。

> **重建声明（2026-10-28）**：下面 §18–§28 的原文在一次 `write` 事故中被截断（`read` 工具对大文件只返回前一段，
> 按「读出全部 → join → 整写回」处理时只写回了前 514 行）。原编号 25–27 的逐节分配、逐字叙述与部分行号已丢失；
> 以下按会话摘要与会话内记录重建，**保留可核对数字与结论**，不再声称逐字还原。教训见 §29.5。

## §18 门禁与副本一致性（2026-10-25 夜）

- `gate.py`（仓库根）：一键门禁，默认档 `mirror` / `tests` / `lint` / `shapes` / `global` / `kb`，
  `--full` 追加 `selftest` / `probes` / `corpus` / `coverage`；`--only <子串>` 选步，`--serial` 串行，`--strict` WARN 当失败。
- **副本陈旧守卫**：`tests/run_tests.py` 启动时先跑 `sync_mlogagent.py --mirror all --check`，发现 `mindustry-blueprint/tools`
  等副本与母本不一致就**拒绝运行**（`refusing to run: the analyzers under test would be the stale COPY`）——
  否则整套测试会「绿着但测的是旧代码」；`--no-mirror-check` 可跳。
- `tools/sync_mlogagent.py`：`--mirror skill|bp|install|all`、`--check`、`--global`（用户级 `~/.dsh/skills/mlog-agentskill`），
  三处仓库内副本各带 `MANIFEST.sha256`（`tests/run_tests.py` 的 `MIRROR_IGNORE` 已含它）。
- 规矩：`tests/expected.json` 只能由 `--write` 生成；改完 `tools/*.py` 必须先 mirror 再跑 tests。

## §19 第六轮四项工作流改进（2026-10-26）

| 项 | 交付 |
|---|---|
| Finding 带 rule id | `tools/rule_ids.py`（最长 `msg` 子串 → 规则 id）；`mlogcheck` 的 finding 带 `rid`；`check --rid` 打印；4 条原本无 id 的检查补了 `rules/*.json` |
| sweep 增量缓存 | `_corpus_sweep.py` 加 `--cache/--no-cache`（按存档 mtime+size 复用 worker 结果）；热跑 273.4 s 落在合并/写 md 段，未 profile |
| 运行期探针 | `tests/probes/run_probes.py` + `manifest.json`，起步 8 条 status 探针（断言 duration / hasEffect），退出码 3 = 无法运行（无 JRE/jar） |
| 一体化发布 | `out/_release.py`：gate → sync_public → 个人串扫描 → 公开仓 tests → commit/push（6 次重试）→ `git ls-files` 打 zip → GitHub release/asset/tag/HEAD 校验 |

踩坑：`out/_release.py` 里 `global REPO` 必须写在 `main()` 第一行，否则 `SyntaxError: name 'REPO' is used prior to global declaration`。
当轮 `gate.py --full` **7/7 passed in 55.6 s**，KB 5554 chunks / 61 files；提交 `a749758`（rule id）、`24fc0e8`（probes 步）。

## §20 外部语料（一）：GitHub 蓝图包（2026-10-26）

- `tools/corpus/fetch_schematics.py`：GitHub tree API + raw 8 线程，7 个仓库 → 833 个 `.msch` / 2.39 MB / 68.3 s（1 重复载荷、2 坏文件）。
  网络实测：`raw.githubusercontent` 0.3–0.7 s、`api.github.com` 0.6 s、`cdn.jsdelivr.net` 16–20 s、
  `codeload .../zip/refs/heads/master` 对 main 分支 404 → 走 tree API + raw 最稳。
- `tools/corpus/classify_schematics.py`：`msch.py` 解码 → 按代码 sha1 去重 → `_procs/<sha16>.mlog` + `_meta.json`；
  **1,078 个去重程序 / 388,263 行**（中位 89、最长 999；micro 883 / logic 143 / hyper 52；1,045 带链接；82 个程序跨多蓝图）。
- `tools/corpus/check_corpus.py`：逐程序 `mlogcheck.analyse(lines, links=declared)`，619 条命中 / 22.3 s；36 条规则只有 11 条开火。
  `link-name-not-bound` 413 条 = **84 条/34 程序真断链**（方块在蓝图里但没连到这个处理器）+ **329 条/92 程序「像链接名的普通变量」**
  （如 `jump 43 equal stop1 false`）→ 后果判读正确、文案 over-claim，0 条有害误报。
- 提交 `d56f40b`；`.gitignore` 第 38 行加 `/logic-corpus/`；报告 `22-web-corpus.md`。

## §21 外部语料（二）：mindustry.top 站点地图（2026-10-26）

- 真 API 是 `https://api.mindustry.top/maps/list`（不是 `/api/maps/list`），只有 `begin`/`search` 两参数，每页 15 条；
  **限流极狠**：连发即 `HTTP 400 Too many requests` → 必须 10–30 s 退避；`.msav` 下载走 IPFS（常 20 s 超时）。
- 抓取：search 词 逻辑/塔防/处理器/logic 累计 67 个 id，落盘 9 个 `.msav`（509,265 B）→ `map_logic.read_save()`
  → **349 个去重程序 / 15,131 行**（中位 30；world-processor 335 / micro 14；带链接仅 75）。
- `check_corpus.py --procs _maps_procs`：835 条命中 / 1.2 s，密度 2.39 条/程序（本地存档 0.87、蓝图包 0.57）；
  `link-name-not-bound` 698 条 = 38 条「方块在本地图但没连到此处理器」+ 660 条「方块类型本地图没有」+ **0 条变量形误报**。
- 工具 `tools/corpus/crawl_maps.py`（限流退避 + 可重入）、`extract_maps.py`；提交 `c9e819e`；报告 `23-map-corpus.md`。
  坑：`map_site.download()` 必须传 `Path`（传 `str` 报 `AttributeError: 'str' object has no attribute 'parent'`）。

## §22 外部语料（三）：Anon-deisu 大仓库（2026-10-26）

- `Anon-deisu/Mindustry-schematic-storage`：17,564 个 `.msch` / 216 MB。**不放工作区**（OneDrive 同步 churn）
  → `C:/Users/lliary/mlog-corpus/`（git 之外）。
- `git clone --depth 1` 失败（`RPC failed; curl 28 Recv failure` / `expected flush after ref listing`）；
  改用 `curl -L codeload.github.com/.../tar.gz/refs/heads/main` → 203 MB / 13 s（约 15 MB/s）。
- `classify_schematics.py --src <解包目录> --dest ...` → **44,241 个去重程序**（后续所有语料统计的分母）。

## §23 语料的三件价值（2026-10-27，用户「这些语料还有什么价值」→ 只做 1/2/4）

1. **指令覆盖率审计**：`tools/corpus/instr_coverage.py`（规范表取 `tools/instr_semantics.json`：53 条指令 + 45 条 op）。
   全量 44,241 程序 / 2,967 万条语句：**53 条指令只有 `clientdata`、`localeprint` 零覆盖，op 只有 `acos` 零覆盖**；
   `draw` 出现 16 种子命令、占全部语句 **81.46%**（像素画统治语料，`drawflush` 15.02%、`jump` 0.76%）；
   语料里不认识的 token 只有 25 个且全部 ≤15 次。两个陷阱：语句可用 `;` 连接；语料里有乱码 token → 非标识符首 token 记 junk。
2. **世界符号清单**：`tools/mlog_needs.py`（`--json/--md/--brief`）输出 sensors/ubind/ucontrol/ulocate/radar/links/globals/atoms；
   地图 349 程序 1.86 s：sensors 54 种（`@x` 373、`@y` 373、`@cryofluid` 333…）、blocks 376 种、globals 13、atoms 218。
   Anon 全量因 `programs_detail` 累积疑似挂死 → 只能抽样（`--no-detail`）。
3. **golden 正例 + 回归基线**：`tests/run_tests.py` 新增 `check_rid` / `check_nolinks` 两种 digest（后者用 `links=[]`，
   才是 `check_corpus` 的真实语义）；用例 `index-only-summary.mlog`、`link-unbound-fragment.mlog`；
   `check_corpus.py` 加 `--stride/--limit/--fail-on-errors`，`gate.py --full` 新增 `corpus` 步（stride 37 抽 400 程序，约 10 s）。

## §24 第 5 批：零覆盖指令探针 · 覆盖率关 · 链接名分级 · v1.0.6（2026-10-27）

- 零覆盖集合变成**签过字的基线**：`tests/corpus-coverage-baseline.json`（18 条），`gate.py --full` 的 `coverage` 步用同一批样本
  跑 `instr_coverage.py --limit 400 --baseline ...`——往 `instr_semantics.json` 加一行、或样本里丢一条指令，集合就变，必须有人重录基线。
- 链接名分级：`link-name-not-bound` 拆出「片段」形态（0 链接 + >200 语句的裁剪片段 → INFO `link-name-unbound-fragment`），
  另有 `link-shaped-variable` 描述「像链接名的普通变量」（外部语料 329 条那一类）。
- 发布 **v1.0.6**（公开仓 + release asset），流程沿用 `out/_release.py`。

## §25 语句解析 fail-open 修复 + `tests/shapes/`（2026-10-27）

- 三处整行锚定正则在语句尾部追加惰性 token 时**静默失配**（`jump` / `read`-`write` / `ulocate`）→ 改为 tokenize 后按字段取值。
- 新增 `tests/shapes/run_shapes.py`：7 种形状 × 4 种变体（追加 1/2/5 个惰性 token 与行尾注释）共 28 条，断言「规则仍必须开火」；
  负向自证 `--module out/_oldchk/mlogcheck_head.py`（有界正则版）应 12 条 FAIL，实测一致。
- 进 gate（`shapes` 步，0.1 s）；同批把 `arity-is-not-effective-params` 转 **SUPPRESSED**（它描述的不是可检的性质）。
- 量化：同批 400 程序抽样 115 findings，规则分布与改前完全一致（长行在真实代码里几乎不存在）。

## §26 §27（原文丢失，仅有结论）

这两个编号的逐节内容在截断中丢失；据会话记录，主题是上面的 fail-open 修复、`arity` 规则转 SUPPRESSED、
以及发布 v1.0.7 前的准备。数字已在 §25 与 §28.5 保留。**不要引用本节的编号做精确回指。**

## §28 gate.py --full 44 s → 15 s（2026-10-27，用户 m04240「压一下耗时」）

- `tests/probes/run_probes.py`：抽出 `run_one()`，每条探针一个 `Server`（一个 JVM），`ThreadPoolExecutor` 并发（`--jobs`，默认 min(8,CPU)）→ 13 条探针 41 s → 9.6 s。
- `tools/mschgen.py`：`_selftest_file()` 提成 module 级（可 pickle），`selftest(jobs=None)` 进程池分片 420 个蓝图；
  `Blueprint` 新增 `deflate_level`（默认 9），自检的两次验证重建传 1。
- 真凶：自检 89% 时间在 `zlib.compress(level=9)`（level 9 = 0.200 s/MB、6 = 0.055、1 = 0.008）；纯进程池只值 1.36x
  （27.4 → 20.1 s）——deflate 9 吃内存带宽，加核没用。顺序应是「先砍工作，再并行」。
- 等价性：自检输出逐字相同（430/430、204 ok/226 skip）；生成路径字节相同（164 B = 164 B）；tests 41/41；`gate.py --full` **14.8 s**。

### 28.5 发布 v1.0.7（2026-10-27，用户「push 然后realease」）

- 公开仓：remote main **64f5b97**（tree d491cbbc，与本地 out/_public 树逐字节一致），tag **v1.0.7** → 64f5b97，
  release https://github.com/EnernalIliary/mlog-agentskill/releases/tag/v1.0.7 ，
  asset **_release_v1.0.7.zip** **894,266 B / 221 entries**，sha256 ee120977e6fcb11062cf5c80684c2da53a2e2c4423e492848465452ef8cbbb8a，
  通过 api 下载回来与本地 zip **逐字节相同**。正文 out/_release_v1.0.7_body.md（2043 字符，5 节）。
- 内容 = 语句解析 fail-open 修复（jump / read-write / ulocate 三处改 tokenize）、tests/shapes/ 不变量测试、
  arity-is-not-effective-params 转 SUPPRESSED、gate.py --full 44 s → 15 s。

**【重要的新路径：github.com:443 整段不通时怎么推】** 发版时 git push 连续 6 次失败
（Failed to connect to github.com port 443 / Recv failure: Connection was reset），
而 api.github.com:443 一直 200（curl 20 s 超时、DNS 只有 20.205.243.166、换 140.82.112.3 一样超时、无代理配置）
→ **web 主机被墙、api 主机通**。解法是 out/_push_api.py：
1) git credential fill 取 token；2) GET /git/ref/heads/main 拿远端 base；
3) git -c core.quotepath=false -C out/_public diff --name-status base HEAD 列变更
（**必须关 quotepath**，否则中文路径被引号包住，读文件报 OSError: Invalid argument；
subprocess 还要 encoding='utf-8'，否则 GBK 解码炸）；4) 逐个 POST /git/blobs（base64）；
5) POST /git/trees（base_tree + 变更项）；6) POST /git/commits（parent = 远端 base）；
7) PATCH /git/refs/heads/main。远端拿到的 tree 与本地 HEAD 的 tree 完全相同（只是 commit sha 不同），
之后 git -C out/_public fetch origin main && reset --hard origin/main 对齐本地（网络恢复后 fetch 就通了）。
发布/上传走 uploads.github.com（302，可用）与 api.github.com，所以只卡 git 那一条路。
uploads.github.com / objects.githubusercontent.com 都通；asset 下载用 api 时要 curl -L（否则 0 字节）。

## §29 文档签名机检 + radar 没有数量参数（2026-10-28，用户 m04462 / m04508）

### 29.1 交付
- tests/docsig/run_docsig.py（新，进 gate 默认档）：文档签名 ↔ tools/instr_semantics.json 四项机检
  （signature 槽位数 / slot 逐槽名字 / example mlog 块参数数 / table 参数表有序子序列），
  --self-test 合成文档自证四项都会开火，--root 可指向反证目录。
- rules/radar-takes-no-count.json（新，kind=semantics，WARN）+ tools/mlogcheck.py 检查：
  radar/uradar 第 6 槽常数 > 1 即报。fixture tests/cases/radar-count-{misuse,ok}.mlog。
- tests/probes/manifest.json + expect_radar 能力 + 3 条探针（单输出 / 第 6 槽写 5 仍是方向 / uradar 6 参整体错位）。
- gate.py：shapes 之后加 docsig 步（默认档现在 7 步，--full 11 步）。
- 文档修正：Logic-Docs-v1.1.0.md 4 处签名 + 4 张表（getblock / setblock / weathersense / spawnwave）；
  蓝图逻辑模式库.md radar/uradar 章节（7 槽、无数量列、30 tick 缓存）；两份 tracked PATTERNS.md 重新生成；
  tools/instr_semantics.json spawnwave note；docs/断言表.md +L1-27/L2-17；docs/验证记录.md +本日整节；
  README / tools/README 补 docsig 步；规则条数 25/36/38 → 39。
- 报告 out/takeover-20261024/26-docsig.md。

### 29.2 量化
| 项 | 值 |
|---|---|
| 文档机检 | 4 文件 / 43 条签名 / 2,243 条示例 / 2 张表；反证目录报 12+ 条 |
| 修掉的错序签名 | 4 处（数目对、顺序错——槽位数检查抓不到，靠 slot 检查） |
| 规则 | 36 → 39（radar-takes-no-count + 前一轮两条），lint 39/39、0 problem |
| 探针 | 13 → 16，全跑 16/16 |
| golden | 40 → 43 digest（新增 2 条 check_rid） |
| gate | --full **11/11 passed in 21.1 s**；KB 5686 chunks / 61 files |

### 29.3 一条要记住的原理
**mlog 文本 token 序 = Java 字段声明序**，与 build(LAssembler) 传参序无关
（LStatement.write() 走 LogicIO 按字段序列化，LStatements.java 零 override）。
证据：out/_sig5_probe.py 反射 read/sensor/getblock/setblock/weathersense 的字段名与值。
⇒ 语义表 spawnwave=[x,y,natural] 是对的，错的是文档；上一轮「语义表错」的结论已作废。
盲区：radar 那种「槽位数没错、语义错」的文档错误没有机械检测器，只能靠 probes + 玩家验收。

### 29.4 候选
1. docsig 的 example 检查只看 token 数，不看语义（radar … 5 u 这种示例照样漏）→ 可加「已知坏形状」名单。
2. PATTERNS.md 生成未脚本化（现在 Copy-Item + fix_skill_links.py 两步手动）→ 收进 tools/。
3. .dsh/skills/*/{BLUEPRINT-ANALYSIS,REFERENCE}.md 的链接深度是这轮才发现的（../ 应为 ../../../），
   其它安装副本可能同类问题 → fix_skill_links.py 可做成 gate 一步。
4. dist/ 与 out/_publish/ 里的旧文档仍是错版（构建产物，下次构建刷新），发布前应重生成。
5. v1.0.8 未授权发布（本轮改动尚未进公开仓）。

### 29.5 一条工具教训（2026-10-28 事故）
read 工具对长文件**只返回前一段**（本次 1,021 行的 handover 只回 514 行，12,244 行的 Logic-Docs 只回 1,225 行），
而 write 是**整文件替换**——「read（以为读全了）→ 改 → write」会静默截断文件。
本轮就是这样两次丢了 handover 的 §18–§28 与 §28.5/§29（§18–§28 已按会话摘要重建，带重建声明）。
**规矩**：改长文件前先 read 到 offset+limit 越过 totalLines 确认拿到全部；或者只做 edit（局部替换）不 write。

## §30 2026-10-28 门禁自身的八个漏洞（交接轮之后）

### 30.1 交付
| 文件 | 改动 |
|---|---|
| `tests/ruleids/run_ruleids.py`（新） | dead-rule / unknown-rid / drift 三条断言；`--write` 写基线 |
| `tests/rule-coverage.json`（新） | rid → [fixture] 基线 |
| `tests/run_tests.py` | `missing` 计入 `bad`（删 golden 不再绿灯） |
| `tools/sync_mlogagent.py` | `--check` 缺 payload 文件 return 1；新增 `--allow-absent` |
| `tests/docsig/run_docsig.py` | 新增 `derived()`：全部 PATTERNS.md / BLUEPRINT-ANALYSIS.md 与源逐行比对（链接深度归一化） |
| `gate.py` | 新增 `ruleids` 步；`--strict` 把 SKIP 算失败；stream 分支超时 → FAIL；`kb_sources()` 加 `rules/*.json` + `tests/cases/*.mlog`；docstring 耗时改实测 |
| `rules/README.md` | 字段表加 `surface`；写明「每条规则必须有正例 fixture」 |
| `rules/*.json` | 修 `undefined-var-read` 陈旧 msg_any；`unary-op-extra-operand` → SUPPRESSED；`cross-processor-slot-undeclared` 加 surface；新增 `ulocate-outbuild-discarded`、`ulocate-outxy-discarded` |
| `tests/cases/*.mlog` | 新增 12 个正例 fixture |
| `README.md` / `docs/验证记录.md` | 步数与数字同步；验证记录追加「门禁自身的八个漏洞」一节 |

### 30.2 量化
41 条规则（SUPPRESSED 8 / INFO 14 / WARN 10 / ERR 9），32 条参与 rid 断言；32 个 rid 在 38 个 fixture 上点火；
43 golden；16 探针；28 形状；docsig 4 文件 + 4 派生副本；KB 5697 chunks / 61 files；
默认门禁 **8/8 in 5.5 s**，`--full` **12/12 in 20.8-24.5 s**。

### 30.3 复跑
`python tests/run_tests.py` 43/43；`python tools/rule_capture.py lint` 41 条 0 problem；
`python tests/ruleids/run_ruleids.py` 0 problem；`python tests/docsig/run_docsig.py` EXIT 0；
`python gate.py --full` 12/12。

### 30.4 教训
这七条代码级漏洞是同一个形状：**空集上恒真**（没有 fixture 就没有死规则，没有副本就没有 MISMATCH，
没有语料 corpus 就是 SKIP，没有 golden 条目就没有 STALE）。写断言时先问「它在干净 checkout 上会不会自动通过」。
另：`rule_capture.py lint` 只证明反例不命中，正例必须另有断言——这就是 `run_ruleids.py` 存在的唯一理由。

### 30.5 下一轮候选
1. 蓝图级（`surface: blueprint`）规则补 fixture：需要造 `.msch` 场景，目前只有 note 提示。
2. 12 个新 fixture 是否进 `expected.json`（现在只靠 ruleids，没有逐字节 golden）。
3. `docs/验证记录.md` 已 394 行，考虑按季度拆文件（否则每次 read 都要分页）。
4. `dist/` 下两份 2026-10-18 的旧导出仍含过期数字，未再生成。
5. v1.0.8 发布未授权；`out/_sync_public.py` 的 NEW_GLOBS 本轮已补 `tests/ruleids/*` 与 `tests/rule-coverage.json`（原先只含 tests/docsig、tests/shapes）。
---

# §31 绑定单位合法性（2026-10-29，m06773）

## 31.1 起因与结论

用户 m06773 要求把「绑定单位合法」定义清楚（1 未被其它逻辑控制：`@controller` = `@unit` 或 `@this`；2 没有死亡）。**结论（本仓库口径）**：`@unit` 合法 ⇔ 没死（`@dead` 为 1 同时覆盖「已死」与「根本没绑到」）**且** `@controller` 是 `@unit` 自身（没有逻辑处理器控制它）或 `@this`（本处理器在控制）。

canonical 片段（四条探针逐态验证）：

```mlog
ubind @flare
sensor ctrl @unit @controller
sensor dd @unit @dead
set ok 0
jump 9 equal dd 1
jump 8 equal ctrl @unit
jump 8 equal ctrl @this
jump 9 always
set ok 1
print ok
end
```

## 31.2 四态真 v160.7 实测

| 状态 | `@controller` | `@dead` | `@controlled` | ok |
|---|---|---|---|---|
| 裸单位（普通 AI） | 单位自身（== `@unit`） | 0 | 0 | 1 |
| 本处理器在控（`la.controller = b`） | 本处理器建筑（== `@this`） | 0 | 1 | 1 |
| 别的处理器在控 | 那个 `LogicBuild` | 0 | 1 | 0 |
| 已死（`u.kill()`）/ 没绑到（`ubind @dagger`） | null | 1 | 0 / null | 0 |

源码：`UnitComp.java:319`（控制者不是 LogicAI 就返回单位自身）、`:277`（dead）、`:296-300`（controlled 0/1/2/3）、`LExecutor.java:685-688`（null 目标 `@dead`=1）、`:322-340`（checkLogicAI 通过即改写 `la.controller` = 抢占）、`:344`（`logicUnitControl` 开关）、`PlayerComp.java:174` / `ai/types/CommandAI.java:107`（两类 `isLogicControllable()==false`）。
抢占实测 `out/_unit_probe13.py`：`BEFORE owner=Building#213[4,4]` → 6 条 `ucontrol move` 后 `AFTER owner=Building#212[0,0]`。

## 31.3 交付清单（9 文件，+285/−11）

| 文件 | 改动 |
|---|---|
| `tools/mlogsim.py` | `run_mlog(..., setup_js=None)`：`STEP_JS` 在 `b.efficiency = 1;` 之后、主循环之前插 `%(setup)s`（程序已编译、单位已存在、第一条指令未跑，`b` = 本处理器建筑） |
| `tests/probes/run_probes.py` | 透传 `setup_js=p.get('setup_js')` |
| `tests/probes/manifest.json` | +4 条探针（共 **20**）：`unit-legal-fresh/dead/self/other-v160` |
| `蓝图逻辑模式库.md` | §4.1 新增「绑定单位合法性：一条检查管住四种状态」；修两处过时警告（`@controller` 曾被说成「不在 sensor 属性总表里、未文档化」，实际 v160.7 `LAccess` 77 项含它，S-18） |
| `mindustry-blueprint/PATTERNS.md`、`.dsh/skills/mindustry-blueprint/PATTERNS.md` | 派生副本重生成（`Copy-Item` + `python tools/fix_skill_links.py <skill dir>`） |
| `docs/断言表.md` | +L2-18..L2-21（表头 85/88 → **89/92**）；L2-07 注文改写（原文「dead=1 不能判死」易被读成「不能用 `@dead`」，实际正相反） |
| `docs/验证记录.md` | 结果总表 +4 行 PASS，文末新增整节 |
| `README.md` | `probes` 16 → **20** 个 JVM |

**教训**：本仓 `蓝图逻辑模式库.md` 是 **CRLF** 入库（`core.autocrlf=false`、无 `.gitattributes`），python 用 `newline="\n"` 写会把全文件变成 LF、diff 从 54 行炸成 4890 行 → 检测办法 `git diff --numstat --ignore-cr-at-eol`，修复办法重写成 CRLF。

## 31.4 复跑

`python gate.py --full` → **12/12 passed in 49.7 s**（mirror 0.5 / tests 3.9 / lint 0.3 / shapes 0.1 / docsig 0.3 / ruleids 0.2 / global 0.3 / selftest 38.5 / probes 43.7 / corpus 24.6 / coverage 7.1 / kb 0.4）；`tests/probes/run_probes.py unit-legal` 4/4；`run_docsig.py` 4 份副本全绿；KB 重建 **5703 chunks / 61 files**。

## 31.5 下轮候选

1. 把「合法性检查」做成静态规则（`ubind` 后直接 `ucontrol` 却既没查 `@dead` 也没查 `@controller`）——需要跨语句数据流，误报风险高，先不做。
2. `@controlled == 0` 与「`@controller == @unit`」的差异（玩家/命令控制）可以再补 1 条探针。
3. 语料侧统计：真实蓝图里有多少 `ucontrol` 前没做合法性检查（`C:/Users/lliary/mlog-corpus/anon-corpus/_procs`，44,241 程序）。
4. v1.0.8 发布（未授权）。
5. handover 自身仍是重建版（§26/§27 只有结论）。

## 31.6 原始文件

`Logic/`、`saves/`、`assetsraw/`、`Mindustry-Source/`、`Arc-Source/` 全程只读。
## §32 第 32 轮：docsig operand 检查 · 速查卡 · 三条 UNRUN 复跑（2026-10-29）

授权：用户 m07083「1.可以 2.跑一下 3.允许 4.做一下 5.最后清理掉 / p1 p5 p2 / p3可以最后交给我判读」→ 本轮只做 P1 → P5 → P2。完整报告 `out/takeover-20261024/30-p1p5p2.md`。

### 32.1 交付（10 项）

| # | 文件 | 改动 |
|---|------|------|
| 1 | `tests/docsig/run_docsig.py` | 第 5 项检查 `operand`（枚举槽名字必须真实存在）；第 6 项检查 `refs`（速查卡引用的 `L\d-\d\d` 必须在断言表存在）；selftest 5 类 |
| 2 | `Logic-Docs-v1.1.0.md` | 6 处真错：`sensor @damage`、`status <apply|clear>` 全节、`ulocate locate`、`@velX/@velY` |
| 3 | `蓝图层逐类精讲.md` + 两份派生 `BLUEPRINT-ANALYSIS.md` | `@velX`→`@velocityX`，派生同步 0 漂移 |
| 4 | `docs/速查卡.md`（新，1969 字符） | 一页六节，每节挂断言 id |
| 5 | `docs/断言表.md` | 新增 L2-22..L2-25；表头 **97 条断言 / 100 行结果**；待复跑 4→1（L4-03）；修回 64 个 `@@BT@@` 占位符 |
| 6 | `docs/验证记录.md` | L2-22..L2-25 + L1-19/L2-08/L2-14 转 PASS；合计 **PASS 88** |
| 7 | `tests/probes/run_probes.py` | `units` 字段 + `ticks` 模式 + setup_js 单行拼接警告 |
| 8 | `tests/probes/manifest.json` | 20 → **26 条**（4 条 P2 + 2 条控制租约） |
| 9 | `tools/mlogsim.py` | `LINK_ALIASES` 加 `container` / `turret` |
| 10 | `tools/README.md` | docsig 段四份→五份文档 + 第 5/6 项检查 |

### 32.2 量化

- docsig operand 一次抓出 **6 处文档真错**（全部 jar 反射实测）：`@damage` 读 null、`status apply/clear` 都编译成 `clear=false`（=施加）、`ulocate locate` → `NoopI{}`（静默不执行）、`@velX/@velY` 不存在（真名 `@velocityX/@velocityY`）。
- L2-25 控制租约：600 tick（`LogicAI.java:18`），两条 ticks 探针（400 tick 持租约 / 700 tick 到期）实测 2/2。
- P2 三条转 PASS：L1-19 fortress `@range`=29.5；L2-08 6 格拿到 10 / 8 格 0（门槛 45+size2×4=53 world=6.625 格）；L2-14 `control shoot turret1 20 20 1` → `@shootX/@shootY`=20/20。L4-03 保留 UNRUN（v146 存档 + mindcode 对拍，成本高于本轮）。
- 断言表 97 条 / 100 行结果；验证记录 PASS 88；探针 26 条；tests 43/43。

### 32.3 复跑

```
python tests/docsig/run_docsig.py   → 5 file(s) / 991 operand line(s) / 13 cited id(s) / OK  EXIT=0
python tests/run_tests.py           → 43/43 passed
python tests/probes/run_probes.py   → 26/26 passed（gate probes 步 32.4 s）
python tools/sync_mlogagent.py --mirror all --check → skill/bp/install 各 21 file(s) in sync  EXIT=0
python gate.py --full               → 12/12 passed in 37.9s
```

KB 必须先重建（`HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1` → `{"chunks": 5709, "files": 61}`），否则 gate 的 kb 步报 stale（首次 11/12 的唯一 WARN）。

### 32.4 下轮候选

1. **P4（用户已允许）**：`link-name-not-bound` 两级化 —— 真断链 WARN / 链接形变量 INFO。语料证据：蓝图包 413 条 = 84 条真断链 + 329 条变量形；地图侧 698 条全是真问题。
2. **P3（判读交用户）**：规则精度全量样本包（三批语料命中按规则归类 + TP/FP 抽样）。
3. **P8**：清理 `out/` 草稿，给 8 条旧 untracked 定性。
4. `control shootp`（吃单位对象）未单独实测；itemTake 的 1.5 s 冷却是否只作用于第一次待更细 tick 网格验证。

### 32.5 原始文件

`Logic/`、`saves/`、`assetsraw/`、`Mindustry-Source/`、`Arc-Source/` 全程只读；本轮写操作只在 `tools/`、`docs/`、`tests/`、根目录文档与两份派生副本。
## §33 第 33 轮：规则精度判读包（P3）· out/ 清理（P8）（2026-10-29）

报告：`out/takeover-20261024/31-p3p8.md`；清理清单：`out/_crawl/cleanup-20261029.md`。

### 33.1 交付

| 项 | 内容 |
|---|---|
| `tools/corpus/precision_sheet.py`（新，224 行） | 规则命中 → 可判读样本表：每条规则 6 条样本（各来自不同程序）+ 机器旁证（`occ`/`assigned`/`in_links`）+ 规则自述；`--verdicts` 回填 TP/FP/mixed；`--stride/--limit/--jobs` 支持大语料抽样 |
| `out/_crawl/precision-{blueprint,maps,anon}.md/.json` | 三批语料的判读表（1078 / 349 / 5531 程序） |
| `out/_crawl/precision-INDEX.md` + `precision-verdicts.json` | 规则 × 语料并排索引 + 20 条规则的空判读模板 |
| `tools/README.md` | §7 外部语料段加两条命令（含 4 万程序抽样 5.5k / 67 s 的实测） |
| `out/_crawl/cleanup-20261029.md` | out/ 清理与 8 条未跟踪文件定性 |

### 33.2 量化

- 判读表覆盖 **20 条规则**（三批语料并集），命中 619 / 835 / 3483 条，开火规则 14 / 8 / 19 条。
- Anon 抽样（44,241 → 5,531，stride 8，jobs 12）67.3 s，0 分析异常；`noop-means-version-drift` 1418 条只落在 5 个程序 → 按条计数会误导，索引里单列。
- 清理：删 136 MB 会话转储 + 16.7 MB sweep 分片 + 7.5 MB sim 临时目录（部分被常驻 java 占用）+ 69 个一次性脚本；保留 1.47 GB 离线复跑资产（模型缓存 / Python 依赖 / JRE）。

### 33.3 复跑

```
python gate.py --full → 12/12 passed in 39.7s
python tools/kb.py build → {"chunks": 5709, "files": 61}
```

提交：`0138938`（docsig operand + 速查卡 + 3 条 UNRUN 探针）、`aef9780`（precision_sheet + README）。

### 33.4 下轮候选

1. 用户判读回填 `out/_crawl/precision-verdicts.json` → 用 `--verdicts` 重跑出带结论的判读表，再据此收紧判据（只许收紧或降级）。
2. `control shootp` 单独实测；itemTake 冷却的 tick 网格；`out/_sim/run-xawzsng3` 等 java 服务退出后删除。
3. 三批语料仍未进 gate（只有 400 程序冒烟）；若要进，需要把 `precision_sheet.py` 的关键断言（旁证计算）加 tests。

### 33.5 原始文件

`Logic/`、`saves/`、`assetsraw/`、`Mindustry-Source/`、`Arc-Source/` 全程只读。

## 34. 未赋值变量两条规则合并（ref m07644）

### 34.1 交付

| 文件 | 改动 |
| --- | --- |
| `tools/mlogcheck.py` | 槽位表 `_NON_NUM_SLOTS` / `_UCONTROL_SLOTS` / `_CONTROL_SLOTS` + `_slot_kinds()`；bool 槽 WARN→INFO；残余分支按槽位分 INFO/ERR；内存索引汇总 ERR→INFO |
| `tools/rule_ids.py` | 平票按 rid 字典序（原来取决于"该规则最长的那条 key"，宽规则会抢走窄规则的命中） |
| `tools/rule_seed.py` | 两个 SEED 条目合成一条，msg_any 三条子串 |
| `rules/undefined-var-read.json` | 重写为合并版（semantics / ERR / ref m07644 / match.sevs 三档 / 三条 msg_any） |
| `rules/undefined-var-is-not-automatically-an-error.json` | 删除 |
| `rules/bool-param-constantly-zero.json` | WARN→INFO，`match.sevs` 同步（只改 severity 不改 match 会让规则永远数不到） |
| `rules/README.md` | 改动表加一行；2026-10-19 审计表下注明第 2 行已合并（不改写历史） |
| `tests/cases/undefined-var-num-slot.mlog` + `tests/run_tests.py` | 新增 case：`op add t zz 1` 的 zz 在 num 槽 → INFO |
| `tests/expected.json` / `tests/rule-coverage.json` | `--write` 重生成（44 digest / 31 rid over 39 case） |

判据：**槽位类型**。num（`numi()/numf()`）与 bool（`bool()`）把 null 读成 0/false → INFO；obj（链接/单位/内容目标）收到 null 对象，指令静默跳过或把 null 写下去 → **ERR**。未列出的槽位默认 num（保守方向：只有证明是 obj 才升级）。常数比较（`tools/mlogcheck.py:1361-1367`，归 `constant-null-guard`）与 surplus 参数仍 WARN，不并入。

### 34.2 量化（旧分级按消息文本反推，脚本 `out/_m15.py`）

| 语料 | 程序 | 命中 | 旧 ERR/WARN/INFO | 新 ERR/WARN/INFO |
| --- | --- | --- | --- | --- |
| blueprint | 1078 | 77 | 39 / 13 / 25 | 6 / 9 / 62 |
| maps | 349 | 10 | 8 / 0 / 2 | 2 / 0 / 8 |
| anon stride 16 | 2766 | 271 | 158 / 20 / 93 | 46 / 17 / 208 |
| 合计 | 4193 | 358 | 205 / 33 / 120 | 54 / 26 / 278 |

ERR 205 → 54（−73.7%）；INFO 120 → 278（+132%）。剩 54 条 ERR 是真 obj 槽。
坑：旧分析器不能单独拷出来跑（靠 `__file__` 找 `tools/*.json`，拷到 `out/` 下就退化，得到 maps old=2328 findings 的荒谬数字）→ 只能"新版跑一遍、按消息反推旧分级"。

### 34.3 复跑

- `python tools/rule_capture.py lint` → 40 rule(s): 40 checked, 0 unguarded, 0 problem(s)
- `python tests/ruleids/run_ruleids.py` → 40 rule(s) (31 active), 31 rid(s) fire on 39 fixture(s), 0 problem(s)
- `python tests/run_tests.py` → 44/44 passed
- `python tools/sync_mlogagent.py --mirror all` 三处 21 file(s)；`--global` 已装 23 file(s)（否则 gate 的 global 步 STALE）
- `python tools/kb.py build` → `{"chunks": 5739, "files": 61}`
- `python gate.py --full` → **12/12 passed in 37.9s**（mirror 0.4 / tests 4.5 / lint 0.3 / shapes 0.2 / docsig 0.4 / ruleids 0.3 / global 0.3 / selftest 23.1 / probes 31.1 / corpus 19.7 / coverage 1.7 / kb 0.1）
- 第一次 gate 是 10/12：ruleids drift（加了 fixture 没重生成 rule-coverage.json）+ global STALE（改了 mlogcheck.py / rule_ids.py 没 `--global`）——这两步在改完工具后必须补。

### 34.4 下一轮候选

1. `out/_crawl/precision-*.md` 三张判读表是合并前快照，规则 id 已变 → 用 `precision_sheet.py` 重跑。
2. `control shootp` 的 obj 槽实测（`docs/断言表.md` L2-14 的 I 级尾巴）。
3. 槽位表覆盖度无自动校验 → 加 shapes 测试：每条指令每个槽位都必须显式落在某张表里或标 num。
4. obj 槽 ERR 的运行期后果只有源码依据 → 至少给 `ucontrol itemTake zz`、`sensor x zz @x` 各加一条 v160.7 探针。


## §35 第 35 轮：游戏内逻辑写入服务 P1（2026-10-29，用户 m07868 / m07888 / m07905）

用户要的新产物不是导出、不是分析报告，而是「代替自己写代码那一层」的游戏内服务。
定稿方案 = 三层 + 一份契约：游戏内 Rhino 模组 `LogicWriter/` → 本地 sidecar `tools/logicd.py`
（意图 → mlog → 全量静态检查 → 游戏 config 载荷）→ 模组 `b.configure(bytes)` 走原版通道写入。

### 35.1 交付

| 文件 | 说明 |
|---|---|
| `tools/logicd.py` | 四端点 `/health` `/capabilities` `/analyze` `/compose`；六模板 patrol / item-threshold / radar-fire / memory-table / timer-flush / counter；`analyse()` 用 `mlogcheck.prepare()` 算语句槽位（标签不算语句） |
| `tests/logicd/run_logicd_tests.py` | 两半：协议 13 项（无 JRE）+ 真 v160.7 写入 6 项（缺 jar → exit 3 = SKIP） |
| `LogicWriter/` | `mod.hjson`（hidden:true）、`scripts/main.js`（面板/HTTP/写入/撤销/7 个控制台函数）、`README.md` |
| `docs/逻辑写入服务-设计.md` | 9 节设计文档（含失败模式表与分期验收） |
| `gate.py` | `--full` 新增 `logicd` 步（第 13 步，与 probes 并发） |
| `README.md` / `tools/README.md` | 快速开始、`--full` 五步、目录表、文件分层第 1 条、sidecar 整节 |

### 35.2 量化

- 协议 13 项全过；六模板在真执行器里 `b.configure()` 后 `b.code` 逐字节相同、首个指令类分别是
  UnitBindI / SenseI / RadarI / WriteI / WaitI / ReadI。
- 契约关键决定：`ok` == 没有 ERR（ERR 拒绝写入）；`line` 是行号、`stmt` 是语句槽位；
  `bytes_b64` 就是 `LogicBlock.compress()` 的格式（`tools/msch.py:447`），所以联机同步白捡。
- 踩到的坑：mlog 标签是 `name:`（`LParser.java:117-125`），不是 `label name`；`instr_semantics.json`
  的 `ops` 是 dict 不是 `{subcommands: [...]}`。

### 35.3 复跑

```
python tests/logicd/run_logicd_tests.py   -> 13 checks + 6 templates, EXIT=0
python tools/kb.py build                  -> {"chunks": 5857, "files": 62}
python gate.py --full                     -> 13/13 passed in 34.7s
```

### 35.4 下一轮候选

1. P2 快检进游戏（`rules.generated.js` + gate 校验重生成一致）。
2. P3 写入层（模板 10 个 + 快照落盘 + 撤销逐字节还原）。
3. P4 意图层（LLM 输出必须过同一道 check 门禁）。
4. `control shootp` 的单位对象分支仍未实测。
5. 面板 UI / F4 / 控制台函数只能在真游戏里点，仍属未验证。


## §36 第 36 轮：逻辑写入服务 P2 —— 快检进游戏（2026-10-29，用户 m08110「好的就按照这个顺序，写详细方案然后归档。开始p2」）



### 36.1 交付



| 文件 | 说明 |

| --- | --- |

| `tools/rules_export.py` | 从 `instr_semantics.json` + `mlogcheck` 的 `LINK_SLOTS` 生成规则表；`--check` 防漂移 |

| `LogicWriter/scripts/rules.generated.js` | 生成物（5880 B，payload v1，不手改） |

| `LogicWriter/scripts/quickcheck.js` | 纯函数快检（ES5/Rhino），五条判据 |

| `tests/logicwriter/{harness.js,cases.json,run_quickcheck_tests.py}` | 14 用例 + require 契约 + 单向交叉验证，0.3 s |

| `gate.py` | 默认档新增 `quickcheck` 步 |

| `LogicWriter/scripts/main.js` | 面板加「本地快检」四行；控制台 `lwCheck()` / `lwScan()` |

| `docs/逻辑写入服务-规划.md` | 新增 §9 实施状态表（P1/P2 完成，P3–P5 未开始） |

| `README.md` / `tools/README.md` / `LogicWriter/README.md` | 三处文档同步 |



提交 `aec9f2a`（12 文件 +1591/−12）。报告 `36-logic-writer-p2.md`。



### 36.2 关键事实



* `instr_semantics.json` 的 `defs`/`uses` 是**参数索引**（param0 = token1），导出必须 +1，否则 `set message1 0` 声明不到变量、快检误报断链。

* `min_build` 高于 146 的只有 5 个（`format` 147、`select` 150、`bullet` 157、op `emod` 150、op `ushr` 150）；`LINK_SLOTS` 只有 9 条指令；`subcommands` 只有 `ucontrol`/`ulocate`/`draw`。

* 游戏只执行 `scripts/main.js`（`Mindustry-Source/core/src/mindustry/mod/Mods.java:809`），其余靠 `require()`（`Scripts.java:30-32`）。

* 真 v160.7 实测（`out/_q_reqprobe.py`，`Vars.mods.getScripts().runConsole('typeof require')`）：`typeof require` = `function`，顶层 `module` = `undefined`。

* 版本号 `Version.build`（`Mindustry-Source/core/src/mindustry/core/Version.java:20-24`），自定义构建 `-1` → 版本门不启用。

* 快检**只许少报**：测试用 `mlogcheck.analyse()` 做单向包含验证，快检说断链的行全量检查必须也这么说。



### 36.3 复跑



`python tests/logicwriter/run_quickcheck_tests.py` EXIT=0（drift in sync / require 契约 ok / 14 用例 / cross 3 例）；

`python gate.py --full` → **14/14 passed in 28.8 s**；KB `{"chunks": 5889, "files": 63}`；docsig OK。



### 36.4 下一轮候选



1. **P3 框选 + 区域快照**（用户已批准的路线图）：F7 框选 → 快照 JSON → 一句话 → 入队。字段复用 `tools/mlog_needs.py` 的分类 + `tools/map_logic.py` 的读法。

2. P4 队列 + 模型 + 门禁（`POST /jobs`、结构化输出、ERR 回灌重试 2 次、可选 200 tick 快跑）。

3. P5 多处理器写入 + 撤销落盘（`<dataDir>/logicwriter/undo/`）。

4. 面板/热键这一层没有机器验证（无头模拟器没界面），需要人上手一次。

5. `lwScan()` 的「100 处理器 < 1 s」没在真地图上量过。



### 36.5 原始文件



`Logic/`、`saves/`、`assetsraw/`、`Mindustry-Source/`、`Arc-Source/` 全程只读；工作树只剩 9 条用户原始文件的 `??`。



## 37. 真 Rhino 的 split(正则) 陷阱（2026-10-29，装模组前验证）

### 37.1 一句话
真 v160.7 的 Rhino 里 `String.prototype.split(带 + 量词的正则)` 等价于空匹配，会把整行拆成单字符；
`quickcheck.js` 的分词正是这一句 → 进游戏后对任何程序都报垃圾。node（V8）测不出来。已改为手写扫描，
并新增 `tests/logicwriter/run_rhino_parity.py`（同一批用例在真引擎里重跑比对）+ `gate.py` 的 `rhinoparity` 步。

### 37.2 证据（真 v160.7）
`"abc def".split(/\s+/)` → `["a","b","c","d","e","f"]`；`split(/ /)`、`split(/\s/)`、`split(/  /)`、`split(/X/)` 正常；
`/[ ]+/`、`/(?: )+/`、`new RegExp("[ ]+")`、`new RegExp("\\s+")` 全坏；连无匹配的 `/x+/` 也按字符切。`String(re)` 仍打印 `/\s+/`。

### 37.3 改动
| 文件 | 改动 |
| --- | --- |
| `LogicWriter/scripts/quickcheck.js` | 删 `RE_WS`/`RE_TRIM`/`RE_NAME`，改手写 `isWs`/`trim`/`tokenize`/`isIdent`；API 与五条判据不变 |
| `tests/logicwriter/run_rhino_parity.py`（新） | node vs 真 Rhino 逐键比对，exit 0/1/3（3=无 JRE，gate 记 SKIP） |
| `gate.py` | 新增 `rhinoparity` 步（2.9 s），排在 `quickcheck` 之后 |
| `LogicWriter/README.md`、`tools/README.md`、`README.md`、`docs/逻辑写入服务-规划.md` | 说明这条陷阱 + 新命令；规划 §9 的 P2 行加 rhinoparity |

### 37.4 产物
`out/_dist/LogicWriter.zip` 16,497 B / sha256 `CAD56E05B690DDC1D8D8381F57BA7C9EA8D22838500C7CDABB90698048E2E485` / 5 条目；
装到 `%APPDATA%\Mindustry\mods\LogicWriter\`（`Vars.java:342 modDirectory`），版本 0.2，控制台 `lwVersion()` 自检。

### 37.5 复跑
`run_quickcheck_tests.py` OK（14 用例）/ `run_rhino_parity.py` 14 case identical / KB `{"chunks": 5889, "files": 63}` /
`gate.py --full` **15/15 passed in 31.3s**。

### 37.6 下一轮候选
1. 真游戏 GUI 里点一遍面板（本轮只有无头引擎验证）。
2. P3：F7 框选 + 区域快照 JSON。
3. 快检的判据仍只覆盖五类；`rules.generated.js` 的 `defs` 索引转换（param0→token1）值得加一条断言测试。

## 38. v0.3 设置界面 + 改名 MlogAuxiliary（MAI）（2026-10-29）

38.1 交付：模组调试入口改为「设置 → Mlog辅助」（`Vars.ui.settings.addCategory`，`SettingsMenuDialog.java:329-330`），显示版本 / 构建 / 快检模块 / sidecar / 数据目录 / mods 目录 + 四个按钮；新增 `tests/mlogauxiliary/run_ui_smoke.py` 与 `gate.py` 的 `ui` 步；按用户 m08663/m08671 改名：目录 `MlogAuxiliary/`、id `mlog-auxiliary`、中文「Mlog辅助」、日志 `[mai]`、控制台 `lw*`->`mai*`、`LW_RULES/LW_QUICKCHECK` 改为 `MAI_*`、`tests/logicwriter` 改为 `tests/mlogauxiliary`、两份 docs 改名；旧 settings 键读一次迁移。

38.2 两个真 bug：①Rhino 里 "use strict" 下的块级函数声明**不提升** → 新函数必须放在 `try` 之前；②读回挂载写 `scope.get(k, scope)` 在真引擎抛 `Cannot find function get`，初始化在规则表之后**整个中止** → 改用 `Packages.rhino.ScriptableObject.getProperty`。这两类错误 node 侧全绿也发现不了，`ui` 步才抓得住。

38.3 复跑：`rules_export.py --check` in sync(53) / quickcheck 14 用例 / rhinoparity 14 case 相同 / ui smoke OK / KB 5891 chunks 63 files / `python gate.py --full` **16/16 in 41.0s**。

38.4 产物与安装：`out/_dist/MlogAuxiliary.zip` 19,992 B sha256 `1CBC488F...74A55FE`（5 条目全带顶层 `MlogAuxiliary/` 前缀，否则 `Mods.java:1070-1074` 会把 zip 根当模组根 → `[E] No main.js found`）；已目录式装进 `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary/`。游戏**便携数据目录**是 `<游戏目录>/saves/`，不是 `%APPDATA%/Mindustry`。

38.5 候选：①真界面像素/按钮仍要人看；②面板模板按钮只用默认参数，改参数走控制台；③旧 settings 键迁移无单测；④P3 框选 + 快照未开始。

## 39. v0.3.1 设置分类没出现 = Java 重载歧义（2026-10-29）

39.1 现象：v0.3 装进游戏后「设置」里没有「Mlog辅助」一栏，而 `last_log.txt` 只留一行
`[mai] settings category failed: InternalError: The choice of Java method arc.scene.ui.layout.Table.table ... is ambiguous`
—— 模组其它部分（规则表、12 个控制台函数）都正常。

39.2 根因（真 v160.7 逐形状实测，`out/_uip2.py`）：`t.table(function)` 在**方法解析阶段**就抛 InternalError；
`row/defaults` 直接 RESOLVED；`add/label/labelWrap/button/field/check/image/pane` 以及 Cell 的
`pad/left/width/colspan` 都能解析（headless 下只是 skin 为 null 的运行期 NPE）；`t.scrollPane(fn)` 根本不存在。
修法 = 设置页**平铺加行**，不用容器回调。

39.3 为什么 smoke 没拦住：假 Table 是纯 JS 桩，只验 JS 逻辑，**看不见 Java 重载解析**。新门禁 =
`maiSelfTest()` 报出页面**实际用到的 Table/Cell 方法名**，`run_ui_smoke.py` 拿这些名字到真引擎里逐个调用，
`ambiguous` / `Cannot find function` / `TypeError` 即 FAIL、`RESOLVED` / `OK_SKIN` 通过；另外源码级拦
`.table(function)` / `.scrollPane(function)`（先剥 `//` 注释再扫）。`fakeTable()` 也删掉了 `table` 桩，
写回去 selfTest 立刻炸。

39.4 另外两改：①`Vars.ui` 可能晚于脚本建好 → 热键钩子里每 60 帧重试注册一次、最多 600 次，且放在
`Vars.state.isMenu()` 早退**之前**（设置菜单本身就在 menu 态）；②`diagLines()` 末尾加一行
`设置分类：已注册 / 还没注册 / 注册失败：<异常原文>`。`mod.hjson` 的 author 由 `DP` 改为 `lliary`，版本 0.3 → 0.3.1。

39.5 复跑：ui smoke exit 0（8 个形状全解析 + 假表 27 行）/ quickcheck 14 用例 / rhinoparity 14 case /
`node --check` 通过 / KB `{"chunks": 5892, "files": 63}` / `python gate.py --full` **16/16 passed in 35.1s**（ui 2.9 s）。

39.6 产物：`out/_dist/MlogAuxiliary.zip` 20,824 B sha256
`BB6447B387036530A9A942C40D9FF9F22D81CAD731929E56956B900A1ABED258`，已目录式覆盖安装到
`E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary/`。
报告 `out/takeover-20261024/39-mai-settings-fix.md`。

39.7 候选：①重启游戏看「设置 → Mlog辅助」是否出现（唯一未验的一环）；②真界面排版/按钮效果仍要人看；
③mods 目录里其它模组多是 Java 包，JS 参考只有 `DP-CameraUnbind`；④P3/P4/P5 未开始。

---

## 40. v0.4.0 -- F4 一句话生成 + 原版编辑器审查栏（2026-10-29）

用户 m08889（面板关不掉）/ m08899（设置 UI 好好设计）/ m08924（审查接原版编辑器）/ m08925（F4 = AI 辅助）。报告 `out/takeover-20261024/40-mai-ai-panel.md`（8 节）。

40.1 面板关不掉的根因：`new Packages.arc.scene.ui.Dialog(title)` 的 `addCloseButton()` 在 `Arc-Source/arc-core/src/arc/scene/ui/Dialog.java:453-455` 是**空实现**，`closeOnBack()`（:458）只登记不自动生效（Mindustry 的 `BaseDialog.java:70` 是构造里显式调的），而 `isModal`（Dialog.java:47）为真 → 无路可关。修：关闭按钮 + closeOnBack + 单实例 panel + 热键互斥。

40.2 F4 = AI 面板：一句话 → `POST /plan {intent, links, ipt}` → `logicd._route()`（关键词表 + 参数抽取）→ `compose()`（模板生成 + 全量检查 + cost + bytes_b64）→ 面板显示模板/理由/findings/前 40 行 → 0 ERR 才有写入按钮。**模型唯一接入点是 `_route()`**，返回形状不变，模组一行不改（结构性保证：模型不能把没检查过的 mlog 塞进存档）。

40.3 审查栏：不碰 canvas、不自造对话框，只在 `Vars.ui.logic`（单例 UI.java:79/:228）`row()` 之后 `add(bar).growX().height(46)`，即 LogicDialog（LogicDialog.java:39-72 只有 canvas/row/buttons 三行）的第四行；`reviewHost !== Vars.ui.logic` 重注入，代码变了（canvas.save()）每 30 帧重算，编辑器没开时每帧两次属性读。

40.4 设置页重排：`section()` 分段标题 + `kv()` 左标签(width 92,right)/右值(labelWrap width 430,left)；只用在真引擎里验证过的 12 个 Table/Cell 方法，不用 `table(fn)`/`scrollPane(fn)`。

40.5 测试：`tests/logicd/` 21 项（6 意图 + 2 参数抽取 + 模糊 ok:false + 空 400）；`run_ui_smoke.py` 解析 14 个方法 + 假表 50 行/格 + 四条源码红线（closeOnBack / buttons.button / Vars.ui.logic+canvas.save / F4→toggleAiPanel）；`run_rhino_parity.py` node 与真 Rhino 逐键一致。

40.6 复跑：KB `{"chunks": 5944, "files": 63}`；`python gate.py --full` **16/16 passed in 48.0s**；node --check 0。

40.7 产物：`out/_dist/MlogAuxiliary.zip`（顶层一层 `MlogAuxiliary/`）+ 目录式装进 `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary/`。

40.8 没做：真机未验（F4 面板排版、审查栏是否压到原版按钮、field 输入法）；模型未接（只有接入点）；中文物品名词表未做；P3 框选+队列 / P5 多处理器写入+撤销落盘未开始；撤销仍是内存快照。原始只读区全程未动。

## §41 v0.4.1 —— 点生成就崩（pane 的 ScrollPane）+ 设置页原版化（2026-10-30）

用户 m09105「设置尝试按照原版的风格分隔。」+「现在点AI生成后游戏直接崩溃。」+「继续做接下来的事」。

41.1 崩溃根因（真机日志 `saves/last_log.txt` 定的）：`[E] rhino.EcmaError: TypeError: Cannot find function add in object ScrollPane. (mlog-auxiliary/main.js#685)`。v0.4.0 用 `d.cont.pane(function(t){...}).get()` 当结果区，`Table.pane(Cons)` 返回 `Cell<ScrollPane>`（Arc `Table.java:295`，`ScrollPane extends WidgetGroup` ScrollPane.java:27），而 Group 有 `clear()`（Group.java:357）却没有公开 `add`（真 API `addChild(Element)`，Group.java:251）→ `clear()` 过后 `add()` 抛错；模态窗又没关闭按钮（`Dialog.addCloseButton()` 空实现，Dialog.java:453-455）→ 崩溃上报 + 进程退出。同一 bug 也在 `openPanel()`。

41.2 修法：结果区自己造 `new Table()`，交给 `pane(host)`（Element 重载 Table.java:311）托管；`pane()` 不可用时回落 `add(host).growX()`。AI 面板、模板面板两处都改。

41.3 设置页原版化：删掉手画 `── 标题 ──`，改 `section(t,title)` = accent 色标题 + `image(Tex.whiteui, Pal.accent).growX().height(3)`（BaseDialog.java:25 的原版分隔线）；行 = `Styles.grayPanel` 容器（SettingsMenuDialog.java:824-846 的 CheckSetting 同款，Styles.java:27/113），行宽 540 / margin 8。行工厂 `realRow()` 可注入，selfTest 传假表（无头真 Table.labelWrap 会 NPE）。

41.4 三道闸：ui smoke 在真引擎断言 ScrollPane 上没有 `add`；源码红线禁 `.pane(function` 与 `.pane(...).get()`；页面用到的 Table/Cell 方法名逐个真引擎解析（本版新增 margin/growX/height/color/image 五个壳）。假表也从「cell 桩 + table 桩」合并成一个自链式 node。

41.5 复跑：`node --check` 0（main.js 48599 B）；`run_ui_smoke.py` PASS（18 方法全绿、假表 66 行/格、诊断 6 行、MAIDIAG 版本 0.4.1）；quickcheck 14 用例 OK；logicd protocol 21 + write path 6；`python gate.py --full` **16/16 passed in 67.0s**（mirror 0.3 / tests 3.3 / lint 0.2 / shapes 0.2 / docsig 0.3 / ruleids 0.3 / quickcheck 0.4 / rhinoparity 6.3 / ui 5.0 / global 0.6 / selftest 32.1 / probes 49.8 / logicd 20.1 / corpus 30.2 / coverage 2.9 / kb 0.2）。

41.6 产物与文档：`MlogAuxiliary/README.md` 标题 → v0.4.1 并新增整节「v0.4.1：修掉「点生成就崩」+ 设置页按原版风格分隔」；`tools/README.md` 设置界面节加「第三个坑是 pane() 交回来的不是 Table」并把按钮清单改成六组；`mod.hjson` version 0.4.1。zip 顶层一层 `MlogAuxiliary/` + 目录式覆盖安装到 `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary/`。

41.7 没做：真机排版要用户重启后看；logicd 中文物品名词表；P3 框选+队列、P5 多处理器写入+撤销落盘；撤销仍是内存快照。原始只读区 Logic/、saves/、assetsraw/、Mindustry-Source/、Arc-Source/ 全程只读。

## §42 v0.4.2 —— 区域快照 + F7 链接候选（P3 第一刀，只读）（2026-10-30）

用户 m09715「游戏内工作流的产物应该最终是逻辑@config，然后上传到服务器或者本地写入。」

42.1 边界：只做 P3 的**只读**一半 —— 扫一片区域成快照，sidecar 回答「每个处理器还能连什么、链接名叫什么」。不写任何东西；写入仍只有 F4 面板（`writeBuild()` → `b.configure(bytes)`）。终点确认：`LogicBlock.config(byte[].class)`（LogicBlock.java:65-69）就是原版推代码通道，载荷 = `compress`（:137-166），**本地写入与联机上传同一个调用**。

42.2 交付：`main.js` 48599 → 56532 B（`isProcessor` / `tileBlockName` / `regionSnapshot` / `regionText` / `regionCandidatesText`、控制台 `maiSnapshot`/`maiSnapshotText`/`maiRegion`/`maiRegionAround`、`KEY_REGION=["f7"]`）；`tools/logicd.py` 25604 → 31286 B（`POST /region` + `region()`）；测试两处扩；版本 0.4.1 → 0.4.2。

42.3 快照：`{schema:1, mod, build, map, world, bounds, cells, truncated, grid[{x,y,block}], processors[{x,y,block,code,links[]}]}`；tile 坐标、空气跳过、**先交换再 clamp 到地图内**（处理器在 (0,0) 是常态，不 clamp 会读 null tile）、`SNAP_MAX_CELLS=4096` 截断。

42.4 `/region` 算法全部照源码：距离 `range=8*10`（LogicBlock.java:49）+ `within(this, range+size*tilesize/2f)`（:736）⇒ 中心距 ≤ 80+size*4；命名 `getLinkName`（:123-135）+ `findLinkName`（:331-360）；尺寸 `tools/block_sizes.json`（446 条）；「代码在用」用 `(?<![A-Za-z0-9_-])name(?![A-Za-z0-9_])`。输出 `candidates[{name,block,x,y,dist,used}]`，排序 (not used, dist, name)。与 `tools/mschgen.py:547 link_name_for()` 全表 446 条零漂移。

42.5 两个引擎事实（升级成断言）：①**`LogicBlock` 是方块类、建筑是内部类 `LogicBlock$LogicBuild`** → `instanceof LogicBlock` 恒假（第一版 processors 空数组即此因），判据改鸭子类型 `executor!==undefined && code!==undefined`；②**`tile.block()` 是方法、`tile.build` 是字段**。断言表新增 L2-26 / L2-27（✅（E）），计数 97/100 → **99 条断言 / 102 行结果**；验证记录加 2026-10-30 小节。

42.6 测试：`tests/logicd/run_logicd_tests.py --no-sim` → **23 checks**（合成快照：container1 坐标/`used`、2x2 在 10.5 格入选、switch 在 11 格落选、已有 container1 时编号变 2、`{'snapshot':42}`→400、命名全表零漂移）；`run_ui_smoke.py` → PASS（`region snapshot: 6 cell(s), 1 processor(s)`，bounds 按 clamp 断言）。docsig OK（5 文件 / 991 operand 行）。

42.7 复跑：KB `{"chunks": 5992, "files": 63}`；`python gate.py --full` **16/16 passed in 34.1s**（mirror 0.5 / tests 2.5 / lint 0.2 / shapes 0.1 / docsig 0.3 / ruleids 0.2 / quickcheck 0.4 / rhinoparity 3.2 / ui 3.0 / global 0.3 / selftest 16.5 / probes 23.1 / logicd 9.5 / corpus 13.9 / coverage 3.9 / kb 0.2）。

42.8 提交与产物：commit **6a920aa**（10 文件 +487/−12）；`out/_dist/MlogAuxiliary.zip` 32,509 B / 5 条目 / sha256 `6C1DE27F…9D05`，目录式覆盖安装到游戏 mods（5 文件逐字节一致，main.js 56532 B）。

42.9 没做：真机 F7 排版未验（无头 `Vars.ui` 为 null）；拖拽框选未做；快照 `blocks`/`items`/`units`/`enemies` 未实现；快照未落盘；`used_unlinked` 还没喂给 `/plan`。原始只读区全程未动。

## 43 v0.4.3：F7 空回复 = 主线程同步等 HTTP 回调（2026-10-30）

43.1 现象：真机 F7 弹窗正文 `sidecar 不可用（ ）` / `pending`（用户截图）；标题、accent 下划线、确定按钮都正常。

43.2 根因：`MlogAuxiliary/scripts/main.js:346 httpJson()` 在 daemon 线程发请求，用 `Core.app.post()`（`:368`）把回调投递回主线程；
而控制台命令与 F7 都在主线程上 `while(got === "pending"){ waited += 50; }`（无 sleep，占着主线程）⇒ 计时器瞬间走完 ⇒ 带字面量 `pending` 返回。
`regionCandidatesText()`（`:903`）按 `indexOf("\n")` 切 code/body，`pending` 无换行 ⇒ 空 code + body=pending。
四个入口全坏：`maiPing` / `maiCompose` / `maiApply` / `maiRegion`（`:955`/`:965`/`:979`/`:1065`）。

43.3 修法：四个入口全改异步（返回「已发出…」，处理放进回调；回调本就在主线程，能调 UI 与 `configure`）；
新增 `regionAroundBox()`（`:1058`）承载 F7，热键只调它；`maiApply` 回调里判 0 ERR 再 `writeBuild`；删除同步 `ping()`；
失败文案改「连不上 sidecar（地址）先跑 python tools/logicd.py」。`main.js` 56532 → 58182 B。

43.4 闸：`run_ui_smoke.py` 新增四条源码红线（禁 `while(x === "pending")`、禁 `while(out === "?")`、要求 `regionAroundBox(`、禁 `regionCandidatesText(rtext)`）。

43.5 断言与文档：断言表加 **L2-28**（✅（E））⇒ 计数 99/102 → **100 条断言 / 103 行结果**；
`MlogAuxiliary/README.md` 新增「v0.4.3：F7 为什么弹出…」整节 + 控制台表 5 行改异步口径；
`tools/README.md` 加「所有 HTTP 入口异步」说明；`docs/验证记录.md` 追加 2026-10-30 小节。

43.6 验证：ui smoke PASS（0.4.3）／logicd 23 checks／KB `{"chunks": 5994, "files": 63}`／**gate --full 16/16 passed in 32.2s**。

43.7 没做：真机 F7 复测待用户（无头 `Vars.ui` 为 null）；P3 后半段（拖拽框选、blocks/items/units/enemies、used_unlinked 回灌 /plan）仍未做。

## 44 v0.4.4：传输层换裸 socket + Rhino 两个 codegen bug（2026-10-30）

44.1 现象：v0.4.3 之后 F7 换个错（用户截图 m09958）——`连不上 sidecar (http://127.0.0.1:8765)` + 整段
`java.lang.IllegalAccessException: class rhino.MemberBox cannot access class
sun.net.www.protocol.http.HttpURLConnection (in module java.base) because module java.base does not export
sun.net.www.protocol.http to unnamed module`。

44.2 根因：`URL.openConnection()` 交回的是内部类 `sun.net.www.protocol.http.HttpURLConnection`（java.base 未 export），
Rhino 按**运行期类**绑成员（`rhino.MemberBox`）⇒ `setRequestMethod`/`getResponseCode`/`getInputStream` 一调就抛。
v0.4.3 没暴露是因为同步等待先失败了。

44.3 修法：`MlogAuxiliary/scripts/main.js` 的 `httpRaw()` 改成 `java.net.Socket` 手写 HTTP/1.1 —— 新增
`endpoint(url)`（正则拆 host/port/path，缺省 127.0.0.1:8765）、`readAllStr(rd)`（`Character.TYPE` 缓冲 +
`java.lang.String(cbuf,0,n)` 循环）；请求 `Connection: close` + 可选 `Content-Length`（UTF-8 字节长度），
响应 `InputStreamReader(...,"UTF-8")` 读到 EOF，按 `\r\n\r\n` 切头/正文，状态码 `substring`+`parseInt`。
协议依据：sidecar 是 `BaseHTTPRequestHandler`（`tools/logicd.py:717`），默认 HTTP/1.0，不 chunked 不 keep-alive。

44.4 **两个 Rhino 编译期 bug**（都让整段脚本静默不执行）：①正则字面量 `/^HTTP\/1\.[01] (\d{3})/` ⇒
`IllegalStateException: FAILED ASSERTION: invalid bytecode`；②`finally` 体里嵌 `try{ }catch(...){}` ⇒
`ArrayIndexOutOfBoundsException: arraycopy: last source index N out of bounds for object array[M]`（最小形
`function t(){ try{ return 1; }finally{ try{ }catch(e){} } }`）。静默的原因：`Scripts.runConsole`
（`Mindustry-Source/core/src/mindustry/mod/Scripts.java:44-65`）`catch(Throwable){ return getError(...) }`——
异常变返回值，不抛不打印。现在 `httpRaw` 末尾用独立 `try{ if(sock!==null){ sock.close(); } }catch(e1){}`，不用 finally。

44.5 设置分类图标（用户要求）：`SettingsMenuDialog.java:324 addCategory(name, Drawable, Cons)` + `Icon.logic`；
无头 `Icon.logic` 与 `Core.atlas` 都是 null ⇒ 加 `categoryIcon()` 兜底，取不到退回纯文字重载（`:329`），不传 null。
代码位置 `main.js:279-288`（helper）+ `registerSettings()` 双分支。

44.6 闸：`tests/mlogauxiliary/run_ui_smoke.py` 起真 `http.server`（端口 0）三探针（GET 200+`MAISIDECAR-OK`、
POST 200 回显 `MAIPING`、`127.0.0.1:1` 回 `code -1`），输出压一行（否则 js() 桥遇 `Exception` 字样抛 SimError）；
新增源码红线：禁 `openConnection(`、要求 `new Packages.java.net.Socket()`、禁 `}finally{`、要求显式 close、
要求 `Packages.mindustry.gen.Icon.logic`。**探针踩坑**：`maiHttpRaw` 打印的正文本里含 `Exception` 会让 js() 抛 SimError，
看起来像“传输失败”，实则是 harness 行为。

44.7 断言与文档：断言表加 **L2-29**（裸 socket，✅E）/ **L2-30**（Icon.logic 徽标，✅S 待真机）/ **L2-31**
（Rhino 两类 codegen bug，✅E）⇒ 计数 100/103 → **103 条断言 / 106 行结果**；`MlogAuxiliary/README.md` 新增
「v0.4.4」整节 + 控制台表加 `maiHttpRaw` + 设置界面图标说明；`tools/README.md` 新增「传输层是裸 socket」与
「写 main.js 的两个禁区」；`docs/验证记录.md` 追加 2026-10-30 v0.4.4 小节；`mod.hjson` version 0.4.4 + 描述补 `maiHttpRaw`。

44.8 验证：ui smoke PASS（0.4.4，18 方法 RESOLVED/OK_SKIN、假表 66 行、快照 6 格 1 处理器、HTTP 200/200/-1）；
`python gate.py --full` **16/16 passed in 34.9 s**；KB `{"chunks": 5997, "files": 63}`。

44.9 没做：设置徽标只能真机目视（无头 Core.atlas=null）；两个 Rhino bug 只在本机 v160.7 复现过；
F7 弹窗版式待真机复测；原始只读区 `Logic/`、`saves/`、`assetsraw/`、`Mindustry-Source/`、`Arc-Source/` 未动。

## 45. v0.4.5：F7 失败文案分级 + 链接名未绑定判据（L2-32）

- **起因**：真机（用户截图 m10326）按 F7 得到 `连不上 sidecar` 加一整段 `JavaException: java.net.ConnectException: Connection refused: getsockopt`。传输层已通，是 sidecar 没起 —— 但文案没有信息量。
- **改动（4 个文件 + 测试）**：
  - `MlogAuxiliary/scripts/main.js`：`httpWhy(code, body)`（连接被拒绝 / 超时 / 其它分开说，各配启动命令；`ok:false` 用响应 `message`）、`lastLine(t)`（只取最后一行、>200 字截断）；失败分支不再贴 Java 栈；面板多一行 `⚠ <name> 代码在用，但没绑上、也不在本区域候选里（同类可用 …）`；`MOD_VERSION = "0.4.5"`。
  - `tools/logicd.py`：`/region` 每个处理器新增 `missing`；新增 `_code_idents`（排除 `@内容`）、`_result_names`（token 1）、`_mlog_words`（`mlogcheck.SPECS` + `OP_*`，**不含 KEYWORDS**，因为 `core` 就在里面）、`_linkish`（基名或方块名前缀，≥3 字母）；有同前缀候选给 `suggest`（`core` → `shard1`）。
  - `MlogAuxiliary/mod.hjson` 0.4.5。
  - `tests/logicd/run_logicd_tests.py`：`/region` 三新用例（`core` → missing+suggest、`set core 1` 后不报、原有编号/范围不变），grid 加 `core-shard @15,10`。
  - `tests/mlogauxiliary/run_ui_smoke.py`：两条红线（要求 `Connection refused` 与 `p.missing`）。
- **文档**：`MlogAuxiliary/README.md` 新 §「v0.4.5」；`docs/断言表.md` 加 L2-32 并改计数 **104 条断言 / 107 行结果**；`docs/验证记录.md` 追加 2026-10-30 v0.4.5 小节（569 行）。
- **验证**：logicd protocol 23 / write path 6；ui smoke PASS（0.4.5）；`gate.py --full` 16/16；KB。
- **交付**：commit **7104e63**（8 文件 +188/−8）、zip 38,237 B / sha256 `6B16D4AAB1DD9803A0057C3979772BCB02A018BE7C84E040205B739670176765`、覆盖安装到 `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary/`；后台 sidecar `out/_logicd_run.log`，`/health` = `{"ok": true, "protocol": 1}`。
- **报告**：`out/takeover-20261024/45-missing-links.md`。
- **未尽**：`read result cell1 0` 的 `cell1` 会被报（语义正确）；大写方块名不收；L2-30 徽标仍是 ✅（S）待真机，用户已口头确认正常。

## 46. v0.4.6：链接坐标是相对的（写入载荷的真 bug，L2-33）

- **起因**：用户 m10692 确认 F7 + sidecar 真机可用后，回头核对「写进去的程序运行时链接变量是什么」，在
  `LogicBlock.config(byte[].class, (build, data) -> build.readCompressed(data, true))`（`LogicBlock.java:65-69`）
  里看到第二个参数 `relative = true`，`readCompressed` 有 `if(relative){ x += tileX(); y += tileY(); }`（`:304-307`）。
- **结论**：载荷存**相对**处理器的偏移，而 `LogicLink.x/y`（`:102`）是**绝对**坐标。模组 `linkList(b)` 上报绝对、
  `logicd.compose()` 原样打包 ⇒ 游戏把绝对坐标当偏移再加一次处理器坐标，整张链接表平移到空地，
  `link.valid=false`、运行时读 `null`，**游戏不报错**。
- **探针**（`out/_v46_probe2.py`，真 v160.7）：处理器 (10,10) + container (13,10)，载荷写绝对 `(13,10)` ⇒
  `container1@23,20->null`；写相对 `(3,0)` ⇒ `container1@13,10->container`。早先 `out/_v46_probe.py` 在
  `srv.base=(0,0)` 处测不出差异，正是这个 bug 长期潜伏的原因。
- **改动**：`tools/logicd.py` 新增 `_relative_links(links, origin)`，`/compose` 与 `/plan` 接受 `origin:{x,y}`
  （非对象 → 400，返回体回显 `origin`；不传则原样透传，老调用方零影响）；`main.js` 新增 `originOf(b)` 并在
  `/plan`、`/compose` 两个请求体都带上；`mod.hjson` 与 `MOD_VERSION` → 0.4.6。
- **测试**：`tests/logicd/run_logicd_tests.py` 协议层加 origin 换算三断言 + 写入路径把处理器另放 `base+(16,16)`
  并回读 `name>block` 全解析，负控（不带 origin）必须出现 `>null`；`run_ui_smoke.py` 两条源码红线。
- **文档**：`MlogAuxiliary/README.md` 新 §v0.4.6；`docs/断言表.md` 加 **L2-33**（✅ E）⇒ **105 条断言 / 108 行结果**；
  `docs/验证记录.md` 追加 2026-10-30 v0.4.6；`tools/README.md` 补 `origin` 说明并把契约测试计数改成 24/7。
- **验证**：logicd protocol 24 / write path 7；ui smoke PASS（0.4.6）；KB `{"chunks": 6032, "files": 63}`；
  `python gate.py --full` **16/16 passed in 36.2s**。
- **报告**：`out/takeover-20261024/46-link-relative-coords.md`。
- **未尽**：真机复测带链接写入（需 sidecar 在跑）；P3 剩余三件（候选回灌 /plan、拖拽框选、快照写文件）。

## 47. v0.4.7：审查栏行内箭头 + 修掉「有链接也报无链接」（L2-34 / L2-35）

- **用户**：m10898/m10905「逻辑即使有链接代码审查也会报无链接的 warn」；m10921「设计一下代码审查的交互，要不在对应行数贴一个箭头提示。点击箭头展示审查不通过的原因。」
- **假 WARN 根因**：`LogicDialog.executor` 是**包私有**字段（真 v160.7 反射实测 `executor:pkg`，`out/_v47_probe3.py`），Rhino 只暴露 public 成员 ⇒ `L.executor` 是 `undefined`，取 `.build` 抛 TypeError 被吞 ⇒ `linkNames()` 返回 `[]` ⇒ 每个链接槽都判成「没链接」。对照探针 `out/_v47_probe.py`：真链接名喂快检零命中、空数组两行 WARN ⇒ 规则本身没错，错在喂进去的东西。
- **修法**：①`main.js` 新增 `logicExecutor()`（`Class.forName` + `getDeclaredField("executor")` + `setAccessible(true)`，再读 public 的 `ex.build`）；②`linkNames()` 读不到时返回 `null`（不是 `[]`），`quickcheck.check()` 用 `stats.linkKnown` 记账并整段跳过链接槽判据，统计行显示「链接 ?（读不到处理器）」；③行内箭头做成覆盖层（`Table.cells` 私有插不进原版行）：`Touchable.childrenOnly` 的 Table 铺在 `statements.parent` 上，箭头 `addChild` + `host.update()` 每帧重排，`line-1` 取孩子、表头行高 38、优先行左侧空白 `x-18`，ERR 红/WARN 橙/INFO 蓝，点箭头 `showText` 列原因；`api.maiArrows` 是测试钩子。
- **测试**：`run_ui_smoke.py` 新增 `arrow_probe()`（真引擎 4 行假 statements + `pack()`，5 条 findings 含越界 line 0/9 ⇒ `arrows 2`、`1:22,213:WARN:1`、`3:22,93:ERR:2`，按公式核位置/颜色/条数）+ 7 条源码红线；`cases.json` 加 `links-unknown` / `links-unknown-vs-empty` 一对，`harness.js` 与 `run_rhino_parity.py` 都改成 `(c.links === undefined) ? [] : c.links`。
- **文档**：`MlogAuxiliary/README.md` 新 `v0.4.7；`docs/断言表.md` 加 **L2-34 / L2-35** ⇒ **107 条断言 / 110 行结果**；`docs/验证记录.md` 追加 2026-10-30 v0.4.7；`tools/README.md` 加「第四个坑是「读不到」被当成「没有」」+ 无头 `Table.add(CharSequence)` 需要 Label 样式的坑。
- **验证**：quickcheck 16 cases；rhino parity 16 identical；ui smoke PASS（0.4.7，review arrows 两枚）；KB `{"chunks": 6037, "files": 63}`；`python gate.py --full` **16/16 passed in 34.7s**。
- **报告**：`out/takeover-20261024/47-review-arrows.md`。
- **未尽**：真机目视（箭头是否压字、点箭头弹窗排版）；语句被删后旧箭头短暂错位（下一次刷新修正）；P3 剩余三件（候选回灌 `/plan`、拖拽框选、快照写文件）。


## §48 v0.4.8：F3 拖拽框选 + 快照落盘（2026-10-30）

- 热键 F3（F7 已给审查、F8 是游戏控制台 `Binding.java:107`、F9/F10 被占）。三态：进入 / 取消 / 有对话框不动。
- `selRect()` 只归一化不 clamp（新断言 L2-36），clamp 归 `regionSnapshot()`。
- 高亮 `Events.run(ET.Trigger.draw)` + `Draw.rect(Tex.whiteui,...)`，不建场景元素（避免 v0.4.1 那类崩溃）。
- 新接口 `POST /snapshot` 落盘 `out/snapshots/snap-<时间>-<sha1 8>.json`，四类 400 负控。
- 测试：ui smoke `select_probe`（含 `MAIDRAWAPI` 反射钉 Draw 重载）+ logicd `/snapshot` 契约；断言表 108 条 / 111 行。
- 报告：`out/takeover-20261024/48-drag-select.md`。

## §49 v0.4.9：F3 两个手感 bug（2026-10-30）

- 用户 m11420：预览区中心在指针上 + F3 弹窗阻止拉框。两条都是真 bug。
- 弹窗吃鼠标：`showText` 开 Dialog ⇒ `Core.scene.hasDialog()` 真、世界收不到点击。改用
  `hint()` → `Vars.ui.showInfoFade`（`UI.java:373`，`:380 Touchable.disabled`），F3 不再弹任何东西。
- 高亮按角点锚定：`Draw.rect(x,y,w,h)` 的 x,y 是**中心**（`Arc Draw.java:378 x - w/2f`）⇒ 新增
  `selDrawArgs(r)` 传中心坐标。
- 起点改为「按下左键那一格」；状态机拆纯函数 `selArm/selCancel/selPress/selMove/selBox/selRelease`；
  只点一下（w=h=1）只提示不落盘。
- 断言 L2-37（109 条 / 112 行）；ui smoke `select_probe` 驱动状态机 + `MAIHINTAPI` 反射 + 红线禁
  `popup("Mlog辅助 · 框选"`。报告 `out/takeover-20261024/49-select-fixes.md`。
## §50 v0.5.0：F3 就是鼠标左键 + 原版选框样式（2026-10-30）

- 用户 m11493 两条：①选框要像原版矩形选框 ②按下 F3 就直接拉矩形（F3 等价鼠标左键）。
- 原版画法照抄 `Mindustry-Source/core/src/mindustry/input/InputHandler.java:1758-1795`：
  `Lines.stroke(2f)` + `Pal.accentBack`（`y-1` 阴影）+ `Pal.accent` 双描边，**无半透明填充**；
  尺寸文本 `Fonts.outline` + `1/renderer.camerascale` + `Draw.z(Layer.endPixeled)`。
- 锚定口径换了：`Lines.rect(x,y,w,h)` 是**左下角+宽高**（`Arc Lines.java:485`），与 `Draw.rect(region,x,y,w,h)`
  的中心锚定（`Draw.java:378`）相反 ⇒ `selDrawArgs()` 改回角点 `{x1*8,y1*8,w*8,h*8}`。
- 状态机去 arm 层：`selHolding`/`selDragging`，`selPress` 立即开拖，`keyDown(f3)` 边沿驱动 press/move/finish，
  松开 F3 即 `selFinish()` 出快照；不再需要按鼠标左键、不再有「就绪」提示。
- 包名坑：`Fonts` 在 `mindustry.ui`（`out/_server160.jar` 里只有 `mindustry/ui/Fonts.class`），
  写成 `mindustry.gen.Fonts` 会被 try/catch 吞掉、字永不出现（`MAIFONTAPI` 探针抓出来的）。
- 断言：L2-37 整行改写 + 新增 L2-38（原版选框三要素）⇒ 110 条 / 113 行。
- 复跑：ui smoke PASS（MAIDIAG 0.5.0）；`node --check` 通过；`gate.py --full` 15/16 + kb warn →
  `tools/kb.py build` 6057 块/63 文件后 16/16；zip 50,543 B sha256 `50251A74…35AF0AE` 已装机。
- 报告：`out/takeover-20261024/50-select-vanilla.md`。诚实缺口：真机手感未验收，无头环境无 GL/鼠标，
  `drawSizeText` 的缩放位置只能靠源码对照。
## §51 v0.6.0：框选之后有区域面板（2026-10-30）

- F3 松手的出口从「落盘 + 纯文本」换成面板：`dumpRegion()` 里 `/snapshot` → 回调里 `/region` →
  `showRegionPanel()`；面板 = 区域摘要 + 落盘路径 + 每处理器候选链接（含 v0.4.5 的 `missing` 告警）。
- 每处理器一行「用 @x,y 生成」→ `buildAt(x,y)`（`t.build` 是字段）→ `showAiPanel(target)`
  （新可选参数）⇒ 直接以该处理器为目标开 F4 面板。
- `buildRegionTable()` 故意放脚本顶层（`selfTest` 在引擎 `try{}` 之外），假表可数行数；
  `showRegionPanel` 在引擎作用域里，`pane()` 给 ScrollPane 所以要自造 host（v0.4.1 教训）。
- 面板建不出来 catch 回落旧 `popup`，候选不丢。
- 断言 L2-39（新）⇒ 111 条 / 114 行；`MAISELF` 行新增「区域表格 8 行」+ 四条 v0.6.0 源码红线。
- 复跑：ui smoke PASS（0.6.0）、`node --check` 通过（94,171 B）、`gate.py --full` 15/16 + kb warn
  → `tools/kb.py build` 6059 块/63 文件；zip 52,564 B sha256 `782003C1…EE4B74B` 已装机。
- 报告：`out/takeover-20261024/51-region-panel.md`。诚实缺口：面板只在真机出现（无头 `Vars.ui` 为 null），
  超过 8 台处理器没有翻页，`labelWrap` 长文本的滚动观感未调。

## §52 v0.6.1 选框偏右上角半格

玩家实测 m11766：「选框位置偏右上角越半格」。根因是坐标口径：`Tile.worldx()` = `x * tilesize`
（`Mindustry-Source/core/src/mindustry/world/Tile.java:166-172`）是格子**中心**，格子左下角是 `(x1 - 0.5) * 8`；
v0.5.0 直接把 `r.x1 * 8` 当左下角传给 `Lines.rect(x,y,w,h)`（左下角锚定，`Lines.java:485`），
于是整框右上各偏 4 px。原版同样减半格（`Placement.java:380-390`）。

改动：`selDrawArgs(r)` → `{x: (r.x1 - 0.5) * 8, y: (r.y1 - 0.5) * 8, w: r.w * 8, h: r.h * 8}`；
版本 0.6.1；`MASELDRAW` 期望 `(bx+5)*8-4`；两条新红线钉半格；断言表 L2-38 证据改写；README / 验证记录各一节。

复跑：ui smoke PASS（`MAIDIAG 0.6.1`）、`node --check` 通过、`gate.py --full` **16/16**（33.8s）、
kb `{"chunks": 6060, "files": 63}`、zip **53,190 B** sha256 `51CA7315...D980CA`、装机 5 文件逐字节 OK。

**门禁假失败教训**：`FAILED: probes, logicd` + `Native memory allocation (mmap) failed` 是残留 JVM 太多
（实测 65 个 `java.exe -jar out/_server160.jar`，共占约 12 GB），`Get-Process java | Stop-Process` 后即 16/16。
别去改代码。报告 `out/takeover-20261024/52-select-half-tile.md`。

诚实缺口：半格按源码口径算，观感仍待真机确认。

## §53 v0.7.0 F2 全图处理器清单

用户「下一f」。P3 到 v0.6.1 后游戏内已有 F3 框选 / F4 面板 / F7 链接候选，但「哪台处理器有问题」
仍要一台台挪鼠标；`maiScan()` 早就能一次扫全图，只是输出在控制台里。v0.7.0 把它做成面板。

**键位**：F2 —— `Binding.java` 里 F1/F5/F6/F8/F11/F12 归游戏，F3/F4/F7 是模组的，F2 是唯一还空着的功能键。

**实现**：`scanProcessors()`（`Groups.build.each` + `isProcessor()` 鸭子类型 → 每台 `api.q.check`，收
`{x,y,lines,err,warn,links,rules}`，按 ERR→WARN→y→x 排序）、`listHead()`/`listRowLabel()`/`buildListTable()`（纯表格，
selfTest 假表可数）、`showListPanel()`（Dialog + 自造 host 给 `pane()`，按钮「复制清单」/「关闭」）、
点一行 `Core.camera.position.set(x*8+4, y*8+4)` + 关面板 + `showAiPanel(buildAt(x,y))`；退路 `popup()` 与
`maiList`/`maiListRows`/`maiListPanel`。只读。

**复跑**：node --check 通过（101,782 B）；ui smoke PASS（`MAISELF:…清单表格 6 行…`、`MAIDIAG 0.7.0`、
`MAILIST:全图 0 个处理器`、`MAILISTROWS:[]`）；`gate.py --full` **16/16**（36.3s）；kb `{"chunks": 6061, "files": 63}`；
zip **55,287 B** sha256 `21FCD283...6B30EB`；装机 5 文件逐字节 OK（main.js 153E99325CB15AF9）。

**诚实缺口**：无头引擎 `Groups.build` 为空，「扫描+排序」只验到 0 处理器；相机跳转不可验。真机需玩家按一次 F2 对数。
报告 `out/takeover-20261024/53-processor-list.md`；断言表 L2-40；规划 §9 新增一行。

## §54 P4 第一刀：作业队列 + 写入门禁

用户「测试均正常，继续下一步」。按规划 §9，P3 两刀、v0.7.0 F2 都已完成，下一段是 **P4**。
P4 的三段里（队列 / 模型 / 门禁）先做**不需要模型的那部分**：模型留成 `provider` 函数，
默认实现就是已有的 `/plan` 意图路由 ⇒ 整条链路离线可跑。

**新文件 `tools/jobqueue.py`**：`job_id = sha1(snapshot+desc+mode)[:16]`、`normalize()/gate()/Store/Queue/template_provider/FakeProvider`。
状态 `queued -> running -> done|rejected|failed|cancelled`，**每次跃迁先 tmp+fsync+os.replace 落盘**；
`Queue.__init__` 把残留 `running` 改回 `queued`（attempts 保留）⇒ sidecar 崩了不丢；`POST /jobs` 同 body 幂等；
`DELETE /jobs?id=` 取消（running 也走检查点退出）。最多 3 次尝试（1 + 2 次 self-repair，findings 当提示回喂）。

**门禁严一档**：`mlogcheck` 对 `link-name-not-bound` 只给 WARN（人还没接完线是常态），
但作业是机器输出直接进处理器 ⇒ `FATAL_RIDS = ('link-name-not-bound',)` 提升为 ERR；被拒作业 `code` 恒为空串。

**logicd 新增三端点**：`POST /jobs`、`GET /jobs?id=|?state=`（不带 state 只回未完成）、`DELETE /jobs?id=`；
CLI 新增 `--jobs-dir` / `--jobs-provider {template,fake}` / `--fake-provider FILE` / `--jobs-drain`。

**测试**：`tests/logicd/run_logicd_tests.py` 的 `test_jobs()` 9 项（干净→done+payload+落盘、幂等、幻觉链接→rejected+attempts 3+code 空、
self-repair→attempts 2、running 时取消、列表/404/400 负控、模板档 item-threshold、重启续跑、gate 单测）。
复跑：`--no-sim` → protocol 25 / **jobs 9**；全量 → protocol 25 / jobs 9 / write path 7 / OK。

**文档**：tools/README（接口十个 + 整段 `POST /jobs` + 文件分层补 jobqueue.py）、规划 §4「实际落地（P4 第一刀）」、
断言表 **L2-41**、验证记录同日一节、报告 `out/takeover-20261024/54-jobs-queue.md`。

**诚实缺口**：游戏内 1 s 轮询 + 完成提示 UI（= P4 第二刀）、真 provider 与 §4.4 三段 prompt、自由档 cost/sim 复检、单 worker 串行。

## §55 v0.8.0 P4 第二刀：模组侧作业队列

**改的是通道不是生成逻辑**：F4 面板「生成」从同步 `POST /plan` 换成 `POST /jobs` 投作业 +
每秒 `GET /jobs?id=` 轮询（`JOB_POLL_MS = 1000`，面板关掉即停），done 时渲染代码并把按钮换成
「写入/关闭」，rejected/failed/cancelled 时渲染 findings 与中文原因，面板多一个「取消作业」
（`DELETE /jobs?id=`）。「直接生成」保留当老 sidecar 的退路；写入仍走 `jobAsPlan()` → `writeBuild()`，
只认 `bytes_b64`，所以写入路径与 v0.7 同一份代码。

**测试（真 v160.7 引擎 + 真 sidecar + 假 provider）**：`run_ui_smoke.py` 新增 `start_sidecar()` / `job_probe()`，
干净作业 → `done` / attempts 1 / 60 字节载荷写进处理器；坏代码（`jump 99 always x 0`）→ `rejected` / attempts 3 / 带 ERR findings。
输出 `job queue: done attempts=1, 60 byte payload written into the processor` /
`job gate: rejected after 3 attempt(s), 1 finding(s)`，EXIT=0。

**新发现的盲区**：处理器零链接时模组发来的 `links` 是空数组，`mlogcheck` 把空数组当「不知道」，
幻觉链接名拦不住；本刀用代码级 ERR 验拒绝路径，链接名一档由 `test_jobs()` 的显式 links 覆盖。

**文档**：MlogAuxiliary/README 标题 + v0.8.0 节、规划 §4「实际落地（P4 第二刀）」+ 盲区注记、
断言表 **L2-42**、验证记录同日一节、tools/README `/jobs` 段补「模组侧已接」、报告
`out/takeover-20261024/55-job-queue-ui.md`。

**诚实缺口**：面板关闭后不再观察作业、没有跨面板完成通知条、零链接门禁盲区。

## §56 v0.8.1 F4 并入 F3 的单格选择

**一句话**：按住 F3 在处理器上点一下（不拖）= 开这台处理器的 AI 面板，拖出矩形仍是区域快照；
F4 键保留为同一个 `toggleAiPanel()` 的别名。

**判据复用**：新增 `processorAt(x, y)` = `buildAt()`（`t.build` 是字段）+ `isProcessor()`（`executor`/`code` 鸭子类型），
和 F2 清单、F7 候选同一套；`selFinish()` 的 1×1 分支先问它，是处理器才 `showAiPanel(one)`，
不是就提示「这一格没有处理器」。旧文案「没有拖动：按住 F3 从一个角拖到另一个角」已删（它假设用户想拖）。

**测试**：ui smoke 的 `select_probe()` 加 `MAIPICK`（处理器格 → `"x,y"`）与 `MAIPICKEMPTY`（相邻容器格 → 空串），
四条源码红线 + 一条反红线（`"没有拖动"` 不得出现）。实测 PASS，`MAIDIAG:版本：0.8.1（游戏构建 160）`，EXIT=0。

**文档**：MlogAuxiliary/README 标题 + v0.8.1 节、断言表 **L2-43**、验证记录同日一节、规划 §9 新增一行、
tools/README「v0.8.1 起 F4 并入 F3」两行、报告 `out/takeover-20261024/56-select-ai-panel.md`。

**诚实缺口**：无头引擎无 `Vars.ui`，面板是否真的弹出仍需真机；空格子单点只提示不给快照（有意）。

## 57 · v0.9.0：F4 热键删除 + 零链接门禁盲区修复

玩家 m12288：「做1，直接整个去掉f4的热键，不用保留。然后做2」。

### 57.1 改了什么

| 文件 | 改动 |
| --- | --- |
| `MlogAuxiliary/scripts/main.js` | 删 `KEY_PANEL` / `toggleAiPanel()` / 6 行 `keyTap`；钩子外层变匿名块；`MOD_VERSION = 0.9.0`；新增 `linkListOrNull(b)` |
| `MlogAuxiliary/mod.hjson` | version 0.9.0，描述改「按住 F3 点一下处理器打开」 |
| `tools/mlogcheck.py` | `analyse(..., links_authoritative=False)`，只在权威时启用链接名判据 |
| `tools/logicd.py` | `links is not None` 时传 `links_authoritative=True`，`names` 保留空列表 |
| `tools/jobqueue.py` | `normalize()` 允许 `links: null`；`_materialize()` 不再 `or []` |
| `tests/logicd/run_logicd_tests.py` | test_jobs 9 → 12 项 |
| `tests/mlogauxiliary/run_ui_smoke.py` | F4 反向红线 + 第三路作业探针 `MAIJOBZERO` |
| `docs/断言表.md` | L2-43 改写（F4 已删）、新增 L2-44 |
| `docs/验证记录.md` / `docs/Mlog辅助-规划.md` / `tools/README.md` / `MlogAuxiliary/README.md` | 同步 |

### 57.2 关键根因（别再踩）

`logicd.analyse()` 原来 `_link_names(links) or None` ⇒ 权威空表 `[]` 被折成 `None` ⇒ `mlogcheck` 跳过链接名判据。
修好 `mlogcheck` 与 `logicd` 之后测试仍红，真凶在 `jobqueue._materialize()` 的 `links = job.get('links') or []`——
它又把 null 变回权威空表。**凡是「三态」（空表 / 未知 / 非空）在管道里传，每一跳都要显式保住第三态。**

### 57.3 复跑

`tests/logicd` protocol 25 / jobs 12 / write path 7；`tests/mlogauxiliary` EXIT=0；`tests/run_tests.py` 44/44；
`gate.py --full` 16/16；`tools/kb.py build` 重建；zip 打包装机。

### 57.4 下一刀

真 provider + 规划 §4.4 三段 prompt（世界事实 / 规则摘要 / 任务与 JSON 契约），仍是离线可验：
provider 走 `--jobs-provider` 的可换缝，测试用录制回放式假模型，不联网。

## 58 · P4 第三刀：真 provider 接缝 + §4.4 三段 prompt

玩家 m12288 的第 3 条（「然后做2」= 我上一轮列的真 provider + 三段 prompt）。

### 58.1 新增与改动

| 文件 | 改动 |
| --- | --- |
| `tools/mlogprovider.py`（新） | `build_prompt()` 三段 / `parse_reply()` / `HttpProvider` / `ScriptedProvider` / `load_script` / `Recorder` / `provider_from_args` |
| `tools/logicd.py` | `--jobs-provider llm` + `--llm-url/--llm-model/--llm-key-env/--llm-timeout/--llm-replay/--llm-record`；缺参数 exit 2 |
| `tools/jobqueue.py` | `_materialize()` 检查回复声明的 `needs_links`，越界即 `link-name-not-bound` ERR |
| `tests/logicd/run_logicd_tests.py` | 新增 half D `test_provider()` 9 项 |
| `tools/README.md` / `docs/Mlog辅助-规划.md` / `docs/断言表.md`（L2-45）/ `docs/验证记录.md` | 同步 |

### 58.2 关键设计点（以后别改坏）

- **三态必须让模型看见**：`links is None` → prompt 写 UNKNOWN，`[]` → 写 EMPTY，非空 → 逐条列 `name @ (x, y)`。
  模棱两可会让模型自己编名字，正好撞上 v0.9.0 刚修的门禁。
- **解析要宽容、校验要严**：围栏与散文都容忍（模型经常加），但 `code`/`template` 二选一、类型不对就 `ProviderError`。
- **llm 是显式开关**：既无 `--llm-url` 也无 `--llm-replay` 时 `exit 2`，绝不静默用模板档冒充模型。
- **录制/回放是测试基础设施**：`--llm-record` 存 JSONL，`--llm-replay` 回放 ⇒ 回归永远离线且确定。

### 58.3 复跑

`tests/logicd/run_logicd_tests.py --no-sim` → protocol 25 / jobs 12 / **provider 9**；
全量 → write path 7（真 v160.7）；`gate.py --full` 16/16；`tools/kb.py build` 重建。

### 58.4 下一刀候选

①模组侧 provider 选择 + 面板显示「模板档/模型」 ②自由档 cost + 200 tick sim 复检 ③P5 多处理器事务写入与撤销。

## 59 · v0.9.1：侧车进程太旧时，面板直接说「重启」

玩家 m17617 截图：面板只有一行 `投递失败：no such endpoint: /jobs`，问这是否正常。

### 59.1 结论

不是模组 bug，是**进程里的旧代码**。跑着的 `tools/logicd.py` 是 18:18:18 启动的 PID 59920——
那一刻仓库里还没有 `/jobs`（v0.8.0 才加）。Python 把模块读进内存后不再看磁盘，
所以 `GET /health` 一直 200（这条从第一版就有），`GET /jobs` 却 404。
重启（PID 61368，22:30:38）后 `GET /jobs` 立刻 200 `{ok:true, jobs:[], count:0}`。

### 59.2 改动

| 文件 | 改动 |
| --- | --- |
| `MlogAuxiliary/scripts/main.js` | 新增 `sidecarStaleHint()` / `jobWhy()`：错误文本含 `no such endpoint` 时换成「sidecar 进程是旧版本 → 关掉旧的再 `python tools/logicd.py --port 8765`」；三个作业接口错误回调统一走 `jobWhy()` |
| `MlogAuxiliary/mod.hjson` / `MlogAuxiliary/README.md` | 版本 0.9.1 + 新增一节说明 |
| `tests/mlogauxiliary/run_ui_smoke.py` | v0.9.1 源码红线：`function sidecarStaleHint(` 与 `no such endpoint` 必须在 |
| `tools/README.md` | sidecar 节新增「改过 `tools/logicd.py` 必须重启」，含排查命令 |

### 59.3 活体复验（不靠游戏，直接打 HTTP）

- `POST /jobs`（container1 + message1，「容器里铜够 120 就打印」）→ `done`，attempts 1，7 语句，`bytes_b64` 184。
- 只给 container1 → `rejected`，`template-needs-link`：模板要打印就必须有 printflush 对象，这是对的，文案已点名 message1。
- 契约细节：`job id = sha1(snapshot+desc+mode)[:16]` 不含 links/origin ⇒ 换链接会幂等命中旧作业；`GET /jobs?id=` 回 `{ok, job}` 单个。

### 59.4 复跑与打包

`gate.py --full` 15/16 PASS + kb WARN（刚改过 tools/README.md）→ `tools/kb.py build` 后 `{chunks 6342, files 65}`；
`run_ui_smoke.py` PASS；zip 62,455 B sha256 `46D131F2DB16743410A1EC631566F431188565868442DE7B397B052203B23BEA`，已装机 5 文件逐字节 OK。

### 59.5 下一刀候选

①面板记住上次的 provider ②多个 message 链接时按距离挑最近的 ③rejected 作业给「加消息块」可点提示。

## 60 · v0.9.2：模板要的链接名不在，就换成同族最近的那个

上一刀候选②。处理器上接的是 `message2`（多处理器共用一台显示时的常态），模板却写死 `printflush message1`，
`compose()` 直接 `template-needs-link` ERR 拒绝——玩家白投一次作业。

### 60.1 判据

链接名 = `<方块名><序号>`（`LogicBlock.java:331-360`），`message1` 与 `message2` 是同一方块的**不同编号**，
语义可换、只差连到谁。规则：模板 ref 未绑定 → 在同族（去尾部数字相同）且**已绑定**的链接里按到处理器的
欧氏距离取最近替换；同族全无才维持原 ERR。

### 60.2 改动

| 文件 | 改动 |
| --- | --- |
| `tools/logicd.py` | 新增 `_link_stem()` / `_nearest_link()` / `_substitute_links()`；`compose()` 先算 subs 再判 missing，替换后重跑 `analyse()`，每条替换插一条 `INFO template-link-substituted`；payload 用替换后的 code |
| `tests/logicd/run_logicd_tests.py` | 新增 compose 用例：container1 + message2@260 + message3@199 + origin 197 → ok、换成 message3、有 INFO rid |
| `tools/README.md` | 锚定档兜底段（同族按距离替换、INFO 语义、`_nearest_link()`、`message1` 不误伤 `message10`） |

判据细节：整词正则 `(?<![A-Za-z0-9_-])old(?![A-Za-z0-9_-])`；links 元素兼容 `{name,x,y}` 与裸字符串；
无 origin 时距离全 0（取第一个）。

### 60.3 坑：同名 helper 被覆盖

第一版叫 `_link_base`，实测不生效——`tools/logicd.py:709` 早有一个 `_link_base(block)`（`getLinkName()` 语义），
后定义覆盖先定义。改名 `_link_stem` 后正常。**往大文件插 helper 前先 grep 名字。**

### 60.4 复跑

in-process 探针 ok（message3 入选、单条 INFO）；同族全缺仍 ERR `template-needs-link` + WARN `link-name-not-bound`；
`run_logicd_tests.py --no-sim` → protocol **26**（原 25）/ jobs 12 / provider 9，EXIT=0；
`gate.py --full` 首跑 15/16（kb stale）→ `kb.py build` `{chunks 6359, files 65}` → **16/16 in 34.3s**。

### 60.5 边界与下一刀

模组侧**一行未改**（`main.js` 没动、`mod.hjson` 不 bump、不重打 zip），因为替换在侧车 `compose()` 内部，
面板拿到的还是同一条 `/compose` 响应。改过 `tools/logicd.py` 记得重启 sidecar（§59）。
下一刀：①面板记住上次选中的 provider ②`rejected` 作业给「加消息块」可点提示 ③自由档 `needs_links` 也走同族兜底。

## 61 · v0.10.0：撤销跨重启 —— 写入前把原代码落盘（P5 第一刀）

P5（多处理器事务写入 + 撤销落盘，`docs/Mlog辅助-规划.md` §5）里第一件能独立做的事：撤销不再只活在内存里。

### 61.1 症状

写错了想回滚，可 `undoStack` 活在 Rhino 全局对象里，**关掉游戏就没了**；第二天开游戏，处理器上是坏代码，
原来那份只能靠存档备份或手抄。

### 61.2 改动

| 文件 | 改动 |
| --- | --- |
| `MlogAuxiliary/scripts/main.js` | 102,341 → 108,228 B：新增 `UNDO_KEEP`/`undoRoot`/`linkPairs`/`snapshotText`/`undoFilesOf`/`undoFiles`/`saveUndoTo`/`saveUndo`/`undoFromDisk`/`undoInfo`；`writeBuild()` 写前落盘并把快照名塞进成功文案；`undo()` 两级；设置页多一行两个按钮；控制台 `maiUndo`/`maiUndoInfo`/`maiUndoProbe`；`selfTest()` 加序列化往返 |
| `MlogAuxiliary/mod.hjson` | 0.9.1 → 0.10.0，description 末尾补撤销目录与控制台函数 |
| `MlogAuxiliary/README.md` | 标题改 v0.10.0 + 新增整节「撤销能跨重启了」 |
| `tests/mlogauxiliary/run_ui_smoke.py` | 新探针行 `MAIUNDO:`、过滤 tuple 加前缀、断言 `MAIUNDO:ok `、三条 v0.10.0 源码红线 |
| `docs/Mlog辅助-规划.md` | §5 加「第一刀（v0.10.0，已落地）」小节；§9 P5 行 未开始 → 部分完成 |
| `docs/断言表.md` / `docs/验证记录.md` | 新增 L2-46（撤销快照往返） |

快照格式：`<dataDir>/mlogauxiliary/undo/<毫秒时间戳>_<x>_<y>.json` = `{schema,x,y,at,why,code,links[]}`，
`why` 是 `write:<模板id>`，上限 40 份。**只还原 `b.code`**（模板的链接表来自处理器当前链接，
回滚代码就够；链接表存下来是给第二刀与排查用的）。

### 61.3 三个坑

1. `Vars.dataDirectory` 是 Arc 的 **`Fi`**（`Arc-Source/arc-core/src/arc/files/Fi.java`），不是 `FileHandle`；
   有 `child/writeString(String,boolean)/readString/list(suffix)/mkdirs/delete/deleteDirectory`，没有 `listFiles()`。
2. `writeString(text, false)` 第二参数是 **append**：传 `true` 会把新快照接在旧内容后面，读回来是坏 JSON。
3. `undoFromDisk()` 不能假设 `Vars.world.build(x,y)` 一定是处理器：拆掉的/换图后是空气，`b.code` 是 `undefined`，
   必须跳过继续往前，否则一份坏快照锁死整个撤销。

### 61.4 复跑

`run_ui_smoke.py` EXIT=0（`MAIUNDO:ok 1793373825237_3_4.json`、`MAISELF` 含「撤销快照 ok」、表格方法 18 个全 OK_SKIN、
假表 70 行/格、作业三路仍全过、`MAIDIAG:版本：0.10.0（游戏构建 160）`）；
`gate.py --full` 首跑 15/16（kb stale）→ `kb.py build` `{chunks 6360, files 65}` → **16/16 in 37.4s**。

### 61.5 边界与下一刀

磁盘快照只回滚代码不回滚链接表；跨重启回滚只有引擎内探针、没有「关游戏再开」的真机手验；
`saveUndo` 失败不阻断写入（撤销是安全网，不是写入前置）。
下一刀（P5 剩余）：一个作业产出 N 段代码的事务写入 + 整体回滚、写前「处理器在你提交后被改过」的冲突提示 ——
两者都要先扩 sidecar 作业契约（job → N 段代码）。另：候选③（自由档同族兜底）**已判定不做**（会削弱 v0.9.0 零链接门禁），
候选①（面板记住 provider）**不存在**（provider 是 sidecar 启动参数，模组侧没有这个 UI）。

## 62 · v0.10.1：投递之后处理器被改过，第一次写入会被拒绝（P5 第二刀）

P5 规划里「写入前重读 code，不一致 → 提示被改过」的模组侧一半。

### 62.1 症状与判据

作业是异步的（模型档可能几十秒），等结果时玩家改了代码，点「写入」会把改动静默覆盖。
冲突基线不是撤销快照（v0.10.0 那份是写入前一刻拍的，拍完立刻写），而是**投递那一刻**的代码：
`String(b.code) !== String(orig)` 即算被改过；字符串全等（含行尾空白）是保守选择。

### 62.2 改动

| 文件 | 改动 |
| --- | --- |
| `MlogAuxiliary/scripts/main.js` | `JOB_ORIG`/`JOB_FORCE`/`procKey`/`rememberOrig`/`forgetOrig`/`conflictReason`/`conflictGate`；`jobSubmit()` 与 `jobSync()` 两条投递路径都记基线；`writeBuild()` 加第三道闸；写成功后 `forgetOrig`；`api.maiConflictProbe()` |
| `MlogAuxiliary/mod.hjson` | 0.10.0 → 0.10.1 + description 一句 |
| `MlogAuxiliary/README.md` | 标题 v0.10.1 + 新增整节 |
| `tests/mlogauxiliary/run_ui_smoke.py` | `MAICONFLICT` 探针 + 端到端冲突用例（投递→改码→第一次拒/第二次覆盖）+ 三条 v0.10.1 源码红线 + 摘要行 |
| `docs/Mlog辅助-规划.md` | §5 加「第二刀（v0.10.1，已落地）」；§9 P5 行改「第一刀 + 第二刀」 |
| `docs/断言表.md` / `docs/验证记录.md` | 新增 L2-47 |

交互：**不用对话框**（无头 `Core.scene` 为 null 会 NPE），改成「拒绝一次 + 再点一次算确认」，
`JOB_FORCE` 只放行一次（第三次又问）。

### 62.3 坑

1. `jobSync()` 是第二条投递路径（`httpRaw("POST","/jobs")` 自己拼，不走 `jobSubmit`），最初漏记基线 →
   端到端用例第一次写入没被拒绝，直接暴露。
2. 写成功后必须 `forgetOrig`，否则同一台处理器的下一次写入会误报冲突。

### 62.4 复跑

`run_ui_smoke.py` EXIT=0（`MAICONFLICT:ok`、`MAIUNDO:ok`、`MAIDIAG:版本：0.10.1`、作业三路全过、
摘要行 `job conflict gate: first write refused, second click overwrote`）；`gate.py --full` 见 §62.5。

### 62.5 环境发现：61 个残留 JVM 把 probes 档打红

本轮 `gate.py --full` 首跑 `probes FAIL`（26 条全红，`insufficient memory for the Java Runtime Environment`）——
`Get-Process java` 有 **61 个** `out/jre21 -jar out/_server160.jar` 残留（最早 20:17，每只 30-220 MB），
可用内存只剩 1.4 GB。清掉后 probes 26/26、gate 16/16 in 47.5s。泄漏源未定位（连进程都没退），
下一刀候选：`Server` 加 finally 兜底 + 收尾扫孤儿 JVM。

### 62.6 边界与下一刀

只覆盖单处理器一次写入。P5 剩下的主体是**多处理器事务写入**（一个作业 N 段代码、全过才写、任一台失败整体回滚），
要先扩 sidecar 作业契约（`jobqueue` 的 job 从 `code` 改成 `codes[]`）。冲突检测只比代码文本、不比链接表。

## §63 孤儿 JVM：子进程跟父进程一起死（2026-10-31）

### 63.1 根因

1. `tools/mlogsim.py` 原 `close()` 只有 `send("exit")` + `wait(15)`，超时 `kill()`；父进程先死就没人发这条命令。
2. `tests/mlogauxiliary/run_ui_smoke.py` 的 `main()` **从不调用 `srv.close()`**（`srv = M.Server(...)` 在 :291，三个 return 都不收尾）⇒ 每跑一次泄漏一个 JVM。
3. `tests/probes/run_probes.py:265-270` 有 try/finally + `close()`，但整轮被 gate 超时 / Ctrl-C 硬杀时 python 跑不到 finally；Windows 父进程被 TerminateProcess 不连带杀子进程。

### 63.2 改动（5 文件 +238/−5）

| 文件 | 改动 |
|---|---|
| `tools/mlogsim.py` | +200：`_win_kill_with_parent()`（Windows job object，`KILL_ON_JOB_CLOSE` = 0x2000，`SetInformationJobObject(job, 9, ...)`，句柄 restype/argtypes 都设成 `c_void_p`）、`_LIVE_SERVERS` + `atexit`、`sweep_orphans()`、`close()` 幂等重写（`_closed` + 发 exit + wait15 + kill + 关 stdin/stdout + CloseHandle）、CLI `--sweep-orphans`、docstring 一段 |
| `tests/probes/run_probes.py` | +10：一轮跑完 `M.sweep_orphans()`，有残留就打印 `swept N stale JVM(s)` |
| `tests/mlogauxiliary/run_ui_smoke.py` | +13/−3：`__main__` try/finally 调 `M._close_live_servers()` |
| `tests/logicd/run_logicd_tests.py` | `wait_job` 超时 30 → 60 s（护栏，不改状态机） |
| `tools/README.md` | +16：「子进程生命周期（孤儿 JVM）」整节 |

`sweep_orphans()` 只认 `java.exe` 且命令行含 `_server160.jar`/`_server159.jar`/`_server146.jar`/`jre21`（游戏本体也跑 java.exe），且 **ppid 已死** 才杀 —— pid 复用会让死父看起来活着，宁可漏杀不误杀；拿不到 PowerShell 就返回 `[]`。

### 63.3 证据

- 硬杀父进程实验（`out/_jvm_test1.py`）：子 python 打印 `UP 72948` → `taskkill /PID <python> /F` → 3 秒后 `ParentProcessId` 为该 python 的 java.exe = `[]` → `RESULT PASS job object took the child down`。
- 扫孤儿实验（`out/_jvm_test2.py`）：baseline `[73508, 5104]` → `--sweep-orphans` 打印 `orphan sweep: 2 stale JVM(s) 73508 5104` → `[]`。
- 正常跑不泄漏（`out/_jvm_test3.py`）：`out/scenes/benches/processor-bench.msch --steps 20 --base 4,32` exit 0、`print: 8|88|88|8`，前后 java 计数 `[]`。

### 63.4 复跑

`tools/kb.py build` → `{chunks: 6421, files: 65}`；`gate.py --full` → **16/16 passed in 42.3s**（probes 29.4 s / logicd 17.9 s / ui 5.2 s），gate 前后 `java.exe` 计数都是 `[]`。
首跑曾 `logicd FAIL`（`job … never reached ('rejected',)`，最后状态 `running`），单独跑 12/12、复跑全绿 ⇒ 判并行满载假超时。

### 63.5 下一刀

job object 是 Windows 专属（非 Windows 只剩 atexit，硬杀仍可能留孤儿，靠 `--sweep-orphans`）。回 P5 主体：多处理器事务写入（一个作业 N 段代码、全过才写、任一台失败整体回滚），要先扩 sidecar 作业契约（`jobqueue` 的 job 从 `code` 改成 `codes[]`）。

## §64 v0.11.0：设置页里填模型地址 / 密钥 / 模型（2026-10-31）

**结论**：模型档从「只有命令行能开」变成「游戏里填三行 + 点一下」。sidecar 三个新端点
（`GET /llm` / `POST /llm` / `POST /models`），provider 在进程内热替换，**不用重启**。
密钥只进不出：任何响应里只有 `key_set` 与掩码尾巴。

**改动**（报告 `out/takeover-20261024/64-llm-settings.md`）：
- `tools/logicd.py`：`LLM_STATE` + `_mask_key` / `llm_state` / `models_url` / `fetch_models` / `apply_llm`；
  三条路由；main 里把命令行参数灌进 `LLM_STATE`。
- `tools/jobqueue.py`：`template_provider()` 的报错追加中文指引（当前是模板档 → 去设置填模型）。
- `MlogAuxiliary/scripts/main.js`：`MOD_VERSION 0.11.0`、三个 settings 键、`llmText/llmSave/llmRefresh/llmApply/`
  `llmFetchModels/showPickList/showLlmModels/llmEnable/llmUseTemplate`、设置页「大模型」段、诊断一行、`maiLlmProbe()`。
- `MlogAuxiliary/mod.hjson` 0.11.0 + description；README 新节；`tools/README.md` 接口十三个 + 模型档段落；
  规划 §9 新增 P4.5 行。

**测试**：`test_llm()` 6 项（假 OpenAI 端点）；ui smoke `MAILLM:ok` + 五条源码红线。
**本轮抓到的真 flake**：job id 是 `sha1(snapshot+desc+mode)`，`test_llm()` 用固定 desc + 默认 `out/jobs`，
第二次跑幂等命中上一轮的 done 作业 → provider 没被调用 → 只在「stub 见过 chat 端点」这条炸。
修法：私有 `--jobs-dir`（mkdtemp）+ desc 带 `stub.port`。**任何用 `/jobs` 的测试都必须给私有队列目录**。

**复跑**：logicd 测试 protocol 26 / jobs 12 / provider 9 / llm 6；ui smoke EXIT=0（`MAILLM:ok 82`、
`MAISELF` 102 行、`MAIDIAG` 版本 0.11.0）；KB `{chunks: 6460, files: 65}`；`gate.py --full` **16/16 in 46.3s**；
zip **71,363 B sha256 28EE9764CD91068E3CA86F8F2E23C076B3B8ABF53BEBB91DAF487D6651C69DD5**，装机 5 文件逐字节 OK。

**下一刀候选**：①设置页加「清空密钥」按钮 ②模型列表加搜索框（>80 条会截断）③P5 剩余：多处理器事务写入
（要先扩 sidecar 作业契约 `code` → `codes[]`）④模板档报错里带一个「去设置」的说明（现在只有文本）。

**环境教训**：`Server.js()` 会把任何含 `Error:` / `Exception` 的输出行当引擎错误抛出 → catch 里**不要**
`log("...: " + e)`，写死文案；run_code 的 JS 模板字面量装不了含反引号的 markdown → 先 `tools.write` 成片段文件，
再用纯 ASCII 的 python 脚本（中文锚点用 `\u` 转义）读文件拼进去。

## §65 v0.12.0：P5 第三刀上半 —— 事务写入（要么全写，要么全不写）

**规划原本的做法被改了**：§5 说这一刀要扩 sidecar 作业契约（`code` → `codes[]`）。实际做成**模组侧 N 个作业协调**，
每台处理器一个作业（各自的 links / snapshot / origin）—— 链接表、零链接门禁、self-repair 本来就是单台判据，
一个 job 塞 N 段代码反而更难判。代价是 N 次投递；sidecar / jobqueue / `/jobs` 零改动。

**改动**（`MlogAuxiliary/scripts/main.js` 120,137 → 127,985 字符，`node --check` 0，`+151/−4`）：
- `MOD_VERSION` 0.12.0；`snapshotText(b, why, batch)` 多 `batch` 字段；`saveUndoTo(root, b, why, batch)` 透传。
- 新增 `UNDO_BATCH` / `batchId()` / **`writeMany(items, why)`**：整批预检 → 整批冲突（有一台被改过就整批拒绝一次，
  再调一次 = 确认覆盖）→ 整批落盘快照（同一个 batch）→ 逐台 `configure`，catch 里把已写的按快照 `updateCode` 回滚。
- `undo()` / `undoFromDisk()` 支持整批：新增 `undoBatchFromDisk(batch, files)`，处理器已拆掉的跳过并删文件。
- 控制台 `api.maiWriteManyProbe(aJson, x, y)`：真引擎现放第二台处理器（结束拆掉），验整批写 / 整批撤销 / 第二台抛错回滚第一台。

**测试**：ui smoke 加 `MAIWRITEMANY` 探针 + 四条源码红线；`python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，
`MAIWRITEMANY:ok`、`MAIDIAG:版本：0.12.0`、摘要行 `batch write: ok 已写入 2 台（事务 …_b）：@0,0 @3,3 | 已回滚 2 台（…）`。

**复跑**：KB `{chunks: 6461, files: 65}`；`gate.py --full` **16/16 in 48.2s**；
zip **74,501 B sha256 54A9C528DEC1B89C5C34E5A0055293D90464705D67701048960AD54D654872E1**，装机 5 文件逐字节 OK。

**边界**：这一刀只有核心与探针，**没有面板按钮**（多台一起投递要面板同时轮询 N 个作业，是下一刀）；
`writeMany` 只吃已 done 的作业结果，不负责投递；回滚只还原代码不还原链接表；单台 `writeBuild` 路径未改。

**下一刀**：①面板批量入口（P5 第三刀下半）②联机拒绝写入的「无权限」提示 ③冲突检测不比链接表 ④打包/安装即用（用户已定最后解决）。

## §66 v0.12.1：模型档报错说人话（地址补全 / 端点自测 / 重启后自动重同步）

**症状**：玩家两张截图，`ERR L0 model endpoint unreachable: HTTP Error 404` 与
`ERR L0 empty reply`，都不指向原因。

**根因三条**：①`GET /llm` 显示 url 是 `https://api.deepseek.com/v1`（API base，
`HttpProvider` 直接 POST 它 → 404），同一 key 经 `POST /models` 是通的（模型名合法）；
②`empty reply` = 端点 200 但 content 空（推理模型吃光 `max_tokens 900` 或代理换路径）；
③sidecar 模型档只在进程内存，重启静默退回模板档。

**改动**：`tools/logicd.py` 加 `completion_url()`（base → `/chat/completions`）与
`POST /llm/probe`（`probe_model()`：最小 chat 调用，回 status/finish_reason/
content_len/reasoning_len/raw）；`tools/mlogprovider.py` `max_tokens` 900→1600、
`HTTPError` 分支带 404 提示与 body、空回复带 `_why_blank()` 诊断、`_alt_text()`
兜底 reasoning；`main.js` `MOD_VERSION 0.12.1`、四个按钮（多「测试端点」）、
`llmProbe()`、`llmSync()`（载入与开面板时把 `Core.settings` 的模型档推回 sidecar）、
`llmEnable()` 比对模型列表。

**测试**：logicd `llm` 6→8、`provider` 9→11（stub 加 `blank`/`strict`）；
ui smoke 加三条 v0.12.1 源码红线。实测 protocol 26 / jobs 12 / provider 11 / llm 8 EXIT=0，
ui smoke EXIT=0（`MAIDIAG:版本：0.12.1`、103 行/格、`MAILLM:ok 82`）。

**假失败**：连挂两次 `FAIL jobs: … never reached ('done',) (last state 'running')`，单独跑
12 项全过、自建探针也对，第三次全绿 ⇒ 环境性偶发（同 §63 的并行满载假超时）。
`jobqueue._run` 的 `_materialize` 调用无 try/except，真挂起要看 sidecar stdout。

**文档**：`MlogAuxiliary/README.md` 标题 v0.12.1 + 新节；`tools/README.md`
「接口十四个」+ `POST /llm/probe` 段；`docs/Mlog辅助-规划.md` P4.5 行补 v0.12.1。

**下一刀**：面板批量入口（P5 第三刀下半）/ 联机无权限提示 / 打包安装即用（用户定最后解决）。

## §67 logicd v0.12.2：重投不再回放旧结论（sidecar 侧，模组未变）

**症状**：玩家把 03:01–03:07 那三条作业都变成 `rejected / attempts 3 / provider-error: empty reply`，
端点修好之后原地再点一次「生成」，拿回来的还是那条 `empty reply`——模型根本没有被再问一次。

**根因**：job id 是内容寻址的
（`tools/jobqueue.py:67` `job_id()` = `sha1(json.dumps({'snapshot','desc','mode'}))[:16]`），
而 `enqueue()` 把所有同 id 提交一律当幂等：`old = self.jobs.get(job['id']); if old is not None: return dict(old), False`。
模组侧 `jobBody()` 送的快照（`main.js:2104` `regionSnapshot()`）不含时间戳/nonce，
所以「同一台处理器 + 同一句话」永远是同一个 id ⇒ **已终态的作业把自己的内容 id 粘死了**。
用 `out/jobs/af91a583e578f39b.json` 的 snapshot 本地重算 hash 与存储 id 完全一致，实证了这条链。

**改动**（`tools/jobqueue.py`，模组不动、不用重装——游戏安装目录至今未定位，重装成本高）：
- 新增 `RETRY_MAX = 99` 与 `Queue._free_id(base)`：旧作业**还在飞**（queued/running）时幂等；
  已终态（done/rejected/failed/cancelled）就把这次的 id 顺延成 `<id>-2`、`<id>-3`…，
  并写 `retry_of` 指回首轮，失败那次仍留在盘上可对比。`enqueue()` 改用它。
- 同版修掉两处写盘薄弱点（§66 记为「环境性偶发」的那次 `FAIL jobs: … last state 'running'` 的真因）：
  `Store.save()` 的 `os.replace` 在 Windows/OneDrive 目录下会撞 `PermissionError: [WinError 5]`
  （`tools/jobqueue.py:177`，同步引擎/扫描器短暂占住文件）——异常被 `_loop` 的
  `except Exception: traceback.print_exc()` 吞掉后，作业**永久停在 running**，面板上「不动」和
  「还在跑」玩家分不出来。现在 save 对这类冲突重试 `SAVE_TRIES = 6` 次（`SAVE_WAIT = 0.03`
  递增退避，`_contended()` 只重试 PermissionError / WinError 5·32·33，`_replace()` 留出测试注入口），
  仍失败才抛；`_loop()` 兜底 `_strand()`：未预期异常 → `failed` + `worker-error` finding + 原因文本
  （已是终态的不覆盖）。
- 模块 docstring 补了「为什么幂等只对在飞成立」与写盘重试/兜底两段。

**测试**（`tests/logicd/run_logicd_tests.py`，`test_jobs()` 12 → 15 项）：
- 终态后重投：`id == <首轮>-2`、`retry_of == 首轮`、`wait_job` 等到 `done`、`attempts == 1`、`<id>-2.json` 落盘；
  在飞（`'慢一点'`，只含 `'慢'`，FakeProvider 取最长 key）时同 body 再投仍 `created:false`。
- 撞车：`_replace` 前两次抛 `PermissionError`、第 3 次放行 → save 成功、`tries == 3`。
- 卡死：`Store.save` 在 `state == 'running'` 时抛一次 `FileNotFoundError` → 作业必须 `failed` +
  findings 含 `worker-error` + 盘上也 `failed`，且 worker traceback 里确实是那个 `FileNotFoundError`
  （stderr 用 `contextlib.redirect_stderr` 收走，别污染 gate 输出）。

**复跑**：`tests/logicd/run_logicd_tests.py --no-sim` → protocol 26 / jobs 15 / provider 11 / llm 8，EXIT=0；
`gate.py` 默认 11/11（1 warn kb → `--kb-build` 后 11/11，163 源文件）；
`gate.py --full` **16/16 in 68.4s**。

**诊断教训（省下一轮）**：`tests/logicd/run_logicd_tests.py:72` 的 `Server` 用
`stderr=subprocess.STDOUT` 起 sidecar，**ready 行之后没有人再读那条 pipe** —— worker 线程的 traceback
全躺在 pipe 缓冲里，所以「作业卡在 running」在测试输出里看不到任何原因。要看它，就把 sidecar 按同样的
参数单独起一份并且开一个线程持续 drain stdout（本轮 `out/_diag2.py` 的做法，用完删掉）。

**边界**：只改 sidecar，模组版本仍是 0.12.1（`MlogAuxiliary/mod.hjson` 未动）；`<id>-N` 上限 99 轮，
超出用随机尾巴；`retry_of` 只指首轮，不链式；写盘重试只在「文件刚被别人占了一下」的语义上重试，
目录不存在/权限真不足这种错第一次就抛。

**下一刀**：①面板批量入口（P5 第三刀下半）②联机拒绝写入的「无权限」提示 ③冲突检测只比代码文本、不比链接表
④打包/安装即用（用户已定最后解决）。

## §68 logicd v0.12.3：推理模型把回复预算想光了（空回复 → 升档重试 + 诊断）

- **症状**：v0.12.2 的 `<id>-2` 修复生效（玩家重启后重投确实换了 id），但作业仍 `rejected`；
  真机作业 `f122e54f918974ff-2` 的 finding 写明 `finish_reason=length; message keys=content,reasoning_content,role;
  usage={"completion_tokens": 1600, "prompt_tokens": 502}`，`content` 是空串。
- **根因**：`deepseek-flash` 是推理模型，`reasoning_content` 与 `content` **共用** `max_tokens`；
  旧的 `max_tokens=1600` 全被思考吃掉（prompt 只 502 token，不是 prompt 太大）。
- **改动**（`tools/mlogprovider.py` + `tools/logicd.py`，模组未动）：`DEFAULT_MAX_TOKENS = 4096`、
  `TOKENS_CEILING = 16000`；`HttpProvider.__call__` 见 `finish_reason=length` 自动升一档重试一次
  （×4、封顶 16000、超时同档 60→180 s）；`_budget_hint()` 把 `--llm-max-tokens` 写进错误；
  `LLM_STATE['max_tokens']` + `GET /llm` 回报 + `POST /llm` 接受（64..64000）+ CLI `--llm-max-tokens`；
  `/llm/probe` 预算 128 → `max(512, max_tokens//4)`；新增 `SIDECAR_VERSION = '0.12.3'` 与
  `GET /health` 的 `version`（老进程回 200 且没有 version，一眼可辨）。
- **测试**：`test_llm()` 8 → 11 项（⑨预算生效且阶梯 `[800, 3200]`、⑩一直截断时错误点名
  `--llm-max-tokens` 且阶梯 `[500, 2000]`、⑪`GET /llm` 回报预算 + 越界 400）；`test_protocol()` 断言
  `/health.version` 形状；`test_provider()` 默认预算断言改成 `== DEFAULT_MAX_TOKENS >= 4096`。
- **复跑**：`tests/logicd/run_logicd_tests.py --no-sim` → protocol 26 / jobs 15 / provider 11 / llm 11，EXIT=0。
- **真机复测未做**（本机无 key）：需要玩家重启 sidecar，`GET /health` 看到 `version: 0.12.3` 后重投同一句描述
  （id 会是 `-3`）。若仍空回复，把 `--llm-max-tokens 8192` 传给 sidecar，finding 里的 `completion_tokens`
  会直接说明还差多少。
- **边界**：模组版本仍是 0.12.1（面板版本号不会变，有意为之）；真端点联调只能在本机带 key 时做。
- **下一刀**：①面板批量入口 ②联机「无权限」提示 ③冲突检测比链接表 ④打包安装即用（最后）。

## §69 logicd + mai v0.12.4：模型思考过程跟着作业回来（v0.12.4，2026-10-31）

报告全文：`out/takeover-20261024/69-model-thinking.md`。触发是玩家 m01106：
「我说游戏内的模型思考过程。还有试图生成的报错信息没有变」。

- **报错没变的根因**：sidecar 还是 15:50:51 起的旧进程（`/health` 当时不报 `version`，无从一眼看出）。
  重启后 pid 51388、`version=0.12.4`。教训：v0.12.3 加的 `version` 是对的，但**改完 sidecar 必须重启**，
  而重启这件事只有玩家能做（密钥在他手里）。
- **新功能**：`HttpProvider._once()` 的每条返回路径经 `_with_reason()` 带上 `reasoning`（上限 12000），
  `jobqueue._run()` 在 error 分支之前把它写进 `job['reasoning']`（上限 20000），模组 `renderJob()` 在状态行
  下面摊开开头 16 行 × 40 字符；`api.maiJobReasoning(jobJson)` 取原文。
- **测试**：`test_provider()` 12 项、`test_llm()` 12 项（假端点回包带 `reasoning_content`）、ui smoke 新增
  `MAIJOBTHINK` + 2 条源码红线；`gate.py --full --kb-build` → 16/16 in 156.8s。
- **装机**：模组已拷到 `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary\`
  （`main.js` + `mod.hjson`），sidecar 已重启；玩家需重启游戏 + 开一次面板（`llmSync` 推模型档）。
- **下一刀**：等玩家真机复测（预算够不够 + 思考段显示效果）；之后回到 C（P5 面板批量入口 / 联机无权限提示）。

## §70 mai + logicd v0.12.5：F3 只弹描述框，框留到作业做完，角标点开作业管理（2026-10-31）

报告全文：`out/takeover-20261024/70-job-box.md`。触发是玩家 m01429 三条需求 + m01444 补充
「f3后的窗口简化到只有一个描述框」。

- **形态**：F3 松手只有 `openQuickJob(r)`（标题一行 + 一个输入框）；「生成」→ `startJobBatch()` 把框内每个处理器
  各投一个作业（P5 批量入口，补上第三刀缺的下半）；`jobBox.r` 留到这批作业全部终态再多留 8 s
  （`JOB_BOX_LINGER_MS`），右下角 `drawJobBadge()` 挂「作业 n/N · 生成中（点开看）」；`jobBadgeClick()` 世界坐标命中
  → `openJobManager()`（本次框选 + `GET /jobs?all=1&limit=24` 历史，详情看思考/findings/代码/写入/取消）。
- **sidecar**：`Queue.history()` + `/jobs` 的 `all` 参数 + `job_brief()`（剥 snapshot/code/bytes_b64/reasoning/links/assumptions），
  `SIDECAR_VERSION = '0.12.5'`。
- **验证**：ui smoke EXIT=0（六个 `MAIJOBBOX*`/`MAIJOBMANAGER` 探针 + 八条源码红线，且 `return dumpRegion(...)` 必须消失）；
  `test_jobs()` 15→16 项；断言表新增 L2-54 / L2-55。
- **装机**：模组 0.12.5 需要重装 + 重启游戏，sidecar 需要重启（`/health` 的 `version` 应为 `0.12.5`）。
- **下一刀**：①真机复测（框留存观感 / 徽标点得着 / 管理窗历史）②联机「无权限」提示 ③冲突检测比链接表 ④打包安装即用（最后）。

## §71 mai v0.12.6：重试中的 findings 不是结论；角标贴住框的右下角（2026-10-31）

报告全文：`out/takeover-20261024/71-v0126-retry-and-badge.md`。触发是玩家两条反馈：
m01735「哦哦，成功了，但是在模型生成被截断的时候还有报错。」与 m01862「在矩形选框的作业提示框错位了。」

- **重试 ≠ 失败**：`findings` 是「当前这次尝试的问题」的实时字段，作业没终态前随时会被下一次尝试覆盖。
  真机 `out/jobs/ef8ff52c4b10a16a.json` 是 `done`/`attempts=2`，但玩家看到的是第一次被截断留下的
  `ERR provider-error ... (finish_reason=length; usage={"completion_tokens": 1600, "prompt_tokens": 513})`。
  模组侧加 `jobRetryHead()`（非终态 → `--- 上一次尝试的问题（第 N 次，还在重试）---`）与
  `jobFindingLines()`（截断补一行人话），`renderJob()` 与 `renderManagerDetail()` 都走；
  sidecar 侧 `_why_blank(doc, budget)` 把 `budget=16000 tokens` 与
  `the model ran out of room mid-thought, before it wrote an answer` 写进消息本身。
- **角标几何**：v0.12.5 的画字与点击区是两份几何，且 arc 的 `font.draw(text, x, y)` 里 **y 是基线、字往上涨**
  （原版 `InputHandler` 的尺寸字画在 `mouseWorldY() + offset`，就是这个语义），于是字压在框底边内侧、
  点击区却在框外——「错位」+「看得见点不着」。现在只有一份几何 `jobBadgeRect(a)`
  （`bx = a.x + a.w - w - 4/scale`、`top = a.y - 4/scale`、基线 `top - 字高`、宽高用 `GlyphLayout` 真量），
  `drawJobBadge()` 按它画、`jobBadge` 命中区按它收，并照原版 `font.setUseIntegerPositions(false)`
  （不关的话 `1/camerascale` 的小数位置被量化，字会飘开框角）。
- **验证**：ui smoke 新增 `MAIBADGERECT` 探针与四条几何断言
  （`right == box.x+box.w-4/scale`、`top == box.y-4/scale`、`y+h == top`、`x+w == right`）
  + 三条源码红线（`function jobBadgeRect(`、`font.setUseIntegerPositions(false)`、`api.maiBadgeRect = function`）；
  `test_provider()` 第 10 项要求空白消息里出现 `budget=` 与 `ran out of room`。
  结果：`protocol 26 / jobs 16 / provider 12 / llm 12`，ui smoke EXIT=0，`gate.py --full --kb-build` 16/16。
- **装机**：模组 0.12.6 覆盖 `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary\`
  后重启游戏；sidecar 也要重启（`/health` 的 `version` 应为 `0.12.6`，否则 `/jobs?all=1` 会被忽略）。

## §72 mai v0.12.7：框选框只在写入成功或主动关闭之后才消失（2026-10-31）

报告全文：`out/takeover-20261024/72-box-persist.md`。触发是玩家 m01944「选框不应该自行消失，
只能在应用后消失，或者主动关闭。」

- **删掉定时消失**：v0.12.5 的 `JOB_BOX_LINGER_MS = 8000`（终态后多留 8 s 就清框）整个删掉；
  `jobBoxTick()` 在 `jobBox.termAt > 0` 时只停止轮询，框与徽标继续画。
- **两条消失路径**：①`writeBuild()` 写成功后 `jobBoxWritten(b)`——只在该处理器落在 `jobBox.r` 里时才清；
  ②`closeJobBox()`：作业管理窗新增「关闭框选框」按钮，或右键点框右下角的徽标（左键仍是打开管理窗）。
  徽标文案加「右键关」，投递提示说明「写入成功后框才消失（右键徽标可主动关）」。
- **验证**：ui smoke 新增 `MAIJOBBOXPIN2`（终态后 `linger` 仍 true）、`MAIJOBBOXCLOSE`（回 `closed`）、
  `MAIJOBBOX4`（`{"box": false}`），加反向红线「`JOB_BOX_LINGER_MS` 不许再出现」与三条正向红线；
  断言表新增 L2-57（现 **116 条**：L1 31 / L2 57 / L3 6 / L4 4 / S 18）。
  `gate.py --full --kb-build` 16/16；logicd 未改（protocol 26 / jobs 16 / provider 12 / llm 12）。
- **装机**：模组 0.12.7 覆盖到 `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary\`
  后重启游戏；sidecar 仍是 0.12.6（这版没改 sidecar）。

## §73 mai v0.12.8：冲突检测连链接表一起比 + 联机「无权限」提示（2026-10-31）

报告全文：`out/takeover-20261024/73-v0128-perm-and-links.md`。触发是用户 m02047「按你的顺序」
（①联机无权限 + ②冲突比链接表 → ③快照补全 → ④打包）。只改模组，sidecar 仍是 0.12.6。

- **冲突基线扩到链接表**：新增 `JOB_LINKS` / `linkSig(b)`（`linkListOrNull` → `名字@x,y` 排序签名，
  null = 不知道不判）/ `linkSigText()`；`rememberOrig()` 记代码 + 链接表两张表，`forgetOrig()` 一起清，
  `conflictReason()` 报「代码 N 行 → M 行」和/或「链接表 [..] → [..]」。理由：模型写的链接名是按
  **投递那一刻**的链接表生成的，链接表变了「代码没变」也会写进一份链接名全红的程序。
- **联机权限（计划书 §5 遗留项）**：真源码取证——`BuildingComp.java:388-392` 的 `configure()` 只发
  `Call.tileConfig`；`InputHandler.java:705-729` 服务端两道闸 `Units.canInteract` +
  `admins.allowAction(… configure …)`，被拒只发撤销包（注释 `undo the config on the client`）⇒
  **客户端拿不到错误**。模组两层：`permWhy(b)` 复刻队伍闸（队伍不对整批一台都不写，消息以「无权限：」
  开头，单机不进）；`armWriteCheck()` / `writeCheckTick()` 写完 1.5 s 回读 `b.code` 与 `wantCode(res)`
  比，连续 3 次对不上才 `hint()` 报「无权限：… 的写入没生效（服务端没有接受）」，方块没了销案。
- **验证**：`node --check` 0；ui smoke EXIT=0（新增 `MAILINKCONFLICT:ok` /
  `MAINET:net=false admin=false player=null perm=null` / `MAIWRITECHECK:offline queue=0` 三行 +
  八条源码红线，旧红线 `JOB_ORIG[procKey(b)] = String(b.code)` 跟着 `rememberOrig` 重构改成
  `JOB_ORIG[k] = String(b.code)`）；`gate.py` 11/11、`gate.py --full --kb-build` 16/16 in 45.9s。
  断言表新增 L2-58 / L2-59（现 **118 条**：L1 31 / L2 59 / L3 6 / L4 4 / S 18）。
- **装机**：模组 0.12.8 覆盖 `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary\`
  后重启游戏；sidecar 不用重启（这版没改 sidecar，仍是 0.12.6）。
- **没做**：真联机未实测（要开服）；下一步是快照补全 `blocks`/`items`/`liquids`/`units`/`enemies`。

## §74 v0.12.9 区域快照补全（库存 / 单位 / 敌方）

- **起点**：规划 §3.2 的 schema 表从 v0.4.2 起就有 `blocks`/`items`/`liquids`/`units`/`enemies`
  四段，实现只填了五段（`docs/Mlog辅助-规划.md:130-131` 自己写着「未实现」）。用户 m02326「继续」
  ⇒ 按 m02047 批准的清单做第 ③ 项。报告：`out/takeover-20261024/74-v0129-snapshot.md`。
- **模组**（`MlogAuxiliary/scripts/main.js`，0.12.9）：`regionSnapshot()` 多出 `blocks`（按格计数）/
  `items` / `liquids`（**按建筑身份 `String(bld.id)` 去重**：2x2 容器在四个格子上是同一个 `bld`，
  100 铜必须还是 100）/ `stores`（每台有库存的建筑一条，上限 `SNAP_MAX_STORES = 16`）/
  `units:{total,types,teams}`（走 `Groups.unit`，按 `Math.floor(u.x / Vars.tilesize)` 落 tile 筛）/
  `enemies:{units,blocks,types}`（无本地玩家时两个计数恒 0 并带 `note`）；`regionText()` 多一行摘要。
  助手：`seqSize()` / `stockOf()` / `addInto()` / `countKeys()` / `stockText()` / `unitStats()`。
- **引擎坑（本轮踩了两次，写进断言表 L2-61）**：`Groups.unit` 是 `EntityGroup`，它把继承来的
  `Seq.get` 挡住了（v160.7 实测 `typeof Groups.unit.get === "undefined"`，真调用报
  `Cannot find function get`），而 `each` / `rawSeq()` 都在；同时它自己声明了 `size ()I`，
  把 `Seq` 的 `public int size` 字段挡住 ⇒ `Groups.unit.size` 是**函数**。两条一起踩就是
  `for(i = 0; i < seq.size; i++)` 一次都不跑、单位数静默变 0。修法：`seqSize()` 两种都试，
  `unitStats()` 先 `rawSeq()` 按索引走、`get` 不是函数就退回 `each(fn)`。
- **sidecar**（`tools/mlogprovider.py`）：`snapshot_facts()` 重写，优先用模组给的 `blocks`（没有才从
  `grid` 回退数），新增四行世界事实 `items stored in the area:` / `liquids stored in the area:` /
  `units in the area: 2 (dagger x2; teams: sharded 2)` / `enemies in the area: 1 unit(s) flare x1,
  1 enemy building(s)`；助手 `_num()` / `_top()`。`tools/logicd.py` 的 `SIDECAR_VERSION` → 0.12.9
  （**这版 sidecar 改了，玩家要重启 sidecar**）。
- **验证**：`node --check` 0；ui smoke EXIT=0（`MAISNAP` 六条 v0.12.9 断言：container 2x2 里 100 铜
  只能算 100 / `blocks.container == 4` / `stores` 恰好 1 条且坐标对 / `units.total == 1` 且
  `types.dagger == 1` / `teams.sharded == 1` / `enemies` 两个计数都是 0，另加七条源码红线）；
  logicd tests 全绿（provider 12 项，五条新断言）；`gate.py` 10/11（kb WARN，正常）、
  `gate.py --full --kb-build` 16/16。断言表新增 L2-60 / L2-61（现 **120 条**：
  L1 31 / L2 61 / L3 6 / L4 4 / S 18）。
- **没做**：真机未验（无头没有本地玩家 ⇒ `enemies` 恒 0 的分支被覆盖，有玩家时的敌方分支只有代码审）；
  `stores` 超 16 台只记前 16 条（总量仍是全的）；单位的血量/朝向没记。下一步 = m02047 清单第 ④ 项
  **打包安装即用**。

## §75 v0.13.0 作业启用/完成播报到聊天框

- **需求**（用户 2026-10-31 20:14 原话）：「在启用和完成的时候把状态发送到聊天框。格式是：
  `<MAI（逻辑徽标）><工作状态（如Generating）>（坐标）:(其它信息)`」。
- **三条引擎事实**（决定写法，详见 `out/takeover-20261024/75-v0130-chat-status.md`）：
  ①聊天框画字用 `Fonts.def`（`ChatFragment.java:48`），图标必须走 `UI.formatIcons(":logic:")`
  （`UI.java:746`，原版发送时也这么干，`ChatFragment.java:230`），写 `[logic]` 不认；
  ②`ChatFragment` 可见性 = `net.active() && ui.hudfrag.shown`，单机每帧 `clearMessages()`
  ⇒ 播报要按 `net.active()` 选通道，单机退回 `hint()`；
  ③`addMessage(String)`（`ChatFragment.java:311-319`）只插本地列表，不广播。
- **改动**（只动模组）：`MlogAuxiliary/scripts/main.js` 的 `netActive()` / `CHAT_DONE` / `chatIcon()` /
  `chatLine(status,x,y,info)`（固定 `MAI<徽标> <状态> (x,y): <信息>`，信息空不留冒号）/ `chatSay(text)`
  （联机进 `ui.chatfrag.addMessage`，否则 `hint`）/ `chatTrim()` / `chatXY()` / `jobChatStart()` /
  `jobChatDone()`（终态按作业 id 去重）；播报点四处：`startJob`、`startJobBatch`、`jobTick`、`jobBoxTick`；
  新自检口 `api.maiChatProbe()`。`MlogAuxiliary/mod.hjson` → 0.13.0。
- **验证**：`node --check` 0；ui smoke EXIT=0，`MAICHAT:ok icon=yes start=MAI<glyph> Generating (12,34):
  给核心补铜（job 3f2a1b9c） cancel=MAI<glyph> Cancelled (1,2)`（无头里 `UI.formatIcons` 也能换出真 glyph
  `\ue80e`）；两条格式断言 + 九条源码红线；`gate.py --full --kb-build` 16/16。断言表新增 L2-62
  （现 **121 条**：L1 31 / L2 62 / L3 6 / L4 4 / S 18）；规划 §9 加 v0.13.0 行；README 加「## v0.13.0」节。
- **没做**：真联机未实测（无头 `Vars.net` 为 null ⇒ 走 `hint()` 回退分支，聊天框分支只有代码审 + 格式单测）；
  播报不广播（`addMessage` 只写本地）；聊天颜色 / 条数上限没碰。

## §76 打包安装即用（v0.13.0 工具链；模组 0.13.0 / sidecar 0.12.9 未变）

清单第 ④ 项落地。详版 `out/takeover-20261024/76-v0130-package.md`。

- 新增 `tools/package.py`：`layout()` 决定包内容（模组三文件 + sidecar 闭包 + `rules/` 40 条 + `packaging/`
  脚本 + `VERSION.txt`），`build()` 出树与 zip（`out/_dist/MAI-0.13.0/`，63 文件、677,274 B；
  zip 235,177 B），`verify()` 真跑一遍，CLI `--verify/--out/--no-zip/--keep`。
- 新增 `packaging/`：`install.ps1`（探测目录、旧版改名 `MlogAuxiliary.bak-<stamp>`、拷完按 `VERSION.txt`
  逐文件核 SHA256）、`uninstall.ps1`、`stop-sidecar.ps1`，以及四个纯 ASCII 的 `.bat` 双击入口和 `使用说明.md`。
- 新增 `tests/packaging/run_pack_tests.py`，进 `gate.py` 的 `package` 步（在 `ui` 之后）：9 组断言，全部行为级。
- 三个坑（都属「看起来成功」）：①`rule_ids` 在函数内导入，行首正则的闭包漏掉它 ⇒ `/health` 正常、`/analyze`
  才炸，改用 `ast.walk` 的 `local_imports()`；②存档目录由 `Vars.java:494-495` 决定（Steam 版 = 游戏目录旁的
  `saves/`），第一版把 `%APPDATA%` 排前面导致装到了游戏不读的目录，已改成 Steam 优先、`%APPDATA%` 兜底；
  ③`install.ps1` 被编辑器回写后丢了 UTF-8 BOM，PowerShell 5.1 按 ANSI 解码 ⇒ 安装成功但中文乱码，已恢复
  BOM 并把「`.ps1` 必须有 BOM / `.bat` 必须纯 ASCII」写成断言。
- 装机：双击路径装到 `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary`，
  `main.js` sha256 `515CFBD0…F2E4` 与仓库一致；测试产生的两个 `.bak-*` 已删。
- 没做：非 Steam 版的真机验证、Steam 库以外路径的自动探测、`停止逻辑后端.bat` 按端口过滤（它杀所有
  `logicd.py` 进程，故本轮只做源码断言没真跑）。
## §77 v0.13.1 后端随包 + 模组自己拉起（2026-10-31）

用户 m03139「能做即装即用吗」→ 给三档方案后选 A：打 exe + 模组自己拉后端；另要一份 JS 移植评估书（选 C 的后半）。

- 目标：把 v0.13.0 的「第三步」（双击 `启动逻辑后端.bat` 留窗口 / 源码检出要装 Python）去掉，玩家侧零依赖。
- `tools/package.py`：`EXE_SUB = 'bin'`、`exe_sources()`（mtime 判定是否重建）、`pyinstaller_cmd()`、
  `build_exe()`（PyInstaller **onedir**，缓存在 `out/_exe/`）、`sidecar_entry()`（优先 `bin/logicd.exe`）、
  `start_sidecar()` 返回 `(proc, banner, kind)`、`verify()` 增加「exe 存在且 >1 MB、`_internal` 在、必须由 exe 启动」、
  `main()` 增加 `--no-exe`。
- `tools/logicd.py`：`FROZEN = getattr(sys, 'frozen', False)` 分支（`HERE = sys._MEIPASS`、
  `WROOT = dirname(sys.executable)`、`MLOG_JOBS_DIR` 默认 `WROOT/out/jobs`）、`SIDECAR_VERSION = '0.13.1'`、
  `SNAP_DIR = WROOT/out/snapshots`、`'path'` 相对 `WROOT`。数据表与 `rules/` 靠 `--add-data` 放进 `_MEIPASS`，`rule_ids.py` 不用改。
- `MlogAuxiliary/scripts/main.js`（0.13.1）：`SIDE` 状态机 + `sidecarExe()` / `sidecarDir()` / `sidecarPort()` /
  `sidecarSpawn()`（`ProcessBuilder` 字符串数组 + `redirectErrorStream` + `redirectOutput(sidecar.log)`）/
  `sidecarTick()`（400 ms 轮询，25 次失败才提示）/ `ensureSidecar()`（`openPanel()` 与 `jobSubmit()` 各调一次，
  `starting` 时 `jobSubmit` 直接回「稍等再投一次」不落作业）/ `sidecarStateText()` / `api.maiSidecarProbe`。
- `packaging/启动逻辑后端.bat`：改成 exe 优先（`goto run_exe`），没有 exe 才退回 `python sidecar/logicd.py`；
  `packaging/使用说明.md` 从三步变两步，故障表补 `sidecar.log` 位置。
- 三个坑：①**onefile 在这台机器上被策略拦住**（`[PYI-xxxx:ERROR] Could not create temporary directory!`，
  换 `%TEMP%` 子目录也一样）⇒ 只能 onedir；②`Runtime.exec` 按空格切路径，`Program Files (x86)` 必炸
  ⇒ `ProcessBuilder` 数组；③不重定向输出的子进程攒满 64 KB 管道会卡死 ⇒ 重定向到 `sidecar.log`。
- 修掉一处编辑残留：`sidecarExe()` 里 `getMod("mods." === "" ? "" : "mlog-auxiliary")` → `getMod("mlog-auxiliary")`。
- 测试：`tests/packaging/run_pack_tests.py` 加 exe/launcher-bat/exe-kind 断言（10 组全绿）；
  `tests/mlogauxiliary/run_ui_smoke.py` 加 `MAISIDECAR` 探针与七条红线（红线不能带行尾注释 —— `code_only` 已剥注释）。
- 结果：包 163 文件 / 18,518,357 B，zip 8,379,571 B；`--verify` PASS；ui smoke EXIT=0；`gate.py --full --kb-build` 17/17。
- 同时交付 `docs/Mlog辅助-JS移植评估.md`（3,000–3,500 行 JS / 14–20 人日 / 六个真风险 / 三档方案 / 六阶段路线），
  规划 §8 把「把 sidecar 整体搬进 Rhino」写成明确不做并链接该评估书。
- 没做：模组在真游戏里拉起 exe 的链路未实测（无头里没有 exe，只验了 `noexe` 退回）；`停止逻辑后端.bat` 仍只做源码断言；
  `_internal` 体积未裁剪（zip 8.4 MB 是带运行时的必然代价）。

## §78 v0.13.2：不可达语句变成 WARN + 生成改用标签 + 面板摊开假设与成本

- 起因：用户 m03631「插件生成的逻辑问题很多，好像没有过逻辑审查」。取证 `out/jobs/43fe34c6557e3eeb.json`：
  `jump 12` 少算一行跳进块中间，`L11` 永不执行；`mlogcheck` 当时回 `no issues found`，只有 `--cost` 里那句 `UNREACHABLE`。
- 通路：`analyse()` 新增 unreachable 段（WARN finding）→ `jobqueue._set()` 存 `cost` → 面板两段（假设 + 成本）→
  重试提示（findings 非空才重试，现在可达性也算 findings）。
- 生成侧：`build_prompt()` 禁行号、给标签规则与 free tier 骨架。标签零成本：`msch.build_logic_data()` 只写代码原文。
- 当场抓到自己的 5 个内置模板结尾死 `end`（`patrol`/`item-threshold`/`radar-fire`/`timer-flush`/`counter`），已删。
- 验证：`tests/run_tests.py` 46/46、`ruleids` 0 problem、`logicd` 全绿（protocol 26 / jobs 16 / provider 12 / llm 12）、
  ui smoke `MAIJOBPANEL:ok assumptions=2 cost=3`、`node --check` 0、门禁 17/17。
- 测试基础设施坑：`mlogsim.Server.js()` 用 `' '.join(script.splitlines())` 送脚本，真实换行会被拼成空格；
  要在 JS 字符串里送换行，Python 源码必须写 `\n`（值 = 反斜杠 + n，再由 Rhino 解析）。
- 详见 `out/takeover-20261024/78-v0132-unreachable.md`；断言表 L2-65；README「## v0.13.2」。
## §79 v0.14.0 W1：一个选框就是一个工作区（数据层）

**需求**：用户 m03632「相当于每个选框就是一个工作区快照。即使写完一次逻辑也不会让工作区消失，保留上下文，可以选择归档或释放」；
m03723「先完成两个小功能吧。然后规划一下工作区快照再继续」；m03985「我同意按照你的做」。
规划稿 `docs/Mlog辅助-工作区快照-规划.md` 分 W1–W5，本轮只做 W1（数据层），**纯模组侧、sidecar 不动（仍 0.13.2）**。

**数据模型**：`Vars.dataDirectory/mlogauxiliary/workspaces/<id>.json`，字段 `schema/mod/id/name/state/map/world/bounds/created/updated/procs[]/jobs[]/archivedAt`；
`procs[]` 每台一行 `{k,x,y,block,desc,links,code,accepted,history}`；上限 `WS_KEEP=200` / `WS_HISTORY=20` / `WS_JOBS=50`，按 `updated` 淘汰。
复用判定 `wsFindActive(rect)`：选框**中心**落在 active 工作区 `bounds` 内且 `map` 相同，命中则 bounds 取并集（`wsAttach`）。

**改动**（`MlogAuxiliary/scripts/main.js`，现 4,366 行）：新段 30 个 `ws*` 函数；钩子 `startJobBatch`（`wsAttach` + `wsRecordJob` + 提示）、
`jobBoxTick`（`wsRecordTerminal`）、`startJob`（`wsTouchHere` + `wsRecordJob`）、`writeBuild`（`wsAccepted`）、`writeMany`（逐台 `wsAccepted`）、
`openQuickJob`（标题带工作区名）、`api.maiJobBox`（加 `ws`）；新口子 `api.maiWorkspaceList/Archive/Restore/Release/Current`；
自检口 `api.maiWorkspaceProbe()`（内存表跑十一件事，返回 `ok dir=no|yes mem=yes`）；版本三处 0.14.0。

**踩坑**：探针最初写在工作区段（:1290），早于 `var api = {`（:3594）⇒ 加载即 TypeError；已移到 `api.maiJobCancel` 之前（现 :4184）。
ui smoke 成功路径的展示白名单不含 `MAIJOBPANEL:`/`MAIWORKSPACE:`，导致断言通过却看不到证据——已补进白名单（`tests/mlogauxiliary/run_ui_smoke.py` 末尾）。

**验证**：`node --check` 0；ui smoke EXIT=0 且可见 `MAIDIAG:版本：0.14.0`、`MAIWORKSPACE:ok dir=yes mem=yes`、`MAIJOBBOX*` 的 JSON 出现 `"ws":null`。

**没做**：界面（W2）、`mode:"improve"`（W3，`jobqueue.normalize()` 只认白名单字段）、跨地图迁移。

报告：`out/takeover-20261024/79-v0140-workspace-w1.md`；断言表 L2-66。

## §80 v0.14.1 工作区快照 W2/W3/W4：界面 + 继续改进 + 导入导出 + 蓝图入口（2026-10-31）

承接 m03632 的工作区快照要求与 `docs/Mlog辅助-工作区快照-规划.md`（W1–W5）。W1 = v0.14.0（提交 `5df6ece`，只有数据层），
用户 m04147 原话「继续，直接做完，然后我验证」⇒ 本版把 W2（界面）、W3（继续改进）、W4（导入导出 + 蓝图入口）一次做完。

**模组侧**（`MlogAuxiliary/scripts/main.js`，现 4,7xx 行，`MOD_VERSION = "0.14.1"`）：新段「工作区界面（v0.14.1，W2/W3/W4）」
放在「区域面板」段之前，含 `wsTimeText`/`wsRowLabel`/`wsBoundsText`/`wsProcLines`/`wsJobLines`、
`wsRestoreBox`（把 `jobBox` 指到工作区 bounds，**故意不给 ids** ⇒ `jobBoxState()` 的 `total === 0` 不画徽标、不轮询空作业）、
`wsRename`/`wsExportText`/`wsExportToDisk`/`wsImportText`（复制语义，撞 id 换新 id）、
`renderWorkspaceDetail`/`renderWorkspaces`/`openWorkspaceDialog`（仿蓝图对话框）、
`wsImprovePayload`/`wsImproveBatch`（每台写过代码的处理器各投一单 improve）、
`blueprintList`（`Vars.schematics === null` 回空数组 —— 无头里它就是 null）、`wsFromBlueprintName`、`renderBlueprintPicker`。
钩子：`jobBody(b, desc, wsInfo)` 在有 wsInfo 时 `job.mode = "improve"` + `job.workspace`；`jobSubmit(..., wsInfo)` 透传；
`startJobBatch(targets, desc, rect, improve)` 逐台算 payload；`openQuickJob` 多一个「改进上一版」按钮；
`wsRecordTerminal` 记 `findings`（`prevFindings` 来源）。新口子 `api.maiWorkspaceDialog/Export/ExportDisk/Import/RestoreBox/Rename/Improve/ImprovePayload/RowLabel/BlueprintList/WorkspaceFromBlueprint`，
`tools/jobqueue.py:_ws_finding()` 把 `{sev,rid,msg}` 渲染成 `WARN <rid>: <msg>`（原来 `str(dict)` 把 Python repr 送进 prompt）。入口：主面板（设置 → Mlog辅助）与作业管理窗底部的「工作区快照」按钮（红线 `d.buttons.button("工作区快照"` 守着）。自检口 `api.maiWorkspace2Probe()` → `MAIWS2:ok`（14 项：rowlabel/bounds/proclines/joblines/export/import/import-id/import-procs/rename/payload/payload-code/payload-id/restorebox/restorebox-ids/restorebox-msg/blueprint/blueprint-miss/improve-miss）。

**sidecar 侧**（teammate `sidecar-dev` 实现，我复核）：`tools/jobqueue.py` 加 `WS_*` 上限与 `workspace_of()`/`_ws_code()`/`_ws_text()`，
`job_id(snapshot, desc, mode, prev_code=None)` **仅 improve** 把 prevCode 计入 blob（new/edit id 与 v0.13.2 逐字节不变，
两个硬编码 legacy id 锁死），`normalize()` mode 白名单加 `improve`、返回 dict 带 `workspace`；
`tools/mlogprovider.py` 的 `previous_version(job)` 在 `=== task ===` 前插 `=== previous version (same area) ===`，
段本体 ≤ 1198 字符（留 2 字符给分隔空行，整段恰好 1200）；`tools/logicd.py` 的 `SIDECAR_VERSION = "0.14.0"`；
`tests/logicd/run_logicd_tests.py` 加 `test_improve()`（7 组）。

**验证**：`node --check` 0；`tests/mlogauxiliary/run_ui_smoke.py` EXIT=0 且可见 `MAIDIAG:版本：0.14.1`、`MAIWORKSPACE:ok dir=yes mem=yes`、`MAIWS2:ok`；
`tests/logicd/run_logicd_tests.py` → protocol 26 / jobs 16 / provider 12 / improve 7 / llm 12、write path 7 模板、`logicd OK`；
`tests/run_tests.py` 46/46；`gate.py --full --kb-build` 17/17。

**踩坑**：①`api.*` 赋值必须晚于 `var api = {`（W1 的老坑，这次全部放在 api 段内）②`var payload` 声明了却没传给 `jobSubmit`
⇒ improve 静默退化成 new，补第 4 个实参 ③PowerShell `python -c` 里拼引号/括号必炸，改文件一律写 `.py` 脚本再跑
④补丁脚本里的中文长串里出现 `'0.14.0'` 这种单引号会把字符串提前闭合，`SyntaxError` 却报在表达式第一行 —— 长文本改放独立 `.txt`。

**已知边界**：工作区不广播（联机写入仍走 `permWhy()` + `armWriteCheck()`）；W5（sidecar 索引）没做；
`GET /jobs?all=1` 的行现在带 `workspace`（单行最多 5–6 KB），暂不剥字段。

报告：`out/takeover-20261024/80-v0141-workspace-ui.md`；断言表 L2-67。

## §81 v0.14.2 写入后框不消失 + 框角两按钮 + 签名并入生成流程（2026-10-31）

承接用户 m04549 的四条：①「AI签名和挂载消失了，修复一下。」（m04559 澄清「挂载 = 签名行之后的 token」，
m04600「好像工作流没有过签名流程，并入一下吧。」）②蓝图文件保存方案 + 蓝图页直接开始对话（只出方案）
③「工作区不应该在写入之后就直接消失。」④「作业区的点开看和右键关文案应该替换成不会autoscale的两个按钮(查看、取消)。」
本轮做 ①③④，②按用户要求只写方案（`docs/Mlog辅助-蓝图方案.md`）。

**item3（模组）**：`jobBoxWritten(b)` 不再 `closeJobBox()`，只 `jobBox.written = (jobBox.written || 0) + 1`；
`jobBadgeText()` 去掉「（点开看 · 右键关）」散文、写入后追加「已写入 N 台」。框留到玩家主动关
（徽标右键 / 管理窗「关闭框选框」）或工作区被归档/释放。

**item4（模组）**：旧的三件套（`jobBadgeText`/`jobBadgeRect`/`drawJobBadge`/`jobBadgeClick`，文字当热区）换成新段
「作业框按钮（v0.14.2）」：`JOB_BTN_H=18`/`JOB_BTN_PAD=9`/`JOB_BTN_GAP=6`/`JOB_BTN_EDGE=4`、
`jobTextMeasure()`、`jobButtonLayout(a)`（从框右下角往左排：取消贴右缘、查看在左）、`drawJobButtons(r, a)`
（`Fill.rect` 底 + `Lines.rect` 边 + 字）、`jobButtonsClick()`（左键：取消=`closeJobBox`，查看=`openJobManager`）。
全部**屏幕空间即时绘制**（`Core.camera.project` 得像素、固定 `1/camerascale` 换算、`font.setUseIntegerPositions(false)`），
绕开 arc autoscale 与 stage 坐标换算（`Arc-Source` 里没有 `Stage.java`）。`api.maiBadgeRect` 改回报按钮几何；
`MOD_VERSION`/`mod.hjson` → 0.14.2。实测 `MAIBADGERECT`：`box{x:4,y:4,w:48,h:48}` / `status{y:-13,h:13}` /
`cancel{x:12,y:-35,w:36,h:18}` / `view{x:-30,...}`（取消右缘 12+36=48=框右缘，两钮间距 6 px，都在框外）。

**item1（sidecar，teammate `sidecar-sign` 实现 + Lead 复验）**：`tools/jobqueue.py:_materialize()` 与
`tools/logicd.py:compose()` 改成「先 `aigenerated.sign_text()` → 再门禁/分析 → 再 `build_logic_data()`」，
作业 JSON 与 `/compose` 回复多一个 `sig`（12 hex），`SignError` 变 `rid=sign-error` 的 ERR finding；
`SIGN_AUTHOR = aigenerated.SIGN_AUTHOR`（`MAI_SIGN_AUTHOR` 可覆盖）；`SIDECAR_VERSION='0.14.2'`。
**关键副产物**：`sign_text()` 的放置规则必须改 —— 6 个内置模板里 5 个以 2 操作数 `jump loop always` 结尾，
旧规则（补 `end` 再把 `end` 换成签名跳）会让签名行落在死循环之后 ⇒ `mlogcheck` 报 `unreachable-statement`、
面板每份产物多一条假警告、`run_logicd_tests.py` 的 `need(not res['findings'])` 必红。新规则：末条是无条件跳转 ⇒
token 进它的 value 槽并删掉后面那个死 `end`（`jump loop always 0 "sig"`），裸 2 操作数先补 `0`；
pid 对 `verify_text()` 会重建的 body 取哈希 ⇒ 既有 id 全部不变。`#` 注释只活在 payload 里、不进交付文本
（游戏汇编丢注释行，`b.code` 由汇编结果重建，留着会被 `armWriteCheck()` 误判成「无权限」）。

**机器验证**：`node --check` 0；`python tests/mlogauxiliary/run_ui_smoke.py` EXIT=0；`python tests/run_tests.py` 46/46
（`slot_end_kept: true→false`）；`python tests/logicd/run_logicd_tests.py` 全绿（protocol 26 / jobs 16 / provider 12 /
improve 8 / llm 12，含 **write path 7 模板**把 `/compose` 的 `bytes_b64` 真灌进 v160.7 处理器再回读 `b.code === code`）；
`out/_v142_tpl_sign.py` 6 模板签名前后行数/findings 不变且 token 恰好 1 个；`out/_v142_verify_sign.py` 三种边界
（2 操作数跳尾、`end`-only 可重签、既有 `写满停*.mlog` 重签逐字节不变）。

**踩坑**：①ui smoke 的 `code_only` 剥 `//` 注释 ⇒ 红线串不能带行尾注释，且必须与代码别名一致（`F.rect` 不是 `Fill.rect`）
②`sign_text()` 在「body 以无条件跳转结尾」时补 `end` 会自己造出 unreachable，必须改成写进 value 槽
③真机 `b.code` 是汇编结果、不含 `#` 注释 ⇒ 签名 payload 之外的注释不能出现在交付文本里。

报告：`out/takeover-20261024/81-v0142-sign-buttons.md`；断言表 L2-68 / L2-69；蓝图方案 `docs/Mlog辅助-蓝图方案.md`。

## §82 v0.14.3 游戏内文案统一

用户 m04981：「我测试，你你把游戏内文案洗一遍，简洁大方，标准是DP-AtomicStatesAssets.zip的文案。」

标准取自 `DP-AtomicStatesAssets.zip` 的 `content/blocks/*.json`：`description` 一句话直陈机制、无口语、无「你/我」、
无感叹号、括号全角、句末「。」。做法：`MlogAuxiliary/scripts/main.js` 里 609 条含 CJK 的字面量按区块分 10 批成对替换
（`out/_copy_b1.py`…`_copy_b10.py`，每对断言 `count`），术语统一（处理器/作业/工作区/框选/写入/预检/审查/模型档/
模板档/sidecar/蓝图），`->`→`→`、`鼠标下`→`光标下`、`写不进磁盘`→`无法写入磁盘`、`没有这个工作区`→`工作区不存在`、
`还没提交`→`未同步`、`sidecar 没在跑`→`sidecar 未运行`；设置页两段长说明与 `--- 模型假定的前提` / `--- 成本` 抬头压短；
`mod.hjson` 的 description 从约 4000 字版本编年史压到 375 字六句。

**本版最容易踩的坑**：文案被自检断言引用——`api.maiLlmProbe` 查「还没提交」（改「未同步」）、`api.maiConflictProbe`
查「被改过」（改「已被改动」）、`api.maiWorkspace2Probe` 的 `wsImproveBatch` 期望串（改「工作区不存在」）、
`tests/mlogauxiliary/run_ui_smoke.py` 的两条红线（「被改过」/「UNREACHABLE：永远执行不到的语句」），以及该文件
`MAIWS2` 分支里写错的 `fail(...)`（本文件没有 `fail`，一旦触发就是 NameError，改成 `problems.append`）。

**机器验证**：`node --check` 0；ui smoke EXIT=0（`MAIWS2:ok`、`MAILLM:ok 72`、`MAICONFLICT:ok`、`MAIBADGERECT` 几何不变）；
`tests/run_tests.py` 46/46；`tests/logicd/run_logicd_tests.py` 全绿（protocol 26 / jobs 16 / provider 12 / improve 8 /
llm 12 / write path 7 模板）。版本三处 0.14.3。

报告：`out/takeover-20261024/82-v0143-copy.md`；断言表 L2-70（总 129 条：L1 31 / L2 70 / L3 6 / L4 4 / S 18）。

## §83 v0.14.4：UI 改原版控件 + sidecar/模型档自启 + 删模板档 + 聊天播报开关

用户 m05298 / m05333 / m05432 三条需求合成一版（详见 `83-v0144-ui.md`）。

- **框角按钮改原版控件**：`jobWidgetBuild()` 把一张 `Table` 挂到 `Vars.ui.hudGroup`，按钮用
  `Styles.defaultt` 的 `TextButton`（`Scl.scl(84/40)`），标题用 `Label(Fonts.outline, Pal.accent)`；
  `jobButtonsSync()` 每帧用 `Camera.project` 对齐到框右下角；控件接管时 `jobButtonsClick()` 直接
  `return false`（防双触发）；**即时绘制保留为降级**（建表失败仍走 `drawJobButtons`）。
- **sidecar 随游戏启动**：脚本尾部与 `ClientLoadEvent` 各 `ensureSidecar(true)`，幂等。
- **模型档自动挂载**：`llmAutoSync()` 在 sidecar 探到 200 时把地址/密钥/模型推过去，60 s 节流。
- **删模板档**：模组删 `openPanel`/`panelShown`/`togglePanel`/`plan`/`renderPlan`/`compose`/
  `llmUseTemplate` 与探针 `maiPanel`/`maiCompose`/`maiApply`、AI 面板「直接生成」；`llmState` 默认
  `kind:"none"`、`llmText()` →「未配置模型」。sidecar 侧 `jobqueue.unconfigured_provider`
  （`fatal: True` ⇒ 只跑一次就 `failed`）成为默认，`apply_llm(kind=template)` → 未配置模型，
  `--jobs-provider` 默认 `none`；`TEMPLATES`/`/compose`/`/plan` 保留给测试。
- **设置页重排**：大模型 → 聊天播报 → 快捷动作 → 本地快检 → 说明 → 运行环境（最后）；sidecar 段删掉。
- **密钥默认遮**：`setPasswordMode(true)` + `setPasswordCharacter('*')`（专门修「Fonts.def 没有 bullet 字形，
  只设 passwordMode 等于没遮」），另加「显示密钥」按钮。
- **聊天播报开关**：`CHAT_SEND_KEY` 默认 false，`chatSay` 判据 `netActive() && chatSendOn()`。
- **投递前先查模型**：`jobSubmit` 未配置时直接回「未配置模型：…」。
- 断言表 L2-71（总 130 条）；ui smoke 与 logicd tests 全绿；报告 83。

## §84 v0.14.5：框角控件的 HUD 倍率自己调

用户 m06525：「做一个hud倍率自己调就好」。详见 `84-v0145-hud-scale.md`。

- `HUD_SCALE_KEY = "mlogauxiliary-hud-scale"`（`Core.settings`，`Settings.getFloat` at arc/Settings.java:357），
  范围 0.5×–2.0×、步长 0.1×，`hudScaleClamp()` 两位小数 + 非法值回 1。
- 设置页新段「框选控件」：`缩小` / 中间格（显示当前倍率，点一下 `hudScaleSet(1)`）/ `放大`；
  段位在「聊天播报」与「快捷动作」之间，运行环境仍最后。
- `jobWidgetBuild()`：`var hk = hudScale()` 后按钮 `size(S.scl(84) * hk, S.scl(40) * hk)`、
  `padLeft(S.scl(6) * hk)`、状态条 `padBottom(S.scl(3) * hk)`，`Label.setFontScale(hk)`（Label.java:306）；
  `jobButtonsSync()` 的 `JOB_BTN_EDGE` 乘 `hk2`。
- `jobWidgetDrop()`：倍率一变就摘表 + `jobWidget=null` + `jobWidgetTried=false`，
  下一帧按新倍率重建（arc 的 Cell 尺寸建表时定死，不重建改设置不生效）。
- 只动框角那一小块；即时绘制降级路径不变（`MAIBADGERECT` 仍 `box{4,4,48,48}`）。断言 L2-72（总 131 条）。

## §85 v0.14.6：发行包能被游戏直接导入 + zip 导入时 sidecar 自解压

用户 m06631：「游戏因为没有检测到mod.hjson无法从zip直接导入，解决一下」。详见 `85-v0146-import-zip.md`。

- 前半（游戏不认整包）：`Mods.importMod()`（Mods.java:107-149）→ `resolveRoot()`（Mods.java:1070-1074，
  zip 根**恰好只有一个目录**才下钻）→ `findMeta()`（Mods.java:997-1000，只在下钻后的那层找 `mod.hjson`）。
  整包顶层有 `mod/`、`install.ps1`、`使用说明.md` 等多项 ⇒ 不下钻 ⇒ 报「没有检测到 mod.hjson」。
- `tools/package.py`：`MOD_NAME = 'MlogAuxiliary'`、`build_mod_zip(tree, out_dir, name)`（顶层只 `MlogAuxiliary/`，
  缺 `mod.hjson` 就 `RuntimeError`）、`build()` 追加 `info['import_zip']`、`verify()` 第 7 步按游戏规则验形状。
- `tests/packaging/run_pack_tests.py` 第 3b 组：同一套规则 + 反向断言「整包 zip 顶层不是单目录」（否则自证）。
- 后半（导入后是 ZipFi）：`sidecarExe()` 原来直接取 `m.root.child(...)` 交给 `ProcessBuilder` —— zip 里的条目执行不了。
  新增 `sidecarIsZip()` / `sidecarCopyTree()` / `sidecarBinDir()`：磁盘安装走原路径；zip 安装解到
  `Vars.dataDirectory/mlogauxiliary/sidecar/<MOD_VERSION>/`（带版本号换新），首次 hint「从模组包解出逻辑后端（首次约 40 MB）…」。
  `sidecarCopyTree()` **不用 try/finally**（v160.7 Rhino codegen 会炸，ui smoke 有红线）。
- `packaging/使用说明.md`：新增「也可以在游戏里直接导入」小节 + 一条排障行。
- 产物：`out/_dist/MAI-0.14.6-mod.zip` 8408196 B（sha256 `4E177F36…CDFF60`）、
  `out/_dist/MAI-0.14.6.zip` 8428606 B（`574C22BD…990342`）。版本三处 0.14.6。断言 L2-73 / L2-74（总 133 条）。
- 真机未验一项：「zip 导入 → 首次解压 → sidecar 起来」需要玩家在游戏里点一次导入才能确认（无头环境没有真 ZipFi）。

## §86 v0.14.7：签名作者名改 `MAI`

用户 m07277「那个签名改成MAI吧」。签名行是 `jump 0 always 0 "aigenerated:<author>:<12hex>[:<payload>]"`，
作者名原来写死中文「猪猪鱼」——CLI 会 `print(sign(...))` 把整行打出去，cp1252 控制台（GitHub `windows-latest` 默认）
直接 `UnicodeEncodeError: 'charmap' codec can't encode characters`，这就是 CI 首跑 run 41231288166 里
`FAIL tool/aigenerated` 的根因。

- `tools/aigenerated.py`：`DEFAULT_AUTHOR = "MAI"`，文件头示例同步；`main()` 仍把 stdout/stderr
  `reconfigure(encoding="utf-8", errors="replace")` 兜底。
- `tools/mlog.py`：`--author` 帮助串改 `signature author (default: MAI)`。
- 下游无需改：`tools/jobqueue.py` / `tools/logicd.py` 读 `aigenerated.SIGN_AUTHOR`（`MAI_SIGN_AUTHOR` 仍可覆盖）。
- 旧签名不失效：`SIG_RE` 第 2 组才参与校验（只比哈希）。
- 版本三处 0.14.7（`main.js` `MOD_VERSION`、`mod.hjson`、`tools/logicd.py` `SIDECAR_VERSION`）；
  `MlogAuxiliary/README.md` 签名说明改 `aigenerated:MAI:<12 位哈希>`；`CHANGELOG.md` 加 0.14.7；
  断言表 L2-75（总 134 条）；规划状态表加 v0.14.7 行。
- 验证：`node --check` 0；`PYTHONIOENCODING=cp1252 python tools/aigenerated.py sign …` 退出码 0；
  `tests/run_tests.py` 46/46（`tests/expected.json` 里 `slot_line`/`terminal_line` 两条期望串同步换成 `MAI:…`）；
  `tests/logicd/run_logicd_tests.py` `logicd OK`；ui smoke EXIT=0；门禁 17/17。
- 坑：`tools/aigenerated.py` 的 `sign` 子命令没有 `-o`（只有 `post` 有），就地改文件；
  动过 `tools/*.py` 就要 `sync_mlogagent.py --mirror all` 再 `--global`，否则门禁 mirror/global 两处红。

## §87 v0.15.0：失败可诊断 + 侧车并发 + 运行环境自证

用户 m07441 提「打磨一下本体」，我给 A/B/C/D/E 六组问题清单，m07485 批准顺序后本轮做完 **A1+A2+B1+C1+C2+A3**（A4/D1/D2/D3 留 v0.15.1）。

- **A1 失败分类**（`tools/mlogprovider.py`）：七类 `transport/http-status/bad-json/empty/truncated/unparsable/config`；
  只有 `transport`+`empty` 重试（0.8/2.0/4.0 s 退避，`RETRY_TOTAL=3`），截断单独翻预算（`TRUNC_TOTAL=4`，×4 token、×3 超时），
  401/403/404 `fatal=True` 立即失败；`_fail()` 在 `doc` 是 `finish_reason=length` 时把类别改写成 `truncated`（不改写旧测试就红）。
- **A2 作业诊断**（`tools/mlogprovider.py` + `tools/jobqueue.py`）：`_diag()`/`_usage()`、`Queue._record_attempt()` 写
  `job.attempt_log[{n,ms,provider,url,model,budget,finish_reason,prompt_tokens,completion_tokens,total_tokens,reply_chars,attempt,http_status,kind,error}]`
  （`ATTEMPT_LOG_MAX=8`）+ `job.diag/model/provider`，finding 带 `kind`；`PROVIDER_EXHAUSTED=('empty','transport')` 第二次同类失败收手并 `_exhausted_text()`。
- **B1 并发**（`tools/jobqueue.py` + `tools/logicd.py`）：`Queue(workers=N)`、`_claim()` 在同一临界区置 `claimed`（防重复执行）、
  残留 `running|claimed` 复位 `queued`；`--jobs-workers` 默认 3。
- **C1+C2 sidecar 自证**：`/health` 加 `pid/port/exe`、`POST /ping`、`POST /shutdown`、`--idle-exit` 看门狗（无人 ping 且无在跑作业就退）；
  模组 `--port 0 --idle-exit 45` + 从 `sidecar.log` 读回端口（`sidecarLogPort`）+ `sidecarPing/sidecarOurs/sidecarVersionMismatch/sidecarRetire`，
  自己的旧版本自动退役，别人的只提示不动（`state="stale"`）。
- **A3 面板**：`JOB_WHY` 七条中文映射 + `jobWhyLines/jobEvidenceLines/jobLastAttempt/jobAttemptLine`；done 打「模型：…」「第 N 次调用：…」，
  失败打「为什么：…」与 `--- 诊断 ---`；探针 `api.maiJobDiagProbe` → `MAIJOBPANELDIAG:ok why=N ev=N …`。

验证：`tests/run_tests.py` 46/46；`run_logicd_tests.py` 新增 `diag`(5)/`life`(3) 段全绿；ui smoke EXIT=0；打包测试 11/11；门禁 **17/17 in 159.9s**；断言表 L2-76..L2-80（**139 条**）；报告 `87-v0150-diag.md`。

坑（详见报告 4 节）：补丁锚点撞上 `ScriptedProvider.__call__` 把 `HttpProvider` 整类删掉（`git checkout` 还原 + 先定位 `class HttpProvider:`）；
一行的 `python -c` 把 CRLF 测试文件改成 LF（`git diff --stat` 才看得出，`git show | python -` 在 PowerShell 里会假报 CRLF）；
`Queue.enqueue()` 返回 `(job, created)`；红线不能带行尾注释；红线锚点 grep 不到时脚本不写盘但 smoke 仍 EXIT=0。

## §88 v0.15.1：批次可辨识 + 框内续聊 + 提示留痕 + 作业窗过滤（2026-11-01）

用户 m07868「把你到的都作完，我再做检查。」⇒ 上一轮点名的 A4 / D1 / D2 / D3 全部做完。

- **A4**：`main.js` 的 `jobBody(b, desc, wsInfo, batch)` 把 `{i, n}` 写进作业体，`jobSubmit` 透传，`startJobBatch` 逐台带 `{i: i+1, n: targets.length}`；
  `tools/jobqueue.py` 的 `normalize()` 校验并夹紧（`batch` **不进 id**，同批仍靠 `-2/-3`）；`tools/mlogprovider.py` 的 `build_prompt()`
  加 `batch: the same sentence was sent to N processors; this is #i` + 「每台链接表不同」+ 「只用白名单里的链接名」。
- **D1**：框角第三按钮「续聊」（`{id: "follow", label: "续聊"}`，即时绘制与原版控件两套）；`jobFollowPick()`（光标下那台，须在框里，否则框里唯一那台）、
  `jobFollowAsk()`（预填工作区 notes / 上次描述）、`jobFollowSubmit()`（`wsAttach` + `wsImprovePayload` → `mode: improve`，作业挂回当前框，不新建框）。
- **D2**：`hint()` 写 `LAST_HINT{text, at}`；设置页「最近提示」段（复制全文 / 清空）；`lastHintLblRefresh()` 逐层判类型（无头 Cell 桩没有 `get()`）。
- **D3**：`managerFilter {text, onlyBad, limit: 100}` + `jobHit(job)`；管理窗「过滤 / 只看失败 / 显示更多（+100，上限 200）」+ 「符合条件 X / Y 个」。
- 探针：`MAIHINT:ok last=yes …`、`MAIFILTER:ok hit=2 of 3 btn=只看失败：关`、`MAIFILTER2:ok … btn=只看失败：开`。

验证：`node --check` 0；`run_logicd_tests.py` 的 `diag` 5→6；ui smoke EXIT=0（`MAIBADGERECT` 三按钮 `follow{-72,-35,36,18}`）；`tests/run_tests.py` 46/46；
断言表 L2-81（**140 条**）；版本三处 0.15.1；报告 `88-v0151-a4d1d2d3.md`。

坑：锚点 `pad(4).left()` + `pane(host).height(320)` 在 `main.js` 出现两次（作业管理窗 / 工作区窗）⇒ 改用「刷新」按钮行；
探针别自带前缀（否则打印成 `MAIFILTER2:MAIFILTER:ok`）；v0.14.2 的「恰好两按钮」红线要放宽；
`lastHintLblRefresh()` 必须先判 `typeof … === "function"`（模拟器 Cell 桩无 `get()`）。

交付：门禁 **17/17 in 175.0s**；包 `out/_dist/MAI-0.15.1`（166 files / 18605868 B），mod zip 8394851 B
`17E1F21D…BD9014`、整包 8415267 B `F8DF9611…794F3C`；包内 exe `/health` = 0.15.1 且 `POST /shutdown` 退出码 0；
装机前 8765 上残留 **0.14.7** 旧后端（pid 57340）已停，`install.ps1 -Silent` 装好（旧版 `MlogAuxiliary.bak-20261101-043054`）；
工作区提交 **`a4cba92`**（13 files +400/−19），公开仓 `main` = **`3ec8bb8`** + tag `v0.15.1`，Release 两附件已传，
CI run **41239699508** success。直连 GitHub 又断，走本机代理 `127.0.0.1:7890` 才推上去。

## §89 v0.15.2：取消后控件消失 + 聊天真消息 + 样板库 8 选 3（2026-11-01）

**触发**：用户 m08164 三条真机问题（+ m08187/m08216 两条格式澄清），并要求「蓝图方案先不用动」。

**改动**
- `MlogAuxiliary/scripts/main.js`：`jobWidgetCancel()` / `jobButtonsClick()` 取消分支补 `jobWidgetHide();`，
  `drawSelection()` 早退分支补 `jobWidgetHide()`（bug1 根因：控件挂在 `ui.hudGroup`，没人摘就一直留着）；
  `chatLine()` → `<MAI:logic:><状态>(x,y):详情`、新增 `chatPretty()`（`UI.formatIcons()`）、
  `chatSay()` 在 `chatSendOn() && netActive()` 时 `Packages.mindustry.gen.Call.sendChatMessage(s)`（bug3）；
  `MOD_VERSION = "0.15.2"`。
- `tools/mlogprovider.py`：新增 `EXAMPLES`（8 条已验证样例）与 `_examples_for(desc, limit=3)`，
  `build_prompt()` 换成「Program shapes … adapt one:」+ 3 条相关样例（bug2）。
- `tools/logicd.py`：`SIDECAR_VERSION = '0.15.2'`。
- 文档：`docs/Mlog辅助-蓝图方案.md` 增 §3.4（B5「详细」页续聊：反射取 `SchematicsDialog.info`、
  每帧按 `title.getText()` 重挂按钮、上下文读 payload v2）+ §3.5（三种载体对比，payload 为权威）；
  `docs/断言表.md` 增 L2-82、总数改 **141 条**（L1 31 / L2 82 / L3 6 / L4 4 / S 18，顺带修正 v0.15.1
  漏改的 139→）；`docs/Mlog辅助-规划.md` 加 v0.15.2 行；`CHANGELOG.md` 加 0.15.2 四条；
  `MlogAuxiliary/README.md` 更新聊天播报格式与样板说明；`MlogAuxiliary/mod.hjson` 版本 + description 两句。
- 测试：`tests/logicd/run_logicd_tests.py` 的 `diag` 增到 7 checks（样板库三条断言）；
  `tests/mlogauxiliary/run_ui_smoke.py` 的 `MAICHAT` 期望改成带尖括号的格式 + 两条新红线。

**教训**：`code_only` 剥 `//` 注释 ⇒ 红线串不能带行尾注释；「控件挂在 hudGroup」这类生命周期问题，
清数据（`jobBox = null`）与摘控件（`jobWidgetHide()`）必须成对，早退分支最容易漏。

## §90 v0.15.3：心跳 JSON 化 + 旧副本移出 mods（2026-11-01）

**触发**：用户 m08537「显示sidecar 已就绪：http://127.0.0.1:9046 但是仍然无法投递」，m08559「直接覆盖修复然后继续你的工作」。

**根因**（两条同时成立）
- `main.js` 的 `sidecarPing()` 发 `httpJson("POST", "/ping", {}, …)`，`httpRaw()` 用 `String(body)` 拼包体 ⇒
  实际发出 `[object Object]` ⇒ `logicd.py` 的 `json.loads` 失败回 400 ⇒ 回调把 `SIDE.state="failed"`、
  `spawned=false`、`url=""`，此后不再发心跳 ⇒ 后端 `serve()` 的 idle 看门狗（45 s）退出进程。
  `sidecarRetire()` 的 `"/shutdown", {}` 同病，所以退役重拉从未生效。
- `packaging/install.ps1` 把旧版移成 `mods\MlogAuxiliary.bak-<stamp>`，仍在 mods 下；
  `Mods.loadMods()` 按 `meta.internalName` 去重、扫描顺序靠后的赢 ⇒ 「装了新版，跑的是上一版」
  （真机现场：`MlogAuxiliary` 0.15.2 无 sidecar.log，`MlogAuxiliary.bak-…-050914` 0.15.1 的日志写着
  `logicd listening on http://127.0.0.1:9046` / `logicd idle for 45 s with no ping, exiting`）。

**改动**
- `MlogAuxiliary/scripts/main.js`：心跳与退役请求 body 改 `"{}"`；`SIDE` 加 `pingFail`，`code === -1` 立即退役、
  4xx/5xx 连续 3 次才退役、up 与 spawn 成功清零；`MOD_VERSION = "0.15.3"`。
- `packaging/install.ps1`：`$bakRoot = <saves>\mod-backups`，旧版移出 mods，历史 `.bak-*` 一并挪走
  （真机挪走 9 个）；末尾提示改 `(outside mods)`。
- `MlogAuxiliary/mod.hjson`：version 0.15.3，description 补心跳/备份两句。
- `tools/logicd.py`：`SIDECAR_VERSION = '0.15.3'`（行为未变）。
- 测试：ui smoke 加心跳正向红线与两条反向红线；logicd 的 `test_life` 加 `raw_post()` 断言 400/200；
  `test_improve` 的 echo 断言改成摘掉 payload 再比文本 + `decode_meta` 的 `ws`（v0.16.0 payload v2）。
- 文档：断言表 L2-83（实数 142）、规划表 v0.15.3 行、CHANGELOG 0.15.3、README 安装段补 `mod-backups` 一句、
  报告 `out/takeover-20261024/90-v0153-heartbeat.md`。

**验证**：`logicd OK`、`46/46 passed`、ui smoke EXIT=0、门禁 17/17 in 105.1s；包内 exe `/health` 0.15.3、
`/ping` 语义正确、`/shutdown` 码 0；装机后 mods 下只剩一份 `MlogAuxiliary`。

**教训**：「已就绪」只代表探测那一刻成功；心跳失败必须马上有可见后果（这次 45 s 自退 + 界面不动 = 长期脱节）。
装机脚本保留旧版时必须离开 mods，改个名字不算离开。

## §91 v0.16.0：框选存成原版蓝图（B1）+ 签名 payload v2（B3）

- `MlogAuxiliary/scripts/main.js`：新增 `blueprintHasName()`、`blueprintSaveBox(r, name, cb)`、`blueprintSaveBoxAsk(ws)`；
  作业管理窗底栏加「存成蓝图」，工作区详情加「存成蓝图」；探针 `maiBlueprintSaveProbe`。
- `tools/aigenerated.py`：`PAYLOAD_V = 2`、`META_KEYS`、`_meta_text()`、`meta_of_job()`、`encode_comments(comments, meta=None)`、
  `decode_payload()`、`decode_meta()`；`sign_text(..., meta=None)` 与 `restore_text()` 相应改。
- `tools/jobqueue.py`：`_materialize(job, out, job_id)`，签发时传 `meta=aigenerated.meta_of_job(job)`。
- `tests/mlogauxiliary/run_ui_smoke.py`：`MAIBP` 探针 + 五条红线（create / `tags.put("name")` / `add` / 回读 / 函数存在）。
- `tests/logicd/run_logicd_tests.py`：`test_improve` 的 echo 断言先剥 payload 再比文本，并断言签名里能解出 `ws`。
- 文档：断言表 L2-84（143 条）、规划 v0.16.0 行、CHANGELOG `## 0.16.0`、README「存成蓝图」、蓝图方案 B1 标完成。
- 关键依据：`Schematics.java:377`（`create` 带 `Stile.config`）、`:347`（`add` 只 showException）、`Schematic.name()` 读 tags、
  `_hash()` 只吃 author+body（所以 meta 不影响 id）。
## §92 v0.16.1：蓝图页「MAI 对话」（B2）+ 「详细」页「继续对话」（B4）

- 入口：`blueprintPageHook()` 挂 `Vars.ui.schematics.buttons`（`BP_PAGE_HOOKED` 守一次）；`blueprintInfoHook()` 反射
  `mindustry.ui.dialogs.SchematicsDialog` 的私有字段 `info`，按 `info.title.getText()` 取蓝图名，并额外检查
  `info.buttons.getChildren()` 是否被原版 `clearChildren()` 清空（同一张图连开两次的常态）。
- 读上下文：`blueprintCtxOf(name)` → `Vars.schematics.all()` 同名 → 扫 `sc.tiles[i].config` 找 `aigenerated:` →
  `sigMetaOf()` 解 payload v2 的 `m`（`ws/name/prompt/job`）。
- **Rhino 硬约束**：字符类里带半角引号的正则（`/aigenerated:([^:"]+):…/`）在真机 codegen 抛
  `IllegalStateException: FAILED ASSERTION: invalid bytecode`；改成手写扫描 + `sigInflate()`（`InflaterInputStream`，
  `guard < 4096`）。二分证据：stub 函数体绿、只留正则仍报、字符类去引号即绿。
- 提交：`mode:"improve"` + `workspace{…prevCode…}` POST `/jobs`，900 ms 轮询 `jobGet()`；写回覆写 `tl.config` →
  `saveChanges()` → `blueprintCtxOf()` 回读；`sch.file` 为空则提示先存盘。
- 验证：`node --check` 0；ui smoke EXIT=0（`MAISIGMETA`/`MAIBPTITLE`/`MAIBPCHAT` 三条探针）；`tests/run_tests.py` 46/46；
  `tests/logicd/run_logicd_tests.py` logicd OK；断言表 **L2-85**（总 144）。
- 版本三处 → 0.16.1（`main.js` `MOD_VERSION`、`MlogAuxiliary/mod.hjson`、`tools/logicd.py` `SIDECAR_VERSION`）。


## §93 v0.17.0：设置页与框选的六项体验改造（用户 m09440 / m09517）

- **自动写入**：`AUTO_WRITE_KEY="mlogauxiliary-auto-write"`、`autoWriteOn/autoWriteSet/autoWriteText/autoWriteRefresh`；
  设置页「写入」段 + F3 描述框各一个开关；`autoWriteApply(b, job)` 要求 `state==="done"` 且 `bytes_b64` 非空 →
  `writeBuild(b, jobAsPlan(job))` + `jobBoxWritten(b)`，挂在 `jobTick()` terminal 分支与 `jobBoxTick()` 回调，
  都在 `jobBoxFinishIfDone()` 之前。
- **主标题**：`titleLine(t, text, scale, color)`（Cell 上 `width(ROW_W)+center()`，`cell.get()` 上 `setFontScale/setColor`）；
  三行 MAI(1.9×) / MlogAuxIliary(1.2×) / 版本行(0.9×)。游戏设置的对话框标题与左侧分类按钮名模组改不了
  （`SettingsMenuDialog.java:50`、`:357-365`，按钮 `size(300f,60f)`）。
- **infoCircle**：`tipOn(el, text)`（`Tooltip.Tooltips.getInstance().create(String)` + `setInstant(true)`；**先判
  `Core.scene === null` 直接返回**，否则无头下 NPE 被 smoke 记 FAIL）+ `infoIcon(row, text)`
  （`row.image(Packages.mindustry.gen.Icon.infoCircle).size(18).padLeft(8).color(accent)`）；`kv(..., expl)` 第 5 参。
  「启用模型档」→「启用模型」三处。
- **框选高亮**：`drawLogicHighlight(r)` 逐格 `Vars.world.tile` + `isLogicBuild` → `L.rect(x*8,y*8,8,8)`，
  只描边不填色，面积上限 1024 格（Rhino 跨语言调用贵）。
- **热键**：`HOT_KEY="mlogauxiliary-hotkey-"` + `hotGet/hotSet/hotKeyCode/hotTap/hotBegin/hotCaptureTick/hotLabelsRefresh`，
  which 一律 `select/list/region`（第一版把中文当 which 写进去，读取处找不到 —— 已修）；
  F3 拉框仍走 `Core.input.keyDown(selKey)`。
- **sidecar 无感**：`PENDING_SUBMITS` + `flushPendingSubmits()`（`SIDE.state==="starting"` 时排队，60 秒内补发），
  去掉每局闪一次的「sidecar 已就绪」提示。
- **蓝图入口**（m09517）：「详细」页同时挂「MAI 对话」与「继续对话」。
- 验证：`node --check` 0；ui smoke EXIT=0（`MAIBADGERECT` 几何不变）；`tests/run_tests.py` 46/46；
  `tests/logicd/run_logicd_tests.py` logicd OK；断言表 **L2-86**（总 145）。
- smoke 同步：`fakeTable` 的 Label/Cell 方法实现但不记 `used`；单作业播报红线缩成 `if(isJobTerminal(job.state)){`。
- 版本三处 → 0.17.0（`main.js` `MOD_VERSION`、`MlogAuxiliary/mod.hjson`、`tools/logicd.py` `SIDECAR_VERSION`）。

## §94 v0.17.1：热键进原版按键绑定 + 标题居中 + 蓝图详情页 MAI + 框选先读签名（2026-11-01）

用户 m09822 四条，全部落在 `MlogAuxiliary/scripts/main.js`（18 处替换），另新增 `MlogAuxiliary/bundles/bundle.properties`
与 `bundle_zh_CN.properties`；sidecar 逻辑未动，只把 `SIDECAR_VERSION` 抬到 0.17.1。

- **热键**：`selKeyBind()` 用 `KeyBind.add("mai-select", new KeyBind.Axis(KeyCode.f3), "mlogauxiliary")` 注册，
  `KeybindDialog.rebuildBinds()` 每次显示遍历 `KeyBind.all` ⇒ 运行期注册即可见；值由 `Settings` 的
  `keybind-default-keyboard-mai-select-key` 管；键名/分类走模组 bundle（`Mods.java:636-660` 合并 `bundles/bundle*.properties`）。
  `selKeyCode()` 反读 `kb.value.key` 回退 f3；删除 v0.17.0 自建的 `HOT_KEY`/`hotBegin`/`hotCaptureTick` 全套；F2/F7 固定。
- **标题居中根因**：`Cell.center()` 只设 `align`（Cell.java:512-514），Label 文字对齐是 `labelAlign`（Label.java:34，默认 left）
  ⇒ 新增 `alignText(el, align)` 调 `Label.setAlignment`，`titleLine()` 与 `section()` 都套用。
- **蓝图详情页**：`blueprintInfoHook()` 只挂一个 `info.buttons.button("MAI", …).width(110)`（与返回/导出/编辑并排），
  点开是上下文管理窗（继续对话 / 写回蓝图 / 复制上下文 / 关闭）；去掉蓝图页底栏与详情页重复的两个入口。
- **框选先读签名**：`sigCtxInRegion()` → `sigMetaOf()` 解 payload v2 的 `m`；`wsLoad(meta.ws)` 命中就用，
  磁盘没有则 `wsFromSig()` 重建；`openQuickJob()` 预填 `ws.notes` 并在标题带工作区名；`startJobBatch(..., wsIn)` 走 `wsAttachCtx()` 不新建。
- 验证：`node --check` 0；ui smoke EXIT=0（新增 11 正 + 2 反断言）；`tests/run_tests.py` 46/46；
  `tests/logicd/run_logicd_tests.py` logicd OK；断言表 **L2-87**（总 146）。
- 版本三处 → 0.17.1（`main.js` `MOD_VERSION`、`MlogAuxiliary/mod.hjson`、`tools/logicd.py` `SIDECAR_VERSION`）。

## §95 v0.18.0 首次启动欢迎 + 快速配置向导（2026-11-01）

需求（用户 m10072 原话）：「第一次启动时候弹出欢迎和快速配置页面，并在验证sidecar可允许，模型配置完成之后重启。」

- **首次判定**：`WELCOME_KEY = "mlogauxiliary-welcome-done"` 存 `Core.settings`；`welcomeSeen()` 读不到就当已看过
  （宁可少弹不每局弹），弹过一次或点「稍后再说」即 `welcomeMarkSeen()`；`welcomeTick()` 挂 update，
  只在非主菜单、`Vars.ui`/`Core.scene` 就绪且 `Core.scene.hasDialog()` 为假时插队。
- **三步**（`welcomeBuild(t, mk)` 纯布线，真机 `Dialog.cont` 与无头 `fakeTable` 共用）：
  1. 状态行 + 「启动并检测后端」→ `ensureSidecar(false)` 后 `GET /health` 回 `ok` 才显示「后端可用：vX · 端口 N」；
  2. 地址/密钥/模型三个 `field` + 「获取模型」「测试端点」「保存并启用」→ 写 `Core.settings` 再 `POST /llm`；
  3. 只有「完成（稍后自己重启）」与「现在退出游戏」（`Core.app.exit()`），不给假的热更按钮。
- **入口**：设置页「大模型」段加「首次配置向导」按钮；`welcomeOpen()` 预填已存配置（地址空则 `LLM_DEFAULT_URL`）。
- **自检**：`api.maiWelcomeProbe()`（`fakeTable` 跑 `welcomeBuild`）输出 `MAIWELCOME:ok seen=no cells=155 side=idle`；
  ui smoke 新增 v0.18.0 段 8 条红线 + 2 条探针断言，EXIT=0。
- **版本三处** → 0.18.0（`main.js` `MOD_VERSION`、`MlogAuxiliary/mod.hjson`、`tools/logicd.py` `SIDECAR_VERSION`）。
- **断言表** L2-88（总 147：L1 31 / L2 88 / L3 6 / L4 4 / S 18）；规划表加 v0.18.0 行；CHANGELOG 加 0.18.0；
  README 加「首次配置（只弹一次）」段；报告 `95-v0180-welcome.md`。
- **教训**：smoke 调试回显必须插在 `joined = '\n'.join(lines)` 之后（插在 `lines` 之前会
  `UnboundLocalError: cannot access local variable 'lines'`）；「没看到输出」≠「没跑」；文档锚点先 `assert count == 1`。

## §96 v0.18.1 设置页观感 / 倍率滑条 / 改键不生效 / 查看行为（2026-11-01）

四轮口头反馈一次做完（用户 m10289 / m10327 / m10374 / m10546），两个真根因都在引擎语义上。

- **主题色/强调色**：`themeColor()` = `#8abcd1`；`emphColor()` = `Pal.accent` 向白 `lerp 0.3`
  （`Mindustry-Source/core/src/mindustry/ui/UI.java:105/107` 的 `[highlight]` 就是这么算的），
  段落标题、两行主标题、`infoIcon()` 统一走 `themeColor()`；长解释 `softWrap(text, 34)`、图标贴行右缘（`INFO_W = 26`）。
- **向导按钮搬家**：「首次配置向导」从「大模型」段首移到「运行环境」段末。
- **最近提示改日志**：`HINT_LOG`(12) + `hintLogPush()`/`hintClock()`/`hintLogText()`/`hintLogCopy()`/`hintLogClear()`。
- **眼睛图标**：`eyeMark(hidden)` → `UI.formatIcons(":eye:")`/`":eyeOff:"`，单图标按钮贴密钥行右缘。
- **倍率滑条 + 改不了的真根因**：设置页换成原版 `arc.scene.ui.Slider` + `hudSliderTick()` 每帧轮询
  （`ProgressBar` 没有 `changed(Runnable)`，只有 `getValue()`/`setValue()`，`ProgressBar.java:207/241/246`）；
  根因是 `arc/Settings.java:357-359` 的 `getFloat()` = `(float)get(...)`，JS 数字存进去是 `java.lang.Double`，
  `(float)Object` 抛 `ClassCastException` ⇒ 永远退回 1×。改存 `String(n)`、读用 `get(key, null)` + `parseFloat`。
- **查看行为**：框角「查看」→ `jobViewPick()`；`done` 走 `previewLogic()`（`Vars.ui.logic.show(code, null, false, fn)`，
  只预览不写入）；未完成走 `jobThinkToChat()` + `chatLocalSay()`（`Vars.ui.chatfrag.addMessage`，只进本机聊天，
  不发 `Call.sendChatMessage`）。旧「作业详情」窗不再从框角打开。蓝图库底栏「MAI 对话」→「MAI 控制面板」（宽 150）。
- **改键不生效**：`KeybindDialog.java:128-150` 的 `rebind()` 对 Axis 默认值走两步 ⇒ 落盘 Axis 只有 `min`/`max`、
  `key` 为 null，旧 `selKeyCode()` 只认 `ax.key` ⇒ 永远退回 f3。现 `selKeyCode()`/`selKeyDown()`/`selKeyName()`
  两种形状都认；F2 也注册成 `mai-list`（`listKeyBind()`/`listKeyTap()`/`listKeyName()`，bundle 加
  `keybind.mai-list.name`），设置页显示「框选键」「清单键」。F7 仍固定。
- **验证**：`node --check` 0；ui smoke EXIT=0（探针 `MAIKEYBIND:ok axis=G / H code=G one=Y onecode=Y back=F3`）；
  门禁 **17/17 in 102.2s**；包 `out\_dist\MAI-0.18.1`（168 files / 18,702,090 B，
  `MAI-0.18.1-mod.zip` sha256 `0F5838B6CC22DCFDC91E2B7960E03A7C955213AB3DF8576B24812848AB76CB80`）；包内 exe `/health`
  = `0.18.1`、`/ping {}` 200、`/ping "[object Object]"` 400、`/shutdown` 200。
- **断点**：装机被「游戏在跑」挡住（`Mindustry.exe` + `logicd.exe` 占着 `saves\mods\MlogAuxiliary`，
  `Move-Item` Access denied）；公开仓 push/tag/Release 也留到用户确认之后。
- **教训**：`run_ui_smoke.py` 有两处前缀白名单（约 `:391-401` 收 `lines`、`:1783-1788` 才 `print`），
  新增探针前缀必须两处都加；`mlogsim.Server` 要 `M.Server(M._default_java(), M.V160_JAR)`；
  锚点缩进要照抄（`kv(t, "框选键", …)` 续行是 11 空格）。

## §97 v0.18.2 主题色/强调色可调 + 选框与高亮分色 + 高亮居中（2026-11-01）

用户 m10938 / m10943。三个改动都在 `MlogAuxiliary/scripts/main.js`。

- **颜色成为设置项**：`THEME_KEY="mlogauxiliary-theme-color"`（默认 `8abcd1`）、
  `EMPH_KEY="mlogauxiliary-emph-color"`（默认按 `UI.java:107` 的 `[highlight]` 现算
  `Pal.accent.cpy().lerp(Color.white, 0.3f)`）。一律存六位十六进制字符串，读用
  `Core.settings.get(key, null)` + 自写 `hex6()` 校验（不用正则，避开 Rhino `invalid bytecode`）。
  **不能存数字**：`arc/Settings.java:357-359` 的 `getFloat` 是 `(float)get(...)`，
  JS 数字是 `java.lang.Double`，强转抛 `ClassCastException`（v0.18.1 倍率 bug 同坑）。
- **设置页「外观」段**（框选控件之后、写入之前）：`colorRow()` = 标签 + 十六进制输入框 +
  `Tex.whiteui` 色块（`setColor` 实时刷）+ 「默认」+ 行尾 `infoIcon`。非法输入退回当前值并提示。
- **画法**：`drawSelection()` 本体改 `D.color(themeColor())`（阴影仍 `Pal.accentBack`）；
  `drawLogicHighlight()` 改 `D.color(emphColor())`，并把 `L.rect(x*8, y*8, 8, 8)` 改成
  `L.rect((x-0.5)*8, (y-0.5)*8, 8, 8)` —— `Tile.java:166-172` 的 `worldx()` 是格子中心，
  `Lines.rect` 是左下角语义，少退半格就偏右上角（v0.6.0 的 `selDrawArgs` 已踩过同一手）。
- **验证**：`node --check` 0（319038 → 324314 字符）；ui smoke EXIT=0，
  探针 `MAITHEME:ok theme=8abcd1ff emph=ffe0a5ff … set=ff8800 back=8abcd1 dflt=8abcd1`；
  门禁 **17/17 in 95.1s**；断言表 L2-90（总 149）。
- **教训**：smoke 的前缀白名单仍是两处（`:397` 收行、`:1795` 才打印），新探针两处都要加；
  `python -X utf8 -c` 里带引号的中文替换串照旧必炸，一律 write 工具写 `.py`；
  版本三处（`main.js` `MOD_VERSION` / `mod.hjson` / `logicd.py` `SIDECAR_VERSION`）同改，
  `mod.hjson` 的版本行是 `version: "x.y.z"`（没有引号包 key），别写成 JSON 形状。

## §98 v0.18.3 设置页瘦身 / MAI 控制面板管工作区 / 本地快检进包（2026-11-01）

用户 m11124 一次六件，其中两件是「功能静默缺失」的真 bug：

- **本地快检「未加载」**：`tools/package.py:161-185` 的 `layout()` 只拷 `scripts/main.js`，而 `main.js` 自己
  `require("rules.generated")` / `require("quickcheck")`（游戏只执行 `scripts/` 里唯一的 `.js`，规则副本必须单独发）。
  装机目录 `scripts/` 只有 main.js ⇒ require 抛异常 ⇒ `RULES` 恒 null。改成 glob `scripts/*.js`，
  `tests/packaging/run_pack_tests.py` 新增 2c 段逐文件比 sha256 + 检查 main.js 是否 require 了每个脚本。
- **设置项「未注册」假阴性**：`selfTest()` 的假表路径会让 `buildSettingsTable()` 跑一遍，此时 `settingsDone`
  还是 false。新增 `SETTINGS_LIVE`（buildSettingsTable 首行 true、末尾 false），判断改 `settingsDone || SETTINGS_LIVE`。
- **设置页瘦身**：删 `快捷动作`/`说明`/`本地快检` 三段（2838 字符），`最近提示` → `诊断与最近提示` 并把
  `diagParts()` 全部行摊进去，按钮只留一个「复制」。新段序：大模型/聊天播报/框选控件/外观/写入/诊断与最近提示/运行环境
  （热键两条是 kv 行，没有 section）。
- **MAI 控制面板**：蓝图库底栏按钮 handler 由 `openBlueprintPicker()` 改 `openWorkspaceDialog()`；
  面板底栏加「撤销上次写入」（`undo()`）、「撤销快照」（`undoInfo()`）。
- **mod.hjson**：author → `Iliary艾铭&DeepSeek`，description → 「在一次选框中创建Mlog工作区并开始VibecodeingMlog。」。
  **坑**：第一次用 `re.S` + `"[^"]*"` 的整段正则，把后面注释里的一对引号一并吃掉、文件从 1589 字节变成 807 字节
  ⇒ 改 hjson 只能按行改（`git checkout --` 恢复后逐行替换）。
- **验证**：`node --check` 0；ui smoke EXIT=0（段序/新红线/反向断言）；`main.js` 324314 → 323188 字符。
- **质量问题**：teammate `quality-analyst` 出报告 `98-quality-analysis.md`：坏逻辑集中在「猜 v160 指令签名」
  （prompt 2675 字符、无参数表）与「把 jump 当 1 基行号」（mlogcheck 按 0 基判回边）两件事，而检查器只查
  参数过多/孤立链接、不查少参数与参数语义，WARN 也不触发重试 ⇒「没给规范 × 没查语义」的乘积。
  R1–R5 修法见报告，另派 `quality-fix` 实现 R1–R4。

## §99 v0.18.3 第二轮：多格处理器按建筑去重 / 高亮整块缩放（2026-11-01）

- 用户 m11320（中核 2×2/超核 3×3 完全框选被下发 4/9 个作业）与 m11340（高亮同步缩放）。
- 根因：`regionSnapshot` 快照循环逐格 `procs.push`（库存已有 `seenIds` 去重、处理器漏了）。
- 修：`seenProcs`（快照）/`seenQ`（`openQuickJob`）/`seenH`（高亮）都按建筑 id 去重；
  高亮每台画一整块外框 `L.rect(bx - bsize*4, by - bsize*4, bsize*8, bsize*8)`（`Building.x/y` 中心 + `block.size`）。
- smoke 红线三条换新（`L.rect(bx - bsize * 4, ...)`、`seenH`、`seenProcs`），EXIT=0；门禁/打包/文档（L2-92）同步。
- 教训：smoke 红线补丁的锚点缩进要现 grep（`if(isProcessor(bld)){` 实际 20 空格缩进在 try 块内，20/24 空格都试错过）；
  红线永远别设计成「往 main.js 里插注释」——改成断言 `code_only` 里的真实代码行。

## §100 v0.18.4 模型思考全文可查看（2026-11-01）

- 用户 `m13036`「为什么不能查看当时的思考内容，而只能看到工作状态」。不是没存，是三处只给状态：
  - 思考一直在：`tools/mlogprovider.py:719-728` 把端点的 `reasoning_content`/`reasoning` 收进
    `res["reasoning"]`（`REASONING_MAX = 12000`），`tools/jobqueue.py:680-684` 作业收尾写 `job["reasoning"]`
    （`REASONING_MAX = 20000`）；而 sidecar 是非流式调用，整轮结束前根本没有文本 ⇒ 生成中确实只有状态词。
  - 终态入口：`jobWidgetView()` 原来 done 只 `previewLogic()`、failed/rejected 只 `hint` 一行；
    思考只挂在 `renderJob()` 与 `renderManagerDetail()`，而两处都只 `jobReasoningLines(job, 16, 40)` 的开头。
  - `GET /jobs?all=1` 故意剥掉 reasoning（`tools/logicd.py:1176-1190` 的 `BRIEF_DROP`）⇒ 列表行没有全文。
- 修（`MlogAuxiliary/scripts/main.js`）：`jobThinkAll()` `:3397`、`jobThinkCopy()` `:3401`（`Core.app.setClipboardText`）、
  `openThinkDialog()` `:3414`（`Packages.arc.scene.ui.Dialog` + `cont.pane` 640×420，`jobReasoningLines(job, 100000, 60)`，
  按钮 `复制全部` / done 时 `看代码` / `关闭`）、`jobThinkFetchOpen()` `:3440`（列表行没有全文时先 `jobGet(id)`）；
  `jobWidgetView()` 终态 `:4006` 一律先 `var tr = openThinkDialog(job);`，回 `no reasoning`/`no ui` 才退回老行为；
  `renderJob()` done 加 `思考`（`:3515`）、失败/被拒那支补 `思考`/`关闭`（`:3537`）；
  `renderManagerDetail()` 加 `思考（N 字符）`/`思考（读取全文）`（`:4567`）。
- 探针 `api.maiJobThinkProbe`（`:6840`）只验取行这一层（无头开不了 Dialog）：`MAIJOBTHINK2:ok len=80 rows=2 w0=60`；
  smoke 加两处前缀白名单 + `jres` 取键 + 四条 `code_only` 红线，EXIT=0。
- 门禁 `python gate.py --full --kb-build`：首次 15/17 —— `package` 撞上一轮被打断留下的
  `out\_exe\dist\logicd`（沙箱给它加了 Everyone deny-delete ACE，`Remove-Item` 报 WinError 5），
  删掉后单独重跑 **PASS 9.0s**；`corpus` 的 `--jobs 8` 在本机沙箱下必炸（Windows multiprocessing 走命名管道，
  `multiprocessing/connection.py:557` `PermissionError: [WinError 5]`），改 `--jobs 1` 串行跑同一 400 样本 → **PASS**（400 programs / 2523 findings / analyse errors 0 / 27.9 s，
  `out/_bench/_gate_corpus.json` 已重写）
- 放宽沙箱后整轮复跑 `python gate.py --full` → **17/17 in 52.8s**（`out/_gate_v184b.log`）——上面两条失败
  都是沙箱/残留目录，不是代码问题。
- 文档：CHANGELOG 0.18.4、规划表 v0.18.4 行、断言表 L2-93 且口径改 **152 条**
  （L1 31 / L2 93 / L3 6 / L4 4 / S 18 —— 旧「147 条 / L2 88」本身已落后 4 条）、版本三处 → 0.18.4、
  报告 `100-v0184-think.md`。
- 包：`python tools/package.py` → `out\_dist\MAI-0.18.4-mod.zip`（169 files / 8,448,226 B，
  sha256 `BC046D16F83BB81A03C22CD1D63F6D30FBF967C5AB06E71BFF47A14D51B91F5F`）与 `MAI-0.18.4.zip`
  （8,469,960 B，sha256 `42910D4B946ED24A812F2D8F9CE8C589590BC75D3FE1AC8FE8D05B1FA0D5BBB1`）；
  装机：2026-11-01 22:44 `install.ps1 -Silent` 覆盖安装到
  `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary`（169 files / 18,712,000 B，
  旧版移到 `saves\mod-backups\MlogAuxiliary-20261101-224430`），`sidecar\bin\logicd.exe` 起在 8799 上 `/health`
  返回 `{"ok":true,"protocol":1,"version":"0.18.4"}` 后正常 `/shutdown`。公开仓 push/tag/Release 等用户确认。
- 教训：`gate.py --only corpus` 不带 `--full` 时这两步根本没进 `build_steps`，会打印 `0/0 passed` —— 别当成功；
  被中断的 PyInstaller 构建目录会带沙箱 deny ACE，删掉再跑 `package` 即恢复。

## §101 v0.19.0 工作区界面重做（左列表 / 右详情 + 世界细框 + 释放确认）（2026-11-02）

- 驱动：用户 m13036 之后的界面改版规划，方案稿 `docs/Mlog辅助-工作区快照-界面改版-方案.md`（A1+A2+A3+C1，C2 只做选中）。
  详细报告见 `out/takeover-20261024/101-v0190-wsui.md`。
- 改前：`renderWorkspaces`（旧 `:4869`）是一列纯文本行，`renderWorkspaceDetail`（旧 `:4830`）另开一屏，
  `openWorkspaceDialog`（旧 `:5470`）600×320 单栏，`wsRelease` 无确认，世界里看不到工作区。
- 改后（`MlogAuxiliary/scripts/main.js`，旧 70 行 → 约 560 行，起点仍 `:4830`）：`wsUI` 状态对象 + 纯函数层
  （`wsStatusOf` 三态 / `wsRowParts` / `wsDetailModel` / `wsFilterList` / `wsSortList` / `wsGhostRects` /
  `wsReleaseConfirmText` / `wsCanLocate` / `wsLocate`）+ `wsRefreshList()`（搜索/排序/chips/卡片）+
  `wsRefreshDetail()`（处理器表 ≤12 / 作业时间线 ≤6 / 动作三层）+ `drawWorkspaceGhosts()`（挂在
  `Events.run(ET.Trigger.draw)` 的 `drawSelection` 之后）+ `wsAskRelease()`（`showConfirm("释放工作区", ...)`）。
  `openWorkspaceDialog()` 改双栏（宽 ≥900 左 300 / 右 440，窄屏单 360），`d.hidden` 清 `wsUI.open`。
- 坑：本 checkout `Pal.java:76-88` **没有 `Pal.scarlet`** ⇒ 异地图/失败用 `Pal.remove`；悬停高亮不做
  （`InputListener` 子类化 Rhino 下 0 先例）；`Styles.flatOver` 不能用于选中态（静态字段要 atlas，无头炸）；
  无 `Vars.ui` 时释放确认必须兜底直接执行，否则功能卡死。
- 自检：`api.maiWorkspace3Probe()` → `ok rows=3 filt=2 sort=3 detail=2 ghosts=1 release=1 mismatch=1 locate=1`；
  smoke 断言 `MAIWS3:ok` + 10 条 `code_only` 红线，EXIT=0（`out/_smoke_v190.log`）。
- 文档：CHANGELOG 0.19.0、规划表 v0.19.0 行、断言表 L2-94/L2-95 且口径改 **154 条**
  （L1 31 / L2 95 / L3 6 / L4 4 / S 18）、版本两处 → 0.19.0、方案文档 §11 实现回填。
- **打包守卫（装机时抓到的坑，已修）**：`main.js:266-271` 的 `sidecarVersionMismatch(h)` 会把 `/health` 版本不等于
  自身版本的 sidecar 退役，而 `tools/logicd.py:87` 的 `SIDECAR_VERSION` 还停在 `0.18.4`（`MOD_VERSION` 已是 0.19.0）
  ⇒ 装上去 AI 全不可用，gate 17/17 抓不到。已修：`SIDECAR_VERSION = '0.19.0'`；`tools/package.py` 的 `build()` 加守卫
  （两处版本不等直接 `SystemExit`）；`tests/packaging/run_pack_tests.py` 加一致性检查；CHANGELOG 加一条。
- 门禁：`python gate.py --full --kb-build` → **17/17 passed**（`out/_gate_v190c.log`）。
- 包（末版，首版两个 zip 作废）：`out/_dist/MAI-0.19.0-mod.zip`（169 files / 8,453,972 B，sha256
  `26FFA21B00698D5CBC72ECDD9E716F2E767B099C7E95530828F3662D627B14D3`）与 `MAI-0.19.0.zip`（8,475,714 B，
  sha256 `2FB5B887FEC8BD0F49CE64AD54A13C97C356941AACC7704209AE53B4C8F9B361`）；`out/_pack190b.log`。
- 装机：`E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary`（Steam 版数据目录在
  游戏旁，见 `Vars.java:494-495`；旧副本备份到 `saves\mod-backups\`），bundled sidecar 0.19.0。
- 公开发布：源码仓 `EnernalIliary/MAI-MlogAuxIliary` push `bba8244` + tag `v0.19.0`；
  Release https://github.com/EnernalIliary/MAI-MlogAuxIliary/releases/tag/v0.19.0（两个 zip 已上传，2026-11-02T04:52:13Z）。
  坑：克隆里 `out/_exe` 带 deny ACE 要先 `rd /s /q`；跑 `tests/run_tests.py` 前先 `python tools/sync_mlogagent.py --mirror all`；
  本机注册表系统代理 127.0.0.1:10808 会让 python urllib 报 `URLError Errno 2`（看着像网络断，其实是代理），已改直连。
