
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = [json.loads(l) for l in open(str(_HERE.parent / "questions.jsonl"), encoding="utf-8")]
mc = [r for r in rows if r["type"]=="mc"][0]
print("=== MC sample ===")
print(mc["q"]); print("ANS:", mc["answer"]); print("WHY:", mc["why"])
code = [r for r in rows if r["type"]=="code"][0]
print("=== CODE sample ===")
print(code["q"]); print("ANS:", code["answer"]); print("WHY:", code["why"])
