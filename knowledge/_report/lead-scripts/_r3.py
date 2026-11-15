
import json,sys
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
recs=json.load(open(r"<repo>\knowledge\00-data\rules.json",encoding='utf-8'))
for t in ('int','float'):
    print('##',t)
    for r in recs:
        if r.get('type')==t: print(' ',r['name'],'=',r.get('value'),'(def',r.get('default'),')')
print('## boolean with value true')
print(', '.join(r['name'] for r in recs if r.get('type')=='boolean' and r.get('value') is True))
print('## boolean false')
print(', '.join(r['name'] for r in recs if r.get('type')=='boolean' and r.get('value') is False))
