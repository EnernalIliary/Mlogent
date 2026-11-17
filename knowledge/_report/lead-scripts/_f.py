
import json,sys
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
p=r"<repo>\knowledge\00-data\formulas.json"
d=json.load(open(p,encoding='utf-8'))
recs = d.get('records') if isinstance(d,dict) else d
print("count",len(recs))
for r in recs[:3]:
    print(json.dumps(r,ensure_ascii=False)[:700]); print()
print([r['id'] for r in recs])
