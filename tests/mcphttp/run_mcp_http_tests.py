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

import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlencode, urlsplit
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVER = os.path.join(ROOT, "tools", "mlog_mcp_http.py")

TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import mlog_mcp  # noqa: E402  (needs the path above; the count comes from here)
import mlog_mcp_http  # noqa: E402
import scene  # noqa: E402
import mlog_acl  # noqa: E402
import mlog_mcp_http_profiles  # noqa: E402
import mlog_oauth  # noqa: E402
import mlog_resource_policy  # noqa: E402
from mlogent.mcp.apps import Apps, SIGNATURE_URI, DASHBOARD_URI, MIME



def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Server:
    def __init__(self, *extra: str, env=None):
        self.port = free_port()
        self.proc = subprocess.Popen(
            [sys.executable, "-X", "utf8", SERVER, "--port", str(self.port), "--quiet"] + list(extra),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", env=env)
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
        revisions = tempfile.TemporaryDirectory(prefix="mlog-revisions-test-")
        cls.addClassCleanup(revisions.cleanup)
        cls.server_env = {**os.environ, "MLOG_REVISION_DIR": revisions.name}
        cls.srv = Server(env=cls.server_env)

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
        self.assertIn("mlog_extract", names)
        self.assertIn("mlog_inject", names)
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

    def test_extract_inventory_selection_and_batch_fetch(self):
        import aigenerated
        import mschgen

        code, *_ = aigenerated.sign_delivery(
            "# purpose\n# " + "b" * 200 + "\n# not in preview\n"
            "set i 0\nretry:\nop add i i 1\njump retry lessThan i 3\njump 0 always 0\nend\n", "test-author")
        blueprint = mschgen.Blueprint("extract")
        blueprint.add_logic(code, links=[mschgen.Link("cell1", 0, 2)])
        second = "# " + "x" * 2100 + "\nprint 42\nend\n"
        blueprint.add_logic(second, x=3)
        paste = base64.b64encode(blueprint.build()).decode("ascii")

        def call(name, args, *, error=False):
            status, body, _ = self.srv.post({
                "jsonrpc": "2.0", "id": 31, "method": "tools/call",
                "params": {"name": name, "arguments": args},
            })
            self.assertEqual(status, 200)
            reply = json.loads(body)["result"]
            self.assertEqual(reply["isError"], error)
            payload = reply["content"][0]["text"]
            return payload if error else json.loads(payload)

        inventory = call("mlog_extract", {"blueprint_code": paste})
        self.assertEqual(inventory["mode"], "inventory")
        self.assertEqual(inventory["total"], 2)
        self.assertEqual([(p["index"], p["x"], p["y"]) for p in inventory["processors"]],
                         [(0, 0, 0), (1, 3, 0)])
        self.assertEqual(inventory["processors"][0]["links"], [{"name": "cell1", "x": 0, "y": 2}])
        self.assertNotIn("code", inventory["processors"][0])
        self.assertEqual(inventory["processors"][0]["comment_preview"], [
            {"line": 1, "text": "# purpose"}, {"line": 2, "text": "# " + "b" * 158},
        ])
        self.assertNotIn("comment_preview", inventory["processors"][1])

        selected = call("mlog_extract", {"blueprint_code": paste, "index": 0})
        self.assertIn("jump retry lessThan i 3", selected["processors"][0]["code"])
        inline = call("mlog_extract", {"mlog": "jump 0 always 0 0"})
        self.assertIn("jump L0 always 0 0", inline["processors"][0]["code"])
        path = call("mlog_extract", {"path": "tests/cases/label-index.mlog"})
        self.assertEqual(path["total"], 1)

        batch = call("mlog_extract", {"blueprint_code": paste, "all": True})
        ref = batch["programs_ref"]["artifact_ref"]
        chunk = call("mlog_fetch", {"ref": ref, "limit": 15})
        tail = call("mlog_fetch", {"ref": ref, "offset": chunk["next_offset"]})
        programs = json.loads(chunk["text"] + tail["text"])
        self.assertEqual([p["index"] for p in programs], [0, 1])
        self.assertIn("jump retry", programs[0]["code"])
        self.assertEqual(programs[1]["code"], second)
        self.assertIn("choose index or all", call(
            "mlog_extract", {"blueprint_code": paste, "index": 0, "all": True}, error=True))
        self.assertIn("within the server workspace", call("mlog_extract", {"path": "../example.mlog"}, error=True))


    def test_inject_changes_only_the_selected_processor_code(self):
        import struct
        import tempfile
        import zlib
        from pathlib import Path

        import aigenerated
        import msch
        import mschgen

        blueprint = mschgen.Blueprint("复杂蓝图", "original description", ["demo"])
        blueprint.add_logic("print 1\nend\n", links=[mschgen.Link("cell1", 1, 0)])
        blueprint.add_block("memory-cell", 1, 0)
        blueprint.add_logic("print 2\nend\n", x=3, rotation=2, links=[mschgen.Link("cell1", -2, 0)])
        blueprint.add_block("message", 4, 0, config=864217)
        raw = blueprint.build()
        # A TypeIO double cannot be losslessly round-tripped by build_schematic.
        body = zlib.decompress(raw[5:])
        old_config = bytes([msch.T_INT]) + struct.pack(">i", 864217)
        self.assertEqual(body.count(old_config), 1)
        body = body.replace(old_config, bytes([msch.T_DOUBLE]) + struct.pack(">d", 1.23456789012345))
        raw = raw[:5] + zlib.compress(body)
        paste = base64.b64encode(raw).decode("ascii")
        replacement = "set n 0\nretry:\nop add n n 1\njump retry lessThan n 3\njump 0 always 0\nend\n"

        def call(tool, args, *, error=False):
            if tool in ("mlog_inject", "mlog_gen"):
                args = dict(args)
                args.setdefault("author", "mcp-test")
            status, reply, _ = self.srv.post({
                "jsonrpc": "2.0", "id": 32, "method": "tools/call",
                "params": {"name": tool, "arguments": args},
            })
            self.assertEqual(status, 200)
            result = json.loads(reply)["result"]
            self.assertEqual(result["isError"], error)
            payload = result["content"][0]["text"]
            return payload if error else json.loads(payload)

        inventory = call("mlog_extract", {"blueprint_code": paste})
        updated = call("mlog_inject", {"blueprint_code": paste, "index": 1, "mlog": replacement})
        self.assertEqual(updated["processor"], inventory["processors"][1])
        new_raw = base64.b64decode(updated["blueprint_base64"])
        self.assertEqual(new_raw[:5], raw[:5])

        new_body = zlib.decompress(new_raw[5:])
        old_spans, new_spans = [], []
        old = msch._parse_body(body, raw[4], logic_spans=old_spans)
        new = msch._parse_body(new_body, new_raw[4], logic_spans=new_spans)
        lo, hi = old_spans[1]
        new_lo, new_hi = new_spans[1]
        self.assertEqual(body[:lo], new_body[:new_lo])
        self.assertEqual(body[hi:], new_body[new_hi:])
        old_processor = zlib.decompress(old.logic_tiles()[1].raw_config)
        new_processor = zlib.decompress(new.logic_tiles()[1].raw_config)
        self.assertEqual(old_processor[0], new_processor[0])
        self.assertEqual(old_processor[5 + struct.unpack_from(">i", old_processor, 1)[0]:],
                         new_processor[5 + struct.unpack_from(">i", new_processor, 1)[0]:])
        self.assertEqual(new.logic_tiles()[0].logic.code, "print 1\nend\n")
        self.assertIn("jump 1 lessThan n 3", new.logic_tiles()[1].logic.code)
        self.assertEqual(aigenerated.verify_text(new.logic_tiles()[1].logic.code), [])

        reopened = call("mlog_extract", {"blueprint_code": updated["blueprint_base64"], "index": 1})
        self.assertIn("jump retry lessThan n 3", reopened["processors"][0]["code"])
        with tempfile.TemporaryDirectory(prefix="inject-test-", dir=ROOT) as directory:
            source = Path(directory) / "untouched.msch"
            source.write_bytes(raw)
            via_path = call("mlog_inject", {"path": str(source), "index": 1, "mlog": replacement})
            self.assertEqual(via_path["blueprint_base64"], updated["blueprint_base64"])
            self.assertEqual(source.read_bytes(), raw)
        self.assertIn("outside", call("mlog_inject", {
            "blueprint_code": paste, "index": 2, "mlog": replacement,
        }, error=True))
        self.assertIn("duplicate label", call("mlog_inject", {
            "blueprint_code": paste, "index": 1, "mlog": "same:\nset a 1\nsame:\nend",
        }, error=True))

    def test_inject_preview_reports_checks_and_guards_against_stale_source(self):
        import hashlib

        import msch
        import mschgen

        blueprint = mschgen.Blueprint("preview")
        original = "print 1\njump 0 always 0\nend\n"
        blueprint.add_logic(original, links=[
            mschgen.Link("cell1", 1, 0), mschgen.Link("message1", 9, 0),
        ])
        blueprint.add_block("memory-cell", 1, 0)
        paste = base64.b64encode(blueprint.build()).decode("ascii")
        args = {"blueprint_code": paste, "index": 0, "mlog": "read n cell1 0\nprint n\n"
                "printflush message2\njump 0 always 0\nend\n"}

        def inject(arguments):
            arguments = dict(arguments)
            arguments.setdefault("author", "mcp-test")
            status, reply, _ = self.srv.post({
                "jsonrpc": "2.0", "id": 33, "method": "tools/call",
                "params": {"name": "mlog_inject", "arguments": arguments},
            })
            self.assertEqual(status, 200)
            result = json.loads(reply)["result"]
            self.assertFalse(result["isError"], result)
            return json.loads(result["content"][0]["text"])

        preview = inject({**args, "preview": True})
        self.assertEqual(preview["mode"], "preview")
        self.assertNotIn("blueprint_base64", preview)
        self.assertNotIn("revision", preview)
        self.assertEqual(preview["source_sha256"], hashlib.sha256(original.encode()).hexdigest())
        self.assertIn("-print 1", preview["diff"])
        self.assertIn("+printflush message2", preview["diff"])
        self.assertNotIn("AI-Generated:Mlogent:", preview["diff"])
        self.assertTrue(any(f["rule_id"] == "link-name-not-bound" and "message2" in f["message"]
                            for f in preview["checks"]["findings"]))
        self.assertEqual(preview["checks"]["links"], [
            {"name": "cell1", "x": 1, "y": 0, "target_block": "memory-cell", "in_blueprint": True},
            {"name": "message1", "x": 9, "y": 0, "target_block": None, "in_blueprint": False},
        ])

        applied = inject({**args, "expected_sha256": preview["source_sha256"]})
        self.assertEqual(applied["mode"], "apply")
        self.assertEqual(applied["diff"], preview["diff"])
        self.assertEqual(applied["checks"], preview["checks"])
        delivered = msch.parse_base64(applied["blueprint_base64"]).logic_tiles()[0].logic.code
        self.assertEqual(hashlib.sha256(delivered.encode()).hexdigest(), preview["replacement_sha256"])
        stale = inject({**args, "blueprint_code": applied["blueprint_base64"],
                        "expected_sha256": preview["source_sha256"]})
        self.assertFalse(stale["ok"])
        self.assertEqual(stale["failure_type"], "source_conflict")
        self.assertEqual(stale["source_sha256"], preview["replacement_sha256"])
        self.assertNotIn("blueprint_base64", stale)
        self.assertNotIn("revision", stale)

    def test_revision_survives_restart_and_rejects_other_blueprints(self):
        import mschgen

        blueprint = mschgen.Blueprint("revision")
        blueprint.add_logic("print 1\njump 0 always 0\nend\n")
        paste = base64.b64encode(blueprint.build()).decode("ascii")

        def call(server, name, args):
            status, body, _ = server.post({
                "jsonrpc": "2.0", "id": 35, "method": "tools/call",
                "params": {"name": name, "arguments": args},
            })
            self.assertEqual(status, 200)
            reply = json.loads(body)["result"]
            self.assertFalse(reply["isError"], reply)
            return json.loads(reply["content"][0]["text"])

        applied = call(self.srv, "mlog_inject", {"blueprint_code": paste, "index": 0,
                                                "mlog": "print 2\njump 0 always 0\nend\n"})
        revision = applied["revision"]

        # A separate process has no access to the injecting process's artifact cache.
        fresh = Server(env=self.server_env)
        try:
            record = call(fresh, "mlog_revision", {"revision": revision})
            self.assertEqual(record["original_mlog"], "print 1\njump 0 always 0\nend\n")
            self.assertEqual(record["diff"], applied["diff"])
            self.assertEqual(record["checks"], applied["checks"])
            restored = call(fresh, "mlog_revision", {
                "revision": revision, "action": "rollback", "blueprint_code": applied["blueprint_base64"],
            })
            self.assertEqual(restored["blueprint_base64"], paste)
            stale = call(fresh, "mlog_revision", {
                "revision": revision, "action": "rollback", "blueprint_code": paste,
            })
            self.assertEqual(stale["failure_type"], "blueprint_conflict")
            self.assertNotIn("blueprint_base64", stale)
        finally:
            fresh.close()

    def test_trace_filters_and_finds_divergence(self):
        trace = ("tick\tpc\tvars\tsource\n"
                 "0\t0\ti=0;j=4;\tset i 0\n"
                 "0\t1\ti=0;j=4;\top add i i 1\n"
                 "1\t2\ti=1;j=4;\tjump retry lessThan i 3\n")
        status, body, _ = self.srv.post({
            "jsonrpc": "2.0", "id": 36, "method": "tools/call",
            "params": {"name": "mlog_trace", "arguments": {
                "trace": trace, "baseline_trace": trace.replace("i=1;", "i=2;"),
                "mlog": "set i 0\n# comment\nretry:\nop add i i 1\njump retry lessThan i 3",
                "label": "retry", "vars": ["i"], "limit": 1,
            }},
        })
        self.assertEqual(status, 200)
        reply = json.loads(body)["result"]
        self.assertFalse(reply["isError"], reply)
        result = json.loads(reply["content"][0]["text"])
        self.assertEqual((result["total"], result["matched"], result["next_offset"]), (3, 2, 1))
        self.assertEqual(result["rows"][0]["line"], 4)
        self.assertEqual(result["rows"][0]["vars"], {"i": "0"})
        self.assertEqual(result["first_divergence"]["step"], 2)
        self.assertEqual(result["first_divergence"]["baseline"]["vars"], {"i": "2"})

    def test_generate_from_file_signs_blueprint_without_rewriting_source(self):
        from pathlib import Path

        import aigenerated
        import msch

        with tempfile.TemporaryDirectory(prefix="gen-test-", dir=ROOT) as directory:
            path = Path(directory) / "source.mlog"
            original = "print 42\njump 0 always 0\nend\n"
            path.write_text(original, encoding="utf-8")
            status, body, _ = self.srv.post({
                "jsonrpc": "2.0", "id": 37, "method": "tools/call",
                "params": {"name": "mlog_gen", "arguments": {"source": str(path),
                                                                     "author": "mcp-test"}},
            })
            self.assertEqual(status, 200)
            result = json.loads(body)["result"]
            self.assertFalse(result["isError"], result)
            paste = json.loads(result["content"][0]["text"])["blueprint_base64"]
            code = msch.parse_base64(paste).logic_tiles()[0].logic.code
            self.assertIn("print 42", code)
            self.assertEqual(aigenerated.verify_text(code), [])
            self.assertEqual(path.read_text(encoding="utf-8"), original)

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
        self.assertEqual(doc["tools"], len(mlog_mcp.TOOLS))
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

    def test_marker_from_svg_rejects_unsupported_and_oversize_geometry(self):
        cases = (
            ('<path d="M0 0 L1 1"/>', "unsupported SVG element"),
            ('<rect width="3" height="2" transform="rotate(10)"/>', "unsupported SVG attribute"),
            ('<polygon points="0,0 9,9 9,0 0,9"/>', "simple polygon"),
            ('<rect width="1" height="1"/>' * 129, "more than 128 markers"),
        )
        for geometry, message in cases:
            with self.subTest(message=message):
                status, body, _ = self.srv.post({
                    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "marker_from_svg", "arguments": {
                        "svg": f'<svg viewBox="0 0 10 10">{geometry}</svg>',
                    }},
                })
                self.assertEqual(status, 200)
                result = json.loads(body)["result"]
                self.assertTrue(result["isError"])
                self.assertIn(message, result["content"][0]["text"])


class Simulation(unittest.TestCase):
    @staticmethod
    def call(args, rid=1):
        return {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                "params": {"name": "mlog_sim", "arguments": args}}

    def test_input_limits_and_projection_paths(self):
        cases = (
            ({"path": "../outside.mlog"}, "within the server workspace"),
            ({"scene": "../outside.json"}, "within the server workspace"),
            ({"logic": "end", "save": "../outside.msav"}, "within the server workspace"),
            ({"logic": "end", "project": "out/_world/daemon.json"}, "JSON feed"),
            ({"logic": "end", "project": "out/_proj/../../outside.json"}, "JSON feed"),
            ({"logic": "end", "ticks": 1201}, "between 1 and 1200"),
            ({"logic": "end", "steps": True}, "between 1 and 2400"),
            ({"logic": "end", "ticks": 601, "trace_vars": []}, "between 1 and 600"),
            ({"logic": "end", "ticks": 1200, "rt": 0.1}, "pacing exceeds"),
        )
        with patch.object(mlog_mcp, "_bounded_sim_worker") as worker:
            for args, message in cases:
                with self.subTest(args=args):
                    status, reply = mlog_mcp_http.dispatch(self.call(args))
                    self.assertEqual(status, 200)
                    self.assertTrue(reply["result"]["isError"])
                    self.assertIn(message, reply["result"]["content"][0]["text"])
            worker.assert_not_called()

    def test_power_profile_rejects_invalid_points_and_modes(self):
        first = {"tick": 1, "power_per_second": 12}
        cases = (
            ({"power": "variable"}, "power must be"),
            ({"power": "none", "power_profile": [first]}, "requires power=grid"),
            ({"power": "grid", "steps": 10}, "requires a tick run"),
            ({"power": "grid", "update": "none"}, "requires a tick run"),
            ({"power_profile": []}, "requires 1"),
            ({"power_profile": [first] * 65}, "requires 1"),
            ({"power_profile": [{"tick": 0, "power_per_second": 12}]}, "start at tick 1"),
            ({"power_profile": [first, first]}, "increase within the run"),
            ({"ticks": 10, "power_profile": [first, {"tick": 11, "power_per_second": 0}]},
             "increase within the run"),
            ({"power_profile": [{**first, "note": "extra"}]}, "requires tick and power_per_second"),
            ({"power_profile": [{**first, "power_per_second": "12"}]}, "power_per_second must be"),
            ({"power_profile": [{**first, "power_per_second": True}]}, "power_per_second must be"),
            ({"power_profile": [{**first, "power_per_second": float("inf")}]}, "power_per_second must be"),
        )
        with patch.object(mlog_mcp, "_bounded_sim_worker") as worker:
            for args, message in cases:
                with self.subTest(args=args):
                    _, reply = mlog_mcp_http.dispatch(self.call({"logic": "end", **args}))
                    self.assertTrue(reply["result"]["isError"])
                    self.assertIn(message, reply["result"]["content"][0]["text"])
            worker.assert_not_called()

    def test_world_probe_validates_query_before_starting_worker(self):
        cases = (
            ({"world_probe": {}}, "must specify at least one supported selection or checks"),
            ({"world_probe": {"tiles": [{"x": True, "y": 0}]}}, "integer x and y"),
            ({"world_probe": {"flags": ["line\nbreak"]}}, "printable text"),
            ({"world_probe": {"rules": ["objectiveFlags"]}}, "must be one of"),
            ({"world_probe": {"tiles": [{"x": 0, "y": 0}] * 33}}, "1 to 32 entries"),
            ({"world_probe": {"rules": ["waves"]}, "steps": 10}, "requires ticks"),
            ({"processor": "hyper"}, "must be auto, micro or world"),
            ({"world_probe": {"checks": [{"flag": "gate", "equals": 1}]}}, "valid bool"),
            ({"world_probe": {"checks": [{"rule": "waveSpacing", "equals": True}]}}, "valid float"),
            ({"world_probe": {"checks": [{"marker": 2**31, "equals": False}]}}, ".marker is invalid"),
            ({"world_probe": {"checks": [{"memory": {"x": 0, "y": 0, "index": -1},
                                           "equals": None}]}}, ".memory is invalid"),
            ({"world_probe": {"checks": [{"unit_count": {"x": 0, "y": 0, "width": 2, "height": 2},
                                           "equals": -1}]}}, "non-negative unit count"),
            ({"world_probe": {"checks": [{"tile": {"x": 8, "y": 9}, "field": "config",
                                           "equals": "value"}]}}, ".field must be one of"),
            ({"world_probe": {"tiles": [{"x": x, "y": 0} for x in range(32)], "checks": [
                {"tile": {"x": 32, "y": 0}, "field": "block", "equals": "air"},
            ]}}, "at most 32 entries including checks"),
        )
        with patch.object(mlog_mcp, "_bounded_sim_worker") as worker:
            for args, message in cases:
                with self.subTest(args=args):
                    _, reply = mlog_mcp_http.dispatch(self.call({"logic": "end", **args}))
                    self.assertTrue(reply["result"]["isError"])
                    self.assertIn(message, reply["result"]["content"][0]["text"])
            worker.assert_not_called()

    def test_power_profile_dispatches_bounded_schedule_data(self):
        points = [{"tick": 1, "power_per_second": 12}, {"tick": 40, "power_per_second": 1.5}]

        def run(command):
            self.assertIn("--ticks=60", command)
            self.assertIn("--power=grid", command)
            self.assertFalse(any(arg.startswith("--init-js") for arg in command))
            profile = next(arg.split("=", 1)[1] for arg in command if arg.startswith("--power-profile="))
            self.assertEqual(json.loads(profile), points)
            return '[{"vars": {}, "mode": "tick"}]'

        with patch.object(mlog_mcp, "_bounded_sim_worker", side_effect=run):
            _, reply = mlog_mcp_http.dispatch(self.call({"logic": "end", "power_profile": points}))
        self.assertFalse(reply["result"]["isError"])
        result = json.loads(reply["result"]["content"][0]["text"])
        self.assertEqual(result["power"], "grid")
        self.assertEqual(result["mode"], "tick")

    def test_scene_nested_source_and_rule_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp)
            root = outer / "workspace"
            root.mkdir()
            inside = root / "inside.mlog"
            outside = outer / "outside.mlog"
            for source in (inside, outside):
                source.write_text("end\n", encoding="utf-8")
            path = root / "scene.json"
            block = {"block": "micro-processor", "x": 2, "y": 2, "code": inside.name}
            data = {"buildings": [block], "world": {"rules": {"waves": False}}}
            path.write_text(json.dumps(data), encoding="utf-8")
            loaded = scene.load(str(path), workspace_root=str(root))
            self.assertEqual(loaded["buildings"][0]["code"], "end\n")
            block["code"] = str(outside)
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(scene.SceneError, "within the server workspace"):
                scene.load(str(path), workspace_root=str(root))
            block["code"] = inside.name
            for rules in ({"waves": "false"}, {"invalid name": True}):
                data["world"]["rules"] = rules
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(scene.SceneError, "world.rules requires"):
                    scene.load(str(path), workspace_root=str(root))

    def test_scene_inline_and_multiple_worker_records(self):
        records = [{"vars": {"n": "42"}, "scene": {"done": True}}, {"vars": {}}]

        def run(command):
            self.assertTrue(any(arg.startswith("--scene=") for arg in command))
            self.assertNotIn("--logic", command)
            self.assertEqual(command[-2], "--")
            self.assertEqual(Path(command[-1]).read_text(encoding="utf-8"), "set n 42\nend\n")
            return json.dumps(records, indent=2)

        with tempfile.TemporaryDirectory(dir=ROOT) as directory, \
                patch.object(mlog_mcp, "_bounded_sim_worker", side_effect=run):
            scene_path = Path(directory) / "scene.json"
            scene_path.write_text(json.dumps({"world": {"size": 16}}), encoding="utf-8")
            result = mlog_mcp.tool_sim({"scene": str(scene_path), "ticks": 8,
                                        "logic": "\ufeffset n 42\nend\n"})
        self.assertEqual(result["vars"], records[0]["vars"])
        self.assertEqual(result["scene"], records[0]["scene"])
        artifact = mlog_mcp.tool_fetch({"ref": result["results_ref"]["artifact_ref"]})
        self.assertEqual(json.loads(artifact["text"]), records)

    def test_worker_timeout_reaps_process(self):
        started = []
        popen = subprocess.Popen

        def start(*args, **kwargs):
            proc = popen(*args, **kwargs)
            started.append(proc)
            return proc

        with patch.object(mlog_mcp, "_MCP_SIM_TIMEOUT", 0.1):
            with patch.object(mlog_mcp.subprocess, "Popen", side_effect=start):
                with self.assertRaisesRegex(RuntimeError, "wall-clock limit"):
                    mlog_mcp._bounded_sim_worker([sys.executable, "-c", "import time; time.sleep(3)"])
        self.assertIsNotNone(started[0].poll())
        self.assertEqual(mlog_mcp._bounded_sim_worker([sys.executable, "-c", "print('ready')"]).strip(),
                         "ready")

    def test_simulation_slot_allows_other_rpc(self):
        started = threading.Event()
        release = threading.Event()

        def wait_for_release(args):
            started.set()
            if not release.wait(5):
                raise RuntimeError("test failed to release simulation")
            return {"done": True}

        with patch.dict(mlog_mcp.HANDLERS, {"mlog_sim": wait_for_release}):
            with ThreadPoolExecutor(max_workers=2) as pool:
                running = pool.submit(mlog_mcp_http.dispatch, self.call({"logic": "end"}))
                try:
                    self.assertTrue(started.wait(2))
                    ping = pool.submit(mlog_mcp_http.dispatch,
                                       {"jsonrpc": "2.0", "id": 2, "method": "ping"})
                    self.assertEqual(ping.result(timeout=2)[1]["result"], {})
                    _, busy = mlog_mcp_http.dispatch(self.call({"logic": "end"}, rid=3))
                    self.assertTrue(busy["result"]["isError"])
                    self.assertIn("simulation_busy", busy["result"]["content"][0]["text"])
                finally:
                    release.set()
                self.assertFalse(running.result(timeout=2)[1]["result"]["isError"])
            self.assertFalse(mlog_mcp_http.dispatch(self.call({"logic": "end"}))[1]["result"]["isError"])


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


class AppsContracts(unittest.TestCase):
    def setUp(self):
        self.apps = Apps(mlog_mcp, mlog_mcp_http_profiles.W)
        self.arguments = {"logic": "set n 42\njump 0 always 0\n", "name": "签名测试"}

    def request(self, **changes):
        return self.apps.request({"operation": "mlog_gen", "arguments": self.arguments, **changes},
                                 "alice", lambda name: True)

    def test_editor_defaults_are_cleaned_before_the_form_snapshot_and_delivery(self):
        source = 'op abs result x b\njump 0 always a b\n'
        pending = self.request(arguments={"logic": source})
        self.assertEqual(pending["code_preview"], 'op abs result x\njump 0 always\n')
        self.assertEqual(pending["parameter_cleanup"], [
            {"line": 1, "removed": ["b"]}, {"line": 2, "removed": ["a", "b"]}])
        self.assertTrue(pending["signature_required"])
        out = self.apps.submit({"request_id": pending["request_id"], "author": "Iliary"}, "alice", lambda name: True)
        code = mlog_mcp.msch.parse_bytes(base64.b64decode(out["result"]["blueprint_base64"])).logic_tiles()[0].logic.code
        self.assertIn('op abs result x\n', code)
        self.assertTrue(out["signed"])
        delivered = mlog_mcp.tool_gen({"logic": 'print "hello" a b\nend\n'})
        self.assertFalse(delivered["signed"])
        self.assertEqual(delivered["parameter_cleanup"], [{"line": 1, "removed": ["a", "b"]}])
        code = mlog_mcp.msch.parse_bytes(base64.b64decode(delivered["blueprint_base64"])).logic_tiles()[0].logic.code
        self.assertEqual(code.strip(), 'print "hello"\nend')

    def test_full_jump_signs_in_form_and_no_slot_is_delivered_unsigned(self):
        pending = self.request(arguments={"logic": "set x 1\njump 0 always 0 0\n"})
        reply = self.apps.handle({"jsonrpc": "2.0", "id": 97, "method": "tools/call", "params": {
            "name": "mlog_signature_submit", "arguments": {"request_id": pending["request_id"], "author": "Iliary"}}}, principal="alice")
        self.assertFalse(reply["result"]["isError"])
        self.assertEqual(reply["result"]["structuredContent"]["status"], "complete")
        pending = self.request(arguments={"logic": "set x 1\nend\n"})
        reply = self.apps.handle({"jsonrpc": "2.0", "id": 98, "method": "tools/call", "params": {
            "name": "mlog_signature_submit", "arguments": {"request_id": pending["request_id"], "author": "Iliary"}}}, principal="alice")
        self.assertFalse(reply["result"]["isError"])
        data = reply["result"]["structuredContent"]
        self.assertFalse(data["signed"])
        self.assertEqual(data["status"], "complete")
        self.assertIn("no safe signature slot", data["result"]["warning"])

    def test_no_slot_skips_author_form_without_adding_or_changing_instructions(self):
        original = "set x 1\nend\n"
        before = len(self.apps.requests)
        _, reply = mlog_mcp_http_profiles.dispatch({"jsonrpc": "2.0", "id": 99, "method": "tools/call",
            "params": {"name": "mlog_gen", "arguments": {"logic": original}}}, apps=self.apps)
        self.assertFalse(reply["result"]["isError"])
        data = reply["result"]["structuredContent"]
        self.assertEqual(data["status"], "complete")
        self.assertFalse(data["signed"])
        code = mlog_mcp.msch.parse_bytes(base64.b64decode(data["result"]["blueprint_base64"])).logic_tiles()[0].logic.code
        self.assertEqual(code.strip(), original.strip())
        self.assertEqual(len(self.apps.requests), before)
        pending = self.request(arguments={"logic": original})
        self.assertFalse(pending["signature_required"])
        self.assertFalse(self.apps.submit({"request_id": pending["request_id"]}, "alice", lambda name: True)["signed"])

    def test_unsigned_fallback_preserves_revision_checks_and_rejects_tampered_signatures(self):
        import mschgen, aigenerated
        blueprint = mschgen.Blueprint("unsigned-inject")
        blueprint.add_logic("set n 1\nend\n")
        encoded = base64.b64encode(blueprint.build()).decode()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory, patch.dict(os.environ, {"MLOG_REVISION_DIR": directory}):
            out = mlog_mcp.tool_inject({"blueprint_code": encoded, "index": 0, "mlog": "set x 1\nend\n"})
            self.assertFalse(out["signed"])
            self.assertTrue(out["revision"])
            code = mlog_mcp.msch.parse_bytes(base64.b64decode(out["blueprint_base64"])).logic_tiles()[0].logic.code
            self.assertEqual(code.strip(), "set x 1\nend")
            conflict = mlog_mcp.tool_inject({"blueprint_code": encoded, "index": 0, "mlog": "set x 1\nend\n", "expected_sha256": "0"*64})
            self.assertEqual(conflict["failure_type"], "source_conflict")
        signed, _ = aigenerated.sign_text(self.arguments["logic"], "Iliary")
        tampered = signed.replace("set n 42", "set n 43")
        with self.assertRaisesRegex(ValueError, "invalid signature"):
            mlog_mcp.tool_gen({"logic": tampered})

    def test_original_generation_tool_routes_missing_author_to_reopenable_form(self):
        for dispatch in (
                lambda req: mlog_mcp_http.dispatch(req, apps=self.apps)[1],
                lambda req: mlog_mcp_http_profiles.dispatch(req, principal="alice", apps=self.apps)[1]):
            req = {"jsonrpc": "2.0", "id": 91, "method": "tools/call",
                   "params": {"name": "mlog_gen", "arguments": dict(self.arguments)}}
            with patch.object(mlog_mcp._blueprints, "generate") as generate:
                reply = dispatch(req)
                generate.assert_not_called()
            result = reply["result"]
            self.assertFalse(result["isError"])
            self.assertEqual(result["structuredContent"]["status"], "pending")
            self.assertEqual(result["_meta"]["ui"]["resourceUri"], SIGNATURE_URI)
            followup = result["structuredContent"]["next_action"]
            self.assertEqual(followup["tool"], "mlog_signature_request")
            reopened = dispatch({"jsonrpc": "2.0", "id": 92, "method": "tools/call",
                                 "params": {"name": followup["tool"], "arguments": followup["arguments"]}})
            self.assertEqual(reopened["result"]["structuredContent"]["request_id"],
                             result["structuredContent"]["request_id"])

    def test_generation_descriptor_and_explicit_author_delivery_match_ui(self):
        _, reply = mlog_mcp_http.dispatch({"jsonrpc": "2.0", "id": 93, "method": "tools/list"}, apps=self.apps)
        tool = next(t for t in reply["result"]["tools"] if t["name"] == "mlog_gen")
        self.assertIn("author", tool["inputSchema"]["properties"])
        self.assertEqual(tool["_meta"]["ui"]["resourceUri"], SIGNATURE_URI)
        self.assertIn("automatically", tool["description"])
        _, reply = mlog_mcp_http.dispatch({"jsonrpc": "2.0", "id": 94, "method": "tools/call",
            "params": {"name": "mlog_gen", "arguments": {**self.arguments, "author": "Alice"}}}, apps=self.apps)
        data = reply["result"]["structuredContent"]
        self.assertEqual(data["status"], "complete")
        self.assertEqual(data["author"], "Alice")
        self.assertTrue(data["result"]["signed"])

    def test_ui_is_absent_by_default_and_explicitly_enabled_over_http(self):
        for flags in ((), ("--enable-ui",)):
            server = Server(*flags)
            try:
                _, raw, _ = server.post({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                names = [t["name"] for t in json.loads(raw)["result"]["tools"]]
                self.assertEqual("mlog_signature_request" in names, bool(flags))
                _, raw, _ = server.post({"jsonrpc": "2.0", "id": 2, "method": "resources/read",
                                          "params": {"uri": SIGNATURE_URI}})
                reply = json.loads(raw)
                if flags:
                    resource = reply["result"]["contents"][0]
                    self.assertEqual(resource["mimeType"], MIME)
                    self.assertIn("确认作者签名", resource["text"])
                else:
                    self.assertIn("error", reply)
            finally:
                server.close()

    def test_ui_resources_use_existing_http_authentication(self):
        server = Server("--enable-ui", "--token", "apps-test-token")
        try:
            request = {"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": SIGNATURE_URI}}
            self.assertEqual(server.post(request)[0], 401)
            self.assertEqual(server.post(request, token="apps-test-token")[0], 200)
        finally:
            server.close()

    def test_signature_is_pending_until_submit_and_replay_is_idempotent(self):
        before = mlog_mcp._cached_author()
        with patch.object(mlog_mcp._blueprints, "generate", wraps=mlog_mcp._blueprints.generate) as generate:
            pending = self.request()
            generate.assert_not_called()
            self.arguments["logic"] = "set n 99\n"
            submit = {"request_id": pending["request_id"], "author": "测试作者"}
            signed = self.apps.submit(submit, "alice", lambda name: True)
            again = self.apps.submit(submit, "alice", lambda name: True)
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(signed, again)
        self.assertEqual(signed["status"], "complete")
        self.assertTrue(signed["result"]["signed"])
        schematic = mlog_mcp.msch.parse_bytes(base64.b64decode(signed["result"]["blueprint_base64"]))
        code = schematic.logic_tiles()[0].logic.code
        import aigenerated
        self.assertEqual(aigenerated.verify_text(code), [])
        self.assertIn("set n 42", code)
        self.assertEqual(mlog_mcp._cached_author(), before)

    def test_request_cannot_cross_principals_expire_or_lose_permissions(self):
        pending = self.request()
        args = {"request_id": pending["request_id"], "author": "Alice"}
        with self.assertRaisesRegex(ValueError, "not found"):
            self.apps.submit(args, "bob", lambda name: True)
        with self.assertRaisesRegex(ValueError, "no longer permitted"):
            self.apps.submit(args, "alice", lambda name: False)
        self.apps.clock = lambda: time.monotonic() + 901
        with self.assertRaisesRegex(ValueError, "expired"):
            self.apps.submit(args, "alice", lambda name: True)

    def test_inject_form_previews_without_an_author_and_confirms_the_saved_target(self):
        import mschgen
        blueprint = mschgen.Blueprint("form-inject")
        blueprint.add_logic("set n 1\njump 0 always 0\n")
        encoded = base64.b64encode(blueprint.build()).decode()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory, \
                patch.dict(os.environ, {"MLOG_REVISION_DIR": directory}):
            pending = self.request(operation="mlog_inject", arguments={"blueprint_code": encoded,
                                   "index": 0, "mlog": self.arguments["logic"]})
            self.assertEqual(list(Path(directory).iterdir()), [])
            self.assertIn("target", pending)
            signed = self.apps.submit({"request_id": pending["request_id"], "author": "Alice"},
                                      "alice", lambda name: True)
            self.assertTrue(signed["result"]["signed"])
            self.assertTrue(signed["result"]["revision"])
            code = mlog_mcp.msch.parse_bytes(base64.b64decode(signed["result"]["blueprint_base64"])).logic_tiles()[0].logic.code
            self.assertIn("set n 42", code)

    def test_existing_author_cannot_be_changed_and_failed_submission_can_retry(self):
        import aigenerated
        signed, _ = aigenerated.sign_text(self.arguments["logic"], "Original")
        pending = self.request(arguments={"logic": signed})
        self.assertTrue(pending["author_locked"])
        with self.assertRaisesRegex(ValueError, "cannot be replaced"):
            self.apps.submit({"request_id": pending["request_id"], "author": "Other"}, "alice", lambda name: True)
        pending = self.request()
        args = {"request_id": pending["request_id"], "author": "Alice"}
        with patch.object(mlog_mcp._blueprints, "generate", side_effect=RuntimeError("worker failed")):
            with self.assertRaisesRegex(RuntimeError, "worker failed"):
                self.apps.submit(args, "alice", lambda name: True)
        self.assertEqual(self.apps.requests[pending["request_id"]]["status"], "pending")
        self.assertEqual(self.apps.submit(args, "alice", lambda name: True)["status"], "complete")

    def test_signature_source_is_snapshotted_and_outputs_are_not_written(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            source = Path(directory) / "source.mlog"
            source.write_text(self.arguments["logic"], encoding="utf-8")
            pending = self.request(arguments={"source": str(source)})
            source.write_text("set n 99\n", encoding="utf-8")
            record = self.apps.requests[pending["request_id"]]
            self.assertIn("set n 42", record["arguments"]["logic"])
            self.assertNotIn("source", record["arguments"])
        for key, value in (("out", "anything.msch"), ("allow_unsigned", True)):
            with self.assertRaisesRegex(ValueError, "signed delivery"):
                self.request(arguments={**self.arguments, key: value})

    def test_profile_filters_resources_tools_and_underlying_permissions(self):
        request = {"jsonrpc": "2.0", "id": 4, "method": "tools/list"}
        for profile in ("reader", "runner"):
            _, reply = mlog_mcp_http_profiles.dispatch(request, profile=profile, apps=self.apps)
            tools = reply["result"]["tools"]
            ui_tools = [t for t in tools if t["name"] == "mlog_signature_request"]
            self.assertEqual(bool(ui_tools), profile == "runner")
            _, resources = mlog_mcp_http_profiles.dispatch(
                {"jsonrpc": "2.0", "id": 5, "method": "resources/list"}, profile=profile, apps=self.apps)
            self.assertEqual(bool(resources["result"]["resources"]), profile == "runner")
        allowed = lambda name: name in {"mlog_signature_request", "mlog_signature_submit"}
        self.assertEqual(self.apps.catalog(allowed), [])
        with self.assertRaisesRegex(ValueError, "not permitted"):
            self.apps.read_resource(SIGNATURE_URI, allowed)
        self.assertTrue(all("_meta" not in t for t in mlog_mcp.TOOLS))

    def test_resources_are_self_contained_and_unknown_uris_are_refused(self):
        for uri in (SIGNATURE_URI, DASHBOARD_URI):
            resource = self.apps.read_resource(uri, lambda name: True)["contents"][0]
            self.assertNotIn("APP_SCRIPT", resource["text"])
            self.assertNotIn("APP_STYLE", resource["text"])
            self.assertNotIn("<script src=", resource["text"])
            self.assertEqual(resource["_meta"]["ui"]["csp"]["connectDomains"], [])
        with self.assertRaises(ValueError):
            self.apps.read_resource("ui://mlogent/../../secret", lambda name: True)

    def test_dashboard_is_read_only_and_reports_partial_failure(self):
        status, players = unittest.mock.Mock(return_value={"ok": True, "map": "测试", "players": 1}), \
            unittest.mock.Mock(return_value={"ok": True, "rows": [{"name": "Alice"}]})
        with patch.dict(self.apps.world.HANDLERS, {"world_status": status, "world_players": players}):
            out = self.apps.dashboard()
            self.assertTrue(out["ok"])
            self.assertEqual(out["players"][0]["name"], "Alice")
            status.assert_called_once_with({})
            players.assert_called_once_with({})
            players.side_effect = RuntimeError("control port refused")
            out = self.apps.dashboard()
            self.assertTrue(out["ok"])
            self.assertIn("control port refused", out["errors"][0])


class ProfileOAuth(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mlog-oauth-test-")
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name) / "oauth_state.json"
        self.patches = [
            patch.object(mlog_oauth, "STORE", str(self.store)),
            patch.object(mlog_oauth, "ENABLED", True),
            patch.object(mlog_oauth, "BASE", "https://mcp.example.test"),
            patch.object(mlog_acl, "match_password",
                         return_value={"name": "test-user", "profile": "reader"}),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    @staticmethod
    def _body(fields):
        return urlencode(fields).encode("utf-8")

    def _register(self, redirect_uri="http://127.0.0.1:43123/callback"):
        raw = json.dumps({"client_name": "test client", "redirect_uris": [redirect_uri]}).encode()
        status, _, body, _ = mlog_oauth.route("POST", "/register", {}, {}, raw)
        self.assertEqual(status, 201)
        return json.loads(body)

    def _authorize(self, client, redirect_uri):
        verifier = "verifier-for-the-oauth-profile-test"
        digest = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).decode("ascii").rstrip("=")
        query = {
            "client_id": client["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "code_challenge_method": "S256",
            "code_challenge": digest,
            "state": "test-state",
        }
        status, _, page, _ = mlog_oauth.route("GET", "/authorize", query, {}, b"")
        self.assertEqual(status, 200)
        self.assertIn(b"test client", page)
        form = {
            **query,
            "password": "correct-password",
        }
        status, _, _, headers = mlog_oauth.route(
            "POST", "/authorize", {}, {}, self._body(form))
        self.assertEqual(status, 302)
        location = urlsplit(headers["Location"])
        code = parse_qs(location.query)["code"][0]
        return code, verifier

    def test_code_and_refresh_tokens_are_single_use_and_store_is_private(self):
        redirect_uri = "http://127.0.0.1:43123/callback"
        client = self._register(redirect_uri)
        code, verifier = self._authorize(client, redirect_uri)
        token_body = self._body({
            "grant_type": "authorization_code",
            "client_id": client["client_id"],
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": verifier,
        })
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(
                lambda _: mlog_oauth.route("POST", "/token", {}, {}, token_body), range(2)))
        self.assertEqual(sorted(result[0] for result in results), [200, 400])
        issued = json.loads(next(result[2] for result in results if result[0] == 200))
        self.assertEqual(mlog_oauth.resolve(issued["access_token"])["profile"], "reader")
        if os.name != "nt":
            self.assertEqual(self.store.stat().st_mode & 0o777, 0o600)

        refresh_body = self._body({
            "grant_type": "refresh_token",
            "client_id": client["client_id"],
            "refresh_token": issued["refresh_token"],
        })
        refreshed = mlog_oauth.route("POST", "/token", {}, {}, refresh_body)
        reused = mlog_oauth.route("POST", "/token", {}, {}, refresh_body)
        self.assertEqual(refreshed[0], 200)
        self.assertEqual(reused[0], 400)

    def test_registration_rejects_untrusted_or_malformed_redirect_uris(self):
        for uris in (
            "https://client.example/callback",
            ["http://attacker.example/callback"],
            ["javascript:alert(1)"],
            ["https://client.example/callback#fragment"],
        ):
            with self.subTest(uris=uris):
                body = json.dumps({"redirect_uris": uris}).encode()
                result = mlog_oauth.route("POST", "/register", {}, {}, body)
                self.assertEqual(result[0], 400)

    def test_unsupported_authorize_method_is_rejected(self):
        self.assertEqual(mlog_oauth.route("PUT", "/authorize", {}, {}, b"")[0], 405)

    def test_malformed_state_file_fails_closed(self):
        self.store.write_text("[]", encoding="utf-8")
        self.assertEqual(mlog_oauth._load(), mlog_oauth._empty())
        self.assertIsNone(mlog_oauth.resolve("not-a-token"))


class ProfilePolicy(unittest.TestCase):
    def test_tool_call_waits_for_a_busy_mcp_worker(self):
        lock = mlog_mcp_http_profiles._LOCK
        self.assertTrue(lock.acquire(timeout=1))

        def handle(payload, emit):
            emit({"jsonrpc": "2.0", "id": payload.get("id"),
                  "result": {"content": [{"type": "text", "text": "ok"}],
                             "isError": False}})

        request = {"jsonrpc": "2.0", "id": 91, "method": "tools/call",
                   "params": {"name": "mlog_check", "arguments": {}}}
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                with patch.object(mlog_mcp_http_profiles.M, "handle", side_effect=handle):
                    pending = pool.submit(mlog_mcp_http_profiles.dispatch, request)
                    time.sleep(0.05)
                    self.assertFalse(pending.done())
                    lock.release()
                    _, reply = pending.result(timeout=2)
        finally:
            if lock.locked():
                lock.release()

        self.assertFalse(reply["result"]["isError"])

    def test_tools_list_is_filtered_by_profile(self):
        profile_data = ({
            "reader": {"label": "reader", "rpm": 30,
                       "tools": ["mlog_check", "world_status"]},
            "runner": {"label": "runner", "rpm": 120, "tools": ["*"]},
        }, [], "runner")

        def handle(payload, emit):
            emit({"jsonrpc": "2.0", "id": payload.get("id"),
                  "result": {"tools": [{"name": "mlog_check"}, {"name": "mlog_sim"}]}})

        with patch.object(mlog_acl, "_table", return_value=profile_data):
            with patch.object(mlog_mcp_http_profiles.M, "handle", side_effect=handle):
                _, reply = mlog_mcp_http_profiles.dispatch(
                    {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, profile="reader")
        names = {tool["name"] for tool in reply["result"]["tools"]}
        self.assertEqual(names, {"mlog_check", "world_status"})

    def test_resource_policy_bounds_heavy_simulation(self):
        self.assertIsNone(mlog_resource_policy.refusal("mlog_sim", {"ticks": 1800}))
        self.assertIn("ticks", mlog_resource_policy.refusal("mlog_sim", {"ticks": 1801}))
        self.assertIn("KiB", mlog_resource_policy.refusal("world_status", {
            "query": "x" * (128 * 1024 + 1),
        }))

    def test_malformed_profile_file_falls_back_to_default_profiles(self):
        with tempfile.TemporaryDirectory(prefix="mlog-acl-test-") as temp:
            path = Path(temp) / "users.json"
            path.write_text('{"profiles": [], "users": null, "static_profile": {}}', encoding="utf-8")
            with patch.object(mlog_acl, "USERS_FILE", str(path)):
                self.assertEqual(mlog_acl.rpm("reader"), 30)
                self.assertEqual(mlog_acl.static_profile(), "reader")
                self.assertTrue(mlog_acl.allows("runner", "world_js"))
                self.assertFalse(mlog_acl.allows("reader", "world_js"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
