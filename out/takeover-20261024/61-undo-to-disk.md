# 61 · v0.10.0：撤销跨重启 —— 写入前把原代码落盘（P5 第一刀）

日期 2026-10-30。P5 规划（`docs/Mlog辅助-规划.md` §5）里的第一件可独立做的事。

## 61.1 症状

写错了想回滚，模组里只有内存栈：`undoStack` 活在 Rhino 的全局对象里，**关掉游戏就没了**。
第二天开游戏，处理器上是坏代码，原来的那份只能靠存档备份或者手抄。

## 61.2 判据

写入通道是 `build.configure(bytes)`，动的是「代码 + 链接表」两样东西；而模板生成的链接表
来自处理器**当前**的链接（`/plan` 的 `links` 是模组读出来传过去的），所以回滚只需要把代码换回去
（`b.updateCode(code)`）。链接表一并存进快照，是留给第二刀（事务写入时逐字节还原）与人工排查的。

## 61.3 改动（`MlogAuxiliary/scripts/main.js`，102,341 → 108,228 B）

| 名字 | 职责 |
| --- | --- |
| `UNDO_KEEP = 40` | 磁盘上最多留 40 份，写新的就删最旧的 |
| `undoRoot()` | `Vars.dataDirectory.child("mlogauxiliary").child("undo")`，不存在则 `mkdirs()`；任何异常 `log` 后返回 `null`（撤销静默失效，但写入不受影响） |
| `linkPairs(b)` | 遍历 `b.links.size` / `.get(i)`，取 `name`/`x`/`y`/`block.name` |
| `snapshotText(b, why)` | `JSON.stringify({schema:1,x,y,at:Date.now(),why,code:String(b.code),links:linkPairs(b)})` |
| `undoFilesOf(root)` / `undoFiles()` | `root.list(".json")` → 按名字排序后反转 = 最新在前（文件名以毫秒时间戳开头） |
| `saveUndoTo(root, b, why)` | 文件名 `Date.now()+"_"+x+"_"+y+".json"`，`writeString(text, false)`；超出上限从尾部删 |
| `saveUndo(b, why)` | 取 `undoRoot()` 后落盘，返回文件名（给写入成功的提示用） |
| `undoFromDisk()` | 按文件名 `split("_")` 取 x/y → `Vars.world.build(x,y)` → 不是处理器（`b.code === undefined`）就跳过继续往前 → `b.updateCode(snap.code)` + 删该文件 |
| `undoInfo()` | 报份数与目录（给「撤销快照」按钮） |

接线：

- `writeBuild()`：`var snapName = saveUndo(b, "write:" + String(res.template || "code"));` →
  `undoStack.push({b: b, code: String(b.code), snap: snapName});` → `configure`；
  成功文案尾部追加 `；撤销快照 <名字>`。
- `undo()`：内存栈非空就用内存（顺手删掉对应磁盘快照），否则 `return undoFromDisk();`。
- 设置页「快捷动作」多一行：**撤销上次写入** / **撤销快照**（`Vars.ui !== null` 保护后 `showText`）。
- 控制台：`maiUndo` / `maiUndoInfo` / `maiUndoProbe`（真引擎自检，见 61.5）。

## 61.4 三个坑

1. **`Vars.dataDirectory` 是 Arc 的 `Fi`，不是 `FileHandle`**：v160.7 里类名就叫 `Fi`
   （`Arc-Source/arc-core/src/arc/files/Fi.java`）。`child`/`writeString(String, boolean)`/`readString`/
   `list(suffix)`/`mkdirs`/`delete`/`deleteDirectory` 都在，但没有 `listFiles()`、没有 `append`。
2. **`writeString(text, false)` 第二个参数是 append**：传 `true` 会把新快照接在旧内容后面，读回来就是坏 JSON。
3. **撤销要能跨重启，就不能依赖 `Vars.world.build()` 的返回值一定是处理器**：拆掉的、换图之后坐标上
   可能是空气或别的方块，读 `b.code` 得到 `undefined`，必须跳过而不是抛异常（否则一次坏快照就锁死撤销）。

## 61.5 验证

- `tests/mlogauxiliary/run_ui_smoke.py` 在真 v160.7 引擎里跑新探针 `MAIUNDO:` +
  `maiUndoProbe()`：把一份假快照写进 `<dataDir>/mlogauxiliary/selftest`，读回来比对
  `x===3 && y===4 && code 相同 && links.length===0`，再删文件与目录 → `MAIUNDO:ok 1793373825237_3_4.json`。
- `maiSelfTest()` 里加了一次纯序列化往返（`fakeB` → `snapshotText` → `parse` → 比对），
  `MAISELF` 行出现「撤销快照 ok」。
- 三条源码红线：`function saveUndoTo(` / `function undoFromDisk(` /
  `undoStack.push({b: b, code: String(b.code), snap: snapName})`。
- 实测：`python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，表格方法 18 个全 OK_SKIN、
  假表 70 行/格、作业三路（done / 门禁拒绝 / 零链接拒绝）全过、`MAIDIAG:版本：0.10.0（游戏构建 160）`。
- `python -X utf8 gate.py --full` → 首跑 15/16（kb WARN stale）→ `tools/kb.py build`（chunks 6360 / files 65）
  → **16/16 passed in 37.4s**。

## 61.6 边界与下一刀

- 磁盘快照只回滚代码，不回滚链接表（第二刀做）；跨重启回滚没有真机手验（探针走的是同一条
  `saveUndoTo`/`undoFromDisk` 路径，但没有「关游戏再开」这一步）。
- `saveUndo` 失败不阻断写入，只在日志里留一行 —— 这是有意的：撤销是安全网，不是写入的前置条件。
- 下一刀（P5 剩余）：一个作业产出多段代码时的事务写入 + 整体回滚、写前「处理器在你提交后被改过」的
  冲突提示；两者都要先扩 sidecar 的作业契约（一个 job → N 段代码）。
