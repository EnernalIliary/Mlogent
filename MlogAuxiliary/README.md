# MlogAuxiliary —— 游戏内Mlog辅助（P1 + P2 + 设置界面 + AI 面板，v0.4.0）

把「写 mlog」这件事从玩家手里拿走：**说意图，不写代码**。

    [游戏内] 选中处理器 → 选模板/填参数 → POST 给本地 sidecar
                                              ↓
    [sidecar] tools/logicd.py: 意图 → mlog → 静态检查(41 条规则 + 成本) → 字节载荷
                                              ↓
    [游戏内] 面板显示 findings + 成本 → 确认 → build.configure(bytes) 写进处理器

P1 做 **API 接入** 与 **写入通道**；P2 把**快检**搬进游戏（没有 Python 也能先判一轮）；
v0.3 起调试入口是**设置 → Mlog辅助**一栏，不再依赖控制台。
v0.4 起有两个正面入口：**F4 的 AI 辅助面板**（一句话 -> sidecar 选模板并预检 -> 预览 -> 写入）
与**原版逻辑编辑器底部的审查栏**（打开原版编辑器就自动挂上，代码一改就重算）。

生成层仍是确定性模板（模型只能选模板、填参数，不能直接产 mlog）；框选 + 队列是 P3/P4，路线见
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
   把鼠标指向一个处理器再按 **F4** 打开 **AI 辅助面板**（一句话生成 + 预检 + 写入）；
  纯模板面板走那一栏的「模板面板」按钮。

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
| `maiAi()` | 打开 AI 辅助面板（等同 F4） |
| `maiReview()` | 纯文本版审查：原版编辑器里的代码 + 快检结论 + findings（不弹窗） |

## 设置界面（v0.4）

`设置 → Mlog辅助`，一栏把调试要看的都摊开，不用再往控制台敲命令：

v0.4 把这一页按用途分段（`── 运行环境 ──` 这样的标题行 + 左标签右值两列）：

* **运行环境**：版本 / 游戏构建（`Version.build`）/ 快检模块是否加载（指令、op 版本门、链接槽各几条）/ 
  数据目录 / mods 目录 / 设置分类状态 —— 装错位置、规则表没加载，一眼看出来；
* **本地快检**：快检能否使用、规则表条数；
* **sidecar**：地址（可直接改，回车即存进 `Core.settings` 的 `mlogauxiliary-url`）、连接测试（GET `/health`）、**复制诊断**到剪贴板；
* **快捷动作**：AI 辅助编程 / 模板面板 / 快检鼠标下的处理器 / 打印诊断 / 重新注册分类 / 审查状态。

排版只用了在真 v160.7 里实测能解析的 `Table` / `Cell` 方法（`add` / `labelWrap` / `button` / `field` +
`colspan` / `left` / `right` / `width` / `pad` / `padTop` / `padBottom` / `padRight` / `row`），
`run_ui_smoke.py` 会把 `maiSelfTest()` 报出的每个方法名拿到真引擎里调一遍。

注册走 `Vars.ui.settings.addCategory(name, Cons<SettingsTable>)`（`SettingsMenuDialog.java:329-330`），
分类只在显示设置菜单时 rebuild（`:357`、`:658`），所以脚本加载时机不影响它出现；脚本加载时 UI 还可能不存在，
`ClientLoadEvent` 上再补注册一次，之后热键钩子里还有一次**有界重试**（每 60 帧一次、最多 600 次）。
诊断里最后一行 `设置分类：` 会直接告诉你注册成功还是在哪个异常上失败。

**v0.3.0 那一栏没出现的原因**：设置表格用了 `t.table(function(tt){...})` 做按钮分组，真 v160.7 的 Rhino 在
**方法解析阶段**就抛 `InternalError: ... Table.table ... is ambiguous`（重载歧义），异常被注册函数吞掉，
于是游戏里根本没有这一栏 —— 而假表 smoke 还是绿的。v0.3.1 改成**平铺加行**（`t.button` / `t.labelWrap` /
`t.field`，实测都能解析），并且 `run_ui_smoke.py` 多了一道探针：把 `maiSelfTest()` 报出的方法名逐个拿到
真引擎里调用，出现 `ambiguous` 即 FAIL。**无头环境**（模拟器、`Vars.ui == null`）里 `maiSettings()` 返回
`no ui` 而不是抛错，设置表格的布线由 `maiSelfTest()` 用假表验证。

## AI 辅助面板（v0.4，F4）

把鼠标指向任意处理器按 **F4**（或设置页的「AI 辅助编程」、控制台 `maiAi()`）：

1. 一句话说清要什么，例如「让 @flare 从 10 10 来回巡逻到 30 12」「容器里铜够 250 就打印」；
2. 模组把这句话 + 该处理器的链接名列表 `POST /plan` 给 sidecar；
3. sidecar 用关键词路由选出模板（六个之一）并抽参数（数字、`@单位`、链接名），再走同一条
   确定性生成 + 全量检查，返回 `{template, params, reason, code, findings, cost, bytes_b64}`；
4. 面板显示**选中的模板与理由**、预检计数、前几条 findings、前 40 行代码；
5. 0 ERR 时出现「写入」按钮 —— 与模板面板同一个写入函数（`build.configure(bytes)`）。

有 ERR 就没有写入按钮：是拒绝写入，不是降级写入。意图太模糊（没命中任何关键词）时服务端
返回 `ok:false` + 六个候选模板名，面板照原样显示，不瞎猜。

**模型只有一个接入点**：`tools/logicd.py` 的 `_route()`。它是纯规则（关键词表 + 参数抽取），
换成模型调用时返回形状不变，模组这一侧一行都不用改 —— 所以模型永远没法把没检查过的 mlog 塞进存档。

## 原版编辑器审查栏（v0.4）

打开**原版逻辑编辑器**（点处理器 → 编辑）时，模组在对话框底部补一条 46 px 状态栏：

* 「审查」+ ERR/WARN/INFO 计数（`Pal.remove` / `Pal.lightOrange` 上色）+ 语句数 / 线性成本 / ipt；
* 「详情」= 全部 findings（`Vars.ui.showText`）；「AI 辅助」= 直接开 AI 面板；
* 代码一改（`canvas.save()` 变了）就重算，最多每 30 帧一次；编辑器没开时每帧只做两次属性读。

接法是最低侵入的：不自造对话框、不碰 canvas，只在 `Vars.ui.logic`（单例，`UI.java:79` / `:228`）
身上 `row()` 之后 `add(bar).growX()`。`LogicDialog` 的构造里 `clearChildren()` 之后只有
`add(canvas).grow()` / `row()` / `add(buttons).growX()` 三样（`LogicDialog.java:39-72`），
所以这一行是它的第四行，原版按钮一个都不动。
## 接口契约（sidecar v1）

| 方法 | 路径 | 请求 | 响应 |
| --- | --- | --- | --- |
| GET | `/health` | – | `{ok, protocol}` |
| GET | `/capabilities` | – | `{ok, protocol, game, instructions, ops, templates[], limits{ipt_max, link_range_tiles}}` |
| POST | `/analyze` | `{code, links, ipt}` | `{ok, findings[{sev,line,stmt,rid,msg}], errors, warns, statements, cost}` |
| POST | `/compose` | `{template, params, links, ipt}` | 同上 + `{template, code, links, bytes_b64, bytes_len}` |
| POST | `/plan` | `{intent, links, ipt}` | `/compose` 的全部字段 + `{intent, params, reason}`；没命中时 `{ok:false, template:null, reason, candidates[]}` |

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
* 自然语言已经能用，但只是**关键词路由**：`/plan` 的 `_route()` 是规则表，没接模型（P4）
* 框选区域 + 排队 + 多处理器写入（P3/P4/P5）
* 真界面的**像素**没法机器验证（无头模拟器里 `Vars.ui` 是 null）：`run_ui_smoke.py` 只验到
  「main.js 整段初始化不抛错 + 设置表格能建到假 Table 上 + 页面用到的每个 Table 方法在真引擎里能解析」，
  按钮点下去的实际效果、这一栏在设置菜单里的位置与排版仍要人看
* 两个面板的模板按钮只用默认参数（改参数走控制台 `maiCompose(id, paramsJson)` 或 AI 面板的一句话）
* AI 面板只覆盖六个模板能表达的意图，多处理器 / 多步流程它做不到
