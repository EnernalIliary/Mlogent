# §69 logicd + mai v0.12.4：模型在想什么，现在面板里能看见

日期：2026-10-31 16:2x–16:3x
触发：玩家第二次贴同一类截图 —— `作业 …1cfaa5ce6d92：被门禁拒绝（尝试 3 次，ERR 1 条）` +
`ERR L0 model endpoint answered with an empty message (finish_re…`，并说「我说游戏内的模型思考过程。
还有试图生成的报错信息没有变」。

## §69.1 两件事，两个答案

1. **「报错信息没有变」= sidecar 还是旧进程。** `GET /health` 当时只回 `{ok, protocol}`（v0.12.3 才加
   `version`），查进程：pid 14816，15:50:51 启动 —— 比我 v0.12.3 的提交（16:00）还早。`out/jobs` 里最新三条
   `c7f21cfaa5ce6d92`（16:19:30）、`d529983fe4cf172c`（16:06:02）、`f122e54f918974ff-2`（15:51:45）全是
   `attempts=3`、`completion_tokens: 1600` 的旧代码产物。杀掉重启后 pid 51388，`/health` 直接报 0.12.4。
2. **「想看游戏内的模型思考过程」= 新功能。** sidecar 把回复里的 `reasoning_content` 存进作业，模组在面板里
   摊开。

## §69.2 为什么以前看不到

- `tools/mlogprovider.py` 的 `HttpProvider._once()` 只取 `_reply_text(doc)`（也就是 `content`）；
  `reasoning_content` 只在 `content` 为空时被 `_alt_text()` 当「备用答案」捡一下，正常路径**直接丢掉**。
- job 契约（`docs/Mlog辅助-规划.md` §4.1、`tools/jobqueue.py` 顶部 docstring）里没有这个字段，模组无从渲染。
- 于是作业失败时，玩家只剩一行 message：分不清「模型想歪了」、「没照做」、还是「预算被思考吃光」。

## §69.3 改动

**sidecar — `tools/mlogprovider.py`**

- `REASONING_MAX = 12000`（回包带多少推理文本）。
- `_with_reason(res, doc)`：`_once()` 的每条返回路径都经过它，把 `reasoning_content`（或 `reasoning`）摘成
  `res["reasoning"]`。
- `_reason_text(doc)`：取推理文本；`_keep_reason(res, src)`：`__call__` 因为 `finish_reason=length` 改写错误
  文本时，不把已经拿到的思考丢掉。

**sidecar — `tools/jobqueue.py`**

- `REASONING_MAX = 20000`（存到作业上多少）。
- `_run()`：provider 返回后、error 分支**之前** `_set(jid, reasoning=think[:REASONING_MAX])` —— 被拒的那次
  才是最想看思考的时候。
- 模块 docstring：契约行加 `reasoning`，并加「Why 'reasoning' is part of the job (v0.12.4)」。

**sidecar — `tools/logicd.py`**：`SIDECAR_VERSION = '0.12.4'`（`/health` 与 `server_version` 同源）。

**模组 — `MlogAuxiliary/scripts/main.js`**

- `jobReasoningText(job)`、`jobReasoningLines(job, maxLines, perLine)`、`REASON_LINE = 40`、`REASON_LINES = 16`。
- `renderJob()`：状态行下面加「--- 模型思考（N 字符[，只显示开头]）---」+ 分段行，所有状态都加。
- `api.maiJobReasoning(jobJson)`：控制台/自检取原文（`api.*` 会被挂到脚本作用域，控制台能直接敲）。
- `MOD_VERSION = "0.12.4"`；`MlogAuxiliary/mod.hjson` 的 `version` 同改，`description` 追加一句。

## §69.4 测试与门禁

- `test_provider()` 12 项（新增 ⑫）：脚本 provider 的回包带 `reasoning` → 作业 `done` 且
  `job["reasoning"]` 保留了那段文本，代码/findings 都不受影响。
- `test_llm()` 12 项（新增 ⑫）：`_StubEndpoint` 现在在正常回复里写 `reasoning_content = STUB_THINK`，走完
  HTTP 的作业必须带上它、且长度 ≤ `REASONING_MAX`。
- ui smoke：`job_probe()` 新增 `MAIJOBTHINK` 行（真 v160.7 引擎里 `maiJobReasoning` 读一个手造作业），断言含
  文本；红线条数 +2（`function jobReasoningLines(`、`api.maiJobReasoning = function`）。
- 结果：`python tests/logicd/run_logicd_tests.py --no-sim` → `protocol: 26 / jobs: 15 / provider: 12 /
  llm: 12`，全绿；`python tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，摘要里 `MAIDIAG:版本：0.12.4（游戏构建 160）`。
- `python gate.py --full --kb-build` → **16/16 passed in 156.8s**（kb 重建覆盖 163 源文件）。

## §69.5 装到真机（我做了前两步，第三步要玩家点）

1. 模组文件已拷：`MlogAuxiliary/scripts/main.js`、`MlogAuxiliary/mod.hjson`
   → `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary\`
   （游戏是 Steam 版、便携数据目录，写在 Program Files 下也不需要管理员，实测 `copy ok`。）
2. sidecar 已重启：pid 51388，`GET /health` → `{"ok":true,"protocol":1,"version":"0.12.4"}`；
   `GET /llm` 暂时是 `template` 档（模型档存在游戏的 Core.settings 里，只有模组推得回来）。
3. 玩家要做的：① **重启游戏**（模组只在启动时读盘）② 打开一次 AI 面板（`showAiPanel()` 第一行就是
   `llmSync()`，会把设置页里的模型档/密钥推回 sidecar）③ 同一句描述再点「生成」。

## §69.6 边界与已知

- 面板只显示开头 16 行 × 40 字符；全文在 `job["reasoning"]`（≤ 20000 字符）与 `out/jobs/<id>.json` 里。
- 模板档、以及不返回 `reasoning_content` 的端点：整段不出现（不是空框）。
- `reasoning` 只保留**最新一次**尝试；自修复过程中前几次的思考不累积。要全量历史得在 provider 层挂 recorder
  （`mlogprovider.load_script`/`Recorder` 是给回放用的，不含推理），本轮没做。
- 游戏内没有「展开全部」按钮；要原文用控制台 `maiJobReasoning(<jobJson>)`。
- 仍待真机确认：v0.12.3 的 `DEFAULT_MAX_TOKENS = 4096` 对 `deepseek-flash` 是否真的够（不够就
  `--llm-max-tokens 8192` 或面板里改）。
