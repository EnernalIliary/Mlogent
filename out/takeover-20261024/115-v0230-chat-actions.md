# 115 · v0.23.0：对话 agent 真能动手（写蓝图 / 跑命令）、能看见玩家与服务器、回话变好看、输入能换行

日期：2026-11-03　版本：v0.23.0　对应模组 `MlogAuxiliary/scripts/main.js` 与侧车 `tools/chats.py`

## 1. 问题（用户一次点了五项）

对话窗里的模型一直只能「说」：

1. 它生成出蓝图码，玩家只能自己去原版蓝图库手抄 —— 缺一个「直接存进蓝图库」的口子；
2. 它想说「你跑一下 status 看看」只能让玩家自己敲命令 —— 缺一个「执行控制台命令」的口子；
3. 它不知道玩家叫什么、在哪、几波、TPS 多少，问「我现在这局怎么样」只能空谈；
4. 它爱用 markdown（标题、加粗、行内代码、列表、围栏代码块），这些整段原样贴进 Label，屏幕上是一堆星号井号；
5. 输入框是单行 `TextField`，回车即发，长问题只能挤一行；而且两只窗口总在屏幕正中，挡视野。

## 2. 方案（关键取舍）

- **动作用「两段式」**：模型只能 `bp_add` / `console_run` **登记意图**，绝不直接落库或执行；模组拿到 `doc.chat.intents` 后弹
  `Vars.ui.showConfirm("MAI · 执行动作", …)` 把这条要做什么摊开给玩家看，点确认才真跑。理由：这两个动作会改硬盘上的蓝图库、会在联机里对外发消息，
  都属于「不可撤销且对外可见」，不能让模型自己决定。也验证过：无 `Vars.ui` 的无头环境 `chatTakeIntents()` 返回 −1、不弹、不执行。
- **只读数据走快照**：玩家/服务器状态由模组侧算好、裁剪后随请求下发，侧车只加两个**只读**工具 `player_info` / `server_info` —— 与 v0.22.0 的 `ws_*` 同一套路，
  进程边界那侧永远拿不到「写」的能力。
- **markdown 转换器必须零正则**：本仓断言表 L2-31 早就记过「Rhino 有两类编译期 codegen bug，try/catch 抓不住」，这一版第一次实现时用了 13 条正则字面量
  直接踩中（详见 3.4），所以最终实现是纯字符扫描。
- **回车发送只能在 listener 里拦**：`TextArea` 回车时先插入换行、再调 listener，所以 listener 拿到的字符串末尾就是这个换行 —— 抠掉它再发，
  Shift 在场就留着。这样既不多写一个按键钩子，也不用改 `TextField` 的机制。

## 3. 改法（文件 / 函数 / 行号）

### 3.1 模组 MlogAuxiliary/scripts/main.js（9183 行，MOD_VERSION 0.23.0）

- **markdown → 标签**（新增 154 行，插在原 `mdInline` 位置）：`mdWrapPairs`(:5147 成对定界符换标签，不成对原样留)、
  `mdLinkToText`(:5163 `[文字](地址)` → `文字 (地址)`)、`mdStripHtml`(:5185 只吃「<字母/空格>」这类短标签)、
  `mdInline`(:5205 行内：代码 → 浅灰、** / __ → 强调色、* / _ → 浅灰)、`mdToTags`(:5258 按行：围栏代码块 / 标题 / 引用 / 无序 / 有序 / 分隔线)。
  方括号转义沿用 `MD_LB = "\u0001"` 占位（arc 只认 [[`，] 不转义）。
- **assistant 气泡**：`chatWrap(dp, mdToTags(content), iw)`（:5115）。
- **玩家 / 服务器快照**：`playerDigest()`(:5924)、`serverDigest()`(:5953)（无头都返回 null；坐标 ÷8 取格；`p.name` 可能是方法所以先 `typeof` 判一下）；
  `chatSend()` 里 `req.player = pd`(:4831) 与 `req.server = sd`。
- **意图队列**：`CHAT_INTENT`(:5307 存 key/shown 去重)、`chatIntentList`(:5308 只认 bp/console、最多 8 条)、`chatIntentLine` / `chatIntentText`、
  `chatTakeIntents`(:5343 用 id#rounds#count 做 key，无 Vars.ui 返回 −1)、`chatRunBp`(:5365)、`chatRunConsole`(:5392)、`chatRunIntents`(:5416 逐条 try + log + showText)、
  `chatShiftDown`(:5434)；`chatPoll()` 的 `running !== true` 分支首行调 `chatTakeIntents(doc.chat)`(:4898)。
- **输入框**：`new Packages.arc.scene.ui.TextArea("")`(:5583) + `setPrefRows(2)` 包 try，listener 里拦换行；输入框与「发送」按钮高度 34→56。
- **贴右停靠**：`DUAL.dockRight = true`、`dualDockRight(d)`(:5500，`d.getScene()` 宽高、scene 宽 − 窗宽 − 12、垂直居中、差 ≤0.5px 不动)、
  `dualDock()`(:5516)；update 钩子每帧调一次（:9055），两个 `d.show();` 之后各补一次。
- **探针** `api.maiChatActionsProbe`(:9004)：`ok md=7 esc=a [[b] c intents=2 took=-1 player=null server=obj dock=true`。

### 3.2 侧车 tools/chats.py（1452 行，纯 LF）

- 常量 `SNAP_*` / `INTENTS_MAX = 4` / `BP_CODE_MAX = 20000` / `CONSOLE_CMD_MAX = 300`（:49-57）；
- TOOLS 追加 `player_info` / `server_info` / `bp_add` / `console_run`（:206 / :217 / :228 / :245），SYSTEM_PROMPT 加三行（只读快照 / 动作需玩家确认 / 超限截断）；
- `start()` 按 key 存在才更新快照、`chat["intents"]` 每轮清零（:620-624）；`_run_loop` 挂 `_CTX.player/server/intents`（:792-796）；
- 实现区 :1212-1330（`_snap_get` / `_snap_lines` / `_snap_report` / `_player_info` / `_server_info` / `_intent_rows` / `_intent_refuse` / `_bp_add` / `_console_run`），分派 :1038-1045；
- `_brief` 只报 intents 条数与 has_player/has_server 布尔（:470-472），`_full` 才给全文（:511）—— 摘要不许把快照原文漏进列表接口。

### 3.3 测试

- `tests/mlogauxiliary/run_ui_smoke.py`：新增 `MAIACT` 打印 + `MAIACT:ok` 断言 + 12 条 v0.23.0 红线（md 转换器存在 / assistant 走 mdToTags / 方括号还原 /
  playerDigest / serverDigest / req.player / chatTakeIntents(doc.chat) / 确认框标题 / Schematics.readBase64 / Call.sendChatMessage / TextArea("") / chatShiftDown / dualDock）；
- `tests/logicd/run_logicd_tests.py`：`_ChatStub` 支持一轮连发多个工具调用（`calls=[(name,args),…]`，旧路径行为不变），`test_chats` 新增第 9 节 6 条 check
  （快照能读回 / 意图字段形状 / 5 条只落 4 条 / brief 只报条数 / 20000 与 300 截断明说 / 下一轮 intents 清零且 null 快照回人话），chats 11→17 条。

### 3.4 踩到的真机级坑（写进断言表 L2-118）

第一版 markdown 转换器用了 13 条正则字面量。`python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` 报
`FAIL engine call: … IllegalStateException: FAILED ASSERTION: invalid bytecode`，且引擎侧 `srv.js` 因为等不到标记而超时。
定位：`out/_server160.jar` 里 `rhino/Kit.class` 有 FAILED ASSERTION、`rhino/regexp/NativeRegExp.class` 有 invalid bytecode ⇒ 是 `Kit.codeBug`，
发生在**构造/编译期**，所以 JS 的 try/catch 抓不住，整段脚本静默不执行（与 L2-31 同源）。全部改成字符扫描后转绿。

## 4. 验证

- `node --check MlogAuxiliary/scripts/main.js` 通过（9183 行）。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → rc 0，关键行：`MAIACT:ok md=7 esc=a [[b] c intents=2 took=-1 player=null server=obj dock=true`、
  `MAIDIAG:版本：0.23.0（构建 160）`、`MAIWS3:ok` / `MAIDUAL:ok` / `MAIWSDIGEST:ok` 全在（日志 `out/_smoke230c.log`）。
- `python -X utf8 tests/logicd/run_logicd_tests.py --no-sim` → 全绿 exit 0：protocol 26 / jobs 17 / provider 12 / improve 8 / llm 12 / **chats 17** / diag 7 / life 3。
- 版本三处对齐：`MOD_VERSION = "0.23.0"`、`MlogAuxiliary/mod.hjson` 的 `version: "0.23.0"`、`SIDECAR_VERSION = '0.23.0'`。

## 5. 留给真机验的

1. 颜色名：本仓 Mindustry 源码 checkout 不全（没有 `mindustry/core/Colors.java`、没有 `Pal.scarlet`），`out/_server160.jar` 里也没有 bundle.properties，
   所以 [accent] / [lightgray] / [gray] / [] 只能靠真机截图确认 —— 若某个名字不认，界面会显示成原文的 [accent]。
2. `bp_add` 落库后是否立刻出现在原版蓝图列表（`Schematics.add` 内部 write + all.sort，理论上要重开蓝图面板才刷新）。
3. 联机里 `console_run` 走 `Call.sendChatMessage("/"+cmd)`：服务端 `clientCommands.handleMessage` 认不认这条消息、有没有权限，得开一局本地联机验。
4. 贴右停靠在小窗口/高 DPI 下会不会压到右侧 UI（`dualDockRight` 拿的是 scene 宽，Arc 的缩放已含在内）。
5. `TextArea` 的 2 行高在真机上够不够；中文输入法组字过程中的回车会不会被当成发送。

## 6. 收尾

门禁 `gate.py --full --kb-build` → **17/17 passed in 139.7s**（`out/_gate_v230.log`）；打包 → `out/_dist/MAI-0.23.0/` **191 files / 19,487,681 B**，
`MAI-0.23.0-mod.zip` 8,740,207 B sha256 `D58E2F8C…`，`MAI-0.23.0.zip` 8,762,789 B sha256 `89109D08…`；
装机 [ok] → `saves\mods\MlogAuxiliary`（备份 `saves\mod-backups\MlogAuxiliary-20261103-145135`），装机时游戏在跑 ⇒ 需重启生效；本地提交见 `git log --oneline --grep=v0.23.0`（11 files / +1130 −16）；
公开仓 push / tag / Release 未做，等用户批准。
