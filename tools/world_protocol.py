"""JSON-line TCP transport and TSV result codecs for the persistent world.

The caller supplies the world, dispatcher and shutdown callback. Importing this
module does not load the daemon, start a JVM or access its persistent directory.
"""
from __future__ import annotations

import json
import re
import socketserver

_NUM = re.compile(r"^-?\d+(\.\d+)?$")


def coerce(v: str):
    """把 JS 拼出来的 "149.0" 还原成 149; 非数字原样返回."""
    if isinstance(v, str) and _NUM.match(v):
        f = float(v)
        return int(f) if f.is_integer() else f
    return v



def units_table(rows: list[dict]) -> str:
    """把 units 的 JSON 行渲染成对齐的纯文本表（给人/agent 直接读）。"""
    if not rows:
        return "(no units)"
    ctrl_names = {0: "free", 1: "logic", 2: "player", 3: "command"}
    body = []
    for r in rows:
        item = r.get("item")
        carry = r.get("carry")
        cap = r.get("itemCapacity")
        kit = "-" if item in (None, "-", "") else "%s %s/%s" % (item, carry, cap)
        ctrl = ctrl_names.get(r.get("controlled"), str(r.get("controlled")))
        body.append([
            str(r.get("id")), str(r.get("type")),
            "%s,%s" % (r.get("x"), r.get("y")),
            str(r.get("controller")), kit,
            str(r.get("flag")), ctrl,
            "1" if r.get("mining") == 1 else "0",
            "1" if r.get("boosting") == 1 else "0",
            "%s/%s" % (r.get("health"), r.get("maxHealth")),
        ])
    head = ["id", "type", "tile", "controller", "items", "flag", "ctrl", "mine", "boost", "hp"]
    widths = [max(len(head[i]), *(len(row[i]) for row in body)) for i in range(len(head))]
    fmt = "  ".join("%-" + str(width) + "s" for width in widths)
    return "\n".join([fmt % tuple(head)] + [fmt % tuple(row) for row in body])



def parse_tsv(lines: list[str], cols: list[str]) -> dict:
    rows, trunc = [], False
    for ln in lines:
        parts = ln.split("\t")
        if parts[0] == "TRUNC":
            trunc = True
            continue
        if parts[0] == "ERR":
            raise RuntimeError(ln[4:])
        rows.append({k: coerce(v) for k, v in zip(cols, parts)})
    return {"rows": rows, "count": len(rows), "truncated": trunc}



class API(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True



def make_handler(world, stop_cb, dispatch):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            for raw in self.rfile:
                try:
                    req = json.loads(raw.decode("utf-8"))
                except Exception as e:
                    self._send({"ok": False, "error": "bad json: %s" % e})
                    continue
                try:
                    resp = dispatch(world, req, stop_cb)
                except Exception as e:
                    resp = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}
                self._send(resp)

        def _send(self, obj):
            try:
                self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
                self.wfile.flush()
            except Exception:
                pass
    return Handler


class OperationRouter:
    """One explicit handler per operation; duplicate registration is an error."""
    def __init__(self, groups):
        self.handlers = {}
        for operations, handler in groups:
            for operation in operations:
                if operation in self.handlers:
                    raise ValueError('duplicate world operation: ' + operation)
                self.handlers[operation] = handler

    def dispatch(self, world, request, stop_cb):
        operation = (request.get('op') or '').strip()
        handler = self.handlers.get(operation)
        if handler is None:
            return {'ok': False, 'error': 'unknown op: %r' % operation}
        return handler(world, request, stop_cb)
