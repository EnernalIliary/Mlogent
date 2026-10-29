"""Smoke the whole main.js init path in the REAL game engine (v160.7 Rhino).

The settings UI cannot be built headless (Vars.ui is null there -- Vars.java:209/332),
so this test does what the game does, minus the pixels:

  * loads rules.generated.js and quickcheck.js into the script scope, then main.js
    with its two require("...") calls swapped for those globals;
  * asserts init reports "ready" and never prints "init failed"/"bootstrap failed";
  * asks the mod itself to build its settings table against a fake Table
    (maiSelfTest) -- this catches Table/Cell API drift and broken wiring;
  * reads the diagnostics block (maiDiag) and checks it names both directories;
  * confirms maiSettings() says "no ui" headless instead of throwing.

Gate treats exit 3 as SKIP (no JRE / no jar).

Why this exists: the first version of the console-function mount read scope.get(k, scope)
back, which throws "Cannot find function get" under the real engine -- main.js died
after loading its rule table and the mod looked half-installed.
"""
import io, os, sys

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

    problems = []
    if 'ready,' not in joined:
        problems.append('mod never reported ready')
    if 'init failed' in joined or 'bootstrap failed' in joined:
        problems.append('init threw')
    if 'MAISELF:\u8bbe\u7f6e\u8868\u683c\u53ef\u5efa' not in joined:
        problems.append('maiSelfTest did not build the settings table')
    if 'MAISELF:' in joined and '0 \u884c' in joined:
        problems.append('maiSelfTest filled no rows')
    if '\u6570\u636e\u76ee\u5f55' not in joined or 'mods \u76ee\u5f55' not in joined:
        problems.append('maiDiag is missing a directory line')
    if 'MAISET:no ui' not in joined:
        problems.append('maiSettings should report "no ui" headless')

    if problems:
        print('FAIL ' + '; '.join(problems))
        print(joined[-1500:])
        return 1
    print('ui smoke: main.js initialised in the real engine')
    for l in lines:
        if l.startswith(('MAISELF:', 'MAIDIAG:')):
            print('  ' + l[:300])
    return 0


if __name__ == '__main__':
    sys.exit(main())
