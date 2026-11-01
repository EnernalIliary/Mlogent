# v0.18.1 —— 设置页观感 / 倍率滑条 / 改键不生效 / 查看行为（2026-11-01）

本轮把用户连续三轮的口头反馈做完，重点其实是两个「看起来是 UI 玄学、根因在引擎语义」的 bug：
**倍率拖了不动**（`Settings.getFloat` 对 `Double` 抛类型异常）和**改键不生效**
（原版改键把绑定写成 `min`/`max` 两段，`key` 为 `null`）。

## 需求原文

- m10289：「设置页面的info保持在每个选框最右侧，给一些提示换行。设置主题色改为[#8abcd1]强调色为[highlight]」
- m10327：「首次配置向导的按钮放在最后的运行环境。最近提示改成可复制的文本日志。隐藏密钥按钮使用游戏原有的:eye:图标放在密钥栏最右侧。」
- m10374：「框选控件缩放做成滑条，参考原版设置。而且好像改不了。 模型生成界面的开启自动写入也不生效。 查看详情的UI窗口做的不好，
  现在点击在生成完成后查看就会打开逻辑编辑界面预览AI写的逻辑。在未生成完成时点击查看则会在聊天框打印思考过程，
  这个只能打印到本地聊天框，不发送到服务器。彻底移除旧版的查看详情。 原来的入口改到蓝图库的底层按钮，也就是"MAI对话"更名为MAI控制面板。」
- m10546：「设置控制更改的热键不生效。」

## 一、主题色 / 强调色 / 行尾图标（m10289）

- `themeColor()` = `Color.valueOf("8abcd1")`；`emphColor()` = `Pal.accent` 向白 `lerp 0.3`。
  依据 `Mindustry-Source/core/src/mindustry/ui/UI.java:105/107`：`[highlight]` 就是 accent 与白插值 0.3，
  所以「强调色用 `[highlight]`」等价于自己算一遍，颜色与游戏内文一致。
- 段落标题、两行主标题、`infoIcon()` 全走 `themeColor()`；长解释 `softWrap(text, 34)` 换行，
  图标 `expandX()` + `right()` 贴行右缘（`INFO_W = 26` 给图标留位，值区宽度同步收窄）。

## 二、向导按钮搬家 / 提示日志 / 眼睛图标（m10327）

- 「首次配置向导」按钮由「大模型」段首移到最后的「运行环境」段末（段顺序不变）。
- 「最近提示」由「一行按钮」改成文本日志：`HINT_LOG`（`HINT_LOG_MAX = 12`）+ `hintLogPush(at, text)` +
  `hintClock(at)`（`SimpleDateFormat("HH:mm:ss")`）+ `hintLogText()`，下面一行「复制日志」「清空」。
- 密钥「显示/隐藏」：`eyeMark(hidden)` → `UI.formatIcons(":eye:")` / `":eyeOff:"`（取不到图标就退回中文），
  单图标按钮挂在密钥行末尾并 `expandX()/right()` 贴右缘，悬浮提示「显示或隐藏密钥明文」。

## 三、倍率滑条 + 「改不了」的根因（m10374①）

- 设置页「框选控件」段换成原版 `arc.scene.ui.Slider(HUD_SCALE_MIN, HUD_SCALE_MAX, HUD_SCALE_STEP, false)`，
  右侧数字用 `hudScaleLbl`；`arc` 的 `ProgressBar` **没有** `changed(Runnable)`（只有 `getValue()`/`setValue()`，
  `ProgressBar.java:207/241/246`），所以 `hudSliderTick()` 每帧轮询值变化再落地。
  无头环境（`Core.scene` 为 null，拿不到 style）建滑条会抛 ⇒ try 住后退化回原来的按钮。
- **「改不了」的真正原因**：`Arc-Source/arc-core/src/arc/Settings.java:357-359` 的
  `getFloat(name, def)` 是 `(float)get(name, def)`；JS 数字经 `Core.settings.put()` 存成 `java.lang.Double`，
  `(float)Object` 会先当 `Float` 强转再拆箱 ⇒ `ClassCastException`，`hudScale()` 的 catch 每次退回 1.0。
  修法：`hudScaleRaw()` 用 `Core.settings.get(key, null)` 拿 `Object` 再 `parseFloat(String(o))`（老值可能是 `Double`，
  不能直接 `getString`/`getFloat`），写回存 `String(n)`。

## 四、查看 / 详情行为（m10374③④）

- 框角「查看」不再打开旧「作业详情」窗：`jobWidgetView()` → `jobViewPick()`（光标下那台优先，否则框里第一台）。
  - 作业 `done` → `previewLogic(job)`：`Vars.ui.logic.show(code, null, false, fn)`，**只预览不写入**。
  - 未完成 → `jobThinkToChat(job)`：把进度与 `jobReasoningLines()` 逐行用 `chatLocalSay()` 送进
    `Vars.ui.chatfrag.addMessage`（只进本机聊天列表，不走 `Call.sendChatMessage`，服务器收不到）。
- 蓝图库底栏入口「MAI 对话」更名「MAI 控制面板」（宽 130 → 150），注释与 ui smoke 红线同步。

## 五、改键不生效（m10546）

- 引擎事实：`KeybindDialog.rebind()`（`Mindustry-Source/core/src/mindustry/ui/dialogs/KeybindDialog.java:128-150`）
  对默认值是 `Axis` 的绑定走两步：先按 min、再按 max，最后 `bind.value = new Axis(minKey, newKey)`；
  `KeyBind.load()` 读回来的也是 `min`/`max`，**`key` 恒为 null**（`Axis(KeyCode min, KeyCode max)` 不设 key）。
  模组原来只读 `value.key` ⇒ 改完永远读不到 ⇒ 一直退回硬编码 f3。
- 修复：`selKeyCode()`/`selKeyDown()`/`selKeyName()` 两种形状都认（有 `key` 用 `key`，否则用 `min`），
  并在设置页显示当前绑成了什么键（「框选键」）。F2「处理器清单」也注册成 `mai-list`
  （`listKeyBind()`/`listKeyTap()`/`listKeyName()`），分类「MAI」、条目「处理器清单（MAI）」；
  `update` 里 `hotTap("f2")` 改成 `listKeyTap()`，并预热注册。F7（区域候选）仍固定。

## 六、验证

| 项 | 结果 |
| --- | --- |
| `node --check MlogAuxiliary/scripts/main.js` | 0 |
| `tests/mlogauxiliary/run_ui_smoke.py` | EXIT=0（含新探针 `MAIKEYBIND:ok axis=G / H code=G one=Y onecode=Y back=F3`） |
| 新增红线 | `selKeyAxis`、`ax.min` 判定、`listKeyTap`、`mai-list` 注册、`listKeyTap()` 调用、两行 kv（框选键/清单键） |
| `python -X utf8 gate.py --full --kb-build` | **17/17 passed in 102.2s** |
| 打包 `out\_dist\MAI-0.18.1` | 168 files / 18,702,090 B；`MAI-0.18.1-mod.zip` sha256 `0F5838B6…B76CB80`；`MAI-0.18.1.zip` sha256 `1284A23B…CBD427` |
| 包内 exe | `/health` = 200 `0.18.1` `ok=true`；`/ping {}` → 200；`/ping "[object Object]"` → 400；`/shutdown` → 200 |

## 七、踩坑（可复用）

- **`print()` 不打出来 ≠ 没执行**：`run_ui_smoke.py` 有**两处前缀白名单**——约 `:391-401` 收 `lines`、
  约 `:1783-1788` 才真正 `print`。只改前者，探针输出永远看不见（本次排查绕了半小时）。
  定位手法：把 smoke 实际执行的 js 落盘（`out/_smoke_js.txt`）再原样重放，确认那行确实在脚本里。
- `tools/mlogsim.py` 的 `Server.js(script)` 用 `" ".join(script.splitlines())` 拼一条命令、等 `undefined` 收尾；
  `Server` 构造要 `M.Server(M._default_java(), M.V160_JAR)`，无参构造会 `TypeError`。
- 临时改测试文件做实验，先 `Copy-Item` 备份，跑完还原。
- `python -X utf8 -c` 里带引号/中文/`\\u` 的串仍会炸（`SyntaxError: unterminated string literal`）⇒ 一律写 `.py` 文件。
- PowerShell 里 `python - <<'EOF'` 不是 heredoc（解析成重定向）⇒ 用 write 工具落脚本。
- 实测锚点缩进要照抄：`kv(t, "框选键", …)` 的续行是 **11 空格**，按 12 空格写 `count=0`。

## 八、待办

- 装机被阻：用户当时**游戏在跑**（`Mindustry.exe` + `logicd.exe` 占着 `saves\mods\MlogAuxiliary`），
  `install.ps1` 的 `Move-Item` 报「Access denied」。需先退出游戏再装。
- 发版（公开仓 push + tag `v0.18.1` + Release + CI）等用户确认这轮改动后做。
