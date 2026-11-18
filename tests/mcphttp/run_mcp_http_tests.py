#!/usr/bin/env python3
"""Contract tests for the HTTP transport (`tools/mlog_mcp_http.py`).

The stdio server is what an agent runs next to its tools; this one is what a
server runs for many clients, so the things worth pinning are the ones a proxy
or a client library depends on: status codes, the notification rule (202, no
body), the auth gate, and the refusal to expose an executor on a public
interface without a token.

No JVM needed: every case here answers without the executor.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER = os.path.join(ROOT, "tools", "mlog_mcp_http.py")


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Server:
    def __init__(self, *extra: str):
        self.port = free_port()
        self.proc = subprocess.Popen(
            [sys.executable, "-X", "utf8", SERVER, "--port", str(self.port), "--quiet"] + list(extra),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        self.banner = json.loads(self.proc.stdout.readline() or "{}")
        self.base = "http://127.0.0.1:%d" % self.port

    def post(self, payload, token: str | None = None, raw: bytes | None = None):
        body = raw if raw is not None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base + "/mcp", data=body,
                                     headers={"Content-Type": "application/json"})
        if token:
            req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), dict(exc.headers or {})

    def get(self, path: str, token: str | None = None):
        req = urllib.request.Request(self.base + path)
        if token:
            req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), dict(exc.headers or {})

    def close(self):
        self.proc.kill()
        self.proc.wait(timeout=10)
        for stream in (self.proc.stdout, self.proc.stderr):
            try:
                stream.close()
            except Exception:
                pass


class Protocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = Server()

    @classmethod
    def tearDownClass(cls):
        cls.srv.close()

    def test_initialize_returns_a_protocol_version_and_a_session_id(self):
        status, body, headers = self.srv.post(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05", "capabilities": {}}})
        self.assertEqual(status, 200)
        reply = json.loads(body)
        self.assertEqual(reply["id"], 1)
        self.assertIn("protocolVersion", reply["result"])
        self.assertEqual(reply["result"]["serverInfo"]["name"], "mlog-toolkit")
        # a session id is optional in the spec but a client library will reuse it
        self.assertIn("Mcp-Session-Id", headers)

    def test_tools_list_matches_the_stdio_server(self):
        status, body, _ = self.srv.post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertEqual(status, 200)
        names = [t["name"] for t in json.loads(body)["result"]["tools"]]
        self.assertIn("mlog_doctor", names)
        self.assertIn("mlog_validate", names)
        self.assertEqual(len(names), len(set(names)), "tool names must be unique")

    def test_a_notification_gets_202_and_no_body(self):
        status, body, _ = self.srv.post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertEqual(status, 202)
        self.assertEqual(body, b"", "a notification must not carry a reply")

    def test_a_tool_call_that_fails_is_reported_not_raised_as_http_error(self):
        status, body, _ = self.srv.post(
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "mlog_check", "arguments": {"code": "jump 5 always"}}})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["result"]["isError"])

    def test_an_unknown_method_is_minus_32601(self):
        status, body, _ = self.srv.post({"jsonrpc": "2.0", "id": 4, "method": "no/such"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["error"]["code"], -32601)

    def test_broken_json_is_400(self):
        status, body, _ = self.srv.post(None, raw=b"{not json")
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"]["code"], -32700)

    def test_health_is_cheap_and_says_how_many_tools(self):
        status, body, _ = self.srv.get("/health")
        self.assertEqual(status, 200)
        doc = json.loads(body)
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["tools"], 15)
        self.assertIn("uptime_s", doc)

    def test_get_mcp_is_405_rather_than_a_broken_stream(self):
        status, _, headers = self.srv.get("/mcp")
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "POST")

    def test_a_batch_is_answered_as_a_list(self):
        status, body, _ = self.srv.post([
            {"jsonrpc": "2.0", "id": 10, "method": "ping"},
            {"jsonrpc": "2.0", "id": 11, "method": "tools/list"},
        ])
        self.assertEqual(status, 200)
        replies = json.loads(body)
        self.assertEqual([r["id"] for r in replies], [10, 11])


class Auth(unittest.TestCase):
    def test_a_token_is_required_when_configured(self):
        srv = Server("--token", "s3cret")
        try:
            status, _, _ = srv.post({"jsonrpc": "2.0", "id": 1, "method": "ping"})
            self.assertEqual(status, 401)
            status, body, _ = srv.post({"jsonrpc": "2.0", "id": 1, "method": "ping"},
                                       token="s3cret")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["result"], {})
            self.assertEqual(srv.get("/health")[0], 401)
            self.assertEqual(srv.get("/health", token="s3cret")[0], 200)
        finally:
            srv.close()

    def test_a_public_bind_without_a_token_is_refused(self):
        # The refusal happens before any socket is opened, so this is portable.
        cp = subprocess.run([sys.executable, "-X", "utf8", SERVER,
                             "--bind", "0.0.0.0", "--port", str(free_port())],
                            capture_output=True, text=True, timeout=60)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("refusing to bind", cp.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
