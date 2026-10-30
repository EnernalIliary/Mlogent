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


def select_probe(srv):
    """v0.5.0: F3 IS the left mouse button -- hold to drag, release to snapshot.

    The mouse cannot be driven here, so the state machine is pinned directly: selPress()
    is the button going down (there is no arming step any more) and selRelease() is it
    coming up. The highlight must use the vanilla rectangle recipe -- Lines.stroke(2) plus
    a Pal.accentBack/Pal.accent double outline anchored at the box's LOWER-LEFT corner
    (InputHandler.java:1758-1795) -- not a translucent fill, and not a centre anchor.
    """
    bx, by = srv.base
    return [
        "print('MAIRECT:' + maiSelRect(%d, %d, %d, %d));" % (bx + 4, by + 4, bx - 1, by - 1),
        "print('MAIRECT2:' + maiSelRect(%d, %d, %d, %d));" % (bx - 1, by - 1, bx + 4, by + 4),
        "print('MAIDUMP:' + JSON.stringify(maiDump(%d, %d, %d, %d)));"
        % (bx - 1, by - 1, bx + 4, by + 4),
        # the highlight is Lines.rect(x,y,w,h) + Lines.stroke(2) + Draw.color(Color); pin
        # those overloads by reflection (a headless engine has no GL context, so drawing
        # itself would throw and the bug would hide in the catch).
        "var DL = Packages.java.lang.Class.forName('arc.graphics.g2d.Lines');",
        "var lm = DL.getMethods(), hasLRect = 'NO', hasStroke = 'NO';",
        "for(var li = 0; li < lm.length; li++){",
        "  var ln = String(lm[li].getName()), lp = lm[li].getParameterTypes();",
        "  if(ln === 'rect' && lp.length === 4 && String(lp[0].getName()) === 'float'){ hasLRect = 'YES'; }",
        "  if(ln === 'stroke' && lp.length === 1 && String(lp[0].getName()) === 'float'){ hasStroke = 'YES'; }",
        "}",
        "var DD = Packages.java.lang.Class.forName('arc.graphics.g2d.Draw');",
        "var dm = DD.getMethods(), hasCol = 'NO';",
        "for(var di = 0; di < dm.length; di++){",
        "  var dn = String(dm[di].getName()), dp = dm[di].getParameterTypes();",
        "  if(dn === 'color' && dp.length === 1 && String(dp[0].getName()) === 'arc.graphics.Color'){ hasCol = 'YES'; }",
        "}",
        "print('MAIDRAWAPI:' + hasLRect + ':' + hasStroke + ':' + hasCol + ':' + (Packages.mindustry.graphics.Pal.accentBack === null ? 'noaccentback' : 'accentback'));",
        # the size label needs the generated Fonts holder (mindustry.gen.Fonts.outline)
        "var hasFont = 'NO';",
        "try{ var FC = Packages.java.lang.Class.forName('mindustry.ui.Fonts'); var ff = FC.getField('outline'); if(ff !== null){ hasFont = 'YES'; } }catch(e1){ hasFont = 'NO'; }",
        "print('MAIFONTAPI:' + hasFont);",
        # v0.5.0: F3 down = button down (no arming), F3 up = button up
        "print('MASELIDLE:' + maiSelState());",
        "print('MASELPRESS:' + maiSelPress(%d, %d));" % (bx + 5, by + 5),
        "print('MASELDOWN:' + maiSelState());",
        "print('MASELMOVE:' + maiSelMove(%d, %d));" % (bx + 9, by + 7),
        "print('MASELREL:' + maiSelRelease());",
        "print('MASELEND:' + maiSelState());",
        # the highlight args are the box's LOWER-LEFT corner in world units (x8)
        "print('MASELDRAW:' + maiSelDraw(%d, %d, %d, %d));" % (bx + 5, by + 5, bx + 9, by + 7),
        # the hint must be showInfoFade (a Touchable.disabled label, UI.java:373), never
        # showText -- a Dialog eats the mouse and the drag never starts.
        "var UF = Packages.java.lang.Class.forName('mindustry.core.UI');",
        "var um = UF.getMethods(), hasFade = 'NO';",
        "for(var ui = 0; ui < um.length; ui++){",
        "  var un = String(um[ui].getName()), up = um[ui].getParameterTypes();",
        "  if(un === 'showInfoFade' && up.length === 1 && String(up[0].getName()) === 'java.lang.String'){ hasFade = 'YES'; }",
        "}",
        "print('MAIHINTAPI:' + hasFade);",
    ]


def arrow_probe():
    """v0.4.7: findings -> one arrow per line, glued to that line's StatementElem.

    The mapping (finding.line -> statements child index -> pixel position) IS the feature,
    and it rests on two engine facts a JS fake cannot pin: children come back in statement
    order, and the header row of each StatementElem is 38 px tall (LCanvas.java:427-491).
    The icon is passed in because a headless engine has no atlas (Icon.right is null), and
    line 0 / line 9 must be skipped instead of throwing -- a stale finding after an edit
    can point past the end of the code.
    """
    return [
        "var arT = Packages.arc.scene.ui.layout.Table;",
        "var arRoot = new arT();",
        "var arSt = new arT();",
        "arRoot.add(arSt).padLeft(40).padTop(12).growX();",
        "var arKids = [];",
        "for(var arI = 0; arI < 4; arI++){",
        "  var arE = new arT();",
        # no Label here: add(CharSequence) needs a Label style from Core.scene, which is
        # null in a headless engine -- an Image child needs no style.
        "  arE.add(new Packages.arc.scene.ui.Image(new Packages.arc.graphics.g2d.TextureRegion())).growX().height(38);",
        "  arSt.add(arE).growX().height(60);",
        "  if(arI < 3){ arSt.row(); }",
        "  arKids.push(arE);",
        "}",
        "arRoot.pack();",
        "print('MAIARST:' + arSt.x + ',' + arSt.y);",
        "for(var arJ = 0; arJ < arKids.length; arJ++){",
        "  print('MAIARROWKID:' + arJ + ':' + arKids[arJ].x + ',' + arKids[arJ].y + ',' + arKids[arJ].getHeight());",
        "}",
        "var arF = JSON.stringify([",
        "{sev:'WARN', line:1, rid:'link-name-not-bound', msg:'one'},",
        "{sev:'ERR', line:3, rid:'sensor-not-a-property', msg:'three-a'},",
        "{sev:'INFO', line:3, rid:null, msg:'three-b'},",
        "{sev:'WARN', line:9, rid:null, msg:'past the end'},",
        "{sev:'WARN', line:0, rid:null, msg:'before the start'}",
        "]);",
        "var arDr = new Packages.arc.graphics.g2d.TextureRegion();",
        "print('MAIARROWS:' + maiArrows(arSt, arF, arDr));",
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
    ] + region_probe(srv) + select_probe(srv) + arrow_probe() + [
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
    if '\u533a\u57df\u8868\u683c' not in joined:          # 区域表格
        problems.append('maiSelfTest did not build the region table')
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
    # v0.4.5: a refused socket is the everyday "sidecar isn't running" case, so the
    # panel must translate it instead of pasting the Java stack, and a link name the
    # code reads but nothing answers to must be named in the panel (p.missing).
    if 'Connection refused' not in code_only:
        problems.append('main.js stopped explaining a refused sidecar connection')
    if 'p.missing' not in code_only:
        problems.append('the region panel stopped reporting unbound link names (p.missing)')
    # v0.4.6: the payload stores link coordinates relative to the processor
    # (LogicBlock.java:304-307), so every request that carries links has to say where
    # the processor is.  Without the origin the game keeps the link entries but none of
    # them resolves (valid=false), which is silent at run time.
    if 'function originOf(' not in code_only:
        problems.append('main.js lost originOf() -- link coordinates would be written '
                        'as absolute numbers into a relative payload')
    if 'origin: originOf(b)' not in code_only:
        problems.append('/plan or /compose stopped sending the processor origin')
    # v0.4.8: F3 drag-select.  F8 is the vanilla console (Binding.java:107
    # console = KeyCode.f8) and F9/F10 are taken too, so the box lives on F3; the
    # highlight is drawn in world space instead of becoming a scene element (v0.4.1
    # crashed exactly by inventing a result area in the scene tree).
    for needle, why in (('var KEY_SELECT  = ["f3"];', 'F3 is no longer the select key'),
                        ('function selRect(', 'selRect() is gone -- drag normalisation lost'),
                        ('function mouseTile(', 'mouseTile() is gone'),
                        ('function drawSelection(', 'the drag highlight is gone'),
                        ('Events.run(ET.Trigger.draw',
                         'the drag highlight is no longer drawn in world space'),
                        ('function dumpRegion(', 'dumpRegion() is gone'),
                        ('api.maiSelRect = function', 'the selRect test hook is gone')):
        if needle not in code_only:
            problems.append('v0.4.8: ' + why)
    # v0.4.9: F3 must not open a dialog (it ate the mouse: user reported 2026-10-30 that
    # the popup blocked dragging), and the drag must be anchored at the mouse-down tile.
    for needle, why in (('function hint(', 'the non-blocking hint() is gone'),
                        ('function selPress(', 'selPress() is gone -- the drag has no press anchor'),
                        ('function selDrawArgs(', 'selDrawArgs() is gone'),
                        ('api.maiSelPress = function', 'the selPress test hook is gone')):
        if needle not in code_only:
            problems.append('v0.4.9: ' + why)
    if 'popup("Mlog辅助 · 框选"' in code_only:
        problems.append('v0.4.9: F3 still pops a Dialog -- a Dialog takes the mouse and the drag never starts')
    # v0.5.0: F3 is the left mouse button (user 2026-10-30: "f3就是鼠标左键"), and the
    # highlight copies the vanilla rectangle recipe (InputHandler.java:1758-1795):
    # Lines.stroke(2) + accentBack/accent double outline, anchored at the lower-left
    # corner. No arming step, no translucent fill, no keyTap (that only fires on release).
    for needle, why in (('var selHolding = false', 'the hold state is gone'),
                        ('function drawSizeText(', 'the vanilla size label is gone'),
                        ('L.stroke(2);', 'the 2px outline stroke is gone'),
                        ('Pal.accentBack', 'the accentBack shadow line is gone'),
                        ('Core.input.keyDown(selKey)', 'F3 is no longer read as a held button')):
        if needle not in code_only:
            problems.append('v0.5.0: ' + why)
    for needle, why in (('selArmed', 'the arming step is back -- F3 must start the drag itself'),
                        ('D.alpha(0.35)', 'the translucent fill is back -- vanilla is outline only'),
                        ('keyTap(Packages.arc.input.KeyCode[KEY_SELECT',
                         'F3 is read as a tap again -- it must be a held button')):
        if needle in code_only:
            problems.append('v0.5.0: ' + why)
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

    # ---- v0.4.8 F3 drag-select: a backwards drag is the same box, and the summary is
    # produced without the sidecar (a headless engine has no Vars.ui, so the post is
    # skipped rather than throwing inside a daemon thread).
    bx, by = srv.base
    rect = rect2 = dump = None
    for l in text.splitlines():
        if l.startswith('MAIRECT:'):
            try:
                rect = json.loads(l[len('MAIRECT:'):])
            except Exception as exc:
                problems.append('maiSelRect returned bad JSON: %s' % exc)
        elif l.startswith('MAIRECT2:'):
            try:
                rect2 = json.loads(l[len('MAIRECT2:'):])
            except Exception as exc:
                problems.append('maiSelRect returned bad JSON: %s' % exc)
        elif l.startswith('MAIDUMP:'):
            try:
                dump = json.loads(l[len('MAIDUMP:'):])
            except Exception as exc:
                problems.append('maiDump returned bad JSON: %s' % exc)
    if rect is None or rect2 is None:
        problems.append('maiSelRect printed nothing')
    else:
        if rect != rect2:
            problems.append('a backwards drag gave a different box: %r vs %r' % (rect, rect2))
        # selRect() only normalises the drag; clamping to the map is regionSnapshot()'s
        # job (the probe drags to -1,-1 on purpose: a processor at 0,0 is the normal case).
        want_box = {'x1': bx - 1, 'y1': by - 1, 'x2': bx + 4, 'y2': by + 4}
        want_box['w'] = want_box['x2'] - want_box['x1'] + 1
        want_box['h'] = want_box['y2'] - want_box['y1'] + 1
        if rect != want_box:
            problems.append('drag rect %r wanted %r' % (rect, want_box))
    if dump is None:
        problems.append('maiDump printed nothing')
    else:
        for piece in ('区域 ', '处理器 1', 'micro-processor'):
            if piece not in dump:
                problems.append('dump summary is missing %r: %r' % (piece, dump[:160]))
    # ---- v0.5.0: F3 IS the left button. Press starts the drag with no arming step,
    # release ends it; the highlight is the vanilla outline anchored at the box corner.
    sel = {}
    for l in text.splitlines():
        for key in ('MASELIDLE', 'MASELPRESS', 'MASELDOWN', 'MASELMOVE', 'MASELREL',
                    'MASELEND', 'MASELDRAW', 'MAIDRAWAPI', 'MAIHINTAPI', 'MAIFONTAPI'):
            if l.startswith(key + ':'):
                sel[key] = l[len(key) + 1:]

    def sel_state(key, label):
        raw = sel.get(key)
        if raw is None:
            problems.append('%s printed nothing' % label)
            return {}
        try:
            return json.loads(raw)
        except Exception as exc:
            problems.append('%s returned bad JSON: %s' % (label, exc))
            return {}

    idle = sel_state('MASELIDLE', 'maiSelState (before press)')
    if idle.get('holding') is not False or idle.get('dragging') is not False:
        problems.append('the select must start idle (holding/dragging false): %r' % (idle,))
    if sel.get('MASELPRESS') != 'true' or sel.get('MASELMOVE') != 'true':
        problems.append('selPress/selMove refused a plain press: %r %r'
                        % (sel.get('MASELPRESS'), sel.get('MASELMOVE')))
    down = sel_state('MASELDOWN', 'maiSelState (while held)')
    if down.get('holding') is not True or down.get('dragging') is not True:
        problems.append('pressing F3 must hold AND drag immediately: %r' % (down,))
    want_box = {'x1': bx + 5, 'y1': by + 5, 'x2': bx + 9, 'y2': by + 7, 'w': 5, 'h': 3}
    try:
        got_box = json.loads(sel.get('MASELREL') or '{}')
    except Exception as exc:
        problems.append('maiSelRelease returned bad JSON: %s' % exc)
        got_box = {}
    if got_box != want_box:
        problems.append('the drag box is not anchored at the mouse-down tile: %r wanted %r'
                        % (got_box, want_box))
    end = sel_state('MASELEND', 'maiSelState (after release)')
    if end.get('holding') is not False or end.get('dragging') is not False:
        problems.append('releasing did not clear the select state: %r' % (end,))
    # vanilla anchors the outline at the box's lower-left corner in world units (x8):
    # Lines.rect(x, y, w, h) draws from (x, y) up-right, unlike Draw.rect's centre anchor.
    want_draw = {'x': (bx + 5) * 8, 'y': (by + 5) * 8, 'w': 40, 'h': 24}
    try:
        got_draw = json.loads(sel.get('MASELDRAW') or '{}')
    except Exception as exc:
        problems.append('maiSelDraw returned bad JSON: %s' % exc)
        got_draw = {}
    if got_draw != want_draw:
        problems.append('the highlight is not corner-anchored: %r wanted %r'
                        % (got_draw, want_draw))
    draw_api = (sel.get('MAIDRAWAPI') or '').split(':')
    if draw_api[:3] != ['YES', 'YES', 'YES'] or len(draw_api) < 4 or draw_api[3] != 'accentback':
        problems.append('Lines.rect(float,float,float,float)/Lines.stroke(float)/'
                        'Draw.color(Color)/Pal.accentBack missing: %r' % (sel.get('MAIDRAWAPI'),))
    if sel.get('MAIFONTAPI') != 'YES':
        problems.append('mindustry.gen.Fonts.outline is missing -- the size label has no font: %r'
                        % (sel.get('MAIFONTAPI'),))
    if sel.get('MAIHINTAPI') != 'YES':
        problems.append('UI.showInfoFade(String) is missing -- the non-blocking hint has no API: %r'
                        % (sel.get('MAIHINTAPI'),))

    # ---- v0.4.7 review arrows: finding.line -> statements child -> pixel position
    arrows = None
    ast = None
    kids = {}
    for l in text.splitlines():
        if l.startswith('MAIARROWS:'):
            arrows = l[len('MAIARROWS:'):].split()
        elif l.startswith('MAIARST:'):
            try:
                ast = [float(x) for x in l[len('MAIARST:'):].split(',')]
            except Exception:
                ast = None
        elif l.startswith('MAIARROWKID:'):
            m = re.match(r'MAIARROWKID:(\d+):([-\d.]+),([-\d.]+),([-\d.]+)$', l)
            if m:
                kids[int(m.group(1))] = tuple(float(m.group(i)) for i in (2, 3, 4))
    if arrows is None:
        problems.append('maiArrows printed nothing')
    else:
        # 2 arrows (line 1 WARN, line 3 ERR+INFO -> ERR wins), and 0 / 9 are out of range
        # "arrows N" is one token, so arrows[0] == 'arrows' and arrows[1] == str(N)
        if arrows[:2] != ['arrows', '2'] or len(arrows) != 4:
            problems.append('arrows: %r (wanted 2: line 1 and line 3; 0 and 9 must be skipped)' % (arrows,))
        got = {}
        for tok in arrows[2:]:
            parts = tok.split(':')
            if len(parts) != 5:   # line:x,y:SEV:items:v
                problems.append('arrow token %r' % tok)
                continue
            xy = parts[1].split(',')
            got[int(parts[0])] = (float(xy[0]), float(xy[1]), parts[2], int(parts[3]), parts[4])
        if set(got) != {1, 3}:
            problems.append('arrow lines %r, wanted {1, 3}' % (sorted(got),))
        if 1 in got and got[1][2:4] != ('WARN', 1):
            problems.append('line 1 arrow: %r, wanted WARN with 1 finding' % (got[1],))
        if 3 in got and got[3][2:4] != ('ERR', 2):
            problems.append('line 3 arrow: %r, wanted ERR (worst of ERR+INFO) with 2 findings' % (got[3],))
        for line, v in got.items():
            if v[4] != 'v':
                problems.append('arrow on line %d is not visible' % line)
            if ast is None or (line - 1) not in kids:
                continue
            kx, ky, kh = kids[line - 1]
            want_x = ast[0] + kx - 16 - 2          # left gutter when there is room
            if want_x < 2:
                want_x = ast[0] + kx + 2
            want_y = ast[1] + ky + kh - 19 - 8     # header row is 38 px tall
            if abs(v[0] - round(want_x)) > 1 or abs(v[1] - round(want_y)) > 1:
                problems.append('arrow on line %d at %r, wanted (%r, %r)' % (line, v[:2], round(want_x), round(want_y)))
        if 1 in got and 3 in got and not got[1][1] > got[3][1]:
            problems.append('arrow on line 1 is not above the one on line 3 -- children order is off')

    # ---- v0.4.7: the review arrows, and the fake-WARN fix they came with.
    # LogicDialog.executor is package-private (real v160.7 reflection: MAIFIELDS showed
    # 'executor:pkg'), and Rhino only exposes public members -- so L.executor was
    # undefined, linkNames() came back empty, and every link slot looked unbound.
    # Read it through the reflective accessor instead of touching the field directly.
    if 'function logicExecutor(' not in code_only:
        problems.append('main.js lost logicExecutor() -- LogicDialog.executor is package-private; '
                        'a direct read is undefined and every link slot looks unbound')
    if re.search(r'(?<![A-Za-z_.])L[.]executor', code_only):
        problems.append('main.js reads L.executor directly again -- Rhino cannot see a package-private field')
    if 'setAccessible(true)' not in code_only:
        problems.append('logicExecutor() no longer calls setAccessible(true)')
    # linkNames() must distinguish "no links" ([]) from "cannot read them" (null):
    # an empty array makes quickcheck report a WARN on every link slot.
    if 'linkKnown' not in code_only:
        problems.append('the review stopped telling "no links" apart from "cannot read the link table"')
    if 'function syncArrows(' not in code_only or 'Touchable.childrenOnly' not in code_only:
        problems.append('the in-line review arrows are gone (syncArrows / Touchable.childrenOnly)')
    if 'function tapLine(' not in code_only:
        problems.append('arrow taps are not wired through tapLine()')
    if 'function layoutArrows(' not in code_only:
        problems.append('arrows are no longer re-positioned every frame (layoutArrows)')
    # ---- v0.6.0 the region panel: F3 -> dump + /region -> dialog with a per-processor button
    if 'function buildRegionTable(' not in code_only or 'function showRegionPanel(' not in code_only:
        problems.append('the region panel is gone (buildRegionTable / showRegionPanel)')
    if 'function buildAt(' not in code_only or 'showAiPanel(b);' not in code_only:
        problems.append('the region panel no longer hands a processor to the AI panel')
    if 'labelWrap(String(candText))' not in code_only:
        problems.append('the region panel lost its scrollable candidate text (labelWrap)')
    if 'function showAiPanel(target)' not in code_only:
        problems.append('showAiPanel() no longer accepts an explicit target build')

    if problems:
        print('FAIL ' + '; '.join(problems))
        print(joined[-1500:])
        return 1
    print('ui smoke: main.js initialised in the real engine')
    if snap is not None:
        print('  region snapshot: %d cell(s), %d processor(s)' % (len(snap.get('grid') or []), len(snap.get('processors') or [])))
    if arrows is not None:
        print('  review arrows: ' + ' '.join(arrows[2:]))
    if shapes:
        print('  table methods resolved: ' + ' '.join(
            '%s=%s' % (m, shapes.get(m, '?')) for m in used))
    for l in lines:
        if l.startswith(('MAISELF:', 'MAIDIAG:')):
            print('  ' + l[:300])
    return 0


if __name__ == '__main__':
    sys.exit(main())
