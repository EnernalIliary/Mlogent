# Deploying the MCP server

Three files here, one shape: the repo sits at `/opt/mlogent`, a single Python
process answers on a local port, and something in front of it handles TLS.

Why the process is on `127.0.0.1` even when clients are remote: **an
unauthenticated mlog executor is remote code execution.** `mlog_sim` runs a
program the caller sends, and `world_js` evaluates JavaScript inside the game
server. Bind it to a public interface and you are handing out an interpreter.
So: loopback bind, token required, reverse proxy for TLS.

## Bare metal (systemd)

```bash
sudo useradd --system --create-home --uid 10001 mlog
sudo git clone --depth 1 https://github.com/EnernalIliary/Mlogent /opt/mlogent
sudo chown -R mlog:mlog /opt/mlogent

sudo install -d -m 750 -o mlog -g mlog /etc/mlogent
printf 'MLOG_MCP_TOKEN=%s\n' "$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')" \
  | sudo tee /etc/mlogent/mcp.env >/dev/null
sudo chmod 600 /etc/mlogent/mcp.env

sudo cp /opt/mlogent/deploy/mlogent-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now mlogent-mcp
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8765/health
```

`systemctl status` and `journalctl -u mlogent-mcp -f` are the two commands you
will use; the unit logs one line per request unless `--quiet`.

## Container

```bash
docker build -f deploy/Dockerfile -t mlogent-mcp .
docker run -d --name mlogent-mcp -p 127.0.0.1:8765:8765 \
  -e MLOG_MCP_TOKEN="$TOKEN" -v "$PWD/out:/opt/mlogent/out" mlogent-mcp
```

The image has no JVM, so the executor-backed tools answer
`unsupported_environment`. To get them, mount a runtime and point at it:

```bash
docker run ... \
  -v /srv/mindustry:/opt/mlogent/runtime:ro \
  -e MLOG_JAR=/opt/mlogent/runtime/server-release.jar \
  -e MLOG_JAVA=/opt/mlogent/runtime/jdk-21/bin/java \
  -e MINDCODE_JAR=/opt/mlogent/runtime/mindcode-3.19.3.jar \
  -e MINDCODE_JAVA=/opt/mlogent/runtime/jdk-25/bin/java \
  mlogent-mcp
```

`mlogsim` needs Java 21+, Mindcode 3.19.3 needs Java 22+ (class file 66). Both
answer `unsupported_environment` when they cannot find a runtime — the server
stays up, the static tools keep working.

## Reverse proxy

Caddy, which is the shortest correct config:

```
mcp.example.com {
    reverse_proxy 127.0.0.1:8765
}
```

nginx equivalent, note the `proxy_buffering off` (a long `mlog_diff` should not
be held in a buffer until it finishes):

```nginx
location / {
    proxy_pass         http://127.0.0.1:8765;
    proxy_http_version 1.1;
    proxy_set_header   Host $host;
    proxy_read_timeout 300s;
    proxy_buffering    off;
}
```

## Client side

Any MCP client that speaks streamable HTTP needs just the URL and the header:

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

A client that only does stdio can still reach a remote server through a bridge,
but if the client runs on the same machine, prefer stdio directly
(`python tools/mlog_mcp.py`): no token, no port, no proxy.

## What is not here

* No server→client streaming (`GET /mcp` is 405). Every tool in this server is
  request/response; an SSE endpoint would advertise pushes that never happen.
* No per-user isolation. One token, one process, one scratch directory. If you
  need tenants, run one container per tenant.
* No rate limiting. Put it in the proxy if you need it (`limit_req` in nginx).
