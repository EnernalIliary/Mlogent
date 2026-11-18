# 1.2.2 — 服务器上的 MCP 也能查知识库

1.2.1 把 MCP 抬到了 HTTP 上；这一版补上它唯一缺的那块：**事实**。

## 加了什么

1. **`mlog_kb`（第 16 个工具）**：`{query, k, kind}` → `{count, hits[{path, heading,
   start, end, score, snippet}], mode: "keyword", note}`。`kind: "all"` 时把 `docs/` 也搜进去。
2. **`tools/kb_grep.py`（新模块，纯标准库）**：按标题切段、BM25 排序。分词刻意钝：ASCII 标识符
   整词 + 按 `-_.` 拆开，中文按二元组。冷跑 300 ms（读 6 MB Markdown），热跑 80 ms（索引按文件数
   与最新 mtime 缓存）。
3. **`mcp` 包带上 `knowledge/`**：不带的服务器只会老实回 0 条，那比没有这个工具更糟。
   包里可以删掉它 —— 删了 `mlog_kb` 就降级成「0 条」，其余 15 个工具照常。
4. **`mlog_doctor` 报 `knowledge: {present, root, sections}`**：先把「没有数据」和「没命中」区分开。

## 两个检索器，别混用

| | `tools/kb.py` | `tools/kb_grep.py` |
|---|---|---|
| 方式 | bge-small-zh 向量 + trigram BM25 + RRF（可选 cross-encoder 重排） | 词面 BM25 |
| 前提 | `fastembed` + 模型 + `build` 出 SQLite | 无，直接读 Markdown |
| 用在哪 | 本机查资料、评测集 | 部署出去的 `mlog_kb` |

质量上 `kb.py` 更好（语义近的也能中），但服务器不能假设有 embedding 模型；
`kb_grep` 对「链接名读档重算」这种精确问题反而更稳，因为它不会被向量稀释标识符。

## 验一遍

```bash
unzip mlog-agent-1.2.2-mcp.zip -d mcp && cd mcp
python tools/mlog_mcp_http.py --port 8765 --token "$TOKEN" &
curl -s -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"mlog_kb","arguments":{"query":"core-shard 中文名","k":3}}}' \
  http://127.0.0.1:8765/mcp
# 期望命中 knowledge/02-world/W14-name-blocks-industry.md
```

包里自检：`python tests/run_tests.py`（50/50）、`python gate.py --only kbgrep --only mcphttp`。

## 边界

* `mlog_kb` 是词面检索：同义改述（「核心」问「core」）不保证命中；要语义就本地跑 `kb.py`。
* 中文只做二元组，没有分词词典，所以很短的问句可能命中多个弱相关段落 —— `score` 是相对值，
  不是置信度。
* 仍然不做服务端推送、不做多租户隔离；令牌一个、进程一个、`out/` 一个。
