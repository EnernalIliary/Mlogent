# 发布后校验

- 库: <repo>\out\_kb\kb.sqlite3  (42536960 B)
- knowledge: -
- 时间: 2026-11-08 04:41:42

| 项 | 判定 | 依据 |
|---|---|---|
| STRUCT | **FAIL** | 语料含工作产物 9 个: knowledge/_report/_fx/knowledge/00-data/README.md, knowledge/_report/_fx/knowledge/02-world/X01-fixture.md, knowledge/_report/_fx2/knowledge/02-world/X02-fixture.md |
| COUNT | **FAIL** | chunks 8113 vs expect-chunks 8094（差 +19） |
| RETRIEVAL | **PASS** | A@1 14/20 (>=12) · outside_top1 1 (<=4) · A@3 15 · p50 Nonems |

- chunks=8113 files=140 kinds={'code': 6266, 'data': 163, 'doc': 1684}
- 结果: **FAIL**
