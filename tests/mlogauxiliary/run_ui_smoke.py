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
import io, os, re, sys

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
    if 'toggleAiPanel();' not in code_only:
        problems.append('F4 does not open the AI panel (toggleAiPanel) -- m08925 asked for that')

    if problems:
        print('FAIL ' + '; '.join(problems))
        print(joined[-1500:])
        return 1
    print('ui smoke: main.js initialised in the real engine')
    if shapes:
        print('  table methods resolved: ' + ' '.join(
            '%s=%s' % (m, shapes.get(m, '?')) for m in used))
    for l in lines:
        if l.startswith(('MAISELF:', 'MAIDIAG:')):
            print('  ' + l[:300])
    return 0


if __name__ == '__main__':
    sys.exit(main())
