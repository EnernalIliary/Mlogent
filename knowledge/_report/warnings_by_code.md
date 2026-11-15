# warning 按 code 统计（check_kb.py --json）

- 生成: kb-stage/_warnstat.py  ·  根: <repo>/knowledge
- files=37  errors=0  warnings=166  tokens~29666
- 退出码: 0

## 总表

| code | 条数 | 占比 | 含义 |
|---|---:|---:|---|
| W_NUM_NO_SOURCE | 120 | 72.3% | 数字声明行缺来源标记（[src: / [实测 / 见 DATA） |
| W_REF_UNKNOWN | 19 | 11.4% | 相关 小节引用了库里不存在的 ID |
| W_SRC_FORMAT | 14 | 8.4% | src 条目不像 路径:行号 / jar: 形式 |
| W_DATA_RECORD | 9 | 5.4% | 00-data 记录缺 id/src/ver 之一 |
| W_TOKENS_STALE | 3 | 1.8% | frontmatter tokens 与实际估算不符 |
| W_DOMAIN_EMPTY | 1 | 0.6% | 域目录下没有文章 |

## 按文件（Top 20，warning 数最多）

| 文件 | warning 数 | 主要 code |
|---|---:|---|
| 04-units/U01-movement.md | 11 | W_NUM_NO_SOURCE x6 |
| 02-world/W03-power.md | 10 | W_NUM_NO_SOURCE x6 |
| 02-world/W02-crafting-recipes.md | 8 | W_NUM_NO_SOURCE x6 |
| 02-world/W04-liquids.md | 8 | W_NUM_NO_SOURCE x6 |
| 02-world/W05-heat.md | 8 | W_NUM_NO_SOURCE x6 |
| 03-combat/C04-status.md | 8 | W_NUM_NO_SOURCE x6 |
| 03-combat/C06-unit-weapons.md | 8 | W_NUM_NO_SOURCE x6 |
| 03-combat/C07-support.md | 8 | W_NUM_NO_SOURCE x6 |
| 03-combat/C08-waves.md | 8 | W_NUM_NO_SOURCE x6 |
| 03-combat/C09-defense.md | 8 | W_NUM_NO_SOURCE x6 |
| 03-combat/C10-numbers.md | 8 | W_NUM_NO_SOURCE x6 |
| 03-combat/C01-damage-pipeline.md | 7 | W_NUM_NO_SOURCE x6 |
| 03-combat/C02-turrets.md | 7 | W_NUM_NO_SOURCE x6 |
| 03-combat/C03-bullets.md | 7 | W_NUM_NO_SOURCE x6 |
| 07-patterns/P01-architecture.md | 7 | W_NUM_NO_SOURCE x6 |
| 08-evidence/anti-patterns.md | 7 | W_NUM_NO_SOURCE x6 |
| 02-world/W01-blocks-multiblock-anchor.md | 6 | W_REF_UNKNOWN x3 |
| 03-combat/C05-armor.md | 6 | W_NUM_NO_SOURCE x6 |
| 07-patterns/P05-radar-targeting.md | 5 | W_NUM_NO_SOURCE x5 |
| 07-patterns/P03-comm-bus.md | 3 | W_NUM_NO_SOURCE x3 |
