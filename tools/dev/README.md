# tools/dev

这里是从 `tools/` 根目录挪过来的一次性脚本：探针、patch、调试、抓取、导出。
移动前它们和稳定工具混在一起，目录看起来像 200 多个工具；现在只有真正带入口/被文档引用的留在上一层。

注意：

- 这些脚本**不保证还能跑**：它们写死了 `Path(__file__).resolve().parents[1]` 之类的仓库根假设，挪深一层后路径会指到 `tools/`。要用的话先把根路径改回 `parents[2]`。
- 不要从这里 import，也不要把它当接口；稳定实现都在 `tools/` 顶层。
- 语料分析脚本在 `tools/corpus/`，不在本目录：`_sweep_saves.py`、`_sweep_analyse.py`、`_label_programs.py`、`_err_table.py` 等。
- 目录内容默认被 `.gitignore` 忽略；要保留某个脚本请 `git add -f`。

## 可复现的数据导出器（例外：需要保留并被人引用）

`dump_game.py` —— 从 v160.7 真执行器（`out/_server160.jar` + `out/jre21/`，可用 `MLOGSIM_JAR` / `MLOGSIM_JAVA` 覆盖）
重导 `data/game/{items,liquids,blocks,units,meta}.json`：`python tools/dev/dump_game.py`。
它已按本文的约定改成 `ROOT = Path(__file__).resolve().parents[2]`，所以在任何目录下都能跑；
字段全部直接取自 `Vars.content` 反射，取不到的记 `null`（不再填 `-1` 之类的假值）。

blocks 共 15 个字段：`id, name, size, health, category, hasPower, requirements,
consumers, outputs, craftTime, itemCapacity, liquidCapacity, range, reload,
outputLiquids`。几个容易踩的点：

- `craftTime` 不是 `Block` 的字段，只存在于 `GenericCrafter` 及其子类 —— 447 个方块里
  33 个有真值、414 个是 `null`（`null` = 该类没有这个字段，不是"瞬间完成"）。
- 分离器的产物在 `results` 而不是 `outputItems`；`outputLiquids` 只覆盖产出液体的方块
  （2026-11 之前这两个都是空的）。
- 数值 `round(..., 4)`：执行器给的是 float32，不四舍五入会写成 `0.20000000298023224`。

`tools/game.py` 的提示语与 `knowledge/` 的文档都指向这个路径。

## 源码拓荒脚本（从 tools/ 顶层移入）

`block_ids_from_source.py`、`blocks_from_source.py`、`content_names_from_source.py`、
`items_from_source.py`、`units_from_source.py`、`sensor_from_source.py`、
`sensor_attrs_from_jar.py`、`classdump.py`、`fix_skill_links.py` —— 说明见
`tools/README.md` 的「tools/dev/」一节。产品链路不 import 它们。
