# Mlog辅助 —— 设计

> 目标不是"把逻辑导出成文件"，也不是"给逻辑做静态分析报告"，而是**让玩家不写 mlog**：
> 玩家只表达意图（选一个模板、填几个参数），模组 + 本地 sidecar 负责生成代码、做静态检查、
> 写进处理器。仓库已有的解析/检查/成本/模拟能力是这条流水线的**质检环节**，不是产物本身。

## 1. 三层结构

    ┌─────────────────────────── 游戏内（Rhino JS 模组 MlogAuxiliary/）───────────────────────────┐
    │  鼠标指向处理器 → F4 → 面板列出意图模板 → 点一个 → POST /compose → 显示 findings 与成本     │
    │  确认 → build.configure(bytes) ── 原版 config 通道 ──→ 服务端 readCompressed(data, true)    │
    └───────────────────────────────────────────┬───────────────────────────────────────────────┘
                                                │ HTTP 127.0.0.1:8765（JSON）
    ┌───────────────────────────────────────────┴───────────────────────────────────────────────┐
    │  本地 sidecar tools/logicd.py                                                              │
    │  /capabilities  指令表 + 模板清单 + 上限                                                    │
    │  /analyze       mlogcheck.analyse() 全量规则 + cost_report()                                │
    │  /compose       模板 → 代码 → 自检 → msch.build_logic_data() → bytes_b64                    │
    └───────────────────────────────────────────────────────────────────────────────────────────┘

三层的分工是**按"谁已经是唯一真相"**划的：

* 生成与检查放在 Python，因为规则（`rules/*.json`，41 条）、指令表（`tools/instr_semantics.json`）、
  成本模型（`tools/mlogcheck.py` 的 `cost_report`）已经存在，而且被 gate 钉住。在 Rhino 里重写一份，
  等于制造第二个会静默漂移的副本。
* 编码放在 Python，因为 `tools/msch.py:447 build_logic_data()` 生成的字节流**就是**游戏
  `LogicBlock.compress()` 的格式（版本字节 1 + 代码 + 链接表 deflate）。模组只转发 base64。
* 游戏里只留"必须在那儿"的三件事：**目标处理器**（只有游戏知道鼠标指着谁）、**UI**、**写入**。

## 2. 写入通道：为什么是 config，不是改字段

`Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java`：

| 行 | 事实 |
| --- | --- |
| `:65-69` | `config(byte[].class, (build, data) -> { if(!accessible()) return; build.readCompressed(data, true); })` |
| `:114-116` | `accessible() = !privileged \|\| editor \|\| playtestingMap != null \|\| allowEditWorldProcessors` |
| `:137-166` | `compress(code, links)`：版本字节 `1`、`writeInt(len)+code`、`writeInt(links.size)`、每链接 `writeUTF(name)+writeShort(x)+writeShort(y)` |
| `:256-258` | `class LogicBuild { public String code = ""; }` |
| `:362-369` | `updateCode(str)` → `LAssembler.assemble(str, privileged)`（**只改本地**，不同步） |

结论：**写入走 `configure(byte[])`**。它天然是"客户端 → 服务端"的通道，联机时由服务端执行，
模组不需要自己实现同步；而 `updateCode()` 只改本地字段，联机下会被服务端状态覆盖。
所以撤销（P1）用 `updateCode` 只是**本地应急回滚**，正式撤销（P3）必须同样走 configure。

## 3. 接口契约（v1）

| 方法 | 路径 | 请求 | 响应 |
| --- | --- | --- | --- |
| GET | `/health` | – | `{ok, protocol:1}` |
| GET | `/capabilities` | – | `{ok, protocol, game, instructions[53], ops[45], templates[{id,title,params[{name,type,default,help}]}], limits{ipt_max:40, link_range_tiles:10}}` |
| POST | `/analyze` | `{code, links, ipt}` | `{ok, findings[{sev,line,stmt,rid,msg}], errors, warns, statements, cost}` |
| POST | `/compose` | `{template, params, links, ipt}` | 同上 + `{template, code, links, bytes_b64, bytes_len}` |

约定：

* `ok == (errors == 0)`。**ERR 一律拒绝写入**，WARN/INFO 允许写入但必须显示在面板上。
* `links` 接受 `["container1"]` 或 `[{name,x,y}]`；缺省坐标补 0（游戏侧写入时会用处理器自己的链接表）。
* `findings[].line` 是**代码行号**（1 起），`stmt` 是**指令槽位序号**（0 起）。两者不同：
  标签行不是语句（`LParser.java:117-125` 把标签记成"下一条语句"），sidecar 用
  `mlogcheck.prepare()` 做这层换算 —— 面板要高亮的是行号，不是槽位。
* 模板引用了请求里没有的链接名 → 服务端补一条 `rid=template-needs-link` 的 ERR（不让"忘了连方块"
  变成"写进去什么都不动"）。
* 坏 JSON → 400，未知端点 → 404，未知模板/参数类型错 → 400，请求上限 4 MB。

## 4. 模板层：先确定性，后语言

P1 的六个模板（`tools/logicd.py` 的 `TEMPLATES`，全部确定性、参数带类型校验）：

| id | 意图 | 关键语句 |
| --- | --- | --- |
| `patrol` | 绑一个单位，在两点之间来回走 | `ubind` / `ucontrol move` / `wait` / `jump` |
| `item-threshold` | 容器里某物品够了就在消息块上打印 | `sensor` / `jump greaterThanEq` / `printflush` |
| `radar-fire` | 炮塔瞄最近的敌人 | `radar enemy any any distance <t> 1 target` / `control shootp` |
| `memory-table` | 往内存格写一个值再读回来 | `write` / `read` |
| `timer-flush` | 每 N 秒打印一行 | `wait` / `printflush` |
| `counter` | 每秒在内存格里加一 | `read` / `op add` / `write` |

为什么先确定性：**没有门禁的生成代码写进玩家存档是灾难**。模板的每个参数都有类型，生成的代码在
`/compose` 里就已经过了全量规则检查；语言模型（P4）将来只能作为"生成候选"接进来，
输出必须过同一道 `/analyze` 门禁，并且把 findings 一起显示给玩家看。

## 5. 快检与全量检查的分工（P2）

| 层 | 跑在哪 | 覆盖 | 延迟 |
| --- | --- | --- | --- |
| 全量 | sidecar（Python） | 41 条规则 + 成本模型 + 可选模拟器对拍 | 十毫秒级（HTTP 往返） |
| 快检 | 游戏内（Rhino） | 链接名绑定 / 未赋值变量 / ipt 超预算 / 版本门 | 微秒级，离线可用 |

快检的规则表由 `rules/*.json` 生成 `MlogAuxiliary/scripts/rules.generated.js`，gate 里校验
"重新生成是否与仓库内文件一致"，防止两份规则表漂移（仓库已经因为文档/表不一致吃过亏：
radar 的"数量参数"神话就是文档教出来的，见 `docs/断言表.md` L2-17）。

## 6. 安全与失败模式

| 情况 | 行为 |
| --- | --- |
| 有 ERR | 面板显示 findings，**写入按钮不出现**；`maiApply` 直接返回"拒绝写入" |
| sidecar 不可达 | 面板显示"离线"并给出启动命令；P1 没有快检，所以此时不提供写入（宁可不能写，也不盲写） |
| 目标不是处理器 | 鼠标下的方块做鸭子类型判断（`executor` / `code` 字段），不是就拒绝 |
| Rhino 主线程 | HTTP 全在 `Threads.daemon()` 里跑，结果用 `Core.app.post()` 回到游戏线程 |
| 游戏版本漂移 | 源码是 v159.3 快照、游戏是 v160.7；写入通道与 `LogicBlock.compress` 格式两版一致（探针与集成测试都在 160.7 上跑） |
| 特权处理器 | `accessible()` 为假时游戏自己会丢弃 config，模组只报"写入失败"，不绕过 |

## 7. 分期

| 期 | 内容 | 验收 |
| --- | --- | --- |
| **P1（本版）** | sidecar 三接口 + 模组骨架 + 写入通道 | 坏代码 → 显示 findings 且拒绝写入；六模板字节灌进真 v160.7 处理器，`b.code` 一致、指令类正确、链接表完整 |
| P2 | 游戏内快检 + 全图扫描 + 点击跳转 | 100 个处理器扫描 < 1 s；`rules.generated.js` 与 `rules/*.json` 一致（gate） |
| P3 | 模板扩到 10 个 + 原子写 + 落盘 undo + diff 预览 | 生成 → 0 ERR → 写入 → 撤销后逐字节还原 |
| P4 | 意图层（表单/一句话，可选 LLM） | LLM 输出必须附 findings，0 ERR 才可写 |

## 8. 已验证 / 未验证

机器验证（`tests/logicd/run_logicd_tests.py`，进 `gate.py --full`）：

* 协议层 13 项：健康、能力表（53 指令 / 45 op / 6 模板 / ipt 上限 40）、好代码通过、坏代码（对象槽位
  读未赋值变量）被拒、六模板 `compose` 0 findings、字节经 `msch.parse_logic` 往返一致、
  缺链接 → `template-needs-link`、400/404 语义、链接名打错仍是 WARN 且能送到客户端。
* 写入层 6 项：把 `/compose` 的 `bytes_b64` 交给真 v160.7 处理器的 `build.configure(bytes)`，
  读回 `b.code` 一致、`executor.instructions.length > 0`（游戏自己的 `LAssembler` 接受了载荷）、
  链接表 4 条完整；首个指令类分别是 `UnitBindI` / `SenseI` / `RadarI` / `WriteI` /
  `WaitI` / `ReadI`，与模板一一对应。

**未验证**：面板 UI（无头模拟器里没有界面）、热键、控制台挂载 —— 这三样只能在真游戏里点一遍。
它们的代码路径都包在 `try/catch` 里，失败时日志留 `[mlog-auxiliary]` 前缀，不会静默。

## 9. 关键坐标

| 东西 | 位置 |
| --- | --- |
| sidecar | `tools/logicd.py`（端点、六个模板、`analyse()`） |
| 编码器 | `tools/msch.py:447 build_logic_data()`、`:322 parse_logic()`、`:159 LogicLink` |
| 分析器 | `tools/mlogcheck.py:840 analyse()`、`:2068 cost_report()`、`:1999 prepare()` |
| 模组 | `MlogAuxiliary/mod.hjson`、`MlogAuxiliary/scripts/main.js`、`MlogAuxiliary/README.md` |
| 契约测试 | `tests/logicd/run_logicd_tests.py` |
| 游戏侧 | `LogicBlock.java:65-69/114-116/137-166/256-258/362-369`、`LParser.java:117-125` |
