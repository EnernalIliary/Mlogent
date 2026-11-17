
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
base = r"<scratch-dir>\kb-stage\00-data"
B = {x['id']:x for x in json.load(open(os.path.join(base,'blocks.json'),encoding='utf-8'))}
for k in ['duo','laser-drill','conveyor','router','battery','core-shard']:
    if k in B:
        b=B[k]
        keep={kk:vv for kk,vv in b.items() if kk in ('id','category','size','health','armor','itemCapacity','liquidCapacity','hasPower','hasItems','hasLiquids','rotate','solid','buildVisibility','group','power','consumers','requirements','speed','drillTime','tier','craftTime','range','reload','ammoTypes','coolantMultiplier','maxAmmo')}
        print(k, json.dumps(keep, ensure_ascii=False)[:700])
        print('---')
U = {x['id']:x for x in json.load(open(os.path.join(base,'units.json'),encoding='utf-8'))}
print('dagger', json.dumps({k:U['dagger'].get(k) for k in ('health','armor','speed','flying','hitSize','range','weapons','itemCapacity','buildSpeed')}, ensure_ascii=False)[:600])
T = json.load(open(os.path.join(base,'turrets.json'),encoding='utf-8'))
print('turret ids:', ','.join(x['id'] for x in T))
