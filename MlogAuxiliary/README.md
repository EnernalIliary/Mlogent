# MlogAuxiliary —— 游戏内Mlog辅助（P1 + P2 + 设置界面）

把「写 mlog」这件事从玩家手里拿走：**说意图，不写代码**。

    [游戏内] 选中处理器 → 选模板/填参数 → POST 给本地 sidecar
                                              ↓
    [sidecar] tools/logicd.py: 意图 → mlog → 静态检查(41 条规则 + 成本) → 字节载荷
                                              ↓
    [游戏内] 面板显示 findings + 成本 → 确认 → build.configure(bytes) 写进处理器

P1 做 **API 接入** 与 **写入通道**；P2 把**快检**搬进游戏（没有 Python 也能先判一轮）；
v0.3 起调试入口是**设置 → Mlog辅助**一栏，不再依赖控制台。
生成层目前是确定性模板，不接 LLM；框选 + 队列 + 模型是 P3/P4，路线见
`docs/Mlog辅助-规划.md`。

## 为什么写入走 config 通道

`LogicBlock` 的 `config(byte[].class, ...)` 就是原版「客户端把代码推给服务端」的通道
（`Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:65-69`），
载荷格式是 `compress(code, links)`：版本字节 + 代码 + 链接表 deflate（同文件 `:137-166`）。
模组直接 `build.configure(bytes)`：

* 单机与联机同一条路径 —— 联机时由服务端执行 `readCompressed`，**不用自己造同步**；
* 载荷由 `tools/msch.py:447 build_logic_data()` 生成，和游戏自己的编码器同一格式，
  `tests/logicd/run_logicd_tests.py` 会把这段字节灌进真 v160.7 处理器逐条验。

## 安装

1. 先找到**真正在用的数据目录** —— 不要凭印象。Steam 版可能是桌面版（`%APPDATA%\Mindustry`），
   也可能是**便携版**（数据目录就是游戏目录下的 `saves`）。判据：游戏跑起来后看这两个位置的
   `last_log.txt` 谁的修改时间是刚刚，或者直接用游戏内「模组 → 打开文件夹」。
2. 把 `MlogAuxiliary/` **整个目录**放进那个 `mods` 下（本机实测是
   `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary/`）。
   **用 zip 也行，但 zip 里必须只包一层 `MlogAuxiliary/` 目录**：`Mods.resolveRoot()`（`Mods.java:1070-1074`）
   只在「根下恰好一个目录」时才下钻，否则把 zip 根当模组根，`scripts/main.js` 会 `exists()==false`，
   日志里就是 `[E] No main.js found for mod mlog-auxiliary.` —— 模组列表里看得见它、脚本却一行没跑，
   控制台自然找不到 `maiVersion`。`out/_dist/MlogAuxiliary.zip` 已经按这个形状打好了。
3. 启动 sidecar：`python tools/logicd.py`（默认 `http://127.0.0.1:8765`）。不开也能进游戏，
   只是没有生成/写入；**本地快检照常工作**。
4. 进游戏（模组是 `hidden` 的，不会出现在模组列表里，这是故意的：联机不会被当成不兼容模组）：
   **设置 → Mlog辅助**，这一栏会直接告诉你加载是否成功（版本 / 构建 / 快检模块 / sidecar / 两个目录）。
   把鼠标指向一个处理器再按 **F4** 打开写入面板，或点那一栏的「打开面板」。

## 控制台函数

| 函数 | 作用 |
| --- | --- |
| `maiVersion()` | 模组版本 + sidecar 地址 |
| `maiPing()` | 同步 GET `/health`（调试用，会卡一帧） |
| `maiSel()` | 报告鼠标下的方块是不是处理器、它现在有几行代码几个链接 |
| `maiPanel()` | 打开面板 |
| `maiCompose(template, paramsJson)` | 同步 compose，返回 JSON 文本（调试用） |
| `maiApply(template, paramsJson)` | compose + 直接写进鼠标下的处理器（0 ERR 才写） |
| `maiUndo()` | 撤销上一次写入（P1 是内存快照，重启游戏即失效） |
| `maiCheck([code])` | 本地快检：不给参数就查鼠标下的处理器，给了就查这段代码 |
| `maiScan()` | 全图扫描所有处理器跑本地快检，返回「N 个处理器 / 多少有命中 / 规则分布 / 耗时」 |
| `maiDiag()` | 诊断文本（就是设置界面里那段） |
| `maiSelfTest()` | 拿一张假 Table 建一遍设置表格，报告填了多少行/格（无 UI 环境的自检） |
| `maiSettings()` | 再尝试注册设置分类；返回 `registered` 或 `no ui` |

## 设置界面（v0.3）

`设置 → Mlog辅助`，一栏把调试要看的都摊开，不用再往控制台敲命令：

* 版本 / 游戏构建（`Version.build`）/ 快检模块是否加载（指令、op 版本门、链接槽各几条）
* sidecar 地址（可直接改，回车即存进 `Core.settings` 的 `mlogauxiliary-url`）与**上次**探测结果
* **数据目录**与 **mods 目录**的绝对路径 —— 装错位置时一眼就能看出来
* 按钮：连接测试（GET `/health`）/ 打开面板 / 快检鼠标下的处理器 / 打印诊断到控制台

注册走 `Vars.ui.settings.addCategory(name, Cons<SettingsTable>)`（`SettingsMenuDialog.java:329-330`），
分类只在显示设置菜单时 rebuild（`:357`、`:658`），所以脚本加载时机不影响它出现；脚本加载时 UI 还可能不存在，
`ClientLoadEvent` 上再补注册一次。**无头环境**（模拟器、`Vars.ui == null`）里 `maiSettings()` 返回 `no ui` 
而不是抛错，设置表格的布线由 `maiSelfTest()` 用假表验证。

## 接口契约（sidecar v1）

| 方法 | 路径 | 请求 | 响应 |
| --- | --- | --- | --- |
| GET | `/health` | – | `{ok, protocol}` |
| GET | `/capabilities` | – | `{ok, protocol, game, instructions, ops, templates[], limits{ipt_max, link_range_tiles}}` |
| POST | `/analyze` | `{code, links, ipt}` | `{ok, findings[{sev,line,stmt,rid,msg}], errors, warns, statements, cost}` |
| POST | `/compose` | `{template, params, links, ipt}` | 同上 + `{template, code, links, bytes_b64, bytes_len}` |

* `ok` 的语义是 **没有 ERR**。有 ERR 时模组拒绝写入，WARN/INFO 照常写入但会列在面板上。
* `findings[].line` 是代码里的行号（1 起），`stmt` 是指令槽位序号 —— 两者不同，因为标签行不是语句
  （`LParser.java:117-125`）。
* 模板声明要用某个链接名而请求里没有 → 服务端补一条 `rid=template-needs-link` 的 ERR。

## 游戏内快检（P2）

`scripts/quickcheck.js` 是纯函数、无游戏依赖的 ES5，回答五类**单行**问题：指令是否存在、
`ucontrol`/`draw`/`ulocate` 子命令是否拼错（拼错整行会被解析成 `NoopI`，静默不执行）、
是否用到比当前 build 更新的指令、链接槽里的名字是否真的连着、语句数是否超过 1000（尾部会被截断）。

规则表 `scripts/rules.generated.js` 由 `python tools/rules_export.py` 从
`tools/instr_semantics.json` + `tools/mlogcheck.py` 生成；`gate.py` 跑 `--check` 防漂移，
`tests/mlogauxiliary/` 跑 14 个用例、`require()` 契约、以及「quickcheck 说断链时全量检查也必须同意」的单向验证。

真 Rhino 与 node 的**逐条比对**是独立一步：`python tests/mlogauxiliary/run_rhino_parity.py`
（无 JRE 时 SKIP）。理由是真 v160.7 的 Rhino 里 `"abc def".split(/\s+/)` 会按**每个字符**切开
（带 `+` 量词的正则在它的 `String.prototype.split` 里等价于空匹配，只有单字符模式正常），
node 侧永远发现不了 —— 所以本文件的分词、裁剪、标识符判断全部手写扫描，不用 `split(正则)`。

两条源码事实（v160.7 实测）：

* 游戏只执行 `scripts/main.js`（`Mods.java:809`），其余文件必须 `require()` 进来；
  `Scripts.java:30-32` 装了 CommonJS 模块提供器，实测 `typeof require` 是函数。
* 版本号取 `Packages.mindustry.core.Version.build`（`Version.java:22`，自定义构建是 `-1`，
  此时版本门不启用）。

**边界**：快检只许少报，不许瞎报。未赋值变量的槽位分级、成本 CFG、值域这些需要数据流
推理的判据不在游戏内，仍由 sidecar 回答。

## 明确没做

* 撤销只在内存里，不落盘（P3：`<dataDir>/mlogauxiliary/undo/`）
* 没有 diff 预览，整段替换（P3）
* 没有框选/队列（P3/P4）
* 没有自然语言/LLM（P4）
* 真界面的**像素**没法机器验证（无头模拟器里 `Vars.ui` 是 null）：`run_ui_smoke.py` 只验到
  「main.js 整段初始化不抛错 + 设置表格能建到假 Table 上」，按钮点下去的实际效果仍要人看
* 面板里的模板按钮只用默认参数（改参数仍走控制台 `maiCompose(id, paramsJson)`）
