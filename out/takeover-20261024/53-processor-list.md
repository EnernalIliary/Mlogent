# 53 · v0.7.0：F2 全图处理器清单

日期 2026-10-30 ｜ 触发：用户「下一f」 ｜ 提交：见 git log

## 1. 为什么是这个

P3 走到 v0.6.1 之后，游戏内已经有三个入口：F3 框选、F4 面板、F7 链接候选。
但「**哪台处理器有问题**」这件事仍然只能一台一台把鼠标挪过去按 F4 —— 而 `maiScan()`
（`main.js` 里早就有）其实一次就能扫全图，只是输出是控制台里的一段纯文本，玩家在游戏里看不到。

所以下一刀是**把 `maiScan` 的遍历做成面板**，顺手接上「点一行就跳过去改」这个动作。
键位选 F2：`Mindustry-Source/core/src/mindustry/input/Binding.java` 里
F1（`blockInfo`）/F5（`togglePowerLines`）/F6（`toggleBlockStatus`）/F8（`console`）/
F11（`fullscreen`）/F12（`screenshot`）都归游戏，F3/F4/F7 是我们自己的 —— **F2 是唯一还空着的功能键**。

## 2. 做了什么

| 部分 | 实现 |
|---|---|
| 扫描 | `scanProcessors()`：`Groups.build.each` → `isProcessor(g)`（鸭子类型 `executor + code`，与 `targetBuild()` 同判据，`instanceof LogicBlock` 在 v160.7 永远为假）→ 每台跑 `api.q.check(api.r, src, linkNames(g), {build})`，收 `{x,y,lines,err,warn,links,rules}` |
| 排序 | ERR 多 → WARN 多 → y → x（问题最多的在最上面） |
| 表格 | `listHead()` 一行摘要（`全图 N 个处理器，ERR a / WARN b，ms`，快检不可用时加注）、`listRowLabel()` 每行 `@x,y  12 行  ERR 2  WARN 1`、`buildListTable()` 最多 24 行 + 「…还有 N 个」 |
| 面板 | `showListPanel()`：`Dialog` + 自造 `Table` 交给 `d.cont.pane(host)`（v0.4.1 教训：pane() 交回 ScrollPane，没有 `add`）；按钮「复制清单」/「关闭」 |
| 跳转 | 点一行 → `Core.camera.position.set(x*8+4, y*8+4)`（`Tile.worldx() = x*8` 是格子中心，+4 是为了压在格子中心附近）→ 关面板 → `showAiPanel(buildAt(x,y))` |
| 退路 | 面板抛异常 → `popup()` 纯文本；控制台 `maiList()`（文本）/ `maiListRows()`（JSON）/ `maiListPanel()` |
| 自检 | `selfTest()` 多建一张「清单表格」（假 rows 两条）→ 输出「清单表格 6 行」 |

只读：不写方块、不写代码，跑的是审查栏同一个快检函数。

## 3. 验证

| 项 | 命令 | 结果 |
|---|---|---|
| 语法 | `node --check MlogAuxiliary/scripts/main.js` | 通过（101,782 B） |
| ui smoke | `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` | PASS：`MAISELF:…清单表格 6 行…`、`MAIDIAG:版本：0.7.0`、`MAILIST:全图 0 个处理器…`、`MAILISTROWS:[]` |
| 门禁 | `python -X utf8 gate.py --full` | **16/16 passed**（36.3s） |
| 知识库 | `python -X utf8 tools/kb.py build` | `{"chunks": 6061, "files": 63}` |
| 打包 | `python -X utf8 out/_v45_zip.py` | zip **55,287 B** sha256 `21FCD283F909D6EA23CCA2F56E8E308E3FAE13CC0544A6F55BF92225AD6B30EB` |
| 装机 | `python -X utf8 out/_v45_install.py` | 5 文件逐字节 OK（main.js 153E99325CB15AF9） |

新增测试断言：`MAISELF` 含「清单表格」；`MAILIST:` 必须以「全图 」开头；`MAILISTROWS:` 必须是 JSON 数组；
五条源码红线（`KEY_LIST = ["f2"]` / `scanProcessors` / `buildListTable` / `showListPanel` + `maiListPanel` /
相机跳转那一行 / `isProcessor(g)`）。

## 4. 诚实缺口

无头引擎里 `Groups.build` 是空的（模拟器只放了一个处理器且不注册进 Groups.build），
所以「扫描 + 排序」只验到「0 个处理器时首行是 全图 」，**真机上要玩家按一次 F2** 看清单数量与图上是否一致。
相机跳转也没法在无头里验（没有 renderer 的相机位移可读回）。

## 5. 下一步候选

- 清单里点一行目前直接开 F4；如果玩家更想「只看不改」，可以改成「跳相机 + 关面板」。
- 清单可以加一列「链接数 / 未绑定链接名」（`/region` 已经有这个数据，但那是 HTTP 往返，全图扫会慢）。
