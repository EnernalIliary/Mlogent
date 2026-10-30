# 56 · v0.8.1：F4 并入 F3 的单格选择

日期 2026-10-30 · 上一版 v0.8.0（a5f7b69）

## 1. 动机

v0.7.0 起有两把键：F3 = 框选（拉矩形出区域快照），F4 = 开 AI 面板。真机上这两件事是同一件事的两个粒度——
「选中一台处理器」就是 1×1 的框选。玩家 m12209 的说法是「f4并入f3的单格选择」，即单格选择应该直接进 AI 面板。

## 2. 怎么合

- 新增 `processorAt(x, y)`：`buildAt(x, y)` 拿到方块，`isProcessor()` 判是不是处理器（`executor` / `code` 鸭子类型，
  与 F2 清单、F7 候选同一套判据；`instanceof LogicBlock` 在 v160.7 恒假）。
- `selFinish()` 的 1×1 分支：先 `processorAt(r.x1, r.y1)`，是处理器就 `showAiPanel(one)`，不是就提示
  「这一格没有处理器：单格按住 F3 选中处理器 = 开 AI 面板；拖出矩形 = 区域快照」。
  旧的「没有拖动：按住 F3 从一个角拖到另一个角」文案删掉——它假设用户想拖，而现在单点是有意义的。
- 矩形拖拽路径一字未动：仍走 `dumpRegion(r.x1, r.y1, r.x2, r.y2)`（v0.6.0 的区域面板）。
- **F4 键保留**（`KEY_PANEL = ["f4"]` → `toggleAiPanel()`）：老习惯还能用，只是不再需要记。
- 控制台新增 `api.maiPick(x, y)`：能选中处理器返回 `"x,y"`，否则空串（无头测试的钩子）。

## 3. 测试（真 v160.7 引擎）

`tests/mlogauxiliary/run_ui_smoke.py` 的 `select_probe()` 里加两行 JS：

- `MAIPICK:` = `maiPick(bx, by)`（bx,by 是造出来的处理器格）→ 断言等于 `"%d,%d" % (bx,by)`；
- `MAIPICKEMPTY:` = `maiPick(bx + 1, by + 1)`（相邻的容器格）→ 断言空串。

四条源码红线：`function processorAt(`、`showAiPanel(one);`、`var one = processorAt(r.x1, r.y1);`、
`api.maiPick = function`；另加一条反红线：`"没有拖动"` 不得出现在 main.js 里。

实测 `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py`：`MAIDIAG:版本：0.8.1（游戏构建 160）`，
v0.8.0 的 `job queue` / `job gate` 两行仍在，EXIT=0。

## 4. 改了哪些文件

| 文件 | 改动 |
| --- | --- |
| `MlogAuxiliary/scripts/main.js` | 100,803 → 101,686 字符：`processorAt()`、`selFinish()` 1×1 分支、`api.maiPick`、`MOD_VERSION` 0.8.1 |
| `MlogAuxiliary/mod.hjson` | version 0.8.1 |
| `tests/mlogauxiliary/run_ui_smoke.py` | 42,318 → 51,356 字符：`MAIPICK` / `MAIPICKEMPTY` 两行 + 四条源码红线 + 一条反红线 |
| `MlogAuxiliary/README.md` | 标题版本 + v0.8.1 整节 |
| `docs/断言表.md` | 新增 **L2-43** |
| `docs/验证记录.md` | 2026-10-30 v0.8.1 节 |
| `docs/Mlog辅助-规划.md` | §9 实施状态表新增一行 |
| `tools/README.md` | 「v0.8.1 起 F4 并入 F3」两行 |

## 5. 诚实缺口

- 无头引擎没有 `Vars.ui`，所以「面板真的弹出来」仍要真机验收；测试只钉到「选中了就调 `showAiPanel`」和
  「没处理器就不调」。
- 空格子单点只给 `showInfoFade` 提示，不给区域快照——这是有意的（避免误点产生一堆快照文件），
  但如果玩家希望「单格也给区域」，改一行即可。
- 面板开出来后焦点在世界还是面板上仍取决于原版 Dialog 行为，没有额外测。
