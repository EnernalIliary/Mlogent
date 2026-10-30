# 52 · v0.6.1：选框偏右上角半格 —— Tile.worldx() 是格子中心

日期 2026-10-30 ｜ 触发：玩家实测（m11766）「选框位置偏右上角越半格」｜ 提交：见 git log

## 1. 现象

v0.5.0/v0.6.0 用 F3 拉框时，高亮矩形整体向右上各偏半个格子（4 px），但快照落盘的 bounds 是对的 —— 说明**只是画的位置错**，选中的格子没错。

## 2. 根因

坐标口径。高亮走 `Lines.rect(x, y, w, h)`，这个函数按**左下角 + 宽高**画
（`Arc-Source/arc-core/src/arc/graphics/g2d/Lines.java:485` → `:493` → 内部 `Fill.crect`），
和 `Draw.rect(region,x,y,w,h)` 的中心锚定（`Draw.java:378` `x - w/2f`）相反 —— 这一点 v0.5.0 已经对了。

错在给它的 x/y：`Tile.worldx()` 返回 `x * tilesize`
（`Mindustry-Source/core/src/mindustry/world/Tile.java:166-172`），那是格子的**中心**世界坐标，
不是左下角。格子 `(x1,y1)` 的左下角是 `(x1 - 0.5) * 8`。v0.5.0 直接把 `r.x1 * 8` 传进去，
于是整框在 x 和 y 上各多 4 px = 半个格子，视觉上就是「偏右上角」。

原版选框也是先减半格的：
`Mindustry-Source/core/src/mindustry/input/Placement.java:380-390`
`drawResult.x = result.x * tilesize - block.size * scaling * tilesize / 2`
（air：size 1、scaling 1 ⇒ 减 `tilesize/2 = 4`；y 同理）。

## 3. 改动

| 文件 | 改动 |
|---|---|
| `MlogAuxiliary/scripts/main.js` | `selDrawArgs(r)` → `{x: (r.x1 - 0.5) * 8, y: (r.y1 - 0.5) * 8, w: r.w * 8, h: r.h * 8}`；注释写明 Tile.java:166-172 与 Placement.java:380-390 依据；`MOD_VERSION = "0.6.1"` |
| `MlogAuxiliary/mod.hjson` | version 0.6.1 |
| `tests/mlogauxiliary/run_ui_smoke.py` | `MASELDRAW` 期望改 `{x:(bx+5)*8-4, y:(by+5)*8-4, w:40, h:24}`；新增红线两条：`(r.x1 - 0.5) * 8` 与 `(r.y1 - 0.5) * 8` 必须同时出现（少了半格就红） |
| `MlogAuxiliary/README.md` | 新增「## v0.6.1：选框偏了半格 —— Tile.worldx() 是格子中心」，标题版本改 v0.6.1 |
| `docs/断言表.md` | L2-38 证据改写：加半格依据、两条新红线、`MASELDRAW` 期望值 |
| `docs/验证记录.md` | 新增「## 2026-10-30 v0.6.1 选框偏右上角半格（L2-38 改写）」 |

只改一行代码就够 —— 其余都是把「为什么是半格」钉进文档与测试，防止下次又被 `worldx()` 的名字骗。

## 4. 复跑

| 项 | 命令 | 结果 |
|---|---|---|
| 语法 | `node --check MlogAuxiliary/scripts/main.js` | 通过（94,528 B） |
| 选框探针 | `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` | PASS（`MAIDIAG:版本：0.6.1`；`MASELDRAW` 命中新期望） |
| 门禁 | `python -X utf8 gate.py --full` | **16/16 passed**（清掉残留 JVM 后 33.8s；见 §5） |
| 知识库 | `python -X utf8 tools/kb.py build` | `{"chunks": 6060, "files": 63}` |
| 打包 | `python -X utf8 out/_v45_zip.py` | zip **53,190 B** sha256 `51CA731551CE2826A92430811A795E2912CF9F50DFA525E9A7BF5FFE98D980CA`（main.js 94,528 B） |
| 装机 | `python -X utf8 out/_v45_install.py` | 5 文件逐字节 OK，已拷 `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary`（main.js sha 前 16 位 0D6AD21CCBB8D88B） |

## 5. 附带发现：门禁的假失败是 JVM 内存压力

第一次 `gate.py --full` 报 `13/16 -- FAILED: probes, logicd`，错误是 JVM 侧

```
# Native memory allocation (mmap) failed to map 532676608 bytes. Error detail: G1 virtual space
```

不是代码问题。实测机器上残留 **65 个** `out/jre21/.../java.exe`（全是 `-jar out/_server160.jar`，
每个 148-256 MB），是历次 probes/logicd/ui smoke 起过的模拟器服务没退干净；清掉后 free 从 2,853 MB 回到 10,542 MB，
门禁立刻 16/16。**以后 gate 出现 probes/logicd 假失败，先 `Get-Process java | Stop-Process` 再跑**，
别去改代码。

## 6. 诚实缺口

半格修正是按源码口径算的，无头环境没有 GL，**观感仍要玩家在真机上看一眼**：拉一个 3×2 的框，
看高亮矩形的四条边是不是正好压在格子边界上（而不是向右上半格）。
