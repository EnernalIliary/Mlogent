
import json,sys
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
p=r"<repo>\knowledge\00-data\rules.json"
d=json.load(open(p,encoding='utf-8'))
recs=d.get('records') if isinstance(d,dict) else d
print(type(d), len(recs)); print(json.dumps(recs[:5],ensure_ascii=False,indent=1)[:900])
rt=r"<repo>\knowledge\00-data\rt_list_Rules.json"
d2=json.load(open(rt,encoding='utf-8')); recs2=d2.get('records') if isinstance(d2,dict) else d2
print("rt",len(recs2)); print(json.dumps(recs2[:3],ensure_ascii=False)[:600])
import collections
print(collections.Counter([r.get('type') for r in recs]).most_common(12))
