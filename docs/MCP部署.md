# 把 MCP 跑在服务器上

`tools/mlog_mcp.py` 说的是 stdin/stdout 上的 JSON-RPC —— 适合客户端和工具在同一台机器。
服务器上要的是另一种东西：一个常驻进程、很多客户端、一个别人能轮询的健康检查。
所以 `tools/mlog_mcp_http.py` 只加了**传输层**，没有第二份工具表：它 import `mlog_mcp.handle`，
同一个方法表回答两种传输。

## 传输形状

```
POST /mcp     JSON-RPC 请求或批次 → 200 带回包；通知（无 id）→ 202 空包
GET  /health  200 {"ok":true,"name","version","tools":16,"repo","uptime_s","pid"}
GET  /mcp     405 Allow: POST（这一版不提供服务端推送）
```

会话：`initialize` 的响应带 `Mcp-Session-Id`，之后的请求可以带回来，也可以不带
（这一版不做强制 —— 工具都是无状态的请求/响应）。

## 安全：先读这一段

**没有鉴权的 mlog 执行器就是一个远程代码执行入口。** `mlog_sim` 会执行调用方发来的程序，
`world_js` 会在游戏服务端里求值 JavaScript。所以：

- 默认只绑 `127.0.0.1`；
- 绑定非回环地址而没有 `--token` 时，进程**拒绝启动**（`--insecure` 才能绕过，别绕）；
- 容器里绑定 `0.0.0.0` 是必须的，所以 Dockerfile 自己加了 `--insecure`，但强制要求
  `MLOG_MCP_TOKEN`，没有就退出码 2。

```bash
TOKEN=$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')
python tools/mlog_mcp_http.py --port 8765 --token "$TOKEN"
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/health
```

## 三种部署方式

| 方式 | 文件 | 什么时候用 |
|---|---|---|
| systemd | `deploy/mlogent-mcp.service` | 一台常驻 Linux 机器，仓库在 `/opt/mlogent` |
| Docker | `deploy/Dockerfile` | 想连 JVM 一起隔离，或者多台同构部署 |
| 直接跑 | `python tools/mlog_mcp_http.py` | 局域网调试、ngrok 之类的临时隧道 |

三种都配 `deploy/README.md` 里的 Caddy / nginx 反代（TLS 由反代做，
长调用要把 `proxy_read_timeout` 放大、`proxy_buffering` 关掉）。

## 运行环境

镜像里**没有 JVM**，所以 `mlog_sim` / `mlog_validate` 的仿真段 / `mlog_diff` /
`mindcode_compile` 会回 `unsupported_environment`。要这些工具，挂一个运行时进去：

```bash
-e MLOG_JAR=/opt/mlogent/runtime/server-release.jar \
-e MLOG_JAVA=/opt/mlogent/runtime/jdk-21/bin/java \
-e MINDCODE_JAR=/opt/mlogent/runtime/mindcode-3.19.3.jar \
-e MINDCODE_JAVA=/opt/mlogent/runtime/jdk-25/bin/java
```

`mlogsim` 要 Java 21+，Mindcode 3.19.3 要 Java 22+（class 66）。
`mlog_extract` 的带标签 mlog 输出也可离线使用；选 `format: "mindcode"` 时需要 Mindcode 运行时。

找不到运行时时服务照常起、静态工具照常可用 —— 这是有意的降级，不是故障。

## 客户端接法

```json
{
  "mcpServers": {
    "mlog": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "headers": { "Authorization": "Bearer <token>" }
    }
  }
}
```

只支持 stdio 的客户端如果就在本机，直接用 stdio 版（`python tools/mlog_mcp.py`）更省事：
没端口、没令牌、没反代。

## 多用户权限档

默认的 `mlog_mcp_http.py` 使用单个 Bearer 令牌。需要给不同用户分配权限和限流时，
可以改用 `mlog_mcp_http_profiles.py`，监听参数、静态令牌和 `/mcp` 协议保持相同：

```bash
python tools/mlog_mcp_http_profiles.py --bind 127.0.0.1 --port 8765 --token "$MLOG_MCP_TOKEN"
```

它会合并 `mlog_mcp` 与可用的 `world_mcp` 工具，再按 `MLOG_USERS_FILE` 指向的 JSON 配置
过滤工具并限流。未设置该变量时读取 `/etc/mlogent/users.json`。配置包含 `profiles`、`users`
和可选的 `static_profile`；用户项用 `password_sha256` 保存授权口令的 SHA-256 摘要：

```json
{
  "static_profile": "runner",
  "profiles": {
    "reader": {"label": "只读", "rpm": 30, "tools": ["mlog_doctor", "mlog_check"]},
    "runner": {"label": "全权", "rpm": 120, "tools": ["*"]}
  },
  "users": [
    {"name": "guest", "profile": "reader", "password_sha256": "<sha256>"}
  ]
}
```

设置 `MLOG_OAUTH_PASSWORD` 后会启用 OAuth 2.1 授权码 + PKCE、动态客户端注册和刷新令牌。
OAuth 登录口令通过 `users` 表匹配，环境变量中的 `MLOG_OAUTH_PASSWORD` 对应 `runner` 档。
`MLOG_OAUTH_BASE` 指定发布的 issuer URL，`MLOG_OAUTH_STORE` 指定持久化状态文件；默认写入
仓库 `out/oauth_state.json`，文件权限为 `0600`。备份和迁移时保留该文件与 `out/` 数据。

`MLOG_USERS_FILE`、`MLOG_OAUTH_BASE`、`MLOG_OAUTH_STORE` 和 `MLOG_OAUTH_PASSWORD` 都应配置在
服务环境文件中，不要写入仓库。`/health` 的 `tools` 数量只统计 `mlog_mcp` 工具，完整权限过滤
结果以 MCP `tools/list` 为准。

## 运维

- 健康检查：`GET /health` 是**廉价**的（不探 JVM、不跑 doctor），可以每 10 秒打一次；
  要看执行器就调 MCP 工具 `mlog_doctor`。
- 日志：一行一请求，写 stderr；`--quiet` 关掉。systemd 下 `journalctl -u mlogent-mcp -f`。
- 并发：`mlog_sim` 在独立进程中执行，每次最多 45 秒。同一服务进程同时执行一个模拟，
  新的并发模拟请求返回 `simulation_busy`。其余 RPC 串行处理，模拟期间可继续调用。
- 电网：`mlog_sim` 的 `power=grid` 使用原版电网。`power_profile` 接收有限个
  `tick` 和 `power_per_second` 数值点，更新当前模拟中的沙盒电源。用法见 [工具说明](../tools/README.md)。
- 发布与回滚：记录部署包的 Git 提交或镜像摘要，并保留上一份已验证产物。MCP 的接口版本可通过
  `GET /health` 的 `version` 或 `initialize` 的 `serverInfo.version` 查询，部署包的来源可查
  `PACKAGE.txt`。升级后检查 `/health` 和 `tools/list`；需要回退时切回上一份产物。
- 蓝图历史：`mlog_inject` 的版本记录默认写到 `out/_mlog_revisions/`，格式为 `mlog-revision/v1`。
  部署容器时将此目录放在持久卷，或用 `MLOG_REVISION_DIR` 指向服务用户可写的持久路径。
  记录包含原蓝图和检查结果，服务切换版本时应保留并备份这份数据。记录当前由运维按需清理。
- 限额与隔离：反代可用 nginx `limit_req` 限制请求速率。profiles 入口按用户过滤工具并限流，
  但所有档位仍共享一个进程和 `out/` 目录，不提供文件系统租户隔离；需要隔离时按租户部署独立实例。

## 与 stdio 版的差别

| | stdio (`mlog_mcp.py`) | HTTP (`mlog_mcp_http.py`) |
|---|---|---|
| 客户端位置 | 同机 | 任意 |
| 鉴权 | 由启动它的进程决定 | Bearer token |
| 并发 | 单流 | 多连接，模拟与其他 RPC 分开执行 |
| 健康检查 | 无 | `GET /health` |
| 代码 | 当前 MCP 工具表 | 同一份 `handle()`，同一份工具表 |

测试在 `tests/mcphttp/`（不需要 JVM），覆盖传输、鉴权、模拟输入检查、超时和并发。
