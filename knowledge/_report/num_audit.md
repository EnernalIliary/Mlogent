# 数字审计报告（文章 vs 00-data）

- 生成: num_audit.py  ·  知识库根: <repo>\knowledge
- 可审计表: 00-data/blocks.json, 00-data/turrets.json, 00-data/units.json
- 命中: 24 条，A_MATCH=24  A_MISMATCH=0  A_SUSPECT=0

## 02-world/W01-blocks-multiblock-anchor.md（6 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 139 | size | 3 | 3 | 00-data/blocks.json | +0.0% | A_MATCH |  |
| 139 | size | 3 | 3 | 00-data/blocks.json | +0.0% | A_MATCH |  |
| 139 | size | 2 | 2 | 00-data/blocks.json | +0.0% | A_MATCH |  |
| 139 | size | 1 | 1 | 00-data/blocks.json | +0.0% | A_MATCH |  |
| 139 | size | 1 | 1 | 00-data/blocks.json | +0.0% | A_MATCH |  |
| 139 | size | 9 | 9 | 00-data/blocks.json | +0.0% | A_MATCH |  |

## 02-world/W10-storage.md（1 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 38 | itemCapacity | 0 | 0 | 00-data/units.json | - | A_MATCH |  |

## 03-combat/C01-damage-pipeline.md（3 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 117 | armor | 22 | 22 | 00-data/units.json | +0.0% | A_MATCH |  |
| 126 | armor | 0 | 0 | 00-data/units.json | - | A_MATCH |  |
| 126 | armor | 9 | 9 | 00-data/units.json | +0.0% | A_MATCH |  |

## 03-combat/C02-turrets.md（4 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 36 | reload | 20 | 20 | 00-data/turrets.json | +0.0% | A_MATCH |  |
| 36 | reload | 100 | 100 | 00-data/turrets.json | +0.0% | A_MATCH |  |
| 129 | reload | 34.286 | 34.286 | 00-data/turrets.json | +0.0% | A_MATCH |  |
| 129 | reload | 3.5 | 3.5 | 00-data/turrets.json | +0.0% | A_MATCH |  |

## 03-combat/C03-bullets.md（1 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 122 | range | 160 | 160 | 00-data/turrets.json | +0.0% | A_MATCH |  |

## 03-combat/C05-armor.md（2 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 161 | armor | 22 | 22 | 00-data/units.json | +0.0% | A_MATCH |  |
| 163 | armor | 14 | 14 | 00-data/blocks.json | +0.0% | A_MATCH |  |

## 03-combat/C09-defense.md（5 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 44 | armor | 14 | 14 | 00-data/blocks.json | +0.0% | A_MATCH |  |
| 150 | armor | 15 | 15 | 00-data/blocks.json | +0.0% | A_MATCH |  |
| 161 | armor | 0 | 0 | 00-data/blocks.json | - | A_MATCH |  |
| 161 | armor | 16 | 16 | 00-data/blocks.json | +0.0% | A_MATCH |  |
| 165 | armor | 16 | 16 | 00-data/blocks.json | +0.0% | A_MATCH |  |

## 04-units/U01-movement.md（1 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 141 | speed | 2.7 | 2.7 | 00-data/units.json | +0.0% | A_MATCH |  |

## 08-evidence/CHEAT.md（1 条，异常 0）

| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |
|---:|---|---:|---:|---|---:|---|---|
| 142 | armor | 22 | 22 | 00-data/units.json | +0.0% | A_MATCH |  |

AUDIT_RESULT: OK
