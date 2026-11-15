# INDEX_CONTRACT.md — knowledge/index.json 的索引契约

> 生成器：`knowledge/tools/build_index.py`（单一真源）。本文件描述**字段语义**，改字段必须先改本文件与生成器。
> 消费者：MCP 前置路由、CI 门禁、人工检索。任何字段只能加不能改名（v1 冻结）。

## 顶层字段
| 字段 | 类型 | 语义 | 稳定性 |
|---|---|---|---|
| `version` | int | 契约版本，当前 1 | 冻结 |
| `generated` | ISO8601 | 生成时间（`--check` 比对时剔除） | 每次变 |
| `root` | str | 固定 `"knowledge"`（路径均以此为前缀） | 冻结 |
| `read_order` | [str] | 推荐阅读顺序 | 可加 |
| `counts` | obj | 汇总数字，见下 | 可加 |
| `domains` | [obj] | 8 个域，固定顺序 01..08 | 冻结 |
| `data` | [obj] | `00-data/*.json` 机读表 | 可加 |
| `evidence` | [obj] | `08-evidence/` 下逐个文件 | 可加 |
| `evidence_dirs` | [obj] | `08-evidence/{claims,probes,bench}/` 目录汇总（空目录也出现） | 新增 v1.1 |
| `docs` | [obj] | 契约文档（KB.md / CONVENTIONS.md / VERSION.md） | 可加 |
| `notes` | [str] | 口径说明（tokens 为估算等） | 可加 |

## counts（判断"库是否可用"的唯一入口）
```json
{"articles":37, "by_domain":{"01-execution":6,"02-world":5,"03-combat":10,"04-units":1,
  "05-campaign":0,"06-mlog":8,"07-patterns":6,"08-evidence":1},
 "data_tables":10, "data_records":948, "data_raw_tables":7,
 "evidence_files":21, "evidence_by_kind":{"top":6,"bench":15}, "evidence_dirs":2,
 "tokens_total":34073, "empty":false}
```
- `data_tables`/`data_records` **只统计 kind=canonical** 的表；`rt_*`、`*_raw.json` 计入 `data_raw_tables`，只列出不计数。
- `empty=true` 表示没有任何文章（空库骨架）。`04-units`/`05-campaign` 为 0 时属于内容缺口，不是索引错误。

## domains[].articles[] — 文章的 10 个字段
| 字段 | 说明 |
|---|---|
| `id` | `DOMAIN.SUB.NNN`，与 frontmatter 同源；缺失时为空串（门禁会报 E_MISSING_FIELD） |
| `path` | `knowledge/02-world/W01-xxx.md`（**含** knowledge/ 前缀，可直接拼仓库根） |
| `title` / `domain` / `status` / `conf` | 取自 frontmatter；`conf ∈ {S,E,I,U}` |
| `ver` | 始终是数组，如 `["v160.7_rt","v159.3_src"]` |
| `tokens` / `tokens_est` | tokens 为 frontmatter 回填值；`tokens_est=true` 表示该值是本脚本估算（汉字 0.62 + 英文词 0.75） |
| `lines` | 物理行数（>250 行按约定应拆分） |

## data[] — 00-data 机读表
```json
{"path":"knowledge/00-data/blocks.json","kind":"canonical","records":447,
 "bytes":311169,"keys":["armor","category","class","health","id","itemCapacity","name","rotate","size","src","ver"]}
```
- `kind`：`canonical`（正式事实表：blocks/turrets/units/items/liquids/bullets/status/rules/formulas/src_anchors）｜`raw`（`rt_*` 反射抽查件，**不可直接引用为事实**）。
- `records` 支持两种顶层形态：数组，或 `{records|items|entries|rows|data:[...]}`；其他 dict 视为「值→记录」映射。
- `keys` 是该表前 2000 条记录的字段并集（最多 40 个），用于回答"这张表能查什么"，不保证完整。
- 记录内数值统一 `{v, unit}`（CONVENTIONS「00-data 口径」）；索引不展开 unit。

## evidence[] / evidence_dirs[] — 证据层
- `evidence[]` 逐文件：`{path, kind, bytes, desc}` + `.jsonl` 有 `lines`、`.json` 有 `entries`。
- `evidence_dirs[]`：`{path, kind, desc, files, bytes}`，`kind ∈ {claims, probes, bench}`。
- **probes/** 目前 0 文件（目录已建）——探针脚本落地后会自动出现，`files`>0 才算证据层可用。
- `claims.jsonl` 每行一条可复测断言；`claims-excluded.jsonl` 为剔除项（同样计数，勿混用）。

## 使用示例
1. **路由**：先读 `counts.by_domain` 判断哪个域有内容；再按 `domains[].articles[].tokens` 选要载入的篇目，避免整库塞进上下文。
2. **取值**：文章里的数字若标 `见 DATA#blocks`，用 `data[]` 找表 → 读该表 `#fragment`（`#id=duo`）。
3. **门禁**：`build_index.py --check` 退出码 1 = index.json 过期（剔除 `generated` 后比对）；CI 里与 `check_kb.py` 串行跑。
4. **MCP**：检索走 kb.py（FTS+向量），index.json 只做导航与计数，不参与相似度。

## 与门禁的分工
| 关注点 | check_kb.py | build_index.py |
|---|---|---|
| frontmatter 完整性 / 七段 / 来源标记 | ✅ 逐篇 | ❌ |
| 数字与 00-data 冲突 | ✅ `--audit`（num_audit.py） | ❌ |
| 全库总览 / 计数 / 导航 | ❌ | ✅ |
| 00-data 记录与 keys | 仅校验 data: 引用 | ✅ 汇总 |
