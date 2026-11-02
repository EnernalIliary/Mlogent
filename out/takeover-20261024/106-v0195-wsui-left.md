# 106 · v0.19.5：工作区左栏不再被拉满一整行（+ 真机排版自检）

日期：2026-11-02　驱动：用户 m01884「MAI的左栏。仍然没变」+ 选项答「按钮/输入框还是被拉得很宽，占满一整行」

## 一、取证（真机，不靠猜）

- `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\last_log.txt` 里 18:31:27 那一行：
  `[mai] ws dialog: screen=1707x1044 scl=1 plan=1080x760 list=356 detail=710 wide=true` ⇒ 用户看到的就是 v0.19.4，
  对话框宽度确实已经封到 1080（0.19.3 时是 1500），标题也已左对齐。**改宽度这条路已经走到头了**。
- 那「占满一整行」是怎么来的：左栏 356 → `iw = 334`，而 v0.19.2 起栏里两行控件都是按栏宽算的 ——
  搜索框 `Math.max(90, iw - 158 - 6) = 170`、排序按钮写死 `158`、四个 chips `wsChipWidth(334) = 80`。
  170+6+158 = 334、80×4+pad = 332 —— **两行各自刚好把整栏填满**，视觉上就是「按钮/输入框被拉宽、占满一行」。
- 模型读不了图（`read_image` 报 `does not declare image input`），所以这一版顺手加了个几何自检，
  下次再有排版问题直接读数字。

## 二、根因

不是几何 bug，是**排布策略**：把「栏宽」当成控件的目标宽度（`iw - 固定宽` 的填空式布局），
于是栏越宽控件越宽，而控件本身的文字根本没变长。正确的做法是让控件按文字宽度走，栏宽只当上限。

## 三、改法（`MlogAuxiliary/scripts/main.js`）

| 位置 | 改前 | 改后 |
| --- | --- | --- |
| `wsDialogPlan()` | `listW = clamp(availW*0.33, 320, 400)` → 356 | `listW = clamp(availW*0.30, 300, 360)` → 324 |
| `wsRefreshListBody()` 搜索框 | `.width(Math.max(90, iw - sortW - 6))` → 170 | `.width(150)` 固定 |
| 排序按钮 | `.width(sortW=158)` | 去掉 `.width()`，走自然宽度 + `ellipsis(true)` |
| 筛选 chips | `.width(wsChipWidth(iw))` 四等分 | `.maxWidth(wsChipWidth(iw))` —— 按文字宽度，超上限才截断 |
| 卡片 / 计数行 | `growX()` / `.width(iw)` | 不变（列表行本来就该铺满） |
| 新增 `wsGeomDump()` | — | 开窗后第一帧 dump 真实宽度到 `last_log.txt` |

几何自检的实现要点：Arc 的 `Element.getWidth()` 在 `validate()`（布局）之前是 0，**不能在 `wsRefreshListBody()` 里读**。
所以 `openWorkspaceDialog()` 置 `wsUI.needGeom = true`，`Events.run(Trigger.draw)` 里（`drawWorkspaceGhosts` 之后）
调 `wsGeomDump()`，第一帧之后把 `dialog(...) pane(...) host(...) #0 ... | #1 ...` 写一行日志，dump 完立刻清标志，
`d.hidden` 也清。行里带 `Class w= x= h=` 和文字前缀，能直接看出哪个控件有多宽。

## 四、验证

- `node --check MlogAuxiliary/scripts/main.js` → EXIT=0。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，关键行：
  `MAIWS3:ok rows=3 filt=2 sort=3 detail=2 ghosts=1 release=1 mismatch=1 locate=1 plan=324x742 cap=96/168 scl=1`。
- 探针新增断言：`plan.listW === 324`（`plan-listw`）、`plan-min` 改成 300–360、`plan-detail-min` ≥300。
- smoke 新增 v0.19.5 红线：`function wsGeomDump(`、`wsUI.needGeom = true`、`bar.add(tf).width(150)`、`maxWidth(cw)`。

## 五、留给真机验

- 重开「工作区快照」面板：左栏应变窄（324），搜索框 150、排序按钮只占「排序：更新」几个字的宽度，
  四个筛选按钮按文字宽度排列、右侧留白；卡片仍铺满整栏。
- 同一次打开会在 `saves/last_log.txt` 写一行 `[mai] ws geom: …`，把那一行发回来就能对着数字判断。

## 六、门禁 / 打包 / 装机 / 发布

- `python gate.py --full --kb-build` → **17/17 passed in 108.1s**（`out/_gate_v195.log`，kb 覆盖 168 源文件）。
- `python tools/package.py` → `out/_dist/MAI-0.19.5/` **178 files / 18,803,149 B**；
  `MAI-0.19.5-mod.zip` **8,461,519 B** sha256 `156EAA0BD079D4B04455364CF97DA36F6A50EDD906CABABEAD3B501E174FEF52`；
  `MAI-0.19.5.zip` **8,483,258 B** sha256 `2BEAC03A2D62974384A2960F39A5157D7E6DA3595F8833A48850A8F143191E0B`。
- 装机：`Get-Process logicd | Stop-Process -Force` → `out/_dist/MAI-0.19.5/install.ps1 -Target "E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods"`
  → `[ok] MAI 0.19.5 installed`，旧副本备份 `saves\mod-backups\MlogAuxiliary-20261102-184248`；
  实测装机目录 `mod.hjson` 为 `version: "0.19.5"`，`main.js` 里 `wsGeomDump` / `bar.add(tf).width(150)` / `maxWidth(cw)` 各 1 处。
- 本地提交 **0376b2d**（9 files / +182 −11；第一次误把 `out/takeover-20261024` 下大量未跟踪文件一并 `git add -A` 进去，
  已 `git reset --mixed` 后只暂存目标文件重提）。
- 公开仓（`out/_publish/mai-clone`）：`out/_v195_pub.py` 拷 232 文件 → 克隆里 `tests/run_tests.py` 48/48、
  `tests/packaging/run_pack_tests.py` 13 checks 0 problem（logicd / ui smoke 因克隆里没有 v160 jar 而 SKIP）→
  提交 **1782d37** "v0.19.5: size the left column to its text instead of filling the row" + tag `v0.19.5`，
  `git push origin main` / `push origin refs/tags/v0.19.5` 均 exit 0（PS 把 git stderr 报成 NativeCommandError 属噪音）。
- Release：`out/_v195_release.py` → POST 201 + 两个资产 201 → `releases/latest` = v0.19.5；
  https://github.com/EnernalIliary/MAI-MlogAuxiIliary/releases/tag/v0.19.5
- 待用户真机复核：重开面板看左栏是否不再铺满；同一次打开会在 `saves/last_log.txt` 留一行 `[mai] ws geom: …`。
