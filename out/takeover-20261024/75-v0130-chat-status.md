# §75 v0.13.0 作业启用/完成播报到聊天框

用户 2026-10-31 20:14 的需求（原话）：

> 在启用和完成的时候把状态发送到聊天框
> 格式是：
> `<MAI（逻辑徽标）><工作状态（如Generating）>（坐标）:(其它信息)`

## §75.1 为什么这件事不是「一行 print」

先要搞清三件事，否则写出来的是「看起来在聊天框里、其实玩家看不到」的东西：

1. **图标怎么进聊天框**。聊天框画字用的是 `Fonts.def`（`Mindustry-Source/core/src/mindustry/ui/fragments/ChatFragment.java:48`
   `font = Fonts.def;`）。`Fonts.def` 只有 ASCII 的字形（`Mindustry-Source/core/src/mindustry/ui/Fonts.java:97`
   `for(char c = 0; c < 127; c++)` 那一段是给逻辑字体的），逻辑图标是 `Fonts.registerIcon()` 塞进 `Fonts.def` /
   `Fonts.outline` 的额外 glyph（`Fonts.java:162-163`）。要把图标写进字符串，只能走 `UI.formatIcons()`：
   `Mindustry-Source/core/src/mindustry/core/UI.java:746` 按 `:` 切 token，`Iconc.codes.containsKey(token)` 命中就换成
   图标字符。原版发送聊天时自己也是这么干的（`ChatFragment.java:230` `message = UI.formatIcons(message);`）。
   ⇒ 语法是 `:logic:`，**不是** `[logic]`（那是 Label 的标签语法，聊天框不认）。

2. **单机根本没有聊天框**。`ChatFragment` 的可见性是
   `net.active() && ui.hudfrag.shown`（`ChatFragment.java:50-60`），并且 `!net.active()` 时每帧
   `clearMessages()`。所以播报不能只往聊天框写，必须按 `net.active()` 选通道：联机会话进聊天框，
   单机 / 无头退回原来的 `hint()` 淡出提示。否则单机玩家投递作业后什么也看不到。

3. **播报不会刷别人的屏**。`ChatFragment.addMessage(String)`（`ChatFragment.java:311-319`）只是
   `messages.insert(0, message)`，不发包、不广播。这是本地日志，联机里只有自己看得到。

## §75.2 改动清单（只动模组）

| 位置 | 改动 |
|---|---|
| `MlogAuxiliary/scripts/main.js` | `MOD_VERSION` → `0.13.0`；`netActive()`；`CHAT_DONE` / `chatIcon()` / `chatLine()` / `chatSay()` / `chatTrim()` / `chatXY()` / `jobChatStart()` / `jobChatDone()`；四处播报点；`api.maiChatProbe` |
| `MlogAuxiliary/mod.hjson` | version 0.13.0 + description 末尾追加一节 |
| `tests/mlogauxiliary/run_ui_smoke.py` | `MAICHAT` 探针 + 两条格式断言 + 九条源码红线 |
| `docs/断言表.md` | L2-62 + 计数句改 121 条（L1 31 / L2 62 / L3 6 / L4 4 / S 18） |
| `docs/Mlog辅助-规划.md` | §9 新增 v0.13.0 行 |
| `MlogAuxiliary/README.md` | 新增「## v0.13.0：作业启用和完成时，状态直接进聊天框」 |

格式由 `chatLine(status, x, y, info)` 一处拼：

```
MAI<逻辑徽标> <状态> (x,y): <其它信息>
```

信息为空时不留冒号（`chatLine` 里判断 `info` 非空才拼 `": " + info`）。状态词与信息：

| 状态 | 触发点 | 信息 |
|---|---|---|
| `Generating` | 单作业投递成功（`startJob`）/ 批量每投出一台（`startJobBatch`） | 描述截 24 字 + `（job <id>）` |
| `Done` | 轮询到终态 `done`（`jobTick` / `jobBoxTick`） | `模板 · N 条语句 · M 字节 · 0 ERR`（有 ERR 时 `ERR n`） |
| `Rejected` | 终态 `rejected` | `静态检查有 ERR（n 条）` |
| `Cancelled` | 终态 `cancelled` | `已取消` |
| `Failed` | 其余失败终态 | explanation 截 60 字 |

终态按作业 id 去重（`CHAT_DONE[id]`）：单作业面板轮询与批量框轮询是两条路径，同一个作业两边都看到也只播一次。

## §75.3 验证

- `node --check MlogAuxiliary/scripts/main.js` → 0。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，新探针一行：

```
MAICHAT:ok icon=yes start=MAI<glyph> Generating (12,34): 给核心补铜（job 3f2a1b9c） cancel=MAI<glyph> Cancelled (1,2)
```

  `icon=yes` 说明无头引擎里 `UI.formatIcons(":logic:")` 也能换出真 glyph（`\ue80e`），不是原样留下 `:logic:`。
  `cancel=` 那半条证明「信息为空不留冒号」。
- 断言：`MAICHAT:ok` + ` Generating (12,34): 给核心补铜` + ` Cancelled (1,2)`。
- 红线九条：`function chatLine(` / `function chatSay(` / `ui.chatfrag.addMessage(s)` /
  `Packages.mindustry.core.UI.formatIcons(":logic:")` / `jobChatStart(b, String(res.id), desc)` /
  `jobChatStart(t.b, jid, desc)` / `jobChatDone(jobBox.jobs[want])` /
  `if(isJobTerminal(job.state)){ jobChatDone(job); aiJob = null; }` / `api.maiChatProbe = function`。
- `python gate.py --full --kb-build` → 16/16（改动文档前 92.2 s 一轮、收尾再一轮）。

## §75.4 没做 / 边界

- **真联机未实测**：无头引擎里 `Vars.net` 是 null（`MAINET:net=false`），所以 `netActive()` 为假、走的是
  `hint()` 回退分支。聊天框那条分支只有代码审 + 格式单测，需要玩家开一局联机才能看到真效果。
- 播报不广播：`addMessage` 只写本地列表，队友看不到（有意，避免刷屏）。
- 聊天记录条数上限、颜色都没碰；`chatIcon()` 拿不到 glyph 时留空串，不会把 `:logic:` 原样吐出去。
