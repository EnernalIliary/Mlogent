# 79 · v0.14.0 W1：一个选框就是一个工作区（数据层）

日期：2026-10-31
需求来源：用户 m03632（工作区快照）、m03723（先做两个小功能再规划）、m03985「我同意按照你的做」
规划稿：`docs/Mlog辅助-工作区快照-规划.md`（W1–W5 五阶段；本轮只做 W1）

## 79.1 为什么先做数据层

用户的原话是「相当于每个选框就是一个工作区快照。即使写完一次逻辑也不会让工作区消失，保留上下文，可以选择归档或释放工作区释放工作区就不再留存上下文」。

拆开是四件事：①选框 ↔ 工作区一一对应 ②写完不消失、保留上下文 ③能归档/释放 ④有仿蓝图的界面。

界面（W2）、继续改进（W3）都依赖同一件东西：**工作区得先有地方存、有稳定的 id、有「这块区域属于哪个工作区」的判定**。
所以 W1 只做这一层，且**纯模组侧**——sidecar 版本不动（仍是 0.13.2）。

## 79.2 数据模型

落盘位置：`Vars.dataDirectory/mlogauxiliary/workspaces/<id>.json`（与撤销快照 `.../undo/` 同一层）。

```json
{
  "schema": 1, "mod": "0.14.0",
  "id": "ws1793456316430_1",
  "name": "区域 (12,34)",
  "state": "active",
  "map": "Ground Zero",
  "world": {"width": 300, "height": 300},
  "bounds": {"x1": 8, "y1": 30, "x2": 16, "y2": 38},
  "created": 1793456316430, "updated": 1793456319000,
  "procs": [{
    "k": "12,34", "x": 12, "y": 34, "block": "processor",
    "desc": "给核心补铜", "links": [{"name": "container1", "x": 9, "y": 33}],
    "code": "loop:\nsensor n container1 @copper\nend",
    "accepted": 2,
    "history": [{"at": 1793456319000, "desc": "给核心补铜", "code": "…"}]
  }],
  "jobs": [{"id": "3f2a1b9c", "desc": "给核心补铜", "at": 1793456316430, "state": "done"}],
  "archivedAt": 0
}
```

上限：工作区 200（`WS_KEEP`）、每个处理器的历史 20 条（`WS_HISTORY`）、作业引用 50 条（`WS_JOBS`）。
淘汰按 `updated` 升序，即最久没动过的先掉。

复用判定：`wsFindActive(rect)` = 选框**中心**落在某个 `state === "active"` 工作区的 `bounds` 内，且 `map` 相同；
命中则 `bounds` 取并集（先框一小块再框一大块仍是同一个工作区）。选中心而不是「完全包含」，因为玩家两次拖框很难一模一样。

## 79.3 改动清单（`MlogAuxiliary/scripts/main.js`，4,366 行）

| 位置 | 改动 |
| --- | --- |
| 新段（`// ---- 写前冲突检测` 之前） | 常量 + 30 个 `ws*` 函数：`wsRoot`/`wsFileOf`/`wsReadText`/`wsWriteText`/`wsDeleteFile`/`wsFileNames`/`wsParseText`/`wsLoad`/`wsSave`/`wsList`/`wsPrune`/`wsCenter`/`wsNameFor`/`wsNew`/`wsFindActive`/`wsProcOf`/`wsTouchProc`/`wsAttach`/`wsTouchHere`/`wsAccepted`/`wsRecordJob`/`wsRecordTerminal`/`wsArchive`/`wsRestore`/`wsRelease`/`wsStateText` |
| `startJobBatch` | 首行 `var ws = wsAttach(rect, targets, desc);`，`box` 带 `ws`；投递成功回调 `wsRecordJob(ws, jid, desc);`；投递完提示追加「工作区「X」已保存，继续框这块会复用」 |
| `jobBoxTick` | `jobChatDone(...)` 之后 `wsRecordTerminal(wsLoad(jobBox.ws), jobBox.jobs[want]);` |
| `startJob` | 描述检查后 `var ws = wsTouchHere(b, desc);`，回调里 `wsRecordJob(ws, String(res.id), desc);` |
| `writeBuild` | `jobBoxWritten(b)` 之后 `wsAccepted(b, res);` |
| `writeMany` | `forgetOrig` 循环之后逐台 `wsAccepted(items[i].b, items[i].res);` |
| `openQuickJob` | 标题拼「· 工作区「X」」+ 一行说明（复用/新建） |
| `api.maiJobBox` | JSON 加 `ws: jobBox.ws \|\| null` |
| `api.maiWorkspace*` | `List` / `Archive` / `Restore` / `Release` / `Current` 五个口子（W2 的界面直接调） |
| 自检口 | `api.maiWorkspaceProbe()`（在 `var api` 之后，:4184）：把三个存储原语换成内存表，跑 save / roundtrip / procs / reuse / noreuse / job / archived / state / restore / release-load / release-file 十一件事 |
| 版本 | `MOD_VERSION` 0.13.2 → 0.14.0；`mod.hjson` 同步 + description 追加 |

## 79.4 验证

- `node --check MlogAuxiliary/scripts/main.js` → exit 0。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，且可见
  `MAIDIAG:版本：0.14.0`、`MAIJOBPANEL:ok assumptions=2 cost=3 first=假定一`、**`MAIWORKSPACE:ok dir=yes mem=yes`**、
  `MAIJOBBOXPIN` 的 JSON 里出现 `"ws":null`（新字段生效）。
- 无头模拟器里 `Vars.dataDirectory` 是有值的（`MAIDIAG` 的「数据目录」行指向 `out/_sim/run-*/config`），所以 `dir=yes`；
  探针仍然走内存表，不依赖真磁盘。

## 79.5 边界 / 没做

- **没有界面**：归档/释放/列表/预览都在 W2；本轮只保证 `api.maiWorkspaceList/Archive/Restore/Release` 能用。
- **没有 `mode:"improve"`**：`jobBody()` 不带 `workspace`，因为 `tools/jobqueue.py:normalize()` 只认白名单字段
  （`desc`/`mode`/`snapshot`/`links`/`origin`/`ipt`/`created`…），多塞的字段会被静默丢掉——要它有用得改 sidecar，归 W3。
- **没有跨地图迁移**：`map` 不一致就不复用，旧工作区留着但不会自动接上。
- 单台处理器投递只在已有工作区里记 `job`，不凭空造工作区（避免作业面板点一台就长出一堆单处理器工作区）。
