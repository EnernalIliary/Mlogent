# 62 · v0.10.1：投递之后处理器被改过，第一次写入会被拒绝（P5 第二刀）

日期 2026-10-30。P5 规划里「写入前重读 code，与快照不一致 → 提示被改过」的**模组侧一半**。

## 62.1 症状

作业是异步的：面板投递后要等 sidecar 跑完（模型档可能几十秒）。等结果的时候玩家顺手在原版编辑器里
改了代码，回来点「写入」——作业结果把这段改动静默覆盖，且没有任何提示。

## 62.2 判据

冲突基线不是撤销快照（v0.10.0 那份是**写入前一刻**拍的，拍完立刻写，中间没人有机会改），
而是**投递那一刻**的代码。判定：`String(b.code) !== String(orig)` 即视为被改过。
保守到字符串全等（行尾空白不同也算改过）是有意的：宁可按一次确认，也不静默覆盖。

## 62.3 改动（`MlogAuxiliary/scripts/main.js`）

| 名字 | 职责 |
| --- | --- |
| `JOB_ORIG` / `JOB_FORCE` | `"x,y" -> 投递时代码` / `"x,y" -> 已拒绝过一次` |
| `procKey(b)` | `String(b.tile.x) + "," + String(b.tile.y)`，异常回 `"?"` |
| `rememberOrig(b)` | 记基线并清 force 标记；`jobSubmit()` 与 `jobSync()` **两条投递路径都调** |
| `forgetOrig(b)` | 写成功后基线过期（否则下一次写入会误报） |
| `conflictReason(b)` | 代码相同 → `null`；不同 → 「处理器在你投递作业之后被改过（提交时 N 行，现在 M 行）」 |
| `conflictGate(b)` | 有冲突且未 force → 置 force 并返回拒绝文案；已 force → 消费掉并放行（**只放行一次**） |
| `api.maiConflictProbe()` | 无头自检：假处理器（只有 `tile` 与 `code`）验三分支，不碰存档、不写快照 |

`writeBuild()` 的四道闸变成：0 ERR → 有载荷 → **没被改过（新）** → 落快照 + `configure`。

## 62.4 两个坑

1. **`jobSync()` 是第二条投递路径，最初漏了记基线**：它是控制台/测试用的同步入口
   （`httpRaw("POST", "/jobs")` 自己拼，没走 `jobSubmit`），漏记导致端到端用例第一次写入没被拒绝。
   ui smoke 里「投递 → 改代码 → 第一次写入必须被拒」这条用例直接把它抓出来了。
2. **不用对话框**：无头环境 `Core.scene` 是 null，`showConfirm` 会 NPE。所以交互设计成
   「拒绝一次 + 再点一次算确认」，真机与测试走同一条代码路径，不必为测试造第二条。

## 62.5 验证

- `MAICONFLICT:ok`：拒绝 → 放行一次 → 第三次又问 → 代码没动过不问（三分支全覆盖）。
- 端到端（真 sidecar + 真 v160.7 处理器）：`maiJobSyncAt` 投递 → `updateCode('set n 7' + \n + 'end')`
  → 第一次 `maiJobWrite` 返回「被改过」且**处理器代码未变**；第二次「已写入」。
  摘要行：`job conflict gate: first write refused, second click overwrote`。
- `run_ui_smoke.py` EXIT=0；`MAIDIAG:版本：0.10.1（游戏构建 160）`；作业三路（done / 门禁拒绝 / 零链接拒绝）仍全过。
- `gate.py --full`：见 §62.6（本轮实跑数据）。

## 62.6 边界与下一刀

只覆盖「单处理器 + 一次写入」。多处理器事务写入（一个作业 N 段代码、全部预检通过才写、任一台失败整体回滚）
是 P5 剩下的主体，要先扩 sidecar 的作业契约（`jobqueue` 的 job 结构从 `code` 改成 `codes[]`）。
冲突检测只比代码文本，不比链接表；链接表由 `configure` 的载荷决定，目前没有「玩家改了链接」的场景。

## 62.7 环境发现：61 个残留 JVM 把 probes 档打红过一次

本轮 `gate.py --full` 首跑 `probes FAIL`，26 条全红，错误是
`There is insufficient memory for the Java Runtime Environment to continue` / `os::commit_memory ... failed`。
不是代码回归：`Get-Process java` 有 **61 个**残留 JVM（全部是 `out/jre21/... -jar out/_server160.jar`，
最早 20:17 起，每只 30-220 MB），系统可用内存只剩 1.4 GB。
`Stop-Process` 清掉后 → `tests/probes/run_probes.py` **26/26 passed**、`gate.py --full` **16/16 in 47.5s**。

泄漏源没定位（`tools/mlogsim.py` 的 `Server.close()` 只关进程不删 `out/_sim/run-*`，但这里连进程都没退，
更像异常路径或被 kill 的 run 留下的孤儿）。**下一刀候选**：给 `Server` 加 `finally` 兜底 +
在 `run_probes`/`run_ui_smoke` 收尾时扫一遍 `out/jre21` 起的 java 清孤儿，否则连续跑一天就会撞内存墙。
