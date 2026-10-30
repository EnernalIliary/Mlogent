"""Smoke the whole main.js init path in the REAL game engine (v160.7 Rhino).

The settings UI cannot be built headless (Vars.ui is null there -- Vars.java:209/332),
so this test does what the game does, minus the pixels:

  * loads rules.generated.js and quickcheck.js into the script scope, then main.js
    with its two require("...") calls swapped for those globals;
  * asserts init reports "ready" and never prints "init failed"/"bootstrap failed";
  * asks the mod itself to build its settings table against a fake Table
    (maiSelfTest) -- this catches Table/Cell API drift and broken wiring;
  * takes the Table/Cell method names maiSelfTest reported using, and calls each
    one on a REAL arc.scene.ui.layout.Table in the engine: a shape that hits a
    Java overload ambiguity (t.table(function) does in v160.7) fails here, which
    a fake JS table can never catch;
  * reads the diagnostics block (maiDiag) and checks it names both directories;
  * confirms maiSettings() says "no ui" headless instead of throwing.
  * greps the source for the v0.4.0 wiring a headless engine cannot show: closeOnBack()
    plus a close button on the modal panel, the review bar hooked to Vars.ui.logic, F4 -> AI panel.

Gate treats exit 3 as SKIP (no JRE / no jar).

Why this exists: the first version of the console-function mount read scope.get(k, scope)
back, which throws "Cannot find function get" under the real engine -- main.js died
after loading its rule table and the mod looked half-installed.
"""
import http.server, io, json, os, re, sys
import threading

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

SCRIPTS = os.path.join(ROOT, 'MlogAuxiliary', 'scripts')
MAIN = os.path.join(SCRIPTS, 'main.js')


def preloaded(tmpdir):
    """main.js with require() swapped for globals of the same script scope."""
    src = io.open(MAIN, 'rb').read().decode('utf-8')
    src = src.replace('RULES = require("rules.generated");', 'RULES = MAI_RULES;')
    src = src.replace('QUICK = require("quickcheck");', 'QUICK = MAI_QUICKCHECK;')
    p = os.path.join(tmpdir, 'main_preloaded.js')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(src)
    return p


def region_probe(srv):
    """P3: place a container and a vault next to the processor, then snapshot them.

    The snapshot is the mod's own code path (maiSnapshot -> regionSnapshot), so this
    pins the two engine facts that are easy to get wrong: tile.block() is a METHOD
    while tile.build is a FIELD, and empty tiles must be skipped (their block name
    is 'air').  A JS-side fake cannot catch either."""
    bx, by = srv.base
    return [
        "var W = Packages.mindustry.Vars.world;",
        "W.tile(%d, %d).setBlock(Packages.mindustry.Vars.content.block('container'));" % (bx + 2, by + 1),
        "W.tile(%d, %d).setBlock(Packages.mindustry.Vars.content.block('switch'));" % (bx + 4, by + 1),
        "print('MAISNAP:' + maiSnapshot(%d, %d, %d, %d));" % (bx - 1, by - 1, bx + 4, by + 4),
    ]


ECHO_MARK = 'MAISIDECAR-OK'


class _Echo(http.server.BaseHTTPRequestHandler):
    """Answers like tools/logicd.py: JSON, Content-Length, HTTP/1.0 style close."""

    def _reply(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._reply({'ok': True, 'mark': ECHO_MARK, 'method': 'GET', 'path': self.path})

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n).decode('utf-8', 'replace') if n else ''
        self._reply({'ok': True, 'mark': ECHO_MARK, 'method': 'POST', 'echo': raw})

    def log_message(self, *args):
        pass


def echo_server():
    """A real local HTTP server: the socket transport cannot be faked in JS."""
    hs = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _Echo)
    threading.Thread(target=hs.serve_forever, daemon=True).start()
    return hs, hs.server_address[1]


def http_probe(port):
    # One line per probe, and never echo the body of the dead-port case: the simulator's
    # js() bridge raises SimError on any console line containing "Exception"/"Error:",
    # which would look like a transport failure instead of the expected code -1.
    return [
        "var p1 = maiHttpRaw('GET', 'http://127.0.0.1:%d/health', null);" % port,
        "print('MAIHTTP1:' + p1.split('\\n')[0] + ':' + (p1.indexOf('MAISIDECAR-OK') >= 0 ? 'MARK' : 'NOMARK'));",
        "var p2 = maiHttpRaw('POST', 'http://127.0.0.1:%d/plan', 'MAIPING');" % port,
        "print('MAIHTTP2:' + p2.split('\\n')[0] + ':' + (p2.indexOf('MAIPING') >= 0 ? 'ECHO' : 'NOECHO'));",
        "var p3 = maiHttpRaw('GET', 'http://127.0.0.1:1/health', null);",
        "print('MAIHTTP3:' + p3.split('\\n')[0]);",
    ]
def main():
    try:
        import mlogsim as M
    except Exception as e:
        print('SKIP no mlogsim: %s' % e)
        return 3
    jar = getattr(M, 'V160_JAR', None)
    if not jar or not os.path.exists(jar):
        print('SKIP no v160 jar')
        return 3
    java = M._default_java()
    if not java:
        print('SKIP no java')
        return 3

    d = os.path.join(ROOT, 'out', '_lw_ui')
    os.makedirs(d, exist_ok=True)
    pre = preloaded(d).replace(chr(92), '/')
    sc = SCRIPTS.replace(chr(92), '/')

    srv = M.Server(java, jar)
    srv.prepare()
    M.run_mlog(srv, 'p', 'noop', steps=1, update='none')
    js = ' '.join([
        "var s = Packages.mindustry.Vars.mods.getScripts();",
        "var F = Packages.java.nio.file.Files, P = Packages.java.nio.file.Paths, JS = Packages.java.lang.String;",
        "function rd(p){ return new JS(F.readAllBytes(P.get(p)), 'UTF-8'); }",
        "s.runConsole(rd('%s/rules.generated.js'));" % sc,
        "s.runConsole(rd('%s/quickcheck.js'));" % sc,
        "s.runConsole(rd('%s'));" % pre,
        "print('MAISELF:' + maiSelfTest());",
        "print('MAIDIAG:' + maiDiag().replace(/\\n/g, ' | '));",
        "print('MAISET:' + maiSettings());",
    ] + region_probe(srv) + [
        "void 0;",
    ])
    try:
        out = srv.js(js)
    except Exception as e:
        print('FAIL engine call: %s' % str(e)[-400:])
        return 1
    text = '\n'.join(str(x) for x in out)
    lines = [l for l in text.splitlines()
             if '[mai]' in l or 'mlog-auxiliary' in l
             or l.startswith(('MAISELF:', 'MAIDIAG:', 'MAISET:'))]
    joined = '\n'.join(lines)

    # ---- resolve every Table/Cell method the page actually uses, in the engine
    used = []
    for l in text.splitlines():
        if l.startswith('MAISELF:') and '\u7528\u5230\u7684\u65b9\u6cd5' in l:
            used = [x for x in l.split('\u7528\u5230\u7684\u65b9\u6cd5 ')[-1].strip().split(',') if x]
    if not used:
        used = []

    # arg shells: the method name is enough, because only Java overload RESOLUTION
    # is under test here -- any runtime failure caused by a null skin counts as OK.
    SHELL = {
        'defaults': '', 'row': '',
        'add': "t.add('x');",
        'label': "t.label('x');",
        'labelWrap': "t.labelWrap('x');",
        'field': "t.field('v', function(){});",
        'button': "t.button('b', function(){});",
        'check': "t.check('c', false, function(){});",
        'image': "t.image('info');",
        'pane': "t.pane(function(tt){});",
        'table': "t.table(function(tt){});",
        'scrollPane': "t.scrollPane(function(tt){});",
        'pad': "t.add('x').pad(4);",
        'left': "t.add('x').left();",
        'width': "t.add('x').width(120);",
        'colspan': "t.add('x').colspan(2);",
        'get': "t.add('x').get();",
        'padTop': "t.add('x').padTop(4);",
        'padBottom': "t.add('x').padBottom(4);",
        'padRight': "t.add('x').padRight(4);",
        'right': "t.add('x').right();",
        'clear': 't.clear();',
        'color': "t.add('x').color(Packages.arc.graphics.Color.white);",
        'margin': 't.margin(8);',
        'growX': "t.add('x').growX();",
        'height': "t.add('x').height(40);",
    }
    missing = [m for m in used if m not in SHELL]
    probe = [
        "var T = Packages.arc.scene.ui.layout.Table;",
        "function cls(e){ var s = '' + e;"
        " if (s.indexOf('ambiguous') >= 0) return 'AMBIGUOUS';"
        " if (s.indexOf('Cannot find function') >= 0) return 'NOFUNC';"
        " if (s.indexOf('TypeError') >= 0) return 'TYPE';"
        " return 'OK_SKIN'; }",
        "var out = [];",
    ]
    for m in used:
        if m in SHELL:
            probe.append("(function(){ var t = new T(); var r;"
                         " try { %s r = 'RESOLVED'; } catch(e){ r = cls(e); }"
                         " out.push('%s=' + r); })();" % (SHELL[m], m))
    # the console only echoes a trailing array literal without printing 'undefined',
    # and Server.js waits for that marker -- so print explicitly and end with void 0
    # v0.4.1: Table.pane() hands back Cell<ScrollPane>, and Group has no public add()
    # (Arc-Source/arc-core/src/arc/scene/Group.java -- addChild(Element) is the real API).
    # That is exactly why v0.4.0 crashed on out.add() while out.clear() worked.
    probe.append("(function(){ var sp;"
                 " try { sp = new Packages.arc.scene.ui.ScrollPane(new T()); }"
                 " catch(e){ sp = null; }"
                 " out.push('ScrollPaneHasAdd=' + ((sp !== null && typeof sp.add === 'function') ? 'YES' : 'NO')); })();")
    probe.append("print('MAISHAPES: ' + out.join(' '));")
    probe.append("void 0;")
    shapes = {}
    if used and not missing:
        try:
            res = srv.js(' '.join(probe))
            flat = ' '.join(str(x) for x in res)
            for k, v in re.findall('([A-Za-z]+)=([A-Z_]+)', flat):
                shapes[k] = v
        except Exception as e:
            shapes = {'<engine>': 'FAIL ' + str(e)[-200:]}

    problems = []
    if 'ready,' not in joined:
        problems.append('mod never reported ready')
    if 'init failed' in joined or 'bootstrap failed' in joined:
        problems.append('init threw')
    if 'MAISELF:\u8bbe\u7f6e\u8868\u683c\u53ef\u5efa' not in joined:
        problems.append('maiSelfTest did not build the settings table')
    if 'MAISELF:' in joined and '\u586b\u4e86 0 ' in joined:
        problems.append('maiSelfTest filled no rows')
    if '\u6570\u636e\u76ee\u5f55' not in joined or 'mods \u76ee\u5f55' not in joined:
        problems.append('maiDiag is missing a directory line')
    if 'MAISET:no ui' not in joined:
        problems.append('maiSettings should report "no ui" headless')
    if not used:
        problems.append('maiSelfTest did not report which Table methods it used')
    if missing:
        problems.append('no engine probe shell for Table method(s): ' + ', '.join(missing))
    bad = [m + '=' + shapes.get(m, 'MISSING') for m in used
           if shapes.get(m) not in ('RESOLVED', 'OK_SKIN')]
    if bad:
        problems.append('Table method(s) do not resolve in the engine: ' + ', '.join(bad))
    # comments talk about the ambiguity, so cut them before scanning code
    code_only = '\n'.join(l.split('//')[0] for l in io.open(MAIN, 'rb').read().decode('utf-8').splitlines())
    if re.search('[.](table|scrollPane)[(][ ]*function', code_only):
        problems.append('main.js calls t.table(function) / t.scrollPane(function) -- '
                        'ambiguous in this engine, keep the settings rows flat')

    # v0.4.0 wiring: a headless engine has no scene, so these can only be pinned
    # at the source level.  Each one is a bug that already shipped once.
    if 'closeOnBack()' not in code_only:
        problems.append('the modal panel never calls closeOnBack() -- arc Dialog.addCloseButton() '
                        'is an empty default (Dialog.java:453-455), so it cannot be dismissed')
    if 'buttons.button(' not in code_only:
        problems.append('the panel has no visible close button in d.buttons')
    if 'Vars.ui.logic' not in code_only or 'canvas.save()' not in code_only:
        problems.append('the review bar is not wired to the vanilla logic editor '
                        '(Vars.ui.logic / canvas.save) -- m08924 asked for that review')
    # v0.4.1 crash: Table.pane(cons) gives you a ScrollPane, which has no add().
    # Hand pane() a real Table instead -- that is what host = new Table() is for.
    if re.search('[.]pane[(][ ]*function', code_only):
        problems.append('main.js passes a builder to pane() -- that returns a ScrollPane, '
                        'not a Table; build a Table and hand it to pane(host)')
    if re.search('[.]pane[(][^;\n]*[.]get[(][)]', code_only):
        problems.append('pane(...).get() is a ScrollPane, not a Table (v0.4.0 crashed on it)')
    if shapes.get('ScrollPaneHasAdd', 'NO') == 'YES':
        problems.append('this engine DOES give ScrollPane an add() -- the v0.4.1 workaround '
                        'may be unnecessary, re-check')
    if 'toggleAiPanel();' not in code_only:
        problems.append('F4 does not open the AI panel (toggleAiPanel) -- m08925 asked for that')

    # v0.4.3: an HTTP callback cannot be waited for on the main thread.  httpJson
    # delivers it through Core.app.post, so a spin loop here always times out --
    # that is exactly why F7 showed sidecar unavailable with a literal pending.
    if re.search('while[ ]*[(][ ]*[A-Za-z_]+[ ]*===[ ]*"pending"', code_only):
        problems.append('main.js busy-waits for an HTTP callback: the callback is posted back to the main thread, so it never lands')
    if re.search('while[ ]*[(][ ]*out[ ]*===[ ]*"[?]"', code_only):
        problems.append('ping() busy-waits on /health -- same deadlock, use probeSidecar()')
    if 'function regionAroundBox(' not in code_only:
        problems.append('the region request is not async (regionAroundBox) -- F7 would hang')
    if 'regionCandidatesText(rtext)' in code_only:
        problems.append('F7 still treats maiRegion() as synchronous')

    # ---- v0.4.4: the sidecar transport is a hand-rolled socket now.
    # URL.openConnection() hands back sun.net.www.protocol.http.HttpURLConnection, which
    # java.base does not export; Rhino binds members against the RUNTIME class (MemberBox),
    # so setRequestMethod / getResponseCode / getInputStream all threw
    # IllegalAccessException.  A JS-side fake socket would never catch that, so talk to a
    # real local HTTP server -- and to a dead port, which must come back as code -1.
    hs, hport = echo_server()
    try:
        try:
            hout = srv.js(' '.join(http_probe(hport) + ['void 0;']))
            htext = '\n'.join(str(x) for x in hout)
        except Exception as exc:
            htext = ''
            problems.append('maiHttpRaw threw in the engine: %s' % str(exc)[-300:])
        hres = {}
        for k, code, flag in re.findall(r'MAIHTTP([123]):(-?\d+)(?::(MARK|NOMARK|ECHO|NOECHO))?', htext):
            hres[k] = (int(code), flag)
        for k, code, flag in (('1', 200, 'MARK'), ('2', 200, 'ECHO'), ('3', -1, '')):
            got = hres.get(k)
            if got is None:
                problems.append('MAIHTTP%s printed nothing' % k)
                continue
            if got[0] != code:
                problems.append('MAIHTTP%s code=%r wanted %r' % (k, got[0], code))
            elif flag and got[1] != flag:
                problems.append('MAIHTTP%s body flag=%r wanted %r' % (k, got[1], flag))
    finally:
        hs.shutdown()
        hs.server_close()

    # v0.4.4 red lines: the transport must stay a raw socket, and the settings category
    # must show the vanilla logic badge (Icon.logic).
    if 'openConnection(' in code_only:
        problems.append('main.js calls URL.openConnection() again -- Rhino cannot call methods '
                        'on sun.net.www.protocol.http.HttpURLConnection (IllegalAccessException)')
    if 'new Packages.java.net.Socket()' not in code_only:
        problems.append('the sidecar transport is no longer a raw java.net.Socket')
    if 'Packages.mindustry.gen.Icon.logic' not in code_only:
        problems.append('the settings category lost the vanilla logic badge (Icon.logic)')
    # v0.4.4: try/finally with a nested try/catch inside the finally body makes the v160.7
    # Rhino codegen die (ArrayIndexOutOfBoundsException "arraycopy ..." / "invalid bytecode"),
    # and Scripts.runConsole hands that error back as a String, so the whole mod loads
    # silently dead.  Keep the transport on try/catch + an explicit close.
    if '}finally{' in code_only:
        problems.append('main.js introduced try/finally again -- the v160.7 Rhino codegen '
                        'throws on finally bodies that contain try/catch')
    if 'try{ if(sock !== null){ sock.close(); } }catch(e1){}' not in code_only:
        problems.append('the socket transport lost its explicit socket close')
    # ---- P3 region snapshot, read back from the engine
    snap = None
    for l in text.splitlines():
        if l.startswith('MAISNAP:'):
            try:
                snap = json.loads(l[len('MAISNAP:'):])
            except Exception as exc:
                problems.append('maiSnapshot returned bad JSON: %s' % exc)
    if snap is None:
        problems.append('maiSnapshot printed nothing')
    else:
        bx, by = srv.base
        names = sorted(str(c.get('block')) for c in snap.get('grid') or [])
        # a 2x2 container is 4 tiles, the 1x1 switch is 1, the processor is 1:
        # every other tile in the box is empty and its block name is 'air'.
        want_names = ['container'] * 4 + ['micro-processor', 'switch']
        if names != want_names:
            problems.append('region grid is %r, wanted %r (empty tiles must be skipped)'
                            % (names, want_names))
        if snap.get('cells') != 6:
            problems.append('region cells: %r' % (snap.get('cells'),))
        procs = snap.get('processors') or []
        if len(procs) != 1 or str(procs[0].get('code')) != 'noop':
            problems.append('region processors: %r' % (procs,))
        elif procs[0].get('x') != bx or procs[0].get('y') != by:
            problems.append('region processor at %r, expected %r' % (procs[0], (bx, by)))
        # the box is clamped to the map: a processor at 0,0 asks for -1,-1
        want = {'x1': max(0, bx - 1), 'y1': max(0, by - 1),
                'x2': bx + 4, 'y2': by + 4}
        if snap.get('bounds') != want:
            problems.append('region bounds: %r' % (snap.get('bounds'),))
        if snap.get('truncated') is not False:
            problems.append('region truncated flag: %r' % (snap.get('truncated'),))

    if problems:
        print('FAIL ' + '; '.join(problems))
        print(joined[-1500:])
        return 1
    print('ui smoke: main.js initialised in the real engine')
    if snap is not None:
        print('  region snapshot: %d cell(s), %d processor(s)' % (len(snap.get('grid') or []), len(snap.get('processors') or [])))
    if shapes:
        print('  table methods resolved: ' + ' '.join(
            '%s=%s' % (m, shapes.get(m, '?')) for m in used))
    for l in lines:
        if l.startswith(('MAISELF:', 'MAIDIAG:')):
            print('  ' + l[:300])
    return 0


if __name__ == '__main__':
    sys.exit(main())
