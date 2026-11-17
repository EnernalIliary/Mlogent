
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import os, sys, importlib, collections
sys.path.insert(0, str(_HERE.parent))
os.environ["AS_REPO"] = str(_REPO)
sys.stdout.reconfigure(encoding="utf-8")
import _gen_core as C
mods = {m: importlib.import_module(m) for m in ["_gen_d1","_gen_d2a","_gen_d2b","_gen_d2c"]}
for m, fn in [("_gen_d1","build_exec"),("_gen_d1","build_var"),("_gen_d1","build_flow"),
              ("_gen_d2a","build_io"),("_gen_d2a","build_draw"),("_gen_d2a","build_world"),
              ("_gen_d2b","build_unit"),("_gen_d2b","build_perf"),("_gen_d2b","build_block"),
              ("_gen_d2c","build_power"),("_gen_d2c","build_liquid"),("_gen_d2c","build_combat")]:
    C._QS.clear(); getattr(mods[m], fn)()
    c = collections.Counter(x["difficulty"] for x in C._QS)
    flag = "OK " if (len(C._QS)==25 and c[1]==6 and c[2]==13 and c[3]==6) else "BAD"
    print(f"{flag} {fn:14s} n={len(C._QS):3d} E{c[1]:3d} M{c[2]:3d} H{c[3]:3d}")
