# 107 · v0.19.6：工作区标题/卡片真正左对齐（单元格 align 不继承表）

驱动：用户 m02101「还是没改到，标题还是居中的，按钮底部的详情明明都正确省略了。」+ 截图 m02100（609×766 裁切）。

## 一、取证（真机 + 截图像素）

- 日志 `saves/last_log.txt`：`[mai] v0.19.5 ready, 86/86 console function(s)`、
  `[mai] ws dialog: screen=1707x1044 scl=1 plan=1080x760 list=324 detail=742 wide=true`
  ⇒ 窗口尺寸换算（v0.19.3）和宽度封顶（v0.19.4）、左栏按文字宽度（v0.19.5）**全部生效**，不是宽度问题。
- `[mai] ws geom:` 数字：`host(Table w=324)`、`#0 [TextField w=150][TextButton w=148]`、
  `#1 chips [全部 60][进行中 77][已归档 76][地图不符 96]`、`#2 Label w=237` ⇒ 控件宽度都对。
- 截图像素（PIL 量，`out/_probe_cards.png` 2× 放大）：卡片 4px 状态色条落在**卡片中间 x≈270**，
  工作区名字「区域 (216,41)」被挤到**卡片最右 x≈505 并被裁掉**，副行 `1 台 · 11-2 17:42 · 最近作业 #FFc4Ø…` 却正常左起。
- 顺带发现旧 dump 的 `x` 全是 -1：`Element` 没有无参 `getX()`（只有 `getX(int alignment)`，`Element.java:380`），
  `e.getX()` 抛异常被 catch 吞掉 ⇒ 上一版拿不到横向位置，才一直只能靠截图猜。

## 二、根因（源码实证）

1. **单元格对齐不继承表格**：`Arc-Source/arc-core/src/arc/scene/ui/layout/Table.java:1243` 是 `align = c.align;`
   （不是「cell 没写就用表 align」），`Cell.align` 默认 0（`Cell.java:31` `int align;`），
   ⇒ 落到 `Table.java:1249` 的居中分支 `c.elementX = currentX + (spannedCellWidth - c.elementWidth) / 2;`。
   所以 `card.left()` / `bar.left()` 只是把**整张表**靠左摆，管不住里面的格子。
2. **卡片是两行两列，副行落在第 0 列**：row0 = [image 4px] [name]，`card.row()`，row1 = [sub，width=iw-30]。
   sub 宽度 ~iw-30 把第 0 列撑到整卡宽，色条那个 cell 没写 `.left()` ⇒ 在超宽列里居中 ⇒ 跑到卡片中间；
   name 落到第 1 列（被挤到 ~505）后被裁。
3. **标题被 `fillX()` 撑满**：`Dialog.java:78` `titleTable.add(this.title).expandX().fillX().minWidth(0);`
   + `:79 add(titleTable).growX().row();` ⇒ Label 铺满整行，文字按自身 align 漂到中间；
   这一行撑开还会带着 `:209 add(cont).expand().fill()` 的行一起变宽。

## 三、改法（`MlogAuxiliary/scripts/main.js`）

| 位置 | 改法 |
| --- | --- |
| 左栏卡片（`wsRefreshListBody`） | 整卡 `card.left().top()`；色条 `image(Tex.whiteui).width(4).height(26).color(col).left()`；名字 `.left().padLeft(6).width(max(80, iw-34)).ellipsis(true)`；副行 `.left().padLeft(12).colspan(2).width(max(80, iw-40))` —— 用 colspan 跨两列，一次性消掉列宽冲突 |
| 筛选 chips | 标签换短：`全部 / 进行中 / 已归档 / 不符`（`不符` 加 tooltip「地图不符（工作区记录的地图跟当前地图不一样）」）；删掉 `maxWidth(cw)` + ellipsis（原来 cw=72 把三格截成「进行…/已归…/地图…」）；每个 button cell 加 `.left()` |
| 搜索行 | `bar.add(tf).width(150).height(34).padRight(6).left()`；排序按钮 `.height(34).ellipsis(true).left()` |
| 详情右栏 | 状态 `stateCn`、创建/更新时间、「⌖ 定位」、处理器表 4 个表头 + 4 列、作业行色点/状态/#id/描述、三排动作按钮，**逐格**补 `.left()`（时间列仍 `.right()`） |
| 对话框标题 | `d.titleTable.clearChildren(); d.titleTable.left(); d.titleTable.add(d.title).left().padLeft(2);`（紧跟 `d.title.setAlignment(Align.left)`） |
| 内容区 | `d.cont.defaults().pad(3).left();` 之后加 `d.cont.left().top();` |
| 自检 | `wsGeomOne` 改读字段 `e.x`（`getX()` 无参不存在）；`wsGeomDump` 额外 dump 标题行（`titleTable` + 前 3 个子元素） |

## 四、验证（无头）

- `node --check MlogAuxiliary/scripts/main.js` → EXIT=0。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，无 FAIL：
  `MAIWS3:ok rows=3 filt=2 sort=3 detail=2 ghosts=1 release=1 mismatch=1 locate=1 plan=324x742 cap=96/168 scl=1`。
- smoke 新增 v0.19.6 红线 6 条：`card.image(Tex.whiteui).width(4).height(26).color(col).left()`、
  `.left().padLeft(12).colspan(2)`、`d.titleTable.clearChildren()`、`d.cont.left().top()`、
  `try{ x = Math.round(Number(e.x)); }catch(e2){ }`、`["mismatch", "不符", …]`。
- 占位：门禁 / 打包 / 装机 / 发布见第六节。

## 五、留给真机验

1. 重启游戏 → 打开「工作区快照」：标题应在左上角，左栏每张卡片的色条贴左边缘、名字紧跟其后。
2. 若还有居中/遮挡，**请发整窗截图**（上次的裁切把标题条裁掉了），或贴日志里 `[mai] ws geom:` 那一行 ——
   现在它带 `title(...)` 与真实 `x`，可以直接对数字判断是谁在居中。

## 六、门禁 / 打包 / 装机 / 发布

## 六、门禁 / 打包 / 装机 / 发布

- 门禁 `python gate.py --full --kb-build` → **17/17 passed in 114.9s**（`out/_gate_v196.log`；恢复 CRLF 换行后复跑 17/17 in 50.8s，`out/_gate_v196b.log`）；把 main.js 换行恢复成 CRLF 后复跑 **17/17 in 50.8s**（`out/_gate_v196b.log`，kb 覆盖 168 源文件）。
- 打包 `python tools/package.py` → `out/_dist/MAI-0.19.6/` **178 files / 18,805,928 B**；
  `MAI-0.19.6-mod.zip` **8,461,225 B** / 169 files / sha256 `4AD3E0C9C9756AB271264AC19A6FA281841CF0B1872218C531BDADC6EC015DDA`；
  `MAI-0.19.6.zip` **8,482,963 B** / sha256 `D0F65673649506CFA58629091A1179BFD75EF71ECCDD6943DB5D7350FEE56B9C`。
- 装机：`Get-Process logicd | Stop-Process -Force` → `out/_dist/MAI-0.19.6/install.ps1 -Target "E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods"`
  → `[ok] MAI 0.19.6 installed`，旧副本备份 `saves\mod-backups\MlogAuxiliary-20261102-190226`；
  装后实测 `mod.hjson version=0.19.6`、`main.js MOD_VERSION=0.19.6`，且 `d.titleTable.clearChildren()` / `colspan(2)` / `Number(e.x)` 各命中。
- 发布：本地提交 **b7fa158**（9 files / +208 −46）；公开仓克隆 `out/_publish/mai-clone` 提交 **8e115b6**
  "v0.19.6: left-align the workspace title and cards (cell align does not inherit the table)" + tag `v0.19.6`，
  `git push origin main` 与 `git push origin refs/tags/v0.19.6` 均成功（1782d37..8e115b6 / [new tag]）；
  Release https://github.com/EnernalIliary/MAI-MlogAuxiIliary/releases/tag/v0.19.6 两个资产均 201，
  `releases/latest` = v0.19.6。
  （本机 git 直连 github.com:443 不通，push 需 `$env:HTTPS_PROXY="http://127.0.0.1:10808"`；python 走直连 opener 正常。）

