#!/usr/bin/env python3
"""Contract tests for the in-game logic-writing service (mod <-> tools/logicd.py).

Two halves, because they fail for different reasons:

  A. protocol   -- pure python: start logicd on an ephemeral port, drive it over
                   HTTP, assert the JSON shape the mod codes against.  This is the
                   half that must run everywhere, so it needs no JRE and no jars.
  B. write path -- one real v160.7 processor: take /compose's bytes_b64, hand them
                   to build.configure(bytes) exactly as the mod will, and read the
                   processor back.  This is what proves the payload is not merely
                   "our" encoding but the game's own -- the instruction classes the
                   game compiled (UnitBindI, RadarI, ...) are the evidence, plus
                   b.code and the link table surviving the round trip.

Why configure() and not "write the code field": LogicBlock.config(byte[].class)
is the vanilla channel a client uses to push code to the server
(Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:65-69),
and the mod writes through it so multiplayer works without inventing sync.

Exit: 0 everything passed, 1 a check failed, 3 half B could not run (no JRE or no
versioned jar -- the jars live in out/ and are not in git, so a fresh clone SKIPs
half B instead of failing).

Usage
-----
    python tests/logicd/run_logicd_tests.py            # both halves
    python tests/logicd/run_logicd_tests.py --no-sim   # protocol half only
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'tools'))

LINKS = [{'name': 'container1', 'x': 1, 'y': 2}, {'name': 'message1', 'x': 3, 'y': 4},
         {'name': 'turret1', 'x': 5, 'y': 6}, {'name': 'cell1', 'x': 7, 'y': 8}]

GOOD = 'sensor n container1 @copper\njump ok greaterThanEq n 1\nok:\nprintflush message1\nend'
# zzz is read in control shootp's target slot, which takes an OBJECT: null there
# does not become 0, so this must be refused (rule undefined-var-read, ERR).
BAD = 'control shootp turret1 zzz 1\nend'


class Fail(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise Fail(msg)


class Server:
    """logicd on an ephemeral port; the ready line carries the real one."""

    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, str(ROOT / 'tools' / 'logicd.py'), '--port', '0'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        self.port = None
        deadline = time.time() + 40
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                break
            if 'listening on' in line:
                self.port = int(line.strip().rsplit(':', 1)[1])
                break
        if self.port is None:
            self.close()
            raise Fail('logicd never printed its ready line')

    @property
    def base(self):
        return 'http://127.0.0.1:%d' % self.port

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path, timeout=30) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    def post(self, path, obj):
        req = urllib.request.Request(self.base + path, data=json.dumps(obj).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


# ---------------------------------------------------------------- half A

def test_protocol():
    """Returns the capabilities payload so half B reuses the same template list."""
    checks = 0
    srv = Server()
    try:
        st, health = srv.get('/health')
        need(st == 200 and health.get('ok') is True, 'health: %r' % (health,))
        need(health.get('protocol') == 1, 'health protocol: %r' % (health,))
        checks += 1

        st, cap = srv.get('/capabilities')
        need(st == 200 and cap.get('ok') is True, 'capabilities status %s' % st)
        need(len(cap.get('instructions') or []) >= 50,
             'capabilities instructions: %d' % len(cap.get('instructions') or []))
        need(len(cap.get('ops') or []) >= 40, 'capabilities ops: %d' % len(cap.get('ops') or []))
        need(cap['limits']['ipt_max'] == 40, 'ipt_max: %r' % (cap['limits'],))
        tids = [t['id'] for t in cap.get('templates') or []]
        need(len(tids) >= 6, 'templates: %r' % (tids,))
        for t in cap['templates']:
            need(t.get('title') and isinstance(t.get('params'), list),
                 'template %r has no title/params' % t.get('id'))
        checks += 1

        st, res = srv.post('/analyze', {'code': GOOD, 'links': LINKS, 'ipt': 2})
        need(st == 200 and res['ok'] is True, 'analyze good code refused: %r' % (res.get('findings'),))
        need(res['statements'] == 4, 'statements: %r (labels are not statements)' % res['statements'])
        need(bool(res.get('cost')), 'analyze returned no cost report')
        checks += 1

        st, res = srv.post('/analyze', {'code': BAD, 'links': LINKS, 'ipt': 2})
        need(st == 200 and res['ok'] is False, 'analyze accepted an ERR program')
        need(res['errors'] >= 1, 'errors: %r' % res['errors'])
        rids = [f['rid'] for f in res['findings'] if f['sev'] == 'ERR']
        need('undefined-var-read' in rids, 'ERR findings: %r' % rids)
        checks += 1

        import msch
        for tid in tids:
            st, res = srv.post('/compose', {'template': tid, 'params': {}, 'links': LINKS})
            need(st == 200, 'compose %s status %s' % (tid, st))
            need(res['ok'] is True and res['errors'] == 0,
                 'compose %s not clean: %r' % (tid, res.get('findings')))
            need(not res['findings'], 'compose %s findings: %r' % (tid, res['findings']))
            parsed = msch.parse_logic(base64.b64decode(res['bytes_b64']))
            need(parsed.code.strip() == res['code'].strip(),
                 'compose %s bytes decode to a different code' % tid)
            need([l.name for l in parsed.links] == [l['name'] for l in LINKS],
                 'compose %s link table: %r' % (tid, [l.name for l in parsed.links]))
            checks += 1

        st, res = srv.post('/compose', {'template': 'radar-fire', 'links': ['message1']})
        need(st == 200 and res['ok'] is False, 'compose with a missing link was accepted')
        rids = [f['rid'] for f in res['findings']]
        need('template-needs-link' in rids, 'missing-link findings: %r' % rids)
        checks += 1

        st, res = srv.post('/compose', {'template': 'no-such-template'})
        need(st == 400 and res['ok'] is False, 'unknown template status %s' % st)
        st, res = srv.post('/compose', {'template': 'patrol', 'params': {'x1': 'abc'}, 'links': LINKS})
        need(st == 400 and res['ok'] is False, 'bad param status %s' % st)
        st, res = srv.post('/analyze', {'code': 42})
        need(st == 400, 'non-string code status %s' % st)
        st, res = srv.get('/nope')
        need(st == 404, 'unknown endpoint status %s' % st)
        checks += 1

        # a real link typo is a WARN, not an ERR: the write is allowed but the panel
        # has to show it, so pin that the finding reaches the client at all.
        st, res = srv.post('/analyze', {'code': 'sensor n vault9 @copper\nprint n\nend', 'links': LINKS})
        need(st == 200 and any(f['rid'] == 'link-name-not-bound' for f in res['findings']),
             'a typo link name produced no link-name-not-bound finding')
        checks += 1

        # /plan: one sentence in, a template choice + params + the same payload out.
        # This is the seam a language model would take over, so the shape has to be
        # pinned: template, params, reason, and a payload that is already checked.
        cases = [
            ('let @flare patrol between 10 10 and 30 12', 'patrol'),
            ('watch copper in the container, shout when it reaches 250', 'item-threshold'),
            ('point the turret at the nearest enemy and fire', 'radar-fire'),
            ('count up in the cell by 5 every second', 'counter'),
            ('at index 3 store 42 in the memory cell', 'memory-table'),
            ('print a line every 2 seconds', 'timer-flush'),
        ]
        for text, want in cases:
            st, res = srv.post('/plan', {'intent': text, 'links': LINKS, 'ipt': 2})
            need(st == 200, 'plan %r status %s' % (text, st))
            need(res.get('template') == want,
                 'plan %r chose %r, wanted %r (reason %r)' % (text, res.get('template'), want, res.get('reason')))
            need(isinstance(res.get('params'), dict), 'plan %r params: %r' % (text, res.get('params')))
            need(res.get('reason'), 'plan %r gave no reason' % text)
            need(res.get('bytes_b64') and res.get('bytes_len', 0) > 0, 'plan %r returned no payload' % text)
            need(res.get('errors') == 0, 'plan %r produced ERR: %r' % (text, res.get('findings')))
            checks += 1
        # the params are extracted, not just the template name
        st, res = srv.post('/plan', {'intent': cases[0][0], 'links': LINKS})
        need(res['params'].get('unit') == 'flare' and res['params'].get('x2') == 30,
             'plan extracted patrol params: %r' % (res.get('params'),))
        st, res = srv.post('/plan', {'intent': cases[1][0], 'links': LINKS})
        need(res['params'].get('item') == 'copper' and res['params'].get('threshold') == 250
             and res['params'].get('container') == 'container1',
             'plan extracted item params: %r' % (res.get('params'),))
        checks += 1
        # Chinese intents: the sentence is Chinese, the game speaks English.  Both the
        # item name and the link kind have to survive the trip, or every Chinese
        # sentence silently lands on the defaults and still looks like it worked.
        st, res = srv.post('/plan', {'intent': '容器里铜够 100 就打印', 'links': LINKS})
        need(st == 200 and res.get('template') == 'item-threshold',
             'zh plan chose %r' % (res.get('template'),))
        zp = res.get('params') or {}
        need(zp.get('item') == 'copper' and zp.get('threshold') == 100
             and zp.get('container') == 'container1', 'zh item params: %r' % (zp,))
        st, res = srv.post('/plan', {'intent': '让 @flare 从 10 10 来回巡逻到 30 12', 'links': LINKS})
        zp = res.get('params') or {}
        need(res.get('template') == 'patrol' and zp.get('unit') == 'flare' and zp.get('x2') == 30,
             'zh patrol: %r %r' % (res.get('template'), zp))
        st, res = srv.post('/plan', {'intent': '每 2 秒报时一次', 'links': LINKS})
        need(res.get('template') == 'timer-flush' and (res.get('params') or {}).get('seconds') == 2,
             'zh timer: %r %r' % (res.get('template'), res.get('params')))
        checks += 1
        # a vague sentence is refused with the menu, not guessed at
        st, res = srv.post('/plan', {'intent': 'make something nice', 'links': LINKS})
        need(st == 200 and res['ok'] is False and res.get('template') is None,
             'plan on a vague intent: %r' % (res,))
        need(len(res.get('candidates') or []) >= 6, 'plan candidates: %r' % (res.get('candidates'),))
        st, res = srv.post('/plan', {'intent': '   '})
        need(st == 400 and res['ok'] is False, 'plan with an empty intent status %s' % st)
        checks += 1

        return cap, checks
    finally:
        srv.close()


# ---------------------------------------------------------------- half B

JS = """
var b = Vars.world.build(%d, %d);
if(b === null || b.executor === null){ print('NOPROC'); } else {
    var arr = Packages.java.util.Base64.getDecoder().decode('%s');
    b.configure(arr);
    var ins = b.executor.instructions;
    var cls = ins.length > 0 ? String(ins[0].getClass().getSimpleName()) : '-';
    print('CFG\\tlen=' + ins.length + '\\tcodeok=' + (b.code === %s) + '\\tlinks=' + b.links.size + '\\tfirst=' + cls);
}
void 0
"""


def test_write_path(cap):
    """compose -> bytes_b64 -> build.configure(bytes) -> read the processor back."""
    import mlogsim as M
    java = M._default_java()
    jar = M.V160_JAR
    if not java or not jar or not pathlib.Path(jar).is_file():
        print('SKIP write path: no JRE or missing jar %s' % jar)
        return 0, 'skip'
    tids = [t['id'] for t in cap['templates']]
    checks = 0
    srv = M.Server(java, jar)
    srv._core_spec = 'copper:100'
    srv._unit_spec = [['flare', 1]]
    srv.prepare()
    srvd = None
    try:
        # materialize the processor first, then reconfigure that same building for
        # every template: the game's own assembler runs on each configure(), so a
        # template the game cannot parse would come back with len=0.
        M.run_mlog(srv, 'p', 'noop', steps=1, update='none', processor='auto')
        # the same process the mod talks to, reached over HTTP -- no shortcut call
        # into compose() here, the bytes must travel the real path.
        srvd = Server()
        for tid in tids:
            st, res = srvd.post('/compose', {'template': tid, 'params': {}, 'links': LINKS})
            need(st == 200 and res['ok'], 'compose %s: %r' % (tid, res.get('findings')))
            out = srv.js(JS % (srv.base[0], srv.base[1], res['bytes_b64'], json.dumps(res['code'])))
            lines = out if isinstance(out, list) else str(out).splitlines()
            line = next((str(l) for l in lines if str(l).startswith('CFG\t')), None)
            need(line is not None, 'write path %s: no CFG line (got %r)' % (tid, lines))
            fields = dict(kv.split('=', 1) for kv in line.split('\t')[1:] if '=' in kv)
            need(fields.get('codeok') == 'true', '%s: b.code differs after configure' % tid)
            need(int(fields.get('len') or 0) > 0,
                 '%s: the game compiled 0 instructions (it rejected the payload)' % tid)
            need(int(fields.get('links') or 0) == len(LINKS),
                 '%s: link table want %d got %s' % (tid, len(LINKS), fields.get('links')))
            checks += 1
        return checks, 'ok'
    finally:
        if srvd is not None:
            srvd.close()
        srv.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description='logicd contract tests')
    ap.add_argument('--no-sim', action='store_true', help='protocol half only (no JRE needed)')
    a = ap.parse_args(argv)
    try:
        cap, n = test_protocol()
        print('protocol: %d check(s) passed' % n)
    except Fail as exc:
        print('FAIL protocol: %s' % exc)
        return 1
    except Exception as exc:
        print('FAIL protocol: %s: %s' % (type(exc).__name__, exc))
        return 1
    if a.no_sim:
        print('logicd OK (protocol only)')
        return 0
    try:
        n, state = test_write_path(cap)
    except Fail as exc:
        print('FAIL write path: %s' % exc)
        return 1
    except Exception as exc:
        print('FAIL write path: %s: %s' % (type(exc).__name__, exc))
        return 1
    if state == 'skip':
        print('logicd OK (protocol only, write path skipped)')
        return 3
    print('write path: %d template(s) accepted by the game' % n)
    print('logicd OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
