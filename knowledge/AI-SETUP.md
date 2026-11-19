# Handing this knowledge base to an AI (AI-SETUP)

> Three ways to wire it in, ordered from the least to the most environment you can change. Any one of them brings an AI to "mechanics expert" level.

## Option A: feed it directly (zero configuration, fastest)

Give the model these two files as context or attachments:

1. `KB.md` (entry point, protocol, Top 14 traps, directory map)
2. `08-evidence/CHEAT.md` (the cheat card: 40 traps + 30 numbers + 20 routes)

When you need to dig deeper, have the AI read the matching article itself via the paths in `index.json` (each is 130-250 lines with a fixed seven-section structure: In one sentence / Rules·formulas / Numbers / Source anchors / Measurements and counter-examples / Common misconceptions / Related).
For data questions read `00-data/*.json` directly (machine-readable, with id and src).

## Option B: local retrieval (recommended; can run the 300-question evaluation)

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

Retrieval chain: dense (bge-small-zh ONNX) + SQLite FTS5 trigram BM25 + RRF fusion, with an optional bge-reranker; a single query takes 70-280 ms (depending on the candidate count).

Three query-time switches are on by default (all inside `tools/kb.py`, and can be turned off with environment variables):

| Switch | Default | Effect |
|---|---|---|
| `KB_ONLY_KNOWLEDGE` | 1 | search `knowledge/` only (applies when no `kind` is passed); keeps off-library code chunks from stealing ranking slots |
| `KB_DEDUPE_FILE` | 1 | among adjacent chunks of the same file keep only the highest-scoring one |
| `KB_ASCII_BOOST` | 1 | up-weights ASCII identifiers in the query (`@counter`, `ucontrol`); fixes mixed Chinese-English queries |
| `KB_CANDIDATES` | 40 | fetch 40 candidates first, then rerank/dedupe and finally cut to k |

Together the three raise the 300-question hit@1 from 45% to **59.0%** and hit@6 to **85.0%**; turning any one of them off lowers the score noticeably.

## Option C: MCP service (for agents)

The repository already ships an MCP service (the MCP entry point of `tools/kb.py`) exposing `kb_search(query, k)`. Once an agent mounts it, the model drives retrieval itself, which saves more context than feeding files by hand.

- config example (`~/.dsh/profiles/default/cordis.patch.yml`): `command: python`, `args: ["tools/kb.py", "serve"]`. The working directory of the MCP subprocess is not under your control, so fill in an absolute path for your own machine if you need one (do not copy an old drive letter).
- **after changing `kb.py` you must restart the MCP process**: `serve()` is a single-process stdin loop that warms up the embedder at startup and has no reload. A data update (`out/_kb/kb.sqlite3`) needs no restart.
- use `kind="data"` for data tables and `kind="code"` for out-of-library scripts (that bypasses the knowledge-only hard filter).

## System prompt (paste-ready)

```text
你是 Mindustry 机制专家。回答规则：
1. 先检索再回答：优先 00-data/*.json 查数值，其次文章正文，最后 08-evidence/claims.jsonl。
2. 每个数字给来源：00-data 的 id，或 文件:行。没有来源就不说。
3. 单位写清：/tick 还是 /s（×60）、tile 还是 px（×8）；数值默认 v160.7，语义按 v159.3 源码。
4. 版本冲突并列写，例如 toxopid 护甲 22（v160.7 jar；v159.3 源码 13）。
5. 回答前读该主题的「常见误解」小节，先反驳直觉再下结论。
6. 不确定就标 conf: U 并说明缺哪一步验证。
```

## Checking whether the AI really learned it (300 questions)

```powershell
python knowledge\tools\eval_kb.py --kb knowledge --root <仓库根> --engine kb -k 6
python knowledge\tools\eval_kb.py --kb knowledge --root <仓库根> --engine lexical -k 6
```

- question bank: `08-evidence/bench/questions.jsonl` (300 questions, 12 domains × 25, difficulty 72/156/72).
- also `questions-derive.jsonl` (cross-source derivation questions, not part of the main metric) and `subset_report.py` (split by source_kind).
- **reference results (A+B+C all on, k=6, published library v1.2)**: coverage 100% / hit@1 **59.0%** / hit@6 **85.0%** / mrr 0.685 / strong@6 93.4% / off-library slots 0%; of which the 22 formula-derivation questions score 72.7% and the 24 cross-source derivation questions 95.8%.
- baseline: lexical 45.3 / 78.7; hybrid with the three switches off 45.0 / 67.5 (off-library documents take 52% of the slots). Evolution and ablations are in `bench/README.md` §10.

## In one sentence

Feeding `KB.md` + `08-evidence/CHEAT.md` gets you to "makes no beginner mistakes"; only options B/C get you to "can derive and can be verified".