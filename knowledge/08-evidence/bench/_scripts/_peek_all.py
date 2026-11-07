
import os, sys, importlib, collections
sys.path.insert(0, r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\08-evidence\bench")
os.environ["AS_REPO"] = r"F:\OneDrive\桌面\AtomicStates"
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
