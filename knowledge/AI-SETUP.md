# 把这份知识库交给 AI（AI-SETUP）

> 三种接入方式，按你能改动多少环境从低到高排列。任选其一即可让 AI 具备「机制高手」水平。

## 方式 A：直接投喂（零配置，最快）

把这两个文件作为上下文/附件给模型：

1. `KB.md`（入口、协议、陷阱 Top 14、目录地图）
2. `08-evidence/CHEAT.md`（40 陷阱 + 30 数字 + 20 路由的速查卡）

需要深挖时，让 AI 按 `index.json` 里的路径自己读对应文章（每篇 130-250 行，七节结构固定：一句话 / 规则·公式 / 数值 / 源码锚点 / 实测与反例 / 常见误解 / 相关）。
数据问题直接读 `00-data/*.json`（机器可读，带 id 与 src）。

## 方式 B：本地检索（推荐，可跑 300 题评测）

```powershell
# 1) 建库（KB_ROOT 必须是仓库根，不是 knowledge 目录！）
$env:KB_ROOT='<仓库根>'
$env:KB_DIR='<仓库根>\out\_kb_build'
python knowledge\tools\kb.py build
# 2) 发布（MCP 持句柄时不能直接覆盖，必须 backup 原地重写）
python knowledge\tools\publish_db.py out\_kb_build\kb.sqlite3 out\_kb\kb.sqlite3
# 3) 校验
python knowledge\tools\dbstat.py out\_kb\kb.sqlite3
python knowledge\tools\smoke_kb.py --db out\_kb\kb.sqlite3 --questions knowledge\08-evidence\bench\questions.jsonl
```

检索链：dense（bge-small-zh ONNX）+ SQLite FTS5 trigram BM25 + RRF 融合，可选 bge-reranker；单次查询 70-280 ms（视候选数）。

默认开启三个查询期开关（都在 `tools/kb.py` 里，可用环境变量关掉）：

| 开关 | 默认 | 作用 |
|---|---|---|
| `KB_ONLY_KNOWLEDGE` | 1 | 只检索 `knowledge/`（不传 `kind` 时生效），挡住库外 code chunk 抢排序 |
| `KB_DEDUPE_FILE` | 1 | 同一文件的相邻 chunk 只保留最高分那条 |
| `KB_ASCII_BOOST` | 1 | 查询里的 ASCII 标识符（`@counter`、`ucontrol`）加权，修中英混排 |
| `KB_CANDIDATES` | 40 | 先取 40 条再重排/去重，最后截 k |

三者合计把 300 题 hit@1 从 45% 提到 **59.0%**、hit@6 到 **85.0%**；关掉任一项都会明显下降。

## 方式 C：MCP 服务（给 Agent 用）

仓库已带 MCP 服务（`tools/kb.py` 的 MCP 入口），暴露 `kb_search(query, k)`。Agent 侧挂上后，检索由模型自己发起，比手工投喂更省上下文。

- 配置示例（`~/.dsh/profiles/default/cordis.patch.yml`）：`command: python`，`args: ["tools/kb.py", "serve"]`。MCP 子进程的工作目录不受控，若需要绝对路径请按本机实际仓库位置填写（不要照抄旧盘符）。
- **改过 `kb.py` 必须重启 MCP 进程**：`serve()` 是单进程 stdin 循环、启动即预热 embedder，没有 reload。数据更新（`out/_kb/kb.sqlite3`）不需要重启。
- 查数据表用 `kind="data"`，查库外脚本用 `kind="code"`（会绕过只查 knowledge 的硬过滤）。

## 系统提示词（可直接粘贴）

```text
你是 Mindustry 机制专家。回答规则：
1. 先检索再回答：优先 00-data/*.json 查数值，其次文章正文，最后 08-evidence/claims.jsonl。
2. 每个数字给来源：00-data 的 id，或 文件:行。没有来源就不说。
3. 单位写清：/tick 还是 /s（×60）、tile 还是 px（×8）；数值默认 v160.7，语义按 v159.3 源码。
4. 版本冲突并列写，例如 toxopid 护甲 22（v160.7 jar；v159.3 源码 13）。
5. 回答前读该主题的「常见误解」小节，先反驳直觉再下结论。
6. 不确定就标 conf: U 并说明缺哪一步验证。
```

## 验证 AI 是否真的学会了（300 题）

```powershell
python knowledge\tools\eval_kb.py --kb knowledge --root <仓库根> --engine kb -k 6
python knowledge\tools\eval_kb.py --kb knowledge --root <仓库根> --engine lexical -k 6
```

- 题库：`08-evidence/bench/questions.jsonl`（300 题，12 域 × 25，难度 72/156/72）。
- 另附 `questions-derive.jsonl`（跨源推导题，不进主指标）与 `subset_report.py`（按 source_kind 拆分）。
- **参考结果（A+B+C 全开，k=6，已发布库 v1.2）**：coverage 100% / hit@1 **59.0%** / hit@6 **85.0%** / mrr 0.685 / strong@6 93.4% / 库外槽 0%；其中公式推导题 22 题 72.7%、跨源推导题 24 题 95.8%。
- 对照：lexical 基线 45.3 / 78.7；未开三开关的 hybrid 45.0 / 67.5（库外文档占 52% 的槽）。演进与消融见 `bench/README.md` §10。

## 一句话

投喂 `KB.md` + `08-evidence/CHEAT.md` 就能到「不犯低级错误」；接方式 B/C 才能到「能推导、可验证」。