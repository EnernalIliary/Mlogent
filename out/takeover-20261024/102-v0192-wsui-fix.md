# 102 v0.19.2「工作区快照」窗口排版修复

- 日期：2026-11-02
- 驱动：用户 m01050 截图 + 「很多地方字符重叠了。而且窗口宽度不够。按钮有意外换行。简单修一下，不要push。我来检查。」
- 版本：0.19.2（`MlogAuxiliary/scripts/main.js` 的 `MOD_VERSION`、`MlogAuxiliary/mod.hjson`、`tools/logicd.py` 的 `SIDECAR_VERSION` 三处一致）

## §1 症状（截图：游戏内约 1366×758，截图 1736×963）

1. 顶部一行：搜索框压住排序按钮（`搜索 名字/备...` 被 `排序：最近更\n新` 盖住），排序按钮自己折成两行。
2. 筛选 chips 被压成「地图不\n符」两行，且「● 」前缀把按钮挤爆。
3. 左侧卡片：名字与副行（`1 台 · 更新 · 最近作业 #...`）叠在一起。
4. 右侧处理器表：表头「位置/方块/代码/写入」与内容行叠字（`@451,219 logic-process` 压到 `3 行`）。
5. 作业时间线：状态字（`生成中`）压住描述。
6. 底部「导出 JSON」折成两行。

## §2 根因（Arc 源码依据）

- `Label` 默认 `wrap = false`：cell 给了固定 `width` 也不会截断文字，超宽部分照样画出去 ⇒ 压到邻居身上。
  修法就是 Mindustry 自己在用的 `.ellipsis(true)`（`Arc-Source/arc-core/src/arc/scene/ui/layout/Cell.java:262`；
  先例 `JoinDialog.java:272/301`、`WaveInfoDialog.java:175`、`MapListDialog.java:192`、`PlacementFragment.java:406`）。
- `TextButton` 的 label 在 cell 里**会**折行（`wrap` 对按钮的默认行为是折行），宽度小于文字宽就变两行。
- `Cell.fontScale()` 只对 `Label` 生效（`Cell.java:311` 里 `if(element instanceof Label)`）⇒ 按钮字号缩不了，只能加宽。
- 实测字号：CJK ≈16 px、拉丁 ≈8–9 px。`排序：最近更新` ≈ 112 px 宽 ⇒ `width(132)` 不够（还要 pad）；
  `● 地图不符` ≈ 96 px ⇒ `width(92)` 折行；`导出 JSON` ≈ 104 px ⇒ `width(110)` 仍挤。
- 0.19.1 只放大了**面板**，栏内排版还是 0.19.0 的窄列宽 ⇒ 窗口变大后反而更容易看出叠字。

## §3 改法（全在 `MlogAuxiliary/scripts/main.js`）

- 新 helper：`wsListPaneWidth()`（读 `wsUI.listW`，缺省 380）、`wsDetailPaneWidth()`（读 `wsUI.detailW`，缺省回 list）、
  `wsFilterCn(key)`；`wsUI` 加 `listW/detailW` 两个字段。
- `wsRefreshList()`：`iw = pw - 22`；搜索框 `width = max(90, iw-158-6)`；排序按钮 `width(158)` + ellipsis；
  四个 chips 等分 `cw = max(60, floor((iw-14)/4))` + ellipsis，**去掉「● 」前缀**（选中态改在计数行
  `— N 个工作区 · 筛选：进行中 —` 显示，省得前缀把按钮挤折行）；卡片去掉写死的 `height(46)`，
  改 `.growX().padTop(2).padBottom(4)` 让两行字自己撑高；名字 `width max(80, iw-26)`、副行 `width max(80, iw-30)`、
  `fontScale(0.85)`，两者都 `ellipsis(true)`；色条高 28。
- `wsRefreshDetail()`：`iw = wsDetailPaneWidth() - 22`；头部名字 `width max(90, iw-86)` + 状态 80 都 ellipsis；
  bounds 行 / 备注 / 分节标题 / 空态提示统一 `.width(iw).ellipsis(true)`；处理器表列宽
  `cPos = 92`、`cCode = 92`、`cWrite = 60`、`cBlock = max(80, iw-92-92-60-6)`（方块列吃剩余宽度），
  一律 ellipsis、去掉 `substring(0,12)` 硬截；作业行 `cState = 64`、`cId = 90`、`cTime = 86`、
  `cDesc = max(60, iw-8-6-64-90-86-6)`，时间列 `.right()`；主按钮 `width max(120, floor((iw-8)/2))` 高 40，
  次按钮（存成蓝图 / 归档|取消归档 / 改名 / 导出 JSON）与「释放工作区…」**全部去掉写死宽度**，只留 `height(32)` + ellipsis。
- `renderBlueprintPicker()`：用 `wsListPaneWidth()` 算 `iw`（原来写死 `width(560)`，在 421 宽的左栏里必定溢出）。
- `openWorkspaceDialog()`：尺寸计算抽成纯函数 `wsDialogPlan(sw, sh)` →
  `availW = clamp(w-40, 520, 1500)`、`availH = clamp(h-150, 320, 820)`（-150 留给标题栏 + 底栏）、
  `listW = clamp(availW*0.3, 340, 470)`、`detailW = max(300, availW-listW-14)`、`onlyW = min(availW, 560)`、
  `wide = w >= 980`；算好的宽写进 `wsUI` 供栏内排版；`cont.defaults().pad(3)`；
  底部五个按钮（刷新 / 撤销上次写入 / 撤销快照 / 从蓝图创建 / 关闭）只留 `height(34)` + ellipsis。

## §4 验证

- `node --check MlogAuxiliary/scripts/main.js` → EXIT 0。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT 0，
  `MAIWS3:ok rows=3 filt=2 sort=3 detail=2 ghosts=1 release=1 mismatch=1 locate=1 plan=398x914`。
- `maiWorkspace3Probe`（`main.js:7467` 起）新增断言：`wsDialogPlan(1366,768).wide === true`、
  `listW >= 340`、`detailW >= 300`、`availW === 1326`、`listW + detailW + 14 <= availW`、
  `wsDialogPlan(900,600).wide === false`、`wsDialogPlan(0,0).availW === 1240`（0 回退 1280 再 -40）、
  `wsFilterCn` 两个值；计数末尾多一段 ` plan=398x914`。
  踩坑：第一次把 fallback 期望写成 1280，报 `MAIWS3:bad plan-fallback` —— 回退值还要再减 40。

## §5 留给真机验

1. 1366×758 与 1920×1080 两种窗口下开「工作区快照」，看是否还有叠字 / 折行。
2. 把所有名字改成超长（30+ 汉字）、备注写长句，看左栏卡片与右栏备注是否老实省略号。
3. 窄屏（窗口 < 980 px）单栏：点行进详情、「← 返回列表」回来是否正常。
4. `⌖ 定位` 与世界里细框仍然正常（这两块本次没动）。
