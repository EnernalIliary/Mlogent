# 57 · v0.9.0：F4 热键删除 + 零链接门禁盲区修复

日期：2026-10-30　　玩家指令（逐字）：**「做1，直接整个去掉f4的热键，不用保留。然后做2」**

## 1. 为什么动这两处

上一轮（v0.8.1）把 F4 并进 F3 之后，F4 只是留了个别名函数，玩家明确说「不用保留」——
留着一个没人按的键位既是死代码，也是以后误改的入口。同一条消息里的第 1 条是上一轮报告里
点出的门禁盲区：**处理器一个链接都没接时，幻觉链接名拦不住**。

## 2. F4 彻底删除

- `MlogAuxiliary/scripts/main.js`：删 `var KEY_PANEL = ["f4"];`、删 `toggleAiPanel()`（唯一调用者就是 F4 那段）、
  删 update 钩子里 6 行 `keyTap`；外层 `if(KEY_PANEL !== null){` 退化成匿名块。
- `MOD_VERSION = "0.9.0"`，`mod.hjson` 描述「按 F4 打开」→「按住 F3 点一下处理器打开」，9 处注释同步。
- `tests/mlogauxiliary/run_ui_smoke.py`：把原来的正向红线（必须有 `toggleAiPanel();`）换成**反向红线**——
  源码里再出现 `KEY_PANEL`、`toggleAiPanel` 或字符串 `"f4"` 即失败。

## 3. 零链接门禁：空表被折成了「不知道」

根因链：模组发 `links` → `logicd.analyse()` 用 `_link_names(links) or None` → 空列表变 `None` →
`mlogcheck` 的 `if links is not None and v not in link_vars:` 整段跳过 → `sensor x container9 @copper`
在零链接处理器上判干净 → 写进处理器。

四处改动：

1. `tools/mlogcheck.py`：`analyse(..., links_authoritative=False)`，只影响 >200 语句的碎片启发式分支；默认关，语料/golden 行为不变。
2. `tools/logicd.py`：`links is not None` 时传 `links_authoritative=True`，`names` 保留空列表本身。
3. `tools/jobqueue.py`：`normalize()` 允许 `links: null`；`_materialize()` 去掉 `or []`（这是第一次改完仍红的真凶——
   它把 null 又变回权威空表）；只有给 `msch` 造载荷才 `links or []`。
4. `MlogAuxiliary/scripts/main.js`：新增 `linkListOrNull(b)`，读不到链接表才发 `null`。

## 4. 验收（全部真 v160.7 引擎 / 真 sidecar）

- `tests/logicd/run_logicd_tests.py --no-sim` → `protocol: 25` / **`jobs: 12 check(s) passed`**（原 9 项，新增零链接 rejected、null done、gate 单元三连）。
- `tests/mlogauxiliary/run_ui_smoke.py` → `job zero-link gate: rejected, rule=link-name-not-bound (the processor links to nothing)`，`MAIDIAG:版本：0.9.0`，EXIT=0。
- `tests/run_tests.py` → **44/44**（改 `mlogcheck` 后先 `tools/sync_mlogagent.py --mirror all`，否则测试拒跑）。
- `gate.py --full` → 16/16；`tools/kb.py build` 重建。

## 5. 诚实缺口

- `links_authoritative` 只覆盖「零链接 + 形似链接名变量」这一条路径；语料侧仍按默认 False 走，
  也就是说外部语料的误报率没有被这次改动影响（好事，但也没有被改进）。
- 真 provider（模型侧）仍未接，作业仍由模板档或假 provider 产出——这是下一刀。
- F4 删掉之后，**开 AI 面板的唯一入口是按住 F3 在处理器上点一下**；键位冲突风险交给玩家真机验收。
