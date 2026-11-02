# v0.21.0 档1：对话窗与工作区窗共用一套外壳（2026-11-02）

## 1 起因

用户 m04199：「这个对话很舒服，能直接把工作区快照并入MAI对话里面吗？不用做，只告诉我是否可行和方案。」
当时给了三档：档0 互联跳转（约 60 行）/ 档1 共用双栏骨架 + 同一窗口两种模式（约 250–350 行）/
档2 列表合流（约 300–400 行）/ 档3 侧车 workspace 工具化（2–3 天）。
用户 m04211：「可以，先做档1，再做档3」 ⇒ 本轮只做档1，档2 暂缓，档3 等装机验证后另起。

## 2 为什么先抽外壳而不是先拆布局

v0.19.4 / v0.19.6 / v0.20.2 三次排版事故（标题居中、卡片色条跑到中间、新对话按钮铺满左栏）有一个共同成因：
「对话框初始化」这段代码在 `openChatDialog()` 与 `openWorkspaceDialog()` 里各有一份 ——
`new Packages.arc.scene.ui.Dialog("Mlog辅助 · … v" + MOD_VERSION)`、`d.cont.defaults().pad(3).left()`、
`d.title.setAlignment(Align.left)`、`d.titleTable.clearChildren()` 重建，逐字同构。修一份漏一份，于是同一个 bug 反复出现。
所以档1 的第一刀不是挪布局，而是**把外壳变成只有一份**：先建立共用外壳，再让两个窗口成为它的两种模式。

## 3 改法（`MlogAuxiliary/scripts/main.js`）

在 `function openChatDialog(){` 之前新增共用外壳区（行号见收尾）：

- `var DUAL = { last: "chat" };` —— 记住上一次的模式（真机上看，切走再切回不会重置到对话）。
- `dualModes()` / `dualModeCn(mode)` —— 模式表与中文名（`chat`→「对话」、`ws`→「工作区」）。
- `dualHideOthers(mode)` —— 开一个之前先 `hide()` 另一个；两边各自 `hidden()` 负责收尾
  （对话窗 `CHAT_UI.open = false` 并退订轮询，工作区窗清 `wsUI.ghosts` / `wsUI.needGeom`）。
- `dualSwitch(mode)` —— 分段开关的落点：`DUAL.last = mode; dualHideOthers(mode); return open…Dialog();`。
- `dualChrome(d, mode)` —— 标题行：`d.title` 左对齐 + `titleTable.clearChildren()` 后用自然宽度靠左放标题，
  再在右侧挂两个 64×22 的分段按钮「对话」「工作区」，当前模式那个 `disabled(true)`。
  这一段把 v0.19.4（整行被标题撑开）与 v0.19.6（cell 默认居中）两次的补救合并成唯一实现。
- `dualDialog(titleCn, mode)` —— 统一构造：`dualHideOthers(mode)` → `new Dialog("Mlog辅助 · " + titleCn + " v" + MOD_VERSION)`
  → `d.cont.defaults().pad(3).left(); d.cont.left().top()` → `d.closeOnBack()` → `dualChrome(d, mode)` → 返回 d。

两个 open 函数只留一行：

| 窗口 | 原来 | 现在 |
| --- | --- | --- |
| 对话 | `new Dialog(..."自由对话 v"...)` + `cont.defaults()` + `left().top()` + `title.setAlignment` + `titleTable` 重建 + `buttons.left()`（8 行） | `var d = dualDialog("自由对话", "chat");` |
| 工作区 | 同上（标题「工作区快照」）+ 两段 v0.19.4/v0.19.6 的解释注释（17 行） | `var d = dualDialog("工作区快照", "ws");` + 保留 `try{ d.buttons.left(); }catch(e0c){ }` |

**刻意不改**：`chatPlan()` / `wsDialogPlan()` 的宽度数学、两窗各自的分栏与底栏顺序。
理由：两者都有探针断言（`MAICHATUI` 的 980/206/22/752 恒等式、`MAIWS3` 的 plan-fit 与 `caps`），
一次性重写会把已稳的排版重新变成风险。底栏也不统一 —— 对话窗按 L2-109 右对齐（新对话在最右），
工作区窗按 L2-98 靠左，各自有红线守着。

## 4 自检与红线

- 新探针 `api.maiDualProbe`（无头可跑，只碰纯状态）：`MAIDUAL:ok modes=chat,ws cn=对话/工作区 last=chat`。
- `tests/mlogauxiliary/run_ui_smoke.py`：探针打印 + 前缀白名单（两处）+ `if 'MAIDUAL:ok' not in joined` 断言；
  v0.21.0 红线 9 条正向（`function dualDialog(` / `function dualChrome(` / `function dualSwitch(` /
  `function dualHideOthers(` / `var d = dualDialog("自由对话", "chat");` / `var d = dualDialog("工作区快照", "ws");` /
  `seg.button("对话"` / `seg.button("工作区"` / `dualChrome(d, mode);`）+ 2 条反向
  （源码里不许再出现 `new Packages.arc.scene.ui.Dialog("Mlog辅助 · 自由对话 v"` 与 `…工作区快照 v"`）。
- `node --check MlogAuxiliary/scripts/main.js` → exit 0；ui smoke exit 0。

## 5 留给真机验的

1) 打开「MAI 对话」→ 标题行右侧应看到「对话」（灰、不可点）与「工作区」（可点）；点「工作区」应换成工作区窗，
   标题行里的「工作区」变灰、「对话」可点；再点回来，会话列表与之前选中的会话应还在（`DUAL.last` 与 `CHAT_UI` 各自保留状态）。
2) 从作业管理窗「＋ 新建对话」或蓝图页「MAI 对话」打开时，若工作区窗正开着，应先关掉它而不是两个窗口叠着。
3) 若切换后仍有窗口被撑宽 / 按钮拉伸，`last_log.txt` 里会有 `[mai] chat geom:` 与 `[mai] ws geom:` 两行真实宽高，
   这次多了一项模式信息（`dual` 状态不进 dump，但 `last=` 在 `MAIDUAL` 探针里）。

## 6 收尾

门禁 `python -X utf8 gate.py --full --kb-build` → **17/17 passed in 112.4s**（`out\_gate_v210.log`）。
打包 → `out/_dist/MAI-0.21.0/` **191 files / 19,418,242 B**；`MAI-0.21.0-mod.zip` 8,710,049 B（sha256 `5A1B92F2…`）、
`MAI-0.21.0.zip` 8,732,632 B（sha256 `6BF9F7FF…`）。装机 [ok]，备份 `MlogAuxiliary-20261102-223457`。
本地提交、公开仓提交 **9b42e44** + tag `v0.21.0`、Release v0.21.0（两个 zip 201）。
下一步：等真机复核「对话 / 工作区」切换是否顺手；通过后再做档3（工作区工具化，侧车 `/chats` 里加 workspace 工具）。
