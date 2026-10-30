# 63 · 孤儿 JVM：让模拟器子进程跟父进程一起死（P5 之外的第 2 条候选）

日期 2026-10-31。触发：v0.10.1 收尾时 `gate.py --full` 首跑 probes 26 条全红，
`There is insufficient memory for the Java Runtime Environment to continue`，
`Get-Process java` 有 61 个残留 JVM。用户选第 2 条候选（「2.我看看ui你两下解决」）。

## 63.1 根因三条

1. `tools/mlogsim.py` 原 `close()` 只有 `send("exit")` + `wait(15)`，超时 `kill()` —— 只覆盖「父进程还活着」这一条路径。
2. `tests/mlogauxiliary/run_ui_smoke.py` 的 `main()` 从不调用 `srv.close()`（`srv = M.Server(...)` 在 :291，三个 return 都没收尾）
   ⇒ **每跑一次 ui smoke 泄漏一个 JVM**。
3. `tests/probes/run_probes.py:265-270` 有 try/finally + `close()`，但整轮被 gate 超时 / Ctrl-C 硬杀时 python 没机会跑 finally；
   Windows 上父进程被 TerminateProcess 不会连带杀子进程 ⇒ JVM 继续活着占内存。

## 63.2 改动表

| 文件 | 改动 |
|---|---|
| `tools/mlogsim.py` | +200 行：Windows job object（`KILL_ON_JOB_CLOSE`）、`_LIVE_SERVERS` 注册表、`atexit` 兜底、`sweep_orphans()`、`close()` 幂等重写、CLI `--sweep-orphans`、docstring 一段 |
| `tests/probes/run_probes.py` | +10 行：一轮跑完扫一次孤儿，打印 `swept N stale JVM(s)` |
| `tests/mlogauxiliary/run_ui_smoke.py` | +13/−3：`__main__` 用 try/finally 调 `_close_live_servers()`（补上从来不关的历史债） |
| `tests/logicd/run_logicd_tests.py` | `wait_job` 超时 30 s → 60 s（一次并行 gate 下的假超时，见 63.4） |
| `tools/README.md` | +16 行「子进程生命周期（孤儿 JVM）」整节 |

关键实现点：`_win_kill_with_parent(proc)` 用 ctypes 建 job 并 `AssignProcessToJobObject`，
`BasicLimitInformation.LimitFlags = 0x2000`、`SetInformationJobObject(job, 9, ...)`；
`CreateJobObjectW.restype = ctypes.c_void_p` 且三个调用都设 `argtypes`（否则 64 位句柄被截断）。
job 句柄属于本进程 ⇒ 本进程怎么死，内核都带走子进程。

`sweep_orphans()` 只认 `java.exe` 且命令行含 `_server160.jar` / `_server159.jar` / `_server146.jar` / `jre21`
（游戏本体也跑 java.exe，不能一刀切），并且 **ppid 不在活进程集合里** 才杀 —— pid 复用会让死父看起来活着，宁可漏杀不误杀。

## 63.3 两条实验证据

实验 1（`out/_jvm_test1.py`，硬杀父进程）：子 python 起 `Server` 打印 `UP 72948`；
PowerShell 查到 `ParentProcessId` = 该 python 的 java.exe 正是 `72948`；`taskkill /PID <python> /F` 后 3 秒再查 → `[]`，
`RESULT PASS job object took the child down`。

实验 2（`out/_jvm_test2.py`，扫孤儿 + 正常跑）：baseline `[73508, 5104]` →
`python -X utf8 tools/mlogsim.py --sweep-orphans` → `orphan sweep: 2 stale JVM(s) 73508 5104` → `[]`；
随后正常跑 `out/scenes/benches/processor-bench.msch --steps 20 --base 4,32` exit 0、`print: 8|88|88|8`，
跑完再查 `[]`（`out/_jvm_test3.py`）。

## 63.4 复跑

- `tests/probes/run_probes.py`：PASS（gate 内 29.4 s，26/26）。
- `tests/mlogauxiliary/run_ui_smoke.py`：PASS（gate 内 5.2 s）。
- `python -X utf8 tools/kb.py build` → `{chunks: 6421, files: 65}`。
- `python -X utf8 gate.py --full` → **16/16 passed in 42.3s**；gate 前后 `java.exe` 计数都是 `[]`。

诚实记录：本轮第一次 `gate --full` 有 `logicd FAIL`（`job 6578288dd08d03e8 never reached ('rejected',)`，最后状态 `running`），
单独跑 `tests/logicd/run_logicd_tests.py --no-sim` 12/12、复跑 gate 也全绿 —— 判定为并行满载下的假超时（fake provider 是毫秒级），
把 `wait_job` 的 30 s 提到 60 s 作为护栏，没有改动作业状态机。

## 63.5 边界与下一刀

- job object 是 Windows 专属；非 Windows 走 atexit 兜底（硬杀仍可能留孤儿，靠 `--sweep-orphans` 清）。
- `sweep_orphans()` 需要 PowerShell（`Get-CimInstance`）；拿不到就静默返回 `[]`，不会误杀。
- 下一刀回到 P5 主体：**多处理器事务写入**（一个作业 N 段代码、全过才写、任一台失败整体回滚），要先扩 sidecar 作业契约（`jobqueue` 的 job 从 `code` 改成 `codes[]`）。
