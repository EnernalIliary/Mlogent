# 65 · P5 第三刀上半：事务写入（v0.12.0）

日期：2026-10-31。版本：MlogAuxiliary v0.12.0。相关：规划 §5 P5、§9 P5 行；断言表 L2-48；验证记录同日段。

## 65.1 症状

规划里 P5 要的是「一个 job 产出 N 段代码、全部预检通过才写、任一台失败回滚已写的」。
之前只能一台一台点：中途某台失败，存档就停在一半新一半旧的状态，撤销也只能一台一台退。

## 65.2 设计决策：不扩 sidecar 的作业契约

规划 §5 原文说这一刀「要扩 sidecar 的作业契约（`code` → `codes[]`）」。实测后改成**模组侧用 N 个作业协调**：

- 每台处理器各投一个作业（各自的 `links` / `snapshot` / `origin`）。链接表、零链接门禁、self-repair 循环
  天然按台独立 —— 这比把 N 段代码塞进一个 job 更准，因为判据（这个链接名在**这台**处理器上绑没绑）本来就是单台的。
- 代价是 N 次投递、N 次轮询。写入阶段做成事务，把「一半新一半旧」这个真问题解决掉。
- 好处：sidecar 的作业契约、`jobqueue.py`、`/jobs` 全部零改动，v0.9.x 的门禁语义不被稀释。

## 65.3 改动表

`MlogAuxiliary/scripts/main.js`（120,137 → 127,985 字符，`node --check` EXIT=0，`+151/−4`）：

| 位置 | 改动 |
| --- | --- |
| `MOD_VERSION` | 0.11.0 → 0.12.0 |
| `snapshotText(b, why, batch)` | 快照 JSON 多一个 `batch: String(batch || "")` 字段（在 `why` 之后、`code` 之前） |
| `saveUndoTo(root, b, why, batch)` | 加第四参并透传；`saveUndo(b, why)` 不变（两参 → batch 为空串） |
| 新增「事务写入」段 | `UNDO_BATCH` / `batchId()` / `writeMany(items, why)` |
| `undo()` | 栈顶带 `many` → 逐台 `updateCode` + 删各自快照；否则走单台老路径，最后仍回落 `undoFromDisk()` |
| `undoFromDisk()` | 见 `snap.batch` 非空 → `undoBatchFromDisk(batch, files)` 整批还原 |
| 控制台 | `api.maiWriteManyProbe(aJson, x, y)` |

`writeMany` 的顺序（这是整刀的核心）：

1. **整批预检**：任一台目标不存在 / `res.ok !== true` / 没有 `bytes_b64` → 返回「拒绝写入（一台都没写）：…」，一台都不碰。
2. **整批冲突**：`conflictReason` 有一台命中且没 force → 置 `JOB_FORCE` 并「拒绝写入（一台都没写）：…；确认覆盖请再点一次」，
   再调一次才放行（与 v0.10.1 单台语义一致，只放行一次）。
3. **整批落盘**：先给每台 `saveUndoTo(..., "batch:" + why, batch)`，同一个 `batch` id。
4. **逐台 configure**：catch 里把已写的按 `snaps[j].code` `updateCode` 回滚，返回「写入失败（@x,y：…）；已回滚 N 台：…」。
5. 全成功：`forgetOrig` 每台、`undoStack.push({many: snaps, batch})`、返回「已写入 N 台（事务 <batch>）：@x,y …」。

## 65.4 回滚语义与边界

- 回滚用 `updateCode`，只还原**代码**；链接表本来属于各台处理器自己，不由作业改。
- 撤销按批次：内存栈一条 `{many, batch}`；跨重启时 `undoFromDisk()` 见到带 batch 的最新快照就整批还原，
  处理器已被拆掉的跳过并删掉那份文件（返回「已按事务 <batch> 回滚 X/N 台」）。
- **这一刀只有核心与探针，没有面板按钮**：多台一起投递要面板同时轮询 N 个作业，是下一刀。
- `writeMany` 只吃「已经 done 的作业结果」，不负责投递；单台写入 `writeBuild` 一行未改。

## 65.5 复跑与打包

- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0。关键行：
  `MAISELF:设置表格可建，填了 102 行/格…撤销快照 ok`、`MAIDIAG:版本：0.12.0`、`MAIUNDO:ok 1793382165910_3_4.json`、
  `MAICONFLICT:ok`、`MAILLM:ok 82`、`MAIWRITEMANY:ok`，摘要行
  `batch write: ok 已写入 2 台（事务 1793382167907_b）：@0,0 @3,3 | 已回滚 2 台（事务 1793382167907_b）：@0,0 @3,3`；
  作业三路（done / rejected 3 次 / zero-link）与冲突门禁全过；表格方法 18 个全 OK_SKIN。
- `python -X utf8 tools/kb.py build` → `{"chunks": 6461, "files": 65}`。
- `python -X utf8 gate.py --full` → **16/16 passed in 48.2s**。
- `python -X utf8 out/_v45_zip.py` → zip **74,501 B sha256 54A9C528DEC1B89C5C34E5A0055293D90464705D67701048960AD54D654872E1**
  （main.js 146,105 / README 55,930 / mod.hjson 2,656 / quickcheck 8,486 / rules.generated 6,463），5 条目全带顶层 `MlogAuxiliary/`。
- `python -X utf8 out/_v45_install.py` → 装机 5 文件逐字节 OK（`E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary`）。

## 65.6 下一刀候选

1. **面板批量入口**（P5 第三刀下半）：区域面板多选 + 一次投 N 个作业 + 同时轮询 + 全部 done 后调一次 `writeMany`。
2. 联机下服务端拒绝写入时的「无权限」提示（现在只会报 config 失败）。
3. 冲突检测只比代码文本，不比链接表（v0.10.1 起就是已知保守）。
4. 打包/安装即用（用户已定「最后解决」）：PyInstaller 单 exe + 模组侧 ProcessBuilder 拉起。
