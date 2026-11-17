# 检索冒烟

- 题库: <scratch-dir>\kb-stage\_report\smoke_demo.jsonl（6 题，其中 6 题有 expect）
- 库: <scratch-dir>\kb-stage\_kb_build2\kb.sqlite3
- 模型预热: 1.6s  ·  单题 p50=233ms  p90=281ms  max=281ms
- top1 命中 2/6（33%）  top3 4/6（67%）  top6 5/6（83%）

| # | 题干 | top1 | 命中@3 | ms | 首条命中 |
|---:|---|---|---|---:|---|
| 1 | 护甲减伤公式 | Y | Y | 281 | knowledge/03-combat/C05-armor.md |
| 2 | conveyor 每秒运几件 | N | N | 212 | 00-data/formulas.json |
| 3 | ucontrol 参数顺序 | N | Y | 220 | knowledge/06-mlog/M07-单位与逻辑控制.md |
| 4 | 多格方块 锚点 footprint | Y | Y | 234 | knowledge/02-world/W01-blocks-multiblock-anchor.md |
| 5 | 处理器每秒执行多少指令 | N | N | 233 | 00-data/formulas.json |
| 6 | wait 精度 tick | N | Y | 177 | knowledge/06-mlog/M03-控制流.md |

## 未命中明细（1）

- 题干: conveyor 每秒运几件  ·  expect=['W']
    - 00-data/formulas.json
    - docs/MBO与配比计算器.md
    - knowledge/03-combat/C02-turrets.md
