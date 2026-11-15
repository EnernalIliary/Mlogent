# 08-evidence 索引（文件名以 `_` 开头 ⇒ 门禁 check_kb.py 不当作文章扫描）

证据层不放文章，只放**可机读的断言-证据对**。文章里的每条结论都应在 `claims.jsonl` 里找得到对应 `id`。

## 文件清单

| 文件 | 条数 | 说明 |
|---|---|---|
| `claims.jsonl` | **85** | 收录的断言：L1 全 31 + L2 27 + L3 6 + S 18，另 L2-32/33/34（游戏内部结构） |
| `claims-excluded.jsonl` | **17** | 排除的断言（模组传输 4 + 面板/工具开发 13），字段与 claims 完全相同 |
| `bench/` | 13 文件 | 问答基准生成脚本（`_gen_d1.py` 等），脚本开头写死答案与出处 |

## 字段

```json
{ "id": "L1-23", "area": "exec", "claim": "…断言原文…", "expect": "…预期…",
  "how": "S：…；E：…（探针/文件）", "verdict": "✅", "evidence": "判定列原文：…｜…",
  "ver": ["v160.7"], "conf": "E", "src": ["docs/断言表.md:19", "docs/验证记录.md:11"] }
```

| 字段 | 取值 | 含义 |
|---|---|---|
| id | L1-01…L1-31 / L2-01…L2-47 / L3-01…L3-06 / S-01…S-18 | 继承 `docs/断言表.md` 的原始编号，**不重编** |
| area | exec / runtime / session / scene | 执行语义 / 引擎运行时 / 会话渠道 / 场景机制 |
| verdict | ✅ / ⚠️ / ❌ | 成立 / 存疑或未跑 / 不成立 |
| conf | S / E / U | 源码行号 / 真机实测 / 未验证（I 未使用，见下） |
| src | `docs/断言表.md:行`、`docs/验证记录.md:行` | 行号可直接跳转复核 |

## verdict 归一化规则（原表「判定」列文字 → 枚举）

| 判定列原文含 | verdict | 备注 |
|---|---|---|
| ✅ | ✅ | 原样 |
| ❌ 或单独一个 `E` | ❌ | `E` 表示 Experiment 失败 |
| ⚠ 或 UNRUN | ⚠️ | UNRUN = 未跑 |
| 空白/无判定列（S 表多数） | ✅ | 仅当 `how` 里有 PASS 或实测；否则 ⚠️ |

`evidence` 字段一律以「判定列原文：…」开头，保留原始文字便于回溯；S-14..S-18 判定为 E（真机实测过），S-02..S-13 的判定列写的是**判定标准**不是结论 ⇒ 归 ⚠️ 或依验证记录定。

## 统计（生成时实测）

| 维度 | 分布 |
|---|---|
| verdict | ✅ 76 / ⚠️ 6 / ❌ 3 |
| conf | E 70 / S 6 / U 9 |
| area | exec 31 / runtime 30 / session 18 / scene 6 |
| 有验证记录配对 | **77 / 85 = 90.6%** |
| 无验证记录 | 8 条：L1-25 L1-26 L1-28 L1-29 L1-30 L1-31 S-01 S-12（其证据散落在验证记录的非表格章节，`src` 只有断言表行号） |

## 为什么是 85 条而不是 102

`docs/断言表.md` 表头自述 188 条，去重后 202 个 id。CONVENTIONS 硬规则 5/6 禁止写产品/工具开发与模组内容，因此：

| 排除批次 | id | 理由 |
|---|---|---|
| 模组传输 | L2-28, L2-29, L2-30, L2-31 | Rhino codegen / HTTP sidecar / settings 分类 / URL.openConnection（模组侧） |
| 工具与产品开发 | L2-35…L2-47（13 条） | 审查箭头、框选、F2 清单、F3 面板、作业队列、provider prompt、undo 快照、写前冲突 |

被排除的 L2-32/33/34 保留：`getLinkName` 的 core-shard→shard 命名、`LogicBlock.config` 写入载荷坐标、`LogicDialog.executor` 包私有 —— 属引擎内部结构，不是工具开发。

## 用法

```bash
# 找某条断言 grep -i '"id": "L1-25"' claims.jsonl
# 统计（需要 jq） jq -r .conf claims.jsonl | sort | uniq -c
# 只看不成立的 grep '"verdict": "❌"' claims.jsonl
```

## 需要警惕的地方

- `claims.jsonl` 是**原始证据层**，不是答案层：写文章时应引用 `id` 并复述结论，不要直接粘贴整行。
- 9 条 `conf: U` 的断言不能进 KB 答案路径（CONVENTIONS 规定）。
- 有 2 条 ❌ 源于**文档/旧结论被推翻**（如 L1-25 `op select`、L2-22 `status apply/clear`），它们仍然有价值：作为「常见误解」的反例来源。
