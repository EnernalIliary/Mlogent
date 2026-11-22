"""Opt-in MCP Apps resources and tools. No changes to the existing tool surface.

Requests hold immutable inputs in a bounded, expiring, principal-scoped store.
The UI only submits a request id and author; it cannot replace reviewed code.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import base64
import hashlib
import json
from pathlib import Path
import secrets
import threading
import time

MIME = "text/html;profile=mcp-app"
SIGNATURE_URI = "ui://mlogent/signature-v1.html"
DASHBOARD_URI = "ui://mlogent/world-dashboard-v1.html"
ASSETS = Path(__file__).with_name("ui")
NAMES = frozenset({"mlog_signature_request", "mlog_signature_submit", "world_dashboard"})


def _tool(name, description, schema, uri=None, *, readonly=True, app_only=False):
    meta = {"ui": {"visibility": ["app"] if app_only else ["model", "app"]},
            "openai/widgetAccessible": True}
    if uri:
        meta["ui"]["resourceUri"] = uri
        meta["openai/outputTemplate"] = uri
    return {"name": name, "description": description, "inputSchema": schema,
            "outputSchema": {"type": "object"}, "_meta": meta,
            "annotations": {"readOnlyHint": readonly, "destructiveHint": False,
                            "openWorldHint": False}}


def _object(properties=None, required=None):
    return {"type": "object", "properties": properties or {},
            "required": required or [], "additionalProperties": False}


class Apps:
    def __init__(self, mcp, world=None, *, clock=time.monotonic):
        self.mcp, self.world, self.clock = mcp, world, clock
        self.requests = {}
        self.lock = threading.Lock()
        self.ttl = 900
        self.limit = 128
        self.tools = [
            _tool("mlog_signature_request",
                  "Open an author signature form in ChatGPT before generating or injecting a blueprint. "
                  "Creates a pending request only; no blueprint is written until the user submits the form. "
                  "Use the original mlog_gen/mlog_inject tools for text-only workflows.",
                  _object({"operation": {"type": "string", "enum": ["mlog_gen", "mlog_inject"]},
                           "arguments": {"type": "object", "description":
                                         "Arguments for the selected tool; output paths and unsigned delivery are not supported."}},
                          []), SIGNATURE_URI),
            _tool("mlog_signature_submit", "Submit the author for an existing signature request. "
                  "Author is optional for inputs without a safe signature slot; those are delivered unsigned. "
                  "Uses the saved reviewed inputs; repeated submission returns the existing result.",
                  _object({"request_id": {"type": "string"},
                           "author": {"type": "string", "maxLength": 100}},
                          ["request_id"]), readonly=False, app_only=True),
        ]
        if world is not None:
            self.tools.append(_tool("world_dashboard", "Open or refresh the read-only world dashboard: "
                                    "live server status and online players. Does not change the game.",
                                    _object(), DASHBOARD_URI))
        request_schema = self.tools[0]["inputSchema"]
        request_schema["properties"]["request_id"] = {"type": "string", "description": "Reopen an existing pending form returned by mlog_gen/mlog_inject."}
        request_schema["oneOf"] = [{"required": ["operation", "arguments"]},
                                   {"required": ["request_id"]}]

    def decorate(self, tools, allowed=lambda name: True):
        """Bind legacy delivery tools too, so missing authors open the form directly."""
        tools = deepcopy(tools)
        can_sign = self.permitted("mlog_signature_request", allowed) and self.permitted("mlog_signature_submit", allowed)
        for tool in tools:
            if tool["name"] in ("mlog_gen", "mlog_inject") and can_sign and allowed(tool["name"]):
                tool["_meta"] = _tool("", "", {}, SIGNATURE_URI)["_meta"]
                tool["outputSchema"] = {"type": "object"}
                tool["description"] += (" With UI enabled, omitting author on unsigned input automatically opens "
                                         "the author signature form; wait for the user to submit it. "
                                         "Inputs without a safe signature slot are delivered unsigned directly. "
                                         "Do not invent an author. Pass author explicitly for text-only delivery.")
            elif tool["name"] == "mlog_doctor":
                tool["description"] += " For an interactive world status view use world_dashboard instead."
        return tools

    def _unsigned_without_author(self, name, args):
        if args.get("author") or args.get("allow_unsigned") or args.get("preview"):
            return False
        code = args.get("logic" if name == "mlog_gen" else "mlog")
        if name == "mlog_gen" and args.get("source"):
            code = self.mcp._blueprint_context().workspace_input_path(args["source"], (".mlog",)).read_text(encoding="utf-8-sig")
        if not isinstance(code, str) or not code.strip():
            return False
        import aigenerated
        return not aigenerated._find(code) and self.mcp._blueprints.has_signature_slot(code)

    def decorate_reply(self, payload, reply, allowed=lambda name: True):
        if payload.get("method") != "tools/call" or not reply or "result" not in reply:
            return reply
        name = (payload.get("params") or {}).get("name")
        result = reply["result"]
        if result.get("isError"):
            return reply
        if name == "mlog_doctor":
            data = json.loads(result["content"][0]["text"])
            data["ui"] = {"enabled": True, "available_tools": [t["name"] for t in self.catalog(allowed)
                           if "model" in t["_meta"]["ui"]["visibility"]],
                          "hint": "Use world_dashboard for the interactive world view; unsigned mlog_gen/mlog_inject calls open the author form."}
            result["content"][0]["text"] = json.dumps(data, ensure_ascii=False)
            return reply
        if name not in ("mlog_gen", "mlog_inject") or not self.permitted("mlog_signature_request", allowed):
            return reply
        if "structuredContent" not in result:
            output = json.loads(result["content"][0]["text"])
            if output.get("ok") is False:
                return reply
            author = (payload.get("params", {}).get("arguments") or {}).get("author", "")
            if output.get("blueprint_base64") and output.get("signed"):
                import aigenerated
                schematic = self.mcp.msch.parse_bytes(base64.b64decode(output["blueprint_base64"]))
                hits = [h for tile in schematic.logic_tiles() for h in aigenerated._find(tile.logic.code)]
                if hits:
                    author = hits[0].group(1)
            data = {"kind": "signature", "status": "preview" if output.get("mode") == "preview" else "complete",
                    "author": author, "signed": output.get("signed"), "result": output}
            result["structuredContent"] = data
            result["content"][0]["text"] = json.dumps(data, ensure_ascii=False)
        result["_meta"] = {"ui": {"resourceUri": SIGNATURE_URI}, "openai/outputTemplate": SIGNATURE_URI}
        return reply

    def permitted(self, name, allowed):
        if not allowed(name):
            return False
        if name.startswith("mlog_signature_"):
            return allowed("mlog_gen") or allowed("mlog_inject")
        return self.world is not None and allowed("world_status") and allowed("world_players")

    def catalog(self, allowed=lambda name: True):
        return deepcopy([t for t in self.tools if self.permitted(t["name"], allowed)])

    def _resources(self, allowed):
        return [(SIGNATURE_URI, "作者签名", "mlog_signature_request"),
                (DASHBOARD_URI, "世界仪表盘", "world_dashboard")]

    def resources(self, allowed):
        return [{"uri": uri, "name": title, "mimeType": MIME}
                for uri, title, name in self._resources(allowed) if self.permitted(name, allowed)]

    def read_resource(self, uri, allowed):
        if uri not in [r["uri"] for r in self.resources(allowed)]:
            raise ValueError("UI resource not found or not permitted")
        page = "signature" if uri == SIGNATURE_URI else "dashboard"
        html = (ASSETS / (page + ".html")).read_text(encoding="utf-8")
        html = html.replace("/* APP_STYLE */", (ASSETS / "style.css").read_text(encoding="utf-8"))
        html = html.replace("/* APP_SCRIPT */", (ASSETS / "app.js").read_text(encoding="utf-8"))
        return {"contents": [{"uri": uri, "mimeType": MIME, "text": html,
                "_meta": {"ui": {"prefersBorder": True,
                                   "csp": {"connectDomains": [], "resourceDomains": []}},
                          "openai/widgetDescription": "Mlogent " + page,
                          "openai/widgetPrefersBorder": True,
                          "openai/widgetCSP": {"connect_domains": [], "resource_domains": []}}}]}

    def _prune(self):
        now = self.clock()
        for key in list(self.requests):
            if now >= self.requests[key]["expires"] and self.requests[key]["status"] != "submitting":
                del self.requests[key]

    def request(self, args, principal, allowed):
        if "request_id" in args:
            if set(args) != {"request_id"}:
                raise ValueError("request_id cannot be combined with new request arguments")
            with self.lock:
                self._prune()
                record = self.requests.get(args["request_id"])
                if not record or record["principal"] != principal or not allowed(record["operation"]):
                    raise ValueError("signature request expired, not found or not permitted")
                return deepcopy(record.get("result") or record["view"])
        operation = args.get("operation")
        if operation not in ("mlog_gen", "mlog_inject") or not allowed(operation):
            raise ValueError("operation is invalid or not permitted")
        payload = args.get("arguments")
        if not isinstance(payload, dict) or len(json.dumps(payload).encode()) > 512 * 1024:
            raise ValueError("arguments must be an object within 512 KiB")
        payload = deepcopy(payload)
        schema = next(t["inputSchema"] for t in self.mcp.TOOLS if t["name"] == operation)
        if set(payload) - set(schema["properties"]):
            raise ValueError("unknown arguments for selected tool")
        if payload.get("allow_unsigned") or payload.get("out") or payload.get("preview"):
            raise ValueError("signature requests require signed delivery without output paths or preview mode")
        context = self.mcp._blueprint_context()
        context = replace(context, get_author=lambda: None, set_author=lambda value: None)
        target = None
        cleanup = []
        if operation == "mlog_gen":
            if bool(payload.get("logic")) == bool(payload.get("source")):
                raise ValueError("provide exactly one of logic or source")
            if payload.get("source"):
                payload["logic"] = context.workspace_input_path(payload.pop("source"), (".mlog",)).read_text(encoding="utf-8-sig")
            code = payload.get("logic")
            if isinstance(code, str):
                code, cleanup = self.mcp._blueprints.clean_parameters(code)
                payload["logic"] = code
        else:
            if bool(payload.get("path")) == bool(payload.get("blueprint_code")):
                raise ValueError("provide exactly one of blueprint_code or path")
            if payload.get("path"):
                raw = context.workspace_input_path(payload.pop("path"), (".msch",)).read_bytes()
                payload["blueprint_code"] = (base64.b64encode(raw).decode() if raw.startswith(b"msch")
                                             else raw.decode("utf-8-sig"))
            code = payload.get("mlog")
            if isinstance(code, str):
                code, cleanup = self.mcp._blueprints.clean_parameters(code)
                payload["mlog"] = code
            # Reuse the original preview to check target selection and expected revision.
            preview = self.mcp._blueprints.inject({**payload, "author": "pending", "preview": True}, context=context)
            if not preview.get("ok"):
                raise ValueError(preview.get("message") or "invalid blueprint target")
            payload["expected_sha256"] = preview["source_sha256"]
            target = {"processor": preview["processor"], "source_sha256": preview["source_sha256"]}
        if not isinstance(code, str) or not code.strip():
            raise ValueError("a non-empty program is required")
        import aigenerated
        hits = aigenerated._find(code)
        if hits and aigenerated.verify_text(code):
            raise ValueError("input contains an invalid signature")
        existing_author = hits[0].group(1) if hits else ""
        digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
        request_id = secrets.token_urlsafe(24)
        view = {"kind": "signature", "status": "pending", "request_id": request_id,
                "operation": operation, "name": str(payload.get("name") or "未命名蓝图"),
                "sha256": digest, "lines": len(code.splitlines()), "code_preview": code[:6000],
                "preview_truncated": len(code) > 6000, "expires_in": self.ttl,
                "author": existing_author or str(payload.get("author") or ""),
                "author_locked": bool(existing_author)}
        view["signature_required"] = bool(hits) or self.mcp._blueprints.has_signature_slot(code)
        if cleanup:
            view["parameter_cleanup"] = cleanup
        if target is not None:
            view["target"] = target
        with self.lock:
            self._prune()
            if len(self.requests) >= self.limit:
                raise ValueError("too many pending signature requests; retry after they expire")
            self.requests[request_id] = {"principal": principal, "operation": operation,
                                       "arguments": payload, "expires": self.clock() + self.ttl,
                                       "status": "pending", "view": view}
        return deepcopy(view)

    def submit(self, args, principal, allowed):
        author = args.get("author", "")
        if (not isinstance(author, str) or len(author) > 100
                or any(ord(c) < 32 or ord(c) == 127 or c in ':"' for c in author)):
            raise ValueError('author must contain 1–100 printable characters without colon or double quote')
        author = author.strip()
        with self.lock:
            self._prune()
            record = self.requests.get(args.get("request_id"))
            if not record or record["principal"] != principal:
                raise ValueError("signature request expired or not found")
            if not allowed(record["operation"]):
                raise ValueError("signature operation is no longer permitted")
            view = record["view"]
            if view.get("signature_required", True) and not author:
                raise ValueError("an author is required for this signature request")
            if view["author_locked"] and author != view["author"]:
                raise ValueError("existing signed author cannot be replaced")
            if record["status"] == "complete":
                if author != record["author"]:
                    raise ValueError("request already signed by another author")
                return deepcopy(record["result"])
            if record["status"] != "pending":
                raise ValueError("signature request is already being submitted")
            record["status"] = "submitting"
        try:
            # UI authors must not read or mutate the legacy process-wide author cache.
            context = replace(self.mcp._blueprint_context(), get_author=lambda: None,
                              set_author=lambda value: None)
            fn = (self.mcp._blueprints.generate if record["operation"] == "mlog_gen"
                  else self.mcp._blueprints.inject)
            output = fn({**record["arguments"], "author": author, "allow_unsigned": False}, context=context)
            if output.get("ok") is False or (output.get("signed") is False and view.get("signature_required", True)):
                raise ValueError(output.get("message") or output.get("warning") or "signature failed")
            result = {**view, "status": "complete", "author": author, "signed": output.get("signed"), "result": output}
        except Exception:
            with self.lock:
                record["status"] = "pending"
            raise
        with self.lock:
            record.update(status="complete", author=author, result=result)
        return deepcopy(result)

    def dashboard(self):
        errors, status, players = [], {}, {}
        for name, target in (("world_status", status), ("world_players", players)):
            try:
                target.update(self.world.HANDLERS[name]({}))
                if target.get("ok") is False:
                    errors.append(str(target.get("error") or name + " failed"))
            except Exception as exc:
                errors.append(name + ": " + str(exc))
        return {"kind": "dashboard", "ok": bool(status.get("ok")), "status": status,
                "players": players.get("rows", []), "errors": errors,
                "updated_at": datetime.now(timezone.utc).isoformat()}

    def call(self, name, args, principal, allowed):
        if not self.permitted(name, allowed):
            raise ValueError("UI tool is not permitted")
        if name == "mlog_signature_request":
            return self.request(args, principal, allowed)
        if name == "mlog_signature_submit":
            return self.submit(args, principal, allowed)
        if name == "world_dashboard":
            return self.dashboard()
        raise ValueError("unknown UI tool")

    def handle(self, payload, principal="static", allowed=lambda name: True):
        """Return None for legacy methods; otherwise a complete JSON-RPC reply."""
        method, rid = payload.get("method"), payload.get("id")
        params = payload.get("params") or {}
        if not isinstance(params, dict):
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "params must be an object"}}
        name = params.get("name")
        legacy = method == "tools/call" and name in ("mlog_gen", "mlog_inject")
        if method not in ("resources/list", "resources/read") and not (method == "tools/call" and name in NAMES) and not legacy:
            return None
        try:
            if method == "resources/list":
                result = {"resources": self.resources(allowed)}
            elif method == "resources/read":
                result = self.read_resource(params.get("uri"), allowed)
            else:
                arguments = params.get("arguments", {})
                if not isinstance(arguments, dict):
                    raise ValueError("arguments must be an object")
                if legacy:
                    if (not allowed(name) or not self.permitted("mlog_signature_request", allowed)
                            or not self.permitted("mlog_signature_submit", allowed)
                            or not self._unsigned_without_author(name, arguments)):
                        return None
                    data = self.request({"operation": name, "arguments": arguments}, principal, allowed)
                    data["message"] = "Author signature required. Show the attached form and wait for user input; do not invent an author or retry generation. If the form is not shown, reopen it using next_action."
                    data["next_action"] = {"tool": "mlog_signature_request", "arguments": {"request_id": data["request_id"]}}
                else:
                    data = self.call(name, arguments, principal, allowed)
                result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
                          "structuredContent": data, "isError": False}
            return {"jsonrpc": "2.0", "id": rid, "result": result}
        except Exception as exc:
            message = str(exc)
            if "no safe signature slot" in message:
                message = ("无法签名：代码中没有可复用的无条件跳转签名槽。支持 jump <目标> always 0 "
                           "和 jump <目标> always 0 0。请保持原有控制流后重新提交代码；不会自动追加指令。")
            if method == "tools/call":
                return {"jsonrpc": "2.0", "id": rid, "result": {
                    "content": [{"type": "text", "text": message}], "isError": True}}
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": message}}
