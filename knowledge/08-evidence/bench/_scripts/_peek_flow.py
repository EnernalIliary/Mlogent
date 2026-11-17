
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import os, sys, collections
sys.path.insert(0, str(_HERE.parent))
os.environ["AS_REPO"] = str(_REPO)
sys.stdout.reconfigure(encoding="utf-8")
import _gen_core as C, _gen_d1
C._QS.clear(); _gen_d1.build_flow()
print(len(C._QS))
for i, x in enumerate(C._QS, 1):
    print(i, x["difficulty"], x["type"], x["q"].split("\n")[0][:60])
