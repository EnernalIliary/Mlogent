
import os, sys, collections
sys.path.insert(0, r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\08-evidence\bench")
os.environ["AS_REPO"] = r"F:\OneDrive\桌面\AtomicStates"
sys.stdout.reconfigure(encoding="utf-8")
import _gen_core as C, _gen_d1
C._QS.clear(); _gen_d1.build_flow()
print(len(C._QS))
for i, x in enumerate(C._QS, 1):
    print(i, x["difficulty"], x["type"], x["q"].split("\n")[0][:60])
