import importlib, sys

IDS = ["L1-%02d" % i for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)] + ["L1-18", "L1-19", "L1-20", "L1-21"]
fails = 0
for pid in IDS:
    mod = importlib.import_module("probe_" + pid)
    try:
        fails += 1 if mod.main() else 0
    except Exception as e:
        print("%s  EXCEPTION  %r" % (pid, e))
        fails += 1
print("TOTAL fails=%d/%d" % (fails, len(IDS)))
try:
    import _harness
    _harness.close()
except Exception:
    pass
sys.exit(1 if fails else 0)
