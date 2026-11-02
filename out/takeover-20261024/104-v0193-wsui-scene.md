# v0.19.3：工作区窗口按 scene 单位算尺寸（像素 → scene 换算）

- 版本：0.19.3（`main.js` 的 `MOD_VERSION` / `mod.hjson` 的 `version` / `tools/logicd.py:87` 的 `SIDECAR_VERSION` 三处一致）
- 驱动：用户 m01237「工作区的按钮宽度太长导致标题被拉到右边遮挡了。修改，然后push realesse」+ 两张真机截图
  （对话框宽度盖过整个游戏窗口、右边详情栏只剩一条缝、按钮看着极长、搜索框与「排序」按钮叠字）。

## 一、取证

真机截图（用户 m01237 附的两张）四条：

1. 对话框左右两栏总面积明显宽于游戏窗口 —— 右边详情栏被挤出屏幕，只留一条边。
2. 底栏动作按钮（「恢复选框」「继续改进」「存成蓝图」…）每个都被拉长，右侧按钮直接出屏。
3. 标题 `Mlog辅助 · 工作区快照 v0.19.1` 被右侧内容压住/挤到边上。
4. 左栏搜索框与「排序」按钮、筛选 chips 与计数行互相叠字（0.19.2 用固定宽度+省略号只缓解了文字长度，没解决叠加）。

## 二、根因（单位错了，不是宽度算多了）

**`Core.graphics.getWidth()/getHeight()` 的单位是像素，而 Arc 的 `Table` / `Cell.width()` / `ScrollPane` 用的是 scene 单位**，
两者差一个 UI 缩放系数 `Scl.scl()`。0.19.1 把像素直接喂给 `wsDialogPlan()`，于是：

- 玩家界面缩放 1.5 ⇒ 对话框宽 1310 **scene 单位** ≈ 1965 像素，屏幕上只放得下 1310 像素 ⇒ 宽出一倍多；
- 对话框内部的栏宽也是按这个超大的数排 ⇒ 按钮被拉长、左栏吃掉详情栏、标题被挤出原位。

官方源码一律除一次（不是猜的）：

- `Mindustry-Source\core\src\mindustry\ui\dialogs\JoinDialog.java:647`：
  `Math.min(Core.graphics.getWidth() / Scl.scl() * 0.9f, 550f)`；
- 同类：`ModsDialog.java:114` / `:117`、`MapLocalesDialog.java:210` / `:516`、`MapListDialog.java:116`；
- `Arc-Source\arc-core\src\arc\scene\ui\layout\Table.java:745` / `:752` —— `margin*` 内部自己就 `Scl.scl(...)`，
  说明表格的数值单位是 scene；
- `Arc-Source\arc-core\src\arc\scene\ui\layout\Scl.java:22-37` —— 桌面端 `scl()` = UI 缩放设置 `product`；
- 仓内已有先例：`main.js:3889` 的 `worldToScreen()` 就是 `var gw = Core.graphics.getWidth(), sw = Core.scene.getWidth(); ... k = gw / sw;`。

## 三、改法（`MlogAuxiliary/scripts/main.js`）

| 位置 | 改动 |
| --- | --- |
| 新增 `wsSclFactor()` | 优先 `Core.graphics.getWidth() / Core.scene.getWidth()`；取不到退回 `Packages.arc.scene.ui.layout.Scl.scl()`；再退回 1。 |
| 新增 `wsSceneUnits(px, scl)` | `Math.round(px / max(1, scl))`，非正数回 0。 |
| 新增 `wsScreenSize()` | 先取 `Core.scene.getWidth()/getHeight()`（本来就是 scene 单位）；取不到用像素 ÷ `wsSclFactor()`；最后兜底 1280×720。返回 `{w, h, scl}`。 |
| `wsDialogPlan(sw, sh)` | 入参语义改成 **scene 单位**：`availW = clamp(w-56, 520, 1500)`、`availH = clamp(h-190, 320, 820)`、`listW = clamp(availW*0.3, 340, 430)`、`detailW = max(300, availW-listW-14)`、`onlyW = min(availW,560)`、`wide = w >= 900`。 |
| `openWorkspaceDialog()` | `var scr = wsScreenSize(); var plan = wsDialogPlan(scr.w, scr.h);`（不再直接读像素）。 |
| `wsRefreshList()` / `wsRefreshDetail()` | 只保留守卫 + 调 `wsRefreshListBody()` / `wsRefreshDetailBody()`，`wsUI.busyList` / `wsUI.busyDetail` 防重入；异常 `log("ws list refresh failed: ", e)`。 |
| 搜索框 | `setTextFieldListener` 里先置 `wsUI.focusSearch = true` 再刷新；重建后 `Core.scene.setKeyboardFocus(tf)` + `tf.setCursorPosition(len)`。 |
| `api.maiWorkspace3Probe` | 断言改到 scene 单位：`wsSceneUnits(2049,1.5) === 1366`、`wsSceneUnits(0,1.5) === 0`、`wsSclFactor() > 0`、换算等价性、`wsDialogPlan(880,600).wide === false`、`wsDialogPlan(900,600).wide === true`；计数串尾加 `scl=`。 |

叠字那条的机理（截图 3/4）：卡片/按钮自己的回调里再次 `host.clear()` 重建，外层那次刷新还没走完 ⇒
两次 `clear()/add()` 交错，同一个 `Table` 里留下两代控件（并排画，不是互相覆盖）。0.19.2 只改字宽，所以叠字还在。

## 四、验证

- `node --check MlogAuxiliary/scripts/main.js` → EXIT=0。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，
  `MAIWS3:ok rows=3 filt=2 sort=3 detail=2 ghosts=1 release=1 mismatch=1 locate=1 plan=393x903 scl=1`。
- smoke 新增 v0.19.3 红线：`function wsSclFactor(` / `function wsScreenSize(` / `function wsSceneUnits(` /
  `function wsDialogPlan(` / `wsUI.busyList`，任一删除即 FAIL。
- `python gate.py --full --kb-build` → **17/17 passed in 235.6s**（日志 `out/_gate_v193.log`，`kb` 重建 168 个源文件）。
- 打包：`python tools/package.py` → `out/_dist/MAI-0.19.3/`（178 files / 18,796,496 B）、
  `MAI-0.19.3-mod.zip` 8,459,115 B / 169 files / sha256 `B98CA084CE1AB672288D3A7B2676046A34B7AC32DF959C14B0576DD9DCAF94D4`、
  `MAI-0.19.3.zip` 8,480,853 B / sha256 `ADBDD2EC95FB45BFD03166F44437D4D43F2972C7EE817EBDC5F42CBBE513B086`（日志 `out/_pack193.log`）。
- 装机：`install.ps1 -Target "...\Mindustry\saves\mods"` → `[ok] MAI 0.19.3 installed`，旧副本备份到
  `saves\mod-backups\MlogAuxiliary-20261102-135545`。

## 五、留给真机验

1. 重开「工作区快照」对话框：窗口应**明显小于游戏窗口**（左右各留 ~28 scene 单位），两栏都在屏幕内。
2. 底栏按钮不再拉长、不再出屏；标题完整可见不被压。
3. 左栏搜索框 / 排序按钮 / 筛选 chips **不再叠字**；点卡片后详情栏正常换内容。
4. 搜索框能连着打多个字（焦点不丢）。
5. 若玩家把界面缩放改大/改小，窗口应跟着一起缩放而不是溢出。

## 六、发布

- 本地提交 `9cdc280`（9 files / +210 −22）。
- 公开仓 `EnernalIliary/MAI-MlogAuxiIliary`：克隆在 `out/_publish/mai-clone`，`out/_v193_pub.py` 拷 232 个文件进克隆
  （`tests/run_tests.py` 48/48；logicd 与 ui smoke 在克隆里因没有 v160 jar 而 SKIP，本仓 `gate.py --full` 已 17/17），
  提交 `5fb3eb3` "v0.19.3: size the workspace dialog in scene units, not pixels"，tag `v0.19.3` 已 push。
- Release：`out/_v193_release.py`（直连 opener，绕开本机 10808 代理）→
  https://github.com/EnernalIliary/MAI-MlogAuxiIliary/releases/tag/v0.19.3 ，两个资产都 201 上传，
  `releases/latest` 复核 = v0.19.3 + 两个资产。
