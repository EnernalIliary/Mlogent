#!/usr/bin/env python
"""mlog_mcp_http.py -- the MCP server over HTTP, for deployment on a server.

`mlog_mcp.py` speaks JSON-RPC over stdin/stdout, which is right when the client
and the tools live in the same place.  A server-hosted deployment needs the
opposite: one long-lived process, many clients, and a health check something
else can poll.  So this file adds a transport -- not a second tool surface.  It
imports `mlog_mcp.handle` and lets the same method table answer.

Transport shape (MCP "streamable HTTP", the simple part of it):

    POST /mcp     JSON-RPC request or batch; 200 with the reply, or 202 for
                  notifications (a notification has no id, so there is nothing
                  to say back)
    GET  /health  200 JSON: name, version, tool count, repo, uptime
    GET  /mcp     405 -- this build does not stream server->client messages;
                  every tool here is request/response, so SSE would be a
                  promise the tools cannot keep

Auth is a single bearer token (`--token` or `MLOG_MCP_TOKEN`).  Off by default so
that `127.0.0.1` works out of the box; turn it on the moment the bind address is
not loopback.  The process refuses to bind to a non-loopback address without a
token unless `--insecure` says otherwise, because an unauthenticated mlog
executor on a public port is a remote code execution endpoint: `mlog_sim` runs
caller-supplied mlog and `world_js` runs Rhino.

Run:
    python tools/mlog_mcp_http.py --port 8765 --token "$MLOG_MCP_TOKEN"
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import uuid
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

import mlog_mcp as M  # noqa: E402

MAX_BODY = 8 * 1024 * 1024
START = time.time()

# Legacy handlers share mutable task and executor state. The isolated
# simulation worker does not need that lock, but only one job runs at a time.
_LOCK = threading.Lock()
_SIM_SLOT = threading.BoundedSemaphore(1)


def _json_body(obj: bytes) -> dict:
    return {"jsonrpc": "2.0", "id": None,
            "error": {"code": -32700, "message": "parse error: %s"
                      % obj[:120].decode("utf-8", "replace")}}


def dispatch(payload):
    """Run one JSON-RPC object (or a batch) and return (status, reply_or_None)."""
    if isinstance(payload, list):
        if not payload:
            return 200, {"jsonrpc": "2.0", "id": None,
                         "error": {"code": -32600, "message": "empty batch"}}
        replies = []
        for item in payload:
            status, reply = dispatch(item)
            if status == 400:
                return status, reply
            if reply is not None:
                replies.append(reply)
        return 200, (replies if replies else None)
    if not isinstance(payload, dict) or "method" not in payload:
        return 200, {"jsonrpc": "2.0", "id": payload.get("id") if isinstance(payload, dict) else None,
                     "error": {"code": -32600, "message": "not a JSON-RPC request"}}
    collected = []
    params = payload.get("params")
    if (payload["method"] == "tools/call" and isinstance(params, dict)
            and params.get("name") == "mlog_sim"):
        if not _SIM_SLOT.acquire(blocking=False):
            return 200, {"jsonrpc": "2.0", "id": payload.get("id"), "result": {
                "content": [{"type": "text", "text": "simulation_busy: one simulation is already running"}],
                "isError": True,
            }}
        try:
            M.handle(payload, emit=collected.append)
        finally:
            _SIM_SLOT.release()
    else:
        with _LOCK:
            M.handle(payload, emit=collected.append)
    return 200, (collected[0] if collected else None)


class Handler(BaseHTTPRequestHandler):
    server_version = "mlog-mcp-http/" + M.VERSION
    protocol_version = "HTTP/1.1"

    # -- plumbing ---------------------------------------------------------
    def log_message(self, fmt, *args):
        if not self.server.quiet:
            sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _send(self, status: int, body: dict | None, extra: dict | None = None):
        raw = b"" if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if raw:
            self.wfile.write(raw)

    def _authorised(self) -> bool:
        token = self.server.token
        if not token:
            return True
        got = self.headers.get("Authorization", "")
        if got.startswith("Bearer "):
            got = got[7:].strip()
        return got == token

    def _guard(self) -> bool:
        if self._authorised():
            return True
        self._send(401, {"jsonrpc": "2.0", "id": None,
                         "error": {"code": -32001, "message": "unauthorized"}},
                   {"WWW-Authenticate": 'Bearer realm="mlog-mcp"'})
        return False

    # -- routes -----------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            if not self._guard():
                return
            self._send(200, {
                "ok": True, "name": M.NAME, "version": M.VERSION,
                "protocol": M.PROTO, "tools": len(M.TOOLS),
                "repo": str(HERE.parent), "python": sys.version.split()[0],
                "uptime_s": round(time.time() - START, 1),
                "pid": os.getpid(),
            })
            return
        if path == "/mcp":
            self.send_response(405)
            self.send_header("Allow", "POST")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send(404, {"error": "no such path: %s" % path})

    def do_POST(self):
        path = self.path.split("?")[0]
        if path != "/mcp":
            self._send(404, {"error": "no such path: %s" % path})
            return
        if not self._guard():
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            self._send(400, {"jsonrpc": "2.0", "id": None,
                             "error": {"code": -32600, "message": "empty body"}})
            return
        if length > MAX_BODY:
            self._send(413, {"jsonrpc": "2.0", "id": None,
                             "error": {"code": -32600, "message": "body too large"}})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send(400, _json_body(raw))
            return

        status, reply = dispatch(payload)
        extra = {}
        head = payload[0] if isinstance(payload, list) and payload else payload
        if isinstance(head, dict) and head.get("method") == "initialize":
            extra["Mcp-Session-Id"] = uuid.uuid4().hex
        if reply is None:
            self._send(202, None, extra)
        else:
            self._send(status, reply, extra)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, handler, token="", quiet=False):
        super().__init__(addr, handler)
        self.token = token
        self.quiet = quiet


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="MCP server for the mlog toolchain, over HTTP.")
    ap.add_argument("--bind", default="127.0.0.1",
                    help="address to listen on (default 127.0.0.1; use 0.0.0.0 in a container)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default=os.environ.get("MLOG_MCP_TOKEN", ""),
                    help="require `Authorization: Bearer <token>` (env: MLOG_MCP_TOKEN)")
    ap.add_argument("--insecure", action="store_true",
                    help="allow a non-loopback bind without a token (do not do this)")
    ap.add_argument("--quiet", action="store_true", help="no access log")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    loopback = args.bind in ("127.0.0.1", "::1", "localhost")
    if not loopback and not args.token and not args.insecure:
        print("refusing to bind %s without --token: mlog_sim executes caller-supplied "
              "programs, so an open port is an open executor (pass --insecure to override)"
              % args.bind, file=sys.stderr)
        return 2
    try:
        httpd = Server((args.bind, args.port), Handler, token=args.token, quiet=args.quiet)
    except OSError as exc:
        print("cannot listen on %s:%d: %s" % (args.bind, args.port, exc), file=sys.stderr)
        return 1
    host, port = httpd.server_address[:2]
    print(json.dumps({"listening": "http://%s:%d/mcp" % (host, port),
                      "health": "http://%s:%d/health" % (host, port),
                      "tools": len(M.TOOLS), "auth": bool(args.token),
                      "protocol": M.PROTO}, ensure_ascii=False), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # pragma: no cover - a crash here should be loud
        traceback.print_exc()
        raise
