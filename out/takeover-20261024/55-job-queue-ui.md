# 55 · P4 第二刀：模组侧作业队列（v0.8.0）

## 1. 动机
F4 面板的「生成」原来直接 `POST /plan`：同步语义、不落盘、不能取消，而分析器对
`link-name-not-bound` 只给 WARN。P4 第一刀（`tools/jobqueue.py` + `/jobs` 三端点，commit 738eddd）
已经把队列、状态机、门禁做出来了，但游戏侧还没接。这一刀只换通道，不换生成逻辑。

## 2. 契约与实现
- `jobBody(b, desc)` → `{job: {mode:"new", desc, links, ipt: 2, origin, snapshot}}`；
  快照 = `regionSnapshot(b.tile.x-6, b.tile.y-6, b.tile.x+6, b.tile.y+6)`，拿不到时回落空骨架
  （`jobqueue.normalize` 要求 snapshot 是 dict）。
- `jobSubmit()` 异步投递 `POST /jobs`；`jobGet()` / `jobCancel()` 分别对 `GET/DELETE /jobs?id=`。
- `jobTick()` 挂在每帧钩子（`reviewTick()` 之后），`JOB_POLL_MS = 1000`；面板关掉即 `aiJob = null`，
  回调里用 `if(aiJob !== mine) return;` 防串台。
- `renderJob()`：done 时列代码 + 把 `d.buttons` 换成「写入 / 关闭」；rejected/failed/cancelled 时列
  findings 与 `jobProgressText()` 的中文原因。
- `jobAsPlan(job)` 把 job 适配成 `/plan` 的形状交给既有的 `writeBuild()` —— 写入路径一行没变，
  仍然只认 `bytes_b64`。
- 退路：旧的「直接生成」（同步 `/plan` + `renderPlan`）保留，老 sidecar 没有 `/jobs` 时面板仍可用。
- 控制台：`maiJob` / `maiJobSync` / `maiJobSyncAt` / `maiJobWrite` / `maiJobProgress` / `maiJobCancel` / `maiJobState`。

## 3. 验收（真 v160.7 引擎 + 真 sidecar）
`tests/mlogauxiliary/run_ui_smoke.py` 新增 `start_sidecar()`（`--jobs-provider fake`，25 s 内等 `/health`）
与 `job_probe()`，在**引擎里**跑两条作业：

- 干净作业（`set n 0` / `op add n n 1` / `print n` / `end`）→ `state=done`、attempts 1、`bytes_b64` 非空，
  `maiJobWrite` 把 60 字节载荷写进处理器并回读出 `set n 0`，`maiJobProgress` 报「完成」。
- 坏代码作业（`jump 99 always x 0`）→ `state=rejected`、attempts 3（1 + 2 次 self-repair）、`code` 为空串、
  findings 带 ERR。
- 源码红线 8 条：`function jobBody(`、`function jobSubmit(`、`function jobTick(`、`jobTick();`、
  `function renderJob(`、`api.maiJobSyncAt = function`、`POST", "/jobs"`、「直接生成」。

## 4. 诚实缺口
1. 面板关闭后不再观察作业（服务端仍跑完并落盘，只是没人提示）。
2. 没有跨面板的「完成」通知条。
3. **零链接处理器**：模组发来的 `links` 是空数组，`mlogcheck` 把空数组当「不知道」而不是「确实没有」，
   幻觉链接名在这种情况下拦不住；这一刀改用代码级 ERR 验证拒绝路径，链接名那一档由 `test_jobs()` 的
   显式 links 覆盖。

## 5. 复跑
`node --check MlogAuxiliary/scripts/main.js`；`python -X utf8 tests/mlogauxiliary/run_ui_smoke.py`；
`python -X utf8 gate.py --full`；`python -X utf8 tools/kb.py build`；
`python -X utf8 out/_v45_zip.py` + `out/_v45_install.py`。
