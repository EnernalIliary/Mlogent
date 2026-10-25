# out/ 目录说明

这里是一次性产物和工作区，不是源码。可重建的内容不要提交。

| 路径 | 内容 | 是否入库 |
|---|---|---|
| `scenes/` | 5 张现实场景 `.msav`、3 个合成台（`benches/`）、快照脚本与 PNG | 入（小文件） |
| `_kb/`、`_kbmodels/`、`_kblibs*/` | 本地知识库索引、模型、依赖 | 否 |
| `_archive/` | 一次性排查/补丁脚本（2026-10-24 归档） | 否 |
| `_sim/`、`_sim_*.log` | 模拟器 workdir 与日志 | 否 |
| `*.mlog`、`*.msch`、`*.json`、`*.png` | 会话里生成的 demo、探针、图 | 否（除非明确引用） |

重新生成场景/合成台的入口：`python out/scenes/benches/run.py`、`python out/scenes/_snapshot.py`。
游戏事实与速查：`out/_dump_game.py` → `data/game/`；`out/_gen_game_docs.py` → `docs/游戏速查/`。
