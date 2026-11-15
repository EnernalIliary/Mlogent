
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
b = r"<local-dir>\dse\kb"
base = r"<scratch-dir>\kb-stage\00-data"
def load(n):
    with open(os.path.join(base,n), encoding='utf-8') as f: return json.load(f)
for n in ['blocks.json','bullets.json','units.json','turrets.json','liquids.json','items.json','status.json','rules.json']:
    d = load(n)
    if isinstance(d, dict):
        keys = list(d.keys())[:6]
        print(n, 'dict keys=', keys, 'len=', len(d))
    else:
        print(n, 'list len=', len(d), 'first keys=', list(d[0].keys())[:12] if d else None)
