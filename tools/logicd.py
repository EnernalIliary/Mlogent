#!/usr/bin/env python3
"""logicd -- the local half of the in-game logic-writing service.

The mod (MlogAuxiliary/) never composes mlog itself.  It posts an *intent* here, this
process turns it into code, checks it with the same analyzer the gate uses, and
hands back the exact byte payload the game's own config channel expects
(LogicBlock.compress: version byte + code + link table, see
Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:137-166).
The mod then calls build.configure(bytes) -- which is also the multiplayer path,
because that config is applied on the server (LogicBlock.java:65-69).

Why a sidecar and not "all in JS"
---------------------------------
The rules, the instruction table and the cost model already exist in Python and are
what the gate pins.  Re-implementing them in Rhino would create a second copy that
drifts silently.  So the contract is: game = transport + UI + a few instant checks,
sidecar = composition + full analysis.  When the sidecar is unreachable the mod
still works in "offline" mode (templates bundled in JS, instant checks only).

Protocol (v1, JSON over HTTP, loopback only)
--------------------------------------------
    GET  /health        -> {"ok":true,"protocol":1}
    GET  /capabilities  -> instructions, ops, templates, limits
    POST /analyze       {code, links:[name|{name,x,y}], ipt}      -> findings + cost
    POST /compose       {template, params, links, ipt}            -> code + findings + bytes_b64

Everything returns "ok": false when any finding is ERR: a write is refused, not
downgraded.  WARN/INFO are returned with the payload so the panel can show them
next to the confirm button.

Usage
-----
    python tools/logicd.py                    # 127.0.0.1:8765
    python tools/logicd.py --port 0           # ephemeral port, printed on the ready line
    python tools/logicd.py --print-template patrol   # dump one template, no server
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mlogcheck as C          # noqa: E402
import msch                    # noqa: E402

PROTOCOL = 1
GAME = 'mindustry v160.7 (executor jar out/_server160.jar)'

#: LogicBlock.instructionsPerTick is 1 by default and clamped to
#: maxInstructionsPerTick = 40 (LogicBlock.java:46,48,826) -- the panel shows the
#: budget against this cap.
IPT_MAX = 40
#: a non-privileged processor can only link within 10 tiles (LogicBlock.range)
LINK_RANGE_TILES = 10


# ---------------------------------------------------------------- templates

class Template:
    """One deterministic pattern.  Params are typed so a bad request is a 400."""

    def __init__(self, tid, title, params, build):
        self.id = tid
        self.title = title
        self.params = params      # name -> (type, default, help)
        self.build = build        # (params) -> (lines, referenced link names)

    def spec(self):
        return {'id': self.id, 'title': self.title,
                'params': [{'name': k, 'type': v[0], 'default': v[1], 'help': v[2]}
                           for k, v in self.params.items()]}


def _p(params, name, kind, default):
    v = params.get(name, default)
    if kind == 'int':
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ValueError('param %r must be an integer, got %r' % (name, v))
    if kind == 'float':
        try:
            return float(v)
        except (TypeError, ValueError):
            raise ValueError('param %r must be a number, got %r' % (name, v))
    if kind == 'link':
        s = str(v or '').strip()
        if not s or not s.replace('_', 'a').replace('-', 'a').isalnum():
            raise ValueError('param %r must be a link name, got %r' % (name, v))
        return s
    if kind == 'unit':
        s = str(v or '').strip()
        if not s:
            raise ValueError('param %r must be a unit type' % name)
        return s if s.startswith('@') else '@' + s
    if kind == 'item':
        s = str(v or '').strip()
        if not s:
            raise ValueError('param %r must be an item name' % name)
        return s if s.startswith('@') else '@' + s
    s = str(v if v is not None else '')
    if len(s) > 120:
        raise ValueError('param %r is too long' % name)
    return s.replace('\n', ' ').replace('\r', ' ')


def _t_patrol(params):
    unit = _p(params, 'unit', 'unit', 'flare')
    x1, y1 = _p(params, 'x1', 'int', 10), _p(params, 'y1', 'int', 10)
    x2, y2 = _p(params, 'x2', 'int', 20), _p(params, 'y2', 'int', 10)
    hold = _p(params, 'wait', 'float', 1)
    lines = ['ubind ' + unit,
             'loop:',
             'ucontrol move %d %d 0 0 0' % (x1, y1),
             'wait %s' % hold,
             'ucontrol move %d %d 0 0 0' % (x2, y2),
             'wait %s' % hold,
             'jump loop always',
             'end']
    return lines, []


def _t_item_threshold(params):
    cell = _p(params, 'container', 'link', 'container1')
    item = _p(params, 'item', 'item', 'copper')
    thr = _p(params, 'threshold', 'int', 100)
    msg = _p(params, 'message', 'link', 'message1')
    lines = ['loop:',
             'sensor n %s %s' % (cell, item),
             'jump enough greaterThanEq n %d' % thr,
             'print "low"',
             'printflush %s' % msg,
             'enough:',
             'wait 1',
             'jump loop always',
             'end']
    return lines, [cell, msg]


def _t_radar_fire(params):
    turret = _p(params, 'turret', 'link', 'turret1')
    lines = ['loop:',
             'radar enemy any any distance %s 1 target' % turret,
             'jump fire notEqual target null',
             'wait 0.5',
             'jump loop always',
             'fire:',
             'control shootp %s target 1' % turret,
             'jump loop always',
             'end']
    return lines, [turret]


def _t_memory_table(params):
    cell = _p(params, 'cell', 'link', 'cell1')
    idx = _p(params, 'index', 'int', 0)
    val = _p(params, 'value', 'int', 42)
    lines = ['write %d %s %d' % (val, cell, idx),
             'read out %s %d' % (cell, idx),
             'print out',
             'printflush message1',
             'end']
    return lines, [cell]


def _t_timer_flush(params):
    msg = _p(params, 'message', 'link', 'message1')
    secs = _p(params, 'seconds', 'float', 2)
    text = _p(params, 'text', 'str', 'tick')
    lines = ['loop:',
             'wait %s' % secs,
             'print "%s"' % text,
             'printflush %s' % msg,
             'jump loop always',
             'end']
    return lines, [msg]


def _t_counter(params):
    cell = _p(params, 'cell', 'link', 'cell1')
    step = _p(params, 'step', 'int', 1)
    lines = ['loop:',
             'read n %s 0' % cell,
             'op add n n %d' % step,
             'write n %s 0' % cell,
             'wait 1',
             'jump loop always',
             'end']
    return lines, [cell]


TEMPLATES = {t.id: t for t in [
    Template('patrol', 'bind a unit and move it between two tiles', {
        'unit': ('unit', 'flare', 'unit type, @ optional'),
        'x1': ('int', 10, 'first tile x'), 'y1': ('int', 10, 'first tile y'),
        'x2': ('int', 20, 'second tile x'), 'y2': ('int', 10, 'second tile y'),
        'wait': ('float', 1, 'seconds to hold at each end'),
    }, _t_patrol),
    Template('item-threshold', 'print when a container holds enough of an item', {
        'container': ('link', 'container1', 'container link name'),
        'item': ('item', 'copper', 'item name, @ optional'),
        'threshold': ('int', 100, 'count that counts as enough'),
        'message': ('link', 'message1', 'message link name'),
    }, _t_item_threshold),
    Template('radar-fire', 'point a turret at the nearest enemy unit', {
        'turret': ('link', 'turret1', 'turret link name'),
    }, _t_radar_fire),
    Template('memory-table', 'write and read one memory cell slot', {
        'cell': ('link', 'cell1', 'memory cell link name'),
        'index': ('int', 0, 'cell slot'), 'value': ('int', 42, 'value to store'),
    }, _t_memory_table),
    Template('timer-flush', 'print a line every N seconds', {
        'message': ('link', 'message1', 'message link name'),
        'seconds': ('float', 2, 'period in seconds'), 'text': ('str', 'tick', 'line to print'),
    }, _t_timer_flush),
    Template('counter', 'count up in a memory cell forever', {
        'cell': ('link', 'cell1', 'memory cell link name'),
        'step': ('int', 1, 'increment per second'),
    }, _t_counter),
]}


# ---------------------------------------------------------------- analysis

def _link_names(links):
    """Accept ["a","b"] or [{"name":"a","x":1,"y":2}] and return the name list."""
    names = []
    for link in links or []:
        if isinstance(link, dict):
            n = link.get('name')
        else:
            n = link
        if n:
            names.append(str(n))
    return names


def _link_objects(links):
    out = []
    for link in links or []:
        if isinstance(link, dict):
            out.append(msch.LogicLink(str(link.get('name', '')), int(link.get('x', 0)),
                                      int(link.get('y', 0))))
        else:
            out.append(msch.LogicLink(str(link), 0, 0))
    return out


def analyse(code, links, ipt=2):
    """Run the same analyzer the gate runs; return a JSON-ready dict."""
    lines = code.splitlines()
    # A label line is NOT a statement (LParser.java:117-125), so count slots with
    # the analyzer's own prepare() instead of counting non-blank lines.
    stmts = [(ln + 1, c) for ln, c in C.prepare(lines)]
    # Finding.line is a STATEMENT index; the panel highlights a line of the code
    # text, so translate through prepare()'s own (line, code) pairs.
    srcline = {i: ln for i, (ln, _) in enumerate(stmts)}
    findings = []
    for f in C.analyse(lines, links=_link_names(links) or None, ipt=ipt):
        findings.append({'sev': f.sev, 'line': srcline.get(f.line, f.line + 1),
                         'stmt': f.line, 'rid': _rid(f), 'msg': f.msg})
    errors = sum(1 for f in findings if f['sev'] == 'ERR')
    warns = sum(1 for f in findings if f['sev'] == 'WARN')
    try:
        cost = C.cost_report(stmts, links=_link_names(links) or None)
    except Exception as exc:                       # cost model is advisory only
        cost = '  (cost model failed: %s)' % exc
    return {'ok': errors == 0, 'findings': findings, 'errors': errors, 'warns': warns,
            'statements': len(stmts), 'cost': cost}


def _rid(finding):
    try:
        from rule_ids import rule_id
        return rule_id(finding.sev, finding.msg)
    except Exception:
        return ''


def compose(req):
    """template + params + links -> code, findings, and the game's own byte payload."""
    tid = req.get('template')
    tmpl = TEMPLATES.get(tid)
    if tmpl is None:
        raise ValueError('unknown template %r (known: %s)' % (tid, ', '.join(sorted(TEMPLATES))))
    params = req.get('params') or {}
    if not isinstance(params, dict):
        raise ValueError('params must be an object')
    lines, refs = tmpl.build(params)
    code = '\n'.join(lines)
    links = req.get('links') or []
    names = _link_names(links)
    # The template knows which links it writes into the code; a missing one is a
    # hard error here (the analyzer would also say so, but a template should name it).
    missing = [n for n in refs if n not in names]
    res = analyse(code, links, ipt=int(req.get('ipt') or 2))
    if missing:
        res['findings'].insert(0, {
            'sev': 'ERR', 'line': 0, 'rid': 'template-needs-link',
            'msg': 'template %r writes %s into the code but the processor has no such link '
                   '(link names are <blockname><n>, e.g. container1; see docs/速查卡.md section 6)'
                   % (tid, ', '.join(missing))})
        res['errors'] += 1
        res['ok'] = False
    payload = msch.build_logic_data(code, _link_objects(links))
    return {'ok': res['ok'], 'template': tid, 'code': code,
            'findings': res['findings'], 'errors': res['errors'], 'warns': res['warns'],
            'statements': res['statements'], 'cost': res['cost'],
            'links': _link_names(links),
            'bytes_b64': base64.b64encode(payload).decode('ascii'),
            'bytes_len': len(payload)}


def capabilities():
    try:
        sem = json.load(open(os.path.join(HERE, 'instr_semantics.json'), encoding='utf-8'))
    except Exception:
        sem = {}
    ins = sem.get('instructions') or {}
    ops = sorted((sem.get('ops') or {}).keys())
    return {'ok': True, 'protocol': PROTOCOL, 'game': GAME,
            'instructions': sorted(ins.keys()),
            'ops': list(ops),
            'templates': [t.spec() for t in TEMPLATES.values()],
            'limits': {'ipt_max': IPT_MAX, 'link_range_tiles': LINK_RANGE_TILES}}


# ---------------------------------------------------------------- http

class Handler(BaseHTTPRequestHandler):
    server_version = 'logicd/1'

    def log_message(self, fmt, *args):        # keep stdout clean for the ready line
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?')[0]
        try:
            if path == '/health':
                self._send(200, {'ok': True, 'protocol': PROTOCOL})
            elif path == '/capabilities':
                self._send(200, capabilities())
            else:
                self._send(404, {'ok': False, 'error': 'no such endpoint: ' + path})
        except Exception as exc:
            self._send(500, {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc)})

    def do_POST(self):
        path = self.path.split('?')[0]
        try:
            n = int(self.headers.get('Content-Length') or 0)
            if n > 4 * 1024 * 1024:
                self._send(413, {'ok': False, 'error': 'request too large'})
                return
            raw = self.rfile.read(n) if n else b'{}'
            try:
                req = json.loads(raw.decode('utf-8') or '{}')
            except Exception as exc:
                self._send(400, {'ok': False, 'error': 'bad json: %s' % exc})
                return
            if not isinstance(req, dict):
                self._send(400, {'ok': False, 'error': 'body must be a JSON object'})
                return
            if path == '/analyze':
                code = req.get('code')
                if not isinstance(code, str):
                    self._send(400, {'ok': False, 'error': 'code must be a string'})
                    return
                res = analyse(code, req.get('links'), ipt=int(req.get('ipt') or 2))
                self._send(200, res)
            elif path == '/compose':
                try:
                    self._send(200, compose(req))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            else:
                self._send(404, {'ok': False, 'error': 'no such endpoint: ' + path})
        except Exception:
            self._send(500, {'ok': False, 'error': traceback.format_exc(limit=3)})


def serve(host, port):
    srv = ThreadingHTTPServer((host, port), Handler)
    real = srv.server_address
    print('logicd listening on http://%s:%d' % (real[0], real[1]), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


def main(argv=None):
    ap = argparse.ArgumentParser(description='local half of the in-game logic-writing service')
    ap.add_argument('--host', default='127.0.0.1', help='bind address (loopback by default)')
    ap.add_argument('--port', type=int, default=8765, help='0 = pick a free port')
    ap.add_argument('--print-template', metavar='ID', help='dump one template and exit')
    a = ap.parse_args(argv)
    if a.print_template:
        t = TEMPLATES.get(a.print_template)
        if t is None:
            print('unknown template %r; known: %s' % (a.print_template, ', '.join(sorted(TEMPLATES))))
            return 2
        print(t.build({})[0] and '\n'.join(t.build({})[0]))
        return 0
    serve(a.host, a.port)
    return 0


if __name__ == '__main__':
    sys.exit(main())
