
import json,subprocess,sys,os
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
root=r"<repo>\knowledge"
gate=os.path.join(root,"tools","check_kb.py")
p=subprocess.run([sys.executable,"-u",gate,"--root",root,"--json"],capture_output=True)
txt=p.stdout.decode('utf-8',errors='replace'); d=json.loads(txt[txt.index('{'):])
print(list(d.keys()))
for k,v in d.items():
    if isinstance(v,list) and v and isinstance(v[0],dict):
        print(k, len(v), list(v[0].keys())); print(json.dumps(v[0],ensure_ascii=False)[:300])
