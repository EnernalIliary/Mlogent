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

### Empty-world MCP work

`autoPause=true` remains the idle policy. Read-only queries and isolated
`mlog_sim` calls do not wake or change the online map. MCP world execution
handlers, world-backed scenarios/explorations and differential tests hold an
execution lease. On an empty server the lease saves the current world before
switching to `大肥鱼的调试世界` (only if not already there), then runs the world.
The map switch rechecks player count on the game thread; online players prevent
automatic switching. Explicit lifecycle/map/pause commands retain their own
semantics, and destructive handlers acquire their lease only after the existing
veto buffer finishes. Once a task returns or throws, its lease is released and
the empty world pauses. The game owns a 60-second expiry renewed every 15 seconds,
so a crashed MCP worker cannot hold the world awake forever. A lease covers
the tool's execution lifetime, not arbitrary background game logic after return.
The selected debug map remains loaded after the task; the previous map has a
timestamped `config/saves/mcp-before-work-*.msav` backup.

The public `reader` profile may additionally allow inline `mlog_gen`,
`mlog_inject` and `mlog_sim`. Set `rpm: 30`, `work_rpm: 10` and
`simulation_limits: {"ticks": 600, "steps": 1200}` in its private users.json
profile. Generation, injection and simulation share the work bucket; other
tools use the independent normal bucket. Signature form opening uses the
normal bucket, while submission uses the work bucket. Enable
`mlog_signature_request` and `mlog_signature_submit` for the author form.
Limits apply per principal; public guest OAuth sessions share the guest quota.
These public work tools reject server input/output paths, scene uploads and
live-world projection feeds. Runner permissions and its total quota are
unchanged. Tool discovery advertises the same inline-only inputs and limits
enforced at dispatch.

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
when unsigned input has no explicit author (unless `allow_unsigned=true`). Such
requests are delivered only after form submission; a process-wide author default
does not bypass this step. Signing is strict by default: inputs without a safe
slot return an error and no blueprint. Only explicit `allow_unsigned=true`
permits unsigned delivery, marked with `signed: false` and a warning. No
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
program or change an existing signed author. Form submissions require an author;
no-slot submissions display a signing failure without delivering a blueprint. Repeated
submission of the same request/author returns the saved delivery. Form authors
do not alter the process-wide author defaults used by legacy tools.

Generation and injection remove known editor placeholders only from provably
unused trailing operand positions: the exact unquoted tokens `true`, `false`,
`a`, and `b`. Other names may be declarations, so they are retained, as are
numbers, strings, unknown commands, interior operands and signed programs.
Cleanup does not add/remove instructions or change jump destinations. Results
report removals in `parameter_cleanup`; a signature form snapshots and displays
the cleaned code before confirmation.

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
# On-demand game world (Linux)

`tools/world_sleep.py` can own `world_server.py` instead of keeping the JVM
running. Defaults: public TCP/UDP 6567, private backend 16567, 300 seconds empty
before saving and stopping. It retains the five newest generated hibernation
saves. Existing manual saves are untouched.

Install the firewall helper from Mlogent-Ops as `/etc/mlogent/world-sleep-firewall.sh`
and run it as root on every service start: the native
backend binds wildcard addresses and must not be reachable externally. The
provided script blocks remote IPv4/IPv6 TCP/UDP access to 16567 while allowing
loopback. Keep that script consistent with `--backend-port` if changing it.

Example systemd service override (adjust Python/Java and checkout paths):

```ini
[Service]
Type=notify
NotifyAccess=main
WorkingDirectory=/opt/mlogent
ExecStartPre=+/bin/sh /etc/mlogent/world-sleep-firewall.sh
ExecStart=
ExecStart=/opt/uv-python/cpython-3.12-linux-x86_64-gnu/bin/python3.12 /opt/mlogent/tools/world_sleep.py --java /opt/jre21/bin/java --idle-seconds 300
KillMode=mixed
TimeoutStopSec=75
```

Before migration, validate an empty-world save and seed `out/_world/sleep-state.json`
with its `save` basename, cached status/maps, and serialized kick packet. Do not
replace a live service with players online. A cold supervisor with no saved state
hosts the default debug map on the first request.

The frontend immediately performs the ArcNet TCP/UDP handshake, waits for the
shared background boot, performs the backend handshake with its own ID, restores
the real peer IP in `NetConnection.address`, then relays opaque game packets.
The backend's private port is never advertised. Test the active Mindustry build
after upgrading: the packet IDs/handshake are version-sensitive.

Clients can usually stay on the original connection. The proxy's boot wait is
24 seconds, leaving time within the vanilla client's approximately 30-second
world-loading deadline; slower startup returns the configured custom kick.
An individual client's timeout does not cancel shared startup. Vanilla clients
queue ordinary UI messages until loading completes, so the waking text is
available in server discovery and the timeout kick, not a custom loading overlay.

Exact discovery/kick wording is defined in `world_sleep_protocol.py`:

- Sleeping title: `[gray]Mlogent.execute(Mindustry);[]`
- Running title: `Mlogent.execute(Mindustry);`, with `[#rrggbb]` colors interpolated from `#8abcd1` to `#ffb6c1`. Letters retain individual colors; punctuation inherits the preceding color when needed to fit the 255-byte discovery-name limit. The proxy preserves the full name despite the native 100-byte name truncation.
- Sleeping description: `大肥鱼休眠中，可发起连接请求以唤醒。首次连接需要约 20 秒。`
- Map: the actual map cached before hibernation (default debug map only if no cached name exists).
- Waking/timeout: `正在唤醒大肥鱼，这通常需要几十秒，如果链接超时，可以稍等再次尝试链接。`

Private control is `out/_world/sleep.sock` (Unix, mode 0600). `world_client` uses
it automatically; supplying an explicit handshake bypasses it for the owner.
Status/maps/player queries are cached while asleep and never wake the JVM.
World work wakes it; the existing `world_work` game lease controls ticking and
empty-only debug-map selection. Players, connecting clients, work leases, and
pending `/abort` actions prevent idle shutdown. Saving/occupancy checks/closing
the game listener run together on the game thread. Failed inspection/save keeps
the game running. Native `SaveIO.load` restores the snapshot instead of Wayzer's
overridden console `load`, which treats saves as maps and loses their names.
`world_start` without overrides wakes a manually stopped managed world.

`world_stop` atomically stops an already sleeping managed world immediately,
without starting the JVM or registering an in-game veto. A running world keeps
the 60-second player veto period. Once approved, shutdown validates a new snapshot
and publishes it as the next startup's recovery point before terminating the JVM.
Save failure leaves the game running; recovery-pointer publication failure keeps
the previous pointer and reopens the listener. A completed stop returns
`status: stopped`, `manualStop: true`, and (for a running world) the recovery save
basename. Repeated stops of a sleeping/stopped world are immediate and idempotent.

Normal service termination checkpoints the active world before stopping its
owned process group. `KillMode=mixed` is essential: `control-group` sends SIGTERM
to the JVM before the supervisor can save. MCP-only updates need not restart the
world supervisor. Background work that outlives its MCP handler still requires
an explicit managed lease; enabling a map processor alone does not pin the JVM.

Private administrative requests (same OS user/root only):

```python
import world_sleep_client as control
control.request({'op': 'supervisor_status'})
control.request({'op': 'idle_policy', 'idleSeconds': 300})  # runtime only, >=10
```

Rollback: remove the supervisor service override, stop the supervisor gracefully,
restore the original `world_server.py` ExecStart and restart. Remove the MCP
override too if reverting its source. Preserve `sleep-state.json` and its latest
snapshot; the original world entry point otherwise hosts the configured map
instead of resuming that snapshot. Frontend-only health probes do not prove the
world JVM is awake; use `world_status.sleepState`.

### Optional server-operations extension

Server maintenance lives in the independent Mlogent-Ops project: synchronization
policies, traffic/pressure diagnostics, incident-only flight recording, world
resource/heap drop-ins, firewall deployment helpers and benchmark reports.
The MCP/API/runtime and sleep protocol remain in this project.

`tools/world_ops_bridge.py` is the only policy-loading boundary. Install the
`mlogent-ops` package or set `MLOGENT_OPS_ROOT=/opt/mlogent-ops`. The owned
`out/_world/snapshot-profile.json` may also set `opsRoot` to that directory,
so an already-running supervisor's next wake finds the extension. Missing or
broken optional operations code falls back to native synchronization; it must
not prevent the core world service from starting.

Deploy the operations recorder and world resource settings from Mlogent-Ops,
not from this release's `tools/` or `deploy/`. The recorder uses the existing
local daemon protocol and never wakes an idle world just to collect data.
Operational thresholds and retention policy are documented in Mlogent-Ops.
