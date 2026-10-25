#!/usr/bin/env python3
"""Runtime probes: assert what the real executor DOES, not what a lint says.

Why this exists
---------------
Every semantic claim in docs/断言表.md used to be checked by hand: boot the v160.7
jar, place a processor, read a number off the scene, write it down. That is how the
status-effect slot kept its claim backwards for a whole release -- the static check
and the report agreed with each other and neither had run.

Each probe in manifest.json is a program plus the numbers the real executor must
produce. Adding a semantic claim means adding a probe, and a wrong claim now fails
a gate instead of surviving until someone re-reads a class file.

Usage
-----
    python tests/probes/run_probes.py              # all probes
    python tests/probes/run_probes.py status-v160  # ids containing this

Exit: 0 every probe passed, 1 a probe failed, 3 nothing could run (no JRE, or the
versioned jars are absent -- they live in out/ and are not in git, so a fresh clone
SKIPs this rather than failing it).
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'tools'))

JAR_ATTR = {'160': 'V160_JAR', '159': 'V159_JAR'}

#: runs inside the game: report duration and the applied bit for the named effects
JS = r'''
var G = Packages.mindustry.gen.Groups.unit;
var U = null;
for(var i = 0; i < G.size(); i++){
    var u = G.index(i);
    if(u.team == Packages.mindustry.game.Team.sharded){ U = u; break; }
}
if(U === null){ print('NOUNIT'); } else {
    var SE = Packages.mindustry.Vars.content.statusEffects();
    var want = %s;
    for(var j = 0; j < SE.size; j++){
        var e = SE.get(j);
        if(!want[e.name]) continue;
        print('E\t' + e.name + '\t' + Math.round(U.getDuration(e)) + '\t' + U.hasEffect(e));
    }
}
'''


def probe_js(names):
    return JS % json.dumps({n: 1 for n in names})


def read_effects(lines):
    got = {}
    for line in lines:
        if not line.startswith('E\t'):
            continue
        _, name, dur, has = line.split('\t')[:4]
        got[name] = (int(float(dur)), has == 'true')
    return got


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    manifest = json.loads((HERE / 'manifest.json').read_text(encoding='utf-8'))
    probes = manifest['probes']
    if argv:
        probes = [p for p in probes if any(a.lower() in p['id'].lower() for a in argv)]
    try:
        import mlogsim as M
    except Exception as exc:
        print('SKIP cannot import tools/mlogsim.py: %s' % exc)
        return 3
    java = M._default_java()
    if not java:
        print('SKIP no java found (set MLOGSIM_JAVA)')
        return 3

    passed = []
    failed = []
    skipped = []
    for p in probes:
        jar = getattr(M, JAR_ATTR[p['jar']], None)
        if not jar or not pathlib.Path(jar).is_file():
            skipped.append((p['id'], 'missing jar ' + str(jar)))
            continue
        names = list(p.get('expect') or {})
        srv = None
        try:
            srv = M.Server(java, jar)
            srv._core_spec = 'copper:100'
            srv._unit_spec = [['flare', 1]]
            srv.prepare()
            M.run_mlog(srv, 'p', p['code'], steps=int(p.get('steps', 20)))
            got = read_effects(srv.js(probe_js(names)))
        except Exception as exc:
            failed.append((p['id'], '%s: %s' % (type(exc).__name__, str(exc)[:120])))
            continue
        finally:
            if srv is not None:
                try:
                    srv.close()
                except Exception:
                    pass
        bad = []
        for name, want in (p.get('expect') or {}).items():
            dur, has = got.get(name, (None, None))
            if dur != want:
                bad.append('%s duration want %s got %s' % (name, want, dur))
        for name, want in (p.get('expect_has') or {}).items():
            dur, has = got.get(name, (None, None))
            if has != want:
                bad.append('%s hasEffect want %s got %s' % (name, want, has))
        if bad:
            failed.append((p['id'], '; '.join(bad)))
        else:
            passed.append(p['id'])

    for pid in passed:
        print('PASS ' + pid)
    for pid, why in skipped:
        print('SKIP ' + pid + ' -- ' + why)
    for pid, why in failed:
        print('FAIL ' + pid + ' -- ' + why)
    ran = len(passed) + len(failed)
    print('%d/%d probe(s) passed, %d skipped' % (len(passed), ran, len(skipped)))
    if failed:
        return 1
    return 0 if passed else 3


if __name__ == '__main__':
    raise SystemExit(main())
