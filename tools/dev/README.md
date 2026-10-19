# tools/dev

这里是从 `tools/` 根目录挪过来的一次性脚本：探针、patch、调试、抓取、导出。
移动前它们和稳定工具混在一起，目录看起来像 200 多个工具；现在只有真正带入口/被文档引用的留在上一层。

注意：

- 这些脚本**不保证还能跑**：它们写死了 `Path(__file__).resolve().parents[1]` 之类的仓库根假设，挪深一层后路径会指到 `tools/`。要用的话先把根路径改回 `parents[2]`。
- 不要从这里 import，也不要把它当接口；稳定实现都在 `tools/` 顶层。
- 语料分析脚本在 `tools/corpus/`，不在本目录：`_sweep_saves.py`、`_sweep_analyse.py`、`_label_programs.py`、`_err_table.py` 等。
- 目录内容默认被 `.gitignore` 忽略；要保留某个脚本请 `git add -f`。
