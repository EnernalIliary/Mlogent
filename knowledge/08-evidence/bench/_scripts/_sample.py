
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = [json.loads(l) for l in open(r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\08-evidence\bench\questions.jsonl", encoding="utf-8")]
mc = [r for r in rows if r["type"]=="mc"][0]
print("=== MC sample ===")
print(mc["q"]); print("ANS:", mc["answer"]); print("WHY:", mc["why"])
code = [r for r in rows if r["type"]=="code"][0]
print("=== CODE sample ===")
print(code["q"]); print("ANS:", code["answer"]); print("WHY:", code["why"])
