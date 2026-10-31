# 70 · mai + logicd v0.12.5：F3 只弹描述框，框留到作业做完，角标点开作业管理

日期 2026-10-31。触发是玩家 m01429 的三句需求（逐字）：

> 框选区域在作业完成之前保留，
> 正在进行的作业在框选区域的右下角显示，点击作业可以查看详细的思考过程。
> 要有一个统一的作业管理窗口。

以及 m01444 的补充：「f3后的窗口简化到只有一个描述框。」

## 70.1 为什么原来的形态做不到

F3 松手走的是区域快照面板（`selFinish()` → `dumpRegion()` → `showRegionPanel()`）：矩形画完就消失，
作业状态只挂在某一个 AI 面板的实例里（`aiJob` 是单槽）。想一次改三台处理器，只能「点一台 → 写描述 → 生成 →
等 → 写入」，换个处理器前面那台的状态就再也看不见了。P5 的第三刀上半（v0.12.0）已经把**事务写入**
（`writeMany()`）做出来了，缺的是**面板上的批量入口**——一次框选、一句话、一批作业。

## 70.2 改法

**F3 = 一个描述框**（`openQuickJob(r)`）：标题一行（单台写坐标，多台写「区域里 N 个处理器」）+ 一个输入框 + 生成/取消。
「生成」→ `startJobBatch(targets, desc, r)`，框里每个处理器各 `jobSubmit` 一个作业（一个处理器一个作业，各写各的）。

**矩形留到这批作业全部终态**（`jobBox = {r, ids, jobs, pend, started, termAt, lastPoll}`）：
`drawSelection()` 在「没在拖」的分支里画 `jobBox.r`；`jobBoxTick()` 每 `JOB_POLL_MS` 只轮询未终态的 id，
全部终态时记 `termAt`，再多留 `JOB_BOX_LINGER_MS = 8000` 才清。

**徽标**（`drawJobBadge()`）：世界坐标画在框底边外侧、右对齐，字用 `Fonts.outline` 按 `1/camerascale` 缩放，
字宽用 `new Packages.arc.graphics.g2d.GlyphLayout(font, text).width` 量（量不出来按字数估——宁可点区大一点，
也不要「看得见点不着」），并写 `jobBadge = {x,y,w,h}` 命中区：
`作业 1/3 · 生成中（点开看）` / `作业 3/3 · 完成（点开看）` / `作业 3/3 · 2 成 1 败（点开看）`。

**点击**（`jobBadgeClick()`）：`Core.input.keyTap(KeyCode.mouseLeft)` + `Core.input.mouseWorldX/Y()` 命中徽标
→ `openJobManager()`。这一下点击世界也会收到（原版是「放方块」那条路），所以只在真有作业框时才抢，
而且框是玩家自己刚画的那块，通常不在放方块的节奏里。

**作业管理窗**（`openJobManager()` / `renderManager()` / `renderManagerDetail()`）：上半「本次框选」，
下半「全部作业（最近的 24 个）」来自 `GET /jobs?all=1&limit=24`；点一条进详情：状态行 + 模型思考
（v0.12.4 的 `jobReasoningLines`）+ findings（≤6）+ `done` 的「写入到 @x,y」（走 `writeBuild(b, jobAsPlan(job))`，
仍是事务写入那条路）+ 非终态的「取消这个作业」+「返回列表」。列表是异步拉的，`managerSeq` 作废迟到回调，
免得点进详情后列表行被追加到详情页里。

## 70.3 sidecar 侧：`/jobs` 要能回答「发生过什么」

`Queue.list()` 答的是在飞（queued/running）。管理窗要历史，于是：

- `tools/jobqueue.py`：`Queue.history(limit=50, state=None)` —— 全部作业按 `(created, id)` 降序；
- `tools/logicd.py`：`/jobs` 加 `all`（`1/true/yes`，`limit` 默认 50、夹 1..200），命中时用 `job_brief()`
  （`BRIEF_DROP = ('snapshot','code','bytes_b64','reasoning','links','assumptions')`）剥重字段
  ——列表每秒拉一次，不能几十 KB 地拖；`SIDECAR_VERSION = '0.12.5'`。

## 70.4 验证

- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，真 v160.7 引擎里整套状态机：
  `MAIJOBBOX0:{"box":false}` → `MAIJOBBOXPIN:{..."total":2,"terminal":0,"linger":false,"badge":"作业 0/2 · 生成中（点开看）"}`
  → `MAIJOBBOXFIN:{..."done":1,"failed":1,"linger":true,"badge":"作业 2/2 · 1 成 1 败（点开看）"}`
  → `MAIJOBBOXCLR:cleared` → `MAIJOBBOX3:{"box":false}` → `MAIJOBMANAGER:no ui`；
  源码红线八条（`function openQuickJob(` / `return openQuickJob(r);` / `function drawJobBadge(` /
  `jobBox !== null && jobBox.r` / `function jobBoxTick(` / `function jobBadgeClick(` / `function openJobManager(` /
  `"/jobs?all=1&limit=`），并断言 `return dumpRegion(r.x1, r.y1, r.x2, r.y2);` **不再出现**；
  旧的 v0.8.1 两条红线（`showAiPanel(one);`、`var one = processorAt(r.x1, r.y1);`）按新路径退役。
- `python -X utf8 tests/logicd/run_logicd_tests.py --no-sim` → protocol 26 / jobs 16 / provider 12 / llm 12。
- 断言表新增 L2-54（模组侧：描述框 / 保留框 / 徽标 / 管理窗）、L2-55（sidecar 侧 `/jobs?all=1` + `job_brief`）。

## 70.5 边界与下一刀

- 模组版本 `0.12.5`（`mod.hjson` 与 `MOD_VERSION` 同版号）：**这次模组必须重装/重启游戏**，sidecar 必须重启
  （`GET /health` 的 `version` 是 `0.12.5` 才对）。
- 旧的区域快照面板没删（控制台 `maiDump` 与 AI 面板那条老路还在）；F2 清单面板不动。
- 联机拒绝写入的「无权限」提示、冲突检测比链接表、打包安装即用（最后）仍未做。
