# -*- coding: utf-8 -*-
import os, sys, runpy
sys.stdout.reconfigure(encoding="utf-8")
STAGE = r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage"
os.environ["KB_ROOT"] = "F:\\OneDrive\\桌面\\AtomicStates"
os.environ["KB_DIR"] = STAGE + r"\_kb_final"
sys.path.insert(0, STAGE + r"\tools")
sys.argv = ["kb.py", "build"]
runpy.run_path(STAGE + r"\tools\kb.py", run_name="__main__")
