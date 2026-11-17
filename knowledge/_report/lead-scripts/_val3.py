
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
base = r"<scratch-dir>\kb-stage\00-data"
B = {x['id']:x for x in json.load(open(os.path.join(base,'blocks.json'),encoding='utf-8'))}
for k in ['graphite-press','silicon-smelter','duo','foreshadow','water-extractor','thermal-generator','mass-driver','payload-conveyor']:
    if k in B:
        print(k, '->', list(B[k].keys()))
print()
print('graphite-press', json.dumps({kk:B['graphite-press'].get(kk) for kk in ('craftTime','outputs','craftEffect','consumers','requirements','health','size')}, ensure_ascii=False)[:800])
BL = {x['id']:x for x in json.load(open(os.path.join(base,'bullets.json'),encoding='utf-8'))}
print('bullet b331767859', json.dumps({kk:BL['b331767859'].get(kk) for kk in ('id','name','damage','speed','lifetime','class')}, ensure_ascii=False)[:400])
T = json.load(open(os.path.join(base,'turrets.json'),encoding='utf-8'))
d=[x for x in T if x['id']=='duo'][0]
print('turret duo', json.dumps({kk:d.get(kk) for kk in ('range','reload','maxAmmo','ammoTypes','coolantMultiplier','targetAir','targetGround','inaccuracy','shootCone')}, ensure_ascii=False)[:600])
