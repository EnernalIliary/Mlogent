# -*- coding: utf-8 -*-
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import os, sys, runpy
sys.stdout.reconfigure(encoding="utf-8")
STAGE = str(_KB)
os.environ["KB_ROOT"] = str(_REPO)
os.environ["KB_DIR"] = str(_KB / "_kb_final")
sys.path.insert(0, str(_KB / "tools"))
sys.argv = ["kb.py", "build"]
runpy.run_path(str(_KB / "tools" / "kb.py"), run_name="__main__")
