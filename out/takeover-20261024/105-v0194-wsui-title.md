# 105 · v0.19.4 工作区标题左对齐与按钮宽度上限（2026-11-02）

驱动：用户 m01690「你把工作区的标题居中了，导致工作区按钮宽度被拉伸」。

## 一、取证

- 装机目录 `mod.hjson` = 0.19.3；Mindustry 进程 pid 51268 起于 2026-11-02 17:12:14，晚于 13:55 的安装 ⇒ 用户看到的是 0.19.3，不是旧版残留。
- 模型读不了图（`read_image` 报 `does not declare image input`），截图上不了眼；桌面截图存 `out/_shot_ws.png`，探针 `out/_shot_probe.py`（EnumWindows 找窗口 + PIL 13.0.0），当时窗口已最小化（RECT -21333…）⇒ 放弃图像分析。
- 可靠的文字取证通道：`log()`（`MlogAuxiliary/scripts/main.js:55`，`print("[mai] " + msg)`）实时写进 `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\last_log.txt`，里面有 `[mai] v0.19.3 ready, 86/86 console function(s)`。本版把排版数字也写进这个文件（见改法第 4 条）。
- Arc 源码事实：`Dialog.java:57-59` 暴露 `public final Table cont, buttons; public final Label title; public final Table titleTable;`；构造 `:77-79` `titleTable.add(this.title).expandX().fillX().minWidth(0); add(titleTable).growX().row();`；`:209-211` `add(cont = new Table()).expand().fill(); row(); add(buttons = new Table()).fillX();`。`Label.java:34` `protected int labelAlign = Align.left;`，`setAlignment(int)` 在 `Label.java:284`。Table 没有 `setAlignment`，只有 `left()/right()/align(int)`。
- 居中先例：`main.js:693 function titleLine(t, text, scale, color)` 会 `cell.center()` + `alignText(lbl, Align.center)`，但只用在 `:983-985` 与 `:1567`（MAI 面板 / 欢迎页），工作区窗不在其中 —— 工作区窗的标题是 Dialog 自带 title。

## 二、根因

0.19.3 把单位修对了，但窗口仍按「宽 -56 / 高 -190」几乎顶满屏幕，于是：

1. 标题所在单元格是 `expandX().fillX()`，标题一旦被居中（或标题行里有别的居中元素），就会撑满整行、把它所在的列顶宽；
2. 同一列里的筛选 chips 用 `floor((iw-14)/4)`（四等分），详情页主按钮用 `floor((iw-8)/2)`（半栏）—— 面板越宽按钮越长，看起来就是「标题把按钮拉宽了」。

即：不是某个按钮写死了宽度，而是**宽度全部按面板宽度等分、且面板没有上限**。

## 三、改法（`MlogAuxiliary/scripts/main.js`）

| 位置 | 改动 |
| --- | --- |
| `wsDialogPlan(sw, sh)`（入参 scene 单位） | `availW = clamp(w-56, 520, 1080)`（**新上限 1080**）、`availH = clamp(h-190, 320, 760)`、`listW = clamp(availW*0.33, 320, 400)`、`detailW = max(300, availW-listW-14)`、`onlyW = min(availW,560)`、`wide = w >= 900` |
| 新增 `wsChipWidth(iw)` | `clamp(floor((iw-14)/4), 56, 96)` —— 筛选 chips 不再随面板无限变宽 |
| 新增 `wsPrimaryWidth(iw)` | `clamp(floor((iw-8)/2), 100, 168)` —— 详情页「恢复选框」「继续改进」不再半栏宽 |
| `wsRefreshListBody()` | `var cw = wsChipWidth(iw);` |
| `wsRefreshDetailBody()` | `var bw = wsPrimaryWidth(iw);` 并用于两个主按钮 |
| `openWorkspaceDialog()` | `d.title.setAlignment(Packages.arc.util.Align.left)` + `d.titleTable.left()` + `d.buttons.left()`（各自 try/catch，无头环境不建窗也能过） |
| `openWorkspaceDialog()` | 打开时 `log("ws dialog: screen=" + scr.w + "x" + scr.h + " scl=" + scr.scl + " plan=" + plan.availW + "x" + plan.availH + " list=" + plan.listW + " detail=" + plan.detailW + " wide=" + wide)` ⇒ 真机数字进 `last_log.txt` |
| `api.maiWorkspace3Probe` | `plan.availW === 1080`、`plan-cap`（>1080 报错）、`chip-cap`/`chip-min`（96 / 56）、`primary-cap`/`primary-min`（168 / 100）、`plan-fallback`（`wsDialogPlan(0,0).availW === 1080`）；counts 串加 `cap=96/168` |
| 版本三处 | `main.js:31` `MOD_VERSION = "0.19.4"`、`MlogAuxiliary/mod.hjson:5` `version: "0.19.4"`、`tools/logicd.py` `SIDECAR_VERSION = '0.19.4'` |

## 四、验证

- `node --check MlogAuxiliary/scripts/main.js` → SYNTAX OK。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，关键行：
  `MAIWS3:ok rows=3 filt=2 sort=3 detail=2 ghosts=1 release=1 mismatch=1 locate=1 plan=356x710 cap=96/168 scl=1`。
- smoke 新增 v0.19.4 红线（掉了就报错）：`d.title.setAlignment(Packages.arc.util.Align.left)`、`function wsChipWidth(`、`function wsPrimaryWidth(`、`d.buttons.left()`。
- 文档：`CHANGELOG.md` 新增 `## 0.19.4`；`docs/Mlog辅助-规划.md` 版本表插 v0.19.4 行；`docs/断言表.md` 追加 L2-98（标题/按钮靠左 + 宽度上限）、L2-99（对话框宽度上限 1080），口径行改为 **158 条**（L1 31 / L2 99 / L3 6 / L4 4 / S 18）。

## 五、留给真机验

- 装 0.19.4 后打开一次「工作区快照」，`saves/last_log.txt` 里应出现一行 `[mai] ws dialog: screen=…x… scl=… plan=1080x… list=… detail=… wide=true` —— 这一行就是真机排版基准，出问题先看它。
- 重点看三处：① 标题是否还在最左边；② 顶部四个筛选按钮是否还是被摊满一行（上限 96，正常应明显短于面板四分之一）；③ 详情页「恢复选框」「继续改进」是否还是半栏宽（上限 168）。
- 我读不了截图（模型无图像输入），若还有拉伸请描述「哪一排按钮、在左栏还是右栏、大概占面板几分之几」，或直接把 `last_log.txt` 里那行 `[mai] ws dialog:` 发我。

## 六、门禁 / 打包 / 装机 / 发布（实测数字）

- `python gate.py --full --kb-build` → **17/17 passed in 196.4s**（日志 `out/_gate_v194.log`；kb 重建，覆盖 168 个源文件）。
- `python tools/package.py` → `out/_dist/MAI-0.19.4/` **178 files / 18,799,096 B**；
  `MAI-0.19.4-mod.zip` **8,458,878 B** / sha256 `65C2C38EFF95A9E55BE6D13B95DBB8E12630B0B99B554C16377C575C73AFF181`；
  `MAI-0.19.4.zip` **8,480,617 B** / sha256 `6020A37A0352855084F765DC8EA7D6A87A03E28A0B2300E35151C032603D99E5`（日志 `out/_pack194.log`）。
- 装机：`Stop-Process logicd` → `out/_dist/MAI-0.19.4/install.ps1 -Target "E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods"` → `[ok] MAI 0.19.4 installed`，旧副本备份 `saves\mod-backups\MlogAuxiliary-20261102-174202`；装机目录 `mod.hjson` 实测 `version: "0.19.4"`。
- 本地提交 `817b94d`（9 files / +133 −13）。
- 公开仓（`EnernalIliary/MAI-MlogAuxiIliary`，克隆 `out/_publish/mai-clone`）：提交 `150d27d` + tag `v0.19.4` 已 push（远端 `150d27d60eee2dba0f56c6210a980505d6d9c2c6`）。
  发布前在克隆里跑了测试：`tests/run_tests.py` 48/48；`tests/packaging/run_pack_tests.py` 13 checks 0 problem；logicd / ui smoke 因克隆里没有 v160 jar 而 SKIP（预期）。
- Release https://github.com/EnernalIliary/MAI-MlogAuxiIliary/releases/tag/v0.19.4 ，两个资产上传均 201，`releases/latest` 已复核 = v0.19.4。

