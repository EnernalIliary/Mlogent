# v0.20.3 对话窗宽度：Arc 表格的列宽跨行共享

日期：2026-11-02　触发：用户 m03832「还是不对，你看现在的情况」（附整屏截图）

## 1. 取证

- 装机目录 `saves\mods\MlogAuxiliary\scripts\main.js` 与仓库版本 sha256 前缀一致（61c24ac9dd49545a，471449 B），
  `last_log.txt` 首行 `[mai] v0.20.2 ready, 87/87 console function(s)` ⇒ 用户跑的就是 v0.20.2，不是没装。
- `[mai] chat dialog: screen=1707x1044 scl=1 plan=980x680 list=206 detail=752 wide=true`（重复 3 次，用户点了 3 次入口）
- `[mai] chat geom: dialog(Dialog w=1768 x=-30 h=803) title(Table w=1760 x=4 h=21 …) scene=1707x1044
  listW=206 detailW=752 | listPane(ScrollPane w=206 x=3 h=680) | input(TextField w=820 x=0 h=34) | host(Table w=206 …)`
- 对照：工作区窗 `ws geom: dialog(Dialog w=1095 x=306 h=843)`，plan 1080 只多 15，正常。
- 截图现象（左栏贴屏幕左边缘 x≈-30、底栏「新对话」被右边缘裁成「新对」）与 `x=-30 / w=1768` 完全一致。

## 2. 根因

`openChatDialog()` 里两栏排成 cont 的**同一行三个 cell**：

```
row0 = [ pane(listT) 206 ][ image 2 + padLeft7 + padRight7 = 16 ][ pane(detailT) 752 ]   → 三列
row1 = [ inRow 974 ]                                                                   → 只占第 0 列
```

Arc 的 `Table` 是**列网格**，列宽跨行共享（`Table.java` computeSize 里 `columnPrefWidth[column]` 取各行该列的最大值）：

- 第 0 列 = max(206 + pad6, 974 + pad6) = 980
- 第 1 列 = 16，第 2 列 = 752 + pad6 = 758
- prefWidth = 980 + 16 + 758 = **1754**，加 Dialog 自身 pad 与背景 ≈ **1768** ⇒ 与真机 dump 精确吻合。

高度 803 = 21（title）+ 680（两栏）+ 34（输入行）+ 45（底栏）+ pad，纵向本来就没坏，只有横向被列求和顶宽。
工作区窗没有第二条全宽行，两列相加就等于预算，所以它一直是对的 —— 这也是 0.20.2 只算预算不够的原因。

## 3. 改法

`MlogAuxiliary\scripts\main.js` 的 `openChatDialog()`：

1. 两栏那一行包进一个新表 `body`（`var body = wsT(); body.left().top();`），列表 pane / 竖线 / 详情 pane 都加到 `body` 上；
2. `d.cont.add(body).width(max(200, availW - 6)).left().row();` —— cont 的这一格宽度就是预算可用宽，body 内部三列合计 206+16+752 = 974 = availW-6；
3. 输入行仍在 cont 的下一条行、同一列（宽度同样 `availW - 6`），cont 只有一列 ⇒ prefWidth 只有一个 980。
4. `catch` 退回时同时把 `CHAT_UI.listPane / detailPane` 置 null，避免 dump 拿旧对象。

`chatGeomDump()` 增加一段 dump：`cont(<w x h> cols=N pref=P budget=B dw=D)`，其中 budget = listW + gapW + detailW。

## 4. 验证

- `node --check MlogAuxiliary/scripts/main.js` exit 0。
- `python -X utf8 tests\mlogauxiliary\run_ui_smoke.py` exit 0，`MAIW3/MAICHATUI` 探针照旧：
  `MAIWS3:ok … plan=324x742 cap=96/168 scl=1`、`MAICHATUI:ok plan=980x548 list=206 detail=752 …`。
- 新增红线 7 条（v0.20.3 组）：body wrapper 存在、列表 pane 定宽且 `.left()`、body 行宽度 = availW-6、dump 里有 `cols=`/`budget=`；
  反向 2 条：`d.cont.pane(listT).width(plan.listW).height(availH);` 与 `var cellR = d.cont.pane(detailT)` 都不许再出现。
- 同时修掉一条旧红线：v0.20.0 的 `d.cont.image(Tex.whiteui).width(2)` 因为分隔线搬到 `body` 上而失效，改成 `body.image(Tex.whiteui).width(2)`。

## 5. 留给真机验

重启游戏后点任一入口开对话窗，`saves\last_log.txt` 里应出现：

```
[mai] chat geom: dialog(Dialog w≈995 x≈356 h≈803) … cont(<…> cols=1 pref=980 budget=980 dw≈995)
```

- `cols=1` ⇒ 列数正确；`dw` 与 `budget` 只差外壳 pad 与边框（≈15）。
- 若仍宽，看 `cols=` 是否 >1，或 `pref=` 是否远大于 980 —— 这两项就是下一轮的直接线索。

## 6. 版本 / 门禁 / 打包

- 三处版本 0.20.3：`main.js` 的 `MOD_VERSION`、`MlogAuxiliary/mod.hjson`、`tools/logicd.py` 的 `SIDECAR_VERSION`。

- 门禁 `python -X utf8 gate.py --full --kb-build` → **17/17 passed in 109.9s**（`out\_gate_v203.log`，kb 覆盖 169 源文件）。
- 打包 `python -X utf8 tools\package.py` → `out/_dist/MAI-0.20.3/` **191 files / 19,416,227 B**；
  `MAI-0.20.3-mod.zip` **8,711,602 B / 182 files** sha256 `423A5FAABC2FDCF5C364D08FB6A9CA05ADEA34E52F422752DFE79AE1C046FC53`；
  `MAI-0.20.3.zip` **8,734,185 B** sha256 `DE2BD620A3CB2453B93BD9EEC765DC57EBD62060F1B1EAB68D126366A31327DF`。
- 装机：`[ok] MAI 0.20.3 installed` → `saves\mods\MlogAuxiliary`，旧副本备份 `saves\mod-backups\MlogAuxiliary-20261102-214516`；
  装机目录实测 `version: "0.20.3"`。装的时候游戏在跑（Mindustry pid 44648，21:13 启动）⇒ **必须重启才生效**。
- 本地提交 **420ebf0**（9 files / +155 −11）。
- 公开仓：`out/_v203_pub.py` 拷 234 文件进 `out/_publish/mai-clone` → 克隆里 `tests/run_tests.py` 48/48、
  `tests/packaging/run_pack_tests.py` 13 checks 0 problem（logicd / ui smoke 因无 v160 jar SKIP）→ 提交 **3d21f60**
  "v0.20.3: stop the chat dialog from growing past its width budget" + tag `v0.20.3`；
  push 走代理（`git -c http.proxy=http://127.0.0.1:10808 push origin main` / `push origin refs/tags/v0.20.3`，均 rc=0）。
- Release：`out/_v203_release.py` → POST 201、两个资产均 201，`releases/latest` = v0.20.3。
  https://github.com/EnernalIliary/MAI-MlogAuxiIliary/releases/tag/v0.20.3
