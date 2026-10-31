# 80 · v0.14.1 工作区快照 W2/W3/W4：界面 + 继续改进 + 导入导出 + 蓝图入口

日期：2026-10-31。触发：用户 m04147「继续，直接做完，然后我验证」（承接 m03632 的工作区快照要求与
`docs/Mlog辅助-工作区快照-规划.md` 的 W1–W5 分阶段）。W1（v0.14.0，提交 `5df6ece`）只落了数据层，
磁盘上有 JSON 但玩家看不见、也不能「接着上一版改进」——本版把 W2/W3/W4 一次做完。

## 1. 做了什么

### 1.1 W2：工作区界面（仿蓝图对话框）

`MlogAuxiliary/scripts/main.js` 新段「工作区界面（v0.14.1，W2/W3/W4）」：

- 预览文本：`wsTimeText()`（`10-31 22:10`）、`wsRowLabel()`（`名字 · N 台 · 进行中/已归档 · 时间`）、
  `wsBoundsText()`（`地图 <name> (x1,y1)-(x2,y2)`）、`wsProcLines()`（每台 `@x,y block N 行 · 写过 M 次 · 描述`）、
  `wsJobLines()`（最近 3 个作业 `#id 状态 描述 时间`）。
- `openWorkspaceDialog()`：`Dialog("Mlog辅助 · 工作区快照 v" + MOD_VERSION)` + `pane(host).height(320).width(600)`，
  底部按钮「刷新 / 从蓝图创建 / 关闭」。
- `renderWorkspaces()`：列表分两段（进行中、已归档），空段给一句人话提示。
- `renderWorkspaceDetail()`：标题 + 范围 + 创建/更新时间 + 备注 + 处理器清单 + 最近作业，
  按钮「恢复选框 / 继续改进 / 归档（或取消归档）/ 释放 / 导出 JSON / 返回列表」。
- `wsRestoreBox(id)`：把 `jobBox` 重新指到该工作区的 `bounds`，**故意不给 `ids`** ——
  `jobBoxState()` 在 `total === 0` 时不画徽标（`jobBadgeText()` 返回空），也不会去轮询空作业。
- `wsRename(id, name)`：去换行/制表符、剥首尾空白、上限 40 字符、空名拒绝。

### 1.2 W3：继续改进（`mode:"improve"`）

- 模组侧 `wsImprovePayload(ws, b)` → `{id, name, notes, prevCode, prevJob, prevFindings}`；
  没有 `prevCode` 就返回 `null`（第一次投递不产生空段）。
- `jobBody(b, desc, wsInfo)`：有 `wsInfo` 时 `job.mode = "improve"` 且 `job.workspace = wsInfo`；
  `jobSubmit(b, desc, cb, wsInfo)` 透传；`startJobBatch(targets, desc, rect, improve)` 逐台算 payload。
- `openQuickJob()`：框内工作区有上一版时，多一个「改进上一版」按钮（描述留空则默认「在上一版的基础上继续改进」）。
- `wsImproveBatch(id, desc)`：工作区里每台写过代码的处理器各投一单 improve（找不到建筑就跳过）。
- `wsRecordTerminal()` 现在把 `findings`（`sev`/`rid`/`msg` 截 300 字符、最多 12 条）也记进 `jobs[]`，
  这是 `prevFindings` 的来源。
- sidecar 侧（teammate `sidecar-dev` 实现，我复核后并入）：
  - `tools/jobqueue.py`：`WS_NAME_MAX=120` / `WS_NOTES_MAX=500` / `WS_CODE_MAX=4000` / `WS_JOB_MAX=64` /
    `WS_FINDINGS_MAX=12` / `WS_FINDING_MAX=300`；`workspace_of()` / `_ws_code()` / `_ws_text()`；
    `job_id(snapshot, desc, mode, prev_code=None)` **只在 improve 时**把 prevCode 计入 blob
    （new/edit 的作业 id 与 v0.13.2 逐字节不变，用两个硬编码 legacy id 常量锁死）；`normalize()` 的
    mode 白名单加 `improve`、返回 dict 带 `workspace`。
  - `tools/mlogprovider.py`：`previous_version(job)`（`PREV_VERSION_MAX=1200`、`PREV_FINDINGS_MAX=6`），
    `build_prompt()` 在 `=== task ===` 前插 `=== previous version (same area) ===`；
    4000 字符 prevCode 实测段本体 1198 字符，加与 `=== task ===` 之间的分隔空行恰好 1200（卡在硬上限内）。
  - `tools/logicd.py`：`SIDECAR_VERSION = "0.14.0"`。

### 1.3 W4：导入导出 + 蓝图入口

- `wsExportText(id)` / `wsExportToDisk(id)`（写 `<dataDir>/mlogauxiliary/workspaces/export/<id>.json`）。
- `wsImportText(text)`：复制语义 —— 撞 id 就换一个新 id，不覆盖现有工作区；`procs` 只保留
  `k/x/y/block/desc/links/code/accepted`（`history` 丢掉，历史属于原工作区）。
- `blueprintList(maxRows)`：`Vars.schematics === null` 时回空数组（**无头模拟器里它就是 null**，
  直接 `sch.all()` 会炸），`size` 先当方法再当字段。
- `wsFromBlueprintName(name)`：按玩家脚下摆范围（`Vars.player.tileOn()`），无头没玩家就摆地图中心；
  建出来的工作区 `notes` 记「来自蓝图「X」(W×H)」，处理器清单为空。
- `renderBlueprintPicker()`：把蓝图列成按钮，点一个建一个工作区。

### 1.4 入口（第一次做完漏了，补上）

光有 `openWorkspaceDialog()` 玩家打不开。两个入口：

- 「设置 → Mlog辅助」主面板底部按钮 **工作区快照**（`openPanel()` 的 `d.buttons`）。
- 作业管理窗（点框右下角徽标）底部按钮 **工作区快照**（`openJobManager()` 的 `d.buttons`）。

红线 `d.buttons.button("工作区快照"` 守着它，删掉就红。

### 1.5 顺手修掉的一个真 bug：findings 以 Python repr 进 prompt

模组送的是 `{sev, rid, msg}` 对象，`tools/jobqueue.py` 的 `workspace_of()` 原来
`rows.append(str(f)[:300])` —— 模型读到的是
`- {'sev': 'WARN', 'rid': 'unreachable-statement', 'msg': 'x can never run'}`。
改成 `_ws_finding(f)`：对象渲染成 `WARN unreachable-statement: x can never run`，
字符串原样截断，None 丢弃。`tests/logicd/run_logicd_tests.py` 的 `test_improve()`
加了断言（不许出现 `{`、必须以 `WARN <rid>:` 开头），实测 prompt 段变成：

```
=== previous version (same area) ===
  set n 1
  jump 0 always
  - WARN unreachable-statement: x can never run
```

## 2. 验证（机器可验）

```
node --check MlogAuxiliary/scripts/main.js                     → exit 0
python -X utf8 tests/mlogauxiliary/run_ui_smoke.py             → EXIT=0
    MAIDIAG:版本：0.14.1（游戏构建 160） ...
    MAIWORKSPACE:ok dir=yes mem=yes
    MAIWS2:ok
python -X utf8 tests/logicd/run_logicd_tests.py                → logicd OK (exit 0)
    protocol 26 / jobs 16 / provider 12 / improve 7 / llm 12 check(s) passed
    write path: 7 template(s) accepted by the game
python -X utf8 tests/run_tests.py                              → 46/46 passed
python -X utf8 gate.py --full --kb-build                       → 17/17 PASS
```

`MAIWS2:ok` 是新增的自检口 `api.maiWorkspace2Probe()`，在内存表上跑 14 项：
`rowlabel` / `bounds` / `proclines` / `joblines` / `export` / `import` / `import-id` / `import-procs` /
`rename` / `payload` / `payload-code` / `payload-id` / `restorebox` / `restorebox-ids` / `restorebox-msg` /
`blueprint` / `blueprint-miss` / `improve-miss`。任何一项失败都会在 `MAIWS2:bad <项>` 里点名，
ui smoke 断言 `MAIWS2:ok`。

## 3. 这一版踩到的坑

1. **`api.*` 的赋值位置必须晚于 `var api = {`**：W1 时把 `api.maiWorkspaceProbe` 写在工作区段里（约 :1290，
   而 `var api = {` 在 :3594）⇒ 脚本一加载就 `TypeError`。这次所有新口子都放在 `api` 段内。
2. **`var payload` 声明了但没传给 `jobSubmit`**：第一次补丁只在 `startJobBatch` 里加了
   `var payload = ...`，调用处仍是 `jobSubmit(t.b, desc, function(...){...})` ⇒ improve 永远退化成 new。
   修法是给那次调用补第 4 个实参 `, payload`（用 grep `jobSubmit\(t.b` 复核过）。
3. **PowerShell 单行 `python -c` 里带引号/括号的替换会被 PS 解析器打断**（`表达式或语句中包含意外的标记`），
   而且这次连「把补丁脚本里的 `'0.14.0'` 换成双引号」这种小修都被吃掉。
   教训重复第二次：**改文件一律写 `.py` 脚本文件再跑**，不在 `-c` 里拼引号。
4. **补丁脚本里的中文长串同样怕引号**：`out/_w2_doc_v141.py` 里一行 `'...SIDECAR_VERSION='0.14.0'...'`
   把单引号字符串提前闭合，`SyntaxError` 报在 `row = (` 的**第一行**（Python 把整个表达式的起点当错误位置），
   很容易误判成「文件被写坏了」。改法是把长文本放进独立 `.txt`，脚本只负责读 + 插行。
5. **`blueprintList()` 不能假设 `Vars.schematics` 存在**：无头里它是 `null`（`Vars.ui`、`Vars.player`、
   `Core.camera` 同样是 null）。所以蓝图入口第一版不 hook 原版 `SchematicsDialog`（它 `setup()` 里自己重建 cont），
   只在自己的对话框里加一页。

## 4. 已知边界

- 工作区是本地上下文，不广播；联机里写入仍走 `permWhy()` + `armWriteCheck()` 两条闸。
- W5（sidecar 索引工作区、CLI 可读）**没做**，规划里它本来就是可选项。
- 「继续改进」一次投一单/台处理器，没有跨处理器的协同寻址（规划 §8 明确不做）。
- `GET /jobs?all=1` 的历史行现在会带 `workspace`（prevCode 最多 4000 字符），单行 payload 可能到 5–6 KB；
  目前模组侧只读列表行做展示，暂不剥字段（要剥就改 `job_brief()` 的 `BRIEF_DROP`，属 sidecar 语义，留作后续）。
