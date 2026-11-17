
import json,sys,collections
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
for p in [r"<repo>\knowledge\00-data\rules.json", r"<repo>\knowledge\00-data\rt_list_Rules.json"]:
    try:
        d=json.load(open(p,encoding='utf-8'))
    except Exception as e:
        print(p,"ERR",e); continue
    print(p.split('\\')[-1], type(d).__name__, len(d) if not isinstance(d,dict) else list(d.keys())[:6])
recs=json.load(open(r"<repo>\knowledge\00-data\rules.json",encoding='utf-8'))
print(collections.Counter([r.get('type') for r in recs]).most_common())
grouped=collections.defaultdict(list)
for r in recs: grouped[r.get('type')].append(r['name'])
for t,ns in grouped.items(): print(t, len(ns), ns[:8])
