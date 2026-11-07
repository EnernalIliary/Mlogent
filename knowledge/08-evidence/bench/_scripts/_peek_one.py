
import os, sys, importlib, collections
sys.path.insert(0, r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\08-evidence\bench")
os.environ["AS_REPO"] = r"F:\OneDrive\桌面\AtomicStates"
sys.stdout.reconfigure(encoding="utf-8")
import _gen_core as C
mod = importlib.import_module(sys.argv[1]); fn = getattr(mod, sys.argv[2])
C._QS.clear(); fn()
print(len(C._QS), dict(collections.Counter(x["difficulty"] for x in C._QS)))
for i, x in enumerate(C._QS, 1):
    print(i, x["difficulty"], x["type"], x["q"].split("\n")[0][:64])
