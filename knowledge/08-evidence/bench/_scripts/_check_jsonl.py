
import json, sys, collections, os
sys.stdout.reconfigure(encoding="utf-8")
p = r"F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\08-evidence\bench\questions.jsonl"
rows = [json.loads(l) for l in open(p, encoding="utf-8")]
print("n", len(rows), "bytes", os.path.getsize(p))
print("keys", sorted(rows[0]))
for r in rows:
    if r["type"] == "code":
        print("CODE", r["id"], r["domain"], r["difficulty"], "lines", len(r["q"].split(chr(10))))
print("---sample mc---")
print(rows[5]["q"]); print("ANS:", rows[5]["answer"]); print("WHY:", rows[5]["why"]); print("SRC:", rows[5]["src"], rows[5]["ver"])
print("---sample calc---")
c = [r for r in rows if r["type"]=="calc"][0]
print(c["q"]); print("ANS:", c["answer"]); print(c["why"])
print(collections.Counter(r["ver"] for r in rows))
bad = [r["id"] for r in rows if "\\n" in r["q"] or "\\u00" in r["q"] or chr(92)+chr(96) in r["q"]]
print("escape-residue", bad[:10])
