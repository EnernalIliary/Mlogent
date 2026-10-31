# 84 v0.14.5：框角控件的 HUD 倍率自己调

- 日期：2026-11-01
- 用户原话（m06525）：「做一个hud倍率自己调就好」

## 1. 起因

v0.14.4 把框角的「查看 / 取消」换成原版 `TextButton` 时，尺寸是我写死的 `Scl.scl(84) × Scl.scl(40)`。HUD 上的手感因人而异（分辨率、UI 缩放、个人习惯），我估的只是起点，而且真机我也验不了位置与大小。所以把倍率交出去，由玩家自己调。

## 2. 做法

- 键：`HUD_SCALE_KEY = "mlogauxiliary-hud-scale"`，存在 `Core.settings`（`Settings.getFloat` 在 arc/Settings.java:357）。
- 范围：`HUD_SCALE_MIN = 0.5`、`HUD_SCALE_MAX = 2`、`HUD_SCALE_STEP = 0.1`；`hudScaleClamp()` 保留两位小数，值非法（NaN、0、负数）回 1。
- 函数：`hudScale()` 读 + 夹、`hudScaleText()` 出文案、`hudScaleSet(v)` 写 + `jobWidgetDrop()`、`hudScaleStep(dir)` 加减档、`hudScaleRefresh()` 刷设置页那一格的文案。
- 设置页新增「框选控件」段：`缩小` / 中间格（显示 `倍率 1.0×`，点一下回 1.0×）/ `放大`，下面一行解释。段位夹在「聊天播报」与「快捷动作」之间，运行环境仍在最后。
- 缩放点：`jobWidgetBuild()` 里 `var hk = hudScale()`，按钮 `size(S.scl(84) * hk, S.scl(40) * hk)`、`padLeft(S.scl(6) * hk)`、状态条 `padBottom(S.scl(3) * hk)`，状态文字用 `Label.setFontScale(hk)`（Label.java:306）；`jobButtonsSync()` 的贴边距 `var edge = JOB_BTN_EDGE * hk2`。
- 改倍率要重建：arc 的 Cell 尺寸是建表那一刻定的，光改设置不生效。所以 `jobWidgetDrop()` 摘表、`jobWidget = null`、`jobWidgetTried = false`，下一帧 `jobButtonsSync()` 重新 `jobWidgetBuild()`。

## 3. 边界

- 只动框角那一小块，不碰游戏其它 HUD、不碰即时绘制降级路径（`MAIBADGERECT` 探针几何仍是 `box{4,4,48,48}`，作为降级回归）。
- 单机 / 联机行为一致；倍率不影响作业逻辑与 sidecar。

## 4. 验证

| 命令 | 结果 |
| --- | --- |
| `node --check MlogAuxiliary/scripts/main.js` | 0 |
| `python tests/mlogauxiliary/run_ui_smoke.py` | EXIT=0（新红线 8 条 + 设置页七段顺序断言） |
| `python tests/run_tests.py` | 46/46 |
| `python tests/logicd/run_logicd_tests.py` | logicd OK（sidecar 只改版本号） |

待真机：0.5×/1.0×/2.0× 三档在 HUD 上的观感，以及倍率改完是否立刻重排（应当下一帧生效）。
