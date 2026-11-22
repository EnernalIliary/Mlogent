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

## Versioned releases

When MCP code runs from `/opt/mlogent-releases/<release>` while the live world
and runtime data stay under `/opt/mlogent`, link each release's `out/` to the
shared runtime directory before starting or switching the service. The world
tools resolve `out/` relative to their installed code, so `WorkingDirectory`
alone does not make a versioned release see the live world's handshake, server
jar, or saved runtime data.

```bash
RELEASE=/opt/mlogent-releases/<release>
test -d "$RELEASE/tools" && test -d /opt/mlogent/out
if [ -L "$RELEASE/out" ]; then
  test "$(readlink -f "$RELEASE/out")" = "$(readlink -f /opt/mlogent/out)"
elif [ -e "$RELEASE/out" ]; then
  echo "refusing to replace existing release out/" >&2
  exit 1
else
  ln -s /opt/mlogent/out "$RELEASE/out"
fi
test "$(readlink -f "$RELEASE/out")" = "$(readlink -f /opt/mlogent/out)"
```

Keep this link when activating each new release; do not copy or duplicate
`out/`, since the world server and MCP process must share the same live state.

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

The `mlog_sim` marker preview uses the JVM's `java.desktop` module in headless
mode. On Linux, install Fontconfig and a system font for labels. The Docker
image provides Fontconfig and DejaVu Sans. Install a CJK font on the host or
inside the container if you need Chinese, Japanese or Korean labels in PNGs.

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

### Optional ChatGPT interfaces

UI is disabled by default. Add `--enable-ui` to the HTTP service command to
expose separate MCP Apps tools and HTML resources:

```bash
python tools/mlog_mcp_http_profiles.py --bind 127.0.0.1 --port 8765 \
  --token "$MLOG_MCP_TOKEN" --enable-ui
```

Without the flag the original tools keep their existing responses. With UI
enabled, `mlog_gen` and `mlog_inject` automatically open a pending author form
when unsigned input has a safe signature slot but no explicit author. Such
requests are delivered only after form submission; a process-wide author default
does not bypass this step. Inputs with no safe signature slot are generated or
injected directly without a signature, even if no author was supplied. The
result has `signed: false` and a warning, and the UI labels it unsigned. No
signature-carrier instructions are appended. A full `jump <target> always 0 0`
can reuse the final zero placeholder; custom nonzero/string operands are not
overwritten. Invalid existing signatures still fail instead of being bypassed.
Explicit-author delivery and injection previews render their results
in the same component. `mlog_signature_request` can also open a form directly
or reopen the `request_id` returned in a pending result; `world_dashboard` opens a
read-only status/player dashboard. `mlog_signature_submit` is app-only and
signs the saved request after form submission. The simpler
`mlog_mcp_http.py` also supports the flag and signature form; use the profiles
entry point for the world dashboard, which needs its world tools.

UI tools use the existing bearer/OAuth connection. A profile must permit the
UI tool and its underlying operation: `mlog_gen`/`mlog_inject` for signing,
both `world_status` and `world_players` for the dashboard. The `runner` profile
with `tools: ["*"]` already permits them. No credentials are placed in HTML.

Client tool catalogs must include the new definitions: `mlog_gen` has an
`author` input and, with the flag enabled, signature UI metadata. Reading
`mlog_doctor` only checks the backend; its result now names the available UI
tools, while `world_dashboard` is the tool that opens the world interface.

Signature requests expire after 15 minutes or a service restart. Inputs are
snapshotted before displaying the form; submission cannot substitute a different
program or change an existing signed author. No-slot inputs opened explicitly
in a form can be submitted without an author and are labeled unsigned. Repeated
submission of the same request/author returns the saved delivery. Form authors
do not alter the process-wide author defaults used by legacy tools.

Example call to open a form (it creates no blueprint until submission):

```json
{
  "name": "mlog_signature_request",
  "arguments": {
    "operation": "mlog_gen",
    "arguments": {
      "logic": "set n 42\njump 0 always 0\n",
      "name": "Example"
    }
  }
}
```

Clients that support MCP Apps read `ui://` resources and render them in a
sandbox. Text-only clients still receive the pending request and can call the
original generation tools. The HTTP authentication gate covers resources too;
turning on UI does not grant additional world or generation permissions.

Validation: `python tests/mcphttp/run_mcp_http_tests.py` covers transport,
permissions, request expiry, snapshotting and signed delivery.
`node tests/mcphttp/run_apps_ui_tests.js` exercises a real browser against the
local HTTP server (requires Playwright; set `CHROMIUM_PATH` and `PYTHON` when
needed). Its host harness tests MCP Apps messaging, not the ChatGPT product UI.

Protocol references: [MCP Apps](https://apps.extensions.modelcontextprotocol.io/api/documents/overview.html),
[ChatGPT UI](https://developers.openai.com/plugins/build/chatgpt-ui).

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
