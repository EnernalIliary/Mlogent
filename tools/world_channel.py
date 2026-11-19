"""Serialized console and JS/file-result channels over an owned process."""
from __future__ import annotations

import threading
import os
import time
import uuid


class WorldChannel:
    def __init__(self, process):
        self.process = process

    def console(self, cmd, quiet=0.30, timeout=8.0):
        process = self.process
        with process._lock:
            start = time.monotonic()
            seq = process.seq
            process.send(cmd)
            lines = self._collect(seq, quiet, timeout)
            return {'ok': True, 'cmd': cmd, 'lines': lines,
                    'ms': round((time.monotonic() - start) * 1000)}

    def _collect(self, seq0, quiet, timeout):
        process = self.process
        out, changed, last = [], time.monotonic(), seq0
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with process._cv:
                process._cv.wait(min(0.05, max(0, deadline - time.monotonic())))
                new = [line for seq, line in process.lines if seq > last]
                if new:
                    last = process.lines[-1][0]
            if new:
                out.extend(new)
                changed = time.monotonic()
            elif out and time.monotonic() - changed >= quiet:
                break
            elif process.eof:
                break
        return out

    def _read_result(self, path, deadline):
        while time.monotonic() < deadline:
            try:
                with open(path, 'r', encoding='utf-8') as stream:
                    text = stream.read()
            except OSError:
                time.sleep(min(0.02, max(0, deadline - time.monotonic())))
                continue
            try:
                os.remove(path)
            except OSError:
                pass
            return text
        return None

    def js(self, body, timeout=None):
        process = self.process
        timeout = timeout or getattr(process, 'js_timeout', 60.0)
        result = 'res-%s.txt' % uuid.uuid4().hex[:12]
        path = os.path.join(process.data_dir, result)
        script = (
            'var sb = new java.lang.StringBuilder();'
            ' try { (function(){ ' + ' '.join(body.splitlines()) + ' })(); }'
            " catch (e) { sb.append('ERR\t' + e); }"
            " var __w = new java.io.PrintWriter('%s', 'UTF-8');"
            '__w.print(sb.toString()); __w.close();' % result
        )
        with process._lock:
            seq = process.seq
            process.send('js ' + ' '.join(script.splitlines()))
            text = self._read_result(path, time.monotonic() + timeout)
            if text is not None:
                if text.startswith('ERR\t') and '\n' not in text:
                    raise RuntimeError(text[4:])
                return text.splitlines()
            with process._cv:
                tail = [line for index, line in process.lines if index > seq][-12:]
        raise RuntimeError('js 超时 (%.0fs): %s' % (timeout, ' | '.join(tail)))

    def put_file(self, text, prefix='in'):
        name = '%s-%s.txt' % (prefix, uuid.uuid4().hex[:12])
        with open(os.path.join(self.process.data_dir, name), 'w', encoding='utf-8', newline='') as stream:
            stream.write(text)
        return name

    def take_file(self, name, timeout=10.0):
        text = self._read_result(os.path.join(self.process.data_dir, name),
                                 time.monotonic() + timeout)
        if text is None:
            raise RuntimeError('读不到 JS 输出文件 %s' % name)
        return text

    def wait_for(self, needle, timeout):
        process = self.process
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with process._cv:
                hit = [line for _, line in process.lines if needle in line]
                if hit:
                    return hit
                if process.eof:
                    raise SystemExit('服务端提前退出, 见 ' + process.log_path)
                process._cv.wait(min(0.05, max(0, deadline - time.monotonic())))
        raise SystemExit('等 %.0fs 没等到 %r, 见 %s' % (timeout, needle, process.log_path))


COMMAND_OPERATIONS = frozenset(("console", "js", "say", "pause", "save", "load", "shutdown"))

def command(w, req, *, audit, stop_cb):
    op = (req.get("op") or "").strip()
    if op == "console":
        cmd = str(req.get("cmd") or "").strip()
        if not cmd:
            return {"ok": False, "error": "empty cmd"}
        audit("console", cmd=cmd)
        return w.console(cmd, quiet=float(req.get("quiet") or 0.3),
                         timeout=float(req.get("timeout") or 8))
    if op == "js":
        src = str(req.get("code") or "")
        if not src.strip():
            return {"ok": False, "error": "empty code"}
        audit("js", code=src[:500])
        return {"ok": True, "lines": w.js(src, timeout=float(req.get("timeout") or 0) or None)}
    if op == "say":
        txt = str(req.get("text") or "").rstrip()
        audit("say", text=txt)
        return w.console("say " + txt, quiet=0.2, timeout=5)
    if op == "pause":
        on = bool(req.get("on", True))
        audit("pause", on=on)
        return w.console("pause " + ("on" if on else "off"), quiet=0.25, timeout=6)
    if op == "save":
        name = str(req.get("name") or "world").strip().replace(" ", "_")
        audit("save", name=name)
        return w.console("save " + name, quiet=0.5, timeout=30)
    if op == "load":
        name = str(req.get("name") or "").strip()
        if not name:
            return {"ok": False, "error": "empty name"}
        audit("load", name=name)
        return w.console("load " + name, quiet=0.8, timeout=120)
    if op == "shutdown":
        audit("shutdown")
        threading.Thread(target=stop_cb, daemon=True).start()
        return {"ok": True, "bye": True}
    return NotImplemented
