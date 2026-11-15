# 检索冒烟

- 题库: <scratch-dir>\kb-stage\_report\smoke_demo.jsonl（6 题，其中 6 题有 expect）
- 库: <repo>\out\_kb\kb.sqlite3
- 模型预热: 1.7s  ·  单题 p50=214ms  p90=216ms  max=216ms
- top1 命中 1/6（17%）  top3 2/6（33%）  top6 3/6（50%）

| # | 题干 | top1 | 命中@3 | ms | 首条命中 |
|---:|---|---|---|---:|---|
| 1 | 护甲减伤公式 | N | N | 216 | knowledge/03-combat/C01-damage-pipeline.md |
| 2 | conveyor 每秒运几件 | N | N | 216 | docs/MBO与配比计算器.md |
| 3 | ucontrol 参数顺序 | N | Y | 194 | knowledge/06-mlog/M07-单位与逻辑控制.md |
| 4 | 多格方块 锚点 footprint | Y | Y | 214 | knowledge/02-world/W01-blocks-multiblock-anchor.md |
| 5 | 处理器每秒执行多少指令 | N | N | 194 | mindustry-blueprint/REFERENCE.md |
| 6 | wait 精度 tick | N | N | 188 | knowledge/06-mlog/M03-控制流.md |

## 未命中明细（3）

- 题干: 护甲减伤公式  ·  expect=['C05']
    - knowledge/03-combat/C01-damage-pipeline.md
    - docs/游戏速查/单位.md
- 题干: 处理器每秒执行多少指令  ·  expect=['E0']
    - mindustry-blueprint/REFERENCE.md
    - tools/chats.py
    - knowledge/06-mlog/M01-执行模型总览.md
- 题干: wait 精度 tick  ·  expect=['E0']
    - knowledge/06-mlog/M03-控制流.md
    - knowledge/06-mlog/M08-性能与限制.md
    - docs/断言表.md
