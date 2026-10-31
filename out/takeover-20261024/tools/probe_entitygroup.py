"""Separate calls, one question each, so a hang or a hard Java error is localised."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import mlogsim as M  # noqa: E402

srv = M.Server(M._default_java(), M.V160_JAR)
srv.prepare()
M.run_mlog(srv, 'p', 'noop', steps=1, update='none')

SETUP = ("var G = Packages.mindustry.gen.Groups.unit;"
         "var u = Packages.mindustry.content.UnitTypes.dagger.create(Packages.mindustry.game.Team.sharded);"
         "u.x = 28; u.y = 20; G.add(u);")

CALLS = [
    ('size', "print('S1:' + (typeof G.size) + ' ' + G.size());"),
    ('rawSeq', "var r = G.rawSeq(); print('S2:' + (r === null) + ' ' + (typeof r));"),
    ('each', "var c = 0; G.each(function(x){ c++; }); print('S3:' + c);"),
    ('get', "print('S4:' + (typeof G.get));"),
    ('itemsGet', "print('S5:' + (typeof Packages.mindustry.Vars.content.items().get));"),
    ('rawSeqGet', "var r = G.rawSeq(); print('S6:' + (typeof r.get) + ' ' + (typeof r.size));"),
    ('itemsEach', "var c = 0; Packages.mindustry.Vars.content.items().each(function(x){ c++; }); print('S7:' + c);"),
]
for name, body in CALLS:
    try:
        out = srv.js(SETUP + body)
    except Exception as e:
        print('%-10s EXC %s' % (name, str(e)[-200:]))
        continue
    print('%-10s %s' % (name, [str(x) for x in out if str(x).startswith('S')]))
