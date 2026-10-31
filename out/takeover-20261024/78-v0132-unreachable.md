# 78 — v0.13.2：不可达语句变成 WARN、生成改用标签、面板摊开假设与成本

日期：2026-10-31。起因：用户 m03631「插件生成的逻辑问题很多，好像没有过逻辑审查，你看看什么情况。」，
m03632 批准 F1/F2/F3（并明确 F3 不需要「防空转」——全速空转可以接受）。

## 78.1 为什么：检查器算出来了，但没人看见

用户最后一条作业 `out/jobs/43fe34c6557e3eeb.json`（21:32，desc `控制炮台攻击玩家`，16 条语句，`findings: []`，`state: done`）：

```
0-3   control enabled salvo1..4 1
4     radar player any any distance salvo1 1 target
5     jump 12 strictEqual target null        <- 应为 11
6-9   control shootp salvoN target 1
10    jump 5 always 0 0                     <- 应为 4
11-14 control shootp salvoN null 0
15    jump 5 always 0 0
```

两个错叠在一起：`jump 12` 跳进「停止射击」块的正中间 ⇒ `L11` 永不执行；`jump 5` 回跳到 jump 自己而不是 radar ⇒
雷达只跑一次，之后一直拿旧的 `target` 空转。

`python tools/mlogcheck.py` 当时回 `no issues found`（0 error / 0 warning / 0 info）。加 `--cost` 才看得见：

```
UNREACHABLE : 1 statement(s) can never run:
L11: control shootp salvo1 null 0
loop heads: L5(?)
worst-case path ~11 instructions
```

也就是说：**可达性分析一直在算，结论只写进成本报告**。`tools/jobqueue.py` 的 `_set()` 存了
`findings/explanation/assumptions/template/params`，偏偏没存 `cost`；面板的作业详情只看
`findings/errors/warns`；重试提示只在 `findings` 非空时出现。于是「语义上有问题」的代码一路绿灯写进游戏。

扫描 `out/jobs/` 里 16 条已完成作业：11 条零 findings，其中 3 条含「永远执行不到」的语句。

## 78.2 改了什么

| 层 | 文件 | 改动 |
| --- | --- | --- |
| 检查器 | `tools/mlogcheck.py` | `analyse()` 在 dedupe 之前把 `reachable_set()` 之外的语句追加成 `Finding("WARN", line, "unreachable-statement", …)` |
| 规则 | `rules/unreachable-statement.json`（新） | kind=semantics、severity=WARN、`match.msg_any=["can never run"]`、counter_example=`tests/cases/loop-labels-ok.mlog` |
| 用例 | `tests/cases/unreachable-statement.mlog`（新）、`tests/cases/loop-labels-ok.mlog`（新） | 正例报 1 WARN（语句下标 3）；反例干净 |
| 基线 | `tests/expected.json`、`tests/rule-coverage.json` | 46 条 digest（`label-index` 新增 `["WARN", 2]` 是真阳性：乒乓死循环末尾的 `end` 永不执行）；32 active 规则 0 problem |
| 作业 | `tools/jobqueue.py` | `_set(..., cost=res.get('cost') or '', ...)` —— 成本进作业 JSON |
| 生成 | `tools/mlogprovider.py:build_prompt()` | 行号规则换成标签规则 + free tier 骨架 |
| 面板 | `MlogAuxiliary/scripts/main.js` | `jobAssumptionLines()` / `jobCostLines()`；`renderJob()` done 分支新增两段；`api.maiJobPanelProbe` |
| 模板 | `tools/logicd.py` | 5 个内置模板删掉尾部死 `end` |
| 版本 | `main.js` / `logicd.py` / `mod.hjson` | 0.13.2 |

## 78.3 为什么标签是零成本的

`tools/msch.py:447 build_logic_data(code, links)` 只把**代码原文** utf-8 写进 logic data
（`struct.pack(">i", len(code_bytes)) + code_bytes`），不做字节码编译；`tools/mlogcheck.py:2005 prepare()`
本来就解析标签（`if len(toks) >= 2 and toks[0] == "jump" and toks[1] in labels`），缺目标有 `no-target-jump` 规则。
所以「让模型写 `loop:` + `jump loop always`」不需要改编码器、不需要改游戏侧任何东西。

## 78.4 这条规则当场抓到了我们自己的模板

`logicd.compose()` 逐个跑 7 个内置模板，5 个报 `unreachable-statement`：

```
patrol -> L8   item-threshold -> L9   radar-fire -> L9
timer-flush -> L6   counter -> L7
```

全是同一个毛病：`jump loop always` 后面再跟一行 `end`（`memory-table` 是 `printflush` 后跟 `end`，正常）。
已删掉这 5 处的尾 `end`，重跑扫描为 0。这条正好印证用户那句「生成的逻辑问题很多」——连自己的模板都带死语句。

## 78.5 验证

- `tests/run_tests.py` → **46/46 passed**（含两条新 case）。
- `tests/ruleids/run_ruleids.py` → `41 rule(s) (32 active), 32 rid(s) fire on 43 fixture(s), 0 problem(s)`。
- `tests/logicd/run_logicd_tests.py` → `protocol 26 / jobs 16 / provider 12 / llm 12 / write path 7 templates`，全过。
  中途它先红了一次：`FAIL protocol: compose patrol findings: [... 'rid': 'unreachable-statement' ...]` —— 这就是 78.4 的来源。
- `tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，`MAIDIAG:版本：0.13.2`，断言 `MAIJOBPANEL:ok assumptions=2 cost=3`。
- `python tools/sync_mlogagent.py --mirror all` → 21 个文件 0 changed，三个 mirror verify 全 match。
- `node --check MlogAuxiliary/scripts/main.js` → exit 0。
- `python gate.py --full --kb-build` → 17/17。

## 78.6 一个测试基础设施的坑（值得记）

`tools/mlogsim.py:456 Server.js()` 用 `self.send("js " + " ".join(script.splitlines()))` —— 控制台一次读一行，
所以脚本里**真实换行会被空格拼掉**。想往 JS 字符串里送一个换行，Python 源码里必须写 `\\n`（两个反斜杠 + n，
这样 Python 的值是「反斜杠 + n」两个字符，再由 Rhino 当转义解析）。我第一次只写了一个反斜杠，
结果 `cost` 三行被拼成一行、`MAIJOBPANEL:bad assumptions=2 cost=1`。

## 78.7 没做

- 「空转要加 wait」的警告：用户明确说不需要（全速空转对服务器开销不大），所以 `spin-deadlock` 保持原样。
- 让模型「按 CFG 自查」：本轮只做标签 + 可达性反馈，模型仍然可能写错别的语义。
- 工作区快照（用户 m03632 的新需求）：用户 m03723 说先做完这两个小功能，规划书另行。
