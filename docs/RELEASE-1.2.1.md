# 1.2.1 — 四包发布

四个 zip，按「谁要用什么」分。下载同一个版本号的四个文件到同一个目录，
`sha256sum -c SHA256SUMS.txt` 能验完整性。

| 包 | 大小 | 谁用 | 里面是什么 |
|---|---|---|---|
| `mlog-agent-1.2.1-toolchain.zip` | 1.32 MB | 写 mlog 的人、CI | `tools/ rules/ data/ tests/ docs/ scenes/ bench/ deploy/` + `gate.py` + 清单 |
| `mlog-agent-1.2.1-knowledge.zip` | 1.35 MB | 查事实的人 | `knowledge/`（130+ 篇 + 12 张 canonical 表 + 85 条 claim）+ `data/game/` |
| `mlog-agent-1.2.1-skills.zip` | 0.61 MB | Agent 宿主 | 两个可拖进 `~/.dsh/skills/` 的技能包 |
| `mlog-agent-1.2.1-mcp.zip` | 0.88 MB | 部署 MCP 服务的人 | `tools/ rules/ data/ deploy/` + 部署文档，**不含 tests 与知识库** |

## 这一版新做的

1. **HTTP 传输**（`tools/mlog_mcp_http.py`）：`POST /mcp` 回答 JSON-RPC（单包或批次），
   `GET /health` 给反代和容器探针用。工具表只有一份 —— 它 import `mlog_mcp.handle()`，
   所以 stdio 和 HTTP 永远是同一组 15 个工具。
2. **第四份包 `mcp`**：只有服务端要的东西。`deploy/` 里带 systemd unit、Dockerfile
   （非 root、`HEALTHCHECK` 打 `/health`）和三段反代写法（Caddy / nginx / 直接跑）。
3. **安全边界写死在代码里**：默认绑 `127.0.0.1`；绑非回环且没有 `--token` 又没 `--insecure`
   时**拒绝启动**（退出码 2）。理由直白：`mlog_sim` 执行调用方发来的程序，`world_js`
   在游戏服务端求值 JS —— 没有鉴权的 mlog 执行器就是远程代码执行。
4. **`tests/mcphttp/`（11 项，不需要 JVM）**：状态码、通知 202 空包、失败工具调用
   （200 + `isError`，不是 HTTP 错误）、未知方法 `-32601`、坏 JSON `400`、批次回列表、
   `GET /mcp` 405、鉴权 401、非回环无令牌拒启。
5. **`gate.py` 29 步**（新增 `mcphttp`）；`docs/MCP部署.md` 写清传输形状、三种部署方式、
   运行时降级（没有 JVM 时哪些工具回 `unsupported_environment`）、客户端配置与运维。
6. `mlog_mcp.handle()` 换成可注入的 sink（`emit`），stdio 路径行为不变 —— 这是为了让
   HTTP 层复用同一份应答格式，而不是复制一份 `_reply`。

## 验一遍

```bash
# 工具链：纯 Python，没有 jar 也能跑完该跑的
unzip mlog-agent-1.2.1-toolchain.zip -d toolchain && cd toolchain
python gate.py                      # 期望 16 PASS / 11 SKIP / 0 FAIL（Java 与知识库不在包里）
python tests/run_tests.py           # 期望 50/50

# 知识库叠上去，两个依赖它的步骤就会由 SKIP 变 PASS
unzip ../mlog-agent-1.2.1-knowledge.zip -d .
python gate.py --only claims --only bundles

# MCP：解开就能起，不需要写代码
unzip mlog-agent-1.2.1-mcp.zip -d mcp && cd mcp
python tools/mlog_mcp_http.py --port 8765 --token "$(python -c 'import secrets;print(secrets.token_urlsafe(24))')"
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/health
```

## 已知边界

* 镜像/包里**没有 JVM**：`mlog_sim`、`mlog_validate` 的仿真段、`mlog_diff`、
  `mindcode_compile` 会回 `unsupported_environment`。要它们就把运行时挂上来
  （`MLOG_JAR` / `MLOG_JAVA` / `MINDCODE_JAR` / `MINDCODE_JAVA`；mlogsim 要 Java 21+，
  Mindcode 3.19.3 要 Java 22+）。
* 不做服务端推送（`GET /mcp` 是 405）。这套工具都是请求/响应，SSE 会承诺兑现不了的东西。
* 不做多租户隔离与限流：一个令牌、一个进程、一个 `out/`。要多租户就一个容器一份。
* 发行副本里的本地路径已被改写成 `<repo>/<home>/<stage>`（证据日志里原来是个人绝对路径，
  仓库内保留原样 —— 那是证据原件）。
* `TextureMDT`（贴图素材）不在包里：它比本仓库大，且 `gen_name_docs.py` /
  `gen_game_aliases.py` 已在有官方语言包时不需要它。
