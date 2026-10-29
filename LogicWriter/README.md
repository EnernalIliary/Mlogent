# LogicWriter —— 游戏内逻辑写入服务（P1 + P2）

把「写 mlog」这件事从玩家手里拿走：**说意图，不写代码**。

    [游戏内] 选中处理器 → 选模板/填参数 → POST 给本地 sidecar
                                              ↓
    [sidecar] tools/logicd.py: 意图 → mlog → 静态检查(41 条规则 + 成本) → 字节载荷
                                              ↓
    [游戏内] 面板显示 findings + 成本 → 确认 → build.configure(bytes) 写进处理器

P1 做 **API 接入** 与 **写入通道**；P2 把**快检**搬进游戏（没有 Python 也能先判一轮）。
生成层目前是确定性模板，不接 LLM；框选 + 队列 + 模型是 P3/P4，路线见
`docs/逻辑写入服务-规划.md`。

## 为什么写入走 config 通道

`LogicBlock` 的 `config(byte[].class, ...)` 就是原版「客户端把代码推给服务端」的通道
（`Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:65-69`），
载荷格式是 `compress(code, links)`：版本字节 + 代码 + 链接表 deflate（同文件 `:137-166`）。
模组直接 `build.configure(bytes)`：

* 单机与联机同一条路径 —— 联机时由服务端执行 `readCompressed`，**不用自己造同步**；
* 载荷由 `tools/msch.py:447 build_logic_data()` 生成，和游戏自己的编码器同一格式，
  `tests/logicd/run_logicd_tests.py` 会把这段字节灌进真 v160.7 处理器逐条验。

## 安装

1. 把整个 `LogicWriter/` 目录放到 `<游戏目录>/saves/mods/LogicWriter/`（便携版数据目录 = 游戏目录）。
2. 启动 sidecar：`python tools/logicd.py`（默认 `http://127.0.0.1:8765`）。
3. 进游戏，把鼠标指向一个处理器，按 **F4** 打开面板（或控制台敲 `lwPanel()`）。

sidecar 不可达时面板会明说「离线」，此时不提供写入 —— 但**本地快检照常工作**，
可以先用 `lwCheck()` / `lwScan()` 看看现有代码有什么问题。宁可不能写也不要盲写。

## 控制台函数

| 函数 | 作用 |
| --- | --- |
| `lwVersion()` | 模组版本 + sidecar 地址 |
| `lwPing()` | 同步 GET `/health`（调试用，会卡一帧） |
| `lwSel()` | 报告鼠标下的方块是不是处理器、它现在有几行代码几个链接 |
| `lwPanel()` | 打开面板 |
| `lwCompose(template, paramsJson)` | 同步 compose，返回 JSON 文本（调试用） |
| `lwApply(template, paramsJson)` | compose + 直接写进鼠标下的处理器（0 ERR 才写） |
| `lwUndo()` | 撤销上一次写入（P1 是内存快照，重启游戏即失效） |
| `lwCheck([code])` | 本地快检：不给参数就查鼠标下的处理器，给了就查这段代码 |
| `lwScan()` | 全图扫描所有处理器跑本地快检，返回「N 个处理器 / 多少有命中 / 规则分布 / 耗时」 |

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
`tests/logicwriter/` 跑 14 个用例、`require()` 契约、以及「quickcheck 说断链时全量检查也必须同意」的单向验证。

两条源码事实（v160.7 实测）：

* 游戏只执行 `scripts/main.js`（`Mods.java:809`），其余文件必须 `require()` 进来；
  `Scripts.java:30-32` 装了 CommonJS 模块提供器，实测 `typeof require` 是函数。
* 版本号取 `Packages.mindustry.core.Version.build`（`Version.java:22`，自定义构建是 `-1`，
  此时版本门不启用）。

**边界**：快检只许少报，不许瞎报。未赋值变量的槽位分级、成本 CFG、值域这些需要数据流
推理的判据不在游戏内，仍由 sidecar 回答。

## 明确没做

* 撤销只在内存里，不落盘（P3：`<dataDir>/logicwriter/undo/`）
* 没有 diff 预览，整段替换（P3）
* 没有框选/队列（P3/P4）
* 没有自然语言/LLM（P4）
* UI 面板这一层没有机器验证过（无头模拟器里没有界面）
