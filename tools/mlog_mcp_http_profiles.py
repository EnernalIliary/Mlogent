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

import mlog_acl as ACL
import mlog_resource_policy as LIMITS
import mlog_oauth as OAUTH
import argparse
import io
import contextlib
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
from mlogent.mcp.apps import Apps

try:
    import world_mcp as W  # noqa: E402  (42 个 world_* 工具，薄壳直连活世界 daemon)
except Exception:  # pragma: no cover
    W = None

MAX_BODY = 8 * 1024 * 1024
START = time.time()

#: `mlog_fetch` hands back blobs the trimmed answers parked in `M._ARTIFACTS`.
#: One dict, many threads: serialise dispatch so a fetch cannot read a half
#: written entry, and so two calls cannot pick the same artifact id.
_LOCK = threading.Lock()
_TOOL_LOCK_WAIT_SECONDS = 90


def _json_body(obj: bytes) -> dict:
    return {"jsonrpc": "2.0", "id": None,
            "error": {"code": -32700, "message": "parse error: %s"
                      % obj[:120].decode("utf-8", "replace")}}


def _rpc_error(payload, code, message):
    return {"jsonrpc": "2.0", "id": payload.get("id"),
            "error": {"code": code, "message": message}}


def dispatch(payload, profile="runner", principal="static", apps=None):
    """Run one JSON-RPC object (or a batch) and return (status, reply_or_None)."""
    if isinstance(payload, list):
        if not payload:
            return 200, {"jsonrpc": "2.0", "id": None,
                         "error": {"code": -32600, "message": "empty batch"}}
        if len(payload) > 16 or any(isinstance(item, list) for item in payload):
            return 200, {"jsonrpc": "2.0", "id": None, "error": {
                "code": -32600, "message": "Use a flat batch of at most 16 requests."}}
        replies = []
        for item in payload:
            status, reply = dispatch(item, profile, principal, apps=apps)
            if status == 400:
                return status, reply
            if reply is not None:
                replies.append(reply)
        return 200, (replies if replies else None)
    if not isinstance(payload, dict) or "method" not in payload:
        return 200, {"jsonrpc": "2.0", "id": payload.get("id") if isinstance(payload, dict) else None,
                     "error": {"code": -32600, "message": "not a JSON-RPC request"}}
    collected = []
    _t0 = time.time()
    _method = payload.get("method")
    _params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
    _name = _params.get("name")
    if not isinstance(_name, str):
        _name = ""
    if _method == "tools/call":
        if not ACL.allows(profile, _name):
            return 200, {"jsonrpc": "2.0", "id": payload.get("id"),
                         "result": {"content": [{"type": "text",
                                                 "text": ACL.deny_message(profile, _name)}],
                                    "isError": True}}
        arguments = _params.get("arguments", {})
        if not isinstance(arguments, dict):
            return 200, _rpc_error(payload, -32602, "Tool arguments must be an object.")
        if profile == "reader" and _name == "mlog_extract" and arguments.get("format", "mlog") != "mlog":
            return 200, _rpc_error(payload, -32602, "The reader profile supports mlog extraction only.")
        refusal = ACL.argument_refusal(profile, _name, arguments)
        if refusal:
            return 200, _rpc_error(payload, -32602, refusal)
        refusal = LIMITS.refusal(_name, arguments)
        if refusal:
            return 200, _rpc_error(payload, -32602, refusal)
        quota_tool = _name
        # Opening an author form is a normal request. Its actual submission
        # consumes the work quota, so UI generation is not charged twice.
        if (apps and _name in ("mlog_gen", "mlog_inject")
                and apps.permitted("mlog_signature_request", lambda name: ACL.allows(profile, name))
                and apps._unsigned_without_author(_name, arguments)):
            quota_tool = "mlog_signature_request"
        _ok, _wait = ACL.allow(principal, profile, quota_tool)
        if not _ok:
            label = "处理额度" if ACL.quota_bucket(profile, quota_tool) == "work" else "普通额度"
            return 200, {"jsonrpc": "2.0", "id": payload.get("id"),
                         "error": {"code": -32002,
                                   "message": "请求太快，%d 秒后再试（%s，%s每分钟 %d 次）"
                                              % (_wait, ACL.get(profile).get("label") or profile,
                                                 label, ACL.rpm(profile, quota_tool))}}
    # The simulator and artifact store share process state. Allow one tool
    # call at a time, with a short wait for non-heavy calls.
    # Metadata and ping do not mutate that state.
    needs_lock = _method == "tools/call"
    if needs_lock:
        if not _LOCK.acquire(timeout=_TOOL_LOCK_WAIT_SECONDS):
            return 200, _rpc_error(payload, -32003, "MCP is busy; retry shortly.")
    try:
        special = apps.handle(payload, principal, lambda name: ACL.allows(profile, name)) if apps else None
        if special is not None:
            collected.append(special)
        elif (W is not None and _method == "tools/call"
                and _name in getattr(W, "HANDLERS", {})):
            _buf = io.StringIO()
            with contextlib.redirect_stdout(_buf):
                W.handle(payload)
            for _ln in _buf.getvalue().splitlines():
                _ln = _ln.strip()
                if _ln.startswith("{"):
                    collected.append(json.loads(_ln))
                    break
            if not collected:
                collected.append({"jsonrpc": "2.0", "id": payload.get("id"),
                                   "result": {"content": [{"type": "text",
                                               "text": "world 工具没有返回"}],
                                              "isError": True}})
        else:
            M.handle(payload, emit=collected.append)
    finally:
        if needs_lock:
            _LOCK.release()
    _reply = collected[0] if collected else None
    if isinstance(payload, dict) and payload.get("method") == "tools/call":
        _nm = (payload.get("params") or {}).get("name")
        _res = (_reply or {}).get("result") or {}
        _txt = (_res.get("content") or [{}])[0]
        _head = str(_txt.get("text", ""))[:100].replace("\n", " ")
        sys.stderr.write("%s tools/call %s %s %.2fs %s\n" % (
            time.strftime("%H:%M:%S"), _nm,
            "ERROR" if _res.get("isError") else "ok",
            time.time() - _t0, _head))
    if _method == "tools/list" and isinstance(_reply, dict):
        _res = _reply.get("result")
        if isinstance(_res, dict) and isinstance(_res.get("tools"), list):
            if W is not None:
                _res["tools"] = _res["tools"] + list(W.TOOLS)
            if apps is not None:
                _res["tools"] = list(_res["tools"]) + apps.catalog(lambda name: ACL.allows(profile, name))
            _res["tools"] = ACL.filter_tools(profile, _res["tools"])
            if apps is not None:
                _res["tools"] = apps.decorate(_res["tools"], lambda name: ACL.allows(profile, name))
            if profile == "reader":
                _res["tools"] = [ACL.public_tool(tool) for tool in _res["tools"]]
                for index, tool in enumerate(_res["tools"]):
                    if tool.get("name") == "mlog_extract":
                        schema = tool["inputSchema"]
                        fields = dict(schema["properties"])
                        fields["format"] = {**fields["format"], "enum": ["mlog"]}
                        _res["tools"][index] = {**tool, "inputSchema": {
                            **schema, "properties": fields}}
                        break
    if _method == "initialize" and isinstance(_reply, dict):
        if apps is not None:
            _reply["result"]["capabilities"]["resources"] = {}
        _si = ((_reply.get("result") or {}).get("serverInfo"))
        if isinstance(_si, dict):
            _si["name"] = "Mlogent世界服务器"
    if apps is not None:
        _reply = apps.decorate_reply(payload, _reply, lambda name: ACL.allows(profile, name))
    return 200, _reply


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

    def _send_raw(self, status, ctype, body, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _auth_profile(self):
        """The profile this request may use, or None when unauthenticated."""
        self._user = "anon"
        if not self.server.token:
            self._user = "static"
            return ACL.static_profile()
        got = self.headers.get("Authorization", "")
        if got.startswith("Bearer "):
            got = got[7:].strip()
        if not got:
            return None
        if got == self.server.token:
            self._user = "static"
            return ACL.static_profile()
        entry = OAUTH.resolve(got)
        if not entry:
            return None
        self._user = entry.get("user") or entry.get("client_id") or "oauth"
        return entry.get("profile") or "runner"

    def _authorised(self) -> bool:
        profile = self._auth_profile()
        if profile is None:
            return False
        self._profile = profile
        return True

    def _guard(self) -> bool:
        if self._authorised():
            return True
        self._send(401, {"jsonrpc": "2.0", "id": None,
                         "error": {"code": -32001, "message": "unauthorized"}},
                   {"WWW-Authenticate": OAUTH.never_challenge()})
        return False

    # -- routes -----------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?")[0]
        _qs = {}
        if "?" in self.path:
            from urllib.parse import parse_qs as _pq
            _qs = {k: v[0] for k, v in _pq(self.path.split("?", 1)[1]).items()}
        _oauth = OAUTH.route("GET", path, _qs, self.headers, b"")
        if _oauth is not None:
            self._send_raw(*_oauth)
            return
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
            try:
                _len = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                _len = 0
            _body = self.rfile.read(_len) if 0 < _len <= MAX_BODY else b""
            _resp = OAUTH.route("POST", path, {}, self.headers, _body)
            if _resp is not None:
                self._send_raw(*_resp)
            else:
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
            self.close_connection = True
            self._send(413, {"jsonrpc": "2.0", "id": None,
                             "error": {"code": -32600, "message": "body too large"}})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send(400, _json_body(raw))
            return

        status, reply = dispatch(payload, getattr(self, "_profile", "runner"),
                                getattr(self, "_user", "anon"), apps=self.server.apps)
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

    def __init__(self, addr, handler, token="", quiet=False, enable_ui=False):
        super().__init__(addr, handler)
        self.token = token
        self.quiet = quiet
        self.apps = Apps(M, W) if enable_ui else None


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
    ap.add_argument("--enable-ui", action="store_true", help="expose opt-in ChatGPT MCP Apps tools and resources")
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
        httpd = Server((args.bind, args.port), Handler, token=args.token, quiet=args.quiet,
                       enable_ui=args.enable_ui)
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
